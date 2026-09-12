"""Isolated right-M9 checks. Uses local physics only; no GPU or live services."""
import copy
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from arena import apply_sources, default_sources, sample_sources, source_at_mouth
from body import make_body, reset_body, muscle_parameters, muscle_state, body_signature
from neuromuscular import NeuromuscularJunction

ROOT = (Path(__file__).resolve().parents[1] / 'runtime')


def replay(events_s, *, dt=0.0001, release_block=False, load=0.0, clamp=None, parameters=None):
    p = muscle_parameters() if parameters is None else parameters
    sim, fly, controller = make_body(parameters=p, clamp_angle=clamp)
    try:
        sim.mj_model.opt.timestep = dt
        reset_body(sim, fly, controller)
        nmj = NeuromuscularJunction(dt, p['nmj'])
        times = np.asarray(events_s) / dt
        assert np.allclose(times, np.rint(times), rtol=0, atol=1e-8)
        events = set(np.rint(times).astype(int))
        data, model = sim.mj_data, sim.mj_model
        assert model.nu == model.na == model.nv == model.nq == 1 and controller is None
        assert model.actuator_trntype[0] == mujoco.mjtTrn.mjTRN_TENDON
        assert model.actuator_dyntype[0] == mujoco.mjtDyn.mjDYN_MUSCLE
        assert model.actuator_gaintype[0] == mujoco.mjtGain.mjGAIN_MUSCLE
        rows = []
        data.qfrc_applied[0] = load  # Positive external torque opposes protraction.
        for step in range(round(0.6 / dt)):
            data.ctrl[0] = nmj.advance(step + 1 in events, release_block=release_block)
            sim.step()
            mujoco.mj_forward(model, data)
            state = muscle_state(sim)
            tension = state['total_tension_uN']
            np.testing.assert_allclose(tension, state['active_tension_uN'] + state['passive_tension_uN'], atol=1e-10)
            np.testing.assert_allclose(data.qfrc_actuator[0], -tension * data.actuator_moment[0], atol=1e-10)
            np.testing.assert_allclose(data.qfrc_actuator[0] * data.qvel[0], -tension * data.actuator_velocity[0], atol=1e-10)
            rows.append([data.time, data.qpos[0], data.qvel[0], data.ctrl[0], data.act[0],
                         state['active_tension_uN'], state['passive_tension_uN'],
                         data.qfrc_actuator[0], data.actuator_length[0], data.qfrc_constraint[0]])
        rows = np.array(rows)
        assert np.isfinite(rows).all() and not np.any(data.warning.number)
        assert np.all((rows[:, 4] >= 0) & (rows[:, 4] <= 1))
        assert rows[:, 1].min() >= p['joint_range_rad'][0] - 0.02
        assert rows[:, 1].max() <= p['joint_range_rad'][1] + 0.02
        assert nmj.received == len(events) and not nmj.pending
        assert nmj.delivered == (0 if release_block else len(events))
        return rows
    finally:
        sim.close()


def main():
    p = muscle_parameters()
    nmj = NeuromuscularJunction(0.0001, p['nmj'])
    signal = [nmj.advance(i == 0) for i in range(20)]
    assert np.flatnonzero(signal)[0] == 11, 'Force excitation preceded emitted event plus delay'
    nmj.reset()
    assert nmj.received == nmj.delivered == nmj.tick == 0 and not nmj.pending
    assert nmj.excitation == 0 and nmj.efficacy == 1
    sim, fly, controller = make_body()
    try:
        reset_body(sim, fly, controller)
        data, model = sim.mj_data, sim.mj_model
        # The native tendon derivative must have the protraction sign over its range.
        for q in np.linspace(*p['joint_range_rad'], 11):
            lengths = []
            for offset in (-1e-6, 1e-6):
                data.qpos[0] = q + offset
                mujoco.mj_forward(model, data)
                lengths.append(data.actuator_length[0])
            derivative = (lengths[1] - lengths[0]) / 2e-6
            assert derivative > 0
            np.testing.assert_allclose(data.actuator_moment[0], derivative, rtol=1e-4)
        reset_body(sim, fly, controller)
        position = source_at_mouth(sim, 0)
        sources = default_sources(False)
        sources[0].update(enabled=True, x=float(position[0]), y=float(position[1]), odor=0)
        apply_sources(sim, sources)
        sensed = sample_sources(sim, sources)
        assert sensed['contacts'] == [0] and sensed['sugar_hz'] == 200
        distance = mujoco.mj_geomDistance(model, data, model.geom('food_0').id,
                                         model.geom('fly/c_haustellum').id, 1, np.zeros(6))
        assert 0 < distance < 0.02, 'Contact placement interpenetrates the mouth'
    finally:
        sim.close()
    trace_path = ROOT / 'neural-motor/mn9-spike-traces.json'
    raw = trace_path.read_bytes()
    source = json.loads(raw)
    # Legacy capture used start-of-bin labels for events returned after each update.
    events = [np.asarray(t['spike_times_s']) + t['dt_s'] for t in source['traces']]
    quiet = replay([])
    blocked = replay(events[0], release_block=True)
    np.testing.assert_allclose(blocked, quiet, rtol=0, atol=0)
    np.testing.assert_allclose(quiet[:, [3, 4, 5, 7]], 0, atol=1e-12)
    active, bitter = replay(events[0]), replay(events[1])
    assert active[:, 5].max() > 0 and active[:, 7].min() < 0
    assert active[:, 1].min() < quiet[:, 1].min() - 1e-4
    loaded = replay(events[0], load=0.05)
    assert loaded[:, 1].min() > active[:, 1].min()
    clamp_angle = float(quiet[0, 1])
    clamped = replay(events[0], clamp=clamp_angle)
    assert abs(clamped[:, 1] - clamp_angle).max() < 0.001
    assert clamped[:, 5].max() > 0 and abs(clamped[:, 9]).max() > 0
    fine = replay(events[0], dt=0.00005)
    metrics = lambda r: np.array([r[:, 1].min(), r[:, 4].max(), r[:, 5].max()])
    error = abs(metrics(active) - metrics(fine)) / np.maximum(abs(metrics(fine)), 1e-12)
    assert error.max() < 0.05
    sensitivity = []
    for factor in (0.8, 1.2):
        variant = copy.deepcopy(p)
        pivot = np.array([0.43, 0, -0.274])
        variant['origin_head_mm'] = (pivot + factor * (np.array(p['origin_head_mm']) - pivot)).tolist()
        variant['insertion_rostrum_mm'] = (factor * np.array(p['insertion_rostrum_mm'])).tolist()
        result = replay(events[0], parameters=variant)
        sensitivity.append(dict(attachment_factor=factor, min_angle_rad=float(result[:, 1].min()),
                                peak_tension_uN=float(result[:, 5].max())))
    output = ROOT.parent / 'runs/muscle-control'
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'traces.npz', quiet=quiet, blocked=blocked, active=active,
                        bitter=bitter, loaded=loaded, clamped=clamped)
    receipt = dict(status='PASS: estimated right-M9 implementation, not biological validation',
        body_sha=body_signature(), trace_sha256=hashlib.sha256(raw).hexdigest(),
        event_timestamp='legacy output-bin index + one DT = end of neural step',
        model=p['model'], input_spikes=[len(e) for e in events],
        actuator_count=1, gait_controller=False, target_angle_controller=False,
        checks=['event delay', 'reset', 'tendon moment arm', 'force decomposition', 'torque/power',
                'nonpenetrating contact placement', 'zero input', 'release block', 'load',
                'isometric reaction', 'half-step convergence', 'finite state', 'geometry sensitivity'],
        passive_rest_angle_rad=float(quiet[-1, 1]), min_active_angle_rad=float(active[:, 1].min()),
        peak_active_tension_uN=float(active[:, 5].max()), max_relative_half_step_error=float(error.max()),
        geometry_sensitivity=sensitivity, parameter_status=p['evidence_status'])
    (output / 'local-check.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

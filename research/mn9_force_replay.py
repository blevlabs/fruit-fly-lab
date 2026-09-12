"""Raw simulated MN9 spikes -> estimated NMJ -> native muscle -> synthetic lever.

This is an integration check, NOT calibrated adult M9 or sensory-loop validation.
Uses mm, g, s (force microN, torque nN*m), as declared by the mechanics probe.
Run: .venv/bin/python -B neural-motor/mn9_force_replay.py
"""

import hashlib
import json
import math
from pathlib import Path

import mujoco as mj
import numpy as np

from muscle_mechanics_probe import XML


# Synthetic hypotheses, not measured adult M9 parameters. Never fit to food response.
NMJ = dict(delay_s=0.001, tau_exc_s=0.008, tau_recovery_s=0.1,
           spike_gain=0.2, depression=0.2)
COLUMNS = ("time_s", "efficacy", "excitation", "step_control", "activation",
           "angle_rad", "length_mm", "velocity_mm_s", "active_force_uN",
           "passive_force_uN", "torque_nNm", "constraint_torque_nNm")


def replay(spikes, duration_s, *, dt=0.0001, release_block=False,
           clamp=False, opposing_load=0.0, params=None):
    p = NMJ if params is None else params
    if (not all(math.isfinite(v) for v in p.values())
            or min(p["tau_exc_s"], p["tau_recovery_s"]) <= 0
            or min(p["delay_s"], p["spike_gain"]) < 0
            or not 0 <= p["depression"] <= 1):
        raise ValueError("Invalid NMJ parameters")
    if not (math.isfinite(dt) and math.isfinite(duration_s)
            and 0 < dt <= duration_s and math.isfinite(opposing_load)):
        raise ValueError("Invalid simulation duration, step or load")
    spikes = np.asarray(spikes, dtype=float)
    if (spikes.ndim != 1 or not np.isfinite(spikes).all()
            or np.any(np.diff(spikes) <= 0) or np.any(spikes < 0)
            or np.any(spikes + p["delay_s"] >= duration_s)):
        raise ValueError("Spikes must be ordered, unique and inside the replay")
    times = (spikes + p["delay_s"]) / dt
    # ponytail: fixed-grid replay; split timesteps at events if off-grid input is needed.
    if not np.allclose(times, np.rint(times), rtol=0, atol=1e-8):
        raise ValueError("This bench requires delayed spikes on the integration grid")
    steps = duration_s / dt
    if not math.isclose(steps, round(steps), rel_tol=0, abs_tol=1e-8):
        raise ValueError("Duration must be on the integration grid")
    events = set(np.rint(times).astype(int))
    if len(events) != len(spikes):
        raise ValueError("Distinct spikes cannot share a grid step")
    xml = XML
    if clamp:
        xml = xml.replace("</mujoco>", """<equality><joint joint1="hinge"
          polycoef="0 0 0 0 0" solref="0.002 1"/></equality></mujoco>""")
    model = mj.MjModel.from_xml_string(xml)
    model.opt.timestep = dt
    data = mj.MjData(model)
    data.qfrc_applied[0] = -opposing_load  # External assay load, independent of food.
    lr, acc0 = model.actuator_lengthrange[0], model.actuator_acc0[0]
    gain, bias = model.actuator_gainprm[0, :9], model.actuator_biasprm[0, :9]
    efficacy, excitation = 1.0, 0.0
    decay = math.exp(-dt / p["tau_exc_s"])
    recovery = math.exp(-dt / p["tau_recovery_s"])
    rows = []
    for step in range(round(steps)):
        if step in events and not release_block:
            excitation += p["spike_gain"] * efficacy
            efficacy *= 1 - p["depression"]
        # Mid-interval excitation drives native activation; no rate or angle target.
        mid_excitation = excitation * math.sqrt(decay)
        data.ctrl[0] = mid_excitation / (1 + mid_excitation)
        mj.mj_step(model, data)
        mj.mj_forward(model, data)
        excitation *= decay
        efficacy = 1 - (1 - efficacy) * recovery
        length, velocity = data.actuator_length[0], data.actuator_velocity[0]
        activation = data.act[model.actuator_actadr[0]]
        active = activation * mj.mju_muscleGain(length, velocity, lr, acc0, gain)
        passive = mj.mju_muscleBias(length, lr, acc0, bias)
        rows.append([data.time, efficacy, excitation, data.ctrl[0], activation,
                     data.qpos[0], length, velocity, active, passive,
                     data.qfrc_actuator[0], data.qfrc_constraint[0]])
    result = np.asarray(rows)
    assert np.isfinite(result).all() and not np.any(data.warning.number)
    assert np.all((result[:, 1] >= 0) & (result[:, 1] <= 1))
    assert np.all((result[:, 4] >= 0) & (result[:, 4] <= 1))
    return result


def summary(rows):
    return dict(peak_activation=float(rows[:, 4].max()),
                peak_active_tension_uN=float(-rows[:, 8].min()),
                final_angle_rad=float(rows[-1, 5]))


def main():
    path = Path(__file__).resolve().parents[1] / "runtime/neural-motor/mn9-spike-traces.json"
    raw = path.read_bytes()
    payload = json.loads(raw)
    assert payload["kind"] == "simulated-neural-spike-traces"
    assert payload["biological_recording"] is False
    traces = payload["traces"]
    assert traces and all(t["neuron_id"] == 720575940660219265 for t in traces)
    results = {}
    for trace in traces:
        # The trace label and stimulus metadata never enter the force computation.
        rows = replay(trace["spike_times_s"], trace["duration_s"] + 0.1)
        results[trace["name"]] = dict(spikes=len(trace["spike_times_s"]), **summary(rows))
    train = traces[0]["spike_times_s"]
    duration = traces[0]["duration_s"] + 0.1
    rest = replay([], duration)
    blocked = replay(train, duration, release_block=True)
    np.testing.assert_allclose(rest, blocked, rtol=0, atol=0)
    np.testing.assert_allclose(rest[:, [2, 3, 4, 5, 8, 10]], 0, atol=1e-12)
    free = replay(train, duration)
    clamped = replay(train, duration, clamp=True)
    loaded = replay(train, duration, opposing_load=0.0005)
    assert abs(clamped[:, 5]).max() < 0.001 and clamped[:, 8].min() < 0
    assert abs(clamped[:, 11]).max() > 0  # Reaction despite near-zero movement.
    assert loaded[-1, 5] < free[-1, 5]
    fine = replay(train, duration, dt=0.00005)
    coarse_metrics, fine_metrics = np.array(list(summary(free).values())), np.array(list(summary(fine).values()))
    relative_error = abs(coarse_metrics - fine_metrics) / np.maximum(abs(fine_metrics), 1e-12)
    assert relative_error.max() < 0.05
    spaced = replay([0.02, 0.07, 0.12, 0.17], 0.3)
    clustered = replay([0.02, 0.022, 0.024, 0.026], 0.3)
    assert not math.isclose(spaced[:, 4].max(), clustered[:, 4].max(), rel_tol=0.01)
    print(json.dumps(dict(
        status="PASS: synthetic spike-to-force integration; not biological validation",
        source_sha256=hashlib.sha256(raw).hexdigest(), source_commit=payload["source_commit"],
        mujoco=mj.__version__, units="mm, g, s; force microN; torque nN*m",
        nmj_parameters=NMJ, parameter_status="synthetic and unfitted",
        mechanics="muscle_mechanics_probe.XML; synthetic lever and generic native muscle",
        sensory_feedback="not implemented", trials=results,
        checks=["zero input", "release block", "isometric reaction", "opposing load",
                "half-step convergence", "equal-count timing dependence", "finite bounded state"],
        max_relative_half_step_error=float(relative_error.max()),
        clamped_peak_angle_rad=float(abs(clamped[:, 5]).max()),
        clamped_peak_reaction_nNm=float(abs(clamped[:, 11]).max()),
    ), indent=2))


if __name__ == "__main__":
    main()

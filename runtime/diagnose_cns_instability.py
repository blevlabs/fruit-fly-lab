"""Capture ordinary Session motor events, then replay its exact mechanical inputs.

Capture requires the staged CUDA worker layout. Replay uses its saved MJB and
mechanical state without a CNS, changing only the requested integration options.
No output is a resumable individual checkpoint or biological qualification.
"""
import argparse
from collections import deque
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace

import mujoco as mj
import numpy as np

HERE = Path(__file__).resolve().parent
if not (HERE / 'cns_body.py').exists():
    sys.path.insert(0, str(HERE.parent))
import checkpoint

NMJ_FIELDS = ('tick', 'received', 'delivered', 'efficacy', 'excitation', 'pending')
FLUID_FIELDS = ('pressure_pa', 'liquid_volume_mm3', 'capacitance_mm3_pa', 'net_boundary_volume_mm3')
PHYSICAL_FILES = ('cns_body.py', 'cns-model.json', 'neuromuscular.py', 'flight_integration.py',
                  'flight_mechanics.py', 'proboscis_muscles.py', 'arena.py',
                  'neural-motor/malecns-motor-map.json')
ARRAYS = ('qpos', 'qvel', 'qacc', 'qacc_smooth', 'act', 'ctrl', 'actuator_force',
          'qfrc_bias', 'qfrc_passive', 'qfrc_actuator', 'qfrc_constraint', 'qfrc_applied',
          'qM', 'ten_length', 'ten_velocity')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def physical_sources():
    root = HERE if (HERE / 'cns_body.py').exists() else HERE.parent
    return {name: sha(root / name) for name in PHYSICAL_FILES}


def json_write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def fields(obj, names):
    return {key: tuple(getattr(obj, key)) if key == 'pending' else copy.deepcopy(getattr(obj, key))
            for key in names}


def grid_tick(time_s, dt):
    tick = round(time_s / dt)
    if not math.isclose(tick * dt, time_s, rel_tol=0, abs_tol=1e-11):
        raise ValueError('Event/state time is off the requested integration grid')
    return tick


def require_timestep(actual, expected):
    """Read-only identity guard; numerical changes belong to mechanical replay."""
    if not all(math.isfinite(v) and v > 0 for v in (actual, expected)):
        raise ValueError('Expected a positive finite capture timestep')
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-15):
        raise ValueError(f'Loaded capture timestep {actual} differs from expected {expected}')


def restore_nmj(nmj, state, original_dt):
    checkpoint.require_keys(state, NMJ_FIELDS)
    for key in NMJ_FIELDS:
        value = state[key]
        if key == 'tick':
            value = grid_tick(value * original_dt, nmj.dt)
        elif key == 'pending':
            value = deque(grid_tick(tick * original_dt, nmj.dt) for tick in value)
        setattr(nmj, key, copy.deepcopy(value))


def mechanical_state(session, sources, release_block):
    model, data = session.sim.mj_model, session.sim.mj_data
    native = np.empty(mj.mj_stateSize(model, mj.mjtState.mjSTATE_INTEGRATION))
    mj.mj_getState(model, data, native, mj.mjtState.mjSTATE_INTEGRATION)
    return dict(kind='motor-event-mechanical-replay-v1', native=native,
        initial_neural_tick=session.brain.tick, neural_dt=session.brain.dt,
        physics_dt=session.sim.timestep, sources=copy.deepcopy(sources), release_block=release_block,
        motor_ids=session.motor_ids, regular_positions=session.regular_positions,
        flight_positions=session.flight_positions,
        coverage={k: copy.deepcopy(session.coverage[k]) for k in ('motor_units', 'flight_motor_units')},
        nmjs=[fields(n, NMJ_FIELDS) for n in session.motors.nmjs],
        flight=[dict(nmj=fields(s.nmj if u['kind'] == 'asynchronous' else s, NMJ_FIELDS),
                     muscle=fields(s, ('activation', 'fast_strain', 'slow_strain'))
                     if u['kind'] == 'asynchronous' else None)
                for u, s in zip(session.flight.units, session.flight.states)],
        flight_forces=copy.deepcopy(session.flight.last_forces),
        fluid=fields(session.fluid, FLUID_FIELDS), physical_sources=physical_sources())


def model_bytes(model):
    buffer = np.empty(mj.mj_sizeModel(model), dtype=np.uint8)
    mj.mj_saveModel(model, None, buffer)
    return buffer.tobytes()


class Diagnostics:
    """Bounded successful-step history; full failure vectors are diagnostic only."""
    def __init__(self, model, data, output, focus, ring_steps):
        self.model, self.data, self.output = model, data, Path(output)
        self.joint = model.joint(focus)
        self.focus = int(self.joint.dofadr[0])
        self.body = int(self.joint.bodyid[0])
        self.ring = deque(maxlen=ring_steps)
        self.completed = 0
        self.initial_time = float(data.time)
        self.pending = None
        self.stage = 'initial'
        self.max_abs_raw_qacc = 0.
        per_step = sum(getattr(data, key).nbytes for key in ARRAYS) + 3*data.qvel.nbytes + data.qpos.nbytes
        if per_step * ring_steps > 256 * 1024**2:
            raise ValueError('Requested diagnostic ring exceeds 256 MiB; use fewer ring steps')
        json_write(self.output / 'model-info.json', dict(
            focus_joint=focus, focus_dof=self.focus, focus_body=model.body(self.body).name,
            focus_mass_g=float(model.body_mass[self.body]),
            focus_body_inertia_g_mm2=model.body_inertia[self.body].tolist(),
            focus_damping=float(model.dof_damping[self.focus]),
            focus_armature=float(model.dof_armature[self.focus]),
            focus_stiffness=float(model.jnt_stiffness[self.joint.id]),
            joint_names=[model.joint(i).name for i in range(model.njnt)],
            joint_dofadr=model.jnt_dofadr.tolist(), joint_qposadr=model.jnt_qposadr.tolist(),
            actuator_names=[model.actuator(i).name for i in range(model.nu)],
            tendon_names=[model.tendon(i).name for i in range(model.ntendon)],
            dt=float(model.opt.timestep), integrator=int(model.opt.integrator),
            solver=int(model.opt.solver), tolerance=float(model.opt.tolerance),
            iterations=int(model.opt.iterations), noslip_iterations=int(model.opt.noslip_iterations),
            mjMAXVAL=float(mj.mjMAXVAL), projected_ring_bytes=per_step*ring_steps,
            array_semantics='qpos/qvel are after mj_step; qacc/force/M are that step raw quantities before the subsequent Session mj_forward; qpos_before/qvel_before identify the force evaluation pose; qacc_before preserves the entry acceleration before a warning can alter it; dv_dt is actual integrated velocity change'))

    def step(self, operation):
        self.stage = 'mj_step'
        self.pending = dict(time_before=float(self.data.time), qpos_before=self.data.qpos.copy(),
                            qvel_before=self.data.qvel.copy(), qacc_before=self.data.qacc.copy())
        operation()
        row = {key: getattr(self.data, key).copy() for key in ARRAYS}
        row.update(self.pending)
        row['dv_dt'] = (self.data.qvel - self.pending['qvel_before']) / self.model.opt.timestep
        self.completed += 1
        row.update(time=float(self.data.time), completed_step=self.completed,
                   ncon=int(self.data.ncon), nefc=int(self.data.nefc))
        self.ring.append(row)
        self.max_abs_raw_qacc = max(self.max_abs_raw_qacc, float(np.max(np.abs(self.data.qacc))))
        self.pending = None
        self.stage = 'after_mj_step_or_sensing'

    def save_failure(self, error):
        d, m = self.data, self.model
        arrays = {key: getattr(d, key).copy() for key in ARRAYS}
        if self.pending is not None:
            arrays.update(self.pending)
        dense_m = np.empty((m.nv, m.nv))
        mj.mj_fullM(m, dense_m, d.qM)
        arrays['mass_matrix'] = dense_m
        for key in ('efc_type', 'efc_id', 'efc_pos', 'efc_vel', 'efc_force', 'efc_aref'):
            arrays[key] = getattr(d, key).copy()
        # Retain the focus column without allocating a dense constraint matrix.
        column = np.zeros(d.nefc)
        if mj.mj_isSparse(m):
            for row in range(d.nefc):
                adr, count = d.efc_J_rowadr[row], d.efc_J_rownnz[row]
                local = np.flatnonzero(d.efc_J_colind[adr:adr+count] == self.focus)
                if len(local):
                    column[row] = d.efc_J[adr + local[0]]
        elif d.nefc:
            column = d.efc_J.reshape(d.nefc, m.nv)[:, self.focus].copy()
        arrays['efc_J_focus'] = column
        selected = np.argsort(d.contact.dist)[:64]
        for key in ('geom', 'dist', 'pos', 'frame'):
            arrays['contact_' + key] = getattr(d.contact, key)[selected].copy()
        arrays['selected_contact_indices'] = selected
        arrays['body_cvel'] = d.cvel.copy()
        arrays['body_ximat'] = d.ximat.copy()
        np.savez_compressed(self.output / 'failure-arrays.npz', **arrays)
        bad = np.flatnonzero(~np.isfinite(d.qacc) | (np.abs(d.qacc) > mj.mjMAXVAL))
        json_write(self.output / 'failure.json', dict(kind='diagnostic-not-restorable-checkpoint',
            error=f'{type(error).__name__}: {error}', stage=self.stage,
            native_time_s=float(d.time), completed_steps=self.completed,
            qacc_bad_dofs=bad.tolist(), qacc_bad_values=[str(v) for v in d.qacc[bad]],
            focus_qacc=str(d.qacc[self.focus]), contacts_total=int(d.ncon), contacts_retained=len(selected),
            constraint_rows=int(d.nefc), raw_acceleration_checked_before_implicit_update=True))

    def flush(self):
        if self.ring:
            np.savez_compressed(self.output / 'last-steps.npz',
                **{key: np.stack([row[key] for row in self.ring]) for key in self.ring[0]})


def fatal_warning(message):
    raise RuntimeError('MuJoCo physics warning: ' + message)


def capture(args, receipt):
    # Importing Session is deliberately restricted to CUDA capture, not replay.
    import torch
    from arena import validate_sources
    from cns_live import Session
    payload = json.loads(args.sources.read_text())
    sources = validate_sources(payload['sources'] if isinstance(payload, dict) else payload)
    session, diagnostics, events, ticks = None, None, [], []
    try:
        session = Session(seed=args.seed)
        if args.restore:
            session.restore_checkpoint(args.restore)  # Keep ordinary exact-identity validation.
            if session.seed != args.seed:
                raise ValueError('Requested seed differs from restored individual')
        require_timestep(session.sim.timestep, args.expected_dt)
        session.update(dict(paused=True, reset=session.reset_id, sources=sources,
                            release_block=args.release_block))
        initial = mechanical_state(session, sources, args.release_block)
        checkpoint.save(args.output / 'mechanical-initial.npz', initial)
        mj.mj_saveModel(session.sim.mj_model, str(args.output / 'model.mjb'))
        receipt.update(initial_time_s=session.sim.time, initial_neural_tick=session.brain.tick,
            expected_physics_dt=args.expected_dt,
            original_individual_id=session.individual_id, identity=session.identity(),
            fixed_sources=sources, release_block=args.release_block,
            model_sha256=sha(args.output/'model.mjb'), initial_sha256=sha(args.output/'mechanical-initial.npz'),
            physical_sources=initial['physical_sources'], scope='Ordinary coupled CNS capture; no behavior scoring')
        diagnostics = Diagnostics(session.sim.mj_model, session.sim.mj_data, args.output, args.focus_joint, args.ring_steps)
        original_advance, original_step = session.brain.advance, session.sim.step

        def advance():
            spikes = original_advance()
            motor_events = spikes[0, session.motor_indices].to(dtype=torch.bool).cpu().numpy()
            events.append(np.packbits(motor_events, bitorder='little'))
            ticks.append(session.brain.tick)
            return spikes

        session.brain.advance = advance
        session.sim.step = lambda: diagnostics.step(original_step)
        remaining = grid_tick(args.seconds, session.brain.dt)
        if remaining < 1:
            raise ValueError('Capture duration must include at least one neural interval')
        with (args.output/'progress.jsonl').open('x') as stream:
            while remaining:
                count = min(100, remaining)
                frame = session.update(dict(paused=False, reset=session.reset_id, steps=count,
                    sources=sources, release_block=args.release_block))
                stream.write(json.dumps(dict(time_s=frame['time'], neural_tick=frame['step'],
                    qacc_focus=float(session.sim.mj_data.qacc[diagnostics.focus]),
                    max_abs_qacc=float(np.max(np.abs(session.sim.mj_data.qacc))),
                    contacts=frame['physics_contacts'], constraints=frame['physics_constraints']))+'\n')
                stream.flush()
                remaining -= count
        receipt['status'] = 'CAPTURE_COMPLETE'
    except BaseException as error:
        receipt.update(status='FAIL', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
        if diagnostics:
            diagnostics.save_failure(error)
    finally:
        if session is not None:
            np.savez_compressed(args.output/'motor-events.npz', motor_ids=np.asarray(session.motor_ids, dtype=np.int64),
                neural_ticks=np.asarray(ticks, dtype=np.int64),
                event_bits=np.stack(events) if events else np.empty((0, (len(session.motor_ids)+7)//8), dtype=np.uint8))
            receipt.update(final_native_time_s=float(session.sim.time), computed_neural_intervals=len(events),
                event_sha256=sha(args.output/'motor-events.npz'))
            if diagnostics:
                diagnostics.flush()
                receipt.update(completed_physics_steps=diagnostics.completed,
                               max_abs_successful_step_raw_qacc=diagnostics.max_abs_raw_qacc)
            session.sim.close()


def load_mechanics(directory, dt, integrator):
    from arena import validate_sources
    from cns_body import MotorUnits
    from flight_integration import FlightMotorUnits
    from proboscis_muscles import ProboscisHydraulics
    receipt = json.loads((directory/'receipt.json').read_text())
    for name, field in [('model.mjb', 'model_sha256'), ('mechanical-initial.npz', 'initial_sha256'), ('motor-events.npz', 'event_sha256')]:
        if sha(directory/name) != receipt[field]:
            raise ValueError('Capture file changed: ' + name)
    state = checkpoint.load(directory/'mechanical-initial.npz')
    if state['kind'] != 'motor-event-mechanical-replay-v1' or state['physical_sources'] != physical_sources():
        raise ValueError('Mechanical source/config/map identity differs; stage matching source files')
    validate_sources(state['sources'])
    model = mj.MjModel.from_binary_path(str(directory/'model.mjb'))
    before = model_bytes(model)
    original_dt, original_integrator = model.opt.timestep, int(model.opt.integrator)
    dt = original_dt if dt is None else dt
    if not math.isfinite(dt) or not 0 < dt <= original_dt:
        raise ValueError('Replay timestep must be positive and no larger than capture step')
    grid_tick(original_dt, dt)
    substeps = grid_tick(state['neural_dt'], dt)
    if substeps < 1:
        raise ValueError('Physical step exceeds neural event interval')
    model.opt.timestep = dt
    if integrator is not None:
        model.opt.integrator = getattr(mj.mjtIntegrator, 'mjINT_' + integrator.upper())
    data = mj.MjData(model)
    checkpoint.array_like(state['native'], np.empty(mj.mj_stateSize(model, mj.mjtState.mjSTATE_INTEGRATION)))
    mj.mj_setState(model, data, state['native'], mj.mjtState.mjSTATE_INTEGRATION)
    mj.mj_forward(model, data)
    mj.mj_setState(model, data, state['native'], mj.mjtState.mjSTATE_INTEGRATION)
    regular, flight, fluid = MotorUnits(model, state['coverage']), FlightMotorUnits(model, state['coverage']['flight_motor_units']), ProboscisHydraulics(model)
    if sorted(set(regular.ids) | set(flight.ids)) != state['motor_ids']:
        raise ValueError('Mechanical motor identities differ')
    for nmj, saved in zip(regular.nmjs, state['nmjs']):
        restore_nmj(nmj, saved, state['physics_dt'])
    for unit, muscle, saved in zip(flight.units, flight.states, state['flight']):
        restore_nmj(muscle.nmj if unit['kind'] == 'asynchronous' else muscle, saved['nmj'], state['physics_dt'])
        if saved['muscle'] is not None:
            for key, value in saved['muscle'].items():
                setattr(muscle, key, value)
    flight.last_forces = copy.deepcopy(state['flight_forces'])
    for key in FLUID_FIELDS:
        setattr(fluid, key, copy.deepcopy(state['fluid'][key]))
    return state, model, data, regular, flight, fluid, substeps, (before, original_dt, original_integrator)


def compare_ring(directory, output, original_dt, dt):
    if not (directory/'last-steps.npz').exists() or not (output/'last-steps.npz').exists():
        return dict(matched_steps=0)
    with np.load(directory/'last-steps.npz', allow_pickle=False) as a, np.load(output/'last-steps.npz', allow_pickle=False) as b:
        ratio = grid_tick(original_dt, dt)
        lookup = {int(step): i for i, step in enumerate(b['completed_step'])}
        pairs = [(i, lookup[int(step)*ratio]) for i, step in enumerate(a['completed_step']) if int(step)*ratio in lookup]
        result = dict(matched_steps=len(pairs), comparison='Same absolute physical times in retained rings; no claim beyond captured motor-event horizon')
        if pairs:
            ia, ib = np.asarray(pairs).T
            for key in ('qpos', 'qvel', 'act', 'ctrl'):
                result[key] = dict(exact_equal=bool(np.array_equal(a[key][ia], b[key][ib])),
                    max_abs_error=float(np.max(np.abs(a[key][ia]-b[key][ib]), initial=0)))
        return result


def replay(args, receipt):
    from arena import sample_contact_taste
    diagnostics = None
    try:
        state, model, data, regular, flight, fluid, substeps, original = load_mechanics(args.capture, args.dt, args.integrator)
        sim = SimpleNamespace(mj_model=model, mj_data=data, timestep=model.opt.timestep)
        receipt.update(scope='Open-loop mechanical replay of captured CNS events; not a new coupled CNS trajectory',
            capture=str(args.capture), captured_receipt_sha256=sha(args.capture/'receipt.json'),
            event_sha256=sha(args.capture/'motor-events.npz'), initial_time_s=float(data.time),
            physics_dt=float(model.opt.timestep), integrator=int(model.opt.integrator),
            physical_sources=physical_sources(), fixed_sources=state['sources'])
        diagnostics = Diagnostics(model, data, args.output, args.focus_joint, args.ring_steps)
        with np.load(args.capture/'motor-events.npz', allow_pickle=False) as archive:
            ids, ticks, packed = archive['motor_ids'], archive['neural_ticks'], archive['event_bits']
            if (not np.array_equal(ids, state['motor_ids']) or ticks.dtype != np.int64
                    or packed.dtype != np.uint8 or packed.shape != (len(ticks), (len(ids)+7)//8)
                    or not np.array_equal(ticks, np.arange(state['initial_neural_tick']+1, state['initial_neural_tick']+len(ticks)+1))):
                raise ValueError('Invalid captured event identities, shape or clock')
            events = np.unpackbits(packed, axis=1, count=len(ids), bitorder='little').astype(bool)
        silent = np.zeros(len(state['motor_ids']), dtype=bool)
        for neural_tick, event in zip(ticks, events):
            for substep in range(substeps):
                due = event if substep == substeps-1 else silent
                regular.advance(data, due[state['regular_positions']], release_block=state['release_block'])
                flight.advance(data, due[state['flight_positions']], release_block=state['release_block'])
                wet = bool(sample_contact_taste(sim, state['sources'])['wet_contacts'])
                fluid.advance(data, model.opt.timestep, inlet_pressure_pa=0.0 if wet else None)
                data.qfrc_applied[:] = fluid.generalized_forces(data)
                diagnostics.step(lambda: mj.mj_step(model, data))
                mj.mj_forward(model, data)  # Same extra forward call as Session.update.
            if not math.isclose(data.time, neural_tick*state['neural_dt'], abs_tol=1e-9):
                raise RuntimeError('Mechanical replay clock differs from captured event clock')
        receipt.update(status='REPLAY_COMPLETE', computed_neural_intervals=len(events),
                       event_horizon_s=float(ticks[-1]*state['neural_dt']) if len(ticks) else float(data.time))
    except BaseException as error:
        receipt.update(status='FAIL', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
        if diagnostics:
            diagnostics.save_failure(error)
    finally:
        if diagnostics:
            diagnostics.flush()
            receipt.update(final_native_time_s=float(data.time), completed_physics_steps=diagnostics.completed,
                max_abs_successful_step_raw_qacc=diagnostics.max_abs_raw_qacc,
                captured_ring_comparison=compare_ring(args.capture, args.output, state['physics_dt'], model.opt.timestep))
            changed_dt, changed_integrator = model.opt.timestep, int(model.opt.integrator)
            model.opt.timestep, model.opt.integrator = original[1:]
            unchanged = model_bytes(model) == original[0]
            model.opt.timestep, model.opt.integrator = changed_dt, changed_integrator
            receipt['model_unchanged_except_timestep_integrator'] = unchanged
            if not unchanged:
                receipt.update(status='FAIL', model_integrity_error='Unexpected model-array change during mechanical replay')


def self_check():
    from neuromuscular import NeuromuscularJunction
    require_timestep(1e-5, 1e-5)
    require_timestep(2.5e-6, 2.5e-6)
    for actual, expected in [(2.5e-6, 1e-5), (1e-5, 0), (1e-5, math.nan)]:
        try:
            require_timestep(actual, expected)
        except ValueError:
            pass
        else:
            raise AssertionError('Capture timestep mismatch accepted')
    p = dict(delay_s=.001, tau_exc_s=.008, tau_recovery_s=.1, spike_gain=.2, depression=.2)
    a = NeuromuscularJunction(1e-5, p)
    for i in range(20):
        a.advance(i == 0)
    b = NeuromuscularJunction(5e-6, p)
    restore_nmj(b, fields(a, NMJ_FIELDS), a.dt)
    assert b.tick == 2*a.tick and tuple(b.pending) == tuple(2*t for t in a.pending)
    for _ in range(150):
        a.advance(False)
        b.advance(False)
        b.advance(False)
        assert math.isclose(a.excitation, b.excitation, abs_tol=1e-12)
    model = mj.MjModel.from_xml_string('<mujoco><option timestep=".00001" integrator="implicitfast"/><worldbody><body><joint name="hinge"/><geom type="sphere" size=".1" mass="1"/></body></worldbody></mujoco>')
    data = mj.MjData(model)
    with tempfile.TemporaryDirectory() as directory:
        recorder = Diagnostics(model, data, directory, 'hinge', 2)
        for _ in range(3):
            recorder.step(lambda: mj.mj_step(model, data))
            mj.mj_forward(model, data)
        recorder.flush()
        recorder.save_failure(RuntimeError('synthetic diagnostic-format check'))
        with np.load(Path(directory)/'last-steps.npz', allow_pickle=False) as saved:
            assert saved['completed_step'].tolist() == [2, 3]
            np.testing.assert_array_equal(saved['dv_dt'], 0)
    print('PASS: capture timestep guard; delayed-event regridding preserves physical delivery time; bounded raw/integrated-step diagnostics serialize')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('self-check')
    for name in ('capture', 'replay'):
        p = sub.add_parser(name)
        p.add_argument('--output', required=True, type=Path)
        p.add_argument('--focus-joint', default='fly/flight_R_ax4_flexure_1')
        p.add_argument('--ring-steps', type=int, default=512)
        if name == 'capture':
            p.add_argument('--sources', required=True, type=Path)
            p.add_argument('--seed', type=int, default=0)
            p.add_argument('--seconds', type=float, default=.8)
            p.add_argument('--expected-dt', type=float, default=1e-5,
                           help='Require this loaded Session timestep; does not change the model (default: 10 us)')
            p.add_argument('--restore', type=Path)
            p.add_argument('--release-block', action='store_true')
        else:
            p.add_argument('capture', type=Path)
            p.add_argument('--dt', type=float)
            p.add_argument('--integrator', choices=('implicitfast', 'implicit'))
    args = parser.parse_args()
    if args.mode == 'self-check':
        self_check()
        return
    if args.ring_steps < 1 or (args.mode == 'capture' and
            (args.seed < 0 or not math.isfinite(args.seconds) or args.seconds <= 0
             or not math.isfinite(args.expected_dt) or args.expected_dt <= 0)):
        parser.error('Positive finite duration/timestep/ring size and nonnegative seed required')
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = dict(status='RUNNING', kind='instability-diagnosis', biological_validation='not tested',
                   capability='not tested', runner_source_sha256=sha(__file__), mujoco=mj.__version__)
    old_warning = mj.get_mju_user_warning()
    mj.set_mju_user_warning(fatal_warning)
    try:
        (capture if args.mode == 'capture' else replay)(args, receipt)
    finally:
        mj.set_mju_user_warning(old_warning)
        receipt['wall_seconds'] = time.monotonic()-started
        json_write(args.output/'receipt.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('identity', 'traceback', 'physical_sources')}, indent=2))
    if receipt['status'] == 'FAIL':
        raise SystemExit(1)


if __name__ == '__main__':
    main()

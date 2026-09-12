"""Causal whole-CNS -> supported muscles -> body -> supported senses worker.

No direct neural/motor stimulation, default walking drive, gait or action policy.
Unimplemented peripheral pathways remain explicit in the ready/coverage report.
"""
from contextlib import redirect_stdout
from collections import deque
import copy
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import random
import re
import sys
import uuid

import pyarrow
import numpy as np
import torch
import mujoco

from cns import CNS
from cns_body import MotorUnits, body_signature, config, make_body
from cns_senses import Senses
from flight_integration import FlightMotorUnits
from proboscis_muscles import ProboscisHydraulics
from arena import apply_sources, default_sources, validate_sources, sample_contact_taste, SOURCE_Z_MM
import checkpoint

ROOT = Path(__file__).resolve().parent
NMJ_FIELDS = ('tick', 'received', 'delivered', 'efficacy', 'excitation', 'pending')
FLUID_FIELDS = ('pressure_pa', 'liquid_volume_mm3', 'capacitance_mm3_pa', 'net_boundary_volume_mm3')
SENSORY_FIELDS = dict(vision=('last_tick', 'source_state', 'irradiance', 'hits', 'origins'),
    proprio=('last_time', 'last_angles', 'velocity'),
    thermal=('time', 'temperature', 'adapted_temperature'))
SESSION_FIELDS = ('reset_id', 'trial_id', 'individual_id', 'seed', 'total_spikes',
    'total_motor_spikes', 'motor_counts', 'last_sources', 'last_request',
    'fluid_report', 'max_fluid_residual_mm3')
SOURCE_FILES = ('cns.py', 'cns_live.py', 'checkpoint.py', 'cns_body.py', 'cns_senses.py',
    'cns_vision.py', 'cns_proprio.py', 'cns_thermal.py', 'arena.py', 'body.py',
    'neuromuscular.py', 'leg_muscles.py', 'head_muscles.py', 'proboscis_muscles.py',
    'flight_mechanics.py', 'flight_integration.py', 'cns-model.json', 'muscle9.json',
    'eon-brain/code/run_pytorch.py', 'neural-motor/malecns-motor-map.json',
    'neural-motor/malecns-sensory-map.json')


def source_hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCE_FILES}


LOADED_SOURCES = source_hashes()


def fields(obj, names):
    return {name: tuple(getattr(obj, name)) if name == 'pending' else copy.deepcopy(getattr(obj, name)) for name in names}


def restore_fields(obj, values, names):
    checkpoint.require_keys(values, names)
    for name in names:
        setattr(obj, name, deque(values[name]) if name == 'pending' else copy.deepcopy(values[name]))


def physics_warning(message):
    raise RuntimeError(f'MuJoCo physics warning: {message}')


class Session:
    def __init__(self, seed=0):
        with redirect_stdout(sys.stderr):
            self.brain = CNS()
            self.sim, self.fly, self.coverage = make_body()
            self.motors = MotorUnits(self.sim.mj_model, self.coverage)
            self.flight = FlightMotorUnits(self.sim.mj_model, self.coverage['flight_motor_units'])
            self.fluid = ProboscisHydraulics(self.sim.mj_model)
            self.senses = Senses()
        model_bytes = np.empty(mujoco.mj_sizeModel(self.sim.mj_model), dtype=np.uint8)
        mujoco.mj_saveModel(self.sim.mj_model, None, model_bytes)
        self.compiled_model_sha256 = hashlib.sha256(model_bytes.tobytes()).hexdigest()
        self.substeps = round(self.brain.dt / self.sim.timestep)
        if self.substeps < 1 or not math.isclose(self.brain.dt, self.substeps * self.sim.timestep):
            raise RuntimeError('Neural timestep must contain an integer number of physical substeps')
        if not math.isclose(self.brain.dt, config()['neural_timestep_s']):
            raise RuntimeError('Declared neural timestep differs from the actual neural model')
        if not self.senses.wired_ids <= self.brain.sensory_ids:
            raise RuntimeError('An environmental input is not a MaleCNS sensory neuron')
        self.motor_ids = sorted(set(self.motors.ids) | set(self.flight.ids))
        if not set(self.motor_ids) <= set(map(int, self.brain.motor_ids)):
            raise RuntimeError('A peripheral force input is not a MaleCNS motor neuron')
        self.motor_indices = torch.tensor([self.brain.lookup[i] for i in self.motor_ids], device='cuda')
        positions = {body_id: i for i, body_id in enumerate(self.motor_ids)}
        self.regular_positions = [positions[i] for i in self.motors.ids]
        self.flight_positions = [positions[i] for i in self.flight.ids]
        self.silent_events = np.zeros(len(self.motor_ids), dtype=bool)
        self.reset_id = 0
        self.seed = seed
        self.reset()
        self._identity = self._build_identity()

    def reset(self):
        """A fresh individual; trial transitions and pause never call this."""
        self.brain.reset(self.seed)
        self.motors.reset()
        self.flight.reset()
        self.sim.reset()
        self.senses.reset()
        apply_sources(self.sim, default_sources(False))
        self.fluid.reset(self.sim.mj_data)
        self.fluid_report = dict(pressure_pa=self.fluid.pressure_pa.tolist(),
            liquid_volume_mm3=self.fluid.liquid_volume_mm3.tolist(),
            net_boundary_volume_mm3=dict(self.fluid.net_boundary_volume_mm3),
            scope='Primed circuit at initialization; initial liquid is not newly ingested food')
        self.max_fluid_residual_mm3 = 0.0
        self.total_spikes = self.total_motor_spikes = 0
        self.counts = torch.zeros_like(self.brain.rates)
        self.motor_counts = np.zeros(len(self.motor_ids), dtype=np.int64)
        self.last_sources = None
        self.last_request = None
        self.trial_id = 0
        self.individual_id = str(uuid.uuid4())

    def _build_identity(self):
        if source_hashes() != LOADED_SOURCES:
            raise RuntimeError('Source changed since import; retain the loaded worker and stage changes separately')
        return dict(schema=1, sources=copy.deepcopy(LOADED_SOURCES),
            body=body_signature(), compiled_model=self.compiled_model_sha256, senses=self.senses.sha256,
            graph=self.brain.manifest['artifact_sha256'], parameters=config(),
            dependencies={d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
            python=sys.version, gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda,
            state_spec=int(mujoco.mjtState.mjSTATE_INTEGRATION),
            motor_ids=self.motor_ids, neural_ids_sha256=hashlib.sha256(self.brain.ids.tobytes()).hexdigest())

    def identity(self):
        """The loaded implementation's identity, unaffected by later disk edits."""
        return copy.deepcopy(self._identity)

    def export_state(self):
        """Explicit scientific state, including caches that affect the next step."""
        model, data = self.sim.mj_model, self.sim.mj_data
        native = np.empty(mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_INTEGRATION))
        mujoco.mj_getState(model, data, native, mujoco.mjtState.mjSTATE_INTEGRATION)
        flight = []
        for unit, state in zip(self.flight.units, self.flight.states):
            flight.append(dict(kind=unit['kind'], nmj=fields(state.nmj if unit['kind'] == 'asynchronous' else state, NMJ_FIELDS),
                muscle=fields(state, ('activation', 'fast_strain', 'slow_strain')) if unit['kind'] == 'asynchronous' else None))
        return dict(identity=self.identity(), brain=self.brain.export_state(), native=native,
            session=fields(self, SESSION_FIELDS), counts=self.counts.cpu().numpy().copy(),
            nmjs=[fields(nmj, NMJ_FIELDS) for nmj in self.motors.nmjs], flight=flight,
            flight_forces=copy.deepcopy(self.flight.last_forces), fluid=fields(self.fluid, FLUID_FIELDS),
            senses={name: fields(getattr(self.senses, name), names) for name, names in SENSORY_FIELDS.items()},
            rng=dict(python=random.getstate(), numpy=np.random.get_state(),
                torch=torch.get_rng_state().numpy().copy(),
                cuda=[v.numpy().copy() for v in torch.cuda.get_rng_state_all()]))

    def _validate_state(self, state):
        checkpoint.require_keys(state, ('identity', 'brain', 'native', 'session', 'counts', 'nmjs',
            'flight', 'flight_forces', 'fluid', 'senses', 'rng'))
        if state['identity'] != self.identity():
            raise ValueError('Checkpoint model, data, source or runtime identity differs')
        self.brain.validate_state(state['brain'])
        checkpoint.array_like(state['native'], np.empty(mujoco.mj_stateSize(self.sim.mj_model, mujoco.mjtState.mjSTATE_INTEGRATION)))
        checkpoint.array_like(state['counts'], self.counts.cpu().numpy())
        checkpoint.require_keys(state['session'], SESSION_FIELDS)
        s = state['session']
        if any(type(s[k]) is not int or s[k] < 0 for k in ('reset_id', 'trial_id', 'seed', 'total_spikes', 'total_motor_spikes')):
            raise ValueError('Invalid checkpoint counters')
        if type(s['individual_id']) is not str or str(uuid.UUID(s['individual_id'])) != s['individual_id']:
            raise ValueError('Invalid individual identity')
        checkpoint.array_like(s['motor_counts'], self.motor_counts)
        if s['last_sources'] is not None:
            validate_sources(s['last_sources'])
        request = s['last_request']
        if request is None:
            if state['brain']['tick'] or s['last_sources'] is not None:
                raise ValueError('Missing current checkpoint environment/intervention')
        else:
            checkpoint.require_keys(request, ('paused', 'reset', 'steps', 'sources', 'release_block'))
            if (type(request['paused']) is not bool or type(request['release_block']) is not bool
                    or type(request['steps']) is not int or not 1 <= request['steps'] <= 100
                    or type(request['reset']) is not int or request['reset'] != s['reset_id']
                    or request['sources'] != s['last_sources']):
                raise ValueError('Invalid current checkpoint environment/intervention')
        native_probe = mujoco.MjData(self.sim.mj_model)
        mujoco.mj_setState(self.sim.mj_model, native_probe, state['native'], mujoco.mjtState.mjSTATE_INTEGRATION)
        for i, source in enumerate(s['last_sources'] or default_sources(False)):
            mocap = self.sim.mj_model.body(f'source_{i}').mocapid[0]
            expected = (source['x'], source['y'], SOURCE_Z_MM) if source['enabled'] else (999, 999, SOURCE_Z_MM)
            if not np.array_equal(native_probe.mocap_pos[mocap], expected):
                raise ValueError('Checkpoint source settings differ from physical source positions')
        del native_probe
        if len(state['nmjs']) != len(self.motors.nmjs) or len(state['flight']) != len(self.flight.states):
            raise ValueError('Checkpoint motor-state count differs')
        physical_tick = state['brain']['tick'] * self.substeps
        if not math.isclose(state['native'][0], state['brain']['tick'] * self.brain.dt, abs_tol=1e-9):
            raise ValueError('Checkpoint body/neural clock mismatch')

        def validate_nmj(value, nmj):
            checkpoint.require_keys(value, NMJ_FIELDS)
            if (value['tick'] != physical_tick or any(type(value[k]) is not int or value[k] < 0 for k in ('tick', 'received', 'delivered'))
                    or not 0 <= value['efficacy'] <= 1 or not math.isfinite(value['excitation']) or value['excitation'] < 0
                    or value['delivered'] > value['received'] or not isinstance(value['pending'], tuple)
                    or any(type(t) is not int or not physical_tick <= t <= physical_tick+nmj.delay_steps for t in value['pending'])
                    or any(a >= b for a, b in zip(value['pending'], value['pending'][1:]))):
                raise ValueError('Invalid delayed NMJ checkpoint state')

        for value, nmj in zip(state['nmjs'], self.motors.nmjs):
            validate_nmj(value, nmj)
        for value, unit, current in zip(state['flight'], self.flight.units, self.flight.states):
            checkpoint.require_keys(value, ('kind', 'nmj', 'muscle'))
            if value['kind'] != unit['kind']:
                raise ValueError('Checkpoint muscle class differs')
            asynchronous = unit['kind'] == 'asynchronous'
            validate_nmj(value['nmj'], current.nmj if asynchronous else current)
            if asynchronous:
                checkpoint.require_keys(value['muscle'], ('activation', 'fast_strain', 'slow_strain'))
                if not all(math.isfinite(v) for v in value['muscle'].values()) or not 0 <= value['muscle']['activation'] <= 1:
                    raise ValueError('Invalid asynchronous muscle checkpoint')
            elif value['muscle'] is not None:
                raise ValueError('Unexpected synchronous muscle history')
        checkpoint.require_keys(state['fluid'], FLUID_FIELDS)
        for name in FLUID_FIELDS[:-1]:
            checkpoint.array_like(state['fluid'][name], getattr(self.fluid, name))
        if np.any(state['fluid']['liquid_volume_mm3'] <= 0) or np.any(state['fluid']['capacitance_mm3_pa'] <= 0):
            raise ValueError('Invalid primed fluid checkpoint')
        checkpoint.require_keys(state['fluid']['net_boundary_volume_mm3'], self.fluid.net_boundary_volume_mm3)
        checkpoint.require_keys(state['senses'], SENSORY_FIELDS)
        for name, names in SENSORY_FIELDS.items():
            checkpoint.require_keys(state['senses'][name], names)
        physical_time = float(state['native'][0])
        for group, name in [('thermal', 'time'), ('proprio', 'last_time')]:
            value = state['senses'][group][name]
            if value is None and group == 'proprio' and physical_tick == 0:
                continue
            if type(value) not in (float, int) or not math.isfinite(value) or not math.isclose(value, physical_time, abs_tol=1e-12):
                raise ValueError('Checkpoint sensory/body clock mismatch')
        vision = state['senses']['vision']
        if vision['last_tick'] is not None:
            if type(vision['last_tick']) is not int or not 0 <= vision['last_tick'] <= physical_tick:
                raise ValueError('Invalid optical checkpoint clock')
            expected_sources = tuple((v['enabled'], v['x'], v['y']) for v in s['last_sources'])
            if vision['source_state'] != expected_sources or vision['origins'] is None:
                raise ValueError('Invalid optical checkpoint registration/cache')
        elif physical_tick or vision['source_state'] is not None:
            raise ValueError('Missing optical checkpoint clock/cache')
        # Optional caches are absent only before their first observation.
        for group, name, shape in [('vision', 'irradiance', (len(self.senses.vision.ids),)),
                ('vision', 'hits', (len(self.senses.vision.columns),)), ('vision', 'origins', (len(self.senses.vision.columns), 3)),
                ('proprio', 'velocity', (6,)), ('proprio', 'last_angles', (6,)),
                ('thermal', 'temperature', (2,)), ('thermal', 'adapted_temperature', (2,))]:
            value = state['senses'][group][name]
            if value is None and name in ('origins', 'last_angles'):
                continue
            if not isinstance(value, np.ndarray) or value.shape != shape or not np.isfinite(value).all():
                raise ValueError('Invalid sensory checkpoint array')
        checkpoint.require_keys(state['rng'], ('python', 'numpy', 'torch', 'cuda'))
        random.Random().setstate(state['rng']['python'])
        np.random.RandomState().set_state(state['rng']['numpy'])
        torch.Generator().set_state(torch.from_numpy(state['rng']['torch']))
        if len(state['rng']['cuda']) != torch.cuda.device_count():
            raise ValueError('Checkpoint CUDA RNG count differs')
        for index, value in enumerate(state['rng']['cuda']):
            torch.Generator(device=f'cuda:{index}').set_state(torch.from_numpy(value))

    def _apply_state(self, state):
        # Source settings also mutate broad-phase model masks, outside mjData.
        sources = state['session']['last_sources'] or default_sources(False)
        apply_sources(self.sim, sources)
        model, data = self.sim.mj_model, self.sim.mj_data
        mujoco.mj_setState(model, data, state['native'], mujoco.mjtState.mjSTATE_INTEGRATION)
        mujoco.mj_forward(model, data)
        # mj_forward computes derived observables but can update warmstart. The
        # saved integration state, not that extra solve, owns the next trajectory.
        mujoco.mj_setState(model, data, state['native'], mujoco.mjtState.mjSTATE_INTEGRATION)
        self.brain.import_state(state['brain'])
        restore_fields(self, state['session'], SESSION_FIELDS)
        self.counts.copy_(torch.from_numpy(state['counts']))
        for value, nmj in zip(state['nmjs'], self.motors.nmjs):
            restore_fields(nmj, value, NMJ_FIELDS)
        for value, unit, current in zip(state['flight'], self.flight.units, self.flight.states):
            restore_fields(current.nmj if unit['kind'] == 'asynchronous' else current, value['nmj'], NMJ_FIELDS)
            if unit['kind'] == 'asynchronous':
                restore_fields(current, value['muscle'], ('activation', 'fast_strain', 'slow_strain'))
        self.flight.last_forces = copy.deepcopy(state['flight_forces'])
        restore_fields(self.fluid, state['fluid'], FLUID_FIELDS)
        for name, names in SENSORY_FIELDS.items():
            restore_fields(getattr(self.senses, name), state['senses'][name], names)
        if self.senses.vision.origins is not None:
            self.senses.vision.ground = set(np.flatnonzero(model.geom_type == mujoco.mjtGeom.mjGEOM_PLANE))
            self.senses.vision.food = {model.geom(f'food_{i}').id for i in range(2)}
        random.setstate(state['rng']['python'])
        np.random.set_state(state['rng']['numpy'])
        torch.set_rng_state(torch.from_numpy(state['rng']['torch']))
        torch.cuda.set_rng_state_all([torch.from_numpy(v) for v in state['rng']['cuda']])

    def import_state(self, state):
        try:
            self._validate_state(state)
        except RuntimeError as error:
            raise ValueError(f'Invalid checkpoint state: {error}') from error
        previous = self.export_state()
        try:
            self._apply_state(state)
        except Exception:
            self._apply_state(previous)
            raise

    def save_checkpoint(self, path):
        state = self.export_state()
        self._validate_state(state)
        checkpoint.save(path, state)

    def restore_checkpoint(self, path):
        self.import_state(checkpoint.load(path))

    def transition_trial(self, sources, *, release_block=False):
        """Change the physical environment without resetting acquired state."""
        frame = self.update(dict(paused=True, reset=self.reset_id, sources=sources, release_block=release_block))
        self.trial_id += 1
        return frame

    def checkpoint_command(self, request, directory):
        """Named local slots only; an SSH command cannot supply a filesystem path."""
        checkpoint.require_keys(request, ('checkpoint', 'name'))
        action, name = request['checkpoint'], request['name']
        if action not in ('save', 'restore') or type(name) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', name) is None:
            raise ValueError('Expected save/restore and a 1–64 character checkpoint name')
        path = Path(directory)/(name+'.npz')
        if action == 'save':
            self.save_checkpoint(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            # Read once before mutation. A receipt-read failure after restore
            # must not tell the viewer to keep sending the old reset/environment.
            payload = path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            self.import_state(checkpoint.load(io.BytesIO(payload)))
        return dict(type='checkpoint', action=action, name=name, step=self.brain.tick,
            time=self.sim.time, individual_id=self.individual_id, reset=self.reset_id,
            sources=copy.deepcopy(self.last_sources or default_sources(False)),
            release_block=False if self.last_request is None else self.last_request['release_block'],
            sha256=digest)

    def update(self, request):
        if not isinstance(request, dict):
            raise ValueError('Expected command object')
        if (request.get('manual_mode', False) or any(request.get('stimulus_hz', [0, 0]))
                or request.get('sugar_hz', 0) or request.get('bitter_hz', 0)
                or 'gain_hz' in request or 'feeding_gain_hz' in request):
            raise ValueError('The whole-CNS session accepts physical sources, not direct drive or motor gains')
        sources = validate_sources(request.get('sources', self.last_sources or default_sources(False)))
        paused, reset_id, steps = request['paused'], request['reset'], request.get('steps', 100)
        release_block = request.get('release_block', False)
        if (type(paused) is not bool or type(reset_id) is not int or reset_id < 0
                or type(steps) is not int or not 1 <= steps <= 100 or type(release_block) is not bool):
            raise ValueError('Invalid pause, reset, steps or release-block intervention')
        if reset_id != self.reset_id:
            self.reset()
            self.reset_id = reset_id
        if sources != self.last_sources:
            apply_sources(self.sim, sources)
            self.last_sources = sources
        self.last_request = dict(paused=paused, reset=reset_id, steps=steps, sources=copy.deepcopy(sources), release_block=release_block)
        rates, irradiance, sensed = self.senses.observe(self.sim, sources)
        if not paused:
            model, data = self.sim.mj_model, self.sim.mj_data
            reuse_stages = (mujoco.__version__ == '3.9.0'
                and model.opt.integrator == mujoco.mjtIntegrator.mjINT_IMPLICITFAST
                and not (model.opt.enableflags & mujoco.mjtEnableBit.mjENBL_SLEEP)
                and model.nplugin == 0 and all(callback() is None for callback in (
                    mujoco.get_mjcb_control, mujoco.get_mjcb_sensor,
                    mujoco.get_mjcb_passive, mujoco.get_mjcb_contactfilter)))
            self.counts.zero_()
            for _ in range(steps):
                self.brain.set_sensory_rates(rates)
                self.brain.set_irradiance(self.senses.vision.ids, irradiance)
                spikes = self.brain.advance()
                self.counts += spikes
                events = spikes[0, self.motor_indices].to(dtype=torch.bool).cpu().numpy()
                self.motor_counts += events
                for substep in range(self.substeps):
                    # The newly computed neural event occurs at the interval's
                    # end. Queue it only at the final physical substep's end.
                    due = events if substep == self.substeps-1 else self.silent_events
                    self.motors.advance(self.sim.mj_data, due[self.regular_positions], release_block=release_block)
                    self.flight.advance(self.sim.mj_data, due[self.flight_positions], release_block=release_block)
                    wet = bool(sample_contact_taste(self.sim, sources)['wet_contacts'])
                    self.fluid_report = self.fluid.advance(self.sim.mj_data, self.sim.timestep,
                        inlet_pressure_pa=0.0 if wet else None)
                    self.max_fluid_residual_mm3 = max(self.max_fluid_residual_mm3,
                        abs(self.fluid_report['conservation_residual_mm3']))
                    # Work-conjugate internal fluid-pressure loads, not a
                    # locomotor/body assistance force. Never accumulate old loads.
                    self.sim.mj_data.qfrc_applied[:] = self.fluid.generalized_forces(self.sim.mj_data)
                    if substep and reuse_stages:
                        # The retained post-step forward pass already computed
                        # position/velocity stages. Only controls and applied
                        # forces changed; step2 still uses implicitfast in 3.9.
                        mujoco.mj_checkPos(model, data)
                        mujoco.mj_checkVel(model, data)
                        if data.warning.number.any():
                            raise RuntimeError('Invalid state before cached native step')
                        mujoco.mj_step2(model, data)
                    else:
                        self.sim.step()
                    mujoco.mj_forward(self.sim.mj_model, self.sim.mj_data)
                rates, irradiance, sensed = self.senses.observe(self.sim, sources)
            self.total_spikes += int(self.counts.sum().item())
            self.total_motor_spikes += int(self.counts[0, self.brain.motor_tensor_indices].sum().item())
            data = self.sim.mj_data
            if (not all(np.isfinite(x).all() for x in (data.qpos, data.qvel, data.act, data.actuator_force))
                    or np.any(data.warning.number) or not all(torch.isfinite(s).all().item() for s in self.brain.state)):
                raise RuntimeError('Nonfinite state or physics warning')
            if not math.isclose(self.sim.time, self.brain.tick * self.brain.dt, abs_tol=1e-9):
                raise RuntimeError('CNS/body clock mismatch')
        data = self.sim.mj_data
        tension = -data.actuator_force * self.sim.mj_model.actuator_gear[:, 0]
        ifm_activation = [state.activation for unit, state in zip(self.flight.units, self.flight.states)
                          if unit['kind'] == 'asynchronous']
        return dict(type='frame', time=float(self.sim.time), step=self.brain.tick,
            paused=paused, reset=reset_id, sources=sources, sensed=sensed,
            qpos=data.qpos.tolist(), qvel=data.qvel.tolist(), act=data.act.tolist(), ctrl=data.ctrl.tolist(),
            qfrc_applied=data.qfrc_applied.tolist(),
            total_spikes=self.total_spikes, total_motor_spikes=self.total_motor_spikes,
            connected_motor_spikes=int(self.motor_counts.sum()),
            active_muscle_units=int(np.count_nonzero(data.act > 0.001) + np.count_nonzero(np.array(ifm_activation) > .001)),
            muscle_tension_uN=tension.tolist(), max_muscle_tension_uN=float(np.max(tension)),
            flight_ifm_activation=ifm_activation,
            max_flight_active_force_uN=max((v['active_force_uN'] for v in self.flight.last_forces.values()), default=0),
            fluid=self.fluid_report, max_fluid_conservation_residual_mm3=self.max_fluid_residual_mm3,
            physics_contacts=int(data.ncon), physics_constraints=int(data.nefc),
            physics_arena_peak_bytes=int(data.maxuse_arena),
            thorax_position_mm=data.body('fly/c_thorax').xpos.tolist(),
            motor_counts=self.motor_counts.tolist(), release_block=release_block,
            manual_mode=False, sugar_hz=sensed['sugar_hz'], bitter_hz=sensed['bitter_hz'])


def emit(value):
    print(json.dumps(value, allow_nan=False, separators=(',', ':')), flush=True)


def main():
    mujoco.set_mju_user_warning(physics_warning)
    session = Session()
    try:
        coverage = {k:v for k,v in session.coverage.items() if k not in
            ('muscle_paths','motor_units','flight_paths','flight_motor_units','flight_contact_geometry','unresolved_motor_ids')}
        record = dict(body=session.coverage, senses=session.senses.coverage,
                      brain=session.brain.manifest, body_sha=body_signature())
        (ROOT / 'malecns-v1/body-coverage.json').write_text(json.dumps(record, indent=2) + '\n')
        emit(dict(type='ready', protocol=6, device='cuda', gpu=torch.cuda.get_device_name(0),
            neurons=len(session.brain.ids), motor_neurons=len(session.brain.motor_ids),
            connected_motor_ids=session.motor_ids,
            body_sha=body_signature(), senses_sha=session.senses.sha256, mujoco=mujoco.__version__,
            neural_code_sha=session.brain.code_sha256,
            worker_code_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            dataset=session.brain.manifest['dataset'], model=config()['model'],
            nq=session.sim.mj_model.nq, nv=session.sim.mj_model.nv, na=session.sim.mj_model.na,
            nu=session.sim.mj_model.nu, body_coverage=coverage, sensory_coverage=session.senses.coverage,
            neural_timestep_s=session.brain.dt, physics_timestep_s=session.sim.timestep,
            physics_substeps=session.substeps,
            checkpoint_schema=1,
            visual_dynamics=session.brain.visual_model))
        while line := sys.stdin.readline(4097):
            if len(line) > 4096:
                while not line.endswith('\n'):
                    line = sys.stdin.readline(4097)
                    if not line:
                        break
                emit(dict(type='error', error='Command too large'))
                continue
            try:
                request = json.loads(line)
                emit(session.checkpoint_command(request, ROOT/'individuals') if isinstance(request, dict) and 'checkpoint' in request else session.update(request))
            except (ValueError, TypeError, KeyError, OSError) as error:
                emit(dict(type='error', error=str(error)))
            except RuntimeError as error:
                emit(dict(type='error', error=str(error), fatal=True))
                raise SystemExit(1)
    finally:
        session.sim.close()


if __name__ == '__main__':
    main()

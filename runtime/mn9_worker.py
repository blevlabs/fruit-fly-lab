"""Persistent CUDA brain and MuJoCo physics, controlled through SSH stdin/stdout."""
from contextlib import redirect_stdout
import json
import math
from pathlib import Path
import sys

import pyarrow  # Eon requires libarrow to load before torch.
import numpy as np
import torch
import mujoco

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'eon-brain' / 'code'))
from benchmark import get_experiment, path_comp, path_con, path_wt
from run_pytorch import DT, MODEL_PARAMS, TorchModel, get_hash_tables, get_weights
from body import (PROBOSCIS_ACTUATOR, PROBOSCIS_JOINT, body_signature, make_body,
                  muscle_parameters, muscle_state, reset_body)
from arena import apply_sources, default_sources, sample_sources, validate_sources
from neuromuscular import NeuromuscularJunction

CHUNK_STEPS = 100  # Transport only; neural, muscle and contact updates occur every step.


class Simulation:
    def __init__(self):
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA is unavailable; no CPU fallback')
        with redirect_stdout(sys.stderr):
            lookup, _ = get_hash_tables(path_comp)
            self.arena_neurons = json.loads((ROOT / 'arena-neurons.json').read_text())
            groups = self.arena_neurons['groups']
            self.p9_ids = groups['walking']['left'] + groups['walking']['right']
            self.p9 = [lookup[n] for n in self.p9_ids]
            self.odor = [[lookup[n] for n in groups['food_odor'][side]] for side in ('left', 'right')]
            self.warmth = [[lookup[n] for n in groups['warmth'][side]] for side in ('left', 'right')]
            self.steering = [lookup[n] for side in ('left', 'right') for n in groups['steering'][side]]
            self.stimuli = json.loads((ROOT / 'stimuli.json').read_text())
            self.sugar = [lookup[n] for n in get_experiment('sugar')['neu_exc']]
            self.bitter = [lookup[n] for n in self.stimuli['bitter_ids']]
            self.mn9 = [lookup[n] for n in self.stimuli['mn9_ids']]
            weights = get_weights(path_con, path_comp, path_wt).to('cuda')
            self.brain = TorchModel(1, weights.shape[0], DT, MODEL_PARAMS,
                                   weights, exc_indices=[], device='cuda')
            self.muscle_parameters = muscle_parameters()
            if self.stimuli['mn9_ids'] != [self.muscle_parameters['neuron_id']]:
                raise RuntimeError('M9 requires the identified right MN9, without a mirrored input')
            self.sim, self.fly, self.controller = make_body()
        if not math.isclose(self.sim.timestep, DT / 1000):
            raise RuntimeError('Brain and physics timesteps differ')
        self.rates = torch.zeros(1, weights.shape[0], device='cuda')
        self.nmj = NeuromuscularJunction(self.sim.timestep, self.muscle_parameters['nmj'])
        self.muscle_id = self.sim.mj_model.actuator(PROBOSCIS_ACTUATOR).id
        if self.controller is not None or self.sim.mj_model.nu != 1:
            raise RuntimeError('The MN9 assay must contain only its muscle actuator')
        self.reset_counter = 0
        self.reset()

    def reset(self):
        torch.manual_seed(0)
        self.state = self.brain.state_init()
        reset_body(self.sim, self.fly, self.controller)
        self.nmj.reset()
        self.input_cache = None
        self.rates.zero_()
        self.p9_hz = np.zeros(2)
        self.odor_hz = np.zeros(2)
        self.warmth_hz = np.zeros(2)
        self.steering_hz = np.zeros(2)
        self.taste_hz = np.zeros(2)
        self.mn9_hz = np.zeros(len(self.mn9))
        self.mn9_spikes = np.zeros(len(self.mn9), dtype=int)
        self.total_spikes = self.active_neurons = 0

    def set_inputs(self, taste, sensed):
        inputs = list(zip((self.sugar, self.bitter), taste))
        inputs += list(zip(self.odor, sensed['odor_hz']))
        inputs += list(zip(self.warmth, sensed['warmth_hz']))
        values = tuple(float(rate) for _, rate in inputs)
        if values == self.input_cache:
            return
        self.rates.zero_()
        self.brain.neurons.refrac_steps.fill_(round(MODEL_PARAMS['tRefrac'] / DT))
        for indices, rate in inputs:
            if rate > 0:
                self.rates[0, indices] = float(rate)
                self.brain.neurons.refrac_steps[indices] = 0
        self.input_cache = values

    def update(self, request):
        if not isinstance(request, dict):
            raise ValueError('Expected a command object')
        stimulus = np.asarray(request.get('stimulus_hz', [0, 0]), dtype=float)
        manual_taste = np.asarray([request.get('sugar_hz', 0), request.get('bitter_hz', 0)], dtype=float)
        sources = validate_sources(request.get('sources', default_sources(False)))
        manual = request.get('manual_mode', False)
        arena_enabled = request.get('arena_enabled', True)
        if type(manual) is not bool or type(arena_enabled) is not bool:
            raise ValueError('Invalid experiment mode')
        paused, reset = request['paused'], request['reset']
        steps = request.get('steps', CHUNK_STEPS)
        release_block = request.get('mn9_release_block', False)
        if type(steps) is not int or not 1 <= steps <= CHUNK_STEPS or type(release_block) is not bool:
            raise ValueError('Invalid step count or transmission intervention')
        if stimulus.shape != (2,) or not np.isfinite(stimulus).all() or np.any(stimulus):
            raise ValueError('Direct walking stimulation is disabled in the muscle assay')
        if 'feeding_gain_hz' in request or 'gain_hz' in request:
            raise ValueError('Rate-to-angle and gait gains were removed; muscle parameters are in muscle9.json')
        if manual_taste.shape != (2,) or not np.isfinite(manual_taste).all() or np.any((manual_taste < 0) | (manual_taste > 500)):
            raise ValueError('Taste rates must be between 0 and 500 Hz')
        if not manual and np.any(manual_taste):
            raise ValueError('Direct stimulation requires explicit manual experiment mode')
        if type(paused) is not bool or type(reset) is not int or reset < 0:
            raise ValueError('Invalid pause/reset command')
        if reset != self.reset_counter:
            self.reset()
            self.reset_counter = reset
        apply_sources(self.sim, sources)
        sensory_sources = sources if arena_enabled else default_sources(False)
        sensed = sample_sources(self.sim, sensory_sources)
        taste = np.maximum(manual_taste, [sensed['sugar_hz'], sensed['bitter_hz']])
        if not paused:
            counts = torch.zeros_like(self.rates)
            with torch.no_grad():
                for _ in range(steps):
                    # Observe at t; emitted neural events are timestamped t+dt.
                    self.set_inputs(taste, sensed)
                    self.state = self.brain(self.rates, *self.state)
                    counts += self.state[2]
                    emitted = bool(self.state[2][0, self.mn9[0]].item())
                    self.sim.mj_data.ctrl[self.muscle_id] = self.nmj.advance(
                        emitted, release_block=release_block)
                    self.sim.step()
                    mujoco.mj_forward(self.sim.mj_model, self.sim.mj_data)
                    sensed = sample_sources(self.sim, sensory_sources)
                    taste = np.maximum(manual_taste, [sensed['sugar_hz'], sensed['bitter_hz']])
            duration = steps * DT / 1000
            measured_hz = counts[0, self.p9].cpu().numpy() / duration
            smoothing = 1 - math.exp(-duration / 0.05)
            self.p9_hz += smoothing * (measured_hz - self.p9_hz)
            self.steering_hz += smoothing * (counts[0, self.steering].cpu().numpy() / duration - self.steering_hz)
            for groups, readout in ((self.odor, self.odor_hz), (self.warmth, self.warmth_hz)):
                hz = np.array([counts[0, ids].mean().item() / duration for ids in groups])
                readout += smoothing * (hz - readout)
            taste_hz = np.array([counts[0, indices].mean().item() / duration
                                 for indices in (self.sugar, self.bitter)])
            self.taste_hz += smoothing * (taste_hz - self.taste_hz)
            mn9_counts = counts[0, self.mn9].cpu().numpy()
            self.mn9_spikes += mn9_counts.astype(int)
            self.mn9_hz += smoothing * (mn9_counts / duration - self.mn9_hz)
            self.total_spikes += int(counts.sum().item())
            self.active_neurons = int((counts > 0).sum().item())
            data = self.sim.mj_data
            if (not all(np.isfinite(x).all() for x in (data.qpos, data.qvel, data.act, data.actuator_force))
                    or not torch.isfinite(self.state[3]).all().item() or np.any(data.warning.number)):
                raise RuntimeError('Non-finite state or MuJoCo numerical warning')
            if not math.isclose(self.sim.time, self.nmj.tick * self.sim.timestep, abs_tol=1e-9):
                raise RuntimeError('Neural/NMJ/body clocks diverged')
        muscle = muscle_state(self.sim)
        muscle.update(received_spikes=self.nmj.received, delivered_spikes=self.nmj.delivered,
                      pending_spikes=len(self.nmj.pending), release_block=release_block,
                      synaptic_efficacy=self.nmj.efficacy, nmj_excitation=self.nmj.excitation)
        return dict(type='frame', time=float(self.sim.time), paused=paused,
                    qpos=self.sim.mj_data.qpos.tolist(), qvel=self.sim.mj_data.qvel.tolist(),
                    act=self.sim.mj_data.act.tolist(), ctrl=self.sim.mj_data.ctrl.tolist(),
                    step=self.nmj.tick, muscle=muscle, p9_hz=self.p9_hz.tolist(),
                    steering_hz=self.steering_hz.tolist(),
                    odor_hz=self.odor_hz.tolist(), warmth_hz=self.warmth_hz.tolist(),
                    sensed=sensed, sources=sources, manual_mode=manual,
                    sugar_hz=float(taste[0]), bitter_hz=float(taste[1]),
                    taste_hz=self.taste_hz.tolist(), mn9_hz=self.mn9_hz.tolist(),
                    mn9_spikes=self.mn9_spikes.tolist(),
                    proboscis_angle=float(self.sim.mj_data.joint(PROBOSCIS_JOINT).qpos[0]),
                    stimulus_hz=stimulus.tolist(), total_spikes=self.total_spikes,
                    active_neurons=self.active_neurons, reset=reset)


def emit(message):
    print(json.dumps(message, allow_nan=False, separators=(',', ':')), flush=True)


def main():
    session = Simulation()
    try:
        emit(dict(type='ready', protocol=5, gpu=torch.cuda.get_device_name(0),
                  device='cuda', neurons=session.rates.shape[1], p9_ids=session.p9_ids,
                  mujoco=mujoco.__version__, body_sha=body_signature(),
                  sugar_neurons=len(session.sugar), bitter_neurons=len(session.bitter),
                  excluded_bitter_ids=session.stimuli['excluded_v630_bitter_ids'],
                  mn9_ids=session.stimuli['mn9_ids'],
                  excluded_mn9_ids=session.stimuli['excluded_v630_mn9_ids'],
                  odor_neurons=sum(map(len, session.odor)), warmth_neurons=sum(map(len, session.warmth)),
                  pain=session.arena_neurons['pain'],
                  motor_model=session.muscle_parameters['model'], motor_scope='tethered right MN9-M9',
                  muscle_parameters=session.muscle_parameters,
                  coupling_dt_s=session.sim.timestep, event_timestamp='end of neural step',
                  nq=session.sim.mj_model.nq, nv=session.sim.mj_model.nv))
        while line := sys.stdin.readline(4097):
            if len(line) > 4096:
                raise ValueError('Command is too large')
            try:
                emit(session.update(json.loads(line)))
            except (ValueError, TypeError, KeyError) as error:
                emit(dict(type='error', error=str(error)))
    finally:
        session.sim.close()


if __name__ == '__main__':
    main()

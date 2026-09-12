"""Complete released neuronal graph in the existing lumped CUDA LIF model.

This module has no body, environment, action selector, gait or muscle commands.
Only annotated sensory neurons can receive environmental input through its API.
"""
import hashlib
import json
from pathlib import Path
import sys

import pyarrow  # Load before torch, as required by the installed Eon environment.
import numpy as np
import pandas as pd
import torch

from checkpoint import array_like, require_keys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'eon-brain/code'))
from run_pytorch import DT, MODEL_PARAMS, TorchModel


class VisualHybrid(TorchModel):
    """Eon dynamics plus explicitly estimated graded PR/L1/L2 compartments.

    Continuous release has spike-equivalent units solely to share the existing
    chemical-synapse integrator; it is never counted as an action potential.
    """
    def __init__(self, *args, photo_indices, lamina_indices, visual_params, **kwargs):
        super().__init__(*args, **kwargs)
        self.p = visual_params
        self.photo = torch.as_tensor(photo_indices, device=self.weights.device)
        self.graded = torch.as_tensor(np.sort(np.r_[photo_indices, lamina_indices]), device=self.weights.device)
        self.dt_s = DT / 1000
        self.light = torch.zeros(1, len(photo_indices), device=self.weights.device)
        self.recurrent_weights = None
        if self.weights.is_cuda:
            # Native sparse bmm honors PyTorch's deterministic mode; CUDA CSR
            # matmul did not preserve bitwise sums for continuous release.
            torch.use_deterministic_algorithms(True)
            self.recurrent_weights = self.weights.to_sparse_coo().unsqueeze(0).coalesce()

    def state_init(self):
        state = super().state_init()
        state[3][:, self.photo] = self.p['photoreceptor_rest_mV']
        self.light.zero_()
        return state

    def forward(self, rates, conductance, delay, output, v, refrac, generator=None):
        previous_spikes = output.clone()
        previous_spikes[:, self.graded] = 0
        refrac = torch.where(previous_spikes > 0, torch.zeros_like(refrac), refrac + 1)
        mask = (refrac >= self.neurons.refrac_steps.unsqueeze(0)).float()
        mask[:, self.graded] = 1
        weighted = (torch.bmm(self.recurrent_weights, output.unsqueeze(2)).squeeze(2)
                    if self.recurrent_weights is not None else torch.matmul(output, self.weights.transpose(0, 1)))
        recurrent = self.scale * weighted
        conductance_new, delay = self.neurons.synapse(recurrent, conductance, delay, mask)
        stimulus = self.scale * self.poisson(rates, generator=generator)
        spikes, v_new = self.neurons.neuron(conductance, stimulus, v)
        p = self.p
        # Graded cells have no threshold/reset or refractory period. Recurrent
        # feedback remains in the same graph, including feedback into receptors.
        graded_v = v[:, self.graded] + (1 - np.exp(-self.dt_s / p['graded_tau_s'])) * (
            conductance[:, self.graded] - (v[:, self.graded] - self.neurons.neuron.v_rest))
        v_new[:, self.graded] = graded_v
        drive = p['photo_current_max_mV'] * self.light / (self.light + p['half_saturation_radiance'])
        v_new[:, self.photo] = v[:, self.photo] + (1 - np.exp(-self.dt_s / p['graded_tau_s'])) * (
            conductance[:, self.photo] + drive - (v[:, self.photo] - p['photoreceptor_rest_mV']))
        # Coarse finite-voltage compartment bounds, not calibrated ionic currents.
        v_new[:, self.graded] = v_new[:, self.graded].clamp(-90, 20)
        spikes[:, self.graded] = 0
        conductance_new = conductance_new * (1 - spikes)
        output = spikes.clone()
        output[:, self.graded] = self.dt_s * p['release_equivalent_max_hz'] * torch.sigmoid(
            (v_new[:, self.graded] - p['release_midpoint_mV']) / p['release_slope_mV'])
        return conductance_new, delay, output, v_new, refrac


class CNS:
    def __init__(self, directory=None):
        if not torch.cuda.is_available():
            raise RuntimeError('The whole-CNS worker requires CUDA')
        directory = ROOT / 'malecns-v1' if directory is None else Path(directory)
        self.manifest = json.loads((directory / 'manifest.json').read_text())
        self.code_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        for name, expected in self.manifest['artifact_sha256'].items():
            with (directory / name).open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != expected:
                raise ValueError(f'MaleCNS artifact hash mismatch: {name}')
        self.neurons = pd.read_feather(directory / 'neurons.feather')
        with np.load(directory / 'connectome.npz', allow_pickle=False) as graph:
            self.ids = graph['neuron_ids']
            indptr, indices = graph['indptr'], graph['indices']
            values = graph['synapse_count'].astype(np.float32)
            signs = graph['fast_current_sign']
            if (not np.array_equal(self.ids, self.neurons.bodyId.to_numpy())
                    or len(indptr) != len(self.ids) + 1 or indptr[-1] != len(values)
                    or np.any(indices < 0) or np.any(indices >= len(self.ids))
                    or np.any(np.diff(indptr) < 0) or not np.isfinite(values).all()
                    or np.any(values <= 0)):
                raise ValueError('Invalid MaleCNS graph layout')
            # All structural connections are retained in the artifact. Unknown
            # transmitter signs remain zero/unresolved, never invented as reward or drive.
            values *= signs[indices]
            weights = torch.sparse_csr_tensor(
                torch.as_tensor(indptr.astype(np.int64), device='cuda'),
                torch.as_tensor(indices.astype(np.int64), device='cuda'),
                torch.as_tensor(values, device='cuda'), size=(len(self.ids), len(self.ids)))
        self.lookup = {int(body_id): i for i, body_id in enumerate(self.ids)}
        superclass = self.neurons.superclass.fillna('')
        sensory = superclass.str.contains('sensory').to_numpy()
        self.sensory_ids = set(map(int, self.ids[sensory]))
        self.motor_indices = np.flatnonzero(superclass.isin(['vnc_motor', 'cb_motor']).to_numpy())
        self.motor_ids = self.ids[self.motor_indices]
        self.motor_tensor_indices = torch.as_tensor(self.motor_indices, device='cuda')
        visual_params = json.loads((ROOT / 'cns-model.json').read_text())['vision']
        photo = self.neurons['class'].eq('visual').to_numpy() & sensory
        photo_indices = np.flatnonzero(photo)
        self.photo_ids = set(map(int, self.ids[photo]))
        self.photo_lookup = {int(self.ids[i]): j for j, i in enumerate(photo_indices)}
        lamina_indices = np.flatnonzero(self.neurons['type'].isin(visual_params['graded_lamina_types']).to_numpy())
        self.model = VisualHybrid(1, len(self.ids), DT, MODEL_PARAMS, weights,
            exc_indices=np.flatnonzero(sensory).tolist(), device='cuda',
            photo_indices=photo_indices, lamina_indices=lamina_indices, visual_params=visual_params)
        self.visual_model = dict(photoreceptors=len(photo_indices), graded_lamina_cells=len(lamina_indices),
                                parameters=visual_params, other_cells='Lumped LIF approximation')
        self.rates = torch.zeros(1, len(self.ids), device='cuda')
        self.generator = torch.Generator(device='cuda')
        self.dt = DT / 1000
        self.reset()

    def reset(self, seed=0):
        if type(seed) is not int or seed < 0:
            raise ValueError('Seed must be a nonnegative integer')
        self.generator.manual_seed(seed)
        self.state = self.model.state_init()
        self.rates.zero_()
        self.tick = 0
        self.input_cache = None
        self.light_cache = None

    def set_sensory_rates(self, by_id):
        """Input rates in Hz, addressed only to actual annotated sensory IDs."""
        if not isinstance(by_id, dict):
            raise ValueError('Expected a sensory-ID to rate dictionary')
        items = tuple(sorted(by_id.items()))
        if items == self.input_cache:
            return
        if any(type(body_id) is not int or body_id not in self.sensory_ids
               or body_id in self.photo_ids for body_id, _ in items):
            raise ValueError('Environmental input is restricted to annotated sensory neurons')
        rates = np.array([rate for _, rate in items], dtype=np.float32)
        if not np.isfinite(rates).all() or np.any(rates < 0) or np.any(rates > 500):
            raise ValueError('Sensory rates must be finite and within 0–500 Hz')
        self.rates.zero_()
        if items:
            indices = torch.tensor([self.lookup[body_id] for body_id, _ in items], device='cuda')
            self.rates[0, indices] = torch.as_tensor(rates, device='cuda')
        self.input_cache = items

    def set_irradiance(self, ids, values):
        """Relative broadband irradiance for registered photoreceptors only."""
        ids = tuple(ids)
        values = np.asarray(values, dtype=np.float32)
        if self.light_cache is not None and ids == self.light_cache[0] and np.array_equal(values, self.light_cache[1]):
            return
        if (values.shape != (len(ids),) or len(set(ids)) != len(ids)
                or not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1000)
                or any(type(i) is not int or i not in self.photo_ids for i in ids)):
            raise ValueError('Expected unique photoreceptor IDs and finite relative irradiance in [0, 1000]')
        self.model.light.zero_()
        if ids:
            index = torch.as_tensor([self.photo_lookup[i] for i in ids], device='cuda')
            self.model.light[0, index] = torch.as_tensor(values, device='cuda')
        self.light_cache = ids, values.copy()

    def advance(self):
        with torch.no_grad():
            self.state = self.model(self.rates, *self.state, generator=self.generator)
        self.tick += 1
        spikes = self.state[2].clone()
        spikes[:, self.model.graded] = 0
        return spikes

    def motor_spikes(self):
        return self.state[2][0, self.motor_tensor_indices].to(dtype=torch.bool).cpu().numpy()

    def export_state(self):
        return dict(state=tuple(v.detach().cpu().numpy().copy() for v in self.state),
            rates=self.rates.cpu().numpy().copy(), light=self.model.light.cpu().numpy().copy(),
            generator=self.generator.get_state().numpy().copy(), tick=self.tick,
            input_cache=self.input_cache,
            light_cache=None if self.light_cache is None else (self.light_cache[0], self.light_cache[1].copy()))

    def validate_state(self, state):
        require_keys(state, ('state', 'rates', 'light', 'generator', 'tick', 'input_cache', 'light_cache'))
        if type(state['tick']) is not int or state['tick'] < 0 or len(state['state']) != len(self.state):
            raise ValueError('Invalid neural checkpoint clock or state count')
        for incoming, current in zip(state['state'], self.state):
            array_like(incoming, current.cpu().numpy())
        for name, current in [('rates', self.rates), ('light', self.model.light),
                              ('generator', self.generator.get_state())]:
            array_like(state[name], current.cpu().numpy())
        if np.any(state['rates'] < 0) or np.any(state['rates'] > 500) or np.any(state['light'] < 0) or np.any(state['light'] > 1000):
            raise ValueError('Invalid neural checkpoint inputs')
        # Caches determine whether input arrays are updated. Validate both together.
        expected = np.zeros_like(state['rates'])
        cache = state['input_cache']
        if cache is not None:
            if (not isinstance(cache, tuple) or len(dict(cache)) != len(cache)
                    or any(type(i) is not int or i not in self.sensory_ids or i in self.photo_ids for i, _ in cache)):
                raise ValueError('Invalid sensory checkpoint cache')
            for body_id, rate in cache:
                expected[0, self.lookup[body_id]] = rate
        if not np.array_equal(expected, state['rates']):
            raise ValueError('Checkpoint sensory cache differs from input')
        expected = np.zeros_like(state['light'])
        cache = state['light_cache']
        if cache is not None:
            ids, values = cache
            if (not isinstance(ids, tuple) or len(set(ids)) != len(ids) or values.shape != (len(ids),)
                    or any(type(i) is not int or i not in self.photo_ids for i in ids)):
                raise ValueError('Invalid optical checkpoint cache')
            for body_id, value in zip(ids, values):
                expected[0, self.photo_lookup[body_id]] = value
        if not np.array_equal(expected, state['light']):
            raise ValueError('Checkpoint optical cache differs from input')
        torch.Generator(device='cuda').set_state(torch.from_numpy(state['generator']))

    def import_state(self, state):
        self.validate_state(state)
        self.state = tuple(torch.as_tensor(v.copy(), device='cuda') for v in state['state'])
        self.rates.copy_(torch.from_numpy(state['rates']))
        self.model.light.copy_(torch.from_numpy(state['light']))
        self.generator.set_state(torch.from_numpy(state['generator']))
        self.tick = state['tick']
        self.input_cache = state['input_cache']
        self.light_cache = None if state['light_cache'] is None else (state['light_cache'][0], state['light_cache'][1].copy())


def check():
    cns = CNS()
    counts = torch.zeros_like(cns.rates)
    for _ in range(100):
        counts += cns.advance()
    assert counts[:, cns.model.graded].sum().item() == 0
    try:
        cns.set_sensory_rates({int(cns.motor_ids[0]): 100})
    except ValueError:
        pass
    else:
        raise AssertionError('Motor neuron accepted environmental input')
    # A declared artificial sensory-bus test, not natural odor or a behavioral trial.
    olfactory = cns.neurons.loc[cns.neurons['class'].eq('olfactory'), 'bodyId'].tolist()
    traces = []
    for _ in range(2):
        cns.reset(seed=0)
        cns.set_sensory_rates({int(i): 10 for i in olfactory})
        counts.zero_()
        for _ in range(1000):
            counts += cns.advance()
        assert all(torch.isfinite(state).all().item() for state in cns.state)
        assert counts.sum().item() > 0
        traces.append((counts.clone(), tuple(state.clone() for state in cns.state)))
    assert torch.equal(traces[0][0], traces[1][0])
    assert all(torch.equal(a, b) for a, b in zip(traces[0][1], traces[1][1]))
    receipt = dict(status='PASS: whole-neuronal-graph CUDA integration, not behavioral validation',
        dataset=cns.manifest['dataset'], neurons=len(cns.ids),
        structural_edges=cns.manifest['neuronal_edge_rows'],
        unresolved_transmitter_edges=cns.manifest['unresolved_outgoing_edge_rows'],
        dt_s=cns.dt, motor_neurons=len(cns.motor_ids), sensory_input_neurons=len(olfactory),
        artificial_test_rate_hz=10, artificial_test_seconds=cns.tick * cns.dt,
        artificial_test_spikes=int(counts.sum().item()),
        motor_spikes=int(counts[0, cns.motor_tensor_indices].sum().item()),
        reset_reproducible=True, direct_motor_input_rejected=True,
        visual_dynamics=cns.visual_model,
        neural_code_sha256=cns.code_sha256,
        model_parameters=MODEL_PARAMS, graph_artifacts=cns.manifest['artifact_sha256'],
        limitations=cns.manifest['limitations'], body_connected=False)
    (ROOT / 'malecns-v1/cuda-check.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    check()

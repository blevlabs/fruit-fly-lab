"""Finite published-notebook BSG source-law study, isolated from the fly runtime.

Lazar & Yeh 2020 S1 Notebook, doi:10.1371/journal.pcbi.1007751; original
OlfTrans functions, copyright 2021 Tingkai Liu, BSD-3-Clause. Source/license
evidence and the private-RNG substitution live in the existing BSG source audit.
This is neither the printed appendix SDE nor a reproduction of Figure A2.
"""
import argparse
import copy
import hashlib
import json
import platform
import runpy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/research/m3/bsg-source-audit'
OUTPUT = ROOT / 'runs/bsg-source-reference'
source = runpy.run_path(str(Path(__file__).with_name('bsg_source_audit.py')))
_, _, SourceBSG = source['source_classes'](inspect_locals=False)
CURRENTS_PA = np.array([0., 5., 20., 50., 100.])
REPLICAS, DURATION_S, BURN_IN_S = 24, 3., 1.
SEED, TIMESTEPS_S = 20260912, (3e-5, 1.5e-5)
BOUNDED = ('v', 'n', 'm', 'h', 'a', 'b')


class BSG:
    """Original vectorized drift/post expressions with notebook update semantics."""

    def __init__(self, count, dt_s, seed):
        if type(count) is not int or count <= 0 or not np.isfinite(dt_s) or dt_s <= 0:
            raise ValueError('A positive replica count and finite positive seconds timestep are required')
        self.dt_s = float(dt_s)
        self.model = SourceBSG(num=count, sigma=.0019 / np.sqrt(dt_s))
        self.model.rng = np.random.Generator(np.random.PCG64(seed))
        self.steps = 0
        self.clips = {k: np.zeros(count, dtype=np.int64) for k in BOUNDED}

    def step(self, current_pA):
        current = np.asarray(current_pA, dtype=float)
        if current.shape != (self.model.num,) or not np.isfinite(current).all():
            raise ValueError('Expected one finite source-label current per replica')
        derivatives = self.model.gradient(stimulus=current)
        for key, derivative in derivatives.items():
            value = self.model.states[key] + self.dt_s * self.model.Time_Scale * derivative
            low, high = self.model.bounds[key]
            if key in self.clips:
                self.clips[key] += (value < low) | (value > high)
            # Fresh arrays retain old v1/v2 samples while voltage advances. The
            # source CPU in-place update would alias those history arrays.
            self.model.states[key] = np.clip(value, low, high)
        self.model.states.update(self.model.non_gradient())
        self.steps += 1
        if not all(np.isfinite(a).all() for a in self.model.states.values()):
            raise FloatingPointError(f'Nonfinite source state at step {self.steps}')
        return self.model.spike

    def snapshot(self):
        return dict(dt_s=self.dt_s, steps=self.steps,
                    states={k: dict(dtype=str(a.dtype), values=a.tolist()) for k, a in self.model.states.items()},
                    params={k: a.tolist() for k, a in self.model.params.items()},
                    rng=copy.deepcopy(self.model.rng.bit_generator.state),
                    clips={k: a.tolist() for k, a in self.clips.items()})

    @classmethod
    def restore(cls, snapshot):
        restored = cls(len(snapshot['states']['v']['values']), snapshot['dt_s'], 0)
        assert snapshot['params'] == {k: a.tolist() for k, a in restored.model.params.items()}
        assert set(snapshot['states']) == set(restored.model.states)
        restored.model.states = {k: np.array(v['values'], dtype=v['dtype']) for k, v in snapshot['states'].items()}
        restored.model.rng.bit_generator.state = snapshot['rng']
        restored.steps = snapshot['steps']
        restored.clips = {k: np.array(v, dtype=np.int64) for k, v in snapshot['clips'].items()}
        return restored


def source_step_check():
    """Compare the reused vector step against the audited scalar notebook examples."""
    receipt = json.loads((AUDIT / 'source-check.json').read_text())
    # The historical receipt fingerprints its original audit snapshot. The
    # relocated loader is separately fingerprinted in newly generated results.
    assert receipt['check_sha256'] == hashlib.sha256((AUDIT / 'check_source.py').read_bytes()).hexdigest()
    expected = receipt['source_transition_examples']
    reference = BSG(len(expected), 3e-5, 0)
    reference.model.states['v'] = np.array([r['initial_voltage_mV'] for r in expected])
    innovations = iter([np.full(len(expected), z) for z in expected[0]['prescribed_standard_normal_innovations']])
    reference.model.rng = SimpleNamespace(standard_normal=lambda count: next(innovations))
    old_v2 = reference.model.v2.copy()
    reference.step(np.full(len(expected), 10.))
    assert np.array_equal(reference.model.v1, old_v2)
    for i, row in enumerate(expected):
        for key, value in row['clipped_gates'].items():
            assert np.isclose(reference.model.states[key][i], value, rtol=1e-13, atol=1e-14)
        assert np.isclose(reference.model.v[i], row['post_voltage_mV'], rtol=1e-13, atol=1e-14)
        assert reference.model.spike[i] == row['spike']


def run_assay(dt_s, seed, output, verify_continuation=False):
    current = np.repeat(CURRENTS_PA, REPLICAS)
    model = BSG(len(current), dt_s, seed)
    total = round(DURATION_S / dt_s)
    burn = int(np.ceil(BURN_IN_S / dt_s))
    midpoint = total // 2
    assert abs(total * dt_s - DURATION_S) < 1e-12
    assert 0 <= burn * dt_s - BURN_IN_S < dt_s
    counts = np.zeros(len(current), dtype=np.int64)
    tail = hashlib.sha256()
    # Streaming counts/hash keep the finite assay small; no full voltage movie.
    for step in range(1, total + 1):
        spikes = model.step(current)
        # Source detector refers to the previous sample: peak time=(step-1)*dt.
        # Thus steps>burn count detected peaks in [1s,3s), with a 2s denominator.
        if step > burn:
            counts += spikes.astype(np.int64)
        if step > midpoint:
            tail.update(spikes.astype(np.uint8).tobytes())
        if verify_continuation and step == midpoint:
            checkpoint = dict(model=model.snapshot(), observation_counts=counts.tolist(),
                              current_pA=current.tolist(), burn_steps=burn, total_steps=total)
            (output / 'continuation-checkpoint.json').write_text(json.dumps(checkpoint, allow_nan=False) + '\n')
    final = model.snapshot()
    continuation = 'NOT_REQUESTED for this resolution'
    if verify_continuation:
        checkpoint = json.loads((output / 'continuation-checkpoint.json').read_text())
        resumed = BSG.restore(checkpoint['model'])
        resumed_counts = np.array(checkpoint['observation_counts'], dtype=np.int64)
        resumed_hash = hashlib.sha256()
        for _ in range(resumed.steps, total):
            spikes = resumed.step(np.array(checkpoint['current_pA']))
            if resumed.steps > checkpoint['burn_steps']:
                resumed_counts += spikes.astype(np.int64)
            resumed_hash.update(spikes.astype(np.uint8).tobytes())
        assert resumed.snapshot() == final
        assert np.array_equal(resumed_counts, counts)
        assert resumed_hash.hexdigest() == tail.hexdigest()
        continuation = dict(status='PASS exact JSON-restored source states, RNG, clipping counts and observation counts',
                            checkpoint_time_s=midpoint * dt_s, tail_spike_sha256=tail.hexdigest(),
                            final_source_state_keys=list(final['states']), rng='PCG64 full bit-generator state')
    rates = counts.reshape(-1, REPLICAS) / (DURATION_S - BURN_IN_S)
    rows = []
    critical = student_t.ppf(.975, REPLICAS - 1)
    for i, current_value in enumerate(CURRENTS_PA):
        samples = rates[i]
        mean, sd = float(samples.mean()), float(samples.std(ddof=1))
        half = float(critical * sd / np.sqrt(REPLICAS))
        rows.append(dict(current_source_label_pA=float(current_value),
                         replica_spike_counts=counts.reshape(-1, REPLICAS)[i].tolist(),
                         replica_rates_Hz=samples.tolist(), mean_Hz=mean, sd_Hz=sd,
                         sem_Hz=sd / np.sqrt(REPLICAS), mean_95pct_t_interval_Hz=[mean - half, mean + half],
                         clipping_fraction_all_steps={k: float(a.reshape(-1, REPLICAS)[i].sum() / (total * REPLICAS))
                                                      for k, a in model.clips.items()}))
    label = f'{round(dt_s * 1e6):02d}us'
    (output / f'{label}-final-state.json').write_text(json.dumps(final, allow_nan=False) + '\n')
    result = dict(dt_s=dt_s, source_sigma_parameter=float(.0019 / np.sqrt(dt_s)),
                  diffusion_per_sqrt_s=1.9, duration_s=DURATION_S, burn_in_s=BURN_IN_S,
                  observation_window_s=[BURN_IN_S, DURATION_S], observations='local-maximum peak timestamps in [1,3) s',
                  first_admitted_peak_sample_s=burn * dt_s,
                  replicas_per_current=REPLICAS, seed=dict(entropy=seed.entropy, spawn_key=list(seed.spawn_key),
                                                         generator='numpy.random.PCG64'),
                  random_draw_order='five source gate draws (n,m,h,a,b), each vector ordered current then replica; distinct draws per path',
                  rows=rows, continuation=continuation, all_states_finite=True,
                  tail_spike_sha256=tail.hexdigest())
    (output / f'{label}-assay.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    source_step_check()
    seeds = np.random.SeedSequence(SEED).spawn(2)
    results = []
    for i, (dt, seed) in enumerate(zip(TIMESTEPS_S, seeds)):
        result = run_assay(dt, seed, output, verify_continuation=i == 0)
        results.append(result)
        print(json.dumps(dict(dt_s=dt, rates_Hz=[r['mean_Hz'] for r in result['rows']],
                              continuation=result['continuation'])), flush=True)
    differences = []
    for coarse, fine in zip(results[0]['rows'], results[1]['rows']):
        var_a, var_b = coarse['sd_Hz'] ** 2 / REPLICAS, fine['sd_Hz'] ** 2 / REPLICAS
        se = np.sqrt(var_a + var_b)
        df = (var_a + var_b) ** 2 / ((var_a ** 2 + var_b ** 2) / (REPLICAS - 1)) if se else None
        half = student_t.ppf(.975, df) * se if se else 0.
        delta = fine['mean_Hz'] - coarse['mean_Hz']
        differences.append(dict(current_source_label_pA=coarse['current_source_label_pA'],
                                mean_fine_minus_coarse_Hz=delta, independent_replica_standard_error_Hz=float(se),
                                unadjusted_95pct_Welch_interval_Hz=[float(delta - half), float(delta + half)],
                                interval_excludes_zero=bool(abs(delta) > half),
                                interpretation='descriptive timestep sensitivity; no biological or equivalence margin asserted'))
    receipt = dict(
        claim='Finite current-to-spike study of the published notebook transition law using a new reproducible RNG',
        source_transition='PASS against audited scalar notebook examples',
        exact_continuation=results[0]['continuation'],
        original_CUDA_trajectory='NOT_REPRODUCED: new PCG64 streams, unrecorded original GPU-clock seed',
        paper_FigA2='NOT_REPRODUCED: printed equation/configuration discrepancy retained',
        biological_validation='NOT_RUN', heldout_validation='NOT_RUN', runtime_integration='NONE', M3_full_gate='OPEN',
        fixed_protocol=dict(currents_source_label_pA=CURRENTS_PA.tolist(), replicas=REPLICAS,
                            duration_s=DURATION_S, burn_in_s=BURN_IN_S, dt_s=list(TIMESTEPS_S),
                            root_seed=SEED, fitting=False, diffusion_per_sqrt_s=1.9,
                            fixed_source_parameters=SourceBSG.Params,
                            sigma_default_note='Default sigma=2.05 is replaced by the explicit published notebook .0019/sqrt(dt)',
                            initial_state=SourceBSG.States, clipping='exact source gates[0,1], voltage[-80,80], then source post',
                            source_current_units='pA labels from source; no native capacitance/area calibration inferred'),
        sampling_uncertainty='Independent simulated replicas, not biological replicates. Two-second rate SD/SEM and descriptive t intervals; Welch differences are unadjusted. Identical replica counts would give degenerate intervals, not proof of a noiseless true rate.',
        timestep_comparison=differences,
        smaller_timestep='One refinement only; rate agreement is not proof of trajectory or distribution convergence',
        state_semantics='Fresh arrays preserve notebook/CUDA voltage history; source gradient and post expressions retained, five Gaussian calls use private RNG',
        environment=dict(python=platform.python_version(), numpy=np.__version__),
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), Path(__file__).with_name('bsg_source_audit.py'), AUDIT / 'source-check.json',
                                 ROOT / 'data/research/m3/olftrans-reference/sources/OlfTrans-cpu-model.py')},
        outputs_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.json')
                        if p.name != 'reference-check.json'})
    (output / 'reference-check.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status='finite source-law assay complete', timestep_comparison=differences,
                          biological_validation='NOT_RUN', M3_full_gate='OPEN')), flush=True)


def composed_odor(output):
    """Saved paper-OTP currents drive notebook-BSG; retain raw spike sample indices."""
    source_step_check()
    otp_dir = ROOT / 'data/research/m3/olftrans-reference'
    otp_receipt = json.loads((otp_dir / 'reference-check.json').read_text())
    trace_file = otp_dir / 'waveforms.npz'
    assert hashlib.sha256(trace_file.read_bytes()).hexdigest() == otp_receipt['trace_sha256']
    dt_s = 15e-6
    seed = np.random.SeedSequence(SEED, spawn_key=(2,))
    labels = [f'{shape}/{i}' for shape in ('step', 'ramp', 'parabola') for i in range(3)]
    with np.load(trace_file) as saved:
        source_time = saved['stimulus_time_s']
        currents = np.concatenate([saved[f'{shape}_model_current_pA'] for shape in ('step', 'ramp', 'parabola')])
    assert source_time[0] == 0 and currents.shape == (9, len(source_time))
    assert np.isfinite(currents).all() and currents.min() >= -1e-8 and currents.max() < 62.13
    total = int(np.floor(source_time[-1] / dt_s))
    input_time = np.arange(total) * dt_s
    assert input_time[-1] < total * dt_s <= source_time[-1]
    input_current = np.array([np.interp(input_time, source_time, curve) for curve in currents])
    model = BSG(9 * REPLICAS, dt_s, seed)
    neuron_indices, peak_indices = [], []
    for peak_index, values in enumerate(input_current.T):
        spikes = model.step(np.repeat(values, REPLICAS))
        active = np.flatnonzero(spikes)
        neuron_indices.extend(active.tolist())
        peak_indices.extend([peak_index] * len(active))
    event_neuron = np.array(neuron_indices, dtype=np.uint16)
    event_peak_sample = np.array(peak_indices, dtype=np.int32)
    counts = np.bincount(event_neuron.astype(int), minlength=model.model.num).reshape(9, REPLICAS)
    duration = total * dt_s
    rates = counts / duration
    assert counts.sum() == len(event_neuron) and len(event_neuron) == len(event_peak_sample)
    assert len(event_peak_sample) == 0 or (event_peak_sample.min() >= 0 and event_peak_sample.max() < total)
    output.mkdir(parents=True, exist_ok=True)
    events = output / 'spikes.npz'
    np.savez_compressed(events, event_neuron_index=event_neuron, event_peak_sample_index=event_peak_sample,
                        neuron_waveform_index=np.repeat(np.arange(9), REPLICAS),
                        neuron_replica_index=np.tile(np.arange(REPLICAS), 9),
                        waveform_labels=np.array(labels), counts=counts, rate_Hz=rates,
                        dt_s=np.array(dt_s), simulated_duration_s=np.array(duration))
    with np.load(events) as readback:
        assert np.array_equal(np.bincount(readback['event_neuron_index'].astype(int), minlength=model.model.num)
                              .reshape(9, REPLICAS), counts)
    (output / 'final-state.json').write_text(json.dumps(model.snapshot(), allow_nan=False) + '\n')
    critical = student_t.ppf(.975, REPLICAS - 1)
    rows = []
    for i, label in enumerate(labels):
        mean, sd = float(rates[i].mean()), float(rates[i].std(ddof=1))
        half = float(critical * sd / np.sqrt(REPLICAS))
        rows.append(dict(waveform=label, replica_spike_counts=counts[i].tolist(),
                         whole_trace_mean_Hz=mean, sd_Hz=sd, sem_Hz=sd / np.sqrt(REPLICAS),
                         mean_95pct_t_interval_Hz=[mean - half, mean + half],
                         saved_current_min_pA=float(currents[i].min()), saved_current_peak_pA=float(currents[i].max()),
                         clipping_fraction={k: float(v.reshape(9, REPLICAS)[i].sum() / (total * REPLICAS))
                                            for k, v in model.clips.items()}))
    receipt = dict(
        claim='Composed saved paper-OTP plus executable notebook-BSG source-law reference; not a figure reproduction',
        implementation='PASS source correspondence, finite states, declared domain/grid and raw-event/count readback',
        biological_validation='NOT_RUN: measured PSTH timestamp/window convention unresolved',
        heldout_validation='NOT_RUN', paper_FigA2_or_Fig4='NOT_REPRODUCED', runtime_integration='NONE', M3_full_gate='OPEN',
        protocol=dict(receptor='Or59b', odor='acetone', source_waveforms='all nine /elife15 step/ramp/parabola curves in original order',
                      source_time_units='s', current_units='source-label pA', replicas_per_waveform=REPLICAS,
                      dt_s=dt_s, steps=total, original_source_end_s=float(source_time[-1]), simulated_end_s=duration,
                      omitted_terminal_interval_s=float(source_time[-1] - duration),
                      interpolation='piecewise linear saved current; sample at left edge t=k*dt for each full BSG step',
                      endpoint='floor(source_end/dt) full steps; no extrapolation or fractional final step',
                      peak_timestamp='event_peak_sample_index*dt; detection is one timestep later',
                      spike_output='raw events, exact neuron→waveform/replica mapping and per-replica counts; no PSTH alignment selected',
                      initial_state=SourceBSG.States, warmup_s=0, burn_in_s=0,
                      root_seed=SEED, spawn_key=[2], generator='numpy.random.PCG64',
                      normal_draw_order='n,m,h,a,b vectors; waveform-major then replica-major',
                      source_sigma_parameter=float(.0019 / np.sqrt(dt_s)), diffusion_per_sqrt_s=1.9,
                      fitting=False, extra_time_shift_s=0, current_clipping_or_rescaling=False,
                      source_preparation=otp_receipt['protocol']['preparation']),
        current_domain=dict(finite=True, minimum_pA=float(currents.min()), maximum_pA=float(currents.max()),
                            tiny_negative_note='Saved OTP roundoff down to the recorded minimum is retained; no current clipping',
                            accepted_numerical_lower_bound_pA=-1e-8),
        all_states_finite=True, total_spike_events=int(counts.sum()), rows=rows,
        sampling_uncertainty='Descriptive Student-t intervals across 24 independent simulated paths; not biological replicate uncertainty',
        immediate_external_datum='Author definition of the 100 ms PSTH window attached to each /elife15/*/psth/x timestamp, including any additional spike/stimulus offset and trial averaging rule',
        biological_comparison_limit='No unique aligned error score without that convention; trial-level spikes or measurement uncertainty and prespecified acceptance margins are additionally needed for statistical physiological validation',
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), trace_file, otp_dir / 'reference-check.json',
                                 Path(__file__).with_name('bsg_source_audit.py'), AUDIT / 'source-check.json')},
        outputs_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (events, output / 'final-state.json')})
    (output / 'reference-check.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(implementation=receipt['implementation'], whole_trace_rates_Hz=[r['whole_trace_mean_Hz'] for r in rows],
                          events=int(counts.sum()), biological_validation=receipt['biological_validation'], M3_full_gate='OPEN')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--composed-odor', action='store_true', help='Drive BSG from the nine saved fine OTP currents')
    args = parser.parse_args()
    if args.composed_odor:
        composed_odor(args.output or ROOT / 'runs/composed-odor-reference')
    else:
        main(args.output or OUTPUT)

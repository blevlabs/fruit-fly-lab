"""Stimulate sugar-sensing neurons in the full FlyWire v783 Brian2 model."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import brian2 as b2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runtime/shiu-brain'
sys.path.insert(0, str(SOURCE))
import model

# Sugar-sensing neurons used in the authors' example.ipynb.
SUGAR = [720575940624963786, 720575940630233916, 720575940637568838,
         720575940638202345, 720575940617000768, 720575940630797113,
         720575940632889389, 720575940621754367, 720575940621502051,
         720575940640649691, 720575940639332736, 720575940616885538,
         720575940639198653, 720575940620900446, 720575940617937543,
         720575940632425919, 720575940633143833, 720575940612670570,
         720575940628853239, 720575940629176663, 720575940611875570]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration-ms', type=float, default=100)
    parser.add_argument('--rate-hz', type=float, default=150)
    args = parser.parse_args()
    if not np.isfinite([args.duration_ms, args.rate_hz]).all() or min(args.duration_ms, args.rate_hz) <= 0:
        parser.error('duration and rate must be finite and positive')
    output = ROOT / 'runs/brain'
    output.mkdir(parents=True, exist_ok=True)
    cache = ROOT / '.cache' / 'brian2'
    cache.mkdir(parents=True, exist_ok=True)
    b2.prefs.codegen.target = 'cython'
    b2.prefs.codegen.runtime.cython.cache_dir = str(cache)
    b2.seed(0)
    params = dict(model.default_params, r_poi=args.rate_hz * b2.Hz)
    ids = pd.read_csv(SOURCE / 'Completeness_783.csv', index_col=0).index
    excited = ids.get_indexer(SUGAR)
    missing = [neuron for neuron, index in zip(SUGAR, excited) if index < 0]
    if missing:
        print(f'v630 example IDs absent from v783 (excluded, not remapped): {missing}', flush=True)
    excited = excited[excited >= 0]
    assert len(excited) > 0, 'No stimulus neuron IDs found in v783'
    started = perf_counter()
    print('Loading full FlyWire v783 connectivity...', flush=True)
    neurons, synapses, spikes = model.create_model(
        SOURCE / 'Completeness_783.csv', SOURCE / 'Connectivity_783.parquet', params)
    poisson, neurons = model.poi(neurons, excited, [], params)
    network = b2.Network(neurons, synapses, spikes, *poisson)
    print(f'Running {len(neurons):,} neurons and {len(synapses):,} connections...', flush=True)
    network.run(args.duration_ms * b2.ms)
    assert np.isfinite(neurons.v[:]).all(), 'Non-finite membrane potential'
    assert len(spikes.i) > 0, 'No spikes observed; try a longer trial'
    results = pd.DataFrame({'time_ms': spikes.t[:] / b2.ms,
                           'neuron_index': spikes.i[:], 'flywire_id': ids[spikes.i[:]]})
    results.to_csv(output / 'brain-spikes.csv', index=False)
    fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
    ax.scatter(results.time_ms, results.neuron_index, s=2, color='#207b81')
    ax.set(xlabel='Time (ms)', ylabel='Neuron index (FlyWire v783)',
           title='Full-connectome LIF model: sugar-sensory stimulation')
    fig.savefig(output / 'brain-spikes.png', dpi=160)
    plt.close(fig)
    summary = dict(neurons=len(neurons), connections=len(synapses),
                   stimulated_neurons=len(excited), duration_ms=args.duration_ms,
                   stimulus_hz=args.rate_hz, spikes=len(results),
                   active_neurons=results.neuron_index.nunique(),
                   wall_seconds=round(perf_counter() - started, 2),
                   brian2=b2.__version__, seed=0)
    summary['excluded_v630_neuron_ids'] = missing
    (output / 'brain-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('PASS:', json.dumps(summary))


if __name__ == '__main__':
    main()

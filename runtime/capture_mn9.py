"""Capture model-generated MN9 spikes for mechanistic muscle replay tests.

These are simulated neural traces, not biological recordings or muscle validation.
No body controller is run and no stimulus-to-movement rule is used.
"""
import json
from pathlib import Path
import subprocess
import sys

import pyarrow  # Eon requires libarrow to load before torch.
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'eon-brain/code'))
from benchmark import get_experiment, path_comp, path_con, path_wt
from run_pytorch import DT, MODEL_PARAMS, TorchModel, get_hash_tables, get_weights


def main():
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable')
    lookup, _ = get_hash_tables(path_comp)
    stimuli = json.loads((ROOT / 'stimuli.json').read_text())
    sugar = [lookup[n] for n in get_experiment('sugar')['neu_exc']]
    bitter = [lookup[n] for n in stimuli['bitter_ids']]
    mn9_id = stimuli['mn9_ids'][0]
    mn9_index = lookup[mn9_id]
    weights = get_weights(path_con, path_comp, path_wt).to('cuda')
    traces = []
    for name, bitter_rate in [('sugar', 0), ('sugar_bitter', 200)]:
        torch.manual_seed(0)
        targets = sugar + (bitter if bitter_rate else [])
        model = TorchModel(1, weights.shape[0], DT, MODEL_PARAMS, weights,
                           exc_indices=targets, device='cuda')
        state = model.state_init()
        rates = torch.zeros(1, weights.shape[0], device='cuda')
        rates[0, sugar] = 200
        rates[0, bitter] = bitter_rate
        events = torch.zeros(5000, dtype=torch.bool, device='cuda')
        with torch.no_grad():
            for step in range(5000):
                state = model(rates, *state)
                events[step] = state[2][0, mn9_index] > 0
        times = events.nonzero().flatten().cpu().numpy() * DT / 1000
        traces.append(dict(name=name, duration_s=0.5, dt_s=DT / 1000,
            neuron_id=mn9_id, spike_times_s=times.tolist(),
            sugar_input_hz=200, bitter_input_hz=bitter_rate, seed=0))
    result = dict(kind='simulated-neural-spike-traces', biological_recording=False,
        source_repo='https://github.com/eonsystemspbc/fly-brain',
        source_commit=(ROOT/'eon-brain/REVISION').read_text().strip(),
        torch=torch.__version__, model_parameters=MODEL_PARAMS, traces=traces)
    (ROOT / 'mn9-spike-traces.json').write_text(json.dumps(result, indent=2) + '\n')
    print({trace['name']:len(trace['spike_times_s']) for trace in traces})


if __name__ == '__main__':
    main()

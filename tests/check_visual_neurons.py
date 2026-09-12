"""Small CPU compartment check; synthetic connections are never runtime data."""
import json
from pathlib import Path

import pyarrow
import numpy as np
import torch

from cns import DT, MODEL_PARAMS, VisualHybrid


def main():
    p = json.loads((Path(__file__).resolve().parents[1] / 'runtime/cns-model.json').read_text())['vision']
    # PR --histamine--> L1, using a synthetic weight solely to check inhibition.
    weights = torch.tensor([[0., 0.], [-20., 0.]]).to_sparse_csr()
    model = VisualHybrid(1, 2, DT, MODEL_PARAMS, weights, device='cpu',
        photo_indices=np.array([0]), lamina_indices=np.array([1]), visual_params=p)
    traces = []
    with torch.no_grad():
        for light in (0., 1., 0.):
            state = model.state_init()
            model.light[:] = light
            records = []
            for _ in range(1000):
                state = model(torch.zeros(1, 2), *state)
                records.append([state[2][0, 0].item(), state[2][0, 1].item(),
                                state[3][0, 0].item(), state[3][0, 1].item()])
            traces.append(np.array(records))
    dark, bright, repeat = traces
    assert np.array_equal(dark, repeat)
    assert np.isfinite(bright).all() and np.isfinite(dark).all()
    assert np.all(bright[:, :2] > 0) and np.all(bright[:, :2] < DT/1000*p['release_equivalent_max_hz'])
    assert bright[-1, 2] > dark[-1, 2] and bright[-1, 0] > dark[-1, 0]
    assert bright[-1, 3] < dark[-1, 3] and bright[-1, 1] < dark[-1, 1]
    delay_steps = model.neurons.synapse.steps_delay
    assert np.array_equal(dark[:delay_steps+1, 3], bright[:delay_steps+1, 3])
    print(json.dumps(dict(status='PASS: graded light depolarization, delayed histamine inhibition, tonic release and reset',
        dt_s=DT/1000, dark_final=dark[-1].tolist(), bright_final=bright[-1].tolist(),
        note='Synthetic two-cell assay, not a fitted retinal circuit or validated vision'), indent=2))


if __name__ == '__main__':
    main()

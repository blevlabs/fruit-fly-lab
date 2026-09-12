"""Run one Eon experiment on CUDA and save a checked result summary."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

import pyarrow  # Import before torch, as required by Eon's runner.
import torch

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'eon-brain'
sys.path.insert(0, str(SOURCE / 'code'))
from benchmark import BenchmarkLogger, get_experiment
from run_pytorch import run_single_benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, choices=[0.1, 1, 10, 100, 1000], default=0.1)
    parser.add_argument('--trials', type=int, choices=[1, 4, 8, 16, 32], default=1)
    parser.add_argument('--experiment', choices=['sugar', 'p9'], default='sugar')
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', args.label):
        parser.error('label must contain 1–80 letters, digits, underscores, or hyphens')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable; refusing to silently run on CPU')
    output = SOURCE / 'data' / 'results' / args.label
    output.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(0)
    logger = BenchmarkLogger(str(output / 'run.log'))
    try:
        result = run_single_benchmark(args.seconds, args.trials,
                    get_experiment(args.experiment), logger, run_label=args.label)
    finally:
        logger.close()
    if result['status'] != 'success':
        raise RuntimeError(result['status'])
    assert result['n_spikes'] > 0, 'GPU experiment produced no spikes'
    assert Path(result['spike_path']).is_file(), 'Spike output was not saved'
    result.update(gpu=torch.cuda.get_device_name(0), torch=torch.__version__,
                  cuda=torch.version.cuda, seed=0,
                  source_commit=(SOURCE / 'REVISION').read_text().strip())
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS:', json.dumps(result))


if __name__ == '__main__':
    main()

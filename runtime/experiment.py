"""One isolated individual, explicit physical history, the ordinary Session loop.

Example: python experiment.py history.json --output runs/assay-01
history.json: {"seed": 7, "phases": [{"name": "control", "steps": 100,
    "sources": [two ordinary arena source objects], "release_block": false}]}
--restore resumes an exact Session checkpoint before applying the new history.
No scorer, target answer, neural stimulation or joint command enters Session.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

import torch
import mujoco

from arena import validate_sources
from cns_live import Session, physics_warning
from checkpoint import require_keys


def run(history, output, restore=None):
    require_keys(history, ('seed', 'phases'))
    if type(history['seed']) is not int or history['seed'] < 0 or not isinstance(history['phases'], list) or not history['phases']:
        raise ValueError('Explicit seed and nonempty phases required')
    for phase in history['phases']:
        require_keys(phase, ('name', 'steps', 'sources', 'release_block'))
        if (type(phase['name']) is not str or not phase['name'] or type(phase['steps']) is not int
                or phase['steps'] < 1 or type(phase['release_block']) is not bool):
            raise ValueError('Invalid phase name, step count or intervention')
        validate_sources(phase['sources'])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output/'history.json').write_text(json.dumps(history, indent=2, allow_nan=False)+'\n')
    started = time.monotonic()
    session = None
    receipt = dict(status='RUNNING', preparation='Isolated estimated embodied CNS; physical environment only',
        biological_validation='not evaluated', capability='not evaluated',
        runner_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        history_sha256=hashlib.sha256((output/'history.json').read_bytes()).hexdigest())
    try:
        mujoco.set_mju_user_warning(physics_warning)
        session = Session(seed=history['seed'])
        if restore:
            session.restore_checkpoint(restore)
            if session.seed != history['seed']:
                raise ValueError('History seed differs from the restored individual')
        receipt.update(identity=session.identity(), individual_id=session.individual_id,
            initial_step=session.brain.tick, initial_time_s=session.sim.time)
        session.save_checkpoint(output/'initial.npz')
        with (output/'frames.jsonl').open('x') as stream:
            for phase in history['phases']:
                session.transition_trial(phase['sources'], release_block=phase['release_block'])
                remaining = phase['steps']
                while remaining:
                    steps = min(100, remaining)
                    frame = session.update(dict(paused=False, reset=session.reset_id, steps=steps,
                        sources=phase['sources'], release_block=phase['release_block']))
                    stream.write(json.dumps(dict(phase=phase['name'], trial_id=session.trial_id, frame=frame), allow_nan=False)+'\n')
                    stream.flush()
                    remaining -= steps
                session.save_checkpoint(output/'latest.npz')
        receipt.update(status='PASS: requested history executed; no biological/capability acceptance implied',
            final_step=session.brain.tick, final_time_s=session.sim.time,
            experienced_seconds=session.sim.time-receipt['initial_time_s'],
            peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
            final_checkpoint_sha256=hashlib.sha256((output/'latest.npz').read_bytes()).hexdigest())
    except BaseException as error:
        receipt.update(status='FAIL', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
        # Each completed phase's latest checkpoint remains intact. Failed dynamics
        # are not saved over the last valid state.
        raise
    finally:
        receipt['wall_seconds'] = time.monotonic()-started
        (output/'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        if session is not None:
            session.sim.close()
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('history', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--restore', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(json.loads(args.history.read_text()), args.output, args.restore), indent=2))

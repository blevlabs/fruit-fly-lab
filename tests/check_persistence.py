"""Isolated checkpoint regression, including a fresh-process trajectory replay.

Run from the staged candidate on CUDA. Creates only its explicit output directory.
No canonical worker, scene controls or historical receipt is changed.
"""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
from unittest.mock import patch
import zipfile

import numpy as np
import torch
import mujoco

from arena import default_sources, source_at_mouth
import checkpoint
from cns_live import Session, physics_warning


def equal(a, b, path='state'):
    if isinstance(a, np.ndarray):
        assert isinstance(b, np.ndarray) and a.dtype == b.dtype and np.array_equal(a, b), path
    elif isinstance(a, dict):
        assert isinstance(b, dict) and set(a) == set(b), path
        for key in a:
            equal(a[key], b[key], path+'.'+key)
    elif isinstance(a, (list, tuple)):
        assert type(a) is type(b) and len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            equal(x, y, f'{path}[{i}]')
    else:
        assert type(a) is type(b) and a == b, f'{path}: {a!r} != {b!r}'


def continue_history(session, history):
    for phase in history:
        session.transition_trial(phase['sources'], release_block=phase['release_block'])
        session.update(dict(paused=False, reset=session.reset_id, steps=phase['steps'],
            sources=phase['sources'], release_block=phase['release_block']))


def child(directory):
    saved = checkpoint.load(directory/'during.npz')
    session = Session(seed=saved['session']['seed'])
    try:
        session.import_state(saved)
        equal(saved, session.export_state())
        continue_history(session, json.loads((directory/'tail.json').read_text()))
        session.save_checkpoint(directory/'restored-final.npz')
        equal(checkpoint.load(directory/'expected-final.npz'), session.export_state())
        (directory/'child-pass.json').write_text(json.dumps(dict(exact_state=True,
            final_step=session.brain.tick, fresh_process=True), indent=2)+'\n')
    finally:
        session.sim.close()


def check(directory):
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    codec = {'scalar_array': np.array(4.5), 'empty': np.array([], dtype=np.int64),
             'tuple': (7, {'x': np.arange(6, dtype=np.float32).reshape(2, 3)[:, ::2]})}
    checkpoint.save(directory/'codec.npz', codec)
    equal(codec, checkpoint.load(directory/'codec.npz'))
    old_hash = hashlib.sha256((directory/'codec.npz').read_bytes()).hexdigest()
    for target in ('os.replace', 'np.savez_compressed'):
        with patch('checkpoint.'+target, side_effect=OSError('injected interrupted write')):
            try:
                checkpoint.save(directory/'codec.npz', {'replacement': np.arange(10)})
            except OSError:
                pass
            else:
                raise AssertionError('Interrupted write unexpectedly succeeded')
        assert hashlib.sha256((directory/'codec.npz').read_bytes()).hexdigest() == old_hash
    assert not list(directory.glob('*.tmp'))
    np.savez_compressed(directory/'malformed-arrays.npz', metadata=np.array(json.dumps(
        dict(format='fruit-fly-individual', schema=1, tree=None, arrays=[]))))
    damaged = bytearray((directory/'codec.npz').read_bytes())
    with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
        entry = archive.getinfo('metadata.npy')
        assert entry.compress_type == zipfile.ZIP_DEFLATED
        name_size, extra_size = struct.unpack_from('<HH', damaged, entry.header_offset+26)
        offset = entry.header_offset+30+name_size+extra_size
    damaged[offset] = (damaged[offset] & ~6) | 6  # Reserved DEFLATE block type.
    (directory/'corrupt-deflate.npz').write_bytes(damaged)
    corrupt_names = ('malformed-arrays', 'corrupt-deflate')
    for name in corrupt_names:
        try:
            checkpoint.load(directory/(name+'.npz'))
        except ValueError:
            pass
        else:
            raise AssertionError(f'{name} was not rejected as a nonfatal input error')
    print('PASS: codec, corrupt archive rejection and interrupted-write preservation', flush=True)

    session = Session(seed=17)
    try:
        initial = session.export_state()
        session.save_checkpoint(directory/'fresh.npz')
        other = Session(seed=17)
        try:
            other_before = other.export_state()
            equal(initial['identity'], other_before['identity'])
            equal(initial['brain'], other_before['brain'])
            equal(initial['native'], other_before['native'])
            assert initial['session']['individual_id'] != other_before['session']['individual_id']
            x, y = source_at_mouth(session.sim, 0)
            wet = default_sources()
            wet[0].update(x=float(x), y=float(y), temperature=35., odor=.7, taste='sweet', liquid=True)
            session.update(dict(paused=True, reset=0, sources=wet))
            for _ in range(20):
                frame = session.update(dict(paused=False, reset=0, sources=wet, steps=100))
                nmjs = session.motors.nmjs + [s.nmj if u['kind'] == 'asynchronous' else s for u, s in zip(session.flight.units, session.flight.states)]
                if (any(n.pending for n in nmjs) and np.any(session.sim.mj_data.act)
                        and any(s.activation > 0 for u, s in zip(session.flight.units, session.flight.states) if u['kind'] == 'asynchronous')
                        and any(abs(v) > 0 for v in session.fluid.net_boundary_volume_mm3.values())):
                    break
            assert any(n.pending for n in nmjs), 'No in-flight NMJ event at checkpoint'
            assert np.any(session.sim.mj_data.act), 'No active native muscle at checkpoint'
            assert any(s.activation > 0 for u, s in zip(session.flight.units, session.flight.states) if u['kind'] == 'asynchronous'), 'No active IFM history at checkpoint'
            assert any(abs(v) > 0 for v in session.fluid.net_boundary_volume_mm3.values()), 'No fluid exchange at checkpoint'
            assert np.any(session.senses.thermal.adapted_temperature != 22), 'No sensory adaptation at checkpoint'
            equal(other_before, other.export_state())
            print('PASS: two fresh individuals isolated; delayed events, muscles, fluid and adaptation active', flush=True)
        finally:
            other.sim.close()
        during = session.export_state()
        session.save_checkpoint(directory/'during.npz')
        equal(during, checkpoint.load(directory/'during.npz'))
        paused_tick = session.brain.tick
        session.update(dict(paused=True, reset=session.reset_id, sources=wet))
        assert session.brain.tick == paused_tick
        equal(during['brain'], session.export_state()['brain'])
        equal(during['native'], session.export_state()['native'])
        session.import_state(during)
        invalid = []
        bad = copy.deepcopy(during); bad['identity']['schema'] += 1; invalid.append(bad)
        bad = copy.deepcopy(during); del bad['brain']['state']; invalid.append(bad)
        bad = copy.deepcopy(during); bad['senses']['thermal']['time'] += 1; invalid.append(bad)
        bad = copy.deepcopy(during); bad['session']['last_sources'][0]['x'] += 1; invalid.append(bad)
        bad = copy.deepcopy(during); del bad['session']['last_request']['release_block']; invalid.append(bad)
        bad = copy.deepcopy(during); bad['session']['last_request']['release_block'] = 'invalid'; invalid.append(bad)
        bad = copy.deepcopy(during); bad['nmjs'][0]['pending'] = (session.brain.tick*session.substeps-1,); invalid.append(bad)
        for bad in invalid:
            before = session.export_state()
            try:
                session.import_state(bad)
            except (ValueError, TypeError, KeyError):
                pass
            else:
                raise AssertionError('Invalid checkpoint accepted')
            equal(before, session.export_state())
        corrupt = directory/'corrupt.npz'
        corrupt.write_bytes((directory/'during.npz').read_bytes()[:1000])
        before = session.export_state()
        try:
            session.restore_checkpoint(corrupt)
        except ValueError:
            pass
        else:
            raise AssertionError('Truncated checkpoint accepted')
        equal(before, session.export_state())
        dry = copy.deepcopy(wet); dry[0]['liquid'] = False
        bad_requests = [dict(checkpoint='save', name=name)
            for name in ('', '../escape', '/tmp/escape', 'a'*65, 7)]
        bad_requests += [dict(checkpoint='erase', name='during'),
                         dict(checkpoint='restore', name='during', path='elsewhere')]
        before = session.export_state()
        for request in bad_requests:
            # A regressed path guard must fail the check without writing outside it.
            with patch.object(session, 'save_checkpoint', side_effect=AssertionError('Invalid slot reached save')):
                try:
                    session.checkpoint_command(request, directory)
                except ValueError:
                    pass
                else:
                    raise AssertionError('Invalid checkpoint command accepted')
            equal(before, session.export_state())
        for name in (*corrupt_names, 'absent'):
            expected_error = FileNotFoundError if name == 'absent' else ValueError
            try:
                session.checkpoint_command(dict(checkpoint='restore', name=name), directory)
            except expected_error:
                pass
            else:
                raise AssertionError('Corrupt or missing checkpoint command accepted')
            equal(before, session.export_state())
        session.update(dict(paused=True, reset=session.reset_id, sources=wet, release_block=True))
        blocked = session.export_state()
        saved = session.checkpoint_command(dict(checkpoint='save', name='blocked'), directory)
        assert saved['release_block'] is True
        equal(blocked, session.export_state())
        session.update(dict(paused=True, reset=session.reset_id+1, sources=dry, release_block=False))
        before = session.export_state()
        with patch.object(Path, 'read_bytes', side_effect=OSError('injected receipt read failure')):
            with patch.object(session, 'import_state', wraps=session.import_state) as imported:
                try:
                    session.checkpoint_command(dict(checkpoint='restore', name='blocked'), directory)
                except OSError:
                    pass
                else:
                    raise AssertionError('Failed checkpoint read unexpectedly succeeded')
                imported.assert_not_called()
        equal(before, session.export_state())
        payload = (directory/'blocked.npz').read_bytes()
        with patch.object(Path, 'read_bytes', side_effect=[payload, OSError('second read after restore')]) as read:
            restored = session.checkpoint_command(dict(checkpoint='restore', name='blocked'), directory)
            assert read.call_count == 1, 'Restore read the checkpoint again after mutation'
        assert restored == dict(saved, action='restore')
        assert restored['sha256'] == hashlib.sha256(payload).hexdigest()
        assert restored['sources'] == wet and restored['reset'] == blocked['session']['reset_id']
        assert restored['release_block'] is True
        equal(blocked, session.export_state())
        session.import_state(during)
        print('PASS: pause, rejected commands, source/reset/intervention restore and read-before-mutation', flush=True)
        tail = [dict(sources=wet, release_block=False, steps=100),
                dict(sources=dry, release_block=True, steps=25),
                dict(sources=wet, release_block=False, steps=100)]
        (directory/'tail.json').write_text(json.dumps(tail, indent=2)+'\n')
        before_trial = session.export_state()
        session.transition_trial(wet)
        equal(before_trial['brain'], session.export_state()['brain'])
        equal(before_trial['native'], session.export_state()['native'])
        assert session.trial_id == before_trial['session']['trial_id']+1
        session.import_state(before_trial)
        continue_history(session, tail)
        session.save_checkpoint(directory/'expected-final.npz')
        identity = session.identity()
        final_step = session.brain.tick
        session.reset()
        reset = session.export_state()
        equal(initial['brain'], reset['brain'])
        equal(initial['native'], reset['native'])
        assert reset['session']['individual_id'] != during['session']['individual_id']
        assert reset['session']['trial_id'] == 0
    finally:
        session.sim.close()
    # A process boundary prevents surviving Python/CUDA objects from supplying
    # omitted state. The child loads only the checkpoint and declared history.
    result = subprocess.run([sys.executable, '-B', __file__, '--child', str(directory)],
        text=True, capture_output=True)
    (directory/'child.log').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError(f'Fresh-process continuation failed; see {directory}/child.log')
    equal(checkpoint.load(directory/'expected-final.npz'), checkpoint.load(directory/'restored-final.npz'))
    receipt = dict(status='PASS: exact deterministic individual persistence', identity=identity,
        check_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        implementation=dict(codec=True, delayed_events=True, active_native_muscles=True,
            asynchronous_history=True, fluid_exchange=True, sensory_adaptation=True,
            fresh_individual_isolation=True, pause=True, trial_transition=True, full_reset=True,
            fresh_process_continuation=True, corrupt_incompatible_rejection=True, interrupted_write_recovery=True,
            corrupt_deflate_rejection=True, malformed_array_inventory_rejection=True,
            checkpoint_command_validation=True, failed_command_preserves_individual=True,
            restored_sources_reset_release_block=True, read_before_restore=True),
        checkpoint_step=during['brain']['tick'], final_step=final_step,
        checkpoint_bytes=(directory/'during.npz').stat().st_size,
        wall_seconds=time.monotonic()-started, exact_scope='All exported scientific state, including global RNGs; wall-time profiling/renderer counters excluded',
        numerical_qualification='Exact replay at existing fixed timesteps; no new biological equation or timestep claim',
        biological_validation='not evaluated', capabilities='No learned memory or natural repertoire claim')
    (directory/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


def check_runner(directory):
    """Held-out CLI history: same initial individual, with or without process exit."""
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    warm = default_sources(False)
    warm[0].update(enabled=True, x=1.5, y=.5, odor=.2, temperature=26., taste='sweet', liquid=True)
    changed = copy.deepcopy(warm)
    changed[0]['enabled'] = False
    changed[1].update(enabled=True, x=-2., y=.8, odor=.8, temperature=35., taste='bitter', liquid=False)
    phases = [dict(name='heldout-warm', steps=137, sources=warm, release_block=False),
              dict(name='heldout-changed', steps=83, sources=changed, release_block=True)]
    runs = [('uninterrupted', phases, directory/'fresh.npz'),
            ('first', phases[:1], directory/'fresh.npz'),
            ('resumed', phases[1:], directory/'first/latest.npz')]
    # Fix the history before any candidate trajectory is inspected.
    for name, history, _ in runs:
        (directory/(name+'.json')).write_text(json.dumps(dict(seed=31, phases=history), indent=2)+'\n')
    session = Session(seed=31)
    try:
        session.save_checkpoint(directory/'fresh.npz')
    finally:
        session.sim.close()
    del session
    torch.cuda.empty_cache()
    runner = Path(__file__).resolve().parents[1] / 'runtime/experiment.py'
    for name, _, restore in runs:
        result = subprocess.run([sys.executable, '-B', str(runner), str(directory/(name+'.json')),
            '--output', str(directory/name), '--restore', str(restore)], text=True, capture_output=True)
        (directory/(name+'.log')).write_text(result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError(f'Runner continuation failed; see {directory}/{name}.log')
    fresh = checkpoint.load(directory/'fresh.npz')
    equal(fresh, checkpoint.load(directory/'uninterrupted/initial.npz'))
    equal(fresh, checkpoint.load(directory/'first/initial.npz'))
    equal(checkpoint.load(directory/'first/latest.npz'), checkpoint.load(directory/'resumed/initial.npz'))
    final = checkpoint.load(directory/'uninterrupted/latest.npz')
    equal(final, checkpoint.load(directory/'resumed/latest.npz'))
    expected_frames = [('heldout-warm', 1, 100), ('heldout-warm', 1, 137), ('heldout-changed', 2, 220)]
    for name, bounds, expected in [('uninterrupted', (0, 220), expected_frames),
            ('first', (0, 137), expected_frames[:2]), ('resumed', (137, 220), expected_frames[2:])]:
        receipt = json.loads((directory/name/'receipt.json').read_text())
        assert receipt['status'].startswith('PASS:')
        assert (receipt['initial_step'], receipt['final_step']) == bounds
        assert receipt['individual_id'] == fresh['session']['individual_id']
        equal(fresh['identity'], receipt['identity'])
        assert receipt['final_checkpoint_sha256'] == hashlib.sha256((directory/name/'latest.npz').read_bytes()).hexdigest()
        frames = [json.loads(line) for line in (directory/name/'frames.jsonl').read_text().splitlines()]
        assert [(v['phase'], v['trial_id'], v['frame']['step']) for v in frames] == expected
        for sample in frames:
            phase = next(p for p in phases if p['name'] == sample['phase'])
            frame = sample['frame']
            assert frame['paused'] is False and frame['reset'] == fresh['session']['reset_id']
            assert frame['sources'] == phase['sources'] and frame['release_block'] == phase['release_block']
    assert final['brain']['tick'] == 220 and final['session']['trial_id'] == 2
    assert final['session']['individual_id'] == fresh['session']['individual_id']
    assert final['session']['seed'] == 31 and final['session']['reset_id'] == fresh['session']['reset_id']
    assert final['session']['last_request']['steps'] == 83
    assert final['session']['last_request']['release_block'] is True
    assert final['session']['last_sources'] == changed
    receipt = dict(status='PASS: exact runner continuation across fresh processes', identity=final['identity'],
        check_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        runner_source_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(), seed=31,
        split_step=137, final_step=220, shared_initial_checkpoint_sha256=hashlib.sha256((directory/'fresh.npz').read_bytes()).hexdigest(),
        exact_scope='All exported scientific state, including individual identity and global RNGs',
        implementation=dict(shared_initial_individual=True, explicit_physical_history=True,
            cli_phase_boundaries=True, closed_process_restore=True, exact_exported_state=True),
        numerical_qualification='Exact replay at existing timesteps; no physiological calibration',
        biological_validation='not evaluated', capabilities='No learned memory or natural repertoire claim',
        wall_seconds=time.monotonic()-started)
    (directory/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


def check_save_guard(directory):
    """A failed causal interval must not replace the last valid individual."""
    directory.mkdir(parents=True, exist_ok=False)
    session = Session(seed=17)
    try:
        session.update(dict(paused=True, reset=0, sources=default_sources(False)))
        path = directory/'current.npz'
        session.save_checkpoint(path)
        original = path.read_bytes()
        (directory/'known-good.npz').write_bytes(original)
        # Fault injection: exactly the boundary after neural integration and
        # before the physical substeps, with finite but inconsistent clocks.
        session.brain.advance()
        rejected = False
        try:
            session.save_checkpoint(path)
        except ValueError:
            rejected = True
        preserved = path.read_bytes() == original
        receipt = dict(status='PASS' if rejected and preserved else 'FAIL',
            scope='Reject inconsistent scientific state before replacing a valid checkpoint',
            invalid_save_rejected=rejected, last_valid_bytes_preserved=preserved,
            neural_tick=session.brain.tick, physical_time_s=session.sim.time,
            before_sha256=hashlib.sha256(original).hexdigest(),
            after_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            identity=session.identity(), check_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        (directory/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps({k:v for k,v in receipt.items() if k!='identity'}, indent=2))
        assert rejected and preserved, 'Saving an interrupted interval replaced the last valid checkpoint'
    finally:
        session.sim.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--child', type=Path)
    mode.add_argument('--runner', action='store_true', help='Compare a held-out history through experiment.py CLI')
    mode.add_argument('--save-guard', action='store_true', help='Reject checkpointing an interrupted causal interval')
    args = parser.parse_args()
    mujoco.set_mju_user_warning(physics_warning)
    if args.child:
        child(args.child.resolve())
    elif args.output:
        (check_save_guard if args.save_guard else check_runner if args.runner else check)(args.output.resolve())
    else:
        parser.error('--output is required')

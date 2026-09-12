"""Transport-only checks with fake processes; no scientific runtime or GPU imports."""
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import transport


EXPECTED = dict(type='ready', device='cuda', protocol=6, mujoco='3.9.0',
                body_sha='body', neural_code_sha='neural', worker_code_sha='worker',
                senses_sha='senses')
READY = dict(EXPECTED, checkpoint_schema=1)


class Pipe(io.BytesIO):
    def fileno(self):
        return 10  # os.read is mocked; no real descriptor is used.


@contextmanager
def worker(messages, expected=EXPECTED):
    process = SimpleNamespace(
        stdin=io.StringIO(),
        stdout=Pipe(b''.join(m if isinstance(m, bytes) else
                    ((m if isinstance(m, str) else json.dumps(m)) + '\n').encode() for m in messages)),
        wait=Mock(return_value=0), terminate=Mock(), kill=Mock())
    with patch.object(transport, '_expected_identity', return_value=expected), \
         patch.object(transport.subprocess, 'Popen', return_value=process) as spawn, \
         patch.object(transport.os, 'read', side_effect=lambda fd, count: process.stdout.read(count)), \
         patch.object(transport.select, 'select', return_value=([process.stdout], [], [])):
        yield process, spawn


def rejects(error, call):
    try:
        call()
    except error:
        return
    raise AssertionError(f'Expected {error.__name__}')


def main():
    # Identity verification uses the flat source paths without importing real models.
    modules = dict(mujoco=SimpleNamespace(__version__='3.9.0'),
        body=SimpleNamespace(body_signature=lambda: 'mn9-body'),
        cns_body=SimpleNamespace(body_signature=lambda: 'cns-body'),
        cns_senses=SimpleNamespace(Senses=lambda: SimpleNamespace(sha256='senses')))
    with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, modules):
        root = Path(directory)
        (root / 'cns.py').write_bytes(b'neural source')
        (root / 'cns_live.py').write_bytes(b'worker source')
        with patch.object(transport, 'ROOT', root):
            identity = transport._expected_identity('cns')
            assert identity['neural_code_sha'] == hashlib.sha256(b'neural source').hexdigest()
            assert identity['worker_code_sha'] == hashlib.sha256(b'worker source').hexdigest()
            assert identity['body_sha'] == 'cns-body' and identity['senses_sha'] == 'senses'
            assert transport._expected_identity('mn9')['body_sha'] == 'mn9-body'

    with worker([READY, {'type': 'frame'}, {'type': 'checkpoint'}]) as (process, spawn):
        backend = transport.Backend(mode='cns')
        argv, = spawn.call_args.args
        options = spawn.call_args.kwargs
        assert argv == [sys.executable, '-B', '-u', str(transport.ROOT / 'cns_live.py')]
        assert options['cwd'] == transport.ROOT and options['env']['MUJOCO_GL'] == 'disable'
        assert not options.get('shell') and 'stderr' not in options
        assert backend.update({'paused': True}) == {'type': 'frame'}
        assert backend.checkpoint('save', 'sample_1') == {'type': 'checkpoint'}
        sent = process.stdin.getvalue().splitlines()
        assert list(map(json.loads, sent)) == [dict(paused=True), dict(checkpoint='save', name='sample_1')]
        for action, name in [('erase', 'x'), ('restore', '../x'), ('save', '')]:
            rejects(ValueError, lambda: backend.checkpoint(action, name))
        assert process.stdin.getvalue().splitlines() == sent
        backend.close()
        backend.close()
        assert process.stdin.closed and process.stdout.closed
        process.terminate.assert_not_called()

    mn9 = dict(type='ready', device='cuda', protocol=5, mujoco='3.9.0', body_sha='body')
    with worker([mn9], mn9) as (_, spawn):
        backend = transport.Backend()
        assert spawn.call_args.args[0][-1] == str(transport.ROOT / 'mn9_worker.py')
        rejects(ValueError, lambda: backend.checkpoint('save'))
        backend.close()
    with worker([READY]) as (_, spawn):
        backend = transport.Backend('cns', command='python "/path with spaces/worker.py" --label "two words"')
        assert spawn.call_args.args[0] == ['python', '/path with spaces/worker.py', '--label', 'two words']
        backend.close()
    for command in ('', '   ', '"unclosed', 3):
        with worker([READY]) as (_, spawn):
            rejects(ValueError, lambda: transport.Backend('cns', command=command))
            spawn.assert_not_called()

    for field in EXPECTED:
        with worker([dict(READY, **{field: None})]) as (process, _):
            rejects(RuntimeError, lambda: transport.Backend('cns'))
            assert process.stdin.closed and process.stdout.closed
    for response, error in [('not-json', RuntimeError), ([], RuntimeError),
                            ({'type': 'error', 'error': 'invalid'}, ValueError),
                            ({'type': 'error', 'error': 'fatal', 'fatal': True}, RuntimeError),
                            ({'type': 'ready'}, ConnectionError)]:
        with worker([READY, response]):
            backend = transport.Backend('cns')
            rejects(error, lambda: backend.update({'paused': True}))
            backend.close()
    with worker([READY]):
        backend = transport.Backend('cns')
        rejects(ConnectionError, lambda: backend.update({'paused': True}))
        backend.close()
    with worker([READY]) as (process, _):
        with patch.object(transport.select, 'select', return_value=([], [], [])):
            rejects(TimeoutError, lambda: transport.Backend('cns'))
        assert process.stdin.closed and process.stdout.closed
    with worker([b'{"type":']) as (process, _):
        with patch.object(transport.time, 'monotonic', side_effect=[0, 0, 46]):
            rejects(TimeoutError, lambda: transport.Backend('cns'))
        assert process.stdin.closed and process.stdout.closed
    with worker([READY]) as (process, _):
        backend = transport.Backend('cns')
        process.wait.side_effect = [subprocess.TimeoutExpired('worker', 5),
                                   subprocess.TimeoutExpired('worker', 5), 0]
        backend.close()
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        assert process.stdout.closed
    print('PASS: local transport, strict identity, protocol errors, checkpoint validation and process cleanup')


if __name__ == '__main__':
    main()

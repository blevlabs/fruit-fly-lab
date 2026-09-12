"""JSON-line client for a compatible CUDA worker; no viewer or UI imports."""
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shlex
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent


def _expected_identity(mode):
    import mujoco
    from body import body_signature

    expected = dict(type='ready', device='cuda', protocol=6 if mode == 'cns' else 5,
                    mujoco=mujoco.__version__)
    if mode == 'cns':
        from cns_body import body_signature
        from cns_senses import Senses
        expected.update(
            neural_code_sha=hashlib.sha256((ROOT / 'cns.py').read_bytes()).hexdigest(),
            worker_code_sha=hashlib.sha256((ROOT / 'cns_live.py').read_bytes()).hexdigest(),
            senses_sha=Senses().sha256)
    expected['body_sha'] = body_signature()
    return expected


class Backend:
    def __init__(self, mode='mn9', command=None):
        if mode not in ('mn9', 'cns'):
            raise ValueError('Unknown neural/body model')
        if command is not None and (not isinstance(command, str) or not command.strip()):
            raise ValueError('Backend command must be a nonempty command string')
        script = 'cns_live.py' if mode == 'cns' else 'mn9_worker.py'
        argv = shlex.split(command) if command is not None else [sys.executable, '-B', '-u', str(ROOT / script)]
        if not argv:
            raise ValueError('Backend command must name an executable')
        expected = _expected_identity(mode)
        self._output = bytearray()
        self.process = subprocess.Popen(argv, cwd=ROOT,
            env={**os.environ, 'MUJOCO_GL': 'disable'},
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        try:
            self.info = self.receive()
            for field, value in expected.items():
                if self.info.get(field) != value:
                    raise RuntimeError(f'CUDA worker {field} differs from the local runtime')
        except BaseException:
            self.close()
            raise

    def receive(self):
        deadline = time.monotonic() + 45
        while (newline := self._output.find(b'\n')) < 0:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError('CUDA worker stopped responding')
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise ConnectionError('CUDA worker closed the simulation connection')
            self._output.extend(chunk)
        line = bytes(self._output[:newline])
        del self._output[:newline + 1]
        try:
            message = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise RuntimeError(f'Worker emitted non-protocol output: {line[:500].decode("utf-8", errors="replace")}') from error
        if not isinstance(message, dict):
            raise RuntimeError('Worker response must be a JSON object')
        if message.get('type') == 'error':
            error = RuntimeError if message.get('fatal') else ValueError
            raise error(message.get('error', 'Worker reported an error'))
        return message

    def update(self, controls):
        self.process.stdin.write(json.dumps(controls, allow_nan=False) + '\n')
        self.process.stdin.flush()
        response = self.receive()
        expected = 'checkpoint' if 'checkpoint' in controls else 'frame'
        if response.get('type') != expected:
            raise ConnectionError('Unexpected worker response; refusing another command')
        return response

    def checkpoint(self, action, name='current'):
        if action not in ('save', 'restore') or type(name) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', name) is None:
            raise ValueError('Expected save/restore and a 1–64 character checkpoint name')
        if self.info.get('checkpoint_schema') != 1:
            raise ValueError('This worker does not support individual checkpoints')
        return self.update(dict(checkpoint=action, name=name))

    def close(self):
        # EOF asks the owned worker to release its simulation and CUDA state.
        with suppress(BrokenPipeError):
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        finally:
            self.process.stdout.close()

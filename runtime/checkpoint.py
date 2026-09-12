"""Atomic, non-executable individual checkpoints: JSON tree plus NumPy arrays."""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import zipfile
import zlib

import numpy as np


def require_keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f'Checkpoint fields differ: expected {sorted(keys)}')


def array_like(value, reference):
    if (not isinstance(value, np.ndarray) or value.shape != reference.shape
            or value.dtype != reference.dtype or not np.isfinite(value).all()):
        raise ValueError('Checkpoint array shape, dtype or finite-value mismatch')


def save(path, state):
    """Replace only after a complete, flushed write; failure keeps the old file."""
    arrays, descriptors = {}, {}

    def encode(value):
        if isinstance(value, np.ndarray):
            if value.dtype.kind not in 'biuf' or not np.isfinite(value).all():
                raise ValueError('Checkpoint arrays must contain finite real numbers')
            name = f'a{len(arrays)}'
            arrays[name] = np.array(value, copy=True, order='C')
            descriptors[name] = dict(shape=list(value.shape), dtype=value.dtype.str,
                sha256=hashlib.sha256(arrays[name].tobytes()).hexdigest())
            return {'array': name}
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, dict):
            if not all(type(k) is str for k in value):
                raise ValueError('Checkpoint dictionary keys must be strings')
            return {'dict': {k: encode(v) for k, v in value.items()}}
        if isinstance(value, (tuple, list)):
            return {'tuple' if isinstance(value, tuple) else 'list': [encode(v) for v in value]}
        if value is None or type(value) in (bool, int, str):
            return value
        if type(value) is float and math.isfinite(value):
            return value
        raise ValueError(f'Unsupported checkpoint value: {type(value).__name__}')

    tree = encode(state)
    metadata = json.dumps(dict(format='fruit-fly-individual', schema=1,
        tree=tree, arrays=descriptors), allow_nan=False, separators=(',', ':'))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name+'.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            np.savez_compressed(stream, metadata=np.array(metadata), **arrays)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load(path):
    try:
        return _load(path)
    except (zipfile.BadZipFile, EOFError, zlib.error, RuntimeError) as error:
        raise ValueError('Corrupt or interrupted checkpoint archive') from error


def _load(path):
    """Reject malformed or changed data; never import objects or execute pickle."""
    with np.load(path, allow_pickle=False) as archive:
        metadata = archive['metadata']
        if metadata.shape != () or metadata.dtype.kind != 'U':
            raise ValueError('Invalid checkpoint metadata')
        record = json.loads(str(metadata))
        require_keys(record, ('format', 'schema', 'tree', 'arrays'))
        if record['format'] != 'fruit-fly-individual' or type(record['schema']) is not int or record['schema'] != 1:
            raise ValueError('Incompatible checkpoint schema')
        if not isinstance(record['arrays'], dict):
            raise ValueError('Invalid checkpoint array inventory')
        if set(archive.files) != {'metadata', *record['arrays']} or len(archive.files) != len(set(archive.files)):
            raise ValueError('Checkpoint array inventory mismatch')
        arrays = {}
        for name, descriptor in record['arrays'].items():
            require_keys(descriptor, ('shape', 'dtype', 'sha256'))
            value = archive[name]
            if (value.dtype.kind not in 'biuf' or list(value.shape) != descriptor['shape']
                    or value.dtype.str != descriptor['dtype'] or not np.isfinite(value).all()
                    or hashlib.sha256(value.tobytes()).hexdigest() != descriptor['sha256']):
                raise ValueError(f'Corrupt checkpoint array: {name}')
            arrays[name] = value
        used = set()

        def decode(value):
            if isinstance(value, dict):
                if len(value) != 1:
                    raise ValueError('Invalid checkpoint tree')
                tag, child = next(iter(value.items()))
                if tag == 'array' and child in arrays and child not in used:
                    used.add(child)
                    return arrays[child]
                if tag == 'dict' and isinstance(child, dict):
                    return {k: decode(v) for k, v in child.items()}
                if tag in ('tuple', 'list') and isinstance(child, list):
                    values = [decode(v) for v in child]
                    return tuple(values) if tag == 'tuple' else values
                raise ValueError('Invalid checkpoint node')
            if value is None or type(value) in (bool, int, str):
                return value
            if type(value) is float and math.isfinite(value):
                return value
            raise ValueError('Invalid checkpoint scalar')

        result = decode(record['tree'])
        if used != set(arrays):
            raise ValueError('Unreferenced checkpoint array')
        return result

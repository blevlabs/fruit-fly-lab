"""Validate public source, documentation and data without starting simulations."""
import argparse
import ast
import gzip
import io
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import urllib.parse
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.venv', '.cache', '__pycache__', 'runs', 'archive', 'malecns-v1', 'dist', 'raw', 'downloaded'}
RULES = {
    'private key': re.compile(r'-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----'),
    'personal home path': re.compile(r'/(?:Users|home)/[^\s/"<>]+/|[A-Za-z]:\\Users\\'),
    'credential': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|sk-[A-Za-z0-9_-]{32,}|AKIA[A-Z0-9]{16})\b'),
    'private IPv6 address': re.compile(r'\b(?:f[cd][0-9a-f]{2}|fe80)(?::[0-9a-f]{0,4}){3,}\b', re.IGNORECASE),
    'captured access-challenge metadata': re.compile(r'__cf_' + r'chl_|X-Real' + r'-Ip|window\._cf_' + r'chl_opt'),
    'captured challenge URL': re.compile(r'/cdn-cgi/(?:challenge-platform|content)[/?]'),
    'populated web session token': re.compile(r'(?:name=["\'](?:csrf-token|authenticity_token)["\'][^>]*?(?:content|value)=["\'][^"\']+|["\'](?:csrf[_-]?token|authenticity_token)["\']\s*:\s*["\'][^"\']+)', re.IGNORECASE),
    'signed URL credential': re.compile(r'[?&](?:access_token|id_token|auth_token|X-Amz-Signature|X-Goog-Signature)='),
}
IP = re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])')

def inspect_text(text, label, errors, denied):
    text = text.replace('\x00', '').replace('\\x00', '')
    for kind, pattern in RULES.items():
        if pattern.search(text):
            errors.append(f'{label}: {kind}')
    # SVG path coordinates and explicit software versions are not IP addresses.
    ip_text = re.sub(r'\bd=["\'][MmZzLlHhVvCcSsQqTtAa0-9eE+.,\s-]+["\']', '', text)
    for match in IP.finditer(ip_text):
        token = match.group()
        try:
            ipaddress.IPv4Address(token)
        except ipaddress.AddressValueError:
            continue
        prefix = ip_text[max(0, match.start()-40):match.start()]
        if re.search(r'(?:[\w_-]*version|\bv\.)["\s:=]+$', prefix, re.IGNORECASE):
            continue
        if re.search(r'<sec\b[^>]*\bid=["\']sec$', prefix):
            continue
        # CUDA dependency versions can have four components; they are not hosts.
        if label == 'uv.lock':
            line = ip_text[ip_text.rfind('\n', 0, match.start())+1:ip_text.find('\n', match.end())]
            if re.fullmatch(r'\s*version\s*=\s*"'+re.escape(token)+r'"\s*', line):
                continue
            if 'https://files.pythonhosted.org/' in line and re.search(r'/[^/\s"]+-'+re.escape(token)+r'-[^/\s"]+\.whl', line):
                continue
        errors.append(f'{label}: numeric IP address')
        break
    if any(value in text for value in denied):
        errors.append(f'{label}: private marker from local deny list')

def inspect_file(path, errors, denied):
    label = str(path.relative_to(ROOT))
    suffix = path.suffix.lower()
    def inspect_numpy(stream, member_label):
        version = np.lib.format.read_magic(stream)
        reader = (np.lib.format.read_array_header_1_0 if version == (1, 0)
                  else np.lib.format.read_array_header_2_0)
        _, _, dtype = reader(stream)
        if dtype.hasobject:
            errors.append(f'{member_label}: object-array metadata cannot be inspected without pickle')
            return
        if dtype.kind not in ('U', 'S') and dtype.fields is None:
            return
        stream.seek(0)
        values = np.load(stream, allow_pickle=False)
        def fields(array):
            if array.dtype.names:
                for name in array.dtype.names: fields(array[name])
            elif array.dtype.kind in ('U', 'S'):
                for value in array.flat:
                    inspect_text(value.decode(errors='replace') if isinstance(value, bytes) else str(value), member_label, errors, denied)
        fields(values)
    if suffix in ('.npz', '.xlsx', '.docx'):
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if member.filename.endswith('.npy'):
                    with archive.open(member) as stream:
                        inspect_numpy(stream, label+'!'+member.filename)
                elif member.filename.endswith(('.xml', '.json', '.txt', '.rels')):
                    inspect_text(archive.read(member).decode('utf-8', errors='replace'), label+'!'+member.filename, errors, denied)
    elif path.name.endswith(('.csv.gz', '.tsv.gz', '.json.gz', '.txt.gz')):
        with gzip.open(path, 'rt') as stream:
            for line in stream: inspect_text(line, label, errors, denied)
    elif suffix in ('.h5', '.hdf5', '.h5j'):
        import h5py
        with h5py.File(path, 'r') as hdf:
            def inspect_hdf(name, node):
                inspect_text(name+str(dict(node.attrs)), label, errors, denied)
                if isinstance(node, h5py.Dataset) and h5py.check_string_dtype(node.dtype):
                    inspect_text(str(node.asstr()[()]), label+'!'+name, errors, denied)
            inspect_hdf('/', hdf)
            hdf.visititems(inspect_hdf)
    elif path.name.endswith('-signal-video.bin'):
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format_tags:stream_tags',
                                 '-of', 'json', str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f'{label}: scientific video metadata inspection failed')
        else:
            inspect_text(result.stdout, label, errors, denied)
    elif path.name.endswith('-signal.raw'):
        # Indexed decoded uint8 voxel streams have no textual metadata channel.
        # The export index verifies their exact bytes and source dimensions.
        pass
    elif path.name.endswith('-stack-header.bin'):
        inspect_text(path.read_bytes().replace(b'\0', b'').decode('utf-8', errors='ignore'), label, errors, denied)
    elif suffix == '.npy':
        with path.open('rb') as stream: inspect_numpy(stream, label)
    elif suffix in ('.mat', '.fig'):
        try:
            from scipy.io import loadmat
        except ImportError:
            errors.append(f'{label}: scipy required to inspect MATLAB metadata')
            return
        def visit(value):
            if isinstance(value, dict):
                for x in value.values(): visit(x)
            elif isinstance(value, (list, tuple)):
                for x in value: visit(x)
            elif isinstance(value, np.ndarray):
                if value.dtype.kind in ('O', 'U', 'S'):
                    for x in value.flat: visit(x)
            elif isinstance(value, (str, bytes)):
                inspect_text(value.decode(errors='replace') if isinstance(value, bytes) else value, label, errors, denied)
        visit(loadmat(path, simplify_cells=True))
    elif suffix in ('.feather', '.parquet'):
        import pyarrow as pa
        import pyarrow.feather as feather
        import pyarrow.parquet as parquet
        table = feather.read_table(path) if suffix == '.feather' else parquet.read_table(path)
        for key, value in (table.schema.metadata or {}).items():
            inspect_text(key.decode(errors='replace')+value.decode(errors='replace'), label, errors, denied)
        for column in table.columns:
            if pa.types.is_string(column.type) or pa.types.is_large_string(column.type) or pa.types.is_dictionary(column.type):
                for value in column.to_pylist():
                    if value is not None: inspect_text(str(value), label, errors, denied)
    elif suffix == '.pdf':
        result = subprocess.run(['pdftotext', '-q', str(path), '-'], capture_output=True, text=True)
        if result.returncode:
            errors.append(f'{label}: PDF text inspection failed')
        else:
            inspect_text(result.stdout, label, errors, denied)
    elif suffix in ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.gif'):
        from PIL import Image
        with Image.open(path) as picture:
            inspect_text(str(picture.info), label, errors, denied)
            if hasattr(picture, 'tag_v2'): inspect_text(str(dict(picture.tag_v2)), label, errors, denied)
    else:
        try:
            inspect_text(path.read_text(), label, errors, denied)
        except UnicodeError:
            errors.append(f'{label}: unrecognized binary format')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deny-file', type=Path, help='Optional local-only private markers; never commit this file')
    parser.add_argument('--include-archive', action='store_true', help='Also inspect restored scientific archive metadata')
    parser.add_argument('--static-only', action='store_true')
    args = parser.parse_args()
    denied = args.deny_file.read_text().splitlines() if args.deny_file else []
    denied = [v for v in denied if v]
    listed = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                            cwd=ROOT, capture_output=True, text=True)
    if listed.returncode == 0:
        paths = [ROOT/name for name in listed.stdout.split('\0') if name and (ROOT/name).is_file()]
    else:
        paths = [p for p in ROOT.rglob('*') if p.is_file() and not set(p.relative_to(ROOT).parts) & SKIP]
    if args.include_archive:
        paths += [p for p in (ROOT/'archive').rglob('*') if p.is_file()]
    paths = sorted(set(paths))
    errors, links = [], 0
    for path in paths:
        if path.suffix == '.py' and 'archive' not in path.parts:
            ast.parse(path.read_text(), filename=str(path))
        if path.suffix == '.json':
            json.loads(path.read_text())
        if path.suffix == '.toml' or path.name == 'uv.lock':
            tomllib.loads(path.read_text())
        inspect_file(path, errors, denied)
        if path.suffix == '.md' and 'archive' not in path.parts:
            for target in re.findall(r'\]\(([^\n)]+)\)', path.read_text()):
                target = target.strip('<>').split(' "')[0]
                if urllib.parse.urlsplit(target).scheme or target.startswith('#'):
                    continue
                target = urllib.parse.unquote(target.split('#')[0])
                if target and not (path.parent/target).exists():
                    errors.append(f'{path.relative_to(ROOT)}: missing local link {target}')
                links += 1
    if errors:
        print('\n'.join(sorted(set(errors))))
        raise SystemExit(1)
    print(f'PASS: {len(paths)} public files; syntax, metadata, {links} local links and publication boundaries')
    if not args.static_only:
        for check in ('check_transport.py', 'check_mappings.py', 'check_public_inputs.py', 'check_restore_reference_data.py'):
            subprocess.run([sys.executable, '-B', str(ROOT/'tests'/check)], check=True, cwd=ROOT)

if __name__ == '__main__':
    main()

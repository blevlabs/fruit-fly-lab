"""Restore selected published study files without running models or downloading data.

Use --list to inspect the available study selections, then --study NAME to copy.
Huang's selected inputs are already versioned in data/research and are not restored.
Restoration preserves published bytes; it does not qualify a model reproduction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[1]
STUDIES = {
    'odor': ('m3/odor-reference',),
    'odor-dose': ('m3/odor-reference/temporal-dose/source-index',),
    'olftrans': ('m3/olftrans-reference',
        'publication-review/flybrainlab-sources/antenna-data.h5',
        'publication-review/flybrainlab-sources/olftrans-replay-boundary.json'),
    'bsg': ('m3/bsg-source-audit', 'm3/bsg-source-reference',
        'm3/olftrans-reference/sources'),
    'composed-odor': ('m3/composed-odor-reference', 'm3/bsg-source-audit',
        'm3/olftrans-reference'),
    'photoreceptor': ('m3/photoreceptor-reference',),
    'water': ('m3/water-reference', 'm3/sources/water2010.xml'),
    'crop': ('m2/internal-state',),
    'ms-wed': ('m4-m7/ms-wed-reference',),
}


def relative_path(value):
    if (not isinstance(value, str) or not value or '\\' in value
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError(f'Invalid archive path: {value!r}')
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError(f'Absolute archive path is not allowed: {value}')
    return path


def safe_path(root, relative):
    path = root
    parts = relative_path(str(relative)).parts
    for index, part in enumerate(parts):
        path = path / part
        if path.is_symlink():
            raise ValueError(f'Symlink is not allowed: {path.relative_to(root)}')
        if index < len(parts) - 1 and path.exists() and not path.is_dir():
            raise ValueError(f'Expected a directory: {path.relative_to(root)}')
    return path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_index(root):
    path = safe_path(root, 'data/scientific-archive.json')
    if not path.is_file():
        raise ValueError('Missing archive index: data/scientific-archive.json')
    index = json.loads(path.read_text())
    if not isinstance(index, dict):
        raise ValueError('Archive index must be a JSON object')
    if index.get('schema_version') != 1 or index.get('status') != 'READY_FOR_PUBLICATION':
        raise ValueError(f'Archive export is not ready: {index.get("status", "missing status")}')
    if not isinstance(index.get('entries'), list):
        raise ValueError('Archive index has no entries list')
    return index


def selection(index, studies):
    prefixes = {prefix for study in studies for prefix in STUDIES[study]}
    matched = set()
    files = {}
    unavailable = set()
    for entry in index['entries']:
        if not isinstance(entry, dict):
            raise ValueError('Archive index entry must be a JSON object')
        published = entry.get('published_path')
        path = relative_path(published or entry['source_path'])
        base = PurePosixPath('archive/program' if published else 'outputs/program')
        if not path.is_relative_to(base):
            continue
        relative = path.relative_to(base).as_posix()
        matches = {p for p in prefixes if relative == p or relative.startswith(p + '/')}
        if not matches:
            continue
        matched.update(matches)
        if not published:
            unavailable.add(relative)
            continue
        if entry.get('source_path') != 'outputs/program/' + relative:
            raise ValueError(f'Archive source/published path mismatch: {published}')
        sha = entry.get('published_sha256')
        size = entry.get('published_bytes')
        if (not isinstance(sha, str) or re.fullmatch(r'[0-9a-f]{64}', sha) is None
                or type(size) is not int or size < 0):
            raise ValueError(f'Missing published hash or size: {published}')
        record = (published, sha, size)
        if relative in files and files[relative] != record:
            raise ValueError(f'Conflicting archive entries: {relative}')
        files[relative] = record
    if prefixes - matched:
        raise ValueError('Study paths missing from archive index: ' + ', '.join(sorted(prefixes - matched)))
    return files, sorted(unavailable)


def restore(studies, root=ROOT):
    root = Path(root).resolve()
    files, unavailable = selection(load_index(root), studies)
    pending, existing = [], []
    # Validate the complete selection before creating any destination files.
    for relative, (published, sha, size) in sorted(files.items()):
        source = safe_path(root, published)
        target_relative = 'data/research/' + relative
        target = safe_path(root, target_relative)
        if not source.is_file():
            raise ValueError(f'Missing published source: {published}')
        if source.stat().st_size != size or digest(source) != sha:
            raise ValueError(f'Published source hash/size mismatch: {published}')
        if target.exists():
            if not target.is_file() or target.stat().st_size != size or digest(target) != sha:
                raise ValueError(f'Existing file differs; preserved without overwriting: {target_relative}')
            existing.append(target_relative)
        else:
            pending.append((published, target_relative, sha, size))
    copied = []
    for published, target_relative, sha, size in pending:
        source, target = safe_path(root, published), safe_path(root, target_relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        safe_path(root, target_relative)
        # A hard link publishes the verified temporary file without replacing a race winner.
        with tempfile.NamedTemporaryFile(dir=target.parent) as temporary:
            with source.open('rb') as stream:
                shutil.copyfileobj(stream, temporary)
            temporary.flush()
            if Path(temporary.name).stat().st_size != size or digest(Path(temporary.name)) != sha:
                raise ValueError(f'Source changed during copy: {published}')
            safe_path(root, target_relative)
            try:
                os.link(temporary.name, target)
            except FileExistsError:
                safe_path(root, target_relative)
                if not target.is_file() or target.stat().st_size != size or digest(target) != sha:
                    raise ValueError(f'Existing file differs; preserved without overwriting: {target_relative}')
                existing.append(target_relative)
            else:
                copied.append(target_relative)
    return dict(copied=copied, existing=existing, unavailable_references=unavailable)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument('--list', action='store_true', help='List indexed published files and unavailable references; copy nothing')
    command.add_argument('--study', action='append', choices=sorted(STUDIES), help='Restore one study; repeat to select several')
    args = parser.parse_args()
    try:
        if args.list:
            index = load_index(ROOT)
            for study in STUDIES:
                files, unavailable = selection(index, [study])
                print(f'{study}: {len(files)} indexed published files, {len(unavailable)} unavailable references')
        else:
            result = restore(args.study)
            print(f'Restored {len(result["copied"])} files; verified {len(result["existing"])} existing files.')
            for relative in result['unavailable_references']:
                print(f'Not published; not restored: {relative}')
            print('Published files only; restoration does not establish a runnable or validated model.')
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Restore failed: {error}\n')


if __name__ == '__main__':
    main()

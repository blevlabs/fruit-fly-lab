"""Fetch only explicitly selected public source files and verify their hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def fetch(item):
    target = ROOT / item['path']
    if not target.resolve().is_relative_to(ROOT.resolve()) or not item['url'].startswith(('https://', 'http://')):
        raise ValueError('Invalid manifest destination or URL')
    def digest(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    if target.exists():
        if digest(target) != item['sha256']:
            raise ValueError(f'Existing file differs from the manifest: {item["path"]}; preserve it before replacing')
        return 'already verified'
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        request = urllib.request.Request(item['url'], headers={'User-Agent': 'fruit-fly-lab/0.2 source-reproduction'})
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name+'.', suffix='.tmp', delete=False) as out:
            temporary = Path(out.name)
            with urllib.request.urlopen(request, timeout=60) as response:
                while chunk := response.read(1024*1024):
                    out.write(chunk)
        if digest(temporary) != item['sha256']:
            raise ValueError(f'Download hash differs from the pinned source: {item["path"]}')
        temporary.replace(target)
        return 'downloaded and verified'
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', help='Explicit dataset group to download')
    parser.add_argument('--list', action='store_true', help='List files/terms without downloading')
    args = parser.parse_args()
    files = json.loads((ROOT/'data/downloads.json').read_text())['files']
    if args.list or args.group is None:
        for item in files:
            print(f'{item["group"]}: {item["path"]} [{item["license"]}]')
        return
    selected = [item for item in files if item['group'] == args.group]
    if not selected:
        parser.error('Unknown group; use --list')
    for item in selected:
        print(f'{item["path"]}: {fetch(item)}', flush=True)

if __name__ == '__main__':
    main()

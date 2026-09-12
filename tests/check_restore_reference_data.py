"""Temporary-fixture checks; never touch the real archive or execute a model."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/restore_reference_data.py'
spec = importlib.util.spec_from_file_location('restore_reference_data', SCRIPT)
restore_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore_data)
PREFIX = 'm3/odor-reference/temporal-dose/source-index/'


def entry(name, payload=b'original scientific bytes\n', published=True):
    relative = PREFIX + name
    sha = hashlib.sha256(payload).hexdigest()
    return dict(source_path='outputs/program/' + relative,
        published_path='archive/program/' + relative if published else None,
        published_sha256=sha if published else None,
        published_bytes=len(payload) if published else None,
        original_sha256=sha, original_bytes=len(payload),
        status='exact_copy' if published else 'reference_only')


def fixture(root, entries, status='READY_FOR_PUBLICATION'):
    (root / 'data').mkdir(exist_ok=True)
    (root / 'data/scientific-archive.json').write_text(json.dumps(
        dict(schema_version=1, status=status, entries=entries)))
    for item in entries:
        if item['published_path']:
            source = root / item['published_path']
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b'original scientific bytes\n')


def rejects(call, message):
    try:
        call()
    except ValueError as error:
        assert message in str(error), str(error)
    else:
        raise AssertionError(f'Expected rejection containing {message!r}')


def main():
    item = entry('sample.csv')
    destination = 'data/research/' + PREFIX + 'sample.csv'
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        unavailable = entry('withheld.mat', published=False)
        fixture(root, [item, unavailable])
        # An excluded private original must never become a fallback source.
        private = root / unavailable['source_path']
        private.parent.mkdir(parents=True)
        private.write_bytes(b'private original; not published')
        result = restore_data.restore(['odor-dose', 'odor'], root)
        assert result['copied'] == [destination]
        assert result['unavailable_references'] == [PREFIX + 'withheld.mat']
        assert (root / destination).read_bytes() == b'original scientific bytes\n'
        assert not (root / 'data/research' / (PREFIX + 'withheld.mat')).exists()
        assert private.read_bytes() == b'private original; not published'
        again = restore_data.restore(['odor-dose'], root)
        assert again['copied'] == [] and again['existing'] == [destination]

    for fault, message in [('in_progress', 'not ready'), ('missing', 'Missing published source'),
                           ('corrupt', 'hash/size mismatch'), ('conflict', 'Existing file differs')]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other = entry('z-last.csv')
            fixture(root, [item, other], 'EXPORT_IN_PROGRESS' if fault == 'in_progress' else 'READY_FOR_PUBLICATION')
            source = root / other['published_path']
            if fault == 'missing':
                source.unlink()
            elif fault == 'corrupt':
                source.write_bytes(b'changed')
            elif fault == 'conflict':
                target = root / 'data/research' / (PREFIX + 'z-last.csv')
                target.parent.mkdir(parents=True)
                target.write_bytes(b'keep existing version')
            rejects(lambda: restore_data.restore(['odor-dose'], root), message)
            assert not (root / destination).exists(), 'Preflight copied an earlier file before failure'
            if fault == 'conflict':
                assert target.read_bytes() == b'keep existing version'

    for fault in ('source_file', 'source_directory', 'target_file', 'target_directory', 'index'):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root, external = Path(directory), Path(outside)
            fixture(root, [item])
            secret = external / 'outside.bin'
            secret.write_bytes(b'outside must remain untouched')
            source, target = root / item['published_path'], root / destination
            if fault == 'source_file':
                source.unlink()
                source.symlink_to(secret)
            elif fault == 'source_directory':
                source.unlink()
                source.parent.rmdir()
                source.parent.symlink_to(external, target_is_directory=True)
            elif fault == 'target_file':
                target.parent.mkdir(parents=True)
                target.symlink_to(secret)
            elif fault == 'target_directory':
                (root / 'data/research').symlink_to(external, target_is_directory=True)
            else:
                index = root / 'data/scientific-archive.json'
                index.unlink()
                index.symlink_to(secret)
            rejects(lambda: restore_data.restore(['odor-dose'], root), 'Symlink')
            assert secret.read_bytes() == b'outside must remain untouched'
            assert list(external.iterdir()) == [secret]

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fixture(root, [item])
        index = restore_data.load_index(root)
        rejects(lambda: restore_data.selection(index, ['crop']), 'missing from archive index')
        for unsafe in ('/outside', '../outside', 'archive/program/../../outside', 'archive\\outside'):
            rejects(lambda: restore_data.relative_path(unsafe), 'archive path')
        conflict = dict(item, published_sha256='0' * 64)
        rejects(lambda: restore_data.selection(dict(entries=[item, conflict]), ['odor-dose']), 'Conflicting archive entries')
        mismatched = dict(item, source_path='outputs/program/another-study/sample.csv')
        rejects(lambda: restore_data.selection(dict(entries=[mismatched]), ['odor-dose']), 'path mismatch')
        with patch.object(restore_data, 'ROOT', root), \
             patch.dict(restore_data.STUDIES, {'odor-dose': (PREFIX.rstrip('/'),)}, clear=True), \
             patch('sys.argv', [str(SCRIPT), '--list']), redirect_stdout(io.StringIO()) as output:
            restore_data.main()
        assert '1 indexed published files' in output.getvalue()
        assert not (root / 'data/research').exists(), '--list copied files'

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fixture(root, [item])
        def race_winner(source, target):
            target.write_bytes(b'concurrent existing version')
            raise FileExistsError(target)
        with patch.object(restore_data.os, 'link', side_effect=race_winner):
            rejects(lambda: restore_data.restore(['odor-dose'], root), 'Existing file differs')
        assert (root / destination).read_bytes() == b'concurrent existing version'
        assert sorted(p.name for p in (root / destination).parent.iterdir()) == ['sample.csv']
    print('PASS: explicit archive restore, hashes, preflight, no-overwrite, excluded originals and symlink rejection')


if __name__ == '__main__':
    main()

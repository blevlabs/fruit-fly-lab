"""Small file, codec and source-input checks; never advance a scientific model."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'runtime'), str(ROOT/'research')]
import checkpoint

def main():
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)/'state.npz'
        state = dict(clock=3, queue=(4, 8), array=np.arange(12).reshape(3, 4))
        checkpoint.save(target, state)
        restored = checkpoint.load(target)
        assert restored['clock'] == 3 and restored['queue'] == (4, 8)
        assert np.array_equal(restored['array'], state['array'])
        original = target.read_bytes()
        with patch.object(checkpoint.os, 'replace', side_effect=OSError('injected write failure')):
            try:
                checkpoint.save(target, dict(clock=4))
            except OSError:
                pass
            else:
                raise AssertionError('Injected write unexpectedly succeeded')
        assert target.read_bytes() == original

        spec = importlib.util.spec_from_file_location('fetch_data', ROOT/'scripts/fetch_data.py')
        downloader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(downloader)
        payload = b'known source bytes'
        item = dict(path='source.bin', url='https://example.org/source', sha256=hashlib.sha256(payload).hexdigest())
        with patch.object(downloader, 'ROOT', Path(temporary)):
            with patch.object(downloader.urllib.request, 'urlopen', return_value=io.BytesIO(payload)) as opened:
                assert downloader.fetch(item) == 'downloaded and verified'
                assert downloader.fetch(item) == 'already verified'
                assert opened.call_count == 1
            try:
                downloader.fetch(dict(item, path='../escape'))
            except ValueError:
                pass
            else:
                raise AssertionError('Download destination escaped the repository')
            (Path(temporary)/'source.bin').write_bytes(b'changed input')
            try:
                downloader.fetch(item)
            except ValueError:
                pass
            else:
                raise AssertionError('Existing changed input was accepted')

    tree = ast.parse((ROOT/'runtime/cns_live.py').read_text())
    names = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'SOURCE_FILES' for t in n.targets))
    assert all((ROOT/'runtime'/name).is_file() for name in names)
    parameters = json.loads((ROOT/'runtime/cns-model.json').read_text())
    assert parameters['timestep_s'] == 2.5e-6 and parameters['neural_timestep_s'] == 1e-4
    motors = json.loads((ROOT/'runtime/neural-motor/malecns-motor-map.json').read_text())['motors']
    assert len(motors) == len({row['bodyId'] for row in motors}) == 815
    assert sum(row['semantic_muscle_key'] is not None for row in motors) == 481
    spec = importlib.util.find_spec('flygym')
    assets = Path(spec.origin).parent/'assets'
    geometry = assets/'model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml'
    assert hashlib.sha256(geometry.read_bytes()).hexdigest() == '04f6070d6733940357be005ca72c02ba0d9455538ff018da70c74de7458e9531'
    assert (assets/'model/flybody/fruitfly.xml').is_file()

    # Read author arrays only. No conditioning, ODE, neural or physical run.
    try:
        import scipy.io
    except ImportError:
        pass
    else:
        import huang_reference as huang
        means, sems = huang.observations()
        assert np.isfinite(means).sum() == np.isfinite(sems).sum() == 86
        folder = ROOT/'data/research/m7/huang-reference/sources/generated-model-fitting'
        manifest = json.loads((folder/'manifest.json').read_text())
        count = 0
        for item in manifest['files']:
            path = folder/item['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
            modules = 2 if '_2modules_' in path.name else 3
            _, curves, _, _ = huang.original_curves(path, modules)
            count += curves.size
        assert count == 240
    print('PASS: atomic non-executable codec, verified data downloads, flat source inputs, motor map and original reference arrays')

if __name__ == '__main__':
    main()

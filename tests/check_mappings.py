"""Data-only public mapping checks. No model imports, simulation, or network access."""
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COUNTS = {
    'ORN_DM1': 74, 'ORN_DM2': 54, 'ORN_DM4': 32, 'ORN_VM2': 41, 'ORN_VA2': 83,
    'TRN_VP2': 7, 'TRN_VP3a': 6, 'contact_bitter': 38, 'contact_sugar': 34, 'contact_water': 17,
}


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(annotations=None):
    source = ROOT/'scripts/build_sensory_map.py'
    spec = importlib.util.spec_from_file_location('build_sensory_map', source)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    provenance = json.loads((ROOT/'data/sensory-map-provenance.json').read_text())
    mapping_path = ROOT/provenance['output']['path']
    optics_path = ROOT/provenance['optical_data']['path']
    assert sha256(mapping_path) == provenance['output']['sha256']
    assert sha256(optics_path) == provenance['optical_data']['sha256'] == builder.OPTICS_SHA256
    assert provenance['annotations']['sha256'] == builder.ANNOTATIONS_SHA256
    mapping = json.loads(mapping_path.read_text())
    optics = json.loads(optics_path.read_text())
    assert mapping['dataset'] == optics['dataset'] == 'male-cns:v1.0'
    assert mapping['license'] == optics['license'] == provenance['license'] == 'CC-BY-SA-4.0'
    assert not {'primary_taste_companion', 'flywire_type_crosswalk', 'runtime_snapshot', 'prepared_graph'} & set(mapping)
    assert 'coverage_id' not in mapping['neurons']['columns']
    assert mapping['neurons']['columns'] == builder.NEURON_COLUMNS
    rows = [dict(zip(mapping['neurons']['columns'], r)) for r in mapping['neurons']['rows']]
    ids = [r['bodyId'] for r in rows]
    assert len(ids) == len(set(ids)) == mapping['counts']['sensory_entries'] == 17937
    assert ids == sorted(ids)
    assert all('sensory' in r['superclass'] for r in rows)
    groups = {g['id']: g for g in mapping['input_groups']}
    assert set(groups) == set(EXPECTED_COUNTS)
    for name, count in EXPECTED_COUNTS.items():
        group = groups[name]
        expected = [r for r in rows if r['type'] in builder.GROUPS[name]]
        assert len(expected) == group['count'] == count
        assert list(group['body_ids_by_root_side']) == list(builder.SIDES)
        for side, values in group['body_ids_by_root_side'].items():
            assert values == [r['bodyId'] for r in expected if (r['rootSide'] or '<null>') == side]
    assert sum(len(groups[n]['body_ids_by_root_side'][side])
               for n in groups if n.startswith('ORN_') for side in ('L', 'R')) == 269
    assert [len(groups['contact_water']['body_ids_by_root_side'][s]) for s in ('L', 'R')] == [9, 8]
    visual = mapping['visual_columns']
    assert visual == optics['visual_columns']
    columns = visual['column_to_view_direction']['rows']
    assert len(columns) == 1696
    mapped = [r for r in columns if r['column'] is not None]
    assert len(mapped) == len({r['column'] for r in mapped}) == 1694
    assert all(r['side'] in ('L', 'R') for r in mapped)
    vectors = np.array([[r['x'], r['y'], r['z']] for r in mapped])
    assert np.isfinite(vectors).all()
    assert np.max(np.abs(np.linalg.norm(vectors, axis=1)-1)) < 1e-5
    table = visual['receptor_column_coverage']
    receptors = [dict(zip(table['columns'], r)) for r in table['rows']]
    assert len(receptors) == 6091
    wired = [r for r in receptors if r['view_direction_available']]
    assert len(wired) == len({r['bodyId'] for r in wired}) == 5713
    assert {r['bodyId'] for r in wired} <= set(ids)
    assert {r['column'] for r in wired} <= {r['column'] for r in mapped}
    if annotations is not None:
        rebuilt = builder.build(annotations, optics_path)
        assert builder.encode(rebuilt).encode() == mapping_path.read_bytes()
    print('PASS: source hashes, licensed data, 17937 sensory entries, ten exact type/side groups, 5713 optical IDs and direction norms'
          + ('; independent annotation rebuild is byte-identical' if annotations is not None else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annotations', type=Path, help='Also rebuild from the pinned local annotation Feather file')
    check(parser.parse_args().annotations)

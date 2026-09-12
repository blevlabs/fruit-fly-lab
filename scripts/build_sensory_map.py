"""Build the runtime sensory map from pinned, licensed local data. No simulation."""
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS_NAME = 'body-annotations-male-cns-v1.0-minconf-0.5.feather'
ANNOTATIONS_SHA256 = '2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2'
OPTICS_SHA256 = '697beb8b56a6795ad3213a7dcb55b4a875464be3c72a002e605d406ae3d05fe2'
NEURON_COLUMNS = [
    'bodyId', 'superclass', 'class', 'subclass', 'type', 'flywireType', 'mancType',
    'rootSide', 'somaSide', 'entryNerve', 'receptorType', 'status', 'statusLabel',
    'instance', 'synonyms', 'matchingNotes', 'mcnsSerial', 'mancSerial',
    'assignedOlHex1', 'assignedOlHex2',
]
GROUPS = {
    'ORN_DM1': ('ORN_DM1',), 'ORN_DM2': ('ORN_DM2',), 'ORN_DM4': ('ORN_DM4',),
    'ORN_VM2': ('ORN_VM2',), 'ORN_VA2': ('ORN_VA2',),
    'TRN_VP2': ('TRN_VP2',), 'TRN_VP3a': ('TRN_VP3a',),
    'contact_bitter': ('LB1a', 'LB1b', 'LB1c', 'LB1d'),
    'contact_sugar': ('LB3b', 'LB3c'), 'contact_water': ('LB3a',),
}
SIDES = ('L', 'R', 'unknown', '<null>')


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n'


def build(annotations, optics):
    import pandas as pd

    if sha256(annotations) != ANNOTATIONS_SHA256 or sha256(optics) != OPTICS_SHA256:
        raise ValueError('Input differs from the pinned annotations or optical data')
    raw = pd.read_feather(annotations, columns=NEURON_COLUMNS)
    neurons = raw[raw.superclass.str.contains('sensory', na=False)].sort_values('bodyId')
    if len(neurons) != 17937 or not neurons.bodyId.is_unique:
        raise ValueError('Unexpected sensory inventory')
    optical = json.loads(Path(optics).read_text())
    if optical['dataset'] != 'male-cns:v1.0' or optical['license'] != 'CC-BY-SA-4.0':
        raise ValueError('Unexpected optical dataset or license')
    groups = []
    for name, types in GROUPS.items():
        selected = neurons[neurons.type.isin(types)]
        sides = selected.rootSide.fillna('<null>')
        if not set(sides) <= set(SIDES):
            raise ValueError(f'Unrecognized root side in {name}')
        groups.append(dict(id=name, count=len(selected), selected_types=list(types),
            body_ids_by_root_side={side: selected[sides.eq(side)].bodyId.tolist() for side in SIDES},
            can_reuse_body_signal_after_id_join=name not in ('TRN_VP3a', 'contact_water')))
    return dict(schema_version=2, dataset='male-cns:v1.0', license='CC-BY-SA-4.0',
        attribution='MaleCNS collaborators (CC BY 4.0); Arthur Zhao / Reiser Lab optical data (CC BY-SA 4.0). See data/sensory-map-provenance.json.',
        counts=dict(sensory_entries=len(neurons)), input_groups=groups,
        neurons=dict(columns=NEURON_COLUMNS, rows=json.loads(neurons.to_json(orient='values'))),
        visual_columns=optical['visual_columns'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annotations', type=Path, default=ROOT/'data/raw/malecns'/ANNOTATIONS_NAME)
    parser.add_argument('--optics', type=Path, default=ROOT/'data/optical-map.json')
    parser.add_argument('--output', type=Path, default=ROOT/'runtime/neural-motor/malecns-sensory-map.json')
    args = parser.parse_args()
    mapping = build(args.annotations, args.optics)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encode(mapping))
    print(json.dumps(dict(output=str(args.output), sha256=sha256(args.output),
                         sensory_entries=mapping['counts']['sensory_entries'])))

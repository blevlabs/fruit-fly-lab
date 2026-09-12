"""Prepare the released MaleCNS neuronal graph, without selecting action circuits.

Run in the local backend environment. Raw segment edges remain auditable;
glia/unclassified fragments are not silently treated as biological neurons.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
from scipy.sparse import coo_matrix


ANNOTATIONS = 'body-annotations-male-cns-v1.0-minconf-0.5.feather'
TRANSMITTERS = 'body-neurotransmitters-male-cns-v1.0.feather'
BASE_URL = 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/'
# This is the lumped fast-current approximation used by the existing LIF model.
# It does not implement receptor-specific sign or neuromodulator biochemistry.
FAST_SIGN = {'acetylcholine': 1, 'glutamate': -1, 'gaba': -1, 'histamine': -1,
             'dopamine': 1, 'octopamine': 1, 'serotonin': 1}


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def map_edges(ids, pre, post, counts):
    """Return source/destination indices only where both IDs are included neurons."""
    if len(ids) == 0 or np.any(np.diff(ids) <= 0):
        raise ValueError('Neuron IDs must be nonempty, sorted and unique')
    if any(np.asarray(x).shape != np.asarray(pre).shape for x in (post, counts)):
        raise ValueError('Mismatched edge columns')
    if np.asarray(pre).ndim != 1 or np.any(counts <= 0):
        raise ValueError('Expected one-dimensional positive synapse counts')
    src, dst = np.searchsorted(ids, pre), np.searchsorted(ids, post)
    valid = (src < len(ids)) & (dst < len(ids))
    valid &= ids[np.minimum(src, len(ids) - 1)] == pre
    valid &= ids[np.minimum(dst, len(ids) - 1)] == post
    return src[valid].astype(np.int32), dst[valid].astype(np.int32), counts[valid].astype(np.int32)


def check():
    ids = np.array([10, 20, 40])
    src, dst, count = map_edges(ids, np.array([10, 99, 20, 40]),
                                np.array([20, 10, 40, 3]), np.array([2, 3, 4, 5]))
    assert src.tolist() == [0, 1] and dst.tolist() == [1, 2] and count.tolist() == [2, 4]
    # Matrix rows are postsynaptic targets; columns are presynaptic sources.
    matrix = coo_matrix((count, (dst, src)), shape=(3, 3)).tocsr()
    assert (matrix @ np.array([1, 0, 0])).tolist() == [0, 2, 0]
    assert (matrix @ np.array([0, 1, 0])).tolist() == [0, 0, 4]
    try:
        map_edges(ids, np.array([10]), np.array([20]), np.array([-1]))
    except ValueError:
        pass
    else:
        raise AssertionError('Negative structural weight accepted')


def prepare(raw, output):
    annotations = pd.read_feather(raw / ANNOTATIONS)
    transmitters = pd.read_feather(raw / TRANSMITTERS)
    if not annotations.bodyId.is_unique or not transmitters.body.is_unique:
        raise ValueError('Duplicate source identifiers')
    # Include every classified neuron plus traced neurons lacking a superclass.
    # Exclusion is based on reconstruction identity, never on response or behavior.
    keep = annotations.superclass.notna() | annotations.status.eq('Traced')
    neurons = annotations[keep].copy().sort_values('bodyId').reset_index(drop=True)
    if neurons.status.isin(['Glia', 'Unimportant']).any():
        raise ValueError('Neuron inclusion conflicts with a source non-neuronal label')
    neurons = neurons.merge(transmitters, left_on='bodyId', right_on='body', how='left', validate='one_to_one')
    ids = neurons.bodyId.to_numpy(dtype=np.int64)
    signs = neurons.consensus_nt.map(FAST_SIGN).fillna(0).to_numpy(dtype=np.float32)
    neurons['fast_current_sign'] = signs
    neurons['transmission_status'] = np.where(signs == 0, 'unresolved', 'lumped_LIF_estimate')
    output.mkdir(parents=True, exist_ok=True)
    neurons.to_feather(output / 'neurons.feather')
    annotations[~keep].reset_index(drop=True).to_feather(output / 'excluded-annotations.feather')
    sources, destinations, weights = [], [], []
    raw_edges = raw_synapses = kept_synapses = 0
    outgoing_unresolved_edges = outgoing_unresolved_synapses = 0
    path = raw / 'connectome-weights.feather'
    with pa.memory_map(str(path), 'r') as stream:
        reader = ipc.open_file(stream)
        for batch_index in range(reader.num_record_batches):
            batch = reader.get_batch(batch_index)
            pre = batch.column('body_pre').to_numpy()
            post = batch.column('body_post').to_numpy()
            count = batch.column('weight').to_numpy()
            raw_edges += len(count)
            raw_synapses += int(count.sum())
            src, dst, count = map_edges(ids, pre, post, count)
            kept_synapses += int(count.sum())
            unresolved = signs[src] == 0
            outgoing_unresolved_edges += int(unresolved.sum())
            outgoing_unresolved_synapses += int(count[unresolved].sum())
            sources.append(src); destinations.append(dst); weights.append(count)
            if batch_index % 400 == 0:
                print(f'Batches {batch_index}/{reader.num_record_batches}; raw edges {raw_edges:,}', flush=True)
    source = np.concatenate(sources)
    destination = np.concatenate(destinations)
    count = np.concatenate(weights)
    del sources, destinations, weights
    topology = coo_matrix((count, (destination, source)), shape=(len(ids), len(ids))).tocsr()
    topology.sum_duplicates(); topology.sort_indices()
    assert int(topology.data.sum()) == kept_synapses and topology.nnz == len(count)
    np.savez_compressed(output / 'connectome.npz', neuron_ids=ids, indptr=topology.indptr,
                        indices=topology.indices, synapse_count=topology.data,
                        fast_current_sign=signs)
    receipt = dict(dataset='male-cns:v1.0', source=BASE_URL,
        annotation_rows=len(annotations), neurons=len(neurons),
        neuron_inclusion='superclass present OR status Traced; no activity/behavior filter',
        excluded_annotation_status_counts=annotations[~keep].status.fillna('missing').value_counts().to_dict(),
        superclass_counts=neurons.superclass.fillna('unclassified_traced').value_counts().to_dict(),
        raw_segment_edge_rows=raw_edges, raw_segment_synapses=raw_synapses,
        neuronal_edge_rows=int(topology.nnz), neuronal_synapses=kept_synapses,
        excluded_segment_edge_rows=raw_edges - int(topology.nnz),
        unresolved_transmitter_neurons=int((signs == 0).sum()),
        unresolved_outgoing_edge_rows=outgoing_unresolved_edges,
        unresolved_outgoing_synapses=outgoing_unresolved_synapses,
        transmitter_counts=neurons.consensus_nt.fillna('missing').value_counts().to_dict(),
        matrix_orientation='row=postsynaptic, column=presynaptic',
        weights='Exact positive released synapse counts, unthresholded within neuronal subset',
        fast_current_assumptions=FAST_SIGN,
        unresolved_policy='Structural edges preserved; unresolved transmitter contributes no fast current. No invented transmitter.',
        limitations=['Structural import is not full physiological or whole-animal validation.',
                     'Lumped LIF signs are estimates; receptor-specific glutamate effects and aminergic biochemistry are not resolved.',
                     'Unknown peripheral receptors, muscles, and fragmented/unclassified segments remain explicit coverage gaps.'],
        source_sha256={name:sha256(raw/name) for name in (ANNOTATIONS,TRANSMITTERS,'connectome-weights.feather')},
        artifact_sha256={name:sha256(output/name) for name in ('neurons.feather','connectome.npz')})
    (output / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=Path(__file__).parent / '.cache/malecns-v1')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'malecns-v1')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    check()
    if not args.check:
        prepare(args.raw, args.output)

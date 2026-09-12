"""Isolated two-chemical Hallem-Carlson reference, with no runtime integration.

Outputs are signed, baseline- and diluent-corrected mean spikes/s in the first
500 ms. They are not absolute firing rates, Poisson inputs, or a continuous
transduction law. The source expressed individual Or genes in empty neurons.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/research/m3/odor-reference'
DATA = FOLDER / 'hallem2006-reference-data.json'
DATA_SHA256 = 'bdd1ad6b41289ed8a3f87ca8e2fc111dfccdb1fb1da0a1e9fa59349b4e43536e'


def reference_data():
    raw = DATA.read_bytes()
    if hashlib.sha256(raw).hexdigest() != DATA_SHA256:
        raise ValueError('The fixed odor reference data changed')
    return json.loads(raw)


def corrected_response(compound, *, exposed_sides=('L', 'R'), protocol=None):
    """Replay a measured chemical endpoint on supported, sided anatomical IDs.

    ``compound`` is an exact molecular name from the selected source pair;
    None is the solvent-corrected blank. Side exposure is an imposed isolated
    assay condition, not a simulated plume. No source label chooses an action.
    """
    data = reference_data()
    sides = tuple(exposed_sides)
    if len(sides) != len(set(sides)) or set(sides) - {'L', 'R'}:
        raise ValueError('Exposure sides must be unique L/R entries')
    if compound is not None and (type(compound) is not str or compound not in data['selected_compounds']):
        raise ValueError('Only the two measured compounds or the solvent blank are supported')
    if protocol is not None and protocol != data['reference_protocol']:
        raise NotImplementedError('Only the measured dilution, solvent, airflow and 500-ms protocol are supported')
    values = data['selected_response_delta_spikes_per_s'].get(compound, {})
    # ponytail: measured endpoints only; add dose/time transfer with measured data.
    return {body: values.get(receptor, 0.0) if side in sides else 0.0
            for receptor, binding in data['bindings'].items()
            for side, ids in binding['body_ids_by_root_side'].items() for body in ids}


def check():
    from scipy.io import loadmat

    data = reference_data()
    for relative, expected in data['source_sha256'].items():
        relative = relative.replace('outputs/program/', 'data/research/')
        if relative.startswith('neural-motor/'):
            relative = 'runtime/' + relative
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    source = loadmat(FOLDER / 'sources/flyResponsesWithNames.mat', simplify_cells=True)
    assert source['orNames'].tolist() == data['source_receptor_names']
    assert source['odorNames'].tolist() == data['source_odor_names']
    assert source['relRates'].shape == (110, 24)
    assert source['relRates'].tolist() == data['response_delta_spikes_per_s']
    assert source['bkgRates'].tolist() == data['background_mean_spikes_per_s']
    assert source['bkgStd'].tolist() == data['background_sd_spikes_per_s']

    mapping = json.loads((ROOT / 'runtime/neural-motor/malecns-sensory-map.json').read_text())
    rows = [dict(zip(mapping['neurons']['columns'], row)) for row in mapping['neurons']['rows']]
    all_ids, withheld = set(), set()
    for receptor, binding in data['bindings'].items():
        for side, ids in binding['body_ids_by_root_side'].items():
            expected = {r['bodyId'] for r in rows if r['type'] == binding['male_cns_type']
                        and r['class'] == 'olfactory' and r['entryNerve'] == 'AN' and r['rootSide'] == side}
            assert set(ids) == expected and not all_ids.intersection(ids)
            all_ids.update(ids)
        withheld.update(r['bodyId'] for r in binding['withheld'])
    assert len(all_ids) == 121 and len(withheld) == 6 and not all_ids.intersection(withheld)
    assert data['selected_response_delta_spikes_per_s'] == {
        'methyl acetate': {'Or22a': 54.0, 'Or43b': 21.833, 'Or59b': 269.0},
        'ethyl acetate': {'Or22a': 52.667, 'Or43b': 132.0, 'Or59b': 177.0}}

    trials = {}
    for compound in data['selected_compounds']:
        combined = corrected_response(compound)
        assert set(combined) == all_ids
        for side in ('L', 'R'):
            trial = corrected_response(compound, exposed_sides=(side,))
            exposed = {body for b in data['bindings'].values() for body in b['body_ids_by_root_side'][side]}
            assert {body for body, response in trial.items() if response != 0.0} == exposed
            assert all(trial[body] == combined[body] for body in exposed)
            trials[f'{compound}:{side}'] = trial
        assert corrected_response(compound, exposed_sides=('R', 'L')) == combined
        assert not any(corrected_response(compound, exposed_sides=()).values())
    assert not any(corrected_response(None).values())
    assert corrected_response('methyl acetate') == corrected_response('methyl acetate')
    # Compare receptor means, not totals inflated by anatomical population sizes.
    a, b = [data['selected_response_delta_spikes_per_s'][name] for name in data['selected_compounds']]
    determinant = a['Or43b'] * b['Or59b'] - a['Or59b'] * b['Or43b']
    assert determinant != 0.0  # Recorded profiles are not a common scalar mixture.
    rejected = []
    for compound, kwargs, error in [
            ('sweet', {}, ValueError), ('food_0', {}, ValueError), (False, {}, ValueError),
            ('methyl acetate', {'exposed_sides': ('unknown',)}, ValueError),
            ('methyl acetate', {'exposed_sides': ('L', 'L')}, ValueError),
            ('methyl acetate', {'protocol': {**data['reference_protocol'], 'liquid_dilution_fraction': .001}}, NotImplementedError),
            ('methyl acetate', {'protocol': {**data['reference_protocol'], 'odor_pulse_s': 1.0}}, NotImplementedError),
            ('methyl acetate', {'protocol': {**data['reference_protocol'], 'solvent': 'water'}}, NotImplementedError),
            ('methyl acetate', {'display_color': 'red'}, TypeError),
            ('methyl acetate', {'gas_concentration_mol_m3': .001}, TypeError)]:
        try:
            corrected_response(compound, **kwargs)
        except error:
            rejected.append(error.__name__)
        else:
            raise AssertionError('Unsupported exposure accepted')
    negative_entries = sum(value < 0 for row in data['response_delta_spikes_per_s'] for value in row)
    assert negative_entries > 0  # Original signed observations were not clipped.
    return {
        'claim': 'two measured chemical response patterns at one reference protocol; no natural odor encoder',
        'reference_protocol': data['reference_protocol'],
        'source_preparation': data['source_genotype'],
        'matched_nuisances': data['matched_nuisances'],
        'unmatched_or_unmeasured': data['unmatched_or_unmeasured'],
        'receptor_mean_delta_spikes_per_s': data['selected_response_delta_spikes_per_s'],
        'source_replicate_counts_caption_derived': data['selected_replicate_counts'],
        'source_background_statistics_not_odor_noise': {
            receptor: {'mean_spikes_per_s': data['background_mean_spikes_per_s'][data['source_receptor_names'].index(receptor)],
                       'sd_spikes_per_s': data['background_sd_spikes_per_s'][data['source_receptor_names'].index(receptor)]}
            for receptor in data['selected_receptors']},
        'bindings': data['bindings'], 'sided_anatomical_ids': 121, 'withheld_unknown_side_ids': sorted(withheld),
        'single_side_trials_delta_spikes_per_s': trials,
        'recorded_profile_noncollinearity_determinant_Hz_squared': determinant,
        'source_negative_entries_preserved': negative_entries,
        'domain_rejections': rejected,
        'calibration_replay': 'PASS exact source means; no response gain, clipping, normalization or dose fitting',
        'holdout': 'NOT_RUN: unused compounds are retained data, not predictions from a model; no prospective biological holdout',
        'untouched_controls': 'solvent-subtracted blank stays zero; source baseline statistics and signed matrix retained; runtime, maps, arena and individual state unchanged',
        'implementation': 'PASS source bytes, exact joins, chemistry/side separation and domain checks',
        'numerical': 'PASS table orientation, unrounded values and stateless replay; no numerical integration claimed',
        'biological_validation': 'OPEN empty-neuron to native-cell transfer, absolute rate, gas concentration, kinetics and independent prediction',
        'capability': 'NOT_DEMONSTRATED: no CNS discrimination, memory, behavior or natural plume trial',
        'M3_full_gate': 'OPEN',
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (DATA, Path(__file__), FOLDER / 'source-audit/hallem-carlson-2006-primary-source-audit.json')}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/odor-reference/reference-check.json')
    args = parser.parse_args()
    result = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(args.output), 'implementation': 'PASS', 'numerical': 'PASS',
                      'biological_validation': 'OPEN', 'M3_full_gate': 'OPEN'}))

"""Isolated LB3a water endpoint reference; never imported by the fly runtime.

Cameron et al. 2010, doi:10.1038/nature09011, counted labellar spikes in the
first second after contact with water containing 1 mM KCl recording carrier.
The control mean was 12.0 spikes (SEM 0.9). This is not an instantaneous rate,
a dose curve, a spike train, or a measured response of each MaleCNS cell.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'runtime/neural-motor/malecns-sensory-map.json'
SOURCE = ROOT / 'data/research/m3/sources/water2010.xml'
SOURCE_AUDIT = ROOT / 'data/research/m3/water-reference/sources/cameron2010-source-audit.json'
SOURCE_SHA256 = '6361b49d3e4df7df9de7ad76852174bcf66bf9dd1c631f8627e1bbdebe50d535'
MEAN_FIRST_SECOND_SPIKES = 12.0
SEM_FIRST_SECOND_SPIKES = 0.9


def lb3a_ids():
    """Use the existing primary-source group, with raw type/side cross-checks."""
    mapping = json.loads(MAP.read_text())
    group = next(g for g in mapping['input_groups'] if g['id'] == 'contact_water')
    sides = group['body_ids_by_root_side']
    rows = [dict(zip(mapping['neurons']['columns'], row)) for row in mapping['neurons']['rows']]
    if (mapping['dataset'] != 'male-cns:v1.0' or group['count'] != 17
            or len(sides['L']) != 9 or len(sides['R']) != 8
            or any(ids for side, ids in sides.items() if side not in ('L', 'R'))):
        raise ValueError('Expected the primary 17-cell LB3a correspondence')
    ids = sides['L'] + sides['R']
    if len(set(ids)) != 17 or set(ids) != {r['bodyId'] for r in rows if r['type'] == 'LB3a'}:
        raise ValueError('LB3a group does not match exact annotated IDs')
    for side in ('L', 'R'):
        if any(r['rootSide'] != side or r['class'] != 'gustatory'
               for r in rows if r['bodyId'] in sides[side]):
            raise ValueError('LB3a side or modality conflict')
    return {side: tuple(sides[side]) for side in ('L', 'R')}


def first_second_counts(aqueous_contacts, *, added_osmolarity_mOsm_L=0.0,
                        carrier_kcl_mM=1.0, observation_window_s=1.0):
    """Reference mean counts for explicitly contacted sensilla, identified by ID.

    The assay applies one solution to the specified individual receptors.
    Added osmolarity is ABOVE the 1 mM KCl carrier; its absolute osmolality was
    not measured in the source. Empty contact contributes zero external input,
    without asserting that an uncontacted neuron has zero spontaneous firing.
    Whole-labella or per-cell physiological equality is not inferred here.
    """
    ids = {body for values in lb3a_ids().values() for body in values}
    contacts = tuple(aqueous_contacts)
    if (any(type(body) is not int for body in contacts)
            or len(contacts) != len(set(contacts)) or not set(contacts) <= ids):
        raise ValueError('Contacts must be unique exact LB3a integer body IDs')
    values = (added_osmolarity_mOsm_L, carrier_kcl_mM, observation_window_s)
    if any(type(value) not in (float, int) or not math.isfinite(value) for value in values):
        raise ValueError('Expected finite numerical concentration and time values')
    if added_osmolarity_mOsm_L < 0 or carrier_kcl_mM < 0 or observation_window_s <= 0:
        raise ValueError('Concentrations must be nonnegative and the window positive')
    # ponytail: one measured endpoint; add kinetics/doses only with native spike data.
    if carrier_kcl_mM != 1.0 or observation_window_s != 1.0:
        raise NotImplementedError('Only the 1 mM KCl, first-one-second preparation is supported')
    if contacts and added_osmolarity_mOsm_L != 0.0:
        raise NotImplementedError('No quantitative native water-cell spike/osmolarity curve is available here')
    return {body: MEAN_FIRST_SECOND_SPIKES if body in contacts else 0.0 for body in sorted(ids)}


def check():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert MEAN_FIRST_SECOND_SPIKES == 12.0 and SEM_FIRST_SECOND_SPIKES == 0.9
    sides = lb3a_ids()
    dry = first_second_counts(())
    left = first_second_counts(sides['L'])
    right = first_second_counts(sides['R'])
    both = first_second_counts(sides['L'] + sides['R'])
    assert len(dry) == 17 and not any(dry.values())
    assert {body for body, count in left.items() if count > 0} == set(sides['L'])
    assert {body for body, count in right.items() if count > 0} == set(sides['R'])
    assert all(count == MEAN_FIRST_SECOND_SPIKES for count in both.values())
    assert first_second_counts((sides['L'][0],))[sides['L'][1]] == 0.0
    assert first_second_counts(reversed(sides['L'])) == left
    assert first_second_counts(()) == dry and first_second_counts(sides['L']) == left
    assert first_second_counts((), added_osmolarity_mOsm_L=1000.0) == dry
    rejected = []
    cases = [((999999999999,), {}, ValueError),
             ((sides['L'][0], sides['L'][0]), {}, ValueError),
             ((True,), {}, ValueError),
             (sides['L'], {'added_osmolarity_mOsm_L': -1}, ValueError),
             (sides['L'], {'added_osmolarity_mOsm_L': math.nan}, ValueError),
             (sides['L'], {'added_osmolarity_mOsm_L': '0'}, ValueError),
             (sides['L'], {'added_osmolarity_mOsm_L': 100}, NotImplementedError),
             (sides['L'], {'carrier_kcl_mM': 0}, NotImplementedError),
             (sides['L'], {'observation_window_s': 0.1}, NotImplementedError),
             (sides['L'], {'observation_window_s': 2.0}, NotImplementedError),
             (sides['L'], {'display_color': 'sweet'}, TypeError),
             (sides['L'], {'timestep_s': 0.0001}, TypeError)]
    for contacts, kwargs, expected in cases:
        try:
            first_second_counts(contacts, **kwargs)
        except expected:
            rejected.append({'arguments': {k: repr(v) for k, v in kwargs.items()},
                             'expected_error': expected.__name__})
        else:
            raise AssertionError(f'Unsupported assay accepted: {kwargs}')
    return {
        'claim': 'isolated first-second water endpoint reference, no dynamic encoder or runtime wiring',
        'source_doi': '10.1038/nature09011',
        'preparation': {'organ': 'adult labellar l-type bristle tip recording',
                        'source_stated_age_days': [2, 3], 'fresh_medium_before_recording_days': 1,
                        'age_reference': '2-3-day-old flies transferred to fresh medium one day before experiment; exact recording age not separately stated',
                        'recording_sex': 'not stated for Figure 2a/b',
                        'recording_sample_count': None,
                        'genotype': 'Figure 2a/b ppk28 control; full genotype not separately stated for this recording panel',
                        'carrier_kcl_mM': 1.0, 'observation_window_s': 1.0,
                        'measured_absolute_osmolarity_mOsm_L': None,
                        'reference_added_solute_osmolarity_mOsm_L': 0.0},
        'calibration_replay_not_holdout': {'mean_first_second_spikes': MEAN_FIRST_SECOND_SPIKES,
                                         'sem_first_second_spikes': SEM_FIRST_SECOND_SPIKES,
                                         'maximum_absolute_replay_error_spikes': 0.0,
                                         'sem_is_not_single_neuron_noise': True,
                                         'replication_unit': 'recorded sensillum; number of recorded sensilla not recovered',
                                         'anatomical_ids_are_not_experimental_replicates': True,
                                         'sum_across_ids_is_not_source_recording_mean': True},
        'exact_ids_by_root_side': sides,
        'identity_transfer': 'ppk28-matched LB3a group from primary taste companion; no per-cell physiological equality validated',
        'assay_outputs_mean_count_equivalents': {'no_contact': dry, 'left_only': left,
                                                'right_only': right, 'both_sides': both},
        'held_out_from_parameter_choice': {
            'ppk28_null_mean_first_second_spikes': 0.8, 'ppk28_null_sem': 0.1,
            'rescue_mean_first_second_spikes': 6.4, 'rescue_sem': 1.0,
            'native_dose_direction': 'added solutes suppress water-cell response',
            'status': 'NOT_EXECUTABLE: channel deletion/rescue and quantitative dose/kinetic law are not implemented',
            'prospective_holdout': False},
        'domain_rejections': rejected,
        'implementation': 'PASS exact IDs, source hash, contact direction, side/individual isolation and domain rejection',
        'numerical': 'PASS exact stateless endpoint replay; no time integrator, step-size or adaptation claim',
        'biological_validation': 'OPEN: mean endpoint reused; no independent prediction or per-cell validation',
        'demonstrated_capability': 'NONE', 'M3_full_gate': 'OPEN',
        'missing_data': ['native identified-cell spike counts across added osmolarity, including actual solution osmolarity',
                         'within-first-second and sustained response timing, adaptation/recovery, and spontaneous activity',
                         'individual sensillum mapping and transfer from source l-type bristles to MaleCNS LB3a cells',
                         'replicate-level data and prespecified biological comparison margins'],
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (MAP, SOURCE, SOURCE_AUDIT, Path(__file__))}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'runs/water-reference/reference-check.json')
    args = parser.parse_args()
    result = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(args.output), 'implementation': 'PASS', 'numerical': 'PASS',
                      'biological_validation': 'OPEN', 'M3_full_gate': 'OPEN'}))

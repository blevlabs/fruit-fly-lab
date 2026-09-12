"""Exact observed Hallem-Carlson dose/time references; no interpolation or fly run.

S2 and S3/S4 are kept separate: the source does not establish identical diluent
correction or trial correspondence. Responses are signed source statistics,
never absolute spike rates. Temporal values average 500-ms bins after a single
500-ms pulse; each queried point must exist in the recovered original tables.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/research/m3/odor-reference/temporal-dose'
HASHES = {
    'canonical-dose-series.csv': 'a7d5e51e1dc069222949cc005a3ba958475ec8cd08ed1a5ed41d50f2ecd49315',
    'canonical-time-series.csv': '2bddc2315cf21df1d2202c3dc6b815d1c4f0c89c371b421401126962686e5269'}


def source_rows(name):
    raw = (FOLDER / 'source-index' / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != HASHES[name]:
        raise ValueError('Verified source values changed')
    return list(csv.DictReader(io.StringIO(raw.decode())))


def observed_response(odor, dilution_log10, *, bin_start_s=None):
    """Query S2 with no bin, or S3/S4 with an exact bin; None dilution is undiluted fruit."""
    if type(odor) is not str:
        raise ValueError('Expected an exact source stimulus name')
    for value in (dilution_log10, bin_start_s):
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
            raise ValueError('Expected finite numerical dilution/bin, or None')
    name = 'canonical-dose-series.csv' if bin_start_s is None else 'canonical-time-series.csv'
    rows = source_rows(name)
    values = {}
    for row in rows:
        dilution = int(row['dilution_log10']) if row['dilution_log10'] else None
        if (row['odor'] == odor and dilution == dilution_log10
                and (bin_start_s is None or float(row['bin_start_seconds']) == bin_start_s)):
            if row['receptor'] in values:
                raise ValueError('Duplicate source response')
            values[row['receptor']] = float(row['reported_response_spikes_per_second'])
    # ponytail: measured points only; additional doses/times require observations.
    if len(values) != 24:
        raise NotImplementedError('No complete measured receptor panel at this exact dose/bin')
    return values


def check():
    dose, time = [source_rows(name) for name in HASHES]
    assert len(dose) == 1824 and len(time) == 768
    assert len({(r['odor'], r['dilution_log10'], r['receptor']) for r in dose}) == 1824
    assert len({(r['odor'], r['dilution_log10'], r['receptor'], r['bin_start_seconds']) for r in time}) == 768
    assert all(r['original_table'] == 'S2' and r['n'] == '6' and float(r['response_window_seconds']) == .5 for r in dose)
    assert all(r['original_table'] in ('S3', 'S4') and r['n'] == '6'
               and float(r['bin_end_seconds']) - float(r['bin_start_seconds']) == .5
               and float(r['odor_pulse_seconds']) == .5 for r in time)
    for row in dose:
        dilution = int(row['dilution_log10']) if row['dilution_log10'] else None
        assert observed_response(row['odor'], dilution)[row['receptor']] == float(row['reported_response_spikes_per_second'])
    for row in time:
        assert observed_response(row['odor'], int(row['dilution_log10']),
                                 bin_start_s=float(row['bin_start_seconds']))[row['receptor']] == float(row['reported_response_spikes_per_second'])
    receptors = ('Or22a', 'Or43b', 'Or59b')
    dose_profiles = {str(d): {r: observed_response('ethyl acetate', d)[r] for r in receptors}
                     for d in (-2, -4, -6, -8)}
    assert [dose_profiles[str(d)]['Or22a'] for d in (-2, -4, -6, -8)] == [53., 18., 2., -3.]
    traces = {odor: {str(d): {r: [observed_response(odor, d, bin_start_s=t)[r]
                                  for t in (0., .5, 1., 1.5)] for r in receptors}
                     for d in (-2, -4)} for odor in ('pentyl acetate', '2-heptanone')}
    assert traces['pentyl acetate']['-2']['Or22a'] == [156., 51., 46., 40.]
    assert traces['2-heptanone']['-2']['Or22a'] == [109., 21.33, 8., 5.]
    assert traces['pentyl acetate']['-2']['Or43b'][-1] == -.67
    assert observed_response('pentyl acetate', -2)['Or22a'] == 158. != traces['pentyl acetate']['-2']['Or22a'][0]
    rejected = []
    for odor, dilution, start, error in [
            ('methyl acetate', -2, None, NotImplementedError),
            ('ethyl acetate', -2, 0., NotImplementedError),
            ('pentyl acetate', -3, None, NotImplementedError),
            ('pentyl acetate', -2, .25, NotImplementedError),
            ('pentyl acetate', -2, 2., NotImplementedError),
            ('food_0', -2, None, NotImplementedError),
            ('pentyl acetate', math.nan, None, ValueError),
            ('pentyl acetate', -2, True, ValueError)]:
        try:
            observed_response(odor, dilution, bin_start_s=start)
        except error:
            rejected.append({'odor': odor, 'dilution': repr(dilution), 'bin_start_s': repr(start),
                             'exception': error.__name__})
        else:
            raise AssertionError('Unmeasured condition was interpolated or accepted')
    assert observed_response('pentyl acetate', -2, bin_start_s=.5) == observed_response('pentyl acetate', -2, bin_start_s=.5)
    return {
        'claim': 'exact dose/time table queries with independent source-table boundaries',
        'implementation': 'PASS 2592 exact observed values, signed responses and unsupported-condition rejection',
        'numerical': 'PASS table lookup/replay; no numerical integration or continuous kinetics claim',
        'biological_validation': 'OPEN empty-neuron transfer, absolute rate/correction and independent prediction',
        'capability': 'NOT_TESTED', 'M3_full_gate': 'OPEN',
        'dose_observations': 1824, 'temporal_observations': 768,
        'replayed_values': 2592, 'bin_start_times_s': [0., .5, 1., 1.5],
        'time_bin_width_s': .5, 'odor_pulse_s': .5,
        'ethyl_acetate_S2_current_receptors': dose_profiles,
        'pentyl_acetate_and_2_heptanone_S3_S4_current_receptors': traces,
        'correction_boundary': 'S2 includes baseline/diluent correction; S3/S4 extra diluent correction is not restated. The tables are not pooled.',
        'existing_pair_boundary': 'Ethyl acetate has S2 doses; methyl acetate has no S2 dose series. Neither has S3/S4 time bins.',
        'unmeasured_conditions_rejected': rejected,
        'fitting_or_interpolation': False, 'runtime_or_mapping_changes': False,
        'remaining_data': ['raw trials and response variability', 'per-table correction and trial matching',
                           'numerical trajectories for pulse durations shown graphically in Figure S4 but absent from these tables',
                           'gas concentration and native MaleCNS receptor physiology'],
        'additional_graphical_source': 'Supplement Figure S4 depicts 100ms, 500ms, 1s and 5s pulses with SEM, n=6. Its 100ms response uses first bins of100ms and400ms. These graph-only values were not digitized or substituted into the tabulated reference.',
        'source_sha256': {str((FOLDER / 'source-index' / name).relative_to(ROOT)): value for name, value in HASHES.items()},
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=FOLDER / 'exact-dose-time-check.json')
    args = parser.parse_args()
    result = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(args.output), 'replayed_values': 2592, 'implementation': 'PASS',
                      'numerical': 'PASS', 'biological_validation': 'OPEN', 'M3_full_gate': 'OPEN'}))

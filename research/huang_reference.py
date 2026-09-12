"""Isolated Huang/Luo reduced rate-model reference; never imported by fly runtime.

Python translation of the original MATLAB bout recurrence and protocol packing,
copyright (C) 2024 Junjie Luo, Cheng Huang, Mark J. Schnitzer.
SPDX-License-Identifier: GPL-3.0-or-later
This derivative is free software under GNU GPL v3 or later, WITHOUT ANY WARRANTY,
including MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. Full license:
LICENSE
Source correspondence and limits: docs/research/m7-huang-reference.md.

Run: ./fly huang --check
Retain results: ./fly huang --output runs/huang-reference
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import scipy
from scipy.io import loadmat, whosmat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/research/publication-review/huang-luo-sources'
OUTPUT = ROOT / 'data/research/m7/huang-reference'
BASELINE = np.array([0., 0., 0., 35.2, 9., 11.2])
MAX_MBON = BASELINE[3:] + [36.46, 8.9, 19.96]
PUNISHMENT = np.array([27.85, 0., 11.38, 0., 0., 0.])
CELLS = ['PPL1-gamma1pedc', "PPL1-alpha'2alpha2", 'PPL1-alpha3',
         'MBON-gamma1pedc', 'MBON-alpha2sc', 'MBON-alpha3']
STAGES = ['pre-training', 'after 3x', 'after 6x', '1 h', '3 h', '24 h']


def parameters(path):
    """parameter_vec2mat.m: MATLAB logical assignment is column-major."""
    data = loadmat(path)
    vector, offset, result = data['para_mu'].ravel(), 0, []
    for bounds in data['mat_lu_cell'].ravel():
        lower, upper = bounds[..., 0], bounds[..., 1]
        mask = (lower != upper).ravel(order='F')
        values = lower.ravel(order='F').copy()
        count = int(mask.sum())
        values[mask] = vector[offset:offset + count]
        result.append(values.reshape(lower.shape, order='F'))
        offset += count
    assert offset == len(vector) and all(np.isfinite(p).all() for p in result)
    return result


def protocol(kind='figure5c'):
    """Original experimental_condition.m defaults plus the named script edits."""
    if kind not in {'figure5c', 'fitting'}:
        raise ValueError('Only the two preserved original protocols are supported')
    rests = ([3600 - 250 - 300, 7200 - 250, 75600 - 250] if kind == 'figure5c'
             else [3600, 7200 - 250, 75600 - 500])
    schedule, rest_index = [], 0
    for session in ['imaging', 'training', 'imaging', 'training', 'imaging',
                    'rest', 'imaging', 'rest', 'imaging', 'rest', 'imaging']:
        if session == 'rest':
            schedule.append(dict(name=session, duration_s=rests[rest_index],
                                 odor=[0., 0.], punishment=0., imaging=0))
            rest_index += 1
            continue
        duration, isi, repetitions = (30., 135., 3) if session == 'training' else (5., 120., 1)
        for _ in range(repetitions):
            for odor, length, imaging, shock in [([1., 0.], duration, 1, 1.),
                    ([0., 0.], isi, 0, 0.), ([0., 1.], duration, 2, 0.),
                    ([0., 0.], isi, 0, 0.)]:
                schedule.append(dict(name=session, duration_s=length, odor=odor,
                    punishment=shock if session == 'training' else 0.,
                    imaging=imaging if session == 'imaging' else 0))
    if kind == 'figure5c':
        for index in [3, 15, 19, 31]:
            schedule[index]['duration_s'] = 300.
    return schedule


def responses(kc, shock, weights, recurrent):
    """Source solve_DAN_MBON: keep its untransposed initial solve and 10 updates."""
    drive = weights.T @ kc + PUNISHMENT * shock
    response = np.linalg.solve(np.eye(6) - recurrent, drive)
    for _ in range(10):
        response = drive + BASELINE + recurrent.T @ response
        response[3:] = np.clip(response[3:], 0., MAX_MBON)
        response -= BASELINE
    return response


def simulate(params, schedule, frozen=False):
    """Dx_steady_state_MBON_0301_2023.m; values are changes from baseline, Hz."""
    weights = np.repeat(params[0], 2, axis=0)
    if weights.shape != (2, 6):
        raise ValueError('Select one of the original odor-pair parameter sets')
    initial = weights.copy()
    fw0, fw_dt = params[1].item(), params[2][0, 0]
    recurrent, decay, recovery = params[3], params[4].ravel(), params[5].item()
    if np.any(decay <= 0) or recovery <= 0:
        raise ValueError('Time constants must be positive')
    odor_state, change = np.ones(2), np.zeros((2, 3))
    last_training = max(i for i, s in enumerate(schedule) if s['name'] == 'training')
    image_count = sum(s['imaging'] == 1 for s in schedule)
    images = np.zeros((6, 2, image_count))
    image_index, after_training_s, elapsed_s = 0, 0., 0.
    trace = []
    for index, stage in enumerate(schedule):
        duration, odor = stage['duration_s'], np.asarray(stage['odor'])
        if duration < 0 or not np.isfinite(duration) or not np.isfinite(odor).all():
            raise ValueError('Invalid bout duration or odor input')
        end = 1. - (1. - odor_state * np.exp(-.05 * duration * odor)) * np.exp(-duration / recovery)
        kc = .5 * (odor_state + end) * odor
        odor_state = end
        current = responses(kc, stage['punishment'], weights, recurrent)
        if not frozen:
            dan_odor = weights[:, :3].T @ kc + recurrent[3:, :3].T @ current[3:]
            change += np.outer(kc, (fw0 * dan_odor + fw_dt * PUNISHMENT[:3] * stage['punishment']) * duration / 90.)
        if index > last_training:
            after_training_s += duration
        # Original 3-hour regime boundary is measured after the LAST training ISI.
        before = duration if after_training_s <= 10800 else max(0., 10800 - (after_training_s - duration))
        change *= np.exp(-before / decay[[0, 1, 1]] - (duration - before) / decay[[0, 2, 2]])
        weights = initial + np.column_stack([np.zeros((2, 3)), change])
        if stage['imaging']:
            images[:, stage['imaging'] - 1, image_index] = current
            image_index += stage['imaging'] == 2
        # The response precedes this bout's weight update in the MATLAB source.
        pre_weights = initial if not trace else np.asarray(trace[-1]['weights_after'])
        fixed_point = pre_weights.T @ kc + PUNISHMENT * stage['punishment'] + BASELINE + recurrent.T @ current
        fixed_point[3:] = np.clip(fixed_point[3:], 0., MAX_MBON)
        elapsed_s += duration
        trace.append(dict(end_s=elapsed_s, odor_adaptation_after=end.tolist(), kc_mean=kc.tolist(),
                          response_delta_hz=current.tolist(), weights_after=weights.tolist(),
                          fixed_point_residual_hz=float(np.max(np.abs(fixed_point - BASELINE - current)))))
    return images, trace


def controls(schedule, condition):
    result = []
    for index, stage in enumerate(schedule):
        item = {**stage, 'odor': list(stage['odor'])}
        if condition == 'odor_only':
            item['punishment'] = 0.
        elif condition == 'shock_only':
            item['odor'] = [0., 0.]
        elif condition == 'shifted' and index and schedule[index - 1]['punishment']:
            # ponytail: bout-level nonoverlap control; no arbitrary millisecond STDP claim.
            result[-1]['punishment'] = 0.
            shock_duration = result[-1]['duration_s']
            result.append({**item, 'duration_s': item['duration_s'] - shock_duration})
            item = {**item, 'duration_s': shock_duration, 'punishment': 1.}
        result.append(item)
    return result


def observations():
    """Read fixed numeric source cells directly; missing observations remain NaN."""
    path = SOURCE / 'upstream-model/data_and_parameters/Imaging_24hr_data.xlsx'
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    means, sems = [], []
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        assert [s.attrib['name'] for s in workbook.findall('s:sheets/s:sheet', ns)] == ['ACVvsETA', 'OCTvsBEN']
        for number in [1, 2]:
            tree = ET.fromstring(archive.read(f'xl/worksheets/sheet{number}.xml'))
            cells = {c.attrib['r']: float(c.find('s:v', ns).text) for c in tree.findall('.//s:c', ns)
                     if c.attrib.get('t', 'n') == 'n' and c.find('s:v', ns) is not None}
            for dest, offset in [(means, 2), (sems, 3)]:
                dest.append(np.array([[[cells.get(f'{col}{row}', np.nan) for col in columns]
                    for columns in ['CDEFGH', 'KLMNOP']] for row in range(offset, 19, 3)]))
    return np.stack(means, axis=-1), np.stack(sems, axis=-1)


def original_curves(path, modules):
    """Read published MATLAB graphics objects, not predictions generated by this port."""
    figure = loadmat(path, simplify_cells=True)['hgS_070000']
    axes = [a for a in figure['children'] if a['type'] == 'axes']
    indices = [0, 2, 3, 5] if modules == 2 else list(range(6))
    assert len(axes) == len(indices)
    lines, means, sems = [], [], []
    for axis in axes:
        fits = [c['properties'] for c in axis['children'] if c['type'] == 'graph2d.lineseries']
        data = [c['properties'] for c in axis['children'] if c['type'] == 'specgraph.errorbarseries']
        assert len(fits) == len(data) == 2
        for pair in [fits, data]:
            for props, color in zip(pair, [[1, 0, 0], [0, 0, 1]]):
                np.testing.assert_array_equal(props['Color'], color)
                np.testing.assert_array_equal(props['XData'], np.arange(1, 7))
        for props in data:
            np.testing.assert_allclose(props['LData'], props['UData'], rtol=0, atol=0)
        lines.append([p['YData'] for p in fits])
        means.append([p['YData'] for p in data])
        sems.append([p['LData'] for p in data])
    return indices, np.array(lines), np.array(means), np.array(sems)


def run():
    started = time.perf_counter()
    source_hashes = {}
    for folder, path_key in [(SOURCE, 'path'), (OUTPUT / 'sources/generated-model-fitting', 'file')]:
        manifest_path = folder / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for item in manifest['files']:
            path = folder / item[path_key]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == item['sha256'], f'Original source changed: {path}'
            source_hashes[str(path.relative_to(ROOT))] = digest
        source_hashes[str(manifest_path.relative_to(ROOT))] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    means, sems = observations()
    assert means.shape == sems.shape == (6, 2, 6, 2)
    assert np.isfinite(means).sum() == 86 and np.array_equal(np.isfinite(means), np.isfinite(sems))
    assert np.all(sems[np.isfinite(sems)] > 0)
    predictions, traces, comparisons, fit_agreement, parameter_sets = {}, {}, [], [], {}
    for date, directory, kind in [('17-Apr-2024', 'matlab_code/model_fitting/figures', 'fitting'),
                                  ('27-Mar-2023', 'data_and_parameters', 'figure5c')]:
        for modules in [2, 3]:
            path = SOURCE / f'upstream-model/{directory}/Dx_steady_state_nonlinear_3_{date}_{modules}modules.mat'
            assert {name for name, _, _ in whosmat(path)} == {'mat_lu_cell', 'para_mu', 'para_CI', 'para_rand'}
            params = parameters(path)
            stored = loadmat(path)
            parameter_sets[f'{date}_{modules}modules'] = dict(
                para_mu=stored['para_mu'].ravel().tolist(),
                saved_parameter_samples=int(stored['para_rand'].shape[1]),
                used='para_mu only; CI samples retained but not executed')
            for pair_index, (pair, columns) in enumerate([('attractive', [0, 1, 2, 3, 4, 5]),
                                                         ('repulsive', [6, 7, 8, 3, 4, 5])]):
                selected = [params[0][:, columns], *params[1:]]
                key = f'{date}_{modules}modules_{pair}'
                predicted, trace = simulate(selected, protocol(kind))
                predictions[key], traces[key] = predicted, trace
                assert np.isfinite(predicted).all()
                assert max(t['fixed_point_residual_hz'] for t in trace) < 1e-10
                if date == '17-Apr-2024':
                    figure_path = OUTPUT / 'sources/generated-model-fitting' / f'Dx_steady_state_nonlinear_3_{key}.fig'
                    indices, expected, figure_means, figure_sems = original_curves(figure_path, modules)
                    np.testing.assert_allclose(predicted[indices], expected, rtol=0, atol=1e-10)
                    np.testing.assert_allclose(means[indices, :, :, pair_index], figure_means, rtol=0, atol=1e-12)
                    np.testing.assert_allclose(sems[indices, :, :, pair_index], figure_sems, rtol=0, atol=1e-12)
                    predictions[key + '_original_matlab'] = expected
                    comparisons.append(dict(condition=key, stored_points=int(expected.size),
                        max_absolute_error_hz=float(np.max(np.abs(predicted[indices] - expected)))))
                indices = [0, 2, 3, 5] if modules == 2 else list(range(6))
                observed = means[indices, :, :, pair_index]
                errors = predicted[indices] - observed
                valid = np.isfinite(observed)
                fit_agreement.append(dict(condition=key, protocol=kind, observations=int(valid.sum()),
                    rmse_hz=float(np.sqrt(np.mean(errors[valid] ** 2))),
                    weighted_sse=float(np.sum((errors[valid] / sems[indices, :, :, pair_index][valid]) ** 2)),
                    scope='same fitted observations; not independent biological validation'))
    # Controls use the original published March 2023 3-module parameters, no retuning.
    p = parameters(SOURCE / 'upstream-model/data_and_parameters/Dx_steady_state_nonlinear_3_27-Mar-2023_3modules.mat')
    selected = [p[0][:, :6], *p[1:]]
    schedule = protocol('figure5c')
    control_records, control_protocols = {}, {}
    for condition in ['paired', 'frozen', 'odor_only', 'shock_only', 'shifted']:
        current_schedule = controls(schedule, condition)
        result, trace = simulate(selected, current_schedule, frozen=condition == 'frozen')
        predictions['control_' + condition], traces['control_' + condition] = result, trace
        control_protocols[condition] = current_schedule
        final_change = np.asarray(trace[-1]['weights_after']) - np.repeat(selected[0], 2, axis=0)
        if condition in {'frozen', 'shock_only'}:
            np.testing.assert_array_equal(final_change, 0.)
        if condition == 'shock_only':
            np.testing.assert_array_equal(result, 0.)
        control_records[condition] = dict(bouts=len(trace), simulated_s=trace[-1]['end_s'],
            shock_duration_s=sum(s['duration_s'] * s['punishment'] for s in current_schedule),
            mbon_gamma1_CS_plus_delta_hz=result[3, 0].tolist(),
            mbon_alpha3_CS_plus_delta_hz=result[5, 0].tolist(),
            final_effective_weight_change=final_change.tolist())
    np.testing.assert_allclose(predictions['control_shifted'], predictions['control_odor_only'], rtol=0, atol=1e-10)
    for condition in ['frozen', 'odor_only', 'shifted']:
        np.testing.assert_array_equal(predictions['control_' + condition][:, :, 0], predictions['control_paired'][:, :, 0])
    assert control_records['paired']['simulated_s'] == control_records['shifted']['simulated_s']
    assert control_records['paired']['shock_duration_s'] == control_records['shifted']['shock_duration_s'] == 180.
    assert np.max(np.abs(predictions['control_paired'] - predictions['control_shifted'])) > 1.
    control_records['checks'] = dict(
        matched_duration_and_shock_exposure='PASS', frozen_and_shock_only_zero_weight_change='PASS',
        pretraining_equal='PASS',
        shifted_matches_odor_only_max_error_hz=float(np.max(np.abs(predictions['control_shifted'] - predictions['control_odor_only']))),
        scope='deterministic bout-level mechanism controls; no arbitrary CS-US timing prediction')
    for modules in [2, 3]:
        assert parameter_sets[f'17-Apr-2024_{modules}modules']['para_mu'] == parameter_sets[f'27-Mar-2023_{modules}modules']['para_mu']
    receipt = dict(schema=1, status='PASS_ORIGINAL_REDUCED_RATE_MODEL_REFERENCE',
        executed_at_utc=datetime.now(timezone.utc).isoformat(),
        source_revision='5d7c08a9a88f923169a0c3008aca68af421e9a7f',
        claim='Original MATLAB saved fit curves reproduced by a bounded Python translation.',
        source_curve_comparisons=comparisons, checked_original_points=sum(c['stored_points'] for c in comparisons),
        source_curve_tolerance_hz=1e-10, source_workbook_numeric_values_checked=172,
        fit_data_agreement=fit_agreement, controls=control_records, parameter_sets=parameter_sets,
        source_sha256=source_hashes, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        execution=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
                       hardware='local CPU; no GPU/runtime or shared service accessed',
                       wall_s=time.perf_counter()-started,
                       rng='none; deterministic para_mu only', parameter_fitting='NOT_RUN',
                       matlab_or_octave='NOT_RUN; independent stored MATLAB outputs used',
                       ci_resampling='NOT_RUN; no Figure5c 10000-sample CI reconstruction claimed'),
        biological_validation='OPEN; observations were used by original authors for fitting',
        malecns_learning='NOT_IMPLEMENTED_OR_VALIDATED',
        limitations=['Six DAN/MBON outputs, two abstract KC channels and imposed shock input; not molecular kinetics or an individual CNS.',
                     'Bout recurrence assumes the original fixed 3-s CS-US interval and long inter-bout rests.',
                     'March2023 figure protocol and April2024 fitting protocol retained separately.',
                     'No checkpoint, circuit mapping, runtime gains or body changed.'])
    return receipt, predictions, traces, control_protocols, means, sems


def write_outputs(folder, result):
    receipt, predictions, traces, control_protocols, means, sems = result
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    (folder / 'bout-traces.json').write_text(json.dumps(traces, indent=2, allow_nan=False) + '\n')
    (folder / 'protocols.json').write_text(json.dumps(dict(fitting=protocol('fitting'),
        figure5c=protocol('figure5c'), controls=control_protocols), indent=2, allow_nan=False) + '\n')
    np.savez_compressed(folder / 'predictions.npz', **predictions, observed_mean_hz=means, observed_sem_hz=sems)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout='constrained')
    for column, pair in enumerate(['attractive', 'repulsive']):
        key = f'17-Apr-2024_3modules_{pair}'
        for row, cell in enumerate([3, 5]):
            ax = axes[row, column]
            for odor, color, label in [(0, '#be4433', 'CS+'), (1, '#3575a1', 'CS−')]:
                ax.errorbar(range(6), means[cell, odor, :, column], yerr=sems[cell, odor, :, column],
                            fmt='o', color=color, capsize=3, markersize=4, label=f'{label} observations ± SEM')
                ax.plot(range(6), predictions[key][cell, odor], color=color, label=f'{label} Python reference')
                ax.plot(range(6), predictions[key + '_original_matlab'][cell, odor], 'x', color='black', markersize=5)
            ax.set(title=f'{CELLS[cell]} · {pair} pair', xticks=range(6), xticklabels=STAGES,
                   ylabel='Change from baseline (Hz)')
            ax.axhline(0, color='#bbbbbb', linewidth=.6)
            ax.grid(axis='y', alpha=.15)
    axes[0, 0].legend(fontsize=7, loc='lower right')
    fig.suptitle('Huang/Luo original fitted model: Python curves match saved MATLAB values\n'
                 'Black ×: original outputs · source-fit comparison, not independent biological validation', fontsize=12)
    fig.savefig(folder / 'source-fit-comparison.png', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check source curves and controls without writing')
    parser.add_argument('--output', type=Path, help='Retain the same checked results and comparison plot')
    args = parser.parse_args()
    if not args.check and args.output is None:
        parser.error('--check or --output is required')
    result = run()
    if args.output is not None:
        write_outputs(args.output, result)
    print(json.dumps(result[0], indent=2, allow_nan=False))

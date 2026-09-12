"""Isolated MS-WED passive response reference; never imports or edits the live CNS.

Uses nominal ABF DAC commands and the previously fixed fit/holdout plan.
The two female recordings do not establish male or peptide/receptor kinetics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]


def response(t, resistance_MOhm, tau_s, current_pA, onset_s, offset_s):
    """Analytic passive voltage deflection; pA*MOhm*0.001 gives mV."""
    if resistance_MOhm <= 0 or tau_s <= 0 or offset_s <= onset_s:
        raise ValueError('Positive R/tau and a nonempty pulse are required')
    rise = -np.expm1(-np.clip(t - onset_s, 0, offset_s - onset_s) / tau_s)
    return current_pA * resistance_MOhm * 0.001 * rise * np.exp(-np.maximum(t - offset_s, 0) / tau_s)


def euler_check(resistance_MOhm, tau_s, current_pA, onset_s, offset_s, duration_s):
    errors = []
    amplitude = abs(current_pA * resistance_MOhm * 0.001)
    for dt in (100e-6, 50e-6, 25e-6):
        t = np.arange(round(duration_s / dt)) * dt
        command = np.zeros(len(t))
        begin, end = round(onset_s / dt), round(offset_s / dt)
        assert np.isclose(begin * dt, onset_s) and np.isclose(end * dt, offset_s)
        command[begin:end] = current_pA
        voltage = np.zeros(len(t))
        for i in range(len(t) - 1):
            voltage[i + 1] = voltage[i] + dt / tau_s * (0.001 * resistance_MOhm * command[i] - voltage[i])
        error = float(np.max(np.abs(voltage - response(t, resistance_MOhm, tau_s, current_pA, onset_s, offset_s))))
        errors.append({'dt_s': dt, 'maximum_error_mV': error,
                       'first_order_error_bound_mV': amplitude * dt / tau_s,
                       'finite': bool(np.isfinite(voltage).all())})
    passed = all(x['finite'] and x['dt_s'] < tau_s and x['maximum_error_mV'] <= x['first_order_error_bound_mV'] for x in errors)
    passed &= errors[0]['maximum_error_mV'] > errors[1]['maximum_error_mV'] > errors[2]['maximum_error_mV']
    return {'status': 'PASS' if passed else 'FAIL', 'errors': errors}


def check():
    t = np.array([0., .01, .02, .11, 1.])
    y = response(t, 100., .01, -10., .01, .11)
    assert y[0] == y[1] == 0
    assert np.isclose(y[2], -(1 - np.exp(-1)))  # -10 pA * 100 Mohm = -1 mV
    assert np.isclose(y[3], -(1 - np.exp(-10))) and abs(y[4]) < 1e-30
    assert np.array_equal(response(t, 100., .01, 0., .01, .11), np.zeros(len(t)))
    assert euler_check(100., .01, -10., .01, .11, .2)['status'] == 'PASS'
    try:
        response(t, -1., .01, 10., .01, .11)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid resistance accepted')


def pulse(command, dt):
    nonzero = np.flatnonzero(command)
    if not len(nonzero):
        raise ValueError('No nonzero current command')
    begin, end = nonzero[0], nonzero[-1] + 1
    if begin == 0 or not np.all(command[begin:end] == command[begin]):
        raise ValueError('Expected one constant pulse preceded by baseline')
    assert len(nonzero) == end - begin
    return float(command[begin]), begin * dt, end * dt, int(begin)


def run(directory, output):
    start = time.monotonic()
    plan_path = directory / 'rc-comparison-plan.json'
    plan = json.loads(plan_path.read_text())
    results, traces = [], {}
    for record_index, spec in enumerate(plan['records']):
        path = directory / spec['decoded_path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec['sha256']:
            raise ValueError(f'Source hash changed: {path}')
        with np.load(path, allow_pickle=False) as data:
            assert data['adc_units'][0] == 'mV'
            t = data['time_within_sweep_s'].copy()
            voltage = data['adc_samples'][:, 0].astype(np.float64)
            command = data['dac0_command_pA'].copy()
        dt = t[1] - t[0]
        assert t[0] == 0 and dt > 0 and np.allclose(np.diff(t), dt, rtol=0, atol=1e-12)
        assert voltage.shape == command.shape and voltage.shape[1] == len(t)
        assert np.isfinite(voltage).all() and np.isfinite(command).all()
        calibration = spec['calibration_sweep']
        amp, onset, offset, baseline_end = pulse(command[calibration], dt)
        assert amp == spec['calibration_nominal_current_pA']
        baseline = float(voltage[calibration, :baseline_end].mean())
        observed = voltage[calibration] - baseline
        plateau = observed[(t >= offset - .05) & (t < offset)].mean()
        r_start = max(1e-6, float(plateau * 1000 / amp))
        fit = least_squares(lambda p: response(t, *p, amp, onset, offset) - observed,
                            [r_start, .02], bounds=(np.finfo(float).tiny, np.inf), x_scale='jac')
        if not fit.success or not np.isfinite(fit.x).all():
            raise RuntimeError(f'Calibration optimization failed: {fit.message}')
        resistance, tau = map(float, fit.x)
        row = {'recording_id': spec['recording_id'], 'source_sha256': spec['sha256'],
               'R_effective_MOhm_per_nominal_current': resistance, 'tau_effective_s': tau,
               'C_effective_pF_not_independent_measurement': tau / resistance * 1e6,
               'parameter_interpretation': plan['parameter_meaning'],
               'optimizer_success': bool(fit.success), 'calibration_jacobian_rank': int(np.linalg.matrix_rank(fit.jac)),
               'sample_rate_hz': float(1 / dt), 'comparisons': []}
        for sweep, expected_amp in [(calibration, amp), *zip(spec['held_out_sweeps'], spec['held_out_nominal_currents_pA'])]:
            current, on, off, end = pulse(command[sweep], dt)
            assert current == expected_amp
            base = float(voltage[sweep, :end].mean())
            measured = voltage[sweep] - base
            prediction = response(t, resistance, tau, current, on, off)
            mse, null_mse = float(np.mean((prediction - measured)**2)), float(np.mean(measured**2))
            row['comparisons'].append({'sweep': sweep, 'role': 'calibration' if sweep == calibration else 'held_out',
                'nominal_command_pA': current, 'onset_s': on, 'duration_s': off - on,
                'observed_initial_baseline_mV': base, 'rmse_mV': mse**.5,
                'no_response_rmse_mV': null_mse**.5, 'mse_ratio_to_no_response': mse / null_mse,
                'prediction_advantage_over_no_response': mse < null_mse,
                'rmse_over_nominal_response_amplitude': mse**.5 / abs(current * resistance * .001)})
            traces[f'r{record_index}_s{sweep}_measured_delta_mV'] = measured
            traces[f'r{record_index}_s{sweep}_predicted_delta_mV'] = prediction
        zero = spec['zero_current_diagnostic_sweep']
        assert np.all(command[zero] == 0)
        zero_base = float(voltage[zero, :baseline_end].mean())
        row['zero_current_diagnostic'] = {'sweep': zero, 'baseline_mV': zero_base,
            'rms_deflection_mV': float(np.mean((voltage[zero] - zero_base)**2)**.5)}
        row['numerical_check'] = euler_check(resistance, tau, amp, onset, offset, len(t) * dt)
        results.append(row)
        traces[f'r{record_index}_time_s'] = t
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'comparison-traces.npz', **traces)
    receipt = {'implementation': 'PASS: source checks and fixed fit/holdout analysis executed',
        'numerical_correctness': 'PASS' if all(x['numerical_check']['status'] == 'PASS' for x in results) else 'FAIL',
        'biological_validation': 'OPEN: effective two-recording response comparison; no population-equivalence margin',
        'demonstrated_capability': 'NONE_ADDED', 'source_snapshot_commit': plan['source_snapshot_commit'],
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        'trace_sha256': hashlib.sha256((output / 'comparison-traces.npz').read_bytes()).hexdigest(),
        'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'wall_seconds': time.monotonic() - start, 'records': results,
        'limitations': [plan[k] for k in ('scope', 'source_selection', 'state_definition', 'input_authority', 'biological_acceptance', 'intervention_limit')]}
    (output / 'comparison-result.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'numerical_correctness': receipt['numerical_correctness'],
                     'records': [{'id': x['recording_id'], 'R_MOhm': x['R_effective_MOhm_per_nominal_current'],
                                  'tau_ms': x['tau_effective_s'] * 1000,
                                  'held_out_rmse_mV': [y['rmse_mV'] for y in x['comparisons'] if y['role'] == 'held_out']}
                                 for x in results]}, indent=2))
    if receipt['numerical_correctness'] != 'PASS':
        raise RuntimeError('Numerical reference failed; inspect retained receipt')


def plot(output):
    import os
    import tempfile
    os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'fruit-fly-ms-wed-mpl'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    receipt = json.loads((output / 'comparison-result.json').read_text())
    with np.load(output / 'comparison-traces.npz', allow_pickle=False) as traces:
        fig, axes = plt.subplots(2, 3, figsize=(12, 6.4), sharex=True, sharey='row', constrained_layout=True)
        for i, record in enumerate(receipt['records']):
            condition = 'Mated female' if 'Mated female' in record['recording_id'] else 'Virgin female'
            for column, comparison in enumerate(record['comparisons']):
                ax, sweep = axes[i, column], comparison['sweep']
                t = traces[f'r{i}_time_s'] * 1000
                ax.plot(t, traces[f'r{i}_s{sweep}_measured_delta_mV'], color='#76939b', lw=.6, label='Recorded voltage')
                ax.plot(t, traces[f'r{i}_s{sweep}_predicted_delta_mV'], color='#bd533b', lw=1.4, label='Frozen RC prediction')
                for value in [comparison['onset_s'], comparison['onset_s'] + comparison['duration_s']]:
                    ax.axvline(value * 1000, color='.6', lw=.7, ls=':')
                ax.set_title(f"{condition}: {comparison['nominal_command_pA']:g} pA {comparison['role'].replace('_', ' ')}", fontsize=10)
                ax.text(.03, .08, f"RMSE {comparison['rmse_mV']:.2f} mV", transform=ax.transAxes, fontsize=9)
                ax.spines[['top', 'right']].set_visible(False)
                if column == 0:
                    ax.set_ylabel('Voltage from observed baseline (mV)')
                if i == 1:
                    ax.set_xlabel('Time within sweep (ms)')
        axes[0, 0].legend(frameon=False, fontsize=8, loc='lower left', bbox_to_anchor=(0, .13))
        fig.suptitle('MS-WED effective passive reference: nominal commands, two female recordings', fontsize=13)
        fig.savefig(output / 'comparison.png', dpi=160)
        plt.close(fig)
    print(f'Saved {output / "comparison.png"}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--plot', action='store_true', help='Render the existing result without fitting again')
    parser.add_argument('--source', type=Path, default=ROOT / 'data/research/m4-m7/ms-wed-reference')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    check()
    if args.check:
        print('PASS: passive units, pulse timing, zero current, invalid-input rejection and Euler convergence')
    elif args.plot:
        plot(args.output or ROOT / 'runs/ms-wed-reference')
    else:
        run(args.source, args.output or ROOT / 'runs/ms-wed-reference')

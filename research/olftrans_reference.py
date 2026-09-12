"""Isolated published Or59b-acetone transduction reference; no runtime wiring.

Reuses the pinned FlyBrainLab OTP functions (BSD-3-Clause; Tingkai Liu, 2021).
The full upstream source and license are retained in data/research/m3/
olftrans-reference/sources/. Lazar & Yeh 2020 Eq. 2 supplies rectification
missing from the released CPU algebraic update. Output is pA, never spikes/s.
"""
import argparse
import ast
import copy
import hashlib
import json
import platform
from abc import abstractmethod
from collections.abc import Iterable
from functools import lru_cache
from numbers import Number
from pathlib import Path

import h5py
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/research/m3/olftrans-reference'
SOURCES = ROOT / 'data/research/publication-review/flybrainlab-sources'
UPSTREAM = FOLDER / 'sources/OlfTrans-cpu-model.py'
CONFIG = SOURCES / 'olftrans-replay-boundary.json'
DATA = SOURCES / 'antenna-data.h5'
HASHES = {
    UPSTREAM: 'e4cc0a36acb95f22b85e7d16f289b9018e5fa168593aa404b793eb0e8e23955b',
    CONFIG: 'dfcb96017bd56ebf2b41cc0a3e110ff7612e0ff7cb98675a4b56b983022e8493',
    DATA: '89ba48164a6db16d14ad2a9b2b8798d5babfcb0f154140041e7053b3b4553715',
}
STATE_NAMES = ('uh', 'duh', 'x1', 'x2', 'x3')
GROUPS = ('elife15/step', 'elife15/ramp', 'elife15/parabola')


@lru_cache(maxsize=1)
def source_model():
    """Load only verbatim Model/OTP classes, without upstream package imports."""
    for path in (UPSTREAM, CONFIG):
        if hashlib.sha256(path.read_bytes()).hexdigest() != HASHES[path]:
            raise ValueError(f'Frozen reference changed: {path}')
    tree = ast.parse(UPSTREAM.read_text())
    tree.body = [node for node in tree.body
                 if isinstance(node, ast.ClassDef) and node.name in ('Model', 'OTP')]
    namespace = dict(np=np, copy=copy, abstractmethod=abstractmethod,
                     Iterable=Iterable, Number=Number)
    exec(compile(tree, str(UPSTREAM), 'exec'), namespace)
    return namespace['OTP'], json.loads(CONFIG.read_text())['OTP_parameters']


def transduce(time_s, concentration_ppm, *, max_step_s=0.002, rtol=1e-7, atol=1e-9):
    """Published deterministic OTP, zero initial state at the first timestamp.

    Piecewise-linear source concentration; no padding, baseline subtraction,
    rescaling, latency shift, hidden warmup, or PSTH interpolation. A new model
    is created for every call. Original algebraic functions are evaluated at
    each ODE stage, with paper Eq. 2 rectification; CPU Euler clipping is unused.
    """
    t = np.asarray(time_s, dtype=float)
    u = np.atleast_2d(np.asarray(concentration_ppm, dtype=float))
    if (t.ndim != 1 or len(t) < 2 or not np.isfinite(t).all()
            or not (np.diff(t) > 0).all() or u.ndim != 2 or u.shape[1] != len(t)
            or u.shape[0] == 0 or not np.isfinite(u).all() or (u < 0).any()):
        raise ValueError('Expected increasing finite seconds and nonnegative finite ppm curves')
    if any(not np.isfinite(x) or x <= 0 for x in (max_step_s, rtol, atol)):
        raise ValueError('Integration step and tolerances must be positive and finite')
    OTP, params = source_model()
    model = OTP(num=len(u), **params)

    def rhs(now, flat_state):
        model.states.update(zip(STATE_NAMES, flat_state.reshape(5, -1)))
        model.states.update(model.non_gradient())
        model.states['v'] = np.maximum(0.0, model.v)  # Published Eq. 2, absent in CPU update.
        stimulus = np.array([np.interp(now, t, curve) for curve in u])
        gradients = model.gradient(stimulus=stimulus)
        return np.array([gradients[name] for name in STATE_NAMES]).ravel()

    solution = solve_ivp(rhs, (t[0], t[-1]), np.zeros(5 * len(u)), t_eval=t,
                         method='DOP853', max_step=max_step_s, rtol=rtol, atol=atol)
    if not solution.success or not np.isfinite(solution.y).all():
        raise RuntimeError(f'OTP integration failed: {solution.message}')
    states = solution.y.reshape(5, len(u), len(t))
    # Reject material state-domain errors; do not hide numerical drift by clipping.
    if states[2:].min() < -1e-8 or states[2:4].max() > 1 + 1e-8:
        raise RuntimeError('Integrated channel state left its physical domain')
    current = params['Imax'] * states[3] / (states[3] + params['c'])
    return dict(states=states, current_pA=current,
                drive_ppm=np.maximum(0, states[0] + params['gamma'] * states[1]),
                function_evaluations=solution.nfev)


def check(output):
    """One runnable source, protocol, equilibrium, reset and convergence check."""
    for path, expected in HASHES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    OTP, params = source_model()
    assert params == dict(br=.0217, dr=2.94, gamma=.2105, b1=.8, a1=45.,
                         a2=146.1, b2=117.2, a3=2.539, b3=.9096, kappa=8841.,
                         p=1., c=.06546, Imax=62.13)
    assert OTP.Params['gamma'] == .215 and OTP.Params['br'] == OTP.Params['dr'] == 1.
    source = OTP(**params, uh=5., duh=-100.)
    assert source.non_gradient()['v'][0] < 0  # The documented source discrepancy exists.

    controls_t = np.linspace(0, 10, 1001)
    controls = transduce(controls_t, np.array([np.zeros(1001), np.full(1001, 50.)]))
    assert np.array_equal(controls['states'][:, 0], np.zeros((5, 1001)))
    alpha, beta = params['a1'], params['b1']
    omega = alpha * np.sqrt(1 - beta ** 2)
    analytic_filter = 50 * (1 - np.exp(-alpha * beta * controls_t)
                            * (np.cos(omega * controls_t)
                               + alpha * beta / omega * np.sin(omega * controls_t)))
    filter_error = float(np.max(np.abs(controls['states'][0, 1] - analytic_filter)))
    assert filter_error < 1e-7
    x1_ss = params['br'] * 50 / (params['br'] * 50 + params['dr'])
    x2_ss = brentq(lambda x: params['a2'] * x1_ss * (1 - x) - params['b2'] * x
                  - params['kappa'] * x ** (2 / 3)
                  * (params['a3'] * x / params['b3']) ** (2 / 3), 0, 1)
    expected_current = params['Imax'] * x2_ss / (x2_ss + params['c'])
    equilibrium_error = abs(float(controls['current_pA'][1, -1]) - expected_current)
    assert equilibrium_error < 1e-4
    assert controls['current_pA'][1].max() > 1.2 * expected_current
    short_t = np.linspace(0, .2, 101)
    first = transduce(short_t, np.full(101, 50.))
    assert np.array_equal(first['states'], transduce(short_t, np.full(101, 50.))['states'])
    for t, u in [([0, 0], [1, 1]), ([0, 1], [-1, 0]), ([0, 1], [0, np.nan]),
                 ([0, 1], [1]), ([0, np.inf], [1, 1])]:
        try:
            transduce(t, u)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid concentration/time protocol accepted')

    arrays, rows, metadata = {}, [], []
    with h5py.File(DATA, 'r') as data:
        for group in GROUPS:
            g = data[group]
            assert dict(g.attrs) == {'odorant': 'acetone', 'receptor': 'or59b'}
            t, u, pt, py = [g[k][()] for k in ('stimulus/x', 'stimulus/y', 'psth/x', 'psth/y')]
            assert t.shape == (17499,) and u.shape == (3, 17499)
            assert pt.shape == (139,) and py.shape == (3, 139)
            assert np.allclose(np.diff(t), .0002, rtol=0, atol=2e-14)
            assert np.allclose(np.diff(pt), .025, rtol=0, atol=2e-14)
            assert all(np.isfinite(a).all() for a in (t, u, pt, py))
            assert u.min() >= 0 and py.min() >= 0
            if rows:
                assert np.array_equal(t, arrays['stimulus_time_s'])
            arrays['stimulus_time_s'] = t
            shape = group.split('/')[-1]
            arrays[f'{shape}_stimulus_ppm'] = u
            arrays[f'{shape}_psth_time_s'] = pt
            arrays[f'{shape}_measured_psth_spikes_per_s'] = py
            rows.extend(u)
            metadata.append(dict(group=group, original_curve_order=[0, 1, 2],
                                 concentration_max_ppm=u.max(axis=1).tolist(),
                                 stimulus_support_s=[float(t[0]), float(t[-1])],
                                 psth_support_s=[float(pt[0]), float(pt[-1])]))
    original_t = arrays['stimulus_time_s']
    default = transduce(original_t, rows)
    fine = transduce(original_t, rows, max_step_s=.001, rtol=1e-8, atol=1e-10)
    errors = np.max(np.abs(default['current_pA'] - fine['current_pA']), axis=1)
    assert errors.max() < .001  # Fixed numerical margin, not a biological acceptance margin.
    assert default['drive_ppm'].min() == 0
    assert default['current_pA'].min() >= -1e-8
    assert default['current_pA'].max() < params['Imax']
    for i, group in enumerate(GROUPS):
        shape = group.split('/')[-1]
        for name, values in zip(STATE_NAMES, fine['states']):
            arrays[f'{shape}_model_{name}'] = values[i * 3:(i + 1) * 3]
        arrays[f'{shape}_model_current_pA'] = fine['current_pA'][i * 3:(i + 1) * 3]
        arrays[f'{shape}_model_drive_ppm'] = fine['drive_ppm'][i * 3:(i + 1) * 3]
        metadata[i]['current_peak_pA'] = fine['current_pA'][i * 3:(i + 1) * 3].max(axis=1).tolist()
        metadata[i]['numerical_max_difference_pA'] = errors[i * 3:(i + 1) * 3].tolist()
    output.mkdir(parents=True, exist_ok=True)
    trace_path = output / 'waveforms.npz'
    np.savez_compressed(trace_path, **arrays)
    result = dict(
        claim='Deterministic published OTP equations on source Or59b-acetone waveforms; no BSG or runtime integration',
        implementation='PASS original OTP functions reused; paper rectification explicitly applied',
        numerical='PASS analytic filter, steady state, zero input, adaptation, reset and tolerance refinement',
        biological_validation='OPEN: no matched measured transduction-current arrays; PSTH comparison not performed',
        BSG='OPEN: stochastic gate-noise/time/current conventions unresolved; BSG class never loaded',
        demonstrated_capability='NONE', M3_full_gate='OPEN',
        upstream_revision='3f873eafba3a21b8fcb27231b49835df1d3cbc0c',
        frozen_parameters=params,
        units=dict(time='s', input='ppm', current='pA', uh='ppm', duh='ppm/s',
                   x1='fraction', x2='dimensionless gate', x3='dimensionless calcium gate proxy'),
        protocol=dict(initial_state='all five dynamic states zero at source t=0; not measured prehistory',
                      interpolation='linear concentration only; original curve order and all timestamps preserved',
                      additional_PID_latency_shift_s=0, psth_bin_width_s=.1, psth_overlap_s=.075,
                      psth_spacing_s=.025, psth_timestamp_center_or_edge='UNRESOLVED; unused for fitting',
                      preparation=json.loads(CONFIG.read_text())['biological_preparation']),
        calibration=dict(source_fit='White noise plus Dataset 1 pulse-like responses; Dataset 2 separately fitted',
                         br_dr_dataset2=dict(br=.0211, dr=2.65),
                         chosen_configuration='Fig. 4 explicitly uses Dataset 1 br=.0217, dr=2.94',
                         local_parameter_fitting=False, step='calibration-associated; not claimed as holdout',
                         ramp_parabola='published waveform holdout candidates only; output comparison NOT_RUN',
                         prospective_holdout=False, published_PSTH_errors_reproduced=False),
        numeric_checks=dict(analytic_filter_max_error_ppm=filter_error,
                            steady_current_pA=expected_current, equilibrium_abs_error_pA=equilibrium_error,
                            current_refinement_max_error_pA=float(errors.max()),
                            fixed_numerical_margin_pA=.001,
                            coarse_solver=dict(method='DOP853', max_step_s=.002, rtol=1e-7, atol=1e-9,
                                               function_evaluations=default['function_evaluations']),
                            saved_solver=dict(method='DOP853', max_step_s=.001, rtol=1e-8, atol=1e-10,
                                              function_evaluations=fine['function_evaluations'])),
        waveforms=metadata,
        source_code_differences=['Eq. 2 rectification supplied at every RHS evaluation',
                                'DOP853 replaces released Euler update; source state clipping is not applied',
                                'Linear peri-receptor filter may undershoot; only v is rectified',
                                'CPU current formula ignores p generally, but frozen published p=1 matches Eq. 6',
                                'CPU default br=dr=1 and gamma=.215 overridden by frozen Fig. 4 values'],
        exclusions=['white_noise fitting set', 'staircase and two_odorants not replayed',
                    'multiple_pairs ambiguous identities/units', 'no trial identities or raw spikes inferred',
                    'no acetate substitution, male preparation transfer, individual-cell binding or scene change'],
        environment=dict(python=platform.python_version(), numpy=np.__version__,
                         scipy=scipy.__version__, h5py=h5py.__version__),
        source_sha256={str(p.relative_to(ROOT)): expected for p, expected in HASHES.items()},
        module_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
    )
    (output / 'reference-check.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/olftrans-reference')
    args = parser.parse_args()
    receipt = check(args.output)
    print(json.dumps({k: receipt[k] for k in ('implementation', 'numerical', 'biological_validation',
                                             'BSG', 'M3_full_gate')}, indent=2))

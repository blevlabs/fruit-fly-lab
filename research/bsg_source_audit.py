"""Source-only BSG adjudication; no fitted physiology or stochastic population run.

Lazar & Yeh 2020, S1 Notebook and Appendix, doi:10.1371/journal.pcbi.1007751.
The source transition is evaluated with prescribed nonzero Gaussian innovations,
not with noise disabled. See source-provenance.json and the M3 BSG research report.
"""
import ast
import copy
import hashlib
import json
import math
from abc import abstractmethod
from collections.abc import Iterable
from numbers import Number
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'data/research/m3/bsg-source-audit'
HASHES = {
    'author-notebook.html': 'e8af6ba236fd0e56d37e90320499e80b736cf5c897384fab0b69a35e0743f0ef',
    'publisher-S1-notebook.html': 'e8af6ba236fd0e56d37e90320499e80b736cf5c897384fab0b69a35e0743f0ef',
    'sources/S1-NoisyConnorStevens.py': '37976324b038bce7c859e9fbe4148f0c2e722bd286c698b6fc0dfca938f5ccb5',
    'sources/S1-notebook-code-cells.json': 'c4b0d84bc23e3a673f43d559c8e03a9946b0a5931b841dba1deba205762b4956',
    'sources/neural-20191016-neural-basemodel.py': '6138bcdbe28caf2e862695b49328cbefd95bd2cf43952c8b9fc667417db3a1ed',
    'sources/neural-20191016-neural-backend.py': '24fddc88740d02a04ede596cd66fd0d7e613106a0c0f58d6603ffb69290a83c1',
    'sources/neural-20191016-neural-codegen-cuda.py': 'f9252a84040af8cfbc904e52d94bfa660627f9776db2475a2c1bc6fd08fd1c6e',
    'sources/neural-20191016-setup.py': 'ee90f5a941d3646ca47b954499fdf51c088d33c776ae05c3ceb439499598d724',
    '../../publication-review/flybrainlab-sources/odor-appendix.pdf': 'dce7294403597ca6e7b40073e2147b8a91fa27bc010f5884ff1d4ac9a31ce6f7',
}


def appendix_gates(v):
    """Literal printed S1 p3 equations, visually checked against retained PNG/PDF."""
    rate = lambda z, a: 10 * a if abs(z) < 1e-12 else a * z / -math.expm1(-z / 10)
    an, bn = rate(v + 55, .01), .125 * math.exp(-(v + 65) / 80)
    am, bm = rate(v + 40, .1), 4 * math.exp(-(v + 65) / 18)
    ah, bh = .7 * math.exp(-(v + 65) / 20), 1 / (1 + math.exp(-(v + 35) / 10))
    return dict(n_inf=an / (an + bn), tau_n=2 / (.38 * (an + bn)),
                m_inf=am / (am + bm), tau_m=1 / (.38 * (am + bm)),
                h_inf=ah / (ah + bh), tau_h=1 / (.38 * (ah + bh)),
                a_inf=(.0761 * math.exp((v + 94.22) / 31.84)
                       / (1 + math.exp((v + 1.17) / 28.93))) ** .3333,
                tau_a=.3632 + 1.158 / (1 + math.exp((v + 55.96) / 20.12)),
                b_inf=(1 / (1 + math.exp((v + 53.3) / 14.54))) ** 4,
                tau_b=1.24 + 2.678 / (1 + math.exp((v + 50) / 16.027)))


def source_classes(inspect_locals=True):
    """Reuse source classes; expose intermediates for audit or inject a private RNG.

    The simulation form replaces only np.random.randn with self.rng.standard_normal.
    It retains all original drift, clipping metadata and spike/refractory expressions.
    """
    tree = ast.parse((HERE / 'sources/S1-NoisyConnorStevens.py').read_text())
    ode = next(n for n in tree.body[0].body if isinstance(n, ast.FunctionDef) and n.name == 'ode')
    if inspect_locals:
        ode.body.append(ast.parse('return locals()').body[0])
    namespace = dict(Model=object, np=np, random=SimpleNamespace(gauss=None))
    exec(compile(ast.fix_missing_locations(tree), '<publisher-S1-BSG>', 'exec'), namespace)
    notebook = namespace['NoisyConnorStevens']
    fbl_path = ROOT / 'data/research/m3/olftrans-reference/sources/OlfTrans-cpu-model.py'
    assert hashlib.sha256(fbl_path.read_bytes()).hexdigest() == 'e4cc0a36acb95f22b85e7d16f289b9018e5fa168593aa404b793eb0e8e23955b'
    tree = ast.parse(fbl_path.read_text())
    tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef)
                 and n.name in ('Model', 'NoisyConnorStevens')]
    gradient = next(n for n in tree.body[1].body if isinstance(n, ast.FunctionDef) and n.name == 'gradient')
    if inspect_locals:
        gradient.body[-1] = ast.parse('return locals()').body[0]
    else:
        draws = [n for n in ast.walk(gradient) if isinstance(n, ast.Call)
                 and ast.unparse(n.func) == 'np.random.randn']
        assert len(draws) == 5
        for draw in draws:
            draw.func = ast.parse('self.rng.standard_normal', mode='eval').body
    fbl_ns = dict(np=np, copy=copy, abstractmethod=abstractmethod, Iterable=Iterable, Number=Number)
    exec(compile(ast.fix_missing_locations(tree), str(fbl_path), 'exec'), fbl_ns)
    return notebook, namespace, fbl_ns['NoisyConnorStevens']


def main():
    for name, expected in HASHES.items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected
    cells = [p.get_text() for p in BeautifulSoup((HERE / 'publisher-S1-notebook.html').read_text(),
                                                'html.parser').select('div.input_area pre')]
    assert cells == json.loads((HERE / 'sources/S1-notebook-code-cells.json').read_text())
    assert cells[2] + '\n' == (HERE / 'sources/S1-NoisyConnorStevens.py').read_text()
    assert 'dt  = 3e-5' in cells[3] and '0.0019/np.sqrt(dt)' in cells[5]
    assert "compile(backend='cuda'" in cells[5]
    driver = (HERE / 'sources/neural-20191016-neural-basemodel.py').read_text()
    cuda = (HERE / 'sources/neural-20191016-neural-codegen-cuda.py').read_text()
    backend = (HERE / 'sources/neural-20191016-neural-backend.py').read_text()
    assert 'self._update(d_t*self.Time_Scale, **kwargs)' in driver
    assert "solver = kwargs.pop('solver', 'forward_euler')" in driver
    assert 'states.{{ key }} += dt * gstates.{{ key }};' in cuda
    assert "func = 'curand_normal(&seed)'" in cuda
    assert 'return "({0}+{1}*{2})".format(args[0], args[1], func)' in cuda
    assert 'curand_init(clock64(), nid, 0, &seed[nid]);' in cuda
    assert cuda.index('forward(states, gstates, dt);') < cuda.index('clip(states);') < cuda.index('post(states\n')
    assert '\n            d_t,\n            *args)' in backend  # No additional CUDA timestep scale.

    Notebook, namespace, FBL = source_classes()
    assert Notebook.Time_Scale == 1000 and Notebook.Default_Params['sigma'] == 2.05
    assert Notebook.Default_Params == FBL.Params
    dt = 3e-5
    transitions, gates = [], []
    # Prescribed nonzero standard-normal innovations exercise source noise arithmetic
    # without inventing an unrecorded cuRAND seed or estimating population firing.
    innovations = np.array([.5, -.25, 1., -1.5, .75])
    for voltage in (-70., -60., -50., -40., -30., 0.):
        model = Notebook()
        for key, value in {**Notebook.Default_Params, **Notebook.Default_States}.items():
            setattr(model, key, value[0] if isinstance(value, tuple) else value)
        model.v = voltage
        model.sigma = .0019 / math.sqrt(dt)
        values = iter(innovations)
        namespace['random'].gauss = lambda mean, sigma: mean + sigma * next(values)
        loc = model.ode(stimulus=10.)
        code = {key: float(loc[key]) for key in appendix_gates(voltage)}
        fbl = FBL(v=voltage)
        fbl_loc = fbl.gradient(stimulus=10.)
        assert all(np.isclose(code[k], fbl_loc[k][0], rtol=1e-13, atol=1e-14) for k in code)
        paper = appendix_gates(voltage)
        assert not np.isclose(code['n_inf'], paper['n_inf'])
        assert not np.isclose(code['m_inf'], paper['m_inf'])  # Time-unit conversion cannot change equilibria.
        assert np.isclose(code['tau_a'], paper['tau_a'])
        assert np.isclose(code['tau_b'], paper['tau_b']) and np.isclose(code['b_inf'], paper['b_inf'])
        gates.append(dict(voltage_mV=voltage, notebook=code, printed_appendix=paper,
                          notebook_over_printed_tau={q: code['tau_' + q] / paper['tau_' + q]
                                                    for q in ('n', 'm', 'h')},
                          max_p_or_a_inf_absolute_difference=abs(code['a_inf'] - paper['a_inf'])))
        raw_noise = []
        for key, z in zip(('n', 'm', 'h', 'a', 'b'), innovations):
            q = getattr(model, key)
            drift = (code[key + '_inf'] - q) / code['tau_' + key]
            source_step = dt * 1000 * getattr(model, 'd_' + key)
            expected_step = dt * 1000 * drift + 1.9 * math.sqrt(dt) * z
            assert np.isclose(source_step, expected_step, atol=1e-14, rtol=1e-13)
            raw_noise.append(source_step - dt * 1000 * drift)
            setattr(model, key, np.clip(q + source_step, 0., 1.))
        model.v = np.clip(voltage + dt * 1000 * model.d_v, -80, 80)
        model.refactory += dt * 1000 * model.d_refactory
        model.post()
        assert 0 <= model.spike <= 1 and -80 <= model.v <= 80
        transitions.append(dict(initial_voltage_mV=voltage,
                                prescribed_standard_normal_innovations=innovations.tolist(),
                                preclip_noise_increments=raw_noise,
                                clipped_gates={key: float(getattr(model, key)) for key in ('n', 'm', 'h', 'a', 'b')},
                                post_voltage_mV=float(model.v), spike=float(model.spike)))
    model.v1, model.v2, model.v, model.refactory = -60., -20., -30., 0.
    model.post()
    assert model.spike == 1 and model.refactory == -1.
    model.v1, model.v2, model.v = -60., -20., -30.
    model.post()
    assert model.spike == 0  # Identical local maximum is withheld during the source refractory period.
    noise = []
    for h in (1e-5, 3e-5, 1e-4):
        sigma = .0019 / math.sqrt(h)
        nb_sd, fixed_sd = 1000 * h * sigma, 1000 * h * 2.05
        assert np.isclose(nb_sd ** 2 / h, 1.9 ** 2)
        noise.append(dict(dt_s=h, notebook_sigma_parameter=sigma, notebook_step_sd=nb_sd,
                          notebook_diffusion_per_sqrt_s=nb_sd / math.sqrt(h),
                          notebook_variance_per_s=nb_sd ** 2 / h,
                          fixed_sigma_2_05_step_sd=fixed_sd,
                          fixed_sigma_2_05_diffusion_per_sqrt_s=fixed_sd / math.sqrt(h),
                          fixed_sigma_2_05_variance_per_s=fixed_sd ** 2 / h,
                          fixed_over_notebook_noise_sd=fixed_sd / nb_sd))
    assert noise[-1]['fixed_sigma_2_05_variance_per_s'] > noise[0]['fixed_sigma_2_05_variance_per_s']
    result = dict(
        source_adjudication='PASS publisher/author notebook identity, historical driver scaling and gate differences',
        source_transition_check='PASS one explicit Euler/clipping/post step at six voltages with prescribed nonzero innovations',
        author_reference='EXECUTABLE transition law for pinned source; native CUDA notebook not run',
        paper_figure_A2_reproduction='OPEN: printed equations/noise differ; figure-specific version/protocol/seed absent',
        biological_validation='NOT_RUN', runtime_integration='NONE', M3_full_gate='OPEN',
        source_sha256=HASHES, source_driver_revision='bc4deffe611cdd72d510f744bf816aa56debe35d',
        timestep_noise=noise, gates=gates, source_transition_examples=transitions,
        algebra=dict(notebook='delta_gate_noise = 1000*h*(0.0019/sqrt(h))*Z = 1.9*sqrt(h)*Z',
                     fixed_sigma='delta_gate_noise = 2050*h*Z; diffusion = 2050*sqrt(h)',
                     printed_if_t_seconds='sigma=2.05 implies diffusion 2.05/sqrt(s), distinct from 1.9',
                     printed_if_t_milliseconds='sigma=2.05 implies diffusion 2.05*sqrt(1000)/sqrt(s)',
                     limit='Preclipping moments only; clipping and spike rates need separate timestep checks'),
        source_execution_boundaries=[
            'S1 notebook is a 50 x 50 population illustration, binding-rate sweep and dr=10; not Fig A2/Fig4 configuration',
            'No neural/CUDA/cuRAND version pin in notebook; selected historical commit is a compatible prepublication candidate',
            'Clock64 cuRAND seeds unrecorded; curand_normal uses its own precision even with float64 states',
            'Gate [0,1] and voltage [-80,80] clipping, local maximum >-30 mV, 1 ms refractory are source conventions',
            'Printed appendix uses .38 tau factors, .7 alpha_h and different voltage offsets; notebook/CPU use3.8,.07 and shifts',
            'Printed p_inf exponent .3333 differs slightly from exact cube root in notebook/CPU',
            'Original native imports require PyCUDA/compatible historical Python/compiler; not installed or executed here',
            'Setup metadata says BSD; exact neural license text/variant is not recovered'],
        check_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE / 'source-check.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('source_adjudication', 'source_transition_check',
                                            'author_reference', 'paper_figure_A2_reproduction')}, indent=2))


if __name__ == '__main__':
    main()

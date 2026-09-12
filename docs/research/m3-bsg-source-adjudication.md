# M3 — Original BSG source adjudication

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

**The publisher's S1 Notebook supplies an executable author-code transition law. It does not resolve the contradictory equations in the printed S1 Appendix or reproduce Figure A2.** The notebook's effective gate diffusion is `1.9 s⁻¹ᐟ²` before clipping, using its explicit `sigma=0.0019/sqrt(dt)` and the historical driver's seconds-to-milliseconds conversion. The printed appendix and executable notebook also disagree on gating kinetics and steady gate values; changing time units cannot reconcile those differences.

The adjudication evaluated source expressions without fitting parameters or running a stochastic population experiment. A small runnable source check (original artifact `m3/bsg-source-audit/check_source.py`) verifies the source chain and evaluates single transitions with prescribed nonzero Gaussian innovations. Its receipt (original artifact `m3/bsg-source-audit/source-check.json`) keeps paper-figure reproduction, biological validation and M3 open.

## Exact recovered sources

The [official publisher S1 Notebook](https://journals.plos.org/ploscompbiol/article/file?type=supplementary&id=10.1371/journal.pcbi.1007751.s004) and the [author-hosted notebook](https://antenna.neuronlp.fruitflybrain.org/notebook.html) are **byte-identical**: 2,751,608 bytes, SHA-256 `e8af6ba236fd0e56d37e90320499e80b736cf5c897384fab0b69a35e0743f0ef`. Both HTML files, their nine code cells and the extracted `NoisyConnorStevens` class are retained in bsg-source-audit (original artifact `m3/bsg-source-audit`). Thus the notebook's `0.0019/sqrt(dt)` override is in the published supplement, not merely a later website variant.

The notebook links to [`chungheng/neural`](https://github.com/chungheng/neural) without a revision. Git history was recovered. The latest first-parent ancestor of retrieved HEAD before publication on 2020-04-14 is [`bc4deffe611cdd72d510f744bf816aa56debe35d`](https://github.com/chungheng/neural/tree/bc4deffe611cdd72d510f744bf816aa56debe35d), dated 2019-10-16. Its model driver, CUDA generator, backend and setup metadata are retained with Git blob IDs and SHA-256 hashes in source-provenance.json (original artifact `m3/bsg-source-audit/source-provenance.json`). This is a compatible publication-era driver, **not proof of the revision used by the authors**. The retrieved 2021 HEAD is separately identified there.

The historical source chain is explicit:

- `Model.update` passes `dt * Time_Scale` to the backend; the notebook sets `Time_Scale=1000`, with external `dt=3e-5 s`.
- The notebook does not override the default forward-Euler solver. The CUDA backend passes that scaled timestep to its kernel without another time scale.
- The generator converts `random.gauss(0, sigma)` to `sigma * curand_normal(&seed)`, then updates each dynamic state by `dt * derivative`.
- The CUDA kernel clips the gates to `[0,1]` and voltage to `[-80,80]`, then executes `post`. Its spike detector uses the three-sample local maximum, previous voltage `>-30 mV`, and a 1 ms refractory interval.

The audit executes the notebook arithmetic and postprocessing directly, with only an added return of local intermediates for inspection. It also compares its gate functions against the separately pinned OlfTrans CPU source; they agree at all six checked voltages. The check does not import the historical driver, compile CUDA, or claim native-backend equivalence.

## Noise: the resolved quantity and its limit

For timestep \(h\) in seconds and a standard-normal innovation \(Z\), the source's preclipping increment is

$$
\Delta q_{\rm noise}=1000h\sigma Z.
$$

The notebook's explicit override therefore gives

$$
\sigma=\frac{0.0019}{\sqrt h},\qquad
\Delta q_{\rm noise}=1.9\sqrt h\,Z,
\qquad\frac{\operatorname{Var}(\Delta q_{\rm noise})}{h}=3.61\ {\rm s}^{-1}.
$$

Keeping the class default `sigma=2.05` instead gives \(\Delta q_{\rm noise}=2050hZ\), whose effective diffusion is \(2050\sqrt h\ {\rm s}^{-1/2}\). It changes with the integration timestep.

| External timestep | Notebook increment SD | Fixed `sigma=2.05` increment SD | Notebook diffusion | Fixed-parameter diffusion |
|---|---:|---:|---:|---:|
| 10 µs | 0.00600833 | 0.0205000 | 1.9 s⁻¹ᐟ² | 6.48267 s⁻¹ᐟ² |
| 30 µs, published notebook | 0.01040673 | 0.0615000 | 1.9 s⁻¹ᐟ² | 11.22831 s⁻¹ᐟ² |
| 100 µs | 0.01900000 | 0.2050000 | 1.9 s⁻¹ᐟ² | 20.50000 s⁻¹ᐟ² |

At the published 30 µs step, substituting the default `2.05` would increase preclipping noise SD by **5.90964×**. This is an algebraic result, not a firing-rate experiment. Clipping changes increment moments near state bounds; timestep-invariant preclipping diffusion does not prove timestep-invariant clipped dynamics, spontaneous firing or stimulus responses.

S1 Appendix Eq. A1 calls its noise Brownian and gives `sigma=2.05`; it does not resolve the Brownian time unit against the executable override. If its Brownian parameter uses seconds, the diffusion would be `2.05 s⁻¹ᐟ²`; if it uses milliseconds, it would be `2.05*sqrt(1000) s⁻¹ᐟ²`. Neither interpretation justifies silently replacing the notebook's declared setting. No setting was selected by fitting an 8 spikes/s target.

## Gate equations: a second, independent discrepancy

The original appendix pages were rendered and visually inspected, including page 3 (original artifact `m3/bsg-source-audit/appendix-3.png`). The following differences are present in the rendered publication, not introduced by PDF text extraction:

| Component | Printed S1 Appendix | Publisher S1 Notebook and OlfTrans CPU |
|---|---|---|
| `tau_n`, `tau_m`, `tau_h` rate multiplier | `0.38` | `3.8` |
| `alpha_h` prefactor | `0.7` | `0.07` |
| Potassium activation/deactivation offsets | `V+55`, `V+65` | `V+50+ns`, `V+60+ns`, with `ns=-4.3` |
| Sodium activation/deactivation offsets | `V+40`, `V+65` | `V+35+ms`, `V+60+ms`, with `ms=-5.3` |
| Sodium-inactivation offsets | `V+65`, `V+35` | `V+60+hs`, `V+30+hs`, with `hs=-12` |
| A-channel activation exponent | `0.3333` | Exact cube root |

At `V=-60 mV`, the check obtains:

| Gate quantity | Printed expression | Executable notebook |
|---|---:|---:|
| `n_inf` | 0.39626825 | 0.25432229 |
| `m_inf` | 0.09364195 | 0.02785062 |
| `h_inf` | 0.87784880 | 0.89619317 |
| Numeric `tau_n` | 27.05975176 | 2.97539219 |
| Numeric `tau_m` | 0.78721537 | 0.04764461 |
| Numeric `tau_h` | 4.23751946 | 1.84902722 |

The executable time constants are in its internal milliseconds. The printed column records the literal numerical expressions without inventing an unprinted time-unit reconciliation. The different dimensionless steady-state values `n_inf` and `m_inf` alone rule out a global time conversion as the explanation. The A-channel time constants and inactivation steady state agree; its printed rounded activation exponent produces a smaller discrepancy, at most `3.3644e-5` over the six checked voltages. Conductance coefficients/reversal values agree numerically; this does not identify native-cell capacitance, area or conductance units experimentally.

## Executable transition law

The author's **specified discrete transition law** is executable independently of behavioral fitting: use the supplement's equations, its noise override and step, the historical forward/clipping/post order, and an explicitly recorded new random stream. The audit demonstrates individual transitions with nonzero prescribed innovations at six voltages, plus the source's peak-detection and refractory behavior. The subsequent [BSG reference](m3-bsg-source-reference.md) uses this transition law without choosing a diffusion coefficient by fitting.

This does not recover the original stochastic trajectories. The driver initializes cuRAND with `clock64()` and neuron IDs; the original GPU seeds were not recorded. It uses `curand_normal` even for double-precision state arrays. The notebook does not pin Python, `neural`, code generator, CUDA or cuRAND versions. The adjudication did not execute the historical CUDA notebook. Exact replay would require its original software versions and random-state record. A CPU implementation with a declared new random stream would be a source-law reference, not a bitwise replay of the original CUDA output.

The concrete published notebook is also a **population illustration**: 50 receptor groups × 50 OSNs, a binding-rate sweep, `dr=10`, a 3 s run with a 100 ppm step from 0.5–2.5 s, and 20 ms PSTH windows shifted by 10 ms. It is not the Figure 4 fitted Or59b–acetone configuration and does not contain the Figure A2 current/noise sweep procedure. Its OTP parameters and state/recording order must remain attached to that scope rather than silently replacing the separate frozen Figure 4 OTP reference.

## Exact remaining Figure A2 gap

Figure A2 plots an F–I family for noise levels 0–2.5 and the appendix associates `sigma=2.05` with about 8 spontaneous spikes/s. The supplement does not establish which of the contradictory gate equations and Brownian conventions generated that figure. The recovered notebook supplies neither the figure's sweep executable/configuration nor its raw numerical curves, sampling duration, burn-in/averaging rule, timestep and random-state record. Its different population protocol cannot fill those gaps.

The next source-specific requirement is an author version/correction or the figure-generating source and configuration that ties those choices to Figure A2. A declared notebook-model reference may be run as its own comparison; selecting constants because they visually match Figure A2 would be calibration and would not settle source provenance. This adjudication reports **author transition law: executable; native notebook: not run; Figure A2 reproduction: open; biological validation: not run**.

## Check and attribution

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The historical source check used NumPy and Beautiful Soup to validate frozen notebook/driver/appendix hashes, notebook byte/code identity, the exact driver scaling and noise mapping, unrecorded seed policy, clipping/post order, six-voltage gate comparisons, and the algebraic noise dependence at three timesteps. Its result is recorded in source-check.json (original artifact `m3/bsg-source-audit/source-check.json`).

Attribution: Lazar AA and Yeh CH, *A molecular odorant transduction model and the complexity of spatio-temporal encoding in the Drosophila antenna*, PLOS Computational Biology 16(4), e1007751 (2020), [article and supplementary materials](https://doi.org/10.1371/journal.pcbi.1007751). The retained article XML declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the notebook is its published S1 supplementary artifact. The linked driver names Chung-Heng Yeh as author and declares “BSD” in `setup.py`, but the inspected historical and current trees contain no license text identifying its exact variant/conditions. That incomplete driver license record is retained as evidence; the separate OlfTrans BSD-3-Clause license is not assigned to it by inference.

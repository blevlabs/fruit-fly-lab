# M3 — Published OlfTrans deterministic reference

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

The isolated [reference module](../../research/olftrans_reference.py) runs the published Or59b–acetone odor transduction equations on the nine retained `/elife15` concentration waveforms. It reuses the original FlyBrainLab `OTP` functions with the Figure 4 constants and explicit paper rectification. Output is **modeled transduction current in pA**. Biological current validation remains open: the recovered physiology contains averaged firing rates, not matched measured transduction currents.

This isolated reference does not extend acetone parameters to methyl acetate or ethyl acetate, or equate source female recordings with individual MaleCNS cells. This study does not close M3.

## Reproduction record

The implementation uses NumPy, SciPy and h5py.

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The historical check produced reference-check.json (original artifact `m3/olftrans-reference/reference-check.json`) and waveforms.npz (original artifact `m3/olftrans-reference/waveforms.npz`). The NPZ retains source concentration, source PSTH values and their separate original time arrays, plus five dynamic model states, rectified drive and current. Names include units where dimensional: `*_stimulus_ppm`, `*_model_current_pA`, `*_measured_psth_spikes_per_s`, `stimulus_time_s`, and `*_psth_time_s`. Model states use `(curve, time)` order; curve indices retain the original HDF5 order. They are three stimulus conditions per shape, not three identified flies or 31 anatomical replicates.

## Source and configuration authority

The source is [Lazar and Yeh 2020](https://doi.org/10.1371/journal.pcbi.1007751), Eqs. 2–7, Table 2, Figure 4 and S1 Appendix; the source-configuration record (original artifact `publication-review/flybrainlab-sources/olftrans-replay-boundary.json`) freezes its configuration. The released implementation is [OlfTrans CPU model at `3f873eaf`](https://github.com/FlyBrainLab/OlfTrans/blob/3f873eafba3a21b8fcb27231b49835df1d3cbc0c/olftrans/cpu/model.py). A byte-for-byte source copy (original artifact `m3/olftrans-reference/sources/OlfTrans-cpu-model.py`) is retained. The module loads just its `Model` and `OTP` class definitions from the parsed source; it does not import OlfTrans, initialize its optional data/runtime dependencies, or load its BSG class.

With filtered concentration \(u_h\), derivative \(\dot u_h\), bound-receptor fraction \(x_1\), co-receptor gate \(x_2\), and calcium-feedback gate proxy \(x_3\), the reference uses:

$$
\ddot u_h=-2\alpha_1\beta_1\dot u_h+\alpha_1^2(u-u_h),\qquad
v=\max(0,u_h+\gamma\dot u_h),
$$
$$
\dot x_1=bv(1-x_1)-dx_1,\quad
\dot x_2=\alpha_2x_1(1-x_2)-\beta_2x_2-\kappa x_2^{2/3}x_3^{2/3},\quad
\dot x_3=\alpha_3x_2-\beta_3x_3,
$$
$$
I=I_{\max}\frac{x_2}{x_2+c}\quad(p=1).
$$

`x3` is a dimensionless model gate, not a calibrated calcium concentration. The fractional-power feedback and peri-receptor approximation are published model hypotheses, not independently measured molecular reaction laws.

| Frozen quantity | Value and units |
|---|---|
| Binding / dissociation | `br=0.0217 (ppm·s)⁻¹`, `dr=2.94 s⁻¹` |
| Peri-receptor filter / gradient | `a1=45 s⁻¹`, `b1=0.8`, `gamma=0.2105 s` |
| Co-receptor rates | `a2=146.1 s⁻¹`, `b2=117.2 s⁻¹` |
| Calcium-feedback rates | `a3=2.539 s⁻¹`, `b3=0.9096 s⁻¹`, `kappa=8841 s⁻¹` |
| Current saturation | `c=0.06546`, `p=1`, `Imax=62.13 pA` |

These are fitted Figure 4 parameters. The released CPU defaults instead set `br=dr=1` and `gamma=0.215`; other OlfTrans/EOScircuits backends also differ in current scale and kinetics. The paper's separate Dataset 2 fit uses `br=0.0211`, `dr=2.65`; it is not substituted here because Figure 4 explicitly uses the Dataset 1 values above. No local gain, time shift, parameter search, baseline subtraction or outcome selection was applied.

The published fitting objective includes white noise and Dataset 1 pulse-like responses. The paper also performs a second fit with Dataset 2 pulse-like responses and the same white-noise input. Consequently a white-noise match would be calibration replay, and step waveforms are not claimed as independent holdouts here. Ramp and parabola remain published waveform holdout candidates with frozen parameters; there is **no biological holdout score** in this artifact because it does not generate spikes and lacks measured current targets. This is not a prospective holdout experiment, nor a reproduction of the paper's PSTH error table.

## Protocol and data preservation

The [author-hosted HDF5](http://amacrine.ee.columbia.edu:15000/data.h5) (original artifact `antenna-data.h5`) has SHA-256 `89ba48164a6db16d14ad2a9b2b8798d5babfcb0f154140041e7053b3b4553715`. All selected groups explicitly identify `acetone` and `or59b`. Each has three nonnegative finite concentration arrays with 17,499 samples over 0–3.4996 s at 0.0002 s spacing, and three PSTHs with 139 samples over 0–3.45 s at 0.025 s spacing. Raw sample order and source values are preserved; unlike the upstream convenience loader, this reference does not trim the concentration support to the PSTH or sort curves by amplitude.

[Kim et al. 2015](https://doi.org/10.7554/eLife.06651), the source experiment, calibrated its photoionization-detector voltage to ppm and advanced the detector recording by 2 ms during preprocessing. The reference does not repeat that advance. Its female flies were 2–5 days post-eclosion, genotype `NP3062-GAL4/NP3062-GAL4;UAS-mCD8::GFP/UAS-mCD8::GFP;+/+`. Or59b OSN action potentials were isolated from extracellular sensillum recordings. The reported PSTH uses 100 ms bins with 75 ms overlap. The HDF5's convention for bin-center versus bin-edge timestamps remains unresolved; no additional alignment is invented. Per-fly/per-trial identities and raw spike events are absent from this selected data.

For numerical integration, source concentration is interpolated linearly between samples. Every run starts its five dynamic states at zero at source `t=0`; no prehistory is available, so this is an explicit initial-condition choice, not a measured resting state. The source concentration tails and nonzero measurement baseline are retained. Negative concentrations would be rejected rather than silently clipped. The ambiguous identities and time units in `/multiple_pairs` are excluded.

## Numerical check and released-code differences

The published ODE is evaluated with SciPy DOP853. The retained `OTP.gradient()` and `OTP.non_gradient()` functions provide its derivatives and algebraic expressions. Three differences from a literal released CPU time-step replay are deliberate and visible:

1. Paper Eq. 2 rectifies `v`; the released CPU `non_gradient()` does not. The check confirms that omission on a declining-input state, then the adapter applies the paper's rectification before receptor binding at every ODE evaluation.
2. The adaptive ODE solver replaces the source's forward-Euler update and its hard state clipping. In particular, the peri-receptor filter is linear and may undershoot; only the concentration drive `v` is rectified. Material negative gate states or states above the receptor/channel domain cause a failed check. Tiny numerical tolerances are not a new physiological bound.
3. Algebraic values are evaluated at the current ODE state. The source CPU and GPU stepping/recording order is not claimed to be identical. The source current function has no general `p` exponent, but its algebra agrees exactly with the frozen published `p=1`.

The one runnable check verifies source/data/configuration hashes, explicit constants, source identity and time spacing, the filter's analytic step response, the analytically constrained steady transduction current, transient adaptation, exact zero input, fresh-state repeatability and malformed-protocol rejection. It then reruns all nine source waveforms with tighter relative/absolute tolerances and halves the maximum solver step. The fixed acceptance margin is **0.001 pA** maximum current difference, a numerical margin with no claimed biological meaning. The JSON receipt gives actual errors and solver versions/evaluation counts. The saved traces use the finer solution.

The completed check used Python 3.12.7, NumPy 1.26.4, SciPy 1.13.1 and h5py 3.11.0. Its maximum current difference was **0.0000650759 pA** across all nine curves. The filter's maximum analytic error was `1.70e-13 ppm`; the 50 ppm constant-input equilibrium was `8.2412989443 pA`, reached within `1.02e-7 pA` at 10 s. All 31 saved arrays were finite. The smallest saved gate value was approximately `−8.2e-16`, within numerical precision and retained without clipping. These are numerical results, not agreement with measured current.

There is no comparison of pA with spikes/s, no fitted conversion between them, and no claim of recovered spontaneous firing. CPU/GPU numerical equivalence and full source-figure reproduction remain unverified.

## Remaining boundaries

At the time of the OTP study, the BSG source conventions were unresolved. S1 Appendix defines Brownian gate noise with `sigma=2.05`, while the released CPU applies a Gaussian term inside the gradient before multiplying by the millisecond time step. The NeuroDriver example also uses explicit step-dependent noise scaling, and the source family has current-unit/default differences. The [subsequent source adjudication](m3-bsg-source-adjudication.md) resolves the notebook transition law while preserving the appendix discrepancy. PSTH averaging and bin timestamp semantics still require resolution before comparing output with the measured waveforms.

Runtime transfer additionally requires physical odor exposure at supported receptor organs, native preparation and cell-type correspondence, declared state/reset behavior, and independent physiological comparison. The earlier Or59b–DM4 anatomical correspondence is not individual physiological calibration. This artifact supplies a bounded mechanistic reference and numerical evidence, not a complete sensory organ or embodied capability.

## Attribution and reuse

The copied OlfTrans source is copyright © 2021 Tingkai Liu, distributed under BSD-3-Clause. Its complete copyright, conditions and disclaimer (original artifact `m3/olftrans-reference/sources/LICENSE.txt`) are retained with the source. Equation and parameter attribution: Lazar AA and Yeh CH, *A molecular odorant transduction model and the complexity of spatio-temporal encoding in the Drosophila antenna*, PLOS Computational Biology 16(4), e1007751 (2020).

The original antenna database is FFBO's *In vivo Antenna Electrophysiology Recordings*, alpha v0.1. Its retained README/license declaration (original artifact `publication-review/flybrainlab-sources/antenna-README.txt`) assigns [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/) to the database and [Database Contents License 1.0](https://opendatacommons.org/licenses/dbcl/1-0/) to individual contents. The source waveform/PSTH extracts in the NPZ preserve that attribution and those terms. Computed current/state traces are model outputs and are separately labeled. The database license is distinct from the source code's BSD license.

## Subsequent BSG source resolution

The [published-notebook audit](m3-bsg-source-adjudication.md) later resolves its pre-clipping gate diffusion as 1.9/sqrt(s) and establishes an executable transition law. The [finite source reference](m3-bsg-source-reference.md) checks that law and exact state/RNG continuation. The printed appendix and Figure A2-specific configuration still differ or remain unavailable; the deterministic OTP results and their biological limits above are unchanged.

# M3 — Composed odor concentration-to-spike source reference

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

The source-reuse study connected the two components: the nine saved fine-resolution **paper-OTP current waveforms** drive the checked **executable-notebook BSG** at 15 µs. All 216 simulated paths completed with finite states, producing **31,003 retained spike events**. Original waveform ordering, current values, default initial states and nonzero gate noise were preserved. Reference receipt (original artifact `m3/composed-odor-reference/reference-check.json`).

This is the documented combination of two source configurations. It is not a reproduction of Figure A2 or Figure 4, a physiological gate pass, or a held-out biological validation. No measured-PSTH alignment or biological RMSE was selected. This study does not close M3.

## Exact composition and protocol

The [BSG reference](../../research/bsg_reference.py) provides the `--composed-odor` entry point; its checked `BSG` class is unchanged. Its class AST was compared against the preserved current-assay source snapshot (original artifact `m3/bsg-source-reference/source-snapshot/bsg_reference-current-assay.py.txt`), whose bytes match that earlier assay's recorded source hash.

| Component or condition | Choice |
|---|---|
| Upstream | Saved fine OTP traces (original artifact `m3/olftrans-reference/waveforms.npz`), verified against their original receipt hash |
| Source waveforms | `/elife15/step`, `/elife15/ramp`, `/elife15/parabola`; original indices `0,1,2` for each |
| Receptor / chemical | Or59b / acetone, with the frozen Figure 4 OTP parameters |
| Downstream | Original notebook gate constants, clipping/order, peak detector and nominal refractory counter |
| Noise | Nonzero `1.9 s⁻¹ᐟ²` gate diffusion; source parameter `sigma=0.0019/sqrt(15e-6)` |
| Replicas | 24 independently driven simulated paths per waveform, 216 total |
| RNG | New NumPy PCG64 stream: SeedSequence entropy `20260912`, child spawn key `[2]` |
| Initial state | Source defaults at `t=0`; no warmup, burn-in, fitted state or additional time shift |
| Step | Constant 15 µs; 233,306 full steps |
| Input interpolation | Piecewise-linear saved current; evaluate at the left edge `t=k*dt` of each BSG step |
| Terminal rule | End at 3.49959 s; omit the final approximately 10 µs of the source support ending at 3.4996 s; no extrapolation or fractional last step |
| Summary rates | Entire simulated interval, including the declared initial-state transient |

The saved currents are in the source's pA convention and source time is in seconds. Their range is `−5.76e-18` to `29.6824714 pA`; the tiny negative minimum is retained OTP numerical roundoff. No input current was clipped, rescaled, baseline-subtracted or retimed. The BSG's internal voltage/gate clipping remains exactly as specified by its source. No gain, noise or timing parameter was fit to the measured PSTH.

The upstream preparation remains the source experiment's 2–5-day female flies and recorded Or59b–acetone responses, as documented in the OTP report. These simulations are receptor-class model paths, not additional biological replicates or individual MaleCNS-cell measurements. Acetone parameters are not relabeled as methyl acetate or ethyl acetate.

## Saved outputs

spikes.npz (original artifact `m3/composed-odor-reference/spikes.npz`) retains every event as `event_neuron_index` and `event_peak_sample_index`, plus exact neuron-to-waveform and replica mappings, per-replica counts/rates, timestep and duration. The peak timestamp is `event_peak_sample_index * dt`; the source's detector emits the flag one timestep later. This distinction is explicit so later binning need not guess an extra timestep shift.

The raw events recount exactly to all saved counts. They are globally time-ordered. final-state.json (original artifact `m3/composed-odor-reference/final-state.json`) retains the final source state, parameters, clipping counters and full RNG state. The input trace hash, module/audit hashes, fixed conditions and output hashes are in the reference receipt. The separate event check (original artifact `m3/composed-odor-reference/event-check.json`) records the raw-event recount and refractory-counter finding below. There are no trial-averaged model bins standing in for the raw spike events.

## Per-waveform result

These are whole-trace model rates over 3.49959 s, with descriptive 95% Student-t intervals across the 24 simulated paths. They are not uncertainty intervals for the recorded animals. Original HDF5 curve order is preserved, including its non-monotonic amplitude ordering.

| Waveform / source index | Peak saved OTP current (pA) | Total events across 24 paths | Mean Hz [95% model-sampling interval] |
|---|---:|---:|---:|
| step / 0 | 29.682 | 4,743 | 56.471 [55.382, 57.560] |
| step / 1 | 22.222 | 3,541 | 42.160 [41.178, 43.141] |
| step / 2 | 25.910 | 4,070 | 48.458 [47.253, 49.664] |
| ramp / 0 | 18.320 | 3,978 | 47.363 [46.397, 48.328] |
| ramp / 1 | 14.196 | 2,985 | 35.540 [34.441, 36.639] |
| ramp / 2 | 16.053 | 3,588 | 42.719 [41.820, 43.619] |
| parabola / 0 | 19.311 | 3,144 | 37.433 [36.035, 38.831] |
| parabola / 1 | 16.099 | 2,203 | 26.229 [25.394, 27.064] |
| parabola / 2 | 18.260 | 2,751 | 32.754 [32.048, 33.460] |

All nine conditions are included. Peak current and whole-trace mean firing measure different parts of each time-varying waveform; the table is not a fitted static F–I relationship.

## Finiteness, clipping and a failed stronger timing assumption

All source state arrays remained finite. No voltage-bound clipping occurred. Across the nine waveforms, the fraction of updates requiring gate clipping was `0.089–0.136%` for `n`, `4.597–6.388%` for `m`, `1.563–2.403%` for `h`, `0.00039–0.00082%` for `a`, and `0.527–0.998%` for `b`. Those are measured source-policy effects, not suppressed numerical failures. The earlier current-step reference's single timestep refinement does not prove convergence of this time-varying composition.

A post-run check imposing a **strict interspike interval of at least 1.000 ms failed**: 58 observed intervals were 66 steps, or 0.990 ms. The raw events were retained. Investigation confirmed this is original source behavior rather than a timestamp or adapter error. The counter increments only while negative, and a spike subtracts 1 ms from its existing value instead of resetting it to `−1 ms`. Positive fractional-step residue therefore persists. An isolated check of the retained source counter/post functions emitted forced eligible peaks at steps `1,68,135,201,268,335`, giving intervals `67,67,66,67,67`. At 15 µs the nominal 1 ms counter consequently permits 0.990/1.005 ms quantization. The observed minimum agrees with that source rule; no artificial hard refractory constraint or event filtering was added.

## Why no biological RMSE is reported

The HDF5 contains measured PSTHs sampled every 25 ms, with published 100 ms windows and 75 ms overlap. It does not resolve whether each saved `psth/x` timestamp names a window's left edge, center or right edge, including the source's boundary/prehistory handling and trial-averaging convention. The original PID preprocessing already advanced its concentration signal by 2 ms; this assay does not apply that advance again. Choosing an additional alignment by minimizing error would fit the comparison rather than recover its protocol.

The missing protocol datum is the author's exact definition of the 100 ms window attached to each `/elife15/*/psth/x` timestamp, including any additional spike-versus-stimulus offset and trial-averaging rule. With that definition, the retained raw model events can be binned without selecting an alignment from the outcome. A statistical physiological pass additionally needs trial-level spikes or measurement uncertainty/replicate information and prespecified acceptance margins. The printed-appendix versus executable-notebook model/version discrepancy remains relevant to any Figure A2/4 reproduction claim.

The source-chain assay is complete at this boundary. No biological score, native-cell transfer or full M3 completion is asserted.

## Reproduction record

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The study used NumPy/SciPy and the source audit. Its [implementation](../../research/bsg_reference.py) consumes the upstream OTP NPZ as a frozen artifact; it does not rerun or refit that solver. Attribution and source/license evidence remain in the [OTP report](m3-olftrans-reference.md), [BSG source adjudication](m3-bsg-source-adjudication.md), and [finite BSG reference](m3-bsg-source-reference.md): Lazar and Yeh, [PLOS Computational Biology 16(4), e1007751 (2020)](https://doi.org/10.1371/journal.pcbi.1007751), publisher supplement; retained OlfTrans code under BSD-3-Clause. The author-hosted electrophysiology database's separate ODbL/DbCL terms remain attached to its source data.

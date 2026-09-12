# M3 — Finite author-model current-to-spike reference

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

The [isolated BSG module](../../research/bsg_reference.py) executes the published S1 Notebook's current-to-spike transition law with nonzero gate noise and a declared new random stream. All ten fixed current/timestep conditions completed with finite source states. Saving all ten source state variables plus the RNG at 1.5 s and resuming from JSON reproduced the remainder of the coarse run exactly, including spike flags, final states, clipping counts and observation counts. Machine-readable receipt (original artifact `m3/bsg-source-reference/reference-check.json`).

This is a source-law implementation study. It does not reproduce the original CUDA random trajectories, the conflicting printed appendix SDE, Figure A2, biological electrophysiology or a held-out sensory response. It exercises the downstream current-to-spike component in isolation; this study does not close M3.

## Fixed protocol

The conditions were declared before the first run and retained after checking the result:

| Quantity | Fixed setting |
|---|---|
| Injected current | `0, 5, 20, 50, 100`, using the source's pA label |
| Replicas | 24 independently driven simulated replicas per current and timestep |
| Input duration | Constant current for 3 s from source default initial states |
| Observation | Discard first 1 s; count detected local maxima in `[1,3)` s; divide by 2 s |
| Timesteps | 30 µs, the published notebook step, and 15 µs |
| Gate diffusion | `1.9 s⁻¹ᐟ²`, nonzero; implemented as source `sigma=0.0019/sqrt(dt_s)` |
| Integration | Original simultaneous forward-Euler derivatives; source clipping; then original spike/refractory postprocessing |
| RNG | NumPy PCG64, root SeedSequence entropy `20260912`, independent child spawn keys `[0]` and `[1]` for the two timesteps |
| Parameter choice | Original notebook drift/gate/reversal constants; no fitting or parameter selection from these results |

Within a resolution, normal draws are made in source order `n,m,h,a,b`, each a vector ordered by current then replica. Different replicas consume distinct Gaussian innovations. The two resolutions use independent streams; this is a comparison of sampled firing distributions, not a coupled Brownian-path convergence test. The replicas are simulated paths, not biological animals or MaleCNS cells.

The source peak detector evaluates the previous voltage sample. Counting uses that peak timestamp, `(step-1)*dt`, rather than mislabeling the newly updated voltage as the peak time. The first admitted discrete peak times are 1.00002 s at 30 µs and 1.000005 s at 15 µs. Both are inside the declared `[1,3)` observation window.

Current units are retained as the source's pA label. This study does not infer a particular native cell's capacitance, membrane area, conductance density or physical current calibration from the model's numerical coefficients.

## Observed source-model firing

Intervals below are descriptive 95% Student-t intervals for the mean across 24 simulated replica rates. Every individual count, rate, SD and SEM is retained in the 30 µs assay (original artifact `m3/bsg-source-reference/30us-assay.json`) and 15 µs assay (original artifact `m3/bsg-source-reference/15us-assay.json`).

| Source current (pA) | 30 µs mean Hz [95% interval] | 15 µs mean Hz [95% interval] | Fine minus coarse Hz [95% Welch interval] |
|---:|---:|---:|---:|
| 0 | 4.646 [4.084, 5.208] | 4.021 [3.502, 4.540] | −0.625 [−1.369, 0.119] |
| 5 | 23.792 [22.369, 25.214] | 22.042 [20.645, 23.438] | −1.750 [−3.689, 0.189] |
| 20 | 109.750 [108.415, 111.085] | 107.958 [106.258, 109.659] | −1.792 [−3.899, 0.315] |
| 50 | 228.000 [226.508, 229.492] | 227.458 [225.758, 229.159] | −0.542 [−2.744, 1.660] |
| 100 | 340.854 [339.437, 342.272] | 341.479 [340.107, 342.851] | +0.625 [−1.295, 2.545] |

All five unadjusted timestep-difference intervals include zero. That finding does not establish numerical equivalence or full convergence: the comparison has finite Monte Carlo uncertainty, two resolutions and a short fixed observation window, with no prespecified equivalence margin. It also does not establish biological correctness. In particular, the observed zero-current firing is about 4–5 Hz for this declared author-code reference; no constants were adjusted toward the appendix's approximately 8 Hz statement.

## Source fidelity and numerical limits

The [preceding source adjudication](m3-bsg-source-adjudication.md) established that the author-hosted and publisher S1 Notebooks are byte-identical, and recovered the historical driver that multiplies external seconds by `Time_Scale=1000`. This reference reuses the source extraction and the retained OlfTrans drift/post expressions whose gate functions agree with the notebook. The only stochastic-call substitution replaces the five global `np.random.randn` calls with an instance-owned `Generator.standard_normal`. The published notebook's explicit noise override is used; the class's fixed `sigma=2.05` default is not substituted for it.

All source gates and constants remain intact: `ms=-5.3`, `ns=-4.3`, `hs=-12`, `gNa=120`, `gK=20`, `gL=0.3`, `ga=47.7`, `ENa=55`, `EK=-72`, `EL=-17`, `Ea=-75`, and `refperiod=1 ms`. Gates are clipped to `[0,1]`, voltage to `[-80,80]`, before the local-maximum detector with previous voltage `>-30 mV` and the source refractory logic. The code assigns fresh arrays when advancing state so that `v1` and `v2` preserve the historical samples used by the notebook/CUDA transition. Calling the old vectorized CPU model's in-place update directly would allow voltage-history aliasing; that update path is not used.

The runnable check compares a vector step against six previously audited scalar-notebook transitions with prescribed nonzero innovations. Independent review also checked 30 successive scalar/vector source steps, including spike history and a singular-rate branch. The real assay uses the declared PCG64 streams throughout.

Clipping is part of this source law and is measured rather than hidden. Across the five currents, the sodium-activation gate `m` required clipping on **1.57–14.96%** of coarse updates and **0.85–9.54%** of fine updates, including burn-in. The voltage bound was hit on at most **0.001%** of coarse updates and zero fine updates. The per-condition counts for all six bounded variables are retained. Preclipping diffusion is timestep-consistent algebraically; the appreciable and resolution-dependent gate clipping is an additional reason not to infer convergence solely from mean rates.

All source states remained finite; no current condition was omitted. Original CUDA/cuRAND precision and GPU-clock seeds were not recreated. These seeded CPU results therefore define a reproducible source-law reference, not the original sample paths.

## Exact continuation

The coarse run saves a checkpoint at 1.5 s (original artifact `m3/bsg-source-reference/continuation-checkpoint.json`), after 50,000 steps. It includes `spike`, `v1`, `v2`, `v`, `n`, `m`, `h`, `a`, `b`, `refactory`, all parameters, timestep/step count, full PCG64 state, current inputs, clipping counts and observation counters. Derived gradients are recomputed from these states on the next step.

Reading that JSON into a fresh object and executing the remaining 50,000 steps exactly matched the uninterrupted run's full final snapshot and all per-replica spike counts. The complete tail sequence of spike flags also matched, SHA-256 `e6b032426452b0634e73999823766ef39078eb34138b419667defb4a5efd147f`. This is exact continuation within the declared CPU implementation and library versions; it is not restoration of an original author CUDA trajectory or of the embodied fly.

## Corrected implementation issue

The first coarse analysis used `round(1 s / 30 µs)`, which could admit the peak sample at 0.99999 s while declaring `[1,3)`. Review identified the error. The final implementation uses `ceil`, checks the discrete boundary, and reran the unchanged conditions with the same random streams. None of the replica counts changed because no spike flag occurred in that excluded sample. A rerun receipt self-hash issue was also corrected by excluding the receipt itself from the artifact hash list. The superseded results and source copy (original artifact `m3/bsg-source-reference/superseded-window-boundary/reason.txt`) are retained for audit; the main assay files are the corrected run.

## Reproduction record and remaining work

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The historical study used Python 3.12.7, NumPy 1.26.4, SciPy 1.13.1 and Beautiful Soup. Assay JSONs, final states, the continuation checkpoint and hashes are in bsg-source-reference (original artifact `m3/bsg-source-reference`). The reference simulation streams counts and a spike-sequence hash rather than retaining a voltage movie; the fixed protocol, initial seed and saved checkpoint define the original reproduction conditions.

A subsequent [concentration-to-spike study](m3-composed-odor-reference.md) combines these OTP and BSG components with their distinct configuration provenance declared. Waveform/PSTH alignment and independent physiological comparison remain unresolved. The printed appendix's gate-factor/voltage-offset discrepancies and the missing Figure A2 figure-specific configuration remain as documented in the source adjudication. Neither a monotonic source-model F–I curve nor exact continuation resolves those biological/source-version questions.

Attribution: [Lazar and Yeh, PLOS Computational Biology 16(4), e1007751 (2020)](https://doi.org/10.1371/journal.pcbi.1007751), publisher S1 Notebook; article/supplement CC BY 4.0. Reused OlfTrans CPU functions are copyright © 2021 Tingkai Liu under the retained BSD-3-Clause license (original artifact `m3/olftrans-reference/sources/LICENSE.txt`). The historical `neural` driver's incomplete BSD metadata record remains separate; no unverified license variant was assigned to it.

# Next biological mechanism: adult fast tibia-flexor spike-to-force reference

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**Decision: DATA-BLOCKED.** Select one offline reference assay: whether a causal response to recorded spikes in the adult **81A07 fast tibia-flexor motor unit** predicts independently held-out probe displacement and force under the same restrained-foreleg preparation. Do not fit the live fly or assign this reference to a MaleCNS neuron yet.

This is the most direct recovered route across the present motor-to-force bottleneck: the dataset catalogues synchronized motor-neuron/EMG recordings and probe motion. CM9 supplies electrical measurements without isolated force, while the TDT preparation removes the living excitation–contraction chain. Neither substitutes for this selected assay. The separate 2.5-µs stability work supplies numerical evidence only; it does not supply the missing biology or close M2/M5. **All remaining M0–M12 requirements stay in scope.**

The machine-readable decision is decision.json (original artifact `program/biological-decision/decision.json`). This package uses existing retrieved sources and results only. No raw-trace fit was performed for this decision.

## Exact preparation and identities

The selected source is [Azevedo et al. 2020](https://elifesciences.org/articles/56754), Figure 4 and Methods, with the archived Dataset3 selection (original artifact `program/m2/sources/foreleg-zenodo-Dataset3_SlowInterFast_ForcePerSpike.m`). The reported physiology preparation uses **female flies 1–4 days after eclosion**, the **right foreleg**, constrained proximal structures and tibial loading of a flexible probe; room-temperature saline includes **1.5 mM CaCl₂ and 4 mM MgCl₂, pH 7.2**. Electrical acquisition is 50 kHz and probe video approximately 170 fps. Per-trial age, temperature, genotype, load/pose and channel calibration must come from the actual notes and records; a nominal Methods cohort is not complete per-specimen metadata.

| Role frozen now, before raw traces are read | Source cell/fly and protocol | Source selection | Published archive identity |
|---|---|---|---|
| Calibration anchor | `171102_F2_C1`, `81A07`, fast, `EpiFlash2T` | Trials 47–173; position labels −200/−100/0/100/200 | Dryad **585422**, 369,295,693 bytes |
| Untouched biological holdout A | `171101_F1_C1`, same driver/class/protocol | Trials 16–330; same position-label set | Dryad **585421**, 779,878,231 bytes |
| Untouched biological holdout B | `171103_F1_C1`, same driver/class/protocol | Trials 72–223; same position-label set | Dryad **585423**, 524,538,785 bytes |

All three sets of raw trial arrays remain unread/unretrieved. Published aggregate outcomes are already known, so this is not an unseen-paper test. The source labels are not tibial angles or calibrated loads until the notes/registration establish their meaning and units.

The current motor map, SHA-256 **`ad0761f7b3f572b934cf0406d0e86d7bcb4600ec7b5532dab1e6e0dc6e4bb17b`**, identifies RF `leg.tibia_flexor` candidates **810098, 821635, 827188, 1050031705 and 1050189039**. It does **not** identify which is the 81A07 fast unit. A reference PASS would therefore remain separate from runtime transfer. That transfer additionally needs the exact motor/fiber-territory correspondence, recruited capacity and joint/probe/tendon geometry, plus justification for female-to-male physiological transfer. No ID is selected by axon size or by a desired movement.

## Readouts, equations and identifiability

The primary observation is calibrated probe displacement **y(t)** at actual exposure times, aligned to measured motor spike times **tₖ**. Preserve raw sample indices, voltage/EMG channels and their declared units, exposure timestamps, probe tracking/scale, stimulus parameters, position labels and exclusion notes. Do not assume that `forceProbeStuff.CoM` already has micrometre units from its field name or plot labeling.

The probe relation, after a documented baseline correction, is:

```text
m ÿ + c ẏ + k y = F_probe(t)
```

Use metres, seconds, kilograms, kg/s, N/m and newtons in this equation. The independently replayed static calibration gives **k = 0.223419451 N/m**. Archived source supports **m ≈ 1.702×10⁻⁷ kg** and **c ≈ 1.377×10⁻⁴ kg/s**; uncertainty for the dynamic fit is still missing. Static `k y` and dynamic probe force are different readouts. Neither is tendon F0. [Probe evidence and discrepancies](m2-foreleg-source-notes.md)

The first falsifiable reference is a **linear summation null**, used only offline:

```text
F_probe_increment(t) = Σ K(t − tₖ), with K(t<0)=0
```

K is the effective single-spike probe-force response in newtons per event. Drive the calibrated probe equation forward and compare exposure-averaged predicted displacement with observations. This avoids treating noisy second derivatives of a 170-fps trace as exact force. The directly identifiable response is initially the combined spike-to-probe-displacement transfer; separating K from probe dynamics requires the verified dynamic calibration and adequate temporal information. No kernel is fitted or installed by this decision.

Single-spike records can constrain effective amplitude, latency and waveform **only to their demonstrated timing/SNR resolution**. They cannot separately identify NMJ release gain, depression/recovery constants, calcium scale, excitation/activation time constants, maximum tendon force, moment arms or motor-unit capacity. Doublet peak ratios cannot uniquely identify synaptic depression because twitch overlap and mechanics also affect summation. The published approximate 10-µN fast response and approximately 8.5-ms half-rise are context, not error margins or parameter defaults.

## Calibration, holdout and causal controls

Freeze an accession/trial manifest using metadata before opening force values. At source **position label 0**, with no drug treatment and acquisition-valid records, use the anchor's **even-numbered, exactly-one-spike trials** for calibration. Reserve its **odd-numbered single-spike trials** for technical prediction checks and **all exactly-two-spike trials** for the primary summation test, using actual inter-spike intervals. If those strata do not exist or are too sparse, report INCONCLUSIVE; do not change the split after seeing responses.

Keep both named holdout cells wholly outside fitting, model choice, baseline tuning and margin selection. Their matching position-0 single/doublet trials test replication across flies; do not renormalize each holdout to its peak or fit a new amplitude to its responses. Other positions and higher-count trials remain untouched for later load/pose or train tests; this first PASS would not cover them.

The biological replication unit is an independently recorded **fly/cell**, not a spike, camera frame or repeated trial. Same-cell technical holdouts do not create extra biological N. The two reserved cells are a first replication tranche, not a power calculation. Population claims remain inconclusive unless independent calibration data justify the specimen count and uncertainty model.

Controls required for the claim:

- **Recorded no-spike/sham trials at matched light and load**, if verified in the actual files, test light/tracking artefacts and unobserved recruitment. Source scripts reference zero-spike analysis, but usable records have not been verified. Missing controls block causal attribution.
- **Recorded selective stimulation plus verified neuron/EMG identity** must support the claimed unit's participation. MLA comparisons may help assess central recruitment; MLA is not a glutamatergic NMJ block and cannot be counted as one.
- **Offline zero-event and timing-shuffled predictions** test software causality and timing specificity. They do not replace experimental controls. Nothing except measured spikes and declared physical initial/load conditions enters the predictor.

The recovered `Script_tableOfForcePerSpike.m` path discards fast-unit responses with `peak<10` in its probe-coordinate units. Its relationship to the final published generating path remains unverified. Preserve this source-censored reproduction separately from a **primary uncensored analysis** using outcome-independent acquisition QC. A small response is not a recording failure. The exact dynamic force correction, `CoM` scale, source exclusions and any manual timing overrides must be reconciled before biological adjudication.

## Prespecified adjudication

Fix primary endpoints now: displacement-waveform RMS error in µm over actual post-spike exposure samples through +250 ms; signed peak probe-force error in µN; signed **probe-displacement half-rise-time error**, measured from the first motor spike, in ms; and the error in the within-cell doublet/single peak-force ratio. Displacement half-rise is not reconstructed-force half-rise. Compute single- and doublet-waveform errors separately. An unresolved or near-zero single-spike denominator makes the ratio inconclusive, not clipped. Use the source-alignment window **−20 to +250 ms** and retain the source's separately defined peak-window reproduction as a separate output. Preserve actual exposure times and repeated timestamps; do not jitter measurements to make a smoother curve.

**Numerical biological equivalence margins are currently undefined. That absence blocks PASS.** Before unblinding the held-out force responses, obtain independent measurement/dynamic-calibration uncertainty and a defensible biological variability/replication basis, then freeze endpoint margins in µm, µN, ms and dimensionless ratios as appropriate. Do not derive them from model error, a desired force, a successful behavior, the static calibration's R², or its column-holdout residual.

| Verdict | Required evidence |
|---|---|
| **DATA-BLOCKED — current** | Trial bytes, unit/processing provenance, necessary controls or predeclared uncertainty/margins are unavailable. No biological score is issued. |
| **INCONCLUSIVE** | Data permit analysis but identification, replication, power or uncertainty is insufficient; a confidence interval overlaps an acceptance boundary; or selective causal attribution remains ambiguous. Keep the affected gate open. |
| **FAIL — selected reference hypothesis** | With valid preparation, controls and frozen margins, a prespecified held-out endpoint is incompatible with its allowed interval. Reject the linear reference at that scope and investigate the owning transmission/muscle/load mechanism. Do not tune live gains or discard weak responses. |
| **PASS — stated preparation only** | Every prespecified held-out endpoint's 95% error interval lies within its independently justified, pre-unblinding margin; causal controls, numerical adequacy and independent replication also pass. This supports only the tested fast-unit/preparation transfer. It does not identify a MaleCNS unit or close whole-fly biology. |

Implementation and numerical checks are recorded separately. Any biological margin, source stratum or endpoint changed after holdout inspection requires a new untouched test set; it cannot turn the same failed evaluation into PASS.

## Exact blocker and one next action

The existing retrieval receipt (original artifact `program/m2/sources/foreleg-source-manifest.json`) records **zero raw trial bytes**. Ordinary Dryad download routes returned **403**; API downloads returned **401 requiring a current bearer token**. Public previews worked, but subsequent browser verification was blocked by the browser URL security policy. No further access attempt was made for this decision.

**Next decision: admit a verified copy of archive 585422 for metadata-only QA.** Obtain it through the public archive or a source-owner mirror, with its accompanying notes and calibration metadata. This first archive enables extraction feasibility, not biological PASS. Full evaluation also needs the two reserved cells, an uncensored trial audit, dynamic calibration uncertainty and controls. A smaller author-supplied packet containing the named position-0 single/doublet/no-spike records and complete metadata can replace whole-archive transfer if provenance and completeness are verified.

Before analysis, verify the archive digest, expected trial-member names and accompanying metadata. A missing archive leaves the reference data-blocked. Package data requirements are documented in the [results index](../../results/README.md).

Independent work that can change this decision is narrowly defined: recover the trial records; reconcile the existing source's units/force-correction/censoring path; recover independent uncertainty and control records; or establish the exact fast-unit anatomical crosswalk and fiber/load geometry. The first two can make the reference runnable; uncertainty/controls/replication enable adjudication; anatomy enables later runtime transfer. Numerical stability, additional synthetic force checks or another whole-animal run cannot replace these missing data.

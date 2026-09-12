# M2 independent force-calibration results

This note records historical studies from September 2026. Reported checks and source hashes identify those studies; they are not new verification of the packaged software. See [current status](../status.md), the [research roadmap](../roadmap.md), and the [historical provenance archive](../../results/README.md).

Historical results, 2026-09-12 UTC: **implementation and numerical reference checks passed; biological force calibration remained open.** The named skinned-TDT reference is separate from the runtime; CM9 electrical measurements are not converted to calcium or force.

The [script](../../research/check_peripheral_calibration.py), measured/source-fitted data (original artifact `neural-motor/peripheral-calibration-data.json`; [archive](../../results/README.md)) and final result receipt (original artifact `outputs/program/m2/calibration-results.json`; [archive](../../results/README.md)) retain units, preparation, source/map/configuration hashes, initial state, stimuli and distinct evidence levels. The data has a run copy (original artifact `outputs/program/m2/reference-data.json`; [archive](../../results/README.md)). Source manifest (original artifact `outputs/program/m2/source-manifest.json`; [archive](../../results/README.md)) and foreleg source manifest (original artifact `outputs/program/m2/sources/foreleg-source-manifest.json`; [archive](../../results/README.md)) retain URLs, hashes and access failures.

## Evidence and comparisons

| Assay | Independent evidence | What ran | Remaining gate |
|---|---|---|---|
| Foreleg fast/intermediate/slow units | Azevedo 2020 public dataset, analysis archive, probe calibration and Methods | Archived probe coefficient reconstruction; raw-trial retrieval attempted | Raw paired force/spike trial access, extraction/replay, specimen split and exact MaleCNS unit crosswalk |
| Young adult CM9 | Mahoney 2014 Table 1/Figure 5; 2016 article and supplement inventory | Existing NMJ regular trains, 50-ms paired increments and native scalar activation at 10/5 µs | Condition-matched electrical waveforms, multiple intervals/recovery, isolated M9 calcium/force/load |
| Skinned adult TDT | Eldred 2010 Tables 2–3, visually checked in the author PDF | Source-fitted Hill calcium/force–velocity reference; native-law shape comparison; reserved slack-test comparison | Raw specimen values/covariance, preparation discrepancies, living spike-to-force and anatomical capacity allocation |

### Foreleg data and force-probe units

See the [foreleg retrieval record](m2-foreleg-source-notes.md) for exact datasets, archive identities and failed endpoints. Public metadata exposes preprocessed electrophysiology and synchronized probe-position recordings. The historical access failure does not imply that the measurements do not exist.

The archived `Methods_BarRelaxation.m` SI block identifies **c = 0.1377×10⁻³ kg/s**, consistent with the reported mass and millisecond decay. The publication/non-SI comment's `0.1377 kg/s` is inconsistent. The archived implementation supports the smaller SI coefficient independently of the initial dimensional inference; fit uncertainty still needs the calibration trials. Retain static probe force **k·displacement** separately from dynamic force and tendon tension. [Azevedo paper](https://elifesciences.org/articles/56754), [analysis archive](https://doi.org/10.5281/zenodo.4527659)

The source's measured balance/displacement matrix is available: replay of its selected columns and missing-value handling retains **42 points**, giving **k = 0.223419451 N/m**, intercept **4.42075×10⁻⁸ N**, and **R² = 0.993363**. A separate column-based diagnostic fits 28 points and predicts 14 reserved points with **4.45185 µN RMSE**; no independent specimen identity or empirical acceptance margin is supplied. This calibrates the instrument, not the muscle. The original Figure 4 dynamic force-correction path and a manual half-rise override also require reconciliation before a faithful trial replay.

No fast/intermediate/slow law was assigned to arbitrary MaleCNS rows. The exact per-unit muscle territory and probe-to-tendon moment-arm/load relation remain required before runtime calibration.

### TDT material reference and native-law mismatch

The reference uses the source's fitted Hill parameters at 15°C and the stated sarcomere length; it excludes eccentric contraction, length dependence and excitation kinetics. Using source means gives Ca50 **2.39883 µM**, unloaded shortening **5.13333 ML/s**, peak-power velocity **1.36203 ML/s** and tension fraction **0.265331**. These reconstruct published fits; agreement with quantities derived from those fits is not a holdout pass. The separate slack assay reports **6.1±0.3 ML/s**, was not used for these constants, and differs by **−0.96667 ML/s**. Specimen overlap/covariance is unavailable. [Eldred et al., Tables 2–3](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/)

At optimal length, the native MuJoCo concentric law is `(1−v/vmax)²`; its peak-power tension is **4/9**, independent of force or velocity scaling. The reported TDT optimum is **0.26±0.01**. This is a descriptive model-form mismatch, not a preregistered equivalence test. The repair belongs in the muscle's constitutive shape if transfer to a runtime target becomes justified. Increasing motor gain cannot fix it. The native-function identity was checked to **2.22×10⁻¹⁶** maximum absolute error.

Retain source discrepancies: Methods give 10 mM MgATP mounting solution, Results use 20 mM for tension/slack; prose calls 6.1 “lower” than 5.10 despite the tables. Do not infer whole-muscle capacity from the representative prepared bundle or borrow skinned calcium sensitivity for dimensionless NMJ excitation.

### CM9 and frozen effective drive

The biological reference remains **9.03±0.33 mV EPSP**, **1.12±0.08 mV mEPSP**, n=13, in 7-day virgin female `w1118`, 0.5 mM Ca/3 mM Mg saline. Quantal content is the mean of per-recording ratios, not the ratio of aggregate means. Figure 5's n=8 train assay is reserved separately; a nonsignificant result is not a numerical zero-depression target. [Mahoney et al. 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/)

Unchanged model predictions are **0.878694** second/first release increment at 50 ms and stationary per-event efficacy **0.764351 at 20 Hz / 0.586799 at 40 Hz**. Those are model state ratios, not measured EPSP or force ratios. Actual periodic controls match the analytic discrete law within **5.88×10⁻¹⁴**; halving 10 µs to 5 µs changes mean activation by at most **6.48×10⁻⁶**. Native activation dynamics were checked directly, without a body simulation.

The 2016 XML exposes source data for hypertonic spontaneous event counts and complexin staining; neither supplies the missing paired-pulse/recovery waveforms. [Mahoney et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5012858/)

### Intact TDT ergometer route

The Harvey 2008 author manuscript explicitly limits the apparatus to an index of twitch output: its approximately 14-Hz resonant beam cannot resolve the under-30-ms force transient or yield exact force/work. It reports one-leg peak deflection **110±34 µm (SD), n=100**. This narrows the earlier abstract-only lead: it is useful for a matched apparatus comparison, not an absolute tendon-force calibration. The [coauthor-uploaded manuscript](https://www.researchgate.net/publication/5408237_Neuromuscular_control_of_a_single_twitch_muscle_in_wild_type_and_mutant_Drosophila_measured_with_an_ergometer) was recovered through indexed primary text; direct file access returned 403. The [2012 method](https://pubmed.ncbi.nlm.nih.gov/22037247/) remains a full-text/load-calibration dependency; its full quantitative record was not recovered in this study.

## Open data gates and next action

1. Obtain ordinary public download access to the listed Dryad files or an author-provided mirror. Extract trial timestamps, neuronal events, baseline, probe position and metadata with published code; reserve independent specimens and pulse/load histories before fitting. Use the verified SI probe coefficient and retain its uncertainty.
2. Obtain per-specimen CM9 voltage waveforms with stimulus times, absolute units, multiple paired intervals, prolonged trains and recovery under one recorded cohort/saline/temperature. For mechanical calibration additionally obtain load-resolved isolated M9 force/calcium and PCSA/moment arms.
3. Obtain TDT force-clamp/slack raw values and clarify MgATP/comparison discrepancies; determine whole-muscle and recruited territory PCSA and living calcium/spike dynamics before applying the material reference to a particular motor route.

Public code and table data support further constituent work. The historical study did not establish an independent physiological acceptance margin, a held-out specimen test, or validated physical behavior. **M2 force calibration remained open** at the conclusion of this study; current package checks and remaining research are tracked in the linked status and roadmap.

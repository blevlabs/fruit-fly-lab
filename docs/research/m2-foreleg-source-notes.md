# M2 foreleg source recovery

This note records historical studies from September 2026. Reported checks and source hashes identify those studies; they are not new verification of the packaged software. See [current status](../status.md), the [research roadmap](../roadmap.md), and the [historical provenance archive](../../results/README.md).

Historical physiological source analysis, 2026-09-11. The source manifest (original artifact `foreleg-source-manifest.json`; [archive](../../results/README.md)) records public URLs, SHA-256, archived-code checksums and data-access limitations.

**Result:** independent probe calibration is recoverable. The archived analysis explicitly resolves the paper's damping-unit discrepancy to **0.0001377 kg/s**. Experimental spike/probe traces are publicly catalogued, but **zero trial bytes were recovered** because the tested download routes rejected access during the study. M2 physiological validation remains open; these results do not set a muscle gain or establish normal movement.

## Source-backed units and numerical replay

- [Archived FlySound calibration](https://github.com/elifesciences-publications/FlySound/blob/559a86e1bdccaba0b64c17ab97d7d09fd830cfa9/FlySoundDevices/forceProbeCalibration.m#L77-L109), pinned SHA `559a86e1bdccaba0b64c17ab97d7d09fd830cfa9`: lines 77–91 contain the balance measurements; lines 93–105 baseline-subtract columns, stack the selected columns and discard NaNs; lines 106–109 convert displacement to metres, balance units to kilograms, multiply by 9.8 m/s² and fit force against displacement. Replaying those exact operations gives **42 retained points, k = 0.223419450958753 N/m, intercept = 4.42074768933605e−8 N, R² = 0.993362760277835**. This agrees with the reported rounded 0.2234 N/m. The source's NaN-baseline handling and selected-column set were preserved, not silently repaired. Arithmetic receipt (original artifact `outputs/program/m2/sources/foreleg-probe-source-replay.json`; [archive](../../results/README.md)).
- The [paper's Methods](https://elifesciences.org/articles/56754#s4) report mass 0.1702 mg, damping 0.1377 kg/s, and approximately 2.5 ms relaxation with a 5.8 ms oscillation period. The printed damping units are inconsistent with that mass and timing.
- [Author analysis, pinned commit](https://github.com/tony-azevedo/FlyAnalysis/blob/c68159f1f7a4ecc957c708ae8411fd2550482f63/Records/Azevedo_2020_Records/Methods_BarRelaxation.m#L419-L471): lines 423–424 convert fitted coefficients from milliseconds to seconds; line 461 computes mass as k/B and identifies approximately **1.7e−7 kg**; line 469 explicitly identifies **0.1377e−3 kg/s**. The earlier mixed-unit block at line 376 contains the same incorrect kg/s label as the paper.
- This is not only a present-day code interpretation: [Methods_BarRelaxation.m in the archived Zenodo companion deposit](https://zenodo.org/api/records/4527659/files/Methods_BarRelaxation.m/content), DOI [10.5281/zenodo.4527659](https://doi.org/10.5281/zenodo.4527659), matches that GitHub file exactly after newline normalization. The downloaded bytes pass the deposit's MD5 checksum. Thus the SI conversion is archived source evidence. No author erratum was recovered, and the fitted mass/damping uncertainty remains unavailable.
- **Derived consistency check, not a new measurement:** k = 0.2234 N/m, m = 1.702e−7 kg, c = 1.377e−4 kg/s imply damping ratio 0.35309, envelope relaxation 2m/c = 2.47204 ms and damped period 5.86182 ms. These calculations corroborate the archived SI block. They do not replace the original relaxation trajectories or establish precise error bars.

The dynamic model concerns the probe under its original preparation. Its parameters must not be transferred into muscle calcium, activation or tendon mechanics. Static probe force likewise is not tendon F0.

## What data exists and what was actually retrieved

[Dryad dataset 10.5061/dryad.76hdr7stb](https://datadryad.org/dataset/doi:10.5061/dryad.76hdr7stb), version **105831** inspected in this study, lists **60 files, approximately 48.76 GB**. Its metadata describes preprocessed electrical recordings, stimulus parameters, synchronous camera exposure times and video-derived force-probe positions. The [archived README](https://zenodo.org/api/records/4527659/files/README.txt/content) specifies MATLAB trial structures, included spike detection/probe tracking, per-cell notes and natural electrical units. The deposit excludes original videos for space. Metadata and analysis code were downloaded; archived electrical/probe arrays were not.

The [archived Dataset3 script](https://zenodo.org/api/records/4527659/files/Dataset3_SlowInterFast_ForcePerSpike.m/content) supplies explicit genetic labels and trial identities:

| Reference identity | Candidate record | Author trial selection | Dryad file ID / archive size |
|---|---|---|---|
| Fast, 81A07 | 171102_F2_C1 | EpiFlash2T 47–173; multiple probe offsets | 585422 / 369,295,693 bytes |
| Intermediate, 22A08 | 180405_F3_C1 | EpiFlash2T 42–125; zero offset | 585433 / 450,813,051 bytes |
| Intermediate example | 180807_F1_C1 | EpiFlash2T 40 and 68 are explicit example trials | 585440 / 1,044,842,909 bytes |
| Slow, 35C09 | 180111_F2_C1 | CurrentStep2T 5–42; zero offset | 585424 / 291,303,979 bytes |

The script additionally references fast example `170921_F1_C1` trials 22 and 37 and `190123_F3_C1` trial 78. Their individual archives are not named in the inspected top-level list; nested `Dataset_3-20210119T203151Z-001.zip` (file 585415, 2,140,734,915 bytes) has not been inspected. This does not establish that those records are absent.

### Historical data-access limit

The study recovered public metadata and archived analysis code, but no experimental electrical/probe trial arrays. The inspected public catalogue preview listed 457 members in the fast-unit archive, including acquisition metadata and `.mat` files. Catalogue availability was not treated as successful data retrieval.

A complete replay requires selected trials and accompanying notes, with original spike indices, exposure timestamps, probe positions, stimulus parameters, inclusion flags and genetic identity preserved. Separate cells, pulses and poses must be reserved before fitting. No calibration/holdout split was executed in this study.

## Analysis provenance and remaining biological limits

The archived single-spike analysis groups by cell and spike count, aligns electrical/probe records to detected spikes, pools asynchronous camera samples across trials, and estimates half-rise from a fitted rising segment. The archived `Script_alignSingleSpikes.m` records alignment at lines 19–28, 112–127 and 146–188; line 276 explicitly overrides one cell's half-rise to 7.7 ms. The original archived-script label is `foreleg-zenodo-Script_alignSingleSpikes.m`; see the [historical provenance archive](../../results/README.md). Raw replay must document this override, source exclusions and the difference between probe-displacement and force timing. A single 170 Hz video trace does not independently resolve a 2.5 ms transient.

The paper says Figure 4D–F include probe inertia and drag. The recovered `Script_tableOfForcePerSpike.m` from FlyAnalysis's `TutLabMaster` branch computes displacement peaks, and the archived plotting script rescales the axis by k; this path does **not** visibly perform dynamic correction. The exact generating force-correction path or final processed result tables is therefore still required before claiming a faithful numerical Figure 4 replay. Do not silently reinterpret a position-derived plot as a fully reconstructed dynamic force trace.

**Motor assignment remains unresolved.** The genetic fast/intermediate/slow identities are reference preparations, not MaleCNS IDs. The historical foreleg `leg.tibia_flexor` candidates are LF 807165/809912/818057/819384/909831 and RF 810098/821635/827188/1050031705/1050189039. No recovered source connects these individual IDs to 81A07, 22A08 or 35C09. Required evidence is an anatomical correspondence through the named motor neuron and its innervated fiber territory, including accessory/distal flexors. Axon size ranking and the historical word “reductor” do not establish this assignment. Probe-contact/joint/tendon geometry and per-unit recruited muscle capacity are also required to turn probe measurements into tendon parameters.

Historical implementation/source recovery: partial. Numerical static calibration replay: passed. Biological per-unit calibration: not executed. Demonstrated animal capabilities: not assessed by this source work.

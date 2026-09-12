# M3 R1-R6 photoreceptor reference

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

Recovered **100 recorded voltage traces and 200 released simulation traces**, plus the pinned phototransduction source and original Song et al. 2012 supplement. The numeric arrays pass source-summary checks. **An original absorbed-photon-to-voltage reproduction remains unavailable:** the exact stimulus vectors, figure-specific executable configuration, and one background identity are unresolved. No photoreceptor model was implemented or executed, and this work does not close M3.

All retained files are in photoreceptor-reference (original artifact `m3/photoreceptor-reference`). Source retrieval and checks were completed on 2026-09-12 UTC.

## Original Song 2012 experiment and supplement

[Song et al. 2012](https://doi.org/10.1016/j.cub.2012.05.047) studies outer R1-R6 photoreceptors. White-noise response statistics determine bump shape and latency at each background; the adjusted model predicts naturalistic responses. This is a comparison across stimulus classes, not a documented held-out cell cohort or unseen-intensity test.

The [original Europe PMC package](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3420010/supplementaryFiles) was downloaded and inventoried: 1,397,060 bytes, containing seven JPG figures, seven GIF thumbnails and `mmc1.pdf`. It contains **no numeric stimulus/response arrays or executable code**. The retained article XML (original artifact `m3/photoreceptor-reference/song-2012.xml`) likewise identifies only Document S1. This bounds the inspected release; it does not prove that no unpublished or separately held data exist.

The supplement (original artifact `m3/photoreceptor-reference/song-2012-mmc1.pdf`), 636,919 bytes, SHA-256 `9b22e3e0b50d4403769db0e3ea28d62536c9ee4d80fea4dbea54426b53301f2b`, supplies these protocol boundaries. The retained article XML declares CC BY 3.0; that publication license is separate from the software licenses below.

| Item | Source boundary |
|---|---|
| Model input | Absorbed photons per 1 ms bin, distributed among 30,000 microvilli. Low-intensity quantum-bump counts calibrate absorption. No RGB, lumen or scene-radiance conversion is supplied. |
| Current recordings | Dissociated ommatidia from newly eclosed `w1118`, whole-cell clamp at 20 ± 1°C and −70 mV, including junction-potential correction. |
| Voltage recordings | Intact wild-type red-eye R1-R6, sharp intracellular electrodes. The main paper's WN/NS intensity comparison uses 25°C. These are separate preparations. |
| Natural stimulus | A one-second, 10,000-point van Hateren sequence; the original record ID and sample interval within that collection are not supplied. |
| Adaptation | Experiments discard the initial 5–20 repetitions. Simulations repeat the one-second input twice and normally analyze 1001–2000 ms across 100 runs. |
| Parameter evidence | Table S1 includes tuned reaction/feedback constants. Background-specific `ns` and `la` calibration must be preserved. Molecular parameter identification is incomplete. |

Relevant supplement locations: pp. 7–9, 11–15 and 24–26, using PDF page numbers. Do not replace the missing original vector with a newly generated signal of similar statistics and call it figure reproduction.

## Recovered numeric outputs from the later model release

The [2017 eLife paper](https://elifesciences.org/articles/26117) links the Juusola source and numeric Figure 1/3 workbooks; its publisher page declares CC BY 4.0, with no separate workbook license found in the inspected files. These are later experiments/model outputs, **not recovered Song 2012 trials**. The three downloaded v2 workbooks each contain five sheets (20, 50, 100, 200 and 500 Hz), with 2,000 samples per sheet and 20 runs per sample.

| Exact publisher file | Publisher identity | Observed worksheet suffix | SHA-256 |
|---|---|---|---|
| [elife-26117-fig1-data1-v2.xlsx](https://cdn.elifesciences.org/articles/26117/elife-26117-fig1-data1-v2.xlsx) | Recorded responses, BG0 | `BG0` | `cb457117a713ad69c985d687c33d96d46ec027b66718b214be379b048d084c0d` |
| [elife-26117-fig3-data1-v2.xlsx](https://cdn.elifesciences.org/articles/26117/elife-26117-fig3-data1-v2.xlsx) | Simulated responses, BG0 | **`BG05`** | `4b3526e4eff65ccc8bf9cf9fbc54ec90357766d60dbef1fe9fe8d3cd0a287592` |
| [elife-26117-fig3-data2-v2.xlsx](https://cdn.elifesciences.org/articles/26117/elife-26117-fig3-data2-v2.xlsx) | Simulated responses, BG0.5 | `BG05` | `f5a52fd8179f9cbafb92e987b06f9da5ee37bfef0be1fda9e66659f1acd36f72` |

Direct inspection establishes the schema, independently of the captions:

- `B1` is `Time (ms)`; `B2:B2001` is exactly 1 through 2000, at 1 ms intervals. `C:V` contains `Run1` through `Run20`, `W` the source mean, and `X` its source SD. Column A is empty. There are **no stimulus columns** in the retained sheets.
- All numeric cells are finite. Independently recomputed row means and sample SDs (`ddof=1`) match the supplied summaries, with maximum absolute discrepancies below `6.8e-14` and `1.3e-12`, respectively.
- Each trace has an approximately zero temporal mean (recorded maximum absolute mean <`1.7e-7`; simulations <`2.5e-13`). They are numerically centered voltage traces; their zero is not an identified absolute resting potential. The article presents voltage in mV, while the workbook run headers do not repeat that unit or document the baseline-subtraction operation.
- The two Figure 3 workbooks have identical sheet names but different numeric data. The Figure 3 data 1 caption/sheet background conflict is retained, not silently corrected. No matched-background error score is reported.

The recorded runs in Figure 1 come from one cell across repeated stimuli; they are not 100 independently sampled cells. The later publication discards initial adapting trials and optimizes modeled effective photon intensity for information transfer. Its optimal mean input is therefore an analysis choice, not direct scene-to-photon calibration or an independent validation target. Pupil and network contributions also limit direct single-cell model/recording equality.

## Original figure projects: exact retrieval boundary

The author-deposited [Dryad dataset](https://datadryad.org/dataset/doi:10.5061/dryad.12751) is public, with CC0 dedication stated by the article. API metadata identifies dataset 17165, version 17225/version number 1, published 2018-08-28 and last modified 2020-06-30. Its 59 files total 2,192,278,252 bytes. The two relevant projects are only 32,000,885 bytes together:

| Original project | File ID | Bytes | Published MD5 |
|---|---:|---:|---|
| [Figure 1 (all responses to stimuli).opj](https://datadryad.org/downloads/file_stream/58484) | 58484 | 17,510,289 | `291dabd46d932e790a74f82fc1669c71` |
| [Figure 3 (all WN simulations final).opj](https://datadryad.org/downloads/file_stream/58491) | 58491 | 14,490,596 | `131edc4cc78a2129c4c8361ccb3c45ce` |

During the historical retrieval, both public download links returned HTTP 403. Their `/api/v2/files/{id}/download` routes returned HTTP 401 with a bearer-token requirement. No OPJ bytes were recovered, so **whether they contain the missing stimulus vectors is unverified**. File IDs, API pages, version information and failed-download responses are retained. The full dataset was not requested.

A bounded reader route exists if those two files become available: upstream [liborigin 3.0.4](https://sourceforge.net/projects/liborigin/files/liborigin/3.0/) reads OPJ and has a native C++ CLI. Its stock export must be checked for workbook-sheet coverage and floating-point precision before use. The OPJ inputs were unavailable for reader evaluation.

## Executable source and parameter identity

The exact original files and their licenses are retained under `sources/`, with byte counts and hashes in source-files.json (original artifact `m3/photoreceptor-reference/source-files.json`). They are reference copies, not imported runtime dependencies.

| Source | Pinned revision | Execution and identity boundary |
|---|---|---|
| [Juusola MATLAB model](https://github.com/JuusolaLab/Microsaccadic_Sampling_Paper/tree/a4453f7e47abf2ea2a924c376d4c1c157c6011e2/BiophysicalPhotoreceptorModel) | `a4453f7e47abf2ea2a924c376d4c1c157c6011e2` | Source headers identify June 2017. Main script requires absent `LightSkew_b2p3_speed205` data, uses clock-seeded `RandStream`, sets `fnstr=50`, `la=0.2`, then sums 100 groups of 300 microvilli. Its voltage-feedback script chooses a BG1 membrane configuration and performs 100 feedback iterations. This is not a Figure 1/3 replay driver. |
| [Neurokernel retina](https://github.com/neurokernel/retina/tree/fdab351e6c5530c8f051193158856ba6ef11d715) | `fdab351e6c5530c8f051193158856ba6ef11d715` | BSD-3-Clause. Example input is 10,000 photons/s starting at 0.2 s in a one-second run, with `dt=1e-4`. Component needs PyCUDA, CUDA RNG and Neurokernel. No source numeric expected voltage trace accompanies that example. |
| [VisTrans](https://github.com/FlyBrainLab/VisTrans/tree/ba096778d4bd895a0e0fab02b9c519c5941bc82b) | `ba096778d4bd895a0e0fab02b9c519c5941bc82b` | BSD-3-Clause. Released component reads photon/current input and updates voltage through CUDA kernels; source execution requires its GPU stack. No verified mapping to Song's original figure protocol was found. |

**License:** the pinned Juusola repository contains `LICENCE.txt` (British spelling), whose text is GNU GPL version 3. This source is not BSD. The license notice is distinct from any assessment of a future combined implementation.

Two direct parameter differences prevent claiming exact Song 2012 parameter identity: the 2012 Table S1 gives 25 TRP/TRPL channels per microvillus, while the 2017 initializer sets `para(26)=27`; the 2012 voltage-feedback equations set TRP reversal potential to 0 mV, while `Vol_FeedbackCluster.m` uses 20 mV. Preserve these versions and resolve figure correspondence before copying constants. Unit conversions also require care: the MATLAB photon series uses counts per 1 ms bin; the Neurokernel step specifies a rate per second. The same numeric array cannot be passed to both unchanged.

The historical study inspected source and numeric output; it did not execute the MATLAB, Neurokernel or VisTrans models or translate their implementations.

## Supported assay and remaining physiological evidence

The completed assay was **source-output integrity and summary reproduction**: one recorded R1-R6 response matrix and its released mean/SD, extended across the three retained workbooks to expose identity conflicts. It checks source hashes, schema, sample times, finite values and the actual summary arithmetic. It is not a phototransduction simulation or a physiology qualification result.

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The retained reference-check.json (original artifact `m3/photoreceptor-reference/reference-check.json`) reports `PASS_SOURCE_ARRAY_CHECK_ONLY`: 28 original source files and 15 numeric sheets checked, `model_executed=false`, `matched_photon_to_voltage_assay_ready=false`.

The smallest subsequent mechanistic assay is a **single R1-R6**, one exact absorbed-photon time series and its matched original source voltage ensemble. For the original 2012 route, obtain the WN calibration arrays, NS vector and 100-trial output with exact `ns`/`la`, preparation and adaptation indices. For the later 2017 route, first retrieve and inspect only the two OPJ projects, resolve BG0/BG05, and establish the specific source driver, input scaling, state initialization and RNG convention. Compare ensemble dynamics using the source's preprocessing before any runtime transfer. A generated step can separately check the Neurokernel example with its required CUDA dependencies, but cannot substitute for the missing original physiological assay.

All of this remains restricted to R1-R6 photon absorption and voltage generation. It establishes no R7/R8 validity, no visual axes for MaleCNS cells, no full-retina anatomy, and no embodied visual capability.

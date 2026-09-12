# Dynamic physiology sources for the two acetates

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

**Both original protocols and useful source code are recoverable, but neither inspected publication exposes the numeric recordings needed for a reproducible acetate spike-model fit and independent holdout.** The exact missing records are identified below. The study identifies source protocols and data limits without fitting a response law. Acetone data were not substituted for either acetate.

The retained evidence and source manifest are under outputs/program/m3/acetate-dynamics (original artifact `m3/acetate-dynamics`). Sources were inspected on **2026-09-12 UTC**. Publisher APIs confirm final **version 3** dated **2019-06-18** for Martelli/Fiala and **2017-07-24** for Gorur-Shandilya et al.; these are historical publications, not new 2026 experiments. Successful manuscript retrieval is separate from availability of raw experimental data.

| Original source | Exact relevant channel | Anatomical correspondence | Recovered evidence |
|---|---|---|---|
| [Martelli and Fiala 2019, eLife 43735](https://doi.org/10.7554/eLife.43735) | Methyl acetate → ab2A/Or59b; corresponding DM4 terminal calcium | `ORN_DM4`: 16 left, 15 right; one unknown-side cell withheld | Final **Figure 3** pulse/background/dose protocol and separate spike/calcium comparisons. |
| [Gorur-Shandilya et al. 2017, eLife 27670](https://doi.org/10.7554/eLife.27670) | Ethyl acetate → native ab3A | `ORN_DM2`: 24 left, 29 right; one unknown-side cell withheld | Gaussian mean/variance and naturalistic assays, published receptor-adaptation equations and selected fit parameters; original acquisition/sorting code. |

The exact body-ID lists and their source hash are preserved in existing-class-correspondence.json (original artifact `m3/acetate-dynamics/existing-class-correspondence.json`). This is a class correspondence, not a claim that each anatomical ID was recorded. Native ab3A includes Or22a/Or22b and is not the earlier Or22a-only empty-neuron preparation. These studies use female physiology preparations, distinct from the MaleCNS specimen.

## Methyl acetate: the source is Figure 3

The final paper's Figure 3 identifies ab2A/Or59b firing and DM4 terminal calcium. Its illustrated sequence has a one-second isolated pulse at 5–6 s, a ten-second gap, background from 16 s, and a one-second test at 31–32 s. The example pulse/background labels are nominal dilutions `10^-8.5` and `10^-9`. These diagram coordinates are not recovered sample timestamps, and the dilutions are not verified ppm or molar concentrations. Experiments used females aged 6–7 days at 20°C. Firing is in spikes/s; imaging is percent ΔF/F from multiple terminals. They were measured separately.[1]

Figure 2 primarily concerns DM1 calcium modeling. Figure 3 supplement 1 A–C also shows ab1B/DM1 in the image and main text despite an inconsistent ab2A/Or59b caption; those panels cannot calibrate Or59b. The detailed methyl-acetate source audit (original artifact `m3/acetate-dynamics/methyl-acetate/protocol-source-audit.md`) preserves recording methods, reported sample sizes and these exclusions.

The published fit/holdout procedure removes the first 35 seconds of a calcium time series, fits the next two-thirds, and evaluates the final third. It supplies neither a Figure 3 spike-model partition nor independent animal identities. It must not be reassigned to an Or59b spike encoder.[1]

**Public route outcome:** the final publisher API returned HTTP 200 and lists figure images plus a transparent reporting form. It exposes no numeric figure source data, dataset accession or analysis-code repository. The form's source-data section is blank. The custom MATLAB spike-sorting routine is mentioned but not supplied through those routes. The exact missing material is the original Figure 3 per-sensillum voltage/spike records, stimulus/valve and PID traces, animal/sensillum/trial IDs, inclusion labels, rate-estimation settings and concentration calibration. Original filenames are not published in the inspected assets; none were invented. The route stops at this external data dependency.

## Ethyl acetate: usable equations, unrecovered trials

The default preparation is native ab3A in Canton-S females aged 3–5 days; the explicitly identified optogenetic experiments use a different genotype and must remain separate. Figure 3 reports 55 trials from seven ORNs in three flies; Figure 4 reports 248 trials from five ORNs in two flies. Repeated trials are not independent animals. Naturalistic stimuli repeat a frozen random sequence; variance changes every five seconds. The primary input is PID volts, LFP is mV, and firing is spikes/s.[2]

The authors **did calibrate PID output to absolute odorant flux**, shown in Figure 1 supplement 1 in µmol/s versus volts. However, the inspected source supplies that calibration as a plot, not the exact numerical coefficients, individual calibration observations or matching trial waveforms. No volts-to-ppm/molarity conversion was invented. Main and odorized airflows are separately specified, so flux and concentration must not be conflated.[3]

Figure 8 supplies an adaptive Or–Orco model with `alpha=12.5 s^-1`, `beta=1.26 s^-1`, `epsilon_L=0.86`, `K_on=0.1 V` and `K_off=400 V`. Its caption explicitly says it was fitted to **both Gaussian and naturalistic data**. The naturalistic comparison is therefore not an independent holdout. The readout uses fitted filters and a firing nonlinearity; complete fitted readout parameters, fitting code and trial membership were not recovered.[4]

The full bounded protocol and parameter record is protocol-and-reuse-boundary.json (original artifact `m3/acetate-dynamics/ethyl-acetate/protocol-and-reuse-boundary.json`). These parameters belong to that source's detector-unit model and are not a measured physical binding-rate tensor for all DM2 cells.

## What the released code actually provides

The paper links `spikesort` and `kontroller`. Their source trees and licenses were inspected without installation. Relevant original I/O code is retained with hashes in original-io-code-manifest.json (original artifact `m3/acetate-dynamics/ethyl-acetate/original-io-code-manifest.json`).

| Repository | Pinned revision | Scope |
|---|---|---|
| [Publisher's spikesort archive](https://github.com/elifesciences-publications/spikesort/tree/126a2b3178714032afc86bfd7e64068b6e1abd8c) | `126a2b3178714032afc86bfd7e64068b6e1abd8c`, 2018-05-04 | Spike sorting and saved-trial I/O; explicitly associated with the paper. This is the inspected archive revision, not an independently established publication-day software build. |
| [Original spikesort](https://github.com/emonetlab/spikesort/tree/c4d71c0a5f90a80186b93261b838ddfc087e4c24) | `c4d71c0a5f90a80186b93261b838ddfc087e4c24`, 2018-10-15 | Repository comparison inspected for this historical study. |
| [Kontroller](https://github.com/emonetlab/kontroller/tree/f5e57de887c47f2bd831c2a399a316d230499178) | `f5e57de887c47f2bd831c2a399a316d230499178`, 2017-01-10 | MATLAB acquisition and hardware control; supplies the saved-data schema. |

The repositories contain no experimental recording files. The retained `loadFile_kontroller.m` reads `SamplingRate`, `ControlParadigm` and channel names. `readData_kontroller.m` retrieves stimulus and voltage by paradigm/trial and can read sorted `spikes.A/B/N`. Kontroller also documents optional metadata and timestamps. These are concrete import routes **if the original MAT/kontroller recordings are obtained**. They do not provide the paper's Figure 8 fitting pipeline.

The sorting benchmark references recording files absent from the release, including `manually_inspected.mat`, `best_pca.mat` and `best_tsne.mat`. Even if recovered, that benchmark has not been identified as the article's acetate response dataset. It cannot substitute for the requested experimental trials. The software repositories use GPL v3; the retained test report separately declares CC BY-NC-SA 4.0. No source code was executed or incorporated into the simulator.

**Public route outcome:** final version-3 publisher metadata contains eight figure groups, 21 image assets and mathematical expressions, with no numeric source-data/code attachment or dataset accession. The version-2 supplemental ZIP contains 13 figure PDFs only and is retained as a versioned figure bundle. The [author's publication entry](https://srinivas.gs/) links the paper, PDF and talk, without a raw-data download. The remaining external dependency is the original recorded MAT/kontroller files with trial/fly/sensillum assignments, sorted spikes, exact detector calibration and complete fitting/readout configuration. Those records are necessary for an exact trial-level reconstruction.

## Fit and holdout disposition

No executable, independently identified acetate **spike** fit/holdout slice was recovered from these sources. Martelli's available split is a within-series calcium split; Gorur-Shandilya's model uses both displayed stimulus families for fitting. A future spike-model comparison must preserve original trial identities and predeclare disjoint evaluation records after data recovery. It must not turn adjacent bins, repeated presentations of the same frozen waveform, terminal fluorescence, or previously fitted naturalistic traces into independent validation.

The study established the source/protocol inventory for these two publications. Numerical response reproduction and biological holdout remain open. Both exact receptor-class correspondences can support later experiments once the identified data arrive; neither establishes sensory coverage or demonstrated behavior.

## Primary sources

1. Martelli C, Fiala A. 2019. [Slow presynaptic mechanisms that mediate adaptation in the olfactory pathway of Drosophila](https://doi.org/10.7554/eLife.43735), final version 3, Figure 3 and Methods. [Publisher metadata](https://api.elifesciences.org/articles/43735).
2. Gorur-Shandilya S, Demir M, Long J, Clark DA, Emonet T. 2017. [Olfactory receptor neurons use gain control and complementary kinetics to encode intermittent odorant stimuli](https://doi.org/10.7554/eLife.27670), final version 3, Figures 3–4 and Methods. [Publisher metadata](https://api.elifesciences.org/articles/27670).
3. Gorur-Shandilya et al. [Figure 1 supplement 1, PID calibration](https://doi.org/10.7554/eLife.27670.004); retained original supplemental PDF.
4. Gorur-Shandilya et al. [Figure 8](https://doi.org/10.7554/eLife.27670.021) and [Figure 8 supplement 2](https://doi.org/10.7554/eLife.27670.023), with the explicit combined fitting scope.

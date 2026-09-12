# M4/M7 central physiology and plasticity evidence

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**Status: the γ1 reference is now anchored to exact MaleCNS cells and retained structural edges. M4 physiological validation and M7 learning remain open.** This report records source retrieval and an anatomical reference audit executed on 2026-09-11/12; it does not report a simulated learning result.

The governing [full-program research roadmap](../roadmap.md) retains the frozen Eon/graded control. The [neural physiology review](whole-cns-neural-physiology.md) and scientific corrections in the [electrochemical plan](../roadmap.md) remain applicable. In particular, a synapse count is neither a receptor conductance nor a dopamine learning rule. Moving to a rate equation would leave those missing quantities unresolved.

## What was executed

The [circuit audit](../../research/check_m4_m7_reference.py) verified incoming CSR orientation, absent-target rejection and exact graph identity without executing neuronal dynamics.

The audit receipt (original artifact `program/m4-m7/circuit-audit.json`) matches the pinned graph identities: `neurons.feather` SHA-256 `10fa864a4de8e9c857e0a9bfcb78e70910818047bd632b51db8cb3a7692a0e71`; `connectome.npz` SHA-256 `8a48ac6232523652ff21efdc65b2e6986aa9e584b3cf25a121f72f53d5d32652`. All **167,216 neurons, 25,587,572 edges and 124,193,283 contacts** remain. The evidence receipt (original artifact `program/m4-m7/evidence-receipt.json`) records local/source hashes, access failures and the absence of runtime effects.

| Boundary | Result |
|---|---|
| Source extraction implementation | Passed: actual CSR incoming direction, absent-target rejection, ID ordering and source identities |
| Neural numerical correctness | Not run; no new dynamical model was introduced |
| Biological validation | Open; source observations are references, not reproduced model responses |
| Persistent/adaptive capabilities | Not run; circuit identity does not establish teaching, retention, reversal or transfer |

## Exact γ1 anatomical reference

The local official MaleCNS v1 annotations identify the following retained cells. No FlyWire or hemibrain numerical ID was copied. Cross-dataset **type** names remain provenance; the physiological animals are different specimens.

| MaleCNS bodyId | Official instance | Consensus transmitter | Actual incoming γ-KC edges / contacts |
|---|---|---|---|
| 10704 | `MBON11(y1pedc>a/B)_L` | GABA, also present in source `ground_truth` | 806 / 11,152 |
| 11402 | `MBON11(y1pedc>a/B)_R` | GABA, also present in source `ground_truth` | 779 / 16,668 |
| 11900 | `PPL101(y1ped)_L` | dopamine, also present in source `ground_truth` | 1,512 / 7,679 |
| 11327 | `PPL101(y1ped)_R` | dopamine, also present in source `ground_truth` | 1,520 / 7,540 |

There are **1,557 retained `KCg*` cells**, all with source consensus acetylcholine: 1,342 `KCg-m`, 206 `KCg-d`, two each of `KCg-s1` through `KCg-s4`, and one `KCg`. These are anatomical candidates; they are not the source preparation's odor-active or SPARC-labeled cells. The audit saves their exact IDs and 7,377 selected actual edges, including PPL101→KC/MBON edges independently of KC→MBON edges. It does not invent a complete KC–DAN–MBON triangle or exclude a real edge by somatic side.

The aggregate graph's missing coordinate information was pursued through the [public MaleCNS catalog](https://male-cns.janelia.org/download/) and anonymous neuPrint queries. **55,253 actual contact pairs** were retrieved in four bounded exports, retaining source pre/post coordinates, confidence, anatomical ROI and compartment labels. The dataset UUID is `4b2087c0fbe046bfaf0d60bc970e3e5d`; source metadata explicitly specifies **8-nm voxels**. The export was restricted to the selected circuit. Exact queries and hashes (original artifact `program/m4-m7/sources/gamma1-source-retrieval.json`), public route receipts (original artifact `program/m4-m7/sources/gamma1-public-catalog-receipts.json`).

| Source export | All retrieved contacts | γ-KC→MBON11 contacts where applicable |
|---|---:|---:|
| All KC classes→MBON11 10704 | 16,863 | 11,152 |
| All KC classes→MBON11 11402 | 24,597 | 16,668 |
| PPL101 11900→all KC classes/MBON11 | 6,619 | — |
| PPL101 11327→all KC classes/MBON11 | 7,174 | — |

The runnable `--synapses outputs/program/m4-m7/sources` check verifies file hashes and exact contact counts against **all 4,343 overlapping prepared neuron pairs**; it passes with zero disagreement. Check receipt (original artifact `program/m4-m7/synapse-reference-check.json`). ROI summaries require the same literal label on both synaptic endpoints and retain `g1(L)`, `g1(R)`, `PED(L)` and `PED(R)` separately. Both PPL101 cells have bilateral contacts. Source compartment labels include axon, dendrite, linker and unknown; they are retained without using them to discard contacts. The γ-KC-specific ROI counts are saved separately (original artifact `program/m4-m7/sources/gamma1-gamma-kc-roi-counts.json`).

This resolves the selected circuit's coordinate-access dependency. Remaining missing quantities are receptor localization/action, dopamine diffusion/reuptake, contact efficacy, physiological KC ensembles and the mechanism/extent of activity-dependent eligibility. A PPL101 chemical edge alone cannot define the spatial reach of modulation. **Do not enable plasticity across all `KCg*` cells or all outgoing PPL101 edges from this extraction.**

## M4 transmitter and receptor audit

The complete unresolved-cell CSV (original artifact `program/m4-m7/unresolved-transmission.csv`) contains **3,656 IDs** with zero fast sign in the frozen approximation, accounting for **589,524 outgoing edges and 2,051,771 contacts**. Of those cells, 514 have no transmitter-table row and 3,142 have `consensus_nt=unclear`; none has a populated source `ground_truth`. Low-confidence individual predictions were not substituted for that consensus. All unresolved structural contacts remain present.

The annotation field named `receptorType` is populated only for 752 VNC sensory rows (`putative_ppk23`, `putative_ppk25`, `putative_IR52b`). It supplies **no postsynaptic CNS transmitter-receptor identities**, including for the four γ1 reference cells.

The publicly retrieved [Eckstein/Bates 2024 ground-truth and type tables](https://zenodo.org/records/10593546) provide a useful targeted next source route. Literal complete official `flywireType` or `hemibrainType` matches yield 57 candidate cells (original artifact `program/m4-m7/transmitter-crosswalk-candidates.json`). Most are peptides or amines; eight l-LNv cells have literature glycine assignments and two PPL203 cells have **dopamine plus GABA** assignments. Multi-name annotation matches were excluded. These are source leads: the underlying cited preparation, correspondence and postsynaptic action still require adjudication. They do not justify 57 newly enabled lumped fast signs. The [classification paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11106717/) distinguishes empirical transmitter authority from classification confidence; the saved tables also retain the original literature citations.

Further primary evidence narrows mechanisms without supplying whole-CNS parameters:

- [Barnstedt et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4819445/) supports KC acetylcholine, nicotinic MBON transmission, VAChT dependence and peptide interaction. Its calcium and pharmacology assays do not identify MBON11 single-contact conductance, capacitance, release probability or complete receptor kinetics. Adult KC output must not inherit a mammalian glutamate/NMDA rule.
- [Sanfilippo et al. 2024](https://pubmed.ncbi.nlm.nih.gov/38262414/) maps receptor subunits to subcellular domains; the named MBON receptor examples are MBON13/14, not MBON11. Mi9–T4 localization is relevant to visual-pathway follow-up. Localization is not a conductance measurement and must not be copied to unmatched cells. The final Neuron record was confirmed; its Europe PMC XML endpoint returned 404 in this run.
- [Agrawal et al. 2020](https://elifesciences.org/articles/60299) supplies adult nonspiking 13Bα recordings and current injection/pharmacology. The authors leave partial cholinergic block versus electrical coupling as alternatives. Neither this result nor the broad 13B hemilineage licenses fabricated gap junctions or conversion of every `IN13B*` neuron. Exact driver/morphology-to-MaleCNS subtype correspondence remains required.

Agrawal's [Dryad dataset](https://datadryad.org/dataset/doi:10.5061/dryad.k3j9kd55t) was located and file metadata read. The ephys ZIP is 7,496,404,627 bytes, source SHA-256 `da35baf951913526572a664ef7146ad3e367674d9283a82bcff0bce56e3a5fce`. API download requests returned 401; the advertised public file-stream routes returned 403 for ephys and imaging. No recording was downloaded or fitted. This is an **access dependency**, not evidence that measurements do not exist; successful public/account access or an author-provided subset of the current-step traces is the next route. The exact requests are in the evidence receipt.

### New independent cibarial static reference

[Sui, Yi, Zhou et al. 2026, Extended Data Figure 5](https://www.nature.com/articles/s41593-026-02412-y/figures/12) supplies individual threshold, resting-voltage and paired input-resistance observations. The original workbook (original artifact `program/m4-m7/sources/yi-2026-extended5.xlsx`) was downloaded, and its unlabeled A–D group order and units were verified against the figure axes. The audit's `--cibarial` mode preserves every value and source coordinate in the static reference (original artifact `program/m4-m7/cibarial-static-reference.json`).

| Cell | n | Threshold mean ± sample SD (mV) | Resting voltage mean ± sample SD (mV) |
|---|---:|---:|---:|
| MN12V | 10 | −42.958 ± 1.382 | −50.375 ± 2.164 |
| MN12D | 8 | −41.528 ± 1.597 | −53.115 ± 0.976 |
| MN11V | 8 | −39.411 ± 1.580 | −51.371 ± 3.020 |
| MN11D | 13 | −29.130 ± 3.253 | −52.303 ± 2.865 |

Paired input resistance is 88.750±16.495 MΩ for MN12D and 134.325±43.350 MΩ for MN11V (n=6); all six paired differences are positive. These are SD, not SEM. Supplementary Table 2 specifies **in vivo feeding** for the voltage measurements. The reporting summary permits either sex generally, but the workbook lacks per-observation sex, age and temperature. Full genotypes are in Supplementary Table 1. No capacitance, time constant or raw ramp waveform was supplied in this workbook. This enables a named static calibration reference, not a dynamic fit or automatic transfer to MaleCNS LIF thresholds. Papers, figures and source observations remain distinct artifacts.

## M7 selected preparation and independent controls

Full primary papers are retained under sources (original artifact `program/m4-m7/sources/plasticity-primary-source-retrieval.json`). Published means below are contextual observations with SEM, not manufactured calibration targets or acceptance margins. A value measured in the paper is not a value reproduced by this simulator.

**Hige 2015: in vivo aversive γ1 reference.** Females 36–72 h after eclosion; MB320C drives CsChrimson in PPL1-γ1pedc, with MBON-γ1pedc recording. One-second OCT/MCH pulses use 2% saturated vapor. Four 1-ms 627-nm pulses at 2 Hz start 0.2 s after OCT onset (14.7 mW/mm²). Backward control starts odor 0.5 s after the last light pulse. Responses use 0–1.4 s with spontaneous firing subtracted. Reported CS+ spikes fall 118±8.3→24±7.4 (n=7); EPSC charge falls 90±3.7% (n=5). Suppression persists at least 40 min. Backward timing and adjacent-compartment DAN stimulation do not reproduce it. Voltage-clamp recordings use −60/−70 mV and intracellular QX-314. Missing: individual charge/voltage traces, full acquisition/retention series, baseline covariance and trial metadata. This is aversive conditioning, not proof of a food-reward pathway. [Primary text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/)

**Yamada 2024: ex vivo presynaptic plasticity reference.** Isolated brains 48–72 h after eclosion; sparse SPARC labeling of approximately 3–7% of γ KCs; MBON-γ1pedc voltage clamp −60 mV. Focal dopamine is 1 mM: thirty 1-s-on/1-s-off cycles; 1-ms KC pulses at 2 Hz for 60 s begin 0.3 s before injection. PPR separation is 400 ms; baseline ≥3 min; recording resumes 2.5 min later. At 3–4 min, depression is 54.7±8.5%, with PPR increasing 91.4±16.6% (n=6). Dopamine-only and KC-only do not induce LTD; SCH23390 100 μM, Rp-cAMPS 100 μM and H-89 10 μM block it. cAMP elevation alone does not establish presynaptic LTD. BAY 41–2272 100 μM, delivered in three 1-min pairings separated by 1 min, produces γ-KC potentiation 77.9±11.9% and PPR decrease 24.8±5.3% at 16–17 min (n=5). This pharmacological sGC manipulation does not measure NO release. Original recordings are available by reasonable request to the corresponding author; none were linked as public source arrays. [Primary text/data statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068490/)

**Handler 2019: keep γ4 timing/receptor controls separate.** Main physiology is γ4-MBON calcium in explants (male/female, 1–4 days), not γ1 electrical transmission. KC stimulation is 10 mM calycal ACh iontophoresis, 500 ms; PAM-DAN stimulation is 2 mM ATP through P2X₂, five 100-ms pulses with 20-ms intervals. ISI is DAN onset minus KC onset. Forward/concurrent pairing depresses; backward pairing potentiates; ±6 s largely removes plasticity. DopR1 deletion removes depression; DopR2 deletion or Gαq inhibition removes potentiation. Readout is peak ΔF/F within 2 s, averaging two pre/post responses. Its behavioral odor/CsChrimson protocol is a separate assay. Data and analysis/acquisition code are request-only from the corresponding author. Missing individual timing-response curves cannot be replaced with one universal dopamine sign. [Primary text/data statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/)

The located PMC supplementary-file URLs returned HTML challenges, not verified PDFs. Hige's complete 15-page paper PDF was successfully retrieved from Janelia. Source-access failures and paper downloads must not be described as downloaded physiological recordings.

## Next executable experiment and remaining gates

The next model decision requires individual baseline EPSC/voltage records, paired-pulse/train/recovery traces, intervention time series and stimulus metadata from the selected γ1 preparation. These distinguish a transient release/resource change from persistent efficacy, and presynaptic change from altered postsynaptic response. The cAMP/PKA evidence leaves an activity-dependent gate downstream of cAMP unresolved; assigning an invented time constant or naming a scalar “calcium” would not resolve it. No arbitrary chemical or learning rule was introduced.

Once the records are available, fit the baseline electrical/release reference on explicitly named biological preparations. Hold out separate preparations and the timing, dopamine-only/KC-only, receptor/PKA-blockade and cGMP intervention conditions. Set numerical convergence tolerance from the chosen integrator and biological comparison margins from empirical repeatability before the held-out evaluation. Do not reuse plotted group means as both calibration and holdout or invent a numerical biological tolerance in their absence.

The minimum required dataset is: **machine-readable per-preparation γ1 MBON voltage/EPSC/PPR and cAMP/PKA/cGMP-related traces, raw timestamps and stimulus/drug delivery histories, genotype/sex/age/temperature, recording exclusions, and the mapping from traces to published panels and individual biological replicates**. Hige/Yamada also require the sampled KC labeling/activation information; Handler requires γ4-specific timing curves and the cited analysis code.

Even a validated isolated circuit would not close integrated M7. Remaining requirements include distinct supported sensory cue patterns, an identified consequence-sensitive modulatory compartment for the chosen aversive or appetitive task, a calibrated downstream physical response route, exact M6 restore of learned state, acquisition/recall/reversal/transfer/sequential-learning trials and their causal controls. M8–M11 capability claims remain gated on the relevant learned/persistent individual. The precise present result is **source/identity progress with open numerical, biological and capability gates**.

## Follow-up: primary adjudication of the 57 transmitter candidates

The [primary-source adjudication](m4-transmitter-primary-adjudication.md) now covers all 57 exact IDs and all 19 types. It separates supported chemical/anatomical phenotypes from unresolved release and receptor laws, corrects the Niens/Wolff/Nässel citation issues, and preserves the original consensus. No runtime transmission was enabled. The public Wu 2024 MS-WED/DA-WED electrophysiology route is being investigated as a separate bounded reference; its data, model scope and numerical/biological outcomes must be reported separately from this identity audit.

## Follow-up: bounded MS-WED response experiment

The [standalone MS-WED response reference](m4-ms-wed-response-reference.md) has now executed against two female donor recordings. Source decoding and numerical convergence checks pass; frozen per-recording RC fits predict held-out negative amplitudes with 0.49–1.09 mV RMSE. Visual inspection identifies additional response components and drift that one RC does not reproduce. Effective nominal-command parameters were not assigned to the live male graph; recipient identity and peptide/receptor kinetics remain open. The data, fixed fit/holdout plan, script, trace arrays and plot are retained for the next source/mechanism decision.

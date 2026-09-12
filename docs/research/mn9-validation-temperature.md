# MN9–muscle-9: falsifiable validation and thermal-sensory plan

Historical validation proposal: 2026-09-11. Scope: adult *Drosophila melanogaster*. This is a proposed experimental programme, not a report of experiments performed or biological fidelity achieved.

For current package evidence, see [status](../status.md); planned work is in the [roadmap](../roadmap.md). Historical artifacts are indexed in the [results provenance archive](../../results/README.md).

**Decision:** proceed with an explicitly estimated, force-driven MN9–muscle-9 research model and independent component tests. Do not declare the complete sensorimotor chain validated yet. Adult CM9 neuromuscular recordings and motor perturbation experiments exist; calibrated muscle-9 force–length, force–velocity, passive mechanics and an identified muscle-9 proprioceptive loop remain gaps in the sources examined. Food-temperature sensing needs a local labellar input distinct from antennal warming. No evidence below licenses a hot-food withdrawal rule.

The historical starting model used a **138,639-neuron** simulation, with MN9 rate driving a proboscis-position proxy. Arena temperature was sampled only at the antennae and drove **seven `TRN_VP2` warmth neurons**; no burn or nociception model was present. These are baseline assumptions for the proposal, not current package-verification results.

## 1. Evidence that can constrain the milestone

**Status labels:** M = reported measurement, with its experimental conditions; D = digitization/derivation from published data; E = estimated model parameter; P = proposed experiment or acceptance rule. A measurement from another muscle is not an M value for muscle 9. All studies below concern adults unless explicitly marked otherwise.

### Neuromuscular transmission and movement

| Primary source and acquisition route | Quantitative evidence | Appropriate constraint and limitation |
| --- | --- | --- |
| Mahoney et al. (2014), [article, Table 1 and Figures 1–4](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/), [DOI](https://doi.org/10.1523/JNEUROSCI.3556-13.2014) | M: 7-day `w1118` virgin females: EPSP **9.03 ± 0.33 mV**, mEPSP **1.12 ± 0.08 mV**, quantal content **8.55 ± 0.61**, resting potential **−37.43 ± 1.44 mV**, input resistance **8.43 ± 0.81 MΩ**; **n=13**, means ± SEM, one recording/animal. Saline: **0.5 mM Ca²⁺, 3 mM Mg²⁺**. | Direct adult CM9 electrical benchmark, independent of food choice. EPSP/mEPSP amplitudes constrain effective transmission, not force. Quantal content is computed per preparation: the ratio of group means need not equal mean quantal content. The study also provides **10 μM philanthotoxin-433** and **415 mM total sucrose, 120 s** hypertonic challenges; these constrain receptor/homeostatic and vesicle-pool mechanisms if such mechanisms are claimed. Neither is a muscle-load experiment. |
| Eaton & Mahoney (2017), [CM9 recording protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413541/), [publisher protocol](https://bio-protocol.org/en/bpdetail?id=2401&type=0) | M/protocol: pharyngeal-nerve stimulation **0.5–5 V, 300 μs**; EPSP appearance must have a distinct stimulation threshold. The published sequence uses **1 Hz for 60 s**. Recipe: **0.5 mM Ca²⁺, 20 mM Mg²⁺**. | Practical route to evoked and miniature responses. Its magnesium concentration differs from the 2014 study: preserve that distinction when reproducing amplitudes. The head is dissected and the proboscis repositioned to tension the muscle; this is not intact force calibration. The protocol notes an additional small, non-vGlut-positive innervation of uncertain function. Treat 1 Hz as an event/train rate, not an adequate digitization rate for millisecond potentials. |
| McKellar et al. (2020), [Figure 7](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316511/#fig7), [Video 14](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316511/#video14), [original movie download](https://pmc.ncbi.nlm.nih.gov/articles/instance/7316511/bin/elife-54978-video14.mp4) | M: **14–16 flies/genotype**, 3–7-day males, behaviour at **25°C**. Tethered sucrose assay: **100 mM** presented to legs after **5 h food/water deprivation**, target beyond proboscis contact. Several angle comparisons use **200 ms** after onset; activation from rest uses maximum displacement. Movie plays at **1/30 speed**. | Activation produces rostrum protraction and haustellum extension; MN9 TNT silencing impairs both during feeding, while resting pose is not detectably altered and labellar movement remains. Activation during ongoing extension does not add further extension. Figure 7 supplement 2 supplies unnormalized angle plots. Table 1 identifies MN9 split halves **VT061715 / VT005008**. Use angle distributions and perturbation effects as holdouts, not as force measurements. Full-length digitized trajectories from this example movie are D, not a population dataset. |
| Schwarz et al. (2017), [motor-control study and videos](https://elifesciences.org/articles/19892), [archived primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5315463/) | M: sucrose-evoked motor perturbations include **200 mM sucrose**, with normalized extension measurements and selective activation/inhibition. | An independent laboratory's kinematic/perturbation check. Reconcile muscle identities against McKellar's anatomical crosswalk before combining conditions; the papers differ in assignments for some muscles. Repeated whole-proboscis extension is a multi-motor output, not an acceptable compulsory MN9-alone waveform. |

**Mechanical gap:** the search found no directly usable adult muscle-9 dataset containing a calibrated force–length curve, force–velocity curve, passive load curve and paired spike train. This is a bounded search result, not proof that none exists. Published geometry and movement cannot uniquely recover those quantities.

An example of genuinely measured **adult, different-muscle** mechanics is the tergal depressor of the trochanter/jump muscle: wild-type myosin preparations have maximum active stress **37 ± 3 mN/mm²**, resting stress **0.9 ± 0.2 mN/mm²**, and slack-test velocity **6.1 ± 0.3 muscle lengths/s** at the study's conditions. These are methodological precedents or explicitly external priors, **not muscle-9 constants**. [Eldred et al., Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/)

### Identified sensory feedback

Zhou et al. (2019) separate labellar **bristle** mechanosensory neurons, which facilitate labellar spread, from **peg** mechanosensory neurons, which drive retraction. For bristle transduction, tested displacements were **1, 2, 4, 7, 10 μm**; half-maximal current occurred at **4.0 ± 0.5 μm**, **n=8**, with approximately **3 ms** receptor-current delay. The paper also examines fast sensory-to-motor transmission, but its motor drivers label multiple cells. These results do not establish a specific muscle-9 length receptor or a peg→MN9 synapse. [Primary article, Figures 2 and 5–6; supplementary movies](https://pmc.ncbi.nlm.nih.gov/articles/PMC6531006/)

P: use those contact pathways only after matching peripheral sensory identity and the relevant brain neurons. Record sensillum displacement, not an arbitrary contact bit. A bristle-deflection curve cannot be converted into a force curve without measuring bristle compliance. Do not identify every `NOMPC+` neuron with the same response or project every retraction-associated signal directly onto MN9.

## 2. Where thermal inputs belong

### Local food-temperature evidence

Li et al. (2020), adult males starved **2 h**, used **0.5 M sucrose**, **0.2–0.4 s** contact, three offerings **60 s** apart. At **17°C**, PER was **64 ± 5%, 50 ± 4%, 25 ± 6%** across offerings (means ± SEM); **21–23°C** responses approached 100%. Antennal removal preserved cooling suppression. Bitter-GRN or MSN silencing strongly reduced it; combined silencing nearly removed it. Sweet-GRN calcium responses were not directly suppressed. [Figures 1–3](https://pmc.ncbi.nlm.nih.gov/articles/PMC7329267/)

For a **23→17°C** labellar cooling ramp, S6/I6/L3 peak rates were **14.7 ± 1.2 / 8.2 ± 1.2 / 10.3 ± 2.9 Hz**; half-decline times **3.7 ± 0.8 / 5.2 ± 0.5 / 9.6 ± 1.6 s**, respectively. S6/I6 responses were attributed to bitter GRNs; L3 to MSNs. Rh6 contributes to S-type bitter cooling responses, not every cooling cell. Figures/supplementary movies are available; no separate raw-data archive is identified. [Figure 4 and STAR Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7329267/)

Use the [published correction](https://doi.org/10.1016/j.cub.2020.04.084) when interpreting Figure 2F; its “peak”/“no” labels were corrected.

### Pathway decision table

| Temperature/exposure variable | Primary evidence | Model decision |
| --- | --- | --- |
| Local temperature at labellar sensory endings | Local cooling and neural perturbations above. | Add a separately measurable labellar exposure in a later implementation. Temperature changes may arrive through contact **or local air**, so do not require food contact for all thermosensation. Sugar and mechanical stimulation remain separate physical inputs to the appropriate cells. The exact mapping to FlyWire cells in the simulated connectome remains to be established. |
| Antennal/aristal temperature and its history | Heating-responsive aristal axons project to **VP2**, cooling-responsive ones to **VP3**. The arista contains three, sometimes four, warm/cool pairs. [Marin et al. (2020), Figure 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC7443704/) | The seven modeled `TRN_VP2` cells are an anatomical mapping hypothesis for antennal warming, not seven food-temperature or damage sensors. Verify IDs, sides and duplicates; do not change cell count merely to enforce an ideal bilateral count. |
| Phasic versus sustained antennal input | Adult aristal recordings show strong history dependence. Cooling cells have similar steady-state rates at **30°C (102 ± 20 Hz)** and **25°C (92 ± 19 Hz)**, **n=7**, rather than simply firing more at colder temperatures. Hot-cell recordings require their own response curves. [Budelli et al. (2019), Figures 1 and 3; supplement](https://pmc.ncbi.nlm.nih.gov/articles/PMC6709853/) | Test ramps, reversal and adaptation. Do not transfer these **cool-cell** firing rates to VP2 warmth cells or equate a temperature offset with a universal firing-rate increment. Use the hot-cell curves as the VP2 benchmark. |
| Internal head temperature | AC neurons show persistent temperature-dependent firing above roughly **25°C**. Experiments include approximately **3°C**, **1 min** steps; **9 cells/6 animals** for a firing-rate comparison. Their downstream LPN circuit was tested in heat-dependent sleep. [Alpert et al. (2022), Figure 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC9529852/) | Internal sensors require internal temperature or an explicitly estimated heat-transfer model. Antennal point temperature is not an internal thermometer. This is not direct evidence for a hot-food rejection circuit. |
| Feeding state changes thermal preference | Taste/refeeding experiments test thermal preference after **5–60 min** feeding manipulations and involve AC/cold-sensing pathways. The preference assay itself lasts **30 min**. [Umezaki et al. (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11611295/) | Keep this direction of causality distinct: feeding state can change preferred environmental temperature. It does not show that acutely warming food must suppress PER. Refeeding/source statistics are available; this is a later state-modulation validation, not a muscle fitting target. |
| Noxious exposure at a particular body site | Adults jump from copper surfaces **>45°C**, and laser heating of the abdomen produces an intensity-dependent response latency. [Xu et al. (2006)](https://pubmed.ncbi.nlm.nih.gov/17081265/) Another adult assay reaches a **46°C** lower surface while internal air remains at most **31°C**; painless/TrpA1 perturbations affect avoidance. [Neely et al. (2011)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3164203/) | These are site- and assay-specific nociception findings, not a universal burn threshold or a labellar withdrawal transfer function. A surface's temperature cannot substitute for tissue temperature and exposure duration. Nociception, injury and subjective pain are distinct claims. |

The evidence supports separate labellar, antennal and internal thermal variables. The appropriate route depends on **where heat reaches the animal**, its time course, and the identified sensory cells. A single global temperature-to-valence function collapses these distinctions.

P: hot-food trials above the validated labellar range should initially be labelled **exploratory, outcome unspecified**. Record extension, dwell time, withdrawal and sensory activity without prescribing any outcome. A model that rejects hot food is not validated by that fact; failure to reject it is not, by itself, evidence of a broken MN9 muscle.

Larval class-IV nociceptor/rolling studies and larval numbered body-wall muscles are **different life-stage evidence**. Adult muscle 9 is not larval muscle 9, nor a larval MN9-labelled motor unit. No larval or cross-species numerical parameter is promoted to an adult CM9 measurement here.

## 3. Parameters: identifiable versus currently confounded

The candidate causal decomposition is:

**MN9 spike times → release/postsynaptic response → excitation–contraction/activation state → active and passive force as functions of muscle length and velocity → articulated motion → measured contact/deformation → identified afferent spikes → brain.**

This is a model hypothesis to test, not evidence that every stage has been measured.

| Parameter/block | What current evidence identifies | What is E/unidentifiable from a movement movie | Minimum discriminating measurement |
| --- | --- | --- | --- |
| Cell/side/muscle identity | Anatomical origins, insertions, innervation and driver-defined motor effects | Exact dataset IDs, missing axons and driver-to-connectome equivalence | Anatomical crosswalk with stable IDs, laterality and synaptic partners |
| Quantal response and effective release | CM9 EPSP, mEPSP, input resistance and effective quantal content under specified saline | Separate release probability and number of release sites; receptor kinetics from amplitudes alone | Single-event waveforms, failures, variance and paired-pulse/train responses; explicit membrane model and summation correction |
| Activation dynamics | No direct muscle-9 calibration located here | Calcium sensitivity, activation/deactivation time constants, saturation; reporter time constant versus biological time constant | Paired spikes, muscle voltage/calcium and isometric force; independently characterized indicator response |
| Geometry and moment arm | Fixed anatomy and joint images constrain placement | In-vivo moment arm across motion, fibre/tendon compliance and physiological optimal length | Measured attachment paths and muscle length over joint angle; tendon/fibre separation where possible |
| Maximum force and force–length/velocity curves | No direct muscle-9 load dataset located | Force scale versus moment arm; force–velocity curvature; eccentric behaviour | Calibrated load cell/flexible probe, isometric length series and controlled shortening/lengthening under matched activation |
| Passive force and joint damping | Resting pose alone only constrains equilibrium | Muscle passive tension versus joint elasticity, damping, antagonist activity and contact friction | Slow passive sweeps plus release transients; antagonist activity measured or independently controlled |
| Sensory feedback gain and delay | Bristle deflection-to-current/spiking and perturbation evidence for contact circuits | Muscle-9 proprioception, sensory IDs, force-to-deflection conversion, unmeasured synaptic sign/gain | Passive joint perturbation without food, then separately deflect identified sensilla; record identified afferents and downstream cells |
| Thermal transduction and tissue dynamics | Specific cell/exposure response curves | Celsius-to-injected-current gain, individual tissue temperature, local adaptation, muscle/NMJ temperature coefficients | Local temperature traces paired with sensory spikes; direct-MN9 replay with tissue temperature controlled |

Only the product of several gains may be constrained by an endpoint angle. Increasing release, activation or maximum force while reducing a moment arm can preserve that angle. Likewise, a delayed movement can arise from transmission, activation, mechanical inertia or the observation pipeline. Report intervals and these tradeoffs rather than selecting one parameter set and calling it measured.

## 4. Concrete tests in dependency order

All numerical grids and acceptance rules in this section are **P**, not reported adult firing ranges or biological constants. Tests are proposed for a numerical replay assay or new experimental acquisition.

### A. Causal and physical checks before behavioural fitting

1. **Timestamped replay.** Preserve per-cell spike times, simulation time, integration step, units and side. Replay the same train with different numerical batch sizes and observation sampling rates. Force and motion must agree within the numerical tolerance below. Event timing must remain independent of output sampling. Save NMJ state, activation, muscle length/velocity, forces, joint state and afferent events in the same clock.
2. **Remove downstream drive at distinct stages.** Compare zero MN9 spikes, release blocked, postsynaptic transmission blocked and active force disabled. Existing states may decay and passive forces may move the joint; there must be no newly spike-driven active work after the corresponding block. TNT-equivalent release block and electrical neuron silencing are different interventions. Other muscles must not silently receive substituted MN9 drive.
3. **Isometric versus free motion.** Clamp the rostrum at several poses. The same spike input should produce a measurable reaction force with no commanded displacement. Remove the clamp and measure movement. If the implementation cannot produce force against a clamp, it has not replaced the position proxy.
4. **Passive mechanics.** With active drive disabled, displace and release the joint. Account for elastic, gravitational, contact and dissipative energy; do not require zero passive force. A settling equilibrium must emerge from these forces. A scripted return to a desired angle fails this test.
5. **Convergence.** Halve the integration step and repeat the same replay. Proposed numerical threshold: changes in peak force, angular excursion and onset latency must be **<5%**, or below instrument/time-bin resolution for near-zero quantities. This is an engineering check, not a biological tolerance. Passive runs must not gain unexplained energy.

### B. Identify transmission and activation without food

Use the adult CM9 preparation with the exact source saline, age, sex, temperature and muscle-fibre selection recorded. Obtain spontaneous and evoked events first. For new acquisition, use electrical sampling at least **10 kHz** as an initial design choice, with anti-alias filtering and stimulus synchronization documented; increase it if the latency question requires it.

P stimulus panel: single pulses; paired pulses with **10, 20, 50, 100, 200, 500 ms** intervals; **1, 5, 10, 20, 50 Hz**, **0.5 s** trains, followed by a recovery period justified by measured return to baseline. Actual presynaptic spikes must be confirmed. This panel tests history dependence; it does not assert these rates occur naturally. Avoid interpreting optical pulse frequency as a confirmed motor-neuron spike frequency.

Fit NMJ parameters to electrical observations only. Fit activation to independently observed voltage/calcium/force, with the indicator's observation model included. Reserve one train frequency, one recovery interval and independent animals/days. A matched endpoint with an incorrect EPSP, relaxation transient or held-out train response fails that stage.

The pharmacological/homeostatic challenges in Section 1 are optional model-discrimination tests. A fixed-transmission milestone need not implement ageing or homeostasis, but must explicitly limit its claim to the validated state; it cannot cite those processes as implemented.

### C. Acquire muscle-9 mechanics under independent load

Use a calibrated cantilever or force probe coupled to the rostrum with measured application point and angle. Measure probe stiffness independently and compute force from probe deflection; transform to torque using the measured geometry. Tip force includes transmission through other structures, so isolating intrinsic muscle parameters requires additional fibre/tendon information.

P acquisition sequence:

- Measure passive torque across **five evenly spaced positions within the observed physiological range**, in both directions, before fitting active mechanics. Quantify hysteresis, drift and antagonist activity.
- At those positions, apply the same confirmed spike train and obtain isometric active-minus-passive force. Repeat at more than one activation level to test separability of activation and length effects.
- Measure shortening against zero added load and **three calibrated nonzero loads**. Select the loads from a separate pilot that establishes instrument resolution and the animal's measured force range. Freeze them before validation; report actual newtons/torques, not only percentages of model-predicted maximum force.
- Obtain slow imposed shortening and lengthening trials at matched activation. Fit one velocity range; reserve a different velocity/load combination and an independent day.

No contraction force, damping or preferred length may be adjusted using sucrose success or hot-food rejection. Until this acquisition exists, publish an E-labelled parameter ensemble and sensitivity results; a force-model implementation may proceed, but force–length/velocity validation remains **no-go**.

### D. Motor perturbation holdouts

After component calibration is frozen, reproduce the Section 1 source protocols and score head, rostrum, haustellum and labellar motion separately. Include activation from rest, activation during ongoing extension and MN9 release block during sensory-evoked reaching. Use both driver-only and effector-only experimental controls; collect acute perturbations as a separate test of developmental compensation from chronic silencing.

Keep one publication/cohort entirely out of calibration. If McKellar's data influenced geometry or kinetics, mark the affected comparison as a fit check and use new animals or the independent study for validation. Never count Video 14 and its source figure as independent datasets. Preserve all repetitions within an animal when splitting data.

A one-muscle milestone must identify which coordinates it claims to reproduce. Full retraction, labellar spreading and food ingestion require additional motors. Coupled movement needs measured mechanics or identified neural mediation; commanding secondary joints to match the movie is a failure. Do not require a prescribed whole-proboscis cycle from MN9 alone.

### E. Close a sensory loop only with identified cells

First replay measured contact/deformation open-loop into a matched sensory model. Reserve part of the displacement range for validation. Then generate contact from the physical movement and compare predicted afferent latency, rate and adaptation against independent recordings.

Discriminate feedback from mechanics with four matched conditions: intact loop; afferent transmission blocked; afferent spike replay independent of current motion; passive externally imposed motion/contact. Motor input and mechanical load must be held fixed in the initial comparisons. A claimed feedback correction must disappear or change specifically when its sensory route is interrupted, with the peripheral sensory response and central response checked separately.

If the afferent identity or connection to the simulated brain is missing, return **unmapped feedback**. Do not inject generic “proboscis position” or “error” spikes into convenient neurons. A verified contact-afference path may be claimed as such; it is not evidence for muscle-length proprioception.

### F. Thermal tests after freezing the motor model

Use the local cooling protocol in Section 2 as the first behavioural thermal holdout. Fit thermal transduction only to sensory recordings. Retain the behavioural percentages, repeated-offering trend and silencing responses as independent predictions. A neuron-level fit and a behaviour-level fit to the same experimental trial are not independent validation.

| Test | Controlled contrast | Discriminating readout |
| --- | --- | --- |
| F1: local site | Change labellar temperature while antenna/head remain fixed; separately change antennal temperature while labellum/head remain fixed | Local sensory spikes, MN9 spikes, force and motion. Measure all local temperatures; do not assume thermal isolation. Compare intact and antenna-blocked cases against the source result. |
| F2: thermal dynamics | Reach the same final local temperature by fast/slow ramps and from opposite directions; include a constant-temperature hold | Onset, adaptation and sustained firing for each class; fit neither warming nor cooling as a memoryless valence multiplier. |
| F3: causal sensory interventions | Replay the source's bitter-GRN, MSN and combined transmission blocks; add Rh6 loss/rescue with the documented cell restriction | Predict effect sizes on both sensory activity and feeding response. Leave sweet transduction and muscle parameters frozen. A behavioural rescue produced by retuning motor gain fails. |
| F4: physical confounds | Match sucrose concentration, contact geometry/force, humidity and trial order; record viscosity and evaporation | Distinguish altered sensory transduction from altered contact/load. Use temperature-matched no-sucrose and sham-contact controls. |
| F5: peripheral motor temperature | Replay identical confirmed MN9 spikes while muscle/head temperature changes independently of sensory input | NMJ, activation and force kinetics. A temperature effect here must be measured and assigned to that block, not mislabelled a feeding decision. Any Q10 is E until calibrated. |
| F6: arena integration | Let motion determine antennal and labellar trajectories through a measured thermal field | Input follows sensor location and local exposure, not food identity or reward. The historical antenna-only configuration cannot establish labellar-food-temperature validation. |
| F7: high-temperature exploration | Local warming outside the evidence range, with temperature and exposure time logged | Outcome unspecified. No hot-food rejection or tissue-damage pass criterion until a relevant adult, site-specific dataset and identified circuit exist. |

Avoid temperature-gated neuronal effectors when the independent variable is temperature, unless their activation function and controls explicitly separate the manipulation from native thermosensation. Optogenetic controls must likewise exclude heating and visual effects.

## 5. Data acquisition and analysis contract

The acquisition routes below distinguish published observations from data that still need measurement or recovery.

| Needed data | Public acquisition route/status | Work still needed |
| --- | --- | --- |
| Adult CM9 electrical reference | Mahoney [Table 1/full article](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/) and [recording protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413541/) | Transcribe exact condition-labelled table values; obtain new raw trials for kinetics, train responses and load pairing. No raw electrophysiology archive verified here. |
| MN9 perturbation kinematics | [McKellar article, figures and movies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316511/); [Video 14 file](https://pmc.ncbi.nlm.nih.gov/articles/instance/7316511/bin/elife-54978-video14.mp4); [independent Schwarz study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5315463/) | Digitize displayed points/angles with uncertainty; confirm playback versus acquisition timing before deriving velocity. No machine-readable all-animal trajectory archive verified. |
| Contact afferents and motor perturbations | [Zhou article and supplementary materials](https://pmc.ncbi.nlm.nih.gov/articles/PMC6531006/) | Extract displacement-response and latency curves; distinguish displayed examples from biological replicates. The article states that additional raw data are available on request; no public raw-data download was verified. |
| Labellar cooling physiology and behaviour | [Li article and supplementary movies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7329267/); [supplementary PDF](https://pmc.ncbi.nlm.nih.gov/articles/instance/7329267/bin/NIHMS1582605-supplement-2.pdf); [correction](https://doi.org/10.1016/j.cub.2020.04.084) | Extract the recorded temperature trajectory as well as neural output. Separate sensory fitting from behavioural scoring. Digitization is not access to raw per-fly data. |
| Antennal warming/cooling | [Budelli article/supplement](https://pmc.ncbi.nlm.nih.gov/articles/PMC6709853/); author-linked [analysis code](https://github.com/masonklein/neurophys/); [Marin anatomical study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7443704/) | Analyse warmth-cell data specifically; validate circuit IDs and sides. The linked code is an acquisition lead, not a verified raw spike archive. |
| Internal thermosensing and state | [AC electrophysiology](https://pmc.ncbi.nlm.nih.gov/articles/PMC9529852/); [taste/temperature-preference article with source files](https://pmc.ncbi.nlm.nih.gov/articles/PMC11611295/) | AC raw data are available on request per the paper, not verified as a public download. Temperature-preference source files must be inspected for their actual contents before calling them raw observations. |
| Muscle-9 mechanics and specific proprioception | No matched public dataset verified in this search | New physical measurement and cell identification; retain explicit E/unmapped status meanwhile. |

For each observation retain DOI/URL, figure/panel, acquisition method, species/stage, genotype, sex, age, feeding/deprivation state, saline, local temperature trace, stimulus, load, units, sample size and whether errors are SEM, SD or confidence intervals. Distinguish raw observations, displayed summary values and digitized estimates. Use two independent annotations on a subset to estimate digitization/tracking error; do not normalize every trial to its own maximum and thereby erase amplitude failures.

Preregister the calibration/holdout split, observables and analysis before fitting. Use animal/day as replication units; neither video frames nor repeated contacts are independent animals. For PER report binomial uncertainty with repeated trials grouped by fly; source cohort-level SEM cannot be silently converted into invented individual trials. For physiology/motion report effect size, latency, waveform error and parameter intervals, including negative results.

## 6. Go/no-go criteria

These gates separate an implemented hypothesis from an experimentally validated mechanism. The original proposal did not report completed gate evaluations; current numerical evidence is tracked in [status](../status.md).

| Gate | Go | No-go / permitted narrower claim |
| --- | --- | --- |
| G0: causal force implementation | Spikes enter an explicit transmission/activation/force chain; clamp, block, passive-energy and replay/convergence checks pass | Any position target, outcome-tuned food/temperature-dependent actuator gain, scripted withdrawal, or output-sampling-dependent actuation: no-go. Independently measured temperature effects on NMJ/muscle kinetics remain legitimate. |
| G1: transmission | Condition-matched adult CM9 electrical amplitudes and held-out event/train responses agree within prespecified experimental uncertainty | Movie match alone: only an estimated transmission model |
| G2: mechanics | Independently calibrated force–length, velocity and passive measurements predict held-out loads and starting poses | Absent direct load data: permit an E-labelled force-model prototype; no muscle-9 mechanical-fidelity claim |
| G3: motor effect | Frozen components predict independent activation/silencing effects and rostrum kinematics within a declared scope | Missed effect signs, compensatory tuning, or demands for unsupported multi-muscle behaviour: no-go for that claim |
| G4: sensory closure | Named afferents, physical stimulus mapping and brain connections are documented; blocked/replayed-afference contrasts support the claimed loop | Generic position/error feedback or an unidentified MN9 proprioceptor: no-go; contact-afference alone must be labelled narrowly |
| G5: thermal feeding | Independent sensory calibration predicts held-out local-cooling and intervention effects; site-isolation controls pass | Antenna-only warmth drive, global thermal valence or fitting to acceptance/rejection: no-go |
| G6: nociception/injury | Adult site-specific transduction, circuit identity and exposure-response data predict independent nociceptive perturbations; an injury claim additionally requires measured tissue damage | Current milestone: no-go for burn or biologically validated hot-food withdrawal claims. Nociceptive-circuit validation would not establish subjective pain. |

P statistical acceptance: define an equivalence margin for each observable from a **separate measurement-repeatability pilot and the scientific resolution required**, before seeing model predictions. Accept only if the **95% confidence interval** for model–data discrepancy lies inside that margin, and prespecified causal effect signs match the held-out interventions. If measurement uncertainty is too wide to discriminate the competing models, the result is **inconclusive**, not a pass. Do not widen margins or prediction intervals after a failure. Report structural non-identifiability even when predictions pass.

**Immediate next acquisition:** condition-matched CM9 electrical replay plus calibrated passive/isometric rostrum force. In parallel, assemble the published MN9 perturbation and labellar cooling holdouts without using them to select muscle parameters. This makes the first replacement falsifiable while keeping the unmeasured force and sensory links visible.

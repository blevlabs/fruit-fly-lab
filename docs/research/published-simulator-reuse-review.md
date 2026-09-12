# Published fly simulators and reusable brain–body interfaces

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

## Assessment

**Substantial reusable work already exists, but none of the inspected public implementations supplies the complete anatomical, physiologically calibrated adult fly required by the program.** The closest demonstrations combine real connectome data with learned motor decoders, selected descending-neuron controls, imposed stepping patterns, or direct body motion. Those systems demonstrate useful engineering capabilities within their declared models; they do not supply the missing sensory-organ, neuromuscular and physiological correspondences. Eon's own technical explanation explicitly identifies its incomplete downstream motor hierarchy.[^eon]

The practical conclusion is to **reuse the strongest components and measurements, while continuing the missing mechanism work**. The inspected model already uses the contemporary FlyGym body stack, FlyMimic foreleg geometry, the Eon neural implementation, and a same-specimen MaleCNS brain/VNC graph. A migration to another named simulator would repeat substantial work and would not resolve the outstanding motor-unit or sensory-transduction gaps. Current upstream revisions were checked; no newer FlyGym or Eon implementation containing the missing complete body bridge was found.[^flygymcode][^eoncode]

The review did find useful work that was missing from the existing source inventory:

- BANC's published peripheral tables give more specific neck targets and expose five current MaleCNS retinal/neck classification conflicts.
- A new respiration study identifies **19 current MaleCNS efferent neurons** outside the original 815-motor selector, with an explicit 19-versus-18 population discrepancy to resolve.
- Hair-plate physiology and leg-bristle mapping studies provide concrete M1/M3 source packages.
- FlyBrainLab provides released mechanistic odor and photoreceptor models. An **80.6 MB original odor-response dataset was recovered**, including an already-matched Or59b class.
- The original Huang/Luo memory-model source supplies experimental workbooks, fitted parameters and equations that should be evaluated directly, rather than inferred from game-demo plasticity.

These findings change the next source actions. They do not change the runtime mapping counts or certify any full-program acceptance gate. The review is bounded to the original publications, supplements, repositories, releases and public demonstrations documented below, including the inspected community implementation catalogue. It does not assert that no private or unpublished implementation exists.

## What would count as the completed interface

The target is a specific causal chain: physical conditions affect organs; identified receptors transduce those conditions; the retained CNS transforms their activity; identified motor neurons excite their actual muscle units; forces change the body; and the changed body produces new sensory signals. Every boundary requires both an identity map and a dynamic model. A body mesh, a neuron label, a firing trace and a successful task each answer different questions.

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| EM connectome and cell annotations | Reconstructed chemical contacts, cell identities and some biological classifications | Synaptic conductance, receptor kinetics, peripheral attachments or learned state |
| Peripheral tracing and matched microscopy | A specific sensory organ or muscle target at the stated resolution | Force–frequency curves, transduction dynamics, exact anatomy of another specimen |
| Implemented loop | The stated software passes signals and updates state | Accurate integration, biological fidelity or useful behavior |
| Numerical comparison | Agreement under a stated timestep, precision, reset or continuation test | Correct anatomy or physiology |
| Independent biological comparison | Prediction of an observation outside the fitting data, under matched preparation | Unmeasured systems or the full adult repertoire |
| Task success | The implemented model accomplishes the measured task | That its connectome, sensory encoding or motor interface is biologically correct |

Digital Sphinx provides an unusually clear demonstration of the last distinction: a worm connectome, random fly-to-worm sensory projection and a learned decoder can produce plausible fly walking. It is a counterexample to using successful movement alone as validation of biological correspondence, not an argument against connectome modeling.[^sphinx][^sphinxcode]

## Original simulator families

The source datasets have different anatomical boundaries. FlyWire is a female brain; FANC is a female nerve cord; MANC is a male nerve cord; BANC and MaleCNS contain brain and nerve cord in one specimen. Cross-dataset type correspondences support reuse, but a root/body ID from one dataset cannot become an edge or peripheral identity in another without the corresponding evidence.[^flywireoriginal][^fanc][^manc][^banc][^malecns]

The published MaleCNS paper was read through the browser, including STAR Methods. Its final count is 166,700 neurons; an older Google publication summary still reports 166,691. The paper's sensory-to-motor analysis uses maximum flow on the graph and explicitly requires functional validation. That publication-level count also differs from the model's expanded selection; preserve each selector and source identity rather than normalizing the numbers into one “complete” count.[^malecns]

| System | Neural/anatomical scope | Actual sensory and motor boundary | Reusable result | Full target met? |
|---|---|---|---|---|
| Shiu 2024 | FlyWire v630 brain; 127,400 modeled neurons | Poisson activation of identified cells; spike readouts at MNs/DNs | Circuit assays, original predictions and experimental outcomes | No physical body or VNC |
| Eon public brain code / embodiment | FlyWire brain; accelerated Shiu-family dynamics | Public code is neural benchmarking; demonstrated body uses selected DNs and imitation controllers | Neural execution and cross-backend comparisons | No complete public body bridge or downstream motor hierarchy |
| NeuroMechFly 2022 | Physical adult body with constructed oscillator controller | PD movement replay or optimized oscillator/spring–damper actuation | Body geometry, kinematics and physics experiments | No anatomical connectome controller |
| NeuroMechFly v2 / FlyGym | Physical body, multiple modeled sensors; optional FlyVis subnet | Visual-network readout and other high-level rules feed CPG/reflex stepping | Existing body, sensing and reference experiments | Motor-neuron/muscle mapping incomplete |
| FlyBody 2025 | Detailed female body and idealized sensors | RL MLP controllers; position/torque actions and wing-pattern generator | Body assets, anatomical images, locomotion data | No complete biological neural interface |
| FlyMimic | Anatomical foreleg muscle model | Hill-type muscles controlled by imitation-trained policy | 15 foreleg muscle/tendon paths, source model files | No all-body map or connectomic policy |
| Özdil antennal grooming | Anatomical central grooming subnetwork | Learned MN-voltage→angle decoders; separate kinematic body replay | Named circuit identities and experimental coordination evidence | Leg MNs excluded; no full physiological loop |
| Pugliese | Selected MANC/MaleCNS VNC circuits | Source-defined neural stimulation and recurrent dynamics | Candidate rhythm mechanisms, size/connectivity data | No complete body/sensory implementation |
| FlyVis | Consensus, tiled optic-lobe motion circuit | Visual input→graded neural dynamics→trained optic-flow readout | Neural tuning comparisons and visual-model ensemble | Visual subsystem only |
| FlyBrainLab / OlfTrans / VisTrans | Modular sensory and brain-circuit models | Mechanistic odor/photon transduction at supported class resolution | Physiological reference models and data | No specimen-matched whole adult loop |
| FlyGM / earlier flyGNN | Whole-brain topology used as graph architecture | Learned observation encoder, neuron updates and action decoder | Learned-controller comparison design | No anatomical muscle adapter; code unreleased at inspected route |

### Shiu and Eon: preserve the neural baseline, do not extend its validation by analogy

Shiu's feeding and grooming predictions have real experimental support. The paper reports 91% agreement over 164 tested predictions, or 84% after excluding the predominantly negative optogenetic screen. However, it explicitly says the quantitative MN9 firing-to-rostrum relation is unknown. Its shared synaptic weight was chosen using the sugar→MN9 response, so that response is not an independent calibration of muscle force.[^shiu]

The original `model.py` implements homogeneous LIF dynamics with an exponentially decaying **voltage-equivalent** drive, not a measured conductance in siemens. Its stimulation helper uses a large Poisson-input multiplier and removes refractory time for stimulated cells. There is no chemical-concentration model, sensory organ, NMJ or body in that implementation. Current upstream still equals the local pinned revision `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`.[^shiucode]

The publisher workbook was recovered and inventoried. It includes the 106-cell-type optogenetic comparison, actual behavioral numerator/denominator tables, and the prediction categories and citations. Those records can support exact, preparation-matched neural/behavioral reference assays. The accessible Edmond API also catalogues the original simulation-output archive; its 4.5 GB results ZIP was not needed for this interface audit.[^shiusupp][^shiudata]

Eon's March 2026 methods describe selected DNs driving imitation-trained walking and grooming controllers, partly hand-chosen sensory/DN scaling, and limited behavioral influence from current visual activity. Its public August 2026 repository contains neural runners and comparison utilities, rather than the demonstrated complete embodiment bundle. The existing GPU implementation is useful; its demo cannot supply a missing biological motor hierarchy simply by copying the announced architecture.[^eon][^eoncode]

### Body simulators: most usable geometry is already incorporated

Original NeuroMechFly optimizes a constructed oscillator/spring–damper system and separately replays measured movements. NeuroMechFly v2 improves the sensory/body platform, but its fly-following example still converts visual-network activity into engineered steering, then hybrid CPG/reflex stepping. Its supplement places motor-neuron/muscle integration in future work.[^nmf][^nmf2][^nmf2supp]

The source confirms the boundary. Current CPG code turns phase into `PreprogrammedSteps` angles and phase-defined adhesion; the hybrid controller adds prescribed retraction/stumbling corrections from simulated contact. The publication-era visual wrapper supplies a useful retinotopic interface, but it inherits the turning controller. FlyGym 2.x was rewritten in April 2026, so publication-era scripts and today's API are separate reproducibility targets.[^flygymcode][^flygymlegacy]

FlyBody provides detailed morphology and meaningful physics-based locomotion results using trained controllers. The paper expressly distinguishes its actuator commands from biological muscle commands. The supplement models haltere-like and proprioceptive information through ideal gyro, acceleration, angle and velocity sensors; these are not neuron-specific organ transfer functions. Its actuator and aerodynamic choices include values selected for functioning locomotion and hovering, rather than independent motor-unit calibration.[^flybody][^flybodysupp]

The useful FlyBody assets are its body XML/meshes, anatomical imaging, kinematics, observable interfaces and reference fluid calculations. Its MLP policies and phase-driven wingbeat generator are different mechanisms from the required adult motor/NMJ/muscle chain. The exact original dataset catalog, file IDs and terms are retained in the source inventory; bulk imaging and walking archives were not downloaded again.[^flybodycode][^flybodydata]

FlyMimic is a genuine advance in muscle geometry and mechanics. The public OpenSim variants—including the file named `best_combined_full.osim`—both contain the same 15 left-foreleg muscles, not a complete six-leg muscle body. Its paper describes additional middle/hindleg modeling, but those exact assets were not found at the documented public implementation route. Local `leg_muscles.py` already uses the current FlyGym copy of this geometry, with SHA-256 `04f6070d6733940357be005ca72c02ba0d9455538ff018da70c74de7458e9531`.[^flymimic][^flymimiccode]

A further distinction matters for the Eon-cited grooming work. Özdil's 2026 publication tests central inhibitory coordination, while learned decoders map antennal/neck MN voltages to joint angles. The training code jointly fits neural and decoder parameters. Those circuit identities and measured responses are useful; the decoder is not the missing physical muscle map.[^grooming][^groomingcode]

### Neural and learned controllers: reuse the hypothesis at its supported boundary

Pugliese's current repository remains the already-inspected revision `faee4b06869855ae0164cbf217fb6ec28ef3521b`. It provides a tractable recurrent VNC rhythm hypothesis and associated data, not a whole-body simulator. The inspected model already records its limited exact-ID/size coverage. Replacing the retained CNS with that stimulated subset would change the question rather than resolve missing full-body feedback.[^pugliese][^pugliesecode]

FlyVis supplies a stronger visual-response reference than a generic all-spiking optic lobe. Its 64-cell-type consensus circuit is tiled from sampled FIB datasets, and its parameters are optimized on an optic-flow task before neural tuning is assessed. Current source includes graded-release equations, retinotopic inputs and pretrained-model download identities. These are suitable comparison tools; they are not a same-specimen replacement graph for MaleCNS or uniquely measured receptor kinetics.[^flyvis][^flyviscode]

FlyGM uses learned sensory encoding, shared trainable graph updates and an efferent decoder, first imitating FlyBody policies and then optimizing with PPO. Flight uses a wingbeat-pattern generator. The official project still advertises code as forthcoming, and its graph description differs from the latest manuscript. It is a potentially useful engineered-controller comparison, but neither runnable complete anatomy nor a source-grounded motor adapter was available.[^flygm][^flygmpage]

Adjacent neural papers were also checked: the Loihi 2 work accelerates neural execution; the September 2026 orientation-map paper bypasses photoreceptors by stimulating L1–L3 and selects a neural gain for sufficient medulla firing; network-structure work studies activation propagation; larval neuromechanics concerns a different body and developmental stage. None supplies the missing adult peripheral loop.[^loihi][^orientation][^networkstructure][^larval]

## Newly useful anatomical and physiological packages

### BANC target tables and neck classification conflicts

BANC's final publication uses v888 and a new data archive, replacing the preprint's v626/archive. Its supplementary CSVs include peripheral-target fields and revised FlyWire/MANC classifications. The 608 nonempty targets among 805 BANC motor rows include generic organ labels, so that count is not 608 resolved muscle units. The MaleCNS-aligned supplemental table itself lacks a peripheral-target column.[^banc][^banctables]

The exact-root comparison yields four worthwhile cases:

| Published type / target | Current MaleCNS candidates | Required adjudication |
|---|---|---|
| CvN3 → sclerite rotator | 10554, 10699; GNG648 / CB0913 | Peripheral side and underlying terminal anatomy |
| CvN1/CvN2 → oblique-horizontal **or** transverse-horizontal muscle | 12180, 13128, 11879, 12342, 12097, 231558 | The source leaves the target alternative unresolved |
| VCvN3 → oblique-horizontal muscle | 12173, 12631; GNG314 / CB0004 | Current MaleCNS retinal subclass conflicts with exact FlyWire/BANC neck classification |
| VCvN1/VCvN2 → oblique-horizontal muscle | 12076, 12126, 13592; GNG647 / CB0918 | Same class conflict; combined type does not resolve individual fiber allocation |

All 12 corresponding exact FlyWire roots are independently classified as neck motor neurons in the pinned official annotation table. That supports a concrete classification review. It does not justify choosing a motor's peripheral side or changing muscle capacity. The retained evidence package preserves both original labels and the candidate source targets.[^banctables][^flywireanno]

Bulk adoption of `malecns_match` would be unsafe scientifically: the published table includes matches whose actual MaleCNS type disagrees, including MN4b→MN2Da and MN8→MN2V examples. Retinal/antennal rows mostly remain generic, and the proboscis `side` field does not resolve the six peripheral laterality cases. The original source questions remain open where the new tables do not answer them.[^banctables]

### Respiration expands the effector inventory

Luo's July 2026 respiration study supplies an important overlooked class. Its author notebook names 19 MaleCNS spiracle-motor candidates; all exist in current v1.0 as `ENXXX226`, superclass `vnc_efferent`, outside the original motor selector. Four have source-supported thoracic groupings: 807088/906222 mesothoracic and 809582/810035 metathoracic. This is an actionable inventory expansion.[^respiration][^respirationcode]

The paper and MANC list describe 18 cells, while the MaleCNS list contains 19. The extra member is localized to curated `mancGroup=17510`: one left-soma and two right-soma cells. All must be preserved until resolved. Abdominal segment/side assignments, closer attachments, flap mechanics, neural-to-force response and aperture-to-gas/water flux are still missing. The linked Dryad record currently reports that its identifier cannot be viewed; this is a specific external data dependency.[^respirationcode][^respirationdata]

### Hair plates, tactile bristles and serial-leg anatomy

Pratt's 2026 study provides six named foreleg hair-plate organs, measured CxHP8 physiology, and published connectivity analysis. Its code names the exact FANC CAVE tables; the data catalog includes angle/calcium and perturbation records. The remaining reusable package is a materialization-pinned identity export and the source geometry. The inspected release did not supply a verified downloadable Blender asset containing those organs, and normalized calcium cannot be imported as firing rate.[^hairplate][^hairplatecode]

Elabbady's 2026 work provides a left-foreleg bristle map and analysis code. The paper's 409-axon population differs from the public 425-entry annotation JSON. Its mapping landmarks are central-neuropil coordinates, not locations on the external leg. The files help resolve identities and somatotopy, while physical receptor-site registration, axon correspondence and cuticle/hair mechanics remain separate work.[^bristle][^bristlecode]

The older FANC atlas already gives a near-complete **69-MN→18-target left-foreleg** correspondence, and MANC provides target/nerve/serial-homology information. These are strong subsystem resources already substantially used here. A newly located ESRF 2026 abstract reports middle/hind-leg XNH with individual motor-unit innervation and sensory receptors, directly matching the remaining serial-leg need. No public segmentation/identity release for that specific new acquisition was located; the concrete missing package is specified in the anatomical appendix.[^fanc][^manc][^esrf]

### Mechanistic sensory models with actual experimental records

FlyBrainLab is an executable circuit platform with molecular sensory libraries, not a completed body map. Its assembled example circuits include population simplifications, so the reusable layer is the supported component model and its data rather than wholesale replacement of current anatomy.[^flybrainlab]

OlfTrans implements filtered odor concentration, binding/co-receptor dynamics, calcium feedback, saturating current and a noisy Connor–Stevens spike generator. The original model has receptor-class assumptions and fitted parameters; steady odor-response tables alone cannot identify binding and dissociation kinetics independently. Its CPU, NeuroDriver and EOScircuits defaults differ, including maximum-current values **62.13, 150 and 150.159**. Reproduce the original figure configuration before choosing any runtime transfer.[^olftranspaper][^olftranscode]

The original HDF5 was recovered intact: **80,572,168 bytes**, SHA-256 `89ba48164a6db16d14ad2a9b2b8798d5babfcb0f154140041e7053b3b4553715`. It contains stimulus/PSTH records, not raw individual spike-event trials. Its `elife15` step/ramp/parabola groups are the clearest Or59b–acetone comparison route; white noise includes source fitting data. The file also contains ambiguous duplicated odor labels and a time vector ending at 3,525,000 beside a roughly 3.5-second stimulus. Those groups remain evidence requiring reconciliation, not values to silently repair.[^olfdata]

Or59b→ab2A→DM4 is already supported in the model's reference mapping; the new dataset therefore overlaps an identified channel. Acetone is not methyl acetate or ethyl acetate. Independent exact-acetate routes are Martelli/Fiala's methyl-acetate/Or59b work and Gorur-Shandilya's ethyl-acetate/ab3A work. Their spike, calcium and detector-voltage quantities must remain distinct.[^taskodor][^martelli][^gorur]

VisTrans/Neurokernel supplies stochastic photon-to-voltage models based on outer R1–R6 physiology and microvilli. Original comparisons include light-adaptation and naturalistic responses, while several molecular parameters remain fitted. The generic retina geometry and synthetic port IDs cannot fill missing MaleCNS retinal correspondence. Begin with one absorbed-photon/voltage reference assay and preserve measured optical registration; R7/R8 and downstream graded transmission need their own support.[^song][^retinarfc][^vistranscode]

### Curated transmitter evidence, beyond single classifier labels

The published MaleCNS methods point to original curated transmitter ground truth and a companion peptide collection. Their current CSVs, type crosswalks, citations and CC-BY-4.0 notices were recovered. Exact whole-string matching against the current 3,656 unresolved cells finds transmitter-source records for **169 cells** and peptide records for **112 cells**, a union of **219 cells**. Positive evidence with source confidence at least three exists for 101 and 90 cells, respectively. These are source-review candidates, not resolved physiological assignments.[^groundtruth]

The source datasets contain negative/untested evidence, cotransmission, conflicts and one-to-many type correspondences that a single consensus label cannot represent. They also include data used to train the classifier, so source agreement is not automatically independent validation. Review each original measurement and cell match; expression alone does not establish release kinetics, postsynaptic receptor effect or a fast-current sign. No unknown edge was assigned a sign by this audit.

## Community implementations, persistence and controls

The expanded community-code audit is retained in separate, versioned evidence reports. It verifies the public demonstration claims against actual source and committed results; descriptive names such as “whole brain,” “snapshot,” “muscle” and “shuffled” are not used as evidence by themselves.

### A real DN–VNC–MN extract, but no new motor identity coverage

`desktop-fly` genuinely ships a MaleCNS locomotor subgraph: 1,045 cells, 17,224 directed edges and 708,689 contacts. Its source hashes and 1,045 annotation identities match the same official inputs used here. All **220 selected MN IDs and all 220 leg assignments already match the current motor map**; no new motor target is supplied.[^desktop]

Its stored DNa02 path **10360→801027→805410**, with 99 and 85 contacts, is a useful compact regression fixture. However, its physical adapter pools motor rates by family, applies saturation and combines channels before reduced joint dynamics; its knee coefficient was explicitly increased to obtain the desired MDN power stroke. All 153 sensory records lack joint/direction tuning and receive pooled body variables. Reuse the extraction/path records, not these gains or sensory assignments as physiological calibration.[^desktopmechanics]

`flygame` does not provide an immediate deterministic speedup for this model. The inspected executable initializes a generated regional graph, uses a CPG/position-actuator body, and exchanges neural/body state asynchronously. Its proprioceptive addition is overwritten by the following intent update, a static source finding. Its checkpoint utility is not integrated with the complete application state, and wing support is a stub. Advertised speedup was not backed by a comparable paired benchmark.[^flygame]

`flyloop` retains source-derived MaleCNS data, but computes target bearing/boundary steering and injects a selected DN directly. DN rates become speed/yaw; legs and flight are animated by prescribed functions. Its snapshot is telemetry, not complete resumable individual state. This is useful graph visualization and I/O engineering, not a missing sensory–muscle plant.[^flyloop]

### Original public demonstrations

The original social posts were read, not inferred from reposts. Slava's pong author explicitly reports trained weights and separate states; Sudoku's author describes two trained, Sudoku-structured output models and animated walking; the tycoon author discloses a game planner and unvalidated learning; MindFly's author describes a focus threshold triggering 10 Hz neural stimulation. The sound-conditioning, football and FlyOut posts provide no complete reproducibility/control package. These are accurately bounded author claims, not evidence that the physical or adaptive gates are already solved.[^social]

### Game interfaces and claimed learning, checked against source

| Repository | What actually supplies the action/learning | Useful reuse and boundary |
|---|---|---|
| `nftechie/doomfly` | Named DN→Doom decoder; selected KC→MBON11 plasticity and substantial neural checkpointing | Original physiology reference, state/error handling and memory-erasure controls; author capability gates remain failed |
| `ornata/fly` / Fly64 | Approximate retina→fixed MaleCNS model→handwritten Mario decoder | Data manifests and deterministic stimulus replay; no fly muscles or learned neural state |
| `alextitonis/fly.ai` | Direct visual-feature-cell stimulation from privileged game state; trained external readout | Bilateral pathway diagnostics; retinal failure must be repaired rather than hidden by feature injection |
| `mutkuoz/flydoom` | Brain-only mixed neural model, proxy sensory fields and DN/game decoder | Rich negative-result and identical-configuration controls; no VNC/body or persistent synaptic learner |
| `martialsystems/fly_chess` | Synthetic chess fixture with trained legal-move head; separate 475-cell MaleCNS assay | Real/rewired circuit-selectivity control; its tuned gain is not physiological calibration |
| `fruitflydev/flycoinrh` | Screenshot/DN cursor adapter; callback-driven KC→MBON gains | DoOR source joins; reversed DAN-matrix lookup and incomplete saved state prevent adoption as a learning model |
| `theflyRH/thefly-brain` | Fixed FlyWire sugar→MN9 assay; cold resting-state restoration per trial | Small rest/stimulation/rewiring reference; no learned individual |
| `ranagwho/Fruitfly-Doomscroller` | KC-dependent depression coexists with an engineered visual-novelty decoder controlling scroll | A failure mode to guard against: weight change need not cause the task decision |
| `erojasoficial-byte/fly-brain` | Generic Hebbian update; CPG/hybrid body controllers; weight-vector-only resume | Inspectable prototype, with incomplete physiological and continuation guarantees |
| `snedea/flybrain` | Missing movement groups filled with synthesized motor values; explicit food-directed steering | Source provenance/visualization only for this target; not an anatomical motor solution |
| `sjcabs/fly_connectome_data_tutorial` | Versioned joins, named neural perturbations and comparative analysis | Useful loaders and exact FAFB IDs; MaleCNS example is v0.9 and some physiological files are currently missing |
| `watthem/awesome-fruit-fly-connectome` | Discovery index | Useful leads; contains a FlyBody/Eon attribution error and cannot validate linked claims |

These rows are grounded in the pinned source and specific control/result files, not project names or marketing descriptions. Exact revisions, licenses, hashes, source ranges and diagnostic findings are retained in the community evidence reports.[^doomfly][^fly64][^flyai][^flydoom][^flychess][^flycoin][^thefly][^doomscroll][^rojas][^snedea][^tutorial][^index]

Doomfly deserves a more precise assessment than “a weak dopamine rule.” Its current implementation has anatomical KC/MBON/DAN selectors, filtered rate states, two memory variables, explicit reinforcement history, delayed-event state and atomic identity/hash-guarded checkpoints. It restores neural memory into a **new game arena**, a different contract from this model's complete coupled-body continuation. Its source can inform missing checks without replacing the current working M6 implementation.[^doomfly]

Its 4,184 selected plastic pair edges include **all KC classes→MBON11**, not just the program's 1,585 gamma-KC pairs. Aggregate PPL101→MBON contact fractions are not a map of compartment-eligible plastic contacts. Use the program's exact synapse-ROI data to decide eligibility. The author's “shuffled” survival condition shifts reinforcement timing; it does not rewire the connectome. In its small retained pilot, plastic memory did not improve survival, while erasure restored the frozen trace. That is useful causal bookkeeping with a negative outcome.[^doomflyresults]

The original Huang/Luo paper and model are the better physiological reference. They use interacting gamma1/alpha2/alpha3 modules, effective fitted connections and specific conditioning/interval assumptions. The supplement distinguishes KC and DAN trace amplitudes/rates; Doomfly adds equal one-second traces, zero KC baseline, relative efficacy bounds and other adaptations. Its implementation is therefore not the original validated recurrence transferred unchanged to MaleCNS.[^huang][^huangcode]

The recovered publisher workbook independently yields **20.09 ± 4.301930 Hz** for PPL1-γ1pedc and **37.16625 ± 9.060136 Hz** for MBON-γ1pedc, sample SD, 20 observations each. The original preparations use female flies, 3–8 days at surgery, with 1 kHz voltage imaging. These measurements constrain a reference assay; they do not identify a unique tonic input current. A different 35.2 Hz baseline belongs to the paper's fitted recurrence dataset and should not be silently combined with these measurements.[^huangdata]

Other persistence claims are materially weaker. Rojas saves a weight vector without complete neural/body/RNG state or stable edge-identity checks. Flycoin saves gains but resets fast neural state each control window; its PAM/PPL1 compartment code indexes MBON→DAN where it claims DAN→MBON. Doomscroller's live decision is dominated by an external visual prediction-error quantity, while its depression update is not dopamine-gated. These are source-level reasons to separate stored weight change from restored physiological learning.[^rojas][^flycoin][^doomscroll]

The most reusable game-project contribution is diagnostic discipline: blank-input controls, identical component/full-loop configuration, replaying matched stimuli into perturbed graphs, isolating the actual downstream pathway, and erasing only acquired state. “Shuffled anatomy,” “shuffled reinforcement” and “frozen learning” are different interventions. Existing local checks should be extended only where a concrete missing control is identified.[^flydoom][^flychess][^doomflyresults]

The tutorial also exposes source routes for visual-system transcriptomics, Frechter lateral-horn responses and DoOR. Its two transcriptomic and two physiological CSV paths returned 404 at the documented public bucket; the older bucket returned 401. These remain exact missing source objects, not recovered physiology. DoOR's primary receptor/glomerulus records are useful, while a demo's response clipping, mixture rule or arbitrary Hz rescaling is not chemical transduction.[^tutorial][^door]

No external demo, game, wallet integration or unknown application was executed during this review.

## Reuse decisions for M0–M12

| Milestone | Concrete reuse action | What remains open |
|---|---|---|
| M0 | Preserve source revisions, original data hashes, candidate identity lists and failed studies from this review | Source availability is not acceptance; keep expanded organ/repertoire inventory |
| M1 | Adjudicate BANC neck cases; add ENXXX226 to the effector audit; use FANC hair/bristle tables and existing motor atlas | Exact peripheral side/subtarget and cross-specimen correspondence; spiracle/serial-leg source discrepancies |
| M2 | Keep already-imported FlyGym/FlyMimic geometry; pursue original middle/hind XNH and respiratory mechanics | Independent NMJ/muscle force, complete hinge/folding, internal-organ physics and calibration |
| M3 | Reproduce clean Or59b–acetone references; extract exact-acetate studies; evaluate R1–R6 phototransduction; recover hair/bristle physical maps | All required sensory identities, physical units, tuning, spectrum and organ feedback |
| M4 | Use Shiu/FlyVis comparisons, original transduction studies, exact curated transmitter/peptide source candidates and bounded newer neural data | Cell-specific signs/receptors/kinetics, gap junctions, modulation and independent full-CNS physiology |
| M5 | Reuse original locomotion/grooming/flight datasets as separately specified comparisons; use matched-input perturbation controls | Every required physical repertoire item needs a fixed model, qualified mechanisms and held-out result |
| M6 | Compare useful external state manifests/fault controls against the existing working checkpoint contract | Any newly imported sensory/plastic state must be added and tested; do not replace verified persistence without a demonstrated gap |
| M7 | Start from original experimentally constrained plasticity equations/data, with exact compartment-eligible contacts | Physiological fit/holdout separation, integrated acquired advantage, retention, reversal and transfer |
| M8 | Treat learned-controller models as explicitly separate comparison hypotheses where useful | A learned self-prediction/uncertainty mechanism inside the persistent model and causal held-out benefit |
| M9 | Retain measured adult graph as control; keep any engineered growth IDs/rules separate | No reviewed package closes truthful structural changes, retained memories and adaptive-benefit controls |
| M10 | Reuse only applicable lineage/isolation bookkeeping after measuring the actual lifetime evaluator | Heritable within-life learnability improvement under fixed interfaces and independent evolutionary controls |
| M11 | Use two-instance demos only as I/O examples, with no inherited semantic or decoder credit | Learned causal communication, compositional/partner transfer and culture through permitted interactions |
| M12 | Reconstruct accepted studies from exact source/data/configuration identities | No full closure until every required physical and adaptive acceptance result exists |

The shortest justified next steps are **source-backed reference assays and exact anatomical adjudications**, not another whole-simulator integration. Several required measurements remain external dependencies. Where public source routes fail, the retained records name the file, table, identity ambiguity or assay that is missing; they do not replace that datum with a behavior-producing guess.

## Evidence package and limits

This review performed original-text/source inspection, file hashing, workbook/HDF5/CSV parsing, annotation joins, source-path checks and model-asset counts. It did **not** reproduce an upstream neural simulation, train a controller, validate the current coupled physics, change the runtime or alter an individual. Reported upstream behavioral results remain the authors' results unless an explicit independent recalculation is noted.

Detailed evidence is retained under `outputs/program/publication-review/`: original simulator notes, anatomy candidates, sensory source/data records, community implementation audits, social-source observations, repository revisions and the inspected catalogue. The source inventory (original artifact `program/publication-review/source-inventory.json`) and reuse matrix (original artifact `program/publication-review/reuse-matrix.md`) summarize inspection and adoption boundaries. Raw labels and failed access attempts remain visible. The package index (original artifact `program/publication-review/README.md`) links exact reusable files and all detailed reports.

Source terms differ: Shiu/FlyVis are MIT; FlyGym/FlyBody/FlyMimic source is Apache-2.0; Eon's derivative code is GPL with MIT portions; OlfTrans/VisTrans are BSD-3-Clause; the Juusola photoreceptor source has GNU GPL v3 in `LICENCE.txt`; several anatomical/physiological datasets have separate terms. A paper's open-access license is not automatically a license for every code or data artifact. Missing implementation-license files and inaccessible dataset routes are recorded individually in the source inventories.

Two catalogue corrections matter: Lappalainen's FlyVis paper is **10.1038/s41586-024-07939-3**, and **10.1038/s41586-025-09029-4 is the FlyBody paper**, not Eon's embodiment. Source-post repetition, a community index and a working animation do not provide additional independent validation.

## Sources

[^eon]: Eon Systems. [How the Eon Team Produced a Virtual Embodied Fly](https://eon.systems/updates/embodied-brain-emulation). 10 March 2026. Official methods and limitations; not a peer-reviewed embodiment paper.
[^eoncode]: Eon Systems. [fly-brain, revision a3db62f](https://github.com/eonsystemspbc/fly-brain/tree/a3db62f9436074e485c0278290c2164ed6150808). 29 August 2026. README, entry point, neural runners and comparison utilities.
[^flygymcode]: NeLy-EPFL. [FlyGym, revision 38c8ec6](https://github.com/NeLy-EPFL/flygym/tree/38c8ec61034cd59bc5ba0de20688d4a3c0000d60). 28 June 2026. Body/assets, CPG and hybrid-controller source, muscle tutorial; exact local revision/XML comparison.
[^sphinx]: Brunton/Tuthill collaborators. [The digital sphinx: Can a worm brain control a fly body?](https://elifesciences.org/reviewed-preprints/111516). eLife reviewed preprint v1, 17 August 2026; DOI 10.7554/eLife.111516.1.
[^sphinxcode]: Brunton Lab. [DigitalSphinx2026, revision fd40f45](https://github.com/Brunton-Lab/DigitalSphinx2026/tree/fd40f4540fac19fee9477a88d384d3a553e83c9a). 22 May 2026. Recurrent state wrapper, sensory projection, policy and configurations.
[^shiu]: Shiu PK et al. [A Drosophila computational brain model reveals sensorimotor processing](https://doi.org/10.1038/s41586-024-07763-9). Nature 634, 210–219, 2 October 2024. Original Methods and experimental comparisons.
[^shiucode]: Shiu PK, Spiller N. [Drosophila_brain_model, revision 91bdd1e](https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960). 14 September 2024. `model.py`, notebooks, data-version instructions and MIT license.
[^shiusupp]: Shiu et al. [Original supplementary tables](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07763-9/MediaObjects/41586_2024_7763_MOESM2_ESM.xlsx). Workbook retrieved, hashed and inventoried.
[^shiudata]: Shiu et al. [Model source and simulation data archive](https://doi.org/10.17617/3.CZODIW). Edmond version 3, 20 September 2023; current `edmond.mpg.de` API metadata inspected.
[^nmf]: Lobato-Rios V et al. [NeuroMechFly, a neuromechanical model of adult Drosophila melanogaster](https://doi.org/10.1038/s41592-022-01466-7). Nature Methods 19, 620–627, 2022. Original Methods and supplement.
[^nmf2]: Wang-Chen et al. [NeuroMechFly v2: simulating embodied sensorimotor control in adult Drosophila](https://doi.org/10.1038/s41592-024-02497-y). Nature Methods 21, 2353–2362, 2024.
[^nmf2supp]: Wang-Chen et al. [Original supplementary information](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41592-024-02497-y/MediaObjects/41592_2024_2497_MOESM1_ESM.pdf). Notes 1 and 10 and controller/sensory methods.
[^flygymlegacy]: NeLy-EPFL. [FlyGym Gymnasium publication-era API, revision d285260](https://github.com/NeLy-EPFL/flygym-gymnasium/tree/d285260a1c8a7b3494150cd1590f2c9fe4b5e06b). 1 April 2026. Realistic visual wrapper and closed-loop fly-following code.
[^flybody]: Vaxenburg R et al. [Whole-body physics simulation of fruit fly locomotion](https://doi.org/10.1038/s41586-025-09029-4). Nature 643, 1312–1320, 2025.
[^flybodysupp]: Vaxenburg et al. [Original supplementary information](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-025-09029-4/MediaObjects/41586_2025_9029_MOESM1_ESM.pdf). Actuator/sensor tables and mechanics/control methods.
[^flybodycode]: Turaga Lab. [flybody, revision d015e9b](https://github.com/TuragaLab/flybody/tree/d015e9bfe441bd90ae431bac24c55cb74bdbce26). 30 July 2025. Body, fluid, agent and pattern-generator implementations.
[^flybodydata]: Vaxenburg et al. [MuJoCo fruit-fly body model datasets](https://doi.org/10.25378/janelia.25309105). Figshare version 4, seven-file catalog and separate data terms inspected.
[^flymimic]: Özdil G et al. [Musculoskeletal simulation of limb movement biomechanics in Drosophila melanogaster](https://arxiv.org/html/2509.06426v2). Original manuscript v2, methods and Appendix A.1/A.4; repository cites ICLR 2026.
[^flymimiccode]: Özdil G et al. [FlyMimic, revision 9ea1131](https://github.com/gizemozd/FlyMimic/tree/9ea1131626cd76f7203b74076ef8f0e9cab30bef). 27 March 2026. OpenSim/MuJoCo assets, PPO training and mocap task.
[^grooming]: Özdil G et al. [Centralized brain networks controlling antennal grooming coordination](https://doi.org/10.1038/s41467-026-72152-x). Nature Communications 17, 5617, 2026.
[^groomingcode]: NeLy-EPFL. [Antennal grooming, revision 65787ac](https://github.com/NeLy-EPFL/antennal-grooming/tree/65787ac7fa35aa5520addb6d3e4ac27887bbaf60); Özdil [decoder-training implementation](https://github.com/gizemozd/flyvis/blob/8d2ca41b5bbb5917b11d3e838e77e5459123dab7/grooming_scripts/grooming_network_train_MLP.py). Named neurons and jointly fitted neural/angle decoders.
[^pugliese]: Pugliese et al. [Connectome simulations identify a central pattern generator circuit for fly walking](https://www.biorxiv.org/content/10.1101/2025.09.12.675944v2). Preprint v2, 30 April 2026; publication status verified through official API.
[^pugliesecode]: Pugliese et al. [Pugliese_2026, revision faee4b0](https://github.com/smpuglie/Pugliese_2026/tree/faee4b06869855ae0164cbf217fb6ec28ef3521b). 10 September 2026. Current source compared with existing exact-revision project review.
[^flyvis]: Lappalainen JK et al. [Connectome-constrained networks predict neural activity across the fly visual system](https://doi.org/10.1038/s41586-024-07939-3). Nature 634, 1132–1140, 2024.
[^flyviscode]: Turaga Lab. [FlyVis, revision 92b3845](https://github.com/TuragaLab/flyvis/tree/92b3845cc426dd309a1a0e1b3890156c42e14021). 18 August 2026. Consensus connectome, dynamics, stimulus and pretrained-model download code.
[^flygm]: [Whole-Brain Connectomic Graph Model Enables Whole-Body Locomotion Control in Fruit Fly](https://arxiv.org/html/2602.17997v3). arXiv v3, 14 June 2026. Observation encoder, graph updates, decoder and training methods.
[^flygmpage]: LNS Group. [Official FlyGM project](https://lnsgroup.cc/research/FlyGM/). Code availability and project-method description inspected 12 September 2026.
[^loihi]: Wang F et al. [Neuromorphic Simulation of Drosophila Melanogaster Brain Connectome on Loihi 2](https://arxiv.org/abs/2508.16792). 22 August 2025. Neural hardware execution/comparison, not body mapping.
[^orientation]: Liew JN et al. [Connectome-Based Modelling Reveals Orientation Maps in the Drosophila Optic Lobe](https://arxiv.org/html/2609.01330v1). 1 September 2026. Methods and Appendix B; code HEAD d73b18712579c969feba625ecfd3df52f4d328f4 inspected at README level.
[^networkstructure]: Zhang X et al. [Network Structure Governs Drosophila Brain Functionality](https://arxiv.org/html/2404.17128v4). Original preprint Methods; later publication DOI 10.1016/j.fmre.2025.01.017.
[^larval]: Sun X et al. [A neuromechanical model for Drosophila larval crawling based on physical measurements](https://doi.org/10.1186/s12915-022-01336-w). BMC Biology 20, 130, 2022. Different developmental stage/body.
[^banc]: Bates AS, Phelps JS et al. [Distributed control circuits across a brain-and-cord connectome](https://doi.org/10.1038/s41586-026-10735-w). Nature, 2026. Final v888 study and data availability.
[^banctables]: Bates et al. [BANC supplementary data 2](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10735-w/MediaObjects/41586_2026_10735_MOESM4_ESM.txt), [FlyWire supplementary data 3](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10735-w/MediaObjects/41586_2026_10735_MOESM5_ESM.txt), and [MANC supplementary data 4](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10735-w/MediaObjects/41586_2026_10735_MOESM6_ESM.txt). Complete CSVs parsed; exact rows and hashes retained.
[^flywireanno]: FlyWire Consortium. [Official annotation table, revision 8587524](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/8587524c1748ce5ef2080822a2fc890fc03bf597/supplemental_files/Supplemental_file1_neuron_annotations.tsv). Exact-root neck type readback.
[^respiration]: Luo et al. [Neural control of respiration in Drosophila](https://doi.org/10.64898/2026.07.28.740380). Preprint, posted 29 July 2026; [author PDF](https://faculty.washington.edu/tuthill/docs/respiration2026.pdf).
[^respirationcode]: Luo et al. [Spiracle connectomics source, revision d30a3eb](https://github.com/camellyc/connectomics_code/tree/d30a3eb713a3683efe385241a6664a1d382d343b). MaleCNS/MANC notebooks, exact lists and grouping; checked against current official v1.0 annotations.
[^respirationdata]: Luo et al. [Respiration dataset record](https://doi.org/10.5061/dryad.zkh1893s4). Public API reports the identifier cannot currently be viewed; no physiological dataset download claimed.
[^hairplate]: Pratt et al. [Proprioceptive limit detectors contribute to sensorimotor control of the Drosophila leg](https://doi.org/10.1038/s41467-026-69333-z). Nature Communications 17, 2664, 2026.
[^hairplatecode]: Pratt et al. [Hair_Plate_Paper v1.0.0](https://github.com/Prattbuw/Hair_Plate_Paper/tree/d0b1ca45e56477ece6f442fe940d97d6fc1104eb); [original data record](https://doi.org/10.5061/dryad.fxpnvx153). CAVE table names, analysis code, data catalog and license inspected.
[^bristle]: Elabbady et al. [A central somatotopic map of the fly leg supports spatially targeted grooming](https://doi.org/10.1016/j.cub.2026.03.045). Current Biology 36, 2192–2206.e4, 2026.
[^bristlecode]: Tuthill Lab. [elabbady_bristles_2026, revision 69de9c9](https://github.com/tuthill-lab/elabbady_bristles_2026/tree/69de9c9b5043e955c9dccb4c532b1dbee725136d). Annotation JSON, mapping landmarks and connectivity-analysis notebooks.
[^fanc]: Azevedo AW et al. [Connectomic reconstruction of a female Drosophila ventral nerve cord](https://doi.org/10.1038/s41586-024-07389-x). Nature 631, 360–368, 2024; [motor anatomical appendix](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf).
[^manc]: Cheong HSJ et al. [MANC motor identification](https://doi.org/10.7554/eLife.96084.3), especially supplementary files 3 and 6; Marin et al., [systematic MANC annotations](https://elifesciences.org/reviewed-preprints/97766v1).
[^esrf]: Ispizua J et al. [Reconstruction of the neuromusculature of Drosophila legs, ESRF User Meeting abstract booklet](https://www.esrf.fr/files/live/sites/www/files/events/conferences/2026/User%20Meeting%202026/UM2026_E-booklet.pdf). 2026; [4 February programme](https://www.esrf.fr/files/live/sites/www/files/events/conferences/2026/UDM3/UDM3%20programme%202026.pdf).
[^flybrainlab]: Lazar AA, Liu T, Turkcan MK, Zhou Y. [Accelerating with FlyBrainLab the discovery of the functional logic of the Drosophila brain in the connectomic and synaptomic era](https://doi.org/10.7554/eLife.62362). eLife, 2021. Circuit libraries and their scope.
[^olftranspaper]: Lazar AA, Yeh CH. [A molecular odorant transduction model and the complexity of spatio-temporal encoding in the Drosophila antenna](https://doi.org/10.1371/journal.pcbi.1007751). PLOS Computational Biology, 2020. Original fitted parameters and comparisons.
[^olftranscode]: FlyBrainLab. [OlfTrans, revision 3f873ea](https://github.com/FlyBrainLab/OlfTrans/tree/3f873eafba3a21b8fcb27231b49835df1d3cbc0c); [EOScircuits, revision 2ade33d](https://github.com/FlyBrainLab/EOScircuits/tree/2ade33db402997f5001f1707f136370c660dce33). CPU/NeuroDriver/antenna parameter differences inspected.
[^olfdata]: FFBO. [In vivo Antenna Electrophysiology Recordings, alpha v0.1](http://amacrine.ee.columbia.edu:15000/), [HDF5](http://amacrine.ee.columbia.edu:15000/data.h5), [README and data terms](http://amacrine.ee.columbia.edu:15000/README.txt). Exact bytes and all 418 dataset metadata records retained.
[^taskodor]: Task D et al. [Chemoreceptor co-expression in Drosophila melanogaster olfactory neurons](https://doi.org/10.7554/eLife.72599). eLife, 2022, Table 3. Receptor/glomerulus correspondence.
[^martelli]: Martelli C, Fiala A. [Slow presynaptic mechanisms that mediate adaptation in the olfactory pathway of Drosophila](https://doi.org/10.7554/eLife.43735). eLife, 2019, final version 3, Figure 3 (10.7554/eLife.43735.006). Exact methyl-acetate/Or59b protocol inspected; original numeric trials remain unavailable.
[^gorur]: Gorur-Shandilya S et al. [Olfactory receptor neurons use gain control and complementary kinetics to encode intermittent odorant stimuli](https://doi.org/10.7554/eLife.27670). eLife, 2017. Ethyl-acetate/ab3A adaptation source route.
[^song]: Song Z et al. [Stochastic, adaptive sampling of information by microvilli in fly photoreceptors](https://doi.org/10.1016/j.cub.2012.05.047). Current Biology, 2012, original article and supplementary model/experimental parameters.
[^retinarfc]: Lazar AA, Ukani NH, Zhou Y. [A Parallel Processing Model of the Drosophila Retina, Neurokernel RFC 3](https://neurokernel.github.io/rfc/nk-rfc3.pdf). 2015. Generic optical geometry and simulation architecture.
[^vistranscode]: FlyBrainLab. [VisTrans, revision ba09677](https://github.com/FlyBrainLab/VisTrans/tree/ba096778d4bd895a0e0fab02b9c519c5941bc82b); Neurokernel [retina, revision fdab351](https://github.com/neurokernel/retina/tree/fdab351e6c5530c8f051193158856ba6ef11d715). R1–R6 components, templates and source licenses.
[^desktop]: DenisSergeevitch. [desktop-fly, revision 32b0001](https://github.com/DenisSergeevitch/desktop-fly/tree/32b00011e83c3dc85fa3ea0b3934155b04f1635d). 5 September 2026. Source ETL, shipped graph/path report, exact annotation and local motor-map overlap.
[^desktopmechanics]: DenisSergeevitch. [Locomotor.swift](https://github.com/DenisSergeevitch/desktop-fly/blob/32b00011e83c3dc85fa3ea0b3934155b04f1635d/Locomotor.swift), [LegDynamics.swift](https://github.com/DenisSergeevitch/desktop-fly/blob/32b00011e83c3dc85fa3ea0b3934155b04f1635d/LegDynamics.swift). Actual pooled sensory/rate-to-body mapping and tuning comments.
[^flygame]: stanbot8. [flygame, revision a09221d](https://github.com/stanbot8/flygame/tree/a09221de3a44290e0d98dc6da57566ebce12687e). 18 March 2026. Brain initialization, main-loop ordering, CPG, checkpoint and wing source audited.
[^flyloop]: 4R7I5T. [flyloop, revision a033ba6](https://github.com/4R7I5T/flyloop/tree/a033ba6c94bb0461cc3b5a8d20fd9834247b6642). 10 September 2026. Graph builder, sensory/behavior decoder, worker and body animation source.
[^social]: Original author posts: [Slava pong](https://x.com/slvDev/status/2098531088196911175), [Sudoku](https://x.com/smjain/status/2098596658913407380), [tycoon](https://x.com/oguzthedev/status/2098454610998333574), [MindFly](https://x.com/VicVRad/status/2098451315969888636), [sound conditioning](https://x.com/shmulc8/status/2098424905037467809), [football](https://x.com/NotWhoYouDream/status/2098528126976262205), [FlyOut](https://x.com/93bitmap/status/2098577395393647043). September 2026. Original posts/relevant author replies read; detailed per-post limitations retained in `social-demo-sources.md`.
[^flywireoriginal]: Dorkenwald S et al. [Neuronal wiring diagram of an adult brain](https://doi.org/10.1038/s41586-024-07558-y). Nature 634, 124–138, 2024. Adult female brain scope.
[^malecns]: Berg S et al. [Sexual dimorphism in the complete Drosophila male central nervous system connectome](https://doi.org/10.1016/j.cell.2026.08.015). Cell 189, 5504–5526.e15, 3 September 2026. Published full text/STAR Methods read through browser; exact-source note retained.
[^doomfly]: nftechie. [doomfly, revision 71ecf53](https://github.com/nftechie/doomfly/tree/71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33). 9 September 2026. Circuit selector, v6 rule/brain state, checkpoint manager and continuation-test source.
[^doomflyresults]: nftechie. [Doomfly v6 survival analysis](https://github.com/nftechie/doomfly/blob/71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33/outputs/doom-learning/physiology-v6/survival-pilot/analysis.json) and [circuit record](https://github.com/nftechie/doomfly/blob/71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33/outputs/doom-learning/physiology-v6/survival-pilot/circuit.json). Author results inspected, not independently rerun.
[^fly64]: ornata. [Fly64, revision f2f4114](https://github.com/ornata/fly/tree/f2f4114e53eaa326e54129f27a5383f93c6957af). Source/technical notes, optical mapping, model, decoder and replay controls.
[^flyai]: alextitonis. [fly.ai, revision 088d06b](https://github.com/alextitonis/fly.ai/tree/088d06b428aa78f9990f21a6cfa716c70390dd8e). Source feature injection, named-neuron perturbations, fixed decoder and reservoir readout.
[^flydoom]: mutkuoz. [flydoom, revision dffc37f](https://github.com/mutkuoz/flydoom/tree/dffc37fc48f7736d6614f5bc240694971900c824). 7 September 2026. Actual model/frontends/decoder, manuscript and retained negative-result/control records.
[^flychess]: martialsystems. [fly_chess, revision 831106b](https://github.com/martialsystems/fly_chess/tree/831106b744c3c8103d41703cb941ec1764edc942). 10 September 2026. 475-cell circuit assay, sign-stratified rewiring, distinct synthetic chess head and author results.
[^flycoin]: fruitflydev. [flycoinrh, revision 8748e5b](https://github.com/fruitflydev/flycoinrh/tree/8748e5bd30794d14afeb3441904221b52a002cac). Source graph orientation, `mushroom.py` selector/update/persistence, `flysim.py` reset and actual `roam.py` calls. No transactional code executed.
[^thefly]: theflyRH. [thefly-brain, revision 4e9f472](https://github.com/theflyRH/thefly-brain/tree/4e9f4722c337e7d85cee3072ddb78bfa99234ca8). 10 September 2026. Fixed neural assay and trial/rewiring implementation; no external financial actions inspected as capability evidence.
[^doomscroll]: ranagwho. [Fruitfly-Doomscroller, revision b03ba91](https://github.com/ranagwho/Fruitfly-Doomscroller/tree/b03ba91d89ce16f3cb7e974b2d10a917b1fc7cac). 10 September 2026. Actual session novelty path, depression update and decision/persistence boundaries.
[^rojas]: erojasoficial-byte. [fly-brain, revision 27cec28](https://github.com/erojasoficial-byte/fly-brain/tree/27cec28d5d202eb004683fb4c1a1033eec8deea0). 21 March 2026. Brain/body bridge, generic Hebbian update, weight-only save and two-fly comparison/recovery code. `rndlabsoy/fly-brain-full` resolves to the same inspected commit.
[^snedea]: snedea. [flybrain, revision 9191824](https://github.com/snedea/flybrain/tree/9191824d17871b7851645782d53d23f213ddb938). Metadata, synthesized motor outputs, behavioral state machine and explicit food steering.
[^tutorial]: SJCABS. [fly_connectome_data_tutorial, revision 85c6624](https://github.com/sjcabs/fly_connectome_data_tutorial/tree/85c66244cfb2c02b2442905c4428b42a0d8e6656). Versioned loaders and notebooks 05–07. Exact public data-route failures retained.
[^index]: watthem. [awesome-fruit-fly-connectome, revision a07fb02](https://github.com/watthem/awesome-fruit-fly-connectome/tree/a07fb0280015821feccc7af2e043f806406f89bc). Discovery index, inspected 12 September 2026; substantive DOI attribution error identified.
[^huang]: Huang C, Luo J et al. [Dopamine-mediated interactions between short- and long-term memory dynamics](https://doi.org/10.1038/s41586-024-07819-w). Nature, 2024. Original article and computational supplementary appendix retrieved.
[^huangcode]: Schnitzer Lab. [Luo_Huang_2024_MB_model, revision 5d7c08a](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model/tree/5d7c08a9a88f923169a0c3008aca68af421e9a7f). 2 June 2024. MATLAB recurrence, `Imaging_24hr_data.xlsx`, fitted `.mat` parameter sets and GPL-3.0-or-later notice.
[^huangdata]: Huang/Luo et al. [Publisher supplementary archive](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11525173/supplementaryFiles), Source Data Fig. 1, `Panel d!B3:B22` and `Panel e!B3:B22`. Forty observations independently extracted; bytes, hashes and recomputed sample statistics retained in `huang-luo-sources/` and the community-learning receipt.
[^door]: Münch D, Galizia CG. [DoOR 2.0—Comprehensive Mapping of Drosophila melanogaster Odorant Responses](https://doi.org/10.1038/srep21841). Scientific Reports, 2016; [primary DoOR.data repository](https://github.com/ropensci/DoOR.data). Response/class-join resource; not a complete physiological encoder.
[^groundtruth]: Bates AS, Jefferis GSXE, Adjavon DY, Funke J and collaborators. [drosophila_neurotransmitters, revision a941741](https://github.com/flyconnectome/drosophila_neurotransmitters/tree/a9417412c8a70fcc9f80a65ca5bc6064eba07be3), 23 June 2026, and [drosophila_neuropeptides, revision 7a1416a](https://github.com/flyconnectome/drosophila_neuropeptides/tree/7a1416a5e244d415e8cabdd3172592dab7d65dc2), 3 September 2026. Exact source/type-match audit and all input hashes retained in `transmitter-ground-truth/`; no physiological assignment made.

# Scientific coherence review of the fruit-fly program

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the , and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

This review concerns the earlier FlyWire/MN9 demonstration and the experimental design needed to replace its imposed motion with a mechanistic force chain. It is not a description of the later whole-MaleCNS runtime. The synthetic prototype had a recorded engineering pass, while its biological G1–G6 gates remained open.

**Evidence labels:** **Verified** means directly inspected source or a saved result, not biological validation. **Inference** is a conclusion from that evidence. **Proposed** means a correction or future experiment. **Estimated** parameters remain estimated even when a simulation using them passes its software checks. **P1** findings can invalidate the next experiment or violate the current requirement; **P2** findings must be resolved before the affected later claim or reproducibility gate.

## What is established, and what should be retained

The current arena is an approximate Eon LIF connectome with odor, mouth-contact taste, and antennal warmth inputs. P9/DNa02 activity feeds an engineered walking controller; MN9 feeds an engineered position actuator. It is not a validated reconstruction of natural behavior. This assessment is supported by the historical README, worker:95–137 (historical source `live.py`), and [body](../../runtime/body.py).

Several central distinctions are already correct and should survive revision:

- The executive plan separates electrical activity, synaptic efficacy, contact remodeling, and new neurons; it distinguishes engineered growth from adult biological neurogenesis.
- It separates physiological fidelity from adaptive capability and rejects neuron count or task success as proof of consciousness. Its self-model and uncertainty tests already include simpler alternatives.
- The companion separates genotype from acquired memory, genetic from cultural generations, assumed calendar years from actual computation, and communication from human-language equivalence.
- The README explicitly treats lack of approach as a model outcome and discloses the preset leg controller and unknown motor calibration. the historical README, [related discussion](../../README.md)

The problem is principally how these safeguards become ordered, enforceable experiment gates.

## Prioritized findings

### R1 — Establish a causal motor reference before interpreting learned behavior

A fixed controller can obscure whether a circuit or its readout generates movement. The dependency is a verified motor-event-to-force reference, identified physical feedback, and complete persistent state. Isolated plasticity physiology can be studied independently; a learned behavioral claim additionally needs a supported sensory/consequence/motor path.

### R2 — P1: a fixed neural decoder can still impose the behavior absent from the circuit

**Evidence — verified.** The executive accepts action selection through a fixed documented motor interface and proposes keeping it fixed during learning. The actual interface includes `PreprogrammedSteps`, hybrid body-feedback control, and MN9 rate divided by an 80 Hz gain to choose a fraction of a preset angle. [body](../../runtime/body.py); worker:124–137 (historical source `live.py`).

**Consequence — inference.** Decoder invariance rules out changing the decoder between trials; it does not establish that neural circuits generate the movement. A model could pass a learning or body-prediction test by modulating or predicting the preprogrammed controller. Likewise, a new muscle implementation could reproduce the old angles simply by fitting its force scale to those imposed targets. Neither would establish the requested motor mechanism.

**Correction — proposed.** Define the admissible motor path explicitly: timestamped identified motor-neuron spikes → declared neuromuscular transmission → muscle activation → active/passive force → anatomical transmission and physical motion. Estimated physical parameters are permitted with units, provenance, uncertainty, and independent calibration. The scientific mode must exclude preset gait trajectories, target-angle servos, default walking drive, and stimulus/reward-dependent motor gains. The legacy controller may remain an explicitly identified comparison, never evidence for natural motor generation. An isolated replay intervention may test muscle mechanics; it must not be presented as spontaneous or sensory-evoked behavior.

**Gate — proposed.** Holding motor spikes, initial peripheral state, and physical conditions fixed must hold the downstream force trajectory fixed when only source labels or evaluation targets change. Blocking modeled transmission must remove the associated neural contribution to activation/force. Passive motion and other muscles need not disappear. Freeze the muscle model before sensory tests; do not use the old approximately 60°/3° angles as fitting targets. This agrees with the existing warning in [MN9 baseline](mn9-current-baseline.md).

### R3 — P1: equal integration steps do not establish causal neural–muscle timing

**Evidence — verified.** The README says brain and physics use matching 0.1 ms steps with 10 ms exchanges. The worker samples sensory state once, runs all 100 neural steps, aggregates spikes, smooths MN9 over 50 ms, then runs all 100 body steps using the resulting command. The executive requires preserving within-chunk spike timing for plasticity but does not give the equivalent neuromuscular/sensory coupling contract. the historical README; worker:94–137 (historical source `live.py`).

**Consequence — inference.** This is a block-coupled approximation. An aggregate containing late neural events is applied over an entire body block; contact changes inside that block cannot affect its neural inputs. Matching step sizes alone does not demonstrate correct transmission latency, twitch summation, or feedback timing. No quantitative error bound for this coupling was found.

**Correction and gate — proposed.** Specify event timestamps, update order, and any deliberate delays before connecting the muscle model. Preserve individual MN9 events through transmission/activation, and advance mechanics and feedback with a causal schedule. Rendering can remain batched. Compare identical spike replay under different packet/display chunking and reduce the neural–physical coupling interval separately from the integrator step. Accept only if the relevant latency, force, and motion conclusions converge within declared tolerances. Reuse the existing event export, which correctly labels its traces as simulated rather than biological. [Capture](../../runtime/capture_mn9.py)

### R4 — P1: the proposed odor-choice/reversal task lacks independently specified cue and consequence interfaces

**Evidence — verified.** The executive proposes odor-guided food choice and reversal, and the companion builds its first evolutionary task on that environment. Currently every source contributes a scalar to the same odor field; left/right rates drive the same fixed ORN populations. Changing sweet to bitter does not change odor identity. Taste is a contact-gated 200 Hz input; the inspected arena/worker contains no food consumption, nutrient state, or food-to-reinforcement implementation. [arena](../../runtime/arena.py); worker:30–40, 95–107 (historical source `live.py`).

**Consequence — inference.** At matched geometry and odor strength, swapping two sources' identities gives the same distal odor input. A claimed odor-identity reversal could instead measure place learning, intensity discrimination, or immediate taste response. Proboscis motion/contact also cannot stand in for ingestion, satiety, or a delayed reinforcement signal without specifying those additional links. Failure of this task would not isolate failure of plasticity.

**Correction and gate — proposed.** Before learning, define exactly what distinguishes the two cues in the neural input and demonstrate that distinction at matched intensity. Use independently justified receptor patterns for an odor claim; otherwise call them artificial neural cues. Specify whether the consequence is scheduled experimental reinforcement, sensory contact, or modeled ingestion, with its timing and neural route. Do not award proximity-to-food or desired-motion feedback to make navigation work. Keep source identity and correct answers outside the neural input. Verify cue access, outcome access, and an admissible motor response separately before interpreting acquisition/reversal. A restrained cue-response assay is a possible first learning experiment after the MN9 work; it is not a shortcut to a validated foraging task.

### R5 — P1: the selected γ1 plasticity assay does not by itself bridge to appetitive teaching

**Evidence — verified.** The executive selects the γ1 circuit while its main acceptance scenario is a taught cue–food association. Hige et al.'s cited primary study concerns aversive olfactory learning, with compartment-specific dopamine pairing and synaptic depression. This makes it a relevant physiological reference, not a demonstrated food-reward-to-motor chain for this simulator. [Hige et al. 2015, abstract and Figures 1, 5–7](https://pubmed.ncbi.nlm.nih.gov/26637800/).

**Consequence — inference.** Reproducing γ1 depression would not establish that food drives the right modulatory compartment or that the resulting change affects the chosen motor output. Inferring a reward sign from “dopamine” or changing readout signs until attraction appears would bypass the biological question. The plan already cautions against universal reward scalars, but its phase transition leaves this bridge unspecified.

**Correction — proposed.** Retain γ1 as a separately scored plasticity reference, studied later or in parallel as component research. Before an appetitive claim, name the outcome-sensitive cells, relevant modulatory pathway/compartment, plastic synapses, and downstream route to the selected action; preserve missing links explicitly. Either reproduce the selected preparation's actual conditioning protocol or choose a separately supported appetitive preparation. Do not force the aversive reference to yield food approach. A synthetic reinforcement experiment remains permissible only as an explicitly engineered learning hypothesis, with no natural-food-behavior claim.

### R6 — P1: temperature reactivity has no top-level causal scope or success gate

**Evidence — verified.** Temperature appears in parameter metadata and chemistry notation, but not as an explicit execution-phase outcome. The README correctly says current warmth is antennal and separate from nociception. The code exposes 22–45°C source settings, an approximate static field, and a memoryless warmth-rate mapping; it does not alter neural/NMJ/muscle kinetics with tissue temperature. The saved probe records MN9 counts of 48 at a 22°C source and 43 at a 45°C source, without establishing a physiological explanation. the historical README; [arena](../../runtime/arena.py); temperature probe:3–35 (original artifact `temperature-feeding-probe.json`).

**Consequence — inference.** “Reacts to temperature” can otherwise mean a receptor emits spikes, the central network changes activity, muscle physics changes, feeding changes, or injury occurs. These are different hypotheses. An antennal warmth experiment cannot validate local food-temperature sensing, and a change in muscle force need not be a neural feeding decision. A warm food source failing to suppress feeding is not grounds to add a rejection rule.

**Correction and gate — proposed.** Add a temperature stage after the frozen MN9 motor model, with independently named exposure sites and separate sensory, central, and peripheral effects. Compare sensory temperature changes at fixed motor parameters with identical MN9 replay under independently varied peripheral temperature. Initially leave uncalibrated peripheral temperature effects explicitly absent; any proposed temperature coefficient is an estimate. Declare both the tested temperature/time range and outcomes outside it. No requirement for hot-food withdrawal, attraction, avoidance, burn, or pain belongs in the acceptance gate without the corresponding evidence and pathway. Adopt the already written component and site-isolation proposals in [thermal review](mn9-validation-temperature.md) and [related discussion](mn9-validation-temperature.md), at the stated preparation and evidence level.

### R7 — P1: acceptance principles need claim-specific stopping rules, rather than promotion by a convincing movie

**Evidence — verified.** The executive has a strong comparison table and says to set tolerances from measurements, but the raw data package has not been assembled and its gates remain principles. The README reports single-seed implementation receipts; the arena check requires a zero-spike fixture and a preset sweet/bitter angle difference. The MN9 replay traces are generated by the same approximate brain model. the historical README; [check_arena](../../tests/check_arena.py); [Capture](../../runtime/capture_mn9.py).

**Consequence — inference.** Passing a software fixture is not an independent observation of biology. Matching a final angle does not identify release, activation, force, moment arm, or passive resistance separately. Conversely, preserving the old angle threshold or universal silence requirement can reject a more defensible physical model for the wrong reason. Simulation seeds measure stochastic variation in that model, not between-animal variation.

**Correction — proposed.** For the next milestone, make one compact experiment record containing: the claim; preparation and units; measured versus estimated parameters; calibration observations; untouched holdout protocols; primary readouts; interventions and nuisance controls; numerical convergence criteria; replication unit; and pass/fail/inconclusive rules. Obtain or identify the comparison data before declaring a biological validation gate executable. If data cannot discriminate parameterizations, report an estimated force-model prototype and the missing measurement; do not require unavailable measurements before any useful prototype can exist.

**Minimum decision rules — proposed.**

- A block/replay/force-accounting check can pass implementation even when biological fidelity is untested. A copied model-generated spike train is an integration input, never independent physiological validation.
- Calibrate transmission/activation/mechanics independently where possible, then predict held-out loads, starting poses, pulse histories, and interventions without fitting target behavior. An endpoint-only fit supports only that endpoint prediction.
- Separate deterministic regression seeds, stochastic repeats, uncertain anatomical/physical parameters, and biological replicates. Prespecify effect-size/error margins and precision requirements; do not widen them after observing failure.
- A completed experiment may reject or leave a capability hypothesis unresolved. Mark “experiment complete; hypothesis unsupported” separately from “capability demonstrated.” Do not add progressively more mechanisms until a desired behavior appears.
- Keep the silent no-input check as a named legacy fixture. A new model's baseline should follow its declared intrinsic, sensory, and passive state; lack of motor spikes does not imply absence of all passive motion.

The thermal review has already proposed a useful measured/derived/estimated/proposed vocabulary, identifiability table, and explicit inconclusive outcome. Reuse these instead of creating a separate validation framework. [Thermal review](mn9-validation-temperature.md), [related discussion](mn9-validation-temperature.md)

### R8 — Keep numerical claims attached to immutable source versions

The earlier documentation cited a protocol-3 displacement of about 4.204 mm, while its replaced result file contained protocol 4 and 4.2429157604 mm. Reused filenames had obscured the evidence version. Every scientific result should identify its source/data/configuration, stimulus history, seed and protocol; a later result must not silently replace the basis of an older claim.

### R9 — P2: evolutionary selection can optimize the experimental shortcuts unless its mutable surface and final holdout are fixed

**Evidence — verified.** The companion proposes bounded learning/developmental parameters, designed selection scores, periodic held-out evaluation, and later detailed-model reevaluation. It correctly includes ancestors, random search, mutation-without-selection, and learning-disabled controls. However, it does not explicitly exclude sensory encoders, motor gains, reward routing, or test-generation settings from the mutable genotype, or distinguish validation feedback from a final untouched test.

**Consequence — inference.** Better descendants might have a stronger innate response, easier sensory access, or more effective actuation rather than better learning. A repeatedly inspected “held-out” environment becomes part of selection if it influences candidates, objectives, or stopping decisions. Descendants from one search are also not independent evolutionary replicates. Designed optimization is a legitimate later experiment but cannot be used to fit attraction/avoidance and then claim unforced natural behavior.

**Correction and gate — proposed.** Enumerate the first genotype's mutable fields and freeze all input, motor, task, and scoring interfaces. Compare each candidate before and after learning on fresh cue assignments, including a learning-disabled counterpart; measure the acquired advantage separately from initial performance. Separate training, development/selection validation, and final unseen task sets. Record all evaluations, including failed candidates, when comparing compute with random search. Use independent evolutionary runs as the unit for claims about selection reliability. Keep this branch deferred under the current priority and never promote its selected behavior as biological validation.

### R10 — P2: communication gates need explicit learner attribution and matched channel interventions

**Evidence — verified.** The companion appropriately rejects hand-coded dictionaries and hidden language-model decisions, and separates generalization, composition, and cultural transmission. Its L0 is still a cue-association task; L1 requires a sender and receiver, but the actual neural message-production/readout/plasticity components remain unspecified. Removal/shuffling is listed without a matched nuisance-control protocol. .

**Interpretation.** The caution is warranted: Lowe et al. demonstrate that message/action correlations can exist without messages influencing the receiver. Chaabouni et al. show that generalization and compositionality need not track one another. The companion accurately reflects these limited findings; neither establishes language in a fly-derived circuit. [Lowe et al. 2019](https://www.ifaamas.org/Proceedings/aamas2019/pdfs/p693.pdf); [Chaabouni et al. 2020](https://aclanthology.org/2020.acl-main.407/).

**Correction and gate — proposed.** Mark L0 as a prerequisite association result, not an additional linguistic achievement. Before L1, specify which neurons/state choose a symbol, how received symbols enter the circuit, and which synapses learn their use; keep an externally trained decoder's contribution separate. State the structured information already supplied by the task interface. Test both sender-information dependence and receiver choice changes using replacements matched for message length, timing, and input magnitude, alongside no-channel controls. Mere removal can change neural drive or timing. Define compositional interventions before examining the learned protocol and test fresh partners/cohorts with fixed exposure budgets. These additions make the existing claims falsifiable without expanding into a human-language project.

### R11 — P2: “detailed evaluator” and “open-ended” need claim-specific definitions

**Evidence — verified.** The executive distinguishes a frozen point-neuron baseline, a selected mechanistic circuit, and spatial reference models. The companion later calls the current GPU runtime a detailed evaluator without specifying which mechanism has higher fidelity. The executive defines open-ended as no hard-coded final architecture, whereas the evolution branch discusses innovation and changing niches. .

**Consequence — inference.** Full graph size is not greater physiological fidelity for every mechanism. Two models can agree because they share the same motor or chemical assumption. Repeated neural growth demonstrates expandable software, not continuing adaptive innovation. The documents mostly recognize this distinction, but the gate labels can still overstate what was checked.

**Correction — proposed.** Name the evaluator by what it resolves: full-graph LIF context, calibrated local MN9 unit, selected chemical circuit, or spatial reference. Reduced/full-model agreement is model consistency; independent recordings/perturbations support biological fidelity. Do not treat the point-neuron GPU baseline as a gold standard for NMJ, chemistry, thermal transduction, learning, or language. Use “expandable architecture” for the engineering growth property; reserve any innovation claim for the actual finite task sequence and evaluation horizon. Retain the existing fixed-final-size, random-growth, and equal-compute/equal-experience comparisons.

## Reconciliation of the four MN9 reports

The final synthesis incorporates the four available specialist reports. Their primary-source findings are attributed below; this review independently adjudicates how those findings constrain the plan rather than repeating their searches.

| Boundary | Specialist evidence and proposed resolution |
|---|---|
| **What the first unit represents** | The anatomy review identifies the surviving root as **right MN9**, reports ipsilateral m9 innervation and head-to-rostral-apodeme attachment topology, and retains a laterality conflict in an old notebook comment. Use a unilateral rostrum assay with explicitly estimated geometry; do not mirror the neural drive into the missing side, add a direct distal actuator, or call this complete feeding. [Anatomy](mn9-anatomy.md), [related discussion](mn9-anatomy.md) |
| **Which physiology transfers** | The dynamics review reports adult CM9 electrophysiology, preparation-dependent responses, and glutamatergic evidence; it does not recover a complete measured spike-to-force function. Keep these NMJ parameters separate from the cholinergic KC→MBON pilot, and do not substitute a low-confidence brain transmitter prediction for adult NMJ evidence. Electrical amplitudes, optical pulse settings, and movement durations are not activation or force constants. [Dynamics](mn9-dynamics.md); [Anatomy](mn9-anatomy.md) |
| **Who owns activation and passive force** | The dynamics proposal evolves `a`; native MuJoCo muscle actuators also evolve activation from excitation. Choose one owner of activation, not two filters in series by accidental composition. If native activation owns `a`, supply the declared bounded excitation; if the neural/peripheral model owns `a`, use a force path that does not silently apply another activation ODE. Likewise count each passive tissue force once. The updated mechanics report resolves the current convention as mm–g–s, with spatial muscle force in μN. This unit contract is not biological calibration. [Dynamics](mn9-dynamics.md); [Mechanics](mn9-mujoco-mechanics.md), [related discussion](mn9-mujoco-mechanics.md) |
| **What remains open after movement appears** | The anatomy review adds a candidate distal sd-L feedback route, with unresolved driver specificity, exact roots, and transduction; this qualifies “no identified feedback” to “no validated exact MN9 feedback loop.” The thermal review separately requires local sensory exposures, frozen motor calibration, and independent intervention tests. Neither candidate afferents nor the synthetic mechanics proof closes the full biological chain. [Anatomy](mn9-anatomy.md); [Thermal](mn9-validation-temperature.md), [related discussion](mn9-validation-temperature.md) |

**Adjudication:** retain the completed synthetic force-chain prototype as an estimated, testable model and the starting point for further evidence. Its reported pass does not complete biological G1–G6. Retain adult physiology and anatomical constraints without inventing missing constants. MN9 → M9 is the first mechanistic milestone. MB learning remains later/parallel component research, and the persistent-model, growth, evolution, and communication goals remain intact but conditional. No report supplies grounds to restore programmed motor behavior or fit a desired attraction/avoidance outcome.

## Short implementable next sequence

These are proposed follow-on edits and experiments, not actions performed by this review.

1. **Define the claim and reference version.** Record the allowed measured/estimated physical parameters, excluded behavior-generating shortcuts and exact source/data identity before selecting an acceptance experiment.
2. **Consolidate the prototype's parameter and interface record.** Use the four completed reviews to record exact cell/side/muscle identity, geometry, units, activation ownership, and independent observations. Distinguish measured constants from estimates and unresolved values. Confirm those records against the delivered prototype without restarting its build; any uninspected prototype detail remains unverified in this review.
3. **Preserve the synthetic pass and address the remaining biological gates.** Retain the existing replay/check receipts. G1 transmission and G2 mechanics need condition-matched independent data; G3 needs held-out motor perturbations, G4 identified sensory closure, G5 site-specific thermal validation, and G6 separate nociception/injury evidence. These remain incomplete. Validate only the claimed scope, use an explicit estimated-model status where measurements are missing, and keep G6 deferred rather than making injury a prerequisite for MN9 work. No target-angle fitting or preset stepping belongs in this process.
4. **Integrate MN9, then extend named pathways.** Use the fixed sensory replay and physical scene to attribute changes to the new motor path. Add downstream motor units and identified afferents one pathway at a time; map missing VNC/peripheral links explicitly. Disable legacy gait output in the mechanistic evaluation. Full-pathway completion requires the declared chain, not an active descending neuron or a moving body.
5. **Test temperature with the motor model frozen.** Separate exposure sites, sensory transduction, central changes, and peripheral physical effects; use the thermal review's controls. Record non-response and unexpected response without changing gains to produce a preferred action. Publish only the narrow temperature claim actually tested.
6. **Integrate learning only after task feasibility is established.** Define discriminable cues, an identified or explicitly engineered reinforcement route, and an admissible observable action. The MB plasticity reference may proceed earlier in parallel, separately from the first learning test. Require retained, experience-dependent neural change before E2/L1; add growth, self-modeling, evolution, and communication only under their specific controlled hypotheses. Basic cost accounting can accompany the earlier bench without becoming a separate population project.

## Evidence interpretation

Source inspection and saved synthetic results support the design critique at the historical model version. They do not establish physiological fit, complete sensory closure or adaptive capability. Later mechanisms and package checks are assessed separately on the status page.

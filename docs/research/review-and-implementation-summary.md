# Fruit-fly research and implementation review

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

This review consolidates the early MN9 anatomy, physiology, mechanics and thermal studies. The earlier demonstration used an imposed mouth angle and preset gait machinery. The isolated event-to-force prototype tested a replacement causal chain; it did not yet establish anatomical M9 or natural behavior.

## Main findings

| Priority | Finding | Required resolution |
|---|---|---|
| P1 | The plans have competing first milestones: mushroom-body plasticity, a lifetime evaluator, and the MN9 force chain. | Use one shared order: MN9 mechanics, causal integration and identified sensory/motor pathways, site-specific temperature, then the learning-dependent branches. Isolated MB physiology research can proceed in parallel. |
| P1 | Live MN9 activity still chooses a target angle; P9/DNa02 still drive preset gait machinery. Keeping those mappings fixed does not make movement circuit-generated. | Replace the relevant actuation with motor events → transmission → activation → force. Keep source labels, desired actions, and reward scores outside that physical conversion. |
| P1 | The live worker advances 100 neural steps, aggregates them, then applies one command over 100 body steps. | Specify causal event timing and neural/body update order. Keep transport/rendering batches separate from biological integration; verify coupling convergence before interpreting delays or feedback. |
| P1 | One right MN9 is mapped; M9 attachment topology is supported, but metric geometry, peripheral kinetics, force curves, and exact afferent closure remain incomplete. | Build an explicitly estimated unilateral preparation. Record uncertainty, preserve missing IDs, and validate only observables supported by independent data. Do not invent the opposite spike train, antagonists, or a target return angle. |
| P1 | Temperature currently drives antennal warmth neurons. It does not represent labellar food temperature, muscle temperature dependence, or injury. | Treat each exposure site and pathway separately. Fit transduction to sensory evidence and observe the resulting neural/motor response; hot-food rejection is not an imposed acceptance criterion. |
| P1 for learning | Both arena objects use the same odor mixture; contact is not an implemented ingestion/reinforcement process. The selected γ1 plasticity reference does not by itself supply an appetitive learning pathway. | Before interpreting odor reversal, specify distinguishable cues, consequences, the modulatory/plastic circuit, and its route to an admissible action. Separate physiological reference reproduction from an engineered teaching task. |
| P2 | Within-session recurrence is not durable learned memory. Evolution and communication presume learning and isolated individual state that do not yet exist. | Add complete continuation and fresh-individual semantics before those experiments. Freeze sensory/motor/task interfaces when evaluating evolved learning rules. |
| P2 | Documentation is stale: executive protocol/odor claims, a removed manual-stimulation checkbox, and a backend copy recipe missing arena files. | Update the source descriptions together from current evidence when revising them. Preserve distinct historical receipts. No runtime rebuild is required merely to correct the documentation. |

These are implementation and claim priorities, not evidence of a physiological result. Full findings and source-line references are in the two plan reviews
linked below.

## What the biological research establishes

Adult MN9 innervates ipsilateral muscle 9. M9 pulls from the ventral head capsule
through a tendon onto the rostral apodeme, producing rostrum protraction. The
published workbook and current annotation identify the included FlyWire root
`720575940660219265` as **right MN9**; an old notebook comment disagrees and is
documented. The opposite legacy root is absent. Metric attachment coordinates
were not recovered from the reviewed supplementary material.
[Adult anatomy](https://elifesciences.org/articles/54978),
[identity and geometry review](mn9-anatomy.md).

Adult CM9 provides direct glutamatergic NMJ evidence, electrical amplitudes, and
condition-dependent short-term depression. It does not supply a complete
measured spike-to-force transfer function. Delays, muscle activation/relaxation,
force scale, passive loading, and force–length/velocity parameters therefore
remain estimated or unmeasured. Published cohorts, saline, age, and diet must
remain attached to measurements; they cannot be pooled into one universal
motor-neuron gain.
[Adult CM9 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/),
[dynamics review](mn9-dynamics.md).

MuJoCo supplies spatial tendon transmission and generic activation and
active/passive muscle force laws. The mechanics study verified these against the installed
3.9 binary. FlyGym's primary documentation establishes **mm–g–s**, so spatial
muscle force is **µN** and hinge torque **nN·m**. Its bundled 15-muscle asset
applies to the left foreleg, not M9. Those fitted leg parameters and its imitation
controller cannot calibrate the proboscis.
[Units](https://neuromechfly.org/tutorials/1b_advanced_model_composition/),
[mechanics review](mn9-mujoco-mechanics.md).

The thermal review identifies local labellar cooling physiology as a useful
independent test, distinct from antennal warmth. Candidate proboscis contact and
proprioceptive pathways exist, but exact sensory roots, transduction, and the
claimed closed loop still need resolution. This research does not establish a
burn or pain model.
[Labellar cooling study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7329267/),
[validation and temperature review](mn9-validation-temperature.md).

## Implemented and checked in this work

The first engineering prototype now exists:

**Per-timestep simulated MN9 events → delayed, history-dependent NMJ excitation
→ native muscle activation → length/velocity-dependent force → synthetic lever
motion.**

mn9_force_replay.py (historical source `mn9_force_replay.py`)
reuses the isolated MuJoCo mechanics probe. It receives only spike times and
physical/assay parameters; the sugar/bitter labels never enter force computation.
It uses one activation state, owned by MuJoCo, rather than accidentally filtering
activation twice. NMJ excitation and available efficacy retain spike history.

The replay uses the 48-event sugar and 6-event sugar-plus-bitter computational
traces captured from the existing Eon model. They are **not biological
recordings**. Geometry and every peripheral parameter are synthetic and unfitted.
No desired mouth angle or attraction/withdrawal score was used to choose them.

Passed checks:

- No-input and release-block controls remove the active drive in this fixture.
- A constrained joint produces reaction force despite negligible movement.
- An external opposing load changes motion; equal-count trains with different
  timing produce different activation trajectories.
- Halving the step from 0.1 to 0.05 ms changes the reported metrics by at most
  **0.00137%**. States remain finite and bounded with no numerical warnings.
- The separate mechanics check verifies native force–length/velocity/passive
  behavior, force decomposition, geometric torque, power, and sensor readback.

These demonstrate a working causal software chain. They do not validate adult
M9, absolute physiological latency, sensory closure, feeding, or locomotion.
The captured spike file uses the source's discrete output-bin labels; a live
integration still needs an explicit beginning/end-of-step convention. The bench
requires events on its integration grid and contains no network packet loop.
Its native tendon has constant length rather than series compliance. The free
lever has no damping or restoring force and can coast after activation declines.

Historical script names are `muscle_mechanics_probe.py` and `mn9_force_replay.py`. Consult the [package README](../../README.md) for supported commands and the results index for selected output artifacts.

Force replay receipt (original artifact `mn9-force-replay-check.json`),
mechanics receipt (original artifact `muscle-mechanics-check.json`),
[parameter ledger and current baseline](mn9-current-baseline.md).

Historical figure: Synthetic MN9 force replay; not biological validation (original artifact `mn9-force-replay.png`)

## Ordered next implementation

1. **Register one right M9 mechanical preparation.** Digitize head origin,
   rostral-apodeme insertion, and hinge landmarks from scale-bearing anatomy;
   retain projected/depth uncertainty. Use explicit estimates where measurements
   are absent. Choose fiber/tendon, passive, and force hypotheses independently
   of desired behavior. The deliverable is one anatomical hypothesis with a
   parameter ledger and sensitivity results, not complete feeding.
2. **Replace the MN9 servo through a causal local replay first.** Keep raw motor
   events, define timestamp and delay semantics, and let mechanics determine
   motion. Use the existing block/load/convergence checks. Biological validation
   remains limited by the available independent electrical and mechanical data.
3. **Integrate neural/body state and identified feedback.** Separate display
   batches from the coupling interval. Remove duplicate servo output for the
   tested joint. Map each afferent and physical input explicitly; leave
   unresolved proprioception open. Add complete state continuation before
   persistent-learning experiments, including pending events and muscle state.
4. **Extend the declared motor and temperature scope.** Expand proboscis units,
   then one documented VNC-to-muscle chain using explicit dataset correspondence.
   Full-body walking requires full declared circuit/muscle coverage. Add
   site-specific thermal transduction with frozen motor parameters; unexpected
   behavior is a result to investigate, not a reason to insert a response rule.
5. **Resume learning-dependent research.** Establish discriminable cues,
   consequences, plasticity, retention, and causal controls before evolution or
   communication. Distinguish learned capabilities, engineered inheritance,
   cultural transmission, and physiological fidelity. Neither graph growth nor
   full-graph model agreement proves biological or cognitive success.

At this historical stage, the synthetic replay was complete while anatomical M9 integration was still untested. The demonstration retained its mouth servo and hybrid leg controller. Later implementation status is reported separately.

## Component reports

| Review | Deliverable |
|---|---|
| Adult anatomy, identity, attachment geometry | [mn9-anatomy.md](mn9-anatomy.md) |
| Adult NMJ and activation evidence | [mn9-dynamics.md](mn9-dynamics.md) |
| Native mechanics, units, reusable code | [mn9-mujoco-mechanics.md](mn9-mujoco-mechanics.md) |
| Independent validation and thermal pathways | [mn9-validation-temperature.md](mn9-validation-temperature.md) |
| Whole-plan scientific coherence | [plan-scientific-review.md](plan-scientific-review.md) |
| Whole-plan implementation, data, compute | [plan-implementation-review.md](plan-implementation-review.md) |

The historical review recorded source hashes. Its
source-line findings refer to those snapshots. Review conclusions and synthetic
receipts must not be promoted to biological validation; use the existing
validation report's separate implementation, physiology, mechanics, feedback,
thermal, and nociception gates.

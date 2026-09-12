# Body feedback and fluid coupling in the expanded CNS model

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

This records implemented mechanisms and their assumptions. It does not establish
normal walking, flight, feeding or full-animal completeness. The unchanged
MaleCNS graph supplies central connectivity; no motor policy or gait is added.

## Femoral chordotonal input

`cns_proprio.py` binds **291** sensory IDs: 93 claw, 61 hook and 137 club entries.
The join requires an exact supported type, proprioceptive class, root side and
one of ProLN/MesoLN/MetaLN. Two conflicting entries, 906066 and 933699, remain
unconnected. The inventory comes from the frozen MaleCNS annotations, not a
selection based on motor responses. Limb counts are LF 17, RF 11, LM 65, RM 66,
LH 64 and RH 68; missing cells are not synthesized to equalize the sides.

The physical femur–tibia angle uses the current knee-to-femur-base and
knee-to-ankle vectors. Zero is folded, pi extended. Its time derivative is
causal and filtered with an estimated 1-ms constant. Repeated observations at
the same physical time do not advance that filter. The actual body motion,
including externally caused motion, changes these observations.

Published recordings distinguish position-sensitive claw, direction-sensitive
hook and bidirectional movement/vibration-sensitive club populations. Claw
population responses become larger toward the flexed or extended portions of
the range and are small near 90 degrees. Those features inform the response
families here. The experimental 18-degree lower reference is not a claimed
mechanical joint stop. [Mamiya et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6481666/)

| Type | Implemented response hypothesis |
|---|---|
| SNpp50 / SNpp51 | Flexion / extension position response |
| SNpp41 / SNpp39 | Flexion / extension movement response |
| SNpp40/47/56/57/60 | Bidirectional movement response |

**The polarity assignment is inferred, not measured for these cells.** MANC
Figure 59 identifies different predicted effects of these types on flexor and
extensor circuits. Interpreting those pathways as opposing feedback motivates
the assignments above; it does not prove their sensory tuning. No simulated
walking or motor outcome was used to choose them.
[MANC sensory circuit analysis](https://elifesciences.org/reviewed-preprints/97766v1)

Position responses are rectified linear population approximations about 90
degrees. Movement responses are saturating functions of signed or absolute
velocity. The 200-Hz ceiling, 7.33-rad/s movement scale and filter constant are
estimates, not calcium-to-spike calibration. Individual goniotopy, hysteresis,
club frequency tuning and the arculum/tendon transfer remain unresolved. A
joint-kinematic proxy is not a reconstruction of the sensory organ's mechanics.
[Mechanical feature selectivity](https://pmc.ncbi.nlm.nih.gov/articles/PMC10644877/)

`check_cns_proprio.py` checks actual joint perturbations, limb isolation,
directional/bidirectional responses, pause/reset, parameter rejection, gain
sensitivity and reversal of the declared polarity hypothesis. Reversal changes
97 input-neuron responses; neither choice is selected from motor behavior.
Its imposed perturbations exist only in the assay. The runtime
never applies them or seeks a target angle.

## Opponent thermal input

`cns_thermal.py` binds seven VP2 heating receptors and six VP3a aristal cooling
receptors. It samples current arista positions and maintains estimated peripheral
temperature and adaptation states. Warming raises VP2 input and lowers VP3a
input; cooling produces the opposite change. At a held temperature both relax
toward their declared baseline. The older absolute 30-degree warmth threshold
is not used in this expanded branch.

Adult recordings support phasic warming/cooling responses and basal activity.
They do not calibrate this model's common 30-Hz baseline, 25 Hz/degree gain,
20-ms peripheral exchange, 2-s adaptation or 200-Hz ceiling.
[Budelli et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6709853/)

VP3b remains separate: its non-aristal/slow pathway is not assigned the VP3a
kinetics. Humidity, other sacculus receptors, internal thermosensation and
damage/nociception remain missing. Heating/cooling signals do not become an
escape instruction. [Thermosensory anatomy](https://pmc.ncbi.nlm.nih.gov/articles/PMC7443704/)

The callable check in `cns_thermal.py` verifies opponent responses, adaptation,
side isolation and exact pause/reset. The current source controls still span
22–45 degrees; cooling occurs on a decrease within that range or movement away
from a warm source. Below-ambient environments are not represented by those
controls.

## Contact taste and liquid boundaries

The new left and right labellar meshes are sampled separately. Contact on one
side only drives that side's mapped sugar/bitter population. The sensory model
uses a 20-micrometre contact margin and estimated 200-Hz stimulus rate; it does
not resolve individual sensillum positions or chemical dose-response curves.
Native geometric contact also generates physical forces, independently of
taste. Disabled sources have their geometry and aggregate body collision masks
disabled.

Sources have an explicit `liquid` property, exposed as **Liquid surface** in the
native controls. Existing food sources default to liquid surfaces. A dry source
can provide contact taste while leaving the fluid inlet closed. Odor, taste,
temperature, optical appearance and liquid availability do not choose a motor
action. `check_cns_senses.py` checks these separations and unilateral contact.

`ProboscisHydraulics` is the primed eight-cell circuit described in
[the proboscis methods](whole-proboscis-mechanics.md). Each physical step reads
actual lumen geometry, solves pressure/volume conservation and applies
work-conjugate pressure loads to the wall and crop-junction joints. A wet
labellar contact opens an ambient-pressure inlet; a dry mouth seals it.
Neither boundary selects a pumping sequence or muscle command.

The initial liquid-filled circuit is an explicit initial condition. Crop and
proventricular reservoir pressures are fixed estimates; salivary supply is
closed. Dry filling, menisci, cavitation, finite crop storage, solute advection,
metabolism and changing body mass with food are not modeled. Reported boundary
exchange is not automatically a measurement of newly digested food.

## Time and force accounting

The CNS advances every 100 microseconds. Body mechanics, NMJs, asynchronous
muscles and the fluid circuit advance every 10 microseconds. Newly emitted
neural events enter only the last of the ten physical substeps, at the neural
interval's end, before their modeled conduction/NMJ delay. No spike is repeated
across the ten substeps.

Native muscle actuators and custom asynchronous force actuators use different
gear signs. Reported tendon tension is `-actuator_force * gear[0]`. Fractional
graded neuronal release is not counted as spikes, and custom asynchronous
muscle activation is included separately from MuJoCo's native activation array.
The fluid force buffer is rebuilt each physical step; old pressure loads never
accumulate. Those loads occupy internal wall/radial joint coordinates and are
not body assistance or a locomotor force.

Unchanged source settings do not trigger extra constraint solves at transport
boundaries. Thus display packet size has no intended physical role. The final
integration check compares body state, motor counts, asynchronous activation
and fluid state across packet schedules.

## Dense contact solver correction

The inherited FlyGym configuration enabled five NoSlip postprocessing
iterations. This added hard-friction correction forms a constraint-space
inertia matrix; dense wing/ground contact exhausted first 25 MiB and then
256 MiB of arena memory at about 27 ms. Increasing the allocation alone did
not solve the cause.

The expanded body uses the ordinary Newton friction solution with
`noslip_iterations=0` and a 256-MiB arena. All 3,864 wing collision patches
remain active, with the same friction, geometry, muscle and neural parameters.
The repeated 100-ms probe reached 1,918 contacts and 7,710 constraints with
only 6.75 MiB peak arena use. The worker treats a physics warning as fatal;
it does not continue after dropping constraints. This is numerical resource
qualification, not validation of biological friction or body behavior.

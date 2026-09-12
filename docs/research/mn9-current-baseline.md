# MN9 implementation baseline: historical reference

This records the implementation and synthetic checks examined on 2026-09-11, not current package checks or physiological validation.

For current package evidence, see [status](../status.md); planned work is in the [roadmap](../roadmap.md). Historical artifacts are indexed in the [results provenance archive](../../results/README.md).

- The prepared graph contained 138,639 neurons. The MN9 readout was
  FlyWire ID `720575940660219265`, identified as right MN9 by the published
  workbook and annotation; the opposite-side legacy ID was absent.
- The baseline proboscis implementation used a position actuator. Smoothed MN9
  firing divided by an estimated 80 Hz gain set a fraction of a fixed 1.05-radian
  target angle. It did not model neuromuscular transmission, muscle activation,
  force-length, force-velocity, or anatomical moment arms.
- The original `body.py` added a pitch hinge to the rostrum mesh, with the haustellum
  attached downstream. This provided geometry, but not a reconstructed muscle.
  See the package’s [body implementation](../../runtime/body.py) for current code.
- The baseline leg controller was FlyGym's hybrid controller with preprogrammed
  steps. Its output was not evidence of a nerve-cord simulation or neural locomotion.
- The neural interface preserved the full recurrent neural state. A mechanistic
  muscle model needs per-timestep MN9 spikes, not just 10 ms aggregate counts
  or a smoothed rate.

## Historical checks

The original artifact `live-check.json` records a fixed 0.5-second neural calibration: 48 MN9
spikes with sugar, 6 with sugar plus bitter. The position-actuator outputs were
about 60° and 3° respectively. Those angles were imposed by the conversion and
must not be targets for fitting a muscle model.

The original artifact `temperature-feeding-probe.json` records a contact-food check. With a
45°C source, the approximate field at the antennae is about 43.4°C and warmth
receptor activity rises; MN9 still produced 43 spikes versus 48 at 22°C. The
model did not implement mouth/body thermal injury or a verified nociceptive
pathway. These observations do not justify a “hot food means don't eat” rule.

The original artifact `descending-odor-probe.csv` is a neuron-output survey with no motor
controller. Odor activates DNb05, DNg13, DNa02, and other descending neurons,
while P9 and the identified forward-walking populations are mostly silent in the
tested conditions. Activity alone does not establish each cell's muscle target
or justify routing all active neurons into forward walking.

These artifacts are described in the [historical provenance archive](../../results/README.md); they are not new package-check receipts.

## Spike replay input

[capture_mn9.py](../../runtime/capture_mn9.py) exports time-resolved, model-generated MN9 spikes for
replay into a mechanistic muscle unit. Such traces can test integration and
causal accounting, but cannot fit or validate biological muscle dynamics. The
anatomy, dynamics, mechanics, and validation reports describe the
independent evidence and identify remaining estimates.

## Historical force-chain implementation

[mn9_force_replay.py](../../research/mn9_force_replay.py)
replayed those per-cell events into delayed, stateful NMJ excitation and
MuJoCo's native activation and muscle force law. The transmission model retains
available efficacy and decaying excitation; recent spikes affect subsequent
responses. Its saturation is a mathematical hypothesis, not measured receptor
occupancy or calcium. Native muscle activation supplies the third state. The
only control input to the muscle is excitation; neither food labels nor a target
angle enter the function.

The geometry is the **synthetic lever** from
[muscle_mechanics_probe.py](../../research/muscle_mechanics_probe.py),
not a reconstruction of the fly's rostrum. All peripheral parameters are
unfitted hypotheses. This preserves the distinction between testing the causal
software chain and validating adult M9.

| Parameter block | Values in this bench | Evidence status |
|---|---|---|
| NMJ delay | 1 ms | Synthetic total conduction/transmission delay |
| Excitation | 8 ms decay, 0.2 increment per fully available event | Synthetic, dimensionless; not voltage or calcium |
| Synaptic efficacy | 0.2 depression per event, 100 ms recovery | Phenomenological hypothesis; adult CM9 supports testing short-term depression, not these numbers |
| Native activation | 10/40 ms base rise/fall constants | Generic synthetic settings; native activation-dependent time constants |
| Muscle force/length | 0.02 µN maximum isometric scale; 1 mm optimal fiber; 0.25 mm constant tendon | Synthetic; no adult M9 geometry or force calibration |
| Body | 1 mm lever, 0.001 g, no gravity, no passive joint spring | Synthetic assay; no imposed retraction |
| Integration | 0.1 ms fixed grid, native RK4 with interval excitation updates | Numerical choice, checked at 0.05 ms |

FlyGym's documented units are **mm, g, s**, giving µN force and nN·m hinge torque.
See the [mechanics report](mn9-mujoco-mechanics.md)
for primary authority, force curves, and the native API.

Both checks passed in the original study. These results have not been re-established
by this document for the public package. The force replay tests zero input, release block, reaction
under a joint clamp, opposing load, half-step convergence, spike timing with
equal event counts, and finite bounded state. The half-step difference in the
reported metrics is at most **0.00137%**; this is a numerical result, not a
physiological accuracy estimate. The mechanical probe separately checks native
force–length/velocity/passive terms, torque, power, and sensor readback.

Original artifacts `mn9-force-replay-check.json`, `muscle-mechanics-check.json`,
and `mn9-force-replay.png` record the implementation evidence; see the
[historical provenance archive](../../results/README.md). Sugar/bitter labels identify the originating
brain experiment only; no behavioral contrast is a pass criterion or fitting
target. The replay records the SHA-256 of the captured input in its receipt.

**Absent from this historical assay:** anatomical M9 geometry, calibrated peripheral kinetics,
series-elastic tendon mechanics, antagonist drive, identified proprioceptive or
contact-afference closure, and integration with the articulated fly model. Native muscle
mechanics assumes constant tendon length. The free lever can keep moving after
activation falls because this assay has no damping or restoring force. That is
an assay limitation, not predicted proboscis behavior. The original articulated-fly demonstration retained
its position servo and hybrid walking controller. Current implementation claims
belong in the [package status](../status.md).

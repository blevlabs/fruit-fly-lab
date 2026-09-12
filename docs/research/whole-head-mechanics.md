# Head, antenna and retinal mechanics

This component provides **24 native muscle/tendon prototypes** on the existing NeuroMechFly: 12 neck, eight antennal and four retinal paths. A cervical support, its bilateral head-condyle constraints, passive antennal articulation and internal retinal structures supply mechanical transmission. This is source-informed topology with uncalibrated metric/material estimates, not a fitted posture controller or biological validation.

Implementation: [head_muscles.py](../../runtime/head_muscles.py). [Proboscis and pressure/flow mechanics](whole-proboscis-mechanics.md) compose in either order.

The numerical results below are historical simulation evidence from 2026-09-11; they were not rerun for this documentation revision. The original check artifact is [check_head_muscles.py](../../tests/check_head_muscles.py); see the [historical provenance archive](../../results/README.md). See [current package status](../status.md) and the [research roadmap](../roadmap.md) for subsequent validation and open work.

## Integration

```python
from head_muscles import add_head_muscles
records += add_head_muscles(fly)  # before world attachment, existing leg joints permitted
```

The signature also accepts `group_force_uN=28.0`, `activation_time_s=(0.01,0.04)` and `sensory_force_uN=1.0`. Returned records use the existing common schema: `local_actuator_name`, `local_tendon_name`, world-qualified `actuator_name`/`tendon_name`, `target_muscle`, `force_uN`, `limb`, `side`, `semantic_muscle_key`, `peripheral_target_sides`, `joint_names`, attachment `sites`, lengths, timing and provenance. Every actuator is a native muscle on a native spatial tendon, compatible with the motor-unit capacity splitter. IDs are empty and mapping status is unmapped until supported motor outputs are connected.

| Physical bank | Semantic keys | Example qualified actuator |
|---|---|---|
| Neck (`limb="neck"`) | `neck.VL1`, `neck.VL2`, `neck.TH1`, `neck.TH2`, `neck.AD`, `neck.LEV` | `fly/neck_muscle_left_VL1` |
| Antenna (`limb="antenna"`) | `antenna.m1`, `.m2`, `.m3`, `.m4` | `fly/antenna_muscle_left_m1` |
| Retina (`limb="retina"`) | `retina.MOT`, `retina.MOS` | `fly/retina_muscle_left_MOT` |

Each key has separate left/right physical records. These physical locations do not infer neuronal laterality. Binding uses **`peripheral_target_sides` from the motor map**, including the verified contralateral outputs of CvN6/7, rather than using soma side. No region-only antennal or retinal motor annotation is promoted to an exact muscle correspondence here.

Native body handles, original body hierarchy, original eye-lens bodies, existing joint parameters and the full NeuroMechFly object are retained. New raw MuJoCo structures are exposed by name without fabricating `BodySegment` enum entries. Historical checks covered standard colorization, tracking-camera creation and world attachment after construction. No action field, head-angle servo, default spike train, movement cycle, clock-spike generator or sensory feedback controller is included.

## Neck authority and mechanism

[Gorko et al., 2024, Nature](https://www.nature.com/articles/s41586-024-07222-5), especially **[Extended Data Fig. 7](https://www.nature.com/articles/s41586-024-07222-5/figures/11)**, supplies adult Drosophila muscle/cuticle topology. The [supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07222-5/MediaObjects/41586_2024_7222_MOESM1_ESM.pdf) identifies the corresponding muscle groups; its SHA-256 on inspection was `0d79fcef0205b2eb27cd0f1e205862ecebea7610fb5bbb43fa6421c370bdc7d2`. The authors' accessible [paper PDF](https://faculty.washington.edu/tuthill/docs/gorko%202024.pdf) was also read. **The paper's fitted movement/action-field model and proprioceptive feedback model are not imported.**

| Target | Source-supported endpoints | Reduced transmission |
|---|---|---|
| VL1 | Lateral sternal-apodeme region to posterior head through a long tendon | Thorax → head |
| VL2 | Sternal region medial to VL1 to posterior head through a long tendon | Thorax → head |
| TH1 | Lateral/posterior dorsal thorax to posterior head through the long curved TH tendon | Thorax → head |
| TH2 | More ventroanterior origin than TH1, joining the posterior head tendon | Thorax → head |
| AD | Dorsal pronotal region to cervical sclerite | Thorax → separate cervical support → head via condyles |
| LEV | Dorsal pronotal region to cervical sclerite | Thorax → separate cervical support → head via condyles |

AD/LEV are not attached directly to the head to bypass the support. `neck_cervical_sclerite` is an estimated rigid support at the existing head origin `(0.0287,0,0.000698)` mm in thorax coordinates. It has yaw and roll coordinates. The original head has yaw, roll and pitch coordinates. Two native body-to-body `connect` constraints keep points `(0,±0.075,0)` mm on the support and head together, leaving relative pitch about the bilateral condylar axis free. The six scalar constraint rows have **rank two**, so five coordinates supply **three effective head-rotation DOFs**. This closed linkage preserves the original head subtree and all its handles.

Joint names are `neck_head_yaw`, `neck_head_roll`, `neck_head_pitch`, `neck_support_yaw`, `neck_support_roll`. All have estimated ±0.5 rad stops, zero angle-restoring spring and 0.005 nN·m·s/rad damping. These are material/numerical limits, not Gorko's observed convergence poses. The condylar constraints use a numerical stabilization time of 0.2 ms at a 10 µs step; this is not a muscle activation constant or biological tissue-compliance measurement.

**Straight paths and support rigidity are reductions.** The [OH-to-TH tendon coupling in Extended Data Fig. 8](https://www.nature.com/articles/s41586-024-07222-5/figures/12), varying curvature, full cervical sclerite deformation, other neck muscles and translations are not reconstructed. No fixed pulley was invented to stand in for the missing OH muscles.

### Neck attachment estimates

The following coordinates are **chosen, unfitted millimeter estimates**, informed by the depicted regions. Origins are relative to the native neck pivot in the thorax; insertion coordinates are in the head or support frame. Right-side geometry mirrors y. No figure-derived metric registration or measured moment arm is claimed.

| Target | Left origin relative to pivot | Left insertion | Insertion owner | LT fraction |
|---|---|---|---|---:|
| VL1 | `(−.330,.145,−.200)` | `(−.010,.090,−.060)` | Head | .25 |
| VL2 | `(−.320,.100,−.190)` | `(−.010,.055,−.055)` | Head | .25 |
| TH1 | `(−.360,.280,.100)` | `(−.008,.090,.065)` | Head | .25 |
| TH2 | `(−.300,.260,.055)` | `(−.008,.084,.062)` | Head | .25 |
| AD | `(−.120,.025,.120)` | `(−.020,.080,−.020)` | Cervical support | .05 |
| LEV | `(−.100,.110,.160)` | `(−.025,.075,−.030)` | Cervical support | .05 |

For all paths, L0 is the remaining positive fraction of reference length. The tendon fraction distinguishes the long-tendon groups only approximately. Native generic force curves and 28 µN per-side/group capacity remain estimates; no contraction was fitted to a desired head pose.

## Antennal authority and mechanism

[Suver, Medina and Nagel, 2023, Figure 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC9992063/#F2) identifies **four muscles within the first antennal segment**, numbered anterior to posterior, with tendon insertions at the interior of the second segment. The paper distinguishes the active scape–pedicel joint from the passive pedicel–funiculus joint. It provides genetic access to selected groups, not exact MaleCNS neuron IDs for every muscle.

Four native MTUs on each side connect **head-fixed scape-region origin sites to the existing pedicel body**. No external scape shape or changed body class is added: the missing scape is a fixed attachment frame on the head. Two local active-joint coordinates (`antenna_{side}_pitch`, `antenna_{side}_yaw`) represent the supported multidirectional movement. The existing funiculus receives a passive hinge (`antenna_{side}_funicular`) along its rig longitudinal direction; **no muscle is attached across that passive joint**.

Attachment recipes are explicit in `head_muscles.py`: m1/m4 occupy estimated dorsomedial paths, m3 a ventrolateral path, and m2 an intermediate structural path. The paper's m3 down/back effect and dorsomedial m1/m4 anatomy inform placement; no deflection amplitudes, wind-response time courses, flicking pattern or fitted angle are imported. Pedicel quaternions are normalized before transforming origin coordinates to head coordinates, matching MuJoCo's compiled rig.

Estimated active-joint stops are ±0.4 rad, spring 0.01 nN·m/rad and damping 0.0001 nN·m·s/rad. Passive funicular stops are ±0.3 rad, spring 0.004 and damping 0.00003 in the same units. These spring references describe the authored resting material geometry, not motor control targets. No antennal body mass is added. Auditory frequency response, wind loading and identified afferent encoding remain unvalidated.

## Retinal authority and mechanism

[Fenk et al., 2022, Figure 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC10103069/#F1) identifies two muscles per adult Drosophila eye:

- **MOT, musculus orbito-tentoralis:** posterior tentorial-bar attachment through a long tendon to the anteromedial orbital rim.
- **MOS, musculus orbito-scapalis:** antennal-cup edge through a shorter tendon to a more dorsal frontomedial orbital rim.

The orbital ridge surrounds the retina. The paper directly distinguishes moving photoreceptors from **stationary lenses**. Accordingly the existing `l_eye`/`r_eye` lens geometry remains rigid relative to the head. A new internal `retina_{side}_orbital_ridge` body carries two small compliant translational modes, anterior and dorsal. These are deformation-mode approximations; no anatomical ball-joint pivot is asserted. Each side receives MOT and MOS tensile paths from the identified head regions to different rim locations.

The internal reference center is derived from the existing eye mesh frame; the diagnostic ellipsoid and attachment offsets are unmeasured estimates. New coordinate stops are ±0.012 mm, stiffness 2000 µN/mm and damping .1 µN·s/mm. The paper's reported optical shifts were not used as endpoints. This module does not alter eye-camera rays, photoreceptor sampling or visual-neuron input from retinal position; having a moving retinal body does not establish sensory encoding or gaze behavior.

## Force, mass and neural gaps

All MTUs use native MuJoCo tendon transmission, `mjDYN_MUSCLE`, active/passive force–length curves and bounded `[0,1]` excitation/activation. Native units are mm–g–s, µN and nN·m. Activation/deactivation parameters stay **10/40 ms**, including at **10 µs physics steps**. Neck capacities default to 28 µN per side/group; smaller antennal/retinal units default to an explicitly unmeasured 1 µN. Sensory-head LT/L0 partition is 10/90% of reference path length. Both are positive.

There is no extra mass from duplicating internal anatomy. The cervical support receives **1 µg from the native thorax**; each internal retina receives **1 µg from that side's native eye geom**. The original masses exceed the compiler's remaining-body minimum after redistribution. Total compiled mass is conserved to floating-point precision. Segment inertia changes from that redistribution are estimated. No masses or force scales are derived by behavior fitting.

The historical motor map, `malecns-motor-map.json` ([provenance archive](../../results/README.md)), has SHA-256 `c8bbfec04646edad8b6beb45301f45d78ec3869c12bbf407513b7d046dbd55eb`. In that map, **18 named neck rows can bind all 12 neck prototypes**. CvN4/5 are ipsilateral; **CvN6/7 are contralateral**, as the map's canonical output-side list records. For example, CvN6 body 10156 binds left VL1 and CvN7 body 10754 binds right VL1. This does not use a soma-side fallback.

That map contains **13 antennal and seven retinal motor rows with no exact named target**. Therefore all eight antennal and four retinal prototypes remain without neural correspondence. Their mechanical anatomy is implemented, but no unvalidated association to a region-only neuron or genetic driver is installed. Other unmapped neck rows and omitted muscles remain explicit gaps; this is not a complete reconstructed neck motor system.

## Historical verification

The original `check_head_muscles.py` result was **PASS**. Checks covered:

- Preserved original body handles, hierarchy, leg passive properties, rigid lenses, colorization, tracking camera and world attachment.
- 24 native tendon/muscle units with independent bounded activation, positive L0/LT and agreement between declared and compiled reference lengths.
- Two native condylar connections, rank-two constraints, force transmission from AD/LEV through the support to the head, and no prescribed head-angle response.
- Geometry/Jacobian/force agreement; largest finite-difference error **8.33e−11**. Minimum sampled actual fiber length **0.0204555 mm**.
- Independent 10 µs diagnostic pulses across every unit. Largest sampled condylar position error **0.001367 mm**; these are compliant numerical constraints, not exact biological joints.
- Total mass difference **2.17e−19 g**; both head→proboscis and proboscis→head construction orders compile **59** combined native prototypes and retain both condylar constraints.
- Motor-map output-side/topology readback at the cited revision, including explicit contralateral CvN6/7 checks and preserved unknown antennal/retinal correspondences.

These constituent checks do not establish brain-driven behavior, biological fidelity or sensory encoding. Full-body neural integration and sensory interfaces require separate evidence, as recorded in the [current package status](../status.md).

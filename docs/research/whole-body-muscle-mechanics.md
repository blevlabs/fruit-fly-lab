# Leg musculature: implemented mechanics and remaining evidence gaps

This note records historical studies from September 2026. Reported checks and source hashes identify those studies; they are not new verification of the packaged software. See [current status](../status.md), the [research roadmap](../roadmap.md), and the [historical provenance archive](../../results/README.md).

Historical model, 2026-09-11: `add_leg_muscles(fly)` constructed **134 muscle–tendon paths and 460 sites**: LF/RF 24 each, LM/RM 22 each, LH/RH 21 each. It adds 12 bodies and 24 scalar joint coordinates for separate trochanter/femur interfaces and moving pretarsal assemblies. **Physics steps of 10 μs or smaller are required for the checked angular-accuracy tolerance.** The neural/NMJ integration interval must be specified independently of the mechanical timestep.

This is a source-informed mechanical model with explicit estimates. It does not select actions, generate a gait, command angles, inject walking drive, or fit parameters to movement outcomes. It does not establish normal-fly behavior or complete biological muscle coverage.

The implementation is described in [leg_muscles.py](../../runtime/leg_muscles.py), with a component check in [check_leg_muscles.py](../../tests/check_leg_muscles.py). The historical numerical study used NumPy, FlyGym 2.1 and MuJoCo 3.9.

## Coverage and binding

The last extension adds 44 paths and retires the four ambiguous combined sterno/tergo prototypes, producing **40 net additional paths relative to the previous 94**.

| Newly represented target | Paths across six legs | Matching MN records in the inspected motor map | Resolution |
|---|---:|---:|---|
| `Sternotrochanter` | 6 | 14 | Separate ventral-thoracic head; estimated origin and shared extensor-apodeme route |
| `Tergotr.` | 6 | 12 | Separate tergal head; estimated origin and shared extensor-apodeme route |
| `Fe reductor` | 12 | 20 | Two traced fiber representatives per leg; hypothesized interface compliance |
| `ltm2-femur` | 12 | 12 | Proximal/distal femoral representatives pulling the shared long apodeme |
| `ltm1-tibia` | 6 | 9 | Estimated tibial origin pulling the same distal route |
| `TTM` | 2, LM/RM only | 6 TTMn/STTMm | Dedicated middle-leg jump-complex route; exact semantic key below |
| **Total** | **44** | **73 unique MNs** | Counts of eligible named records, anatomical eligibility rather than proof of dynamic connection |

The motor map (original artifact `neural-motor/malecns-motor-map.json`; [archive](../../results/README.md)) supplies neuron identities and peripheral sides. This module never derives a CNS ID from an anatomy skeleton, actuator suffix, soma side or muscle name. Its prototype records start with `motor_neuron_ids=[]`; the motor-unit binder fills these during binding. That does not mean the integrated CNS has zero connected muscles.

Per-leg mechanics in the historical model:

| Muscle/path group | Foreleg, each | Middle leg, each | Hind leg, each |
|---|---:|---:|---:|
| Tergopleural promotor a/b | 2 | 0 | 0 |
| Pleural promotor | 1 | 0 | 0 |
| Pleural remotor/abductor | 1 | 1 | 1 |
| Sternal anterior rotator / posterior rotator / adductor | 3 | 3 | 3 |
| Trochanter flexor a/b | 2 | 2 | 2 |
| Accessory trochanter flexor / trochanter extensor | 2 | 2 | 2 |
| Tibia flexor / extensor | 2 | 2 | 2 |
| Accessory tibia flexor, anterior/posterior representatives | 2 | 2 | 2 |
| Tarsus levator / representative depressor | 2 | 2 | 2 |
| Sternotrochanter / tergotrochanter | 2 | 2 | 2 |
| Femur reductor representatives | 2 | 2 | 2 |
| Femoral long-tendon muscle representatives | 2 | 2 | 2 |
| Tibial long-tendon muscle | 1 | 1 | 1 |
| TTM jump-complex representative | 0 | 1 | 0 |
| **Total** | **24** | **22** | **21** |

All middle/hind transfers and all inter-specimen registrations remain estimated. Muscle-group correspondence does not establish individual fiber innervation, recruitment order or force capacity.

## Model assembly and required physical structures

Call once after adding `AxisOrder.YAW_PITCH_ROLL` leg joints and the neutral initial pose, **before world attachment**. Tibia–tarsus pitch joints must exist. Joint-transmission leg actuators and duplicate muscle installation are rejected.

```python
records = add_leg_muscles(fly)
# Attach to the world and compile afresh. Resolve native IDs by names.
# Resolve anatomical motor targets and advance each MN/NMJ independently.
```

Each record supplies `target_muscle`, `limb`, matching `peripheral_limb`, `side`, local and world-qualified actuator/tendon names, capacity fractions, source/estimate status, attachment data, and `physics_max_timestep_s=1e-5`. New-structure records additionally supply:

- `structures`: body names, pivot/frame offsets, passive-joint description and inherited armatures.
- `structural_joint_names`: world-qualified new joint names.
- `contact_geom_names`: world-qualified new geometry names. Ground/food contact-pair registration must deduplicate these names across records.

For each limb `lf/lm/lh/rf/rm/rh`, the new contact names are:

```
<fly.name>/leg_muscle_<limb>_trochanter_geom
<fly.name>/leg_muscle_<limb>_pretarsal_geom
```

The new body names are `leg_muscle_<limb>_trochanter` and `leg_muscle_<limb>_pretarsus`. New scalar joint names end in `femur_compliance_x`, `femur_compliance_y`, `femur_compliance_z`, and `pretarsal_flexion` under that same prefix. **This adds 24 coordinates to the native `qpos` layout**; the isolated leg fixture grows from 66 to 90. Other appendages add their own coordinates, so always use the compiled model's size.

Existing joint names and properties survive. The old `*_trochanterfemur` body name denotes the distal femoral piece, with its origin shifted by 15% of the original shaft vector. Child positions and attachment coordinates are compensated so the original cuticle surface and pose are retained at zero added-joint angles. The original coxa–trochanter joints move to the new proximal body. New raw bodies/joints are not entries in FlyGym's static `Skeleton`; use native model state and the supplied names for them.

Inserting the bodies reparses a **copy** of the MJCF and refreshes FlyGym's element dictionaries. External `Mjs*` references captured before this call must be reacquired afterward. Serialization and validation compile copies, with static fusion disabled during serialization to preserve named root/head frames. No running `MjModel` is modified.

### Neural clock versus physics clock

The check uses native `IMPLICITFAST` at 10 μs and compares against 5 μs. At 100 μs the model stays finite, but the full-coactivation angle test does not meet the previous 0.003-rad tolerance. For a 100-μs neural/NMJ tick, hold each resulting excitation over ten 10-μs physics steps. **Do not initialize NMJ timing from a 10-μs physics step while advancing that NMJ only once per 100 μs.** If all clocks are changed, advance each at its declared interval. The module reports this requirement instead of altering global integration settings.

### Per-MN activation and capacity

Each MN's event stream and NMJ must remain independent. For a physical capacity budget `F0`, path share `w_j`, and `N` matched motor units, the studied approximation is `F0_m,j = F0 * w_j / N`. Each native actuator receives that MN's excitation, without a pooled spike rate or a second activation filter. Scale both active and passive capacity, and replace the full-capacity prototype rather than retaining it in parallel.

The two representative paths for `Tr flexor`, accessory tibia flexor, femur reductor and `ltm2-femur` each carry half their group budget. These are geometric/capacity approximations, not identified MN-to-fiber links. All new representatives retain `subdivision_mapping_required=True`.

**TTM binding:** LM/RM records use `target_muscle="TTM"` and `semantic_muscle_key="wing.tergotrochanteral_jump"`. The `wing.` namespace does not change their mechanical middle-leg placement. Bind by the supplied semantic key and the motor record's peripheral target side(s), independently of subclass. No alias to intrinsic `Tr extensor` is made.

The exact fiber partition between T2 `Tergotr.` and TTM/STTM annotations is unresolved. Their two representative routes share **one** default 28-μN `T2_tergotrochanteral_complex` capacity budget, split 14/14 μN before per-MN partitioning. This prevents a new annotation label from automatically doubling physical capacity. The equal split and separate estimated dorsal attachment patches are assumptions, not evidence of two independently measured muscles or equal-sized motor units.

## Anatomy and geometry provenance

### Retained FlyMimic paths and coordinate frames

The installed 15-path XML (original artifact `flygym/src/flygym/assets/model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml`; [archive](../../results/README.md)) is pinned to SHA-256 `04f6070d6733940357be005ca72c02ba0d9455538ff018da70c74de7458e9531`. It carries an Apache 2.0 notice. Its anatomy-initialized geometry was subsequently optimized by its authors; it is **not raw anatomical measurement**. Its fitted force/kinetic values and imitation policy are not imported. [FlyMimic methods and appendices](https://arxiv.org/html/2509.06426v2).

Registration uses actual body/site transforms at the zero-reference configuration. For each source segment, joint-center separation supplies a longitudinal axis; the declared pitch axis projected perpendicular to it supplies a transverse axis. A right-handed frame and target/source length ratio define the similarity transform. Right-side sites are reflected in segment coordinates. Source femur sites first include the actual trochanter→femur offset `[-0.01994,0.07244,-0.06238]` mm. Original via-point sequences remain intact. Site directions are never chosen from actuator names alone.

Serial transfer of the original paths uses named muscle groups in [Cheong et al., Figure 7](https://pmc.ncbi.nlm.nih.gov/articles/PMC13384506/) and [Supplementary file 6](https://cdn.elifesciences.org/articles/96084/elife-96084-supp6-v2.csv), inspected SHA-256 `b56b0563f6a6000b2a43fbc7ebec46297668e8e3b6c6d596843d5ad5aab83a65`. These are putative group homologies, not a transfer of MANC IDs into MaleCNS.

### Separate sternotrochanter, tergotrochanter and TTM paths

The [Azevedo appendix](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf), Figures A5/A6, distinguishes sternal versus tergal origins and their shared trochanter extensor tendon. The new paths therefore begin on different thoracic cuticle patches, pass through the coxa and terminate on the trochanter-side apodeme. They span both thorax–coxa and coxa–trochanter joints.

Thoracic attachment patches are estimated from the modeled thorax mesh near each coxa. The shared apodeme proxy averages the paired donor via/insertion coordinates from the formerly combined paths. **The source a/b paths are not renamed as individually identified heads**; their four ambiguous foreleg prototypes are removed. Middle/hind origins and routing remain transferred estimates.

The middle-leg TDT/TTM originates at dorsal thoracic cuticle and inserts through its tendon into the middle leg. That topology supports the dedicated jump route, distinct from intrinsic coxal `Tr extensor`. [Eldred et al., Figure 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/). The primary giant-fiber study describes three motor neurons supplying the second leg's tergotrochanteral muscle; exact individual attachment/force allocations remain unresolved here. [Bacon and Strausfeld 1986](https://doi.org/10.1007/BF00603798).

### Public XNH traces beyond the 15-path asset

The [Kuan/Phelps publication](https://www.nature.com/articles/s41593-020-0704-9) and [authors' resource page](https://connectomics.hms.harvard.edu/x-ray-holographic-nano-tomography-datasets) expose CATMAID project 61. Its centerlines and cuticle meshes were read through public endpoints. Coordinates are nanometers and are divided by 1,000,000 to obtain mm. The [Azevedo appendix](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf), SHA-256 `822c298e50da9fee3ce75f1dabda040574eac9fc854fdf92837856a82c8515f6`, supplies muscle nomenclature and topology. Relevant figure/text pages were inspected. Geometry IDs below are **not neuron IDs for CNS binding**.

| Geometry representative | Public skeleton | Raw response SHA-256 |
|---|---|---|
| Accessory tibia flexor, anterior | [606022](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/606022/compact-detail) | `0e610f93abc423a8aaae77237b9898b89a0d70096a936f2305470db6ab8b93d7` |
| Accessory tibia flexor, posterior | [602225](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/602225/compact-detail) | `551630e5284a628cb1fb5e23abc0578529381d64428f89f03337ec7e3b78f837` |
| Femoral LTM, proximal | [609813](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/609813/compact-detail) | `9bdccc8dc4c1629ed45077803fa0200a5faa98a099543e8affeaf19ca955c854` |
| Femoral LTM, distal | [609856](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/609856/compact-detail) | `3602b5773faf40eee738392dda417a703515bd42cda4aba9a0a570e631ac5c48` |
| Femur reductor, region 1 | [603409](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/603409/compact-detail) | `a6c2181e76e52daebef663ba3120a3608507ed43809f219bf2101396670795db` |
| Femur reductor, region 2 | [603329](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/603329/compact-detail) | `08bbc8a402b99499cf1231c7971e0547fd49b9d54601184384b2539f77cbc770` |
| Common long apodeme | [601725](https://radagast.hms.harvard.edu/catmaidvnc/61/skeletons/601725/compact-detail) | `12a568f6036fe013bd3ed72b7cda3595f43bbb87b70b69e503da7532afa6eca3` |

Representatives are the centerlines closest to median arc length within their annotated anatomical groups, selected before simulation. Group sizes were 14/15 for anterior/posterior accessory flexors, 2/4 for proximal/distal LTM2 fibers and 27/2 for the two trochanter fiber groups. Endpoint chords simplify the traced fibers. The trochanter traces run from femoral insertion toward trochanter origin, so their endpoint order is explicitly reversed for origin/insertion assignment.

The module stores the raw endpoints, selected long-apodeme knots and frozen coordinate transforms. Femoral cuticle registration used [volume 112](https://radagast.hms.harvard.edu/catmaidvnc/61/volumes/112/) and the [donor femur mesh](https://github.com/gizemozd/FlyMimic/blob/main/flymimic/assets/models/meshes/stl/LFFemur.stl): fixed-scale rigid surface registration gave 3.533 μm RMS residual. Trochanter registration used [volume 111](https://radagast.hms.harvard.edu/catmaidvnc/61/volumes/111/) and the [donor trochanter mesh](https://github.com/gizemozd/FlyMimic/blob/main/flymimic/assets/models/meshes/stl/LFTrochanter.stl): 5.918 μm RMS. These residuals characterize surface alignment, not attachment accuracy. Neither procedure used force or motion outcomes.

Mesh/volume hashes: femur volume `07b4b64a7f8290de2528bdb6769441545665bb8cb5c9a8911b6cab048b9f3a0f`; femur STL `d4012dff9598fcf021d451b04d0b2bfce666fa8bc5369c7a6844699ff806f3cc`; trochanter volume `8c934fe2bb591bd3ff5e0c07d3f37fdf369f4784dff6802c94dddbab207bf492`; trochanter STL `9eece5e88d044b53517bfe231edddbe8acc3f5cb50bbd2230168f799cfaee9f2`.

Tibial registration uses the shared knee pivot/axis from the registered femur and the principal axis of incomplete [volume 113](https://radagast.hms.harvard.edu/catmaidvnc/61/volumes/113/), hash `3500488e8ecb3dadf036254c393c6dedbc3cfcc58e6015515e947153ba0ddfcd`. Its XNH knee pivot is `[0.1328638211,0.1564272068,0.1614330886]` mm. No unconstrained partial-to-full tibia fit is used. The volume ends before the tibia–tarsus joint; it provides no claw insertion coordinates.

### Femur reductor and the small compliant interface

Figure A10 identifies fibers within the trochanter terminating on the femur. The new paths connect those separate physical pieces. The formerly merged cuticle is partitioned at 15% of shaft length, an estimate based on the donor trochanter's relative extent. All original triangles belong to one of the two pieces; no duplicate full segment is retained.

The three added small rotations are **coordinates of a hypothesized compliant interface**, not three discovered anatomical hinge axes. Their ranges are ±0.02 rad, stiffness 0.02 nN·m/rad and damping 0.002 nN·m·s/rad. The function of this interface and whether its biological motion is appreciable remain uncertain. This implements force transmission under a declared compliance hypothesis rather than claiming the femur-reductor function is known.

### Long apodeme and pretarsal assembly

LTM2 originates in the femur and LTM1 in the tibia; both pull the common long tendon extending to the claw. [Azevedo et al., Figure 4 and Appendix A15/A16](https://pmc.ncbi.nlm.nih.gov/articles/PMC11348827/). The new LTM2 paths use traced origins and proximal apodeme guides through the femur–tibia articulation. LTM1 uses an explicitly estimated origin at 35% of tibial shaft length on the measured apodeme side. Its path starts in the tibia and therefore does not actuate the femur–tibia joint directly.

All three paths share coincident distal guide coordinates through tarsomeres 1–5 and the moving pretarsal attachment. Their forces superpose on the same assumed rigid apodeme; independent elastic tendon copies are not added. Tarsal guides are estimated at internal ventral positions, 20% of outer cuticle radius. Distal topology follows adult tendon anatomy; metric guide positions remain unmeasured. [Soler et al. 2004](https://pubmed.ncbi.nlm.nih.gov/15537687/).

A new pretarsal body carries the distal 25% of the existing terminal cuticle mesh and a ventral attachment site representing the unguitractor plate. This is a **collective pretarsal assembly with an estimated hinge**, not independently resolved claws, pulvilli, auxiliaries and membranes. Its pivot, plate lever arm and cut plane are estimates. The retained mesh has convex collision behavior; true hook engagement and adhesive-pad mechanics are not validated. [Ferris's adult leg/pretarsus figure](https://flybase.org/reports/FBim0000796.html) supplies external topology, not these coordinates.

Pretarsal range is −0.05 to 1.4 rad; passive opening stiffness is 0.002 nN·m/rad, damping 0.0002 nN·m·s/rad. These passive elastic rest properties are not angle commands. The new joints inherit the supplied leg's armature values, 1e-6 g·mm² in the checked fixture, to retain its numerical inertia convention. Limit constraint impedance is 0.9999 with a 2-ms reference timescale. All are explicit mechanical/numerical estimates.

Modeled segment mass is partitioned between pieces; the existing compiler's 1e-6-g minimum body mass adds **6e-6 g total** for the six pretarsal bodies in the checked model. Compiled mass changes from 0.00102431 to 0.00103031 g. This is numerical mass regularization, not measured added tissue. Original joint parameters and global compiler settings are preserved.

### Earlier distal paths retained

Accessory tibia flexors use separate anterior/posterior traced fibers. Their distal myotendinous endpoints are treated as rigid to tibial apodemes; the thin tendons' exact cuticular insertions and compliance remain unresolved. The source's older “tibia reductor” annotation is not the femur reductor.

`Ta levator` and `Ta depressor` retain bone-derived two-site estimates: dorsal origin at 80% and ventral origin at 55% of tibial shaft length, respectively, attaching 5% along tarsus1. The origin/attachment radius is 80% of the corresponding cuticle radius. Direction is grounded in donor insertion geometry and anatomical compartments; fractions are fixed estimates, not optimized for stepping. The retro-depressor branches in Appendix A17 remain absent.

## Force and length ledger

Native units are **mm–g–s**, force μN, hinge torque nN·m, inertia g·mm². [FlyGym units](https://neuromechfly.org/tutorials/1b_advanced_model_composition/).

| Parameter | Implementation / evidence status |
|---|---|
| Ordinary muscle-group capacity | 28 μN by default: estimated PCSA 0.001 mm² × estimated specific tension 28 mN/mm². Not a measured per-muscle capacity. |
| T2 tergotrochanteral complex | One 28-μN budget, split 14/14 between the `Tergotr.` and TTM representatives; unresolved physical/fiber partition. |
| Multi-path groups | Fractions sum to one per group; no extra full-capacity copy per path or MN. |
| Non-LTM optimal length | Whole registered path length at neutral; lumped estimate. Fixed physiological tendon length 0. |
| LTM2 optimal length | Observed representative fiber arc length × registration scale (0.148111/0.202358 mm before scaling), used as an estimated optimal length. |
| LTM1 optimal length | 25% of tibial shaft length, explicitly estimated. |
| LTM fixed tendon length | Reference total path length minus estimated fiber length; checked nonnegative. |
| Native normalization | `range=[0,1]`, `lengthrange=[LT,LT+L0]`; these calibrate force curves, not angle/path targets. |
| Activation / deactivation | Generic 10/40 ms; excitation and activation bounded [0,1], zero reset input. No second activation filter. |
| Force–length–velocity | Generic `lmin=.5`, `lmax=1.6`, `vmax=1.5 L0/s`, `fpmax=1.3`, `fvmax=1.2`. |
| Transmission | Unit gear, spatial tendons; no additional tendon stiffness/damping or fitted force multiplier. |

Independent TDT data exist, but they do **not** establish a whole-muscle runtime capacity. [Eldred et al. 2010, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/) reports transgenic wild-type-myosin TDT preparations at 15°C: maximum Ca-activated stress **37±3 mN/mm²** (n=21), resting stress **0.9±0.2 mN/mm²** (n=7), and unloaded shortening velocity **6.1±0.3 muscle lengths/s** (n=10), means±SE. The reported average **4,950 μm²** cross-section and 125-μm length describe a prepared bundle of 8–10 fibers, not the whole TTM. These values are recorded as independent evidence; no whole-muscle force or new runtime curve is inferred from them here.

The donor XML's force values (10.5807–303.877 μN) are optimized model parameters. They are not a verified anatomical PCSA table. The XNH skeletons' repeated display radius of 4,000 nm is also not a measured fiber cross-section. Thus uniform/default capacities remain explicit estimates; obtaining muscle-specific PCSA is still necessary. No capacity was selected by desired walking, jumping or food behavior.

## Remaining gaps

| Target or mechanism | Boundary retained |
|---|---|
| Generic `ltm` — 21 MN records | Femoral versus tibial origin remains unresolved. No `target_muscle="ltm"` route is invented; identified `ltm1-tibia` and `ltm2-femur` are implemented. |
| `Tergopleural/Pleural promotor` — 8 foreleg MN records | This family does not resolve the separate donor promotor paths. No silent broad alias. |
| T2/T3 promotor paths | Three source-pattern slots per middle/hind leg remain unsupported: tergopleural a/b and pleural promotor, 12 omitted slots total. Absence of a represented path does not mean biological absence. |
| Retro-tarsal-depressor fibers (`tarm1/tarm2`) | Their reversed origins/attachment direction are described in A17 but not represented by the main `Ta depressor` path; MN-to-subdivision mapping is unresolved. |
| Fiber-specific innervation | Representative paths, equal MN capacities, anterior/posterior allocations and TTM/STTM fractions are not resolved anatomical links. |
| Exact new articulation and apodeme geometry | Compliant femoral interface, collective claw hinge, cut planes, rigid apodeme and distal guides remain hypotheses/estimates. |
| Muscle physiology | No per-muscle PCSA/force calibration, measured optimal lengths, fatigue, neuromodulation or temperature-dependent kinetics. |
| Sensory feedback and full behavior | Native physical state is available, but this module adds no sensory neuron mapping, circuit, gait, ingestion, adhesion policy or behavior qualification. |
| Other appendages | Wings, halteres, proboscis, neck and abdomen belong to separate component models. No claim of completing the entire fly from this component. |

FlyMimic Appendix A.1 reports additional middle/hind anatomical reconstructions. Its original OpenSim-development repository returned 404 during research; this does not negate the public XNH geometry recovered above. Further anatomy may refine these explicit gaps without copying an imitation policy or fitting behavior outcomes.

## Historical component verification

The original study reported **PASS at the declared 10-μs physics resolution**, with MuJoCo 3.9/FlyGym 2.1. A prescribed pulse was used only in this constitutive-mechanics assay. The table records that study; it does not report a new execution of the packaged component check.

| Check | Result |
|---|---|
| Structural coverage | 134 prototype actuators/tendons, 460 sites; 90 scalar leg coordinates, including 24 additions; 12 exposed contact geometries |
| Historical binder, isolated model | `cns_body._connect_motor_units` accepted all records: **305 unique leg/jump MNs**, including all 73 newly supported target records; 419 bound actuators plus 14 unbound prototypes, native `nu=433`, `nq=90`. |
| Original cuticle preservation | Maximum reference-position discrepancy 4.20e-8 mm; original joint names/properties retained |
| Source registration and identity | nm→mm transforms, reflection, donor frame offsets, trace IDs and explicit estimate status checked; no invented CNS IDs |
| Capacity and duplication | Group fractions/capacities conserved; old combined sterno/tergo prototypes removed; duplicate import rejected |
| Force transmission | Native force decomposition, tendon Jacobian, velocity and power identity checked; finite-difference Jacobian error 6.67e-10 mm/rad |
| Femur reductor | Torque acts through the added compliant interface, not an unrelated existing leg joint |
| LTM transmission | LTM2 crosses femur–tibia; LTM1 does not. Both act through the distal tarsal route and pretarsal hinge. LF claw moment arm 0.0123642 mm/rad at neutral. |
| TTM semantics | LM/RM placement and exact `wing.tergotrochanteral_jump` key checked; dorsal thoracic origin |
| Contact API | A pair registered externally in a separate fixture produces 0.0675613 μN normal force on the new pretarsal geometry at 2-μm penetration |
| Quiet / activation | Zero activation with zero excitation; finite bounded states under a 120-ms stress trial; zero numerical warnings |
| 100→50 μs | Max final angle difference **0.00874232 rad**: finite but **not qualified** to the retained 0.003-rad tolerance |
| 10→5 μs | Max angle difference **0.00137081 rad**, activation difference **2.07553e-5**; tolerance passes |

The historical results establish software mechanics, registration invariants and the stated numerical limit. They do not validate anatomical accuracy, physiological force capacity, biological motion ranges, substrate grip, or normal and complete fly behavior.

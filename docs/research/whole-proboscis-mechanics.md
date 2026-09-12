# Whole proboscis and crop-entry mechanics

In the 2026-09-11 reconstruction, `add_proboscis_muscles(fly)` adds **35 native muscle/tendon prototypes**, **18 hinge/slide coordinates**, paired labella, seven elastic pharyngeal-wall patches, a salivary-valve patch, and an unpaired crop-entry constrictor. The 35 prototypes comprise 17 mouth targets on each side plus one crop-entry group. `ProboscisHydraulics` optionally supplies passive pressure/flow and pressure reaction loads. All metrics are declared estimates; this is not biological or whole-animal behavioral validation.

The [implementation](../../runtime/proboscis_muscles.py) and [M9 configuration](../../runtime/muscle9.json) are included in this package. The [mechanics check](../../tests/check_proboscis_muscles.py) is included in the package; the [M9 anatomy](mn9-anatomy.md) and [M9 dynamics](mn9-dynamics.md) notes describe the supporting anatomical and physiological evidence. [Head mechanics](whole-head-mechanics.md) compose with this component in either order. See [status](../status.md) and [roadmap](../roadmap.md) for package scope and remaining work.

All checks reported below are historical results from that reconstruction. They have not been rerun as package checks.

## Integration API

```python
from proboscis_muscles import add_proboscis_muscles, ProboscisHydraulics
records = add_proboscis_muscles(fly)  # before world attachment; existing legs permitted
```

The input remains the same NeuroMechFly object. Original body handles, transforms, leg joints, cameras and muscle-accessor conventions are retained. Internal structures are named native MuJoCo bodies, not invented entries in FlyGym's fixed `BodySegment` enumeration. The constructor adds no NMJ signals, action policy, target angles, timed motor inputs, flow trajectory, or sensory rule. Native controls and activation start at zero.

Each returned record retains `limb`, `side`, `target_muscle`/`muscle_target`, `semantic_muscle_key`, `local_actuator_name`, `actuator_name`, `local_tendon_name`, `tendon_name`, `force_uN`, `joint_names`, `sites`, positive fiber/tendon lengths, activation times, and provenance. `motor_neuron_ids=[]` and `mapping_status="unmapped"` indicate that the component supplies no neuron assignment. Names use the supplied `fly.name` as their world prefix.

Paired example:

```json
{
  "limb": "proboscis",
  "side": "right",
  "peripheral_target_side": "R",
  "peripheral_target_sides": ["R"],
  "peripheral_target_topology": "unilateral",
  "target_muscle": "m9",
  "semantic_muscle_key": "proboscis.m9",
  "local_actuator_name": "proboscis_muscle_right_m9",
  "actuator_name": "fly/proboscis_muscle_right_m9",
  "local_tendon_name": "proboscis_muscle_right_m9_tendon",
  "force_uN": 28.0
}
```

The prototype's side describes its physical location, not the soma side or innervation pattern of an eventual neuron. A demonstrated bilateral motor output can bind both corresponding prototypes; it does not justify doubling a prototype's capacity for each neuron.

CEM is a single physical organ group:

```json
{
  "limb": "gut",
  "side": "unpaired",
  "peripheral_target_side": null,
  "peripheral_target_sides": [],
  "peripheral_target_topology": "unpaired_organ_group",
  "target_muscle": "crop-entry muscles",
  "semantic_muscle_key": "gut.crop_entry_muscles",
  "local_actuator_name": "gut_crop_entry_muscle",
  "actuator_name": "fly/gut_crop_entry_muscle",
  "local_tendon_name": "gut_crop_entry_muscle_tendon",
  "force_uN": 28.0
}
```

The common splitter can divide this one capacity among supported CEM inputs. The four radial wall patches are a mechanical discretization, not four named muscles or a recovered circumferential cell partition.

**Labellar contact API:** the body and geom names are both `fly/proboscis_labellum_left` and `fly/proboscis_labellum_right`. Resolve IDs with `model.body(name).id` and `model.geom(name).id`; numeric IDs depend on the final compilation. `LABELLUM_GEOMS` exports the local geom names. M6/M7 records additionally expose qualified `contact_geom_names`. These geoms use the existing explicit-contact-pair convention (`contype=conaffinity=0`): both must be included in explicit food/ground contact pairs. A contact's actual lobe and contact point should select the corresponding taste surface; proximity to the old coarse haustellum is not proof of both-sided contact.

## Supported topology

Primary anatomy: [McKellar et al. 2020, eLife 54978](https://elifesciences.org/articles/54978), including the [publisher XML](https://raw.githubusercontent.com/elifesciences/elife-article-xml/master/articles/elife-54978-v2.xml) and visual inspection of Figures 6–9. McKellar separates eight positioning muscles from eight pharyngeal/salivary muscles; M3 has separately innervated lateral and medial fiber groups.

| Target on each side | Native path / structure | Source and evidence boundary |
|---|---|---|
| m1 | Posterior head wall to distal rostrum cuticle | Rostrum retractor; Fig. 7M–Q |
| m2D | Posterior head wall to distal rostrum cuticle | Accessory retractor; Fig. 7M–Q |
| m2V | Posterior head to anterior haustellum apodeme arm | Two-joint path; distal flexion moment is anatomical inference, not a demonstrated M2V haustellum phenotype; Fig. 8O–P |
| m3L/m3M | Anterior rostrum to haustellum | Separate lateral/medial fiber groups; Fig. 8. L here means lateral, not left |
| m4 | Rigid rostrum to free dorsal Y-apodeme arm | Haustellum extension; Fig. 8 |
| m9 | Ventral head to dorsal rostral apodeme arm | Rostrum protraction; Fig. 7K–Q; original configuration retained |
| m6 | Dorsal haustellum to labellar attachment | Extension hinge on each lobe; Fig. 6B and Fig. 9A–C |
| m7 | Dorsal haustellum to a different labellar attachment | Opening/abduction hinge on each lobe; Fig. 6B and Fig. 9A–C |
| m5, m8 | Haustellum cuticle to two local pharyngeal-wall patches | Fig. 6A identifies wall insertions; the older name “labral compressor” does not override this insertion evidence |
| m10, m11D, m11V, m12D, m12V | Rostrum cuticle to distinct serial wall patches | Fig. 6A and supplement 2; these patches approximate a complex continuous cavity |
| m13 | Cuticle to salivary-duct/pharynx valve patch | Proposed salivation valve, Fig. 6A; exact pressure-loading geometry unknown |

M1/M9 do not acquire direct haustellum actuators from their experimentally observed distal effects. M2Da/b and M4a/b motor labels do not create extra anatomical bundles or capacity.

**CEM:** [Yang et al. 2024, Figures 5b–c and 6](https://pmc.ncbi.nlm.nih.gov/articles/PMC11398398/) identify terminal innervation at the crop-duct/proventriculus junction and an effect on crop entry. This supports one unpaired constricting organ group. Its precise circular fiber partition, tissue shape and individual-neuron territory were not recovered. A closed, four-site circumferential tendon is an explicit reduced reconstruction; it is not a left/right organ split.

## Metric geometry and passive tissue

Native units are **mm, g, s; force µN; hinge torque nN·m**. Existing rostrum and haustellum frame offsets are `J=(0.430,0,-0.274)` and `H=(-0.371,0,-0.0196)` mm; `D=||H||=0.3715174 mm`. These are rig landmarks, not newly measured anatomical pivots. The two prior sagittal hinges and fourteen reaching MTUs retain their attachment geometry, force normalization and activation parameters.

M1/2 origins are estimated fractions of D from J on the posterior head wall; their insertion sites lie near H. M3 originates near anterior rostrum and crosses the distal hinge. M4 terminates on a surrogate dorsal apodeme landmark. Exact recipes are given in the [implementation](../../runtime/proboscis_muscles.py); no point was moved to reproduce an angle endpoint or behavioral movie.

**M9 provenance remains qualified.** Its source-image SHA, four pixel picks, similarity transform, right origin/insertion coordinates, L0=0.4146078712 mm, LT=0.040 mm, force and curves are imported from the original JSON. Left geometry is an explicit mirror. The older Fig. 7K distal landmark correspondence is unverified; visual readback suggests that pick may be the labellar dot. No re-registration or biological calibration is claimed.

**Labella:** the bundled haustellum mesh contains a fused distal outline. Its existing triangles are partitioned by centroid: distal when x>0.105 mm and z<−0.080 mm, then split by y sign; the rest stays on `c_haustellum`. All triangles and their reference positions are retained. This is an estimated segmentation of an existing scan, not a measured tissue boundary. Pivots `(0.130, ±0.045, −0.090)` mm in the haustellum each carry extension about local y and opening about mirrored local x. The M6/M7 endpoints implement the distinct attachment directions in Fig. 9. Open cut boundaries and convex collision hulls are approximations; no new decorative lobe primitives replace the scan.

**Pharyngeal wall/valve bodies:** eight small internal patches follow Fig. 6A's location/order. Each has a slide axis pointing toward its cuticular muscle origins. Paired tendons pull at different lateral positions on the same central patch, so forces add mechanically without copying neural activity. Their linear displacement is an estimated wall deformation mode, not a claim that a pharynx contains anatomical piston joints. Seven patches expand lumen sections; m13 changes a valve opening. Patches are diagnostic group 3, with wall area 0.00252 mm² and rest gap 0.012 mm.

**Crop entry:** four radial patches at a nominal 0.025 mm radius surround the anterior-abdominal junction estimate `(0.050,0,0.030)` mm in `c_abdomen12`. One closed spatial tendon traverses them and returns to its first point. Contraction shortens circumference and reduces the lumen axes. Independent patch displacement permits deformation under load; no radial trajectory is imposed.

| Parameter | Estimate / interpretation |
|---|---|
| Activation/deactivation | Native muscle parameters 10/40 ms throughout; a 10 µs physics step does not shorten these constants |
| Controls/activation | Each bounded in [0,1], separate native state per prototype |
| Force | 28 µN per side/group; M3L/M each 14 µN; CEM 28 µN for the whole unpaired group |
| Force provenance | Unmeasured capacities. Prior M9 assumption: PCSA 0.001 mm² × estimated 28 mN/mm² specific tension; [FlyMimic methods](https://arxiv.org/html/2509.06426v2), not proboscis force calibration |
| New fiber/tendon partition | L0=95%, LT=5% of reference path length; both strictly positive |
| Curves | Native estimated lmin=.5, lmax=1.6, vmax=1.5, fpmax=1.3, fvmax=1.2 |
| Reaching hinges | Existing estimated ranges; zero spring, 0.002 nN·m·s/rad damping |
| Labellar hinges | Extension −0.3…0.8 rad, opening −0.05…0.8 rad; spring .02 nN·m/rad, damping .0002 nN·m·s/rad |
| Wall/valve slides | −.004….025 mm; spring 2000 µN/mm, damping .1 µN·s/mm |
| Crop radial slides | −.015….005 mm about the nominal radius; same spring/damping |

Mechanical stops and spring material references are unfitted numerical/anatomical estimates, not motor commands. Wall elasticity has primary support as a return load opposing pharyngeal dilation; other new tissue compliances remain estimates. Tendons have no separate spring/damper; native muscles retain passive force–length tension. Native `lengthrange=LT+(0.25,1.25)*L0` supplies constitutive calibration, not motion targets.

### Mass accounting

All new mass is **reallocated**, not added on top of mass already present in the native model. With the default rig and compiler bound:

| Donor | Allocation |
|---|---|
| Haustellum, initially 8.09 µg | 1 µg each to m5/m8 walls; remaining 6.09 µg split equally between shaft and two lobes (2.03 µg each) |
| Rostrum, initially 18.2 µg | 1 µg each to m10/m11D/m11V/m12D/m12V/m13 patches; 12.2 µg remains |
| Abdomen12 | 1 µg per crop radial patch, 4 µg total transferred |

Distribution and changed segment inertias are estimates. Total compiled mass is conserved; original geometric surfaces are retained at the reference pose. No separate fluid mass is added to the rigid-body model. The hydraulic model does not update body inertia as food is transported.

## Pressure/flow API

After final world compilation:

```python
fluid = ProboscisHydraulics(model, fly_name=fly.name)
fluid.reset(data)  # explicitly declares an initially primed, liquid-filled circuit
# Each physical step, with liquid contact established externally:
report = fluid.advance(data, dt_s,
    inlet_pressure_pa=0.0 if wet_lobe_contact else None)
# Add to a freshly assembled external-force buffer; do not accumulate old loads.
data.qfrc_applied[:] += fluid.generalized_forces(data)
mujoco.mj_step(model, data)
```

`advance` reads actual wall/valve/crop qpos. It does not set qpos, controls or activation, and does not mutate the applied-force buffer. Optional crop and proventricular reservoir pressures default to 0 Pa gauge; `None` closes a boundary. Salivary pressure defaults to `None` and requires an external physiological boundary condition. A dry/non-contact mouth gets `inlet_pressure_pa=None`; contact detection is not invented inside the component.

The eight cells are m8 → m5 → m12V → m12D → m11V → m11D → m10 → crop-entry junction. A separate proventricular outlet branches after m10, and the salivary branch connects near m12V. This discretizes the continuous anatomy; it does not assign a required neural activation order.

Wall volume is `A*(rest_gap+q)`. Crop-entry volume is `pi*a*b*length`, with a and b obtained from opposing radial wall positions. Conductances use the Poiseuille circular/elliptical laws, current lumen dimensions, estimated duct lengths (0.05/0.10 mm) and viscosity (0.001 Pa·s). An estimated effective modulus of 10,000 Pa defines constant cell capacitances `C=V_reference/K`. With reference liquid volumes L and actual geometric volumes V:

```text
p = (L - V) / C
(C/dt + hydraulic_Laplacian) p_new = (L_old - V_new)/dt + boundary_pressure_terms
L_new = V_new + C*p_new
Q_boundary = G*(p_boundary - p_cell)
Q_mechanical = pressure * d(volume)/dq
```

The solve conserves reference liquid volume. Pressure forces are work-conjugate to wall and radial displacement; CEM changes both junction volume and outlet resistance. `generalized_forces` returns a fresh full-nv vector in native units. `report` includes pressure, geometric/reference liquid volumes, signed boundary flows, cumulative signed boundary volumes, conservation residual and nonnegative hydraulic dissipation. Positive boundary flow enters the circuit; crop delivery is minus its signed boundary flow.

**Limits:** this is a primed, effective-compressibility Newtonian circuit, not a dry-mouth filling, meniscus, cavitation, digestion or solute-advection model. Initial fluid is an explicit initial condition, not newly consumed food. Salivary gate pressure loading, full peristaltic esophageal musculature, true chamber shapes, measured fluid properties and changing body mass are not resolved. No flow is prescribed; hydraulic equilibrium without mechanical or boundary-pressure drive has zero flow. All reported flows are model predictions, not biological measurements.

## Historical neural eligibility and checks

The historical eligibility analysis used an anatomical motor map and its `peripheral_target_sides` field, rather than only its compatibility scalar. Bilateral MN5/MN10/MN11D/MN11V outputs can reach both physical paths. MN6–8 are ipsilateral. CEM's `unpaired_organ_group` has no fabricated L/R value. MN12D and MN13 sides remain unresolved; no MN12V assignment was supplied. All unknown MNx targets remain gaps.

The historical map, SHA-256 `c8bbfec04646edad8b6beb45301f45d78ec3869c12bbf407513b7d046dbd55eb`, yielded **48 pm motor rows eligible for 58 output-path matches, covering 29 of 35 prototypes**. The six unmatched prototypes are both sides of m12D/m12V/m13. Thirteen MNx rows lack targets, and six named MN12D/MN13 rows lack resolved sides. This is eligibility only; constructors/checks create no runtime neural connection.

The original [mechanics assay](../../tests/check_proboscis_muscles.py) reported **PASS** at 10 µs, with a 5 µs comparison; see the [historical provenance archive](../../results/README.md). Activation remains 10/40 ms. The former 100 µs assay step is too large for the newly resolved stiff walls and is not qualified.

The historical checks covered preserved body handles and leg parameters, exact mass conservation, native registration and bounds, bilateral geometry, independent activation, positive actual fiber lengths, source-consistent force directions, recoil, torque/velocity/power identities, and canonical bilateral/unpaired map joins. The complete reference surface before/after labellar partition agreed to **1.66e−8 mm** at mesh vertices. Minimum sampled fiber length: **0.01779295 mm**; largest reaching Jacobian finite-difference error: **1.95e−10 mm/rad**. M9 10/5 µs comparison: **7.38e−6 rad** and **2.53e−5 activation** maximum differences. Activation overrides below 1 ms are rejected so a physics timestep cannot silently become a muscle time constant.

The historical pressure check verified sealed-circuit conservation, zero equilibrium flow, pressure-volume work, dissipative pressure-driven flow, lower crop flow with a constricted gate, and coupled native mechanics at 10 µs. Maximum conservation residual: **1.29e−19 mm³**. No feeding endpoint, desired waveform or successful behavior was a test criterion. These checks did not establish integrated sensory control or whole-animal feeding behavior.

A historical composition check with the leg component compiled **134 leg + 35 mouth/crop + 24 head = 193 native prototypes**, with unique names and both condylar constraints. This established compilation compatibility, not whole-animal behavior. Flight muscles were not included.

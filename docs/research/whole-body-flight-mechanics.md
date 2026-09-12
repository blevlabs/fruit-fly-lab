# Whole-body flight and haltere mechanics

Scope: adult neural-to-muscle control of both wings and halteres, including eventual takeoff, aerodynamic support, steering and landing. Whole-animal flight remains unverified.

The numerical results below are historical simulation evidence from 2026-09-11; they were not rerun for this documentation revision. See [current package status](../status.md), the [research roadmap](../roadmap.md), and the [historical provenance archive](../../results/README.md) for the distinction between these studies and subsequent package checks.

**Bilateral flight/haltere mechanics are attached to NeuroMechFly, with explicit open-wing initial geometry and body-attached surface contact patches.** The historical body-integration check bound 66/83 flight-class motor IDs to separate states across 50 mapped paths; ten additional physical paths remained passive. It checked free-body coupling, six independent wing rotation modes and the mass/inertia budget. The collision repair at the end of this report supersedes the original overlapping folded reference. These studies did not verify whole-animal biological flight or central-neural operation.

Implementation: [flight_integration.py](../../runtime/flight_integration.py) and [flight_mechanics.py](../../runtime/flight_mechanics.py). The original check artifact is `check_flight_mechanics.py`; see the [historical provenance archive](../../results/README.md). The integration layer accepts canonical motor rows; it does not run the neural graph or infer neuronal identities. Inputs are physical state, binary spike events and physical parameters. No action choices, phase variables, prescribed frequencies, wing trajectories, desired angles, walking drive or behavior-fit parameters exist in it.

## What the biology requires

**Indirect power muscles are asynchronous.** DLM/DVM neural events maintain activation; delayed stretch activation and shortening deactivation alter force during physical deformation. Calcium affects power, not merely an on/off switch. The approximately 5 Hz neural versus approximately 200 Hz mechanical rates reported in Drosophila are observations, not simulation settings. A generic synchronous Hill actuator alone does not supply this stretch-history dependence. [Wang, Zhao & Swank, 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3207158/).

**Direct steering muscles are synchronous.** Their spike timing and twitch mechanics act through movable wing-hinge structures. Basalar b1/b2 manipulations affect flight control, but an experimentally inferred control role does not establish a mechanistic mapping from spikes to wing angles. The mechanical path requires delayed NMJ transmission, muscle activation, force–length/velocity response and physical tendon transmission. Native MuJoCo muscle mechanics can provide that constitutive layer once its anatomical and kinetic parameters exist. [Whitehead et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9750141/).

**Haltere mechanics is part of flight control.** Drosophila has an asynchronous hDVM power muscle and seven described direct steering muscles, hB1/hB2, hI1/hI2, hIII1/hIII2/hIII3. Their activity changes mechanosensory feedback. A prescribed phase signal or copied wing motion would bypass the haltere mechanics. [Dickerson et al., 2019](https://pubmed.ncbi.nlm.nih.gov/31607538/).

Mechanical coordination requires compliant thoracic links. Scutellar and sub-epimeral link manipulations support wing–wing and wing–haltere coupling in **soldier flies**; they supply a structural hypothesis, not Drosophila stiffness values. A physical linkage can produce synchronization without prescribing it. [Deora et al., 2021](https://elifesciences.org/articles/53824).

The neural side has a separate gap: electrical coupling among DLM motor neurons contributes to their distributed firing. MN5 crosses relative to its soma and supplies two DLM fibers. Chemical-connectome import and soma laterality alone cannot establish this physiology. No missing electrical synapses should be replaced by a neural or muscle clock. [Hürkey et al., 2023](https://www.nature.com/articles/s41586-023-06099-0).

## Source-model geometry and units

The geometry study used FlyGym source commit `38c8ec61034cd59bc5ba0de20688d4a3c0000d60`, its NeuroMechFly rig, FlyBody rig, original `fruitfly.xml`, joint/actuator/global YAML and composer. These are model properties, not measurements of the MaleCNS specimen.

| Asset, parent-thorax coordinates | Left / right values | Available / missing |
|---|---|---|
| NeuroMechFly wing pivot, mm | `[-.674, +/-.395, .081]` | Rigid wing meshes; mass `2.5e-6 g` each; no flight-muscle attachment sites or deformable thorax |
| NeuroMechFly haltere pivot, mm | `[-.806, +/-.214, -.149]` | Rigid meshes; mass `1.42e-6 g` each; no hDVM/steering tendons |
| FlyBody wing pivot, mm | `[-.0694, +/-.432, .091]` | Three wing hinge axes; source-model springs/actuators, not muscle-to-sclerite transmission |
| FlyBody haltere pivot, mm | `[-.386, +/-.247, -.0866]` | One model hinge; no bending-strain receptor mechanics |
| FlyBody wing fluid ellipsoid semi-axes, mm | `[.005, .551, 1.14]` | Reused in isolated fixture; rigid approximation |
| Fluid/inertia center in wing-local coordinates, mm | Left `[.263,-1.48,-.289]`; right `[-.263,1.48,.289]` | Source quaternions retained exactly in fixture |
| FlyBody wing inertial box | Same half-sizes/centers/orientations; mass `8e-6 g` each | Native box inertia, not a measured complete wing inertia tensor |

The two rigs use different thorax frames and masses; their coordinates are not interchangeable. The original FlyBody XML uses **cm–g–s**, while the FlyGym rig uses **mm–g–s**. Its composer comment documents length ×10 and hinge torque quantities ×100. The isolated fixture reads the original XML with stdlib XML parsing, multiplies lengths by 10, retains mass, and omits original control/spring definitions and meshes.

In mm–g–s: force is µN, torque and work are respectively nN·m and nJ, power is nW. `stress [Pa] × area [mm²] = force [µN]`. SI conversions: mm ×1e−3 → m; g ×1e−3 → kg; µN ×1e−6 → N; nN·m ×1e−9 → N·m.

**Air conversion finding:** the inspected FlyGym `mujoco_globals.yaml` retains source values density `.00128` and viscosity `.000185` after the cm-to-mm length conversion. These correspond to `1.28e−6 g/mm³` and `1.85e−5 g/(mm·s)`, respectively. Using the retained numbers in mm–g–s overstates density by 1000 and viscosity by 10. The finding applies to the inspected configuration; overrides in other configurations were not assessed. The isolated fixture explicitly uses converted values.

FlyBody's published fluid coefficients were optimized until hovering was stable. Those values and its learned locomotion controller are **not used**. Native ellipsoid geometry and force computation can be reused independently. [Vaxenburg et al., 2025](https://www.nature.com/articles/s41586-025-09029-4).

## Motor-row coverage at the historical annotation revision

Original annotation artifact: `body-annotations-male-cns-v1.0-minconf-0.5.feather` ([historical provenance archive](../../results/README.md)), SHA256 `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`. Selection is `superclass == vnc_motor` and `subclass in {wm,hm}`. It returns **67 wm + 16 hm = 83 rows**, not necessarily 83 uniquely identified peripheral muscles. Other motor classes and efferents are outside this count, not declared irrelevant.

All 83 raw `rootSide` entries remain null. The canonical map artifact, `malecns-motor-map.json` ([historical provenance archive](../../results/README.md)), resolves **82/83 peripheral sides and 72/83 named-target-or-family plus side rows**, using `peripheral_target_side` and `peripheral_side_method=curated_mancGroup_plus_MANC_soma_to_exit_relation`. This is cross-dataset anatomical homology, not a direct MaleCNS NMJ trace. Join by `semantic_muscle_key` plus `peripheral_target_side`; never substitute MANC IDs or the convenience `side` field. `807987` remains unresolved. Joined NT records cover all 83: 50 `consensus_nt=glutamate`, 33 `unclear`; no ground-truth NT values are present. Prediction disagreements remain provenance, not an instruction to make a muscle inhibitory.

Below, **A** identifies asynchronous muscle families, **S** identifies synchronous targets/families, **U** means unresolved peripheral target, and **J** means jump/accessory target coordinated with the leg assignment. The body integration binds the 26 A + 40 S rows through the canonical map; U/J rows are not guessed into a wing actuator. Names are literal annotation values; the detailed target crosswalk is recorded in the canonical motor map.

| Annotation type | Count | MaleCNS body IDs | Remaining correspondence |
|---|---:|---|---|
| DLMn a, b | 2 | 801295, 801970 | A: 801295 → left, 801970 → right; individual fiber allocation remains unresolved |
| DLMn c-f | 8 | 800718, 800890, 801895, 801998, 802544, 803013, 803048, 1050014552 | A: individual fiber mapping missing |
| DVMn 1a-c | 6 | 800056, 800412, 801816, 803129, 932322, 932796 | A: preserve separate neurons; no pooling by family |
| DVMn 2a, b | 4 | 803599, 803982, 807799, 807924 | A: individual fiber mapping missing |
| DVMn 3a, b | 4 | 805165, 906612, 932321, 1050045395 | A: individual fiber mapping missing |
| hDVM MN | 2 | 803215, 809085 | A: haltere power; DLM kinetics cannot be claimed as measured hDVM kinetics |
| b1 MN | 2 | 801310, 804301 | S: basalar |
| b2 MN | 2 | 801137, 801350 | S: basalar |
| b3 MN | 2 | 801292, 802120 | S: basalar |
| i1 MN | 2 | 800637, 801220 | S: axillary |
| i2 MN | 2 | 800381, 800573 | S: axillary |
| iii1 MN | 2 | 802835, 803100 | S: axillary |
| iii3 MN | 2 | 802327, 804107 | S: axillary |
| hg1 MN | 2 | 800241, 800917 | S: hinge target |
| hg2 MN | 2 | 803891, 804131 | S: hinge target |
| hg3 MN | 2 | 801021, 903852 | S: hinge target |
| hg4 MN | 2 | 800847, 800906 | S: hinge target |
| ps1 MN | 2 | 800743, 800928 | S: accessory target |
| ps2 MN | 2 | 802837, 803589 | S: accessory target |
| tp1 MN | 2 | 802028, 802315 | S: accessory target |
| tp2 MN | 2 | 800899, 801949 | S: accessory target |
| tpn MN | 2 | 801185, 801815 | S: accessory target |
| TTMn | 2 | 800146, 804642 | J: jump muscle, not asynchronous DLM |
| STTMm | 4 | 801391, 824223, 830847, 924167 | J: exact accessory-target interpretation pending |
| MNwm35 | 2 | 800190, 800606 | U |
| MNwm36 | 2 | 800184, 800696 | U |
| null type, wm | 1 | 807987 | U: matching note says biological variability mcns |
| hi1 MN | 2 | 805137, 908181 | S: haltere steering |
| hi2 MN | 4 | 802055, 807784, 808813, 809985 | S: multiplicity must be resolved, not deduplicated |
| hiii2 MN | 2 | 810460, 934019 | S: haltere steering |
| MNhm03 | 2 | 802659, 802806 | U |
| MNhm42 | 2 | 800474, 801933 | U |
| MNhm43 | 2 | 803310, 906003 | U |

Summary: 26 A, 40 S, 6 J, 11 U. Binding A/S rows supplies estimated mechanical paths, not a claim of measured individual-fiber anatomy. The canonical motor map records muscle/side aliases. DLM `a,b` crosses relative to soma; the cited map preserves that relation. Family motor units receive separate states and equal capacity shares pending individual-fiber measurements. MANC circuit work provides an anatomical identification route, not a muscle force law. [Cheong et al., 2026](https://elifesciences.org/articles/96084).

## Implemented constitutive equations

The existing NMJ schedules an end-of-step spike at its emission time plus delay; it cannot influence an earlier force interval. At release, excitation reservoir `x` increases by `g r`, efficacy `r` is multiplied by `1−U`; between releases, `dx/dt=−x/τx` and `dr/dt=(1−r)/τr`. Its bounded output is `u=x/(1+x)` evaluated at the interval midpoint. A release block suppresses new release; it does not erase existing muscle activation.

For fiber length `l` read from physical state, reference length `L`, dimensionless strain `e=l/L−1`, availability `a`, and two strain-history states:

```text
da/dt = (u − a)/τa
dz_fast/dt = (e − z_fast)/τ_fast
dz_slow/dt = (e − z_slow)/τ_slow
σ_SA = a E_SA (z_fast − z_slow)                    [Pa]
σ_active = max(0, a σ_iso + σ_SA)                  [Pa]
σ_passive = max(0, σ_pre + E_passive e)            [Pa]
T = A (σ_active + σ_passive)                      [µN, A in mm²]
P_fiber_to_mechanics = −T dl/dt                   [nW]
```

The code integrates each linear state exactly for held input, evaluates midpoint force, and rejects `|e| > .03`. Positive stretch produces a delayed positive transient, shortening a negative transient; constant length produces no sustained SA contribution. The linear kernel for a step `Δe` is `Δe[exp(−t/τ_slow)−exp(−t/τ_fast)]`. Its peak time follows from these material time constants; it is **not a wingbeat period**. There is no autonomous phase state, imposed sinusoid or negative-damping actuator.

This is a phenomenological small-strain material component, not a molecular cross-bridge model. It omits active instantaneous stiffness/phase-2 detail, temperature dependence, nonlinear large-strain behavior, ATP depletion and calcium concentration calibration. It has no separately calibrated Hill force–velocity curve: history dependence provides its limited dynamic force response. Positive mechanical work draws implicitly on muscle chemical energy; no metabolic budget is claimed. Passive prestress remains with no spikes, as physical tension, not motor drive.

| Parameter | Implemented value | Evidence classification / limitation |
|---|---:|---|
| `σ_iso` | 1400 Pa | Measured reference scale: Drosophila IFM net isometric stress `1.4±.2 mN/mm²`, skinned fibers, Swank solution, pCa 5, 15°C |
| `σ_pre` | 2800 Pa | Measured reference scale: passive stress `2.8±.4 mN/mm²` at prepared reference length; not intact resting preload |
| `E_passive` | 570000 Pa | Estimated secant from `5.7±.4 kPa` passive stretch stress / .01 strain; not independently measured elastic modulus |
| `E_SA` | 500000 Pa | Estimated scale; reference corrected SA stress `3.5±.5 kPa` after 1% stretch; not an identified dynamic modulus |
| `τ_fast`, `τ_slow` | 1 ms, 10 ms | Assumed kinetic shape; not extracted from a DLM/hDVM recording |
| `L`, `A` | 1 mm, .01 mm² | Assumed per-component dimensions; no individual fiber geometry identified |
| `τa` | 50 ms | Assumed normalized availability kinetics; not a calcium measurement |
| NMJ delay, decay, recovery | 1, 100, 100 ms | Assumed flight parameters using existing event implementation; M9 kinetics not silently reused |
| NMJ gain, depletion | .2, .2 | Assumed dimensionless values |
| Strain domain | ±3% | Explicit model ceiling, not demonstrated biological operating range |
| Wing geometry/mass | Values above | Inherited model estimates; original FlyBody inertial primitive |
| Air density, dynamic viscosity | 1.28 kg/m³; 1.85e−5 Pa·s | Converted source-model environment values; no thermal model |
| Native fluid coefficients | [.5, .25, 1.5, 1, 1] | MuJoCo defaults; unvalidated for this fly, no hover fitting |

The reference stress values and 1%-over-.5-ms assay conditions come from [Glasheen et al., 2017, Tables 2–3](https://pmc.ncbi.nlm.nih.gov/articles/PMC5814588/). They establish useful scales but do not calibrate this reduced law at intact-flight temperature or its assumed geometry.

## Physical requirements identified before body integration

This list records the requirements that motivated the subsequent implementation. The final section distinguishes what the new body attachment supplies from what remains unavailable.

1. **Exact terminal correspondence.** For every relevant body ID require dataset revision, target muscle/fiber, target side, mapping evidence, excitatory NMJ justification and provenance. Keep unresolved rows disconnected. Preserve distinct neurons sharing a target; combine their release at the correct shared fiber rather than summing arbitrary joint commands.
2. **Thorax and hinge transmission.** The follow-up fixture below supplies a reduced physical hypothesis for AP/DV deformation and one axillary transmission mode. Registration to segmented thorax/sclerite surfaces, bilateral independent wing modes, movable basalar/ax3/ax4 structures, contact/folding and calibrated elastic energies remain. One arbitrary hinge torque per named muscle does not meet this requirement.
3. **Force coupling.** For each muscle provide `origin_body`, `origin_xyz_mm`, `insertion_body`, `insertion_xyz_mm`, any wrap sites, `L`, tendon slack/compliance, PCSA and material parameters. Native spatial tendons supply `l(q)` and its Jacobian. Apply tensile force with `Q_m = −(∂l_m/∂q)^T T_m`; use a fixed-gain tendon force actuator for the custom IFM law and native muscle activation/force for synchronous steering. Do not also apply an angle servo, duplicate native activation, or treat DLM as a direct wing tendon.
4. **Haltere deformation and linkage.** Add hDVM plus direct-muscle attachment geometry, passive return elasticity, mass/inertia, lateral bending/torsion and thoracic linkage compliance. A rigid single hinge cannot expose realistic campaniform strain. In a body-rotating derivation `F_Coriolis=−2m Ω×v_relative`; native world-coordinate rigid-body dynamics already contains the corresponding inertial effects, so do not add this force again. Receptor strain must come from physical bending/load geometry, followed by receptor transduction and neural mapping. No hard-coded wing/haltere phase difference.
5. **Aerodynamic load and body flight.** Enable native ellipsoid fluid computation on actual moving wing bodies, not a lift-per-spike function. MuJoCo supplies geometry/velocity-dependent added-mass, drag, lift and viscous terms. The whole-body system must solve `M(q)q̈+C(q,q̇)+g(q)=ΣQ_m+Q_elastic+Q_air+Q_contact`. The initial isolated free-wing fixture has gravity zero and no thorax, root-body lift test or motor coupling; it verifies only the force path. Native fluid theory is stateless and omits wake-history effects. [MuJoCo fluid model](https://mujoco.readthedocs.io/en/stable/computation/fluid.html).
6. **Causal integration and qualification.** Receive actual motor events at their emission times, deliver due NMJ events, read current tendon lengths, update constitutive states, step physics, then transduce new physical sensory observations. Substep if necessary; compare 10 versus 5 µs for flight mechanics before choosing an integration rate. A reproducible continuation requires NMJ queues, muscle states, full physics state and time. Takeoff additionally needs jump/leg interaction, folded-wing clearance and contacts; steering/landing needs actual sensory feedback. These remain whole-animal dependencies.

Before selecting thoracic stiffness or SA gains to obtain sustained flapping, establish force/work under independent material assays and passive loading. Stretch activation does not automatically guarantee adequate self-excitation against aerodynamic losses; published analysis identifies a mismatch between some isolated-muscle estimates and flight-system dissipation. Do not resolve that mismatch by tuning until hovering looks right. [Pons, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10645510/).

## Historical constitutive and fluid checks

The original `check_flight_mechanics.py` result with MuJoCo 3.9.0 was **PASS**. The check exercised delayed event causality, release suppression, passive tension, opposite stretch/shortening effects, a delayed analytically predicted material-response peak, reset/domain validation, timestep convergence, native tendon force sign/virtual work, and finite free-wing dynamics with dissipative air versus zero force in vacuum. Synthetic irregular spikes and a laboratory length step are test fixtures only; the component produces no spike or trajectory input.

Observed peak: 2.55 ms versus analytic 2.55843 ms. Half-dt active-force discrepancy: `0.0002579706` relative (0.0257971%). Native initial fluid power for the specified translational initial condition: approximately `−1739.78 nW` per isolated wing; no prescribed trajectory is applied during its integration. These values are implementation checks, not physiological validation.

No claims of normal-fly behavior, neural flight initiation, sustainable wingbeats, lift sufficient for body weight, stable hover, maneuvering, takeoff/landing, correct wingbeat frequency, calibrated haltere sensing, or whole-animal motor completeness are justified. Most target sides are resolved in the cited map; the remaining integration limits are **individual power-fiber allocation, full hinge/haltere mechanics, specimen registration and physiological qualification**, followed by the neural/electrical and sensory dependencies above.

## Anatomical data and reduced physical transmission

### Public anatomical sources

| Primary source/data | Retrieved or inspected | What it resolves / does not resolve |
|---|---|---|
| [Lindsay, Sustar & Dickinson dataset](https://datadryad.org/dataset/doi:10.5061/dryad.23nm1), [public Zenodo mirror](https://zenodo.org/records/5000357) | `muscle_segmentation.zip`, 102,177,529 bytes, verified MD5 `49b440960e59d903422eab5e00ca5e5f`; 1,540 archive members | Actual confocal muscle stacks and named segmentations; no DLM segmentation, labeled joint surfaces, compliance or verified tendon-end landmarks found |
| [Melis, Siwanowicz & Dickinson, 2024, Fig. 1](https://www.nature.com/articles/s41586-024-07293-4/figures/1) | Original-resolution figure and publisher caption inspected | Notum/scutellar paths, PWP fulcrum and muscle-to-sclerite topology; a schematic, not metric joint coordinates |
| [Melis dataset](https://data.caltech.edu/records/aypcy-ck464) | File inventory and publisher data statement | Muscle/wing time series, Flynet data and robotic force data; no labeled hinge mesh archive listed. Learned wing-motion mappings were not used |
| [Walker et al., 2014](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1001823) | Figures/captions and supplement inventory | Blowfly time-resolved morphology: axillary/internal-arm and basalar attachments; supplements S1–S3 are rendered movies, not downloadable segmentation/landmark tables |
| [Walker & Chabokdast, four-bar thorax measurements](https://sicb.org/abstracts/amplification-and-transmission-of-muscle-strains-in-the-dipteran-flight-motor/) | Primary meeting abstract | Measured blowfly thoracic deformation supports a four-bar reduction; no link dimensions or machine-readable model supplied in the abstract |
| [Lau et al., 2014](https://doi.org/10.1109/TRO.2014.2333112), [author manuscript](https://dr.ntu.edu.sg/server/api/core/bitstreams/965dc82f-a5d9-42ab-906b-b8784d09ad84/content) | Full paper and Fig. 4 inspected | Explicit compliant rigid-link equations and physical flexure design, but for a robot; its motorized crank and robot dimensions/stiffness were not imported |
| [Jürgens et al., 2024 anatomy atlas](https://academic.oup.com/genetics/article/228/2/iyae129/7750380), [image collection](https://figshare.com/projects/An_anatomical_atlas_of_Drosophila_melanogaster_-_the_wildtype/218623) | Paper and data description | External SEM surface anatomy; does not identify internal attachment coordinates or elastic properties |

The public Zenodo mirror provides the archive with the published Dryad checksum. The mechanical fixture uses extracted constants and needs no archive download during a simulation.

### Metric extraction from segmented muscles

`phalloidin_stained_hemithorax.tif` contains 74 planes of 1024×1024 pixels. Its ImageJ metadata gives `unit=micron`, `spacing=2.97928140571728`, and TIFF X/Y resolution `1.32129`, yielding estimated voxel spacing `(0.756836, 0.756836, 2.979281) µm`. Named `combined_stack*.tiff` arrays share this grid but omit calibration tags. Calibration transfer is an explicit same-grid assumption. The RGBA layer exports contain 72-dpi display metadata and must not be used as physical calibration.

For each selected combined stack, collect nonzero voxels, convert coordinates to mm, take the leading covariance eigenvector, and average the lowest/highest 2% of projections to obtain two geometric end caps. These are **estimated muscle-belly ends**, not anatomically verified insertions or tendon endpoints. Brightfield and three orthographic point-cloud projections were visually inspected. Partial fields of view can truncate fibers.

| Segmentation | End-cap span, mm | Use |
|---|---:|---|
| DVM1 | .73210 | Adult size scale only |
| DVM2 | .64713 | Supports order of magnitude of the .65-mm model DV dimension |
| DVM3 | .54774 | Adult size scale only |
| i1 | .28278 | Estimated fiber length and line of action |
| i2 | .25264 | Estimated fiber length and line of action |
| b1 / b2 / b3 | .18219 / .23218 / .20201 | Available for subsequent basalar construction; not wired in this fixture |

The i1 distal/proximal end caps in image `(x,y,z)` mm are `[.37052,.39661,.07819]` and `[.15518,.57739,.10843]`; i2 caps are `[.45350,.40666,.08352]` and `[.46970,.65770,.10687]`. The model assumes `image x→AP`, `image y→−DV`, `stack z→lateral`, giving proximal-minus-distal vectors:

```text
i1: (-.21534, +.03024, -.18078) mm
i2: (+.01620, +.02335, -.25104) mm
```

Both distal ends are translated to the common ax1 insertion, and each proximal vector is extended by .03 mm along its own axis for an assumed tendon. This preserves the observed difference between the oblique i1 and near-vertical i2 directions. Translation to a common insertion follows the published target topology; the frame interpretation, tendon extension and attachment placement remain hypotheses. This is not registration to FlyBody, to the MaleCNS specimen, or to left/right ultrastructure.

### Constructed topology and constitutive mechanics

`ReducedThorax` owns one isolated MuJoCo model. Its four scutal bars form a sagittal rhombus: sternum at `(0,0,0)`, anterior/posterior corners at `(±.45,0,.325)`, and notum at `(0,0,.65)` mm. The upper ends connect to a vertically movable notum. DLM pulls between AP corners; DVM pulls between sternum and notum. Each bar has fixed length `b=sqrt(.45²+.325²)` mm. Consequently:

```text
l_DLM² + l_DVM² = 4 b²
dl_DLM/dl_DVM = −l_DVM/l_DLM
```

Antagonism follows from link geometry, not a sign-selected motor-to-wing torque. The rhombus is an explicit **scutal-compliance hypothesis**. It is not Walker's recovered four-bar geometry, a segmented scutum, or a claim that the real thorax is diamond-shaped. It collapses separate scutum/scutellum modes to one symmetric deformation mode.

For the hinge, ax1 is a rigid link pinned to the moving notum; its distal end is pin-connected to the medial arm of ax2. Ax2 carries the wing and rotates at a fixed PWP fulcrum. The notum→axillary path and PWP fulcrum come from the published topology; replacing contact grooves by permanent pins is an explicit small-displacement hypothesis. The ax4–canoe–ax3 path, basalare, clutch and folding contacts are absent.

Reference hinge coordinates, in the same hypothetical frame:

| Point/quantity | Value | Status |
|---|---|---|
| Notal/ax1 pin | `(.1,.25,.70)` mm | Estimated; moves with notum |
| PWP/ax2 pin | `(.1,.45,.65)` mm | Estimated fixed pleural support |
| Ax1/ax2 medial pin | `(.1,.35,.65)` mm | Estimated |
| Ax1 steering insertion | `(.1,.32,.665)` mm | Estimated common i1/i2 distal attachment |
| Ax2 medial arm | .10 mm | Estimated; sets geometric transmission |
| Ax1 link length | `sqrt(.10²+.05²)` mm | Derived from those pins |
| Wing span/chord/thickness | 2.28 / 1.102 / .010 mm | FlyBody primitive dimensions reoriented into this fixture's wing frame |
| Wing mass | `8e−6 g` | Existing FlyBody estimate; no additional hinge armature |
| Four scutal link masses | `2e−6 g` each | Assumed |
| Notum mass / ax1 and ax2-link masses | `1e−5 / 5e−8 g` each small link | Assumed |
| Rotational flexure stiffness/damping | .1 nN·m/rad; .0001 nN·m·s/rad | Assumed, independently exposed constructor parameters |
| DLM/DVM PCSA | .01 mm² each | Assumed representative fibers, not whole-muscle totals |
| DLM/DVM reference lengths | .90 / .65 mm | Physical reference diagonals, not angle targets |
| DLM/DVM passive prestress | 0 Pa | Assumed unloaded fixture reference; replaces prepared-fiber prestress, not fitted to motion |
| i1/i2 maximum force | 2.8 µN each | Assumed .0001-mm² PCSA × 28-kPa specific tension; neither measured for these muscles |
| i1/i2 native activation times | 1 / 4 ms | Estimated activation/deactivation |
| i1/i2 native force–length/velocity | `lmin=.5, lmax=1.6, vmax=10 L0/s, fpmax=1.3, fvmax=1.2` | Uncalibrated constitutive curves |
| i1/i2 NMJ delay/decay/recovery, gain/depletion | 1 / 2 / 100 ms; .2 / .2 | Estimated; native MuJoCo owns activation |

All rotational springs have a passive rest geometry and stored energy `U=½kq²`; none receives a desired-angle signal. Damping is `−c q̇`. DLM/DVM output physical tensile force through native spatial tendons. i1/i2 use native muscle actuators on ax1 tendons. Wing generalized force is zero when only the DLM force actuator is applied at reference geometry: its influence reaches the wing through constraint reactions. There is no DLM-to-wing torque gain or prescribed displacement law.

The model has seven generalized coordinates and three pin-connection equalities, giving one effective unconstrained mechanical mode in this planar reduction. Thus i1/i2 can load the transmission but cannot yet provide independent stroke, elevation, pitch and camber control. The full flight objective remains larger than this fixture.

Native fluid forces act on the moving wing ellipsoid. The isolated sternum is fixed and gravity is zero; aerodynamic lift of a free body is not tested. Geometry scale changes lengths, volume-scaled masses and area-scaled muscle force; the separately specified hinge stiffness/damping stays fixed. This is a parameter sensitivity option, not a biological allometric law.

### Ports, side evidence and use

```python
from flight_mechanics import ReducedThorax

fixture = ReducedThorax(dt_s=1e-5)
# Supply neural events at this interval's end.
fixture.step({"DLM": dlm_spike, "DVM": dvm_spike,
              "i1": i1_spike, "i2": i2_spike})
# Empty input means no new spikes; no default drive is generated.
fixture.step()
```

`DLM` and `DVM` remain **representative-fiber assay ports in ReducedThorax**, not allocations for all power motor neurons. The `flight_integration` layer below supplies the per-MN allocation separately. The named steering ports correspond to `wing.i1`/`wing.i2`; left-side use selects `peripheral_target_side=L`, i1 `801220` and i2 `800381` in the cited canonical map. DLM `801295→L` and `801970→R` preserve the documented crossing. Body ID `807987` remains unresolved.

The constructor rejects timesteps above 10 µs. End-of-step spikes retain the existing NMJ event convention; muscle states are updated before the next physical integration. `data.qpos/qvel` are current after `step`; endpoint tendon/site measurements require `mujoco.mj_forward` before reading them, as in the check. Reproducible continuation requires all native and NMJ/material states; the fixture has no automatic state persistence.

### Historical reduced-transmission checks

The expanded `check_flight_mechanics.py` passed with MuJoCo 3.9.0. These checks covered exact quiet state, release-block equivalence, geometric DLM/DVM antagonism, propagation through the pinned hinge, nonzero responses from each of the four spike ports, an opposing physical load, notum clamping, no native warnings, closure residual below `1e−5 mm`, geometry ±20%, hinge stiffness ×.5/×2, and 10-versus-5-µs convergence for **every** port.

Using only the check's three irregular synthetic events at .002/.007/.013 s, read at .020 s:

| Stimulated port | Notum displacement, mm | Wing displacement, rad | Half-dt relative discrepancy |
|---|---:|---:|---:|
| DLM | `8.47413e−5` | `−8.48254e−4` | .01815% |
| DVM | `−2.77510e−4` | `2.76714e−3` | .01065% |
| i1 | `−9.50366e−6` | `9.48478e−5` | .44194% |
| i2 | `−3.46649e−5` | `3.46909e−4` | 1.04773% |

An opposing `.002 nN·m` load reduces the DLM wing displacement magnitude to `8.19906e−4 rad`; clamping the notum reduces it to `2.93598e−8 rad`. Numerical pin compliance initially exceeded the check tolerance for steering activation; reducing the constraint stabilization time from 100 to 20 µs fixed that error. Muscle force, geometry, springs and spikes were not adjusted to obtain a wingbeat. Constraint stabilization is numerical and distinct from the declared physical hinge stiffness.

These are small deflections of a supported mechanical hypothesis, not a fitted flapping pattern. **No self-sustained oscillation, biological wingbeat, normal-fly steering, haltere coupling, takeoff or free flight was demonstrated.** Next physical coverage requires the remaining sclerites and basalar ligament path, independent wing modes, nonlinear contacts/folding, full power-fiber allocation, and haltere attachments/strain mechanics. The retrieved segmentation provides concrete muscle geometry for that continuation; the inspected public data did not identify all required joint/contact surfaces.

## Body integration: bilateral wings and halteres

This construction extends beyond `ReducedThorax`. `flight_integration.py` modifies a **newly constructed NeuroMechFly instance** before world attachment. Mesh geometry, wing/haltere masses and anatomical hinge locations are retained. Wing orientation is set once to the explicit open reference described below; haltere reference poses are retained. Every support is attached under `c_thorax` or its moving descendants. The dynamic update writes no `xfrc_applied`, `qfrc_applied`, wing coordinates, joint targets or flight-frequency setting.

### Mechanical construction

Each side has its own scutal rhombus and notum displacement, so the two wings are not constrained to match. The scutellar connection has a finite conservative bending energy `½k(hL−hR)²`, implemented by a native fixed tendon, plus an extensible spatial link. This is an estimated cuticular compliance, not equality of wing phase or frequency.

A two-axis pleural plate carries each PWP. The original wing body receives three translational coordinates constrained to that moving PWP and three independent rotations. Stroke/elevation/pitch axes are derived from the existing mesh's principal normal/chord/span directions. The kinematic constraint nullspace retains rank six across the two wings' rotation coordinates. Thus the three modes per wing are mechanically independent, unlike the one-mode prototype.

An articulated ax1 link joins the notum to ax2's medial wing-root arm. Basalare muscles act on a moving basalare, coupled by a tension-only elastic ligament to the radial spar. Ax3 has a local flexure at the wing's posterior root; ax4 moves relative to the notum and connects through an elastic approximation of the canoe to ax3 and the anal spar. The code has no muscle-to-wing-angle mapping. Forces reach the wing through tendon Jacobians, articulated supports, elastic connections and constraint reactions.

This retains the primary topology illustrated by [Melis et al., Fig. 1](https://www.nature.com/articles/s41586-024-07293-4/figures/1); pin joints and elastic links remain approximations of contact grooves, cuticle and ligaments. Historical nomenclature differs between studies. The source segmentation's `hg1–4` labels and canonical map keys are retained; no extra motor ID is assigned by equating a historical label with a different paper's label.

Pleurosternal paths connect the sternum to a movable pleural support; tergopleural paths connect that support to the mesonotum. These add force-dependent thoracic mechanics, not an inferred stabilization policy or a muscle-controlled angle target. The broad topology comes from the published anatomical reconstructions cited by [Miyan & Ewing](https://doi.org/10.1098/rstb.1985.0154). The newer tp1 physiological study also supports an indirect mechanical role, but its fitted control model is not imported. [Teoh et al., preprint 2025](https://pubmed.ncbi.nlm.nih.gov/41279419/).

Actual haltere bodies receive sweep, lateral bending and torsion coordinates. An asynchronous hDVM path pulls a small estimated basal apodeme. Seven anatomically described synchronous muscles receive separate geometric paths; only canonical named targets with known sides receive CNS bindings. Haltere apodeme geometry is a serial-homology hypothesis, not segmented haltere muscle data. A finite elastic sub-epimeral connection couples pleural motion to each haltere. Native free-body dynamics supplies inertial effects; no additional Coriolis force or periodic haltere signal is added. The power/control distinction and muscle inventory follow [Dickerson et al.](https://pubmed.ncbi.nlm.nih.gov/31607538/).

Native air geoms are attached to moving wing bodies and fitted to mesh extents; their coefficients remain MuJoCo defaults. They remain non-colliding. Dedicated surface patches now provide wing self/object/ground contact. Biological folding, clutch disengagement, detailed hinge mechanics and landing validation still require work. No full-fly takeoff or landing qualification is claimed.

### Reference geometry, parameters and mass

The body integration uses NeuroMechFly's thorax axes: +X anterior, +Y left, +Z dorsal. Image-derived belly-axis vectors are transformed as `(-image_x, -side*image_z, -image_y)`, with `side=+1` left and `−1` right. This is an explicit registration hypothesis: anterior/dorsal orientation comes from the brightfield view, while stack depth is treated as inward from the outer hemithorax. Geometry directions mirror as polar vectors; the fluid-geom quaternion uses a proper rotation. The earlier isolated fixture uses its own abstract coordinate frame and is not a body registration.

The additional segmented belly-axis vectors, in image x/y/z mm, are: iii1 `[-.14640,.17538,-.00093]`, iii3 `[-.03883,.08505,.04213]`, iii2_4 `[-.08098,.08648,-.01360]`, hg1 `[-.04010,.16858,.07786]`, hg2 `[.00570,.08632,.02622]`, hg3 `[.00080,.18939,.08736]`, and hg4 `[.01316,.09357,.03003]`. For these stacks, the lower image-y end cap was taken as distal, an anatomical-direction estimate that must be checked against tendon segmentation. The implementation contains only extracted constants and requires no archive download during a simulation.

| Quantity | Value / construction | Status |
|---|---|---|
| DLM a/b and c–f group PCSA, each side | .02 and .04 mm² | Estimated two- and four-fiber capacities; split across matched MNs |
| DVM1, DVM2, DVM3 PCSA, each side | .03, .02, .02 mm² | Estimated three-, two-, two-fiber capacities |
| Power material law | Existing IFM law; actual reference tendon length; zero unloaded prestress | Estimated kinetics/strain response; reference geometry is computed, not an angle command |
| Direct steering isometric capacity | 2.8 µN per named muscle/path | Estimated; equal matched-MN shares |
| Tergopleural complex capacity | 8.4 µN per side total | `tp1`, `tp2`, and canonical `tp` each receive one third; family/subdivision allocation remains estimated |
| hDVM PCSA | .0005 mm² per side | Assumed, no measured haltere force data |
| Haltere steering isometric capacity | .28 µN per named path | Assumed, separate MN shares for multiply innervated named targets |
| Haltere apodeme arm offsets | About 3–8 µm | Assumed small internal lever dimensions, not a stroke-amplitude target |
| Wing joint passive stiffness/damping | .01 nN·m/rad; .0001 nN·m·s/rad | Estimated, fixed constitutive values |
| Haltere passive stiffness/damping | .01 nN·m/rad; .00002 nN·m·s/rad | Estimated |
| Pleural / sclerite flexure stiffness | .3 / .03 nN·m/rad | Estimated |
| Basalare/scutellar spatial links | 20 µN/mm | Tension only beyond reference slack length |
| Canoe/anal links | 40 µN/mm | Estimated elastic transmission |
| Scutellar bending link | 20 µN/mm; .001 µN·s/mm | Finite differential-heave coupling |
| Sub-epimeral link | 2 µN/mm | Estimated, no prescribed haltere phase |
| Air | `density=1.28e−6`, `viscosity=1.85e−5` in mm–g–s | Converted source environmental values |

The new internal rigid bodies consume **40.4 µg from the existing 307 µg thorax**, leaving **266.6 µg** in the native thorax body. Nothing is silently added to total fly mass. The allocator subtracts each added body's mass, first moment and inertia about the thorax origin from the original thorax spatial inertia, then computes the residual thorax COM and principal inertia. It rejects nonpositive or triangle-inequality-violating residual inertia. Existing wing/haltere masses are retained separately.

The historical check verified total mass, COM and full inertia before/after the internal partition **at the same reference pose**. That reference is the explicit open-wing condition. Opening the original wings legitimately changes whole-animal COM/inertia relative to the folded pose; it does not change wing mass or body-local inertia. The internal partition adds no further change at that reference. FlyGym's standalone compiler floors tiny masses unless disabled; the builder sets `boundmass` and `boundinertia` to zero; world compilation must retain those zero floors.

### Exact integration contract

```python
from flight_integration import (
    add_flight_mechanics, bind_flight_motor_units, FlightMotorUnits,
    AIR_DENSITY, AIR_VISCOSITY,
)

# Existing leg/head/proboscis construction can precede this.
flight_records = add_flight_mechanics(fly)
flight_units, flight_linked_ids = bind_flight_motor_units(
    fly, flight_records, motor_map["motors"])
# Keep flight records out of the generic muscle-cloning binder.

# Attach fly to the ordinary world, then configure before compile:
world.mjcf_root.option.timestep = 1e-5
world.mjcf_root.option.density = AIR_DENSITY
world.mjcf_root.option.viscosity = AIR_VISCOSITY
world.mjcf_root.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
world.mjcf_root.option.iterations = 100
world.mjcf_root.option.tolerance = 1e-12
world.mjcf_root.compiler.fusestatic = False
world.mjcf_root.compiler.boundmass = 0
world.mjcf_root.compiler.boundinertia = 0
# Compile the world into model/data.
flight_bank = FlightMotorUnits(model, flight_units)

# Every PHYSICS interval; events follow flight_bank.ids order:
mujoco.mj_forward(model, data)  # current lengths before computing force
generic_motor_bank.advance(data, generic_events_at_end)
flight_bank.advance(data, flight_events_at_end, release_block=False)
mujoco.mj_step(model, data)
```

The generic bank clears `data.ctrl`; it must run **before** the flight bank, or restrict writes to its owned controls. FlightMotorUnits updates only its own channels. It calls neither `mj_step` nor a neural model.

For 100-µs neural intervals and 10-µs physics, the coupled solver performs ten physical substeps. A spike emitted at the neural interval's end is passed to the flight bank only on the **last** physical substep; the preceding nine receive zero new events. The existing NMJ queues it at that substep's end and applies transmission delay from there. Never repeat the same spike across all ten substeps. This retains causality even if the neural interval is calculated before the physical substeps.

`flight_bank.ids` contains sorted actual MaleCNS IDs. Binding uses only the supplied `semantic_muscle_key`, scalar `peripheral_target_side`, and supported-at-stated-resolution records. Every mapped MN receives its own NMJ and native activation or custom IFM state. Force/area is divided by the matched-MN count. `capacity_fraction` includes any physical-pool partition; `within_path_capacity_fraction` is the per-MN share of that path. Pool-capacity conservation is checked explicitly.

Unmapped geometry retains a **passive-only unit with `bodyId=None`**. It is excluded from `ids` and `linked`, but its passive material response remains part of physics. It is not a fictitious motor neuron. Native muscle activation and the custom IFM availability use estimated excitatory peripheral NMJ release; central NT predictions are not silently converted into peripheral inhibition.

`flight_bank.reset()` clears all NMJ/custom IFM states. Resetting a complete simulation also requires resetting the MuJoCo data, including native activation and controls; the component does not reset the rest of the animal. `last_forces` reports custom IFM force components by actuator name. Native steering force is in the corresponding `data.actuator_force`; joint names and actual tendon names are included in the records for kinematic/strain consumers. Campaniform transduction and receptor mapping require separate sensory models.

### Historical coverage and pre-collision checks

The isolated body-integration check used the cited canonical map and built **60 per-side semantic muscle paths**, **76 physical motor-unit records**, **66 mapped CNS IDs**, and **10 passive-only records**. Fifty paths have mapped motor IDs. The ten passive-only paths are bilateral `wing.iii2_4`, `haltere.hb1`, `haltere.hb2`, `haltere.hiii1`, and `haltere.hiii3`; no putative MN alias was substituted for them.

Of the 83 flight-class rows, the 17 not bound here comprise the 11 unresolved target/side rows already listed and the six `wing.tergotrochanteral_jump` rows. Those six belong to jump/leg force transmission rather than a wing actuator. Mechanical coverage does not determine which central neurons can participate in the neural graph.

The following numerical checkpoint predates the open-reference collision repair. Its scope was constituent mechanics, not collision-free initial geometry. The subsequent historical check repeated these properties with the open reference: all mapped paths, independent MN histories, release blocking, six independent wing rotation modes, reset, conserved capacity, mass/COM/inertia, free-root reaction, no injected body forces, native fluid contributions and passive falling.

| Check | Result |
|---|---|
| Maximum pin error over all mapped-path assays | `2.21841e−5 mm` (0.0222 µm) |
| Integrated-model 10 vs 5 µs discrepancy, DLM c–f | .02613% |
| i1 / b2 / hg3 | .03091% / .03149% / .04509% |
| hDVM / hi2 | .03283% / .05855% |
| No-air/no-gravity COM drift during internal i1 stimulation | `1.61089e−8 mm` |
| Residual linear / angular momentum | `1.48796e−9 g·mm/s` / `1.13726e−9 g·mm²/s` |
| External `xfrc_applied` / `qfrc_applied` | Both identically zero |
| Leg/proboscis compatibility at this stage | 132 leg + 35 proboscis + 60 flight paths; 161 q, 243 actuators |
| Combined-body random-input stress test | 100 ms finite, no native warnings; maximum pin error `2.58866e−5 mm`, maximum IFM strain `.000752162` |
| Other subsystem controls | Preserved by flight bank |

The random events are independent **test inputs only**. The mechanical component does not generate these events or translate sensory input into an action. The first body-integration trial exposed an invalid mass distribution concentrated at sclerite pivots; distributing each link's mass along its geometric extent fixed the large pin errors. This was a mechanics repair, not tuning to obtain flight behavior.

**Remaining scientific limits:** exact specimen registration, individual motor-fiber territories, nonlinear hinge contact/clutch/folding, wing deformation/wake history, haltere cuticular strain fields, unit-specific NMJ/contractile measurements and physiological validation remain incomplete. Numerical haltere attachments and internal thoracic compliance are explicit hypotheses. The code provides body-coupled forces and motor ports; these checks do not prove self-sustained biological wingbeats, adequate lift, flight stability, takeoff/landing or a normal fly's behavior. Central-neural integration requires separate evidence.

## Collision repair and explicit open-wing initial condition

### Failure reproduced and distinguished from source geometry

The original `l_wing`/`r_wing` visual meshes produced a native convex-hull overlap of **0.312990 mm** in the folded reference. The wing's PCA normal extent is **0.329147 mm**, half-extent **0.164574 mm**: this describes overall camber, not membrane thickness. MuJoCo uses a mesh's convex hull for collision, so a whole-wing collision geom fills air between curved surface regions. Its documented solution is multiple convex geoms attached to the same body. [MuJoCo collision geometry](https://mujoco.readthedocs.io/en/stable/).

There is also a real source-pose defect: exact edge/triangle testing of the unchanged mirrored folded meshes found **1,806 triangle-edge crossing events**, including repeated events along shared edges. Thus replacing the global hull alone cannot make the old folded reference collision-free. The source is also non-manifold; it is not a clean, closed thin solid. Neither force tuning nor excluding all wing collisions would resolve that anatomical inconsistency.

### Static reference repair

The model uses an explicit open-wing initial condition. Each original wing is **rigidly rotated about its unchanged anatomical hinge** so its principal span points laterally outward and its surface normal points dorsally. This is a computational starting condition, not a claimed measured resting pose or a biological folding mechanism. Source vertex/face data, camber, veins, mass and body-local inertia remain intact.

Let `B_source` be the proper principal-axis basis in thorax coordinates and `R_old` the old wing-body rotation. The initial rotation is:

```text
B_open,left  = diag( 1,  1, 1)
B_open,right = diag(-1, -1, 1)
R_initial = B_open B_sourceᵀ R_old
```

| Side | Hinge in thorax coordinates, mm | Initial body quaternion (w,x,y,z) |
|---|---|---|
| Left | `[-.674,.395,.081]` | `[.988700920675171,.0195600484864665,-.147708989770402,.0164301034775697]` |
| Right | `[-.674,-.395,.081]` | `[.988700920675171,-.0195600484864665,-.147708989770402,-.0164301034775697]` |

The builder recompiles this reference **before deriving any linkage attachment or muscle reference length**. It stores the original and initial quaternions, unchanged hinges and condition in `fly.flight_reference_pose`. No runtime update reads an angle target or reapplies this orientation. The dynamics API is unchanged.

The reoriented raw surfaces have **0.583230 mm lateral separation** between their Y-axis bounds. The historical integrated free-body construction had zero initial wing contacts after applying the patch-mask contract. The remaining deepest initial contact was non-wing, approximately **0.000474355 mm**; connected-socket adjacency and initial floor clearance require separate treatment. Tethered mode needs the same explicit adjacency treatment because native filtering has a world-welded-parent exception.

### Body-attached collision patches

Each wing's 1,999 source faces contains **1,932 unique nondegenerate triangles**. Each retained triangle receives one native convex triangular prism, formed by offsetting its vertices **±0.00025 mm** along that triangle's normal. The total **0.5 µm skin is an explicit numerical thickness estimate**; it is not inferred from global camber and does not claim measured membrane thickness. Actual wing membranes are much thinner than the overall wing's three-dimensional envelope. [Three-dimensional wing structure study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7115228/).

There are **1,932 contact geoms per wing**. No convex hull bridges between distinct source triangles. An attempted adaptive grouping provided negligible reduction and introduced up to 2 µm of conservative camber fill; it was removed in favor of exact per-triangle geometry. A microscopic prism is generated natively from six vertices, requiring no new geometry dependency or custom collision callback.

All patches:

- Are attached rigidly to the same actual wing body and have zero mass, preserving the established mass/inertia budget.
- Have `contype=1`, `conaffinity=7`, with the original wing's friction/contact parameters.
- Use group 5 and zero alpha. The unchanged visual meshes remain the render/ray surfaces; the existing vision mask excludes group 5.
- Retain the full source surface coverage; only duplicate faces and numerical degeneracies are omitted. Omitted degenerate area in this asset is zero.

The aerodynamic ellipsoid remains a separate non-colliding approximation. Its camber envelope is never used as collision thickness.

The surface-contact set incorporates the patch metadata:

```python
for metadata in fly.flight_contact_geometry.values():
    # Names are qualified as fly_name/geom_name.
    surfaces.difference_update(metadata["visual_geom_names"])
    surfaces.update(metadata["contact_geom_names"])
```

Adapt name qualification to the pre-attachment `MjSpec` as needed. The original visual geoms must not be re-enabled for contact after replacement. Wing records carry `contact_geometry_key` referring to the per-side metadata. `add_flight_mechanics`, motor binding, bank stepping and reset signatures remain unchanged.

### Historical contact-specific checks

The historical `check_wing_contacts()` reproduced the old folded convex-hull penetration, verified clear open-reference surfaces **with contact masks enabled**, checked byte-identical visual mesh vertex data and unchanged wing masses, and tested non-adjacent external spheres of radius **0.03 mm** and **0.7 mm**. A separate point-to-triangle calculation checked the collision distances against the raw visual surface, independently of the convex collider.

| Probe radius | Native gap | Raw-triangle gap | Result |
|---:|---:|---:|---|
| .03 mm | +.002 mm | approximately +.002250 mm | No contact and no force |
| .03 mm | −.001 mm | approximately −.000750 mm | Repulsive force, outward acceleration, decreasing penetration |
| .7 mm | +.002 mm | approximately +.002250 mm | No contact and no force |
| .7 mm | −.001 mm | approximately −.000750 mm | Repulsive force, outward acceleration, decreasing penetration |

The approximately **0.25 µm** difference is the declared outward skin, not a hidden global hull. The checks required the expected signed depth, agreement with raw geometry, correct force direction and increased separation after integration; a merely nonzero response is insufficient.

In the strengthened 10-ms passive load replay, the 1-µm indentation decreased to **0.910594 µm** for the small sphere and **0.908169 µm** for the food-sized sphere. These are approximately 89.4 and 91.8 nm of separation recovery, beyond CCD rounding. No neural drive or externally applied force was supplied during that replay.

The historical mass/COM/inertia regression compared the internal mass allocation with an otherwise identical fly in the **same open reference**. It did not require whole-fly inertia to remain equal to the old folded configuration. With zero mass/inertia floors set before all component construction, the resulting total fly mass was **0.0009997844 g**, matching the bare source under the same compiler settings.

The open-reference geometry changed numerical conditioning of the mixed-muscle stress case. With exactly the same seeded event times, maximum pin error was **0.114408 µm at 10 µs** and **0.068214 µm at 5 µs**, with a **0.067174%** generalized-displacement discrepancy. There were no warnings or contacts in that stress case. The previous 0.1-µm coarse-step gate was therefore revised explicitly: 10-µs pin error must stay below the **0.25-µm outward contact skin**, while the same-event 5-µs replay must remain below 0.1 µm and within 1% displacement difference. No forces, gains, stiffness, event pattern or time-dependent posture control was changed to satisfy this gate.

Historical final verification: the complete component/body suite passed, followed by the strengthened contact replay above. The updated integrated body retained 66 mapped flight IDs, 50 mapped paths and six independent wing rotation modes. All mapped-path pin errors remained below **0.048952 µm**; the largest sampled 10-versus-5-µs motor-response discrepancy was **0.100898%**. Composition at that stage included **134 leg + 35 proboscis + 60 flight paths**. These are historical implementation checks for the explicit initial condition, not biological flight measurements.

Biological wing folding/clutch mechanics, deformable membrane contact and natural flight remain unverified. The repair establishes a clear initial configuration and actual wing-surface collision forces; it does not turn that starting configuration into a behavior policy.

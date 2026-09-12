# MN9 replacement: reusable MuJoCo mechanics

Historical mechanics study: 2026-09-11, using **MuJoCo 3.9.0 and FlyGym 2.1.0**. The numerical checks below establish feasibility for a synthetic assay, not MN9 or adult-proboscis validation. They are not new checks of the public package.

For current package evidence, see [status](../status.md); planned work is in the [roadmap](../roadmap.md). Historical artifacts are indexed in the [results provenance archive](../../results/README.md).

**Finding:** native spatial tendons plus muscle actuators supply activation dynamics, active force–length–velocity behavior, passive muscle tension, and geometric force transmission. The inspected FlyMimic asset demonstrates these components for **15 left-front-leg muscles**, not the proboscis. Reuse the mechanics API; its fitted leg parameters, passive joint settings, and imitation policy do not establish an MN9 model. [MuJoCo muscle overview](https://mujoco.readthedocs.io/en/stable/modeling.html#muscle-actuators); [FlyGym musculoskeletal implementation](https://github.com/NeLy-EPFL/flygym/blob/main/src/flygym/compose/fly/musculoskeletal.py).

## Asset and provenance

The inspected `best_combined_arm_damping_stiff_cvt3.xml` was byte-identical to the [upstream XML](https://raw.githubusercontent.com/NeLy-EPFL/flygym/main/src/flygym/assets/model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml) retrieved on the study date. SHA-256: `04f6070d6733940357be005ca72c02ba0d9455538ff018da70c74de7458e9531`. FlyGym bundles the FlyMimic integration.

Direct XML extraction, **model settings rather than biological measurements**:

| Item | Inspected value / implication |
|---|---|
| Mechanics | 15 `general` actuators with `dyntype`, `gaintype`, `biastype` all `muscle`; 15 spatial tendons, each routed through 2–3 sites |
| Body constraints | Anchored thorax; 14 body joints, seven right-front-leg joint equalities; seven left-front-leg DoFs remain available |
| Proboscis | `Rostrum` and `Haustellum` bodies have no joints; no MN9-labelled actuator or proboscis muscle path |
| Activation | Every actual muscle overrides the default with `dynprm="0.0001 0.0004 ..."`; 0.1/0.4 ms base constants |
| Excitation | `ctrlrange="0.0001 1"`; zero requested control is clamped to a nonzero floor when control clamping is enabled |
| Force scale | Explicit positive `gainprm[2]`: **10.5807–303.877 μN** in FlyGym's documented mm–g–s convention; `scale=1` is therefore unused |
| Curve settings | `lmin=0`, `lmax=2`, `vmax=10 L0/s`, `fvmax=1.4`; `fpmax=0.0752654–4.08279` |
| Lengths | Explicit transmission endpoints collectively span 0.0715242–0.586674 mm; each muscle has its own normalized range |
| Passive joints | Defaults: stiffness 0.4, damping 0.02, armature 0.0005; individual spring references are also supplied |
| Physics | `dt=0.0001 s`, gravity `(0,0,-9801)`, default Euler integrator |
| Sensors | No native `<sensor>` block |

All rows above are independently inspectable in the [asset](https://github.com/NeLy-EPFL/flygym/blob/main/src/flygym/assets/model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml). `MusculoskeletalFly` loads this complete alternate body rather than adding muscles to the existing NeuroMechFly body. The XML references **71 mesh paths** whose meshes were absent from the inspected artifact set. The study parsed the asset with `MjSpec`; it did **not** compile or simulate the complete fly. [Loader source](https://github.com/NeLy-EPFL/flygym/blob/main/src/flygym/compose/fly/musculoskeletal.py).

Adult evidence boundary: FlyMimic uses adult *Drosophila* foreleg imaging to initialize anatomy, then optimizes uncertain parameters against kinematics. Its initial specific tension, **28 mN/mm²**, is an estimate between values from other adult muscle classes; it is not an MN9-muscle measurement. Default force curves were retained because measured *Drosophila* curves were unavailable. The work also uses imitation learning. None of those fitted parameters establishes adult proboscis mechanics or transmission. No larval measurements are imported here. [Özdil et al., methods §3.2, limitations, appendix A.4](https://arxiv.org/html/2509.06426v2).

## Attachments and exact construction API

Sites are fixed in their owning body's **local frame**. An origin on the proximal body and insertion on the moving body define a routed muscle–tendon path. A path crossing a joint produces a configuration-dependent moment arm automatically; placing both endpoints on the same rigid body cannot actuate that joint. Spatial paths may include intermediate sites, or `geom` wrapping around spheres/cylinders with an optional `sidesite`. Mesh contact geometry does not automatically become a tendon obstacle. Tendon `width` is visual, not muscle PCSA. [Spatial tendon reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html#tendon-spatial).

Minimal MJCF, with **synthetic** values matching the probe:

```xml
<!-- origin and insertion are sites on different bodies -->
<tendon>
  <spatial name="line"><site site="origin"/><site site="insertion"/></spatial>
</tendon>
<actuator>
  <muscle name="pull" tendon="line" gear="1"
          ctrllimited="true" ctrlrange="0 1"
          lengthrange="0.5 1.5" range="0.25 1.25"
          force="0.02" timeconst="0.01 0.04"
          lmin="0.5" lmax="1.6" vmax="1.5" fpmax="1.3" fvmax="1.2"/>
</actuator>
```

For the MuJoCo 3.9.0 native `MjSpec` interface, after creating the bodies:

```python
proximal.add_site(name="origin", pos=[0, 0.5, 0], size=[0.01, 0, 0])
distal.add_site(name="insertion", pos=[1, 0, 0], size=[0.01, 0, 0])
t = spec.add_tendon(name="line")
t.wrap_site("origin")
t.wrap_site("insertion")
# Optional routing APIs: t.wrap_geom("obstacle", "side_site"), t.wrap_pulley(2.0)
prm = [0.25, 1.25, 0.02, 200, 0.5, 1.6, 1.5, 1.3, 1.2, 0]
act = spec.add_actuator(
    name="pull", trntype=mj.mjtTrn.mjTRN_TENDON, target="line",
    gear=[1, 0, 0, 0, 0, 0], lengthrange=[0.5, 1.5],
    ctrllimited=mj.mjtLimited.mjLIMITED_TRUE, ctrlrange=[0, 1],
    dyntype=mj.mjtDyn.mjDYN_MUSCLE, dynprm=[0.01, 0.04, 0, 0, 0, 0, 0, 0, 0, 0],
    gaintype=mj.mjtGain.mjGAIN_MUSCLE, gainprm=prm,
    biastype=mj.mjtBias.mjBIAS_MUSCLE, biasprm=prm,
)
```

The low-level route compiled in the historical study. FlyGym's `add_actuator(..., "muscle")` is **unsupported**; its `"general"` route accepts these explicit parameters through `kwargs`. MuJoCo 3.9 exposes `set_to_muscle`, but the 3.9.0 Python binding rejected the two-element `timeconst` and `range` arguments; use MJCF or the verified explicit fields above. Original helper artifact: `flygym/utils/mjcf.py`, documented in the [provenance archive](../../results/README.md); [native model editing](https://mujoco.readthedocs.io/en/stable/programming/modeledit.html).

## Activation, lengths, and forces

`ctrl[i]` is dimensionless excitation, **not spikes, Hz, force, or an angle**. `act[model.actuator_actadr[i]]` is the separate evolving activation state. For `tausmooth=0`, with bounded activation, the native law is

$$
\dot a=(u-a)/\tau,\qquad
\tau=\begin{cases}
\tau_{act}(0.5+1.5a),&u>a\\
\tau_{deact}/(0.5+1.5a),&u\le a.
\end{cases}
$$

`timeconst` has two values in seconds; `tausmooth` has excitation units and smooths the switching. The native function clips its input excitation and uses clipped activation to calculate timescales; this does **not** guarantee bounded numerically integrated activation. The synthetic `<muscle>` compiled with `actlimited=False`. A separate one-step check using the asset's 0.1/0.4 ms constants and 0.1 ms Euler step produced **a=2 from a=0, u=1**. This is a numerical transfer warning, not a claim about a running FlyMimic policy. Choose resolution from kinetics and convergence; explicit `general` activation limits (`actlimited`, `actrange=[0,1]`) are a separate safeguard, not evidence that an unresolved timestep is adequate. [Versioned activation implementation](https://github.com/google-deepmind/mujoco/blob/3.9.0/src/engine/engine_util_misc.c#L882-L916).

For transmission limits \(\ell_- ,\ell_+\) and normalized muscle range \(r_-,r_+\):

$$
L_0=(\ell_+-\ell_-)/(r_+-r_-),\quad L_T=\ell_- -r_-L_0,\quad
L=(\ell-L_T)/L_0,\quad V=\dot\ell/(L_0v_{max}).
$$

`lengthrange` is dimensional **transmission** length; `range` is dimensionless muscle length divided by optimal fiber length. Neither is a target or runtime joint limit. The model treats the biological tendon length \(L_T\) as constant and omits pennation. For known \(L_0,L_T\), compute `range` from the first and last physical path lengths instead of adjusting it to obtain desired movement. [Length model](https://mujoco.readthedocs.io/en/stable/modeling.html#muscle-actuators).

`<compiler><lengthrange .../></compiler>` controls automatic range calculation (`mode="none|muscle|muscleuser|all"`, `useexisting`, `uselimit`). Automatic calculation uses isolated damped motion and omits contact, gravity and passive-force restrictions; it is not a measurement of anatomical ROM. Prefer an explicit, independently justified path envelope. Require increasing ranges and inspect inferred \(L_0>0\), \(L_T\ge0\). Applying the equations to the inspected `LFF_trochanter_extensor` gives **L0=0.127442 mm, LT=−0.023685 mm**. This fitted mapping works algebraically but cannot be interpreted literally as a nonnegative tendon length. [Range computation](https://mujoco.readthedocs.io/en/stable/modeling.html#length-range); [asset values](https://github.com/NeLy-EPFL/flygym/blob/main/src/flygym/assets/model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml).

The compiled arrays `actuator_gainprm[i]` and `actuator_biasprm[i]` each have ten slots; the first nine are

```text
[range_min, range_max, force, scale, lmin, lmax, vmax, fpmax, fvmax]
```

Native force is \(p=-F_0[aF_L(L)F_V(V)+F_P(L)]\); negative means pulling. Positive `force` explicitly supplies \(F_0\); negative selects `scale / actuator_acc0`, a model-inertia-dependent heuristic. Keep `gear=1` for a literal spatial muscle path; gear changes length, velocity and transmitted moment, not just strength. Independently evaluated with MuJoCo 3.9.0 in the historical study:

| Component | Native behavior |
|---|---|
| Active length | Piecewise quadratics; peak 1 at L=1; zero outside `[lmin,lmax]` and at its endpoints |
| Active velocity | Zero for V≤−1; `(V+1)^2` for −1<V≤0; `fvmax−(fvmax−1−V)^2/(fvmax−1)` until V=`fvmax−1`; then saturates at `fvmax` |
| Passive muscle | Zero at L≤1; increases with stretch even at a=0; no activation dependence |
| Passive curve detail | With b=(1+lmax)/2: `fpmax/2*((L−1)/(b−1))^2` for 1<L≤b; `fpmax*(0.5+(L−b)/(b−1))` above b |

**Documentation discrepancy:** the XML reference describes `fpmax` as passive force at `lmax`. The 3.9 source and evaluated binary instead give **1.5×fpmax at lmax**: for `F0=1, fpmax=1.3, lmax=1.6`, `mju_muscleBias(...) = −1.95`. The runnable check pins this behavior explicitly. Use the actual native evaluation when assessing passive loads. [3.9 force implementation](https://github.com/google-deepmind/mujoco/blob/3.9.0/src/engine/engine_util_misc.c#L757-L879); [XML parameter descriptions](https://mujoco.readthedocs.io/en/stable/XMLreference.html#actuator-muscle).

A spatial tendon's `stiffness`, `springlength`, `damping`, and `frictionloss` add separate mechanical effects; joint `stiffness`/`springref` adds another spring. These are not the actuator's passive muscle curve, and tendon stiffness does not by itself implement a compliant tendon in series with the native muscle. Avoid counting the same tissue elasticity twice. [Tendon properties](https://mujoco.readthedocs.io/en/stable/XMLreference.html#tendon-spatial).

## Instrumentation

Python signatures verified in the historical MuJoCo 3.9.0 study; parameter inputs are float64 arrays with the specified lengths:

```python
active_gain = mj.mju_muscleGain(length, velocity, lengthrange_2, acc0, gainprm_9)
passive = mj.mju_muscleBias(length, lengthrange_2, acc0, biasprm_9)
activation_derivative = mj.mju_muscleDynamics(ctrl, activation, dynprm_3)
# Without output clamps, actuator damping, or actearly:
force = activation * active_gain + passive
```

[Function reference](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#mju-musclegain). This force decomposition is exact for the probe, whose defaults contain none of those additions. If `actearly`, force clipping, tendon/joint actuator-force limits, or actuator damping is enabled, account for that before comparing the reconstructed force to applied torque.

| Quantity | Readback |
|---|---|
| Input and activation | `data.ctrl[i]`, `data.act[model.actuator_actadr[i]]`, `data.act_dot[...]`; actuator index is not necessarily activation index |
| Routed geometry | `data.ten_length[t]`, `data.ten_velocity[t]`, `data.site_xpos[site_id]` |
| Actuator geometry/force | `data.actuator_length[i]`, `data.actuator_velocity[i]`, `data.actuator_force[i]` |
| Applied generalized force | `data.qfrc_actuator`; rotational entries are torque, translational entries force |
| Other mechanical forces | `data.qfrc_passive` for passive joint/tendon terms; native muscle bias remains in actuator force |
| Named XML sensors | `actuatorpos`, `actuatorvel`, `actuatorfrc` with `actuator="..."`; `tendonpos`, `tendonvel` with `tendon="..."`; `jointpos`, `jointvel`, `jointactuatorfrc` with `joint="..."` |

[MuJoCo 3.9 data structures](https://mujoco.readthedocs.io/en/3.9.0/APIreference/APItypes.html#mjdata); [sensor definitions](https://mujoco.readthedocs.io/en/stable/XMLreference.html#sensor). Native sensors are numerical instruments, not identified biological sensory neurons.

`actuator_moment` was **sparse in the inspected MuJoCo 3.9.0 model**, not safely reshapeable to `(nu,nv)`. For actuator i:

```python
start, count = data.moment_rowadr[i], data.moment_rownnz[i]
cols = data.moment_colind[start:start + count]
r = data.actuator_moment[start:start + count]
tau_i = np.zeros(model.nv)
tau_i[cols] = r * data.actuator_force[i]
```

Here \(r=\partial\ell/\partial q\), so \(\tau=r p\); a positive-tension convention instead uses moment arm \(-r\). Sum contributions across muscles. Check power equality \(\tau^T\dot q=p\dot\ell\) when no downstream force clamping intervenes. Refresh with `mj_forward` after `mj_step` before comparing current state with derived outputs; record copies, not persistent views into mutable arrays. [Transmission equations](https://mujoco.readthedocs.io/en/stable/computation/index.html#actuation-model); [3.9 `mjData` layout](https://github.com/google-deepmind/mujoco/blob/3.9.0/include/mujoco/mjdata.h).

## Units resolved: millimeter–gram–second

**Primary authority explicitly establishes grams.** FlyGym's advanced composition tutorial specifies “millimeter and gram as base units” and identifies its native force unit as μN. The same page shows `gravity="0 0 -9810"` and the exact thorax `mass="0.000307"`. This declaration also appears in cell 14 of the versioned tutorial notebook. Thus the documented thorax mass is **0.000307 g = 0.307 mg = 3.07×10⁻⁷ kg**, not 0.000307 kg. [Official tutorial, model/units discussion](https://neuromechfly.org/tutorials/1b_advanced_model_composition/); [versioned primary notebook source](https://github.com/NeLy-EPFL/flygym/blob/v2.1.0/tutorials/1b_advanced_model_composition.ipynb).

The implementation passes rigging masses through without conversion; its mesh scale is 1000 and gravity is −9810 mm/s². That connects the documented convention to the inspected source. Original source artifacts: NeuroMechFly `rigging.yaml`, `mujoco_globals.yaml`, and `compose/fly/base_fly.py`; see the [historical provenance archive](../../results/README.md).

Derived native units:

| Quantity | Dimensional derivation / native unit |
|---|---|
| Force, including spatial-muscle `F0` | g·mm/s² = 10⁻³ kg × 10⁻³ m/s² = **10⁻⁶ N = 1 μN** |
| Hinge torque | μN·mm = **10⁻⁹ N·m = 1 nN·m** |
| Hinge transmission moment `∂length/∂q` | **mm/rad**; multiply by signed μN force to obtain native hinge torque |
| Inertia / hinge armature | g·mm² = 10⁻⁹ kg·m² |
| Tendon stiffness / damping | μN/mm / μN·s/mm = 10⁻³ N/m / 10⁻³ N·s/m |
| Hinge stiffness / damping | nN·m/rad / nN·m·s/rad |
| Energy / power | nJ / nW |
| Density corresponding to 1000 kg/m³ | 0.001 g/mm³ |

Sanity check from the exact thorax numbers: `0.000307 × 9810 = 3.01167` native force units, or **3.01167 μN** weight. A **10 μN** muscle therefore uses `force=10`; if its moment magnitude is **0.1 mm/rad**, it supplies **1 μN·mm = 1 nN·m** hinge torque. Entering 10 μN as `0.01` would underpower this model by **1000×**; entering it as `0.00001` would underpower it by **10⁶×**. A joint-transmission actuator instead has angular length and native torque output; its `force` parameter cannot be copied numerically to a spatial-tendon actuator.

The FlyMimic wrapper adopts its XML without rescaling. Under this FlyGym convention, the asset's summed explicit mass is **0.002494271478 g = 2.494271478 mg**; its fitted `F0` values consequently operate as μN. This interprets their units, not their biological accuracy or equivalence to another body model's mass distribution. [Wrapper](https://github.com/NeLy-EPFL/flygym/blob/main/src/flygym/compose/fly/musculoskeletal.py); [asset](https://github.com/NeLy-EPFL/flygym/blob/main/src/flygym/assets/model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml). The upstream OpenSim file retains `length_units=m` and `force_units=N` labels while supplying gravity about −9806.65 and the same mm-scale body offsets/mass numbers. Those labels alone are not a valid SI conversion receipt. [Original OpenSim file](https://github.com/gizemozd/FlyMimic/blob/main/flymimic/assets/models/opensim/best_combined.osim).

Converting physical SI parameters into this model requires **length ×1000, mass ×1000, inertia ×10⁹, force ×10⁶, torque ×10⁹, linear stiffness ×1000**, with seconds unchanged. Scale all body/site positions and `lengthrange`; mesh `scale="1000 1000 1000"` does not convert explicit attachments or inertial values. `vmax` is optimal lengths/second, not mm/s. Hinge state uses radians, irrespective of XML degree input settings. These are unit conversions, not biological estimates.

## Historical synthetic checks and remaining MN9 gaps

[muscle_mechanics_probe.py](../../research/muscle_mechanics_probe.py) contains the synthetic mechanical assay. It uses a synthetic 1 mm lever of mass 0.001 g, a fixed origin 0.5 mm from the hinge, `F0=0.02 μN`, `L0=1 mm`, `LT=0.25 mm`, and 10/40 ms activation constants. All geometry, kinetics and loads are synthetic. Excitation is one 100 ms pulse, starting at 20 ms; it is not a motor-neuron train or NMJ model. The hinge is unrestricted, with no gravity, contact, spring, target-angle servo or trained control. Only `ctrl` is assigned during stepping.

The following results were recorded in the original MuJoCo 3.9.0 study: **PASS**, zero numerical warnings. At 300 ms, rest angle **0**, stimulated angle **0.319352522 rad**, peak activation **0.9968096**, final activation **0.0285867**, peak tension **0.01193296 μN**, peak torque **0.00534321 nN·m**, final tendon length **0.9674958 mm**. Assertions check force–length endpoints, force–velocity shortening cutoff/lengthening saturation, passive stretch force, force decomposition, transmitted torque, power equality and six sensor readbacks. Passive stretch is checked by direct curve evaluation; it is zero along this particular driven trajectory. A separate in-memory rerun at half timestep changed the final angle by **4.08×10⁻¹⁰ rad**.

The intended biological chain still has these explicit gaps:

| Link | Supplied here | Still needed for adult MN9 |
|---|---|---|
| Spikes → NMJ excitation | No biological implementation | Identified motor-unit/muscle mapping; transmission delay, release/summation and any facilitation/depression evidence |
| Excitation → activation | Native generic ODE | Adult target-muscle activation/deactivation evidence; generic defaults are a cross-species modeling assumption |
| Activation → force → movement | Verified synthetic mechanics | Origin/insertion/routing, fiber/tendon lengths, PCSA or peak tension, velocity/passive curves, hinge axes, inertia and opposing tissue/muscle forces |
| Movement → sensory feedback | Accessible physical state | Identified adult sensory organ/neuron, transduction variable, sensitivity, adaptation, delay and circuit connection; joint angle alone is not an identified feedback pathway |

Measured anatomy, physiological measurements, fitted estimates and synthetic placeholders must remain separate in any subsequent model. This synthetic assay did not test an articulated proboscis or neural locomotion. The original artifact `muscle-mechanics-check.json` is identified in the [historical provenance archive](../../results/README.md); current package-check results belong in [status](../status.md).

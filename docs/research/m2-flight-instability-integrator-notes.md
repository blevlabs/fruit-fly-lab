# M2 flight instability: integrator evidence

This note records historical studies from September 2026. Reported checks and source hashes identify those studies; they are not new verification of the packaged software. See [current status](../status.md), the [research roadmap](../roadmap.md), and the [historical provenance archive](../../results/README.md).

Historical inspection: 2026-09-12 02:41 UTC. The initial study compiled the model without integrating a trajectory. Subsequent captured-event replays and matrix analyses are reported below. These are historical numerical results, not checks of the current packaged model.

**Diagnosis from the historical study:** an accurately solved, positive-definite implicit matrix transfers rapid notum closure-constraint acceleration into ax4 through the `hg1` muscle's local force–velocity tangent. The single-step tangent extrapolates far beyond the bounded native muscle force law. The original suspected rotational-bias omission is not supported as the cause of this shock; the analysis did not identify a reason to expect an `implicit` trajectory to remove this shock. The onset of the upstream thoracic oscillation and global trajectory convergence remain open. Mechanism report (original artifact `outputs/program/m2/instability-analysis/report.md`; [archive](../../results/README.md)), numerical results (original artifact `outputs/program/m2/instability-analysis/results.json`; [archive](../../results/README.md))

**Numerical conclusion:** common-state refinement supports **2.5 µs as a stability improvement** for the studied model. It does not establish global convergence or biological validity. The failure occurred in the original **10-µs** configuration; later numerical settings are documented in [current status](../status.md). Completed local comparison (original artifact `local-common-state-comparison/report.md`; [archive](../../results/README.md)).

## Original failure and whole-history comparisons

The ordinary coupled capture (original artifact `outputs/program/m2/instability-capture/receipt.json`; [archive](../../results/README.md)) begins at 0.09 s and fails at 0.69152 s. The original 10-µs same-event replay reproduces the failure; all 512 retained matched steps have exactly equal `qpos`, `qvel`, activation and controls. All four replay receipts affirm that the model is unchanged except for the specified numerical options, and use the same captured event hash `9ed2584eab7f2cb9ff0b81a7dd44e4343c302b0a92bfff8fea862550e2eb84d9`.

| Same-event replay, `implicitfast` | Recorded outcome | What it establishes |
|---|---|---|
| 10 µs (original artifact `outputs/program/m2/instability-replay-10us/receipt.json`; [archive](../../results/README.md)) | Same QACC failure after 60,152 steps at 0.69152 s | Exact reproduction of the retained coupled-capture trajectory and warning |
| 5 µs (original artifact `outputs/program/m2/instability-replay-5us/receipt.json`; [archive](../../results/README.md)) | 120,320 steps complete the captured horizon at 0.6916 s | Warning-free completion of this mechanical replay only |
| 2.5 µs (original artifact `outputs/program/m2/instability-replay-2p5us/receipt.json`; [archive](../../results/README.md)) | 240,640 steps complete the same horizon | Warning-free completion at a second smaller timestep; convergence not yet established |
| 1.25 µs (original artifact `outputs/program/m2/instability-replay-1p25us/receipt.json`; [archive](../../results/README.md)) | 481,280 steps complete the same horizon | Third stable replay; the three-level comparison does not establish monotone coupled convergence |

The final successful 10-µs step changes ax4 velocity from **1.637459 to −1552.287984 rad/s**. The following forward evaluation gives finite QACC **1.0037030×10¹¹ rad/s²**, above the unchanged **10¹⁰** warning threshold. At the shock, the effective matrix has minimum eigenvalue **1.00157×10⁻⁹**, diagonally scaled condition number **36.60**, and native-solve residual norm **9.79×10⁻¹³**. This rejects failed or indefinite factorization at that state.

Right-notum DOF 162 contributes approximately **99%** of the integrated ax4 acceleration through the inverse effective matrix. Its **297.849 µN** constraint reaction comes predominantly from anterior/posterior scutal closures. The `fly/flight_R_wing_hg1_mn800917` derivative provides the coupling: the implied focus-row tangent force is **−18.08 µN**, while the unchanged nonlinear muscle law evaluated at the predicted new velocity gives **−0.261645 µN**. The approximately **69-fold** excess is a tangent extrapolation, not a recorded increase in physiological motor force.

The local reconstruction is approximate, not an exact reproduction of every internal state: its final post-step velocity differs from the recorded vector by at most **1.27×10⁻¹¹**. Read-only algebraic counterfactuals restoring complete branch derivatives predict ax4 velocity **−1347.56 rad/s**; adding the complete bias derivative gives **−1347.55 rad/s**. Branch terms have a secondary effect; the additional bias effect is negligible and neither removes the shock. These calculations are not altered trajectories or candidate physiology. Analysis and reconstruction limits (original artifact `outputs/program/m2/instability-analysis/report.md`; [archive](../../results/README.md))

The completed **5-, 2.5- and 1.25-µs** comparison preserves all **2,655 spikes**, **437 motor IDs**, **6,016 neural intervals**, initial state, sources and physical parameters. It compares state errors on the same 512 times over **0.689045–0.6916 s**, with force/contact evaluations aligned separately. Its three stable trajectories **do not show uniformly diminishing coupled errors**. The earlier two-level comparison (original artifact `outputs/program/m2/step-comparison-5-2p5-evaluation-aligned/report.md`; [archive](../../results/README.md)) remains historical; the three-level report (original artifact `outputs/program/m2/step-comparison-stable-5-2p5-1p25/report.md`; [archive](../../results/README.md)) and results (original artifact `outputs/program/m2/step-comparison-stable-5-2p5-1p25/results.json`; [archive](../../results/README.md)) support this conclusion.

| Readout | 5→2.5 µs maximum error | 2.5→1.25 µs maximum error | Finer/coarser RMS error |
|---|---:|---:|---:|
| Right notum heave | 0.248 nm | 0.0884 nm | 0.304 |
| Right ax4 axial hinge | 1.44×10⁻⁵ rad | 8.08×10⁻⁶ rad | 0.640 |
| Left notum heave | 1.365 nm | 5.065 nm | 3.079 |
| Thorax world position | 3.019 µm | 3.519 µm | 1.165 |
| Thorax world orientation | 0.101° | 0.324° | 3.196 |
| Left DLM c–f tension | 0.02733 µN | 0.09406 µN | 2.794 |

The retained-tail right-ax4 raw-acceleration peaks approximately halve: **2.01726×10⁷ → 1.00297×10⁷ → 5.05675×10⁶ rad/s²**. This supports improvement of the original local failure mechanism, while the left/body errors above grow. Contact counts differ at every one of the **1,024** matched 2.5/1.25-µs force-evaluation samples: **112–116** versus **123–124**. Counts do not measure resultant contact-force error, but establish different contact histories. The 1.25-µs full-run maximum QACC is larger and lies before its retained tail; the receipt lacks that maximum's coordinate and time, so it must not be assigned angular units or attributed to the late ax4 event.

## Completed common-state episode, 1.5–1.52 s

The late capture and refinements were completed in the historical study. The capture starts from the retained **1.5-s coupled model state**, records **200 neural intervals and 100 binary spikes across 437 motor IDs**, and supplies the identical mechanical initial state and event bytes to **2.5-, 1.25- and 0.625-µs** replays. All finish at **1.52 s**. The same-2.5-µs replay reproduces all **1,024 retained states exactly**, including positions, velocities, activation and controls. The late event SHA-256 is `5062b4a6fc5fd81bdfbf8b481c122bf7c900b65a4edb0d7b27c79e6222e469a9`, distinct from the original failure-capture event hash. Results (original artifact `outputs/program/m2/local-common-state-comparison/results.json`; [archive](../../results/README.md))

Primary thorax, wing, head and force errors diminish at matched physical times, and scalar position errors decrease for **160 of 169** coordinates with coarser errors above 10⁻¹² in their own units. The nine exceptions remain recorded. Comparisons use **1,024 common state times over 1.5174425–1.52 s**, with force/contact evaluation starts aligned separately; no interpolation or phase adjustment is used.

| Local readout | 2.5→1.25 µs maximum error | 1.25→0.625 µs maximum error | Finer/coarser RMS error |
|---|---:|---:|---:|
| Right notum heave | 0.00608 nm | 0.00259 nm | 0.503 |
| Left notum heave | 0.0894 nm | 0.0387 nm | 0.298 |
| Right ax4 axial hinge | 1.40×10⁻⁶ rad | 6.78×10⁻⁷ rad | 0.488 |
| Thorax world position | 7.21 nm | 5.51 nm | 0.661 |
| Head roll | 0.003128 rad | 0.001001 rad | 0.418 |
| Left DLM c–f tension | 0.001808 µN | 0.000745 µN | 0.302 |

The contact audit reproduces every retained contact count. **Head–left-labellum recontact** occurs at **1.518930 / 1.5188625 / 1.518875625 s**, so successive onset-time differences decrease **67.5 → 13.125 µs**. **Right-hind tarsus1–ground** switching at the existing approximately **+1-µm margin** produces **50 / 73 / 117** entries and equal exits. Reconstructed entry forces are nonzero, so these events are not merely display bookkeeping; their count is not converged. Contact counts remain **128–130**. Every observed tail body pair was present at the initial 1.5-s state, although some disappeared and re-entered. This episode therefore covers established multi-contact motion with specified recontacts and margin transitions, not general landing or all contact regimes. Contact summary (original artifact `outputs/program/m2/local-common-state-comparison/contact-summary.json`; [archive](../../results/README.md)), scope and reconstruction limits (original artifact `outputs/program/m2/local-common-state-comparison/report.md`; [archive](../../results/README.md))

The strong common-state improvement is consistent with accumulated trajectory/contact-history sensitivity contributing to the earlier non-monotone whole-history errors. It does not uniquely locate every earlier difference or establish global trajectory convergence. The existing 2.5-µs coupled survival evidence and this local refinement support the bounded stability recommendation; another halving or finest-step coupled run is not required solely for that limited claim.

The **2.5-µs** conclusion is limited to numerical stability in the studied system. Global trajectory convergence, contact-event-count convergence, other loads and contact regimes, biological validation and the full physical repertoire remain open.

The common-state episode used the historical motor-map SHA-256 `d52ebe8d084b7c0f7617a787637544cf4620b977c6d37c504c4ef341a8afed98`. Changes to anatomical mappings are distinct from timestep changes and are not validated retroactively by these datasets.

## Original compiled-model inspection

The original artifact `canonical-viewer.log`, line 14 ([archive](../../results/README.md)), reports QACC at DOF 165, time 0.6915 s. The original compilation of `cns_body.make_body()` under MuJoCo **3.9.0** confirmed DOF 165 is `fly/flight_R_ax4_flexure_1`. The following observations and hashes belong to that original inspection, not to the later source changes or reconstructed failing snapshots.

- `flight_integration.py:193-218,360-381`: ax4 is a capsule with mass **5e-8 g**, radius **0.008 mm**, centerline length **0.035 mm**. Two hinge joints share its body: axial/span and normal. Each has stiffness **0.03**, damping **0.0001**, no armature, and no limit. Four `hg` muscle paths pull the ax4; the canoe ligament connects it to ax3.
- `cns_body.py:181-195`: the world uses `implicitfast`, timestep **10 µs**, 100 solver iterations, tolerance **1e-12**, and nonzero air density/viscosity.
- `cns_live.py:367-389` in the historical source: one neural step is 100 µs; its end event is delivered only at the final physical substep. Each substep advances ordinary NMJs, flight states and hydraulics, applies the resulting controls/pressure loads, calls `Simulation.step()`, then refreshes derived observables with `mj_forward`. `flygym/src/flygym/simulation.py:87-89` calls `mj_step` directly.
- `flight_integration.py:566-577` and `flight_mechanics.py:73-102`: asynchronous tension is calculated externally from sampled length and internal NMJ/activation/strain state, then held in `ctrl` through the step. The native actuator is a fixed-gain tendon motor. Neither implicit method differentiates this internal material evolution; its timestep dependence must be checked separately.

Original initial-pose compiled quantities (both sides agree to roundoff):

| Quantity | Axial hinge, R DOF 165 / L 152 | Normal hinge, R DOF 166 / L 153 |
|---|---:|---:|
| `M_ii`, g mm² | 1.52525547445e-12 | 2.49394890511e-11 |
| `h × damping / M_ii` | 655.627871 | 40.0970524 |
| `h² × stiffness / M_ii` | 1.96688361 | 0.120291157 |

The capsule principal inertias are **[9.62698905109e-12, 9.62698905109e-12, 1.52525547445e-12] g mm²**. The two-hinge off-diagonal entry is near roundoff at this pose. These ratios flag fast local scales; they are **not** a coupled-system stability criterion. `M_ii` is not the force-to-acceleration effective inertia when other coordinates and constraints move. Use the complete matrix and constraint solution at the pre-failure pose before drawing that conclusion. There were six contacts at the inspected initial pose; no motion was integrated.

## What the integrators include

MuJoCo 3.9.0 documents `implicit` as an implicit-in-velocity method. It includes smooth-force velocity derivatives subject to the inertia matrix's tree sparsity; constraint-force derivatives and cross-branch tendon damping terms are excluded. `implicitfast` additionally omits RNE Coriolis/centripetal derivatives and symmetrizes the derivative matrix. Existing joint damping is covered by both. Position stiffness is not thereby made implicit. The 3.9.0 special midpoint treatment is for eligible free bodies in vacuum: ax4 has hinge joints, and this world has air. The moving `stable` documentation already describes newer behavior, so use versioned documentation for this run. [MuJoCo 3.9.0 integration](https://mujoco.readthedocs.io/en/3.9.0/computation/index.html#numerical-integration)

The implementation calls `mjd_smooth_vel(..., flg_bias=1)` for `implicit`, versus `flg_bias=0` for `implicitfast`. The derivative routine adds native actuation and passive-force derivatives; the bias flag adds RNE derivatives. This distinction motivated the original rotational-derivative hypothesis; the completed counterfactual analysis above does not support it as the present failure mechanism. [Derivative implementation](https://github.com/google-deepmind/mujoco/blob/3.9.0/src/engine/engine_derivative.c#L1983-L2004)

`mj_step` computes `mj_forward` and checks `qacc` **before** selecting the integrator. The acceleration checker scans coordinates in order and stops at the first bad one; the reported DOF need not be the largest acceleration or the originating force. Raw `qacc` and the implicit step's actual velocity increment are different diagnostic quantities. [Forward/step implementation](https://github.com/google-deepmind/mujoco/blob/3.9.0/src/engine/engine_forward.c#L2075-L2105)

The check is `NaN` or magnitude above `mjMAXVAL`; the installed package reports **1e10**. Infinity also exceeds this bound. Preserve the original failure and all offending coordinates; do not raise this threshold or suppress the warning to declare a pass. [Value-check implementation](https://github.com/google-deepmind/mujoco/blob/3.9.0/src/engine/engine_util_misc.c#L1833-L1836)

## Original diagnostic proposal — superseded by the evidence above

The following sequence records the initial proposal. Exact capture/replay and the subsequent same-event/common-state refinements were completed at the scopes above. The proposed `implicitfast` / `implicit` trajectory comparison was not run: local bias-derivative evidence redirected the work to the completed unchanged-mechanics timestep study.

1. Reproduce the failure using the exact captured motor-event times, initial physical/internal states, source settings and original 10 µs stepping. Keep event capture separate from replay so a changed trajectory cannot change the neural input. First verify the original replay before interpreting alternatives.
2. Replay `implicitfast` and `implicit` at the same physical timestep, starting before the rise in acceleration. Keep anatomy, muscle gains, air, contact, solver, stimuli and state unchanged. Then compare a halved physical timestep for both if the first comparison exposes a difference or leaves the cause unresolved. Rebuild the existing NMJ/IFM clocks at the new timestep and preserve the physical event times. Record any event-grid quantization.
3. Compare common physical times: warning/failure, actual `qvel` and step increment, ax4 orientation, material-domain limits, tendon tension/length, contact/closure residuals and energy/work. Survival alone does not establish convergence. If only `implicit` survives and agrees upon refinement while the omitted bias contribution grows in the failing case, this supports a rotational integration diagnosis. If both fail around the same force/domain/constraint defect, repair that mechanism. These are diagnostic interpretations, not preset acceptance thresholds.

`RK4` is not the first comparison for this heavily damped, externally stepped material system. Native dynamics are reevaluated within RK4, but the studied Python IFM/hydraulic state would still be advanced just once and its output held. That would not provide a fourth-order check of the complete model. MuJoCo also warns that substantial velocity-dependent forces can favor the implicit methods. [MuJoCo 3.9.0 integration](https://mujoco.readthedocs.io/en/3.9.0/computation/index.html#numerical-integration)

## Original diagnostic readout checklist

This checklist records the original capture requirements, not a claim that every quantity was captured. The linked replay receipts, retained arrays and mechanism report specify what is available and the limits of the reconstruction.

- Identity: engine version, source/model/config hashes, integrator/timestep/solver flags, event stream, complete integration state, all internal NMJ/IFM/hydraulic states and physical source history. Retain warmstart accelerations for exact continuation; restore operations themselves can perturb warmstarts unless preserved. MuJoCo may reset state after an instability, so keep the pre-step snapshot. [State and diagnostics](https://mujoco.readthedocs.io/en/3.9.0/programming/simulation.html#state-and-control)
- Dynamics at interval start: `qpos`, `qvel`, `qacc`, `qacc_smooth`; all nonfinite/over-limit indices; ax4 joint/body IDs and world rotation. Store the last finite step and first failing forward evaluation separately. Following a successful step, record `(v_next-v_start)/h`; do not substitute raw `qacc` for this.
- Forces: `qfrc_passive`, `qfrc_bias`, `qfrc_actuator`, `qfrc_applied`, `qfrc_constraint`, `qfrc_smooth`, `xfrc_applied`; per-actuator force, activation, velocity, and tendon moment arms. In a copied state, separating `qfrc_bias(q,v)` from `qfrc_bias(q,0)` distinguishes velocity-dependent bias from gravity. Do not advance any internal state during that readout.
- Inertia: `M(q)`, its ax4/ancestor couplings, body principal inertias and armature. Solve the complete matrix against each force vector to attribute acceleration; raw force magnitudes alone mislead at tiny inertia. Check `M @ qacc - (qfrc_smooth + qfrc_constraint)` with absolute and scale-relative residuals.
- Constraints: contact body/geom names, distance, force and first appearance; equality/limit type and object IDs; `efc_pos`, `efc_vel`, `efc_force`, solver iterations/residuals. Cross-check whether constraint error or motor tension rises first.
- Work/domain: kinetic energy `0.5*v.T@M@v`, native potential energy, each generalized-force power `force@v`, and per-IFM strain/active/passive stress. The externally calculated IFM passive energy is not automatically part of native potential energy. An active, damped, gravity/contact/hydraulic system is not expected to conserve native energy alone.

## Original provenance and remaining gates

The original compiled-model inspection evaluated `make_body()`, `mj_forward`, and `mj_fullM(model, dense_M, data.qM)`. It did not integrate a trajectory. The source hashes below identify that numerical model, rather than the current package.

| Inspected source | SHA-256 |
|---|---|
| `cns_body.py` | `75cb74206da969a00be271ef5a5c13db3661d6cf231bf323f2867af2e08ae29f` |
| `flight_integration.py` | `a192cfa406bdf42dd99a211f2d3aac42bb11b0886b6bfb00b93806975a9a172d` |
| `flight_mechanics.py` | `5086bfe04b0b255b575c15dc6fb3de97e738e8fcb589270d3865bd3a5dd8e628` |
| `cns-model.json` | `4687a044525a71997e75774b8fefa8b039a51f948f3632068efd7bdb1ffff305` |
| `cns_live.py` | `52476199e3dbfa5024555449a5267f329b16016e270133845b2af7f1ebc850cd` |

The source hashes identify the recorded failure and its replays. Later source revisions are separate numerical experiments.

**Remaining scientific limits:** upstream thoracic-oscillation onset; global trajectory and contact-event-count convergence; other loads and contact regimes; and biological validation. The late common-state capture and local refinement are complete historical results supporting the bounded stability conclusion. Independent calibration of mass partition, compliance, muscle law and hinge geometry remains open.

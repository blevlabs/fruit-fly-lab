# Adult Drosophila MN9: transmission and activation dynamics

Historical literature review: 2026-09-11. Scope: adult *D. melanogaster* proboscis muscle 9. This report proposes a reduced model; it does not report new experimental or package-check results.

For current package evidence, see [status](../status.md); planned work is in the [roadmap](../roadmap.md). Historical artifacts are indexed in the [results provenance archive](../../results/README.md).

**Finding:** adult CM9 provides direct neuromuscular electrophysiology, including quantal transmission and short-term depression. It does **not** yet provide a complete measured spike-to-force transfer function. A delayed, stateful excitation–activation model is supportable as a reduced hypothesis; its activation and mechanical parameters cannot honestly be called calibrated from the evidence below.

## Identity and applicability

The CM9 preparation is anatomically relevant: Rawson et al. identify the bilateral E49-labelled neurons innervating cibarial muscle 9. Adult CM9 terminals stain for vesicular glutamate transporter, VGluT. This is a closer preparation than the extensively studied larval body-wall NMJ. [Rawson et al., 2012, Fig. 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC3350605/)

McKellar et al. identify one primary mn9 per side, with muscle 9 protracting the rostrum; its origin is the ventral head wall and its insertion is internal rostrum cuticle. Muscles 1, 2D and 2V contribute opposing retraction. This supports separate muscle forces and signed moment arms. It does not establish that removing MN9 activity alone supplies the force for retraction. [McKellar et al., 2020, Table 1 and Fig. 7](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316511/)

The protocol also notes a smaller, VGluT-negative innervation of CM9 whose function is unresolved. “One primary excitatory neuron” must not become “no other innervation.” [Eaton and Mahoney, 2017, procedure D](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413541/)

Do not confuse adult proboscis MN9 with larval abdominal MN9-Ib/U1, or the optic-lobe cell named Cm9. Measurements below concern adult proboscis preparations unless explicitly labelled otherwise.

## Direct quantitative evidence

Values following ± are reported mean ± SEM/SE, not population ranges. A stimulus setting is a controlled experimental input, not a measured physiological parameter. Quantal content is derived from electrical recordings, not a count of glutamate molecules.

| Quantity / record name | Units | Number or result | Preparation and status | Direct source |
|---|---|---|---|---|
| `stimulus_pulse_width`, `stimulus_voltage` | ms, V | 0.300 ms; 0.5–5 V | Dissected adult head; pharyngeal-nerve suction electrode and sharp CM9 electrode. Protocol settings; **not latency**. | [Eaton–Mahoney, procedure F](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413541/) |
| `EPSP_peak` | mV | 7 d: 9.03 ± 0.33; 35 d: 8.45 ± 0.36; 42 d: 12.75 ± 0.55 | Virgin female `w1118`; n = 13, 10, 16; measured. | [Mahoney et al., 2014, Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/) |
| `mEPSP_peak`, `quantal_content` | mV; quanta/event | 7 d: 1.12 ± 0.08; 8.55 ± 0.61 | Same cohort; miniature amplitude measured, quantal content derived. | [Mahoney 2014, Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/) |
| `train_frequency`, `train_duration` | Hz, s | 20/40 Hz; 15 s | 42 d CM9 depressed at 40 Hz, assessed at 7.5/15 s; 7 d lacked that depression; n = 8/condition. Electrical, **not force–frequency**. | [Mahoney 2014, Fig. 5](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/) |
| `paired_pulse_interval`, `PPR` | ms; ratio | 50 ms; depression on 1X diet, absent on 2X diet | 21 d virgin females; measured short-term effect. Numerical ratio/recovery constant not tabulated in text. | [Mahoney et al., 2016, Fig. 1G–H](https://pmc.ncbi.nlm.nih.gov/articles/PMC5012858/) |
| `EPSP_peak_by_diet` | mV | 1X: 3.46 ± 0.30; 2X: 1.65 ± 0.08 | 21 d `w1118`, n = 8/group; measured. | [Mahoney 2016, Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC5012858/) |
| `PhTx_concentration`, `homeostatic_timescale` | µM; min | 10 µM; EPSP minimum ~5 min, near-baseline recovery ~20 min | Adult ionotropic-glutamate-receptor challenge; slow compensation, not twitch relaxation. | [Mahoney 2014, Fig. 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/) |
| `tip_vmax`, `tip_vmean` | mm/s | 14 d: 5.516 ± 0.269, 3.666 ± 0.215; 42 d: 2.936 ± 0.205, 1.528 ± 0.101 | Virgin females, vehicle controls; n = 12/10; measured whole-PER trajectories, converted from µm/s. | [Kreko-Pierce et al., Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC5207075/) |
| `mEPSP_half_width` | **unit omitted** | 8.17 ± 0.76, wild type | Table 2 leaves its unit blank. Electrical timing lead; **do not silently assign ms or interpret as relaxation**. | [Kreko-Pierce, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC5207075/) |

The electrophysiology used modified HL3: **0.5 mM CaCl₂, 3 mM MgCl₂**, cold head dissection and a retracted, pinned proboscis tensioning CM9. A controlled recording-bath temperature is unspecified. [Mahoney 2016, Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC5012858/)

**Preparation discrepancy:** the 2017 protocol recipe instead lists **20 mM MgCl₂**, 0.5 mM CaCl₂ and pH 7.31. Preserve the recipe attached to each dataset; do not merge these into an assumed standard “adult saline.” [Eaton–Mahoney, Recipes](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413541/)

Paired pulses and prolonged trains in different cohorts constrain different phenomena. Absence of sustained train depression does not prove absence of paired-pulse depression. One depressed second response cannot identify a unique recovery constant. The baseline discrepancies also make a universal “9 mV per MN9 spike” calibration unjustified.

Rawson et al. observed roughly twofold diet-related changes in control CM9 EJP/quantal output without a significant corresponding change in extension speed; they interpret this in terms of a transmission safety factor. This argues against equating electrical amplitude with proportional movement or force. [Rawson 2012, Fig. 5 and discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC3350605/)

## Transmitter, receptors and calcium

**Transmitter:** adult CM9 VGluT staining supports glutamate. **Receptor class:** the adult philanthotoxin challenge above supports excitatory ionotropic glutamate receptors. The reviewed studies do not determine adult M9 receptor subunit mixture, binding/unbinding constants, desensitization kinetics or cleft glutamate concentration. Dlg staining is a postsynaptic scaffold marker, not a receptor-subtype assay. Do not insert an acetylcholine/AChE model or silently import larval GluRIIA/GluRIIB kinetics.

**Neuronal calcium is available; muscle calcium calibration is not.** Gordon and Scott measured G-CaMP in the adult E49 motor-neuron **cell body**: 100 mM sucrose or 200 mM maltose produced roughly 50% fluorescence increases. In simultaneous movement recordings, motion could itself produce changes up to 10%. These are relative reporter signals, not terminal release probability, muscle calcium concentration or a spike-count calibration. [Gordon and Scott, 2009, Fig. 6 and imaging methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC2650400/)

The FLIES preparation demonstrates simultaneous adult E49-soma GCaMP3.0 imaging and PER, providing an experimental route rather than a measured muscle calcium transient. [Yoshihara, 2012, Fig. 9](https://pmc.ncbi.nlm.nih.gov/articles/PMC3466644/)

Kreko-Pierce et al. link adult movement and S107 effects to FK506-BP2/RyR regulation, without measuring spike-triggered M9 [Ca²⁺] or calcium-to-force kinetics. Their PER methods specify **9.2 Hz** video, approximately **109 ms/frame**, despite describing high-speed imaging. This cannot resolve millisecond excitation–contraction delays. [Kreko-Pierce, Results and PER methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC5207075/)

McKellar's motor-activation experiments used **2 s constant light**, filmed at **30 Hz**; separate spontaneous-extension synchrotron recordings used **3000 fps**. Neither is paired MN9-spike/force recording. Exposure duration and frame interval are not muscle activation constants. [McKellar 2020, Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316511/)

## Parameters still missing

“Not found” means not established by the primary sources reviewed, not that no measurement exists anywhere. No numerical biological default is assigned to these gaps.

| Parameter | Units | Adult MN9/M9 constraint available here | Needed measurement or permissible interpretation |
|---|---|---|---|
| `d_conduction` | ms | Not found | MN9 spike at a defined upstream site versus terminal arrival; report path and temperature. Connectome edge delay is not this quantity. |
| `d_NMJ` | ms | Not found | Terminal action potential to EPSP onset. Stimulator-to-EPSP delay also includes distal conduction and stimulation timing. |
| `d_EC` | ms | Not found | Depolarization to calcium/force onset; distinguish force onset from movement against a load. |
| `tau_exc` | ms | No fitted adult M9 value; electrical traces and unit-ambiguous half-width are leads | Fit waveforms after verifying units. Half-width is not generally an exponential time constant. |
| `tau_activation`, `tau_relaxation`, `t_peak_twitch` | ms | Not found for isolated adult M9 | Spike-controlled, load-controlled twitch/calcium/force recordings including offset. PER duration conflates neural drive, antagonists and mechanics. |
| `g_spike` | dimensionless/event | Unidentified excitation-to-activation scale | Fit against force/calcium evidence; EPSP millivolts alone cannot identify it. |
| `U_depression`, `tau_recovery` | dimensionless; ms or s | Paired-pulse/train evidence; no uniquely fitted pair | Multiple interpulse intervals and post-train recovery within a specified cohort. |
| `f_half_force`, `f_fusion` | Hz | Not found | Adult M9 force–frequency/tetanus measurements; 20/40 Hz electrical tests do not supply these. |
| `F_max`, single-spike force | N or µN | Not found | Calibrated tension at known length/load; tip force requires moment-arm conversion. |
| `l_opt`, `v_max`, `f_length`, `f_velocity` | m; optimal-lengths/s; dimensionless curves | No adult M9 dynamic measurements found | Geometry and length/load-controlled measurements. Tip speed is not fibre shortening velocity. |
| `F_passive`, damping | N; N·s/m | Not found | Passive force–length/velocity measurements with activation excluded. |
| resting/evoked `[Ca2+]`, clearance, calcium sensitivity | mol/L; s⁻¹; mol/L | Not found for adult M9 | Calibrated muscle indicator and force; bath [Ca²⁺] and neuronal ΔF/F cannot substitute. |
| facilitation or fatigue constants | ms–s; dimensionless | Not separately identified | Separate presynaptic plasticity, receptor desensitization and muscle fatigue experimentally. |

## Minimal stateful model recommendation

This is an **original reduced-model proposal**, not an equation fitted by the cited authors. Use individual left/right MN9 spike times and three scalar states per muscle:

- `x ∈ [0,1]`: available synaptic efficacy; phenomenological, not measured vesicle count.
- `e ≥ 0`: dimensionless effective postsynaptic excitation; lumps release/receptor/depolarization effects.
- `a ∈ [0,1]`: dimensionless muscle activation supplied to a separate force law.

Deliver each spike at `t_k + d`, where `d = d_conduction + d_NMJ`. Keep both delays in provenance even if only their sum is identifiable. Between events:

```text
dx/dt = (1 - x) / tau_recovery
de/dt = -e / tau_exc
da/dt = (e / (1 + e) - a) / tau_activation
```

At each event, using the pre-event value of `x`:

```text
e <- e + g_spike * x
x <- (1 - U_depression) * x
```

Initialize `x = 1`, `e = 0`, `a = 0`. Require positive time constants, nonnegative gain/delay and `0 ≤ U_depression ≤ 1`. All parameters remain **unfitted estimates until measured**; state bounds and normalization are definitions. No parameter should be selected to make the proboscis extend or withdraw.

The saturation `e/(1+e)` is a minimal mathematical assumption whose scale is absorbed into `g_spike`. It is not a measured Hill curve, receptor occupancy or calcium affinity. Activation stays continuous across spikes and relaxes as excitation clears. One activation time constant is the initial hypothesis; separate rise/fall constants require supporting waveforms. A separately measured excitation–contraction dead time can later be added without disguising it as conduction.

The efficacy state captures the experimentally observed possibility of short-term depression; the evidence does not establish a uniquely vesicle-depletion mechanism. For baseline-corrected excitation increments, this model predicts:

```text
PPR(Delta) = 1 - U_depression * exp(-Delta / tau_recovery)
```

One interval cannot identify both parameters. `U_depression = 0` is the explicit no-depression null model, evaluated against the relevant cohort rather than assumed universal. Add no separate facilitation, calcium-store, fatigue or homeostatic controller without constraints. Minute-scale toxin compensation does not determine millisecond recovery.

Activation must produce **force**, followed by movement through body physics:

```text
F = a * F_max * f_length(l) * f_velocity(dl/dt) + F_passive(l, dl/dt)
joint_torque = -F * (dl/djoint_angle)
```

The sign follows virtual work for a tensile muscle along its attachment geometry. These equations specify an interface, not a calibrated force law. `F_max`, force curves, passive properties and moment arms remain independent evidence requirements. Retraction needs opposing muscle activity and/or measured passive mechanics; declining activation is not a retraction command.

Preserve the simulation timestamp of every spike: averaged rates or counts alone lose interpulse spacing. Numerical batching must preserve those timestamps. The excitation model must not depend on food identity, desired behavior or desired angle.

## Sensory-feedback boundary

An identified adult contact pathway exists: labellar bristle mechanosensory neurons require NOMPC. Deflection evokes receptor currents after approximately **3 ms**; half-response displacement was **4.0 ± 0.5 µm**, n = 8. This is **sensory transduction**, not MN9 NMJ delay. The study's GMR18B07 motor recordings most likely concern labellar spreading and use a driver that is not MN9-specific; they do not establish a rostrum-angle-to-MN9 proprioceptive loop. [Zhou et al., 2019, Figs. 2 and 6](https://pmc.ncbi.nlm.nih.gov/articles/PMC6531006/)

Movement can expose a separately implemented, identified contact sensor to food, with sensory spikes returning through supported neural pathways. A complete MN9 proprioceptive feedback model remains an additional research requirement. Do not supply a synthetic angle-error reflex to close that gap.

## Next measurements

1. Fix cohort and saline/temperature. Obtain stimulus-aligned CM9 electrical traces, paired pulses at multiple intervals, trains and recovery. Fit transmission before mechanical output.
2. Record isolated or geometrically resolved M9 twitch force and muscle calcium alongside nerve/muscle electrical timing. Test single spikes and several train frequencies, lengths and loads; estimate delay, activation, force curves and passive response separately.
3. Validate held-out spike trains and loads. Equal mean rates with different spike timing remain distinct when the fitted transmission model predicts it. Failure to reproduce behavior is a model result, not a reason to retune toward an intended outcome.

Adult leg or jump-muscle values can inform a separately labelled sensitivity analysis, but are not M9 measurements. Larval excitation–contraction studies contain useful force/calcium experiments **in larvae**; their constants are not adopted here. No mammalian or cross-species kinetic values are adopted. [Ormerod et al., larval preparation](https://pmc.ncbi.nlm.nih.gov/articles/PMC9044916/)

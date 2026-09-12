# Whole-CNS neural physiology: Pugliese rate dynamics versus current Eon LIF

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**Recommendation: keep the current whole-MaleCNS neural model while completing the actual sensory–body feedback already under implementation. Pugliese provides a useful alternative neural approximation, but switching to it would not complete the missing central physiology or establish natural whole-animal coordination.** Its strongest additional modeling ingredient is anatomy-dependent excitability. That ingredient needs a complete, exact-ID morphology source and an explicit physical interpretation before transfer to this whole-CNS model.

The source and data review was performed on 2026-09-11. It did not execute the upstream neural model; numerical and biological reproduction remain separate requirements.

## What the primary study establishes

The verified paper is [Pugliese et al., bioRxiv version 2, 30 April 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/), DOI `10.1101/2025.09.12.675944`. The official bioRxiv API returned versions 1 and 2, with no journal publication identifier. It remains a preprint in the retrieved primary record; a repository named `Pugliese_2026` is not itself evidence of journal publication.

The study identifies a candidate recurrent E1–E2–I1 rhythm-generating circuit and tests descending-pathway predictions using optogenetic experiments. Its numerical necessity/sufficiency results are not recordings of the identified interneurons' complete physiology. The paper also reports that its simulations did **not** produce tripod interleg coordination and left some expected muscles, including main tibia flexors, silent or nonrhythmic. Its LIF comparison uses Shiu-style parameters without circuit-specific tuning or validation against those cells' physiology. These results support investigating recurrent neural mechanisms; they do not establish a complete walking controller, flight physiology, or normal-fly capability. [Primary paper, Results, limitations, and LIF Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/)

The source was inspected at [pinned revision faee4b06869855ae0164cbf217fb6ec28ef3521b](https://github.com/smpuglie/Pugliese_2026/tree/faee4b06869855ae0164cbf217fb6ec28ef3521b).

## Actual dynamics and parameter provenance

The source [rate equation](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/simulation/vnc_sim.py#L35) is

$$
\tau_i\dot r_i
=\left[r_i^{\max}\tanh\!\left(
\frac{a_i}{r_i^{\max}}\left(I_i(t)+\sum_j\widetilde W_{ij}r_j-\theta_i\right)
\right)\right]_+-r_i,
$$

where \([x]_+=\max(x,0)\), and \(\widetilde W\) is the signed synapse-count matrix after excitation/inhibition scaling. This is a first-order rate model, not an ion-channel model. Its state has an “Hz” reporting convention; the study explicitly treats it as abstract activity, with external drive in arbitrary units. It has no intrinsic spike events, reset, refractory period, explicit synaptic delay, separate synaptic decay state, adaptation current, or gap-junction conductance in this equation.

| Quantity | Source default | Evidence boundary |
|---|---|---|
| Rate relaxation \(\tau\) | Positive-truncated normal, mean 0.020 s, SD 0.002 s | Literature-informed population prior; not a measurement for each MaleCNS neuron |
| Maximum rate \(r^{\max}\) | Mean 200, SD 10 in reported Hz | Model saturation prior, not each cell's measured ceiling |
| Unscaled gain \(a^*\) | Mean 1, SD 0.1 | Numerical model parameter, not a measured membrane conductance |
| Unscaled threshold \(\theta^*\) | Mean 7.5, SD 0.6 | Arbitrary-input threshold, not −45 mV or a measured rheobase |
| Excitatory/inhibitory multipliers | 0.03 / 0.03 | Synapse-count-to-rate-drive scaling; not 0.03 mV or siemens |
| Heterogeneity | Independent draws by cell and replicate | Random variation is assumed; it does not recover individual physiology |
| Size adjustment | \(a_i=a_i^*/s_i\), \(\theta_i=\theta_i^*s_i\) | Morphology-derived relative size with an assumed excitability relationship |

Values are directly from [neuron defaults](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/configs/neuron_params/default.yaml), [parameter preparation](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/simulation/vnc_sim.py#L1683), and [size normalization](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/utils/sim_utils.py#L73). These defaults are source-backed **model choices**. They are not newly identified physiological constants.

The parameter-selection Methods describe physiological plausibility plus a hyperparameter search on simple monosynaptic networks for recruitment and decay after input removal. That differs from fitting a gait trajectory. Subsequent robustness screens examine rhythmicity across parameters; they do not identify a unique physiological parameter set. [Primary Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/)

An important algebraic simplification clarifies what the size rule does. Let \(u_i=I_i+\sum_j\widetilde W_{ij}r_j\). Then

$$
\frac{a_i^*/s_i}{r_i^{\max}}(u_i-\theta_i^*s_i)
=\frac{a_i^*}{r_i^{\max}}(u_i/s_i-\theta_i^*).
$$

Thus the two parameter adjustments together are equivalent to dividing total input by relative size inside the nonlinearity. They should not be copied as two independent corrections to an already size-normalized current. In a voltage-based LIF model, multiplying a negative voltage threshold by cell size is particularly unjustified: the rate threshold is in a different input coordinate system.

The code computes \(s_i=\mathrm{size}_i/\mathrm{median(size)}\). Missing or zero sizes are replaced by that median. The paper uses volume for MANC/MaleCNS and mesh surface area for FANC/BANC; these are structural measurements followed by a biophysical approximation. A global change in the set used for the median changes every effective input gain even if each neuron's absolute size is unchanged. Preserve the reference population in any reproduction. Do not renormalize against a convenient whole-brain population and call the result the same published model.

## Source data and function contracts that matter for integration

The [default experiment](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/configs/experiment/DNg100_Stim.yaml) selects a 4,604-entry MANC front-leg network, not the whole MaleCNS. Its supplied table maps index `31` to **MANC** bodyId `10093`, DNg100. The core experiment keeps indices `31,277,617,1167`; these map to MANC DNg100, IN17A001, INXXX466 and IN16B036 respectively. Neither those array indices nor the numeric MANC body IDs are MaleCNS neuron correspondences. The `motor module` and `step contribution` columns are analysis labels; the rate equation does not read them as muscle commands.

The MaleCNS files are under the historically named `data/imac t1 connectome data/` directory. The relevant pair is:

- [wTable_20260210_vncRoisOnly.csv](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/data/imac%20t1%20connectome%20data/wTable_20260210_vncRoisOnly.csv)
- [W_20260210_vncRoisOnly.csv](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/data/imac%20t1%20connectome%20data/W_20260210_vncRoisOnly.csv)

Readback found 4,310 unique IDs, with matrix row and column order exactly matching that table. **4,309 IDs exist in the current 167,216-entry prepared graph; bodyId `825433` does not.** All 4,310 source sizes are nonzero/nonmissing, with median `998603428.5` in the source volume units. The current full-CNS table has no size, surface-area, input-resistance or capacitance field. This source therefore leaves **162,907 current neurons without a matched size**, and does not support whole-CNS excitability coverage. No missing ID or size was filled here.

This source network also omits brain-region edges and uses the paper's restricted neuronal selection and weak-connection filtering; it must not replace the complete prepared MaleCNS graph. Recurrent descending/ascending connections already present in the full graph must remain. Reading the source's anatomy is useful; importing its experimental subnetwork as the animal would discard retained full-graph connectivity.

| Contract | Source behavior | Consequence for a full-CNS model |
|---|---|---|
| Matrix orientation | CSV rows are presynaptic; `reweight_connectivity` transposes before `W @ r` | Current prepared CSR already has postsynaptic rows; do not transpose it again |
| Sign/scaling | Positive and negative source weights receive separate multipliers | Preserve raw counts and transmitter evidence separately; do not multiply by both source and Eon gains without a units derivation |
| Parameter arrays | `(replicate, neuron)`; input array `(stimulus, replicate, neuron)` | Replicate dimensions describe experiments, not simultaneous physiological compartments |
| Source stimulus | `make_input` writes arbitrary drive at explicit array indices; default pulse 0.020–1.999 s, magnitude 250 | This is a DN activation experiment. Do not copy it into the sensory-only live animal |
| Initial condition | Rate vector starts at zero | With zero external drive and positive thresholds, zero is a fixed point; spontaneous walking is not promised |
| Time integration | Adaptive Dopri5; `dt=0.001 s` is initial step and saved-output spacing; `rtol=2e-6`, `atol=5e-9` | Not a validated replacement for the 0.1 ms body/neural integration clock |
| Numerical failures | Result NaN/Inf values are changed to zero, then clipped to 0–1000 | Do not copy this into a physical run that must report failures truthfully |
| Loaders | `load_W` accepts CSV/NPY; `load_wTable` accepts CSV/pickle | Other supplied NPZ/Feather datasets are not automatically accepted by these particular helpers |

See the pinned [simulation functions](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/simulation/vnc_sim.py), [data structures](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/data/data_classes.py), [loaders/input helper](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/utils/sim_utils.py#L330), and [simulation defaults](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/configs/sim/default.yaml). Inspection only; none was imported or executed.

## Neural mechanism versus an action script

The half-tanh recurrence has no prescribed gait phase or joint target. Sustained drive can yield an oscillation through recurrent excitation and inhibition; that is an admissible neural mechanism. The sine/cosine code in `sim_utils.py` is a reference for scoring output autocorrelation, not the generator of neuronal activity.

The surrounding experiment machinery is different. [`adjustStimI`](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/simulation/vnc_sim.py#L1143) raises or lowers injected drive based on recruited/high-rate cell counts; it is off in the default config. Pruning removes cells while preserving a motor rhythmicity score; `keepOnly` constructs restricted circuits. These are valid discovery experiments, but none belongs in this live full-graph animal as a physiological mechanism. Do not add tonic DNg100 input, select a favorable random seed, tune excitatory scaling until walking appears, or retain only an oscillatory circuit. A physically justified basal receptor/release process is different from a hidden locomotor drive.

## Comparison with the current Eon/visual hybrid

The inspected [current kernel](../../runtime/cns.py) retains the full prepared graph and imports Eon's `MODEL_PARAMS`. Most neurons are LIF; identified compound photoreceptors and L1/L2 use the local graded extension. [cns-model.json](../../runtime/cns-model.json) explicitly labels those visual constants as estimates. This is broader structural coverage than the source front-leg rate experiment, but still incomplete physiology.

| Quantity | Current Eon source | Pugliese LIF comparison |
|---|---|---|
| Rest/reset/threshold | −52 / −52 / −45 mV | Same values |
| Membrane/synaptic constants | 20 / 5 ms | Same values |
| Nominal delay/refractory | 1.8 / 2.2 ms | Same values |
| Synaptic increment scale | 0.275 mV-equivalent per counted synapse/event | 0.275 mV |
| Integration step | 0.1 ms | 0.01 ms |
| External drive | Bernoulli events with probability `rate_hz * dt_ms / 1000`; amplitude multiplier 250 | Constant `0.15 nA / 10 nS = 15 mV` drive in the notebook |
| Size-dependent excitability | Not applied in current `cns.py` | Rate model applies it; the shown LIF comparison uses uniform constants |

The [source LIF implementation](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/src/lif_model/lif_dynamics.py) is not byte-identical to Eon: event ordering and refractory/delay treatment must be compared before claiming equivalent trajectories. The supplied Extended Data Figure 4 notebook also imports `run_LIF_network` from `sim_utils`, while the inspected definition is in `src/lif_model/lif_dynamics.py`; its duration is 0.3 s versus 3 s in the paper Methods. This review did not run or repair that notebook. The relevant conclusion is that the published candidate oscillator is not specific to the half-tanh formalism, not that this particular checkout was numerically reproduced here.

Eon's `AlphaSynapse` name should not obscure the inspected implementation: it updates one exponentially decaying state plus a delay buffer. That state is called `conductance`, but it enters the voltage update additively beside a voltage difference; it is a **voltage-equivalent drive**, not a measured conductance in siemens. External sensory events receive a different amplification path from recurrent spikes. Neither the name nor the 250 input multiplier establishes receptor physiology. Current graded release is passed through the same structural synapse machinery but is explicitly excluded from action-potential counts.

Primary intracellular work establishes nonspiking VNC populations such as Drosophila 13Bα, alongside spiking populations and heterogeneous response properties. It does not show that every VNC neuron is nonspiking or assign the Pugliese E1/E2/I1 cells measured transfer functions. Much of the broader nonspiking rationale also comes from other insect species. Do not turn an entire hemilineage or all VNC cells into one rate population without exact type correspondence. [Agrawal et al. 2020](https://elifesciences.org/articles/60299)

## If a mixed rate/LIF model is later considered: coupling and units

There is no calibrated brain-LIF-to-VNC-rate interface in the inspected source. A hybrid can be a declared approximation, but it adds choices rather than resolving missing measurements. The following are derived coupling constraints, not proposed fitted parameters.

**Spikes to rate.** For spike times \(t_k\), a causal estimate such as

$$
\widehat r(t)=\sum_{t_k\le t}\frac{e^{-(t-t_k)/\tau_f}}{\tau_f}
$$

has units s⁻¹ and unit area per spike. Choosing \(\tau_f\) changes feedback phase and bandwidth. Eon already has a 5 ms synaptic filter; adding another filter and then a 20 ms rate state does not preserve the original transfer function. A raw binary spike indicator is not a Hz-valued rate. Even a normalized rate estimate still needs an explicit mapping to the rate model's arbitrary input units.

**Rates or graded release to existing chemical synapses.** A release rate \(r\) in s⁻¹ corresponds to \(e_n=r_n h\) event equivalents during a step of length \(h\) seconds. At the current \(h=10^{-4}\) s, 100 Hz means **0.01 event equivalents per step**, not 100 events. The current visual hybrid already uses this convention. Such fractional release is not a motor-neuron action potential and must not be sent through a Boolean spike test: every positive rate would then become one spike per tick, or 10 kHz.

For the inspected Euler synaptic update, ignoring resets/refractory gating, constant fractional release gives

$$
g_{n+1}=(1-h/\tau_s)g_n+wN(rh),
\qquad g_\infty=wN\tau_s r.
$$

With Eon's \(w=0.275\) mV-equivalent and \(\tau_s=0.005\) s, this is `0.001375 * N * r` mV-equivalent. This is only a mean-drive calculation, not an equality of spiking and rate-model trajectories. It also shows why the rate-model multiplier `0.03` cannot simply replace Eon's `0.275`: the parameters multiply different quantities and have different implicit units.

**Retain actual motor spike generation.** The existing NMJ consumes motor events. If upstream interneurons become rate-based, a source-supported motor spike generator is still needed; arbitrary Poisson conversion would erase refractory structure and timing information relevant to muscle activation. A rate must not be mapped directly to a gait, angle, muscle force target, or phase. Keep the existing motor-neuron→NMJ→muscle→physics path.

**Retain one causal time boundary.** Any later hybrid must exchange brain/VNC signals and body feedback at explicit simulation times, include ascending as well as descending edges, and avoid using future averages or replaying a precomputed rate trace as the animal's live input. Source batch solver output is not a closed-loop stateful runtime API. A switched model would need its own state/initialization and interface validation; no such switch is warranted merely because current behavior is absent.

## Neurotransmitter, neuromodulator and electrical-synapse limits

| Missing authority | Current/source approximation | What remains needed |
|---|---|---|
| Postsynaptic receptor identity and localization | One presynaptic NT gives one sign for all its outputs | Connection-specific receptor/reversal evidence; glutamate can inhibit centrally and excite other targets, including muscle |
| Cotransmission | One `consensus_nt` and one fast sign | Separate release/receptor pathways where identified; R8 histamine/ACh cotransmission is a primary counterexample |
| Amines and peptides | Current importer gives dopamine, octopamine and serotonin positive fast-current signs; rate defaults distinguish excitatory/inhibitory drive | Target receptor coupling, concentration, clearance, time scales and state dependence; generic excitation is not neuromodulation or reward physiology |
| Unknown transmitter | Current graph retains structure but sets unresolved fast transmission to zero | Identity/sign evidence; zero current is an explicit omission, not biological absence |
| Electrical synapses | Chemical weight matrices supply no gap-junction conductances | Exact coupled partners, location, conductance and rectification; reciprocal chemical edges do not identify gap junctions |
| Intrinsic cellular dynamics | Uniform LIF or first-order rate priors | Type-linked excitability, adaptation, ion-channel kinetics, morphology/compartments, temperature dependence and release dynamics |

These limits follow primary [transmitter-classification work](https://pmc.ncbi.nlm.nih.gov/articles/PMC11106717/), the [R8 cotransmission study](https://www.nature.com/articles/s41586-023-06681-6), and [electrical-coupling experiments](https://doi.org/10.1016/j.neuron.2010.08.041). Expression or contact alone is not a conductance measurement. No electrical links, receptor assignments, neuromodulatory gains or cotransmitter target IDs were invented in this review.

The current prepared manifest reports **3,656 unresolved-transmitter neurons and 589,524 unresolved outgoing edge rows**. Its structure remains available, while those edges contribute zero fast current. The rate equation does not recover that missing information. Similarly, replacing a positive monoamine sign with a slower arbitrary filter would add a phenomenological modulation model, not identify the correct receptor action.

## Next physiological comparison

1. **Evaluate physical feedback integration with the current kernel and frozen, declared neural parameters.** Real FeCO angle/velocity input, muscle forces and resulting motion can test the existing closed loop without adding a programmed drive. Lack of walking is a result to diagnose, not a reason to adjust parameters until walking appears.
2. **Do not make a Pugliese rate-kernel replacement part of “finish the full fly.”** It would introduce an arbitrary-rate interface, incomplete size normalization and a new motor-event conversion while retaining the same missing receptors, modulation and electrical connectivity. This is not a prerequisite for finishing the remaining body reconstruction.
3. **For the next central-physiology change, require a named, independently grounded parameter or cell-type improvement.** The concrete candidates are exact-ID size/input-resistance coverage with a fixed normalization reference, or a verified nonspiking cell-type correspondence with intracellular constraints. The presently available 4,309 size matches are useful source data, but insufficient for a whole-CNS application. Do not median-fill 162,907 missing values and advertise measured coverage. These candidates remain hypotheses until their missing identity/parameter evidence is supplied.

The justified operating claim is a complete retained neuronal graph with declared dynamical approximations and progressively connected physical inputs/effectors. Neither a component check nor adopting a published oscillator establishes natural whole-fly coordination. This conclusion does not require stopping the remaining body/sensory implementation; it prevents an unsupported neural-model substitution from being mistaken for completion.

## Reproducibility receipt

Source inspection, not a simulation:

| Inspected source | SHA-256 |
|---|---|
| Pugliese `src/simulation/vnc_sim.py` | `58518185d43cd1a723f4ad1278753bc6e54fc5c086575206e82e493e9d960a5c` |
| Pugliese `src/utils/sim_utils.py` | `c8f58e2d77c50325d785c6d707ddba6608e774cbfd10203ed3488ea3320b6653` |
| Pugliese `src/lif_model/lif_dynamics.py` | `be9d726e89ab21ae382e07cece1acebfdb5ff0d0af5a4226fbb339e576cc120a` |
| Pugliese neuron defaults | `b63a37b84e056035d638bb8a36baf53e199d37feb4ddca9d044af3c521247298` |
| MaleCNS source `wTable_20260210_vncRoisOnly.csv` | `593a75c53f1c69600cac747364b8b623655699b1b83e16b41eeef6fe93dd5b2d` |
| MaleCNS source `W_20260210_vncRoisOnly.csv` | `255236baca7a24ead7360636a4ee98fd54d5423026c6ec864bbd717b8d58d3b4` |
| Eon `code/run_pytorch.py` | `699655db7a56045271ba467268be153d0a3318d4cc4cecc0a13f33e69ce79667` |
| Local `runtime/cns.py` at review | `84b5c72a5c57b401f42bc4eee4a9c1e27eb016881e9792a37660fe7043ee36d6` |
| Local `runtime/prepare_cns.py` at review | `0658ff70cda7c25f8d6ad7012536b48567b6a181639fb328b5285212467d5065` |
| Local `cns-model.json` at review | `f34166cb2a48ef7c4186c7ced9f6230d8f8e2cd6fd319215767fd267b7b82f29` |

The paper's v2 full-text XML was read from the [Europe PMC primary full-text endpoint](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13142387/fullTextXML), hash `8601d675a0284d631dfbd65bae9e834c3332e0f11808b81a5136ff2d75078143`. Static CSV checks verified matrix/table ordering, size completeness within the source subnetwork, and exact-ID overlap. These receipts do not claim neural or behavioral validation.

The unit identities above can be checked without running any neuronal simulation:

```sh
python3 - <<'PY'
from math import isclose, tanh
h, r, tau_syn, w = 1e-4, 100.0, 0.005, 0.275
assert isclose(r*h, 0.01)
assert isclose(w*tau_syn*r, 0.1375)  # one synapse, mV-equivalent mean drive
assert isclose(0.15e-9/10e-9, 0.015)  # A/S = V
a0, theta0, size, cap, u = 1.0, 7.5, 2.0, 200.0, 30.0
assert isclose(tanh((a0/size/cap)*(u-theta0*size)),
               tanh((a0/cap)*(u/size-theta0)))
print('PASS: coupling units and size-normalization algebra; no neural simulation')
PY
```

Validation receipt: the unit/algebra assertions above and local report-link checks were executed and passed on 2026-09-11. This was not a neuronal simulation or a behavioral validation.

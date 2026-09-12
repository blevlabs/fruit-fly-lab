# Peripheral force calibration: independent physiology review

This note records historical studies from September 2026. Reported checks and source hashes identify those studies; they are not new verification of the packaged software. See [current status](../status.md), the [research roadmap](../roadmap.md), and the [historical provenance archive](../../results/README.md).

Historical review, 2026-09-11: the exact scalar law in `neuromuscular.py`, an isolated numerical reproduction, and primary adult Drosophila force/electrophysiology evidence.

**Verdict:** the suspected sustained-drive bottleneck is real, but **0.08 is the continuous high-frequency limit of raw excitation, not a global ceiling and not the returned control**. The implementation returns `e/(1+e)`, giving a high-frequency limit of **0.074074…**. At constant input native activation approaches that value. The code is internally consistent; the unsupported step is interpreting its dimensionless output as calibrated fractional muscle activation. **No universal gain multiplier, division by 0.08, or equal motor-unit capacity is scientifically justified by the evidence recovered in this study.** This remains a critical obstacle to a normal-fly physiological claim despite passing constituent force-transmission checks.

Reviewed [NMJ source](../../runtime/neuromuscular.py) SHA-256: `5f7b4057e05d0a8e8aedea8072356d8fa2fb52672f6b67fb5b158dc00a4fde55`. Historical [configuration](../../runtime/cns-model.json) has body step 10 µs, neural step 100 µs, delay 1 ms, excitation decay 8 ms, recovery 100 ms, spike gain 0.2 and depression 0.2. `MotorUnits` instantiates each NMJ at the **body** timestep and preserves a separate NMJ state per neuron; per-path capacity sharing is a separate operation.

## 1. Exact discrete law

Let `h` be the NMJ step, `d=exp(-h/τe)`, `r=exp(-h/τR)`, `γ=spike_gain`, `U=depression`. Define x and e immediately before deliveries at the beginning of step n. Let bₙ be one when an event is delivered and release is allowed, otherwise zero. Under the public binary-event API at most one event is delivered per step.

```text
e⁺ₙ       = eₙ + γ bₙ xₙ
x⁺ₙ       = (1 − U bₙ) xₙ
zₙ        = sqrt(d) e⁺ₙ
uₙ        = zₙ / (1 + zₙ)          # actual return value, not hard clipping
eₙ₊₁      = d e⁺ₙ
xₙ₊₁      = 1 − r + r x⁺ₙ
```

Events passed at a step's end are queued for that timestamp plus the specified delay. With `D=delay/h`, an event supplied on call n first affects call n+1+D. Its returned control samples that later interval's midpoint. This convention is causal and does not add a rate-dependent amplitude factor. Fixed delay shifts a stationary train without changing its stationary distribution. A blocked release is removed from the queue without an excitation jump or resource depletion.

For one released event every **m steps**, `T=mh`, write `R=exp(-T/τR)` and `E=exp(-T/τe)`. Between events the resource recovers for exactly m steps, so

```text
x⁻ₖ₊₁ = 1 − R + (1−U)R x⁻ₖ
x*     = (1 − R) / (1 − (1−U)R)
A      = γ x* / (1 − E)          # raw excitation immediately AFTER an event
zⱼ     = A exp(−(j+1/2)h/τe),  j=0,…,m−1
ū      = (1/m) Σⱼ zⱼ/(1+zⱼ)      # exact sampled-period mean
```

The raw midpoint mean has the closed form

```text
z̄ = γ x* sqrt(d) / [m(1−d)].
```

The continuous-time mean over a period is `γ x* τe/T`. The midpoint mean differs by the factor `h/[2τe sinh(h/(2τe))]`, which tends to one. Because the saturation is nonlinear, `ū` is not `z̄/(1+z̄)` except in the vanishing-ripple limit.

For **U>0**, as T→0 with sufficiently small h:

```text
x* ~ T/(U τR)
e∞ = γ τe/(U τR) = .2*.008/(.2*.1) = .08
u∞ = e∞/(1+e∞) = 2/27 ≈ .074074074.
```

At a fixed step, infinite frequency is not available: the binary API caps delivery at 1/h. Its exact every-step fixed point is

```text
z_grid = γ sqrt(d)(1−r) / [(1−d)(1−(1−U)r)]
u_grid = z_grid/(1+z_grid).
```

At h=10 µs this is **0.0740432182**, for an artificial 100 kHz stress train. At h=100 µs it is **0.0737662599**, for 10 kHz. These are mathematical/grid probes, not plausible physiological firing rates. The actual neural generator has its own timestep/refractory limits.

**This is not an all-time bound.** A fully recovered single event jumps e to 0.2 and produces a first midpoint control about 0.16658. Closely spaced onset events can transiently release a substantial fraction of the resource pool before the recovery-limited steady state is reached. Irregular and burst responses cannot be replaced by the stationary limit. Setting U=0 would remove this recovery-limited asymptote, but is a different physiological model, not an arithmetic repair.

## 2. Scalar numerical results and implications for force

The periodic formula was checked against the imported `NeuromuscularJunction` without a mechanical body model. Maximum control disagreement in the tested h=10 µs trains was **3.6e−13**. A separate scalar activation integration used the native MuJoCo muscle-dynamics equation, checked against `mju_muscleDynamics` at a grid of activation/control values:

```text
τ = τact*(0.5+1.5a)      if u>a
τ = τdeact/(0.5+1.5a)    otherwise
da/dt = (u−a)/τ
```

The native parameters were 10/40 ms; h=10 µs Euler updates model the activation integration used with the historical implicit-fast body integrator. No mechanical trajectory was simulated. [MuJoCo muscle model](https://mujoco.readthedocs.io/en/stable/modeling.html#muscle-actuators)

| Regular input Hz | Mean returned u | Mean native a | Peak native a | Mean active force for F0=28 µN |
|---:|---:|---:|---:|---:|
| 10 | .0131834 | .0472215 | .0760509 | 1.3222 µN |
| 20 | .0227545 | .0609483 | .0748689 | 1.7066 µN |
| 40 | .0353296 | .0670855 | .0721924 | 1.8784 µN |
| 100 | .0519330 | .0696877 | .0707302 | 1.9513 µN |
| 200 | .0611791 | .0711895 | .0714758 | 1.9933 µN |
| 500 | .0683515 | .0726741 | .0727229 | 2.0349 µN |
| 1,000 | .0711045 | .0733240 | .0733365 | 2.0531 µN |
| 10,000, grid stress only | .0737666 | .0739925 | .0739926 | 2.0718 µN |

The activation mean exceeds the control mean at many frequencies because activation rises and falls at different, activation-dependent rates. Therefore multiplying **mean u** by F0 would also be incorrect. A constant-control limit does satisfy a=u. Native force at other lengths/velocities includes the force–length and force–velocity multipliers; passive force is separate. The last column assumes **optimal fiber length, zero velocity, zero passive bias and an unsplit 28 µN capacity**. It is neither tip force nor an assertion that every modeled motor unit has F0=28.

Starting fully recovered, a single event gave peak a≈**0.07665**, or **2.146 µN** for that illustrative F0. A ten-event burst at 1 kHz gave peak a≈**0.23513**, or **6.584 µN**. Single-event activation reached its peak roughly **8.0 ms** after the spike, but its rising half-peak at roughly **2.5 ms**. These are different quantities; the ~8 ms peak cannot be claimed to match an experimental ~8.5 ms *half-rise*.

The analyzed resource law predicts isolated second/first **increment** ratio `1−U exp(−Δ/τR)`, or **0.87869 at 50 ms**. For sustained 20 and 40 Hz, per-event resource settles to **0.76435** and **0.58680** of its recovered value. Those are testable NMJ hypotheses if x is interpreted as synaptic efficacy; they are not force ratios.

## 3. Primary adult evidence that can constrain calibration

### A. Foreleg tibia-flexor units: Azevedo et al. 2020

[Primary paper, Figure 4 and Methods](https://elifesciences.org/articles/56754); [publisher XML](https://raw.githubusercontent.com/elifesciences/elife-article-xml/master/articles/elife-56754-v2.xml).

| Source-backed quantity | Value and meaning |
|---|---|
| Single fast-unit event | Approximately **10 µN at the force probe**, ~50 µm displacement |
| Single intermediate-unit event | Approximately **1 µN at the probe**, ~5 µm displacement |
| Slow-unit event regime | **<0.1 µN per additional spike**; very different tonic behavior from fast/intermediate units |
| Two events versus one | ~**1.6×** peak response for fast/intermediate units; peak force saturates around ten events in the short-stimulation comparison |
| Fast/intermediate half-rise | ~**8.5 ms** to half-maximal probe response |
| Slow response | Increasing firing produces gradual force that does not reach its peak within 500 ms; hyperpolarization's maximal force effect takes ~100 ms |
| Probe calibration | **0.2234 µN/µm = 0.2234 N/m**; calibrated against an analytical balance |
| Muscle calcium | GCaMP6f signals sampled at **50–60 Hz**, useful for recruitment/clustering; no absolute free [Ca²⁺] or universal fluorescence-to-force conversion |

**Conditions:** female flies 1–4 days post-eclosion for these physiology experiments; right foreleg; head/thorax/coxa/femur constrained and tibia loading a flexible probe; room-temperature recording saline, **1.5 mM CaCl₂, 4 mM MgCl₂, pH 7.2**. Somatic/EMG signals were digitized at 50 kHz and probe video at 170 fps. Methods describe 10–20 ms optogenetic flashes; the Figure 4A example specifies 50 ms. Use the corresponding actual spike times, not a duration inferred from a different panel. The MLA experiment blocks central cholinergic input, not evidence for an acetylcholine NMJ.

**What this calibrates:** independent adult motor-unit force transients, relative unit strengths, rise times and short-burst summation, under a defined load. **Figure 4D plots peak force against spike count**, including additional slow-unit spikes above baseline; it is not a stationary force–frequency curve. Reproduce the force-probe geometry/load before converting probe force to tendon F0. Joint moment arms, resting load, antagonist activity and the changing force–length state matter. Equal capacity shares across fast/intermediate/slow units are not supported by their approximately three-order-of-magnitude force range.

A source-unit caution matters for dynamic replay: the Methods text reports probe m=0.1702 mg and c=0.1377 kg/s, alongside a 2.5 ms relaxation constant and 5.8 ms oscillation period. Those values are dimensionally inconsistent: `2m/c` would be ~2.5 µs and the system strongly overdamped. **A damping coefficient near 0.1377 g/s is consistent with the stated dynamics**. That value was initially a dimensional inference; the subsequent [foreleg source analysis](m2-foreleg-source-notes.md) found an explicit SI coefficient of 0.1377×10⁻³ kg/s in the archived analysis. The printed discrepancy remains part of the source record. See the [publication code](https://github.com/elifesciences-publications/FlySound) for the instrument calibration.

### B. Adult CM9: transmission is measured; excitation-to-force is not

[Mahoney et al. 2014, Table 1/Figure 5](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/) report, for 7-day virgin female `w1118` CM9, EPSP **9.03±0.33 mV**, mEPSP **1.12±0.08 mV** and derived quantal content **8.55±0.61** (n=13; reported mean±SEM). The 15-second 40 Hz train comparison found marked depression at 42 days, but **not significant depression at 7 days**; n=8 per condition. This does not support assigning the analyzed model's ~41% stationary per-event efficacy reduction at 40 Hz universally to young CM9. Non-significance is not proof of exactly zero depression; the trace amplitudes and uncertainty should be fit directly.

[Mahoney et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5012858/) report 21-day female CM9 EPSPs of **3.46±0.30 mV** on 1X diet versus **1.65±0.08 mV** on 2X diet, n=8/group, with paired-pulse depression at 50 ms under one diet but not the other. These electrical amplitudes and diet dependence cannot identify a unique universal U and τR. Study saline contained **0.5 mM Ca²⁺ and 3 mM Mg²⁺**; controlled recording-bath temperature was not specified. The [2017 adult CM9 recording protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413541/) instead lists **0.5 mM Ca²⁺, 20 mM Mg²⁺**, with **0.3 ms, 0.5–5 V** nerve stimuli. Pulse width is not NMJ or contraction delay.

[Rawson et al. 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3350605/) discuss substantial changes in electrical transmission without proportional changes in proboscis extension, consistent with a transmission safety factor. This qualitative result cautions against taking EPSP amplitude as linear fractional force. It is not used here to fit feeding behavior. The existing [adult-M9 evidence review](mn9-dynamics.md) records the source/table details and additional condition differences.

**Usable calibration:** stimulus-aligned EPSP/mEPSP amplitude and decay, paired-pulse *increment* ratios, train depression and recovery in the same cohort. **Missing:** simultaneous isolated M9 force/calcium, membrane-to-calcium threshold, absolute muscle calcium, force–frequency/tetanus curve, PCSA and load-resolved moment arms. The mEPSP half-width 8.17±0.76 in [Kreko-Pierce et al., Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC5207075/) has an omitted unit; it cannot establish the modeled 8 ms calcium/excitation decay.

### C. TDT/TTM: independent material constants from Eldred et al. 2010

[Primary paper, Table 2/Figure 2/Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/); [author-hosted PDF, Table 2 visually checked](https://static1.squarespace.com/static/543205c7e4b0e99376e323aa/t/5469f2eee4b02ed9bcbd884a/1416229614488/The%2BMechanical%2BProperties%2Bof%2BDrosophila%2BJump%2BMuscle%2BExpressing%2BWild-Type%2Band%2BEmbryonic%2BMyosin%2BIsoforms.pdf).

| Tr-WT TDT quantity | Measured value (mean±SE) | Conditions/sample |
|---|---:|---|
| Maximum Ca-activated stress | **37±3 mN/mm² = 37±3 kPa** | n=21 |
| Resting stress | **0.9±0.2 mN/mm²** | n=7 |
| pCa50 | **5.62±0.01** | n=6; pCa=−log10([Ca²⁺] in M) |
| Hill coefficient | **10.2±2.1** | n=6 |
| Unloaded shortening | **6.1±0.3 muscle lengths/s** | n=10 |
| Measurement reference | **15°C; sarcomere length 3.6 µm** | Chemically skinned, 8–10 large-fiber preparations |

The preparations came from **2–3-day-old females** expressing the native TDT myosin isoform from the Tr-WT transgene in an Mhc10 background. They were demembranated, not nerve-driven. Typical prepared dimensions were ~125 µm long, 110 µm wide, 45 µm deep (cross-sectional estimate ~4,950 µm²). Measurement baths used pH 7.0, 1 mM free Mg²⁺, 10 mM MgATP and 260 mM ionic strength. Calcium was externally controlled; tension–pCa measurements stepped between relaxing and activating baths, with maximal activation at pCa 5.0. EMB transgenic results are not wild-type adult material values.

These measurements can constrain a **TDT constitutive model independently of jumping outcomes**. The corresponding Ca50 is **2.399 µM**, and the measured equilibrium relation is approximately

```text
F/Fmax = 1 / [1 + 10^(nH*(pCa − pCa50))].
```

They cannot assign pCa to the modeled dimensionless e or infer nerve-frequency activation after skinning removed the NMJ/membrane machinery. Temperature and normalization must be reconciled before using 6.1 ML/s as native `vmax`; it is not an automatically applicable value for other muscles.

The dimensional product `37 mN/mm² * .00495 mm² = 183.15 µN` concerns the reported **prepared bundle** and is a product of representative values, not a measured force of every TTM neuron or whole TDT. Conversely, 28 µN would imply ~**757 µm²** at that stress; this is an implied area, not anatomical evidence. To obtain F0, use measured contractile PCSA, pennation and recruited fiber allocation. **Axon radius/diameter is not muscle PCSA**. A neuronal size ranking does not supply a quantitative muscle-area law.

### D. Useful limits on claims of missing data

A primary **in situ adult jump-muscle twitch ergometer** exists: [Harvey et al. 2008](https://pubmed.ncbi.nlm.nih.gov/18443837/), with the follow-on [Elliott and Sparrow 2012 method](https://pubmed.ncbi.nlm.nih.gov/22037247/). The accessible primary abstracts establish an assay of single-action-potential twitch output, including age/modulatory effects, but this bounded retrieval did not recover a verified absolute force–frequency dataset or the complete load/transmission calibration. Thus it would be wrong to claim that no intact adult TTM force evidence exists; obtaining its full quantitative records is a concrete next calibration source.

As a muscle-class counterexample, [Kawasaki and Ordway 2009, Figure 3F](https://pubmed.ncbi.nlm.nih.gov/19706552/) measured adult **DLM** synaptic recovery after 100 pulses at 5 Hz, 33°C: **τfast=.04 s (41%) and τslow=1.45 s (59%)**, n=4–5. A universal single 100 ms resource state cannot reproduce that two-component recovery. These are **asynchronous flight-muscle NMJ** observations, not TTM/leg/proboscis force calibration; they must not be copied into synchronous-muscle activation or used as a wingbeat clock.

The recent paper [Ormerod et al., excitation–contraction coupling](https://pmc.ncbi.nlm.nih.gov/articles/PMC9044916/) does contain stimulation-frequency/force measurements, but the preparation is **larval**, not adult. Likewise, the commonly cited [insect activation-model comparison](https://pmc.ncbi.nlm.nih.gov/articles/PMC6812852/) is not a ready adult-Drosophila calibration. Neither closes this adult parameter gap.

## 4. Which MaleCNS targets can use which evidence?

The historical independent motor map (original artifact `neural-motor/malecns-motor-map.json`; [archive](../../results/README.md)), SHA-256 `b3e17e97f26b0e85df88777fbda0eb2109292ed0e78658a2eb6bbe5095b72964`. These are possible calibration populations, **candidate mappings rather than established per-unit calibration**.

| Evidence | Historical target/population | Permitted use / unresolved assignment |
|---|---|---|
| Adult CM9 electrophysiology | `proboscis.m9`: **10331→L**, **16949→R** | Anatomically matched muscle class; electrical calibration only, conditional on sex/age/diet/saline. No FlyWire roots borrowed |
| TDT material constants and intact-TTM assay lead | `wing.tergotrochanteral_jump`: L **804642 (TTMn), 830847/924167 (STTMm)**; R **800146 (TTMn), 801391/824223 (STTMm)** | Relevant T2 jump-muscle group. Do not apply bundle force separately to each neuron or equate the prepared fiber subset with every STTMm territory |
| Azevedo foreleg tibia-flexor data | `leg.tibia_flexor`, LF **807165, 809912, 818057, 819384, 909831**; RF **810098, 821635, 827188, 1050031705, 1050189039** | Group/assay prior. The historical rows do not resolve which is the genetically identified fast, intermediate or slow unit |
| Azevedo intermediate/distal fiber anatomy | Possible relationship to additional tibia-flexor/accessory populations requires direct anatomical crosswalk | Do not equate the historical word “reductor” with the modeled `leg.femur_reductor` target, or assign the slow-unit force to it by name alone |

The foreleg data are not automatically a calibrated middle/hind-leg serial homology. None of these papers calibrates every neck, labellar, retinal, antennal, gut or flight muscle. Left/right and bilateral/unpaired assignments require the anatomical evidence recorded in the motor map.

## 5. Is a simple normalization correction scientifically justified?

**Not a numerical multiplier from these sources alone.** The modeled e is neither measured membrane voltage nor measured free calcium. `u=e/(1+e)` fixes the half-saturation scale to e=1 without experimental support. Redefining that scale is scientifically possible, but its numerical value must come from an independent force/calcium/voltage calibration at a defined motor unit, not a desired walking/feeding outcome.

Some tempting “fixes” have different meanings:

- Multiplying γ by **12.5** makes e∞=1 but gives u∞=**0.5**, not 1.
- Replacing the output by `min(1,e/.08)` enforces an artificial saturation at the mathematical resource ceiling and discards the existing dose-response law; no adult source above establishes that choice.
- Scaling F0 by **13.5** restores a chosen high-rate active force while changing the claimed maximum material capacity and passive-force scale. That is not NMJ calibration.
- Setting U=0 may be a useful explicitly labelled young-CM9 null model to compare against train recordings, but is not a proven universal repair and does not calibrate γ or the force transfer.
- Adding a free e50 as well as a free γ does not itself solve identification: scaling both by the same factor leaves u unchanged. Use one declared scale convention, or independently measure e in physical units before fitting e50.

A defensible minimum path is to freeze anatomy/load and material force capacity from independent evidence, identify the relevant motor unit, then estimate a compact spike-to-force transfer from isolated recorded spike/force traces. Use separate short trains and recovery intervals to identify depression, and hold out other rates, lengths and loads. For CM9, fit synaptic dynamics to electrical records before asserting a force link. For TDT, the measured pCa/stress relation is usable only with an explicit, independently calibrated calcium variable or as a separate material benchmark. These are constituent physiological fits, not fits to walking or feeding success.

Until that chain is constrained, the adapter remains **an uncalibrated effective drive model**. Its low sustained activation is real model behavior, but does not by itself prove either that the biological muscle should be stronger or that the simulated animal has normal peripheral physiology. Force sign/bounds tests establish numerical transmission, not correct force capacity or recruitment.

## 6. Historical scalar-analysis listing

The following listing records the original scalar NMJ and native activation analysis. Its source-hash condition applies to the historical source snapshot. It is included as the analysis specification, not as a command verified against the current package. The calculation contains no body trajectory.

```python
import hashlib
import math
from pathlib import Path
import mujoco as mj
from neuromuscular import NeuromuscularJunction

assert hashlib.sha256(Path("neuromuscular.py").read_bytes()).hexdigest() == \
    "5f7b4057e05d0a8e8aedea8072356d8fa2fb52672f6b67fb5b158dc00a4fde55"
p = dict(delay_s=.001, tau_exc_s=.008, tau_recovery_s=.1,
         spike_gain=.2, depression=.2)
h = 1e-5

def adot(u, a):
    tau = .01*(.5+1.5*a) if u > a else .04/(.5+1.5*a)
    return (u-a)/tau

for u in (0, .05, .2, 1):
    for a in (0, .03, .1, .9):
        assert math.isclose(adot(u, a),
            mj.mju_muscleDynamics(u, a, [.01, .04, 0]), abs_tol=1e-12)

worst = 0.0
for rate in (10, 20, 40, 100, 200, 500, 1000, 10000, 100000):
    m = round(1/(rate*h))
    T = m*h
    R, E = math.exp(-T/.1), math.exp(-T/.008)
    x = -math.expm1(-T/.1)/(1-.8*R)
    A = .2*x/(1-E)
    nmj = NeuromuscularJunction(h, p)
    a = 0.0
    start = round(2/h) + nmj.delay_steps + 1
    controls, activations = [], []
    for n in range(start+m):
        u = nmj.advance(n % m == 0)
        a = min(1., max(0., a+h*adot(u, a)))
        if n >= start:
            phase = (n-nmj.delay_steps-1) % m
            z = A*math.exp(-(phase+.5)*h/.008)
            worst = max(worst, abs(u-z/(1+z)))
            controls.append(u)
            activations.append(a)
    print(rate, sum(controls)/m, sum(activations)/m,
          max(activations), 28*sum(activations)/m)
assert worst < 1e-10, worst

for spacing, label in ((None, "single"), (100, "ten at 1kHz")):
    events = {0} if spacing is None else set(range(0, 10*spacing, spacing))
    nmj = NeuromuscularJunction(h, p)
    a = peak_a = peak_u = 0.0
    for n in range(round(.3/h)):
        u = nmj.advance(n in events)
        a += h*adot(u, a)
        peak_u, peak_a = max(peak_u, u), max(peak_a, a)
    print(label, peak_u, peak_a, 28*peak_a)
assert math.isclose(.2*.008/(.2*.1), .08)
print("PASS: exact periodic control, scalar native activation, and onset transients", worst)
```

This bounded review did not recover a complete, condition-matched adult spike→muscle-calcium→tendon-force dataset or an exact fast/intermediate/slow MaleCNS crosswalk. That is the specific evidential limit behind the conclusion that a universal gain correction is unsupported, not a claim that adult mechanical measurements do not exist.

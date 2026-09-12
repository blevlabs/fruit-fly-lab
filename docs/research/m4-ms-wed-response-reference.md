# M4 MS-WED electrical response reference

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**A standalone passive electrical comparator now runs against independent published recordings. Its numerical checks pass and it predicts part of the response at held-out current amplitudes, but one RC does not reproduce the observed fast transitions, slower relaxation and drift. These effective fits are not ready to replace live neuronal physiology.**

The [script](../../research/check_ms_wed_reference.py) uses the fixed comparison plan (original artifact `program/m4-m7/ms-wed-reference/rc-comparison-plan.json`), written before curve fitting, and source snapshot `5edb22959211d96d7b4332c0de8190019fcdc8e8`. The result (original artifact `program/m4-m7/ms-wed-reference/rc-comparison/comparison-result.json`) records plan/script/data hashes, exact recording identities, parameter meanings, errors and environment versions. The earlier [57-ID transmitter adjudication](m4-transmitter-primary-adjudication.md) remains a separate identity result.

## Source and physiological boundary

[Wu et al. 2024](https://doi.org/10.1016/j.cell.2024.07.047) identifies MS-WED as DNp32 and reports MSR2/PKA/ORK1-dependent membrane effects in recipient DA-WED cells. Donor identity transfers through the named type to MaleCNS **524968 (`DNp32_R`)** and **556286 (`DNp32_L`)**. Historical recipient labels `IPS.290` and `WED.162` still lack a verified stable-ID crosswalk in the inspected sources. Strong contacts or similar names were not used to choose a recipient.

The raw-data feasibility report (original artifact `program/m4-m7/ms-wed-reference/report.md`) records the public Zenodo route, five condition-labeled ABFs, ZIP CRC checks, decoder verification, sample scaling and lossless NPZ exports. Only about 5.08 MB of selected compressed members were transferred; complete large ZIPs were not downloaded. The ABF conversion used the independently checked pyabf decoder.

Two **female MS-WED donor** recordings supply the current steps used here. All eight male Figure 6G headers were inspected and are gap-free, so this is not a male dynamic calibration. Each female file contains 23 sweeps. The headers specify **20 kHz**, **350-ms pulses**, and nominal levels **−30 to 190 pA**, differing from the paper's 10-kHz/300-ms/−30-to-80-pA description. Full epochs are preserved and used as recorded. ADC0 is mV; the secondary ADC does not track the commanded steps and is not treated as a measured current monitor. Header zero access-resistance/capacitance fields are not interpreted as physical measurements.

The source preparation is ex vivo β-escin-perforated patch, with one neuron per brain and a stated access-resistance criterion below 40 MΩ. The archive note permits spontaneous or zero-current evoked traces for resting-voltage analysis. Exact per-recording current calibration, recording-site/electrode transfer properties and some protocol discrepancies remain unresolved.

## Fixed model and held-out comparison

For voltage deflection from the observed pre-pulse baseline, the comparator is

$$
\tau_{\rm eff}\,\frac{d\Delta V}{dt}
=0.001 R_{\rm eff} I_{\rm nominal}-\Delta V,
$$

where voltage is mV, nominal DAC command is pA, resistance is MΩ and time is seconds. The 0.001 factor is the unit conversion. No spike rule, reset, receptor state, chemical concentration or neural connection is included.

Each recording is analyzed separately. Two positive parameters, resistance and time constant, are fitted to **all samples of sweep 0 (−30 pA)**. No smoothing or time-window exclusions were applied. The parameters are frozen for sweeps 1 and 2 (**−20 and −10 pA**). Each sweep's observed pre-pulse mean supplies its initial baseline; this predicts conditional deflection and does not replay a persistent individual across sweep gaps. The zero-current sweep is a diagnostic only. Positive/spiking sweeps are outside this declared passive reference.

| Source recording | Effective R (MΩ per nominal input) | Effective τ (ms) | Derived effective C (pF) | Held-out RMSE −20 / −10 pA (mV) |
|---|---:|---:|---:|---:|
| Mated female `2024_04_11_0002` | 345.889 | 11.585 | 33.495 | 0.488 / 0.994 |
| Virgin female `2024_04_15_0004` | 583.203 | 24.998 | 42.864 | 1.094 / 0.682 |

The derived capacitance is `tau/R` for this effective circuit. It is **not an independently measured membrane capacitance**, and it must not be assigned to a MaleCNS cell. One file per condition, selected for small transfer size, cannot establish a population or mating-state effect.

All four held-out predictions improve over the no-response comparator. That is a limited prediction result, not a biological equivalence gate. Relative RMSE is approximately 7–29% of the model's nominal pulse-response amplitude, and a population-equivalence tolerance was not invented. Source traces, predictions and initial baselines remain inspectable.

Historical figure: Recorded and predicted MS-WED voltage responses (original artifact `program/m4-m7/ms-wed-reference/rc-comparison/comparison.png`)

## Numerical correctness and model limitation

The script checks units, pulse timing, zero-current response and rejection of nonpositive resistance. Forward Euler at 100, 50 and 25 µs is compared with the analytic solution at the same command boundaries. States remain finite and errors decrease on every halving:

| Recording fit | Maximum Euler error at 100 / 50 / 25 µs (mV) |
|---|---:|
| Mated female | 0.016534 / 0.008252 / 0.004122 |
| Virgin female | 0.012895 / 0.006442 / 0.003220 |

Those errors are substantially smaller than the measured-trace discrepancies. Reducing the integration step therefore does not repair the biological/recording model mismatch.

Visual inspection shows systematic deviations at onset and recovery, a slower component in the virgin recording, and within-sweep drift, particularly in the mated −10-pA trial. The one-RC assumption is the limiting model boundary. The available data do not uniquely separate intrinsic cell dynamics from recording/electrode effects or delivered-current uncertainty. No extra channel, artificial state-dependent gain or second anatomical compartment was invented to force agreement. Adding such a model requires independent identification and a fresh validation split; the already inspected held-out curves cannot become a new blind test.

## Reproduction and remaining work

Use [research/check_ms_wed_reference.py](../../research/check_ms_wed_reference.py) with the source data specified in the package README. The historical commands were not rerun in the public layout.

The plot command reads the existing result without refitting. The raw conversion can be replayed separately with `outputs/program/m4-m7/ms-wed-reference/export_pilot.py` and its isolated reader. No running simulator is contacted.

Implementation and numerical reference checks pass. Biological transmission validation remains **open**: reconcile input/acquisition/filter metadata; obtain recording-site/access calibration and matched replicate current-step traces; identify the intrinsic or recording mechanism behind the additional response components; and verify recipient cell correspondence before any circuit integration. Time-resolved peptide release, receptor activation and downstream signaling remain separate missing measurements. The gap-free DA-WED control/MSR2-RNAi examples do not identify those kinetics.

No embodied behavior, learning, retention or restored-memory capability was added. M4 and M7 remain open at their stated biological and capability gates.

# M2 crop, filling and internal transport evidence

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

2026-09-12 UTC. **A calibrated finite-crop or initially dry feeding extension is not specified by the recovered measurements.** The supported addition is an isolated replay of a published tube-resistance calculation, with a source-spreadsheet error exposed and retained. No crop capacity, wall stiffness, muscle waveform or body-mass shortcut was invented.

## Existing mechanism and the missing physical boundary

[`ProboscisHydraulics`](../../runtime/proboscis_muscles.py) contains eight primed liquid cells and geometric pressure reactions. Its crop boundary is a supplied pressure, defaulting to zero gauge, while the cumulative signed crop flow is a transport counter. It is not a finite crop volume, material wall law or salivary reservoir. Salivary supply is closed unless a pressure is supplied. Closing the mouth boundary is not an initially dry filling model. The existing positive-liquid check correctly rejects departure from its declared primed domain; no clipping repair was introduced.

A physical finite crop requires at least `dV/dt = Q_in − Q_out` and a supported relation between **transmural** pressure, volume, wall activation and mechanical history. Internal fluid pressure alone does not identify wall stress without the surrounding pressure. The review found volume/shape, contraction-frequency and transit evidence, but no matched adult male pressure–volume–activation data from which to identify that boundary.

## Recovered measurements and permissible use

| Primary source | Recovered datum/preparation | Permissible use and open datum |
|---|---|---|
| [Solari et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5363830/) | Bioassay: 3–7-day male `yw1118`, starved 6±2 h, known ingested volumes then exposed crop. At 0/63/125/188/250 nL, reported contraction means are 9.00/29.33/18.00/16.91/12.75 min⁻¹, n=12 per volume. SE shown graphically. Preparations with no contractions were excluded. | A volume-dependent contraction reference and defined preparation. Administered maximum 250 nL is not a measured capacity, rupture limit or P(V) relation. Do not turn the frequency curve into a scripted actuator. |
| [Yang et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11398398/) | In 24-h-fasted males, optogenetic CEM activation prevents high-sucrose (~1 M) entry into the crop duct; transport resumes after stimulation. Readouts are fluorescence in oesophagus/crop-duct ROIs; Figures 5–6. | Supports crop-entry gating direction and a future causal transport assay. Normalized fluorescence is not calibrated volume, pressure, conductance or per-fiber force. Raw imaging is available from authors on request. |
| [Hadjieconomou et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7610780/) | Published microscopy-derived dimensions and a crop-suction model; source workbook recovered. Female reproductive-state comparison. Crop-area measurements and food transit sequences are provided separately. | Enables the limited resistance calculation below. It does not measure Drosophila crop pressure or compliance; the cited direct pressure comparison is from cockroach. A female post-mating result is not male physiological calibration. |
| [Wang et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC8386590/) | Crop volume estimated by flattened area × 0.18-mm spacer, or spherical diameter during pipette inflation; adult crop/IPC calcium response to distension. | Independent volume/distension assay route. Neither geometric approximation supplies transmural pressure, wall modulus or force. Full local article retrieval was incomplete; verified primary methods are indexed. |
| [Manzo et al. 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3341050/) | Approximately 6-Hz cibarial pumping; viscosity changes prolong filling. Ingestion/pump is derived from measured ingestion rate divided by frequency. MN11 inhibition can cause fluid to return to the proboscis. | Supports viscosity-sensitive flow and the distinction between pumping and net ingestion. It does not justify a one-way ideal valve or a commanded pump sequence. Absolute load/pressure and calibrated geometry remain absent. |

The [2026 TMC paper](https://www.sciencedirect.com/science/article/pii/S0965174826000639) is the current publication of the 2025 preprint and provides an additional crop-size/contraction regulation route. Its accessible primary preview does not supply a pressure–volume law. The preprint full-text route was unavailable; no unseen numerical result was imported.

## Executed source-equation reference

Files: source workbook (original artifact `program/m2/internal-state/41586_2020_2866_MOESM17_ESM.xlsx`), exact cells and provenance (original artifact `program/m2/internal-state/crop-source-inputs.json`), [runnable check](../../research/check_crop_source.py), results (original artifact `program/m2/internal-state/crop-source-results.json`), and evidence manifest (original artifact `program/m2/internal-state/evidence.json`).

```sh
python -B outputs/program/m2/internal-state/check_crop_source.py
```

`Sheet1!C305:G321` gives oesophagus radius **13 µm**, length **0.6 mm**, crop-duct radius **11.5 µm**, length **0.9 mm**, and assumed water viscosity **0.00089 Pa·s**. The sip inputs, transferred from [Itskov et al. 2014](https://www.nature.com/articles/ncomms5560), are **1.05 nL / 0.13 s**. The workbook's `crop radius`/`crop length` labels refer to the crop duct in the Methods model, not the storage lobe. Individual microscopy measurements and uncertainty are absent from this block.

The source cell **G318** contains `=-F318*(1/D311+1/D310)`. D311/D310 are lengths, making the result dimensionally `m²/s`, although labeled Pa. Its cached value is **−4.9358974×10⁻⁸**. The untouched original workbook and cached value are preserved. The Methods equation instead requires:

```text
K_i = π r_i⁴ / (8 μ L_i)
P_crop = −Q (1/K_oesophagus + 1/K_crop_duct)
```

Replaying that equation gives **K_o = 2.10035×10⁻¹⁴ m³/(Pa·s)**, **K_c = 8.57470×10⁻¹⁵ m³/(Pa·s)**, and **−1326.50 Pa** for the imposed **8.07692 nL/s** flow. Applying the source female sip ratio **0.609756** gives **−808.84 Pa**. These agree in scale with the paper's model illustration. They are calculated pressures, not measured biological data or a holdout validation.

The assay checks source identity, resistance arithmetic, fourth-power radius scaling, flow/pressure inversion and rejection of invalid dimensions. **These numerical checks pass.** The calculation assumes cylindrical Newtonian flow, a closed gut branch, zero mouth gauge pressure and prescribed crop enlargement during each sip. Turning those assumed enlargement/sip waveforms into the model's motor control would violate the intended sensory–neural–muscular mechanism.

## Dry filling, salivation and downstream transport

The [adult salivary source record](m2-salivary-source-notes.md) separates adult Drosophila anatomy from larval and other-insect measurements. Adult duct topology supports a physical supply branch, but no verified pressure-flow supply curve, secretion capacity/replenishment or duct-valve material law was recovered. The existing closed supply cannot be replaced by a numerical source pressure without those data.

An initially dry model additionally needs the actual initially wetted regions, gas escape/trapping, lumen geometry, liquid surface tension and advancing/receding contact angles under the chosen food/saliva condition. Cavitation needs absolute pressure and relevant phase/nucleation assumptions. Water properties alone cannot identify the wetting of a biological cuticular lumen. Refilling the currently primed cells or treating negative pressure as an instruction to add liquid would create material without a physical route.

Storage, crop-to-midgut transport, nutrient absorption and elimination remain separate mechanisms. Dye arrival and contraction counts do not identify a secretion rate, nutrient permeability or absorption timescale. Cumulative crop boundary flow is not assimilated energy or an instruction to increase rigid-body mass at an arbitrary location.

## Exact next measurements and source actions

1. Obtain synchronized adult male crop **volume and luminal/hemolymph pressure** through loading/unloading, with known wall activation, rest state, temperature, food and source geometry. Include passive and active trials, relaxation/hysteresis and outflow. This identifies a conservative reservoir's wall relation and domain; a largest meal is insufficient.
2. Obtain the per-specimen oesophagus/crop-duct geometry and clarify Hadjieconomou ED10 G318 references. Request absolute flow or tracer-volume calibration for the Yang CEM manipulation. These data can constrain resistance and gating without selecting a force gain from successful ingestion.
3. Obtain adult Drosophila saliva secretion volume/flow versus pressure, reservoir/replenishment and actual duct/valve dimensions. For dry filling, measure advancing fronts and gas evacuation at known pressure and food composition, with matching wetting properties.
4. Keep independent pressure/volume trajectories and food conditions untouched during calibration. No appropriate physical holdout set has yet been recovered or used.

The completed deliverable is source recovery plus the isolated numerical reference. **No calibrated finite-storage, initially dry filling, salivary transport, nutrient assimilation or elimination mechanism has been implemented or demonstrated. M2 remains open at these named data boundaries.**

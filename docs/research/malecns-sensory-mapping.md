# MaleCNS v1 sensory identities and physical-input coverage

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

This mapping contains **all 17,937 curated entries whose `superclass` contains `sensory`**, including uncertain and incompletely traced entries. It supplies exact MaleCNS `bodyId` values and input gaps for the complete graph; it does not select an action circuit. The mapping is recorded in `malecns-sensory-map.json` (historical provenance archive). It establishes anatomical correspondences without executing a sensory simulation.

**Mapping result:** primary receptor-marker evidence and Supplementary Table 2 support 34 sugar-responsive LB3b/c IDs and 38 bitter LB1a–d IDs. Measured connectivity supports 3,239 inferred R1–R6 column assignments; exact author optical exports complete 5,713 receptor-to-direction chains. The remaining 378 compound-eye entries lack a complete direction chain, and the mapping does not establish native sensory transduction.

The primary source is the [official v1 bulk release](https://male-cns.janelia.org/download/). The JSON records source URLs and SHA-256 hashes, all 17,937 rows, 473 distinct superclass/class/subclass/type combinations, every row's coverage status, 1,772 official optic-column records, primary-companion labellar identities, measured R1–R6→L1 edge evidence, and author-supplied viewing directions. IDs are MaleCNS body IDs, never guessed FlyWire roots. `flywireType` and `mancType` identify corresponding types or groups across specimens; they are not individual-neuron identity maps. Comma-combined types, `putative_` receptor labels, `unknown` sides, and nulls remain unchanged.

## Complete inventory

Counts below come directly from the frozen annotation Feather. This is an inventory of annotated segments, not a claim that every entry is a complete neuron: 15,912 have `status=Traced`, 1,987 have null status, 35 are anchors, and three are orphans. Of 6,091 compound-eye photoreceptor entries, 4,107 are traced, 1,983 have null status, and one is an anchor. An importer that retains only traced entries will lose those other records; that decision must be reported, not described as full receptor coverage. There are 129 sensory IDs without a matching neurotransmitter-table record. The historical 167,216-entry prepared graph retained all 17,937 sensory entries, including untraced/uncertain records.

| Exact curated class | Entries | Physical-input coverage at this snapshot |
|---|---:|---|
| `visual` | 6,091 | 5,867 column assignments with measured/inferred evidence separated; 5,713 have author viewing directions; native registration and phototransduction missing |
| `olfactory` | 2,639 | Five existing ORN types can reuse an explicitly estimated plume/rate template for 269 sided IDs; other chemical tuning and 411 unresolved sides remain |
| `mechanosensory_tactile` | 2,558 | Bristle classes identified; receptor sites, deflection mechanics and tuning missing |
| `mechanosensory` | 1,733 | Johnston's organ, head/mouth bristles and pharyngeal mechanics identified broadly; no physical transduction |
| `unknown_sensory` | 1,712 | Retained without assigning a stimulus |
| `mechanosensory_proprioceptive` | 1,454 | Chordotonal, campaniform, hair-plate, wing/haltere/body families; individual physical mapping missing |
| `gustatory` | 1,428 | 34 sugar-responsive and 38 bitter IDs supported by primary companion; water, amino-acid and high-salt groups separated; physical transduction remains estimated/missing |
| null | 162 | Includes seven `HBeyelet` cells and 155 other unclassified entries |
| `hygrosensory` | 66 | Exact VP types; humidity/evaporation field and transduction missing |
| `chemosensory` | 58 | Broad class does not establish a particular chemical or nociceptive stimulus |
| `thermosensory` | 25 | Seven VP2 heating receptors; VP3 cooling classes; VP1m is humid in the crosswalk despite its class label |
| `mechanosensory_tbc` | 11 | Tentative modality retained |

All sensory superclasses are included: `cb_sensory` 4,868; `ol_sensory` 6,098; `vnc_sensory` 6,370; `sensory_ascending` 537; `sensory_descending` 12; `cb_sensory_tbc` 14; `vnc_sensory_tbc` 36; `sensory_ascending_tbc` two. The JSON's `neurons` is a table represented by `columns` and `rows`; `type_inventory` enumerates every class/type combination and its side, nerve, crosswalk, and coverage counts. Neither table filters on downstream motor activity.

## Olfaction and independent contact taste

The five food-odor types used in the baseline have **the same names in MaleCNS v1**. Both `type` and `flywireType` equal the corresponding FlyWire name. These are the historical baseline's mixture channels, not an exhaustive list of food-responsive ORNs or a chemical identity model.

| FlyWire name → MaleCNS name | Left | Right | Unknown side | Total |
|---|---:|---:|---:|---:|
| `ORN_DM1` → `ORN_DM1` | 35 | 39 | 0 | 74 |
| `ORN_DM2` → `ORN_DM2` | 24 | 29 | 1 | 54 |
| `ORN_DM4` → `ORN_DM4` | 16 | 15 | 1 | 32 |
| `ORN_VM2` → `ORN_VM2` | 17 | 20 | 4 | 41 |
| `ORN_VA2` → `ORN_VA2` | 33 | 41 | 9 | 83 |
| Total | 125 | 144 | 15 | 284 |

Exact ID arrays, including withheld unknown sides, are in the corresponding `input_groups`. Use `rootSide`, not soma side or the side of a central arbor, for antennal origin. Retain the 15 unresolved IDs in the graph without assigning an antenna. Across all olfactory entries, 2,455 enter through `AN` and 184 through `MxLbN`; the latter include `ORN_VA4`, `ORN_VA7l`, `ORN_VC1`, `ORN_VC2`, `ORN_VM7d`, and `ORN_VM7v`. The baseline's two antennal field samples do not establish palp sampling. One `ORN_VA7l` entry is annotated `AN`; preserve that row rather than silently correcting it from the majority.

The baseline Gaussian plume and Poisson input scheme are explicit transduction estimates. There is one generic odor scalar per antenna, not measured concentrations of separate compounds or a receptor-specific response matrix. Do not drive every ORN with that scalar. Four olfactory entries lack a type; 411 lack a resolved side. Exact IDs do not resolve chemical tuning, basal firing, adaptation, or concentration-to-rate constants.

The [official FlyWire annotation snapshot](https://github.com/flyconnectome/flywire_annotations/blob/8587524c1748ce5ef2080822a2fc890fc03bf597/supplemental_files/Supplemental_file1_neuron_annotations.tsv) remains an exact name/group crosswalk, but its coarse quality labels are not the final functional authority. The primary [taste companion, version 2, Results and Figure 2E/G](https://europepmc.org/article/PPR/PPR1072256#S6), provides subtype-level functional evidence. Its [Supplementary Table 2](https://europepmc.org/api/fulltextRepo?pprId=PPR1072256&type=FILE&fileName=EMS208214-supplement-Supplemental_table_2.xlsx&mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&version=2) was checked against the frozen v1 annotation file. **All 164 explicitly subtyped labellar IDs match exactly**, including side. These primary subtype assignments resolve the sugar/water ambiguity independently of motor output.

| MaleCNS subtype | Exact IDs counted | Independent identity evidence | Functional interpretation |
|---|---:|---|---|
| `LB1a–d` | 38 | Authors' Gr33a-GAL4 projection matches | Bitter |
| `LB1e` | 19 | Ir94e morphology and cited receptor physiology | Amino acids including glutamate; not generic bitter |
| `LB3a` | 17 | ppk28-GAL4 projection match | Water |
| `LB3b` | 11 | Gr64f-GAL4 and Ir56b-GAL4 projection matches | Sugar **and** low salt |
| `LB3c` | 23 | Gr64f-GAL4 projection match | Sugar-responsive; exclusivity to sugar is not established |
| `LB3d` | 26 | Ir7c/ppk23/Ir47a morphology and receptor evidence | High salt / heavy-metal ions |
| `LB2a–d` | 18 | Authors found no clear receptor-driver match | Quality unresolved |
| `LB4a/b` | 12 | Authors found no clear receptor-driver match | Quality unresolved |

The historical map's `contact_sugar` group contains **34 exact LB3b/c IDs**. `contact_bitter` contains **38 exact LB1a–d IDs**, replacing the earlier 56-cell coarse crosswalk group; the 18 formerly eligible LB1e entries are removed from generic bitter input. All 19 LB1e cells remain in the complete graph and the amino-acid inventory. `contact_water` contains 17 LB3a IDs, and high-salt/heavy-metal input is kept separate. Two residual generic/untyped old LB3 entries remain unresolved; no fine subtype is invented for them. Older labels such as LB1e=bitter, LB3=sugar/water and LB2/LB4a=low-salt are preserved as raw source metadata, while `primary_taste_companion` and each neuron's updated `coverage_id` record the better-supported functional interpretation.

The paper describes these receptor matches as proposals/likely correspondences. The IDs and published subtype membership are exact; the subtype-to-physiology link is a published inference, not an in-vivo recording from each reconstructed neuron. A sugar stimulus can therefore be assigned to the identified LB3b/c population using explicitly estimated transduction. “Pure sugar” must not mean “these cells respond exclusively to sugar”: LB3b also has low-salt evidence, and the study does not establish a complete ligand-exclusivity profile for LB3c. No physiological firing-rate constants or action-fitted gains were added.

The supplementary GRN sheet has 2,972 rows across three connectomes and 1,441 maleCNS rows. Eleven non-labellar source IDs are absent from the frozen v1 annotations; they are listed in the JSON without replacement or remapping. This follow-up does not revise unrelated leg/wing/peg qualities from that sheet. The existing 200 Hz contact template remains a modeling estimate, not a result of the paper.

The remaining inventory includes `LgAG1–9`, `LgLG1a/b,2–8`, `WG1–4`, `PhG1a/b/c,2–16`, `claw_tpGRN`, `dorsal_tpGRN`, and uncertain types. `WG1–4` account for 385 wing taste entries, separate from wing mechanics. `putative_IR52b`, `putative_ppk23`, and `putative_ppk25` remain putative; none is renamed sugar or bitter. Contact on a foot, wing, labellar peg, or pharynx is not established by collision with the coarse `c_haustellum` geometry. Independent local contact and chemical concentration are required. The existing chemical fields remain independent: changing taste must not change the odor plume, and airborne odor must not activate contact taste.

## Heating, cooling, humidity and nociception

| Exact type | Left / right / unknown | Interpretation and gap |
|---|---|---|
| `TRN_VP2` | 4 / 3 / 0 | Heating; existing antenna temperature/warmth template reusable with estimated transduction |
| `TRN_VP3a` | 3 / 3 / 0 | Cold/cooling; aristal family; response dynamics unimplemented |
| `TRN_VP3b` | 0 / 1 / 0 | Cold/cooling; do not invent a left partner or copy VP3a tuning |
| `TRN_VP1m` | 5 / 6 / 0 | Humid; do not drive it with warmth because its class says thermosensory |
| `HRN_VP1d` | 10 / 8 / 0 | Putative evaporative cooling; humidity-dependent mechanism missing |
| `HRN_VP1l` | 2 / 6 / 0 | Putative saccular cooling; not identical to aristal VP3 |
| `HRN_VP4` | 13 / 14 / 1 | Dry; missing humidity field and one origin side |
| `HRN_VP5` | 4 / 8 / 0 | Moist; missing humidity field |

These distinctions are supported by the official type crosswalk and [Marin et al.'s primary thermo/hygrosensory study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7443704/). The latter marks several saccular functions as putative. The existing field samples at the funiculus are only a spatial approximation to aristal/saccular receptors. Its 22–45 °C source bounds and 22 °C ambient cannot generate below-ambient cooling. The 30 °C warmth onset, 40 °C full scale, and 200 Hz ceiling are modeling estimates, not physiological constants recovered here. Labellar cooling, internal temperature, tissue damage, and NMJ temperature dependence are separate missing mechanisms.

`nociception_candidates_not_confirmed` lists the exact 59 entries named `SNch01`, `SNxx29`, or `SNxx27,SNxx29`. The [MANC annotation paper](https://elifesciences.org/reviewed-preprints/97766v1) discusses candidate abdominal and leg nociceptive families; this is not proof of an individual MaleCNS heat receptor or a calibrated damage model. The native class labels remain `chemosensory`/`unknown_sensory`, and the combined type remains unresolved. **No temperature-to-pain or heat-to-escape path is supplied.**

## Vision and retinotopy

Exact photoreceptor counts are `R1-R6` 3,377; `R7p` 332; `R7y` 482; `R7d` 82; `R7_unclear` 404; `R8p` 330; `R8y` 481; `R8d` 76; `R8_unclear` 442; `R7R8_unclear` 85. Seven additional `HBeyelet` cells remain separate. Every sensory row has null `assignedOlHex1/2` in the bulk annotation file; independent resources and synaptic evidence are therefore required.

The authors' [official optic-column table](https://github.com/flyconnectome/2025malecns/blob/67767d2233657983993ff6c2be48e836a935863c/supplemental_data/optic-column-type-assignments-v1.0.xlsx) supplies these direct links, embedded unchanged except that source `-99` sentinels become null:

| Side | Columns | L1 anchors | R7 IDs | R8 IDs |
|---|---:|---:|---:|---:|
| Left | 880 | 872 | 608 | 625 |
| Right | 892 | 892 | 691 | 704 |

All positive IDs exist in v1; receptor types and sides match. These are **2,628 official R7/R8-to-column links**. L1 IDs are anatomical anchors, never replacement light-input targets. The table does not assign R1–R6, 85 `R7R8_unclear` entries, or `R7_unclear` bodyId **163975**. Its pale/yellow/edge/DRA labels are not receptor spectra or polarization tuning.

### R1–R6 cartridge inference from measured connectivity

The inference used the prepared graph with **postsynaptic rows and presynaptic columns**. `synapse_count` retains the released positive counts, before simulation signs or gains. Both files' hashes were checked against the prepared manifest and recorded in `sources.prepared_graph`:

- `neurons.feather`: `10fa864a4de8e9c857e0a9bfcb78e70910818047bd632b51db8cb3a7692a0e71`
- `connectome.npz`: `8a48ac6232523652ff21efdc65b2e6986aa9e584b3cf25a121f72f53d5d32652`

For every one of the 3,377 R1–R6 entries, collect **all** outgoing synapses to annotated L1 cells. A column is inferred only when there is one unique maximum, that maximum is a strict majority of the entry's total L1-directed synapses, the winning L1 has exactly one official column, and sides agree. No spatial distance, desired visual response, motor output or gain fitting is used. Ties and competing targets are retained explicitly; sorting IDs only orders the evidence.

This method is anatomically motivated by primary [lamina cartridge reconstruction](https://doi.org/10.1002/cne.903050206) and [quantitative cartridge connectivity](https://pmc.ncbi.nlm.nih.gov/articles/PMC3244492/): R1–R6 terminals supply L1/L2 within a cartridge. Under neural superposition, the shared cartridge is the relevant optical direction, not a guessed common retinal ommatidium. **The counts are measured released connectome data; the receptor-to-column assignment is an inference.** It does not establish the individual R1/R2/…/R6 subtype, prove an intact cell, or validate the entire optical model.

| Outcome | R1–R6 entries |
|---|---:|
| Unique dominant L1 with official column and agreeing side | **3,239** |
| Dominant L1 exists but lacks a unique official column | 13 |
| No R1–R6→L1 synapses in the prepared graph | 125 |
| Tied maximum, non-majority maximum, or side conflict | 0 |

There are 3,280 R1–R6→L1 edges involving 3,252 presynaptic entries. Of these entries, 3,230 have just one L1 target and 22 have multiple L1 targets. The smallest dominant fraction is **0.5087719298**; five entries have only one synapse supporting their strongest target. No arbitrary confidence cutoff is imposed: the JSON records complete target/count lists, total counts, top/runner-up counts, top ties, fractions and single-synapse flags for review. Cartridges receive between one and ten assigned entries; the map does not force the expected six terminals by deleting fragments or inventing missing cells.

### Exact author viewing-direction export

The full-text/source search found [Arthur Zhao's Eyemap Archive](https://github.com/artxz/eyemap-archive), pinned to commit `503c7f055d5491a48b60b49ade8c71798d24d8f1`. Its [manifest](https://raw.githubusercontent.com/artxz/eyemap-archive/503c7f055d5491a48b60b49ade8c71798d24d8f1/docs/manifest.json) identifies a standard `eyemap_mcns_f20240701` export and a separate `eyemap_DRA_mcns_f20240701` variant. The exact standard resources are [left CSV](https://raw.githubusercontent.com/artxz/eyemap-archive/503c7f055d5491a48b60b49ade8c71798d24d8f1/docs/data/eyemap_mcns_f20240701/left.csv) and [right CSV](https://raw.githubusercontent.com/artxz/eyemap-archive/503c7f055d5491a48b60b49ade8c71798d24d8f1/docs/data/eyemap_mcns_f20240701/right.csv). Both were read in full, hashed and embedded.

These CSVs explicitly provide `hex1,hex2` alongside `p,q,x,y,z,theta,phi`. **Join by `(side, hex1, hex2)` to the official column-name suffix.** `p,q` uses a different oblique lattice system and must not be substituted. This closes the prior optical-direction retrieval gap without inventing a nearest-column link.

| Standard export | Source rows | Exact official-column matches | Official columns lacking vectors |
|---|---:|---:|---:|
| Left | 850 | 848 | 32 |
| Right | 846 | 846 | 46 |
| Total | 1,696 | **1,694** | **78** |

Two left source rows, `(hex1,hex2)=(3,4)` and `(2,5)`, have no official column and remain unassigned. The [author's coordinate documentation](https://raw.githubusercontent.com/artxz/eyemap-archive/503c7f055d5491a48b60b49ade8c71798d24d8f1/docs/index.html) specifies **+x forward, +y left, +z up/dorsal**. Source vectors are preserved at CSV precision; their norms differ from unity by less than `1e-6`. The supplied degree angles satisfy `theta≈acos(z)` and `phi≈-atan2(y,x)` within rounding, so a runtime should use the Cartesian vectors rather than assume its own azimuth sign convention.

The DRA variant is also retained, with its own sources and rows. Its right export agrees with the standard map, but its 816 shared left-eye hex positions differ in viewing direction by **1.643–9.070°**, median **4.821°**. The standard maleCNS export is the declared map for this artifact. The DRA registration is not automatically substituted for DRA receptor types or used to fill missing standard columns; doing either would hide an anatomical registration choice.

The eye-map data and derived eye-map joins in the JSON carry the source **CC BY-SA 4.0** attribution to Arthur Zhao / Reiser Lab, [Zhao et al. 2025](https://www.nature.com/articles/s41586-025-09276-5) and [Nern et al. 2025](https://doi.org/10.1038/s41586-025-08746-0). This attribution concerns the embedded eye-map material, not unrelated runtime code.

### Per-receptor coverage and remaining physiology

`receptor_column_coverage` enumerates all 6,091 compound-eye entries, labels each column assignment as `official_R7_R8_table`, `inferred_dominant_L1`, or `unmapped`, and records whether the assigned column has an author vector:

- **5,867** have a column: 2,628 official R7/R8 links plus 3,239 inferred R1–R6 links.
- **224** still lack a column: 125 without L1 synapses, 13 without an official L1 anchor, 85 `R7R8_unclear`, and one `R7_unclear`.
- **5,713** have both a column and a standard author viewing vector; 154 additional column-mapped entries lack a vector. Therefore **378** compound-eye entries still lack a complete identity-to-direction chain.

The earlier `unmapped_compound_photoreceptor_body_ids` field retains its direct-table-only meaning; `unmapped_after_inference_body_ids` and `receptor_column_coverage` are the updated coverage authority. All seven `HBeyelet` cells remain separately unmapped. No explicitly typed ocellar primary receptors were found in the sensory subset; OCG interneurons are not substitute receptors.

The inspected FlyGym `vision.yaml` configuration uses 721 ommatidia per eye; that indexing is not equated with MaleCNS columns. The author vectors permit explicit directional sampling. The subsequent [visual-input study](whole-cns-visual-dynamics.md) describes estimated head-frame registration; acceptance angles and calibrated phototransduction remain separate requirements. `flygym_ommatidium_to_column` and `flygym_registration` remain null. The mapping study did not execute an optical simulation.

All 6,098 `ol_sensory` entries have official `consensus_nt=histamine`. [Graded histaminergic retinal signaling](https://pmc.ncbi.nlm.nih.gov/articles/PMC4801898/), baseline release, adaptation, spectral sensitivity and polarization are still physiological work. A Poisson/LIF approximation would require an explicit modeling label; identity and direction data do not turn it into measured phototransduction or establish normal vision, walking, or flight.

## Leg, wing, haltere, head and body mechanics

The following **nerve inventories include all their sensory modalities and uncertain rows**. They are broader than the mechanosensory coverage groups and must not be summed with overlapping class counts.

| Peripheral entry | All entries | Curated class breakdown |
|---|---:|---|
| Wing `ADMN` | 1,000 | 237 proprioceptive; 352 tactile; 385 gustatory; 26 unknown |
| Haltere `DMetaN` | 439 | 396 proprioceptive; 39 tactile; four unknown |
| Notum `PDMN` | 282 | 12 proprioceptive; 264 tactile; six unknown |
| Abdominal `AbN1/2/3/4/T` | 1,144 | 66 proprioceptive; 37 chemosensory; 1,040 unknown; one unclassified |
| Foreleg-region `ProLN` | 992 | Includes gustatory, tactile, proprioceptive, chemical and uncertain inputs |
| Middle-leg `MesoLN` | 1,402 | Same broad modalities |
| Hind-leg `MetaLN` | 1,521 | Same broad modalities |

Entry nerve establishes a region, not a sensor's exact location. In particular, a generic `mechanosensory bristle` or `campaniform sensilla` subclass is not enough to decide which joint or wing surface it monitors. Nerve anatomy and family interpretations follow the [primary MANC annotation work](https://elifesciences.org/reviewed-preprints/97766v1); the JSON always keeps the actual MaleCNS annotations as authority for IDs.

For leg proprioception, curated synonyms identify members of `SNpp50/51` as FeCO claw; `SNpp39/41` as FeCO hook; and `SNpp40/47/56/57/60` as FeCO club. The candidate type inventories contain 94, 61 and 138 entries respectively, including rows with a less certain class; `direct_synonym_body_ids` distinguishes the cells actually carrying the synonym. [Mamiya et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6481666/) and [Chen et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8665017/) support claw position sensitivity, hook directional movement sensitivity, and club movement/vibration sensitivity. They do not resolve each MaleCNS cell's preferred angle, flexion/extension sign, vibration frequency, gain or hysteresis. A single joint angle broadcast to every FeCO cell would erase these distinctions.

Campaniform neurons require local cuticular strain; hair plates and tactile hairs require location- and direction-specific deflection; chordotonal neurons require motion transferred through their attachment mechanics. The inventory retains all `SApp*`, `SNpp*`, `SNta*` and unresolved combined types. Additional `PrN`, `ProCN`, `ProAN`, `DProN`, and `VProN` entries remain in the complete table. A whole-foot contact force is not a measured strain at every sensillum.

Wing feedback requires wing/hinge load transfer and actual receptor sites. Haltere feedback requires base/shaft mechanics and knob-hair contact, including the mechanical effects of motion. Body angular velocity alone does not determine each haltere afferent's spikes. Head/body inputs also include the `BM*` bristle families, `TPMN1/2`, `aPhM1–5`, and JO auditory, wind/gravity and grooming-labeled populations. Their input must be physical displacement or vibration at the identified organ. `grooming` is a source annotation, not an encoded motor command. Pharyngeal deformation and abdominal organ mechanics are not measured by the current rostrum hinge.

At the time of this mapping study, the body model was a tethered one-muscle assay. Native segment poses alone do not provide articulated legs, wing/haltere dynamics, compliant bristles, sensillum strain, sound or airflow mechanics. MuJoCo joint states, velocities and contact forces can supply physical observables after body integration, but sensor geometry and transduction remain separate work. **No gait, wingbeat trajectory, target angle, default drive, takeoff trigger, or motor action is encoded in these artifacts.** Constitutive mechanics specify how loads deform tissue and how receptors respond; an action script specifies what movement to perform. Only the former is an admissible future input model.

## Integration contract and historical integrity check

Join the entire sensory inventory to the full MaleCNS graph by `bodyId`; never use this inventory to prune graph connectivity. `coverage_id` describes each entry's external-input gap, while recurrent/synaptic inputs remain part of the neural model. `can_reuse_after_id_join` means an existing **estimated** physical source template is available, not that the channel is implemented or validated. The mapping's historical `currently_wired_to_malecns` flags are false; they are not a current runtime coverage measure. After the bounded follow-up, existing estimated templates can target 269 sided food-mixture ORNs, 34 primary-companion sugar-responsive LB3b/c entries, 38 LB1a–d bitter entries, and seven warmth receptors. Vision identities/directions have the coverage stated above; native optical transduction, articulated mechanosensation, humidity and additional chemical fields remain unimplemented.

The historical check used pandas, NumPy and the standard library to compare preserved annotation rows, source hashes, primary taste and eye tables, exact author-vector joins, and every R1–R6 inference against the prepared graph. Synthetic cases covered ties and absent evidence; observed assignments contained no tied maxima. This checks data integrity, not whole-animal behavior.

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The historical check passed on 2026-09-11 against annotation and neurotransmitter sources, both primary workbooks, all four author eye-map CSVs, and the prepared graph. This result establishes mapping integrity only. It is not a new package-check result.

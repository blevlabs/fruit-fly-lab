# MaleCNS v1.0 motor-to-muscle mapping

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

Historical mapping snapshot, 2026-09-11. **815/815 annotated motor neurons are retained: 107 cb_motor and 708 vnc_motor.** A named muscle or muscle-family target is supported for **472 (57.9%)**; **343 (42.1%) remain unmapped to an identified muscle**. The 472 comprise 368 named muscle/group labels and 104 family/bundle-level assignments. A supported target plus one or two anatomically identified output sides exists for 460 neurons; six additional CEM rows have an unpaired-organ-group target topology. The single-side scalar is populated for 450 named-target neurons. These are anatomical correspondences, not 472 independently resolved motor units or functioning physical connections.

The complete per-body inventory is malecns-motor-map.json (historical source `malecns-motor-map.json`). It preserves official fields, target/side evidence, missing entries, transmitter predictions, rejected predicted matches and candidate mechanics names. **This assignment created zero runtime bindings, synaptic edges, NMJ edges, controllers or simulated behavior.**

## Population and coverage

The selector is exactly superclass in {cb_motor, vnc_motor} in the official 211,577-row annotation file, without filtering by transmitter, reconstruction status, type, region or available actuator. Endocrine/efferent/ENS classes outside this selector are not reclassified as motors; this inventory does not assert that every peripheral effector has been identified. [Official v1.0 bulk sources](https://male-cns.janelia.org/download/).

| Official subclass / system | All MNs | Named target or family | Muscle unmapped | Peripheral side resolved |
|---|---:|---:|---:|---:|
| fl: front legs | 135 | 133 | 2 | 133 |
| ml: middle legs | 116 | 92 | 24 | 116 |
| hl: hind legs | 130 | 103 | 27 | 124 |
| wm: wings / flight / jump | 67 | 62 | 5 | 66 |
| hm: halteres | 16 | 10 | 6 | 16 |
| nm: neck, brain and VNC | 44 | 18 | 26 | 28 |
| ad: abdomen | 214 | 0 | 214 | 183 |
| am: antennae | 13 | 0 | 13 | 0 |
| pm: proboscis / crop entry | 67 | 54 | 13 | 32 |
| rm: retina | 7 | 0 | 7 | 0 |
| xm: unknown peripheral target | 6 | 0 | 6 | 6 |

The 343 muscle-unmapped entries comprise 266 with only regional source targets and 77 with no assigned muscle label. All 214 abdominal MNs remain unmapped to individual muscles: abdomen/A1/A2 are regional labels. All 13 antennal, 7 retinal and 6 xm rows remain muscle-unmapped. Knowing an exit side does not identify a muscle. [Cheong et al., identification and Supplementary file 3](https://doi.org/10.7554/eLife.96084.3).

## Identity, joins and evidence rules

| Field | Meaning and permitted use |
|---|---|
| bodyId | Primary integer key into male-cns:v1.0, joined to the importer node IDs or body/body_pre/body_post fields; never a FlyWire root ID. |
| mancGroup | Curated anatomical group; joins Cheong Supplementary file 3 group. Bilateral/group identity never licenses copying spikes. |
| type, mancType, subclass | Exact current official type plus system can resolve unambiguous targets when a curated group is unavailable. Multiple cells retain distinct rows. |
| mancBodyid | **Predicted and untrusted for target/side assignment.** Source match and disagreement flags are retained only for audit. |
| mancSerial, mcnsSerial, group, flywireType | Nonunique anatomical/type context, not an individual muscle, fiber or interchangeable neuron. |
| side, somaSide | Official soma side only. rootSide is null throughout. |
| peripheral_target_side | Compatibility scalar, only L/R for unilateral outputs; null also occurs for anatomically bilateral outputs. Read peripheral_target_sides and topology. |
| peripheral_target_sides | Canonical array: [L] or [R] for unilateral; [L,R] for demonstrated bilateral innervation; [] for unresolved or an unpaired-organ-group target, distinguished by topology. |
| peripheral_target_topology | unilateral, bilateral, unpaired_organ_group, or unresolved. CEM organ-group topology does not resolve individual circumferential fibers. |
| semantic_muscle_key | Normalized muscle/group at the stated resolution; not an actuator ID or motor-unit force weight. |
| cheong_support_csv_rows | One-based CSV line numbers including header; source confidence, publication and notes remain auditable. |

The bulk MaleCNS file has **no target column**. maleCNS_target_field is therefore null; official_crosswalk_targets preserves MANC labels and target records the anatomical result. Curated group/type assignments precede supplementary anatomy refinements. Source metadata include hashes for the actual bulk annotations, NT, MANC supplements and installed FlyMimic asset.

There are 483 populated curated mancGroup fields and 673 predicted mancBodyid fields. Predicted body matches produce 140 literal type disagreements with the inspected source; this is an audit count, not a calibrated error rate. The authors' software explicitly warns that a significant fraction of predicted body matches are wrong. [MaleCNS matching documentation](https://natverse.org/malecns/reference/mcns_predict_group.html).

MANC muscles lie outside its EM volume. Its target identities come from primary light-microscopy matching and, for additional leg segments, serial homology. This is the published anatomical correspondence, not a newly retraced MaleCNS axon-to-muscle continuity proof. [Cheong Supplementary file 3](https://cdn.elifesciences.org/articles/96084/elife-96084-supp3-v2.csv), [serial leg groups, file 6](https://cdn.elifesciences.org/articles/96084/elife-96084-supp6-v2.csv).

## Peripheral side, including flight crossing

Side uses Cheong MANC exit_nerve plus the same MANC body's somaSide in the author-provided Pugliese MANC table. That soma-to-exit relationship is transferred through curated MaleCNS mancGroup, or exact official type/subclass where every supporting motor row has complete and consistent evidence. Otherwise the side remains null. Predicted mancBodyid never assigns side. [Pinned Pugliese MANC source](https://github.com/smpuglie/Pugliese_2026/blob/faee4b06869855ae0164cbf217fb6ec28ef3521b/data/manc%20full%20vnc%20data/wTable_20260522_allSynapses.feather).

**82/83 wing/haltere output sides are supported; 72/83 have both a named target and side.** The final join excludes nonmotor MANC rows, resolving the two MNwm35 sides left unresolved by the initial mixed-class check. Their exact muscle targets are still unknown. Body 807987 remains both target- and side-unresolved.

| MaleCNS bodyId | Type | Soma | Peripheral side | Evidence |
|---:|---|:---:|:---:|---|
| 801295 | DLMn a, b | R | **L** | Curated group 10074; MANC 10589 has RHS soma and PDMNa_L exit. |
| 801970 | DLMn a, b | L | **R** | Same group; MANC 10074 has LHS soma and PDMNa_R exit. |
| 800190 | MNwm35 | R | R | Exact MNwm35/wm type correspondence to Cheong group 11991; ipsilateral source relation; target only wing. |
| 800606 | MNwm35 | L | L | Same type-based source match; exact muscle unknown. |
| 807987 | null | R | **null** | No curated type/target crosswalk; biological variability mcns note retained. |

For named positioning-muscle families MN1/MN2/MN3/MN4/MN9, output side follows the anatomical ipsilateral rule and official neuron side. This never copies another hemisphere's activity. Revision 2 separately establishes CvN4/5 ipsilateral and CvN6/7 contralateral innervation, MN6–8 ipsilateral innervation, and bilateral MN5/MN10/MN11D/MN11V outputs. It does not generalize an ipsilateral rule to the whole brain or all proboscis neurons. [McKellar anatomy/Table 1](https://elifesciences.org/articles/54978), [Schwarz MN9 Fig. 3C](https://elifesciences.org/articles/19892).

## Actual MN9 and every proboscis/crop row

**Left MN9 = MaleCNS 10331; right MN9 = 16949.** Both carry flywireType CB0701 but need separate neuronal state/spikes. The existing Eon right-MN9 FlyWire root 720575940660219265 is a different dataset identifier, not a replacement for either bodyId. No graph bridge is added.

The table includes all 67 pm bodies. IDs are grouped by soma side; the last column specifies output-side evidence. Targets use McKellar 2020 nomenclature, including m11V (formerly 12-1) and m12D. MN2Da/MN2Db identify only the m2D parent family; MN4a/MN4b identify only m4. Their a/b labels do not establish separate fibers or force allocation. [McKellar Table 1](https://elifesciences.org/articles/54978#table1).

| Official type | Left soma bodyIds | Right soma bodyIds | Target / output-side evidence |
|---|---|---|---|
| CEM | 19823, 20518, 32852, 482595 | 23511, 34597 | crop-entry muscles; unpaired organ group; fiber partition unresolved |
| MN1 | 11084, 15530 | 580748, 102317324 | m1; ipsilateral |
| MN10 | 925726 | 11861, 515060 | m10; **bilateral L+R** |
| MN11D | 551398 | 11269, 11393 | m11D; **bilateral L+R** |
| MN11V | 49829 | 492462351 | m11V; **bilateral L+R** |
| MN12D | 14237, 533967 | 10619, 440899 | m12D; output side unresolved |
| MN13 | 14907 | 30780 | m13; output side unresolved |
| MN2Da | 14780 | 517268 | m2D; ipsilateral; parent family only |
| MN2Db | 17281 | 10538 | m2D; ipsilateral; parent family only |
| MN2V | 555796 | 519878 | m2V; ipsilateral |
| MN3L | 269067, 556589 | 85275, 511990 | m3L; ipsilateral |
| MN3M | 94688 | 524799 | m3M; ipsilateral |
| MN4a | 18295, 36368 | 27938, 522704 | m4; ipsilateral; parent family only |
| MN4b | 518650 | 11450 | m4; ipsilateral; parent family only |
| MN5 | 535501 | 13359 | m5; **bilateral L+R** |
| MN6 | 924612 | 519667 | m6; ipsilateral |
| MN7 | 16134, 16892 | 17495, 32092 | m7; ipsilateral |
| MN8 | 16827 | 20173 | m8; ipsilateral |
| MN9 | 10331 | 16949 | m9; ipsilateral |
| MNx01 | 101002, 512877, 533971 | 19296 | **unmapped** |
| MNx02 | 10047 | 26137 | **unmapped** |
| MNx03 | 16361, 20600 | 24511 | **unmapped** |
| MNx04 | 1004417640 | 200682 | **unmapped** |
| MNx05 | 917601 | 24808 | **unmapped** |

**MN12V → m12V appears in adult anatomy, but no selected MaleCNS motor is officially typed MN12V.** All 13 MNx01–MNx05 bodies remain muscle-unmapped. None is renamed MN12V. Six CEM bodies identify crop-entry musculature as a group, not a numbered proboscis muscle or resolved left/right gut fiber. [CEM primary anatomy, Fig. 5](https://pmc.ncbi.nlm.nih.gov/articles/PMC11398398/).

Exact neck targets recovered: CvN4 → VL2; CvN5/CvN6/CvN7 → VL1; ADNM1/ADNM2 → TH1/TH2; FNM2 → AD; curated MANC group 45594 (MaleCNS MNnm03) → DProN4 → LEV; group 11059 (MNnm08) → DProN5 → AD. The latter use actual EM IDs in Table 2 and anatomy in Figs. 15–16. Other GNG and systematic neck targets remain missing. [Gorko supplementary Table 2 and Figs. 4–7, 15–16](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07222-5/MediaObjects/41586_2024_7222_MOESM1_ESM.pdf).

## Every wing and haltere motor row

L/R below mean **peripheral** side, not soma. DLM/DVM labels retain unresolved individual fibers and independent neurons. STTMm and TTMn retain Cheong's TTM target as distinct neurons; neither is relabelled DLM or assigned asynchronous power dynamics. No row is connected to a physical actuator by this artifact.

| bodyId | Official type | Peripheral side | Source/anatomical target |
|---:|---|:---:|---|
| 800056 | DVMn 1a-c | R | DVM 1a-c |
| 800146 | TTMn | R | TTM |
| 800184 | MNwm36 | L | wing; muscle unknown |
| 800190 | MNwm35 | R | wing; muscle unknown |
| 800241 | hg1 MN | L | hg1 |
| 800381 | i2 MN | L | i2 |
| 800412 | DVMn 1a-c | L | DVM 1a-c |
| 800474 | MNhm42 | R | haltere; muscle unknown |
| 800573 | i2 MN | R | i2 |
| 800606 | MNwm35 | L | wing; muscle unknown |
| 800637 | i1 MN | R | i1 |
| 800696 | MNwm36 | R | wing; muscle unknown |
| 800718 | DLMn c-f | L | DLM c-f |
| 800743 | ps1 MN | R | ps1 |
| 800847 | hg4 MN | L | hg4 |
| 800890 | DLMn c-f | L | DLM c-f |
| 800899 | tp2 MN | R | tp2 |
| 800906 | hg4 MN | R | hg4 |
| 800917 | hg1 MN | R | hg1 |
| 800928 | ps1 MN | L | ps1 |
| 801021 | hg3 MN | L | hg3 |
| 801137 | b2 MN | L | b2 |
| 801185 | tpn MN | L | tp |
| 801220 | i1 MN | L | i1 |
| 801292 | b3 MN | L | b3 |
| 801295 | DLMn a, b | L | DLM a, b |
| 801310 | b1 MN | L | b1 |
| 801350 | b2 MN | R | b2 |
| 801391 | STTMm | R | TTM |
| 801815 | tpn MN | R | tp |
| 801816 | DVMn 1a-c | R | DVM 1a-c |
| 801895 | DLMn c-f | L | DLM c-f |
| 801933 | MNhm42 | L | haltere; muscle unknown |
| 801949 | tp2 MN | L | tp2 |
| 801970 | DLMn a, b | R | DLM a, b |
| 801998 | DLMn c-f | R | DLM c-f |
| 802028 | tp1 MN | R | tp1 |
| 802055 | hi2 MN | R | hi2 |
| 802120 | b3 MN | R | b3 |
| 802315 | tp1 MN | L | tp1 |
| 802327 | iii3 MN | R | iii3 |
| 802544 | DLMn c-f | R | DLM c-f |
| 802659 | MNhm03 | R | haltere; muscle unknown |
| 802806 | MNhm03 | L | haltere; muscle unknown |
| 802835 | iii1 MN | L | iii1 |
| 802837 | ps2 MN | R | ps2 |
| 803013 | DLMn c-f | L | DLM c-f |
| 803048 | DLMn c-f | R | DLM c-f |
| 803100 | iii1 MN | R | iii1 |
| 803129 | DVMn 1a-c | R | DVM 1a-c |
| 803215 | hDVM MN | L | hDVM |
| 803310 | MNhm43 | L | haltere; muscle unknown |
| 803589 | ps2 MN | L | ps2 |
| 803599 | DVMn 2a, b | R | DVM 2a, b |
| 803891 | hg2 MN | R | hg2 |
| 803982 | DVMn 2a, b | L | DVM 2a, b |
| 804107 | iii3 MN | L | iii3 |
| 804131 | hg2 MN | L | hg2 |
| 804301 | b1 MN | R | b1 |
| 804642 | TTMn | L | TTM |
| 805137 | hi1 MN | R | hi1 |
| 805165 | DVMn 3a, b | L | DVM 3a, b |
| 807784 | hi2 MN | L | hi2 |
| 807799 | DVMn 2a, b | L | DVM 2a, b |
| 807924 | DVMn 2a, b | R | DVM 2a, b |
| 807987 | null | **null** | **unmapped** |
| 808813 | hi2 MN | L | hi2 |
| 809085 | hDVM MN | R | hDVM |
| 809985 | hi2 MN | R | hi2 |
| 810460 | hiii2 MN | R | hiii2 |
| 824223 | STTMm | R | TTM |
| 830847 | STTMm | L | TTM |
| 903852 | hg3 MN | R | hg3 |
| 906003 | MNhm43 | R | haltere; muscle unknown |
| 906612 | DVMn 3a, b | L | DVM 3a, b |
| 908181 | hi1 MN | L | hi1 |
| 924167 | STTMm | L | TTM |
| 932321 | DVMn 3a, b | R | DVM 3a, b |
| 932322 | DVMn 1a-c | L | DVM 1a-c |
| 932796 | DVMn 1a-c | L | DVM 1a-c |
| 934019 | hiii2 MN | L | hiii2 |
| 1050014552 | DLMn c-f | R | DLM c-f |
| 1050045395 | DVMn 3a, b | R | DVM 3a, b |

Eleven flight rows lack muscle identities: MNwm35, MNwm36, unnamed 807987, MNhm03, MNhm42 and MNhm43. No official type iii4 MN occurs among selected wing rows; this is an annotation gap, not evidence that the animal lacks that muscle. Thorax/hinge geometry, synchronous/asynchronous physiology, haltere mechanics and aerodynamics belong to the flight implementation. No flapping, hovering, normal-fly capability or reactive behavior follows from this table.

## FlyMimic15 and the leg mechanics metadata

Of 381 leg neurons, 328 have named muscle/group targets and 53 are muscle-unmapped. **136 have a single name-level candidate in the leg worker metadata; 69 encounter ambiguous bundle correspondence; 123 target muscles absent from FlyMimic15.** This is not 136 validated individual motor-unit bindings.

The installed template is LF only. The leg worker defines 70 estimated MTUs (15 per foreleg, 10 per middle/hind leg). This assignment reads its metadata without compiling or binding it. [Leg mechanics report](whole-body-muscle-mechanics.md), [metadata source](../../runtime/leg_muscles.py).

| MANC target | Exact source actuator | Leg worker muscle_name |
|---|---|---|
| Pleural remotor/abductor | LFC_pleural_remotor_and_abductor | pleural_remotor_abductor |
| Sternal adductor | LFC_sternal_adductor | sternal_adductor |
| Sternal anterior rotator | LFC_sternal_anterior_rotator | sternal_anterior_rotator |
| Sternal posterior rotator | LFC_sternal_posterior_rotator | sternal_posterior_rotator |
| Acc. tr flexor | LFF_accesory_trochanter_flexor | accessory_trochanter_flexor |
| Tr extensor | LFF_trochanter_extensor | trochanter_extensor |
| Ti flexor | LFTibia_flex_93434 | tibia_flexor |
| Ti extensor | LFTibia_extensor_93932 | tibia_extensor |

No annotation row is excluded because the source is LF-only. All 328 named leg-target rows have a resolved peripheral side. The per-row peripheral_limb field supplies lf/rf/lm/rm/lh/rh; flymimic15.mechanics_limb repeats it. candidate_local_actuator_names lists only paths instantiated for that limb; an empty list remains a mechanics gap, not an invented transfer. For single-name candidates, join **resolved peripheral side + leg subclass + exact source_actuator** to returned mechanics records. Use the record's actual actuator_name; candidate_local_actuator_name is supplied for review. Soma side alone is not the join. Literal source spelling accesory is retained; 93434/93932 in source actuator names are not MaleCNS IDs.

| Anatomical target | Mismatch or missing boundary |
|---|---|
| Tergopleural/Pleural promotor | Three candidate paths: tergopleural a/b and pleural promotor. No individual MN allocation among them. |
| Tr flexor | Two source a/b bundles; no specific MN allocation or duplicated drive. |
| Sternotrochanter and Tergotr. | Distinct biological targets versus combined sterno-tergo-trochanter_extensor_a/b names. The mechanics worker returns null target identity for those paths. |
| Acc. ti flexor, Fe reductor, Ta depressor/levator, ltm, ltm1-tibia, ltm2-femur | No equivalent template path. Do not reroute to a nearby/convenient flexor. |
| Middle/hind legs | Promotor and combined sterno/tergo paths are omitted by the leg worker. Other serial geometry is estimated, not a new neuron correspondence. |

Constitutive equations and passive tension are physical models, distinct from action scripts. This artifact supplies no gait phase, wingbeat, desired pose, action selector, default walking signal, food rule or behavior-fit gain. Muscle-family labels do not establish force weights, NMJ kinetics, physiological recruitment or sensory feedback.

## Neurotransmitter and remaining implementation boundaries

814/815 motor bodies have NT records: 306 glutamate, 37 acetylcholine, 2 GABA and 469 unclear consensus predictions. Unnamed front-leg body **1050340850** lacks an NT record but stays in the inventory. Both MN9 rows have low-confidence cell-type acetylcholine predictions despite adult glutamatergic anatomical evidence. Predictions are preserved verbatim: **central-synapse sign and excitatory adult NMJ transmission require separate adjudication**. No motor is removed, or muscle made inhibitory, from this prediction table.

Still missing: 214 abdominal, 13 antennal, 7 retinal, 26 neck, 13 MNx, 53 leg, 11 wing/haltere and 6 unknown-system muscle targets; MN12V is absent as an official type. Known targets still lack complete individual fiber allocation, calibrated NMJ/contraction parameters, attachment geometry and physiological sensory transduction. The inventory is complete for the stated selector, not complete for everything a fly can physically do.

## Reproducing the mapping inventory

The tables in this report describe the historical source revisions, including the original 472 named-target and 343 unresolved-target partition. Later curation changes that partition. Run the [public mapping checks](../../tests/) against the selected release and consult [current status](../status.md); the old count assertions are not retained as executable package checks.

## Revision 2: resolved additions and remaining evidence boundaries

This revision preserves every original bodyId/type/target and adds **16 unilateral sides**, **10 bilateral side sets**, and **six explicit unpaired CEM organ-group topologies**. No new individual muscle identity was justified. Target coverage remains 472/815; no regional label was promoted to a muscle.

For integration, **peripheral_target_sides is canonical**. The old scalar remains null for bilateral cells; that null no longer means evidence is absent. An actual bilateral axon may innervate two physical targets, but this supplies no per-target synaptic weight or force-capacity duplication. Each neuron keeps its own events and state.

### Neck crossing: eight resolved body IDs

Gorko Fig. 4a shows cell bodies and exiting axons on the same side for CvN4/5 and opposite sides for CvN6/7. Fig. 4e/f follows the CvN7 axon to the opposite-side VL1 muscle; Fig. 4h and supplementary Figs. 4–7 identify VL2 versus VL1. This is a visual anatomical readback, not a mapping from the direction of stimulated head movement. Absolute left/right image orientation does not affect the soma-to-axon ipsilateral/contralateral relation. [Primary anatomy PDF, Fig. 4](https://faculty.washington.edu/tuthill/docs/gorko%202024.pdf).

| Type | BodyId: soma → muscle side | Target |
|---|---|---|
| CvN4 | 11316: L → L; 12141: R → R | VL2 |
| CvN5 | 174810: L → L; 10627: R → R | VL1 |
| CvN6 | 192306: L → R; 10156: R → L | VL1 |
| CvN7 | 10754: L → R; 556449: R → L | VL1 |

### Mouth: eighteen additional side-resolved bodies plus CEM topology

Schwarz analyzed 96 single-cell MARCM clones. Its positioning neurons innervate ipsilateral muscles, whereas pharyngeal pumping groups 5, 10, 11 and 12 bifurcate to both sides. Modern muscle names are reconciled through McKellar Table 1. The exact modern m12D/old 11-3 case is deliberately not inferred from the older group-level text. [Schwarz, Figs. 3–4 and Discussion](https://elifesciences.org/articles/19892), [McKellar naming crosswalk](https://elifesciences.org/articles/54978#table1).

| Type | BodyIds | New output relation |
|---|---|---|
| MN6 | 519667, 924612 | ipsilateral |
| MN7 | 16134, 16892, 17495, 32092 | ipsilateral |
| MN8 | 16827, 20173 | ipsilateral |
| MN5 | 13359, 535501 | bilateral L+R from each neuron |
| MN10 | 11861, 515060, 925726 | bilateral L+R from each neuron |
| MN11D | 11269, 11393, 551398 | bilateral L+R from each neuron |
| MN11V | 49829, 492462351 | bilateral L+R from each neuron |
| CEM | 19823, 20518, 23511, 32852, 34597, 482595 | unpaired crop-entry group; no L/R split or individual fiber allocation |

The six CEM neurons project along the oesophagus and branch at the crop-duct/proventriculus-entry junction. At this organ-group resolution the target is not two independent left/right organs; individual terminal allocation around it remains missing. [CEM primary anatomy, Fig. 5b–c](https://pmc.ncbi.nlm.nih.gov/articles/PMC11398398/).

### Gaps that the newly checked sources do not close

| Source checked | Concrete boundary |
|---|---|
| Gorko full anatomy and EM-ID table | No further exact match from the remaining 26 GNG/systematic neck rows to one of the named muscles. |
| Suver 2023 antennal anatomy and 2026 APN2 connectomics | Four antennal muscles and identified motor populations/paths do not supply a MaleCNS body/type-to-individual-muscle crosswalk. The 13 am rows stay unassigned. |
| Fenk 2022 retinal anatomy | MOT and MOS attachments are known; no exact target/side mapping for the selected seven rm bodies was recovered. |
| Falt et al. 2026 retinal preprint | Official abstract/metadata were accessible; full XML returned 403. No identity or electrical edge is taken from the abstract. |
| Current NeuronBridge abdominal workflow | Its GAL4/gut-region matches are explicitly hypotheses. Multineuron expression or a regional label cannot establish which abdominal MN innervates which muscle. All 214 abdominal targets remain unresolved. |
| Cheong named and serial motor tables | The 53 unnamed leg and 11 unnamed wing/haltere targets remain regional/unidentified; predicted mancBodyid cannot repair them. |
| Schwarz + McKellar pumping anatomy | MN12D bodies 10619, 14237, 440899, 533967 have target m12D but unresolved output side; MN13 bodies 14907 and 30780 have m13 identity but no recovered single-cell laterality evidence. Schwarz explicitly reports no MN13 clone. |

The current source-level motor categories also disagree across datasets: MaleCNS PS348 (am) corresponds by official type to FlyWire CB0901 (eye motor); MaleCNS GNG314/GNG647 (rm) correspond to FlyWire CB0004/CB0918 (neck motor). These seven MaleCNS rows retain the current annotations and an explicit category-discrepancy record. Neither broad category establishes a MOS/MOT or neck-muscle edge. [Pinned author annotation source](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/8587524c1748ce5ef2080822a2fc890fc03bf597/supplemental_files/Supplemental_file1_neuron_annotations.tsv).

Sources: [Suver antennal anatomy](https://doi.org/10.1016/j.cub.2023.01.020), [APN2 connectomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC13131640/), [Fenk retinal anatomy](https://doi.org/10.1038/s41586-022-05317-5), [Falt retinal preprint](https://doi.org/10.64898/2026.08.11.744090), [author abdominal candidate workflow](https://natverse.org/neuronbridger/articles/abdominal_peripheral_targets.html).

These are missing links in the recovered primary evidence, not proof that the corresponding muscles or behaviors do not exist. Completing them requires a curated body/type-to-peripheral-target match or a resolved individual axon/NMJ reconstruction; numerical mechanics estimates cannot supply that relationship.

Revision 2 validation: embedded integrity check and all per-row side/topology/source-reference invariants passed. The 32 refined rows comprise 16 unilateral sides, 10 bilateral side sets and six CEM organ-group clarifications; 466 named-target rows now have a supported output topology. No runtime binding or behavior was tested.


## Addendum: what the 343 target gaps mean, and which evidence can close them

2026-09-11, bounded source review. **343 is the number of motor-neuron rows without a supported named peripheral target, not a count of 343 distinct missing muscles.** These rows already have a place in the neural inventory; the missing datum is the identity of the muscle their axon innervates. Adding an actuator, choosing geometry, or routing a spike into a nearby muscle cannot supply that datum. The 32 revision-2 refinements above are unchanged.

A **hard missing label here means absent or explicitly unresolved in the pinned primary annotation/crosswalk resources used by this map**. It does not mean that the answer cannot exist in an unexamined image or an author's unpublished annotation. All 343 need a new accepted target annotation before exact binding; some might obtain that annotation by curating existing public images. Others need target-resolving peripheral data that the currently inspected sources do not contain. There is no justified numerical split between those two possibilities without evaluating the relevant image stacks cell by cell.

The 472 supported target/family rows have separate outstanding implementation and physiological limits. Those limits are not counted among these 343. Likewise, the unresolved output sides of four MN12D and two MN13 cells, and CEM's unresolved individual fiber allocation, are additional issues rather than missing target identities in this tally.

### Exact source-label breakdown

| System | Unmapped motor rows | Regional target only | No assigned target label | What is missing in the primary resources |
|---|---:|---:|---:|---|
| Abdomen | **214** | 201 | 13 | MaleCNS v1 supplies MNad identity/segment/nerve information, but no target column. Cheong's matching MANC rows identify abdomen or abdominal regions; the paper explicitly says abdominal muscle targets still need identification. |
| Antennae | **13** | 0 | 13 | Six named cell-type pairs plus one untyped cell have no muscle-specific target field or accepted match to the four antennal muscles in the recovered adult anatomy. |
| Retina | **7** | 0 | 7 | Three official types, PS349/GNG314/GNG647, are not assigned to MOS versus MOT by the recovered crosswalk. Broad eye/neck/antenna categories differ for some related FlyWire types. |
| Legs | **53** | 45 | 8 | **2 foreleg, 24 middle-leg, 27 hind-leg rows**. The 45 named systematic types retain middle-leg/hind-leg labels after MANC serial matching; eight cells have no named type. |
| Neck | **26** | 10 | 16 | **12 central-brain GNG cells and 14 VNC cells** lack a named muscle identity. Ten VNC cells have only neck targets; four cells carry the unresolved combined type MNnm07,MNnm12. |
| Wing/haltere | **11** | 10 | 1 | Five wing and six haltere rows have absent, uncharacterized or ambiguous terminal targets, detailed below. |
| Proboscis MNx | **13** | 0 | 13 | MNx01–MNx05 have no accepted peripheral-target identity. The separate published existence of MN12V does not identify any MNx cell as that neuron. |
| Unknown system xm | **6** | 0 | 6 | MNxm01–MNxm03 remain without a specific muscle identity. |
| **Total** | **343** | **266** | **77** | The six systems emphasized in the request sum to 324; MNx and xm account for the remaining 19. |

Primary authority: [MaleCNS v1 bulk annotations](https://male-cns.janelia.org/download/), [Cheong motor identification, Fig. 6 and Fig. 7 supplement 1](https://doi.org/10.7554/eLife.96084.3), [Supplementary file 3](https://cdn.elifesciences.org/articles/96084/elife-96084-supp3-v2.csv), [serial leg groups, file 6](https://cdn.elifesciences.org/articles/96084/elife-96084-supp6-v2.csv). The source-3 byte hash was rechecked against the map and is unchanged.

### What current public evidence could still resolve

**Abdomen, 214 rows.** An identified muscle on a published anatomical diagram does not identify its MNad input. A concrete existing lead is **MNad24 bodies 806161 and 806561 → curated MANC group 14871 → line SS48247**. The cited Ehrhardt work lists SS48247 as labeling abdominal motor neurons, but does not identify their individual muscles. This lookup was followed; it produced a genetic-access lead, not a target upgrade. The public **NeuronBridge v3_9_0 MANC/FlyLight libraries** could produce more cell-specific LM candidates. The authors' current abdominal workflow combines those candidates with the **KGutProject 353-line gut-expression screen**, explicitly as hypotheses. A gut region or a broadly expressing driver cannot show which labeled axon reaches which muscle. Further curation could close a row if an existing sparse peripheral stack follows the matched cell to an identified muscle; if only CNS MIPs or mixed gut expression exist, a new peripheral labeling/trace is needed. The 214 are therefore not 214 actuator definitions waiting to be typed into software. [Ehrhardt's current resource](https://elifesciences.org/reviewed-preprints/106548v1), [author abdominal matching workflow and its limitations](https://natverse.org/neuronbridger/articles/abdominal_peripheral_targets.html).

**Antennae, 13 rows.** Suver et al. provide four muscle groups, genetic access to motor populations, and anatomy in the paper/supplements. A concrete source still suitable for detailed image comparison is that paper's **anatomical panels and driver expression**, together with registered MaleCNS/FlyWire morphology. The public Zenodo archive was checked: it contains a README, DLC network archive, code archive and approximately 5 GB of data. Its README describes video-tracking/behavioral figure data; it does not announce a neuron-to-muscle identity table. The code repository likewise did not expose a ready body/type-to-muscle crosswalk. The 2026 APN2 work adds connectome paths to antennal MNs, without assigning each MN to a terminal muscle. Matching a publicly imaged motor cell could yield a new curated identity, but if a driver labels several neurons or only a muscle, a single-cell innervation experiment or equivalent retained source data is required. [Suver anatomy](https://doi.org/10.1016/j.cub.2023.01.020), [verified archive inventory](https://zenodo.org/records/7508037), [code repository](https://github.com/nagellab/SuverEtAl2023), [APN2 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13131640/).

**Retina, 7 rows.** Fenk et al. establish the actual **MOS and MOT muscles** and show their innervating neurons. Those peripheral/anatomical images are a concrete comparison resource, but no accepted assignment from the selected MaleCNS types to MOS/MOT was recovered. The 2026 Falt retinal preprint is a potentially relevant later source; its public abstract and metadata were recovered, while full XML was inaccessible in the prior pass. Its unretrieved full text/supplements remain an evidence-access lead, not evidence that a specific assignment exists. A unique morphology match linked to the peripheral images could permit annotation without a new experiment. If the public images label both motor cells without linking each to its peripheral terminal, cell-resolved labeling or an author-provided verified crosswalk is required. The cross-dataset category discrepancies documented above must be adjudicated rather than selecting the category that makes a desired muscle connection convenient. [Fenk anatomy, Fig. 1](https://doi.org/10.1038/s41586-022-05317-5), [Falt preprint](https://doi.org/10.64898/2026.08.11.744090).

**Legs, 53 rows.** Cheong Fig. 7 supplement 1 specifically documents unmatched or ambiguous serial sets in T2/T3; that is a published limit of the muscle matching, not an absent parser branch. Azevedo's **FANC leg-MN atlas, muscle-identification appendix and LM/X-ray anatomy** remain concrete independent comparison resources. They could support new curated correspondence where morphology and peripheral anatomy agree. They do not automatically make every T2/T3 cell the serial counterpart of a foreleg MN. The current FANC code repository inventory was checked and did not supply a ready MaleCNS muscle-crosswalk file. For the eight untyped cells, identification/proofreading is additionally necessary. If existing reconstructions and LM examples cannot distinguish serial identities, a target-resolving peripheral reconstruction is needed. [Cheong unresolved leg sets](https://doi.org/10.7554/eLife.96084.3), [Azevedo primary atlas](https://doi.org/10.1038/s41586-024-07389-x), [muscle-identification appendix](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf), [FANC source repository](https://github.com/htem/FANC_auto_recon).

**Neck, 26 rows.** Gorko's named motor-neuron library and the **full split-GAL4 images cited at Janelia** could permit additional morphology matches for the remaining GNG/systematic identities. Their existence is not a published correspondence for those cells. The public Bitbucket repository was checked: the inspected figure_4 folder contains 4kl analysis, and its exposed JR153/JR161 stack archive concerns neck sensory lines, not a missing motor-target lookup. Downloading/running that MATLAB analysis would therefore not resolve the 26 identities. A new curated match to the named single-cell anatomy may suffice for a distinguishable cell; otherwise one needs more selective peripheral labeling or complete neuronal tracing. [Gorko Fig. 4 and supplementary anatomy](https://doi.org/10.1038/s41586-024-07222-5), [public code/data repository](https://bitbucket.org/stephenhuston/code_data_gorko_et_al/src/master/), [Janelia split-GAL4 image resource](https://splitgal4.janelia.org/).

### The 11 wing/haltere gaps have explicit, different causes

| MaleCNS rows | Published source limit | Remaining concrete evidence route |
|---|---|---|
| **800190, 800606 — MNwm35** | Cheong calls the iii4 correspondence putative, with match certainty **1/5**; line **SS41027** labels several MNs. | Ehrhardt's current Fig. 8 and SS41027 MCFO/segmented single-cell images contain a named iii4 reference. A new convincing morphology match to that particular cell could settle the identity. The low-confidence MANC match itself is not enough. |
| **800184, 800696 — MNwm36** | Line **R92F05** matches the central morphology, but its muscle is uncharacterized. A pleurosternal target is a published hypothesis. | Existing peripheral R92F05/sparse images could resolve the terminal if they contain it; otherwise target-specific peripheral anatomy is needed. Similarity to ps1 is not a ps1 annotation. |
| **800474, 801933 — MNhm42; 803310, 906003 — MNhm43** | Both are linked to **SS47195**. The newer **2025 reviewed Ehrhardt paper still explicitly cannot distinguish which segmented cell innervates hb1 versus hb2**. | The two neurons and candidate muscles are known. Resolution requires additional evidence associating each cell with its own terminal: decisive reanalysis of retained peripheral images if possible, or new sparse tracing. Swapping the assignments or driving both muscles would create unsupported edges. |
| **802659, 802806 — MNhm03** | **MB430C** is an LM lead; the muscle target is uncharacterized. | A peripheral image/reconstruction tying the matched cell to a specific muscle is required. The existence of a line or haltere arbor is insufficient. |
| **807987 — untyped wm** | No accepted type, muscle or output-side match; the MaleCNS note describes biological variability. | Cell identification/proofreading and a peripheral-target correspondence are both needed. |

The bounded follow-up checked the **2025 Ehrhardt reviewed version**, rather than relying only on its 2023 citation. Its hb1/hb2 ambiguity persists; it also reports that **SS36076 labels hiii3 but no image of that MN could be segmented**. This is a concrete example where a known muscle and a useful genetic reagent still do not supply a resolved single-cell morphology. The raw line/MCFO stacks have not been exhaustively re-curated in this assignment. [Current Ehrhardt anatomy and methods](https://elifesciences.org/reviewed-preprints/106548v1), [Cheong exact match table](https://cdn.elifesciences.org/articles/96084/elife-96084-supp3-v2.csv).

A second later resource, **Dhawan et al. 2026, A neural connectivity atlas for fly flight control**, was followed to its public repository. The inspected annotated_haltere_outputs_v2.csv has 2,576 FANC-neuron rows with IDs, broad types, lineage, transmitter and position; it is not a MaleCNS-to-muscle crosswalk. The paper's public FANC MN segmentations can provide comparison morphology, but a newly accepted cross-dataset identity remains necessary. The available sensory-to-MN connectivity does not decide a muscle target. [Primary paper](https://doi.org/10.1016/j.cub.2025.12.024), [author data repository](https://github.com/serene-da1/Dhawan-et-al-2025-).

### Other 19 gaps and the completion boundary

The **13 MNx** rows require a real match to a particular proboscis/enteric muscle; McKellar's full muscle inventory provides candidate anatomy, not permission to fill an unmatched type by elimination. The **six MNxm** rows lack a specific target. For MNxm01, the source lists **MB564C/MB080C** but explicitly leaves the muscle uncharacterized; MNxm02/03 lack that target match. These can enter the same sparse-anatomy workflow, without inventing a destination.

Consequently, completing the existing software can advance force generation, body mechanics and sensory feedback for supported connections. It cannot make the remaining 343 exact by implementing an arbitrary routing rule. The minimum evidence needed to close each such row is a **curated neuron/type correspondence attached to an identified peripheral muscle**, preserving side and any true multiple-target anatomy. Public image analysis can sometimes create that new annotation; when the images omit or mix the relevant terminals, new target-resolving data are required. No defensible count of how many will need new experiments has yet been established.

**Provenance corrected:** MaleCNS MNwm35 records carry mancGroup 13665, whereas Cheong groups MANC bodies 11991/13665 under source group **11991**. Rows 60–61 support the named **MNwm35 type plus wm subclass** correspondence and ipsilateral soma-to-exit relation. JSON records 800190 and 800606 now explicitly use official_type_and_subclass_plus_MANC_soma_to_exit_relation, with source group 11991 explained in their transfer-status field. The raw official mancGroup field is preserved. No side, target, confidence, source row, or any of the 32 head/mouth refinements changed.

The source-investigation addendum originally left the JSON unchanged. The subsequent provenance correction changed only the two method/status pairs above. Historical motor-map SHA-256: **b3e17e97f26b0e85df88777fbda0eb2109292ed0e78658a2eb6bbe5095b72964**. No new target assignment was made; this source-investigation pass is closed.

# M1 adjudication of four published BANC neck correspondences

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**The evidence supports seven correspondence-level target refinements: two CvN3 neurons to SC-RO and five VCvN neurons to the OH muscle group. Six CvN1/CvN2 candidates remain ambiguous between OH and TH1. All thirteen individual peripheral-side, topology, and fiber/capacity assignments remain open.**

The five OH candidates also support a curated **neck-system classification**, preserving the original MaleCNS `subclass=rm` and `exitNerve=ON` as source annotations. **ON means occipital nerve, not optic nerve.** The differing ON/ventral-cervical terminology is not evidence of an eye-directed axon. [Original FlyWire paper, Fig. 2d](https://pubmed.ncbi.nlm.nih.gov/39358518/)

Assessed against the frozen MaleCNS v1.0 annotations and current map on 2026-09-12 UTC. The adjudication JSON (original artifact `program/m1/banc-neck/adjudication.json`) supplies the exact proposals; the current-row snapshot (original artifact `program/m1/banc-neck/selected-motor-rows-before.json`) retains all thirteen original records.

## Scope and decision

| Current MaleCNS rows | Published identity chain | Supported refinement | Remains unresolved |
|---|---|---|---|
| **10554, 10699**; GNG648; `flywireType=CB0913`; raw `nm/CvN` | Exact FlyWire roots → published CvN3 → Gorko Fig. S3d | Named muscle **SC-RO**, the sclerite rotator | Individual target side/topology, fiber allocation, geometry and force physiology |
| **12180, 13128**; GNG653; `CB0706`; **11879, 12342** GNG276 and **12097, 231558** GNG283; `CB0705`; raw `nm/CvN` | Exact roots → published combined **CvN1,CvN2** → Gorko S1d/S2d | Candidate set **TH1 or OH** only; leave target unassigned | Which named neuron and muscle applies to each current body; all output topology and allocations |
| **12173, 12631**; GNG314; `CB0004`; raw `rm/ON` | Exact roots → published **VCvN3** → published OH target; Gorko generic VCvN anatomy | **OH muscle-group correspondence** and curated neck system, preserving raw fields | Individual peripheral terminal/side; sexually dimorphic type must not imply identical fibers across sexes |
| **12076, 12126, 13592**; GNG647; `CB0918`; raw `rm/ON` | Exact roots → published combined **VCvN1,VCvN2** → published OH target; Gorko generic VCvN anatomy | **OH muscle-group correspondence** and curated neck system, preserving raw fields | VCvN1 versus VCvN2, individual fibers, topology and motor-unit allocation |

These refinements meet the research roadmap's requirement for a source-backed neuron/type correspondence to an identified muscle **at the stated resolution**. They do not meet the separate requirement for a new physical binding: a named muscle/group without current-neuron output topology and capacity allocation does not establish which actuator should receive that neuron's events. M1's full correspondence gate remains open.

## Why the new crosswalk is usable

The final BANC paper describes expert manual annotation of sensory and efferent neurons by comparison with anatomical literature. Its neck-connective Methods identify 49 neck efferents and explicitly use **reference 64, Gorko et al. 2024**, for their names. Published Supplementary Data 3 annotates the exact FAFB/FlyWire v783 roots with anatomical names and peripheral targets. This is source-owned anatomical curation, distinct from an unreviewed similarity ranking. [BANC article and Methods](https://doi.org/10.1038/s41586-026-10735-w), [Supplementary Data 3](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10735-w/MediaObjects/41586_2026_10735_MOESM5_ESM.txt)

The admissible join is:

1. The **exact root ID** in published BANC Supplementary Data 3 identifies a FlyWire neuron and its anatomical target label.
2. The **same exact root ID** in the pinned official FlyWire annotation table supplies its `CB*` type.
3. The current official MaleCNS v1.0 `flywireType` maps each retained MaleCNS body to that type.
4. The original Gorko terminal images support the named muscle/group at the declared granularity.

This route does not use `malecns_match` to assign a target, copy a source individual's output side, or create neural edges. The [pinned official FlyWire annotation](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/8587524c1748ce5ef2080822a2fc890fc03bf597/supplemental_files/Supplemental_file1_neuron_annotations.tsv) and [official MaleCNS v1.0 annotation](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather) retain the source identities independently of the proposed target.

| Published anatomical label | Exact FlyWire root IDs | Published CSV parsed records, including header |
|---|---|---|
| CvN3 | `720575940628164612`, `720575940641811419` | 29786, 29787 |
| CvN1,CvN2 | `720575940631715896`, `720575940624679463`, `720575940607880578`, `720575940622008560` | 25718, 29503, 29500, 29502 |
| VCvN3 | `720575940620182181`, `720575940628372613` | 37948, 37947 |
| VCvN1,VCvN2 | `720575940624327572`, `720575940607641010`, `720575940635776760`, `720575940608078347` | 25737, 25738, 25739, 31956 |

All twelve pinned official FlyWire rows have `cell_sub_class=neck_motor_neuron`. BANC's exact-root tables add the more specific target evidence that the earlier broad-class comparison lacked. The five raw `rm` discrepancies were already known; this review does not describe them as newly discovered.

## Original terminal anatomy and limits

Gorko's [original supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07222-5/MediaObjects/41586_2024_7222_MOESM1_ESM.pdf) provides sparse, in-situ confocal anatomy alongside muscle and cuticle channels. The four relevant original figure pages were visually inspected and retained:

- S1, PDF page 6 (original artifact `program/m1/banc-neck/gorko-page-6.png`): CvN1 terminal at **TH1**.
- S2, PDF page 7 (original artifact `program/m1/banc-neck/gorko-page-7.png`): CvN2 terminal at **OH**.
- S3, PDF page 8 (original artifact `program/m1/banc-neck/gorko-page-8.png`): CvN3 terminal at **SC-RO**.
- S11, PDF page 16 (original artifact `program/m1/banc-neck/gorko-page-16.png`): figure title **VCvN**, terminal panel labels **OH muscles**; the axon label itself says **CvN2**.

The shared S1–S16 legend explicitly identifies the figure's top-left title as the neuron type and panel d as its projection to muscle. That supports reading S11 as the authors' VCvN group anatomy, while retaining the conflicting axon label as a source discrepancy. It does not establish separate VCvN1, VCvN2, and VCvN3 motor-unit territories. The later published BANC table assigns all three named categories to OH; the present proposal preserves that **group-level** resolution.

Gorko Supplementary Table 2 includes named EM matches for other neck neurons, but **none of these four candidate sets**. The new exact-root correspondence comes from the later BANC publication, not a claimed overlooked row in Gorko's table. The public lines remain SS99370 for CvN3 and SS99366 for VCvN; a line name alone was not used as an individual-neuron match.

No new laterality is assigned. Gorko's action-field data were reflected according to the side of the exiting nerve, so the direction of the illustrated movement is not an independent laterality measurement. Source soma sides and BANC nerve-side labels concern their source specimens; they do not supply a validated current MaleCNS neuron→terminal-side topology. The retained figures also do not measure current motor-unit capacities or justify duplicating the force of a shared muscle.

## Conflicting and lower-confidence evidence retained

The independent crosswalk provenance review (original artifact `program/m1/banc-neck/crosswalk-provenance.md`) examined historical human-reviewed match records. Four direct matches retained in the final publication have accepted historical records. Other accepted historical rows disagree with final type assignments or are many-to-one. For example, a historical left CvN3 candidate points to MaleCNS GNG653, while the final source does not retain that match. Historical acceptance therefore cannot replace the final published root-specific annotation. Exact selected history rows and pinned GCS generations are retained in the receipt (original artifact `program/m1/banc-neck/crosswalk-provenance-receipt.json`).

Additional restrictions:

- Four female CB0918 cells correspond at type level to three current male GNG647 cells; two female CB0705 cells correspond to four current male GNG276/GNG283 cells. There is no one-to-one copying or duplicated drive.
- FlyWire root `720575940608078347` carries `status=outlier_seg`. It remains in the evidence inventory but cannot be treated as proof of an intact individual peripheral arbor.
- VCvN3 is labeled sexually dimorphic in the published metadata. This proposal concerns the named muscle group, not identical peripheral fibers, synapses, or physiological parameters across sexes.
- ON is the **occipital** nerve in the original FlyWire paper. The available definitions do not establish a formal ON↔VCvN equivalence for every selected axon; the raw abbreviations remain intact.
- The earlier raw-stack neck comparison (original artifact `program/m1/neck-comparison-evidence.md`) failed its known-cell specificity control. Its highest-ranked candidates are not promoted by this review. The new source route uses published exact-root annotations.

## Checks and next action

Run the bounded, local evidence check:

```sh
python -B outputs/program/m1/banc-neck/check_banc_neck.py
```

The check result (original artifact `program/m1/banc-neck/check.json`) passes the exact thirteen-row scope, unchanged raw map rows, published-root/type joins, seven target proposals, six retained ambiguous cases, absence of new laterality/runtime assignments, and all retained source hashes. It imports no simulator and makes no network requests. The source manifest (original artifact `program/m1/banc-neck/source-manifest.json`) records 23 inputs, including original figure pages and pinned curation/nomenclature documents.

**Anatomical interpretation:** curate the seven target-level refinements and five additive neck-system corrections while preserving all original fields and open topology/capacity records. Keep the six CvN1/CvN2 targets null with alternatives OH/TH1. Before physical binding, obtain a supported current-neuron terminal side/topology and motor-unit allocation; do not infer either from soma side, source-image reflection, matching rank, or behavioral direction.

**Implementation:** evidence and proposal only; map/runtime unchanged. **Numerical correctness:** source/identity replay passes. **Biological validation:** published target correspondence supported at named-muscle or muscle-group resolution; individual topology and physiology remain unqualified. **Demonstrated capability:** no new movement or behavior claimed.


## Subsequent annotation refinement

Seven target/group correspondences and five neck-system corrections were incorporated in a later map revision while preserving the original source fields. The six CvN1/CvN2 alternatives remained unresolved. No additional physical binding followed from the annotation alone: individual terminal topology and motor-unit allocation remained missing.

The historical counts above describe the reviewed source snapshots. Use the [public mapping checks](../../tests/) and [current status](../status.md) for the published map; do not reuse a prior revision's count assertions as a current acceptance test.

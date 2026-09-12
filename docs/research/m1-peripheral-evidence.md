# M1 peripheral correspondence: evidence and exact remaining data

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

Study date: 2026-09-12 UTC. **The bounded source and morphology follow-up recovered one named-muscle refinement for two neurons; M1 remains open.** This report follows the [full-program research roadmap](../roadmap.md) and extends the completed [motor-mapping investigation](malecns-motor-mapping.md). It does not replace the preserved v2 map or its receipts.

The recovered Ehrhardt tables and published registered LM/EM comparison support **MaleCNS 800190 (R) and 800606 (L), MNwm35 → iii4**. The two targets were subsequently curated at correspondence level. Their independent physical bindings remained unimplemented because shared iii3/iii4 paths do not identify iii4-only geometry or capacity.

The frozen v2 inventory contained **378 unconnected motor rows**: **343 unidentified targets, 21 long-tendon subtargets, eight promotor allocations and six proboscis output topologies**. The per-ID evidence ledger (original artifact `program/m1/motor-gap-ledger.json`) preserves that exact baseline with original type/group/serial/nerve/side, supporting Cheong rows, missing datum and source route. It is an evidence index, not a current runtime map. The two curated iii4 targets reduce anatomical target gaps **343 → 341** while physical connection coverage remains **437 connected / 378 unconnected** until separate iii4 mechanics are supported. Physical integration was assessed separately. Sensory correspondences and effector classes outside the motor selector are recorded in the sensory/system inventory.

Implementation, numerical correctness, biological validation and demonstrated capability are separate: this study added source evidence, a checked inventory and an executed morphology comparison. It supplied no physiological or behavioral pass.  Its baseline motor map was SHA-256 `b3e17e97f26b0e85df88777fbda0eb2109292ed0e78658a2eb6bbe5095b72964`; later annotation curation is described separately above.

## First 35 cases

### Long-tendon allocation: 21 rows

The original source distinguishes ltm1 in the tibia from ltm2 in the femur. Both pull on the long tendon. Azevedo Fig. 4d explicitly leaves four smaller FANC neurons' subtargets unresolved; Appendix A15 shows their small morphologies and LM examples. A15–A16 establish population-level anatomy but do not uniquely assign each small FANC neuron to ltm1 or ltm2. The already named large-cell assignments must not be used to fill the small-cell cases by elimination. [Primary paper, Fig. 4d](https://pmc.ncbi.nlm.nih.gov/articles/PMC11348827/), [author appendix, A15–A16](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf).

| MaleCNS body IDs | Retained correspondence | Exact missing datum |
|---|---|---|
| 822274, 860084 | Foreleg MANC group 11786; serial 11786 | Which small LTM cell innervates tibial ltm1 versus femoral ltm2 |
| 822092, 910334, 924189, 1050015101 | Foreleg MANC group 24139; serial 23016; multiple neurons retained | Cell-resolved ltm1/ltm2 assignment within the population; one target must not be copied to every member |
| 813603, 905487 | Middle-leg MANC group 35735; serial 23016 | Cell-resolved subtarget and supported transfer of that subtarget across segments |
| 812872, 824104 | Official serial 11786, no curated MANC group | Individual correspondence as well as ltm1/ltm2 subtarget |
| 824689, 824997, 825681 | Middle-leg generic ltm, no curated group/serial | Individual correspondence and terminal muscle |
| 815097, 823405, 890541, 1050080384, 1050091102, 1050203465 | Hind-leg generic ltm, no curated group/serial | Individual correspondence and terminal muscle |
| 911453, 1050013851 | Foreleg generic ltm, no curated group/serial | Individual correspondence and terminal muscle |

Cheong's file 3 preserves generic `ltm` labels for these supporting cases; file 6 does not convert their serial sets into a named tibial/femoral target. Both files were freshly retrieved and their byte hashes match the retained map. The published medial-branch heuristic is a comparison clue, not an independent proof of the required terminal. [Motor table](https://cdn.elifesciences.org/articles/96084/elife-96084-supp3-v2.csv), [serial table](https://cdn.elifesciences.org/articles/96084/elife-96084-supp6-v2.csv).

**Status:** ambiguous anatomical correspondence, not an unavailable appendix or a missing implementation branch. Minimum closure data: a unique retained FANC/MANC/MaleCNS correspondence plus a single-cell image/trace identifying ltm1 or ltm2. The detailed transfer must preserve limb, individual cell and any multiple-target innervation.

The publisher's Supplementary Table 1 links were also followed to the actual author Neuroglancer JSONs, pinned at commit `ff363505fd1236e63ee77966239e99280fe1ba12`. They explicitly retain separate uncertain and DIP-alpha groups. These are **FANC segment IDs**, not MaleCNS replacements or a new cross-dataset join. [Publisher supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07389-x/MediaObjects/41586_2024_7389_MOESM1_ESM.pdf), [pinned author scenes](https://github.com/EllenLesser/Azevedo_Lesser_Phelps_Mark_2023/tree/ff363505fd1236e63ee77966239e99280fe1ba12/jsons).

| Author scene | FANC segment IDs selected in the source | Target resolution |
|---|---|---|
| `ltm_uncertain.json` | 648518346475434081, 648518346496934372 | Individual femur/tibia allocation explicitly unresolved |
| `ltm_dipalpha.json` | 648518346484620291, 648518346504867443 | Two small DIP-alpha cells; no individual femur/tibia allocation |
| `ltm1_tibia.json` | 648518346493203442, 648518346491158561 | Named tibial reference |
| `ltm2_femur.json` | 648518346486902499, 648518346515711482 | Named femoral reference |

### Promotor allocation: eight rows

Appendix A2 shows four FANC neurons exiting DProN and a GMR10B11 LM example. Its text explicitly leaves each neuron's exact target uncertain. The XNH nerve passes among both the tergopleural and pleural promotors; a shared nerve does not choose the terminal muscle. [Azevedo Appendix A2](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf).

| MaleCNS body IDs | Curated MANC group | Source systematic type |
|---|---:|---|
| 805745, 807281 | 12396 | MNfl56 |
| 801173, 801824 | 12628 | MNfl55 |
| 800061, 802072 | 12686 | MNfl54 |
| 810535, 934091 | 13464 | MNfl53 |

**Status:** explicitly ambiguous in the primary anatomy. Each pair needs a unique choice of pleural versus tergopleural muscle, and any supported subdivision of the tergopleural fibers. The three existing mechanical paths are not three source-confirmed motor pools. New sparse terminal tracing or a newly curated original stack must provide the distinction; common presynaptic partners do not.

The pinned `tgpro_plpro.json` source scene selects FANC segments **648518346491659326, 648518346487756866, 648518346517827432, 648518346517437482** together under the combined muscle-family label. Its linked CNS meshes do not supply the missing peripheral target split.

### MN12D and MN13 output topology: six rows

| MaleCNS body IDs | Supported target | Missing output evidence |
|---|---|---|
| 10619, 14237, 440899, 533967 | Modern m12D | Each neuron's true single-sided, bilateral or unpaired terminal topology; retain four independent neurons |
| 14907, 30780 | Salivary m13 | Individual soma-to-terminal relation and whether the physical target is an unpaired structure or sided muscle allocation |

McKellar Table 1 maps modern m12D to Schwarz's old **11–3**, not old **12–2**. McKellar Fig. 4 labels m12D together with MN11V using `VT050240-AD × GMR10E04-DBD`; it cannot separate those axons' outputs. MN13 uses `VT043700-AD × VT034258-DBD`. In Fig. 5, isolated stochastic MN12D/MN13 CNS neurons are explicitly overlaid with their mirror images. Bilateral-looking CNS panels therefore do not prove that one axon supplies both physical sides. [McKellar Tables 1–2 and Figs. 4–5](https://elifesciences.org/articles/54978).

Schwarz's single-cell study recovered no MN13 clone. Its Fig. 4 confirms bilateral outputs for the individually imaged pumping groups, but does not isolate old 11–3 as modern m12D. That broad group result is insufficient for the four current MN12D rows. The figures were downloaded and visually inspected, including the labeled NMJ panels. [Schwarz Fig. 4 and clone analysis](https://elifesciences.org/articles/19892).

**Status:** ambiguous or absent cell-resolved topology in the examined public panels. This is not evidence that the targets are absent. The needed datum is an original **unmirrored, single-neuron, whole-head** image/segmentation connecting a named MN12D or MN13 soma to all its peripheral terminals, with midline and muscle identity retained. McKellar's public data statement points to the manuscript/supporting material; the inspected public article does not name a separate raw whole-head stack archive. A driver-pair image is not a replacement.

The later 2026 motor-sequence supplement was also inspected. Its authors identify body **10619** as MN12D even though it ranks sixth by NBLAST; the top-ranked **533971** is not the accepted cell. Competing algorithms permute the four existing MN12D bodies. All relevant panels are central comparisons; its bilateral-neuron recordings do not establish bilateral peripheral output. The later-source review (original artifact `program/m1/mn12d-later-source.md`) records the exact panels and scores. [Publisher supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41593-026-02412-y/MediaObjects/41593_2026_2412_MOESM1_ESM.pdf).

## Remaining target gaps and current source routes

The following counts remain frozen v2 anatomical gaps. Every row is enumerated in the ledger. No full annotation-table search was repeated.

| System | Rows | Required missing correspondence |
|---|---:|---|
| Abdominal | 214 | Each retained MNad/group to an individual terminal muscle, including segment, side and true multiple targets |
| Leg | 53 | 2 foreleg, 24 middle-leg and 27 hind-leg cells to individual muscles; eight untyped cells additionally need identification/proofreading |
| Neck | 26 | 12 brain GNG and 14 VNC cells to named neck motor identity, muscle and output topology |
| Antenna | 13 | Each retained motor cell to identified m1/m2/m3/m4 terminal(s); resolve category disagreement where present |
| Retina | 7 | Exact cell to MOS/MOT, or an evidence-backed category correction with its actual target |
| Wing/haltere | 11 | Exact muscle for MNwm35/MNwm36, unnamed 807987, MNhm03/MNhm42/MNhm43 |
| Proboscis MNx | 13 | MNx01–MNx05 to an actual peripheral target; published MN12V existence does not establish the match |
| Unknown system | 6 | MNxm01–MNxm03 to a peripheral system and individual muscle |

The 53 leg target gaps are a published serial-matching boundary: Cheong Fig. 7 supplement 1 includes unresolved/ambiguous T2/T3 sets. The source did not establish matching promotor, tarsal levator or tarsal depressor homologs for every segment. An untyped or unmatched neuron cannot inherit a target from a neighboring named neuron. [Cheong Fig. 7 and matching methods](https://elifesciences.org/articles/96084).

### Wing, haltere, neck and abdominal leads

The wing/neck/abdomen report (original artifact `program/m1/wing-neck-abdomen-evidence.md`) records exact groups, imagery inventories, inspected preparations and data requirements. Janelia pages are accessible: SS41027 has 29 image views, SS47195 has 51, MB430C has 12 and SS48247 has 23. Those representative MIPs show CNS structures, not uniquely identified muscle terminals. The subsequent source-table and registered-overlay retrieval resolved the **named iii4 target** as detailed below. An actual **14,856,366-byte SS45779 MCFO H5J** sample was then retrieved; it contains mixed bilateral signal, with no named iii4 mask and unresolved nominal-versus-encoded dimensions. No coordinates were invented to turn that raw sample into a new reconstruction. [SS41027](https://splitgal4.janelia.org/cgi-bin/view_splitgal4_imagery.cgi?line=SS41027), [SS47195](https://splitgal4.janelia.org/cgi-bin/view_splitgal4_imagery.cgi?line=SS47195), [MB430C](https://splitgal4.janelia.org/cgi-bin/view_splitgal4_imagery.cgi?line=MB430C), [SS48247](https://splitgal4.janelia.org/cgi-bin/view_splitgal4_imagery.cgi?line=SS48247).

| Bodies / group | Exact remaining datum |
|---|---|
| 800190, 800606 / MNwm35 | Named iii4 target now source-supported. Remaining: separate iii4 geometry/attachment/capacity and raw named-cell segmentation provenance for independent reconstruction |
| 800184, 800696 / MNwm36 | R92F05 matched cell's terminal muscle; the proposed pleurosternal target remains uncharacterized |
| 800474, 801933 / MNhm42; 803310, 906003 / MNhm43 | Individual hb1-versus-hb2 terminal allocation; known candidate muscles do not select the assignment |
| 802659, 802806 / MNhm03 | MB430C matched cell's individual haltere-muscle terminal |
| 807987 / untyped wing | Cell identification/proofreading, output side and peripheral target; this cell has no named-line lead |
| 806161, 806561 / MNad24; MANC group 14871 | SS48247 cell-resolved abdominal axon-to-muscle continuity, including each true target |
| 26 retained GNG/MNnm neck cells | Accepted match to a named Gorko motor cell, linked to its existing peripheral muscle anatomy and topology |

The complete Gorko supplement and its EM-ID table were recovered. Further named comparison panels are CvN1→TH1, CvN2→OH, CvN3→SC-RO, CvN8→VL1, VCvN→OH, DProN1→SC-DV1, DProN2→SC-DV2 and DProN3→DE. None supplies an additional accepted match to the remaining current GNG/MNnm IDs. The source S11 panel has a VCvN/CvN2 labeling discrepancy, retained for clarification. The companion report (original artifact `program/m1/wing-neck-abdomen-evidence.md`) lists exact available line/sample identities. [Gorko supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07222-5/MediaObjects/41586_2024_7222_MOESM1_ESM.pdf), [current 20-line release](https://splitgal4.janelia.org/precomputed/Gorko%20et%20al%202024.html).

**iii4 adjudication.** The official reviewed-preprint API recovered the full 2025-05-06 version; PMC revision 3 (2025-02-20) supplied the exact tables. Table 1 sheet 1 **A29/B29/S29** associates MNwm35, MANC **11991/13665**, and **iii4**, with **SS45779** as its specific line. Table 4 **E26 = 3**, explicitly **high on that source's three-level scale (1 low, 2 medium, 3 high)**, supports the central match. Fig. 8C4/C5 provides named peripheral anatomy; Fig. 18 supplement 20C overlays the LM cell with **MANC 13665** in three registered views. This is source-supported cell correspondence, not selection of a nearest neighbor. Preserve Cheong's **1/5 putative** record as a conflicting assessment; these scores use different scales and must not be averaged or silently overwritten. The exact cell readback is retained in MNwm35-exact-table-evidence.json (original artifact `program/m1/wing-neck-abdomen/MNwm35-exact-table-evidence.json`). [Reviewed API](https://api.elifesciences.org/reviewed-preprints/106548), [PMC full text/supplements](https://pmc.ncbi.nlm.nih.gov/articles/PMC10312520/).

The accepted transfer can use the existing exact official **MNwm35 + wm** correspondence to those MANC source cells. It does not use predicted `mancBodyid` or silently reinterpret official `mancGroup=13665`. Already supported peripheral sides remain **800190→R** and **800606→L**. No iii4-specific attachment coordinates, PCSA/capacity, or shared III2/4 tendon allocation was recovered. A combined `wing.iii2_4` prototype therefore remains an unsupported runtime destination.

**Executed neck comparison.** Two complete aligned Gorko H5J brain stacks—IS64892/CvN2 and SS66201/CvN4 control—and all 20 relevant MaleCNS brain-neck skeletons were retrieved in their declared JRC2018-unisex micron space. Exact dimensions/padding were checked, signal decoded, and source-space overlays and cable-weighted signal scores computed. The known CvN4 IDs ranked **2 and 8**, not first; the overlap procedure fails the required specificity control. No top-ranked unknown GNG cell was accepted. The comparison evidence (original artifact `program/m1/neck-comparison-evidence.md`), raw metadata and runnable script preserve the attempt and exact limitation: population signal without a named-cell mask cannot by this procedure establish a unique terminal-linked match. No transform was fitted to force the result.

The MB564C and MB080C source pages were also retrieved for MNxm01. They expose brain/VNC imagery rather than a named terminal muscle, so the six unknown-system rows remain open. [MB564C](https://splitgal4.janelia.org/cgi-bin/view_splitgal4_imagery.cgi?line=MB564C), [MB080C](https://splitgal4.janelia.org/cgi-bin/view_splitgal4_imagery.cgi?line=MB080C).

### Retinal and antennal leads

The retinal/antennal report (original artifact `program/m1/retinal-antennal-evidence.md`) retains all 20 exact MaleCNS IDs, the recovered figures/supplements, 35 HTTP receipts and verified root-ID joins. Fenk's MOS/MOT imagery establishes attachments and a retinal motor reference, but no accepted MaleCNS/CB0804/CB0901-to-muscle correspondence. Falt's later preprint is an **access dependency**: current publisher full HTML/PDF/supplement and the API-specified JATS route return HTTP 429; released MPG `item_3728048` has metadata without attached components; Europe PMC PPR1299617 lists no full text, PDF or supplements. This does not show whether its unretrieved contents resolve the correspondence. [Fenk](https://doi.org/10.1038/s41586-022-05317-5), [Falt](https://doi.org/10.64898/2026.08.11.744090), [MPG metadata](https://pure.mpg.de/rest/items/item_3728048).

Suver's 18D07 and 91F02 associate driver populations with m1/m4 and m3/m4 respectively; muscle-2 motor identity was not recovered. The actual supplement's Fig. S2 is behavioral time traces, not another central-neuron anatomy panel. A single-cell terminal allocation is still required within those driver populations. [Suver primary anatomy](https://doi.org/10.1016/j.cub.2023.01.020), [publisher supplement](https://ars.els-cdn.com/content/image/1-s2.0-S0960982223000209-mmc1.pdf).

The APN2 follow-up's Table S2 was retrieved. Exact root `720575940629183643`, named `GNG.647` there, joins the pinned FlyWire annotation to **CB0886 → MaleCNS GNG649 (10418, 12642)**. It must not be assigned by name to MaleCNS GNG647/CB0918. The other Table S2 roots refine central type correspondence for GNG651/GNG652; none includes a terminal-muscle or output-side field. BANC's later text supports the broad retinal category for CB0901/CB0804 but also supplies no MOS/MOT split. [APN2 full text and Table S2](https://pmc.ncbi.nlm.nih.gov/articles/PMC13131640/), [BANC](https://doi.org/10.1038/s41586-026-10735-w).

These are distinct open states: Falt full text is not retrieved; promotor/hb1-hb2 allocations are anatomically ambiguous in the inspected sources; some driver images contain no target-resolving terminal; new registered morphology curation remains possible for named references. This review does not claim that every raw public stack has been exhausted or that all 343 cells require new experiments.

## Data needed to resolve the remaining correspondences

1. **Long-tendon/promotor allocation:** exact FANC-segment-to-MANC-group correspondence and single-cell peripheral evidence separating ltm1/ltm2 and tergopleural/pleural promotor. Preserve specimen, side, nerve, terminal labels, voxel units, registration transform and every branch; a driver-level list is insufficient.
2. **MN12D/MN13 topology:** unmirrored single-neuron whole-head images with soma side, midline and complete terminals. Separate MN11V from shared split-line expression and determine whether MN13 innervates an unpaired or sided structure.
3. **Unmatched leg cells:** exact target-resolving T2/T3 correspondence, with separate proofreading and terminal-target evidence for untyped cells. Assignment by elimination is unsupported.
4. **MNx and unknown-system cells:** trace each named cell to its peripheral target. MB564C/MB080C samples are useful only when the central neuron can be followed to its terminal.
5. **Retinal targets:** complete Falt figures/supplements and an independently supported MOS/MOT correspondence to CB0804/CB0901 or the listed MaleCNS cells. Resolve category conflicts without inferring a muscle from the category.
6. **Antennal targets:** single-neuron central/peripheral evidence separating m1, m3 and m4 in 18D07/91F02, plus an m2 motor identity. Root 720575940629183643 corresponds to CB0886/GNG649 despite its older GNG.647 label.

## Reproducible source and inventory receipts

Files downloaded for the leg/proboscis branch, their final URLs, HTTP outcomes, byte lengths, UTC retrieval times and SHA-256 values are retained in leg-proboscis/retrievals.json (original artifact `program/m1/leg-proboscis/retrievals.json`). Local extracts and rendered pages preserve A2 and A15–A16 and the inspected McKellar/Schwarz figures. The direct downloads succeeded even where the browsing renderer returned an internal error or HTTP 403; those renderer failures do not imply source unavailability.

Use the [public mapping checks](../../tests/) to verify the published map against its selected source release. Historical assertions for 472/343 or subsequent 481/334 target counts are not current package checks.

**Next action:** obtain independent iii4-only physical anatomy before connecting the two newly identified neurons. For the remaining cells, pursue the named single-cell masks/terminal traces or source-verified correspondences in the data requirements. Falt retrieval can resume when the publisher/source copy becomes accessible. M1 and the affected full-fly gates remain open; a source review or an unsupported ranking does not close them.


### Subsequent neck-source batch

The [BANC neck adjudication](m1-banc-neck-adjudication.md) subsequently adds seven supported target/group correspondences and six retained alternatives. Current counts are reported by the public mapping checks. The revision-3 results above remain the record of the initial iii4 batch; current status is in the [current status](../status.md).

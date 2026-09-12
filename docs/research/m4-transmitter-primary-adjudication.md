# M4 primary adjudication of 57 transmitter candidates

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**All 57 exact MaleCNS IDs, spanning 19 types, have been traced beyond the summary transmitter table. The result is a set of qualified identity refinements, not 57 newly validated transmission laws.** Original MaleCNS consensus values remain unchanged.

The per-ID ledger (original artifact `program/m4-m7/transmitter-primary/57-id-adjudication.json`) retains the original annotations beside each source conclusion. The coverage receipt (original artifact `program/m4-m7/transmitter-primary/57-id-validation.json`) checks all 57 IDs occur exactly once, all 19 current types are retained, all original consensus values remain `unclear`, and runtime signs remain unassigned. The historical candidate table and baseline receipts are preserved.

## Per-type and per-ID conclusions

“Supported” below means the stated molecular/anatomical phenotype at the stated resolution. It does not mean that the original EM animal was chemically assayed, or that a target's response has been calibrated. Explicit cell-type/preparation correspondence can support transfer across specimens; the program does not require an impossible repeat recording from the EM donor.

| Type and all affected MaleCNS IDs | Supported refinement | Remaining ambiguity | Evidence report |
|---|---|---|---|
| l-LNv: 10870, 11114, 11212, 11715, 11999, 17015, 545813, 553895 | Glycine-related function after perturbing the combined small/large LNv population; glycine responsiveness of DN1p targets | Large-LNv-selective synthesis/loading/release and target response were not isolated. The eight cells must not inherit a fixed glycine inhibitory sign | Glycine (original artifact `program/m4-m7/transmitter-primary/glycine/adjudication.md`) |
| PPL203: 13312, 15693 | GABA immunoreactivity in the matched PPL2ab-PN1/L2454 class; putative dopamine identity based on TH-related evidence and location | Simultaneous biochemical identification, dual release, receptor response and kinetics remain unresolved | PPL203 (original artifact `program/m4-m7/transmitter-primary/ppl203/adjudication.md`) |
| OA-AL2i1: 10011, 10072 | Type morphology, tdc2 reporter and OA-positive AL2 population | Anti-OA/tyramine specificity caveat; cell-resolved TβH/release and recipient action missing | Amine/NPF (original artifact `program/m4-m7/transmitter-primary/amine-npf/report.md`) |
| FB6H: 14540, 526639 | Morphology-matched TH-positive cells support dopamine synthesis phenotype | TH does not identify dopamine release, fast cotransmitter or target-specific response | Amine/NPF (original artifact `program/m4-m7/transmitter-primary/amine-npf/report.md`) |
| DNp29: 10195, 10552 | P1/NPFP1 correspondence with named-group NPF transcript, peptide staining and morphology | NPF release/target kinetics and possible small-molecule cotransmitter unresolved | Amine/NPF (original artifact `program/m4-m7/transmitter-primary/amine-npf/report.md`) |
| NPFL1-I: 12271, 14605 | Older L1-l group: NPF transcript, peptide staining and morphology | Same physiological limits; final character in older notation is lowercase l | Amine/NPF (original artifact `program/m4-m7/transmitter-primary/amine-npf/report.md`) |
| CAPA: 10981, 11585 | Exact male author-table classification `SEZ_NSC_CAPA`; corresponding published FlyWire NSC class | Mature Capa products/processing and peptide-specific assays remain needed; `capability` in the source is a precursor/gene designation | Reinhard (original artifact `program/m4-m7/transmitter-primary/reinhard/REPORT.md`) |
| DNES2: 14564, 48615 | Exact male classification `l_NSC_DH31` plus corresponding DH31 NSC transcript class | No DNES2-specific release/recipient response | Reinhard (original artifact `program/m4-m7/transmitter-primary/reinhard/REPORT.md`) |
| DNES3: 16353, 25364, 87303, 535210 | Same exact anatomical class and population transcript support | DNES2-versus-DNES3 physiological distinction unresolved; transcript-cell counts are not connectome-cell counts | Reinhard (original artifact `program/m4-m7/transmitter-primary/reinhard/REPORT.md`) |
| Hugin-RG: 17819, 18794, 18865, 124747 | Exact male classification `SEZ_NSC_Hugin` and published FlyWire class correspondence | Anatomical/hormone designation does not replace mature peptide, release or receptor measurements | Reinhard (original artifact `program/m4-m7/transmitter-primary/reinhard/REPORT.md`) |
| ITP: 17521, 18063, 20146, 69710, 104438, 111191, 564770 | Exact male `l_NSC_ITP` classification, ITP/Tk-associated transcript population, adult NSC peptide colocalization in primary work | ITPa versus ITPL processing, ipc-subgroup transfer and release flux unresolved. These are endocrine NSC, not ITP-positive clock interneurons | Reinhard (original artifact `program/m4-m7/transmitter-primary/reinhard/REPORT.md`) |
| SLP463: 24484, 29895, 76155, 531432 | Published source rows explicitly map FlyWire SLP463 to DN2; DN2 has proctolin reporter/transcript and AstC immuno/reporter evidence | Type-level transfer to the four MaleCNS cells; coexpression does not establish simultaneous release or a postsynaptic action | Reinhard (original artifact `program/m4-m7/transmitter-primary/reinhard/REPORT.md`) |
| AVLP594: 11237, 11317 | Natalisin transcript, antibody and RNAi specificity in the older ADLI/ICLI preparation | Precise ADLI↔AVLP594 primary alias bridge still requires the cited morphology supplement | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |
| DNc01: 11369, 512245 | SIFamide antibody/driver/peptide-RNAi evidence in the four-cell SIFa population | Original experiments pool SIFa and do not separate DNc01 from DNc02 | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |
| DNc02: 10342, 10705 | Same SIFa population support | Duplicate shared SIFa aliases are not independent measurements or subtype-resolved physiology | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |
| DNp32: 524968, 556286 | Wu 2024 explicitly identifies MS-WED as DNp32 with endogenous Ms reporter, anti-MS and MCFO | Release rate/cotransmitter unknown. The native MSR2 pathway depolarizes DA-WED in its tested state; it does not support an inhibitory fast sign | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |
| DNp62: 10504, 10724 | Primary MP1b DSK peptide/expression evidence | Historical source calls the shared DSKMP1B match DNpe089, current type is DNp62; that specific naming bridge remains open | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |
| DSKMP3: 12353, 12522, 12691, 12791 | Wu 2019 explicitly identifies two MP3 pairs using DSK antibody, locus reporters and single-neuron labeling | DSK population release/receptor results are not MP3-specific kinetics; IPC DILP coexpression must not be copied here | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |
| DNpe048: 402239, 521776 | CCAP-Gal4/EM correspondence; Reinhard explicitly supplies DNpe048 alias | 2023 work does not directly assay CCAP peptide or outgoing receptor response; generic synaptic silencing is not peptide-specific release evidence | Other peptides (original artifact `program/m4-m7/transmitter-primary/other-peptides/report.md`) |

## Citation corrections and accessible primary evidence

The initial table provided 16 distinct citation labels. All were investigated; some are not independent primary support for the claimed molecule.

| Original citation | Adjudication |
|---|---|
| Frenkel 2017 | Full primary PDF and relevant figures inspected. Combined LNv synthesis/reuptake perturbation and DN1p glycine responses support the qualified result above. [DOI](https://doi.org/10.1016/j.celrep.2017.03.034) |
| Reinhard 2023 | Original preprint version was identified; full text returned 403/429. Published December 2024 successor, full supplements, author inputs and source workbooks were retrieved. It reuses Frenkel for glycine. [Published DOI](https://doi.org/10.1038/s41467-024-54694-0) |
| Mao & Davis 2009 | TH staining/reporters and PPL2ab morphology, without GABA or dual-release measurement. [DOI](https://doi.org/10.3389/neuro.04.005.2009) |
| “Neins” 2017 | Correct author is Niens. The paper studies dopamine/serotonin, not PPL203 GABA cotransmission. [DOI](https://doi.org/10.3389/fnsys.2017.00076) |
| Dolan 2019 | Actual GABA cell-body colocalization; its table's dopamine entry is presumed, not independently measured monoamine content. [DOI](https://doi.org/10.7554/eLife.43079) |
| Busch 2009 | Primary OA immunochemistry/sparse anatomy inspected, with the source's tyramine crossreactivity caveat. Direct files returned 403; indexed primary content and supplement captions were read. [DOI](https://doi.org/10.1002/cne.21966) |
| Wolff 2015 | Retrieved full XML contains no octopamine, Busch or P1-9 support. The later 2018 morphology discussion cites Busch; do not count 2015 as independent chemical evidence. [2015 DOI](https://doi.org/10.1002/cne.23705), [2018 DOI](https://doi.org/10.1002/cne.24512) |
| Hulse 2021 | Exact FB6H morphology-to-TH match, two antibodies and 12 hemispheres from six brains. [DOI](https://doi.org/10.7554/eLife.66039) |
| Krashes 2009 | Primary NPF population immunochemistry and motivation experiments retrieved. Named P1/L1-l identities required additional Lee 2006 and Shao 2017 primary sources. [DOI](https://doi.org/10.1016/j.cell.2009.08.035) |
| Nässel 2010 | Resolves to Nässel/Winther review, not an independent experiment. [DOI](https://doi.org/10.1016/j.pneurobio.2010.04.010) |
| Miyamoto & Amrein 2019 | Metadata/abstract verified; publisher 403 and full text-mining 401. Specific NPF transport images/methods remain inaccessible through the inspected routes. [DOI](https://doi.org/10.1016/j.cub.2019.02.053) |
| Jiang 2013 | Natalisin in situ, antibody, RNAi specificity and heterologous NTLR assays retrieved. [DOI](https://doi.org/10.1073/pnas.1310676110) |
| Martelli 2017 | Primary SIFa population/peptide perturbation inspected. The hugin receptor experiment concerns input to SIFa neurons, not their output receptor. [DOI](https://doi.org/10.1016/j.celrep.2017.06.043) |
| Carlsson 2010 | Bibliography/abstract resolved; complete primary text not recovered. Direct DNp32 evidence was obtained from Wu 2024 instead. [DOI](https://doi.org/10.1002/cne.22405) |
| Söderberg 2012 | Adult DSK/IPC work retrieved. Exact MP3/MP1b naming required Wu 2019; IPC DILPs do not establish cotransmission in MP1b/MP3. [DOI](https://doi.org/10.3389/fendo.2012.00109) |
| González Segarra 2023 | Identified CCAP-Gal4 cells, FAFB roots and incoming activity/control experiments retrieved; outgoing CCAP receptor/peptide release not measured. [DOI](https://doi.org/10.7554/eLife.88143.3) |

Every detailed report preserves preparation, assay type, source file/hash and the distinction between expression, transport, release, receptor action and kinetics. A citation copied by a later paper does not become an independent experiment.

## Receptor evidence that changes the next action

The primary search also found evidence stronger than the summary labels, with explicit limits:

- **CG12344/Alka:** the 2023 alkaline-taste paper reports that Alka alone responds to high pH but not 0.001–1 mM glycine/GABA in HEK293 cells. It does not negate possible heteromeric DN1p effects, but blocks a naive stand-alone CG12344 glycine conductance assumption. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10665042/)
- **l-LNv receptors:** Fukuda 2025 reports multiple transmitter-receptor genes with T2A-GAL4/clock-marker colocalization. This resolves some type-level expression questions while leaving synaptic localization, assembly and response kinetics open. [Primary paper](https://doi.org/10.1177/07487304251349887)
- **DNp32/MS-WED:** Wu 2024 supplies an explicit donor alias, native MSR2–PKA–ORK1-dependent DA-WED membrane effects, and a public electrophysiology deposit. The bounded raw-trace investigation is proceeding separately; tonic receptor-knockdown comparisons cannot identify peptide binding or clearance kinetics. [Primary paper](https://doi.org/10.1016/j.cell.2024.07.047), [data](https://zenodo.org/records/12701489)
- **ITPa:** Gera's 2025 version of record identifies Gyc76C via cGMP assays and receptor-dependent suppression of stimulated male renal-tubule secretion. Isoform, tissue and concentration remain attached to this result; it is not a point-to-point neural fast sign. [Primary paper](https://doi.org/10.7554/eLife.97043.3)

For the unresolved naming cases, the next datum is the exact morphology/driver correspondence, not a more confident classifier prediction. For transmitter-positive classes, the next datum is native release and receptor-dependent response for the corresponding adult cell type and target preparation. When the source only provides a precursor, mature products/processing must also be established. These are specific biological or access dependencies; the literature review itself is no longer an unexecuted prerequisite for these 57 candidates.

M4 remains open. Implementation is evidence-only; numerical checks here concern exact IDs/source integrity; biological transmission validation and embodied capabilities have not been added.

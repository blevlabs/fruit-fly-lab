# References and source reuse

This project uses published anatomy, simulator components and physiological measurements. A source citation does not mean its implementation was adopted, its experiment was rerun, or the embodied model was biologically validated.

The [complete reference index](reference-index.json) retains **79 primary citations, 44 exact repository/revision pairs and all 30 entries in the simulator catalogue**, plus the additional paper, code and dataset links cited by the research reports. Full revisions, recorded license facts, public URLs and the relevant report names are machine-readable there. Alternate article URLs and figure links are retained without counting them as additional papers. The [simulator review](research/published-simulator-reuse-review.md) explains the comparisons and their limits.

## Code and assets used by the implementation

| Source | Version inspected | Use and recorded terms |
|---|---|---|
| [FlyGym](https://github.com/NeLy-EPFL/flygym/tree/38c8ec61034cd59bc5ba0de20688d4a3c0000d60) / [NeuroMechFly v2](https://doi.org/10.1038/s41592-024-02497-y) | `38c8ec6` / package 2.1.0 | Body composition and assets, Apache-2.0. Its CPG/hybrid stepping controller is not the CNS controller. |
| [Eon fly-brain](https://github.com/eonsystemspbc/fly-brain/tree/a3db62f9436074e485c0278290c2164ed6150808) | `a3db62f` | GPU neural implementation. Original README states GPL-2.0-or-later; nested original Shiu code retains MIT. The public embodiment demonstration is a separate claim. |
| [Shiu et al. 2024](https://doi.org/10.1038/s41586-024-07763-9), [original code](https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960) | `91bdd1e` | Original circuit-assay baseline and antecedent of Eon dynamics; MIT. Its experimental support does not validate the later muscle/body interface. |
| [FlyMimic](https://github.com/gizemozd/FlyMimic/tree/9ea1131626cd76f7203b74076ef8f0e9cab30bef), [manuscript](https://arxiv.org/html/2509.06426v2) | `9ea1131` | Foreleg muscle geometry incorporated through FlyGym, Apache-2.0. Imitation-trained policy not adopted. |
| [MuJoCo](https://github.com/google-deepmind/mujoco/tree/3.9.0) | 3.9.0 | Apache-2.0, with separate third-party notices. Physics, native muscles and numerical integration. See the versioned source and [mechanics report](research/mn9-mujoco-mechanics.md) for the operations used. |
| [Arthur Zhao / Reiser Lab Eyemap Archive](https://github.com/artxz/eyemap-archive/tree/503c7f055d5491a48b60b49ade8c71798d24d8f1) | `503c7f0` | Optical-direction data and derived joins, CC BY-SA 4.0. Cite [Zhao et al. 2025](https://doi.org/10.1038/s41586-025-09276-5) and [Nern et al. 2025](https://doi.org/10.1038/s41586-025-08746-0). |

The FlyBody full-size OBJ mesh bundle used through FlyGym explicitly carries Apache-2.0 terms; this must be distinguished from the separately catalogued FlyBody datasets. FlyGym's retained iFish-derived retina code also has a separate [MIT notice](https://raw.githubusercontent.com/Gil-Mor/iFish/master/LICENSE), copyright © 2021 Gil Mor. Paper, dependency, source-file and asset licenses are distinct records.

## Executed offline references

These references run outside the embodied CNS. Their success establishes the stated source or numerical result, not a whole-fly physiological or learning capability.

| Reference | Original publication and source | Executed scope |
|---|---|---|
| Huang/Luo mushroom-body model | [Huang, Luo et al., Nature 2024](https://doi.org/10.1038/s41586-024-07819-w); [MATLAB source `5d7c08a`](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model/tree/5d7c08a9a88f923169a0c3008aca68af421e9a7f), GPL-3.0-or-later | Python derivative reproduces 240 saved fitted-response values and checks 172 workbook values. Fixed-bout pairing controls pass; no MaleCNS learning rule was installed. [Report](research/m7-huang-reference.md). |
| Odorant transduction and BSG | [Lazar and Yeh, PLOS Computational Biology 2020](https://doi.org/10.1371/journal.pcbi.1007751); [OlfTrans `3f873ea`](https://github.com/FlyBrainLab/OlfTrans/tree/3f873eafba3a21b8fcb27231b49835df1d3cbc0c), BSD-3-Clause | Nine Or59b–acetone OTP waveforms, stochastic source-law checks and exact BSG continuation; composed reference retains 31,003 spikes. Biological PSTH alignment remains unresolved. [OTP](research/m3-olftrans-reference.md), [BSG](research/m3-bsg-source-reference.md), [composition](research/m3-composed-odor-reference.md). |
| Force-probe and material references | [Azevedo et al.](https://elifesciences.org/articles/56754); [original analysis archive](https://doi.org/10.5281/zenodo.4527659); [Eldred et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/) | Instrument calibration and a separate skinned-muscle reference. These do not validate living motor-unit force. [Report](research/m2-calibration-results.md). |
| MS-WED passive electrical reference | [Wu et al., Cell 2024](https://doi.org/10.1016/j.cell.2024.07.047) | Two-recording effective RC comparison with held-out current amplitudes; systematic response mismatch remains. No fitted constants assigned to the CNS. [Report](research/m4-ms-wed-response-reference.md). |
| Static receptor and anatomical data | [Task et al. 2022](https://doi.org/10.7554/eLife.72599), [Hallem-table source](https://github.com/ttesileanu/OlfactoryReceptorDistribution/tree/a071b82519db371f85ebff750f21a3ba466cbbc0), [Cameron et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2865571/) | Published table/endpoint and identity checks; no complete dose/time encoder. [Odor reference](research/m3-odor-reference.md), [sensory evidence](research/m3-sensory-evidence.md). |

The historical [chungheng/neural driver](https://github.com/chungheng/neural/tree/bc4deffe611cdd72d510f744bf816aa56debe35d) helped resolve the BSG time/noise convention. Its metadata says “BSD,” but the exact variant and complete license text were not established. The separately verified OlfTrans BSD-3-Clause terms are not assigned to that driver by inference.

## Biological sources by subsystem

| Area | Principal sources | Detailed research |
|---|---|---|
| Connectomes and motor identity | [MaleCNS](https://doi.org/10.1016/j.cell.2026.08.015), [FlyWire](https://doi.org/10.1038/s41586-024-07558-y), [FANC](https://doi.org/10.1038/s41586-024-07389-x), [MANC](https://doi.org/10.7554/eLife.96084.3), [BANC](https://doi.org/10.1038/s41586-026-10735-w), [McKellar proboscis anatomy](https://elifesciences.org/articles/54978) | [Motor mapping](research/malecns-motor-mapping.md), [peripheral evidence](research/m1-peripheral-evidence.md), [neck adjudication](research/m1-banc-neck-adjudication.md) |
| Peripheral muscle and fluid mechanics | Azevedo/Eldred above; [Mahoney 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3913865/), [Mahoney 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5012858/), [Wang–Zhao–Swank](https://pmc.ncbi.nlm.nih.gov/articles/PMC3207158/), [Glasheen](https://pmc.ncbi.nlm.nih.gov/articles/PMC5814588/), [Manzo](https://pmc.ncbi.nlm.nih.gov/articles/PMC3341050/) | [Muscles](research/whole-body-muscle-mechanics.md), [flight](research/whole-body-flight-mechanics.md), [internal state](research/m2-internal-state-evidence.md), [salivary limits](research/m2-salivary-source-notes.md) |
| Odor and taste | Lazar–Yeh/Task above; [Kim 2015](https://doi.org/10.7554/eLife.06651), [Martelli 2019](https://doi.org/10.7554/eLife.43735), [Gorur-Shandilya 2017](https://doi.org/10.7554/eLife.27670), [DoOR 2.0](https://doi.org/10.1038/srep21841) | [Sensory mapping](research/malecns-sensory-mapping.md), [exact-acetate source limits](research/m3-acetate-dynamic-sources.md) |
| Vision, proprioception and temperature | [Song 2012](https://doi.org/10.1016/j.cub.2012.05.047), [Juusola 2017](https://elifesciences.org/articles/26117), [Mamiya](https://pmc.ncbi.nlm.nih.gov/articles/PMC6481666/), [Pratt hair plates](https://doi.org/10.1038/s41467-026-69333-z), [Elabbady bristles](https://doi.org/10.1016/j.cub.2026.03.045), [Marin thermal/humidity anatomy](https://pmc.ncbi.nlm.nih.gov/articles/PMC7443704/) | [Photoreceptor reference](research/m3-photoreceptor-reference.md), [body feedback](research/whole-cns-body-feedback.md), [sensory evidence](research/m3-sensory-evidence.md) |
| Central transmission and plasticity | [Hige](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/), [Yamada](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068490/), [Handler](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/), [Barnstedt](https://pmc.ncbi.nlm.nih.gov/articles/PMC4819445/), [Agrawal](https://elifesciences.org/articles/60299), Wu/Huang above | [Circuit evidence](research/m4-m7-evidence.md), [transmitter adjudication](research/m4-transmitter-primary-adjudication.md), [MeTu1 source gap](research/m4-metu1-adjudication.md) |

Each row is an entry point. The complete index retains every public source link from the research reports, including figure-specific citations, original code and data-release references. Preparation, species/sex, cell-type correspondence and fitted-versus-independent evidence remain in the associated reports.

## Datasets and terms

| Dataset | Public source | Recorded terms and scope |
|---|---|---|
| MaleCNS v1.0 | [Official release](https://male-cns.janelia.org/download/) | CC-BY terms. Anatomical data do not supply complete receptor/chemical parameters. |
| Eye-map exports | [Pinned archive](https://github.com/artxz/eyemap-archive/tree/503c7f055d5491a48b60b49ade8c71798d24d8f1) | CC BY-SA 4.0 for data and derived joins; attribution above. |
| Antenna electrophysiology alpha v0.1 | [Source and data terms](http://amacrine.ee.columbia.edu:15000/README.txt) | Database ODbL 1.0; individual contents DbCL 1.0. Separate from software BSD terms. |
| Huang/Luo article and supplementary data | [Publication](https://doi.org/10.1038/s41586-024-07819-w) | Article CC BY 4.0; model code separately GPL-3.0-or-later. |
| Photoreceptor response projects | [Dryad](https://doi.org/10.5061/dryad.12751), [publisher data](https://elifesciences.org/articles/26117) | Deposited-data CC0 stated by the article; inspected publisher workbooks and unavailable project files are distinguished. |
| FlyBody datasets | [Figshare v4](https://doi.org/10.25378/janelia.25309105.v4) | Catalogue lists GPL 3.0+. This is distinct from Apache-2.0 software and the explicitly Apache-2.0 mesh bundle. |
| Transmitter/peptide tables | [NT `a941741`](https://github.com/flyconnectome/drosophila_neurotransmitters/tree/a9417412c8a70fcc9f80a65ca5bc6064eba07be3), [peptides `7a1416a`](https://github.com/flyconnectome/drosophila_neuropeptides/tree/7a1416a5e244d415e8cabdd3172592dab7d65dc2) | CC BY 4.0; expression evidence is distinct from release, receptor action and kinetics. |
| Foreleg recordings and analysis | [Dryad](https://doi.org/10.5061/dryad.76hdr7stb), [Zenodo analysis](https://doi.org/10.5281/zenodo.4527659) | Retrieved analysis and unavailable raw trials are recorded separately; do not infer file availability from a dataset citation. |
| Taste companion preprint v2 | [Publication](https://doi.org/10.1101/2025.08.25.671814) | Source record states CC BY-NC-ND 4.0. Cited for biological interpretation; that is not a blanket license for implementation or data redistribution. |

## Reviewed alternatives and community catalogue

The review covers original NeuroMechFly, FlyBody, FlyVis, FlyBrainLab/EOScircuits/VisTrans, Pugliese, FlyGM, Digital Sphinx, antennal-grooming decoders and related neural models. Their usable anatomy, equations or comparison methods are separated from trained behavioral decoders and source-specific assumptions. The Juusola photoreceptor repository contains a **GNU GPL v3 `LICENCE.txt`**; this corrects an earlier missed-file finding. Its source was inspected, but no original photon-to-voltage model was executed.

The [index](reference-index.json) preserves all 30 catalogue names and original public links, including the community body/game systems, discovery indexes and author-post-only demonstrations. The 44 exact repository revisions remain listed even where the implementation was only reviewed. Missing code or data licenses remain marked as unresolved. Source visibility, an author-reported score and this bibliography do not establish permission, independent reproduction or physiological validity.

Follow the original publication and repository links; use the research reports for what was implemented, checked and left open.

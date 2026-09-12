# Attribution and licenses

Original project code is GPL-3.0-or-later; see [LICENSE](LICENSE). This includes
the integrated code derived from or combined with GPL research components.
Third-party files retain their original notices. Data and assets have separate
terms; the project code license does not relicense them.

| Material | Source and use | Terms |
|---|---|---|
| Eon `run_pytorch.py`, `benchmark.py` | Unmodified pinned neural implementation in `runtime/eon-brain/`; revision `a3db62f9436074e485c0278290c2164ed6150808` | GPL-2.0-or-later; [original license](licenses/Eon-GPL-2.0.txt), [notice](runtime/eon-brain/NOTICE.md) |
| Shiu `model.py` | Original Brian2 reference in `runtime/shiu-brain/`; revision `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` | MIT, copyright Philip Shiu and Nico Spiller; [notice](licenses/Shiu-MIT.txt) |
| FlyGym/NeuroMechFly and bundled FlyMimic/FlyBody geometry | Installed from the pinned upstream source; stepping policies are separate from the CNS loop | Apache-2.0; [FlyGym notice](licenses/FlyGym-Apache-2.0.txt); upstream asset-specific notices remain with the dependency |
| Huang/Luo port and selected original model inputs | `research/huang_reference.py`, selected MATLAB/XLSX/FIG inputs under `data/research/` | GPL-3.0-or-later for the original program; original article/data CC BY 4.0 where stated. Copyright Junjie Luo, Cheng Huang and Mark J. Schnitzer. [Source](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model/tree/5d7c08a9a88f923169a0c3008aca68af421e9a7f) |
| OlfTrans source and derived reference | Original model file and isolated Python references | BSD-3-Clause, copyright Tingkai Liu; [original notice](licenses/OlfTrans-BSD-3-Clause.txt) |
| Lazar/Yeh notebook expressions | Original S1 NoisyConnorStevens source and its stated reference interpretation | Original PLOS article/supplement CC BY 4.0; [publication](https://doi.org/10.1371/journal.pcbi.1007751) |
| MaleCNS annotations/graph and motor curation | Versioned factual map, optional prepared graph and original source inputs | CC BY 4.0; MaleCNS collaborators; [release](https://male-cns.janelia.org/download/) |
| Optical data and public sensory map | Author eye directions plus MaleCNS column/graph joins | CC BY-SA 4.0; Arthur Zhao / Reiser Lab; [exact provenance](data/sensory-map-provenance.json) |
| Legacy FlyWire v783 data | Optional original/derived scientific inputs, distinct from MaleCNS | CC BY-NC 4.0; [official guidelines](https://flywire.ai/guidelines) and original source records |
| Antenna electrophysiology | Original inputs to the isolated odor references | ODbL 1.0 database and DbCL 1.0 contents; source notices retained in the scientific archive |

Public source metadata and the archive index record file-level source URLs,
hashes and terms. Original material with noncommercial or no-derivatives terms
retains those terms when included unchanged. Unestablished redistribution rights
are recorded as reference-only; availability on a website is not a new license.
The regenerated live sensory map does not copy the restricted taste table or the
separate historical FlyWire crosswalk.

The [reference guide](docs/references.md) and [complete index](docs/reference-index.json)
distinguish code used in the runtime, executed offline references and reviewed-only
projects. Citing a reviewed project does not claim it was incorporated. Please
credit the original authors and cite the exact source versions used in a study.

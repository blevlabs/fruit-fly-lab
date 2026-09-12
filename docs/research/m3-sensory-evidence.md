# M0/M3 sensory evidence and expanded peripheral inventory

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

The 2026-09-11 audit found 6,358 connected sensory entries in the embodied-v2 baseline, out of 17,937. It individually inventories the remaining **11,579 IDs**, in 446 of the 473 original annotation groups. This adjudicates input gaps; it does not complete those inputs or close M3.

The reproducible records are in outputs/program/m3 (original artifact `m3`):
`sensory-entries.csv` contains every exact ID, its original class/type/side/nerve,
baseline wiring status, missing datum and source route;
`sensory-groups.json` supplies the exact ID arrays grouped by the original four
annotation fields; `sensory-inventory.json` supplies totals, source identities,
gap definitions and explicit evidence boundaries. Historical `currently_wired`
fields in the anatomy map predate embodied-v2 and were **not** used as runtime
coverage. The wired set was read from `Senses` and pinned before extensions.

The historical inventory check matched the frozen annotation and primary taste workbook SHA-256 hashes to the anatomy map.

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The check passed the 17,937-ID partition, all 473 groups, 254 outside-selector entries,
241 organ-level wing correspondences, and hashes of retrieved source files.
This was a data-integrity check without simulation. Its identities and counts describe the frozen baseline.

## Every unconnected category

These are mutually exclusive original `coverage_id` categories, restricted to
the baseline's unwired IDs. Class counts and every exact ID are in the data
files; nerve inventories overlap modalities and must not be added to this table.

| Baseline gap | IDs | Exact datum still needed / next source route |
|---|---:|---|
| Leg mechanics | 2,231 | Cell-to-sensillum/joint/attachment site and axis; local strain or deformation transfer and per-cell tuning. MANC morphology, campaniform atlas, FeCO anatomy/physiology. |
| Additional odor tuning | 1,959 | Identified compound/receptor response matrix, gas concentration and kinetics; correctly located antennal or palp sample. Primary receptor-response data. |
| Unknown/tentative modality | 1,878 | Peripheral organ/modality for each unresolved type or fragment, before choosing a physical stimulus. Retained annotations and individual morphology; new wing organ crosswalk below refines a subset. |
| Body/head/mouth mechanics | 1,455 | Local receptor attachment/site/axis and transfer, including pharyngeal deformation. Rostrum angle or whole-body contact does not establish each input. |
| Other contact taste | 1,292 | Ligand/marker identity, labellar/tarsal/wing/peg/pharyngeal contact site and dose dynamics. Primary taste workbook and underlying receptor studies. |
| Antennal mechanics | 744 | Organ displacement under acoustic/airflow/gravity/contact load, receptor axes and subtype response filters. Includes 672 JO-type entries. |
| Wing mechanics | 589 | Individual sensillum site/orientation, hinge or cuticle transfer and spike timing. New organ matches below do not resolve these quantities. |
| Haltere mechanics | 435 | Individual cell-to-field/site/axis plus mechanical strain transfer and latency; not a common body-angular-velocity signal. |
| Odor root side | 411 | Peripheral-root laterality; then receptor-specific chemical tuning. Soma or central arbor side cannot substitute. |
| Compound-eye direction chain | 378 | 224 lack columns; 154 have columns but lack standard author vectors. Missing receptors/columns cannot be filled by mirroring or nearest neighbors. |
| Humidity / evaporative channels | 69 | Physical humidity/microclimate; subtype physiology for putative VP1d/VP1m roles; one VP4 origin side. |
| Chemical quality unresolved | 58 | Specific ligand and organ; candidate nociceptive anatomy does not establish a heat/injury channel. |
| Labellar high salt / metal | 26 | Ion-specific fields, sensillum site, concentration-response and kinetics. |
| Labellar amino acid | 19 | Amino-acid-specific aqueous concentration and response; LB1e is not generic bitter. |
| Labellar water | 17 | Aqueous contact and osmolarity plus response curve and dynamics. A bounded reference is available below. |
| Remaining cooling | 9 | Eight HRN_VP1l entries and one TRN_VP3b; sacculus/other receptor identity, local thermal transfer and measured kinetics. |
| HB eyelet | 7 | Separate optical registration, acceptance, spectra and transduction; not ordinary compound-eye columns. |
| Residual generic LB3 | 2 | Exact fine subtype; preserve sugar/water ambiguity. |
| **Total** | **11,579** | **All remain open until their specific anatomical/physical/physiological gates pass.** |

Two FeCO exceptions are explicit: **906066** is SNpp40/proprioceptive but enters
ProAN, outside the baseline leg-nerve join; **933699** is SNpp51 but has the raw
`unknown_sensory` class. Neither was added by assuming the conflicting field was
wrong. Already wired FeCO cells also lack individually measured polarity/tuning
and complete organ mechanics. The baseline position/velocity encoder is a
declared hypothesis, not recovered per-cell physiology.

## New primary anatomy improves identity but does not supply strain encoding

[Lesser, Moussa and Tuthill, version of record March 2026](https://elifesciences.org/articles/107867)
provides a MANC-type-to-organ table (Appendix 1, table 1) and peripheral imaging.
Joining its named types to exact MaleCNS ADMN entries yields the following
**organ-level cross-specimen correspondences**, retained separately in
`wing-organ-correspondences.json`. The paper's experiments use female flies and
FANC; this is not a claim of direct peripheral imaging of the MaleCNS specimen.

| Organ | Published MANC types | Exact MaleCNS rows |
|---|---|---:|
| Proximal small campaniform | SApp04/10/11/13/14/18/19/20/21 | 83 |
| Distal small campaniform | SNpp04/08/11/33/36/06/26 | 29 |
| Large campaniform | SNpp30/32/31 | 18 |
| Tegula campaniform | SNpp28/37/38 | 30 |
| Tegula hair plate | SNxx26 | 12 |
| Tegula chordotonal | SNpp07/10 | 19 |
| Radius chordotonal | SNpp29/61/62/63 | 37 |
| Thorax sensor near wing hinge | SNpp16 | 13 |
| **Total** | | **241** |

The 12 SNxx26 rows retain their raw `unknown_sensory` annotation with a separate
published hair-plate correspondence. Eighteen combined `SNpp29,SNpp63` rows can
be assigned to the common radius organ family without pretending to resolve
their individual subtype. Sensor sites, axes, mechanical transfer, firing-rate
functions and latencies remain missing. No new active sensory binding follows
from these matches.

[Dhawan et al., final publication 2026](https://doi.org/10.1016/j.cub.2025.12.024)
and its [accessible primary preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12154908/)
show that a haltere morphological subtype contains receptors from multiple
peripheral fields. Therefore a common subtype-to-strain-axis assignment is not
supported. The deposited FANC reconstructions and images are a route for a
future morphology correspondence, not a MaleCNS body-ID map. The required
measurement is the individual sensillum origin and local strain response.

For legs and body, the [Dinges campaniform atlas](https://kups.ub.uni-koeln.de/25156/)
is an accessible peripheral anatomical route; a sensillum's cuticle position
alone does not identify its MaleCNS cell. For antennae, the
[Johnston's-organ vibration/deflection study](https://pubmed.ncbi.nlm.nih.gov/24847281/)
supplies physiological subgroup evidence, not a displacement/axis assignment
for every annotated JO cell. These routes remain open for detailed registered
morphology and quantitative transfer; this audit does not claim exhaustive
literature failure.

## Smallest supported encoder extension: a bounded water reference

The primary taste workbook matches its pinned hash and supplies the 17 ppk28-matched LB3a IDs, nine left and eight right;
the exact IDs remain in the map's `contact_water` group. No inferred partner is
added. The [primary companion workbook](https://europepmc.org/api/fulltextRepo?pprId=PPR1072256&type=FILE&fileName=EMS208214-supplement-Supplemental_table_2.xlsx&mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&version=2)
provides identity evidence, not rate constants.

[Cameron et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2865571/)
reports adult labellar l-type bristle recordings: water control **12.0 ± 0.9
spikes/s**, ppk28-null **0.8 ± 0.1**, rescue **6.4 ± 1.0** (mean ± SEM).
Recordings counted the first second; all test solutions contained 1 mM KCl.
The methods describe 2–3-day-old flies transferred to fresh medium the day
before testing; recording age is not separately disambiguated.
Solutes suppress the response; the measured reference is not a universal
steady firing rate. Heterologous-cell calcium/osmolality measurements in the
same paper are not native-neuron spike calibration.

The standalone [water_reference.py](../../research/water_reference.py) implements
only this measured endpoint. Its assay accepts explicit individually contacted
LB3a IDs, added osmolarity above the source's **1 mM KCl carrier**, carrier
concentration and observation window. Zero added solute is the supported water
preparation; measured absolute osmolarity was not reported. The output is a
first-second mean count equivalent, **not an instantaneous rate or spike
train**. Uncontacted cells receive zero external stimulus contribution, without
claiming zero spontaneous firing. Contacted solutions with any positive added
osmolarity and observation windows other than one second are rejected as
unsupported. No artificial dose curve, adaptation law or 200-Hz template was
introduced. This is an isolated endpoint reference.

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The reference check (original artifact `m3/water-reference/reference-check.json`)
passes exact subtype/side joins, single-cell and left/right isolation,
contact-response direction, stateless replay, source identity and invalid or
unsupported input rejection. With no integrator, it makes no timestep or
adaptation claim. Reproducing the calibration mean gives zero endpoint replay
error; that is not held-out validation. Ppk28-null/rescue counts and solute
suppression were not used to select the endpoint constant, but no deletion,
rescue or quantitative concentration model exists to predict them. Those
comparisons are explicitly **not executable**.

The publisher's retrieved seven-page supplement and Figure 2 are retained
with retrieval hashes in `m3/water-reference/sources/`.
Supplementary Figure 4 supplies calcium dose responses, including data reused
from Figure 1e; it does not provide a native water-neuron spike/osmolarity
curve. The supplement notes a possible physical access confound at high
concentration. Figure 2a/b does not state recording sex or a replicate count;
behavioral or imaging sample counts cannot substitute. Source recordings were
from l-type sensilla, and applying their population mean to each MaleCNS LB3a
ID remains a cross-preparation reference assumption. The 17 anatomical IDs
are not experimental replicates; summing their reference values is not
comparable to the source's single-sensillum mean. The
source audit (original artifact `m3/water-reference/sources/cameron2010-source-audit.json`)
records these preparation and data limits. The exact missing data
are native per-cell dose/time traces, solution osmolarity, spontaneous
activity, adaptation/recovery, sensillum correspondence and replicate-level
uncertainty. The 17 IDs remain **unwired in embodied-v2**, and the full M3 gate
remains open.

The distinct-odor source study recovered the author-shared
**110-chemical × 24-receptor measured matrix** and a standalone two-acetate
endpoint reference. [The odor report](m3-odor-reference.md) records the exact
121-ID join, matched nominal protocol, signed response values, source-access
outcomes and passing checks. This is not a physical plume or absolute-rate
encoder; native transfer, gas concentration and dynamics remain open. Two
food-source labels using a common ORN mixture still do not create
different odors in the running model.

The subsequent exact-source pass recovered the publisher's original
supplement, verified S1 rounding and all **2,592 S2–S4 dose/time values**, and
added executable queries that reject unmeasured bins and doses. That source
retrieval dependency is closed. Source correction conventions, native transfer
and the selected acetate pair's absent temporal series remain explicit in the
odor report; no continuous sensory law was inferred.

The retrieved [Marin thermo/hygrosensory paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7443704/)
retains VP1l cooling and VP1m humidity as proposed functions awaiting physiology;
VP1d is putative evaporative cooling. No measured VP3b kinetics were recovered
from that source. These limitations remain separate from the existing
13-cell VP2/VP3a estimated thermal implementation.

## Outside the baseline sensory and motor selectors

The frozen annotation contains **254 additional classified entries** excluded
from both selector denominators but retained by the CNS importer:

| Superclass | Entries |
|---|---:|
| vnc_efferent | 94 |
| cb_efferent | 4 |
| efferent_ascending | 8 |
| efferent_descending | 4 |
| cb_endocrine | 72 |
| vnc_endocrine | 22 |
| ENS | 50 |

Exact rows, original fields and missing data are in
`outside-selector-entries.json`. Forty-seven of the 50 ENS entries are Traced;
none has an annotated type, group, class, receptor, entry nerve or exit nerve.
The other 204 entries are Traced. Two additional traced superclass-null
peripheral fragments, **527138** (AN) and **544325** (aPhN), require identity
adjudication and are not counted as two new confirmed whole neurons.

The 254 is the endocrine/efferent/ENS count, not an exhaustive extra sensory
denominator. A broader field audit found **eight `vnc_intrinsic` entries with
an annotated peripheral entry nerve**: 811546, 819020, 820510, 904191, 908119,
909033, 910338 and 1060584352. Seven are Traced; 1060584352 has null status but
is retained by its superclass. These raw field conflicts need anatomical
adjudication. In addition to the two traced fragments, **27 superclass-null
Orphan fragments** have AN/MxLbN entry annotations and are excluded by the
baseline importer. Their owning neurons must be resolved before importing or
counting them as additional receptors. `additional-selector-boundaries.json`
preserves all 41 entry-nerve boundary rows, including the four already counted
endocrine/efferent rows, so overlap is explicit.

That file also retains 48 exact entries with named DN1, LNd, LNv or LPN clock
types outside the sensory selectors. This is a central-regulation inventory;
it does not assert direct photoreception or a shared endogenous oscillator
for those cells. Cell-specific intrinsic dynamics and entrainment mechanisms
belong to M4 and require independent physiology.

The [MaleCNS primary preparation and annotation methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12636603/)
describe an isolated intact CNS, comprising brain, neck and VNC. Sensory axons
are identified entering the reconstruction; their peripheral somata/end organs
are often absent. Superclass-null objects are treated as fragments. Thus even
complete coverage of the baseline selectors cannot certify the complete peripheral
nervous system, external sensory organs, gut circuitry or endocrine targets.
New cells absent from the volume must not receive invented replacement IDs.

Target tissues, secreted ligands/receptors, hemolymph transport and response
kinetics remain required for endocrine/efferent effects. The 50 ENS IDs alone
do not identify complete crop, gut, respiratory or energetic feedback. Raw
CAPA endocrine rows with strand-receptor/abdominal sensory-looking annotations
also need adjudication; they are not automatically relabeled sensory.

A new [McKim neurosecretory study](https://elifesciences.org/reviewed-preprints/102684v2)
and its [July 2026 deposit](https://zenodo.org/records/20795211) supply an exact
71-ID MaleCNS brain-neurosecretory table. All 71 exist as `cb_endocrine` in the
frozen release. Six IDs untyped in that release (14218, 54465, 549638, 31871, 13231,
35813) receive the source's `l_NSC_CRZ` label; six DNES2/3 IDs (48615, 14564,
535210, 25364, 87303, 16353) receive `l_NSC_DH31`. The source retains ten
`l_NSC_unknown` and eight `m_NSC_unknown` cells; MaleCNS ID **134996** is absent
and remains unassigned. These are curated source correspondences, not newly
validated release physiology. Exact rows, source CSV, author table-building
code, CRC32/SHA-256 checks and retrieval receipts are retained under
`m3/endocrine/peripheral-boundary-sources/`.

The deposit's enteric-group table contains 79 FlyWire rows and no MaleCNS
rows; it does not authorize ENS1–5 transfer into the 50 MaleCNS ENS entries.
The author's cross-dataset table pads type groups and binds columns. Sharing
one output-table row therefore does not establish an individual cross-specimen
match. Missing hormone-target/receptor and peripheral-transfer measurements
remain explicit.

## Evidence status and remaining dependency

**Implementation:** the baseline routing was checked by exact IDs; the water/odor references are isolated source assays. **Numerical correctness:** historical inventory, source-table and observed-point reference checks passed. **Biological validation:** all connected encoders still have uncalibrated aspects, and
none of this inventory proves per-cell transduction. **Demonstrated
capabilities:** no behavior is demonstrated by an anatomical join or source
retrieval.

Retrieved public source bytes and SHA-256 hashes are retained under
`m3/sources/`. PMC pages returned access challenges, so their
public Europe PMC XML endpoints were used where available. The final haltere
XML endpoint returned 404; its accessible preprint was retained with its own
version. The taste full-text endpoint returned 500, while the exact primary
workbook succeeded. The MANC reviewed-preprint route returned 403 on this
audit. These are source-access outcomes, not evidence that the biology is
unknown.

The concrete external dependency is **cell-resolved peripheral
correspondence and independent organ/transduction measurements** where the
public records only establish class/organ families. Required examples include
sensillum position/axis and cuticle strain transfer for wing/haltere cells;
receptor sites and dynamics for tactile/internal pathways; missing visual
columns/vectors; and receptor-specific chemical/thermal/osmotic calibration.
New biological measurements are absent from this study. M3
cannot close while these required inputs remain unsupported. Independent
mechanics, persistence and bounded receptor reference assays can continue.

# M3 distinct-odor reference

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

**The original measured response matrix supports a bounded endpoint reference.** The historical check in [odor_reference.py](../../research/odor_reference.py) passed on 2026-09-11. This study does not close M3.

## Source and preparation

The [Hallem–Carlson primary study](https://www.sciencedirect.com/science/article/pii/S0092867406003631)
measured individually expressed Or genes in the ab3A empty-neuron preparation
(`w; Δhalo/Δhalo; Or22a-GAL4/UAS-Or`), using flies younger than four weeks;
sex was not specified. A 500-ms post-onset count is corrected by a 500-ms
unstimulated count and the diluent response, then reported in spikes/s.
The delivery settings were 24 mL/s carrier air and 5.9 mL/s through the odor
pipette. The pure-odor panel uses nominal 10⁻² liquid dilution; both selected
acetates use paraffin oil. These are not measured gas concentrations.

The authors supplied their unrounded Table S1 matrix and individual baseline
records to the authors of the
[receptor-distribution study](https://elifesciences.org/articles/39279).
Its [pinned data documentation](https://github.com/ttesileanu/OlfactoryReceptorDistribution/blob/a071b82519db371f85ebff750f21a3ba466cbbc0/README.md)
describes the conversion and permission to redistribute.
[The retained MATLAB file](https://github.com/ttesileanu/OlfactoryReceptorDistribution/blob/a071b82519db371f85ebff750f21a3ba466cbbc0/data/flyResponsesWithNames.mat)
contains **110 × 24 measured response means**, 24 baseline means and 24
baseline standard deviations. Its SHA-256 is
`1e3521737ab04804e24feb57766293ee626cf7df502da4bde73b1f46eb8fd882`.
No DoOR consensus, imputation, normalization or integer rounding was used.

The source audit recovered **the publisher's complete 14-page PDF** from its
[official CDN attachment](https://ars.els-cdn.com/content/image/1-s2.0-S0092867406003631-mmc1.pdf):
HTTP 200, 7,368,487 bytes, SHA-256
`de4b020b4a42db327800ee856130adfc3857d6695657477cd1feea3b9dd796c2`.
Cell's attachment URL still returned 403 and the API-metadata link returned
404. Historical access outcomes are in the
route receipt (original artifact `m3/odor-reference/temporal-dose/route-receipt.json`);
the earlier source audit remains an unchanged historical receipt.

The Table S1 comparison (original artifact `m3/odor-reference/temporal-dose/table-s1-rounding-check.json`)
confirms all **2,640 response values and 24 baseline means** against the
printed original within its integer rounding (maximum difference 0.5).
The original also resolves the author-MAT label `6-methyl` as
`6-methyl-5-hepten-2-one` and preserves stereochemical detail omitted in a few
MAT names. Those name variants are recorded separately in the source comparison.

## Two-chemical endpoint and exact anatomical join

Methyl acetate and ethyl acetate are chemically distinct members of the same
source panel. They have matched nominal dilution, solvent, pulse/count windows
and delivery settings. The comparison does not equate vapor pressure,
gas-phase molarity, receptor concentration, or unreported temperature/humidity.

| Source-corrected mean response, spikes/s | Or22a | Or43b | Or59b |
|---|---:|---:|---:|
| Methyl acetate | 54.000 | 21.833 | 269.000 |
| Ethyl acetate | 52.667 | 132.000 | 177.000 |

The source caption implies six sensilla per selected response except
methyl-acetate/Or43b, for which the rule gives four. These are inferred from
the caption's rule, not separately recovered per-entry raw counts. Up to three
sensilla could come from one fly. The source did not quantify inhibition for
these low-baseline receptors; all six selected endpoints are positive.

[Task et al.'s primary receptor/co-receptor study](https://elifesciences.org/articles/72599)
provides the glomerulus–gene correspondences in Table 3 and additional direct
physiology supporting DM2 and DM4 identities. Joining those glomeruli to the
frozen MaleCNS types produces:

| Receptor reference | MaleCNS type | Left IDs | Right IDs | Withheld unknown-side IDs |
|---|---|---:|---:|---:|
| Or22a | ORN_DM2 | 24 | 29 | 1 |
| Or43b | ORN_VM2 | 17 | 20 | 4 |
| Or59b | ORN_DM4 | 16 | 15 | 1 |
| **Total** | | **57** | **64** | **6** |

The 121 supported IDs satisfy the raw olfactory class, exact type, antennal
entry nerve and root-side conditions. The six withheld IDs are 925495,
955452, 534097707, 766592451, 891139438 and 1037165389. No anatomical side is
invented. The two other mixture channels in the baseline model, DM1/Or42b and VA2/Or92a, are
absent from the 24-receptor source panel and receive no substituted profile.
The dataset's `receptorType` field is null for these MaleCNS rows; the gene
bridge is published type-level evidence, not direct expression measurement
in each reconstructed cell.

Native DM2 coexpresses Or22b and additional co-receptors, and DM4 also has
co-receptor expression beyond the old single-family description. Empty-neuron
gene responses therefore remain a reference preparation, not proof that every
native MaleCNS cell has the same quantitative tuning. Neither the 121 IDs nor
their population-weighted sum is an experimental replication count or a
replacement for receptor-level means.

## Historical check and remaining work

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The check receipt (original artifact `m3/odor-reference/reference-check.json`)
records the exact IDs and isolated side-specific outputs. The check reads back
the 110 × 24 source matrix, verifies orientation and all unrounded values,
retains all **829 negative observations**, and verifies the anatomical joins.
Both chemicals produce their measured three-component pattern independently
on either side. Blank solvent-corrected input and unexposed sides contribute
zero response difference; this is not a zero-spontaneous-firing claim.
Food/color labels and unsupported dilution, solvent, time or gas-concentration
parameters are rejected. Repeated calls do not advance any state.

The two receptor-level vectors are not scalar multiples of a common mixture;
the Or43b/Or59b determinant is −31,643.559 (spikes/s)². That is a numerical
property of the measured means, not a statistical discrimination threshold or
a demonstrated CNS ability. No vector is rescaled or selected from a motor,
navigation or learning outcome.

**Implementation and numerical checks pass. Biological validation stays
open; behavior and learning were not tested.** Looking up source values
reproduces observations used as references. It supplies no prediction for
unseen doses, mixtures, pulse lengths, adaptation or new cells. Unused matrix
rows remain source data, not a prospective holdout. Baseline SD is not
odor-response uncertainty, and adding the stored background mean to a
background- and diluent-corrected response has not been validated as an
absolute firing-rate reconstruction.

## Tables S2–S4: source routes resolved and exact observations checked

The original supplement places dilution data in **Table S2, page 5**, and
temporal data in **Table S3, page 6**, and **Table S4, page 7**. Its legends
tie S3/S4 to Figure 5. Both temporal pages were visually inspected.

| Original source | Recovered scope | Numerical values |
|---|---|---:|
| S2 | 10 single compounds at 10⁻², 10⁻⁴, 10⁻⁶, 10⁻⁸; nine fruit extracts undiluted and at 10⁻², 10⁻⁴, 10⁻⁶; 24 receptors | 1,824 |
| S3/S4 | Methyl salicylate, pentyl acetate, 2-heptanone and apple extract; 10⁻² and 10⁻⁴; 24 receptors; four 500-ms bins spanning 0–2 seconds after onset of a 500-ms pulse | 768 |

These are means from the empty-neuron preparation, n=6. The time columns
denote bin starts at 0, 0.5, 1 and 1.5 seconds, not instantaneous samples.

The pinned author-shared Tesileanu repository contains only the S1 matrix and
baseline statistics for flies. The previously identified Connectome
Interpreter source index leads to raw CSVs in
[its preprocessing repository](https://github.com/YijieYin/interpret_connectome/tree/a4df3b0d5345d2a34dac813f897d8427f6a6eb45).
Its file named `Hallem_Carlson_2006_S3.csv` combines **both original S3 and S4**.
Every raw value and condition label was checked against the recovered PDF:
**2,592 values and 268 condition labels, zero mismatches**. The package's tidy
versions divide responses by 288 and use DoOR for receptor-to-glomerulus
names. They contain no response imputation, but their normalized values are
not physiological spikes/s and were not adopted here.

The extracted dose CSV (original artifact `m3/odor-reference/temporal-dose/source-index/canonical-dose-series.csv`)
and extracted time CSV (original artifact `m3/odor-reference/temporal-dose/source-index/canonical-time-series.csv`)
retain original receptor names, signed unnormalized values, table/panel/page,
dilution and bin metadata. The
source-index audit (original artifact `m3/odor-reference/temporal-dose/source-index/source-index-audit.json`)
records exact commits, URLs, transformations and limits. The public [exact-point query check](../../research/check_odor_time_dose.py) covers the measured doses and bins.

[Package checks](../../tests/) and the [results index](../../results/README.md) describe the distributed verification material.

The historical source comparison and query checks both passed. The query check (original artifact `m3/odor-reference/temporal-dose/exact-dose-time-check.json`)
replays every tabulated value and rejects unmeasured doses, between-bin times,
out-of-range times and food labels. No interpolation, adaptation equation,
spike train or runtime integration was added.

Usable examples include ethyl-acetate S2 values at four doses: Or22a reports
53, 18, 2 and −3 spikes/s. At 10⁻², the Or22a temporal sequence is
156, 51, 46, 40 for pentyl acetate and 109, 21.33, 8, 5 for 2-heptanone.
Those two molecules can support a separate observed temporal reference at
either measured dilution. **The existing methyl/ethyl-acetate pair was not
silently replaced:** methyl acetate has no S2 series and neither selected
acetate has S3/S4 temporal data.

S2 explicitly includes the diluent correction. The temporal-table legend does
not independently restate that extra correction; its first bins differ from
S1/S2 values for the same nominal stimulus. For example, pentyl-acetate Or22a
is 158 in S2 but 156 in the temporal first bin. The tables remain separate;
the difference is not assigned to noise, a diluent term or adaptation by
assumption. Clarification of table-specific correction and trial correspondence
is needed before pooling or reconstructing absolute firing.

The supplement also contains **Figure S4**, distinct from **Table S4**:
graphical responses to 100-ms, 500-ms, 1-s and 5-s pulses with SEM, n=6.
For 100-ms pulses its first two bins are 100 and 400 ms; subsequent bins are
500 ms. These plotted data were not digitized into the table reference.

**The S2–S4 retrieval dependency is closed.** The observed-point reference
checks are executable. Before a continuous or absolute-rate encoder is
claimed, the next action is to resolve per-table correction/trial details and
define an independent comparison for the proposed transduction mechanism.
Remaining biological dependencies are raw trial and
correction details, numerical trajectories beyond the tabulated bins, native
receptor transfer and concentration at the sensory organ. The selected acetate
pair's missing time series remains a specific measurement gap. Neither
check establishes odor-guided behavior, learning or a complete M3 gate. The historical baseline contained 6,358 connected sensory entries.

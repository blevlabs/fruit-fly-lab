# MeTu1 body 43034: transmitter and import adjudication

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

**Disposition: an upstream connectivity/annotation coverage gap, correctly preserved by the local importer. No import repair or transmitter-sign assignment is warranted.** Body **43034** has no released transmitter-table row and no incoming or outgoing edge in the released raw connectome. It is therefore not one of the cells explicitly labelled `consensus_nt=unclear`; its transmitter fields are absent. The prepared graph faithfully preserves the cell, its missing transmitter information and its zero connectivity.

The source/graph inspection was performed on 2026-09-12. Annotation/transmitter hashes matched the frozen release; published object ETags matched the source-file MD5 values. Exact records are identified in the historical MeTu1 adjudication archive.

## Exact identity and source record

The released annotation identifies 43034 as `MeTu1_L`, with `type=MeTu1`, `flywireType=MeTu1`, `superclass=visual_projection`, `somaSide=L`, `status=Traced`, and the more specific `statusLabel=Prelim Roughly traced`. Its hemibrain field is the combined string `MC61,MC64`. The present conclusion uses the direct MeTu1 correspondence; it does not split that combined alias or infer a new connection from it.

The raw annotation contains **250** MeTu1 cells. **249** have transmitter rows with both `ground_truth=acetylcholine` and `consensus_nt=acetylcholine`. Their shared cell-type prediction is acetylcholine with confidence **0.9429028400197786**. Their individual prediction counts range from 92 to 273. **43034 is the only MeTu1 cell absent from the transmitter table.** These observations are in local-source-and-prepared-readback.json (original artifact `program/m4-m7/metu1/local-source-and-prepared-readback.json`) and structural-and-peer-readback.json (original artifact `program/m4-m7/metu1/structural-and-peer-readback.json`).

A complete read-only scan of **151,856,684 raw segment-edge rows** in 2,318 record batches found **zero incoming and zero outgoing edges** for 43034. The prepared graph independently has zero incoming/outgoing edges and contacts for the same ID. Thus the missing pathways were not removed by the neuronal-subset filter. The raw scan receipt is raw-edge-readback.json (original artifact `program/m4-m7/metu1/raw-edge-readback.json`).

## What the original assay establishes

The curated citation “Nern et al., 2024” refers to the preprint subsequently published as [Nern et al., Nature 2025](https://doi.org/10.1038/s41586-025-08746-0). The final Supplementary Table 5, `Sheet1!A103:H103`, reports **MeTu1**, driver **SS00385**, observed **ChAT** signal, **EASI-FISH**, inferred **ACh**, and `Part_of_training_data=no`. The earlier repository workbook, row 83, contains the same positive marker and transmitter, with the less specific method label “FISH”. The final source resolves that method-label difference.

Supplementary Table 6, row 101, identifies SS00385 as `w; R84F07-p65ADZp in attP40; R70E04-ZpGdbd in attP2`, stock `RRID:BDSC_88550`. The retained primary-assay-table-readback.json (original artifact `program/m4-m7/metu1/primary-assay-table-readback.json`) records exact cells and hashes; the two original spreadsheets are retained alongside it. Both came from the [publisher's supplementary-table archive](https://media.springernature.com/full/springer-static/esm/art%3A10.1038%2Fs41586-025-08746-0/MediaObjects/41586_2025_8746_MOESM4_ESM.zip).

This is positive, cell-type-level evidence for a cholinergic phenotype. The methods describe qualitative assessment of marker expression; they caution that their selective marker screening may miss co-transmission. The MeTu1 row does not separately quantify VGlut-negative or GAD1-negative results, although the later curated table encodes negative glutamate/GABA evidence. The inspected source does not provide a MeTu1-specific assay sex, replicate count, uncertainty estimate, release probability, synaptic current or postsynaptic receptor measurement. It does not measure body 43034 individually.

“Not part of training data” refers to the **optic-lobe paper's classifier**. The later [MaleCNS training source](https://github.com/flyconnectome/drosophila_neurotransmitters/blob/a9417412c8a70fcc9f80a65ca5bc6064eba07be3/gt_sources/male_cns/202509-male_cns_gt_data.csv), CSV line 3075, explicitly includes MeTu1 with this study and ACh evidence. It therefore cannot also serve as independent validation of the current MaleCNS transmitter assignment.

## Consensus procedure and owning code

The [MaleCNS methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12636603/#:~:text=Assignment%20of%20neurotransmitter%20predictions%20to%20neurons) aggregate presynaptic predictions per neuron and cell type. Individual predictions require at least 50 presynapses and confidence at least 0.5; type predictions require at least 100 pooled presynapses and confidence at least 0.5. Consensus normally follows the type prediction, with experimental overrides and stated aminergic exclusions. The published absence of a row for a cell with no released synaptic edges is consistent with this presynapse-derived data path. The exact upstream exporter omission is not independently proved here; the source absence itself is verified.

In [prepare_cns.py](../../runtime/prepare_cns.py), line 72 retains classified or traced neurons, line 76 left-joins the released transmitter table by exact body ID, and lines 78–80 leave missing/unknown consensus values at zero fast-current contribution with status `unresolved`. No present transmitter value is discarded for 43034. In [cns.py](../../runtime/cns.py), line 106 multiplies each retained structural edge by its source cell's stored sign. Because 43034 has no structural edges, changing only its sign would change no recurrent edge value and supply no functional pathway. No runtime trial is claimed from this structural argument.

The exact identity fields do not demonstrate a type mismatch, and the primary tables do not show an ACh-positive curation error. The relevant gap is the unconnected, preliminarily traced source entry. Source-marker support can remain attached to the MeTu1 class without manufacturing the absent individual pathway.

## Separate assessment

| Boundary | Result |
|---|---|
| Implementation/import | **Correct for this cell:** source ID and missing NT row preserved; no raw edge lost. |
| Numerical representation | **Consistent:** raw and prepared incoming/outgoing counts are all zero; stored fast sign is zero. No dynamical simulation was run. |
| Biological validation | **Bounded:** primary ChAT/EASI-FISH evidence supports MeTu1 class identity. Individual release kinetics and target-receptor effects are unmeasured here. |
| Demonstrated capability | **None added:** a source phenotype label cannot repair absent connectivity or demonstrate behavior. |

The next required external datum for this cell is a source reconstruction/synapse release containing its actual contacts, with a corresponding transmitter annotation. Until that exists, keep its structural and physiological gate open. M4 work on other, connected cells can continue independently. The machine-readable disposition and source/code hashes are in adjudication.json (original artifact `program/m4-m7/metu1/adjudication.json`).

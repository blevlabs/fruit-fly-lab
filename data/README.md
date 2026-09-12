# Data and reproducibility

The code repository includes compact curated maps and selected source inputs.
Large prepared graphs and the scientific archive are attached to the release so
existing work can be reused without rerunning preparation or experiments.

| Material | Location | Use |
|---|---|---|
| Motor curation | `runtime/neural-motor/malecns-motor-map.json` | Factual targets, sides, topology, source evidence and explicit gaps |
| Regenerated sensory map | `runtime/neural-motor/malecns-sensory-map.json` | Same runtime IDs/directions, without private metadata or restricted source tables |
| Optical source projection | `data/optical-map.json` | Ordered column vectors and receptor joins; CC BY-SA 4.0 |
| Original Huang model inputs | `data/research/` | Unmodified selected MATLAB/XLSX/FIG inputs, with source hashes and attribution |
| Prepared MaleCNS graph | Release assets → `runtime/malecns-v1/` | Reuse the recorded 167,216-neuron selection directly |
| Original MaleCNS files | Explicit download → `data/raw/malecns/` | Independent graph preparation and sensory-map rebuilding |
| Scientific archive | Release asset → `archive/` | Historical raw inputs, traces, reference code, result records and scientific-state exports |

`downloads.json` records exact URLs, destination paths, hashes and source terms.
`./fly fetch --list` performs no downloads. A selected fetch verifies existing
bytes and refuses to replace a changed file. The [archive guide](../archive/README.md)
and its machine-readable inventory describe inclusion and exclusions.

## Reuse and version boundaries

Use prepared data with the source version that declares it. The graph importer
retains classified/traced neuronal IDs and released contact counts; it excludes
glia/unclassified segments according to the recorded rule. It does not infer
missing physiological signs, organs or behavior.

The public sensory map is independently generated from pinned MaleCNS annotations
and the attributed optical projection. Type-grouping rules are authored in
`scripts/build_sensory_map.py`; selected taste IDs come from the permissively
licensed MaleCNS type fields. The restricted companion table and separate
historical FlyWire crosswalk are not embedded. Exact provenance and comparison
scope are in `sensory-map-provenance.json`.

Historical checkpoint exports preserve scientific arrays but may omit identifying
environment metadata. They are reference states, not a promise of direct restore
into this changed layout. Never weaken the ordinary checkpoint validator to
force compatibility. Matching model, source, data, schema and runtime identities
are still required for an operational restore.

## Legacy and reference inputs

The original FlyWire v783 baseline uses separately licensed input data. The CPU
example expects `Completeness_783.csv` and `Connectivity_783.parquet` in
`runtime/shiu-brain/`; the Eon baseline expects the `2025_`-prefixed counterparts
in `runtime/eon-brain/data/`. These are distinct from the MaleCNS graph.

```sh
./fly fetch --group flywire-cpu
./fly fetch --group flywire-eon
```

The release also retains the optional original FlyBody OBJ mesh bundle with its
Apache-2.0 attribution. It is a separate reference asset; the core CNS uses the
bundled simplified NeuroMechFly geometry and authored muscle paths.

The original source archive and [reference index](../docs/reference-index.json)
record the pinned study inputs. Restore the required reference material before
running an older script. Files that were never acquired, including the selected
81A07 raw trial, cannot be supplied by this repository; their exact source and
missing provenance remain documented.

Data licenses are separate from code licenses. See [THIRD_PARTY.md](../THIRD_PARTY.md)
and each source record. Noncommercial/no-derivatives material retains its terms
when included unchanged. Credentials, personal machine records and operational
archives are excluded.

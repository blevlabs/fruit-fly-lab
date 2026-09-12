# Publication validation

This release organizes and preserves the recorded research work. Packaging checks
do not establish a new physiological result or qualify a new full-body trajectory.

## Checked for this release

- A fresh locked base/research environment installed successfully; dependency
  compatibility checks passed.
- Python syntax, JSON/TOML records and local documentation links were checked.
- Protocol tests used fake processes to exercise local launch, strict identities,
  partial-response deadlines, input rejection and process cleanup.
- Data checks verified the 815-row motor inventory, source/asset hashes and the
  public sensory-map rebuild: 17,937 rows, exact type/side groups, 5,713 wired
  optical IDs and ordered directions.
- Checkpoint-codec tests verified non-executable data roundtrip and preservation
  of the previous file after an interrupted write.
- Original Huang data readers verified 86 means, 86 SEM values and 240 saved
  author curve points without executing the conditioning model.
- Archive-restoration fixtures checked completed-index requirements, source
  hashes, no-overwrite behavior, exclusions and symlink/path rejection.
- Prepared and original connectome files match their pinned source hashes.
- The scientific archive was inspected after decompression. Private operational
  fields were removed where a safe scientific export was possible; captured
  request/challenge records were excluded. Scientific numeric array members were
  checked unchanged. Generic upstream software-version metadata was preserved.
- The new release container uses relative file paths and anonymous filesystem
  ownership/time headers. Its extracted member hashes match the checked files.

`./fly check` runs the small simulation-free checks. Extended archive metadata
inspection uses `--include-archive` with the research extra, Poppler's
`pdftotext`, and FFmpeg's `ffprobe`. A local-only deny list may be supplied with
`--deny-file`; it must never be committed.

## Boundaries

No CNS, body, learning or population simulation was run during publication work.
The native UI was not relaunched. Historical results retain their original
preparation, uncertainty and limitations in the reports and selected summaries.

Source layout, protocol transport, file locators and public metadata changed.
Anatomical mappings used by the runtime, scientific constants and equations were
not tuned to improve behavior. New source/data identities mean old individual
files cannot be silently relabeled as compatible checkpoints.

The archive includes complete numerical arrays where recoverable, not private
operational environments or a guarantee that every old source checker runs with
every exported metadata record. Its index states exact-copy, metadata-sanitized
and reference-only status. Some original inputs were never acquired; some
source material is linked rather than redistributed.

Full biological calibration, natural repertoire, integrated learning and broader
reproduction gates remain open in [status](status.md) and the [roadmap](roadmap.md).

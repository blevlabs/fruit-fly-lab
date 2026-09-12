# Setup

Python 3.12 and `uv` are used. The lockfile pins dependency resolution and the
FlyGym source revision. No account, named machine, network service or secret is
preconfigured.

## Base environment and inspection

```sh
uv sync --frozen
./fly check
./fly help
```

These checks parse source/metadata, inspect documentation links and public
boundaries, and exercise data/codec/protocol fixtures. They do not advance a
neural or physical model. Research input readers need:

```sh
uv sync --frozen --extra research
```

## Prepared CNS data

Prepared data is attached to the repository's release so it need not be rebuilt.
It retains the recorded MaleCNS selection and exact graph hashes:

```sh
./fly fetch --group prepared
```

Alternatively, reproduce preparation from the original release inputs:

```sh
./fly fetch --group malecns
./fly prepare --raw data/raw/malecns --output runtime/malecns-v1
```

The original segment graph is large. Downloads are explicit and hash-verified;
an existing file with different bytes is not overwritten. The compact public
motor/sensory maps are already included. The sensory map can be independently
rebuilt after obtaining the pinned annotations:

```sh
uv run python scripts/build_sensory_map.py
uv run python tests/check_mappings.py --annotations data/raw/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather
```

## Run a finite embodied experiment

The local headless runtime requires Linux, an NVIDIA GPU and a driver compatible
with the locked CUDA PyTorch build. There is no silent CPU substitute for its
neural dynamics.

```sh
uv sync --frozen --extra cuda
./fly experiment examples/warm-source.json --output runs/warm-source-01
```

This command starts a **new simulation**. It writes the declared history, initial
and final state, frames and a receipt. The output directory must not already
exist. To continue a compatible saved individual, add:

```sh
--restore runs/previous-run/latest.npz
```

Source/data/runtime compatibility is checked strictly. Historical archive
checkpoints may require their matching historical implementation and environment;
they are not silently accepted by a changed release.

## Native viewer and separate demos

The Cocoa/MuJoCo viewer is macOS-specific:

```sh
uv sync --frozen --extra viewer
./fly viewer --cns --paused
```

A Mac cannot execute the CUDA brain locally. The optional `--backend-command`
must explicitly name a compatible worker supplied by the operator; no external
machine or connection is configured by this project. Protocol and source/body
identity checks still apply. A portable Linux interactive frontend remains open;
the Linux headless experiment interface is the supported full-CNS entry point.

`./fly walk` is a separate FlyGym hybrid-controller demonstration and supplies no
evidence of natural connectome-generated walking. `./fly brain`, `./fly mn9` and
`./fly gpu` preserve legacy FlyWire-based assays; their separately licensed v783
inputs must be installed as described in [data](../data/README.md).

## Research references

The [scientific archive](../archive/README.md) preserves reusable inputs, outputs
and analysis material. Restore it when working with an older reference study.
Each script's report states its exact preparation and input requirements. For
example, the selected original Huang inputs are included directly:

```sh
./fly huang --help
```

After extracting the archive, inspect and restore an explicit study's available
inputs without running its model:

```sh
./fly restore-data --list
./fly restore-data --study olftrans
```

The helper checks published hashes and refuses conflicting files. It reports
reference-only inputs that were not redistributed; copying available files is
not a claim that every source requirement or scientific gate is satisfied.

Commands that run model dynamics are explicit scientific work, not setup checks.
See [testing](testing.md) and the [reference index](references.md).

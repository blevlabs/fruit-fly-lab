# Fruit Fly Lab

A connectome-constrained fruit-fly research simulator: physical sensory inputs,
neural dynamics, identified motor events, muscle forces and body feedback.

**This is an incomplete research prototype.** The graph and supported physical
loop are implemented. Physiological calibration, normal adult behavior and an
integrated learning agent remain unfinished. Body motion and a successful
numerical run do not establish those capabilities.

## What has been done

| Area | Implemented or demonstrated |
|---|---|
| CNS graph | 167,216 retained MaleCNS v1 neurons; 25,587,572 directed neuronal connections |
| Physical output | 437/815 motor neurons connected; 253 muscle/tendon paths, 211 with neural input |
| Sensory input | 6,358/17,937 entries wired, including optical, proprioceptive, chemical and thermal inputs |
| Closed loop | Physical sources → sensory dynamics → CNS → motor spikes → NMJs/muscles → body/fluid state → sensory feedback |
| Persistence | Explicit scientific state, delays, random generators, atomic saves, strict restore and isolated trials |
| Numerical studies | Bounded timestep/stability work; six three-second histories and a separate pilot passed their stated numerical checks |
| Scientific references | Separate odor/spiking, water, electrical-response, muscle/probe and Huang/Luo learning-model work |
| Reproducibility | Pinned upstream code, licensed mapping data, source manifests, selected results and documented limitations |

## What has not been done

- Complete peripheral anatomy, muscle capacity and living motor-to-force calibration.
- Complete or independently validated sensory transduction and central physiology.
- Complete digestive, energetic, respiratory, salivary and other internal systems.
- Demonstrated natural standing/walking, flight, grooming, feeding or the full adult repertoire.
- Integrated associative learning, retained learned weights, reversal/transfer,
  self-modeling, structural growth, evolution or learned communication.
- Real-time full-body simulation or broad cross-platform native-viewer qualification.

The isolated Huang/Luo reference reproduces an original reduced learning model;
it is not connected to the embodied CNS. Current muscle capacities, many response
laws and geometry transfers remain estimates. No gait generator, target-angle
servo or behavior-fitted motor gain supplies the missing natural behavior.

Read [current status](docs/status.md), the [full roadmap](docs/roadmap.md), and
[selected results](results/README.md) before interpreting a demonstration.

## Start here

Use Python 3.12 and [uv](https://docs.astral.sh/uv/). From a clone:

```sh
uv sync --frozen
./fly check
./fly help
```

These commands install the base environment, check the repository and show its
commands. **They do not start a CNS or physical simulation.** CUDA experiments
require the additional environment and data steps in [setup](docs/setup.md).

The headless embodied runtime targets Linux with an NVIDIA CUDA GPU. Research
references and data/repository checks can run without CUDA. The Cocoa native
viewer is optional and macOS-specific; a Mac cannot run the CUDA brain locally.
There is no preconfigured machine, account, service or credential.

## Repository map

| Directory | Contents |
|---|---|
| `runtime/` | One flat, local runtime: neural worker, body/senses, checkpoint codec, protocol client and optional viewer |
| `research/` | Isolated scientific references and source-analysis scripts |
| `tests/` | Repository/protocol/data checks and explicit scientific checks |
| `data/` | Mapping provenance, selected licensed reference inputs and explicit download manifests |
| `results/` | Selected historical numerical/reference results and their evidence limits |
| `docs/` | Setup, architecture, testing, status, roadmap, references and 43 research reports |
| `examples/` | Explicit experiment histories and separate demonstration entry points |
| `licenses/` | Original third-party license notices |
| `runs/` | Ignored local outputs, created only when an experiment is requested |

Generated connectome files, caches, credentials and individual checkpoints are
not versioned. The publication has a fresh history; operational records and
personal environment configuration are not part of the public project.

## Methods, references and attribution

- [Architecture and data flow](docs/architecture.md)
- [Setup and data acquisition](docs/setup.md)
- [Testing and evidence levels](docs/testing.md)
- [Research report index](docs/research/README.md)
- [Research and external-code references](docs/references.md)
- [Comprehensive reference index](docs/reference-index.json)
- [Code and data licenses](THIRD_PARTY.md)

The bibliography covers the 79-entry simulator-review citation ledger, its 44
pinned repository revisions, all 30 catalogue entries, and additional mechanics,
sensory and physiology sources. Reviewed software is distinguished from code
actually used or adapted.

Original project code is GPL-3.0-or-later. Vendored code and research data retain
their own notices and applicable terms; the code license does not relicense a
dataset. Cite the original studies and implementations as well as this repository.
See [CITATION.cff](CITATION.cff) and [contribution guidance](CONTRIBUTING.md).

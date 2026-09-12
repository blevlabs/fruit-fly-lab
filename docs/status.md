# What works and what remains

Public source organization: September 12, 2026. The project is a research
prototype. No natural full-fly repertoire or integrated persistent-learning
capability has been demonstrated.

## Implemented

- MaleCNS v1 graph preparation: 167,216 retained classified/traced neurons,
  25,587,572 directed neuronal connections and 124,193,283 synapse contacts.
- Estimated neural dynamics, physical sensory observations, identified motor
  events, delayed neuromuscular transmission, muscle forces and body feedback.
- 437/815 motor neurons connected to 211 of 253 muscle/tendon paths; 42 paths
  remain passive prototypes. Named target/family annotations cover 481 rows;
  334 remain unidentified. A named target is not automatically a physical binding.
- 6,358/17,937 sensory entries wired: 5,713 optical, 291 proprioceptive, and
  354 chemical/thermal inputs. Many response laws are uncalibrated.
- Primed proboscis fluid mechanics, flight/haltere component mechanics, explicit
  current-state persistence and isolated physical-history execution.
- Separate published-model references for odor transduction, stochastic spike
  generation, water endpoints, passive electrical response and Huang/Luo plasticity.

## Retained evidence

Historical implementation checks cover deterministic replay, source/input
isolation, delayed events, conservation, reset, pause, atomic checkpoint recovery
and fresh-process continuation. A bounded timestep repair uses 2.5 microseconds
for body/NMJ/fluid updates and 100 microseconds for neural updates.

Six three-second histories plus a 0.1-second pilot completed their declared
finite-state, identity and fluid-conservation checks. They do not establish
global trajectory convergence, physiological accuracy, walking, feeding or flight.
See the [selected results](../results/README.md).

The last bounded performance comparison reduced 100 neural steps from 7.687 to
6.420 wall seconds. Native stream cadence was observed at 14 updates/second;
each update advanced only 100 microseconds. This is far slower than physical real
time. These historical timings are not fresh benchmarks of this reorganized tree.

## Open

Missing or unqualified areas include peripheral identities and capacity allocation;
motor-to-force calibration; tactile, wing/haltere, auditory, humidity and other
sensory dynamics; receptor-specific transmission, modulation and electrical
synapses; complete internal organs, storage, metabolism, salivation and dry filling;
normal resting wing/folding mechanics; and independent full-body behavior tests.

The live CNS has fixed connection weights. Sensory adaptation and NMJ depression
are dynamic state, not evidence of associative learning. The isolated Huang/Luo
model is not connected to the embodied CNS. Teaching, reversal, transfer,
self-modeling, uncertainty-guided behavior, growth, evolution and learned
communication remain research goals in the [roadmap](roadmap.md).

## Publication scope

The public tree reorganizes source and documents the accumulated work. Original
operational logs, machine settings, private Git history, personal checkpoints and
restricted source tables are excluded. Scientific source citations, original
licenses, selected results and explicit data-acquisition recipes are retained.

Checkpoint compatibility includes source/data/runtime identity. A checkpoint from
an earlier layout must not be silently relabeled or treated as compatible with
this release. Generate a fresh individual after completing the setup; future
compatible checkpoints can then be restored through the ordinary strict validator.

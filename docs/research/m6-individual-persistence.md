# M6 simulation persistence and isolated execution

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

The historical studies demonstrated complete-state continuation and recovery for the implemented model. This preserves a dynamical trajectory; it does not demonstrate plasticity or learned memory.

## Implemented state contract

`runtime/cns.py` exports all five neural/synaptic/delay tensors, graded optical drive, sensory inputs and caches, the neural clock and the per-instance CUDA generator. `runtime/cns_live.py` exports the same live `Session`: native `mjSTATE_INTEGRATION`, every delayed NMJ queue/excitation/efficacy, asynchronous activation/stretch history, fluid pressure/volume/compliance/boundary exchange, all sensory caches/adaptation, physical sources, current intervention, trial/reset/individual identity, readout counts and Python/NumPy/global CPU/CUDA RNG states.

MuJoCo's integration state includes warm-start and control inputs, rather than only position and velocity. Source settings also affect collision masks in the model; these are reconstructed before loading native state. Derived observables are refreshed, then saved integration state is reapplied so the extra forward solve does not change the next warm-start. [Native state contract](https://mujoco.readthedocs.io/en/stable/programming/simulation.html#state-and-control)

Loaded source identities, both maps, graph hashes, compiled model, configuration, dependency/Python versions and CUDA/GPU identity accompany the state. A later edit on disk cannot relabel an already loaded individual. Restore rejects missing fields, incompatible identities, inconsistent clocks/caches/source positions and invalid event queues before mutation; an unexpected apply error restores the previous scientific state.

`runtime/checkpoint.py` stores a typed JSON tree and finite NumPy arrays with `allow_pickle=False`, individual array hashes and exact shape/dtype checks. It writes a temporary file, flushes/fsyncs, atomically replaces the named slot and syncs the directory. Interrupted serialization or replacement leaves the last valid checkpoint intact. Malformed inventories, truncated files and invalid compressed data become input errors rather than terminating a valid worker.

Pause advances no neural/body time. A trial transition changes the physical environment while retaining the individual. Full reset creates a fresh individual with the specified seed. Exact restore reinstates the saved state. Wall-time profiling and renderer counters are excluded from scientific state; no cross-hardware bitwise guarantee is claimed from these tests on one execution configuration.

## Historical continuation results

| Assay | Recorded result and scope |
|---|---|
| Active-state checkpoint and continuation | Complete exported state matched across neural steps 400–625, including naturally emitted delayed events, active native/asynchronous muscle state, fluid exchange and thermal adaptation. No synthetic motor event was inserted to activate the fixture. |
| Independent instances and transitions | Separate instances remained independent. Pause and trial transition preserved scientific state; fresh reset cleared it; restore recovered it. |
| Interrupted/corrupt input | Interrupted serialization/replacement, malformed inventories, corrupt compression, truncation, invalid commands, incompatible state and failed restoration preserved the preceding valid state/checkpoint. |
| Prespecified headless history | Seed 31, 137 steps followed by 83 steps: uninterrupted execution matched checkpoint, process close and resumed execution, including random-number state and the declared release-block intervention. |
| Packet schedule and integration | Exact 25/100-step packet behavior, pause/reset, release blocking and wet/dry conservation passed. A 30-frame odor comparison was byte-identical. |
| Interactive/headless agreement | A state saved at 0.09 s, advanced to 0.14 s, then restored recovered the original time and intervention; resaving produced an identical checkpoint. |

The active-state checkpoint was 6,188,726 bytes. The complete regression took 54.71 wall seconds; a separate runner fixture took 35.71 seconds. These historical timings include construction and multiple checks and are not lifetime or population-throughput benchmarks.

An early fixture failed because it stopped before confirming asynchronous muscle activity. The corrected stopping condition observed the required state at 40 ms without altering a physiological parameter. This is an assay correction, not a fitted stimulus.

Original artifacts include `persistence-04/receipt.json`, `runner-01/receipt.json`, `integration-final/integration-check.json`, and `native/native-viewer-check.json` in the M6 historical archive.

## Scientific-state validation before saving

A later fault-injection study found that numerically finite state captured between a neural update and its physical substeps could overwrite a valid checkpoint. Numeric storage integrity alone was insufficient. The corrected save path validates scientific clocks, caches and pending events before writing. The invalid-save check and valid-state continuation regression subsequently passed.

This distinguishes storage correctness from dynamical-state consistency: a file can contain finite arrays and valid checksums while representing incompatible physical times. Both checks are required.

## Physical-step conversion

A separate historical study changed the physical step from 10 to 2.5 µs. It rescaled 447 NMJ clocks and the optical cache while preserving six pending physical event times and every random-number state. Paused observation and fresh-process continuation then matched exactly.

The first conversion omitted the visual-cache counter. A subsequent review exposed that omission, and the corrected conversion reconstructed the complete state directly from the original checkpoint. The former result must not be treated as complete time preservation. This is a clock-conversion test, not evidence of global trajectory accuracy or physiological calibration.

## Public implementation contract

An experiment history defines a nonnegative seed and a nonempty sequence of named phases. Each phase declares neural steps, physical sources and the release-block intervention. Trial transitions retain state; fresh resets initialize a new trajectory. A failed phase preserves the previous valid checkpoint. A checkpoint must contain all state that can influence later evolution, including future learned or structural state when implemented.

The checkpoint codec uses typed JSON and finite NumPy arrays with `allow_pickle=False`, per-array hashes and exact shape/dtype checks. Atomic replacement protects the last valid save. Interactive controls and transport counters must not alter scientific time or dynamics.

See the [runtime state implementation](../../runtime/cns_live.py), [checkpoint codec](../../runtime/checkpoint.py), [experiment runner](../../runtime/experiment.py), and [package checks](../../tests/). Package command validation and current guarantees are recorded in the status page; the historical results above were not rerun during documentation preparation.

Complete-state replay is separate from physiological validity, natural behavior, acquired associations, reversal, transfer, self-prediction, growth, evolution and communication. Those claims require their own evidence and controls.

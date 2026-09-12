# Contributing

Read [status](docs/status.md), [architecture](docs/architecture.md), and the
[research index](docs/research/README.md) before changing a mechanism.

Use an issue or pull request to name the claim, affected source/data versions,
and the smallest independent observation or runnable check that can falsify it.
Keep implementation correctness, numerical accuracy, biological validation and
demonstrated behavior separate. Preserve failed or inconclusive results.

Do not add anatomical edges, gait scripts, target angles, reward-driven motor
gains or convenient sensory labels to manufacture a biological result. Estimated
parameters must say they are estimates and retain units and provenance. Proposed
engineered extensions need their own stated scope.

Run `./fly check` for repository and protocol checks. It does not start a CNS or
physics simulation. Run only the additional checks relevant to your change;
GPU/physical experiments are explicit commands documented in `docs/testing.md`.
Write new runs beneath `runs/`, never over published reference data.

Keep credentials, personal machine settings, checkpoints and generated caches
out of commits. New external code/data must include its exact source, revision,
license and modification history. A paper's license does not automatically
license its separate code or dataset.

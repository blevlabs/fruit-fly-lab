# Parallel simulation study design

This report records a historical study and its inspected model version. Numerical results below are not new package checks; see [current status](../status.md), the [roadmap](../roadmap.md), and the [public results index](../../results/README.md). Original artifact labels identify records in the historical provenance archive.

Parallel execution increases aggregate simulated time; it does not accelerate the biological time experienced by one simulated organism. Each replicate needs independently initialized mutable neural, muscle, fluid, sensory and random-number state. Immutable graph data may be shared when the execution engine supports it.

Measure one worker before comparing two and four concurrent workers. That sequence is an experimental design, not a claim that four workers fit or run efficiently. Record cold load, neural integration, mechanics, synchronization, output and checkpoint costs separately, including peak memory and failed work.

A historical numerical campaign specified one 0.1-second preliminary run and six independently initialized 3.0-second histories using a 2.5-microsecond physical step. This design alone supplied no trajectory-convergence, statistical or biological result. CPU-only mechanical replay can test physical integration independently, but cannot substitute for a coupled neural experiment.

For every run, retain source/data/configuration hashes, dependency versions, seed, initial conditions, intervention history, actual simulation duration, resource measurements and outcome. Use distinct result identities. Parallel trials and repeated frames are not additional biological specimens; determine the replication unit and holdout split from the scientific claim.

The cost of an experiment is the measured cost per integrated duration multiplied by conditions, independent replicates and protocols, including calibration, controls, failures and retained outputs. No performance or cost promise follows from an execution configuration alone.

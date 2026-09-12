# Tests and evidence

`./fly check` runs only repository, protocol and data fixtures. It checks syntax,
JSON/TOML, documentation targets, publication boundaries, mapping identities,
checkpoint encoding and selected source-input files. The protocol tests use fake
processes. No CNS, body simulation, GPU job or source download is started.

The repository also retains explicit scientific checks in `tests/`. These are
not run automatically because several instantiate physics or a full CUDA CNS:

| Check | Scope |
|---|---|
| `check_cns.py` | Full neural/body loop, physical-source interventions and packet comparisons |
| `check_persistence.py` | Active individual state, fresh-process continuation and fault recovery |
| `check_cns_body.py` | Physical bindings, capacities and accounting |
| `check_cns_senses.py`, `check_cns_proprio.py` | Physical observation/routing and feedback hypotheses |
| `check_*_muscles.py`, `check_flight_mechanics.py`, `check_muscle.py` | Component mechanics and invariants |
| `check_visual_neurons.py` | Graded-neuron behavior; requires CUDA |
| `research/check_*.py` | Named source/physiological reference, with its own required inputs |

Run a named check explicitly using the repository's runtime path, for example:

```sh
PYTHONPATH=runtime uv run python tests/check_persistence.py --output runs/persistence-01
```

That example is a **simulation**, requires CUDA and prepared data, and is not part
of the simulation-free publication check. Preserve earlier outputs; do not alter
acceptance margins or suppress warnings to turn a failure into a pass.

## Evidence levels

1. **Implementation:** exact IDs, state, causality, units, isolation, conservation,
   failure handling and reset/restore behavior.
2. **Numerical:** the relevant conclusions converge under an appropriate step or
   geometric refinement within an independently justified error budget.
3. **Biological:** predictions match independent observations for the stated
   preparation, with frozen holdouts, uncertainty and causal controls.
4. **Capability:** the claimed behavior or learned benefit appears on held-out
   tasks and survives the appropriate alternative explanations and interventions.

Passing one level does not close another. A model seed is not an independent
biological specimen. Source reproduction is distinct from a held-out prediction.
Read [status](status.md) and [selected results](../results/README.md) for actual
completed scopes. The public-layout checks do not requalify the historical
full-body trajectories or establish new biological behavior.

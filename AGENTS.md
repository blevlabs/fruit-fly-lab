# Working in this repository

- Read `docs/status.md` before making a current capability claim. Research reports
  document specific historical studies; proposed corrections may already be resolved.
- Keep the neural, muscle, sensory and physical equations unchanged during packaging
  or documentation work. Never invent anatomy or fit motor gains to make behavior appear.
- `./fly check` is simulation-free. CNS, physics, calibration and population runs must
  be explicit tasks, with isolated output directories and appropriate data identities.
- Reuse `Session`, `experiment.py` and the checkpoint codec. Do not create a second runtime.
- Preserve raw evidence and failed studies. Separate implementation, numerical,
  biological and capability results. Keep source/data attribution with reused material.
- Do not commit credentials, private addresses, machine configuration, caches or
  personal checkpoints. Use `scripts/check_repository.py` before publication.
- Use a small relevant check for each behavioral change; avoid broad repeat runs
  that cannot answer a new question. New generated outputs belong under `runs/`.

# Training Branch Share Readiness

## Branch

`training/g13-geometry-force`

## Validated

- G13 training pipeline on the packaged original vessel
- checkpoint save and collaborator-facing load
- resume with optimizer and replay state
- nominal checkpoint evaluation
- test suite (`20 passed, 1 skipped`)
- runtime and development dependency resolution
- generic SOFA environment instructions

## Known Limitations

- Collaborators must provide their own compatible SOFA, SofaPython3, and BeamAdapter installation.
- Every phantom geometry must pass `scripts/check_new_vessel.py` before training.
- The approximately 5k-step demo is a functional check, not a scientific performance result.
- Mid-episode SOFA state is not bitwise restorable during resume.

## Recommended Collaborator Workflow

```text
clone -> checkout training branch -> install -> environment check
-> vessel sanity check -> short training -> full training -> evaluation
```

Use [TRAINING_README.md](../TRAINING_README.md) for exact commands and scene requirements.

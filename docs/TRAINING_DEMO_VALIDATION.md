# G13 Training Demo Validation

Date: 2026-10-24
Branch: `training/g13-geometry-force`
Commit: `15c05f0459e3accec7a9c47747364fd2c6dcc470`
Worktree at start: clean.

## Environment

Validated with the project Python 3.10 environment, PyTorch `2.7.1+cu128`, CUDA `12.8`, SOFA, BeamAdapter, and the bundled repository `eve`. CUDA was visible. The original vessel sanity check passed: 22-D finite observations, 2-D actions, finite geometry features, force extraction, and one action step.

## Demo training

Canonical config: `configs/train_g13.yaml`; original scene: `configs/scenes/original_training_vessel.yaml`. A temporary untracked config changed only runtime settings: `total_steps=5200` and `checkpoint.interval=5000`.

```bash
python scripts/train_g13.py \
  --config <temporary-demo-config.yaml> \
  --scene-config configs/scenes/original_training_vessel.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_demo_release_check_2
```

Result: 5,200 environment steps, replay size 5,200, 5,200 optimizer updates, no simulator failure. At step 5,200: total loss `0.0586459`, force loss `0.0112858`, and all reported TD/world-model losses were finite. Checkpoints `step_5000.pt` and `step_5200.pt` plus SHA256 sidecars were created.

## Checkpoint and evaluation

`step_5200.pt` loaded through the collaborator-facing path, is format v2, records observation dimension 22, contains force-head weights, and requires no old-research-repository import. Functional nominal evaluation on seeds 1000--1004 produced 2/5 successes, mean length 132.8, peak-force mean/max 8.7089/15.3734 N, above-`F_lim` fraction 0.22139, and zero simulator errors. This short-run result is not a performance estimate.

## Resume

Resuming trusted `step_5000.pt` with the identical temporary config completed the remaining 200 steps, restored replay and optimizer state, retained finite losses, and saved a new `step_5200.pt` under `runs/g13_demo_release_check_2_resume/checkpoints/`. Known limitation: mid-episode live SOFA state is not restored bitwise.

## Tests

`pytest -q`: **20 passed, 1 skipped**. The original validation initially exposed an OpenCV/NumPy resolver conflict; requirements now pin the compatible OpenCV 4.8.1.78 release while preserving frozen NumPy 1.24.4.

## Conclusion

**PASS WITH WARNINGS.** The packaged G13 workflow passes environment/scene validation, train -> checkpoint -> load -> evaluate, and resume validation. Warnings: expected SOFA compatibility warnings, the demo is not a performance study, and the dev-requirements resolver conflict should be documented/resolved separately without changing frozen G13 numerical behavior.

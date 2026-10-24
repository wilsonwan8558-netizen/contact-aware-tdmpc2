# G13 Geometry-Force-TD-MPC2 Training

## Overview

This local training branch ports the research G13 pipeline for retraining on a declared vessel. It trains the **same** 22-D-observation, 2-D-action Geometry-Force-TD-MPC2 model family and its integrated `agent.model.force_head`. The force head is jointly trained on each next completed RL interval's maximum distal contact force over 22 SOFA substeps. It is not a standalone predictor, and the task planner does not rank candidates by force. Nothing here changes the frozen G16.1 filter.

The distributed example checkpoint `step_260000.pt` was selected from an original 300k-step run on one procedural vessel. It is intentionally not in Git. Retraining on a new phantom yields **new** weights and requires independent validation; it does not inherit the published evaluation results.

## Original Training Configuration

`configs/train_g13.yaml` reproduces the research numerical configuration: 300,000 steps; seed 1; 5,000 random seed steps and initial updates; one later update per step; batch 256; replay capacity 1,000,000; H=3; Adam LR 3e-4 (encoder factor 0.3); force Smooth L1 β=1 weighted by 0.5; rho=0.5; discount clipped to [0.95, 0.995]; 512 MPPI samples, 64 elites, six iterations; checkpoint every 20,000 steps. The complete values are in YAML and [the source audit](G13_TRAINING_SOURCE_AUDIT.md). Do not use a smoke checkpoint as a scientific model.

The original run did **not** perform inline evaluation. It saved checkpoint candidates and subsequently selected 260k from steps 240k/260k/280k/300k on 30 development seeds, by navigation successes, then mean reward, then fewest simulation errors, then latest step. The optional `--evaluate-at-checkpoints` flag launches a separate nominal process after each checkpoint on the config's evaluation seeds; leave it off for closest original-loop behavior. The recovered YAML's `evaluation.seed=1000` was unused by the original training loop and is **not certified as independent of training episode seeds**; optional inline results are diagnostics, not a holdout. For research-grade selection, audit and predeclare a development cohort and run `evaluate_g13_checkpoint.py` on each candidate after training.

## Environment Requirements

Use Python 3.10, the dependencies in `requirements.txt` and a CUDA-matched PyTorch 2.7.1 build, SOFA with SofaPython3 and BeamAdapter, and the vendored `eve` package. On the original machine, the validated runtime was `steve_tdmpc`, PyTorch 2.7.1+cu128 on CUDA device 0. The scripts reject requested CUDA when unavailable; `--device cpu` is explicit and intended only for structural checks. Run `python scripts/check_environment.py` first. Do not add the research checkout to `PYTHONPATH`.

## Vessel/Scene Requirements

For the known setup, `configs/scenes/original_training_vessel.yaml` uses the already-vendored procedural aortic arch; no external vessel asset is copied. For a phantom, copy `configs/scenes/phantom_template.yaml` and supply a surface mesh, named radiused centerlines, insertion geometry, explicit registration, projection and target. See [RETRAIN_ON_NEW_VESSEL.md](RETRAIN_ON_NEW_VESSEL.md) for the exact 22-D features and coordinate requirements. Mesh paths are relative to the scene YAML. The loader does not infer units, silently rescale, or repair registration.

## Sanity Check a New Vessel

From the repository root, after editing the scene YAML:

```bash
python scripts/check_new_vessel.py --scene-config /path/to/phantom_scene.yaml
```

The check does not train. It resets one SOFA scene, verifies target and finite observation/geometry features, takes one zero action, and checks the 22-substep force monitor. Also inspect mesh and centerlines visually; a one-step check cannot prove target reachability or anatomy fidelity. The original-vessel preflight is:

```bash
python scripts/check_new_vessel.py --scene-config configs/scenes/original_training_vessel.yaml
```

## Start Training

```bash
python scripts/train_g13.py \
  --config configs/train_g13.yaml \
  --scene-config /path/to/phantom_scene.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_phantom
```

The output directory must be empty for a new run. It receives `training_config.json`, JSONL/CSV metrics, full-state checkpoints and SHA256 sidecars. A short diagnostic (not a scientific training run) is:

```bash
python scripts/train_g13.py --config configs/train_g13.yaml \
  --scene-config configs/scenes/original_training_vessel.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_smoke \
  --smoke-steps 50
```

Smoke mode alone changes the step budget, seed steps, initial updates and batch size, and records those changes in its own output config. It must use a fresh output directory.

## Resume Training

```bash
python scripts/train_g13.py --config configs/train_g13.yaml \
  --scene-config /path/to/phantom_scene.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_phantom \
  --resume runs/g13_phantom/checkpoints/step_20000.pt
```

Resume restores agent, optimizers, replay and RNG from a trusted local full-state checkpoint and requires an identical config/scene. **SOFA's live physical state is not serialized.** If a periodic checkpoint landed mid-episode, resume begins that episode again from reset, so the continuation is not bitwise equivalent to uninterrupted training. Preserve original artifacts; do not treat an interrupted/resumed run as exact replication without validation.

## Checkpoint Format

Checkpoints preserve the research format-v2 payload: algorithm, full config, agent/optimizers, step and episode counts, RNG, replay, 22-D metadata, force target, force-head attachment and loss weight. The local trainer additionally writes `step_N.pt.sha256`; the shared `load_g13()` verifies this sidecar for newly trained files. It still requires the fixed known SHA256 for the approved original 260k checkpoint. Full-state PyTorch checkpoints contain pickle and must be loaded **only from a trusted local source**; a checksum sidecar detects accidental modification, not malicious substitution.

## Evaluate a Checkpoint

```bash
python scripts/evaluate_g13_checkpoint.py \
  --checkpoint runs/g13_phantom/checkpoints/step_20000.pt \
  --scene-config /path/to/phantom_scene.yaml \
  --seeds 350000:350009 --device cuda:0 \
  --output runs/g13_phantom/evaluation_step_20000.json
```

The script uses one reused scene across ordered seeds and reports nominal success, episode length/reward, peak force, fraction of steps above the **nominal simulation reference** `F_lim=3.685331040756903 N`, failures/truncations and simulation errors. It does **not** apply G16.1. The reference force is not a clinical injury threshold. Predeclare evaluation and confirmation seeds before comparing checkpoints.

## Retraining on a Phantom Vessel

Prepare/validate the mesh, radiused centerline and scene YAML first; run the sanity check; run a short smoke on that scene; then run a clean full training with a new output directory. Evaluate checkpoints on a separate development cohort and preserve a later untouched confirmation cohort. A new vessel may require substantially more data or a different task formulation, but those would be new experiments—not the exact G13 port.

## Common Failure Modes

- Wrong `eve` import origin: remove older editable stEVE installations from the active environment; the entrypoints fail fast.
- Missing SOFA/BeamAdapter or wrong Generic solver: fix the environment before training, not the frozen numerical method.
- Missing/incorrect mesh, centerline names, radii or insertion frame: fix assets/registration; do not silently change scales.
- Nonfinite geometry, 2-D/3-D tracking misalignment or missing force samples: stop and inspect the scene.
- SHA sidecar or checkpoint mismatch: use an intact, trusted local file; do not bypass verification.
- Out-of-memory with full replay/checkpoints: capacity and batch are part of the original protocol; a reduced configuration is a *new* experiment and must be labeled as such.

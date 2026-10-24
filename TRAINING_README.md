# G13 Training and Retraining Guide

## 1. What This Branch Contains

This branch adds the G13 Geometry-Force-TD-MPC2 training pipeline for retraining on a new vessel or phantom geometry. It uses the same 22-D observation and model family as the shared 260k checkpoint. The frozen G16.1 fuzzy filter is optional at deployment and does not require retraining.

## 2. Branch

Use `training/g13-geometry-force`.

## 3. Environment Setup

From a clean clone, check out `training/g13-geometry-force`, create or activate
your Python 3.10 environment, install the repository requirements, then set up
your own SOFA runtime:

```bash
conda env create -f environment.yml
conda activate contact_aware_tdmpc2
python -m pip install torch==2.7.1+cu128 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-dev.txt
python -m pip install -e .
export SOFA_ROOT=/path/to/SOFA/install
export SOFAPYTHON3_ROOT=$SOFA_ROOT/plugins/SofaPython3
export PYTHONPATH="$PWD:$SOFAPYTHON3_ROOT/lib/python3/site-packages"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$SOFA_ROOT/lib:$SOFAPYTHON3_ROOT/lib:$LD_LIBRARY_PATH"
python scripts/check_environment.py
```

Replace `/path/to/SOFA/install` with your own SOFA installation. Then run:

```bash
python scripts/check_new_vessel.py \
  --scene-config configs/scenes/original_training_vessel.yaml
```

Training requires PyTorch 2.7.1+cu128 with CUDA 12.8 and a visible CUDA device. Install the project dependencies as documented for your environment; do not replace the frozen numerical package versions without validating G13 again.

## 4. Before Training on a New Vessel

Prepare a vessel mesh/scene, centerline, local-radius information, a target definition, and the registration/coordinate transform. Validate every new scene first:

```bash
conda run -n steve_tdmpc python scripts/check_new_vessel.py \
  --scene-config /path/to/phantom_scene.yaml
```

## 5. Scene Configuration

`configs/scenes/original_training_vessel.yaml` is the known-good example. For `phantom_scene.yaml`, supply the phantom assets, centerline/radius data, target, and registration explicitly. Do not assume its scale or orientation matches the original vessel.

## 6. Run the Original-Vessel Demo Training

Short functional demo, not full training (this exact release check used a temporary config containing only `total_steps: 5200` and `checkpoint.interval: 5000`):

```bash
cp configs/train_g13.yaml train_g13_demo.yaml
sed -i 's/^  total_steps: 300000$/  total_steps: 5200/' train_g13_demo.yaml
sed -i 's/^  interval: 20000$/  interval: 5000/' train_g13_demo.yaml
python scripts/train_g13.py \
  --config train_g13_demo.yaml \
  --scene-config configs/scenes/original_training_vessel.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_demo_release_check
```

## 7. Full Training

```bash
python scripts/train_g13.py \
  --config configs/train_g13.yaml \
  --scene-config /path/to/phantom_scene.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_phantom
```

The canonical original training config specifies 300,000 steps.

## 8. Resume Training

```bash
python scripts/train_g13.py \
  --config /path/to/the_same_training_config.yaml \
  --scene-config /path/to/phantom_scene.yaml \
  --device cuda:0 --seed 1 --output-dir runs/g13_phantom_resume \
  --resume runs/g13_phantom/checkpoints/step_XXXXX.pt
```

The config and scene must exactly match the checkpoint. Optimizer and replay state are restored. Live SOFA state is not restored bitwise when resuming mid-episode; this is an accepted limitation.

## 9. Evaluate a Checkpoint

```bash
python scripts/evaluate_g13_checkpoint.py \
  --checkpoint runs/g13_phantom/checkpoints/step_XXXXX.pt \
  --scene-config /path/to/phantom_scene.yaml --seeds 1000:1004 \
  --device cuda:0 --output runs/g13_phantom/evaluation.json
```

Default evaluation is nominal G13. The fuzzy safety filter is optional and separate when supported.

## 10. Checkpoint Files

Training checkpoints live under `output-dir/checkpoints/` with SHA256 sidecars. The shared original final model is `step_260000.pt`, SHA256 `b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be`. New phantom checkpoints must not be expected to share this hash.

## 11. Important Geometry Notes

The 260k checkpoint was trained on one vessel geometry; substantial changes can require retraining. `d0/d1/d2` are signed centerline-radius lumen proxies, not exact collision-mesh wall distances. Check geometry normalization and coordinate registration before collecting training data.

## 12. Recommended Phantom Workflow

```text
prepare phantom vessel assets -> create phantom scene config -> check_new_vessel.py
-> verify 22-D observations -> short training demo -> full G13 training
-> evaluate nominal checkpoint -> optionally apply frozen G16.1 fuzzy safety filter
-> shadow-mode physical deployment -> physical experiments
```

## 13. Troubleshooting

- Wrong `eve` imported: run `scripts/check_environment.py`; it must report the bundled repository path.
- Missing `SOFA_ROOT` or BeamAdapter: export the variables above and re-run the check.
- CUDA unavailable: do not silently train on CPU; fix the CUDA/PyTorch environment.
- Checkpoint hash mismatch: use the matching `.sha256` sidecar and trusted local checkpoint.
- Wrong observation size or NaN geometry: stop and validate the scene with `check_new_vessel.py`.
- Missing centerline/radius, scene registration mismatch, target outside vessel, or raw force unavailable: correct the scene assets/config before training.

## 14. Files Collaborators Should Read

- `docs/TRAINING.md`
- `docs/RETRAIN_ON_NEW_VESSEL.md`
- `docs/OBSERVATION_ACTION.md`
- `docs/PHYSICAL_DEPLOYMENT.md`
- `docs/G13_TRAINING_COMPATIBILITY.md`

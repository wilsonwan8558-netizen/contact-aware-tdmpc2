# G13 training source audit

Audit scope: research worktree `stEVE_safety_head_1e1be81`, selected run `geometry_force_tdmpc2_g13_300k_20261014`, selected `step_260000.pt`. The SHA256 of that checkpoint is `b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be`. It is not copied into this repository. The checkpoint payload confirms format 2, `Geometry-Force-TD-MPC2`, step 260000, observation 22, action 2, integrated `force_head`, force coefficient 0.5, full replay/RNG/optimizer state, and a config equal to the research `g13_config.yaml` (SHA256 `806b339f71254aa0cc5fc994c6e59054e449388f043e160eb24760bf382af48a`). No numerical hyperparameter was guessed.

## Exact producing path

1. `RL_TDMPC/experiments/world_model_g13/g13_train.py` (`fb85605e…`) is the primary 300k entrypoint. It loads the frozen G13 YAML, seeds Python/NumPy/Torch, builds one reused G13 SOFA environment, creates agent/replay, performs random seed collection followed by TD-MPC2 planning and updates, logs, and saves format-v2 checkpoints every 20k steps.
2. `RL_TDMPC/experiments/world_model_g13/g13_env.py` (`0ce85a15…`) wraps `RL_TDMPC/envs/steve_env.py` (`ee340640…`) with current-state geometry from `RL_TDMPC/envs/geometry_features.py` (`b0082e44…`) and the G2 passive distal-force monitor (`RL_TDMPC/experiments/generic_solver_g2/substep_monitor.py`, `74475989…`). The original vessel is procedural `AorticArch(seed=30, scaling_xyzd=[1,1,1,0.75])`; targets are sampled from `[lcca,rcca,lsa,rsa,bct,co]`, with threshold 5 mm. No vessel asset file is required for this mode.
3. `RL_TDMPC/experiments/world_model_g13/g13_model.py` (`d2584083…`) defines the integrated nonnegative `force_head`, aligned force replay and joint training loss. `RL_TDMPC/tdmpc2/agent.py` (`b7ead501…`) and `networks.py` (`4c03b5f4…`) supply unchanged planner/TD-MPC2 mechanics; `replay_buffer.py` (`460e70ef…`) supplies episode-aware sampling. `RL_TDMPC/train.py` (`fa51042e…`) supplied `build_agent_config` and the loss accumulator; `RL_TDMPC/tdmpc2/common.py` (`95163d00…`) supplied seed/RNG/checkpoint/log helpers.
4. Checkpoint selection was **after** training, not inline: `RL_TDMPC/experiments/world_model_g13/g13_select_checkpoint.py` (`dee0e153…`) compared 240k/260k/280k/300k on ordered development seeds 350000–350029, one reused SOFA scene per checkpoint, task-only success then reward then fewest simulation errors then latest step. The frozen selection artifact identifies 260k with 30/30 successes and mean reward 3.7092. Force-planning outcomes did not select the checkpoint.

## Force supervision

For each executed normalized 2-D action at time `t`, the target is `F_(t+1)`: the **maximum** reconstructed 3-mm distal contact force over that completed RL interval's 22 Generic-SOFA substeps, nominal N. It is appended to the same completed episode as the action and successor 22-D observation. Replay samples aligned H=3 subsequences without crossing episodes. The head predicts from `WorldModel.next(z_t,a_t)`, not from privileged future observation. Its loss is per-step `smooth_l1_loss(prediction, force, beta=1.0)`, averaged over batch/output, rho-weighted over H and divided by H, then multiplied by `lambda_force_train=0.5` and added to the original consistency/reward/value/termination loss. All six model parameter groups, including `force_head`, are updated jointly with Adam; the separate actor optimizer remains Adam with `eps=1e-5`. No standalone force predictor is substituted.

## Recovered configuration and run semantics

All original values are in `configs/train_g13.yaml`: 300000 environment steps; seed 1; 5000 random seed steps and 5000 initial updates; one later update per step; replay capacity 1000000; batch 256; train/planner H=3; LR 0.0003; encoder LR multiplier 0.3; loss coefficients consistency 20, reward 0.1, value 0.1, termination 1, force 0.5; rho 0.5; gradient clipping 20; tau 0.01; discount denominator 5, bounds 0.95–0.995; actor entropy 0.0001; episodic termination; model latent/encoder/MLP width 256, SimNorm 8, five Q heads, dropout 0.01, 101 distribution bins and value bounds −10/+10; planner 512 samples, 64 elites, 24 policy trajectories, six iterations, std 0.05–2, temperature 0.5; checkpoint interval 20000 and update-log interval 100. Original device was `CUDA_VISIBLE_DEVICES=0`, `cuda:0`, NVIDIA RTX 5090, PyTorch 2.7.1+cu128. Environment uses image frequency 7.5 Hz, 200-step cap, friction 0.001, Generic SOFA dt 0.006 s and 22 substeps. Original YAML `evaluation.seed=1000`, `episodes=10` was not called by the training loop; checkpoint selection used the separate 30-seed development manifest.

Episode seed is `training.seed + episode_index`; action space is seeded likewise before each reset. The original saved checkpoints may land mid-episode; they contain replay/RNG but not live SOFA state. The new `--resume` therefore cannot promise bitwise continuation after a mid-episode checkpoint.

## Source-to-destination inventory

| Research source (relative) | Share destination | Purpose/status |
|---|---|---|
| `RL_TDMPC/experiments/world_model_g13/g13_config.yaml` | `configs/train_g13.yaml` | Numerical values copied; path comments/output handling minimally adapted. |
| `RL_TDMPC/experiments/world_model_g13/g13_train.py` | `contact_aware_tdmpc2/training/trainer.py`, `scripts/train_g13.py` | Same action/replay/update sequence; CLI, output path, resume, smoke and optional isolated evaluation minimally adapted. |
| `RL_TDMPC/experiments/world_model_g13/g13_model.py` | Existing `tdmpc2/geometry_force.py`; new `training/agent.py`, `training/losses.py`, `training/replay_buffer.py` | Existing identical model/optimizer construction reused; joint loss/update and force replay ported with package imports. |
| `RL_TDMPC/tdmpc2/replay_buffer.py` | `training/replay_buffer.py` | Episode storage/sampling semantics ported; aligned force extension added. |
| `RL_TDMPC/tdmpc2/agent.py`, `networks.py` | Existing `tdmpc2/agent.py`, `world_model.py` | Already shared; agent differs only by package import, world-model source byte-identical. No planner edit. |
| `RL_TDMPC/experiments/world_model_g13/g13_env.py` | Existing `env/g13_env.py` | Already shared with runtime origin/config checks; observation/force wrapper unchanged. |
| `RL_TDMPC/envs/geometry_features.py` | Existing `env/observation.py` | Already shared, with only 22-name tuple added; feature math unchanged. |
| `RL_TDMPC/envs/steve_env.py` | Existing `env/steve_env.py`, adapted for optional `training/scene.py` | Original default scene remains unchanged; explicit mesh/centerline/registration path added for retraining. |
| `RL_TDMPC/experiments/generic_solver_g2/substep_monitor.py` | Existing `env/force_extraction.py` | Already shared, import adapted; force measurement unchanged. |
| `RL_TDMPC/tdmpc2/common.py`, `RL_TDMPC/train.py` | `training/checkpointing.py`, `training/config.py`, `training/trainer.py` | RNG, format-v2 payload, logger, config merge and loss accumulator ported; local output and SHA sidecar added. |
| `RL_TDMPC/experiments/world_model_g13/g13_select_checkpoint.py` | `scripts/evaluate_g13_checkpoint.py` plus this audit | Nominal evaluation mechanics ported; original 30-seed selection rule documented, not silently invoked in training. |

New `training/scene.py`, `scripts/check_new_vessel.py`, and the scene YAMLs configure/validate external vessel geometry; they have no direct original equivalent and do not change the frozen original-vessel path. The source research repository was read-only throughout. Existing TD-MPC2/stEVE attribution and upstream license files are preserved. No new third-party training source with unknown license was introduced; this document makes no redistribution claim.

## Audited research source SHA256

Paths below are relative to the research repository. These hashes identify the audited source, including components already present in the share repository.

| Research source | SHA256 |
|---|---|
| `RL_TDMPC/experiments/world_model_g13/g13_config.yaml` | `806b339f71254aa0cc5fc994c6e59054e449388f043e160eb24760bf382af48a` |
| `RL_TDMPC/experiments/world_model_g13/g13_train.py` | `fb85605ea1425b10ed2e34c0923be89f0f307b0ba8b7b906e06f343d536b8370` |
| `RL_TDMPC/experiments/world_model_g13/g13_model.py` | `d2584083c84d40d7b39737d8f3ed415ca4d44fed5d55ba5f70e0c3a92cc3b3b5` |
| `RL_TDMPC/experiments/world_model_g13/g13_env.py` | `0ce85a157ee985d3b72cb4b3bd90e3ce27006514cd06f10e5ad45ec12ea6ccee` |
| `RL_TDMPC/experiments/world_model_g13/g13_select_checkpoint.py` | `dee0e1530497cbf6bf3ee1e1cc11239a51a38f18e7a337ba6ee49d3835386abc` |
| `RL_TDMPC/tdmpc2/replay_buffer.py` | `460e70efb68de8d917928587fd732d3101df4f98b408e498ec29904e009921b8` |
| `RL_TDMPC/tdmpc2/agent.py` | `b7ead501ad7607f2ce1b1a3a46c23d2f3e16827302a3d9f8c8862900e6b27ef5` |
| `RL_TDMPC/tdmpc2/networks.py` | `4c03b5f414f015bdc406885d98f220842d9a80e6933a2dafaebdf5b81cdefb19` |
| `RL_TDMPC/tdmpc2/common.py` | `95163d00ea79f9c544ac6c8c6d59b9bb6c7a9d5be6581b9ff0a704327d0d7153` |
| `RL_TDMPC/train.py` | `fa51042ebb772dabd09d9f2157dd965f5170c71ead1d0b837c63135167a415f4` |
| `RL_TDMPC/envs/steve_env.py` | `ee340640bcc546b17a5effd6caf01f0d80a435c1f1e984a8a211d98395b24cfe` |
| `RL_TDMPC/envs/geometry_features.py` | `b0082e44da810287d412b3935b60eebb9ea58cae398e98d00e97e1f4e5452b46` |
| `RL_TDMPC/experiments/generic_solver_g2/substep_monitor.py` | `744759896f36d284c9ba039a537a9f5334a5e6f5d99752f036062ae55ced3534` |

**Core-training audit status: recovered.** Bitwise reproduction of a 300k stochastic CUDA run is not claimed; only a short structural smoke is required here.

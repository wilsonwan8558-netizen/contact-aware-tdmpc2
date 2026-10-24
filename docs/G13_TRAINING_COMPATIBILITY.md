# G13 research-to-share training compatibility

Scope: local `training/g13-geometry-force` branch; source run `geometry_force_tdmpc2_g13_300k_20261014`; selected checkpoint SHA256 `b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be`. See [source audit](G13_TRAINING_SOURCE_AUDIT.md). “EXACT” means source-equivalent numerical definition for the original-vessel mode, not a claim that a fresh stochastic 300k CUDA run will yield identical checkpoint bytes.

| Item | Classification | Evidence / adaptation |
|---|---|---|
| Architecture | EXACT | Shared `GeometryForceWorldModel` uses the same 256-D encoder/dynamics, reward/Q/termination/policy networks and integrated Softplus `force_head`; old checkpoint loads. |
| Observation | EXACT | Same 14 original values plus eight geometry values in the frozen 22-index order; shared feature math differs from research only by descriptive names tuple. |
| Action | EXACT | Same normalized 2-D insertion/rotation and symmetric JShaped ±50 mm/s, ±3.14 rad/s mapping. |
| Planner | EXACT | Existing shared TD-MPC2 agent differs from research only in package import; H=3, 512 samples, six iterations, 64 elites, 24 policy trajectories. No force ranking. |
| Replay | EXACT | Completed-episode, uniform valid H=3 sequence sampling with aligned next-interval force labels and identical capacity/seed semantics. |
| Loss | EXACT | Consistency/reward/value/termination plus rho-weighted Huber force loss (`beta=1`, coefficient 0.5), original actor/Q target/grad-clip/soft-target updates. |
| Force-head supervision | EXACT | Completed RL-step maximum of 22 true SOFA substeps; predicted from imagined next latent. No future observation as model input. |
| Optimizer | EXACT | Adam model groups including force head, encoder LR scaled 0.3, actor Adam eps 1e-5, original LR and update schedule. |
| Checkpoint structure | MINIMALLY ADAPTED | Same format-v2 research payload keys; local `.pt.sha256` sidecar and non-overwrite policy added. Shared `load_g13()` still pins the original SHA, and verifies sidecar+metadata for newly trained files. |
| Environment | EXACT (original) / MINIMALLY ADAPTED (new vessel) | Original procedural vessel, Generic-SOFA settings, task/reward/termination, geometry and force wrapper unchanged. Optional explicit mesh/centerline scene builder only activates when supplied. |
| Scene | EXACT (original) / MINIMALLY ADAPTED (new vessel) | Original-vessel YAML must match frozen seed/branches/threshold/projection; phantom scene needs user-provided mesh, radiused centerline, insertion, registration, projection and target. No asset copied. |
| Seed handling | EXACT for fresh run; MINIMALLY ADAPTED for resume | `training.seed + episode_index`, action-space seed per episode, Python/NumPy/Torch initial seed, replay RNG. Resume restores saved RNG/replay but cannot serialize live SOFA state; a mid-episode checkpoint restarts that episode physically. |
| Evaluation | MINIMALLY ADAPTED | Nominal evaluator preserves one reused scene and ordered per-seed resets. Original 30-seed task-only checkpoint selector is documented; generic evaluator accepts declared seeds. Optional separate-process checkpoint evaluation is off by default to avoid perturbing original training loop. |
| Paths/logging/CLI | MINIMALLY ADAPTED | Research absolute/project-root assumptions replaced with explicit config, scene and output-directory inputs; local logs are kept out of Git. |

No core-training item is classified UNRESOLVED. The actual external phantom asset quality, geometry registration, navigation reachability and generalization are **not** established by this port and must be checked for each new vessel. The original run used one procedural vessel; different mesh/radius/target distributions necessarily change the training data and weights. No full 300k run was started.

Validation on this branch: recovered YAML equals the selected checkpoint’s embedded config; the original 260k checkpoint loads in the shared inference path; both original-vessel and mesh-backed 50-step CUDA/SOFA smoke runs populated replay, made one finite joint update (`force_loss≈0.19618`, `total_loss≈1.70683`), saved format-v2 checkpoints and loaded them via `load_g13()`; original, identity-mesh and explicitly scaled/rotated/translated mesh scene sanity checks passed; a single nominal evaluation episode ran with the smoke checkpoint (performance is not scientific). Unit/integration tests: 21 passed with the trusted original checkpoint supplied read-only. No frozen G13/G16.1 numerical component or third-party notice was changed. No commit or push was made.

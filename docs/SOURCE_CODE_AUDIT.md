# Source-code dependency audit (before copying)

Audited research source at Git commit
`540fca2aae99c1e6bc30102a20a3fa0973ac95ea`. The paths below are
relative to that source root. This document records the intended runtime
dependency closure before copying. No G-series collector, analysis, training
script, logs, run directory, or checkpoint is part of the release.

| Classification | Source | Destination | Runtime reason |
|---|---|---|---|
| CORE | `RL_TDMPC/tdmpc2/agent.py` (`TDMPC2Agent`, `RunningScale`) | `contact_aware_tdmpc2/tdmpc2/agent.py` | Frozen `act()` and latent-MPPI planner semantics, checkpoint state loading. |
| CORE | `RL_TDMPC/tdmpc2/networks.py` (`WorldModel` and helpers) | `contact_aware_tdmpc2/tdmpc2/world_model.py` | Exact checkpoint model architecture and planning computations. |
| CORE | `RL_TDMPC/experiments/world_model_g13/g13_model.py` (`GeometryForceWorldModel`, inference portion of `G13Agent`) | `contact_aware_tdmpc2/tdmpc2/geometry_force.py` | 22-D encoder and integrated post-transition `force_head`; the replay/training methods are omitted. |
| SIMULATION | `RL_TDMPC/envs/steve_env.py` | `contact_aware_tdmpc2/env/steve_env.py` | Frozen task, normalized observation/action, reset and reward behavior. |
| SIMULATION | `RL_TDMPC/envs/geometry_features.py` | `contact_aware_tdmpc2/env/observation.py` | Exact 8 added G13 geometry features and their ordering. |
| SIMULATION | `RL_TDMPC/experiments/world_model_g13/g13_env.py` | `contact_aware_tdmpc2/env/g13_env.py` | 22-D wrapper and passive force monitor lifecycle. |
| SIMULATION | `RL_TDMPC/experiments/generic_solver_g2/force_reconstruction.py` | `contact_aware_tdmpc2/env/force_reconstruction.py` | Generic constraint-force/Jacobian reconstruction in the distal 3 mm. |
| SIMULATION | `RL_TDMPC/experiments/generic_solver_g2/substep_monitor.py` | `contact_aware_tdmpc2/env/force_extraction.py` | Max over 22 SOFA substeps per RL step. |
| SIMULATION | tracked `eve/**` source and two `.stl` assets | `eve/**` and `third_party/stEVE_LICENSE` | The stEVE package imports its component namespace recursively and constructs the simulator. The installed `eve` in the working conda environment points to an **older LCP scene**; the tracked source at this commit is needed for the frozen Generic scene. Vendoring this small runtime package prevents an accidental scene substitution without depending on the research worktree or `PYTHONPATH`. Its original MIT license/notice is retained. |
| SAFETY | `RL_TDMPC/experiments/fuzzy_force_cbf_g16/g16_fuzzy.py` | `contact_aware_tdmpc2/safety/fuzzy_inference.py` | Exact ten-rule Mamdani inference and 0.001 centroid grid. The pre-G16.1 action mapping is excluded. |
| SAFETY | `RL_TDMPC/experiments/fuzzy_force_cbf_g16/g161_mapping.py` | `contact_aware_tdmpc2/safety/safety_filter.py` | Final rho=0.10 deadband and positive-insertion-only attenuation. |
| SAFETY | `RL_TDMPC/logs/fuzzy_force_cbf_g16/{fuzzy_membership_definition,fuzzy_rule_base,fuzzy_inference_definition}.json` | `configs/fuzzy_safety.yaml` | Frozen numerical memberships, 10 rules, and inference settings. Historical provenance paths and data hashes are not runtime inputs. |

The exact G13 inference configuration is read from the selected checkpoint and
cross-checked against `configs/tdmpc2.yaml`; the checkpoint itself is **not**
copied. Source helper responsibilities from `RL_TDMPC/train.py`
(`build_agent_config`) and `RL_TDMPC/tdmpc2/common.py` (seed/checkpoint loading)
are replaced by small, repository-local inference helpers. Runtime scene
assertions are derived from `RL_TDMPC/experiments/generic_solver_g2/collect.py`.

Excluded as HISTORICAL/EXPERIMENT-ONLY: all `RL_TDMPC/experiments/**` except
the isolated functions/classes above, `RL_TDMPC/tdmpc2/replay_buffer.py`,
training entry points, G15 model/reward, G16.2 recovery, final comparison
collectors, and all `RL_TDMPC/logs/**` and `RL_TDMPC/runs/**` data.

The vendored `eve` package is an upstream simulation runtime dependency, **not**
the research experiment tree. Its breadth is required by eager package imports
from `eve/__init__.py` and the task's intervention/observation/reward graph.

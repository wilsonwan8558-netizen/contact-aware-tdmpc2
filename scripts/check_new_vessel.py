"""One-reset/one-step geometry and force sanity check; never trains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def inspect_env(env) -> dict:
    import numpy as np
    from contact_aware_tdmpc2.env.scene_check import assert_generic_scene
    observation, _ = env.reset(seed=17)
    assert_generic_scene(env.env)
    geometry = env.last_geometry
    raw_five = np.asarray(env.env._env.observation.observations["position"].wrapped_obs.obs)
    if (observation.shape != (22,) or not np.all(np.isfinite(observation))
            or raw_five.shape != (5, 2) or not np.all(np.isfinite(raw_five))
            or geometry.sampled_tracking_2d_mm.shape != (3, 2)
            or not np.all(np.isfinite(geometry.clearance_mm))
            or not np.isfinite(geometry.radius_mm) or geometry.radius_mm <= 0
            or geometry.direction_valid not in (0.0, 1.0)):
        raise RuntimeError("Invalid G13 geometry/observation after reset")
    tree = env.env.intervention.vessel_tree
    target = np.asarray(env.env.intervention.target.coordinates3d, dtype=float)
    if target.shape != (3,) or not np.all(np.isfinite(target)):
        raise RuntimeError("Invalid target after reset")
    low, high = env.env.raw_action_limits
    if not np.allclose(low, [-50, -3.14]) or not np.allclose(high, [50, 3.14]):
        raise RuntimeError("Frozen action scaling changed")
    next_obs, _, terminated, truncated, info = env.step(np.zeros(2, dtype=np.float32))
    if (next_obs.shape != (22,) or not np.all(np.isfinite(next_obs))
            or not np.isfinite(info["distal_contact_force_max_N"])
            or info["sofa_substeps"] != 22):
        raise RuntimeError("Invalid G13 step/force extraction")
    return {"status": "PASS", "branch_count": len(tree.branches),
            "target_3d_mm": target.tolist(), "observation_dim": 22,
            "action_dim": 2, "five_tracking_points_available": True,
            "clearance_proxy_mm": geometry.clearance_mm.tolist(),
            "local_radius_mm": geometry.radius_mm,
            "direction_valid": geometry.direction_valid,
            "tracking_alignment_error_mm": geometry.tracking_alignment_error_mm,
            "raw_action_low": low.tolist(), "raw_action_high": high.tolist(),
            "zero_step_terminated": bool(terminated), "zero_step_truncated": bool(truncated),
            "zero_step_distal_force_max_N": info["distal_contact_force_max_N"],
            "sofa_substeps": info["sofa_substeps"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-config", required=True)
    parser.add_argument("--config", default="configs/train_g13.yaml")
    args = parser.parse_args()
    env = None
    try:
        from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin
        from contact_aware_tdmpc2.training.config import load_training_config
        from contact_aware_tdmpc2.training.scene import (assert_original_scene_compatible,
                                                         load_scene_config)
        assert_bundled_eve_origin()
        from contact_aware_tdmpc2.env.g13_env import make_g13_env
        config = load_training_config(args.config)
        scene = load_scene_config(args.scene_config)
        environment = dict(config["environment"])
        if scene["kind"] == "from_mesh":
            environment["scene"] = scene
        else:
            assert_original_scene_compatible(scene, environment)
        env = make_g13_env(environment)
        print(json.dumps(inspect_env(env), indent=2, sort_keys=True), flush=True)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), flush=True)
        raise SystemExit(2) from None
    finally:
        if env is not None:
            env.close()


if __name__ == "__main__":
    main()

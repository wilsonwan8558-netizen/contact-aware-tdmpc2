"""Evaluate a trusted nominal G13 checkpoint on one declared vessel scene."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parse_seeds(value: str) -> list[int]:
    if ":" in value:
        first, last = (int(x) for x in value.split(":"))
        if last < first or last-first > 10000:
            raise ValueError("Invalid inclusive seed range")
        return list(range(first, last+1))
    seeds = [int(x) for x in value.split(",")]
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("Seeds must be nonempty and unique")
    return seeds


def evaluate(checkpoint: str, scene_path: str, seeds: list[int], device: str) -> dict:
    import numpy as np
    from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin
    from contact_aware_tdmpc2.tdmpc2.checkpoint import load_g13, set_seed
    from contact_aware_tdmpc2.training.scene import (assert_original_scene_compatible,
                                                     load_scene_config)
    from contact_aware_tdmpc2.env.g13_env import make_g13_env

    assert_bundled_eve_origin()
    agent, config = load_g13(checkpoint, device=device)
    scene = load_scene_config(scene_path)
    env_config = dict(config["environment"])
    if "scene" in env_config:
        if env_config["scene"] != scene:
            raise ValueError("Evaluation scene differs from checkpoint training scene")
    else:
        assert_original_scene_compatible(scene, env_config)
    env = make_g13_env(env_config)
    records = []
    try:
        for seed in seeds:
            set_seed(seed)
            observation, _ = env.reset(seed=seed)
            terminated = truncated = success = simulation_error = False
            reward_sum = 0.0
            forces = []
            length = 0
            while not (terminated or truncated):
                action = agent.act(observation, first_step=length == 0, eval_mode=True)
                observation, reward, terminated, truncated, info = env.step(action)
                length += 1
                reward_sum += float(reward)
                forces.append(float(info["distal_contact_force_max_N"]))
                success = success or bool(info.get("is_success", False))
                simulation_error = simulation_error or bool(info.get("simulation_error", False))
            records.append({"seed": seed, "success": success, "episode_length": length,
                            "episode_reward": reward_sum, "peak_force_N": max(forces),
                            "above_F_lim_steps": sum(f > 3.685331040756903 for f in forces),
                            "terminated": bool(terminated), "truncated": bool(truncated),
                            "simulation_error": simulation_error})
    finally:
        env.close()
    total_steps = sum(row["episode_length"] for row in records)
    return {"controller": "nominal G13, no G16.1 filter", "seeds": seeds,
            "episodes": records, "success_rate": float(np.mean([x["success"] for x in records])),
            "mean_episode_length": float(np.mean([x["episode_length"] for x in records])),
            "mean_reward": float(np.mean([x["episode_reward"] for x in records])),
            "peak_force_max_N": float(max(x["peak_force_N"] for x in records)),
            "peak_force_mean_N": float(np.mean([x["peak_force_N"] for x in records])),
            "above_F_lim_fraction": sum(x["above_F_lim_steps"] for x in records)/total_steps,
            "failures": sum(not x["success"] for x in records),
            "truncations": sum(x["truncated"] for x in records),
            "simulation_errors": sum(x["simulation_error"] for x in records),
            "F_lim_N": 3.685331040756903,
            "F_lim_is_nominal_simulation_reference_not_clinical_threshold": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--scene-config", required=True)
    parser.add_argument("--seeds", required=True, help="Comma list or inclusive first:last")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--output", default=None, help="Optional JSON report path")
    args = parser.parse_args()
    report = evaluate(args.checkpoint, args.scene_config, parse_seeds(args.seeds), args.device)
    if args.output:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

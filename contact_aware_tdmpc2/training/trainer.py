"""G13 300k training loop, adapted only for paths, scene and resumability."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import random
import time

import numpy as np
import torch

from ..env.g13_env import make_g13_env
from .agent import G13TrainingAgent
from .checkpointing import load_training_payload, restore_rng_state, save_checkpoint
from .config import build_agent_config
from .replay_buffer import G13ReplayBuffer
from .scene import assert_original_scene_compatible

F_LIM = 3.685331040756903


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class MetricLogger:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.headers = {}

    def log(self, category: str, values: dict) -> None:
        record = {"category": category, **values}
        with (self.directory / "metrics.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        path = self.directory / f"{category}.csv"
        if category not in self.headers:
            if path.exists() and path.stat().st_size:
                with path.open(newline="", encoding="utf-8") as stream:
                    self.headers[category] = tuple(next(csv.reader(stream)))
            else:
                self.headers[category] = tuple(record)
        header = self.headers[category]
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            if write_header:
                writer.writeheader()
            writer.writerow({name: record.get(name, "") for name in header})


class LossAccumulator:
    def __init__(self) -> None:
        self.sums = {}
        self.count = 0

    def add(self, metrics: dict) -> None:
        for name, value in metrics.items():
            self.sums[name] = self.sums.get(name, 0.0) + float(value)
        self.count += 1

    def pop_means(self) -> dict:
        if not self.count:
            return {}
        result = {name: value/self.count for name, value in self.sums.items()}
        self.sums.clear()
        self.count = 0
        return result


def train(config: dict, scene: dict, output_dir: str | Path, *,
          resume: str | Path | None = None, smoke_steps: int | None = None,
          evaluate_at_checkpoints: bool = False, scene_config_path: str | Path | None = None) -> dict:
    """Run the frozen update loop; optional smoke overrides are diagnostic only."""
    config = json.loads(json.dumps(config))
    if scene["kind"] == "original_aortic_arch":
        # Identical default constructor, with no extra checkpoint config key.
        assert_original_scene_compatible(scene, config["environment"])
    else:
        config["environment"]["scene"] = scene
    if smoke_steps is not None:
        if resume is not None or not 3 <= smoke_steps <= 200:
            raise ValueError("smoke steps must be 3..200 and cannot resume")
        config["training"].update(total_steps=smoke_steps, seed_steps=3,
                                  initial_updates=1, batch_size=8)
    if resume is not None:
        restored = load_training_payload(resume)
        if restored["config"] != config:
            raise ValueError("Resume config/scene differs from saved checkpoint")
    else:
        restored = None
    device_name = str(config["training"]["device"])
    if device_name.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"Requested {device_name} but CUDA is unavailable")
    device = torch.device(device_name)
    run_dir = Path(output_dir).expanduser().resolve()
    if resume is None and run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"Refusing to reuse nonempty training run directory: {run_dir}")
    checkpoint_dir = run_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    logger = MetricLogger(run_dir / "logs")
    (run_dir / "training_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8") if resume is None else None
    seed = int(config["training"]["seed"])
    set_seed(seed)
    env = make_g13_env(config["environment"])
    agent = G13TrainingAgent(22, 2, build_agent_config(config),
                             episode_length=int(config["environment"]["max_episode_steps"]),
                             device=device)
    replay = G13ReplayBuffer(int(config["training"]["replay_capacity"]), 22, 2,
                             int(config["training"]["horizon"]),
                             int(config["training"]["batch_size"]), seed=seed)
    total_steps = episode_index = successes = 0
    if restored is not None:
        agent.load_state_dict(restored["agent"], load_optimizers=True)
        replay.load_state_dict(restored["replay"])
        total_steps = int(restored["total_env_steps"])
        episode_index = int(restored["episode_index"])
        successes = int(restored["success_count"])
        restore_rng_state(restored["rng_state"])
    budget = int(config["training"]["total_steps"])
    if total_steps >= budget:
        env.close()
        raise ValueError("Checkpoint already reached total training budget")
    losses = LossAccumulator()
    start_time = time.time()
    last_update = None
    try:
        while total_steps < budget:
            episode_seed = seed + episode_index
            env.action_space.seed(episode_seed)
            observation, _ = env.reset(seed=episode_seed)
            observations = [observation.copy()]
            actions, rewards, terminations, forces = [], [], [], []
            episode_reward = 0.0
            success = simulation_error = False
            terminated = truncated = False
            while not (terminated or truncated) and total_steps < budget:
                random_action = total_steps < int(config["training"]["seed_steps"]) or agent.update_count == 0
                action = (env.action_space.sample().astype(np.float32) if random_action
                          else agent.act(observation, first_step=len(actions) == 0, eval_mode=False))
                next_observation, reward, terminated, truncated, info = env.step(action)
                total_steps += 1
                if total_steps >= budget and not (terminated or truncated):
                    truncated = True
                force = float(info["distal_contact_force_max_N"])
                if not np.isfinite(force) or force < 0:
                    raise FloatingPointError("G13 frozen distal force label invalid")
                observations.append(next_observation.copy())
                actions.append(action.copy())
                rewards.append(float(reward))
                terminations.append(bool(terminated))
                forces.append(force)
                episode_reward += float(reward)
                success = success or bool(info.get("is_success", False))
                simulation_error = simulation_error or bool(info.get("simulation_error", False))
                observation = next_observation
                episode_done = terminated or truncated or total_steps >= budget
                if episode_done:
                    replay.add_episode(observations, actions, rewards, terminations, forces)
                if total_steps >= int(config["training"]["seed_steps"]) and replay.can_sample():
                    updates = (int(config["training"]["initial_updates"]) if agent.update_count == 0
                               else int(config["training"]["updates_per_step"]))
                    for _ in range(updates):
                        last_update = agent.update(replay)
                        losses.add(last_update)
                if agent.update_count and total_steps % int(config["logging"]["update_interval"]) == 0:
                    metrics = losses.pop_means()
                    if metrics:
                        metrics.update(total_env_steps=total_steps, update_count=agent.update_count,
                                       replay_size=len(replay), elapsed_seconds=time.time()-start_time)
                        logger.log("updates", metrics)
                if total_steps % int(config["checkpoint"]["interval"]) == 0 and smoke_steps is None:
                    path = checkpoint_dir / f"step_{total_steps}.pt"
                    save_checkpoint(path, config, agent, replay, total_steps,
                                    episode_index + (1 if episode_done else 0),
                                    successes + (int(success) if episode_done else 0))
                    print("G13_TRAIN_CHECKPOINT", path, flush=True)
                    if evaluate_at_checkpoints:
                        if scene_config_path is None:
                            raise ValueError("Periodic evaluation requires a scene config path")
                        import subprocess
                        import sys
                        script = Path(__file__).resolve().parents[2] / "scripts/evaluate_g13_checkpoint.py"
                        subprocess.run([sys.executable, str(script), "--checkpoint", str(path),
                                        "--scene-config", str(scene_config_path),
                                        "--seeds", f"{config['evaluation']['seed']}:"
                                        f"{config['evaluation']['seed']+config['evaluation']['episodes']-1}",
                                        "--device", device_name,
                                        "--output", str(run_dir / f"evaluation_step_{total_steps}.json")],
                                       check=True)
            successes += int(success)
            episode_index += 1
            logger.log("episodes", {"total_env_steps": total_steps, "episode": episode_index,
                                   "episode_reward": episode_reward, "episode_length": len(actions),
                                   "success": success, "success_rate": successes/episode_index,
                                   "terminated": bool(terminated), "truncated": bool(truncated),
                                   "simulation_error": simulation_error, "replay_size": len(replay),
                                   "episode_peak_force_N": float(max(forces)),
                                   "episode_above_F_lim_steps": sum(f > F_LIM for f in forces)})
            print("G13_TRAIN_EPISODE", episode_index, total_steps,
                  round(successes/episode_index, 4), flush=True)
    finally:
        env.close()
    final = checkpoint_dir / f"step_{total_steps}.pt"
    if not final.exists():
        save_checkpoint(final, config, agent, replay, total_steps, episode_index, successes)
    result = {"total_env_steps": total_steps, "episode_index": episode_index,
              "successes": successes, "updates": agent.update_count,
              "replay_size": len(replay), "last_update": last_update,
              "final_checkpoint": str(final), "smoke_only": smoke_steps is not None}
    (run_dir / "training_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result

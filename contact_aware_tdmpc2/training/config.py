"""Parse and validate the recovered G13 training configuration."""
from __future__ import annotations

from pathlib import Path
import yaml

SECTIONS = ("environment", "model", "training", "planning", "logging", "checkpoint", "evaluation")


def load_training_config(path: str | Path) -> dict:
    source = Path(path).expanduser().resolve()
    config = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or any(not isinstance(config.get(key), dict) for key in SECTIONS):
        raise ValueError(f"G13 config must contain mapping sections {SECTIONS}")
    if int(config["training"]["horizon"]) != int(config["planning"]["horizon"]):
        raise ValueError("training and planner horizons must agree")
    if int(config["model"]["latent_dim"]) != 256 or int(config["planning"]["horizon"]) != 3:
        raise ValueError("G13 model identity changed")
    if float(config["training"]["lambda_force_train"]) != 0.5:
        raise ValueError("G13 force-head loss coefficient changed")
    for name in ("total_steps", "seed_steps", "initial_updates", "updates_per_step", "batch_size", "replay_capacity"):
        if int(config["training"][name]) <= 0:
            raise ValueError(f"training.{name} must be positive")
    if int(config["checkpoint"]["interval"]) <= 0:
        raise ValueError("checkpoint.interval must be positive")
    return config


def build_agent_config(config: dict) -> dict:
    if int(config["training"]["horizon"]) != int(config["planning"]["horizon"]):
        raise ValueError("training and planner horizons must agree")
    return {**config["model"], **config["training"], **config["planning"]}

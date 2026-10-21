"""Strict loader for the trusted, selected G13 checkpoint."""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import numpy as np
import torch
import yaml

from .geometry_force import G13Agent

ROOT = Path(__file__).resolve().parents[2]


def _config_path(name: str) -> Path:
    source = ROOT / "configs" / name
    return source if source.is_file() else Path(__file__).resolve().parents[1] / "configs" / name


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_g13(checkpoint_path: str | Path, *, device: str = "cuda:0") -> tuple[G13Agent, dict]:
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    path = Path(checkpoint_path).expanduser().resolve()
    frozen = yaml.safe_load(_config_path("tdmpc2.yaml").read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != frozen["checkpoint"]["sha256"]:
        raise RuntimeError("G13 checkpoint SHA256 mismatch")
    # This full-state research checkpoint uses pickle. Load only trusted,
    # hash-verified local files; never load an untrusted downloaded pickle.
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    expected = frozen["checkpoint"]
    for key in ("algorithm", "format_version", "total_env_steps"):
        if checkpoint.get(key) != expected[key]:
            raise RuntimeError(f"G13 checkpoint {key} mismatch")
    if checkpoint.get("observation_dim") != 22:
        raise RuntimeError("G13 checkpoint must use 22-D observation")
    state = checkpoint["agent"]
    if state.get("observation_dim") != 22 or state.get("action_dim") != 2:
        raise RuntimeError("G13 checkpoint agent dimensions mismatch")
    if not any(key.startswith("force_head.") for key in state["model"]):
        raise RuntimeError("G13 checkpoint has no integrated force_head")
    config = checkpoint["config"]
    for key, value in frozen["model"].items():
        if config["model"][key] != value:
            raise RuntimeError(f"G13 model config mismatch: {key}")
    for key, value in frozen["planning"].items():
        if config["planning"][key] != value:
            raise RuntimeError(f"G13 planner config mismatch: {key}")
    for key, value in frozen["agent_initialization"].items():
        if config["training"][key] != value:
            raise RuntimeError(f"G13 agent config mismatch: {key}")
    agent_config = {**config["model"], **config["training"], **config["planning"]}
    agent = G13Agent(22, 2, agent_config,
                     episode_length=int(config["environment"]["max_episode_steps"]),
                     device=torch.device(device))
    agent.load_state_dict(state, load_optimizers=False)
    agent.model.eval().requires_grad_(False)
    return agent, config

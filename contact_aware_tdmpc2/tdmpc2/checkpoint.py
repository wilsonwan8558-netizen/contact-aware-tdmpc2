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


class MissingCheckpointError(RuntimeError):
    """The approved, intentionally unbundled G13 checkpoint is unavailable."""


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
    path = Path(checkpoint_path).expanduser().resolve()
    frozen = yaml.safe_load(_config_path("tdmpc2.yaml").read_text())
    if not path.is_file():
        raise MissingCheckpointError(
            "The G13 checkpoint is intentionally not distributed in Git. "
            f"Expected {frozen['checkpoint']['filename']} with SHA256 "
            f"{frozen['checkpoint']['sha256']}. Obtain the approved file and use "
            "--checkpoint /path/to/step_260000.pt. "
            f"Missing file: {path}"
        )
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    is_frozen = digest == frozen["checkpoint"]["sha256"]
    if not is_frozen:
        sidecar = path.with_suffix(path.suffix + ".sha256")
        tokens = sidecar.read_text(encoding="utf-8").split() if sidecar.is_file() else []
        if not tokens or tokens[0] != digest:
            raise RuntimeError("G13 checkpoint SHA256 mismatch; locally trained checkpoints require a matching .pt.sha256 sidecar")
    # This full-state research checkpoint uses pickle. Load only trusted,
    # hash-verified local files; never load an untrusted downloaded pickle.
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    expected = frozen["checkpoint"]
    required_keys = ("algorithm", "format_version", "total_env_steps") if is_frozen else ("algorithm", "format_version")
    for key in required_keys:
        if checkpoint.get(key) != expected[key]:
            raise RuntimeError(f"G13 checkpoint {key} mismatch")
    if not is_frozen and (not isinstance(checkpoint.get("total_env_steps"), int)
                          or checkpoint["total_env_steps"] < 0):
        raise RuntimeError("Locally trained G13 checkpoint has invalid step metadata")
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

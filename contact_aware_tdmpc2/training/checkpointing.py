"""Research G13 format-v2 full-state checkpoints with local SHA sidecars."""
from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import random
import time

import numpy as np
import torch


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture_rng_state() -> dict:
    state = {"python": random.getstate(), "numpy": np.random.get_state(),
             "torch": torch.get_rng_state()}
    if torch.cuda.is_available():
        state["cuda"] = torch.cuda.get_rng_state_all()
    return state


def restore_rng_state(state: dict) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if "cuda" in state and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state["cuda"])


def save_checkpoint(path: str | Path, config: dict, agent, replay,
                    total_steps: int, episode_index: int, success_count: int) -> Path:
    """Keep every research payload key and the exact force target definition."""
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite G13 checkpoint: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 2,
        "algorithm": "Geometry-Force-TD-MPC2",
        "config": copy.deepcopy(config),
        "agent": agent.state_dict(),
        "total_env_steps": int(total_steps),
        "episode_index": int(episode_index),
        "success_count": int(success_count),
        "rng_state": capture_rng_state(),
        "saved_at_unix": time.time(),
        "observation_dim": 22,
        "force_target": "next-RL-interval max-substep distal contact force, nominal N",
        "force_head_attachment": "predicted next latent WorldModel.next(z_t,a_t)",
        "lambda_force_train": agent.lambda_force_train,
        "replay": replay.state_dict(),
    }
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        torch.save(payload, temporary)
        os.replace(temporary, destination)
        digest = sha256(destination)
        sidecar = destination.with_suffix(destination.suffix + ".sha256")
        sidecar.write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def load_training_payload(path: str | Path, *, device: str | torch.device = "cpu") -> dict:
    source = Path(path).expanduser().resolve()
    sidecar = source.with_suffix(source.suffix + ".sha256")
    tokens = sidecar.read_text(encoding="utf-8").split() if sidecar.is_file() else []
    if not tokens or tokens[0] != sha256(source):
        raise RuntimeError("Training checkpoint SHA256 sidecar missing or mismatched")
    # Full-state pickle is for locally created, trusted checkpoints only.
    payload = torch.load(source, map_location=device, weights_only=False)
    if (payload.get("format_version") != 2 or payload.get("algorithm") != "Geometry-Force-TD-MPC2"
            or payload.get("observation_dim") != 22 or "replay" not in payload):
        raise RuntimeError("Not a resumable G13 format-v2 checkpoint")
    return payload

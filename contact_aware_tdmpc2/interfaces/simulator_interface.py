"""Simulation adapter return contract for demos and platform substitution."""

from __future__ import annotations

from typing import Protocol
import numpy as np


class SimulatorInterface(Protocol):
    def reset(self, *, seed: int) -> tuple[np.ndarray, dict]: ...
    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict]: ...
    def close(self) -> None: ...

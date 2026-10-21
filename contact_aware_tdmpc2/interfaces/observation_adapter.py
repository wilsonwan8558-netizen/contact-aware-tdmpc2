"""Explicit boundary between physical sensing and frozen 22-D controller input."""

from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np

from .robot_interface import RobotInterface


def assemble_observation(base14: np.ndarray, geometry8: np.ndarray) -> np.ndarray:
    base = np.asarray(base14, dtype=np.float32)
    geometry = np.asarray(geometry8, dtype=np.float32)
    if base.shape != (14,) or geometry.shape != (8,):
        raise ValueError("Expected 14 base and 8 geometry features")
    result = np.concatenate((base, geometry)).astype(np.float32)
    if not np.all(np.isfinite(result)):
        raise ValueError("Nonfinite G13 observation")
    return result


class ObservationAdapter(ABC):
    @abstractmethod
    def build(self, robot: RobotInterface) -> np.ndarray:
        """Reconstruct the exact frozen 22-D normalized G13 observation."""

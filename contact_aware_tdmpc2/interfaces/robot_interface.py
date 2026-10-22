"""Hardware-facing contract; deliberately no platform-specific implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np


class RobotInterface(ABC):
    @abstractmethod
    def get_tracking_points(self) -> np.ndarray:
        """Return current ordered guidewire points in a calibrated frame."""

    @abstractmethod
    def get_rotation(self) -> float:
        """Return current device rotation in radians."""

    @abstractmethod
    def get_target(self) -> np.ndarray:
        """Return target in the same frame as tracking points."""

    @abstractmethod
    def send_action(self, insertion_velocity: float, rotation_velocity: float) -> None:
        """Send bounded physical velocities; adapter owns interlocks and watchdog."""

    def reset(self) -> None:
        """Optional robot-side reset; never infer simulator reset semantics."""

"""Replace SOFA-only force reconstruction with a validated physical signal."""

from __future__ import annotations

from typing import Protocol


class ForceInterface(Protocol):
    def read_force(self) -> float:
        """Return a finite nonnegative force estimate after calibration."""

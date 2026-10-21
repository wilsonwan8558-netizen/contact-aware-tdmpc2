"""Frozen symmetric normalized-action to device-velocity mapping."""

from __future__ import annotations

import numpy as np


def to_device_velocity(action: np.ndarray,
                       limits: tuple[float, float] = (50.0, 3.14)) -> np.ndarray:
    """Mirror StEVEEnv._denormalize_action for the frozen JShaped device."""
    value = np.asarray(action, dtype=np.float32)
    if value.shape != (2,) or not np.all(np.isfinite(value)):
        raise ValueError("Expected finite normalized [insertion, rotation] action")
    high = np.asarray(limits, dtype=np.float32)
    if high.shape != (2,) or np.any(high <= 0):
        raise ValueError("Expected two positive velocity limits")
    low = -high
    clipped = np.clip(value, -1.0, 1.0)
    return (low + np.float32(0.5) * (clipped + np.float32(1.0)) *
            (high - low)).astype(np.float32)

"""The single G16.1 change: deadband the frozen G16 risk-to-action mapping."""

from __future__ import annotations

import numpy as np

RHO_0 = 0.10


def effective_risk(rho: float) -> float:
    if not np.isfinite(rho) or not 0.0 <= rho <= 1.0:
        raise ValueError("G16.1 rho must be finite and in [0, 1]")
    if rho <= RHO_0:
        return 0.0
    return float(np.clip((rho - RHO_0) / (1.0 - RHO_0), 0.0, 1.0))


def filter_action_g161(action: np.ndarray, rho: float) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32)
    if action.shape != (2,) or not np.all(np.isfinite(action)):
        raise ValueError("Invalid G16.1 nominal action")
    result = action.copy()
    if result[0] > 0:
        result[0] = np.float32((1.0 - effective_risk(rho)) * float(result[0]))
    if result[0] < 0 and action[0] > 0:
        raise RuntimeError("G16.1 created active withdrawal")
    if result[1] != action[1]:
        raise RuntimeError("G16.1 changed rotation")
    return result

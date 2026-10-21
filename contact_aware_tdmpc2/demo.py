"""Small, non-scientific smoke episodes with the frozen Generic-SOFA task."""

from __future__ import annotations

import numpy as np

from .controller import ContactAwareController
from .env.scene_check import assert_generic_scene
from .tdmpc2.checkpoint import set_seed


def run_episode(env, controller: ContactAwareController, seed: int,
                *, safety_enabled: bool) -> dict:
    set_seed(seed)
    env.action_space.seed(seed)
    observation, _ = env.reset(seed=seed)
    assert_generic_scene(env.env)
    controller.reset_episode()
    current_force = 0.0
    peak_force = 0.0
    modified = 0
    max_rho = 0.0
    max_rho_eff = 0.0
    steps = 0
    success = False
    terminated = truncated = False
    while not (terminated or truncated):
        action, diagnostics = controller.step(observation, current_force,
                                              safety_enabled=safety_enabled)
        if not np.array_equal(action, diagnostics["nominal_action"]):
            modified += 1
        max_rho = max(max_rho, diagnostics["rho"])
        max_rho_eff = max(max_rho_eff, diagnostics["rho_eff"])
        observation, _, terminated, truncated, info = env.step(action)
        current_force = float(info["distal_contact_force_max_N"])
        peak_force = max(peak_force, current_force)
        steps += 1
        success = bool(info.get("is_success", False))
        if info.get("simulation_error", False):
            raise RuntimeError(f"SOFA simulation error on seed {seed}, step {steps}")
    return {"seed": seed, "success": success, "episode_length": steps,
            "peak_force_N": peak_force, "modified_action_fraction": modified / steps,
            "max_rho": max_rho, "max_rho_eff": max_rho_eff}

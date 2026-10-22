"""G13 current-geometry observation plus passive frozen distal-force label."""

from __future__ import annotations

import gymnasium as gym
import numpy as np

from .steve_env import FROZEN_SOFA_FRICTION, make_steve_env
from .observation import GeometryFeatureExtractor, OBSERVATION_DIM
from .force_extraction import CONTROL_SUBSTEPS, SOFA_DT_S, DistalForceMonitor
from ..runtime_checks import assert_bundled_eve_origin, assert_simulation_config


class GeometryForceEnv(gym.Wrapper):
    """Preserve the original task; append geometry and return passive force info.

    The force label is deliberately never part of the observation. The monitor
    is attached to the same reused SOFA scene only after its first reset,
    matching the established Generic G2 measurement lifecycle.
    """

    def __init__(self, config=None) -> None:
        assert_bundled_eve_origin()
        assert_simulation_config(
            implementation_dt_s=SOFA_DT_S,
            implementation_friction=FROZEN_SOFA_FRICTION,
            implementation_substeps=CONTROL_SUBSTEPS,
        )
        base = make_steve_env(config)
        super().__init__(base)
        self.observation_space = gym.spaces.Box(
            low=-np.ones(OBSERVATION_DIM, dtype=np.float32),
            high=np.ones(OBSERVATION_DIM, dtype=np.float32), dtype=np.float32)
        self.extractor = GeometryFeatureExtractor()
        self.monitor = DistalForceMonitor(base)
        self.last_geometry = None
        self._monitor_attached = False

    def _augment(self, original: np.ndarray) -> np.ndarray:
        original = np.asarray(original, dtype=np.float32)
        if original.shape != (14,):
            raise RuntimeError("G13 original observation shape changed")
        self.last_geometry = self.extractor.compute(self.env)
        augmented = np.concatenate((original, self.last_geometry.normalized)).astype(np.float32)
        if augmented.shape != (OBSERVATION_DIM,) or not np.all(np.isfinite(augmented)):
            raise RuntimeError("G13 augmented observation invalid")
        return augmented

    def reset(self, *, seed=None, options=None):
        original, info = self.env.reset(seed=seed, options=options)
        if not self._monitor_attached:
            self.env._simulation.root.addObject(self.monitor)
            self._monitor_attached = True
        return self._augment(original), info

    def step(self, action):
        self.monitor.begin_step()
        original, reward, terminated, truncated, info = self.env.step(action)
        force = self.monitor.finish_step()
        info = dict(info)
        info["distal_contact_force_max_N"] = float(force.maximum_N)
        info["distal_contact_force_mean_N"] = float(force.mean_N)
        info["distal_force_time_integral_Ns"] = float(force.integral_Ns)
        info["distal_contact_substeps"] = int(force.contact_substeps)
        info["sofa_substeps"] = int(force.substep_count)
        return self._augment(original), reward, terminated, truncated, info


def make_g13_env(config=None) -> GeometryForceEnv:
    return GeometryForceEnv(config)

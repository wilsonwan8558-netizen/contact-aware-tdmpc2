"""Collaborator-facing nominal controller and frozen G16.1 action filter."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from .safety.fuzzy_inference import FrozenFuzzyRisk
from .safety.safety_filter import effective_risk, filter_action_g161
from .tdmpc2.checkpoint import load_g13

ROOT = Path(__file__).resolve().parents[1]


class ContactAwareController:
    def __init__(self, checkpoint: str | Path, *, device: str = "cuda:0") -> None:
        self.agent, self.config = load_g13(checkpoint, device=device)
        source_config = ROOT / "configs/fuzzy_safety.yaml"
        packaged_config = Path(__file__).resolve().parent / "configs/fuzzy_safety.yaml"
        self.fuzzy = FrozenFuzzyRisk(source_config if source_config.is_file()
                                     else packaged_config)
        self.first_step = True

    def reset_episode(self) -> None:
        self.first_step = True

    def step(self, observation: np.ndarray, current_force: float,
             *, safety_enabled: bool = True) -> tuple[np.ndarray, dict]:
        obs = np.asarray(observation, dtype=np.float32)
        if obs.shape != (22,) or not np.all(np.isfinite(obs)):
            raise ValueError("Expected finite 22-D G13 observation")
        nominal = self.agent.act(obs, first_step=self.first_step, eval_mode=True)
        self.first_step = False
        with torch.inference_mode():
            o = self.agent._tensor_observation(obs)
            a = torch.as_tensor(nominal, dtype=torch.float32,
                                device=self.agent.device).unsqueeze(0)
            predicted = float(self.agent.model.force(
                self.agent.model.next(self.agent.model.encode(o), a))[0, 0].item())
        clearance = float(np.min(obs[14:17]))
        fuzzy = self.fuzzy.evaluate(float(current_force), predicted, clearance)
        rho = fuzzy["rho"]
        rho_eff = effective_risk(rho)
        safe = filter_action_g161(nominal, rho) if safety_enabled else nominal.copy()
        diagnostics = {
            "nominal_action": nominal.copy(), "predicted_force": predicted,
            "wall_clearance": clearance, "fuzzy_memberships": fuzzy["memberships"],
            "rule_strengths": fuzzy["rule_strengths"], "rho": rho,
            "rho_eff": rho_eff, "safe_action": safe.copy(),
        }
        return safe, diagnostics

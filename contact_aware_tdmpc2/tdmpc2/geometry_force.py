"""Inference-only G13 architecture; matching the selected G13 checkpoint."""

from __future__ import annotations

from typing import Any, Dict, Mapping

import torch
import torch.nn as nn

from .agent import TDMPC2Agent
from .world_model import WorldModel, mlp, weight_init


class GeometryForceWorldModel(WorldModel):
    def __init__(self, observation_dim: int, action_dim: int, config: Dict) -> None:
        super().__init__(observation_dim, action_dim, config)
        mlp_dim = int(config["mlp_dim"])
        self.force_head = nn.Sequential(
            mlp(self.latent_dim, [mlp_dim, mlp_dim], 1), nn.Softplus()
        )
        self.force_head.apply(weight_init)

    def force(self, next_latent: torch.Tensor) -> torch.Tensor:
        return self.force_head(next_latent)


class G13Agent(TDMPC2Agent):
    """Frozen G13 task planner with an integrated force prediction head."""

    def __init__(self, observation_dim: int, action_dim: int,
                 config: Mapping[str, Any], *, episode_length: int,
                 device: torch.device) -> None:
        if observation_dim != 22:
            raise ValueError("G13 primary observation must be 22-D")
        super().__init__(observation_dim, action_dim, config,
                         episode_length=episode_length, device=device)
        self.model = GeometryForceWorldModel(observation_dim, action_dim,
                                             self.config).to(device)
        self.model.train(False)
        lr = float(self.config["lr"])
        self.model_optimizer = torch.optim.Adam([
            {"params": self.model.encoder.parameters(),
             "lr": lr * float(self.config["enc_lr_scale"])},
            {"params": self.model.dynamics.parameters()},
            {"params": self.model.reward_head.parameters()},
            {"params": self.model.termination_head.parameters()},
            {"params": self.model.q_ensemble.parameters()},
            {"params": self.model.force_head.parameters()},
        ], lr=lr)
        self.policy_optimizer = torch.optim.Adam(
            self.model.policy.parameters(), lr=lr, eps=1e-5)
        self.lambda_force_train = float(self.config["lambda_force_train"])
        if not self.lambda_force_train > 0:
            raise ValueError("G13 force training coefficient must be positive")

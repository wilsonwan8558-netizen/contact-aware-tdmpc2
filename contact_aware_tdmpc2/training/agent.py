"""Training-only update extension of the shared frozen G13 model family."""
from __future__ import annotations

import torch

from ..tdmpc2.geometry_force import G13Agent
from .losses import g13_loss_terms


class G13TrainingAgent(G13Agent):
    def loss_terms(self, batch):
        return g13_loss_terms(self, batch)

    def update(self, replay_buffer) -> dict[str, float]:
        batch = replay_buffer.sample(self.device)
        terms, latent_rollout = self.loss_terms(batch)
        if not all(torch.isfinite(value).all() for value in terms.values()):
            raise FloatingPointError("G13 joint world-model loss is nonfinite")
        self.model_optimizer.zero_grad(set_to_none=True)
        terms["total_loss"].backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(
            [p for group in self.model_optimizer.param_groups for p in group["params"]],
            float(self.config["grad_clip_norm"]))
        self.model_optimizer.step()
        policy_info = self._update_policy(latent_rollout.detach())
        self.model.soft_update_target_q(float(self.config["tau"]))
        self.model.train(False)
        self.update_count += 1
        return {**{key: float(value.detach().cpu()) for key, value in terms.items()},
                "model_grad_norm": float(grad_norm.detach().cpu()),
                **policy_info}

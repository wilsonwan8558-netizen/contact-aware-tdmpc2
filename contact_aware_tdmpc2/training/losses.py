"""Research G13 joint TD-MPC2/force loss, with no inference-path changes."""
from __future__ import annotations

import torch
import torch.nn.functional as F

from ..tdmpc2.world_model import soft_cross_entropy


def g13_loss_terms(agent, batch):
    """Mirror research g13_model.G13Agent.loss_terms exactly.

    Force target is each *next completed RL interval's* max-substep distal
    contact force. The head reads the imagined post-transition latent.
    """
    observations, actions, rewards, terminated, forces = batch
    rho = float(agent.config["rho"])
    weights = torch.pow(torch.tensor(rho, device=agent.device),
                        torch.arange(agent.horizon, device=agent.device))
    with torch.no_grad():
        next_latent_targets = agent.model.encode(observations[1:])
        td_targets = agent._td_target(next_latent_targets, rewards, terminated)
    agent.model.train(True)
    latent = agent.model.encode(observations[0])
    latent_rollout = [latent]
    consistency_loss = torch.zeros((), device=agent.device)
    for step in range(agent.horizon):
        latent = agent.model.next(latent, actions[step])
        consistency_loss = consistency_loss + weights[step] * F.mse_loss(
            latent, next_latent_targets[step])
        latent_rollout.append(latent)
    latent_rollout_tensor = torch.stack(latent_rollout, dim=0)
    rollout_latent = latent_rollout_tensor[:-1]
    reward_logits = agent.model.reward(rollout_latent, actions)
    q_logits = agent.model.q(rollout_latent, actions, reduction="all")
    termination_logits = agent.model.termination(latent_rollout_tensor[1:], logits=True)
    force_predictions = agent.model.force(latent_rollout_tensor[1:])
    reward_element = soft_cross_entropy(
        reward_logits, rewards, agent.model.num_bins,
        agent.model.value_min, agent.model.value_max).mean(dim=(1, 2))
    value_element = soft_cross_entropy(
        q_logits, td_targets.unsqueeze(0).expand(agent.model.num_q, -1, -1, -1),
        agent.model.num_bins, agent.model.value_min,
        agent.model.value_max).mean(dim=(0, 2, 3))
    force_element = F.smooth_l1_loss(force_predictions, forces,
                                     beta=1.0, reduction="none").mean(dim=(1, 2))
    terms = {
        "consistency_loss": consistency_loss / agent.horizon,
        "reward_loss": (reward_element * weights).sum() / agent.horizon,
        "value_loss": (value_element * weights).sum() / agent.horizon,
        "termination_loss": F.binary_cross_entropy_with_logits(termination_logits, terminated),
        "force_loss": (force_element * weights).sum() / agent.horizon,
    }
    original = sum(float(agent.config[name.replace("_loss", "_coef")]) * terms[name]
                   for name in ("consistency_loss", "reward_loss", "value_loss", "termination_loss"))
    terms["original_total_loss"] = original
    terms["total_loss"] = original + agent.lambda_force_train * terms["force_loss"]
    return terms, latent_rollout_tensor

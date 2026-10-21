import os
import unittest
import numpy as np
import torch

from contact_aware_tdmpc2.tdmpc2.checkpoint import load_g13


def test_trusted_g13_checkpoint_if_supplied():
    path = os.environ.get("CONTACT_AWARE_CHECKPOINT")
    if not path:
        raise unittest.SkipTest("Set CONTACT_AWARE_CHECKPOINT to test trusted 63-MB G13 file")
    agent, config = load_g13(path, device="cpu")
    assert agent.observation_dim == 22
    assert agent.action_dim == 2
    assert hasattr(agent.model, "force_head")
    assert config["planning"]["num_samples"] == 512
    # CPU reference computed with the original G13 source and this checkpoint
    # under the pinned PyTorch 2.7.1 environment, not from a rollout log.
    torch.set_num_threads(1)
    torch.manual_seed(73)
    observation = np.linspace(-0.5, 0.5, 22, dtype=np.float32)
    action = agent.act(observation, first_step=True, eval_mode=True)
    np.testing.assert_allclose(action, [-0.9963191, -0.9924057], atol=1e-6)

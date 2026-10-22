import numpy as np
import torch

from contact_aware_tdmpc2.controller import ContactAwareController
from contact_aware_tdmpc2.runtime_checks import CONFIG_ROOT
from contact_aware_tdmpc2.safety.fuzzy_inference import FrozenFuzzyRisk


def test_diagnostics_without_checkpoint():
    class Model:
        def encode(self, observation):
            return observation

        def next(self, latent, action):
            assert action.shape == (1, 2)
            return latent

        def force(self, next_latent):
            return torch.tensor([[1.25]], dtype=torch.float32)

    class Agent:
        device = torch.device("cpu")
        model = Model()

        def act(self, observation, *, first_step, eval_mode):
            assert first_step and eval_mode
            return np.array([0.8, -0.4], dtype=np.float32)

        def _tensor_observation(self, observation):
            return torch.as_tensor(observation).unsqueeze(0)

    controller = ContactAwareController.__new__(ContactAwareController)
    controller.agent = Agent()
    controller.fuzzy = FrozenFuzzyRisk(CONFIG_ROOT / "fuzzy_safety.yaml")
    controller.first_step = True
    observation = np.zeros(22, dtype=np.float32)
    observation[14:17] = [0.2, -0.1, 0.3]
    action, diagnostics = controller.step(observation, current_force=0.4)
    assert not controller.first_step
    assert set(diagnostics) == {
        "nominal_action", "predicted_force", "wall_clearance",
        "fuzzy_memberships", "rule_strengths", "rho", "rho_eff", "safe_action",
    }
    assert diagnostics["predicted_force"] == 1.25
    assert abs(diagnostics["wall_clearance"] + 0.1) < 1e-7
    assert diagnostics["rule_strengths"].keys() == {f"R{i}" for i in range(1, 11)}
    np.testing.assert_array_equal(action, diagnostics["safe_action"])
    assert action[0] <= diagnostics["nominal_action"][0]
    assert action[1] == diagnostics["nominal_action"][1]

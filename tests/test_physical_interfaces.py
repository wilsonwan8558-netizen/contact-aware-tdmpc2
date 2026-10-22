import numpy as np

from contact_aware_tdmpc2.interfaces.robot_interface import RobotInterface
from examples import phantom_integration_skeleton as phantom


def test_shadow_uses_separate_force_interface_without_actuation(monkeypatch):
    monkeypatch.setattr(phantom, "assert_bundled_eve_origin", lambda: None)
    assert "get_force" not in RobotInterface.__dict__

    class Robot(RobotInterface):
        sent = False

        def get_tracking_points(self):
            return np.zeros((5, 2), dtype=np.float32)

        def get_rotation(self):
            return 0.0

        def get_target(self):
            return np.zeros(2, dtype=np.float32)

        def send_action(self, insertion_velocity, rotation_velocity):
            self.sent = True

    class Force:
        calls = 0

        def read_force(self):
            self.calls += 1
            return 1.25

    class Adapter:
        def build(self, robot):
            assert isinstance(robot, Robot)
            return np.zeros(22, dtype=np.float32)

    class Controller:
        def step(self, observation, current_force):
            assert observation.shape == (22,)
            assert current_force == 1.25
            return np.array([0.5, -0.25], dtype=np.float32), {"rho": 0.2}

    robot, force = Robot(), Force()
    result = phantom.shadow_step(Controller(), robot, force, Adapter())
    assert force.calls == 1
    assert not robot.sent
    np.testing.assert_allclose(result["candidate_simulator_velocity"],
                               [25.0, -0.785], atol=1e-6)

"""Non-operational sketch: implement adapters and interlocks before hardware use."""

from __future__ import annotations

from contact_aware_tdmpc2 import ContactAwareController
from contact_aware_tdmpc2.env.action_adapter import to_device_velocity
from contact_aware_tdmpc2.interfaces.observation_adapter import ObservationAdapter
from contact_aware_tdmpc2.interfaces.robot_interface import RobotInterface


def shadow_step(controller: ContactAwareController, robot: RobotInterface,
                observation_adapter: ObservationAdapter) -> dict:
    """Compute diagnostics only; deliberately does not send a robot action."""
    observation = observation_adapter.build(robot)
    force = robot.get_force()
    safe_action, diagnostics = controller.step(observation, force)
    diagnostics["candidate_simulator_velocity"] = to_device_velocity(safe_action)
    # Do not call robot.send_action here. Physical speed limits, unit mapping,
    # latency compensation, emergency stop, and validation are not supplied.
    return diagnostics

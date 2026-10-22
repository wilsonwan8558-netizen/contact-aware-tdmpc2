"""Non-operational sketch: implement adapters and interlocks before hardware use."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contact_aware_tdmpc2 import ContactAwareController
from contact_aware_tdmpc2.env.action_adapter import to_device_velocity
from contact_aware_tdmpc2.interfaces.force_interface import ForceInterface
from contact_aware_tdmpc2.interfaces.observation_adapter import ObservationAdapter
from contact_aware_tdmpc2.interfaces.robot_interface import RobotInterface
from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin


def shadow_step(controller: ContactAwareController, robot: RobotInterface,
                force_interface: ForceInterface,
                observation_adapter: ObservationAdapter) -> dict:
    """Compute diagnostics only; deliberately does not send a robot action."""
    assert_bundled_eve_origin()
    observation = observation_adapter.build(robot)
    force = force_interface.read_force()
    safe_action, diagnostics = controller.step(observation, force)
    diagnostics["candidate_simulator_velocity"] = to_device_velocity(safe_action)
    # Do not call robot.send_action here. Physical speed limits, unit mapping,
    # latency compensation, emergency stop, and validation are not supplied.
    return diagnostics

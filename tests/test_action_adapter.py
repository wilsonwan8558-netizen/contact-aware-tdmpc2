import numpy as np

from contact_aware_tdmpc2.env.action_adapter import to_device_velocity


def test_frozen_symmetric_scaling():
    np.testing.assert_allclose(to_device_velocity(np.array([1, -1], np.float32)),
                               [50.0, -3.14], atol=1e-6)
    np.testing.assert_allclose(to_device_velocity(np.array([-1, 1], np.float32)),
                               [-50.0, 3.14], atol=1e-6)
    np.testing.assert_allclose(to_device_velocity(np.array([0, 0], np.float32)),
                               [0.0, 0.0], atol=1e-6)

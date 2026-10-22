import numpy as np

from contact_aware_tdmpc2.env.observation import OBSERVATION_DIM, OBSERVATION_NAMES
from contact_aware_tdmpc2.interfaces.observation_adapter import assemble_observation


def test_order_and_shape():
    assert OBSERVATION_DIM == 22
    assert len(OBSERVATION_NAMES) == len(set(OBSERVATION_NAMES)) == 22
    assert OBSERVATION_NAMES == (
        "p0_x", "p0_y", "p1_x", "p1_y", "p2_x", "p2_y", "p3_x", "p3_y",
        "p4_x", "p4_y", "target_x", "target_y", "sin_device_rotation",
        "cos_device_rotation", "d0_normalized", "d1_normalized",
        "d2_normalized", "sin_delta_theta", "cos_delta_theta",
        "kappa_distal_normalized", "r_local_normalized", "direction_valid",
    )
    base = np.arange(14, dtype=np.float32)
    geometry = np.arange(14, 22, dtype=np.float32)
    result = assemble_observation(base, geometry)
    assert result.shape == (22,)
    assert result.dtype == np.float32
    np.testing.assert_array_equal(result, np.arange(22, dtype=np.float32))

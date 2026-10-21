import numpy as np

from contact_aware_tdmpc2.safety.safety_filter import effective_risk, filter_action_g161


def test_deadband_and_positive_insertion():
    assert effective_risk(0.0) == 0.0
    assert effective_risk(0.10) == 0.0
    assert effective_risk(1.0) == 1.0
    nominal = np.array([0.8, -0.4], dtype=np.float32)
    np.testing.assert_array_equal(filter_action_g161(nominal, 0.10), nominal)
    result = filter_action_g161(nominal, 0.55)
    assert abs(float(result[0]) - 0.4) < 1e-7
    assert result[1] == nominal[1]


def test_nonpositive_translation_and_rotation_unchanged():
    for insertion in (-0.5, 0.0):
        nominal = np.array([insertion, 0.7], dtype=np.float32)
        for rho in (0.0, 0.5, 1.0):
            np.testing.assert_array_equal(filter_action_g161(nominal, rho), nominal)

from pathlib import Path
import hashlib

from contact_aware_tdmpc2.safety.fuzzy_inference import (
    FrozenFuzzyRisk, left_shoulder, right_shoulder, triangle)

CONFIG = Path(__file__).resolve().parents[1] / "configs/fuzzy_safety.yaml"


def test_known_memberships():
    assert left_shoulder(0.0, 1.0, 2.0) == 1.0
    assert left_shoulder(2.0, 1.0, 2.0) == 0.0
    assert triangle(2.0, 1.0, 2.0, 3.0) == 1.0
    assert right_shoulder(2.0, 1.0, 2.0) == 1.0
    result = FrozenFuzzyRisk(CONFIG).evaluate(0.0, 0.0, 0.1)
    assert result["rule_strengths"]["R1"] == 1.0
    assert abs(result["rho"] - 0.09259164292497626) < 1e-14


def test_packaged_config_mirrors_source():
    root = Path(__file__).resolve().parents[1]
    for name in ("simulation.yaml", "tdmpc2.yaml", "fuzzy_safety.yaml"):
        source = (root / "configs" / name).read_bytes()
        packaged = (root / "contact_aware_tdmpc2/configs" / name).read_bytes()
        assert hashlib.sha256(source).digest() == hashlib.sha256(packaged).digest()

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from contact_aware_tdmpc2 import runtime_checks as checks


def test_bundled_eve_origin_accepts_only_expected_package(monkeypatch, tmp_path):
    expected = (checks.REPOSITORY_ROOT / "eve" / "__init__.py").resolve()
    monkeypatch.setattr(checks.importlib, "import_module",
                        lambda name: SimpleNamespace(__file__=str(expected)))
    assert checks.assert_bundled_eve_origin() == expected
    wrong = tmp_path / "old_research" / "eve" / "__init__.py"
    monkeypatch.setattr(checks.importlib, "import_module",
                        lambda name: SimpleNamespace(__file__=str(wrong)))
    with pytest.raises(RuntimeError, match="Wrong eve package"):
        checks.assert_bundled_eve_origin()


def test_fuzzy_frozen_values_and_mirror(monkeypatch, tmp_path):
    original = checks.assert_fuzzy_config()
    for path, changed in (
        (("rho_0",), 0.11),
        (("force_reference_N", "Q75"), 1.1),
        (("clearance_reference_normalized", "Q25"), -0.6),
        (("F_lim_N",), 3.7),
        (("inference", "rho_grid", "step"), 0.002),
    ):
        altered = deepcopy(original)
        node = altered
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = changed
        with pytest.raises(RuntimeError, match="Frozen config mismatch"):
            checks.assert_fuzzy_config(altered)
    altered = deepcopy(original)
    altered["rules"][0]["id"] = "R99"
    with pytest.raises(RuntimeError, match="Frozen config mismatch"):
        checks.assert_fuzzy_config(altered)
    altered = deepcopy(original)
    altered["rules"].pop()
    with pytest.raises(RuntimeError, match="Frozen config mismatch"):
        checks.assert_fuzzy_config(altered)

    package_config = tmp_path / "fuzzy_safety.yaml"
    package_config.write_text(yaml.safe_dump(original))
    monkeypatch.setattr(checks, "CONFIG_ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="source/package config mismatch"):
        altered = deepcopy(original)
        altered["rho_0"] = 0.11
        package_config.write_text(yaml.safe_dump(altered))
        checks.assert_fuzzy_config()


def test_simulation_frozen_values_and_mirror(monkeypatch, tmp_path):
    args = dict(implementation_dt_s=0.006, implementation_friction=0.001,
                implementation_substeps=22)
    original = checks.assert_simulation_config(**args)
    for key, changed in (("implementation_dt_s", 0.007),
                         ("implementation_friction", 0.002),
                         ("implementation_substeps", 21)):
        altered = dict(args)
        altered[key] = changed
        with pytest.raises(RuntimeError, match="Frozen config mismatch"):
            checks.assert_simulation_config(**altered)
    package_config = tmp_path / "simulation.yaml"
    package_config.write_text(yaml.safe_dump(original))
    monkeypatch.setattr(checks, "CONFIG_ROOT", tmp_path)
    for path, changed in (
        (("solver", "dt_s"), 0.007),
        (("solver", "mu"), 0.002),
        (("environment", "friction"), 0.002),
        (("control", "sofa_substeps_per_step"), 21),
    ):
        altered = deepcopy(original)
        altered[path[0]][path[1]] = changed
        package_config.write_text(yaml.safe_dump(altered))
        with pytest.raises(RuntimeError):
            checks.assert_simulation_config(**args)

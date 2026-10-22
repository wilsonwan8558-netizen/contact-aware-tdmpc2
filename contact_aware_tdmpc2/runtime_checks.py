"""Fail-fast checks for vendored imports and frozen configuration mirrors.

The implementation and the values below are frozen. YAML is a reviewed mirror,
not a way to tune the released controller or simulator at runtime.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parent
CONFIG_ROOT = PACKAGE_ROOT / "configs"

FROZEN_FORCE_QUANTILES = {
    "Q75": 1.0855235286650953,
    "Q90": 2.1265156799878246,
    "Q95": 3.685331040756903,
    "Q99": 7.466568793559142,
}
FROZEN_CLEARANCE_QUANTILES = {
    "Q25": -0.6142929047346115,
    "Q50": -0.03466621972620487,
    "Q75": 0.08420414663851261,
}
FROZEN_F_LIM_N = 3.685331040756903
FROZEN_RHO_0 = 0.10
FROZEN_RHO_GRID = {"start": 0.0, "stop": 1.0, "step": 0.001, "point_count": 1001}
FROZEN_INPUT_MEMBERSHIPS = {
    "current_force": {
        "LOW": ["left_shoulder", "Q75", "Q90"],
        "MEDIUM": ["triangle", "Q75", "Q95", "Q99"],
        "HIGH": ["right_shoulder", "Q90", "Q95"],
    },
    "predicted_force": {
        "LOW": ["left_shoulder", "Q75", "Q90"],
        "MEDIUM": ["triangle", "Q75", "Q95", "Q99"],
        "HIGH": ["right_shoulder", "Q90", "Q95"],
    },
    "clearance": {
        "SMALL": ["left_shoulder", "Q25", "Q50"],
        "MEDIUM": ["triangle", "Q25", "Q50", "Q75"],
        "LARGE": ["right_shoulder", "Q50", "Q75"],
    },
}
FROZEN_OUTPUT_MEMBERSHIPS = {
    "NONE": {"shape": "trapezoid", "points": [0.0, 0.0, 0.1, 0.25]},
    "MILD": {"shape": "triangle", "points": [0.1, 0.4, 0.7]},
    "STRONG": {"shape": "trapezoid", "points": [0.55, 0.75, 1.0, 1.0]},
}
FROZEN_SOFA_DT_S = 0.006
FROZEN_SOFA_FRICTION = 0.001
FROZEN_SOFA_SUBSTEPS = 22
FROZEN_RULES = (
    ("R1", (("current", "LOW"), ("predicted", "LOW"), ("clearance", "LARGE")), "NONE"),
    ("R2", (("current", "LOW"), ("predicted", "LOW"), ("clearance", "MEDIUM")), "MILD"),
    ("R3", (("predicted", "MEDIUM"),), "MILD"),
    ("R4", (("current", "MEDIUM"), ("predicted", "LOW")), "MILD"),
    ("R5", (("predicted", "HIGH"),), "STRONG"),
    ("R6", (("current", "HIGH"),), "STRONG"),
    ("R7", (("current", "MEDIUM"), ("predicted", "MEDIUM")), "STRONG"),
    ("R8", (("clearance", "SMALL"), ("predicted", "MEDIUM")), "STRONG"),
    ("R9", (("clearance", "SMALL"), ("predicted", "HIGH")), "STRONG"),
    ("R10", (("clearance", "SMALL"), ("current", "LOW"), ("predicted", "LOW")), "MILD"),
)


def assert_bundled_eve_origin() -> Path:
    """Reject an older editable stEVE import before creating a SOFA scene."""
    expected = (REPOSITORY_ROOT / "eve" / "__init__.py").resolve()
    try:
        eve = importlib.import_module("eve")
    except ImportError as exc:
        raise RuntimeError(f"Bundled eve import failed; expected {expected}") from exc
    origin = getattr(eve, "__file__", None)
    actual = Path(origin).resolve() if origin else None
    if actual != expected:
        raise RuntimeError(
            f"Wrong eve package: imported {actual}; expected bundled {expected}. "
            "Use a clean environment or run the repository entrypoint from its root."
        )
    return actual


def _assert_packaged_mirror(name: str, packaged: dict) -> None:
    source = REPOSITORY_ROOT / "configs" / name
    if source.is_file() and yaml.safe_load(source.read_text()) != packaged:
        raise RuntimeError(f"Frozen source/package config mismatch: {name}")


def _equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"Frozen config mismatch for {label}: {actual!r} != {expected!r}")


def assert_fuzzy_config(config: dict | None = None) -> dict:
    """Verify the packaged fuzzy mirror against frozen method constants."""
    packaged = yaml.safe_load((CONFIG_ROOT / "fuzzy_safety.yaml").read_text())
    _assert_packaged_mirror("fuzzy_safety.yaml", packaged)
    if config is None:
        config = packaged
    _equal(config, packaged, "fuzzy YAML selected at startup")
    _equal(config["rho_0"], FROZEN_RHO_0, "rho_0")
    _equal(config["force_reference_N"], FROZEN_FORCE_QUANTILES, "force quantiles")
    _equal(config["clearance_reference_normalized"], FROZEN_CLEARANCE_QUANTILES,
           "clearance quantiles")
    _equal(config["F_lim_N"], FROZEN_F_LIM_N, "F_lim")
    _equal(config["F_lim_N"], config["force_reference_N"]["Q95"], "F_lim vs Q95")
    _equal(config["inference"]["rho_grid"], FROZEN_RHO_GRID, "fuzzy rho grid")
    _equal(config["input_memberships"], FROZEN_INPUT_MEMBERSHIPS,
           "fuzzy input memberships")
    _equal(config["output"], FROZEN_OUTPUT_MEMBERSHIPS,
           "fuzzy output memberships")
    rules = tuple((row["id"], tuple(tuple(term) for term in row["antecedents"]),
                   row["consequent"]) for row in config["rules"])
    _equal(rules, FROZEN_RULES, "fuzzy rule count/identities/content")
    return config


def assert_simulation_config(*, implementation_dt_s: float,
                             implementation_friction: float,
                             implementation_substeps: int) -> dict:
    """Verify SOFA values without altering the scene or action calculations."""
    config = yaml.safe_load((CONFIG_ROOT / "simulation.yaml").read_text())
    _assert_packaged_mirror("simulation.yaml", config)
    _equal(implementation_dt_s, FROZEN_SOFA_DT_S, "implementation SOFA dt")
    _equal(implementation_friction, FROZEN_SOFA_FRICTION,
           "implementation SOFA friction")
    _equal(implementation_substeps, FROZEN_SOFA_SUBSTEPS,
           "implementation SOFA substeps")
    _equal(config["solver"]["dt_s"], implementation_dt_s, "config SOFA dt")
    _equal(config["solver"]["mu"], implementation_friction, "solver friction")
    _equal(config["environment"]["friction"], implementation_friction,
           "environment friction")
    _equal(config["control"]["sofa_substeps_per_step"], implementation_substeps,
           "SOFA substep count")
    return config

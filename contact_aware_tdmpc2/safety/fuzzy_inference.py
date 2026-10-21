"""Frozen, deterministic Mamdani fuzzy risk and translation-only filter."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml


def left_shoulder(x: float, flat_to: float, zero_at: float) -> float:
    if not flat_to < zero_at:
        raise ValueError("left-shoulder breakpoints are not increasing")
    return float(np.clip((zero_at - x) / (zero_at - flat_to), 0.0, 1.0))


def triangle(x: float, left: float, peak: float, right: float) -> float:
    if not left < peak < right:
        raise ValueError("triangle breakpoints are not strictly increasing")
    return float(max(0.0, min((x - left) / (peak - left),
                              (right - x) / (right - peak))))


def right_shoulder(x: float, zero_to: float, flat_at: float) -> float:
    if not zero_to < flat_at:
        raise ValueError("right-shoulder breakpoints are not increasing")
    return float(np.clip((x - zero_to) / (flat_at - zero_to), 0.0, 1.0))


def trapezoid_grid(grid: np.ndarray, points: list[float]) -> np.ndarray:
    a, b, c, d = map(float, points)
    if not (a <= b <= c <= d) or a == d:
        raise ValueError("invalid output trapezoid")
    if a == b:
        rising = (grid >= a).astype(np.float64)
    else:
        rising = np.clip((grid - a) / (b - a), 0.0, 1.0)
    if c == d:
        falling = (grid <= d).astype(np.float64)
    else:
        falling = np.clip((d - grid) / (d - c), 0.0, 1.0)
    return np.minimum(rising, falling)


def triangle_grid(grid: np.ndarray, points: list[float]) -> np.ndarray:
    a, b, c = map(float, points)
    if not a < b < c:
        raise ValueError("invalid output triangle")
    return np.maximum(0.0, np.minimum((grid - a) / (b - a),
                                       (c - grid) / (c - b)))


class FrozenFuzzyRisk:
    def __init__(self, config_path: Path):
        self.membership = yaml.safe_load(Path(config_path).read_text())
        self.rules = self.membership["rules"]
        inference = self.membership["inference"]
        if (inference["method"] != "Mamdani" or inference["AND"] != "min"
                or inference["OR"] != "max" or inference["implication"] != "min"
                or inference["aggregation"] != "max" or inference["defuzzification"] != "centroid"
                or inference["rho_grid"] != {"start": 0.0, "stop": 1.0, "step": 0.001,
                                              "point_count": 1001}):
            raise RuntimeError("G16 frozen fuzzy inference changed")
        self.grid = np.arange(1001, dtype=np.float64) / 1000.0
        self.outputs = {}
        for name, definition in self.membership["output"].items():
            if definition["shape"] == "trapezoid":
                self.outputs[name] = trapezoid_grid(self.grid, definition["points"])
            elif definition["shape"] == "triangle":
                self.outputs[name] = triangle_grid(self.grid, definition["points"])
            else:
                raise ValueError(f"Unexpected output membership shape: {name}")
        if len(self.rules) != 10 or {row["id"] for row in self.rules} != {
                f"R{i}" for i in range(1, 11)}:
            raise RuntimeError("G16 must contain exactly rules R1-R10")

    def evaluate(self, current_force: float, predicted_force: float,
                 clearance: float) -> dict:
        if not np.all(np.isfinite([current_force, predicted_force, clearance])):
            raise ValueError("G16 fuzzy input is nonfinite")
        if current_force < 0 or predicted_force < 0:
            raise ValueError("G16 force input is negative")
        force = self.membership["force_reference_N"]
        geo = self.membership["clearance_reference_normalized"]
        q75, q90, limit, q99 = (force[key] for key in ("Q75", "Q90", "Q95", "Q99"))
        q25d, q50d, q75d = (geo[key] for key in ("Q25", "Q50", "Q75"))

        def force_sets(value: float) -> dict:
            return {"LOW": left_shoulder(value, q75, q90),
                    "MEDIUM": triangle(value, q75, limit, q99),
                    "HIGH": right_shoulder(value, q90, limit)}

        memberships = {"current": force_sets(current_force),
                       "predicted": force_sets(predicted_force),
                       "clearance": {"SMALL": left_shoulder(clearance, q25d, q50d),
                                     "MEDIUM": triangle(clearance, q25d, q50d, q75d),
                                     "LARGE": right_shoulder(clearance, q50d, q75d)}}
        strengths = {}
        aggregate = np.zeros_like(self.grid)
        for rule in self.rules:
            strength = min(memberships[source][label] for source, label in rule["antecedents"])
            strengths[rule["id"]] = strength
            aggregate = np.maximum(aggregate, np.minimum(strength, self.outputs[rule["consequent"]]))
        area = float(np.sum(aggregate))
        if area <= 0:
            raise RuntimeError("G16 fuzzy rule base did not fire")
        rho = float(np.sum(self.grid * aggregate) / area)
        if not 0 <= rho <= 1:
            raise RuntimeError("G16 defuzzified risk is outside [0,1]")
        return {"memberships": memberships, "rule_strengths": strengths, "rho": rho}

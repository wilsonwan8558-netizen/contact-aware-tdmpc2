"""Explicit vessel assets and registration for G13 retraining.

The original scene is unchanged. A new mesh and radiused centerlines must
arrive in one declared millimetre frame; transforms are explicit, never
inferred from bounds or silently rescaled.
"""
from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np
import yaml


def _vector(value, size: int, name: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be {size} finite numbers")
    return result


def _asset(value: str, base: Path, name: str, *, require_assets: bool) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    path = Path(value).expanduser()
    path = (path if path.is_absolute() else base / path).resolve()
    if require_assets and not path.is_file():
        raise FileNotFoundError(f"{name} not found: {path}")
    return str(path)


def load_scene_config(path: str | Path, *, require_assets: bool = True) -> dict:
    source = Path(path).expanduser().resolve()
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("scene_version") != 1:
        raise ValueError("Scene YAML must have scene_version: 1")
    scene = dict(raw)
    kind = scene.get("kind")
    if kind not in ("original_aortic_arch", "from_mesh"):
        raise ValueError("scene.kind must be original_aortic_arch or from_mesh")
    _vector(scene.get("image_rot_zx_deg"), 2, "image_rot_zx_deg")
    _vector(scene.get("image_center_mm"), 3, "image_center_mm")
    if scene.get("field_of_view_mm") is not None:
        fov = _vector(scene["field_of_view_mm"], 2, "field_of_view_mm")
        if np.any(fov <= 0):
            raise ValueError("field_of_view_mm must be positive")
    target = scene.get("target")
    if not isinstance(target, dict) or target.get("mode") not in ("centerline_random", "manual"):
        raise ValueError("target.mode must be centerline_random or manual")
    if float(target.get("threshold_mm", 0)) <= 0:
        raise ValueError("target.threshold_mm must be positive")
    if target["mode"] == "centerline_random":
        if not isinstance(target.get("branches"), list) or not target["branches"]:
            raise ValueError("target.branches must be nonempty")
    else:
        if not isinstance(target.get("coordinates_mm"), list) or not target["coordinates_mm"]:
            raise ValueError("manual target.coordinates_mm must be nonempty")
        for coordinate in target["coordinates_mm"]:
            _vector(coordinate, 3, "target coordinate")
    if kind == "original_aortic_arch":
        if not isinstance(scene.get("vessel_seed"), int):
            raise ValueError("original vessel_seed must be an integer")
        if target["mode"] != "centerline_random":
            raise ValueError("original-vessel reproduction requires centerline_random targets")
    else:
        scene["mesh_path"] = _asset(scene.get("mesh_path"), source.parent,
                                    "mesh_path", require_assets=require_assets)
        scene["centerline_path"] = _asset(scene.get("centerline_path"), source.parent,
                                          "centerline_path", require_assets=require_assets)
        _vector(scene.get("insertion_position_mm"), 3, "insertion_position_mm")
        direction = _vector(scene.get("insertion_direction_unit"), 3, "insertion_direction_unit")
        if not np.isclose(np.linalg.norm(direction), 1, atol=1e-4):
            raise ValueError("insertion_direction_unit must have length 1")
        registration = scene.get("registration")
        if not isinstance(registration, dict):
            raise ValueError("registration must be explicit")
        scale = float(registration.get("scale_uniform", 0))
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError("registration.scale_uniform must be positive")
        _vector(registration.get("rotation_yzx_deg"), 3, "registration.rotation_yzx_deg")
        _vector(registration.get("translation_xyz_mm"), 3, "registration.translation_xyz_mm")
        if require_assets:
            scene["branches"] = load_centerlines(scene["centerline_path"])
            names = {branch["name"] for branch in scene["branches"]}
            if target["mode"] == "centerline_random" and not set(target["branches"]) <= names:
                raise ValueError("target.branches must exist in centerline file")
            if target["mode"] == "manual":
                for point in target["coordinates_mm"]:
                    sample = np.asarray(point, dtype=np.float64)
                    inside = False
                    for branch in scene["branches"]:
                        points = np.asarray(branch["coordinates_mm"], dtype=np.float64)
                        radii = np.asarray(branch["radii_mm"], dtype=np.float64)
                        vectors = np.diff(points, axis=0)
                        t = np.clip(np.einsum("ij,ij->i", sample-points[:-1], vectors) /
                                    np.einsum("ij,ij->i", vectors, vectors), 0, 1)
                        nearest = points[:-1] + t[:, None]*vectors
                        local_radius = radii[:-1] + t*(radii[1:]-radii[:-1])
                        inside = inside or bool(np.any(np.linalg.norm(sample-nearest, axis=1) <= local_radius))
                    if not inside:
                        raise ValueError("manual target is outside represented radiused lumen")
    return scene


def assert_original_scene_compatible(scene: dict, environment: dict) -> None:
    """Reject YAML values that the frozen original-vessel constructor cannot use."""
    if (scene["kind"] != "original_aortic_arch"
            or scene["vessel_seed"] != environment["vessel_seed"]
            or scene["target"]["mode"] != "centerline_random"
            or scene["target"]["branches"] != environment["target_branches"]
            or scene["target"]["threshold_mm"] != environment["target_threshold"]
            or scene["image_rot_zx_deg"] != [20.0, 5.0]
            or scene["image_center_mm"] != [0.0, 0.0, 0.0]
            or scene["field_of_view_mm"] is not None):
        raise ValueError("Original-vessel scene must match frozen G13 defaults exactly")


def load_centerlines(path: str | Path) -> list[dict]:
    source = Path(path)
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    branches = data.get("branches") if isinstance(data, dict) else None
    if not isinstance(branches, list) or not branches:
        raise ValueError("centerline file must have nonempty branches list")
    names = []
    for branch in branches:
        if not isinstance(branch, dict) or not isinstance(branch.get("name"), str):
            raise ValueError("each branch needs a name")
        names.append(branch["name"])
        coordinates = np.asarray(branch.get("coordinates_mm"), dtype=np.float64)
        radii = np.asarray(branch.get("radii_mm"), dtype=np.float64)
        if (coordinates.ndim != 2 or coordinates.shape[1] != 3 or len(coordinates) < 2
                or radii.shape != (len(coordinates),) or not np.all(np.isfinite(coordinates))
                or not np.all(np.isfinite(radii)) or np.any(radii <= 0)
                or np.any(np.linalg.norm(np.diff(coordinates, axis=0), axis=1) <= 1e-6)):
            raise ValueError(f"Invalid radiused centerline branch {branch['name']}")
    if len(names) != len(set(names)):
        raise ValueError("centerline branch names must be unique")
    return branches


def build_scene(scene: dict):
    """Return (vessel_tree, target_factory_inputs, fluoroscopy_kwargs)."""
    import eve
    from eve.intervention.vesseltree.util.branch import rotate_array

    projection = {"image_rot_zx": list(scene["image_rot_zx_deg"]),
                  "image_center": list(scene["image_center_mm"]),
                  "field_of_view": scene.get("field_of_view_mm")}
    if scene["kind"] == "original_aortic_arch":
        tree = eve.intervention.vesseltree.AorticArch(
            seed=int(scene["vessel_seed"]), scaling_xyzd=[1.0, 1.0, 1.0, 0.75])
        return tree, projection
    registration = scene["registration"]
    scale = float(registration["scale_uniform"])
    angles = list(registration["rotation_yzx_deg"])
    translation = _vector(registration["translation_xyz_mm"], 3, "translation")

    def point_transform(values):
        return rotate_array(np.asarray(values, dtype=np.float64) * scale,
                            *angles) + translation

    mesh_path = Path(scene["mesh_path"])
    import pyvista as pv
    mesh = pv.read(mesh_path)
    if mesh.n_points < 4 or mesh.n_cells < 1:
        raise ValueError("vessel mesh has insufficient surface geometry")
    mesh.scale([scale, scale, scale], inplace=True)
    mesh.rotate_y(angles[0], inplace=True)
    mesh.rotate_z(angles[1], inplace=True)
    mesh.rotate_x(angles[2], inplace=True)
    mesh.translate(translation, inplace=True)
    with tempfile.NamedTemporaryFile(suffix=".obj", delete=False) as temporary:
        transformed_path = Path(temporary.name)
    try:
        pv.save_meshio(str(transformed_path), mesh)
        branches = [eve.intervention.vesseltree.BranchWithRadii(
            branch["name"], point_transform(branch["coordinates_mm"]),
            np.asarray(branch["radii_mm"], dtype=np.float64) * scale)
            for branch in scene["branches"]]
        tree = eve.intervention.vesseltree.FromMesh(
            mesh=str(transformed_path),
            insertion_position=tuple(point_transform(scene["insertion_position_mm"])),
            insertion_direction=tuple(rotate_array(
                np.asarray(scene["insertion_direction_unit"], dtype=np.float64), *angles)),
            branch_list=branches, scaling_xyz=(1.0, 1.0, 1.0),
            rotation_yzx_deg=(0.0, 0.0, 0.0), rotate_branches=False, rotate_ip=False)
    finally:
        transformed_path.unlink(missing_ok=True)
    return tree, projection


def build_target(scene: dict, tree, fluoroscopy):
    import eve
    target = scene["target"]
    if target["mode"] == "centerline_random":
        return eve.intervention.target.CenterlineRandom(
            vessel_tree=tree, fluoroscopy=fluoroscopy,
            threshold=float(target["threshold_mm"]), branches=list(target["branches"]))
    registration = scene.get("registration")
    points = target["coordinates_mm"]
    if registration:
        from eve.intervention.vesseltree.util.branch import rotate_array
        scale = float(registration["scale_uniform"])
        angles = registration["rotation_yzx_deg"]
        translation = np.asarray(registration["translation_xyz_mm"], dtype=np.float64)
        points = (rotate_array(np.asarray(points, dtype=np.float64)*scale, *angles)
                  + translation).tolist()
    return eve.intervention.target.Manual(
        targets_vessel_cs=points, threshold=float(target["threshold_mm"]),
        fluoroscopy=fluoroscopy)

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
import yaml

from contact_aware_tdmpc2.env.observation import OBSERVATION_NAMES
from contact_aware_tdmpc2.tdmpc2.checkpoint import load_g13
from contact_aware_tdmpc2.training.agent import G13TrainingAgent
from contact_aware_tdmpc2.training.checkpointing import save_checkpoint
from contact_aware_tdmpc2.training.config import build_agent_config, load_training_config
from contact_aware_tdmpc2.training.replay_buffer import G13ReplayBuffer
from contact_aware_tdmpc2.training.scene import (assert_original_scene_compatible,
                                                 load_scene_config)
from scripts.check_new_vessel import inspect_env

ROOT = Path(__file__).resolve().parents[1]


def test_training_config_and_observation_identity():
    config = load_training_config(ROOT / "configs/train_g13.yaml")
    assert config["training"]["total_steps"] == 300000
    assert config["training"]["lambda_force_train"] == .5
    assert config["planning"]["horizon"] == 3
    assert config["planning"]["num_samples"] == 512
    assert len(OBSERVATION_NAMES) == 22
    assert OBSERVATION_NAMES[14:] == (
        "d0_normalized", "d1_normalized", "d2_normalized", "sin_delta_theta",
        "cos_delta_theta", "kappa_distal_normalized", "r_local_normalized",
        "direction_valid")


def test_replay_force_alignment_and_shapes():
    buffer = G13ReplayBuffer(100, 22, 2, 3, 4, seed=1)
    obs = np.arange(5*22, dtype=np.float32).reshape(5, 22)
    action = np.zeros((4, 2), dtype=np.float32)
    buffer.add_episode(obs, action, [0, 1, 2, 3], [False]*4, [1, 2, 3, 4])
    batch = buffer.sample(torch.device("cpu"))
    assert [tuple(x.shape) for x in batch] == [(4, 4, 22), (3, 4, 2),
                                               (3, 4, 1), (3, 4, 1), (3, 4, 1)]
    for column in range(4):
        first_obs = int(batch[0][0, column, 0].item()/22)
        assert batch[4][0, column, 0].item() == first_obs+1
    with pytest.raises(ValueError):
        buffer.add_episode(obs, action, [0, 1, 2, 3], [False]*4, [1, 2])


def test_integrated_force_loss_matches_frozen_huber_definition():
    config = load_training_config(ROOT / "configs/train_g13.yaml")
    agent = G13TrainingAgent(22, 2, build_agent_config(config),
                             episode_length=200, device=torch.device("cpu"))
    torch.manual_seed(7)
    observations = torch.rand(4, 2, 22)
    actions = torch.rand(3, 2, 2)*2-1
    rewards = torch.zeros(3, 2, 1)
    terminated = torch.zeros_like(rewards)
    forces = torch.tensor([[[0.], [1.]], [[2.], [3.]], [[4.], [5.]]])
    terms, latent = agent.loss_terms((observations, actions, rewards, terminated, forces))
    predictions = agent.model.force(latent[1:])
    by_step = torch.nn.functional.smooth_l1_loss(
        predictions, forces, beta=1.0, reduction="none").mean(dim=(1, 2))
    weights = torch.tensor([1.0, 0.5, 0.25])
    torch.testing.assert_close(terms["force_loss"], (by_step*weights).sum()/3)
    torch.testing.assert_close(terms["total_loss"],
                               terms["original_total_loss"] + .5*terms["force_loss"])


def test_g13_training_checkpoint_roundtrip_without_shared_checkpoint(tmp_path):
    config = load_training_config(ROOT / "configs/train_g13.yaml")
    agent = G13TrainingAgent(22, 2, build_agent_config(config),
                             episode_length=200, device=torch.device("cpu"))
    assert hasattr(agent.model, "force_head")
    replay = G13ReplayBuffer(100, 22, 2, 3, 4, seed=1)
    checkpoint = tmp_path / "step_1.pt"
    save_checkpoint(checkpoint, config, agent, replay, 1, 1, 0)
    assert checkpoint.with_suffix(".pt.sha256").is_file()
    loaded, metadata = load_g13(checkpoint, device="cpu")
    assert loaded.observation_dim == 22 and loaded.action_dim == 2
    assert hasattr(loaded.model, "force_head")
    assert metadata["training"]["lambda_force_train"] == .5
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    assert payload["format_version"] == 2
    assert payload["force_target"] == "next-RL-interval max-substep distal contact force, nominal N"
    assert "replay" in payload and "rng_state" in payload


def test_scene_schema_and_asset_validation(tmp_path):
    original = load_scene_config(ROOT / "configs/scenes/original_training_vessel.yaml")
    assert original["kind"] == "original_aortic_arch" and original["vessel_seed"] == 30
    environment = load_training_config(ROOT / "configs/train_g13.yaml")["environment"]
    assert_original_scene_compatible(original, environment)
    modified = {**original, "target": {**original["target"], "threshold_mm": 6.0}}
    with pytest.raises(ValueError, match="frozen G13 defaults"):
        assert_original_scene_compatible(modified, environment)
    (tmp_path / "phantom.stl").write_text("placeholder", encoding="utf-8")
    centerline = {"branches": [{"name": "target", "coordinates_mm": [[0, 0, 0], [0, 10, 0]],
                                "radii_mm": [2, 2]}]}
    (tmp_path / "centerlines.yaml").write_text(yaml.safe_dump(centerline), encoding="utf-8")
    scene = {"scene_version": 1, "kind": "from_mesh", "mesh_path": "phantom.stl",
             "centerline_path": "centerlines.yaml", "insertion_position_mm": [0, 0, 0],
             "insertion_direction_unit": [0, 1, 0],
             "registration": {"scale_uniform": 1.0, "rotation_yzx_deg": [0, 0, 0],
                              "translation_xyz_mm": [0, 0, 0]},
             "image_rot_zx_deg": [20, 5], "image_center_mm": [0, 0, 0],
             "field_of_view_mm": None,
             "target": {"mode": "centerline_random", "branches": ["target"], "threshold_mm": 5}}
    path = tmp_path / "scene.yaml"
    path.write_text(yaml.safe_dump(scene), encoding="utf-8")
    loaded = load_scene_config(path)
    assert loaded["branches"][0]["radii_mm"] == [2, 2]
    scene["target"]["branches"] = ["missing"]
    path.write_text(yaml.safe_dump(scene), encoding="utf-8")
    with pytest.raises(ValueError, match="target.branches"):
        load_scene_config(path)
    scene["target"]["branches"] = ["target"]
    scene["registration"]["scale_uniform"] = 0.0
    path.write_text(yaml.safe_dump(scene), encoding="utf-8")
    with pytest.raises(ValueError, match="scale_uniform"):
        load_scene_config(path)


def test_new_vessel_sanity_helper(monkeypatch):
    import contact_aware_tdmpc2.env.scene_check as scene_check
    monkeypatch.setattr(scene_check, "assert_generic_scene", lambda _env: None)
    class FakeEnv:
        def __init__(self):
            self.env = SimpleNamespace(intervention=SimpleNamespace(
                vessel_tree=SimpleNamespace(branches=["a"]),
                target=SimpleNamespace(coordinates3d=np.array([1., 2., 3.]))),
                _env=SimpleNamespace(observation=SimpleNamespace(observations={
                    "position": SimpleNamespace(wrapped_obs=SimpleNamespace(obs=np.zeros((5, 2))))})),
                raw_action_limits=(np.array([-50., -3.14]), np.array([50., 3.14])))
            self.last_geometry = SimpleNamespace(
                sampled_tracking_2d_mm=np.zeros((3, 2)), clearance_mm=np.ones(3),
                radius_mm=2., direction_valid=1., tracking_alignment_error_mm=0.)
        def reset(self, seed):
            return np.zeros(22, dtype=np.float32), {}
        def step(self, action):
            assert np.array_equal(action, np.zeros(2, dtype=np.float32))
            return np.zeros(22, dtype=np.float32), 0., False, False, {
                "distal_contact_force_max_N": 0., "sofa_substeps": 22}
    assert inspect_env(FakeEnv())["status"] == "PASS"


def test_training_runtime_has_no_old_repo_dependency():
    paths = list((ROOT / "contact_aware_tdmpc2/training").glob("*.py"))
    paths += [ROOT / "scripts/train_g13.py", ROOT / "scripts/check_new_vessel.py",
              ROOT / "scripts/evaluate_g13_checkpoint.py"]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "stEVE_safety_head_1e1be81" not in text
        assert "/home/" not in text and "/tmp/" not in text
        assert "sys.path.insert" not in text or path.parent.name == "scripts"

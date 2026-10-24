"""Train G13 Geometry-Force-TD-MPC2 on a declared vessel scene."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/train_g13.yaml")
    parser.add_argument("--scene-config", required=True)
    parser.add_argument("--device", default=None, help="Explicit cpu or cuda:N; default from config")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--resume", default=None, help="Trusted locally trained format-v2 checkpoint")
    parser.add_argument("--smoke-steps", type=int, default=None,
                        help="Diagnostic 3..200-step run; overrides seed/update/batch settings only for smoke")
    parser.add_argument("--evaluate-at-checkpoints", action="store_true",
                        help="Optional diagnostic evaluation on original YAML seeds; audit a separate holdout for selection")
    args = parser.parse_args()
    from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin
    from contact_aware_tdmpc2.training.config import load_training_config
    from contact_aware_tdmpc2.training.scene import load_scene_config
    from contact_aware_tdmpc2.training.trainer import train

    assert_bundled_eve_origin()
    config = load_training_config(args.config)
    scene = load_scene_config(args.scene_config)
    if args.device is not None:
        config["training"]["device"] = args.device
    if args.seed is not None:
        config["training"]["seed"] = args.seed
    result = train(config, scene, args.output_dir, resume=args.resume,
                   smoke_steps=args.smoke_steps,
                   evaluate_at_checkpoints=args.evaluate_at_checkpoints,
                   scene_config_path=args.scene_config)
    print("G13_TRAIN_RESULT", result, flush=True)


if __name__ == "__main__":
    main()

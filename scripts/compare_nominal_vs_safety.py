"""Five fixed paired demo seeds; explicitly not a scientific evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="Trusted G13 step_260000.pt")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin
    assert_bundled_eve_origin()
    from contact_aware_tdmpc2.tdmpc2.checkpoint import MissingCheckpointError
    from contact_aware_tdmpc2 import ContactAwareController
    from contact_aware_tdmpc2.demo import run_episode
    from contact_aware_tdmpc2.env.g13_env import make_g13_env
    seeds = range(1000, 1005)
    for label, enabled in (("nominal", False), ("fuzzy_safety", True)):
        try:
            controller = ContactAwareController(args.checkpoint, device=args.device)
        except MissingCheckpointError as exc:
            parser.exit(2, f"error: {exc}\n")
        env = make_g13_env(controller.config["environment"])
        try:
            for seed in seeds:
                print(label, run_episode(env, controller, seed,
                                         safety_enabled=enabled), flush=True)
        finally:
            env.close()


if __name__ == "__main__":
    main()

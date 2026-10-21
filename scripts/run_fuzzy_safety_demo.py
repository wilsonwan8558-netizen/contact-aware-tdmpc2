"""Run one frozen G16.1 fuzzy-filter smoke episode."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="Trusted G13 step_260000.pt")
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    from contact_aware_tdmpc2 import ContactAwareController
    from contact_aware_tdmpc2.demo import run_episode
    from contact_aware_tdmpc2.env.g13_env import make_g13_env
    controller = ContactAwareController(args.checkpoint, device=args.device)
    env = make_g13_env(controller.config["environment"])
    try:
        print(run_episode(env, controller, args.seed, safety_enabled=True), flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    main()

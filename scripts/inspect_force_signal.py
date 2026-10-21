"""Inspect one zero-action SOFA step's passive distal force measurements."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1000)
    args = parser.parse_args()
    import numpy as np
    from contact_aware_tdmpc2.env.g13_env import make_g13_env
    from contact_aware_tdmpc2.env.scene_check import assert_generic_scene
    env = make_g13_env()
    try:
        env.reset(seed=args.seed)
        assert_generic_scene(env.env)
        _, _, _, _, info = env.step(np.zeros(2, dtype=np.float32))
        for key in ("distal_contact_force_max_N", "distal_contact_force_mean_N",
                    "distal_force_time_integral_Ns", "distal_contact_substeps",
                    "sofa_substeps"):
            print(f"{key}: {info[key]}")
    finally:
        env.close()


if __name__ == "__main__":
    main()

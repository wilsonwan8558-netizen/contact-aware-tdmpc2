"""One inference call using an already reconstructed 22-D observation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from contact_aware_tdmpc2 import ContactAwareController
from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin
from contact_aware_tdmpc2.tdmpc2.checkpoint import MissingCheckpointError


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    assert_bundled_eve_origin()
    try:
        controller = ContactAwareController(args.checkpoint, device=args.device)
    except MissingCheckpointError as exc:
        parser.exit(2, f"error: {exc}\n")
    controller.reset_episode()
    # Replace this example input with a validated real observation. Zeros are
    # structurally valid but not a meaningful physical operating state.
    observation = np.zeros(22, dtype=np.float32)
    safe_action, diagnostics = controller.step(observation, current_force=0.0)
    print("safe_action", safe_action)
    print("risk", diagnostics["rho"], diagnostics["rho_eff"])


if __name__ == "__main__":
    main()

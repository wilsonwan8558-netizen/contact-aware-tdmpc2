"""One inference call using an already reconstructed 22-D observation."""

from __future__ import annotations

import argparse
import numpy as np

from contact_aware_tdmpc2 import ContactAwareController


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    controller = ContactAwareController(args.checkpoint, device=args.device)
    controller.reset_episode()
    # Replace this example input with a validated real observation. Zeros are
    # structurally valid but not a meaningful physical operating state.
    observation = np.zeros(22, dtype=np.float32)
    safe_action, diagnostics = controller.step(observation, current_force=0.0)
    print("safe_action", safe_action)
    print("risk", diagnostics["rho"], diagnostics["rho_eff"])


if __name__ == "__main__":
    main()

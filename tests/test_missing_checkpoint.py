from pathlib import Path
import subprocess
import sys

import pytest

from contact_aware_tdmpc2.tdmpc2.checkpoint import MissingCheckpointError, load_g13


def test_missing_checkpoint_message(tmp_path):
    missing = tmp_path / "step_260000.pt"
    with pytest.raises(MissingCheckpointError) as captured:
        load_g13(missing, device="cpu")
    message = str(captured.value)
    assert "intentionally not distributed in Git" in message
    assert "step_260000.pt" in message
    assert "b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be" in message
    assert "--checkpoint /path/to/step_260000.pt" in message


def test_nominal_cli_missing_checkpoint_is_concise(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts/run_nominal_demo.py"),
         "--checkpoint", str(tmp_path / "step_260000.pt"), "--device", "cpu"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "intentionally not distributed in Git" in result.stderr
    assert "Traceback" not in result.stderr

"""Read-only preflight for the frozen G13/G16.1 collaborator demos."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


def _expected_checkpoint_sha() -> str:
    text = (ROOT / "configs" / "tdmpc2.yaml").read_text()
    match = re.search(r"^\s*sha256:\s*([0-9a-f]{64})\s*$", text, re.MULTILINE)
    if match is None:
        raise RuntimeError("Frozen checkpoint SHA256 is missing from configs/tdmpc2.yaml")
    return match.group(1)


def run(checkpoint: str | None = None) -> int:
    results: list[tuple[str, str, str]] = []

    def report(name: str, status: str, detail: object) -> None:
        results.append((name, status, str(detail)))

    report("Python version", "PASS" if sys.version_info[:2] == (3, 10) else "FAIL",
           f"{sys.version.split()[0]} ({sys.executable}); expected 3.10.x")

    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        torch = None
        report("PyTorch version", "FAIL", f"import failed: {type(exc).__name__}: {exc}")
        report("CUDA availability", "FAIL", "PyTorch unavailable")
        report("torch CUDA runtime", "FAIL", "PyTorch unavailable")
        report("NVIDIA-visible device", "FAIL", "PyTorch unavailable")
    else:
        version = str(torch.__version__)
        report("PyTorch version", "PASS" if version == "2.7.1+cu128" else "FAIL",
               f"{version}; expected 2.7.1+cu128")
        report("torch CUDA runtime", "PASS" if torch.version.cuda == "12.8" else "FAIL",
               f"{torch.version.cuda}; expected 12.8")
        try:
            available = bool(torch.cuda.is_available())
            count = int(torch.cuda.device_count())
            report("CUDA availability", "PASS" if available else "FAIL",
                   f"is_available={available}, device_count={count}")
            name = torch.cuda.get_device_name(0) if available and count > 0 else "none"
            report("NVIDIA-visible device", "PASS" if available and count > 0 else "FAIL", name)
        except Exception as exc:
            report("CUDA availability", "FAIL", f"query failed: {exc}")
            report("NVIDIA-visible device", "FAIL", f"query failed: {exc}")

    for variable in ("SOFA_ROOT", "SOFAPYTHON3_ROOT"):
        value = os.environ.get(variable)
        status = "PASS" if value and Path(value).is_dir() else ("WARN" if not value else "FAIL")
        report(variable, status, value or "not set; import checks below are decisive")

    try:
        sofa = importlib.import_module("Sofa")
    except Exception as exc:
        report("Sofa import", "FAIL", f"{type(exc).__name__}: {exc}")
    else:
        report("Sofa import", "PASS", getattr(sofa, "__file__", "imported"))

    try:
        runtime = importlib.import_module("SofaRuntime")
        loaded = runtime.importPlugin("BeamAdapter")
        report("BeamAdapter availability", "PASS" if loaded else "FAIL",
               f"SofaRuntime.importPlugin('BeamAdapter') returned {loaded!r}")
    except Exception as exc:
        report("BeamAdapter availability", "FAIL", f"{type(exc).__name__}: {exc}")

    try:
        from contact_aware_tdmpc2.runtime_checks import assert_bundled_eve_origin
        origin = assert_bundled_eve_origin()
    except Exception as exc:
        report("Bundled eve import origin", "FAIL", f"{type(exc).__name__}: {exc}")
    else:
        report("Bundled eve import origin", "PASS", origin)

    if checkpoint is None:
        report("Checkpoint path", "WARN", "not supplied (intentionally excluded from Git)")
        report("Checkpoint SHA256", "WARN", "not checked; pass --checkpoint to verify")
    else:
        path = Path(checkpoint).expanduser().resolve()
        if not path.is_file():
            report("Checkpoint path", "FAIL", f"missing file: {path}")
            report("Checkpoint SHA256", "FAIL", "file unavailable")
        else:
            report("Checkpoint path", "PASS", path)
            try:
                expected = _expected_checkpoint_sha()
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                report("Checkpoint SHA256", "PASS" if digest == expected else "FAIL",
                       f"actual={digest}; expected={expected}")
            except Exception as exc:
                report("Checkpoint SHA256", "FAIL", f"{type(exc).__name__}: {exc}")

    for name, status, detail in results:
        print(f"{status:4} {name}: {detail}")
    failures = sum(status == "FAIL" for _, status, _ in results)
    warnings = sum(status == "WARN" for _, status, _ in results)
    print(f"Environment check: {'FAIL' if failures else 'PASS'} "
          f"({failures} FAIL, {warnings} WARN)")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", help="Optional approved G13 step_260000.pt")
    args = parser.parse_args()
    raise SystemExit(run(args.checkpoint))


if __name__ == "__main__":
    main()

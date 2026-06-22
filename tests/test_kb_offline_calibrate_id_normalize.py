"""The id-normalize calibration must pass with exit 0 (frozen-helper reproducibility)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research" / "kb-offline-eval" / "harness" / "calibrate_id_normalize.py"


def _load():
    spec = importlib.util.spec_from_file_location("calibrate_id_normalize", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_calibration_passes():
    assert _load().main() == 0

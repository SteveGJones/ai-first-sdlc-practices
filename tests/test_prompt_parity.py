"""The prompt-parity drift check must pass (agent managed blocks match prompts.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_prompt_parity_check_passes():
    rc = subprocess.run(
        [sys.executable, str(REPO / "tools/validation/check-prompt-parity.py")],
        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout + rc.stderr

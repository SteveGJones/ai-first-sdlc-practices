"""P2 scoring: QA/test-authoring against the exemplar, in BLIND mode —
the model is never told a bug exists anywhere, just asked to write a
thorough test suite for code it's shown. Fully deterministic, unlike
P1's judge: we can actually run the resulting test file against two real
codebases (the correct exemplar, a deliberately-broken variant) and
check whether it discriminates, the same "prove positive AND negative"
discipline as the REST harness and the client contract.

Requirement on the model's test file (documented to it, not inferred):
must import the game logic via `from app.<module> import ...`, so the
identical test file can be pointed at either codebase's `server/`
directory by prepending that directory to PYTHONPATH — the two variants
under test have identical module layout, differing only in the one
injected bug.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class QAFidelityError(Exception):
    """The test file could not be run at all against a target (not a
    Python file, pytest itself failed to invoke, etc.) — distinct from
    the test file running fine and simply passing/failing."""


@dataclass
class RunResult:
    target_name: str
    exit_code: int
    passed: int
    failed: int
    errors: int
    collection_failed: bool
    stdout_tail: str


# Each counted independently — a single combined regex with every group
# optional and unanchored matches an empty string at position 0 before
# ever reaching the real numbers later in the line (found the hard way,
# see qa_fidelity's own test suite / the retrospective).
_PASSED_RE = re.compile(r"(\d+) passed")
_FAILED_RE = re.compile(r"(\d+) failed")
_ERROR_RE = re.compile(r"(\d+) error")


def _parse_summary(stdout: str) -> tuple[int, int, int]:
    # pytest's final summary line, e.g. "3 passed, 1 failed in 0.12s" or
    # "5 passed in 0.03s" or "2 errors in 0.01s" — search from the end,
    # the summary is always the last non-empty meaningful line.
    tail_lines = [line for line in stdout.splitlines() if line.strip()]
    for line in reversed(tail_lines[-5:] if len(tail_lines) >= 5 else tail_lines):
        p = _PASSED_RE.search(line)
        f = _FAILED_RE.search(line)
        e = _ERROR_RE.search(line)
        if p or f or e:
            return (
                int(p.group(1)) if p else 0,
                int(f.group(1)) if f else 0,
                int(e.group(1)) if e else 0,
            )
    return 0, 0, 0


def run_pytest_against(
    test_file: Path, server_dir: Path, target_name: str, timeout_s: int = 120
) -> RunResult:
    """`server_dir` is a directory containing an `app/` package (e.g.
    exemplar/server or broken-variants/wrong-pot-split/server)."""
    if not test_file.exists():
        raise QAFidelityError(f"test file not found: {test_file}")
    if not (server_dir / "app").is_dir():
        raise QAFidelityError(f"no app/ package under {server_dir}")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(server_dir)
    try:
        proc = subprocess.run(
            [
                "python3",
                "-m",
                "pytest",
                str(test_file),
                "-v",
                "--tb=short",
                "-p",
                "no:cacheprovider",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise QAFidelityError(
            f"pytest against {target_name} timed out after {timeout_s}s"
        ) from exc

    passed, failed, errors = _parse_summary(proc.stdout)
    collection_failed = "ERROR" in proc.stdout and passed == 0 and failed == 0
    return RunResult(
        target_name=target_name,
        exit_code=proc.returncode,
        passed=passed,
        failed=failed,
        errors=errors,
        collection_failed=collection_failed,
        stdout_tail="\n".join(proc.stdout.splitlines()[-40:]),
    )


@dataclass
class QAReport:
    passed_own_check: bool  # ran cleanly (no collection errors) against the exemplar
    all_pass_on_exemplar: bool  # every test passes against known-good code
    catches_planted_bug: bool  # at least one test fails against the broken variant
    exemplar_result: RunResult
    broken_variant_result: RunResult
    details: dict = field(default_factory=dict)


def evaluate(
    test_file: Path, exemplar_server_dir: Path, broken_server_dir: Path
) -> QAReport:
    exemplar_result = run_pytest_against(test_file, exemplar_server_dir, "exemplar")
    broken_result = run_pytest_against(test_file, broken_server_dir, "broken_variant")

    passed_own_check = not exemplar_result.collection_failed
    all_pass_on_exemplar = (
        passed_own_check and exemplar_result.failed == 0 and exemplar_result.errors == 0
    )
    catches_planted_bug = broken_result.failed > 0

    return QAReport(
        passed_own_check=passed_own_check,
        all_pass_on_exemplar=all_pass_on_exemplar,
        catches_planted_bug=catches_planted_bug,
        exemplar_result=exemplar_result,
        broken_variant_result=broken_result,
        details={
            "exemplar": vars(exemplar_result),
            "broken_variant": vars(broken_result),
        },
    )

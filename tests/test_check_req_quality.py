"""Tests for tools/validation/check-req-quality.py REQ-quality linter."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the script as a module
_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validation" / "check-req-quality.py"
spec = importlib.util.spec_from_file_location("check_req_quality", _SCRIPT)
check_req_quality = importlib.util.module_from_spec(spec)
sys.modules["check_req_quality"] = check_req_quality
assert spec.loader is not None
spec.loader.exec_module(check_req_quality)


def test_capability_shaped_req_passes_lint(tmp_path: Path) -> None:
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n"
        "### REQ-good-001\n\n"
        "Auditors MUST be able to verify the published ID registry has not been hand-edited.\n\n"
        "**Module:** P1.SP1.M1\n"
    )
    flags = check_req_quality.lint_file(spec_file)
    assert flags == []


def test_function_shaped_opening_is_flagged(tmp_path: Path) -> None:
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n"
        "### REQ-bad-001\n\n"
        "`my_validator(records)` SHALL detect duplicates.\n\n"
        "**Module:** P1.SP1.M1\n"
    )
    flags = check_req_quality.lint_file(spec_file)
    assert len(flags) == 1
    assert flags[0].req_id == "REQ-bad-001"
    assert "function-shaped" in flags[0].rule.lower()


def test_function_word_outside_backticks_is_flagged(tmp_path: Path) -> None:
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n"
        "### REQ-bad-002\n\n"
        "The system MUST call the function that detects duplicates.\n\n"
        "**Module:** P1.SP1.M1\n"
    )
    flags = check_req_quality.lint_file(spec_file)
    assert len(flags) == 1
    assert "function" in flags[0].rule.lower()


def test_function_word_inside_backticks_is_NOT_flagged(tmp_path: Path) -> None:
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n"
        "### REQ-good-002\n\n"
        "Auditors MUST be able to invoke `function-name` from a CLI.\n\n"
        "**Module:** P1.SP1.M1\n"
    )
    # The word 'function' inside backticks (`function-name`) doesn't count
    flags = check_req_quality.lint_file(spec_file)
    assert flags == []


def test_method_word_outside_backticks_is_flagged(tmp_path: Path) -> None:
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n"
        "### REQ-bad-003\n\n"
        "The bundle MUST expose a method that returns the registry.\n\n"
        "**Module:** P1.SP1.M1\n"
    )
    flags = check_req_quality.lint_file(spec_file)
    assert len(flags) == 1
    assert "method" in flags[0].rule.lower()


def test_walks_corpus_and_returns_all_flags(tmp_path: Path) -> None:
    a = tmp_path / "feat-a"
    a.mkdir()
    (a / "requirements-spec.md").write_text(
        "## Requirements\n\n### REQ-bad-001\n\n`f(x)` SHALL ...\n\n**Module:** M\n"
    )
    b = tmp_path / "feat-b"
    b.mkdir()
    (b / "requirements-spec.md").write_text(
        "## Requirements\n\n### REQ-good-001\n\nUsers MUST be able to ...\n\n**Module:** M\n"
    )
    flags = check_req_quality.lint_corpus(tmp_path)
    assert len(flags) == 1
    assert flags[0].req_id == "REQ-bad-001"


def test_corpus_walk_skips_archive_paths(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "requirements-spec.md").write_text(
        "## Requirements\n\n### REQ-bad-archived-001\n\n`f()` SHALL ...\n\n**Module:** M\n"
    )
    flags = check_req_quality.lint_corpus(tmp_path)
    assert flags == []  # archive skipped


def test_main_advisory_mode_returns_zero_with_flags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Default (advisory) mode: prints flags but exits 0."""
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n### REQ-bad-001\n\n`f()` SHALL ...\n\n**Module:** M\n"
    )
    rc = check_req_quality.main(["check-req-quality.py", str(tmp_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "REQ-bad-001" in captured.out
    assert "advisory" in captured.err.lower()


def test_main_strict_mode_returns_one_with_flags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--strict mode: exits 1 when flags are reported."""
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n### REQ-bad-001\n\n`f()` SHALL ...\n\n**Module:** M\n"
    )
    rc = check_req_quality.main(["check-req-quality.py", str(tmp_path), "--strict"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "REQ-bad-001" in captured.out


def test_main_returns_zero_with_no_flags_in_either_mode(tmp_path: Path) -> None:
    """Both modes exit 0 when no flags are reported."""
    spec_file = tmp_path / "requirements-spec.md"
    spec_file.write_text(
        "## Requirements\n\n### REQ-good-001\n\n"
        "Auditors MUST be able to do X.\n\n"
        "**Module:** M\n"
    )
    assert check_req_quality.main(["check-req-quality.py", str(tmp_path)]) == 0
    assert (
        check_req_quality.main(["check-req-quality.py", str(tmp_path), "--strict"])
        == 0
    )


def test_main_returns_two_when_root_does_not_exist(tmp_path: Path) -> None:
    """Missing root: exit 2 (configuration error, neither mode)."""
    rc = check_req_quality.main(
        ["check-req-quality.py", str(tmp_path / "no-such-dir")]
    )
    assert rc == 2

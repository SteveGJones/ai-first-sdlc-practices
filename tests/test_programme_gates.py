"""Tests for plugins.sdlc-programme.scripts.programme.gates."""
import shutil
from pathlib import Path

from sdlc_programme_scripts.programme.gates import (
    GateResult,
    code_gate,
    design_gate,
    requirements_gate,
)

# Aliased to prevent pytest from auto-collecting `test_gate` (the function
# under test) as if it were a test case. The alias name must NOT start with
# `test_`, or pytest will still try to collect it.
from sdlc_programme_scripts.programme.gates import test_gate as run_test_gate


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_FEATURE = REPO_ROOT / "tests/fixtures/programme/feature-sample"


def _copy_feature(tmp_path: Path) -> Path:
    """Copy the sample feature fixture to tmp_path/specs/sample/."""
    dst = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, dst)
    return dst


def test_requirements_gate_passes_for_valid_spec(tmp_path: Path) -> None:
    """Valid requirements-spec passes the gate."""
    feature_dir = _copy_feature(tmp_path)

    result = requirements_gate(feature_dir, "sample")

    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.errors == []


def test_requirements_gate_fails_when_spec_missing(tmp_path: Path) -> None:
    """Missing requirements-spec.md fails the gate."""
    feature_dir = tmp_path / "specs" / "sample"
    feature_dir.mkdir(parents=True)

    result = requirements_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("requirements-spec.md" in e for e in result.errors)


def test_design_gate_passes_when_all_satisfies_resolve(tmp_path: Path) -> None:
    """Design-spec whose every satisfies reference exists in requirements-spec passes."""
    feature_dir = _copy_feature(tmp_path)

    result = design_gate(feature_dir, "sample")

    assert result.passed is True


def test_design_gate_fails_on_broken_satisfies_reference(tmp_path: Path) -> None:
    """Design-spec satisfying a non-existent REQ-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)

    # Inject a broken reference
    design_spec = feature_dir / "design-spec.md"
    text = design_spec.read_text()
    text = text.replace(
        "**satisfies:** REQ-sample-001",
        "**satisfies:** REQ-sample-999",
    )
    design_spec.write_text(text)

    result = design_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("REQ-sample-999" in e for e in result.errors)


def test_design_gate_fails_when_design_spec_missing(tmp_path: Path) -> None:
    """Missing design-spec.md fails the gate."""
    feature_dir = _copy_feature(tmp_path)
    (feature_dir / "design-spec.md").unlink()

    result = design_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("design-spec.md" in e for e in result.errors)


def test_test_gate_passes_when_all_references_resolve(tmp_path: Path) -> None:
    """Test-spec whose every satisfies reference exists in prior phases passes."""
    feature_dir = _copy_feature(tmp_path)

    result = run_test_gate(feature_dir, "sample")

    assert result.passed is True


def test_test_gate_fails_on_broken_des_reference(tmp_path: Path) -> None:
    """Test-spec referencing a non-existent DES-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)

    test_spec = feature_dir / "test-spec.md"
    text = test_spec.read_text()
    text = text.replace(
        "via DES-sample-001",
        "via DES-sample-999",
    )
    test_spec.write_text(text)

    result = run_test_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("DES-sample-999" in e for e in result.errors)


def test_test_gate_fails_on_broken_req_reference(tmp_path: Path) -> None:
    """Test-spec referencing a non-existent REQ-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)

    test_spec = feature_dir / "test-spec.md"
    text = test_spec.read_text()
    text = text.replace(
        "**satisfies:** REQ-sample-001",
        "**satisfies:** REQ-sample-999",
    )
    test_spec.write_text(text)

    result = run_test_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("REQ-sample-999" in e for e in result.errors)


def test_code_gate_passes_when_test_id_in_test_spec(tmp_path: Path) -> None:
    """Code citing a TEST-ID that exists in test-spec passes the gate."""
    feature_dir = _copy_feature(tmp_path)
    code_text = "def do_thing():\n    # implements: TEST-sample-001\n    return 1\n"

    result = code_gate(feature_dir, "sample", code_text=code_text)

    assert result.passed is True


def test_code_gate_fails_when_test_id_not_in_test_spec(tmp_path: Path) -> None:
    """Code citing a non-existent TEST-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)
    code_text = "def do_thing():\n    # implements: TEST-sample-999\n    return 1\n"

    result = code_gate(feature_dir, "sample", code_text=code_text)

    assert result.passed is False
    assert any("TEST-sample-999" in e for e in result.errors)


def test_code_gate_fails_when_code_has_no_implements_annotation(
    tmp_path: Path,
) -> None:
    """Code without any # implements: annotation fails the gate."""
    feature_dir = _copy_feature(tmp_path)
    code_text = "def do_thing():\n    return 1\n"

    result = code_gate(feature_dir, "sample", code_text=code_text)

    assert result.passed is False
    assert any("annotation" in e.lower() for e in result.errors)

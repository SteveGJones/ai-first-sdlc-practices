"""Tests for plugins.sdlc-programme.scripts.programme.traceability."""
import shutil
from pathlib import Path

import pytest

from sdlc_programme_scripts.programme.traceability import (
    TraceabilityError,
    build_matrix,
    export_csv,
    export_markdown,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_FEATURE = REPO_ROOT / "tests/fixtures/programme/feature-sample"


def _copy_feature(tmp_path: Path) -> Path:
    dst = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, dst)
    return dst


def test_build_matrix_returns_one_row_per_req(tmp_path: Path) -> None:
    """The matrix has one row per REQ with the DES and TEST IDs that satisfy it."""
    feature_dir = _copy_feature(tmp_path)

    matrix = build_matrix(feature_dir, "sample")

    assert len(matrix) == 2
    req_001 = next(row for row in matrix if row.req_id == "REQ-sample-001")
    assert req_001.des_ids == {"DES-sample-001"}
    assert req_001.test_ids == {"TEST-sample-001"}

    req_002 = next(row for row in matrix if row.req_id == "REQ-sample-002")
    assert req_002.des_ids == {"DES-sample-002"}
    assert req_002.test_ids == {"TEST-sample-002"}


def test_export_csv_produces_header_and_rows(tmp_path: Path) -> None:
    """export_csv produces a CSV string with header + one row per REQ."""
    feature_dir = _copy_feature(tmp_path)

    csv_text = export_csv(feature_dir, "sample")

    lines = csv_text.strip().split("\n")
    assert lines[0] == "REQ,DES,TEST"
    assert any(
        "REQ-sample-001,DES-sample-001,TEST-sample-001" in line for line in lines[1:]
    )
    assert any(
        "REQ-sample-002,DES-sample-002,TEST-sample-002" in line for line in lines[1:]
    )


def test_export_markdown_produces_table(tmp_path: Path) -> None:
    """export_markdown produces a markdown table with REQ + DES + TEST columns."""
    feature_dir = _copy_feature(tmp_path)

    md = export_markdown(feature_dir, "sample")

    assert "| REQ | DES | TEST |" in md
    assert "| --- | --- | --- |" in md
    assert "| REQ-sample-001 | DES-sample-001 | TEST-sample-001 |" in md
    assert "| REQ-sample-002 | DES-sample-002 | TEST-sample-002 |" in md


def test_build_matrix_orphan_req_appears_with_empty_des_test(tmp_path: Path) -> None:
    """A REQ with no DES/TEST satisfying it appears in the matrix with empty sets."""
    feature_dir = _copy_feature(tmp_path)
    # Add REQ-sample-003 that nothing satisfies
    req_spec = feature_dir / "requirements-spec.md"
    text = req_spec.read_text()
    text += "\n### REQ-sample-003\nUnsatisfied requirement.\n"
    req_spec.write_text(text)

    matrix = build_matrix(feature_dir, "sample")
    orphan = next(row for row in matrix if row.req_id == "REQ-sample-003")
    assert orphan.des_ids == set()
    assert orphan.test_ids == set()


def test_build_matrix_missing_artefact_raises(tmp_path: Path) -> None:
    """If a phase artefact is missing, traceability cannot be built."""
    feature_dir = _copy_feature(tmp_path)
    (feature_dir / "test-spec.md").unlink()

    with pytest.raises(TraceabilityError, match="test-spec.md"):
        build_matrix(feature_dir, "sample")

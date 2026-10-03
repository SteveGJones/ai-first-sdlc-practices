"""Tests for assured.traceability_validators."""

from sdlc_assured_scripts.assured.ids import IdRecord
from pathlib import Path

from sdlc_assured_scripts.assured.traceability_validators import (
    ValidatorResult,
    annotation_format_integrity,
    backward_coverage,
    change_impact_gate,
    cited_ids_resolve,
    forward_link_integrity,
    id_uniqueness,
    index_regenerability,
    orphan_ids,
)


def test_id_uniqueness_passes_when_all_ids_unique() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-002", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = id_uniqueness(records)
    assert isinstance(result, ValidatorResult)
    assert result.passed is True
    assert result.errors == []


def test_id_uniqueness_fails_on_duplicate() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-001", kind="REQ", source="b.md", satisfies=[]),
    ]
    result = id_uniqueness(records)
    assert result.passed is False
    assert any("duplicate" in e.lower() for e in result.errors)
    assert any("REQ-auth-001" in e for e in result.errors)


def test_cited_ids_resolve_passes_when_all_targets_exist() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = cited_ids_resolve(records)
    assert result.passed is True


def test_cited_ids_resolve_fails_on_missing_target() -> None:
    records = [
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-999"]
        ),
    ]
    result = cited_ids_resolve(records)
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)
    assert any("DES-auth-001" in e for e in result.errors)


def test_orphan_ids_warns_when_req_never_cited() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-002", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = orphan_ids(records)
    assert result.passed is True
    assert any("REQ-auth-002" in w for w in result.warnings)


def test_orphan_ids_warns_for_orphan_test_leaf() -> None:
    """E1: TEST with no citing CODE record is now an orphan warning (widened from v0.1.0)."""
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
        IdRecord(
            id="TEST-auth-001",
            kind="TEST",
            source="c.md",
            satisfies=["REQ-auth-001", "DES-auth-001"],
        ),
    ]
    result = orphan_ids(records)
    assert result.passed is True
    assert any("TEST-auth-001" in w for w in result.warnings)


def test_orphan_ids_widened_warns_on_orphan_test() -> None:
    """E1: orphan_ids now also reports orphan TEST/CODE IDs, not just REQ/DES."""
    records = [
        IdRecord(id="TEST-foo-001", kind="TEST", source="t.md", satisfies=["DES-foo-001"]),
    ]
    result = orphan_ids(records)
    # No CODE record cites TEST-foo-001 → orphan warning
    assert result.passed is True
    assert any("TEST-foo-001" in w for w in result.warnings)


def test_forward_link_integrity_passes_when_chain_intact() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
        IdRecord(
            id="TEST-auth-001",
            kind="TEST",
            source="c.md",
            satisfies=["REQ-auth-001", "DES-auth-001"],
        ),
    ]
    result = forward_link_integrity(records)
    assert result.passed is True


def test_forward_link_integrity_fails_when_des_targets_missing_req() -> None:
    records = [
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-999"]
        ),
    ]
    result = forward_link_integrity(records)
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)


def test_forward_link_integrity_requires_des_to_cite_a_req() -> None:
    """A DES with no satisfies links is a defect under Article 15."""
    records = [
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=[]),
    ]
    result = forward_link_integrity(records)
    assert result.passed is False
    assert any(
        "DES-auth-001" in e and "no satisfies" in e.lower() for e in result.errors
    )


def test_forward_link_integrity_requires_test_to_cite_a_des() -> None:
    """A TEST with no satisfies links is a defect under Article 15."""
    records = [
        IdRecord(id="TEST-auth-001", kind="TEST", source="c.md", satisfies=[]),
    ]
    result = forward_link_integrity(records)
    assert result.passed is False
    assert any(
        "TEST-auth-001" in e and "no satisfies" in e.lower() for e in result.errors
    )


def test_backward_coverage_passes_when_every_req_has_des_test() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
        IdRecord(
            id="TEST-auth-001",
            kind="TEST",
            source="c.md",
            satisfies=["REQ-auth-001", "DES-auth-001"],
        ),
    ]
    result = backward_coverage(records)
    assert result.passed is True


def test_backward_coverage_fails_when_req_has_no_des() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
    ]
    result = backward_coverage(records)
    assert result.passed is False
    assert any("REQ-auth-001" in e and "no DES" in e for e in result.errors)


def test_backward_coverage_fails_when_des_has_no_test() -> None:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = backward_coverage(records)
    assert result.passed is False
    assert any("DES-auth-001" in e and "no TEST" in e for e in result.errors)


def test_index_regenerability_passes_when_byte_identical(tmp_path: Path) -> None:
    index_path = tmp_path / "_ids.md"
    index_path.write_text("# ID Registry\n| ID | Kind | Source | Satisfies |\n")

    def regenerate() -> str:
        return "# ID Registry\n| ID | Kind | Source | Satisfies |\n"

    result = index_regenerability(index_path, regenerate)
    assert result.passed is True


def test_index_regenerability_fails_when_drift(tmp_path: Path) -> None:
    index_path = tmp_path / "_ids.md"
    index_path.write_text("# ID Registry\nOLD\n")

    def regenerate() -> str:
        return "# ID Registry\nNEW\n"

    result = index_regenerability(index_path, regenerate)
    assert result.passed is False
    assert any("not idempotent" in e.lower() for e in result.errors)


def test_annotation_format_integrity_passes_on_valid_annotations(tmp_path: Path) -> None:
    f = tmp_path / "login.py"
    f.write_text("def login():\n" "    # implements: REQ-auth-001\n" "    pass\n")
    result = annotation_format_integrity([f], declared_ids={"REQ-auth-001"})
    assert result.passed is True


def test_annotation_format_integrity_fails_on_unknown_id(tmp_path: Path) -> None:
    f = tmp_path / "login.py"
    f.write_text("def login():\n" "    # implements: REQ-auth-999\n" "    pass\n")
    result = annotation_format_integrity([f], declared_ids={"REQ-auth-001"})
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)


def test_annotation_format_integrity_fails_on_malformed_annotation(tmp_path: Path) -> None:
    f = tmp_path / "login.py"
    f.write_text("def login():\n" "    # implements: not_an_id\n" "    pass\n")
    result = annotation_format_integrity([f], declared_ids={"REQ-auth-001"})
    assert result.passed is False
    assert any("malformed" in e.lower() or "not_an_id" in e for e in result.errors)


def test_change_impact_gate_passes_when_disabled() -> None:
    """The gate is opt-in; when disabled, it always passes."""
    result = change_impact_gate(
        changed_code_files=[Path("src/auth/login.py")],
        change_impact_records_dir=Path("docs/change-impacts"),
        enabled=False,
    )
    assert result.passed is True


def test_change_impact_gate_fails_when_enabled_and_no_record(tmp_path: Path) -> None:
    code_file = tmp_path / "src" / "auth" / "login.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("def login(): pass\n")
    impacts_dir = tmp_path / "docs" / "change-impacts"
    impacts_dir.mkdir(parents=True)  # empty
    result = change_impact_gate(
        changed_code_files=[code_file],
        change_impact_records_dir=impacts_dir,
        enabled=True,
    )
    assert result.passed is False
    assert any("change-impact" in e.lower() for e in result.errors)


def test_change_impact_gate_passes_when_record_exists(tmp_path: Path) -> None:
    code_file = tmp_path / "src" / "auth" / "login.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("def login(): pass\n")
    impacts_dir = tmp_path / "docs" / "change-impacts"
    impacts_dir.mkdir(parents=True)
    (impacts_dir / "CHG-001.md").write_text(
        "# Change CHG-001\n## CODE locations touched\n- src/auth/login.py: rewrite\n"
    )
    result = change_impact_gate(
        changed_code_files=[code_file],
        change_impact_records_dir=impacts_dir,
        enabled=True,
    )
    assert result.passed is True

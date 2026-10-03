"""Tests for assured.export — standard-specific traceability formats."""

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.evidence_index import EvidenceIndexEntry, EvidenceKind
from sdlc_assured_scripts.assured.requirement_metadata import RequirementMetadata
from sdlc_assured_scripts.assured.export import (
    export_csv,
    export_do178c_rtm,
    export_fda_dhf_structure,
    export_iec_62304_matrix,
    export_iso_26262_asil_matrix,
    export_markdown,
)
from sdlc_assured_scripts.assured.evidence_status import EvidenceStatus


def _three_id_chain() -> tuple[list[IdRecord], list[EvidenceIndexEntry]]:
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
        IdRecord(
            id="DES-auth-001",
            kind="DES",
            source="docs/specs/auth/design-spec.md",
            satisfies=["REQ-auth-001"],
        ),
        IdRecord(
            id="TEST-auth-001",
            kind="TEST",
            source="docs/specs/auth/test-spec.md",
            satisfies=["REQ-auth-001", "DES-auth-001"],
        ),
    ]
    evidence = [
        EvidenceIndexEntry(
            kind=EvidenceKind.PYTHON_COMMENT,
            source="src/auth/login.py",
            line=10,
            cited_ids=["REQ-auth-001"],
        )
    ]
    return records, evidence


def test_export_do178c_rtm_columns() -> None:
    records, evidence = _three_id_chain()
    output = export_do178c_rtm(records, evidence, metadata={})
    # DO-178C Requirements Traceability Matrix expects: HLR → LLR → Source code → Test cases.
    assert "Requirements Traceability Matrix (DO-178C)" in output
    assert "| HLR | LLR | Source code | Test case |" in output
    assert (
        "| REQ-auth-001 | DES-auth-001 | src/auth/login.py:10 | TEST-auth-001 |"
        in output
    )


def test_export_iec_62304_matrix_columns() -> None:
    records, evidence = _three_id_chain()
    output = export_iec_62304_matrix(
        records, evidence, metadata={}, software_safety_class="B"
    )
    # IEC 62304 expects: Software requirement → Software unit → Verification activity.
    assert "IEC 62304 Software Traceability Matrix" in output
    assert "Software safety class: B" in output
    assert "| Software requirement | Software unit | Verification activity |" in output
    assert "REQ-auth-001" in output
    assert "src/auth/login.py" in output


def test_export_iso_26262_asil_matrix_columns() -> None:
    records, evidence = _three_id_chain()
    output = export_iso_26262_asil_matrix(
        records, evidence, metadata={}, asil_level="C"
    )
    assert "ISO 26262 ASIL Traceability Matrix" in output
    assert "ASIL: C" in output
    assert (
        "| Safety requirement | Architectural element | Implementation | Verification |"
        in output
    )
    assert "REQ-auth-001" in output
    assert "DES-auth-001" in output
    assert "src/auth/login.py" in output
    assert "TEST-auth-001" in output


def test_export_fda_dhf_structure_sections() -> None:
    records, evidence = _three_id_chain()
    output = export_fda_dhf_structure(records, evidence, metadata={})
    # FDA 21 CFR §820.30 Design History File expects sections per design control element.
    assert "FDA Design History File (21 CFR §820.30)" in output
    assert "## Design inputs" in output
    assert "REQ-auth-001" in output
    assert "## Design outputs" in output
    assert "DES-auth-001" in output
    assert "## Design verification" in output
    assert "TEST-auth-001" in output
    assert "## Design validation" in output  # placeholder section per regulation


def test_export_csv_emits_header_and_rows() -> None:
    records, evidence = _three_id_chain()
    output = export_csv(records, evidence, metadata={})
    assert output.startswith("REQ,DES,TEST,CODE")
    assert "REQ-auth-001" in output
    assert "src/auth/login.py:10" in output


def test_export_markdown_emits_table() -> None:
    records, evidence = _three_id_chain()
    output = export_markdown(records, evidence, metadata={})
    assert "| REQ | DES | TEST | CODE |" in output
    assert "| REQ-auth-001 | DES-auth-001 | TEST-auth-001 |" in output


def _three_id_chain_with_no_evidence() -> (
    tuple[list[IdRecord], list[EvidenceIndexEntry]]
):
    """REQ with no DES, no evidence — every evidence placeholder should be MISSING."""
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
    ]
    evidence: list[EvidenceIndexEntry] = []
    return records, evidence


def test_export_do178c_rtm_uses_typed_evidence_status_for_missing() -> None:
    records, evidence = _three_id_chain_with_no_evidence()
    out = export_do178c_rtm(records, evidence, metadata={})
    assert EvidenceStatus.MISSING.display() in out
    assert "—" not in out


def test_export_iec_62304_matrix_uses_typed_evidence_status_for_missing() -> None:
    records, evidence = _three_id_chain_with_no_evidence()
    out = export_iec_62304_matrix(records, evidence, metadata={})
    assert EvidenceStatus.MISSING.display() in out
    assert "—" not in out


def test_export_iso_26262_asil_matrix_uses_typed_evidence_status_for_missing() -> None:
    records, evidence = _three_id_chain_with_no_evidence()
    out = export_iso_26262_asil_matrix(records, evidence, metadata={})
    assert EvidenceStatus.MISSING.display() in out
    assert "—" not in out


def test_export_fda_dhf_structure_uses_typed_evidence_status_for_missing() -> None:
    records, evidence = _three_id_chain_with_no_evidence()
    out = export_fda_dhf_structure(records, evidence, metadata={})
    # FDA DHF does not use "—" placeholder cells; verify MISSING annotation on empty REQ
    assert EvidenceStatus.MISSING.display() in out


# ---------------------------------------------------------------------------
# Task 11A regression test: F-001/F-009 plan-review P1.1
# ---------------------------------------------------------------------------


def test_export_do178c_rtm_recognises_markdown_evidence_in_source_code_column() -> None:
    """An entry with kind=MARKDOWN_HTML_COMMENT must populate the source-code column,
    not produce a MISSING placeholder. Regression test for F-001/F-009 plan-review P1.1.
    """
    records = [
        IdRecord(
            id="REQ-foo-001",
            kind="REQ",
            source="docs/specs/foo/requirements-spec.md",
            satisfies=[],
        ),
        IdRecord(
            id="DES-foo-001",
            kind="DES",
            source="docs/specs/foo/design-spec.md",
            satisfies=["REQ-foo-001"],
        ),
        IdRecord(
            id="TEST-foo-001",
            kind="TEST",
            source="docs/specs/foo/test-spec.md",
            satisfies=["DES-foo-001"],
        ),
    ]
    evidence = [
        EvidenceIndexEntry(
            kind=EvidenceKind.MARKDOWN_HTML_COMMENT,
            source="plugins/sdlc-x/skills/foo/SKILL.md",
            line=5,
            cited_ids=["DES-foo-001"],
        ),
    ]
    metadata: dict[str, RequirementMetadata] = {}
    out = export_do178c_rtm(records, evidence, metadata)
    assert "plugins/sdlc-x/skills/foo/SKILL.md" in out
    assert "MISSING" not in out

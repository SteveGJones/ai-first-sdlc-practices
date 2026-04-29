"""Tests for assured.export — standard-specific traceability formats."""

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.code_index import CodeIndexEntry
from sdlc_assured_scripts.assured.export import (
    export_do178c_rtm,
    export_iec_62304_matrix,
    export_iso_26262_asil_matrix,
)


def _three_id_chain() -> tuple[list[IdRecord], list[CodeIndexEntry]]:
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
    code = [
        CodeIndexEntry(
            file_path="src/auth/login.py", line=10, cited_ids=["REQ-auth-001"]
        )
    ]
    return records, code


def test_export_do178c_rtm_columns():
    records, code = _three_id_chain()
    output = export_do178c_rtm(records, code)
    # DO-178C Requirements Traceability Matrix expects: HLR → LLR → Source code → Test cases.
    assert "Requirements Traceability Matrix (DO-178C)" in output
    assert "| HLR | LLR | Source code | Test case |" in output
    assert (
        "| REQ-auth-001 | DES-auth-001 | src/auth/login.py:10 | TEST-auth-001 |"
        in output
    )


def test_export_iec_62304_matrix_columns():
    records, code = _three_id_chain()
    output = export_iec_62304_matrix(records, code, software_safety_class="B")
    # IEC 62304 expects: Software requirement → Software unit → Verification activity.
    assert "IEC 62304 Software Traceability Matrix" in output
    assert "Software safety class: B" in output
    assert "| Software requirement | Software unit | Verification activity |" in output
    assert "REQ-auth-001" in output
    assert "src/auth/login.py" in output


def test_export_iso_26262_asil_matrix_columns():
    records, code = _three_id_chain()
    output = export_iso_26262_asil_matrix(records, code, asil_level="C")
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

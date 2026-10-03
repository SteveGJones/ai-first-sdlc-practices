"""Tests for assured.code_index — annotation parsing + shelf-index emission."""

from pathlib import Path

from sdlc_assured_scripts.assured.code_index import (
    CodeIndexEntry,
    parse_code_annotations,
    render_code_index,
    render_spec_findings,
)
from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.requirement_metadata import RequirementMetadata


def test_parse_code_annotations_extracts_implements_lines(tmp_path: Path) -> None:
    f = tmp_path / "login.py"
    f.write_text(
        "def login(token):\n"
        "    # implements: DES-auth-005, REQ-auth-003\n"
        "    return token\n"
        "\n"
        "def logout():\n"
        "    # implements: REQ-auth-007\n"
        "    pass\n"
    )
    entries = parse_code_annotations([f], project_root=tmp_path)
    assert len(entries) == 2
    assert entries[0].file_path == "login.py"
    assert entries[0].line == 2
    assert entries[0].cited_ids == ["DES-auth-005", "REQ-auth-003"]
    assert entries[1].cited_ids == ["REQ-auth-007"]


def test_render_code_index_produces_shelf_shape(tmp_path: Path) -> None:
    entries = [
        CodeIndexEntry(
            file_path="src/auth/login.py",
            line=10,
            cited_ids=["REQ-auth-001"],
            terms=["login", "auth", "session"],
            facts=["Issues a session cookie on success"],
        ),
    ]
    output = render_code_index(entries, library_handle="local-project")
    assert "<!-- format_version: 1 -->" in output
    assert "<!-- library_handle: local-project -->" in output
    assert "## 1. src/auth/login.py:10" in output
    assert "**Terms:** login, auth, session" in output
    assert "**Facts:**" in output
    assert "**Links:** REQ-auth-001" in output


def test_render_spec_findings_emits_one_entry_per_id() -> None:
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
    ]
    output = render_spec_findings(records, library_handle="local-project")
    assert "<!-- format_version: 1 -->" in output
    assert "## 1. REQ-auth-001" in output
    assert "**Terms:** REQ, auth" in output
    assert "**Links:**" in output
    assert "## 2. DES-auth-001" in output
    assert "REQ-auth-001" in output


def test_render_code_index_is_idempotent_without_timestamp() -> None:
    """Repeated calls with the same entries produce byte-identical output."""
    entries = [
        CodeIndexEntry(
            file_path="src/auth/login.py",
            line=10,
            cited_ids=["REQ-auth-001"],
            terms=["auth"],
        ),
    ]
    first = render_code_index(entries, library_handle="local-project")
    second = render_code_index(entries, library_handle="local-project")
    assert first == second


def test_render_code_index_omits_last_rebuilt_by_default() -> None:
    """Without a timestamp argument the last_rebuilt header line is absent."""
    entries = [
        CodeIndexEntry(file_path="src/x.py", line=1, cited_ids=["REQ-x-001"]),
    ]
    output = render_code_index(entries, library_handle="h")
    assert "last_rebuilt" not in output


def test_render_code_index_includes_last_rebuilt_when_supplied() -> None:
    """An explicit timestamp is embedded in the header."""
    entries = [
        CodeIndexEntry(file_path="src/x.py", line=1, cited_ids=["REQ-x-001"]),
    ]
    output = render_code_index(
        entries, library_handle="h", timestamp="2026-04-30T00:00:00Z"
    )
    assert "<!-- last_rebuilt: 2026-04-30T00:00:00Z -->" in output


def test_render_spec_findings_is_idempotent_without_timestamp() -> None:
    """Repeated calls with the same records produce byte-identical output."""
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
    ]
    first = render_spec_findings(records, library_handle="local-project")
    second = render_spec_findings(records, library_handle="local-project")
    assert first == second


def test_render_spec_findings_omits_last_rebuilt_by_default() -> None:
    """Without a timestamp argument the last_rebuilt header line is absent."""
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
    ]
    output = render_spec_findings(records, library_handle="h")
    assert "last_rebuilt" not in output


def test_render_spec_findings_emits_per_req_related_when_metadata_provided() -> None:
    records = [
        IdRecord(id="REQ-foo-001", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
        IdRecord(id="REQ-foo-002", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
        IdRecord(id="REQ-foo-003", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
    ]
    metadata = {
        "REQ-foo-002": RequirementMetadata(req_id="REQ-foo-002", related=["REQ-foo-001"]),
    }
    out = render_spec_findings(records, library_handle="x", metadata=metadata)
    assert "**Related:** REQ-foo-001" in out
    section_001 = out.split("REQ-foo-001")[1].split("REQ-foo-002")[0]
    assert "Related:" not in section_001
    section_003 = out.split("REQ-foo-003")[1]
    assert "Related:" not in section_003

"""Tests for assured.code_index — annotation parsing + shelf-index emission."""

from pathlib import Path

from sdlc_assured_scripts.assured.code_index import (
    CodeIndexEntry,
    parse_code_annotations,
    render_code_index,
)


def test_parse_code_annotations_extracts_implements_lines(tmp_path: Path):
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


def test_render_code_index_produces_shelf_shape(tmp_path: Path):
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

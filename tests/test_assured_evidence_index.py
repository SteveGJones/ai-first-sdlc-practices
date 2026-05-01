"""Tests for assured.evidence_index — abstraction for the v0.2.0 file-type registry."""

from sdlc_assured_scripts.assured.evidence_index import (
    EvidenceIndexEntry,
    EvidenceKind,
)


def test_evidence_index_entry_construction() -> None:
    entry = EvidenceIndexEntry(
        kind=EvidenceKind.PYTHON_COMMENT,
        source="src/auth/login.py",
        line=42,
        cited_ids=["DES-auth-005"],
        terms=["login", "auth"],
        facts=["Issues a session cookie on success"],
    )
    assert entry.kind == EvidenceKind.PYTHON_COMMENT
    assert entry.line == 42


def test_evidence_kind_enum_has_four_values() -> None:
    kinds = {k.name for k in EvidenceKind}
    assert kinds == {
        "PYTHON_COMMENT",
        "MARKDOWN_HTML_COMMENT",
        "YAML_FRONTMATTER",
        "SATISFIES_BY_EXISTENCE",
    }


def test_evidence_index_entry_satisfies_by_existence_has_no_line() -> None:
    entry = EvidenceIndexEntry(
        kind=EvidenceKind.SATISFIES_BY_EXISTENCE,
        source="CONSTITUTION.md",
        line=None,
        cited_ids=["REQ-programme-substrate-003"],
        terms=[],
        facts=["Constitution authority document"],
    )
    assert entry.line is None

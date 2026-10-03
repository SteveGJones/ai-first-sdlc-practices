"""Tests for assured.evidence_index — abstraction for the v0.2.0 file-type registry."""

from pathlib import Path

from sdlc_assured_scripts.assured.evidence_adapters import (
    MarkdownHtmlCommentAdapter,
    PythonCommentAdapter,
    SatisfiesByExistenceAdapter,
    YamlFrontmatterAdapter,
)
from sdlc_assured_scripts.assured.evidence_index import (
    EvidenceIndexEntry,
    EvidenceIndexRegistry,
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


def test_python_comment_adapter_extracts_implements_lines(tmp_path: Path) -> None:
    f = tmp_path / "login.py"
    f.write_text(
        "def login(token):\n"
        "    # implements: DES-auth-005, REQ-auth-003\n"
        "    return token\n"
    )
    adapter = PythonCommentAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.PYTHON_COMMENT
    assert entries[0].line == 2
    assert entries[0].cited_ids == ["DES-auth-005", "REQ-auth-003"]


def test_python_comment_adapter_skips_non_python_files(tmp_path: Path) -> None:
    f = tmp_path / "README.md"
    f.write_text("# implements: DES-x-001\n")
    adapter = PythonCommentAdapter()
    assert list(adapter.extract([f], project_root=tmp_path)) == []


def test_markdown_html_comment_adapter_extracts_html_implements_lines(
    tmp_path: Path,
) -> None:
    f = tmp_path / "SKILL.md"
    f.write_text(
        "---\n"
        "name: example-skill\n"
        "---\n"
        "<!-- implements: DES-foo-001 -->\n"
        "\n"
        "# Skill body\n"
    )
    adapter = MarkdownHtmlCommentAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.MARKDOWN_HTML_COMMENT
    assert entries[0].cited_ids == ["DES-foo-001"]


def test_markdown_html_comment_adapter_ignores_h1_implements(tmp_path: Path) -> None:
    """An H1 heading literally named '# implements:' must NOT be treated as evidence."""
    f = tmp_path / "doc.md"
    f.write_text("# implements: REQ-x-001\n")
    adapter = MarkdownHtmlCommentAdapter()
    assert list(adapter.extract([f], project_root=tmp_path)) == []


def test_yaml_frontmatter_adapter_extracts_implements_list(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text(
        "---\n"
        "implements:\n"
        "  - DES-foo-001\n"
        "  - DES-foo-002\n"
        "---\n"
        "# Body\n"
    )
    adapter = YamlFrontmatterAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.YAML_FRONTMATTER
    assert sorted(entries[0].cited_ids) == ["DES-foo-001", "DES-foo-002"]


def test_satisfies_by_existence_adapter_emits_one_entry_per_satisfies_id(
    tmp_path: Path,
) -> None:
    f = tmp_path / "CONSTITUTION.md"
    f.write_text(
        "---\n"
        "satisfies_by_existence:\n"
        "  - REQ-programme-substrate-003\n"
        "---\n"
        "# Constitution\n"
    )
    adapter = SatisfiesByExistenceAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.SATISFIES_BY_EXISTENCE
    assert entries[0].line is None
    assert entries[0].cited_ids == ["REQ-programme-substrate-003"]


def test_registry_dispatches_python_and_markdown_files(tmp_path: Path) -> None:
    py = tmp_path / "a.py"
    py.write_text("def f():\n    # implements: DES-x-001\n    pass\n")
    md = tmp_path / "b.md"
    md.write_text("<!-- implements: DES-x-002 -->\n")
    registry = EvidenceIndexRegistry.with_default_adapters()
    entries = list(registry.scan([py, md], project_root=tmp_path))
    kinds = {e.kind for e in entries}
    assert EvidenceKind.PYTHON_COMMENT in kinds
    assert EvidenceKind.MARKDOWN_HTML_COMMENT in kinds
    assert any(e.cited_ids == ["DES-x-001"] for e in entries)
    assert any(e.cited_ids == ["DES-x-002"] for e in entries)

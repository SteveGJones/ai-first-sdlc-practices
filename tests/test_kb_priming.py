"""Unit tests for sdlc_knowledge_base_scripts.priming."""
from pathlib import Path
from sdlc_knowledge_base_scripts.priming import build_priming_bundle, PrimingBundle


def test_priming_bundle_happy(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "# CLAUDE.md\n\n"
        "Some framework pointers.\n\n"
        "## Knowledge Base\n\n"
        "This project uses the knowledge base.\n\n"
        "### Layout\n\n"
        "Library at library/.\n\n"
        "## Next section\n\n"
        "Unrelated.\n"
    )
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "_shelf-index.md").write_text(
        "# Shelf Index\n\n"
        "## 1. topic-a.md\n"
        "**Terms:** alpha, beta, gamma\n"
        "**Facts:** ...\n\n"
        "## 2. topic-b.md\n"
        "**Terms:** delta, epsilon, alpha\n"
    )
    result = build_priming_bundle(
        question="what do we know about alpha",
        project_dir=tmp_path,
    )
    assert isinstance(result, PrimingBundle)
    assert result.question == "what do we know about alpha"
    assert "This project uses the knowledge base." in result.local_kb_config_excerpt
    assert "Next section" not in result.local_kb_config_excerpt
    assert set(result.local_shelf_index_terms) == {"alpha", "beta", "gamma", "delta", "epsilon"}


def test_priming_bundle_missing_claude_md(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "_shelf-index.md").write_text("# Shelf Index\n")
    result = build_priming_bundle(question="q", project_dir=tmp_path)
    assert result.local_kb_config_excerpt == ""
    assert result.local_shelf_index_terms == []


def test_priming_bundle_missing_shelf_index(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("## Knowledge Base\n\nConfig.\n")
    # no library/ directory
    result = build_priming_bundle(question="q", project_dir=tmp_path)
    assert "Config." in result.local_kb_config_excerpt
    assert result.local_shelf_index_terms == []


def test_priming_bundle_no_kb_section_in_claude_md(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# CLAUDE.md\n\nNothing about the KB here.\n")
    result = build_priming_bundle(question="q", project_dir=tmp_path)
    assert result.local_kb_config_excerpt == ""

"""Unit tests for sdlc_knowledge_base_scripts.kb_config (EPIC #197, issue #154).

TDD: these tests were written before the implementation.
"""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.kb_config import (
    DEFAULT_LAYERS,
    allowed_layers,
    check_layer_compliance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_md(path: Path, frontmatter: str | None = None, body: str = "Content") -> None:
    """Write a markdown file, optionally with YAML frontmatter."""
    if frontmatter is not None:
        path.write_text(f"---\n{frontmatter}\n---\n{body}\n")
    else:
        path.write_text(f"{body}\n")


# ---------------------------------------------------------------------------
# Tests for allowed_layers()
# ---------------------------------------------------------------------------


def test_allowed_layers_returns_defaults_when_no_claude_md(tmp_path: Path) -> None:
    """No CLAUDE.md present → return DEFAULT_LAYERS."""
    result = allowed_layers(tmp_path)
    assert result == DEFAULT_LAYERS


def test_allowed_layers_returns_defaults_when_no_kb_section(tmp_path: Path) -> None:
    """CLAUDE.md exists but has no ## Knowledge Base section → return DEFAULT_LAYERS."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# My Project\n\n## Some Section\n\nSome content.\n")
    result = allowed_layers(tmp_path)
    assert result == DEFAULT_LAYERS


def test_allowed_layers_returns_defaults_when_no_layers_key(tmp_path: Path) -> None:
    """## Knowledge Base section exists but has no layers: key → return DEFAULT_LAYERS."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "# My Project\n\n## Knowledge Base\n\nlibrary_path: library/\n\n## Next Section\n"
    )
    result = allowed_layers(tmp_path)
    assert result == DEFAULT_LAYERS


def test_allowed_layers_returns_project_values_when_declared(tmp_path: Path) -> None:
    """layers: key with list values → return those values (replacing defaults)."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "# My Project\n\n## Knowledge Base\n\nlibrary_path: library/\nlayers:\n"
        "  - methodology\n  - evidence\n  - regulatory\n\n## Next Section\n"
    )
    result = allowed_layers(tmp_path)
    assert result == ["methodology", "evidence", "regulatory"]


def test_allowed_layers_strips_inline_comments(tmp_path: Path) -> None:
    """Inline # comments on layers: list items must be stripped."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "## Knowledge Base\n\nlayers:\n"
        "  - methodology  # core\n"
        "  - regulatory  # new for this project\n"
    )
    result = allowed_layers(tmp_path)
    assert result == ["methodology", "regulatory"]


def test_allowed_layers_stops_at_next_heading(tmp_path: Path) -> None:
    """Parser must stop collecting layers when the next ## heading is encountered."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "## Knowledge Base\n\nlayers:\n"
        "  - methodology\n"
        "  - evidence\n\n"
        "## Another Section\n\nlayers:\n"
        "  - should_not_appear\n"
    )
    result = allowed_layers(tmp_path)
    assert result == ["methodology", "evidence"]
    assert "should_not_appear" not in result


def test_allowed_layers_handles_blank_line_in_list(tmp_path: Path) -> None:
    """Parser must skip blank lines within the layers: list."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "## Knowledge Base\n\nlayers:\n  - methodology\n\n  - evidence\n"
    )
    result = allowed_layers(tmp_path)
    assert result == ["methodology", "evidence"]


# ---------------------------------------------------------------------------
# Tests for check_layer_compliance()
# ---------------------------------------------------------------------------


def test_check_layer_compliance_passes_all_valid(tmp_path: Path) -> None:
    """All files with valid layer: frontmatter → no violations."""
    lib = tmp_path / "library"
    lib.mkdir()
    _write_md(lib / "page1.md", "title: Page 1\nlayer: methodology")
    _write_md(lib / "page2.md", "title: Page 2\nlayer: evidence")
    violations = check_layer_compliance(lib, DEFAULT_LAYERS)
    assert violations == []


def test_check_layer_compliance_flags_missing_layer(tmp_path: Path) -> None:
    """File with frontmatter but no layer: key → flagged as missing."""
    lib = tmp_path / "library"
    lib.mkdir()
    _write_md(lib / "no_layer.md", "title: No Layer")
    violations = check_layer_compliance(lib, DEFAULT_LAYERS)
    assert len(violations) == 1
    path_str, msg = violations[0]
    assert "no_layer.md" in path_str
    assert "missing" in msg.lower()


def test_check_layer_compliance_flags_missing_layer_no_frontmatter(tmp_path: Path) -> None:
    """File with no frontmatter at all → flagged as missing layer."""
    lib = tmp_path / "library"
    lib.mkdir()
    _write_md(lib / "bare.md", frontmatter=None)
    violations = check_layer_compliance(lib, DEFAULT_LAYERS)
    assert len(violations) == 1
    _, msg = violations[0]
    assert "missing" in msg.lower()


def test_check_layer_compliance_flags_invalid_layer(tmp_path: Path) -> None:
    """File with layer: value not in allowed list → flagged as invalid."""
    lib = tmp_path / "library"
    lib.mkdir()
    _write_md(lib / "bad_layer.md", "title: Bad\nlayer: nonexistent")
    violations = check_layer_compliance(lib, DEFAULT_LAYERS)
    assert len(violations) == 1
    _, msg = violations[0]
    assert "invalid" in msg.lower() or "not in" in msg.lower() or "nonexistent" in msg.lower()


def test_check_layer_compliance_accepts_custom_layer(tmp_path: Path) -> None:
    """A custom allowed layer (e.g. 'regulatory') must pass when in the allowed list."""
    lib = tmp_path / "library"
    lib.mkdir()
    custom_layers = ["methodology", "evidence", "regulatory"]
    _write_md(lib / "reg.md", "title: Reg\nlayer: regulatory")
    violations = check_layer_compliance(lib, custom_layers)
    assert violations == []


def test_check_layer_compliance_skips_excluded_files(tmp_path: Path) -> None:
    """_shelf-index.md, log.md, _index.md (root), and raw/ subdir files are skipped."""
    lib = tmp_path / "library"
    lib.mkdir()
    # These should be excluded even with no layer frontmatter
    _write_md(lib / "_shelf-index.md", frontmatter=None)
    _write_md(lib / "log.md", frontmatter=None)
    _write_md(lib / "_index.md", frontmatter=None)
    raw = lib / "raw"
    raw.mkdir()
    _write_md(raw / "source.md", frontmatter=None)
    violations = check_layer_compliance(lib, DEFAULT_LAYERS)
    assert violations == []


def test_check_layer_compliance_multiple_files(tmp_path: Path) -> None:
    """Multiple violations across multiple files are all reported."""
    lib = tmp_path / "library"
    lib.mkdir()
    _write_md(lib / "good.md", "title: Good\nlayer: methodology")
    _write_md(lib / "missing.md", "title: Missing")
    _write_md(lib / "invalid.md", "title: Invalid\nlayer: bogus")
    violations = check_layer_compliance(lib, DEFAULT_LAYERS)
    assert len(violations) == 2
    paths = [v[0] for v in violations]
    assert any("missing.md" in p for p in paths)
    assert any("invalid.md" in p for p in paths)

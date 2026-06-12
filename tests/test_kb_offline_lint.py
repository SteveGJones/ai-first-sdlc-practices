"""Federation-aware lint tests (model-free). kb-offline M2c (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.lint import (  # noqa: F401 (import-shape check)
    FrontmatterIssue,
    check_frontmatter,
)


def _page(lib, name, body):
    (lib / name).write_text(body, encoding="utf-8")


def test_check_frontmatter_flags_missing_fields(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _page(lib, "good.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# Good\nok\n")
    _page(lib, "partial.md", "---\nlayer: evidence\n---\n# Partial\nbody\n")
    _page(lib, "bare.md", "# Bare\njust text\n")
    _page(lib, "_shelf-index.md", "<!-- format_version: 1 -->\n# Shelf\n")
    issues = check_frontmatter(lib)
    by_page = {i.page: i for i in issues}
    assert "good.md" not in by_page
    assert "_shelf-index.md" not in by_page
    assert "confidence" in by_page["partial.md"].detail and "cross_references" in by_page["partial.md"].detail
    assert "layer" not in by_page["partial.md"].detail
    assert "frontmatter" in by_page["bare.md"].detail.lower()


def test_check_frontmatter_clean_library_returns_empty(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _page(lib, "a.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    assert check_frontmatter(lib) == []

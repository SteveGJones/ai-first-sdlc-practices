"""Federation-aware lint tests (model-free). kb-offline M2c (#211)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sdlc_knowledge_base_scripts.lint import (  # noqa: F401 (import-shape check)
    FrontmatterIssue,
    StalenessResult,  # noqa: F401
    check_frontmatter,
    check_staleness,
)
from sdlc_knowledge_base_scripts.registry import LibrarySource


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


def _lib_with_rebuilt(tmp_path, name, rebuilt_iso):
    lib = tmp_path / name
    lib.mkdir()
    header = "" if rebuilt_iso is None else f"<!-- last_rebuilt: {rebuilt_iso} -->\n"
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n{header}# Shelf\n")
    return lib


_NOW = datetime(2026, 6, 11, tzinfo=timezone.utc)


def test_staleness_fresh(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", (_NOW - timedelta(days=5)).isoformat())
    src = LibrarySource(name="local", type="filesystem", path=str(lib))
    res = check_staleness(src, now=_NOW)
    assert res.state == "fresh" and res.age_days == 5 and res.threshold_days == 14


def test_staleness_stale(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", (_NOW - timedelta(days=30)).isoformat())
    src = LibrarySource(name="local", type="filesystem", path=str(lib))
    res = check_staleness(src, now=_NOW)
    assert res.state == "stale" and res.age_days == 30


def test_staleness_unknown_when_no_last_rebuilt(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", None)
    src = LibrarySource(name="local", type="filesystem", path=str(lib))
    res = check_staleness(src, now=_NOW)
    assert res.state == "unknown" and res.age_days is None


def test_staleness_corp_threshold(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "corp-x", (_NOW - timedelta(days=30)).isoformat())
    src = LibrarySource(name="corp-x", type="filesystem", path=str(lib))
    res = check_staleness(src, now=_NOW)
    assert res.state == "fresh" and res.threshold_days == 90

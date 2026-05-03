"""Unit and integration tests for sdlc_knowledge_base_scripts.build_shelf_index."""
from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.build_shelf_index import (
    IndexEntry,
    RebuildStats,
    build_entry,
    compute_hash,
    extract_facts,
    extract_links,
    extract_terms,
    parse_existing_index,
    parse_frontmatter,
    rebuild_shelf_index,
)


def test_parse_frontmatter_valid() -> None:
    text = "---\ntitle: My File\ndomain: testing\n---\nContent"
    result = parse_frontmatter(text)
    assert result["title"] == "My File"
    assert result["domain"] == "testing"


def test_parse_frontmatter_no_frontmatter() -> None:
    assert parse_frontmatter("# Just Content\n") == {}


def test_parse_frontmatter_malformed_yaml() -> None:
    assert parse_frontmatter("---\n: broken {\n---\nContent") == {}


def test_parse_frontmatter_non_dict_yaml() -> None:
    # YAML that parses to a non-dict (list) must return empty dict
    assert parse_frontmatter("---\n- item\n---\nContent") == {}


def test_extract_terms_from_title_and_domain() -> None:
    fm = {"title": "Agent Suitability Rubric", "domain": "sdlc, evaluation"}
    terms = extract_terms(fm, "")
    assert "agent" in terms
    assert "suitability" in terms
    assert "rubric" in terms
    assert "sdlc" in terms
    assert "evaluation" in terms


def test_extract_terms_from_tags_list() -> None:
    fm = {"tags": ["rubric", "dora", "evaluation"]}
    terms = extract_terms(fm, "")
    assert "rubric" in terms
    assert "dora" in terms
    assert "evaluation" in terms


def test_extract_terms_from_headings() -> None:
    content = "## Key Question\n## Core Findings\n### Sub-heading not included\n"
    terms = extract_terms({}, content)
    assert "key question" in terms
    assert "core findings" in terms


def test_extract_terms_deduplicates() -> None:
    fm = {"title": "sdlc", "domain": "sdlc"}
    terms = extract_terms(fm, "## sdlc\n")
    assert terms.count("sdlc") == 1


def test_extract_terms_caps_at_thirty() -> None:
    fm = {"tags": [f"term{i}" for i in range(50)]}
    terms = extract_terms(fm, "")
    assert len(terms) <= 30


def test_extract_facts_from_finding_markers() -> None:
    content = (
        "**Finding**: Elite teams ship in <1 hour. Source: DORA 2024.\n"
        "**Finding**: TDD reduces defects 40%. Source: Madeyski 2010.\n"
    )
    facts = extract_facts(content)
    assert len(facts) == 2
    assert "Elite teams ship" in facts[0]
    assert "TDD reduces defects" in facts[1]


def test_extract_facts_capped_at_five() -> None:
    content = "\n".join(f"**Finding**: Fact {i}." for i in range(10))
    facts = extract_facts(content)
    assert len(facts) == 5


def test_extract_facts_fallback_to_numbered_list() -> None:
    content = "## Core Findings\n\n1. **First finding in list**\n2. **Second finding**\n\n## Other\n"
    facts = extract_facts(content)
    assert len(facts) >= 1
    assert "First finding in list" in facts[0]


def test_extract_facts_returns_empty_when_none() -> None:
    assert extract_facts("# Empty file\nNo findings here.") == []


def test_extract_links_from_cross_references() -> None:
    fm = {"cross_references": ["library/file-a.md", "library/file-b.md"]}
    links = extract_links(fm)
    assert "library/file-a.md" in links
    assert "library/file-b.md" in links


def test_extract_links_empty_when_missing() -> None:
    assert extract_links({}) == []


def test_compute_hash_is_64_char_hex(tmp_path: Path) -> None:
    f = tmp_path / "file.md"
    f.write_text("content", encoding="utf-8")
    h = compute_hash(f)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_hash_deterministic(tmp_path: Path) -> None:
    f = tmp_path / "file.md"
    f.write_text("content", encoding="utf-8")
    assert compute_hash(f) == compute_hash(f)


def test_compute_hash_differs_for_different_content(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("content a", encoding="utf-8")
    b.write_text("content b", encoding="utf-8")
    assert compute_hash(a) != compute_hash(b)


# ---------------------------------------------------------------------------
# Integration tests — rebuild flow
# ---------------------------------------------------------------------------


def _write_library_file(path: Path, title: str, domain: str = "testing") -> None:
    """Helper: write a minimal but valid library file at path."""
    path.write_text(
        f"---\ntitle: {title}\ndomain: {domain}\n"
        "cross_references:\n  - library/other.md\n---\n"
        f"## Key Question\nWhat?\n\n## Core Findings\n\n"
        f"**Finding**: Key fact from {title}. Source: Research 2026.\n",
        encoding="utf-8",
    )


def test_parse_existing_index_reads_hashes(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 1 -->\n"
        "# Shelf-Index\n\n"
        "## 1. file-a.md\n\n"
        f"**Hash:** {'a' * 64}\n"
        "**Terms:** foo\n"
        "**Facts:**\n- fact\n"
        "**Links:** \n\n"
        "## 2. file-b.md\n\n"
        f"**Hash:** {'b' * 64}\n"
        "**Terms:** bar\n"
        "**Facts:**\n- fact\n"
        "**Links:** \n",
        encoding="utf-8",
    )
    mapping = parse_existing_index(shelf)
    assert mapping["file-a.md"] == "a" * 64
    assert mapping["file-b.md"] == "b" * 64


def test_parse_existing_index_returns_empty_for_missing(tmp_path: Path) -> None:
    assert parse_existing_index(tmp_path / "missing.md") == {}


def test_build_entry_populates_all_fields(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "test-entry.md"
    _write_library_file(f, "Test Entry")
    entry = build_entry(f, lib)
    assert entry.file_path == "test-entry.md"
    assert len(entry.hash) == 64
    assert "test" in entry.terms
    assert len(entry.facts) >= 1
    assert "library/other.md" in entry.links


def test_rebuild_shelf_index_initial_build(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry-a.md", "Entry A")
    _write_library_file(lib / "entry-b.md", "Entry B")
    shelf = lib / "_shelf-index.md"

    stats = rebuild_shelf_index(lib, shelf)
    assert stats.added == 2
    assert stats.unchanged == 0
    assert stats.modified == 0
    assert stats.removed == 0
    assert shelf.exists()
    content = shelf.read_text()
    assert "entry-a.md" in content
    assert "entry-b.md" in content


def test_rebuild_shelf_index_incremental_skips_unchanged(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "Entry")
    shelf = lib / "_shelf-index.md"

    rebuild_shelf_index(lib, shelf)
    stats = rebuild_shelf_index(lib, shelf)  # second run, nothing changed
    assert stats.unchanged == 1
    assert stats.modified == 0
    assert stats.added == 0


def test_rebuild_shelf_index_detects_modified_file(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "entry.md"
    _write_library_file(f, "Entry V1")
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)

    f.write_text(f.read_text(encoding="utf-8") + "\nExtra content.", encoding="utf-8")
    stats = rebuild_shelf_index(lib, shelf)
    assert stats.modified == 1
    assert stats.unchanged == 0


def test_rebuild_shelf_index_detects_removed_file(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "entry.md"
    _write_library_file(f, "Entry")
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)

    f.unlink()
    stats = rebuild_shelf_index(lib, shelf)
    assert stats.removed == 1
    assert "entry.md" not in shelf.read_text(encoding="utf-8")


def test_rebuild_shelf_index_full_mode_never_counts_unchanged(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "Entry")
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)  # initial: added=1

    stats = rebuild_shelf_index(lib, shelf, full=True)
    assert stats.unchanged == 0  # full mode never skips


def test_rebuild_shelf_index_excludes_special_files(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    raw = lib / "raw"
    raw.mkdir(parents=True)
    (raw / "source.md").write_text("raw source", encoding="utf-8")
    (lib / "log.md").write_text("# Log\n", encoding="utf-8")
    (lib / "_index.md").write_text("# Index\n", encoding="utf-8")
    _write_library_file(lib / "real.md", "Real Entry")
    shelf = lib / "_shelf-index.md"

    stats = rebuild_shelf_index(lib, shelf)
    assert stats.added == 1  # only real.md
    content = shelf.read_text(encoding="utf-8")
    assert "raw/source.md" not in content
    assert "log.md" not in content
    assert "_index.md" not in content
    assert "real.md" in content


def test_rebuild_shelf_index_writes_header(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)
    content = shelf.read_text(encoding="utf-8")
    assert "<!-- format_version: 1 -->" in content
    assert "<!-- last_rebuilt:" in content
    assert "<!-- library_handle:" in content
    assert "<!-- library_description:" in content


def test_rebuild_shelf_index_preserves_library_handle(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    shelf = lib / "_shelf-index.md"
    # Write a shelf-index that already has a library_handle
    shelf.write_text(
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: 2026-01-01T00:00:00Z -->\n"
        "<!-- library_handle: corp-semi -->\n"
        "<!-- library_description: Corporate findings -->\n"
        "# Shelf\n",
        encoding="utf-8",
    )
    _write_library_file(lib / "entry.md", "Entry")
    rebuild_shelf_index(lib, shelf)
    content = shelf.read_text(encoding="utf-8")
    assert "<!-- library_handle: corp-semi -->" in content
    assert "<!-- library_description: Corporate findings -->" in content


def test_rebuild_shelf_index_appends_to_log(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "Entry")
    log = lib / "log.md"
    log.write_text("# Log\n", encoding="utf-8")
    shelf = lib / "_shelf-index.md"

    rebuild_shelf_index(lib, shelf, log_path=log)
    log_content = log.read_text(encoding="utf-8")
    assert "rebuild-indexes" in log_content
    assert "incremental" in log_content


def test_rebuild_shelf_index_skips_log_if_absent(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "Entry")
    shelf = lib / "_shelf-index.md"
    absent_log = lib / "log.md"
    # Should not raise even though log_path is provided but absent
    rebuild_shelf_index(lib, shelf, log_path=absent_log)
    assert not absent_log.exists()


def test_rebuild_shelf_index_terms_in_output(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "Agent Suitability", domain="sdlc")
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)
    content = shelf.read_text(encoding="utf-8")
    assert "**Terms:**" in content
    assert "agent" in content
    assert "sdlc" in content


def test_rebuild_shelf_index_priming_terms_format(tmp_path: Path) -> None:
    """Terms field must be comma-separated for priming.py _extract_shelf_index_terms."""
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "My Title", domain="my-domain")
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)
    content = shelf.read_text(encoding="utf-8")
    # The priming module scans for: **Terms:** <comma-separated>
    import re as _re
    matches = _re.findall(r"\*\*Terms:\*\*[ \t]*(.*?)(?=\n|$)", content)
    assert matches, "No **Terms:** line found in shelf-index"
    assert "," in matches[0], "Terms must be comma-separated for priming compatibility"

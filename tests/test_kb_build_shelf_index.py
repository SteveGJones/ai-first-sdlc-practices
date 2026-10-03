"""Unit and integration tests for sdlc_knowledge_base_scripts.build_shelf_index."""
from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.build_shelf_index import (
    RAIL_GROWTH_FACTOR,
    RAIL_MIN_ADDED,
    build_entry,
    compute_hash,
    extract_facts,
    extract_links,
    extract_terms,
    main,
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


def test_rebuild_shelf_index_creates_parent_directory(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_library_file(lib / "entry.md", "Entry")
    # shelf-index in a subdirectory that doesn't exist yet
    shelf = lib / "indexes" / "_shelf-index.md"
    stats = rebuild_shelf_index(lib, shelf)
    assert shelf.exists()
    assert stats.added == 1


# ---------------------------------------------------------------------------
# Layer support (Phase B, #154)
# ---------------------------------------------------------------------------


def test_extract_layer_returns_valid_value() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_layer

    assert extract_layer({"layer": "methodology"}) == "methodology"


def test_extract_layer_strips_and_lowercases() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_layer

    assert extract_layer({"layer": "  Methodology  "}) == "methodology"


def test_extract_layer_returns_uncategorized_when_missing() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_layer

    assert extract_layer({}) == "uncategorized"


def test_extract_layer_returns_uncategorized_for_empty_string() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_layer

    assert extract_layer({"layer": ""}) == "uncategorized"


def test_extract_layer_returns_value_even_if_invalid() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_layer

    assert extract_layer({"layer": "INVALID VALUE"}) == "invalid value"


def test_index_entry_has_layer_field() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import IndexEntry

    entry = IndexEntry(
        file_path="test.md",
        hash="a" * 64,
        terms=["term"],
        facts=[],
        links=[],
        layer="methodology",
    )
    assert entry.layer == "methodology"


def test_build_entry_includes_layer(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import build_entry

    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "test.md"
    f.write_text(
        "---\ntitle: Test\ndomain: testing\nlayer: evidence\nstatus: active\n---\n## Key Question\nWhat?\n",
        encoding="utf-8",
    )
    entry = build_entry(f, lib)
    assert entry.layer == "evidence"


def test_build_entry_layer_uncategorized_when_missing(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import build_entry

    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "test.md"
    f.write_text(
        "---\ntitle: Test\ndomain: testing\nstatus: active\n---\n## Key Question\nWhat?\n",
        encoding="utf-8",
    )
    entry = build_entry(f, lib)
    assert entry.layer == "uncategorized"


def test_render_entry_includes_layer_line() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import IndexEntry, _render_entry

    entry = IndexEntry(
        file_path="test.md",
        hash="a" * 64,
        terms=["testing"],
        facts=["A fact."],
        links=[],
        layer="domain",
    )
    rendered = _render_entry(1, entry)
    assert "**Layer:** domain" in rendered
    lines = rendered.splitlines()
    hash_idx = next(i for i, l in enumerate(lines) if l.startswith("**Hash:**"))
    layer_idx = next(i for i, l in enumerate(lines) if l.startswith("**Layer:**"))
    terms_idx = next(i for i, l in enumerate(lines) if l.startswith("**Terms:**"))
    assert hash_idx < layer_idx < terms_idx


def test_extract_terms_includes_layer() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_terms

    fm = {"title": "Test", "domain": "sdlc", "layer": "methodology"}
    terms = extract_terms(fm, "")
    assert "methodology" in terms


def test_rebuild_includes_layer_in_shelf_index(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "test.md").write_text(
        "---\ntitle: Test\ndomain: testing\nlayer: evidence\nstatus: active\n---\n## Key Question\nWhat?\n",
        encoding="utf-8",
    )
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)
    content = shelf.read_text(encoding="utf-8")
    assert "**Layer:** evidence" in content


# ---------------------------------------------------------------------------
# Confidence support (Phase C, #163)
# ---------------------------------------------------------------------------


def test_extract_confidence_high() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_confidence

    assert extract_confidence({"confidence": "high"}) == "high"


def test_extract_confidence_medium() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_confidence

    assert extract_confidence({"confidence": "medium"}) == "medium"


def test_extract_confidence_low() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_confidence

    assert extract_confidence({"confidence": "low"}) == "low"


def test_extract_confidence_unknown_when_missing() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_confidence

    assert extract_confidence({}) == "unknown"


def test_extract_confidence_unknown_for_invalid_value() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_confidence

    assert extract_confidence({"confidence": "excellent"}) == "unknown"


def test_extract_confidence_strips_and_lowercases() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_confidence

    assert extract_confidence({"confidence": "  HIGH  "}) == "high"


def test_index_entry_has_confidence_field() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import IndexEntry

    entry = IndexEntry(
        file_path="test.md",
        hash="a" * 64,
        terms=[],
        facts=[],
        links=[],
        layer="methodology",
        confidence="high",
    )
    assert entry.confidence == "high"


def test_index_entry_confidence_defaults_to_unknown() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import IndexEntry

    entry = IndexEntry(
        file_path="test.md",
        hash="a" * 64,
        terms=[],
        facts=[],
        links=[],
        layer="methodology",
    )
    assert entry.confidence == "unknown"


def test_build_entry_includes_confidence(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import build_entry

    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "test.md"
    f.write_text(
        "---\ntitle: Test\ndomain: testing\nlayer: evidence\nconfidence: high\nstatus: active\n---\n## Q\nWhat?\n",
        encoding="utf-8",
    )
    entry = build_entry(f, lib)
    assert entry.confidence == "high"


def test_build_entry_confidence_unknown_when_missing(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import build_entry

    lib = tmp_path / "library"
    lib.mkdir()
    f = lib / "test.md"
    f.write_text(
        "---\ntitle: Test\ndomain: testing\nlayer: evidence\nstatus: active\n---\n## Q\nWhat?\n",
        encoding="utf-8",
    )
    entry = build_entry(f, lib)
    assert entry.confidence == "unknown"


def test_render_entry_confidence_between_layer_and_terms() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import IndexEntry, _render_entry

    entry = IndexEntry(
        file_path="test.md",
        hash="a" * 64,
        terms=["testing"],
        facts=["A fact."],
        links=[],
        layer="methodology",
        confidence="high",
    )
    rendered = _render_entry(1, entry)
    assert "**Confidence:** high" in rendered
    lines = rendered.splitlines()
    layer_idx = next(i for i, l in enumerate(lines) if l.startswith("**Layer:**"))
    conf_idx = next(i for i, l in enumerate(lines) if l.startswith("**Confidence:**"))
    terms_idx = next(i for i, l in enumerate(lines) if l.startswith("**Terms:**"))
    assert layer_idx < conf_idx < terms_idx


def test_extract_terms_includes_confidence() -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import extract_terms

    fm = {
        "title": "Test",
        "domain": "sdlc",
        "layer": "methodology",
        "confidence": "high",
    }
    terms = extract_terms(fm, "")
    assert "high" in terms


def test_rebuild_includes_confidence_in_shelf_index(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "test.md").write_text(
        "---\ntitle: Test\ndomain: testing\nlayer: evidence\nconfidence: medium\nstatus: active\n---\n## Q\nWhat?\n",
        encoding="utf-8",
    )
    shelf = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, shelf)
    assert "**Confidence:** medium" in shelf.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Vendored-directory exclusions and growth safety rail (issue #241)
# ---------------------------------------------------------------------------


def _md(path: Path, body: str = "# Doc\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: T\n---\n{body}", encoding="utf-8")


def _fixture_241(tmp_path: Path, dump_files: int = 5) -> Path:
    """Two real files plus a vendored iso20022/ tree of .md and .json."""
    library = tmp_path / "library"
    _md(library / "one.md")
    _md(library / "two.md")
    for i in range(dump_files):
        _md(library / "iso20022" / "sub" / f"msg{i}.md")
        (library / "iso20022" / "sub" / f"msg{i}.json").write_text(
            "{}", encoding="utf-8"
        )
    (library / "log.md").write_text("# Log\n", encoding="utf-8")
    return library


def _entry_paths(index: Path) -> list[str]:
    return list(parse_existing_index(index))


def test_rail_constants() -> None:
    assert RAIL_MIN_ADDED == 50
    assert RAIL_GROWTH_FACTOR == 2


def test_ignore_file_keeps_vendored_dir_out_of_index_and_log(tmp_path: Path) -> None:
    library = _fixture_241(tmp_path)
    (library / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    index = library / "_shelf-index.md"
    stats = rebuild_shelf_index(library, index, log_path=library / "log.md")
    assert sorted(_entry_paths(index)) == ["one.md", "two.md"]
    assert stats.added == 2
    assert "iso20022" not in (library / "log.md").read_text(encoding="utf-8")
    assert not stats.refused


def test_rail_refuses_runaway_growth_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _fixture_241(tmp_path, dump_files=60)
    (library / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    index = library / "_shelf-index.md"
    log = library / "log.md"
    rebuild_shelf_index(library, index, log_path=log)
    (library / ".kb-index-ignore").unlink()
    index_before = index.read_bytes()
    log_before = log.read_bytes()

    stats = rebuild_shelf_index(library, index, log_path=log)
    assert stats.refused
    assert stats.added == 60
    assert stats.added_by_dir == {"iso20022": 60}
    assert index.read_bytes() == index_before
    assert log.read_bytes() == log_before

    code = main([str(library)])
    out = capsys.readouterr()
    assert code == 2
    assert "iso20022/: 60 added" in out.err + out.out
    assert ".kb-index-ignore" in out.err + out.out
    assert "--force" in out.err + out.out
    assert index.read_bytes() == index_before
    assert log.read_bytes() == log_before


def test_force_overrides_rail(tmp_path: Path) -> None:
    library = _fixture_241(tmp_path, dump_files=60)
    (library / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    index = library / "_shelf-index.md"
    log = library / "log.md"
    rebuild_shelf_index(library, index, log_path=log)
    (library / ".kb-index-ignore").unlink()

    assert main([str(library), "--force"]) == 0
    assert len(_entry_paths(index)) == 62
    assert "Files added: 60" in log.read_text(encoding="utf-8")


def test_first_build_exempt_from_rail(tmp_path: Path) -> None:
    library = tmp_path / "library"
    for i in range(60):
        _md(library / f"f{i}.md")
    index = library / "_shelf-index.md"
    stats = rebuild_shelf_index(library, index)
    assert not stats.refused
    assert len(_entry_paths(index)) == 60


def test_zero_entry_existing_index_exempt(tmp_path: Path) -> None:
    library = tmp_path / "library"
    for i in range(60):
        _md(library / f"f{i}.md")
    index = library / "_shelf-index.md"
    index.write_text("# Knowledge Base Shelf-Index\n", encoding="utf-8")
    assert not rebuild_shelf_index(library, index).refused


def test_growth_below_min_added_does_not_trip(tmp_path: Path) -> None:
    library = tmp_path / "library"
    for i in range(10):
        _md(library / f"f{i}.md")
    index = library / "_shelf-index.md"
    rebuild_shelf_index(library, index)
    for i in range(40):
        _md(library / f"new{i}.md")
    stats = rebuild_shelf_index(library, index)
    assert not stats.refused
    assert len(_entry_paths(index)) == 50


def test_large_but_proportionate_growth_does_not_trip(tmp_path: Path) -> None:
    library = tmp_path / "library"
    for i in range(100):
        _md(library / f"f{i}.md")
    index = library / "_shelf-index.md"
    rebuild_shelf_index(library, index)
    for i in range(50):
        _md(library / f"new{i}.md")
    assert not rebuild_shelf_index(library, index).refused


def test_dry_run_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _fixture_241(tmp_path)
    index = library / "_shelf-index.md"
    log = library / "log.md"
    log_before = log.read_bytes()
    assert main([str(library), "--dry-run"]) == 0
    assert not index.exists()
    assert log.read_bytes() == log_before
    assert "dry run" in capsys.readouterr().out.lower()


def test_dry_run_reports_rail_verdict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _fixture_241(tmp_path, dump_files=60)
    (library / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    index = library / "_shelf-index.md"
    rebuild_shelf_index(library, index)
    (library / ".kb-index-ignore").unlink()
    before = index.read_bytes()
    code = main([str(library), "--dry-run"])
    out = capsys.readouterr().out
    assert code == 2
    assert "would be refused" in out.lower()
    assert "iso20022/: 60 added" in out
    assert index.read_bytes() == before


def test_cli_output_has_scanned_and_excluded_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _fixture_241(tmp_path, dump_files=3)
    (library / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    assert main([str(library)]) == 0
    out = capsys.readouterr().out
    assert "Scanned:" in out
    assert "Excluded:" in out
    excluded_block = out.split("Excluded:")[1]
    assert "iso20022/" in excluded_block
    assert "iso20022/: 3" not in out.split("Excluded:")[1]
    assert "./: 2" in out


def test_cli_wrong_case_entry_warns_is_scanned_and_not_listed_excluded(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _fixture_241(tmp_path, dump_files=3)
    (library / ".kb-index-ignore").write_text("ISO20022\n", encoding="utf-8")
    assert main([str(library)]) == 0
    out = capsys.readouterr().out
    assert "differs only in case" in out
    scanned_block = out.split("Scanned:")[1].split("Excluded:")[0]
    excluded_block = out.split("Excluded:")[1].split("Warnings")[0]
    assert "iso20022/: 3" in scanned_block
    assert "iso20022/" not in excluded_block
    assert "ISO20022/" not in excluded_block
    index_text = (library / "_shelf-index.md").read_text(encoding="utf-8")
    assert "iso20022/" in index_text


def test_refusal_report_includes_exclusion_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _fixture_241(tmp_path, dump_files=60)
    index = library / "_shelf-index.md"
    (library / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    rebuild_shelf_index(library, index)
    (library / ".kb-index-ignore").write_text("ISO-20022-typo\n", encoding="utf-8")
    code = main([str(library)])
    err = capsys.readouterr().err
    assert code == 2
    assert "ISO-20022-typo" in err
    assert "matches no directory" in err


def test_unmatched_ignore_entry_surfaces_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = tmp_path / "library"
    _md(library / "a.md")
    (library / ".kb-index-ignore").write_text("ghost\n", encoding="utf-8")
    stats = rebuild_shelf_index(library, library / "_shelf-index.md")
    assert any("ghost" in w for w in stats.warnings)
    main([str(library)])
    assert "ghost" in capsys.readouterr().out


def test_no_ignore_file_output_unchanged(tmp_path: Path) -> None:
    library = tmp_path / "library"
    _md(library / "a.md")
    _md(library / "raw" / "skip.md")
    index = library / "_shelf-index.md"
    stats = rebuild_shelf_index(library, index)
    assert _entry_paths(index) == ["a.md"]
    assert (stats.added, stats.refused, stats.warnings) == (1, False, [])


# --- hook-clean output (EPIC #244: pre-commit is a blocking CI check) -------

from sdlc_knowledge_base_scripts import build_shelf_index as _bsi  # noqa: E402
from sdlc_knowledge_base_scripts.kb_stats import _parse_shelf_index  # noqa: E402
from sdlc_knowledge_base_scripts.priming import (  # noqa: E402
    _extract_shelf_index_terms,
)


def _entry(
    name: str, terms: list[str], links: list[str], facts: list[str]
) -> "_bsi.IndexEntry":
    return _bsi.IndexEntry(
        file_path=name,
        hash="a" * 64,
        terms=terms,
        facts=facts,
        links=links,
        layer="methodology",
        confidence="high",
    )


def _assert_hook_clean(text: str) -> None:
    assert text.endswith("\n") and not text.endswith("\n\n")
    for line in text.splitlines():
        assert line == line.rstrip(), f"trailing whitespace: {line!r}"


def test_render_entry_has_no_trailing_space_when_terms_and_links_empty() -> None:
    rendered = _bsi._render_entry(1, _entry("a.md", [], [], []))
    assert "**Terms:**\n" in rendered
    assert rendered.endswith("**Links:**\n")
    _assert_hook_clean(rendered)


def test_render_entry_non_empty_is_byte_identical_to_previous_format() -> None:
    rendered = _bsi._render_entry(2, _entry("b.md", ["x", "y"], ["l1", "l2"], ["f"]))
    assert rendered == (
        "## 2. b.md\n\n"
        f"**Hash:** {'a' * 64}\n"
        "**Layer:** methodology\n"
        "**Confidence:** high\n"
        "**Terms:** x, y\n"
        "**Facts:**\n- f\n"
        "**Links:** l1, l2\n"
    )


def test_index_with_empty_terms_and_links_is_hook_clean_and_parses() -> None:
    entries = [
        _entry("a.md", [], [], ["fact"]),
        _entry("b.md", ["t1", "t2"], ["l1"], ["fact"]),
        _entry("c.md", [], [], []),
    ]
    content = _bsi._build_index_content(entries, "local", "desc")
    _assert_hook_clean(content)

    parsed = _parse_shelf_index(content)
    assert [e.domains for e in parsed] == [[], ["t1", "t2"], []]
    assert [e.links for e in parsed] == [[], ["l1"], []]
    assert [e.facts_count for e in parsed] == [1, 1, 0]


def test_priming_terms_extraction_handles_empty_and_non_empty(
    tmp_path: Path,
) -> None:
    index = tmp_path / "_shelf-index.md"
    index.write_text(
        _bsi._build_index_content(
            [_entry("a.md", [], [], []), _entry("b.md", ["t1", "t2"], [], [])],
            "local",
            "desc",
        ),
        encoding="utf-8",
    )
    assert _extract_shelf_index_terms(index) == ["t1", "t2"]


def test_empty_library_index_is_hook_clean(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    index = lib / "_shelf-index.md"
    rebuild_shelf_index(lib, index, full=True)
    _assert_hook_clean(index.read_text(encoding="utf-8"))


def test_rebuilt_index_and_log_are_hook_clean_and_a_fixed_point(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "one.md").write_text("# One\n\nBody.\n", encoding="utf-8")
    (lib / "two.md").write_text("---\ntitle: Two\n---\n\nBody.\n", encoding="utf-8")
    index = lib / "_shelf-index.md"
    log = lib / "log.md"
    log.write_text("# Log\n", encoding="utf-8")

    rebuild_shelf_index(lib, index, full=True, log_path=log)
    first = index.read_text(encoding="utf-8")
    _assert_hook_clean(first)
    _assert_hook_clean(log.read_text(encoding="utf-8"))

    rebuild_shelf_index(lib, index, full=True, log_path=log)
    second = index.read_text(encoding="utf-8")

    def drop_timestamp(text: str) -> str:
        return "\n".join(
            line for line in text.splitlines() if "last_rebuilt" not in line
        )

    assert drop_timestamp(first) == drop_timestamp(second)
    _assert_hook_clean(log.read_text(encoding="utf-8"))


def test_append_to_log_adds_missing_final_newline_before_entry(
    tmp_path: Path,
) -> None:
    log = tmp_path / "log.md"
    log.write_text("# Log", encoding="utf-8")
    _bsi._append_to_log(log, _bsi.RebuildStats(), full=False)
    text = log.read_text(encoding="utf-8")
    assert text.startswith("# Log\n\n## [")
    _assert_hook_clean(text)

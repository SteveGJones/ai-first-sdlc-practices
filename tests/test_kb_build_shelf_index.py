"""Unit and integration tests for sdlc_knowledge_base_scripts.build_shelf_index."""
from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.build_shelf_index import (
    compute_hash,
    extract_facts,
    extract_links,
    extract_terms,
    parse_frontmatter,
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

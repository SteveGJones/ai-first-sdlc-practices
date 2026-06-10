"""Tests for the entailment verifier (grounding cap + judge + high_impact)."""

from __future__ import annotations

from sdlc_knowledge_base_scripts.contracts import Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.entailment import ground_claim


def _claim(span_text, page="a.md"):
    return Claim(text="c", cited_pages=[PageRef(library="local", page=page)], evidence_spans=[Span(page=page, text=span_text)])


PAGES = {"a.md": "The study found that cost fell 30% over two years."}


def test_verbatim_span_caps_supported():
    assert ground_claim(_claim("cost fell 30%"), PAGES) == EntailmentStatus.supported


def test_normalized_verbatim_caps_supported():
    assert ground_claim(_claim("COST   fell 30%"), PAGES) == EntailmentStatus.supported


def test_fuzzy_only_caps_partial():
    assert ground_claim(_claim("cost fell by thirty percent over two years"), PAGES) == EntailmentStatus.partial


def test_no_match_unsupported():
    assert ground_claim(_claim("revenue tripled"), PAGES) == EntailmentStatus.unsupported


def test_cited_page_not_in_read_set_unsupported():
    c = Claim(
        text="c",
        cited_pages=[PageRef(library="local", page="ghost.md")],
        evidence_spans=[Span(page="ghost.md", text="anything")],
    )
    assert ground_claim(c, PAGES) == EntailmentStatus.unsupported

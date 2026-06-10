"""Tests for the entailment verifier (grounding cap + judge + high_impact)."""

from __future__ import annotations

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.entailment import (
    classify_high_impact,
    ground_claim,
    judge_claim,
    verify_entailment,
)


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


def test_span_pointing_at_uncited_page_does_not_ground():
    # claim cites a.md but its span points at b.md (which IS in the read set) — must NOT ground off b.md
    from sdlc_knowledge_base_scripts.contracts import Claim as _C, PageRef as _P, Span as _S
    pages = {"a.md": "nothing relevant here", "b.md": "cost fell 30%"}
    c = _C(text="c", cited_pages=[_P(library="local", page="a.md")],
           evidence_spans=[_S(page="b.md", text="cost fell 30%")])
    assert ground_claim(c, pages) == EntailmentStatus.unsupported


def test_high_impact_numbers_and_modals():
    assert classify_high_impact("Cost fell 30% in 2024.") is True
    assert classify_high_impact("Teams should adopt trunk-based dev.") is True
    assert classify_high_impact("This must meet ISO 26262 compliance.") is True
    assert classify_high_impact("The topic is broadly discussed.") is False


def test_judge_claim_maps_backend_grade():
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "partial"}'
    assert judge_claim(_claim("cost fell 30%"), PAGES, backend=be) == EntailmentStatus.partial


def test_judge_invalid_grade_defaults_unsupported():
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "bogus"}'
    assert judge_claim(_claim("x"), PAGES, backend=be) == EntailmentStatus.unsupported


def _claim_with_text(text, span_text, page="a.md"):
    return Claim(
        text=text,
        cited_pages=[PageRef(library="local", page=page)],
        evidence_spans=[Span(page=page, text=span_text)],
    )


def test_verify_caps_below_judge(tmp_path):
    # span only fuzzy-matches (cap=partial); judge says supported; final = min = partial
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "supported"}'
    claim = _claim_with_text("cost fell 30% over two years", "cost fell by thirty percent over two years")
    ans = Answer(claims=[claim], rendered_text="")
    out = verify_entailment(ans, PAGES, backend=be)
    assert out.claims[0].entailment_status == EntailmentStatus.partial
    assert out.claims[0].high_impact is True   # has a number/percent word


def test_verify_judge_lowers_within_cap(tmp_path):
    # verbatim span (cap=supported); judge says unsupported; final = unsupported
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "unsupported"}'
    ans = Answer(claims=[_claim("cost fell 30%")], rendered_text="")
    out = verify_entailment(ans, PAGES, backend=be)
    assert out.claims[0].entailment_status == EntailmentStatus.unsupported


def test_verify_skips_judge_when_grounding_unsupported(tmp_path):
    calls = {"n": 0}
    be = FakeBackend()

    def gen(prompt, schema=None):
        calls["n"] += 1
        return '{"status": "supported"}'

    be.generate = gen
    ans = Answer(claims=[_claim("revenue tripled")], rendered_text="")   # no grounding -> unsupported
    out = verify_entailment(ans, PAGES, backend=be)
    assert out.claims[0].entailment_status == EntailmentStatus.unsupported
    assert calls["n"] == 0   # judge not called when grounding already unsupported

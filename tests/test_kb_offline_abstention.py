"""Slice 1 abstention contract + verifier hardening (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, SelectResult, Span
from sdlc_knowledge_base_scripts.entailment import RELEVANCE_FLOOR, ground_claim
from sdlc_knowledge_base_scripts.pipeline import _normalize_reason
from sdlc_knowledge_base_scripts.retrieval import reduce_shelf


def test_select_result_abstention_fields_default():
    s = SelectResult(page_ids=["a.md"])
    assert s.no_relevant_page is False and s.abstention_reason is None
    s2 = SelectResult(page_ids=[], no_relevant_page=True, abstention_reason="nope")
    assert s2.no_relevant_page is True and s2.abstention_reason == "nope"


def test_answer_abstention_fields_default():
    a = Answer(claims=[], rendered_text="x")
    assert a.abstained is False and a.abstention_reason is None
    a2 = Answer(abstained=True, abstention_reason="no supported claims")
    assert a2.abstained is True and a2.rendered_text == "" and a2.abstention_reason == "no supported claims"


def test_normalize_reason():
    assert _normalize_reason("  a\n  b  ", "fb") == "a b"
    assert _normalize_reason(None, "fb") == "fb"
    assert _normalize_reason("", "fb") == "fb"
    assert _normalize_reason("   ", "fb") == "fb"
    assert len(_normalize_reason("x" * 500, "fb")) <= 200


_SHELF = ("<!-- format_version: 1 -->\n# Shelf Index\n\n"
          "## 1. a.md\nHash: x\nLayer: evidence\nTerms: alpha\n\n"
          "## 2. b.md\nHash: y\nLayer: domain\nTerms: beta\n\n"
          "## 3. c.md\nHash: z\nLayer: domain\nTerms: gamma\n")


def test_reduce_shelf_keeps_full_blocks_in_order_from_text():
    out = reduce_shelf(_SHELF, ["c.md", "a.md"])
    assert out.index("c.md") < out.index("a.md")      # order preserved
    assert "Terms: gamma" in out and "Terms: alpha" in out  # full entry blocks, not just headers
    assert "b.md" not in out                           # excluded


# ---------------------------------------------------------------------------
# Task 4: claim<->span relevance floor in ground_claim
# ---------------------------------------------------------------------------

def _claim(text, page, span):
    return Claim(text=text, cited_pages=[PageRef(library="local", page=page)],
                 evidence_spans=[Span(page=page, text=span)])


def test_ground_claim_rejects_verbatim_but_irrelevant_span():
    pages = {"dora.md": "DORA Metrics. Elite teams deploy multiple times per day."}
    c = _claim("The company payroll schedule is not mentioned.", "dora.md", "DORA Metrics")
    assert ground_claim(c, pages) == EntailmentStatus.unsupported


def test_ground_claim_supports_relevant_verbatim_span():
    pages = {"dora.md": "Elite teams deploy multiple times per day."}
    c = _claim("Elite teams deploy multiple times per day.", "dora.md", "deploy multiple times per day")
    assert ground_claim(c, pages) == EntailmentStatus.supported


def test_ground_claim_supports_legitimate_negative():
    pages = {"sdlc-solo.md": "The solo method uses feature branches and requires no formal sign-off."}
    c = _claim("The solo method does not require formal sign-off.", "sdlc-solo.md", "requires no formal sign-off")
    assert ground_claim(c, pages) == EntailmentStatus.supported


def test_relevance_floor_value():
    assert RELEVANCE_FLOOR == 0.20


# ---------------------------------------------------------------------------
# Task 5: epistemic-absence guard in verify_entailment
# ---------------------------------------------------------------------------

from sdlc_knowledge_base_scripts.entailment import is_epistemic_absence  # noqa: E402


def test_epistemic_absence_matches_all_trace_forms():
    yes = ["The payroll schedule is not mentioned in the provided documents.",
           "The provided documents do not contain information regarding a CEO.",
           "I cannot find any information regarding dental insurance in the provided documents.",
           "The location of the London office is not provided in the source text.",
           "No information regarding the gym opening time."]
    for t in yes:
        assert is_epistemic_absence(t) is True, t


def test_epistemic_absence_ignores_legitimate_negatives():
    no = ["The solo method does not require formal sign-off.",
          "Feature flags should be removed when stale.",
          "Trunk-based development avoids long-lived branches."]
    for t in no:
        assert is_epistemic_absence(t) is False, t


# ---------------------------------------------------------------------------
# Task 6: judge_claim receives declared spans + asks for relevance
# ---------------------------------------------------------------------------

from sdlc_knowledge_base_scripts.entailment import judge_claim  # noqa: E402


def test_judge_claim_prompt_includes_declared_spans():
    seen = {}

    class B:
        def generate(self, prompt, schema=None):
            seen["p"] = prompt
            return '{"status": "supported"}'

    c = _claim("Elite teams deploy daily.", "dora.md", "deploy multiple times per day")
    judge_claim(c, {"dora.md": "Elite teams deploy multiple times per day."}, backend=B())
    assert "deploy multiple times per day" in seen["p"]      # declared span surfaced
    assert "relevan" in seen["p"].lower()                    # asks about relevance


# ---------------------------------------------------------------------------
# Task 7: shared finalize_answer (renderer-agnostic, both outcomes)
# ---------------------------------------------------------------------------

from sdlc_knowledge_base_scripts.publication import finalize_answer  # noqa: E402


def test_finalize_answer_empty_render_abstains():
    a = Answer(claims=[])
    finalize_answer(a, "", abstain_reason="no supported claims")
    assert a.abstained is True and a.rendered_text == "" and a.abstention_reason == "no supported claims"


def test_finalize_answer_nonempty_render_clears_stale_flag():
    a = Answer(claims=[], abstained=True, abstention_reason="stale")
    finalize_answer(a, "Some answer text.", abstain_reason="x")
    assert a.abstained is False and a.rendered_text == "Some answer text." and a.abstention_reason is None

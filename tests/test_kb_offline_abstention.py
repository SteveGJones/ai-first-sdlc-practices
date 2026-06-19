"""Slice 1 abstention contract + verifier hardening (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.contracts import Answer, SelectResult
from sdlc_knowledge_base_scripts.pipeline import _normalize_reason


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

"""Saved-answer persistence tests. kb-offline M2a (#211)."""
from __future__ import annotations

import pytest

from sdlc_knowledge_base_scripts.answers import (
    SavedAnswer,
    compute_ref,
    load_answer,
    save_answer,
)
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span


def _answer():
    c = Claim(text="Elite teams deploy multiple times per day.",
              cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="multiple times per day")])
    c.entailment_status = EntailmentStatus.supported
    return Answer(claims=[c], rendered_text="Elite teams deploy multiple times per day.")


def test_compute_ref_is_deterministic_and_short():
    r1 = compute_ref("how often deploy?", "Elite teams deploy multiple times per day.")
    r2 = compute_ref("how often deploy?", "Elite teams deploy multiple times per day.")
    r3 = compute_ref("how often deploy?", "different text")
    assert r1 == r2 and r1 != r3
    assert r1.isalnum() and len(r1) <= 16


def test_save_then_load_round_trip(tmp_path):
    ref = save_answer(str(tmp_path), "how often deploy?", _answer(),
                      libraries=["local"], page_ids=["dora.md"])
    saved = load_answer(str(tmp_path), ref)
    assert isinstance(saved, SavedAnswer)
    assert saved.ref == ref
    assert saved.question == "how often deploy?"
    assert saved.page_ids == ["dora.md"]
    assert saved.answer.claims[0].entailment_status == EntailmentStatus.supported
    assert (tmp_path / ".kb-offline" / "answers" / f"{ref}.json").is_file()


def test_load_missing_ref_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_answer(str(tmp_path), "deadbeef")

"""Tests for sdlc_knowledge_base_scripts.contracts."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdlc_knowledge_base_scripts.contracts import (
    Answer, Claim, Confidence, ExtractJSON, ExtractTarget,
    MutationAction, MutationProposal, PageRef, Span,
)


def test_extractjson_minimal_and_defaults():
    e = ExtractJSON(source="raw/a.md")
    assert e.findings == [] and e.confidence == Confidence.medium and e.targets == []


def test_extractjson_with_targets():
    e = ExtractJSON(source="a.md", findings=["f"],
                    targets=[ExtractTarget(file="topic.md", finding_idx=[0])])
    assert e.targets[0].file == "topic.md"


def test_claim_entailment_status_optional_and_defaults_none():
    c = Claim(text="x", cited_pages=[PageRef(library="local", page="p.md")],
              evidence_spans=[Span(page="p.md", text="quote")])
    assert c.entailment_status is None
    assert c.high_impact is False


def test_answer_holds_claims():
    a = Answer(claims=[Claim(text="x")], rendered_text="X.")
    assert a.claims[0].text == "x"


def test_mutation_proposal_requires_action_and_target():
    m = MutationProposal(target_file="t.md", action=MutationAction.create,
                         frontmatter={"layer": "domain", "confidence": "medium"}, body="# T")
    assert m.action == MutationAction.create and m.expected_hash is None


def test_invalid_confidence_rejected():
    with pytest.raises(ValidationError):
        ExtractJSON(source="a.md", confidence="bogus")


def test_span_library_defaults_to_none_and_is_optional():
    # backward compatible: existing two-arg construction unaffected
    s = Span(page="a.md", text="x")
    assert s.library is None
    # new optional field accepts a handle
    s2 = Span(library="acme-kb", page="a.md", text="x")
    assert s2.library == "acme-kb"

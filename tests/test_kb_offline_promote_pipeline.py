"""promote body-drafting op tests. kb-offline M2a (#211)."""
from __future__ import annotations

import json

import pytest

from sdlc_knowledge_base_scripts.answers import SavedAnswer
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.pipeline import promote


def _saved(*statuses):
    claims = []
    for i, st in enumerate(statuses):
        c = Claim(text=f"claim {i}", cited_pages=[PageRef(library="local", page="a.md")],
                  evidence_spans=[Span(page="a.md", text=f"span {i}")])
        c.entailment_status = st
        claims.append(c)
    ans = Answer(claims=claims, rendered_text="rendered")
    return SavedAnswer(ref="r1", question="q?", libraries=["local"], page_ids=["a.md"],
                       answer=ans, rendered_text="rendered")


def test_promote_drafts_body_from_supported_claims_only():
    saved = _saved(EntailmentStatus.supported, EntailmentStatus.partial, EntailmentStatus.unsupported)
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"body": "# Title\n\nClaim 0 is grounded."})
    be = FakeBackend()
    be.generate = gen
    body = promote(saved, target_file="topic.md", action="create", existing_content=None, backend=be)
    assert body == "# Title\n\nClaim 0 is grounded."
    assert "claim 0" in captured["prompt"]
    assert "claim 1" not in captured["prompt"] and "claim 2" not in captured["prompt"]


def test_promote_zero_supported_raises():
    saved = _saved(EntailmentStatus.partial, EntailmentStatus.unsupported)
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"body": "x"})
    with pytest.raises(ValueError, match="no supported claims"):
        promote(saved, target_file="topic.md", action="create", existing_content=None, backend=be)


def test_promote_repairs_then_fails_on_invalid_json():
    saved = _saved(EntailmentStatus.supported)
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: "not json"
    with pytest.raises(ValueError, match="promote failed"):
        promote(saved, target_file="t.md", action="create", existing_content=None, backend=be, max_repairs=1)

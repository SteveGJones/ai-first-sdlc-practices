"""Federation query tests. kb-offline M2b (#211)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.audit import VALID_EVENT_TYPES
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.federation import (
    _norm, canonicalize_attribution, merge_answers, query_one_library, render_federated,
)


def test_cross_library_query_is_a_valid_event_type():
    assert "cross_library_query" in VALID_EVENT_TYPES


def _lib(tmp_path, name, page, body):
    lib = tmp_path / name
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
    (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
    return lib


def test_query_one_library_returns_verified_answer(tmp_path):
    lib = _lib(tmp_path, "doracorp", "dora.md", "Elite teams deploy multiple times per day.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["dora.md"]})
        return json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                       "cited_pages": [{"library": "local", "page": "dora.md"}],
                                       "evidence_spans": [{"page": "dora.md",
                                                           "text": "deploy multiple times per day"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    answer, page_ids = query_one_library(str(lib), "how often deploy?", backend=be, priming=None)
    assert page_ids == ["dora.md"]
    assert answer.claims[0].entailment_status == EntailmentStatus.supported


def _claim(text, page, status):
    c = Claim(text=text, cited_pages=[PageRef(library="local", page=page)],
              evidence_spans=[Span(page=page, text="x")])
    c.entailment_status = status
    return c


def test_merge_dedupes_identical_and_unions_handles():
    a1 = Answer(claims=[_claim("Deploy daily.", "dora.md", EntailmentStatus.supported)], rendered_text="")
    a2 = Answer(claims=[_claim("Deploy daily.", "ops.md", EntailmentStatus.supported),
                        _claim("Use canary.", "ops.md", EntailmentStatus.supported)], rendered_text="")
    merged, handle_sets = merge_answers([("dora-corp", a1), ("acme-kb", a2)])
    texts = [c.text for c in merged.claims]
    assert texts.count("Deploy daily.") == 1
    assert set(handle_sets[_norm("Deploy daily.")]) == {"dora-corp", "acme-kb"}
    assert "Use canary." in texts
    deploy = next(c for c in merged.claims if c.text == "Deploy daily.")
    assert {r.library for r in deploy.cited_pages} == {"dora-corp", "acme-kb"}


def test_merge_attribution_survives_case_whitespace_variants():
    # same claim, different casing/whitespace across libraries -> one merged claim,
    # BOTH handles attributed in BOTH cited_pages AND the rendered suffix.
    from sdlc_knowledge_base_scripts.federation import _norm
    a1 = Answer(claims=[_claim("Deploy daily.", "dora.md", EntailmentStatus.supported)], rendered_text="")
    a2 = Answer(claims=[_claim("deploy  daily.", "ops.md", EntailmentStatus.supported)], rendered_text="")
    merged, handle_sets = merge_answers([("dora-corp", a1), ("acme-kb", a2)])
    assert len(merged.claims) == 1                                  # deduped despite variant
    assert set(handle_sets[_norm("Deploy daily.")]) == {"dora-corp", "acme-kb"}
    rendered, _ = render_federated(merged, handle_sets)
    assert "dora-corp" in rendered and "acme-kb" in rendered        # BOTH handles in the suffix


def test_render_federated_attributes_and_applies_policy():
    a = Answer(claims=[_claim("Deploy daily.", "dora.md", EntailmentStatus.supported),
                       _claim("Maybe canary.", "dora.md", EntailmentStatus.partial),
                       _claim("Unfounded.", "dora.md", EntailmentStatus.unsupported)], rendered_text="")
    merged, handle_sets = merge_answers([("dora-corp", a)])
    rendered, rejected = render_federated(merged, handle_sets)
    assert "Deploy daily." in rendered and "[dora-corp]" in rendered
    assert "partially supported" in rendered.lower()
    assert "Unfounded." not in rendered
    assert any("Unfounded." in r["text"] for r in rejected)


def test_canonicalize_attribution_splits_qualified_ids():
    c = Claim(
        text="Teams deploy daily.",
        cited_pages=[PageRef(library="x", page="acme-kb/a.md"),
                     PageRef(library="x", page="dora-corp/ops.md")],
        evidence_spans=[Span(page="acme-kb/a.md", text="deploy daily")],
    )
    c.entailment_status = EntailmentStatus.supported
    out = canonicalize_attribution(Answer(claims=[c], rendered_text=""))
    refs = out.claims[0].cited_pages
    assert (refs[0].library, refs[0].page) == ("acme-kb", "a.md")
    assert (refs[1].library, refs[1].page) == ("dora-corp", "ops.md")
    span = out.claims[0].evidence_spans[0]
    assert (span.library, span.page, span.text) == ("acme-kb", "a.md", "deploy daily")
    # grading preserved (never re-graded)
    assert out.claims[0].entailment_status == EntailmentStatus.supported

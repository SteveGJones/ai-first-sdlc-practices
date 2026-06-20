"""Tests for kb-offline prompts + pipeline."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts import prompts
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.pipeline import extract


def test_extract_fragment_is_nonempty_constant():
    assert isinstance(prompts.EXTRACT_FRAGMENT, str)
    assert "JSON" in prompts.EXTRACT_FRAGMENT
    assert "targets" in prompts.EXTRACT_FRAGMENT


def test_reduce_fragment_states_constraints():
    assert "exactly one file" in prompts.REDUCE_FRAGMENT.lower()


def _shelf(tmp_path):
    s = tmp_path / "_shelf-index.md"
    s.write_text("<!-- format_version: 1 -->\n# Shelf\n- topic.md\n")
    return s


def test_extract_parses_valid_json(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("source text")
    payload = json.dumps(
        {
            "source": "a.md",
            "findings": ["f"],
            "confidence": "medium",
            "targets": [{"file": "topic.md", "finding_idx": [0]}],
        }
    )
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be)
    assert result.findings == ["f"]
    assert result.targets[0].file == "topic.md"


def test_extract_repairs_then_succeeds(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("source text")
    good = json.dumps(
        {"source": "a.md", "findings": ["f"], "confidence": "low", "targets": []}
    )
    seq = ["not json at all", good]
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: seq.pop(0)  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be, max_repairs=1)
    assert result.confidence.value == "low"


def test_extract_fails_after_repair_budget(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("x")
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: "still not json"  # type: ignore
    import pytest

    with pytest.raises(ValueError):
        extract(str(src), _shelf(tmp_path), backend=be, max_repairs=1)


def test_synthesize_backfills_cited_pages_from_spans_when_empty():
    """Root cause of gemma4:12b fact_recall=0.0 (#211): the model attributes the page via
    evidence_spans and leaves claims[].cited_pages empty, so ground_claim (which requires
    span.page in cited_pages) orphans every span -> unsupported -> empty answer. synthesize
    must back-fill cited_pages from the spans' declared pages so grounding can attribute it."""
    from sdlc_knowledge_base_scripts.contracts import EntailmentStatus
    from sdlc_knowledge_base_scripts.entailment import ground_claim
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "Elite teams deploy multiple times per day.",
            "cited_pages": [],
            "evidence_spans": [{"page": "dora.md", "text": "deploy multiple times per day"}],
        }],
        "rendered_text": "Elite teams deploy multiple times per day.",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    pages = [{"page": "dora.md", "content": "Elite teams deploy multiple times per day."}]
    ans = synthesize("q", pages, backend=be)
    assert [r.page for r in ans.claims[0].cited_pages] == ["dora.md"]  # back-filled from span
    cap = ground_claim(ans.claims[0], {"dora.md": "Elite teams deploy multiple times per day."})
    assert cap == EntailmentStatus.supported  # grounding now attributes the verbatim span


def test_synthesize_preserves_explicit_cited_pages():
    """When the model DOES populate cited_pages, synthesize must not overwrite it — the
    anti-mis-attribution rule (span grounds only against a cited page) must be preserved."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "x",
            "cited_pages": [{"library": "local", "page": "a.md"}],
            "evidence_spans": [{"page": "b.md", "text": "y"}],
        }],
        "rendered_text": "x",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    ans = synthesize("q", [{"page": "a.md", "content": "..."}], backend=be)
    assert [r.page for r in ans.claims[0].cited_pages] == ["a.md"]  # unchanged


def test_synthesize_strips_trailing_sentinel_token_first_attempt(tmp_path):
    """gemma4:12b emits a trailing <|tool_response> sentinel after its JSON. The pipeline
    must strip known chat-template sentinels before parsing so a valid answer is NOT
    spuriously failed (and no repair budget is burned). Regression for #211 M3 finding."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps(
        {
            "claims": [
                {
                    "text": "c1",
                    "cited_pages": [{"library": "local", "page": "topic.md"}],
                    "evidence_spans": [{"page": "topic.md", "text": "verbatim"}],
                }
            ],
            "rendered_text": "answer",
        }
    )
    contaminated = payload + "<|tool_response>"
    calls = {"n": 0}

    def gen(prompt, schema=None):
        calls["n"] += 1
        return contaminated

    be = FakeBackend()
    be.generate = gen  # type: ignore
    pages = [{"page": "topic.md", "content": "verbatim"}]
    ans = synthesize("q", pages, backend=be, max_repairs=1)
    assert calls["n"] == 1  # parsed first attempt — no repair burned
    assert ans.rendered_text == "answer"
    assert ans.claims[0].text == "c1"


def test_extract_strips_wrapped_sentinel_tokens(tmp_path):
    """Leading + trailing <|...|> sentinels (e.g. <|tool_response|>) are stripped before
    the pydantic model_validate_json parse path."""
    src = tmp_path / "a.md"
    src.write_text("source text")
    payload = json.dumps(
        {"source": "a.md", "findings": ["f"], "confidence": "low", "targets": []}
    )
    contaminated = f"<|tool_response|>\n{payload}\n<|tool_response|>"
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: contaminated  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be, max_repairs=0)
    assert result.findings == ["f"]


def test_promote_strips_trailing_sentinel_in_json_loads_path(tmp_path):
    """The promote body path uses json.loads directly — it must also be sanitized."""
    from sdlc_knowledge_base_scripts.contracts import (
        Claim,
        EntailmentStatus,
        PageRef,
    )
    from sdlc_knowledge_base_scripts.pipeline import promote

    class _Saved:
        question = "q"

        class answer:  # noqa: N801
            claims = [
                Claim(
                    text="c1",
                    cited_pages=[PageRef(library="local", page="topic.md")],
                    entailment_status=EntailmentStatus.supported,
                )
            ]

    contaminated = json.dumps({"body": "# Body\n- text"}) + "<|tool_response>"
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: contaminated  # type: ignore
    body = promote(
        _Saved(), target_file="t.md", action="create", existing_content=None,
        backend=be, max_repairs=0,
    )
    assert body == "# Body\n- text"


def test_reduce_returns_validatable_create_proposal(tmp_path):
    from sdlc_knowledge_base_scripts.contracts import MutationAction
    from sdlc_knowledge_base_scripts.pipeline import reduce_to_proposal

    proposal_json = json.dumps(
        {
            "target_file": "fresh.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "medium"},
            "body": "# Fresh\n- finding",
            "citations": ["Src 2026"],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: proposal_json  # type: ignore
    proposal = reduce_to_proposal(
        target_file="fresh.md",
        is_new=True,
        extracts=[{"source": "a.md", "findings": ["finding"]}],
        existing_content=None,
        backend=be,
    )
    assert proposal.action == MutationAction.create
    assert proposal.target_file == "fresh.md"
    assert proposal.expected_hash is None


def test_select_explicit_abstention(tmp_path):
    from sdlc_knowledge_base_scripts.pipeline import select
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps(
        {"page_ids": [], "no_relevant_page": True, "abstention_reason": "  nothing\n fits "})
    r = select("q", _shelf(tmp_path), backend=be, known_pages={"topic.md"})
    assert r.no_relevant_page is True and r.page_ids == [] and r.abstention_reason == "nothing fits"


def test_select_all_filtered_abstains(tmp_path):
    from sdlc_knowledge_base_scripts.pipeline import select
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["ghost.md"]})
    r = select("q", _shelf(tmp_path), backend=be, known_pages={"topic.md"})
    assert r.no_relevant_page is True and r.page_ids == [] and "id/layer" in r.abstention_reason


def test_select_success_clears_reason(tmp_path):
    from sdlc_knowledge_base_scripts.pipeline import select
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["topic.md"]})
    r = select("q", _shelf(tmp_path), backend=be, known_pages={"topic.md"})
    assert r.no_relevant_page is False and r.page_ids == ["topic.md"] and r.abstention_reason is None

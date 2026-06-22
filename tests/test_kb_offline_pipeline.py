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


def test_synthesize_abstains_zero_claims():
    from sdlc_knowledge_base_scripts.pipeline import synthesize
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps(
        {"claims": [], "rendered_text": "", "abstained": True, "abstention_reason": "pages don't answer"})
    ans = synthesize("q", [{"page": "a.md", "content": "x"}], backend=be)
    assert ans.abstained is True
    assert ans.claims == [] and ans.rendered_text == "" and ans.abstention_reason == "pages don't answer"


def test_synthesize_abstains_clears_claims_and_text():
    """Invariant: Answer.abstained => claims=[], rendered_text="". Even if the model emits an
    absence-claim alongside abstained=True, synthesize must clear both fields so no published
    claim escapes under the abstention flag."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({
        "claims": [{"text": "The answer is absent.", "cited_pages": [], "evidence_spans": []}],
        "rendered_text": "The answer is absent from the pages.",
        "abstained": True,
        "abstention_reason": "  pages do not answer  ",
    })
    ans = synthesize("q", [{"page": "a.md", "content": "x"}], backend=be)
    assert ans.abstained is True
    assert ans.claims == []
    assert ans.rendered_text == ""
    assert ans.abstention_reason == "pages do not answer"


def test_synthesize_recovers_corrupted_span_id_and_backfills():
    """q035 shape: raw cited_pages omitted, corrupted id only on the span. Normalizing the
    span (before back-fill) lets the back-fill produce a correct citation and grounding pass."""
    from sdlc_knowledge_base_scripts.contracts import EntailmentStatus
    from sdlc_knowledge_base_scripts.entailment import ground_claim
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "The single-team method suits one collaborating team.",
            "evidence_spans": [{"page": "sdlc-single-formm.md",
                                "text": "The single-team method suits one collaborating team."}],
        }],
        "rendered_text": "ok",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    pages = [{"page": "sdlc-single-team.md",
              "content": "The single-team method suits one collaborating team."}]
    sink: list = []
    ans = synthesize("q", pages, backend=be, rewrites_sink=sink)
    # span normalized, then back-fill -> correct citation
    assert [s.page for s in ans.claims[0].evidence_spans] == ["sdlc-single-team.md"]
    assert [r.page for r in ans.claims[0].cited_pages] == ["sdlc-single-team.md"]
    cap = ground_claim(ans.claims[0],
                       {"sdlc-single-team.md": "The single-team method suits one collaborating team."})
    assert cap == EntailmentStatus.supported
    # exactly one evidence_span rewrite, zero cited_page rewrites; 3-dp score
    kinds = [r["reference_kind"] for r in sink]
    assert kinds == ["evidence_span"]
    r = sink[0]
    assert (r["from"], r["to"]) == ("sdlc-single-formm.md", "sdlc-single-team.md")
    assert r["handle"] == "" and r["claim_index"] == 0 and r["reference_index"] == 0
    assert r["candidates"] == ["sdlc-single-team.md"] and r["stage"] == "synthesize"
    assert r["score"] == round(r["score"], 3) and 0.75 <= r["score"] <= 1.0


def test_synthesize_drops_genuinely_different_id_no_rewrite():
    """q052 shape: corrupted id is genuinely different (below floor) -> untouched, no record."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "x",
            "evidence_spans": [{"page": "pair-summary.md", "text": "y"}],
        }],
        "rendered_text": "x",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    sink: list = []
    ans = synthesize("q", [{"page": "pair-programming.md", "content": "..."}],
                     backend=be, rewrites_sink=sink)
    assert [s.page for s in ans.claims[0].evidence_spans] == ["pair-summary.md"]  # untouched
    assert sink == []


def test_synthesize_cross_handle_match_not_recovered():
    """A qualified-id corruption whose only good match is under a DIFFERENT handle must drop."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "x",
            "evidence_spans": [{"page": "alpha/sdlc-single-formm.md", "text": "y"}],
        }],
        "rendered_text": "x",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    sink: list = []
    # only candidate is under handle 'beta' -> different bucket -> no recovery
    ans = synthesize("q", [{"page": "beta/sdlc-single-team.md", "content": "..."}],
                     backend=be, rewrites_sink=sink)
    assert [s.page for s in ans.claims[0].evidence_spans] == ["alpha/sdlc-single-formm.md"]
    assert sink == []


def test_synthesize_without_sink_still_recovers():
    """Production callers (federation/accel) pass no sink: recovery still happens, no crash."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "z",
            "evidence_spans": [{"page": "sdlc-single-formm.md", "text": "z"}],
        }],
        "rendered_text": "z",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    ans = synthesize("q", [{"page": "sdlc-single-team.md", "content": "z"}], backend=be)
    assert [s.page for s in ans.claims[0].evidence_spans] == ["sdlc-single-team.md"]


def test_synthesize_safety_rewrite_target_always_in_read_set():
    """Invariant: any rewrite 'to' is a page actually read, same handle as 'from'."""
    from sdlc_knowledge_base_scripts.cited_page_normalize import resolve_cited_page  # noqa: F401
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{"text": "z", "evidence_spans": [{"page": "sdlc-single-formm.md", "text": "z"}]}],
        "rendered_text": "z",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    read = ["sdlc-single-team.md"]
    sink: list = []
    synthesize("q", [{"page": p, "content": "z"} for p in read], backend=be, rewrites_sink=sink)
    for r in sink:
        assert r["to"] in read
        assert (r["to"].split("/", 1)[0] if "/" in r["to"] else "") == r["handle"]

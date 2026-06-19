"""Pure eval-trace derivation helpers (#211)."""
from __future__ import annotations

import json as _json
from pathlib import Path

from sdlc_knowledge_base_scripts.eval.trace import derive_model_calls
from sdlc_knowledge_base_scripts.eval.trace import classify_select_drops
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.eval.runner import RecordingBackend, run_questions, run_verifier_labels, score_run
from sdlc_knowledge_base_scripts.eval.suite import load_questions, load_verifier_labels

SMOKE = Path("plugins/sdlc-knowledge-base/eval/suite/smoke")


def _rec(stage, first_pass, ok=True):
    return {"stage": stage, "first_pass": first_pass, "json_parse_ok": ok,
            "elapsed_ms": 1.0, "raw": "{}"}


def test_derive_select_repair_then_synth_then_two_judges_success():
    slice_ = [_rec("select", True, ok=False), _rec("select", False), _rec("synthesize", True),
              _rec("judge", True), _rec("judge", True)]
    calls = derive_model_calls(slice_, errored=False, error_msg="")
    assert (calls[0]["stage_invocation"], calls[0]["repair_attempt"]) == (1, 1)
    assert (calls[1]["stage_invocation"], calls[1]["repair_attempt"]) == (1, 2)
    assert (calls[2]["stage_invocation"], calls[2]["repair_attempt"]) == (1, 1)
    assert (calls[3]["stage_invocation"], calls[3]["repair_attempt"]) == (1, 1)
    assert (calls[4]["stage_invocation"], calls[4]["repair_attempt"]) == (2, 1)
    assert [c["accepted"] for c in calls] == [False, True, True, True, True]


def test_derive_accepted_on_select_repair_exhaustion_error():
    slice_ = [_rec("select", True, ok=False), _rec("select", False, ok=False)]
    calls = derive_model_calls(slice_, errored=True, error_msg="select failed after 1 repair(s): ...")
    assert [c["accepted"] for c in calls] == [False, False]


def test_derive_accepted_on_synth_exhaustion_keeps_select_accepted():
    slice_ = [_rec("select", True), _rec("synthesize", True, ok=False), _rec("synthesize", False, ok=False)]
    calls = derive_model_calls(slice_, errored=True, error_msg="synthesize failed after 1 repair(s): ...")
    assert calls[0]["accepted"] is True
    assert calls[1]["accepted"] is False and calls[2]["accepted"] is False


def test_derive_accepted_on_non_model_error_keeps_all_invocation_tails():
    slice_ = [_rec("select", True), _rec("synthesize", True)]
    calls = derive_model_calls(slice_, errored=True, error_msg="publish exploded")
    assert calls[0]["accepted"] is True and calls[1]["accepted"] is True


def test_derive_empty_records_returns_empty():
    assert derive_model_calls([], errored=False, error_msg="") == []


def test_derive_non_model_error_with_repair_accepts_completed_tail():
    # a completed select that had a repair, then a non-model (e.g. publish) error
    slice_ = [_rec("select", True, ok=False), _rec("select", False), _rec("synthesize", True)]
    calls = derive_model_calls(slice_, errored=True, error_msg="publish exploded")
    # select repair tail accepted, synthesize accepted (model stages completed before the downstream error)
    assert calls[0]["accepted"] is False           # first select attempt (not the tail)
    assert calls[1]["accepted"] is True            # select invocation tail
    assert calls[2]["accepted"] is True            # synthesize tail


def test_classify_select_drops_unknown_and_filtered():
    known = {"dora.md", "ci-cd.md", "sdlc-assured.md"}
    eligible = {"dora.md", "ci-cd.md"}                     # sdlc-assured filtered out by layer
    model_selected = ["dora.md", "telemetry.md", "sdlc-assured.md"]
    final = ["dora.md"]
    dropped, eligible_unselected = classify_select_drops(model_selected, final, known, eligible)
    by_id = {d["id"]: d["reason"] for d in dropped}
    assert by_id == {"telemetry.md": "unknown_id", "sdlc-assured.md": "filtered_out"}
    assert eligible_unselected == ["ci-cd.md"]             # eligible but the model didn't pick it


def test_classify_select_drops_empty_when_all_final():
    dropped, unsel = classify_select_drops(["dora.md"], ["dora.md"], {"dora.md"}, {"dora.md"})
    assert dropped == [] and unsel == []


def _smoke_gen():
    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _json.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else _json.dumps({"page_ids": []})
        return _json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                        "cited_pages": [{"library": "local", "page": "dora.md"}],
                                        "evidence_spans": [{"page": "dora.md",
                                                            "text": "deploy multiple times per day"}]}],
                            "rendered_text": "Elite teams deploy multiple times per day."})
    return gen


def test_run_questions_emits_trace_rows():
    qs = load_questions(SMOKE / "questions.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = _smoke_gen()
    trace: list = []
    rows = run_questions(str(SMOKE / "library"), qs, backend=rec, trace=trace)
    assert len(rows) == len(qs)
    assert len(trace) == len(qs)
    t = next(r for r in trace if r["id"] == "s1")
    assert t["type"] == "question"
    assert t["page_ids"] == ["dora.md"]
    assert any(c["stage"] == "select" for c in t["model_calls"])
    assert any(c["stage"] == "synthesize" for c in t["model_calls"])
    claim = t["claims"][0]
    assert claim["ground_cap"] == "supported" and claim["final_status"] == "supported"
    assert claim["evidence_spans"][0]["verbatim_in_page"] is True
    assert claim["judge_raw"] == '{"status": "supported"}'
    assert "elapsed_s" in t
    # Fix 5: no row degraded to an assembly-error stub
    assert all("trace_error" not in r for r in trace)
    # Fix 5: ABSTAIN / zero-claim question produces a clean row
    abst = next((r for r in trace if r["did_abstain"]), None)
    if abst is not None:
        assert abst["claims"] == [] and "trace_error" not in abst


def test_run_questions_no_trace_unchanged():
    qs = load_questions(SMOKE / "questions.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = _smoke_gen()
    rows = run_questions(str(SMOKE / "library"), qs, backend=rec)
    assert len(rows) == len(qs) and all("error" in r for r in rows)


def test_run_verifier_labels_emits_isolated_trace_rows():
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = lambda prompt, schema=None: '{"status": "supported"}'
    trace: list = []
    run_verifier_labels(str(SMOKE / "library"), labels, backend=rec, trace=trace)
    assert len(trace) == len(labels)
    for row in trace:
        assert row["type"] == "verifier"
        assert all(c["stage"] == "judge" for c in row["model_calls"])   # only this label's call(s)
        assert "predicted_status" in row and "gold_status" in row


def test_score_run_threads_trace_to_both():
    qs = load_questions(SMOKE / "questions.jsonl")
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    be = FakeBackend()
    be.generate = _smoke_gen()
    trace: list = []
    score_run(str(SMOKE / "library"), qs, labels, backend=be, trace=trace)
    assert any(r["type"] == "question" for r in trace)
    assert any(r["type"] == "verifier" for r in trace)


def test_trace_surfaces_pre_normalization_empty_cited_pages():
    # synthesize emits cited_pages:[] (the gemma bug); pipeline back-fills from the span.
    # The trace must show BOTH: raw with cited_pages:[] AND claims[].cited_pages back-filled.
    def gen(prompt, schema=None):
        if prompt.startswith("Judge whether"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _json.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else _json.dumps({"page_ids": []})
        return _json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                        "cited_pages": [],
                                        "evidence_spans": [{"page": "dora.md",
                                                            "text": "deploy multiple times per day"}]}],
                            "rendered_text": "Elite teams deploy multiple times per day."})
    qs = [q for q in load_questions(SMOKE / "questions.jsonl") if q.id == "s1"]
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = gen
    trace: list = []
    run_questions(str(SMOKE / "library"), qs, backend=rec, trace=trace)
    t = trace[0]
    synth_raw = next(c["raw"] for c in t["model_calls"] if c["stage"] == "synthesize")
    assert '"cited_pages": []' in synth_raw            # pre-normalization output visible
    assert t["claims"][0]["cited_pages"] == ["dora.md"]  # back-filled in the normalized claim
    assert t["claims"][0]["ground_cap"] == "supported"   # grounding now attributes the span


def test_trace_error_row_carries_model_calls():
    # select succeeds, synthesize returns invalid JSON -> synthesize repair-exhausts -> raises.
    def gen(prompt, schema=None):
        if "Shelf-index" in prompt:
            return _json.dumps({"page_ids": ["dora.md"]})
        return "not json at all"     # synthesize never validates -> ValueError
    qs = [q for q in load_questions(SMOKE / "questions.jsonl") if q.id == "s1"][:1]
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = gen
    trace: list = []
    rows = run_questions(str(SMOKE / "library"), qs, backend=rec, trace=trace)
    assert rows[0]["error"] is True
    t = trace[0]
    assert t["type"] == "question" and t.get("error") is True
    assert "synthesize failed" in t["error_msg"]
    assert any(c["stage"] == "select" for c in t["model_calls"])   # raw call history captured


def test_run_questions_rows_identical_with_and_without_trace():
    qs = load_questions(SMOKE / "questions.jsonl")
    rec1 = RecordingBackend(FakeBackend())
    rec1._inner.generate = _smoke_gen()
    rows_no_trace = run_questions(str(SMOKE / "library"), qs, backend=rec1)
    rec2 = RecordingBackend(FakeBackend())
    rec2._inner.generate = _smoke_gen()
    trace: list = []
    rows_traced = run_questions(str(SMOKE / "library"), qs, backend=rec2, trace=trace)
    assert rows_no_trace == rows_traced            # return value byte-identical
    assert len(trace) == len(qs)                   # trace populated only as a side-channel

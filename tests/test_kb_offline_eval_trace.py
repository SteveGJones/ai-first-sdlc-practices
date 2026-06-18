"""Pure eval-trace derivation helpers (#211)."""
from __future__ import annotations

import json as _json
from pathlib import Path

from sdlc_knowledge_base_scripts.eval.trace import derive_model_calls
from sdlc_knowledge_base_scripts.eval.trace import classify_select_drops
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.eval.runner import RecordingBackend, run_questions
from sdlc_knowledge_base_scripts.eval.suite import load_questions

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
    assert "elapsed_s" in t


def test_run_questions_no_trace_unchanged():
    qs = load_questions(SMOKE / "questions.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = _smoke_gen()
    rows = run_questions(str(SMOKE / "library"), qs, backend=rec)
    assert len(rows) == len(qs) and all("error" in r for r in rows)

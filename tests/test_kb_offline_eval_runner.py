"""Runner tests on the smoke fixture via FakeBackend. kb-offline M1c-2 (#211)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.eval.runner import (
    RecordingBackend,
    run_questions,
    run_verifier_labels,
    score_run,
)
from sdlc_knowledge_base_scripts.eval.suite import load_questions, load_verifier_labels

SMOKE = Path("plugins/sdlc-knowledge-base/eval/suite/smoke")


def test_recording_backend_flags_first_pass_and_json_validity():
    inner = FakeBackend()
    seq = iter(['not json', '{"ok": 1}'])
    inner.generate = lambda prompt, schema=None: next(seq)
    rec = RecordingBackend(inner)
    rec.generate("first attempt")
    rec.generate("retry\n\nPrevious output invalid: x")
    assert rec.records[0]["first_pass"] is True and rec.records[0]["valid_json"] is False
    assert rec.records[1]["first_pass"] is False and rec.records[1]["valid_json"] is True


def test_run_questions_scores_fact_and_abstention_on_smoke():
    qs = load_questions(SMOKE / "questions.jsonl")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            if "deploy" in prompt:
                return json.dumps({"page_ids": ["dora.md"]})
            return json.dumps({"page_ids": []})
        return json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                       "cited_pages": [{"library": "local", "page": "dora.md"}],
                                       "evidence_spans": [{"page": "dora.md",
                                                           "text": "deploy multiple times per day"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    rows = run_questions(str(SMOKE / "library"), qs, backend=be)
    assert len(rows) == len(qs)
    deploy_row = next(r for r in rows if r["id"] == "s1")
    assert "dora.md" in deploy_row["predicted_routing"]
    assert deploy_row["should_abstain"] is False


def _working_gen():
    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else json.dumps({"page_ids": []})
        return json.dumps({"claims": [], "rendered_text": ""})
    return gen


def test_run_questions_emits_progress_per_question_when_enabled(capsys):
    # With progress=True the runner prints one trackable line per question to stderr — so a
    # long live run is observable (and a stall is obvious) instead of silent until the report.
    qs = load_questions(SMOKE / "questions.jsonl")
    be = FakeBackend()
    be.generate = _working_gen()
    run_questions(str(SMOKE / "library"), qs, backend=be, progress=True, run_label="run 1/3")
    err = capsys.readouterr().err
    prog = [ln for ln in err.splitlines() if ln.startswith("[eval run 1/3] q ")]
    assert len(prog) == len(qs)                      # exactly one progress line per question
    assert f"/{len(qs)} " in prog[0]                 # index/total shown
    assert qs[0].id in prog[0]                       # question id shown
    assert "s" in prog[0]                            # per-question elapsed seconds


def test_run_questions_silent_without_progress(capsys):
    # Default (progress off) keeps the existing quiet behaviour — no progress lines.
    qs = load_questions(SMOKE / "questions.jsonl")
    be = FakeBackend()
    be.generate = _working_gen()
    run_questions(str(SMOKE / "library"), qs, backend=be)
    err = capsys.readouterr().err
    assert "[eval run" not in err and "] q " not in err


def test_run_verifier_labels_uses_deterministic_verifier():
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "supported"}'
    rows = run_verifier_labels(str(SMOKE / "library"), labels, backend=be)
    by_id = {r["id"]: r for r in rows}
    assert by_id["sv1"]["predicted_status"] == "supported"
    assert by_id["sv3"]["predicted_status"] == "unsupported"
    assert by_id["sv1"]["gold_status"] == "supported"


def test_score_run_aggregates_into_metric_dict():
    qs = load_questions(SMOKE / "questions.jsonl")
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    be = FakeBackend()

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else json.dumps({"page_ids": []})
        return json.dumps({"claims": [], "rendered_text": ""})
    be.generate = gen
    metrics = score_run(str(SMOKE / "library"), qs, labels, backend=be)
    for key in ("fact_recall", "routing_recall", "routing_precision", "abstention_precision",
                "abstention_recall", "verifier_precision", "verifier_recall",
                "first_pass_json_validity", "clean_published_support_rate",
                "invalid_mutation_rejection_floor", "citation_validity_floor",
                "post_repair_json_validity_floor"):
        assert key in metrics
        assert 0.0 <= metrics[key] <= 1.0


def test_run_questions_survives_per_question_failure(capsys):
    # A backend whose select returns '' (invalid JSON) makes pipeline.select raise after
    # repairs are exhausted. run_questions must record a zeroed error row, not crash.
    from sdlc_knowledge_base_scripts.eval.suite import load_questions
    qs = load_questions(SMOKE / "questions.jsonl")[:1]   # one question is enough

    be = FakeBackend()
    be.generate = lambda prompt, schema=None: ""   # always empty -> select raises
    rows = run_questions(str(SMOKE / "library"), qs, backend=be)
    assert len(rows) == 1
    assert rows[0]["error"] is True
    assert rows[0]["found_facts"] == [] and rows[0]["predicted_routing"] == []
    assert rows[0]["did_abstain"] is False
    err = capsys.readouterr().err
    assert "errored" in err and rows[0]["id"] in err


def test_score_run_completes_when_some_questions_error():
    # score_run must complete (return the 12-key metric dict) even if every question errors.
    from sdlc_knowledge_base_scripts.eval.suite import load_questions, load_verifier_labels
    qs = load_questions(SMOKE / "questions.jsonl")
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: ""   # everything fails
    metrics = score_run(str(SMOKE / "library"), qs, labels, backend=be)
    assert "fact_recall" in metrics and 0.0 <= metrics["fact_recall"] <= 1.0
    # all questions errored -> no facts found -> fact_recall 0.0 (over non-abstention rows)

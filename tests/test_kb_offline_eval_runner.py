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

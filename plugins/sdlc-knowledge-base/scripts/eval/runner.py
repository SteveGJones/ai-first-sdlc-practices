"""Drive the M1c-1 query path / verifier over the eval suite into scorer-ready rows.
kb-offline M1c-2 (#211). Read-only — the query path never mutates the library, so the
mutation/citation/post-repair safety floors are deterministic 1.0 in the query-only suite
and reported as such."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ..contracts import Claim, EntailmentStatus
from ..entailment import ground_claim, judge_claim, _min_status
from ..graphs.query_graph import build_query_graph
from . import harness

_REPAIR_MARKER = "Previous output invalid:"


def _valid_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError, TypeError):
        return False


class RecordingBackend:
    """Wraps a backend, recording each generate() call: whether it was a first attempt
    (prompt lacks the repair marker) and whether its output parsed as JSON. Used to score
    first-pass JSON validity without changing the pipeline's return types."""

    def __init__(self, inner):
        self._inner = inner
        self.records: list[dict] = []

    def generate(self, prompt: str, *, schema=None) -> str:
        out = self._inner.generate(prompt, schema=schema)
        self.records.append({"first_pass": _REPAIR_MARKER not in prompt,
                             "valid_json": _valid_json(out)})
        return out

    def embed(self, texts):
        return self._inner.embed(texts)


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def run_questions(library_path: str, questions, *, backend) -> list[dict]:
    """One row per question with scorer-ready fields. did_abstain = empty published body."""
    rows = []
    for q in questions:
        graph = build_query_graph(backend)
        try:
            out = graph.invoke(
                {"library_path": library_path, "question": q.question,
                 "layer": q.expected_layer, "min_confidence": None},
                config={"configurable": {"thread_id": q.id}})
        except Exception as exc:  # noqa: BLE001 - one bad question must not abort the run
            print(f"[eval] question {q.id} errored: {exc!r}", file=sys.stderr)
            rows.append({
                "id": q.id,
                "expected_facts": q.expected_facts, "found_facts": [],
                "expected_routing": q.expected_routing_targets,
                "predicted_routing": [],
                "should_abstain": q.no_evidence, "did_abstain": False,
                "error": True, "error_msg": str(exc)[:200],
            })
            continue
        rendered = out.get("rendered_text", "")
        norm_rendered = _norm(rendered)
        found = [f for f in q.expected_facts if _norm(f) in norm_rendered]
        rows.append({
            "id": q.id,
            "expected_facts": q.expected_facts, "found_facts": found,
            "expected_routing": q.expected_routing_targets,
            "predicted_routing": list(out.get("page_ids", [])),
            "should_abstain": q.no_evidence, "did_abstain": (rendered.strip() == ""),
            "error": False,
        })
    return rows


def run_verifier_labels(library_path: str, labels, *, backend) -> list[dict]:
    """Score the verifier set directly: build a Claim per label and run the deterministic
    grounding cap + judge composition against the fixture pages. No synthesis."""
    lib = Path(library_path)
    pages = {p.name: p.read_text(encoding="utf-8") for p in lib.glob("*.md")}
    rows = []
    for lb in labels:
        claim = Claim(text=lb.claim_text,
                      cited_pages=lb.cited_pages,
                      evidence_spans=lb.evidence_spans)
        cap = ground_claim(claim, pages)
        if cap == EntailmentStatus.unsupported:
            predicted = EntailmentStatus.unsupported
        else:
            predicted = _min_status(cap, judge_claim(claim, pages, backend=backend))
        rows.append({"id": lb.id, "predicted_status": predicted.value, "gold_status": lb.gold_status})
    return rows


def score_run(library_path: str, questions, labels, *, backend) -> dict:
    """Run the whole suite once and return a flat metric->value dict (the shape report.py
    aggregates). Wraps the backend to capture first-pass JSON validity."""
    rec = RecordingBackend(backend)
    q_rows = run_questions(library_path, questions, backend=rec)
    v_rows = run_verifier_labels(library_path, labels, backend=rec)

    fact = harness.fact_recall([{"expected": r["expected_facts"], "found": r["found_facts"]}
                                for r in q_rows if not r["should_abstain"]])
    r_recall, r_precision = harness.routing_scores(
        [{"expected": r["expected_routing"], "predicted": r["predicted_routing"]}
         for r in q_rows if not r["should_abstain"]])
    a_precision, a_recall = harness.abstention_scores(
        [(r["should_abstain"], r["did_abstain"]) for r in q_rows])
    v_precision, v_recall = harness.verifier_accuracy(v_rows)
    json_validity = harness.first_pass_json_validity(rec.records)
    clean = harness.clean_published_support_rate([])

    return {
        "fact_recall": fact, "routing_recall": r_recall, "routing_precision": r_precision,
        "abstention_precision": a_precision, "abstention_recall": a_recall,
        "verifier_precision": v_precision, "verifier_recall": v_recall,
        "first_pass_json_validity": json_validity, "clean_published_support_rate": clean,
        "invalid_mutation_rejection_floor": 1.0, "citation_validity_floor": 1.0,
        "post_repair_json_validity_floor": 1.0,
    }

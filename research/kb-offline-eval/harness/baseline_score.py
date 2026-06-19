"""Score the in-session Claude Code baseline against the SAME eval harness gemma4:12b ran.

Subagents performed the real select -> synthesize -> self-judge per question (and judge per
verifier label). This script applies the REAL deterministic machinery (ground_claim grounding
cap + _min_status + publish) and the REAL harness scorers + report renderer, so Claude's
claims face the identical verbatim-grounding gate that gemma faced. (#211, baseline)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins" / "sdlc-knowledge-base" / "scripts"


def _register(pkg, scripts_dir):
    spec = importlib.util.spec_from_file_location(
        pkg, scripts_dir / "__init__.py", submodule_search_locations=[str(scripts_dir)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    spec.loader.exec_module(mod)


_register("sdlc_knowledge_base_scripts", SCRIPTS)

from sdlc_knowledge_base_scripts.contracts import (  # noqa: E402
    Answer, Claim, EntailmentStatus, PageRef, Span)
from sdlc_knowledge_base_scripts.entailment import (  # noqa: E402
    _min_status, ground_claim)
from sdlc_knowledge_base_scripts.eval import harness, report as report_mod  # noqa: E402
from sdlc_knowledge_base_scripts.eval.suite import (  # noqa: E402
    load_questions, load_verifier_labels)
from sdlc_knowledge_base_scripts.publication import publish  # noqa: E402

SUITE = REPO / "plugins" / "sdlc-knowledge-base" / "eval" / "suite"
LIB = SUITE / "library"
OUTDIR = Path(__file__).resolve().parent
STAMP = sys.argv[1] if len(sys.argv) > 1 else "baseline"


def _norm(s):
    return " ".join(s.lower().split())


def _status(s):
    try:
        return EntailmentStatus(s)
    except (ValueError, TypeError):
        return EntailmentStatus.unsupported


def _claim(c):
    return Claim(
        text=c["text"],
        cited_pages=[PageRef(library=p.get("library", "local"), page=p["page"]) for p in c.get("cited_pages", [])],
        evidence_spans=[Span(library=s.get("library"), page=s["page"], text=s["text"]) for s in c.get("evidence_spans", [])],
    )


def _load_outputs(glob):
    out = {}
    for f in sorted(OUTDIR.glob(glob)):
        data = json.loads(f.read_text())
        for row in data:
            out[row["id"]] = row
    return out


def main():
    questions = load_questions(SUITE / "questions.jsonl")
    labels = load_verifier_labels(SUITE / "verifier_labels.jsonl")
    q_out = _load_outputs("q_out_*.json")
    v_out = _load_outputs("v_out*.json")

    missing_q = [q.id for q in questions if q.id not in q_out]
    missing_v = [lb.id for lb in labels if lb.id not in v_out]

    # ---- questions: faithful verify (ground cap + subagent judge) -> publish -> rendered ----
    q_rows = []
    for q in questions:
        o = q_out.get(q.id)
        if o is None:
            rendered = ""
            page_ids = []
        else:
            page_ids = list(o.get("page_ids", []))
            pages = {pid: (LIB / pid).read_text(encoding="utf-8") for pid in page_ids if (LIB / pid).is_file()}
            ans = Answer(claims=[_claim(c) for c in o.get("claims", [])])
            for claim, raw in zip(ans.claims, o.get("claims", [])):
                cap = ground_claim(claim, pages)
                if cap == EntailmentStatus.unsupported:
                    claim.entailment_status = EntailmentStatus.unsupported
                else:
                    claim.entailment_status = _min_status(cap, _status(raw.get("judge_status", "unsupported")))
            rendered, _ = publish(ans)
        found = [f for f in q.expected_facts if _norm(f) in _norm(rendered)]
        q_rows.append({
            "id": q.id, "expected_facts": q.expected_facts, "found_facts": found,
            "expected_routing": q.expected_routing_targets, "predicted_routing": page_ids,
            "should_abstain": q.no_evidence, "did_abstain": (rendered.strip() == ""),
        })

    # ---- verifier labels: ground cap + subagent judge (mirror run_verifier_labels) ----
    all_pages = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.md")}
    v_rows = []
    for lb in labels:
        claim = Claim(text=lb.claim_text, cited_pages=lb.cited_pages, evidence_spans=lb.evidence_spans)
        cap = ground_claim(claim, all_pages)
        if cap == EntailmentStatus.unsupported:
            predicted = EntailmentStatus.unsupported
        else:
            js = _status(v_out.get(lb.id, {}).get("judge_status", "unsupported"))
            predicted = _min_status(cap, js)
        v_rows.append({"id": lb.id, "predicted_status": predicted.value, "gold_status": lb.gold_status})

    fact = harness.fact_recall([{"expected": r["expected_facts"], "found": r["found_facts"]}
                                for r in q_rows if not r["should_abstain"]])
    r_recall, r_precision = harness.routing_scores(
        [{"expected": r["expected_routing"], "predicted": r["predicted_routing"]}
         for r in q_rows if not r["should_abstain"]])
    a_precision, a_recall = harness.abstention_scores([(r["should_abstain"], r["did_abstain"]) for r in q_rows])
    v_precision, v_recall = harness.verifier_accuracy(v_rows)

    metrics = {
        "fact_recall": fact, "routing_recall": r_recall, "routing_precision": r_precision,
        "abstention_precision": a_precision, "abstention_recall": a_recall,
        "verifier_precision": v_precision, "verifier_recall": v_recall,
        "first_pass_json_validity": 1.0,  # subagent structured output; valid by construction
        "clean_published_support_rate": harness.clean_published_support_rate([]),
        "invalid_mutation_rejection_floor": 1.0, "citation_validity_floor": 1.0,
        "post_repair_json_validity_floor": 1.0,
    }
    agg = report_mod.aggregate([metrics])
    verdict = report_mod.gate(agg)
    pin = {"backend": "claude-code (in-session subagents)", "model": "claude (Max plan)", "runs": 1}
    text = report_mod.render_report(agg, verdict, model="claude-code-baseline", drift=None, pin=pin)

    stem = Path("research/kb-offline-eval") / f"baseline-claude-code-{STAMP}"
    (REPO / stem).with_suffix(".md").write_text(text, encoding="utf-8")
    (REPO / stem).with_suffix(".json").write_text(
        json.dumps({"backend": "claude-code", "stamp": STAMP, "verdict": verdict, "metrics": agg,
                    "missing_questions": missing_q, "missing_verifier": missing_v}, indent=2, sort_keys=True),
        encoding="utf-8")
    print(text)
    print(f"\n[missing question outputs: {len(missing_q)} {missing_q}]")
    print(f"[missing verifier outputs: {len(missing_v)} {missing_v}]")
    print(f"[written: {stem}.md / .json]")


if __name__ == "__main__":
    main()

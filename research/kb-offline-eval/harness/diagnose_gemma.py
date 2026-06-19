"""Diagnose gemma4:12b fact_recall=0.000 against the REAL LangGraph query pipeline.

Runs build_query_graph(OllamaBackend gemma4:12b) on N evidence fact-questions and dumps,
per question and per stage boundary: selected page_ids, the RAW synthesized claims (text +
spans), the deterministic ground_claim cap per claim, the final verified entailment_status,
the published rendered_text, and found vs expected facts. This shows WHERE recall is lost.
(#211 debugging — no fixes, evidence only.)
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
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

from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend  # noqa: E402
from sdlc_knowledge_base_scripts.contracts import Answer, EntailmentStatus  # noqa: E402
from sdlc_knowledge_base_scripts.entailment import ground_claim  # noqa: E402
from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph  # noqa: E402
from sdlc_knowledge_base_scripts.eval.suite import load_questions  # noqa: E402

SUITE = REPO / "plugins" / "sdlc-knowledge-base" / "eval" / "suite"
LIB = SUITE / "library"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10


def _norm(s):
    return " ".join(s.lower().split())


def main():
    pin = {"temperature": 0, "seed": 7, "top_p": 1, "num_ctx": 8192}
    backend = OllamaBackend(model="gemma4:12b", options=pin)
    graph = build_query_graph(backend)
    questions = [q for q in load_questions(SUITE / "questions.jsonl")
                 if q.kind == "fact" and not q.no_evidence][:N]
    traces = []
    for i, q in enumerate(questions, 1):
        t0 = time.monotonic()
        out = graph.invoke(
            {"library_path": str(LIB), "question": q.question,
             "layer": q.expected_layer, "min_confidence": None},
            config={"configurable": {"thread_id": q.id}})
        dt = time.monotonic() - t0
        pages = {p["page"]: p["content"] for p in out.get("pages", [])}
        synth = Answer.model_validate(out["_synth"]) if "_synth" in out else Answer()
        verified = Answer.model_validate(out["_answer"]) if "_answer" in out else Answer()
        claim_rows = []
        for idx, c in enumerate(synth.claims):
            cap = ground_claim(c, pages)
            final = verified.claims[idx].entailment_status if idx < len(verified.claims) else None
            claim_rows.append({
                "text": c.text,
                "cited_pages": [r.page for r in c.cited_pages],
                "spans": [{"page": s.page, "text": s.text,
                           "verbatim_in_page": _norm(s.text) in _norm(pages.get(s.page, ""))}
                          for s in c.evidence_spans],
                "ground_cap": cap.value,
                "final_status": final.value if isinstance(final, EntailmentStatus) else None,
            })
        rendered = out.get("rendered_text", "")
        found = [f for f in q.expected_facts if _norm(f) in _norm(rendered)]
        tr = {
            "id": q.id, "question": q.question,
            "expected_facts": q.expected_facts, "expected_routing": q.expected_routing_targets,
            "page_ids": list(out.get("page_ids", [])),
            "n_synth_claims": len(synth.claims),
            "claims": claim_rows,
            "rendered_text": rendered,
            "did_abstain": rendered.strip() == "",
            "found_facts": found, "elapsed_s": round(dt, 1),
        }
        traces.append(tr)
        # live one-line signal to stderr
        n_supp = sum(1 for c in claim_rows if c["final_status"] == "supported")
        n_verb = sum(1 for c in claim_rows for s in c["spans"] if s["verbatim_in_page"])
        n_span = sum(len(c["spans"]) for c in claim_rows)
        print(f"[diag] {i}/{len(questions)} {q.id} route={out.get('page_ids')} exp={q.expected_routing_targets} "
              f"claims={len(synth.claims)} verbatim_spans={n_verb}/{n_span} supported={n_supp} "
              f"abstain={tr['did_abstain']} found={len(found)}/{len(q.expected_facts)} {dt:.0f}s",
              file=sys.stderr, flush=True)
    Path("tmp/cc_baseline/gemma_trace.json").write_text(json.dumps(traces, indent=2), encoding="utf-8")
    print(f"[diag] wrote tmp/cc_baseline/gemma_trace.json ({len(traces)} questions)", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()

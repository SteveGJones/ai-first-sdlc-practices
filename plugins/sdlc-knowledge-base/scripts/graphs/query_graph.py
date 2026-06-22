"""Read-only query graph (#211, M1c-1): select -> read -> synthesize -> verify -> publish.
No lock/fencing/journal (query never mutates the library).

OFFLINE INTEGRITY: this is an offline tool. We disable LangSmith/LangChain tracing
BEFORE importing langgraph so it never tries to phone home to
api.smith.langchain.com (observed during the M1b spike).
"""

from __future__ import annotations

import os

os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

from pathlib import Path  # noqa: E402
from typing import Optional, TypedDict  # noqa: E402

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402

from ..contracts import Answer  # noqa: E402
from ..entailment import verify_entailment  # noqa: E402
from ..pipeline import select, synthesize  # noqa: E402
from ..provenance import filter_pages, known_page_ids  # noqa: E402
from ..publication import finalize_answer, publish  # noqa: E402
from ..retrieval import reduce_shelf  # noqa: E402


class QueryState(TypedDict, total=False):
    library_path: str
    question: str
    layer: Optional[str]
    min_confidence: Optional[str]
    accelerate: bool
    accelerate_k: int
    page_ids: list
    no_relevant_page: bool
    abstained: bool
    abstention_reason: Optional[str]
    pages: list
    _synth: dict
    _id_rewrites: list
    rendered_text: str
    rejected_claims: list
    _answer: dict


def build_query_graph(backend):
    """Compile and return the read-only query graph. ``backend`` is the
    (Fake/Anthropic/Ollama) backend the select/synthesize/judge steps generate against.
    The synthesized Answer is carried between nodes as a dict (``_synth``) because the
    checkpointer serializes channel state."""

    def n_select(state: QueryState) -> dict:
        import sys
        lib = Path(state["library_path"])
        shelf = lib / "_shelf-index.md"
        known = known_page_ids(lib)
        if state.get("accelerate"):
            from ..embeddings import EmbeddingStore, chunk_pages, corpus_hash
            from ..retrieval import accelerated_candidates
            store = EmbeddingStore.load(lib)
            # Re-derive the corpus hash each query to detect a stale index (a page changed since indexing);
            # a stale index must fall back, never serve stale candidates. Per-query cost is the price of that guard.
            fresh = store is not None and store.provenance.corpus_hash == corpus_hash(
                [(p, h) for p, _, h in chunk_pages(lib)])
            if fresh:
                cand_ids, reduced = accelerated_candidates(
                    state["question"], str(lib), store, backend=backend, k=state.get("accelerate_k") or 20)
                candidates = filter_pages(lib, cand_ids, layer=state.get("layer"),
                                          min_confidence=state.get("min_confidence"))
                # `reduced` is over cand_ids (may include layer/confidence-filtered pages); rebuild
                # the reduced shelf over ONLY eligible ids, best-first (cand_ids is already best-first).
                eligible = set(candidates)
                res = select(state["question"], shelf, backend=backend, known_pages=eligible,
                             shelf_text=reduce_shelf(shelf, [c for c in cand_ids if c in eligible]))
                return {"page_ids": res.page_ids, "no_relevant_page": res.no_relevant_page,
                        "abstention_reason": res.abstention_reason}
            print("[query] accelerate: no fresh index (run kb-offline index); falling back to full-shelf select",
                  file=sys.stderr)
        candidates = filter_pages(lib, sorted(known), layer=state.get("layer"),
                                  min_confidence=state.get("min_confidence"))
        # Feed select ONLY eligible (layer/confidence-filtered) pages so wrong-layer pages are not
        # silently presented then dropped (the q005 contract bug).
        res = select(state["question"], shelf, backend=backend, known_pages=set(candidates),
                     shelf_text=reduce_shelf(shelf, sorted(candidates)))
        return {"page_ids": res.page_ids, "no_relevant_page": res.no_relevant_page,
                "abstention_reason": res.abstention_reason}

    def n_read(state: QueryState) -> dict:
        lib = Path(state["library_path"])
        pages = [
            {"page": pid, "content": (lib / pid).read_text(encoding="utf-8")}
            for pid in state["page_ids"]
            if (lib / pid).is_file()
        ]
        return {"pages": pages}

    def n_synthesize(state: QueryState) -> dict:
        sink: list = []
        ans = synthesize(state["question"], state["pages"], backend=backend, rewrites_sink=sink)
        return {"_synth": ans.model_dump(), "_id_rewrites": sink}

    def n_abstain(state: QueryState) -> dict:
        return {"pages": [], "rendered_text": "", "rejected_claims": [],
                "abstained": True,
                "abstention_reason": state.get("abstention_reason") or "no relevant page",
                "_answer": Answer(abstained=True,
                                  abstention_reason=state.get("abstention_reason") or "no relevant page").model_dump()}

    def n_verify_publish(state: QueryState) -> dict:
        ans = Answer.model_validate(state["_synth"])
        pages_by_name = {p["page"]: p["content"] for p in state["pages"]}
        verified = verify_entailment(ans, pages_by_name, backend=backend)
        rendered, rejected = publish(verified)
        # finalize_answer mutates `verified` IN PLACE (sets rendered_text + reconciles abstained/
        # reason). publish() yields an empty body when no claim survived verification, so this is
        # also the "verify rejected everything" -> abstained path. Read verified.* below, not `rendered`.
        finalize_answer(verified, rendered,
                        abstain_reason=(verified.abstention_reason if verified.abstained else "no supported claims"))
        return {"rendered_text": verified.rendered_text, "rejected_claims": rejected,
                "abstained": verified.abstained, "abstention_reason": verified.abstention_reason,
                "_answer": verified.model_dump()}

    def _after_select(state: QueryState) -> str:
        return "abstain" if (state.get("no_relevant_page") or not state.get("page_ids")) else "read"

    builder = StateGraph(QueryState)
    builder.add_node("select", n_select)
    builder.add_node("abstain", n_abstain)
    builder.add_node("read", n_read)
    builder.add_node("synthesize", n_synthesize)
    builder.add_node("verify_publish", n_verify_publish)
    builder.add_edge(START, "select")
    builder.add_conditional_edges("select", _after_select, {"abstain": "abstain", "read": "read"})
    builder.add_edge("abstain", END)
    builder.add_edge("read", "synthesize")
    builder.add_edge("synthesize", "verify_publish")
    builder.add_edge("verify_publish", END)
    return builder.compile(checkpointer=MemorySaver())

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
from ..provenance import filter_pages  # noqa: E402
from ..publication import publish  # noqa: E402


class QueryState(TypedDict, total=False):
    library_path: str
    question: str
    layer: Optional[str]
    min_confidence: Optional[str]
    page_ids: list
    pages: list
    _synth: dict
    rendered_text: str
    rejected_claims: list
    _answer: dict


def build_query_graph(backend):
    """Compile and return the read-only query graph. ``backend`` is the
    (Fake/Anthropic/Ollama) backend the select/synthesize/judge steps generate against.
    The synthesized Answer is carried between nodes as a dict (``_synth``) because the
    checkpointer serializes channel state."""

    def n_select(state: QueryState) -> dict:
        lib = Path(state["library_path"])
        shelf = lib / "_shelf-index.md"
        known = {
            p.name
            for p in lib.glob("*.md")
            if p.name not in {"_shelf-index.md", "log.md", "_index.md"}
        }
        candidates = filter_pages(
            lib, sorted(known), layer=state.get("layer"), min_confidence=state.get("min_confidence")
        )
        res = select(state["question"], shelf, backend=backend, known_pages=set(candidates))
        return {"page_ids": res.page_ids}

    def n_read(state: QueryState) -> dict:
        lib = Path(state["library_path"])
        pages = [
            {"page": pid, "content": (lib / pid).read_text(encoding="utf-8")}
            for pid in state["page_ids"]
            if (lib / pid).is_file()
        ]
        return {"pages": pages}

    def n_synthesize(state: QueryState) -> dict:
        ans = synthesize(state["question"], state["pages"], backend=backend)
        return {"_synth": ans.model_dump()}

    def n_verify_publish(state: QueryState) -> dict:
        ans = Answer.model_validate(state["_synth"])
        pages_by_name = {p["page"]: p["content"] for p in state["pages"]}
        verified = verify_entailment(ans, pages_by_name, backend=backend)
        rendered, rejected = publish(verified)
        return {"rendered_text": rendered, "rejected_claims": rejected,
                "_answer": verified.model_dump()}

    builder = StateGraph(QueryState)
    builder.add_node("select", n_select)
    builder.add_node("read", n_read)
    builder.add_node("synthesize", n_synthesize)
    builder.add_node("verify_publish", n_verify_publish)
    builder.add_edge(START, "select")
    builder.add_edge("select", "read")
    builder.add_edge("read", "synthesize")
    builder.add_edge("synthesize", "verify_publish")
    builder.add_edge("verify_publish", END)
    return builder.compile(checkpointer=MemorySaver())

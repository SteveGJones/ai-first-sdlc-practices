"""Federated query graph (#211, M2b): resolve -> Send one worker per library -> merge+publish.
Read-only (query never mutates). Parallel fan-out mirrors bulk_ingest_graph; per-library
results accumulate via an Annotated[list, add] reducer. OFFLINE INTEGRITY: tracing disabled
before importing langgraph."""
from __future__ import annotations

import os

os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

import sqlite3  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from operator import add  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Annotated, Optional, TypedDict  # noqa: E402

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.types import Send  # noqa: E402

from ..audit import AuditEvent, log_event  # noqa: E402
from ..contracts import Answer  # noqa: E402
from ..federation import merge_answers, query_one_library, render_federated  # noqa: E402
from ..priming import build_priming_bundle  # noqa: E402
from ..publication import finalize_answer  # noqa: E402


class FederationState(TypedDict, total=False):
    library_specs: list          # [[handle, path], ...]; first is the local root
    local_project_dir: str
    question: str
    layer: Optional[str]
    min_confidence: Optional[str]
    per_library: Annotated[list, add]
    rendered_text: str
    rejected_claims: list
    _answer: dict
    queried: int
    deduped: int
    abstained: bool
    abstention_reason: Optional[str]


def build_federation_query_graph(backend, *, checkpoint_path=None):
    def n_resolve(state: FederationState) -> dict:
        return {}

    def fan_query(state: FederationState):
        specs = state.get("library_specs") or []
        if not specs:
            return "merge_publish"
        local_dir = state["local_project_dir"]
        return [
            Send("query_one", {
                "handle": handle, "path": path, "question": state["question"],
                "layer": state.get("layer"), "min_confidence": state.get("min_confidence"),
                "local_project_dir": local_dir, "is_local": (i == 0), "audit_lib": specs[0][1],
            })
            for i, (handle, path) in enumerate(specs)
        ]

    def n_query_one(state) -> dict:
        priming = None
        if not state["is_local"]:
            priming = build_priming_bundle(state["question"], Path(state["local_project_dir"]))
            # Concurrency note: parallel Send workers append to the shared local
            # audit.log without a lock. Safe only because each line is a single
            # write() under PIPE_BUF (queries truncated to 500 chars in log_event)
            # and POSIX guarantees small appends are atomic. Do NOT widen audit
            # lines past PIPE_BUF or add concurrency here without adding a lock.
            log_event(Path(state["audit_lib"]) / ".kb-offline" / "audit.log", AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="cross_library_query", query=state["question"],
                source_handle=state["handle"], reason="federated query",
                detail={"path": state["path"]}))
        answer, page_ids = query_one_library(
            state["path"], state["question"], backend=backend, priming=priming,
            layer=state["layer"], min_confidence=state["min_confidence"])
        return {"per_library": [{"handle": state["handle"], "answer": answer.model_dump(),
                                 "page_ids": page_ids}]}

    def n_merge_publish(state: FederationState) -> dict:
        per = [(d["handle"], Answer.model_validate(d["answer"])) for d in state.get("per_library", [])]
        merged, handle_sets = merge_answers(per)
        rendered, rejected = render_federated(merged, handle_sets)
        finalize_answer(merged, rendered, abstain_reason="no library produced a supported answer")
        deduped = sum(len(a.claims) for _, a in per) - len(merged.claims)
        return {"rendered_text": merged.rendered_text, "rejected_claims": rejected,
                "_answer": merged.model_dump(), "queried": len(per), "deduped": deduped,
                "abstained": merged.abstained, "abstention_reason": merged.abstention_reason}

    builder = StateGraph(FederationState)
    builder.add_node("resolve", n_resolve)
    builder.add_node("query_one", n_query_one)
    builder.add_node("merge_publish", n_merge_publish)
    builder.add_edge(START, "resolve")
    builder.add_conditional_edges("resolve", fan_query, ["query_one", "merge_publish"])
    builder.add_edge("query_one", "merge_publish")
    builder.add_edge("merge_publish", END)
    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()
    return builder.compile(checkpointer=saver)

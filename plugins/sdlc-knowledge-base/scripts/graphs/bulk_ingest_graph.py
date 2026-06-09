"""Bulk parallel-ingest graph (issue #211, M1b) — the MAP half.

This graph re-uses the SAME M0/M1a building blocks as the single-ingest graph
(`ingest_graph.py`); it does not reimplement any of them. The difference is the
shape: instead of one serial extract node, the bulk graph fans out one extract
per source via `Send`, so independent sources are mapped in parallel (bounded by
the caller-supplied `config={"max_concurrency": N}`).

Parallel counters (committed/rejected/conflicts) use `Annotated[int, add]` reducers
so partial int returns from concurrently-finishing workers are SUMMED correctly.

OFFLINE INTEGRITY: this is an offline tool. We disable LangSmith/LangChain tracing
BEFORE importing langgraph so it never tries to phone home to
api.smith.langchain.com (observed during the M1b spike).
"""

from __future__ import annotations

import os

os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

import json  # noqa: E402
import sqlite3  # noqa: E402
from operator import add  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Annotated, Optional, TypedDict  # noqa: E402

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.types import Send  # noqa: E402

from .. import kb_ingest_bulk as kbb  # noqa: E402
from ..pipeline import extract  # noqa: E402
from ..resume import LibraryLock  # noqa: E402
from .ingest_graph import _LOCKS, release_lock  # noqa: E402, F401


class BulkIngestState(TypedDict, total=False):
    library_path: str
    source_specs: list
    run_id: str
    fencing_token: Optional[int]
    targets: list
    known_citations: list
    committed: Annotated[int, add]
    rejected: Annotated[int, add]
    conflicts: Annotated[int, add]
    reindexed: int


def build_bulk_ingest_graph(
    backend,  # duck-typed backend seam (Fake/Anthropic/Ollama); exposes .generate
    *,
    allowed_layers: list[str],
    checkpoint_path=None,
):
    """Compile and return the bulk ingest graph (MAP half).

    ``backend`` is the (Fake/Anthropic/Ollama) backend the extract nodes generate
    against. ``allowed_layers`` is threaded through for the REDUCE half added in
    Task 3.
    """

    def _extracts_dir(lib: Path) -> Path:
        return lib / ".kb-offline" / "extracts"

    def n_discover(state: BulkIngestState) -> dict:
        lib = Path(state["library_path"])
        lock = LibraryLock(lib)
        token = lock.acquire()
        _LOCKS[state["run_id"]] = lock
        return {"fencing_token": token}

    def fan_map(state: BulkIngestState):
        return [
            Send(
                "extract_one",
                {
                    "library_path": state["library_path"],
                    "run_id": state["run_id"],
                    "source": s,
                },
            )
            for s in state["source_specs"]
        ]

    def n_extract_one(state) -> dict:
        lib = Path(state["library_path"])
        _LOCKS[state["run_id"]].heartbeat()
        source = state["source"]
        slug = kbb.slug_for_source(Path(source))
        edir = _extracts_dir(lib)
        if not kbb.extract_path(edir, slug).exists():
            result = extract(str(source), lib / "_shelf-index.md", backend=backend)
            kbb.persist_extract(edir, slug, json.loads(result.model_dump_json()))
        return {}

    def n_route(state: BulkIngestState) -> dict:
        lib = Path(state["library_path"])
        extracts_dir = _extracts_dir(lib)
        loaded = [json.loads(p.read_text()) for p in sorted(extracts_dir.glob("*.json"))]
        existing = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        route = kbb.route_extracts(loaded, existing_files=existing, size_threshold=200_000)

        targets = [
            {"target_file": tfile, "is_new": slot["is_new"], "extracts": slot["extracts"]}
            for tfile, slot in route.targets.items()
        ]
        known_citations = set()
        for ex in loaded:
            known_citations.update(ex.get("citations", []))
        return {"targets": targets, "known_citations": sorted(known_citations)}

    builder = StateGraph(BulkIngestState)
    builder.add_node("discover", n_discover)
    builder.add_node("extract_one", n_extract_one)
    builder.add_node("route", n_route)

    builder.add_edge(START, "discover")
    builder.add_conditional_edges("discover", fan_map, ["extract_one"])
    builder.add_edge("extract_one", "route")
    # TEMPORARY (map-only milestone): route terminates the graph here. Task 3 will
    # re-point route -> reduce fan-out -> finalize to complete the REDUCE half.
    builder.add_edge("route", END)

    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()

    return builder.compile(checkpointer=saver)

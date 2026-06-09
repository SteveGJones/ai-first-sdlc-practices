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
from ..mutation import recover  # noqa: E402
from ..pipeline import extract  # noqa: E402
from ..resume import LibraryLock  # noqa: E402
from ._reduce import reduce_one_target  # noqa: E402
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
    reindexed: bool


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

    def fan_reduce(state: BulkIngestState):
        return [
            Send(
                "reduce_one",
                {
                    "library_path": state["library_path"],
                    "run_id": state["run_id"],
                    "fencing_token": state["fencing_token"],
                    "allowed_layers": allowed_layers,
                    "known_citations": state["known_citations"],
                    "target": t,
                },
            )
            for t in state["targets"]
        ]

    def n_reduce_one(state) -> dict:
        run_id = state["run_id"]
        _LOCKS[run_id].heartbeat()
        return reduce_one_target(
            state["target"],
            library_path=state["library_path"],
            run_id=run_id,
            lock=_LOCKS[run_id],
            fencing_token=state["fencing_token"],
            allowed_layers=state["allowed_layers"],
            known_citations=state["known_citations"],
            backend=backend,
        )

    def n_finalize(state: BulkIngestState) -> dict:
        report = recover(Path(state["library_path"]))
        release_lock(state["run_id"])
        return {"reindexed": report["reindexed"]}

    builder = StateGraph(BulkIngestState)
    builder.add_node("discover", n_discover)
    builder.add_node("extract_one", n_extract_one)
    builder.add_node("route", n_route)
    builder.add_node("reduce_one", n_reduce_one)
    builder.add_node("finalize", n_finalize)

    builder.add_edge(START, "discover")
    builder.add_conditional_edges("discover", fan_map, ["extract_one"])
    builder.add_edge("extract_one", "route")
    builder.add_conditional_edges("route", fan_reduce, ["reduce_one"])
    builder.add_edge("reduce_one", "finalize")
    builder.add_edge("finalize", END)

    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()

    return builder.compile(checkpointer=saver)

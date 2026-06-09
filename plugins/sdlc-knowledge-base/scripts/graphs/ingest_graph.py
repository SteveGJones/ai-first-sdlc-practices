"""LangGraph re-expression of the M0 single-ingest pipeline (issue #211, M1a).

This is a thin adapter: each node wraps the SAME building-block functions the M0 CLI
(`kb_offline_cli._cmd_ingest`) calls, so behaviour is identical. The graph adds two
things on top of the bare function pipeline:

  1. Checkpoint persistence (SqliteSaver when a path is given, else MemorySaver), so a
     run can be resumed by thread_id.
  2. An explicit RetryPolicy on the read-only extract node only. The commit node has NO
     retry: idempotency is guaranteed by the journal + fencing token + CAS in
     `commit_mutation`, so a blind retry there would be unsafe, not helpful.

The idempotent-create-skip on `CommitConflict` mirrors the M0 CLI exactly so that when
the CLI is later routed through this graph (Task 5) the existing resume-skip behaviour
is preserved.

NOTE: the lock is released in n_finalize; if an upstream node raises uncaught, finalize
is skipped and the lock leaks until its TTL — the CLI wrapper (Task 5) wraps graph.invoke
in try/finally to release from _LOCKS and set the run failed, restoring M0's guarantee.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from .. import kb_ingest_bulk as kbb
from ..mutation import recover
from ..pipeline import extract
from ..resume import LibraryLock
from ._reduce import reduce_one_target

# Locks cannot live in the (checkpointed) state — they are live OS resources keyed by
# run_id and released in the finalize node.
_LOCKS: dict[str, LibraryLock] = {}


def release_lock(run_id: str) -> None:
    """Release + forget the lock held for `run_id`, if any (idempotent)."""
    lock = _LOCKS.pop(run_id, None)
    if lock is not None:
        lock.release()


class IngestState(TypedDict, total=False):
    library_path: str
    source_spec: str
    run_id: str
    fencing_token: Optional[int]
    committed: int
    rejected: int
    conflicts: int
    reindexed: bool


def build_ingest_graph(
    backend,  # duck-typed backend seam (Fake/Anthropic/Ollama); exposes .generate
    *,
    allowed_layers: list[str],
    checkpoint_path=None,
    retry_attempts: int = 3,
):
    """Compile and return the ingest graph. ``backend`` is the (Fake/Anthropic/Ollama)
    backend instance the extract and reduce nodes generate against."""

    def _extracts_dir(lib: Path) -> Path:
        return lib / ".kb-offline" / "extracts"

    def n_discover(state: IngestState) -> dict:
        lib = Path(state["library_path"])
        lock = LibraryLock(lib)
        token = lock.acquire()
        _LOCKS[state["run_id"]] = lock
        return {"fencing_token": token, "committed": 0, "rejected": 0, "conflicts": 0}

    def n_map_extract(state: IngestState) -> dict:
        lib = Path(state["library_path"])
        shelf = lib / "_shelf-index.md"
        extracts_dir = _extracts_dir(lib)
        for src in kbb.discover_sources([state["source_spec"]]):
            slug = kbb.slug_for_source(src)
            ep = kbb.extract_path(extracts_dir, slug)
            if ep.exists():
                continue
            result = extract(str(src), shelf, backend=backend)
            kbb.persist_extract(extracts_dir, slug, json.loads(result.model_dump_json()))
        return {}

    def n_route_reduce_commit(state: IngestState) -> dict:
        lib = Path(state["library_path"])
        extracts_dir = _extracts_dir(lib)
        run_id = state["run_id"]
        token = state["fencing_token"]
        lock = _LOCKS[run_id]

        loaded = [json.loads(p.read_text()) for p in sorted(extracts_dir.glob("*.json"))]
        existing = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        route = kbb.route_extracts(loaded, existing_files=existing, size_threshold=200_000)

        known_citations = set()
        for ex in loaded:
            known_citations.update(ex.get("citations", []))

        committed = 0
        rejected = 0
        conflicts = 0
        for tfile, slot in route.targets.items():
            t_dict = {"target_file": tfile, "is_new": slot["is_new"], "extracts": slot["extracts"]}
            delta = reduce_one_target(
                t_dict,
                library_path=lib,
                run_id=run_id,
                lock=lock,
                fencing_token=token,
                allowed_layers=allowed_layers,
                known_citations=known_citations,
                backend=backend,
            )
            committed += delta.get("committed", 0)
            rejected += delta.get("rejected", 0)
            conflicts += delta.get("conflicts", 0)

        return {"committed": committed, "rejected": rejected, "conflicts": conflicts}

    def n_finalize(state: IngestState) -> dict:
        lib = Path(state["library_path"])
        report = recover(lib)
        release_lock(state["run_id"])
        return {"reindexed": report["reindexed"]}

    builder = StateGraph(IngestState)
    builder.add_node("discover", n_discover)
    # retry re-runs the whole extract loop; cheap because extract-exists skip makes re-runs idempotent
    builder.add_node("map_extract", n_map_extract, retry_policy=RetryPolicy(max_attempts=retry_attempts))
    builder.add_node("route_reduce_commit", n_route_reduce_commit)
    builder.add_node("finalize", n_finalize)

    builder.add_edge(START, "discover")
    builder.add_edge("discover", "map_extract")
    builder.add_edge("map_extract", "route_reduce_commit")
    builder.add_edge("route_reduce_commit", "finalize")
    builder.add_edge("finalize", END)

    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()

    return builder.compile(checkpointer=saver)

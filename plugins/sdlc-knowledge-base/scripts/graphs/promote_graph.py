"""Promote graph (#211, M2a): load saved answer -> draft body -> validate+commit (lock/
fencing/CAS/journal) -> finalize (recover + shelf rebuild + audit). Mirrors ingest_graph
for run-lifecycle/journal/checkpoint traceability. Reuses M0 mutation machinery verbatim.

OFFLINE INTEGRITY: this is an offline tool. We disable LangSmith/LangChain tracing
BEFORE importing langgraph so it never tries to phone home to api.smith.langchain.com.
"""
from __future__ import annotations

import os

os.environ.setdefault("LANGSMITH_TRACING", "false")  # offline integrity
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

import sqlite3  # noqa: E402
import sys  # noqa: E402
from collections import Counter  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Optional, TypedDict  # noqa: E402

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402

from ..answers import load_answer  # noqa: E402
from ..audit import AuditEvent, log_event  # noqa: E402
from ..build_shelf_index import rebuild_shelf_index  # noqa: E402
from ..contracts import EntailmentStatus, MutationAction, MutationProposal  # noqa: E402
from ..mutation import CommitConflict, FenceError, commit_mutation, recover, validate_proposal  # noqa: E402
from ..pipeline import promote  # noqa: E402
from ..provenance import page_frontmatter  # noqa: E402
from ..resume import LibraryLock, content_hash, step_id  # noqa: E402

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
_LOCKS: dict[str, LibraryLock] = {}


def release_lock(run_id: str) -> None:
    """Release + forget the lock held for ``run_id``, if any (idempotent)."""
    lock = _LOCKS.pop(run_id, None)
    if lock is not None:
        lock.release()


class PromoteState(TypedDict, total=False):
    library_path: str
    ref: str
    target_file: str
    action: str
    layer: Optional[str]
    confidence: Optional[str]
    run_id: str
    body: str
    frontmatter: dict
    citations: list
    promoted: int
    dropped: int
    dropped_ids: list
    committed: int
    rejected: int
    conflicts: int
    failed: bool
    reindexed: bool


def _derive_frontmatter(lib: Path, source_pages: list, *, layer, confidence) -> dict:
    layers, confs = [], []
    for p in source_pages:
        fm = page_frontmatter(str(lib), p)
        if fm.get("layer"):
            layers.append(fm["layer"])
        if fm.get("confidence") in _CONFIDENCE_RANK:
            confs.append(fm["confidence"])
    modal_layer = Counter(layers).most_common(1)[0][0] if layers else "domain"
    min_conf = min(confs, key=lambda c: _CONFIDENCE_RANK[c]) if confs else "low"
    return {"layer": layer or modal_layer, "confidence": confidence or min_conf}


def build_promote_graph(backend, *, checkpoint_path=None, allowed_layers=None):
    allowed_layers = allowed_layers or ["methodology", "evidence", "domain", "development"]

    def n_load(state: PromoteState) -> dict:
        lib = Path(state["library_path"])
        _LOCKS[state["run_id"]] = LibraryLock(lib)
        saved = load_answer(str(lib), state["ref"])
        supported = [c for c in saved.answer.claims if c.entailment_status == EntailmentStatus.supported]
        dropped = [c for c in saved.answer.claims if c.entailment_status != EntailmentStatus.supported]
        source_pages = sorted({r.page for c in supported for r in c.cited_pages})
        return {"promoted": len(supported), "dropped": len(dropped),
                "dropped_ids": [c.text for c in dropped], "citations": source_pages,
                "failed": not supported}

    def n_draft(state: PromoteState) -> dict:
        if state.get("failed"):
            return {}
        lib = Path(state["library_path"])
        saved = load_answer(str(lib), state["ref"])
        tfile = state["target_file"]
        existing = (lib / tfile).read_text() if (lib / tfile).exists() else None
        body = promote(saved, target_file=tfile, action=state["action"],
                       existing_content=existing, backend=backend)
        fm = _derive_frontmatter(lib, state["citations"], layer=state.get("layer"),
                                 confidence=state.get("confidence"))
        fm.update({"sources": state["citations"], "provenance": "promoted", "derived_from": state["ref"]})
        return {"body": body, "frontmatter": fm}

    def n_commit(state: PromoteState) -> dict:
        if state.get("failed"):
            return {"committed": 0, "rejected": 0, "conflicts": 0}
        lib = Path(state["library_path"])
        tfile = state["target_file"]
        action = MutationAction.create if state["action"] == "create" else MutationAction.extend
        expected = (
            content_hash((lib / tfile).read_text())
            if action == MutationAction.extend and (lib / tfile).exists()
            else None
        )
        proposal = MutationProposal(target_file=tfile, action=action, frontmatter=state["frontmatter"],
                                    body=state["body"], citations=list(state["citations"]),
                                    cross_refs=[], expected_hash=expected)
        errors = validate_proposal(proposal, library_path=lib, allowed_layers=allowed_layers,
                                   known_citations=set(state["citations"]))
        if errors:
            print(f"REJECTED {tfile}: {errors}", file=sys.stderr)
            return {"committed": 0, "rejected": 1, "conflicts": 0}
        lock = _LOCKS[state["run_id"]]
        token = lock.acquire()
        try:
            commit_mutation(proposal, library_path=lib, fencing_token=token, lock=lock,
                            run_step=step_id(state["run_id"], "promote", tfile))
            return {"committed": 1, "rejected": 0, "conflicts": 0}
        except (CommitConflict, FenceError) as exc:
            print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
            return {"committed": 0, "rejected": 0, "conflicts": 1}

    def n_finalize(state: PromoteState) -> dict:
        lib = Path(state["library_path"])
        report = recover(str(lib))
        # recover() rebuilds the shelf-index only when the journal has committed/staged
        # targets; rebuild explicitly after a successful commit so the new page is indexed.
        if state.get("committed"):
            rebuild_shelf_index(lib, lib / "_shelf-index.md")
        log_event(lib / ".kb-offline" / "audit.log", AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="cross_library_promotion",
            query=load_answer(str(lib), state["ref"]).question if not state.get("failed") else "",
            source_handle=None,
            reason=f"promote {state.get('action')} -> {state.get('target_file')}",
            detail={"ref": state["ref"], "target_file": state.get("target_file"),
                    "action": state.get("action"), "promoted": state.get("promoted", 0),
                    "dropped": state.get("dropped", 0), "dropped_ids": state.get("dropped_ids", [])},
        ))
        release_lock(state["run_id"])
        return {"reindexed": report.get("reindexed")}

    builder = StateGraph(PromoteState)
    builder.add_node("load", n_load)
    builder.add_node("draft", n_draft)
    builder.add_node("commit", n_commit)
    builder.add_node("finalize", n_finalize)
    builder.add_edge(START, "load")
    builder.add_edge("load", "draft")
    builder.add_edge("draft", "commit")
    builder.add_edge("commit", "finalize")
    builder.add_edge("finalize", END)
    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()
    return builder.compile(checkpointer=saver)

"""Shared per-target reduce logic for the serial (ingest_graph) and parallel
(bulk_ingest_graph) reduce phases — keeps conflict classification from drifting (#211)."""

from __future__ import annotations

import sys
from pathlib import Path

from ..contracts import MutationAction
from ..mutation import CommitConflict, FenceError, commit_mutation, validate_proposal
from ..pipeline import reduce_to_proposal
from ..resume import step_id


def reduce_one_target(
    target: dict, *, library_path, run_id, lock, fencing_token, allowed_layers, known_citations, backend
) -> dict:
    """Reduce + validate + commit ONE routed target. Returns a counter delta dict:
    {"committed":1} | {"rejected":1} | {"conflicts":1} | {} (idempotent create-skip).
    Mirrors the exact conflict-classification both graphs require."""
    lib = Path(library_path)
    tfile = target["target_file"]
    existing_content = (lib / tfile).read_text() if (lib / tfile).exists() else None
    proposal = reduce_to_proposal(
        target_file=tfile,
        is_new=target["is_new"],
        extracts=target["extracts"],
        existing_content=existing_content,
        backend=backend,
    )
    errors = validate_proposal(proposal, library_path=lib, allowed_layers=allowed_layers, known_citations=set(known_citations))
    if errors:
        print(f"REJECTED {tfile}: {errors}", file=sys.stderr)
        return {"rejected": 1}
    try:
        commit_mutation(
            proposal, library_path=lib, fencing_token=fencing_token, lock=lock, run_step=step_id(run_id, "reduce", tfile)
        )
        return {"committed": 1}
    except CommitConflict as exc:
        if proposal.action == MutationAction.create and (lib / tfile).exists():
            print(f"SKIPPED {tfile}: already committed", file=sys.stderr)
            return {}
        print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
        return {"conflicts": 1}
    except FenceError as exc:
        print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
        return {"conflicts": 1}

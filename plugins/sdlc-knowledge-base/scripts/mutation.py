"""Deterministic mutation validator, operation journal, durable committer, and
recovery for kb-offline (#211, M0). Models propose; this module validates and writes.
The validator is a safety floor — invalid proposals are rejected 100% of the time."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import yaml

from .contracts import MutationAction, MutationProposal
from .durability import atomic_write_text
from .resume import content_hash

_REQUIRED_FRONTMATTER = ("layer", "confidence")


class _FencingLock(Protocol):
    def current_token(self) -> int:
        ...


def validate_proposal(
    proposal: MutationProposal,
    library_path: str | Path,
    allowed_layers: list[str],
    known_citations: set[str],
) -> list[str]:
    """Return a list of error strings; empty means valid."""
    errors: list[str] = []
    library_path = Path(library_path).resolve()

    # 1. Path containment + shape
    if (
        not proposal.target_file
        or proposal.target_file != Path(proposal.target_file).name
        or proposal.target_file.startswith(".")
    ):
        errors.append(
            f"path: target_file must be a bare library page name, got {proposal.target_file!r}"
        )
    else:
        resolved = (library_path / proposal.target_file).resolve()
        if library_path not in resolved.parents:
            errors.append(f"path: target escapes the library: {proposal.target_file!r}")

    # 2. Required frontmatter
    for key in _REQUIRED_FRONTMATTER:
        if key not in proposal.frontmatter:
            errors.append(f"frontmatter: required key '{key}' missing")

    # 3. Layer validity
    layer = proposal.frontmatter.get("layer")
    if layer is not None and layer not in allowed_layers:
        errors.append(f"layer: '{layer}' not in allowed set {allowed_layers}")

    # 4. Citation existence
    for c in proposal.citations:
        if c not in known_citations:
            errors.append(f"citation: '{c}' does not resolve to a known source")

    # 5. CAS shape: create must not carry expected_hash; extend must.
    if proposal.action == MutationAction.create and proposal.expected_hash is not None:
        errors.append("expected_hash: must be None for a create proposal")
    if proposal.action == MutationAction.extend and proposal.expected_hash is None:
        errors.append(
            "expected_hash: required for an extend proposal (compare-and-swap)"
        )

    return errors


class CommitConflict(RuntimeError):
    """CAS failed: target changed or already exists since validation."""


class FenceError(RuntimeError):
    """The caller's fencing token is no longer current — it was fenced out."""


def _journal_dir(library_path: Path) -> Path:
    d = Path(library_path) / ".kb-offline" / "journal"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_journal(library_path: Path, run_step: str, record: dict) -> None:
    atomic_write_text(
        _journal_dir(library_path) / f"{run_step}.json", json.dumps(record, indent=2)
    )


def _render_page(proposal: MutationProposal) -> str:
    fm = yaml.safe_dump(
        proposal.frontmatter, sort_keys=False, default_flow_style=False
    ).strip()
    return f"---\n{fm}\n---\n{proposal.body}"


def commit_mutation(
    proposal: MutationProposal,
    library_path: str | Path,
    fencing_token: int,
    lock: _FencingLock,
    run_step: str,
) -> Path:
    """Durably commit one validated proposal. Order: journal-intent (fsync) -> fence
    check -> CAS -> durable page write -> journal-commit (fsync). Replay-safe."""
    library_path = Path(library_path)
    target = library_path / proposal.target_file

    # write-ahead: record intent durably BEFORE mutating
    _write_journal(
        library_path,
        run_step,
        {
            "stage": "staged",
            "target": proposal.target_file,
            "action": proposal.action.value,
            "token": fencing_token,
        },
    )

    # fence: a stale (reclaimed-from) caller is rejected here even if it "held" the lock
    if fencing_token != lock.current_token():
        _write_journal(
            library_path, run_step, {"stage": "fenced", "token": fencing_token}
        )
        raise FenceError(f"token {fencing_token} != current {lock.current_token()}")

    # compare-and-swap
    if proposal.action == MutationAction.create and target.exists():
        _write_journal(
            library_path, run_step, {"stage": "conflict", "reason": "exists"}
        )
        raise CommitConflict(f"create: {proposal.target_file} already exists")
    if proposal.action == MutationAction.extend:
        actual = content_hash(target.read_text()) if target.exists() else None
        if actual != proposal.expected_hash:
            _write_journal(
                library_path, run_step, {"stage": "conflict", "reason": "hash"}
            )
            raise CommitConflict(
                f"extend: {proposal.target_file} changed since validation"
            )

    atomic_write_text(target, _render_page(proposal))
    # Recovery contract: a crash AFTER this page write but BEFORE the committed record
    # leaves a `staged` record with the target already on disk. recover() (Task 9) must
    # treat staged-with-existing-target as needs-reindex (hash-guarded, idempotent),
    # not a no-op — else the shelf-index silently drifts.
    _write_journal(
        library_path,
        run_step,
        {"stage": "committed", "target": proposal.target_file, "token": fencing_token},
    )
    return target

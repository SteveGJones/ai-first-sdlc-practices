"""Batch ingestion manifest manager for sdlc-knowledge-base.

Tracks progress of agent-knowledge-updater dispatches over a directory of
staged raw files.  The actual agent dispatch happens in the SKILL.md; this
module provides pure-Python manifest CRUD and file discovery helpers.

CLI usage (for smoke-testing)::

    python3 -m sdlc_knowledge_base_scripts.kb_ingest_batch --help
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_STATUS_RE = re.compile(r"^status:\s*(\S+)", re.MULTILINE)


def _read_status(path: Path) -> str | None:
    """Return the frontmatter ``status`` value from *path*, or None."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    block = m.group(1)
    sm = _STATUS_RE.search(block)
    return sm.group(1) if sm else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_manifest(path: Path) -> dict[str, object] | None:
    """Read a batch-progress manifest from *path*.

    Returns None if the file does not exist or cannot be parsed.
    """
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_manifest(path: Path, manifest: dict[str, object]) -> None:
    """Atomically write *manifest* as JSON to *path*.

    Writes to a ``.tmp`` sibling first, then renames to ensure the manifest
    is never left in a half-written state.
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tmp_path.rename(path)


def build_manifest(
    source_paths: list[Path],
    existing: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build (or update) a batch manifest from *source_paths*.

    Only files whose frontmatter carries ``status: raw`` are added to
    ``pending``.  Files already listed in *existing* ``completed`` or
    ``pending`` are not duplicated.

    Args:
        source_paths: Candidate file paths to consider.
        existing: Prior manifest to merge with (preserves completed/failed).

    Returns:
        A fresh manifest dict.
    """
    completed: list[dict[str, object]] = []
    failed: list[dict[str, object]] = []
    pending: list[str] = []
    started_at: str = _now()

    if existing is not None:
        completed = list(existing.get("completed", []))  # type: ignore[arg-type]
        failed = list(existing.get("failed", []))  # type: ignore[arg-type]
        pending = list(existing.get("pending", []))  # type: ignore[arg-type]
        started_at = str(existing.get("started_at", started_at))

    completed_paths = {str(c["path"]) for c in completed if isinstance(c, dict)}
    pending_set = set(pending)

    for p in source_paths:
        key = str(p)
        if key in completed_paths or key in pending_set:
            continue
        if _read_status(p) == "raw":
            pending.append(key)

    total = len(completed) + len(pending)

    return {
        "started_at": started_at,
        "total": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
    }


def mark_completed(
    manifest: dict[str, object],
    path: str,
    timestamp: str,
) -> dict[str, object]:
    """Return a new manifest with *path* moved from ``pending`` to ``completed``.

    If *path* is not in ``pending`` the manifest is returned unchanged.
    """
    pending = [p for p in manifest["pending"] if p != path]  # type: ignore[union-attr]
    completed = list(manifest["completed"])  # type: ignore[arg-type]
    if path not in [str(p) for p in manifest["pending"]]:  # type: ignore[union-attr]
        # path wasn't in pending; return as-is
        return {**manifest, "pending": pending, "completed": completed}
    completed.append({"path": path, "completed_at": timestamp, "status": "ingested"})
    return {**manifest, "pending": pending, "completed": completed}


def mark_failed(
    manifest: dict[str, object],
    path: str,
    error: str,
    timestamp: str,
) -> dict[str, object]:
    """Move path from pending to failed.

    If *path* is not in ``pending`` the manifest is returned unchanged.
    """
    manifest = dict(manifest)
    manifest["pending"] = [p for p in manifest.get("pending", []) if p != path]
    manifest["failed"] = list(manifest.get("failed", [])) + [
        {"path": path, "error": error, "attempted_at": timestamp}
    ]
    return manifest


def retry_failed(manifest: dict[str, object]) -> dict[str, object]:
    """Return a new manifest with all ``failed`` entries moved back to ``pending``.

    ``failed`` becomes an empty list in the result.
    """
    failed_entries: list[dict[str, object]] = list(manifest.get("failed", []))  # type: ignore[arg-type]
    pending: list[str] = list(manifest.get("pending", []))  # type: ignore[arg-type]
    for entry in failed_entries:
        pending.append(str(entry["path"]))
    return {**manifest, "pending": pending, "failed": []}


def discover_raw_files(raw_dir: Path) -> list[Path]:
    """Return all ``.md`` files in *raw_dir* whose frontmatter is ``status: raw``.

    Hidden files and non-``.md`` files (e.g. ``.batch-progress.json``) are
    excluded.
    """
    results: list[Path] = []
    for candidate in sorted(raw_dir.iterdir()):
        if candidate.suffix != ".md":
            continue
        if candidate.name.startswith("."):
            continue
        if _read_status(candidate) == "raw":
            results.append(candidate)
    return results


def format_batch_dispatch_prompt(
    source_path: Path,
    library_path: Path,
    shelf_index_path: Path,
) -> str:
    """Return the agent dispatch prompt for a single file in batch mode.

    The prompt includes ``BATCH_MODE: create-only`` and instructs the agent
    not to modify existing library files, rebuild indexes, or append to
    log.md.
    """
    return (
        "BATCH_MODE: create-only\n"
        "\n"
        "Integrate the following source into the knowledge base. Batch mode constraints:\n"
        "(1) Do NOT modify existing library files — record conflict-existing-file status and stop;\n"
        "(2) Do NOT run kb-rebuild-indexes;\n"
        "(3) Do NOT append to log.md.\n"
        "\n"
        f"Source: {source_path}\n"
        f"Library: {library_path}\n"
        f"Shelf-index: {shelf_index_path}\n"
    )


# ---------------------------------------------------------------------------
# CLI (smoke-test entry point)
# ---------------------------------------------------------------------------


def main(args: list[str] | None = None) -> int:  # pragma: no cover
    """Minimal CLI for smoke-testing manifest operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch ingestion manifest manager for sdlc-knowledge-base."
    )
    sub = parser.add_subparsers(dest="cmd")

    discover_p = sub.add_parser("discover", help="List raw files in a directory")
    discover_p.add_argument("raw_dir", type=Path)

    ns = parser.parse_args(args)
    if ns.cmd == "discover":
        for f in discover_raw_files(ns.raw_dir):
            print(f)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

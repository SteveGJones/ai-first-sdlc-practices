"""Parallel map-reduce bulk ingest for sdlc-knowledge-base (issue #208).

Pure-Python orchestration core. Agent dispatch (map extractors, reduce
updaters) happens in the SKILL.md via parallel Agent-tool calls; this module
provides discovery, manifest CRUD, extract persistence, routing, prompt
formatting, and finalize helpers. Dispatch is injected as a callable so tests
run without real Agent calls — mirrors orchestrator.py.
"""
from __future__ import annotations

import glob as _glob
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Reuse the schema-agnostic atomic JSON helpers from the batch module.
from .kb_ingest_batch import load_manifest, save_manifest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ExtractDispatchRequest:
    source_path: str
    library_path: str
    shelf_index_path: str
    extractor_model: str


@dataclass(frozen=True)
class ReduceDispatchRequest:
    target_file: str
    is_new: bool
    library_path: str
    shelf_index_path: str
    extracts: list[dict]


@dataclass
class RouteResult:
    targets: dict = field(default_factory=dict)
    oversized: list = field(default_factory=list)


def discover_sources(spec) -> list[Path]:
    """Resolve a glob string, a directory Path, or a list of paths to .md files.

    - dir  -> all *.md directly in the dir (non-recursive), sorted by name
    - glob -> files matching the pattern, sorted
    - list -> each entry resolved; missing paths skipped; deduped, order-stable
    Only files that exist are returned.
    """
    out: list[Path] = []
    seen: set[Path] = set()

    def _add(p: Path) -> None:
        rp = p.resolve()
        if rp in seen:
            return
        if p.is_file():
            seen.add(rp)
            out.append(p)

    if isinstance(spec, (list, tuple)):
        for entry in spec:
            _add(Path(entry))
        return out

    if isinstance(spec, Path) and spec.is_dir():
        for p in sorted(spec.glob("*.md")):
            _add(p)
        return out

    # Treat as glob string (also handles a dir given as str via trailing match)
    pattern = str(spec)
    if Path(pattern).is_dir():
        for p in sorted(Path(pattern).glob("*.md")):
            _add(p)
        return out
    for match in sorted(_glob.glob(pattern)):
        _add(Path(match))
    return out

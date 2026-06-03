"""Parallel map-reduce bulk ingest for sdlc-knowledge-base (issue #208).

Pure-Python orchestration core. Agent dispatch (map extractors, reduce
updaters) happens in the SKILL.md via parallel Agent-tool calls; this module
provides discovery, manifest CRUD, extract persistence, routing, prompt
formatting, and finalize helpers. Dispatch is injected as a callable so tests
run without real Agent calls — mirrors orchestrator.py.
"""
from __future__ import annotations

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

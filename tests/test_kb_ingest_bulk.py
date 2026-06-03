"""Tests for sdlc_knowledge_base_scripts.kb_ingest_bulk."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    ExtractDispatchRequest,
    ReduceDispatchRequest,
    RouteResult,
)


def test_module_imports() -> None:
    assert ExtractDispatchRequest is not None
    assert ReduceDispatchRequest is not None
    assert RouteResult is not None

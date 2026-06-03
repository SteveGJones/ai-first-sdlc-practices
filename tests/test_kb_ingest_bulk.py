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


from sdlc_knowledge_base_scripts.kb_ingest_bulk import discover_sources


def test_discover_sources_from_dir(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    (tmp_path / "skip.txt").write_text("x")
    found = discover_sources(tmp_path)
    assert [p.name for p in found] == ["a.md", "b.md"]


def test_discover_sources_from_glob(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    found = discover_sources(str(tmp_path / "*.md"))
    assert [p.name for p in found] == ["a.md", "b.md"]


def test_discover_sources_from_list_dedupes(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("a")
    found = discover_sources([str(f), str(f)])
    assert found == [f]


def test_discover_sources_missing_path_skipped(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("a")
    found = discover_sources([str(f), str(tmp_path / "nope.md")])
    assert found == [f]

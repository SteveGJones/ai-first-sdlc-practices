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


from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    extract_path, persist_extract, slug_for_source,
)


def test_slug_for_source_stable_and_safe() -> None:
    assert slug_for_source(Path("/x/02-03 Foo Bar.md")) == "02-03-foo-bar"
    assert slug_for_source(Path("/x/Foo_Bar.md")) == "foo-bar"


def test_persist_extract_writes_json(tmp_path: Path) -> None:
    extract = {"source": "a.md", "findings": ["f1"], "confidence": "high", "targets": []}
    p = persist_extract(tmp_path, "a", extract)
    assert p == tmp_path / "a.json"
    import json
    assert json.loads(p.read_text())["findings"] == ["f1"]


def test_extract_path() -> None:
    assert extract_path(Path("/lib/.extracts"), "a") == Path("/lib/.extracts/a.json")


from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    build_bulk_manifest, mark_source_extracted, mark_source_failed,
)


def test_build_bulk_manifest_initial(tmp_path: Path) -> None:
    s = [tmp_path / "a.md", tmp_path / "b.md"]
    m = build_bulk_manifest(s, run_meta={"parallel_n": 16})
    assert set(m["sources"]) == {str(s[0]), str(s[1])}
    assert all(v["status"] == "pending" for v in m["sources"].values())
    assert m["run_meta"]["parallel_n"] == 16
    assert m["targets"] == {}


def test_build_bulk_manifest_resume_preserves_extracted(tmp_path: Path) -> None:
    s = [tmp_path / "a.md", tmp_path / "b.md"]
    m = build_bulk_manifest(s)
    m = mark_source_extracted(m, str(s[0]))
    s2 = s + [tmp_path / "c.md"]
    m2 = build_bulk_manifest(s2, existing=m)
    assert m2["sources"][str(s[0])]["status"] == "extracted"
    assert m2["sources"][str(s2[2])]["status"] == "pending"


def test_mark_source_failed_records_error(tmp_path: Path) -> None:
    s = [tmp_path / "a.md"]
    m = build_bulk_manifest(s)
    m = mark_source_failed(m, str(s[0]), "timeout")
    assert m["sources"][str(s[0])]["status"] == "failed"
    assert m["sources"][str(s[0])]["error"] == "timeout"


from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    mark_target_reduced, mark_target_failed, retry_failed,
)


def test_target_transitions(tmp_path: Path) -> None:
    m = build_bulk_manifest([tmp_path / "a.md"])
    m["targets"]["topic.md"] = {"status": "pending", "source_count": 2, "is_new": False, "error": None}
    m = mark_target_reduced(m, "topic.md")
    assert m["targets"]["topic.md"]["status"] == "reduced"
    m["targets"]["topic.md"] = {"status": "pending", "source_count": 2, "is_new": False, "error": None}
    m = mark_target_failed(m, "topic.md", "context overflow")
    assert m["targets"]["topic.md"]["status"] == "failed"
    assert m["targets"]["topic.md"]["error"] == "context overflow"


def test_retry_failed_requeues_both_phases(tmp_path: Path) -> None:
    m = build_bulk_manifest([tmp_path / "a.md"])
    m = mark_source_failed(m, str(tmp_path / "a.md"), "x")
    m["targets"]["t.md"] = {"status": "failed", "source_count": 1, "is_new": True, "error": "y"}
    m = retry_failed(m)
    assert m["sources"][str(tmp_path / "a.md")]["status"] == "pending"
    assert m["targets"]["t.md"]["status"] == "pending"

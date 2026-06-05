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


from sdlc_knowledge_base_scripts.kb_ingest_bulk import estimate_tokens, normalize_slug


def test_normalize_slug_collapses_variants() -> None:
    assert normalize_slug("Carbon Accounting") == "carbon-accounting"
    assert normalize_slug("carbon_accounting") == "carbon-accounting"
    assert normalize_slug("carbon-accounting.md") == "carbon-accounting"
    assert normalize_slug("  Carbon  Accounting  ") == "carbon-accounting"


def test_estimate_tokens_chars_over_four() -> None:
    assert estimate_tokens("a" * 400) == 100
    assert estimate_tokens("") == 0


from sdlc_knowledge_base_scripts.kb_ingest_bulk import route_extracts


def _extract(source, targets):
    return {"source": source, "findings": ["f"], "statistics": [], "citations": [],
            "confidence": "medium", "targets": targets}


def test_route_groups_existing_files_by_name() -> None:
    extracts = [
        _extract("a.md", [{"file": "topic.md", "finding_idx": [0]}]),
        _extract("b.md", [{"file": "topic.md", "finding_idx": [0]}]),
    ]
    r = route_extracts(extracts, existing_files={"topic.md"}, size_threshold=10_000_000)
    assert set(r.targets) == {"topic.md"}
    assert len(r.targets["topic.md"]["extracts"]) == 2
    assert r.targets["topic.md"]["is_new"] is False
    assert r.oversized == []


def test_route_fuzzy_merges_new_topic_variants() -> None:
    extracts = [
        _extract("a.md", [{"new_topic_slug": "Carbon Accounting", "title": "Carbon Accounting", "finding_idx": [0]}]),
        _extract("b.md", [{"new_topic_slug": "carbon_accounting", "title": "Carbon Accounting", "finding_idx": [0]}]),
    ]
    r = route_extracts(extracts, existing_files=set(), size_threshold=10_000_000)
    assert set(r.targets) == {"carbon-accounting.md"}
    assert r.targets["carbon-accounting.md"]["is_new"] is True
    assert len(r.targets["carbon-accounting.md"]["extracts"]) == 2


def test_route_new_topic_colliding_with_existing_file_routes_to_existing() -> None:
    extracts = [_extract("a.md", [{"new_topic_slug": "topic", "title": "Topic", "finding_idx": [0]}])]
    r = route_extracts(extracts, existing_files={"topic.md"}, size_threshold=10_000_000)
    assert set(r.targets) == {"topic.md"}
    assert r.targets["topic.md"]["is_new"] is False


def test_route_source_touching_multiple_files_fans_out() -> None:
    extracts = [_extract("a.md", [
        {"file": "x.md", "finding_idx": [0]},
        {"file": "y.md", "finding_idx": [1]},
    ])]
    r = route_extracts(extracts, existing_files={"x.md", "y.md"}, size_threshold=10_000_000)
    assert set(r.targets) == {"x.md", "y.md"}


def test_route_flags_oversized_and_excludes_from_targets() -> None:
    big = {"source": "a.md", "findings": ["x" * 4000], "statistics": [], "citations": [],
           "confidence": "low", "targets": [{"file": "hot.md", "finding_idx": [0]}]}
    r = route_extracts([big], existing_files={"hot.md"}, size_threshold=100)
    assert "hot.md" in r.oversized
    assert "hot.md" not in r.targets


def test_route_empty_extracts_returns_empty() -> None:
    r = route_extracts([], existing_files=set(), size_threshold=10_000_000)
    assert r.targets == {}
    assert r.oversized == []


def test_route_skips_target_with_no_identity() -> None:
    extracts = [_extract("a.md", [{"finding_idx": [0]}])]  # no file/new_topic_slug/title
    r = route_extracts(extracts, existing_files=set(), size_threshold=10_000_000)
    assert r.targets == {}
    assert ".md" not in r.targets


from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    format_extract_prompt, format_reduce_prompt,
)


def test_format_extract_prompt_contains_contract() -> None:
    req = ExtractDispatchRequest(
        source_path="raw/a.md", library_path="library",
        shelf_index_path="library/_shelf-index.md", extractor_model="claude-haiku-4-5",
    )
    p = format_extract_prompt(req)
    assert "raw/a.md" in p
    assert "library/_shelf-index.md" in p
    assert "JSON" in p
    assert "targets" in p
    assert "read-only" in p.lower()


def test_format_reduce_prompt_includes_extracts_and_mode() -> None:
    req = ReduceDispatchRequest(
        target_file="topic.md", is_new=False, library_path="library",
        shelf_index_path="library/_shelf-index.md",
        extracts=[{"source": "a.md", "findings": ["f1"], "targets": []}],
    )
    p = format_reduce_prompt(req)
    assert "topic.md" in p
    assert "f1" in p
    assert "BULK_REDUCE" in p
    assert "Do NOT run kb-rebuild-indexes" in p
    assert "Do NOT append to log.md" in p


def test_format_reduce_prompt_new_file_flag() -> None:
    req = ReduceDispatchRequest(
        target_file="new-topic.md", is_new=True, library_path="library",
        shelf_index_path="library/_shelf-index.md", extracts=[],
    )
    p = format_reduce_prompt(req)
    assert "create" in p.lower()

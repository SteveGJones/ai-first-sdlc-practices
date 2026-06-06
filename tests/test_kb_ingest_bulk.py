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


def test_slug_for_source_readable_stable_and_collision_free() -> None:
    # readable base prefix preserved
    assert slug_for_source(Path("/x/02-03 Foo Bar.md")).startswith("02-03-foo-bar-")
    assert slug_for_source(Path("/x/Foo_Bar.md")).startswith("foo-bar-")
    # deterministic: same path -> same slug (resume-safe)
    assert slug_for_source(Path("/x/Foo_Bar.md")) == slug_for_source(Path("/x/Foo_Bar.md"))
    # collision-free: same stem in different dirs -> different slugs
    assert slug_for_source(Path("/a/report.md")) != slug_for_source(Path("/b/report.md"))


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


from sdlc_knowledge_base_scripts.kb_ingest_bulk import summarize_run, write_log_entry


def test_summarize_run_counts(tmp_path: Path) -> None:
    m = build_bulk_manifest([tmp_path / "a.md", tmp_path / "b.md", tmp_path / "c.md"])
    m = mark_source_extracted(m, str(tmp_path / "a.md"))
    m = mark_source_extracted(m, str(tmp_path / "b.md"))
    m = mark_source_failed(m, str(tmp_path / "c.md"), "timeout")
    m["targets"]["t1.md"] = {"status": "reduced", "source_count": 2, "is_new": True, "error": None}
    summary = summarize_run(m, oversized=["hot.md"])
    assert "3" in summary
    assert "timeout" in summary or "1" in summary
    assert "hot.md" in summary


def test_write_log_entry_appends(tmp_path: Path) -> None:
    log = tmp_path / "log.md"
    log.write_text("# Log\n")
    write_log_entry(log, "## [2026-06-03] ingest-bulk | 3 sources / 1 file / 1 failed")
    text = log.read_text()
    assert "ingest-bulk" in text
    assert text.startswith("# Log")


import json as _json


def _seed_library(tmp_path: Path) -> tuple[Path, Path, Path]:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- existing.md\n")
    (lib / "existing.md").write_text("---\nlayer: domain\nconfidence: medium\n---\n# Existing\n")
    (lib / "log.md").write_text("# Log\n")
    return lib, lib / "_shelf-index.md", lib / "log.md"


def test_end_to_end_with_mock_dispatcher(tmp_path: Path) -> None:
    lib, shelf, log = _seed_library(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "s1.md").write_text("source one")
    (raw / "s2.md").write_text("source two")
    extracts_dir = lib / ".extracts"

    # --- MAP: mock extractor returns JSON keyed by source ---
    def map_dispatch(req: ExtractDispatchRequest) -> str:
        name = Path(req.source_path).name
        target = ([{"file": "existing.md", "finding_idx": [0]}] if name == "s1.md"
                  else [{"new_topic_slug": "fresh-topic", "title": "Fresh Topic", "finding_idx": [0]}])
        return _json.dumps({
            "source": req.source_path, "findings": [f"finding from {name}"],
            "statistics": [], "citations": [], "confidence": "medium", "targets": target,
        })

    sources = discover_sources(raw)
    manifest = build_bulk_manifest(sources, run_meta={"size_threshold": 10_000_000})
    for src in sources:
        result = map_dispatch(ExtractDispatchRequest(
            source_path=str(src), library_path=str(lib),
            shelf_index_path=str(shelf), extractor_model="claude-haiku-4-5"))
        extract = _json.loads(result)
        persist_extract(extracts_dir, slug_for_source(src), extract)
        mark_source_extracted(manifest, str(src))

    # --- ROUTE ---
    loaded = [_json.loads(p.read_text()) for p in sorted(extracts_dir.glob("*.json"))]
    route = route_extracts(loaded, existing_files={"existing.md"}, size_threshold=10_000_000)
    assert set(route.targets) == {"existing.md", "fresh-topic.md"}
    assert route.targets["fresh-topic.md"]["is_new"] is True

    # --- REDUCE: mock updater writes the file ---
    def reduce_dispatch(req: ReduceDispatchRequest) -> str:
        path = Path(req.library_path) / req.target_file
        path.write_text(f"# {req.target_file}\n" +
                        "\n".join(f"- {e['findings'][0]}" for e in req.extracts) + "\n")
        return "done"

    for tfile, slot in route.targets.items():
        manifest["targets"][tfile] = {
            "status": "pending", "source_count": len(slot["extracts"]),
            "is_new": slot["is_new"], "error": None}
        reduce_dispatch(ReduceDispatchRequest(
            target_file=tfile, is_new=slot["is_new"], library_path=str(lib),
            shelf_index_path=str(shelf), extracts=slot["extracts"]))
        mark_target_reduced(manifest, tfile)

    # --- FINALIZE ---
    summary = summarize_run(manifest, route.oversized)
    write_log_entry(log, "## [test] ingest-bulk\n" + summary)

    # Assertions
    assert (lib / "fresh-topic.md").exists()
    assert "finding from s2.md" in (lib / "fresh-topic.md").read_text()
    assert "finding from s1.md" in (lib / "existing.md").read_text()
    assert (log.read_text().count("ingest-bulk")) == 1
    # resume: re-running build_bulk_manifest keeps extracted status
    m2 = build_bulk_manifest(sources, existing=manifest)
    assert all(v["status"] == "extracted" for v in m2["sources"].values())


def test_write_log_entry_creates_if_absent(tmp_path: Path) -> None:
    log = tmp_path / "log.md"
    assert not log.exists()
    write_log_entry(log, "## [test] ingest-bulk | 1 source")
    assert log.exists()
    assert "ingest-bulk" in log.read_text()


def test_discover_sources_from_str_dir(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    found = discover_sources(str(tmp_path))  # directory given as a string, not Path
    assert [p.name for p in found] == ["a.md", "b.md"]

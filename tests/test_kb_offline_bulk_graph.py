"""Tests for the bulk ingest graph (FakeBackend; no live model)."""

from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.bulk_ingest_graph import build_bulk_ingest_graph


def _seed(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _multi_source_backend(sources):
    def gen(prompt, schema=None):
        if "Routed extracts" in prompt:
            import re

            m = re.search(r"Target file: (\S+)", prompt)
            tfile = m.group(1) if m else "topic.md"
            return json.dumps(
                {
                    "target_file": tfile,
                    "action": "create",
                    "frontmatter": {"layer": "domain", "confidence": "low"},
                    "body": f"# {tfile}",
                    "citations": [],
                    "cross_refs": [],
                    "expected_hash": None,
                }
            )
        for s in sources:
            if str(s) in prompt:
                slug = s.stem.lower().replace("_", "-")
                return json.dumps(
                    {
                        "source": str(s),
                        "findings": [f"f-{slug}"],
                        "confidence": "low",
                        "targets": [{"new_topic_slug": slug, "title": slug, "finding_idx": [0]}],
                    }
                )
        return json.dumps({"source": "?", "findings": [], "confidence": "low", "targets": []})

    be = FakeBackend()
    be.generate = gen
    return be


def test_bulk_map_fans_out_over_all_sources(tmp_path):
    lib = _seed(tmp_path)
    srcs = []
    for i in range(3):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)
    be = _multi_source_backend(srcs)
    graph = build_bulk_ingest_graph(be, allowed_layers=["domain"])
    graph.invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in srcs], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 8},
    )
    extracts = list((lib / ".kb-offline" / "extracts").glob("*.json"))
    assert len(extracts) == 3


def test_bulk_end_to_end_commits_all_targets(tmp_path):
    lib = _seed(tmp_path)
    srcs = []
    for i in range(3):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)
    be = _multi_source_backend(srcs)
    graph = build_bulk_ingest_graph(be, allowed_layers=["domain"])
    out = graph.invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in srcs], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 8},
    )
    assert out["committed"] == 3
    pages = [p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md"}]
    assert len(pages) == 3
    assert out.get("reindexed")


def test_bulk_resume_skips_extracted_sources(tmp_path):
    lib = _seed(tmp_path)
    s = tmp_path / "s0.md"
    s.write_text("source 0")
    be = _multi_source_backend([s])
    build_bulk_ingest_graph(be, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_specs": [str(s)], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 4},
    )
    # second run: extract already on disk -> extract() not called again
    calls = {"n": 0}
    be2 = _multi_source_backend([s])
    inner = be2.generate

    def counting(prompt, schema=None):
        if "Routed extracts" not in prompt:
            calls["n"] += 1
        return inner(prompt, schema)

    be2.generate = counting
    build_bulk_ingest_graph(be2, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_specs": [str(s)], "run_id": "b2"},
        config={"configurable": {"thread_id": "b2"}, "max_concurrency": 4},
    )
    assert calls["n"] == 0


def test_bulk_rejected_target_counted(tmp_path):
    lib = _seed(tmp_path)
    s = tmp_path / "s0.md"
    s.write_text("source 0")
    be = _multi_source_backend([s])
    out = build_bulk_ingest_graph(be, allowed_layers=["evidence"]).invoke(  # 'domain' proposal rejected
        {"library_path": str(lib), "source_specs": [str(s)], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 4},
    )
    assert out.get("rejected", 0) == 1 and out.get("committed", 0) == 0


def test_bulk_mixed_outcomes_sum_via_reducer(tmp_path):
    # 3 sources -> 3 distinct new-topic targets; pre-create ONE target page so its
    # create -> CommitConflict+exists -> SKIPPED (uncounted), and constrain allowed_layers
    # so the design works: here all 3 are valid 'domain' creates, but one already exists.
    lib = _seed(tmp_path)
    srcs = []
    for i in range(3):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)
    be = _multi_source_backend(srcs)
    # pre-seed the page that source s0 (slug 's0') will target, so its create is an idempotent skip
    (lib / "s0.md").write_text("---\nlayer: domain\nconfidence: low\n---\n# s0\n")
    out = build_bulk_ingest_graph(be, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in srcs], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 8},
    )
    # 2 fresh creates committed, 1 idempotent-skip (uncounted) -> committed==2, conflicts==0
    assert out["committed"] == 2
    assert out.get("conflicts", 0) == 0


def test_bulk_zero_targets_releases_lock_and_finalizes(tmp_path):
    # an extract with NO targets -> route yields zero targets -> fan_reduce empty.
    # finalize must still run: lock released, reindexed present.
    lib = _seed(tmp_path)
    s = tmp_path / "s0.md"
    s.write_text("source 0")
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    import json as _j

    be = FakeBackend()
    be.generate = lambda prompt, schema=None: _j.dumps(
        {"source": str(s), "findings": ["f"], "confidence": "low", "targets": []}
    )
    out = build_bulk_ingest_graph(be, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_specs": [str(s)], "run_id": "z1"},
        config={"configurable": {"thread_id": "z1"}, "max_concurrency": 4},
    )
    assert "reindexed" in out  # finalize ran
    assert not (lib / ".kb-offline" / "lock.json").exists()  # lock released
    assert out.get("committed", 0) == 0


def test_bulk_empty_source_specs_releases_lock(tmp_path):
    lib = _seed(tmp_path)
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    be = FakeBackend()  # never called — no sources
    out = build_bulk_ingest_graph(be, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_specs": [], "run_id": "z2"},
        config={"configurable": {"thread_id": "z2"}, "max_concurrency": 4},
    )
    assert "reindexed" in out
    assert not (lib / ".kb-offline" / "lock.json").exists()

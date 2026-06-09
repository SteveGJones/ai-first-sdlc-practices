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

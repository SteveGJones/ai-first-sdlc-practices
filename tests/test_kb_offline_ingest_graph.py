"""Tests for the ingest_graph (FakeBackend; no live model)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.ingest_graph import build_ingest_graph


def _seed(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _fake(extract_payload, reduce_payload):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: (reduce_payload if "Routed extracts" in prompt else extract_payload)
    return be


def test_ingest_graph_runs_end_to_end(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["finding one"],
            "confidence": "medium",
            "targets": [{"new_topic_slug": "topic-one", "title": "Topic One", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "topic-one.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "medium"},
            "body": "# Topic One\n- finding one",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    graph = build_ingest_graph(be, allowed_layers=["domain"])
    state = {
        "library_path": str(lib),
        "source_spec": str(src),
        "run_id": "run-1",
        "timestamp": "2026-06-07T00:00:00Z",
    }
    result = graph.invoke(state, config={"configurable": {"thread_id": "run-1"}})
    assert (lib / "topic-one.md").exists()
    assert result["committed"] == 1
    assert "topic-one.md" in (lib / "_shelf-index.md").read_text()

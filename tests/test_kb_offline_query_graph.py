"""Tests for the read-only query_graph (FakeBackend)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph


def _lib(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n")
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\ncost fell 30% over two years\n")
    return lib


def test_query_graph_publishes_grounded_claim(tmp_path):
    lib = _lib(tmp_path)

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:                       # select
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [{                   # synthesize
            "text": "Cost fell 30%.",
            "cited_pages": [{"library": "local", "page": "a.md"}],
            "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
            "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke(
        {"library_path": str(lib), "question": "what happened to cost?"},
        config={"configurable": {"thread_id": "q1"}})
    assert "Cost fell 30%." in out["rendered_text"]
    assert out["rejected_claims"] == []


def test_query_graph_excludes_unsupported_claim(tmp_path):
    lib = _lib(tmp_path)

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["a.md"]})
        # claim cites a span that does not appear on the page -> grounding cap unsupported
        return json.dumps({"claims": [{
            "text": "Revenue tripled.",
            "cited_pages": [{"library": "local", "page": "a.md"}],
            "evidence_spans": [{"page": "a.md", "text": "revenue tripled in one quarter"}]}],
            "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke(
        {"library_path": str(lib), "question": "what about revenue?"},
        config={"configurable": {"thread_id": "q2"}})
    assert out["rendered_text"] == ""
    assert len(out["rejected_claims"]) == 1
    assert out["rejected_claims"][0]["reason"] == "unsupported"

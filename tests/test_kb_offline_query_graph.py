"""Tests for the read-only query_graph (FakeBackend)."""
from __future__ import annotations

import json

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


def test_query_graph_layer_filter_drops_wrong_layer(tmp_path):
    """End-to-end proof that the layer provenance filter is wired through
    build_query_graph (closes a whole-slice coverage gap).

    Mechanism chain: n_select globs both pages, filter_pages keeps only the
    evidence-layer page (keep.md) so known_pages == {"keep.md"}; even though the
    model tries to select BOTH pages, select() drops drop.md (not in known_pages);
    n_read therefore never reads drop.md; when synthesize emits a claim citing
    drop.md, ground_claim sees drop.md absent from the read pages dict and marks it
    unsupported, so publish excludes it. keep.md survives, is read, and grounds.
    """
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- keep.md\n- drop.md\n")
    (lib / "keep.md").write_text(
        "---\nlayer: evidence\nconfidence: high\n---\n# Keep\nlatency dropped 40% after caching\n"
    )
    (lib / "drop.md").write_text(
        "---\nlayer: domain\nconfidence: high\n---\n# Drop\nrevenue tripled in Q3\n"
    )

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:                       # select: model tries both
            return json.dumps({"page_ids": ["keep.md", "drop.md"]})
        return json.dumps({"claims": [                     # synthesize
            {"text": "Latency dropped 40%.",
             "cited_pages": [{"library": "local", "page": "keep.md"}],
             "evidence_spans": [{"page": "keep.md", "text": "latency dropped 40%"}]},
            {"text": "Revenue tripled.",
             "cited_pages": [{"library": "local", "page": "drop.md"}],
             "evidence_spans": [{"page": "drop.md", "text": "revenue tripled in Q3"}]},
        ], "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke(
        {"library_path": str(lib), "question": "what changed?", "layer": "evidence"},
        config={"configurable": {"thread_id": "qf"}})
    # keep.md survived the evidence-layer filter, was read, claim grounded + published
    assert "Latency dropped 40%." in out["rendered_text"]
    # drop.md was filtered out (domain layer) -> never in known_pages -> dropped by
    # select -> never read -> its claim cannot ground -> excluded from the body
    assert "Revenue tripled." not in out["rendered_text"]
    # and that claim should be recorded as rejected (unsupported) rather than silently lost
    assert any(c["reason"] == "unsupported" for c in out["rejected_claims"])


def test_query_graph_returns_verified_answer_dict(tmp_path):
    lib = _lib(tmp_path)

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [{"text": "Cost fell 30%.",
                                       "cited_pages": [{"library": "local", "page": "a.md"}],
                                       "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke({"library_path": str(lib), "question": "what about cost?"},
                       config={"configurable": {"thread_id": "qa1"}})
    assert "_answer" in out
    assert out["_answer"]["claims"][0]["entailment_status"] == "supported"
    assert out["_answer"]["claims"][0]["text"] == "Cost fell 30%."


def test_query_graph_accelerate_uses_reduced_shelf(tmp_path):
    import numpy as np
    from sdlc_knowledge_base_scripts.embeddings import (EmbeddingStore, IndexRow, Provenance,
                                                        chunk_pages, corpus_hash)
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md — alpha\n- b.md — beta\n")
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\nalpha body\n")
    (lib / "b.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# B\nbeta body\n")
    rows = [IndexRow(page_id=p, content_hash=h) for p, _, h in chunk_pages(lib)]
    ch = corpus_hash([(p, h) for p, _, h in chunk_pages(lib)])
    vec = {"a.md": [1.0, 0.0], "b.md": [0.0, 1.0]}
    matrix = np.array([vec[r.page_id] for r in rows], dtype=np.float32)
    EmbeddingStore(matrix, rows, Provenance(model="fake-embed", dims=2, normalization="l2", corpus_hash=ch)).save(lib)

    seen = {}

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Question" in prompt and "Shelf" in prompt:
            seen["select_prompt"] = prompt
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [], "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    be.embed = lambda texts: [[1.0, 0.0]]
    graph = build_query_graph(be)
    graph.invoke({"library_path": str(lib), "question": "about alpha?", "accelerate": True, "accelerate_k": 1},
                 config={"configurable": {"thread_id": "acc1"}})
    assert "a.md" in seen["select_prompt"]
    assert "beta" not in seen["select_prompt"]


def test_query_graph_accelerate_falls_back_without_index(tmp_path, capsys):
    lib = _lib(tmp_path)

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [{"text": "Cost fell 30%.",
                                       "cited_pages": [{"library": "local", "page": "a.md"}],
                                       "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke({"library_path": str(lib), "question": "what about cost?", "accelerate": True},
                       config={"configurable": {"thread_id": "acc2"}})
    assert "Cost fell 30%." in out["rendered_text"]
    assert "no fresh index" in capsys.readouterr().err.lower()

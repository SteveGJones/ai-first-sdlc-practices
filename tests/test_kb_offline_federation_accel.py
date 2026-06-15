"""Accelerated federated query (linear path). kb-offline M3c-2 (#211)."""
from __future__ import annotations

import json

import numpy as np

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
from sdlc_knowledge_base_scripts.embeddings import (
    EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
from sdlc_knowledge_base_scripts.federation_accel import accelerated_federation_query


def _build_lib(tmp_path, name, pages, vectors, *, model="fake-embed", extra_rows=None):
    """pages: {page_id: (layer, confidence, body)}; vectors: {page_id: [floats]}.
    extra_rows: optional [(page_id, content_hash, [floats])] tampered rows added to the store
    WITHOUT changing provenance.corpus_hash (simulates a corrupt/stale/tampered index row)."""
    lib = tmp_path / name
    lib.mkdir()
    for pid, (layer, conf, body) in pages.items():
        (lib / pid).write_text(
            f"---\nlayer: {layer}\nconfidence: {conf}\n---\n# {pid}\n{body}\n", encoding="utf-8")
    rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
    rows = chunk_pages(lib)                          # [(page_id, embed_text, content_hash)]
    ch = corpus_hash([(pid, h) for pid, _, h in rows])
    dims = len(next(iter(vectors.values())))
    mat = [vectors[pid] for pid, _, _ in rows]
    irows = [IndexRow(page_id=pid, content_hash=h) for pid, _, h in rows]
    if extra_rows:
        for pid, h, vec in extra_rows:
            mat.append(vec)
            irows.append(IndexRow(page_id=pid, content_hash=h))
    prov = Provenance(model=model, dims=dims, normalization="l2", corpus_hash=ch)
    EmbeddingStore.from_rows(np.array(mat, dtype=np.float32), irows, prov).save(lib)
    return lib


def _gen_factory(select_ids, claim_text, cited_qids, span_qid):
    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": select_ids})
        return json.dumps({"claims": [{
            "text": claim_text,
            "cited_pages": [{"library": "x", "page": q} for q in cited_qids],
            "evidence_spans": [{"page": span_qid, "text": "deploys daily"}]}],
            "rendered_text": ""})
    return gen


def test_accelerated_federation_happy_path_comparative_claim(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "Local note on deploys.")},
                       {"local.md": [1.0, 0.0, 0.0]})
    acme = _build_lib(tmp_path, "acme",
                      {"a.md": ("evidence", "high", "Acme deploys daily.")},
                      {"a.md": [1.0, 0.0, 0.0]})
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    be.generate = _gen_factory(
        ["library/local.md", "acme/a.md"], "Teams deploy daily.",
        ["acme/a.md", "library/local.md"], "acme/a.md")
    specs = [("library", str(local)), ("acme", str(acme))]
    out = accelerated_federation_query(local, specs, "how often deploy?", backend=be, search_k=5)
    assert out is not None
    assert "Teams deploy daily." in out["rendered_text"]
    # ONE synthesis over BOTH libraries -> attribution carries both handles
    assert "acme" in out["rendered_text"] and "library" in out["rendered_text"]
    assert out["queried"] == 2


def test_accelerated_falls_back_when_backend_has_no_embeddings(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "x")}, {"local.md": [1.0, 0.0, 0.0]})

    class _NoEmbed:                      # like AnthropicBackend: no embedding_model_id
        def generate(self, prompt, schema=None):
            return "{}"
    out = accelerated_federation_query(
        local, [("library", str(local))], "q", backend=_NoEmbed(), search_k=5)
    assert out is None                   # caller falls back to M2b


def test_accelerated_falls_back_when_index_stale(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "x")}, {"local.md": [1.0, 0.0, 0.0]})
    # mutate a page after indexing -> corpus_hash no longer matches
    (local / "local.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# changed\n",
                                    encoding="utf-8")
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    out = accelerated_federation_query(local, [("library", str(local))], "q", backend=be, search_k=5)
    assert out is None


def test_accelerated_falls_back_when_index_incompatible(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "x")}, {"local.md": [1.0, 0.0, 0.0]})
    other = _build_lib(tmp_path, "acme",
                       {"a.md": ("evidence", "high", "y")}, {"a.md": [1.0, 0.0, 0.0]},
                       model="other-embed")     # different model -> incompatible
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    specs = [("library", str(local)), ("acme", str(other))]
    out = accelerated_federation_query(local, specs, "q", backend=be, search_k=5)
    assert out is None

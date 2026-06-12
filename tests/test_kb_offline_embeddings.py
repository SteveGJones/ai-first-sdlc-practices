"""Embedding index + store tests. kb-offline M3a (#211)."""
from __future__ import annotations

import numpy as np

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore, IndexRow, Provenance


def test_fake_backend_advertises_embedding_model_id():
    assert FakeBackend().embedding_model_id() == "fake-embed"


def test_anthropic_backend_is_not_embedding_capable():
    from sdlc_knowledge_base_scripts.backends.anthropic_backend import AnthropicBackend
    assert not hasattr(AnthropicBackend, "embedding_model_id")


def _store(vectors, page_ids):
    rows = [IndexRow(page_id=p, content_hash=f"h{i}") for i, p in enumerate(page_ids)]
    prov = Provenance(model="fake-embed", dims=len(vectors[0]), normalization="l2", corpus_hash="c")
    return EmbeddingStore.from_rows(np.array(vectors, dtype=np.float32), rows, prov)


def test_search_returns_nearest_page():
    store = _store([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ["a.md", "b.md", "c.md"])
    res = store.search([0.1, 1.0, 0.1], k=2)
    assert res[0][0] == "b.md"
    assert len(res) == 2 and res[0][1] >= res[1][1]


def test_search_k_larger_than_pages_is_safe():
    store = _store([[1, 0], [0, 1]], ["a.md", "b.md"])
    res = store.search([1, 0], k=8)
    assert len(res) == 2 and res[0][0] == "a.md"


def test_search_empty_index_returns_empty():
    prov = Provenance(model="m", dims=3, normalization="l2", corpus_hash="c")
    store = EmbeddingStore.from_rows(np.zeros((0, 3), dtype=np.float32), [], prov)
    assert store.search([1, 0, 0], k=5) == []


def test_search_aggregates_best_score_per_page_before_topk():
    store = _store([[1, 0, 0], [0.9, 0.1, 0], [0, 1, 0]], ["a.md", "a.md", "b.md"])
    res = store.search([1, 0, 0], k=8)
    page_ids = [p for p, _ in res]
    assert page_ids.count("a.md") == 1 and "b.md" in page_ids


def test_search_zero_query_returns_empty():
    store = _store([[1, 0], [0, 1]], ["a.md", "b.md"])
    assert store.search([0, 0], k=2) == []


def test_search_handles_zero_row_vector_without_nan():
    store = _store([[0, 0, 0], [1, 0, 0]], ["a.md", "b.md"])
    res = store.search([1, 0, 0], k=2)
    assert res[0][0] == "b.md"
    assert all(not np.isnan(s) for _, s in res)

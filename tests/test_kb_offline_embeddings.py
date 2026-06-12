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


def test_save_load_round_trip(tmp_path):
    store = _store([[1, 0, 0], [0, 1, 0]], ["a.md", "b.md"])
    store.save(tmp_path)
    loaded = EmbeddingStore.load(tmp_path)
    assert loaded is not None
    assert [r.page_id for r in loaded.rows] == ["a.md", "b.md"]
    assert loaded.provenance.model == "fake-embed" and loaded.provenance.dims == 3
    np.testing.assert_allclose(loaded.matrix, store.matrix, rtol=1e-6)


def test_load_absent_returns_none(tmp_path):
    assert EmbeddingStore.load(tmp_path) is None


def test_load_invalid_manifest_returns_none(tmp_path):
    d = tmp_path / ".kb-offline"
    d.mkdir(parents=True)
    (d / "embeddings.manifest.json").write_text("not json{", encoding="utf-8")
    assert EmbeddingStore.load(tmp_path) is None


def test_load_missing_generation_returns_none(tmp_path):
    d = tmp_path / ".kb-offline"
    d.mkdir(parents=True)
    (d / "embeddings.manifest.json").write_text('{"active": "ghostgen", "schema_version": 1}', encoding="utf-8")
    assert EmbeddingStore.load(tmp_path) is None


def test_load_rowcount_mismatch_returns_none(tmp_path):
    import json
    store = _store([[1, 0, 0], [0, 1, 0]], ["a.md", "b.md"])
    store.save(tmp_path)
    d = tmp_path / ".kb-offline"
    manifest = json.loads((d / "embeddings.manifest.json").read_text())
    meta_path = d / f"embeddings.{manifest['active']}.meta.json"
    meta = json.loads(meta_path.read_text())
    meta["rows"] = meta["rows"][:1]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert EmbeddingStore.load(tmp_path) is None


def test_save_is_generation_pointer(tmp_path):
    import json
    store = _store([[1, 0, 0]], ["a.md"])
    store.save(tmp_path)
    d = tmp_path / ".kb-offline"
    manifest = json.loads((d / "embeddings.manifest.json").read_text())
    gen = manifest["active"]
    assert (d / f"embeddings.{gen}.npy").is_file()
    assert (d / f"embeddings.{gen}.meta.json").is_file()


def test_load_unsupported_schema_version_returns_none(tmp_path):
    import json
    store = _store([[1, 0, 0], [0, 1, 0]], ["a.md", "b.md"])
    store.save(tmp_path)
    d = tmp_path / ".kb-offline"
    manifest = json.loads((d / "embeddings.manifest.json").read_text())
    manifest["schema_version"] = 2
    (d / "embeddings.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert EmbeddingStore.load(tmp_path) is None


def test_load_wrong_dtype_or_dims_returns_none(tmp_path):
    import json
    store = _store([[1, 0, 0], [0, 1, 0]], ["a.md", "b.md"])
    store.save(tmp_path)
    d = tmp_path / ".kb-offline"
    gen = json.loads((d / "embeddings.manifest.json").read_text())["active"]
    # float64 (provenance.dims=3 still satisfied) — dtype guard alone must reject.
    np.save(d / f"embeddings.{gen}.npy", np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float64), allow_pickle=False)
    assert EmbeddingStore.load(tmp_path) is None
    # shape[1] != provenance.dims (2 cols vs declared 3).
    np.save(d / f"embeddings.{gen}.npy", np.array([[1, 0], [0, 1]], dtype=np.float32), allow_pickle=False)
    assert EmbeddingStore.load(tmp_path) is None


def test_load_non_finite_matrix_returns_none(tmp_path):
    import json
    store = _store([[1, 0, 0], [0, 1, 0]], ["a.md", "b.md"])
    store.save(tmp_path)
    d = tmp_path / ".kb-offline"
    gen = json.loads((d / "embeddings.manifest.json").read_text())["active"]
    np.save(d / f"embeddings.{gen}.npy", np.array([[np.nan, 0, 0], [0, np.inf, 0]], dtype=np.float32), allow_pickle=False)
    assert EmbeddingStore.load(tmp_path) is None

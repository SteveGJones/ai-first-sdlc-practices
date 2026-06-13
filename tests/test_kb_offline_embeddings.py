"""Embedding index + store tests. kb-offline M3a (#211)."""
from __future__ import annotations

import numpy as np

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash


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


def _mk(lib, rel, body):
    p = lib / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_chunk_pages_page_id_is_relative_posix_and_strips_frontmatter(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _mk(lib, "dora.md", "---\nlayer: evidence\n---\n# DORA\nDeploy often.\n")
    _mk(lib, "sub/ops.md", "# Ops\nCanary.\n")
    _mk(lib, "_shelf-index.md", "<!-- format_version: 1 -->\n# Shelf\n")
    _mk(lib, "raw/src.md", "raw source")
    rows = {pid: (text, h) for pid, text, h in chunk_pages(lib)}
    assert set(rows) == {"dora.md", "sub/ops.md"}
    assert "layer: evidence" not in rows["dora.md"][0]
    assert "# DORA" in rows["dora.md"][0] and "Deploy often." in rows["dora.md"][0]


def test_corpus_hash_changes_on_rename():
    rows_a = [("a.md", "h1"), ("b.md", "h2")]
    rows_b = [("a.md", "h1"), ("renamed.md", "h2")]
    assert corpus_hash(rows_a) != corpus_hash(rows_b)


def test_corpus_hash_order_independent():
    rows_a = [("a.md", "h1"), ("b.md", "h2")]
    rows_b = [("b.md", "h2"), ("a.md", "h1")]
    assert corpus_hash(rows_a) == corpus_hash(rows_b)


def test_chunk_pages_small_page_is_single_row(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _mk(lib, "small.md", "# Small\nshort body\n")
    rows = chunk_pages(lib)
    assert len([r for r in rows if r[0] == "small.md"]) == 1


def test_chunk_pages_oversized_splits_into_section_rows(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    big = "# Big\n" + ("preamble. " * 50) + "\n## Section A\n" + ("aaa " * 80) + "\n## Section B\n" + ("bbb " * 80) + "\n"
    _mk(lib, "big.md", big)
    rows = [r for r in chunk_pages(lib, section_threshold=200) if r[0] == "big.md"]
    assert len(rows) >= 3
    assert all(pid == "big.md" for pid, _, _ in rows)
    texts = " | ".join(t for _, t, _ in rows)
    assert "Section A" in texts and "Section B" in texts
    assert len({h for _, _, h in rows}) == len(rows)


def test_chunk_pages_default_threshold_keeps_normal_pages_single(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _mk(lib, "dora.md", "---\nlayer: evidence\n---\n# DORA\nElite teams deploy multiple times per day.\n")
    assert len(chunk_pages(lib)) == 1

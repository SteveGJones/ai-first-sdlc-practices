"""Shareable embedding fingerprint (#211, M3c-3)."""
from __future__ import annotations

import json

import numpy as np
import pytest

from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
from sdlc_knowledge_base_scripts.embeddings import (
    EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
from sdlc_knowledge_base_scripts.fingerprint import (
    FORMAT_VERSION, Manifest, _kmeans, _vectors_sha256, export_fingerprint,
    load_fingerprint, write_fingerprint)


def _artifact(vectors, *, tier="page", weights=None):
    a = {
        "version": FORMAT_VERSION,
        "tier": tier,
        "manifest": {"handle": "acme", "owner": "Acme", "contact": "kb@acme.example"},
        "provenance": {"model": "nomic-embed-text", "dims": len(vectors[0]),
                       "normalization": "l2"},
        "vectors": vectors,
        "data_sha256": _vectors_sha256(vectors),
    }
    if weights is not None:
        a["weights"] = weights
    return a


def test_write_then_load_round_trips_vectors_bit_exact(tmp_path):
    vecs = np.array([[0.6, 0.8, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    art = _artifact(vecs.tolist())
    p = tmp_path / "acme.kbfp.json"
    write_fingerprint(p, art)
    fp = load_fingerprint(p)
    assert fp is not None
    assert fp.tier == "page"
    assert fp.manifest.handle == "acme" and fp.manifest.contact == "kb@acme.example"
    assert fp.provenance.model == "nomic-embed-text" and fp.provenance.dims == 3
    assert np.array_equal(fp.vectors, vecs)        # bit-exact float32 round-trip
    assert fp.vectors.dtype == np.float32


def test_load_rejects_tampered_vectors(tmp_path):
    art = _artifact([[1.0, 0.0], [0.0, 1.0]])
    art["vectors"][0][0] = 0.5                     # tamper after the hash was computed
    p = tmp_path / "t.kbfp.json"
    write_fingerprint(p, art)
    assert load_fingerprint(p) is None


def test_load_rejects_unknown_version(tmp_path):
    art = _artifact([[1.0, 0.0]])
    art["version"] = 999
    art["data_sha256"] = _vectors_sha256(art["vectors"])
    p = tmp_path / "v.kbfp.json"
    write_fingerprint(p, art)
    assert load_fingerprint(p) is None


def test_load_rejects_missing_fields_and_unreadable(tmp_path):
    p = tmp_path / "bad.kbfp.json"
    p.write_text(json.dumps({"version": FORMAT_VERSION, "tier": "page"}), encoding="utf-8")
    assert load_fingerprint(p) is None
    p2 = tmp_path / "broken.kbfp.json"
    p2.write_text("{not json", encoding="utf-8")
    assert load_fingerprint(p2) is None


def test_load_preserves_coarse_weights(tmp_path):
    art = _artifact([[1.0, 0.0], [0.0, 1.0]], tier="coarse", weights=[3, 1])
    p = tmp_path / "c.kbfp.json"
    write_fingerprint(p, art)
    fp = load_fingerprint(p)
    assert fp is not None and fp.tier == "coarse" and fp.weights == [3, 1]


def _norm_rows(m):
    m = np.asarray(m, dtype=np.float32)
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def test_kmeans_is_deterministic_for_seed():
    vecs = _norm_rows([[1, 0, 0], [0.9, 0.1, 0], [0, 1, 0], [0, 0.95, 0.05], [0, 0, 1]])
    c1, w1 = _kmeans(vecs, 3, seed=7)
    c2, w2 = _kmeans(vecs, 3, seed=7)
    assert np.array_equal(c1, c2) and w1 == w2


def test_kmeans_clamps_k_to_row_count():
    vecs = _norm_rows([[1, 0], [0, 1]])
    centroids, weights = _kmeans(vecs, 8, seed=7)
    assert centroids.shape[0] == 2 and len(weights) == 2


def test_kmeans_weights_sum_to_row_count_and_centroids_normalized():
    vecs = _norm_rows([[1, 0, 0], [0.8, 0.2, 0], [0, 1, 0], [0, 0, 1], [0, 0.1, 0.9]])
    centroids, weights = _kmeans(vecs, 3, seed=7)
    assert sum(weights) == 5
    norms = np.linalg.norm(centroids, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_kmeans_k1_antipodal_centroid_is_nonzero_unit():
    vecs = _norm_rows([[1.0, 0.0], [-1.0, 0.0]])
    centroids, weights = _kmeans(vecs, 1, seed=7)
    assert centroids.shape == (1, 2)
    assert abs(float(np.linalg.norm(centroids[0])) - 1.0) < 1e-5   # unit, not zero
    assert weights == [2]


def test_kmeans_separable_clusters_assign_correctly():
    vecs = _norm_rows([[1, 0, 0], [0.99, 0.01, 0], [0, 1, 0], [0.01, 0.99, 0]])
    centroids, weights = _kmeans(vecs, 2, seed=7)
    assert sorted(weights) == [2, 2]


def _build_store_lib(tmp_path, name, pages, vectors, *, model="nomic-embed-text"):
    """pages: {page_id: body}; vectors: {page_id: [floats]}. Builds a library with a real
    EmbeddingStore whose corpus_hash matches its pages (fresh)."""
    lib = tmp_path / name
    lib.mkdir()
    for pid, body in pages.items():
        (lib / pid).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {pid}\n{body}\n",
                               encoding="utf-8")
    rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
    rows = chunk_pages(lib)
    ch = corpus_hash([(pid, h) for pid, _, h in rows])
    dims = len(next(iter(vectors.values())))
    mat = np.array([vectors[pid] for pid, _, _ in rows], dtype=np.float32)
    irows = [IndexRow(page_id=pid, content_hash=h) for pid, _, h in rows]
    prov = Provenance(model=model, dims=dims, normalization="l2", corpus_hash=ch)
    EmbeddingStore.from_rows(mat, irows, prov).save(lib)
    return lib


def test_export_page_tier_ships_all_vectors_no_ids(tmp_path):
    lib = _build_store_lib(tmp_path, "library",
                           {"deploys.md": "Elite teams deploy daily.", "safety.md": "Safety cases."},
                           {"deploys.md": [1.0, 0.0, 0.0], "safety.md": [0.0, 1.0, 0.0]})
    store = EmbeddingStore.load(lib)
    art = export_fingerprint(store, tier="page", manifest=Manifest(handle="acme", owner="Acme"))
    assert art["tier"] == "page" and len(art["vectors"]) == 2
    assert "weights" not in art
    blob = json.dumps(art)
    # privacy: no filenames, no content, no corpus_hash, no shelf
    assert "deploys.md" not in blob and "safety.md" not in blob
    assert "Elite teams" not in blob and "corpus_hash" not in blob
    assert "Shelf" not in blob and "layer" not in blob


def test_export_coarse_tier_centroids_and_weights(tmp_path):
    lib = _build_store_lib(
        tmp_path, "library",
        {"a.md": "x", "b.md": "y", "c.md": "z", "d.md": "w"},
        {"a.md": [1.0, 0.0, 0.0], "b.md": [0.95, 0.05, 0.0],
         "c.md": [0.0, 1.0, 0.0], "d.md": [0.0, 0.0, 1.0]})
    store = EmbeddingStore.load(lib)
    art = export_fingerprint(store, tier="coarse",
                             manifest=Manifest(handle="acme"), clusters=2)
    assert art["tier"] == "coarse" and len(art["vectors"]) == 2
    assert sum(art["weights"]) == 4
    # round-trips and verifies
    p = tmp_path / "acme.kbfp.json"
    write_fingerprint(p, art)
    assert load_fingerprint(p) is not None


def test_export_coarse_no_weights_omits_field(tmp_path):
    lib = _build_store_lib(tmp_path, "library",
                           {"a.md": "x", "b.md": "y"},
                           {"a.md": [1.0, 0.0], "b.md": [0.0, 1.0]})
    store = EmbeddingStore.load(lib)
    art = export_fingerprint(store, tier="coarse", manifest=Manifest(handle="acme"),
                             clusters=2, weights=False)
    assert "weights" not in art


def test_export_rejects_unknown_tier(tmp_path):
    lib = _build_store_lib(tmp_path, "library", {"a.md": "x"}, {"a.md": [1.0, 0.0]})
    store = EmbeddingStore.load(lib)
    with pytest.raises(ValueError):
        export_fingerprint(store, tier="bogus", manifest=Manifest(handle="acme"))

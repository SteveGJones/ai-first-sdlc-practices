"""Shareable embedding fingerprint (#211, M3c-3)."""
from __future__ import annotations

import json

import numpy as np

from sdlc_knowledge_base_scripts.fingerprint import (
    FORMAT_VERSION, _kmeans, _vectors_sha256, load_fingerprint, write_fingerprint)


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

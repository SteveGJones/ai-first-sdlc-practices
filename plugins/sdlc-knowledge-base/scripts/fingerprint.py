"""Shareable embedding fingerprint (#211, M3c-3) — privacy-preserving cross-org "find who to
ask" discovery. Export turns a built EmbeddingStore into a portable *.kbfp.json (publisher-chosen
tier: coarse k-means centroids, or page-level bag of vectors with page_ids stripped); discover
embeds a question once and ranks received fingerprints by coverage. Embeddings discover; reasoning
stays where access exists. numpy + IO only — no graph, no backend at rest."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .embeddings import Provenance, _l2_normalize
from .fusion import compatible

FORMAT_VERSION = 1


@dataclass
class Manifest:
    handle: str
    owner: str = ""
    contact: str | None = None


@dataclass
class Fingerprint:
    tier: str                  # "coarse" | "page"
    manifest: Manifest
    provenance: Provenance     # corpus_hash filled with "" (never exported)
    vectors: np.ndarray        # (K|N, dims) float32, L2-normalized
    weights: list | None = None   # coarse tier only


def _canonical_vectors(vectors) -> str:
    """Deterministic text form of the vector array for hashing: shortest-repr floats, no
    whitespace, independent of file formatting. Accepts a nested list or an ndarray."""
    rows = vectors.tolist() if isinstance(vectors, np.ndarray) else vectors
    return json.dumps(rows, separators=(",", ":"))


def _vectors_sha256(vectors) -> str:
    return hashlib.sha256(_canonical_vectors(vectors).encode("utf-8")).hexdigest()


def write_fingerprint(path, artifact: dict) -> None:
    Path(path).write_text(json.dumps(artifact, indent=2), encoding="utf-8")


def load_fingerprint(path) -> "Fingerprint | None":
    """Parse + validate a *.kbfp.json. Returns None (with a stderr reason) for any unreadable /
    unknown-version / missing-field / integrity-failed / malformed-shape artifact, so a bad file
    is skipped, never crashes a discover run."""
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[fingerprint] {p.name}: unreadable ({exc}); skipping", file=sys.stderr)
        return None
    if not isinstance(raw, dict) or raw.get("version") != FORMAT_VERSION:
        print(f"[fingerprint] {p.name}: unsupported version "
              f"{raw.get('version') if isinstance(raw, dict) else '?'}; skipping", file=sys.stderr)
        return None
    try:
        tier = raw["tier"]
        man = raw["manifest"]
        prov = raw["provenance"]
        vec_list = raw["vectors"]
        expected = raw["data_sha256"]
    except (KeyError, TypeError):
        print(f"[fingerprint] {p.name}: missing fields; skipping", file=sys.stderr)
        return None
    if tier not in ("coarse", "page"):
        print(f"[fingerprint] {p.name}: unknown tier {tier!r}; skipping", file=sys.stderr)
        return None
    if _vectors_sha256(vec_list) != expected:
        print(f"[fingerprint] {p.name}: integrity check failed (data_sha256); skipping", file=sys.stderr)
        return None
    try:
        vectors = np.array(vec_list, dtype=np.float32)
        provenance = Provenance(model=prov["model"], dims=int(prov["dims"]),
                                normalization=prov["normalization"], corpus_hash="")
        manifest = Manifest(handle=man["handle"], owner=man.get("owner", ""),
                            contact=man.get("contact"))
    except (KeyError, TypeError, ValueError) as exc:
        print(f"[fingerprint] {p.name}: malformed ({exc}); skipping", file=sys.stderr)
        return None
    if vectors.ndim != 2 or vectors.shape[1] != provenance.dims or not np.isfinite(vectors).all():
        print(f"[fingerprint] {p.name}: vector shape/dims invalid; skipping", file=sys.stderr)
        return None
    return Fingerprint(tier=tier, manifest=manifest, provenance=provenance,
                       vectors=vectors, weights=raw.get("weights"))


def export_fingerprint(store, *, tier: str, manifest: Manifest, clusters: int = 8,
                       weights: bool = True, seed: int = 7) -> dict:
    """Build a *.kbfp.json artifact dict from a built EmbeddingStore. tier 'page' ships the
    store's L2-normalized row vectors with page_ids stripped; tier 'coarse' ships k-means
    centroids (+ per-centroid page counts unless weights=False). Emits no page_ids, no content,
    no corpus_hash, no shelf (see the threat model). 'page' n_hits at discovery counts matching
    vectors — equal to pages when no page exceeds the section threshold (the common case)."""
    if tier not in ("coarse", "page"):
        raise ValueError(f"tier must be 'coarse' or 'page', got {tier!r}")
    matrix = _l2_normalize(np.ascontiguousarray(store.matrix, dtype=np.float32))
    weights_field = None
    if tier == "page":
        vecs = matrix
    else:
        vecs, w = _kmeans(matrix, clusters, seed)
        if weights:
            weights_field = w
    vec_list = vecs.tolist()
    artifact = {
        "version": FORMAT_VERSION,
        "tier": tier,
        "manifest": {"handle": manifest.handle, "owner": manifest.owner,
                     "contact": manifest.contact},
        "provenance": {"model": store.provenance.model, "dims": store.provenance.dims,
                       "normalization": store.provenance.normalization},
        "vectors": vec_list,
        "data_sha256": _vectors_sha256(vec_list),
    }
    if weights_field is not None:
        artifact["weights"] = weights_field
    return artifact


def _kmeans(vectors: np.ndarray, k: int, seed: int) -> tuple:
    """Seeded Lloyd's k-means over (already L2-normalized) row vectors. Returns
    (centroids, weights): min(k, n) L2-normalized centroids and the integer page count assigned
    to each. Deterministic for a given (vectors, k, seed); empty clusters keep their centroid."""
    vectors = np.ascontiguousarray(vectors, dtype=np.float32)
    n = vectors.shape[0]
    k = min(k, n)
    if k == 0:
        return np.zeros((0, vectors.shape[1]), dtype=np.float32), []
    rng = np.random.default_rng(seed)
    init = rng.choice(n, size=k, replace=False)
    centroids = vectors[init].astype(np.float32).copy()
    labels = np.full(n, -1, dtype=np.int64)
    for _ in range(50):
        sims = vectors @ centroids.T          # (n, k) cosine — all rows normalized
        new_labels = np.argmax(sims, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for j in range(k):
            members = vectors[labels == j]
            if members.shape[0]:
                centroids[j] = members.mean(axis=0)
        centroids = _l2_normalize(centroids)
    zero = np.linalg.norm(centroids, axis=1) == 0
    if zero.any():
        centroids[zero] = vectors[init[zero]]   # restore distinct unit seed vectors
        centroids = _l2_normalize(centroids)
    weights = [int((labels == j).sum()) for j in range(k)]
    return centroids, weights


@dataclass
class DiscoverHit:
    handle: str
    owner: str
    contact: str | None
    tier: str
    score: float
    n_hits: int | None


def score_fingerprint(qvec, fp: Fingerprint, *, hit_threshold: float = 0.5) -> tuple:
    """(score, n_hits) for a fingerprint vs a query vector. score = max cosine over the
    fingerprint's vectors (centroids for coarse, pages for page). n_hits = #vectors >=
    hit_threshold for the page tier (None for coarse). q is L2-normalized here."""
    q = np.asarray(qvec, dtype=np.float32)
    qn = np.linalg.norm(q)
    if qn:
        q = q / qn
    if fp.vectors.shape[0] == 0:
        return float("-inf"), (0 if fp.tier == "page" else None)
    sims = fp.vectors @ q
    score = float(sims.max())
    n_hits = int((sims >= hit_threshold).sum()) if fp.tier == "page" else None
    return score, n_hits


def discover(qvec, fingerprints, *, query_provenance, min_score: float = 0.0,
             hit_threshold: float = 0.5, top=None) -> list:
    """Rank compatible fingerprints by coverage score (desc). Incompatible
    (model/dims/normalization) fingerprints are dropped with a stderr warning — never scored.
    min_score filters; top truncates."""
    hits = []
    for fp in fingerprints:
        if not compatible(query_provenance, fp.provenance):
            print(f"[discover] {fp.manifest.handle}: incompatible embedding "
                  f"({fp.provenance.model}/{fp.provenance.dims}/{fp.provenance.normalization})"
                  "; skipping", file=sys.stderr)
            continue
        score, n_hits = score_fingerprint(qvec, fp, hit_threshold=hit_threshold)
        if score < min_score:
            continue
        hits.append(DiscoverHit(handle=fp.manifest.handle, owner=fp.manifest.owner,
                                contact=fp.manifest.contact, tier=fp.tier,
                                score=score, n_hits=n_hits))
    hits.sort(key=lambda h: h.score, reverse=True)
    if top is not None:
        hits = hits[:top]
    return hits

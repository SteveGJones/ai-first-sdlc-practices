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
from .fusion import compatible  # noqa: F401  (used in Task 4)

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

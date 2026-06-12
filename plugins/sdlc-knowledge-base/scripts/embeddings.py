"""Embedding index + store (#211, M3a) — the OPTIONAL, off-by-default accelerator foundation.
numpy exact cosine search over an L2-normalized float32 matrix, behind a narrow EmbeddingStore
seam. Page-level chunking; row-per-vector keyed by page_id (section-fallback additive later).
Index is derived/gitignored/rebuildable."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Provenance:
    model: str
    dims: int
    normalization: str          # "l2"
    corpus_hash: str
    schema_version: int = 1


@dataclass
class IndexRow:
    page_id: str
    content_hash: str


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    m = np.ascontiguousarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (m / norms).astype(np.float32)


class EmbeddingStore:
    def __init__(self, matrix: np.ndarray, rows: list, provenance: Provenance):
        self.matrix = matrix
        self.rows = rows
        self.provenance = provenance

    @classmethod
    def from_rows(cls, matrix: np.ndarray, rows: list, provenance: Provenance) -> "EmbeddingStore":
        if matrix.shape[0]:
            norm = _l2_normalize(matrix)
        else:
            norm = matrix.astype(np.float32).reshape(0, provenance.dims)
        return cls(norm, list(rows), provenance)

    def search(self, query_vec, k: int = 8) -> list:
        if self.matrix.shape[0] == 0:
            return []
        q = np.asarray(query_vec, dtype=np.float32)
        qn = np.linalg.norm(q)
        if qn == 0:
            return []
        q = q / qn
        scores = self.matrix @ q
        best: dict = {}
        for i, row in enumerate(self.rows):
            s = float(scores[i])
            if s > best.get(row.page_id, float("-inf")):
                best[row.page_id] = s
        page_ids = list(best.keys())
        P = len(page_ids)
        k_eff = min(k, P)
        if k_eff == 0:
            return []
        arr = np.array([best[p] for p in page_ids], dtype=np.float32)
        sel = np.argpartition(-arr, k_eff - 1)[:k_eff]
        sel = sel[np.argsort(-arr[sel])]
        return [(page_ids[i], float(arr[i])) for i in sel]

"""Embedding index + store (#211, M3a) — the OPTIONAL, off-by-default accelerator foundation.
numpy exact cosine search over an L2-normalized float32 matrix, behind a narrow EmbeddingStore
seam. Page-level chunking; row-per-vector keyed by page_id (section-fallback additive later).
Index is derived/gitignored/rebuildable."""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .durability import atomic_write_text


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

    def save(self, library_path) -> None:
        """Crash/reader-safe via immutable generation files + an atomically-replaced pointer.
        Write embeddings.<gen>.npy + embeddings.<gen>.meta.json (fresh unique gen, write-once),
        then atomic_write_text the manifest naming the active gen. Prune stale generations
        best-effort after the flip (a leftover never corrupts a load)."""
        d = Path(library_path) / ".kb-offline"
        d.mkdir(parents=True, exist_ok=True)
        gen = uuid.uuid4().hex[:16]
        np.save(d / f"embeddings.{gen}.npy", self.matrix, allow_pickle=False)
        meta = {"provenance": vars(self.provenance),
                "rows": [{"page_id": r.page_id, "content_hash": r.content_hash} for r in self.rows]}
        atomic_write_text(d / f"embeddings.{gen}.meta.json", json.dumps(meta, indent=2))
        atomic_write_text(d / "embeddings.manifest.json",
                          json.dumps({"active": gen, "schema_version": self.provenance.schema_version}))
        for p in d.glob("embeddings.*.npy"):
            g = p.name[len("embeddings."):-len(".npy")]
            if g != gen:
                try:
                    p.unlink()
                    (d / f"embeddings.{g}.meta.json").unlink(missing_ok=True)
                except OSError:
                    pass

    @classmethod
    def load(cls, library_path) -> "EmbeddingStore | None":
        """Usable store, or None (= rebuild-required, stderr reason) for any absent/corrupt/
        incompatible state — the index is derived, so a defect cleanly rebuilds."""
        d = Path(library_path) / ".kb-offline"
        manifest_path = d / "embeddings.manifest.json"
        if not manifest_path.is_file():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema_version") != 1:
                print(f"[index] unsupported schema_version {manifest.get('schema_version')}; rebuild required",
                      file=sys.stderr)
                return None
            gen = manifest["active"]
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            print("[index] manifest unreadable; rebuild required", file=sys.stderr)
            return None
        npy = d / f"embeddings.{gen}.npy"
        meta_path = d / f"embeddings.{gen}.meta.json"
        if not (npy.is_file() and meta_path.is_file()):
            print(f"[index] generation {gen} files missing; rebuild required", file=sys.stderr)
            return None
        try:
            matrix = np.load(npy, allow_pickle=False)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            prov = Provenance(**meta["provenance"])
            rows = [IndexRow(page_id=r["page_id"], content_hash=r["content_hash"]) for r in meta["rows"]]
        except (json.JSONDecodeError, ValueError, KeyError, TypeError, OSError) as exc:
            print(f"[index] index unreadable ({exc}); rebuild required", file=sys.stderr)
            return None
        if (matrix.dtype != np.float32 or matrix.ndim != 2 or matrix.shape[0] != len(rows)
                or matrix.shape[1] != prov.dims or not np.isfinite(matrix).all()):
            print("[index] index matrix invalid (shape/dtype/dims/finite); rebuild required", file=sys.stderr)
            return None
        return cls(matrix, rows, prov)

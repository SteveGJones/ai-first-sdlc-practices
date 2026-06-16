# kb-offline M3c-3 — shareable-fingerprint discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A library owner can `kb-offline fingerprint export` their built embedding index into a portable, privacy-preserving `*.kbfp.json`, and a discoverer can `kb-offline discover "<question>"` to rank received fingerprints into a "who to ask" list — all without any access to the underlying content, filenames, or shelf.

**Architecture:** One new pure module `scripts/fingerprint.py` (numpy + IO, no graph, no backend at rest) holding the artifact IO + integrity, a seeded k-means, export, scoring, and discovery; plus two thin CLI subcommands (`fingerprint export`, `discover`). Export reads an existing `EmbeddingStore` and (for the coarse tier) clusters it; discover embeds the question once, gates each fingerprint on integrity + embedding compatibility, scores by max cosine, and ranks. Spec: `docs/superpowers/specs/2026-06-16-kb-offline-M3c3-shareable-fingerprint-discovery-design.md`.

**Tech Stack:** Python 3.9+, the project `.venv`, pytest, numpy (already an `[offline]` dep). No new deps. `flake8 --max-line-length=127`. Commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## Environment & scope

- **`.venv` for everything.** Source under `plugins/sdlc-knowledge-base/scripts/`; tests import the `sdlc_knowledge_base_scripts` package (registered by `tests/conftest.py`). Run pytest from the repo root.
- **In scope:** `fingerprint.py` (Manifest, Fingerprint, `_canonical_vectors`, `_vectors_sha256`, `write_fingerprint`, `load_fingerprint`, `_kmeans`, `export_fingerprint`, `score_fingerprint`, `discover`); CLI `fingerprint export` + `discover` with a `fingerprints_override` test seam; a gated live smoke.
- **Out of scope:** a separate `import` command; calibrated coverage bands; any content read/shelf/synthesis on discover; M3d.

## Reused APIs (call, do not re-create)

- `embeddings.EmbeddingStore.load(library_path) -> EmbeddingStore | None`; `.matrix` (L2-normalized float32, one row per vector — small pages = one row/page, oversized pages = section rows); `.rows` (`IndexRow(page_id, content_hash)`); `.provenance` (`Provenance(model, dims, normalization, corpus_hash, schema_version)`); `EmbeddingStore.from_rows(matrix, rows, provenance)`; `.save(library_path)`.
- `embeddings.chunk_pages(library_path) -> [(page_id, embed_text, content_hash)]`; `embeddings.corpus_hash(page_hash_pairs) -> str`; `embeddings.IndexRow`; `embeddings.Provenance`; `embeddings._l2_normalize(matrix)`.
- `fusion.compatible(prov_a, prov_b) -> bool` (model + dims + normalization; corpus_hash excluded).
- `backends.fake_backend.FakeBackend` — `.embed(texts) -> [[float]*8]` (8-dim, deterministic per text), `.embedding_model_id() -> "fake-embed"`. `AnthropicBackend` omits `embedding_model_id`.
- CLI helpers: `_make_backend(name, override, *, options=None, model=None)`; subparsers built in `main`; dispatch by `args.cmd`; existing override params `library_specs_override`, `sources_override`.

## File structure

| File | Change | Responsibility |
|---|---|---|
| `plugins/sdlc-knowledge-base/scripts/fingerprint.py` | new | artifact IO + integrity, `_kmeans`, `export_fingerprint`, `score_fingerprint`, `discover` |
| `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py` | modify | `fingerprint export` + `discover` subcommands + `_cmd_fingerprint` + `_cmd_discover` + `fingerprints_override` |
| `tests/test_kb_offline_fingerprint.py` | new | IO, integrity, k-means, export+privacy, scoring, discovery |
| `tests/test_kb_offline_cli.py` | modify | export + discover CLI tests |
| `tests/test_kb_offline_ollama_smoke.py` | modify | gated live export-both-tiers + discover smoke |

---

## Task 1: Artifact IO + integrity (`Fingerprint`, `load`/`write`, sha256)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/fingerprint.py`
- Test: `tests/test_kb_offline_fingerprint.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_fingerprint.py`:
```python
"""Shareable embedding fingerprint (#211, M3c-3)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from sdlc_knowledge_base_scripts.fingerprint import (
    FORMAT_VERSION, Manifest, _vectors_sha256, load_fingerprint, write_fingerprint)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -v`
Expected: FAIL (ModuleNotFoundError: `fingerprint`).

- [ ] **Step 3: Implement the IO + integrity layer**

Create `plugins/sdlc-knowledge-base/scripts/fingerprint.py`:
```python
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
        print(f"[fingerprint] {p.name}: unsupported version {raw.get('version') if isinstance(raw, dict) else '?'}"
              "; skipping", file=sys.stderr)
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
```

(`compatible` and `_l2_normalize` are imported now even though they are first *used* in Tasks 3/4 — importing them here keeps the module's import block stable across tasks. flake8 will flag them as unused until then; if that blocks the Task 1 commit, add `# noqa: F401` to those two import lines and remove the noqa in Task 3/4. Prefer adding the noqa now.)

- [ ] **Step 4: Run tests + lint**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -v`
Expected: PASS (5 tests).
Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fingerprint artifact IO + sha256 integrity (load/write) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Seeded k-means (`_kmeans`)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/fingerprint.py`
- Test: `tests/test_kb_offline_fingerprint.py`

**Contract (spec §2):** Lloyd's k-means with seeded init over L2-normalized row vectors; `k` clamped to the row count; returns `(centroids, weights)` with each centroid re-L2-normalized and `weights[j]` = pages assigned to cluster j; deterministic for a given `(vectors, k, seed)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_fingerprint.py`:
```python
from sdlc_knowledge_base_scripts.fingerprint import _kmeans


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -k kmeans -v`
Expected: FAIL (ImportError: cannot import name `_kmeans`).

- [ ] **Step 3: Implement `_kmeans`**

Append to `plugins/sdlc-knowledge-base/scripts/fingerprint.py`:
```python
def _kmeans(vectors: np.ndarray, k: int, seed: int) -> tuple:
    """Seeded Lloyd's k-means over (already L2-normalized) row vectors. Returns
    (centroids, weights): min(k, n) L2-normalized centroids and the integer page count assigned
    to each. Deterministic for a given (vectors, k, seed); empty clusters keep their centroid."""
    vectors = np.ascontiguousarray(vectors, dtype=np.float32)
    n = vectors.shape[0]
    k = min(k, n)
    if k == 0:
        return np.zeros((0, vectors.shape[1] if vectors.ndim == 2 else 0), dtype=np.float32), []
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
    weights = [int((labels == j).sum()) for j in range(k)]
    return centroids, weights
```

- [ ] **Step 4: Run tests + lint**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -v`
Expected: PASS (8 tests).
Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fingerprint._kmeans — seeded deterministic Lloyd's k-means (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `export_fingerprint` (both tiers + privacy)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/fingerprint.py`
- Test: `tests/test_kb_offline_fingerprint.py`

**Contract (spec §3, §5):** page tier ships `store.matrix` rows (page_ids stripped); coarse tier ships `_kmeans` centroids (+ `weights` unless `weights=False`). Artifact carries `{version, tier, manifest, provenance{model,dims,normalization}, vectors, [weights], data_sha256}` — **never** page_ids, content, corpus_hash, or shelf.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_fingerprint.py`:
```python
from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
from sdlc_knowledge_base_scripts.embeddings import (
    EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
from sdlc_knowledge_base_scripts.fingerprint import export_fingerprint


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
    import pytest as _pytest
    lib = _build_store_lib(tmp_path, "library", {"a.md": "x"}, {"a.md": [1.0, 0.0]})
    store = EmbeddingStore.load(lib)
    with _pytest.raises(ValueError):
        export_fingerprint(store, tier="bogus", manifest=Manifest(handle="acme"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -k export -v`
Expected: FAIL (ImportError: cannot import name `export_fingerprint`).

- [ ] **Step 3: Implement `export_fingerprint`**

Append to `plugins/sdlc-knowledge-base/scripts/fingerprint.py`:
```python
def export_fingerprint(store, *, tier: str, manifest: Manifest, clusters: int = 8,
                       weights: bool = True, seed: int = 7) -> dict:
    """Build a *.kbfp.json artifact dict from a built EmbeddingStore. tier 'page' ships the
    store's L2-normalized row vectors with page_ids stripped; tier 'coarse' ships k-means
    centroids (+ per-centroid page counts unless weights=False). Emits no page_ids, no content,
    no corpus_hash, no shelf (see the threat model). 'page' n_hits at discovery counts matching
    vectors — equal to pages when no page exceeds the section threshold (the common case)."""
    if tier not in ("coarse", "page"):
        raise ValueError(f"tier must be 'coarse' or 'page', got {tier!r}")
    matrix = np.ascontiguousarray(store.matrix, dtype=np.float32)
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
```

- [ ] **Step 4: Run tests + lint**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -v`
Expected: PASS (12 tests).
Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fingerprint.export_fingerprint — coarse/page tiers, page_ids stripped (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `score_fingerprint` + `discover`

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/fingerprint.py`
- Test: `tests/test_kb_offline_fingerprint.py`

**Contract (spec §4, §5):** `score = max cosine` over the fingerprint's vectors; page tier also returns `n_hits` = #vectors ≥ `hit_threshold` (None for coarse). `discover` drops incompatible fingerprints (via `fusion.compatible`) with a stderr warning, applies `min_score`, ranks by score desc, truncates to `top`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_fingerprint.py`:
```python
from sdlc_knowledge_base_scripts.fingerprint import DiscoverHit, discover, score_fingerprint


def _fp(vectors, *, handle="acme", tier="page", model="m", owner="Acme", contact=None):
    return Fingerprint(
        tier=tier, manifest=Manifest(handle=handle, owner=owner, contact=contact),
        provenance=Provenance(model=model, dims=len(vectors[0]), normalization="l2", corpus_hash=""),
        vectors=np.array(vectors, dtype=np.float32))


def test_score_page_tier_max_cosine_and_n_hits():
    fp = _fp([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.7071, 0.7071, 0.0]])
    score, n_hits = score_fingerprint([1.0, 0.0, 0.0], fp, hit_threshold=0.5)
    assert abs(score - 1.0) < 1e-5
    assert n_hits == 2          # vec0 (1.0) and vec2 (~0.707) >= 0.5


def test_score_coarse_tier_n_hits_none():
    fp = _fp([[1.0, 0.0], [0.0, 1.0]], tier="coarse")
    score, n_hits = score_fingerprint([1.0, 0.0], fp)
    assert abs(score - 1.0) < 1e-5 and n_hits is None


def test_discover_ranks_on_topic_above_off_topic():
    qprov = Provenance(model="m", dims=3, normalization="l2", corpus_hash="")
    on = _fp([[1.0, 0.0, 0.0]], handle="on-topic")
    off = _fp([[0.0, 0.0, 1.0]], handle="off-topic")
    hits = discover([1.0, 0.0, 0.0], [off, on], query_provenance=qprov)
    assert [h.handle for h in hits] == ["on-topic", "off-topic"]
    assert hits[0].score > hits[1].score


def test_discover_drops_incompatible_with_warning(capsys):
    qprov = Provenance(model="nomic-embed-text", dims=3, normalization="l2", corpus_hash="")
    good = _fp([[1.0, 0.0, 0.0]], handle="good", model="nomic-embed-text")
    bad = _fp([[1.0, 0.0, 0.0]], handle="bad", model="other-model")
    hits = discover([1.0, 0.0, 0.0], [good, bad], query_provenance=qprov)
    assert [h.handle for h in hits] == ["good"]
    assert "incompatible" in capsys.readouterr().err


def test_discover_min_score_and_top():
    qprov = Provenance(model="m", dims=3, normalization="l2", corpus_hash="")
    a = _fp([[1.0, 0.0, 0.0]], handle="a")
    b = _fp([[0.0, 0.0, 1.0]], handle="b")
    assert [h.handle for h in discover([1.0, 0.0, 0.0], [a, b], query_provenance=qprov,
                                       min_score=0.5)] == ["a"]
    assert len(discover([1.0, 0.0, 0.0], [a, b], query_provenance=qprov, top=1)) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -k "score or discover" -v`
Expected: FAIL (ImportError: cannot import name `discover`).

- [ ] **Step 3: Implement scoring + discovery**

Append to `plugins/sdlc-knowledge-base/scripts/fingerprint.py`:
```python
@dataclass
class DiscoverHit:
    handle: str
    owner: str
    contact: "str | None"
    tier: str
    score: float
    n_hits: "int | None"


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
```

(If Task 1's import line had `# noqa: F401` on `compatible`/`_l2_normalize`, remove it now — both are used.)

- [ ] **Step 4: Run tests + lint**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fingerprint.py -v`
Expected: PASS (17 tests).
Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fingerprint.py tests/test_kb_offline_fingerprint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fingerprint.score_fingerprint + discover — ranked who-to-ask (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: CLI `fingerprint export`

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`
- Test: `tests/test_kb_offline_cli.py`

**Contract (spec §6):** `kb-offline fingerprint export --library <dir> --tier coarse|page [...]` reads the existing store (no backend), enforces a freshness gate (`--allow-stale` override), writes `<handle>.kbfp.json` (or `--out`). `--tier` is required; `--clusters` validated `>= 1`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_cli.py`:
```python
def _build_store_lib_cli(tmp_path, pages, vectors):
    import numpy as np
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
    from sdlc_knowledge_base_scripts.embeddings import (
        EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
    lib = tmp_path / "library"
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
    EmbeddingStore.from_rows(mat, irows,
                             Provenance(model="m", dims=dims, normalization="l2",
                                        corpus_hash=ch)).save(lib)
    return lib


def test_fingerprint_export_writes_artifact(tmp_path):
    lib = _build_store_lib_cli(tmp_path, {"a.md": "x", "b.md": "y"},
                               {"a.md": [1.0, 0.0], "b.md": [0.0, 1.0]})
    out = tmp_path / "acme.kbfp.json"
    rc = cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page",
                   "--handle", "acme", "--out", str(out)])
    assert rc == 0 and out.is_file()
    art = json.loads(out.read_text())
    assert art["tier"] == "page" and art["manifest"]["handle"] == "acme"
    assert len(art["vectors"]) == 2


def test_fingerprint_export_requires_tier(tmp_path):
    import pytest as _pytest
    with _pytest.raises(SystemExit):
        cli.main(["fingerprint", "export", "--library", str(tmp_path)])


def test_fingerprint_export_no_store_errors(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    rc = cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page"])
    assert rc == 1


def test_fingerprint_export_freshness_gate(tmp_path):
    lib = _build_store_lib_cli(tmp_path, {"a.md": "x"}, {"a.md": [1.0, 0.0]})
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# a\nCHANGED\n",
                              encoding="utf-8")          # corpus drifts from the index
    out = tmp_path / "a.kbfp.json"
    assert cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page",
                     "--out", str(out)]) == 1            # stale -> refuse
    assert cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page",
                     "--out", str(out), "--allow-stale"]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k fingerprint_export -v`
Expected: FAIL (argparse: invalid choice / no `fingerprint` command).

- [ ] **Step 3: Add the subparser + command + dispatch**

In `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`, add `_cmd_fingerprint` (place near `_cmd_index`):
```python
def _cmd_fingerprint(args) -> int:
    if args.fp_cmd != "export":
        return 2
    from .embeddings import EmbeddingStore, chunk_pages, corpus_hash
    from .fingerprint import Manifest, export_fingerprint, write_fingerprint

    if args.clusters < 1:
        raise SystemExit("fingerprint export: --clusters must be >= 1")
    lib = Path(args.library)
    store = EmbeddingStore.load(lib)
    if store is None:
        print("fingerprint export: no embedding index — run `kb-offline index` first", file=sys.stderr)
        return 1
    fresh = corpus_hash([(pid, h) for pid, _, h in chunk_pages(lib)])
    if store.provenance.corpus_hash != fresh and not args.allow_stale:
        print("fingerprint export: index is stale (corpus changed since last index) — "
              "re-run `kb-offline index`, or pass --allow-stale", file=sys.stderr)
        return 1
    handle = args.handle or lib.name
    manifest = Manifest(handle=handle, owner=args.owner, contact=args.contact)
    artifact = export_fingerprint(store, tier=args.tier, manifest=manifest,
                                  clusters=args.clusters, weights=not args.no_weights)
    out = Path(args.out) if args.out else Path(f"{handle}.kbfp.json")
    write_fingerprint(out, artifact)
    print(f"wrote {out} (tier={args.tier}, {len(artifact['vectors'])} vectors)")
    return 0
```
Add the subparser in `main` (next to the `index`/`lint` parsers):
```python
    p_fp = sub.add_parser("fingerprint")
    fp_sub = p_fp.add_subparsers(dest="fp_cmd", required=True)
    p_fpx = fp_sub.add_parser("export")
    p_fpx.add_argument("--library", default="library")
    p_fpx.add_argument("--tier", required=True, choices=["coarse", "page"])
    p_fpx.add_argument("--out", default=None)
    p_fpx.add_argument("--handle", default=None)
    p_fpx.add_argument("--owner", default="")
    p_fpx.add_argument("--contact", default=None)
    p_fpx.add_argument("--clusters", type=int, default=8)
    p_fpx.add_argument("--no-weights", action="store_true")
    p_fpx.add_argument("--allow-stale", action="store_true")
```
Add the dispatch line (next to the other `if args.cmd == ...` checks):
```python
    if args.cmd == "fingerprint":
        return _cmd_fingerprint(args)
```

- [ ] **Step 4: Run tests + lint**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -v`
Expected: PASS (existing CLI tests + 4 new).
Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): CLI `fingerprint export` — tiered artifact + freshness gate (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: CLI `discover`

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`
- Test: `tests/test_kb_offline_cli.py`

**Contract (spec §6):** `kb-offline discover "<q>" [--backend] [--fingerprint P]... [--fingerprints DIR] [--min-score F] [--top N] [--hit-threshold F]` embeds the question once (requires an embedding-capable backend, else exit 2), loads/gates received fingerprints, prints the ranked who-to-ask list, exit 0 even when nothing covers. A `fingerprints_override` test seam injects `Fingerprint` objects directly.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_cli.py`:
```python
def _fake_embed_backend(vec):
    be = FakeBackend()
    be.embed = lambda texts: [list(vec)]      # type: ignore
    return be


def _cli_fp(vectors, *, handle, model="fake-embed", tier="page", owner="Acme", contact=None):
    import numpy as np
    from sdlc_knowledge_base_scripts.embeddings import Provenance
    from sdlc_knowledge_base_scripts.fingerprint import Fingerprint, Manifest
    return Fingerprint(
        tier=tier, manifest=Manifest(handle=handle, owner=owner, contact=contact),
        provenance=Provenance(model=model, dims=len(vectors[0]), normalization="l2", corpus_hash=""),
        vectors=np.array(vectors, dtype=np.float32))


def test_discover_prints_ranked_list(tmp_path, capsys):
    fps = [_cli_fp([[0.0, 0.0, 1.0]], handle="off-topic"),
           _cli_fp([[1.0, 0.0, 0.0]], handle="on-topic", contact="kb@acme.example")]
    rc = cli.main(["discover", "how often deploy?"],
                  backend_override=_fake_embed_backend([1.0, 0.0, 0.0]),
                  fingerprints_override=fps)
    assert rc == 0
    out = capsys.readouterr().out
    # on-topic ranked first, contact + tier rendered
    assert out.index("on-topic") < out.index("off-topic")
    assert "kb@acme.example" in out and "page" in out


def test_discover_no_fingerprints_exits_zero(capsys):
    rc = cli.main(["discover", "q"], backend_override=_fake_embed_backend([1.0, 0.0]),
                  fingerprints_override=[])
    assert rc == 0
    assert "no covering libraries" in capsys.readouterr().out.lower()


def test_discover_requires_embedding_backend():
    class _NoEmbed:                            # like AnthropicBackend: no embedding_model_id
        def generate(self, prompt, schema=None):
            return "{}"
    rc = cli.main(["discover", "q"], backend_override=_NoEmbed(), fingerprints_override=[])
    assert rc == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k discover -v`
Expected: FAIL (argparse: no `discover` command / `main` has no `fingerprints_override`).

- [ ] **Step 3: Add the subparser + command + dispatch + main param**

In `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`, add `_cmd_discover` (place after `_cmd_fingerprint`):
```python
def _cmd_discover(args, backend_override, fingerprints_override=None) -> int:
    from .embeddings import Provenance
    from .fingerprint import discover, load_fingerprint

    backend = _make_backend(args.backend, backend_override)
    model_fn = getattr(backend, "embedding_model_id", None)
    if model_fn is None or getattr(backend, "embed", None) is None:
        print("discover: backend has no embedding capability — discovery requires an "
              "embedding-capable backend (e.g. --backend ollama)", file=sys.stderr)
        return 2

    if fingerprints_override is not None:
        fingerprints = fingerprints_override
    else:
        paths = list(args.fingerprint_paths)
        fp_dir = Path(args.fingerprints) if args.fingerprints else Path.home() / ".sdlc" / "fingerprints"
        if fp_dir.is_dir():
            paths.extend(sorted(str(p) for p in fp_dir.glob("*.kbfp.json")))
        fingerprints = [fp for fp in (load_fingerprint(p) for p in paths) if fp is not None]
    if not fingerprints:
        print("discover: no usable fingerprints found (use --fingerprint/--fingerprints)", file=sys.stderr)
        print("no covering libraries found")
        return 0

    qvecs = backend.embed([args.question])
    if len(qvecs) != 1:
        print("discover: embedding did not return exactly one vector", file=sys.stderr)
        return 2
    qvec = list(qvecs[0])
    qprov = Provenance(model=model_fn(), dims=len(qvec), normalization="l2", corpus_hash="")
    hits = discover(qvec, fingerprints, query_provenance=qprov,
                    min_score=args.min_score, hit_threshold=args.hit_threshold, top=args.top)
    if not hits:
        print("no covering libraries found")
        return 0
    for h in hits:
        pages = f"{h.n_hits} pages" if h.n_hits is not None else "—"
        print(f"{h.handle} · {h.owner or '—'} · {h.contact or '—'} · {h.score:.4f} · {h.tier} · {pages}")
    return 0
```
Add the subparser in `main` (next to `fingerprint`):
```python
    p_disc = sub.add_parser("discover")
    p_disc.add_argument("question")
    p_disc.add_argument("--backend", default="ollama")
    p_disc.add_argument("--fingerprint", action="append", default=[], dest="fingerprint_paths")
    p_disc.add_argument("--fingerprints", default=None)
    p_disc.add_argument("--min-score", type=float, default=0.0)
    p_disc.add_argument("--top", type=int, default=None)
    p_disc.add_argument("--hit-threshold", type=float, default=0.5)
```
Update `main`'s signature to thread the new override (mirror the existing `sources_override` / `library_specs_override` keyword params — READ the current signature and add consistently):
```python
def main(argv=None, *, backend_override=None, library_specs_override=None,
         sources_override=None, fingerprints_override=None) -> int:
```
Add the dispatch line:
```python
    if args.cmd == "discover":
        return _cmd_discover(args, backend_override, fingerprints_override)
```

- [ ] **Step 4: Run tests + lint**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -v`
Expected: PASS (all CLI tests + 3 new discover tests).
Then the whole non-live suite: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass (233 from M3c-2 + the new fingerprint/CLI tests).
Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): CLI `discover` — embed-once, gate, rank received fingerprints (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Live Ollama smoke (gated, skips without Ollama)

**Files:**
- Modify: `tests/test_kb_offline_ollama_smoke.py` (append)

The live-smoke suite is gated behind the real Ollama backend (skips when unavailable; never fails CI). Add one smoke that builds a real index, exports both tiers, and runs `discover` with a real `nomic-embed-text` question-embed — asserting non-crash ranked output. **Inspect the file first** to reuse its actual skip guard (`@pytest.mark.skipif(not _ollama_ready())`) and its real `OllamaBackend(...)` construction and `EmbeddingStore`-build pattern (it is NOT a fixture named `ollama_backend` — match what is really there).

- [ ] **Step 1: Inspect the existing guard**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -v` and read the top of the file to reuse its `_ollama_ready()` skipif, its `OllamaBackend` constructor, and the real-index build (`chunk_pages` → `be.embed` → `EmbeddingStore.from_rows(...).save(lib)` with `Provenance.model = be.embedding_model_id()`).

- [ ] **Step 2: Write the smoke test**

Append, matching the file's real conventions (the helper below assumes the same `_ollama_ready`/`OllamaBackend` pattern the other live tests use; adapt names to the file):
```python
def test_live_ollama_fingerprint_discover(tmp_path):
    import numpy as np
    import pytest
    if not _ollama_ready():                       # reuse this file's guard
        pytest.skip("ollama daemon/model not available")
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
    from sdlc_knowledge_base_scripts.embeddings import (
        EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
    from sdlc_knowledge_base_scripts.fingerprint import (
        Manifest, discover, export_fingerprint, load_fingerprint, write_fingerprint)

    be = OllamaBackend()                          # defaults: nomic-embed-text embeddings

    def _index(lib, pages):
        lib.mkdir()
        for pid, body in pages.items():
            (lib / pid).write_text(
                f"---\nlayer: evidence\nconfidence: high\n---\n# {pid}\n{body}\n", encoding="utf-8")
        rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
        rows = chunk_pages(lib)
        texts = [t for _, t, _ in rows]
        mat = np.array(be.embed(texts), dtype=np.float32)
        ch = corpus_hash([(pid, h) for pid, _, h in rows])
        prov = Provenance(model=be.embedding_model_id(), dims=mat.shape[1],
                          normalization="l2", corpus_hash=ch)
        irows = [IndexRow(page_id=pid, content_hash=h) for pid, _, h in rows]
        EmbeddingStore.from_rows(mat, irows, prov).save(lib)
        return EmbeddingStore.load(lib)

    acme = _index(tmp_path / "acme",
                  {"deploys.md": "Elite teams deploy multiple times per day."})
    dora = _index(tmp_path / "dora",
                  {"culture.md": "Generative culture improves software delivery performance."})

    pa = tmp_path / "acme.kbfp.json"
    pd = tmp_path / "dora.kbfp.json"
    write_fingerprint(pa, export_fingerprint(acme, tier="page", manifest=Manifest(handle="acme")))
    write_fingerprint(pd, export_fingerprint(dora, tier="coarse",
                                             manifest=Manifest(handle="dora"), clusters=2))
    fps = [load_fingerprint(pa), load_fingerprint(pd)]
    assert all(f is not None for f in fps)

    qvec = be.embed(["how often do elite teams deploy?"])[0]
    qprov = Provenance(model=be.embedding_model_id(), dims=len(qvec),
                       normalization="l2", corpus_hash="")
    hits = discover(qvec, fps, query_provenance=qprov)
    # both fingerprints are compatible (same model) -> both ranked; no crash
    assert len(hits) == 2
    assert {h.handle for h in hits} == {"acme", "dora"}
```

- [ ] **Step 3: Run (skips without Ollama)**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -v`
Expected: PASS (executing live — Ollama is available) or SKIP. **Defer this run until the gemma4:12b ratification finishes** (Ollama has one inference slot); embeddings via `nomic-embed-text` are cheap, but avoid contending with the running generation job.

- [ ] **Step 4: Lint + commit**

Run: `.venv/bin/python -m flake8 --max-line-length=127 tests/test_kb_offline_ollama_smoke.py`
Expected: clean.
```bash
git add tests/test_kb_offline_ollama_smoke.py
git commit -m "$(cat <<'EOF'
test(kb-offline): live Ollama smoke for fingerprint export + discover (skips w/o Ollama) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Final verification (after all tasks)

- [ ] **Full non-live suite green**

Run: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q`
Expected: all pass; no regressions in fusion/embeddings/federation/CLI.

- [ ] **Lint the whole changed surface**

Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fingerprint.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_fingerprint.py tests/test_kb_offline_cli.py tests/test_kb_offline_ollama_smoke.py`
Expected: clean.

---

## Self-review notes

**Spec coverage:** §1 scope (B, both tiers) → Tasks 3/5/6. §2 architecture/module interface → all tasks (`fingerprint.py`). §3 artifact format (version/tier/manifest/provenance/vectors/weights/data_sha256; nested arrays; no corpus_hash/page_ids) → Tasks 1+3 (+ privacy tests). §4 scoring (max cosine, n_hits page-only, raw-score+tier ranking, min_score/top/hit_threshold) → Task 4 (+ CLI 6). §5 threat model (page_ids stripped, content/corpus_hash/shelf absent, compatibility gate) → Tasks 3 (privacy assertions) + 4 (compat gate). §6 CLI (`fingerprint export` required `--tier`, freshness gate, `--allow-stale`; `discover` embed-once, embedding-capable gate, sources, exit 0 on empty) → Tasks 5+6. §7 testing (round-trip, privacy, tiers, integrity/compat, scoring, CLI, gated live smoke) → Tasks 1-7.

**Placeholder scan:** none — every code step is complete. Task 7's `_ollama_ready`/`OllamaBackend` references are flagged as "match the file's real conventions" (Step 1 inspects them), the deliberate live-smoke pattern, not a production placeholder.

**Type/name consistency:** `Manifest(handle, owner="", contact=None)`, `Fingerprint(tier, manifest, provenance, vectors, weights=None)`, `export_fingerprint(store, *, tier, manifest, clusters=8, weights=True, seed=7) -> dict`, `load_fingerprint(path) -> Fingerprint|None`, `score_fingerprint(qvec, fp, *, hit_threshold=0.5) -> (score, n_hits)`, `discover(qvec, fingerprints, *, query_provenance, min_score=0.0, hit_threshold=0.5, top=None) -> [DiscoverHit]`, `DiscoverHit(handle, owner, contact, tier, score, n_hits)` — used identically across module + CLI + tests. The provenance passed to `compatible` is a `Provenance` on both sides (query built with `corpus_hash=""`; fingerprint built with `corpus_hash=""` in `load_fingerprint`), and `compatible` ignores `corpus_hash`. CLI `main` gains `fingerprints_override=None`, threaded to `_cmd_discover(args, backend_override, fingerprints_override)`.

**Honest note:** page-tier `n_hits` counts matching *vectors*, which equals matching *pages* only when no page exceeds the `chunk_pages` section threshold (the common case for the eval/test corpora). Section-chunked large pages contribute multiple vectors; this is documented in `export_fingerprint`'s docstring and is acceptable for a coverage heuristic (it never inflates a library's top score, only the n_hits column).

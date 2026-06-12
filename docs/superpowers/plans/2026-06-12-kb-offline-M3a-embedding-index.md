# kb-offline M3a — embedding index + store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the off-by-default, rebuildable embedding index for the offline kit — `kb-offline index` embeds library pages and stores them behind a narrow numpy-backed `EmbeddingStore` with provenance, hash-based incremental re-embed, and crash/reader-safe atomic replacement.

**Architecture:** numpy exact search (L2-normalized float32 `.npy` matrix + JSON sidecar, behind an `EmbeddingStore` seam). Page-level chunking (row-per-vector by `page_id`). `search` aggregates best-score-per-page then takes top-k with a `k_eff` small-index guard. Persistence = immutable `embeddings.<gen>.{npy,meta.json}` + one atomically-replaced `embeddings.manifest.json` pointer. `kb-offline index` gates on embedding-capable backends only.

**Tech Stack:** Python 3.9+, numpy (new `[offline]` dep), the project `.venv`, pytest. Backends' `embed()` seam. Spec: `docs/superpowers/specs/2026-06-12-kb-offline-M3a-embedding-index-design.md`.

---

## Environment & scope

- **`.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. Confirm numpy is installed in the venv after Task 1 (`.venv/bin/python -c "import numpy"`); if not, `.venv/bin/pip install numpy`. Lint: flake8@127.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **In scope:** `embeddings.py` (store + chunking), `embedding_model_id()` on capable backends, numpy dep, `kb-offline index` CLI.
- **Out of scope:** section-fallback chunking, accelerated retrieval + recall@k gate (M3b), federation RRF (M3c), conflict lint (M3d), sqlite-vec.

## Reused APIs (verified)

- Backends: `embed(texts: list[str]) -> list[list[float]]` (all). `FakeBackend.embed` → deterministic 8-dim vectors. `OllamaBackend.embed_model` = `"nomic-embed-text"`. `AnthropicBackend.embed` **raises** (not embedding-capable).
- `resume.content_hash(text) -> sha256 hex`.
- `durability.atomic_write_text(path, text, encoding="utf-8") -> Path` (fsync file+dir, temp+rename).
- `kb_lint_fix._is_library_file(path, library_path) -> bool` (excludes `_shelf-index.md`/`_index.md`/`log.md`/`raw/`, non-`.md`) and `_FRONTMATTER_RE` (`.match(text)`; `text[m.end():]` is the body after the frontmatter block; CRLF-aware).
- CLI: `kb_offline_cli.main(argv=None, *, backend_override=None, allowed_layers=None, library_specs_override=None, sources_override=None)`; `_make_backend(name, override, *, options=None, model=None)`; subparsers var `sub`; `import sys`/`Path` present.

## File structure (M3a)

| File | Responsibility |
|---|---|
| `scripts/backends/base.py` (modify) | document `embedding_model_id()` as the embedding-capability signal |
| `scripts/backends/ollama_backend.py` (modify) | `embedding_model_id()` → `self.embed_model` |
| `scripts/backends/fake_backend.py` (modify) | `embedding_model_id()` → `"fake-embed"` |
| `scripts/embeddings.py` (new) | `Provenance`, `IndexRow`, `EmbeddingStore` (from_rows/load/save/search), `chunk_pages`, `corpus_hash` |
| `scripts/kb_offline_cli.py` (modify) | `index` subcommand (capability gate, incremental embed, atomic replace) |
| `pyproject.toml` (modify) | add `numpy` to `[offline]` |
| Tests | `tests/test_kb_offline_embeddings.py`, append CLI test to `tests/test_kb_offline_cli.py`, live smoke to `tests/test_kb_offline_ollama_smoke.py` |

---

## Task 1: numpy dep + `embedding_model_id()` capability on backends

**Files:** Modify `pyproject.toml`, `scripts/backends/{base,ollama_backend,fake_backend}.py`; Test `tests/test_kb_offline_embeddings.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_embeddings.py`:
```python
"""Embedding index + store tests. kb-offline M3a (#211)."""
from __future__ import annotations

import pytest

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_fake_backend_advertises_embedding_model_id():
    assert FakeBackend().embedding_model_id() == "fake-embed"


def test_anthropic_backend_is_not_embedding_capable():
    from sdlc_knowledge_base_scripts.backends.anthropic_backend import AnthropicBackend
    # AnthropicBackend must NOT expose embedding_model_id (capability signal for the index gate)
    assert not hasattr(AnthropicBackend, "embedding_model_id")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -v`
Expected: FAIL (FakeBackend has no `embedding_model_id`).

- [ ] **Step 3: Add numpy + the capability method**

In `pyproject.toml`, add `numpy` to the `[offline]` extra:
```toml
offline = [
  "langgraph",
  "langgraph-checkpoint-sqlite",
  "ollama",
  "numpy",
]
```
Then `.venv/bin/pip install numpy` (confirm `.venv/bin/python -c "import numpy; print(numpy.__version__)"`).

In `scripts/backends/fake_backend.py`, add the method to `FakeBackend`:
```python
    def embedding_model_id(self) -> str:
        return "fake-embed"
```
In `scripts/backends/ollama_backend.py`, add to `OllamaBackend`:
```python
    def embedding_model_id(self) -> str:
        return self.embed_model
```
In `scripts/backends/base.py`, add a doc note to the `Backend` Protocol (below `embed`) — do NOT make it a required Protocol method (Anthropic intentionally lacks it):
```python
    # Embedding-capable backends ALSO expose `embedding_model_id(self) -> str` returning the
    # embedding model's identity (for index provenance). Backends whose embed() is unsupported
    # (e.g. AnthropicBackend) intentionally omit it — its absence is the capability signal the
    # `kb-offline index` gate checks via getattr(backend, "embedding_model_id", None).
```
Do NOT add `embedding_model_id` to `AnthropicBackend`.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -v` → 2 passed. flake8 clean on the three backend files + test.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/pyproject.toml plugins/sdlc-knowledge-base/scripts/backends/base.py plugins/sdlc-knowledge-base/scripts/backends/ollama_backend.py plugins/sdlc-knowledge-base/scripts/backends/fake_backend.py tests/test_kb_offline_embeddings.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): numpy [offline] dep + embedding_model_id capability on embed backends (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `EmbeddingStore` core — dataclasses + construct + `search`

**Files:** Create `scripts/embeddings.py`; Test append to `tests/test_kb_offline_embeddings.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
import numpy as np

from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore, IndexRow, Provenance


def _store(vectors, page_ids):
    rows = [IndexRow(page_id=p, content_hash=f"h{i}") for i, p in enumerate(page_ids)]
    prov = Provenance(model="fake-embed", dims=len(vectors[0]), normalization="l2", corpus_hash="c")
    return EmbeddingStore.from_rows(np.array(vectors, dtype=np.float32), rows, prov)


def test_search_returns_nearest_page():
    # 3 orthogonal-ish vectors; query closest to row 1
    store = _store([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ["a.md", "b.md", "c.md"])
    res = store.search([0.1, 1.0, 0.1], k=2)
    assert res[0][0] == "b.md"            # nearest
    assert len(res) == 2 and res[0][1] >= res[1][1]   # ordered desc


def test_search_k_larger_than_pages_is_safe():
    store = _store([[1, 0], [0, 1]], ["a.md", "b.md"])
    res = store.search([1, 0], k=8)       # k > P must NOT crash (k_eff guard)
    assert len(res) == 2 and res[0][0] == "a.md"


def test_search_empty_index_returns_empty():
    prov = Provenance(model="m", dims=3, normalization="l2", corpus_hash="c")
    store = EmbeddingStore.from_rows(np.zeros((0, 3), dtype=np.float32), [], prov)
    assert store.search([1, 0, 0], k=5) == []


def test_search_aggregates_best_score_per_page_before_topk():
    # two rows share page 'a.md' (simulates future section rows); 'a.md' must appear ONCE
    store = _store([[1, 0, 0], [0.9, 0.1, 0], [0, 1, 0]], ["a.md", "a.md", "b.md"])
    res = store.search([1, 0, 0], k=8)
    page_ids = [p for p, _ in res]
    assert page_ids.count("a.md") == 1 and "b.md" in page_ids   # deduped to best, not page-hogging


def test_search_zero_query_returns_empty():
    store = _store([[1, 0], [0, 1]], ["a.md", "b.md"])
    assert store.search([0, 0], k=2) == []


def test_search_handles_zero_row_vector_without_nan():
    store = _store([[0, 0, 0], [1, 0, 0]], ["a.md", "b.md"])
    res = store.search([1, 0, 0], k=2)
    assert res[0][0] == "b.md"            # zero row scores 0, never NaN
    assert all(not np.isnan(s) for _, s in res)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k search -v`
Expected: FAIL (ImportError: embeddings).

- [ ] **Step 3: Implement the store core in `scripts/embeddings.py`**

Create `scripts/embeddings.py`:
```python
"""Embedding index + store (#211, M3a) — the OPTIONAL, off-by-default accelerator foundation.
numpy exact cosine search over an L2-normalized float32 matrix, behind a narrow EmbeddingStore
seam. Page-level chunking; row-per-vector keyed by page_id (section-fallback additive later).
Index is derived/gitignored/rebuildable."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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
    """Row-wise L2 normalize; zero rows stay zero (no NaN)."""
    m = np.ascontiguousarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0                      # guard: zero rows -> divide by 1 -> stay zero
    return (m / norms).astype(np.float32)


class EmbeddingStore:
    def __init__(self, matrix: np.ndarray, rows: list, provenance: Provenance):
        self.matrix = matrix                     # (N, dims) L2-normalized float32
        self.rows = rows                         # list[IndexRow], parallel to matrix rows
        self.provenance = provenance

    @classmethod
    def from_rows(cls, matrix: np.ndarray, rows: list, provenance: Provenance) -> "EmbeddingStore":
        """Construct from raw (un-normalized) vectors; normalizes at build."""
        norm = _l2_normalize(matrix) if matrix.shape[0] else matrix.astype(np.float32).reshape(0, provenance.dims)
        return cls(norm, list(rows), provenance)

    def search(self, query_vec, k: int = 8) -> list:
        """Exact cosine top-k PAGES. Aggregates best score per page_id FIRST, then selects the
        page-level top-k with a k_eff = min(k, P) guard (bare argpartition(...,k) crashes when
        k >= length). Empty index or zero query -> []."""
        if self.matrix.shape[0] == 0:
            return []
        q = np.asarray(query_vec, dtype=np.float32)
        qn = np.linalg.norm(q)
        if qn == 0:
            return []
        q = q / qn
        scores = self.matrix @ q                 # (N,) cosine
        best: dict[str, float] = {}
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
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k search -v` → 6 passed. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/embeddings.py tests/test_kb_offline_embeddings.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): EmbeddingStore core — L2 cosine search, page-aggregate top-k, k_eff guard (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `save`/`load` — generation + manifest atomic, corruption → rebuild

**Files:** Modify `scripts/embeddings.py`; Test append to `tests/test_kb_offline_embeddings.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
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
    store = _store([[1, 0, 0], [0, 1, 0]], ["a.md", "b.md"])
    store.save(tmp_path)
    # corrupt the sidecar: drop a row so rows(1) != matrix rows(2)
    import json
    d = tmp_path / ".kb-offline"
    manifest = json.loads((d / "embeddings.manifest.json").read_text())
    meta_path = d / f"embeddings.{manifest['active']}.meta.json"
    meta = json.loads(meta_path.read_text())
    meta["rows"] = meta["rows"][:1]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert EmbeddingStore.load(tmp_path) is None


def test_save_is_generation_pointer(tmp_path):
    store = _store([[1, 0, 0]], ["a.md"])
    store.save(tmp_path)
    d = tmp_path / ".kb-offline"
    import json
    manifest = json.loads((d / "embeddings.manifest.json").read_text())
    gen = manifest["active"]
    assert (d / f"embeddings.{gen}.npy").is_file()
    assert (d / f"embeddings.{gen}.meta.json").is_file()
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k "save or load" -v`
Expected: FAIL (no `save`/`load`).

- [ ] **Step 3: Implement `save`/`load`**

Append to `scripts/embeddings.py` (add imports at top: `import json`, `import sys`, `import uuid`, `from .durability import atomic_write_text`):
```python
    def save(self, library_path) -> None:
        """Crash/reader-safe via immutable generation files + an atomically-replaced pointer.
        Write embeddings.<gen>.npy + embeddings.<gen>.meta.json (fresh unique gen, write-once),
        then atomic_write_text the manifest naming the active gen. Prune stale generations
        best-effort after the flip."""
        d = Path(library_path) / ".kb-offline"
        d.mkdir(parents=True, exist_ok=True)
        gen = uuid.uuid4().hex[:16]
        np.save(d / f"embeddings.{gen}.npy", self.matrix, allow_pickle=False)
        meta = {"provenance": vars(self.provenance),
                "rows": [{"page_id": r.page_id, "content_hash": r.content_hash} for r in self.rows]}
        atomic_write_text(d / f"embeddings.{gen}.meta.json", json.dumps(meta, indent=2))
        atomic_write_text(d / "embeddings.manifest.json",
                          json.dumps({"active": gen, "schema_version": self.provenance.schema_version}))
        # prune older generations (best-effort; a leftover never corrupts a load)
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
        incompatible state — the index is derived, so a defect just triggers a clean rebuild."""
        d = Path(library_path) / ".kb-offline"
        manifest_path = d / "embeddings.manifest.json"
        if not manifest_path.is_file():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema_version") != 1:
                print(f"[index] unsupported schema_version {manifest.get('schema_version')}; rebuild required", file=sys.stderr)
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
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -v` → all pass. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/embeddings.py tests/test_kb_offline_embeddings.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): EmbeddingStore save/load — generation+manifest atomic, corruption->rebuild (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `chunk_pages` + `corpus_hash`

**Files:** Modify `scripts/embeddings.py`; Test append to `tests/test_kb_offline_embeddings.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
from sdlc_knowledge_base_scripts.embeddings import chunk_pages, corpus_hash


def _mk(lib, rel, body):
    p = lib / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_chunk_pages_page_id_is_relative_posix_and_strips_frontmatter(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _mk(lib, "dora.md", "---\nlayer: evidence\n---\n# DORA\nDeploy often.\n")
    _mk(lib, "sub/ops.md", "# Ops\nCanary.\n")
    _mk(lib, "_shelf-index.md", "<!-- format_version: 1 -->\n# Shelf\n")   # excluded
    _mk(lib, "raw/src.md", "raw source")                                  # excluded (raw/)
    rows = {pid: (text, h) for pid, text, h in chunk_pages(lib)}
    assert set(rows) == {"dora.md", "sub/ops.md"}            # meta + raw excluded; POSIX rel path
    assert "layer: evidence" not in rows["dora.md"][0]       # frontmatter stripped
    assert "# DORA" in rows["dora.md"][0] and "Deploy often." in rows["dora.md"][0]


def test_corpus_hash_changes_on_rename(tmp_path):
    # same content, different page_id -> different corpus_hash (rename sensitivity)
    rows_a = [("a.md", "h1"), ("b.md", "h2")]
    rows_b = [("a.md", "h1"), ("renamed.md", "h2")]   # b.md -> renamed.md, same content hash
    assert corpus_hash(rows_a) != corpus_hash(rows_b)


def test_corpus_hash_order_independent(tmp_path):
    rows_a = [("a.md", "h1"), ("b.md", "h2")]
    rows_b = [("b.md", "h2"), ("a.md", "h1")]
    assert corpus_hash(rows_a) == corpus_hash(rows_b)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k "chunk or corpus" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement**

Append to `scripts/embeddings.py` (add imports: `from .resume import content_hash`, `from .kb_lint_fix import _FRONTMATTER_RE, _is_library_file`):
```python
def _strip_frontmatter(text: str) -> str:
    m = _FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def chunk_pages(library_path) -> list:
    """Page-level rows: (page_id, embed_text, content_hash). page_id = library-relative POSIX
    path; embed_text = page with YAML frontmatter stripped; content_hash over embed_text.
    Reuses the fixer's _is_library_file exclusions (skips meta files + raw/, non-.md)."""
    lib = Path(library_path)
    out = []
    for md in sorted(lib.rglob("*.md")):
        if not _is_library_file(md, lib):
            continue
        page_id = md.relative_to(lib).as_posix()
        embed_text = _strip_frontmatter(md.read_text(encoding="utf-8"))
        out.append((page_id, embed_text, content_hash(embed_text)))
    return out


def corpus_hash(page_hash_pairs) -> str:
    """Hash over sorted (page_id, content_hash) pairs — a content-preserving RENAME changes it;
    order-independent."""
    joined = "\n".join(f"{pid}\x00{h}" for pid, h in sorted(page_hash_pairs))
    return content_hash(joined)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -v` → all pass. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/embeddings.py tests/test_kb_offline_embeddings.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): chunk_pages (POSIX page_id, frontmatter-stripped) + rename-sensitive corpus_hash (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `kb-offline index` CLI (capability gate + incremental + atomic) + live smoke

**Files:** Modify `scripts/kb_offline_cli.py`; Test append to `tests/test_kb_offline_cli.py`, `tests/test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Write the failing CLI tests**

Append to `tests/test_kb_offline_cli.py`:
```python
def test_cli_index_builds_and_is_incremental(tmp_path, capsys):
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "a.md").write_text("---\nlayer: evidence\n---\n# A\nAlpha content.\n")
    (lib / "b.md").write_text("# B\nBeta content.\n")
    be = FakeBackend()
    rc = cli.main(["index", "--library", str(lib), "--backend", "fake"], backend_override=be)
    assert rc == 0
    out = capsys.readouterr().out
    assert "indexed" in out.lower() and "2" in out          # 2 pages
    store = EmbeddingStore.load(lib)
    assert store is not None and {r.page_id for r in store.rows} == {"a.md", "b.md"}
    assert store.provenance.model == "fake-embed"
    # re-run unchanged -> incremental: 0 re-embedded
    rc2 = cli.main(["index", "--library", str(lib), "--backend", "fake"], backend_override=be)
    assert rc2 == 0
    assert "0 re-embedded" in capsys.readouterr().out


def test_cli_index_rejects_anthropic(tmp_path):
    import pytest
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "a.md").write_text("# A\n")
    with pytest.raises(SystemExit, match="does not support embeddings"):
        cli.main(["index", "--library", str(lib), "--backend", "anthropic"])
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k index -v`
Expected: FAIL (`invalid choice: 'index'`).

- [ ] **Step 3: Implement the `index` CLI**

In `scripts/kb_offline_cli.py`, add `_cmd_index`:
```python
def _cmd_index(args: argparse.Namespace, backend_override) -> int:
    import numpy as np
    from .embeddings import EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash
    backend = _make_backend(args.backend, backend_override)
    if getattr(backend, "embedding_model_id", None) is None:
        raise SystemExit(f"backend '{args.backend}' does not support embeddings; use ollama or fake")
    lib = Path(args.library)
    model = backend.embedding_model_id()
    pages = chunk_pages(lib)                       # [(page_id, embed_text, content_hash)]

    existing = EmbeddingStore.load(lib)
    compatible = existing is not None and existing.provenance.model == model
    prior = {}
    if compatible:
        prior = {r.page_id: (r.content_hash, i) for i, r in enumerate(existing.rows)}

    reused_vecs, new_rows, new_texts, reembedded, unchanged = [], [], [], 0, 0
    final_rows, vec_slots = [], []                 # vec_slots: ("reuse", idx) | ("new", new_index)
    to_embed = []
    for page_id, text, chash in pages:
        if page_id in prior and prior[page_id][0] == chash:
            final_rows.append(IndexRow(page_id=page_id, content_hash=chash))
            vec_slots.append(("reuse", prior[page_id][1]))
            unchanged += 1
        else:
            final_rows.append(IndexRow(page_id=page_id, content_hash=chash))
            vec_slots.append(("new", len(to_embed)))
            to_embed.append(text)
            reembedded += 1
    removed = len(prior) - unchanged if compatible else 0
    if removed < 0:
        removed = 0

    new_vecs = np.array(backend.embed(to_embed), dtype=np.float32) if to_embed else None
    dims = (new_vecs.shape[1] if new_vecs is not None and new_vecs.shape[0]
            else (existing.provenance.dims if compatible else 0))
    matrix = np.zeros((len(final_rows), dims), dtype=np.float32) if dims else np.zeros((0, 0), dtype=np.float32)
    for row_i, (kind, idx) in enumerate(vec_slots):
        if kind == "reuse":
            matrix[row_i] = existing.matrix[idx]
        else:
            matrix[row_i] = new_vecs[idx]
    prov = Provenance(model=model, dims=dims, normalization="l2",
                      corpus_hash=corpus_hash([(r.page_id, r.content_hash) for r in final_rows]))
    EmbeddingStore.from_rows(matrix, final_rows, prov).save(lib)
    print(f"indexed {len(final_rows)} pages ({reembedded} re-embedded, {unchanged} unchanged, "
          f"{removed} removed); index at {lib / '.kb-offline'}")
    return 0
```
Add the subparser (under `sub`):
```python
    p_index = sub.add_parser("index")
    p_index.add_argument("--library", default="library")
    p_index.add_argument("--backend", default="ollama")
```
Add the dispatch: `if args.cmd == "index": return _cmd_index(args, backend_override)`.
Note: reused vectors in `existing.matrix` are already L2-normalized; `from_rows` re-normalizes the assembled matrix (idempotent for already-unit rows; newly-embedded rows get normalized for the first time) — consistent and correct. Confirm `_make_backend("fake", backend_override)` returns the override (it does for any name when override is not None).

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k index -v` → 2 passed. Then full gate:
```bash
.venv/bin/python -m pytest tests/ -k "kb and not live" -q
.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_offline_embeddings.py tests/test_kb_offline_cli.py
.venv/bin/python tools/validation/check-prompt-parity.py
```
All green / clean / parity OK.

- [ ] **Step 5: Append the live Ollama index smoke** to `tests/test_kb_offline_ollama_smoke.py`:
```python
@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_index(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.embeddings import chunk_pages, EmbeddingStore, IndexRow, Provenance, corpus_hash
    import numpy as np
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\n---\n# DORA\nElite teams deploy multiple times per day.\n")
    be = OllamaBackend()  # embed_model nomic-embed-text
    pages = chunk_pages(lib)
    vecs = np.array(be.embed([t for _, t, _ in pages]), dtype=np.float32)
    rows = [IndexRow(page_id=p, content_hash=h) for p, _, h in pages]
    prov = Provenance(model=be.embedding_model_id(), dims=vecs.shape[1], normalization="l2",
                      corpus_hash=corpus_hash([(p, h) for p, _, h in pages]))
    EmbeddingStore.from_rows(vecs, rows, prov).save(lib)
    loaded = EmbeddingStore.load(lib)
    assert loaded is not None and loaded.provenance.model == "nomic-embed-text"
    assert loaded.provenance.dims > 0
    hit = loaded.search(be.embed(["how often do elite teams deploy?"])[0], k=1)
    assert hit and hit[0][0] == "dora.md"   # the one page is the nearest
```
(Run it manually if Ollama is up: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -k index -v -s` — it SKIPs in CI.)

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py tests/test_kb_offline_ollama_smoke.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): CLI index subcommand — capability gate + incremental embed + atomic store (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** §1 store (search k_eff + page-aggregate + zero guards; save/load generation+manifest + corruption→None) → Tasks 2+3; §2 chunking (POSIX page_id, frontmatter strip) → Task 4; §3 incremental + provenance-mismatch full rebuild + atomic → Task 5 (`_cmd_index` reuse/re-embed/removed logic; `compatible` gate on model match) + Task 3 (atomic); §4 CLI + capability gate + provenance-from-backend (`model`/`dims` observed) → Task 5; §1 embedding descriptor contract → Task 1. All 8 decisions + 6 review-resolutions covered.
- **Type/name consistency:** `Provenance(model, dims, normalization, corpus_hash, schema_version)`; `IndexRow(page_id, content_hash)`; `EmbeddingStore.from_rows/load/save/search`; `chunk_pages -> [(page_id, embed_text, content_hash)]`; `corpus_hash(pairs)`; `embedding_model_id()`; CLI `index --library --backend` — consistent across tasks.
- **Review-resolution coverage:** k_eff (Task 2 `test_search_k_larger_than_pages`); generation+manifest atomic (Task 3 `test_save_is_generation_pointer`); backend gate + provenance-from-backend (Task 5 `test_cli_index_rejects_anthropic` + model assertion); page-aggregate-before-topk (Task 2 `test_search_aggregates_best_score_per_page`); page_id POSIX + rename-sensitive corpus_hash (Task 4); load corruption→None (Task 3 four corruption tests).
- **Known verification points:** confirm numpy installs in the venv (Task 1); `np.save` appends `.npy` only if absent — we pass the full `embeddings.<gen>.npy` name (np.save will NOT double-append since it ends in .npy); `existing.matrix[idx]` reuse assumes row order stable across loads (it is — rows + matrix are parallel and saved/loaded together); the provenance-mismatch path (`compatible=False`) forces every page into `to_embed` (full rebuild) — confirm `removed` stays ≥0 and dims come from the fresh embeddings.
- **Build-only:** nothing consumes the index in M3a; proven via store search unit tests + the live smoke's own search assertion. Retrieval wiring is M3b.
- **No silent caps:** the summary line reports re-embedded/unchanged/removed; load corruption prints the reason to stderr before rebuild.

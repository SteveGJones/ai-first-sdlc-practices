# kb-offline M3a — embedding index + store design (optional accelerator foundation)

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph`. **Builds on:** the backend `embed(texts) -> list[list[float]]` seam (all backends; `OllamaBackend` uses `nomic-embed-text`), `resume.content_hash`, `provenance`/`kb_lint_fix._is_library_file` page conventions, `durability.atomic_write_text`. **Parent:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (§Embedding accelerator).

**Goal:** Build the foundational, **off-by-default**, rebuildable embedding index for the offline kit — `kb-offline index` embeds library pages and stores them behind a narrow store interface with provenance and hash-based incremental re-embed. This is the foundation the M3b accelerated-retrieval / M3c RRF-federation / M3d conflict-lint slices build on.

**Decomposition note:** M3 = **M3a (index+store, this spec)** / M3b (accelerated retrieval + recall@k gate) / M3c (federation RRF + index-compat rejection) / M3d (semantic cross-library conflict lint). M3a is build-only and self-contained.

---

## Decisions (from brainstorm)

1. **Store = numpy exact search now, abstraction from day one.** A contiguous **L2-normalized float32** matrix in a standalone `.npy` (mmap-friendly) + a JSON metadata sidecar. Behind a narrow `EmbeddingStore` interface so a sqlite-vec (or other) backend can replace it later with no churn to M3b/M3c callers. (Correction noted: sqlite-vec's current `vec0` is exact KNN/full-scan, not ANN — so it offers neither recall loss nor a million-vector advantage today; numpy exact search wins on dependency-lightness at this kit's scale.)
2. **numpy declared explicitly** in the `[offline]` extra — no transitive-install reliance.
3. **Load the matrix once per store/process** and reuse across searches (not per-search).
4. **Search** = matrix-vector product (cosine = dot on normalized vectors) → `np.argpartition` → sort only the selected top-k.
5. **Provenance block** persists `model`, `dims`, `normalization`, `corpus_hash`, `schema_version` (for M3c index-compat rejection + staleness).
6. **Atomic index replacement** after incremental rebuild (temp files → atomic rename; never a torn `.npy`/sidecar pair).
7. **Chunking: page-level only in M3a**; store is **row-per-vector keyed by `page_id`** so the deferred section-fallback chunker is purely additive (more rows, same `page_id`, same resolve-to-page path).
8. **Scale measured in vectors, not pages.** Migration trigger (documented): re-evaluate the backend when measured vector-search p95 exceeds budget, or a typical library approaches ~100k–250k vectors (~300–750 MB float32 matrix).
9. **Index is derived/gitignored/off-by-default**; build is model-touching but **linear — no graph, no lock** (rebuildable; atomic write suffices).

---

## §1 `EmbeddingStore` (`scripts/embeddings.py`)

```python
@dataclass
class Provenance:
    model: str
    dims: int
    normalization: str       # "l2"
    corpus_hash: str         # content_hash over sorted (page_id, content_hash) pairs — so a
                             # content-preserving RENAME (page_id changes) still changes it
    schema_version: int = 1

@dataclass
class IndexRow:
    page_id: str
    content_hash: str
    # vector lives in the matrix at the row's position; rows + matrix are parallel

class EmbeddingStore:
    """Narrow store seam. Holds a loaded (N, dims) L2-normalized float32 matrix + parallel
    row metadata + provenance. Matrix loaded ONCE per instance and reused."""
    def __init__(self, matrix, rows: list[IndexRow], provenance: Provenance): ...
    @classmethod
    def load(cls, library_path) -> "EmbeddingStore | None":
        """Returns a usable store, or None meaning 'no usable index — rebuild required'. None
        is returned for BOTH absent AND unusable, with a one-line stderr reason on the unusable
        cases (the index is derived, so any defect just triggers a clean rebuild, never an
        error to the operator). Unusable = manifest missing / unreadable; named generation files
        missing; invalid JSON; unsupported schema_version; matrix/row-count mismatch; matrix
        dtype != float32 or ndim != 2 or dims != provenance.dims; any non-finite value in the
        matrix."""
    def save(self, library_path) -> None:
        """Atomic, crash-safe, reader-safe via generation + pointer (a two-file rename is NOT
        atomic as a pair — a reader between the renames sees a mismatched .npy/sidecar). Write
        IMMUTABLE generation-named files `embeddings.<gen>.npy` + `embeddings.<gen>.meta.json`
        (gen = a fresh token), fsync them, then atomically replace ONE pointer manifest
        `embeddings.manifest.json` (= {"active": "<gen>", schema_version}) via temp+rename.
        Readers load the manifest, then the named generation — always a consistent pair. Prune
        stale generations after the pointer flips (best-effort; a leftover never corrupts)."""
    def search(self, query_vec, k: int = 8) -> list[tuple[str, float]]:
        """Exact cosine top-k PAGES. Algorithm (section-ready + small-index-safe):
          1. N == 0 (empty index) -> return [].
          2. L2-normalize the query (zero query -> all-zero scores, returns []/lowest).
          3. scores = matrix @ q  (cosine on normalized vectors).
          4. AGGREGATE to best score per page_id FIRST (a page may own multiple rows once
             section-fallback arrives), THEN select the page-level top-k — selecting k ROWS
             first would return < k pages and allow page-hogging.
          5. P = number of distinct pages; k_eff = min(k, P); if k_eff == 0 -> []; else
             np.argpartition(-page_scores, k_eff - 1)[:k_eff], then sort those k_eff desc.
        Returns [(page_id, score)] best-first. (np.argpartition requires kth < length, so
        k_eff guards the small-library / k>P case that a bare argpartition(..., k) would crash.)"""
```
- **Persistence layout (`library/.kb-offline/`, all gitignored — derived):** a pointer manifest `embeddings.manifest.json` (`{"active": "<gen>", "schema_version": 1}`) + per-generation immutable pairs `embeddings.<gen>.npy` (the matrix) and `embeddings.<gen>.meta.json` (`{provenance, rows:[{page_id, content_hash}]}`). Only the manifest is ever overwritten (atomically); generations are write-once. (Covered by the existing `.kb-offline/` gitignore.)
- **Normalization:** vectors are L2-normalized at build time; a zero/degenerate vector is stored as zeros and scores 0 (never NaN — guard the divide).

## §2 Chunking — page-level (`scripts/embeddings.py` or a small helper)

```python
def chunk_pages(library_path) -> list[tuple[str, str, str]]:
    """One row per content page: (page_id, embed_text, content_hash). Reuses the fixer's
    _is_library_file exclusions (skips _shelf-index.md/_index.md/log.md/raw/). page_id = the
    page's library-relative path as a normalized POSIX string (e.g. 'sub/dora.md') — stable,
    unique under the recursive rglob discovery, and the citable unit. embed_text is the page
    with its YAML frontmatter stripped (the '# Title' + body — the searchable content);
    content_hash = resume.content_hash(embed_text)."""
```
- Frontmatter stripped (it's metadata, not searchable content) via the existing frontmatter regex; the `# title` heading + body are embedded.
- Row-per-vector schema keyed by `page_id` — section rows (future) reuse the same shape.

## §3 Incremental re-embed + atomic replacement (in the `index` op)

- Load the existing `EmbeddingStore` (if any). Compute current pages via `chunk_pages`.
- **Re-embed only new/changed** pages (current `content_hash` ∉ existing rows). **Reuse** existing vectors for unchanged pages (matched by `page_id` + `content_hash`). **Drop** rows for pages no longer present.
- **Provenance mismatch** (the existing index's `model`/`dims`/`normalization` differs from the current backend's) → **full rebuild** (re-embed everything), not a partial merge (vectors from different models are incomparable).
- Recompute `corpus_hash`; assemble the new matrix (reused + freshly-embedded rows); `store.save(...)` does the **atomic** temp-write + rename of both files.

## §4 `kb-offline index` CLI

```
kb-offline index [--library <root>] [--backend ollama|fake]
```
- **Embedding-capability gate (resolves the "advertises a backend it can't use" defect):** only embedding-capable backends are accepted. `AnthropicBackend.embed` always raises, so `--backend anthropic` is **rejected up front** with a clear message (`SystemExit("backend 'anthropic' does not support embeddings; use ollama or fake")`) — not a mid-run crash. Choices are `ollama` (default) and `fake` (tests).
- **Embedding descriptor contract:** embedding-capable backends expose `embedding_model_id() -> str` (`OllamaBackend` → its `embed_model`, e.g. `nomic-embed-text`; `FakeBackend` → `"fake-embed"`). `AnthropicBackend` does not implement it (or it raises) — that's the capability signal the `index` gate checks. **Provenance is sourced from the backend, not hardcoded:** `provenance.model = backend.embedding_model_id()`; `provenance.dims = len(first returned embedding)` (observed from the actual output, so declared-vs-actual can't drift); `provenance.normalization = "l2"`.
- Reads pages → `chunk_pages` → embed changed via `backend.embed` (batched in one or a few calls) → build/update store → atomic replace.
- **Linear, no graph, no lock** (derived rebuildable artifact; atomic write).
- Prints: `indexed N pages (M re-embedded, K unchanged, D removed); index at <path>`.
- `--backend fake` (with `backend_override` test seam, mirroring the other commands) drives deterministic tests.

## §5 Testing + scope

- **Store unit tests (FakeBackend deterministic `embed`):** `search` returns the expected page for a query vector (nearest by cosine); top-k ordering; **best-score-per-page aggregation BEFORE top-k** (so k pages are returned, no page-hogging — exercised with a duplicate-page-id row set even before section chunking exists); **small-index/empty:** `k > P` and `N == 0` return cleanly (no `argpartition` crash) via `k_eff`; provenance round-trips `save`→`load`; zero-vector query/​row guard (no NaN).
- **Load corruption/compat tests:** `load` returns `None` (→ rebuild) for: no manifest; manifest names a missing generation; invalid JSON; unsupported `schema_version`; matrix/row-count mismatch; wrong dtype/ndim/dims; non-finite values — each with the stderr reason.
- **Atomicity test:** `save` writes immutable `embeddings.<gen>.*` then flips the manifest pointer last; a load that races sees a consistent pair; a leftover stale generation never corrupts a load.
- **Backend-gate test:** `index --backend anthropic` exits with the clear "does not support embeddings" message (no mid-run crash); `ollama`/`fake` proceed. `embedding_model_id()` flows into `provenance.model`; `provenance.dims` == observed embedding length.
- **Incremental tests:** changing one page re-embeds only that page (others' vectors reused, byte-identical); removing a page drops its row; **renaming a page (same content) changes `corpus_hash`** (page_id in the hash); a model/dims provenance change triggers full rebuild.
- **CLI `index`:** end-to-end build with `--backend fake`; re-run is incremental (M re-embedded == 0 when nothing changed); the printed summary counts.
- **Live Ollama `index` smoke** behind `_ollama_ready()` (real `nomic-embed-text`): indexes a tiny library, asserts the `.npy` + sidecar exist with the right provenance model/dims.
- **CI execution split preserved:** all gated tests use FakeBackend; live smoke skips in CI.
- **Build-only:** nothing consumes the index in M3a (retrieval is M3b); the store is proven via its own `search` unit tests.

## Components & isolation

| File | Responsibility |
|---|---|
| `scripts/embeddings.py` (new) | `Provenance`, `IndexRow`, `EmbeddingStore` (load/save/search + construct-from-rows), `chunk_pages` |
| `scripts/backends/base.py`, `ollama_backend.py`, `fake_backend.py` (modify) | add `embedding_model_id() -> str` to embedding-capable backends (Anthropic omits it = capability signal) |
| `scripts/kb_offline_cli.py` (modify) | `index` subcommand (capability gate → read→chunk→embed-changed→atomic-replace) |
| `pyproject.toml` (modify) | add `numpy` to the `[offline]` extra |
| Tests | `tests/test_kb_offline_embeddings.py`, append CLI test to `tests/test_kb_offline_cli.py`, live smoke to `tests/test_kb_offline_ollama_smoke.py` |

## Out of scope (deferred)

- **Section-level fallback chunking** ("find fine, read coarse" for oversized pages) — the store schema is ready (row-per-vector by page_id); the chunker lands in M3b/a-follow-on.
- **Accelerated retrieval** (pre-filter into `select`, off-by-default opt-in) + the **recall@k eval gate** — M3b.
- **Federation RRF merge + index-compat rejection** (cross-library) — M3c (M3a persists the provenance that M3c's compat check reads).
- **Semantic cross-library conflict lint** — M3d.
- sqlite-vec store — behind the same interface if/when the measured migration trigger fires.

## Decisions log (M3a delta)

1. numpy exact search now; `.npy` (L2-normalized float32, contiguous, mmap-friendly) + JSON metadata sidecar; narrow `EmbeddingStore` seam.
2. numpy explicit `[offline]` dep; matrix loaded once per process.
3. search = matrix-vector + `np.argpartition` + top-k sort; de-dupe to best score per page_id.
4. provenance = model/dims/normalization/corpus_hash/schema_version; mismatch → full rebuild.
5. atomic replacement of `.npy` + sidecar together; index gitignored/derived/off-by-default.
6. page-level chunking only in M3a; row-per-vector by page_id (section-fallback additive later).
7. `index` is linear, no graph/lock; build-only (retrieval is M3b).
8. migration trigger documented: measured p95 latency or ~100k–250k vectors.

### Spec-review resolutions (pre-implementation hardening)

- **[P1] small-index `search` crash** → `k_eff = min(k, P)`, `N==0`/empty → `[]`, partition at `k_eff-1` (a bare `argpartition(..., k)` crashes when `k ≥ length`).
- **[P1] non-atomic two-rename pair** → immutable generation files `embeddings.<gen>.{npy,meta.json}` + one atomically-replaced `embeddings.manifest.json` pointer; readers load manifest→named generation (always a consistent pair).
- **[P1] CLI advertised an embedding-incapable backend + no provenance contract** → `index` accepts only `ollama`/`fake`; `anthropic` rejected up front; `embedding_model_id()` capability/identity method on capable backends; `provenance.model` from the backend, `provenance.dims` observed from the first embedding (no declared/actual drift).
- **[P1] de-dupe-after-row-top-k returned < k pages** → aggregate best score per `page_id` FIRST, then page-level top-k (section-ready, no page-hogging).
- **[P2] page_id/corpus_hash identity** → `page_id` = normalized library-relative POSIX path; `corpus_hash` over sorted `(page_id, content_hash)` pairs (content-preserving rename still changes it).
- **[P2] load corruption/compat** → `load` returns `None` (= rebuild-required, stderr reason) for missing-file/invalid-JSON/unsupported-schema/row-count-mismatch/wrong-dims-dtype/non-finite — derived index, so any defect cleanly rebuilds.

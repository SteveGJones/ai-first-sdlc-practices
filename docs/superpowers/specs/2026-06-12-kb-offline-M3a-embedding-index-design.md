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
    corpus_hash: str         # hash over all row content_hashes (order-independent)
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
    def load(cls, library_path) -> "EmbeddingStore | None":  # None if no index present
        ...
    def save(self, library_path) -> None:   # atomic: temp .npy + temp sidecar -> rename both
        ...
    def search(self, query_vec, k: int = 8) -> list[tuple[str, float]]:
        """Exact cosine top-k. L2-normalize query, matrix @ q, np.argpartition(-, k), sort the
        k. Returns [(page_id, score)] best-first. De-dupes to best score per page_id (so a page
        with multiple rows — future sections — surfaces once at its best section score)."""
```
- **Persistence:** `library/.kb-offline/embeddings.npy` (the matrix) + `library/.kb-offline/embeddings.meta.json` (`{provenance, rows:[{page_id, content_hash}]}`). Both **gitignored** (add `.kb-offline/embeddings.*` to the kit's gitignore guidance if not already covered by `.kb-offline/`).
- **Normalization:** vectors are L2-normalized at build time; a zero-vector (degenerate) is stored as zeros and scores 0 (never NaN — guard the divide).
- **`search` de-dupe-to-best-per-page** is forward-compatible with section rows (M3b) without changing the interface.

## §2 Chunking — page-level (`scripts/embeddings.py` or a small helper)

```python
def chunk_pages(library_path) -> list[tuple[str, str, str]]:
    """One row per content page: (page_id, embed_text, content_hash). Reuses the fixer's
    _is_library_file exclusions (skips _shelf-index.md/_index.md/log.md/raw/). embed_text is the
    page with its YAML frontmatter stripped (the '# Title' + body — the searchable content);
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
kb-offline index [--library <root>] [--backend ollama|anthropic|fake]
```
- Reads pages → `chunk_pages` → embed changed via `backend.embed` (batched in one or a few calls) → build/update store → atomic replace.
- **Linear, no graph, no lock** (derived rebuildable artifact; atomic write). Backend default `ollama` (the embed model is the backend's `embed_model`, `nomic-embed-text` for Ollama).
- Prints: `indexed N pages (M re-embedded, K unchanged, D removed); index at <path>`.
- `--backend fake` (with `backend_override` test seam, mirroring the other commands) drives deterministic tests.

## §5 Testing + scope

- **Store unit tests (FakeBackend deterministic `embed`):** `build` + `search` returns the expected page for a query vector (nearest by cosine); top-k ordering; de-dupe-to-best-per-page; provenance round-trips through `save`/`load`; `load` returns `None` when no index exists; zero-vector guard (no NaN).
- **Incremental tests:** changing one page re-embeds only that page (others' vectors byte-identical); removing a page drops its row; a model/dims provenance change triggers full rebuild; `save` is atomic (no torn state if interrupted — assert temp-then-rename).
- **CLI `index`:** end-to-end build with `--backend fake`; re-run is incremental (M re-embedded == 0 when nothing changed); the printed summary counts.
- **Live Ollama `index` smoke** behind `_ollama_ready()` (real `nomic-embed-text`): indexes a tiny library, asserts the `.npy` + sidecar exist with the right provenance model/dims.
- **CI execution split preserved:** all gated tests use FakeBackend; live smoke skips in CI.
- **Build-only:** nothing consumes the index in M3a (retrieval is M3b); the store is proven via its own `search` unit tests.

## Components & isolation

| File | Responsibility |
|---|---|
| `scripts/embeddings.py` (new) | `Provenance`, `IndexRow`, `EmbeddingStore` (build/load/save/search), `chunk_pages` |
| `scripts/kb_offline_cli.py` (modify) | `index` subcommand (read→chunk→embed-changed→atomic-replace) |
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

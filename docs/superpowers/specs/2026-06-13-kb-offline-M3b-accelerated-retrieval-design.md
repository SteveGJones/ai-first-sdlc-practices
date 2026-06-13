# kb-offline M3b — accelerated retrieval + recall@k gate design

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph`. **Builds on:** M3a (`EmbeddingStore.search`, `chunk_pages`, `corpus_hash`, the `index` CLI), M1c-1 (`pipeline.select`, `query_graph`), M1c-2 (eval suite `expected_routing_targets`, `harness`, `thresholds`). **Parent:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (§Embedding accelerator).

**Goal:** Make the M3a embedding index do real work — an **opt-in, off-by-default** accelerated retrieval path where embeddings **discover** a candidate shortlist and the shelf-index reasoning **selects** over a reduced shelf — plus a recall@k eval gate proving the prefilter doesn't drop answers. Includes the M3a-deferred section-fallback chunking.

**Decomposition note:** M3 = M3a (index+store, DONE) / **M3b (accelerated retrieval + recall@k gate, this spec)** / M3c (federation RRF + the privacy-preserving "find who to ask" federation-discovery) / M3d (semantic conflict lint). M3b is **single-library**.

---

## Architecture principle (the layer split — see memory `feedback_embeddings_discovery_vs_reasoning`)

Two distinct, non-collapsed layers:
- **Discovery (embeddings):** fast, fuzzy, high-recall candidate generation. (In M3c+, also privacy-preserving + shareable across orgs = "find who to ask"; out of scope here.)
- **Reasoning / assembly (shelf-`select`):** the curated, reasoned selection that gives **quality**. **Never replaced** — embeddings recall, the shelf decides.

The accelerated path: **embeddings discover top-N → reduced shelf (those N entries) → `select` reasons over it.** Default path (embeddings off) is the M1c-1/M2b full-shelf reasoned select, **unchanged**.

## Decisions (from brainstorm)

1. **Reduced-shelf integration** (the scale win): discover → build a reduced shelf of the top-N entries → `select` reasons over it. Not "constrain known_pages only" (that reads the full shelf = no scale benefit).
2. **Shortlist width N = 20 default**, `--accelerate-k` override; the recall@k gate validates the width.
3. **recall@k gate = absolute**: mean embedding recall@N of `expected_routing_targets` ≥ **0.95** (ratified `EMBEDDING_RECALL_AT_K`). (Shelf-only retrieval trivially sees all pages → 1.0, so a comparative baseline is meaningless; the absolute floor proves the prefilter rarely drops a needed page.)
4. **Section-fallback chunking included**: pages > ~2000 chars split on `##` into section rows (parent page_id); `search` resolves a section hit to the whole page.
5. **`--accelerate` opt-in; missing/stale index → warn + full-shelf fallback** (never fail the query). Staleness = index `corpus_hash` ≠ current library `corpus_hash`.
6. **Single-library** — federation-discovery is M3c.

---

## §1 Section-fallback chunking (`embeddings.chunk_pages`, extended)

```python
def chunk_pages(library_path, *, section_threshold: int = 2000) -> list:
    """Rows (page_id, embed_text, content_hash). Pages whose frontmatter-stripped body is
    <= section_threshold chars -> ONE page-level row (M3a behavior). Over threshold -> split
    the body on `##` headings: a preamble row (text before the first `##`) + one row per `##`
    section, ALL sharing the page's page_id, each with its own content_hash. A section hit
    resolves to the whole page in search (best-score-per-page dedupe)."""
```
- All rows of a page carry the same `page_id` (the library-relative POSIX path); section identity is the row's `content_hash` (over the section text). Empty/whitespace sections are skipped.
- Backward compatible: small pages still produce exactly one row; the M3a tests stay green (their pages are under 2000 chars).
- Incremental re-embed + `corpus_hash` already operate per-row, so a changed section re-embeds only that row; `corpus_hash` over all (page_id, content_hash) rows.
- `section_threshold` is a parameter (the `index` CLI may expose `--section-threshold` later; default 2000 for M3b).

## §2 Accelerated discovery → reduced shelf (`scripts/retrieval.py`, new)

```python
def accelerated_candidates(question, library_path, store, *, backend, k: int = 20) -> tuple[list, str]:
    """Discovery: embed(question) -> store.search(qvec, k) -> top-k page_ids. Build a REDUCED
    shelf-index text = the shelf header + only the entry lines for those pages. Returns
    (page_ids, reduced_shelf_text). The reduced shelf is what `select` reasons over."""
```
- `qvec = backend.embed([question])[0]`.
- **Reduced shelf construction:** read `library/_shelf-index.md`; keep the header (the `<!-- ... -->` comment lines + the `# Shelf Index` title + any intro before the first entry) and only the **entry lines** that reference a candidate page. **Entry→page matching:** an entry line matches a candidate `page_id` if the page_id (or its basename for flat libraries) appears in the line. (Robust-match detail pinned in the plan; if no entries match — e.g. a shelf without per-page bullets — fall back to listing the candidate page_ids as a synthetic shelf so `select` still has something to reason over.)
- Order entry lines by the discovery rank (best-first) so the most-similar candidates lead.

## §3 `pipeline.select` reasons over a reduced shelf

`select(question, shelf_index_path, *, backend, known_pages, max_repairs=1, priming=None, shelf_text=None)`:
- New optional `shelf_text`: when provided, `select` uses it as the shelf content **instead of reading `shelf_index_path`**; when `None`, reads the file (M1c-1 behavior — byte-identical prompt, existing tests + eval unaffected).
- The accelerated path calls `select(question, shelf, backend=backend, known_pages=set(candidate_page_ids), priming=priming, shelf_text=reduced_shelf_text)`. Reasoned selection logic is unchanged; it just sees the reduced shelf, and `known_pages` constrains picks to the shortlist.

## §4 `query --accelerate` wiring (`query_graph.n_select` + CLI)

- CLI: `query "<q>" [--accelerate] [--accelerate-k N]` (default N=20). `--accelerate` and `--accelerate-k` thread into the query graph state.
- `n_select` decision:
  - **accelerate ON and fresh index** (`EmbeddingStore.load(lib)` is not None **and** `store.provenance.corpus_hash == corpus_hash(chunk_pages(lib) page/​hash pairs)`): accelerated path — `accelerated_candidates(...)` → `select(..., shelf_text=reduced, known_pages=candidates)`. (Still applies `filter_pages` layer/min_confidence to the candidate set so `--layer`/`--min-confidence` remain honored.)
  - **else** (accelerate off, or no index, or stale index): the **unchanged** full-shelf path. On accelerate-requested-but-no/stale-index, print a stderr warning (`[query] accelerate: no fresh index (run kb-offline index); falling back to full-shelf select`) and proceed normally — never fail.
- The query path stays read-only.

## §5 recall@k eval gate

- New ratified threshold in `eval/thresholds.py`: `EMBEDDING_RECALL_AT_K = 0.95`.
- New scorer `eval/harness.py`: `recall_at_k(rows) -> float` where `rows = [{expected, shortlist}]` (non-abstention questions only); per-question recall = `|set(expected) ∩ set(shortlist)| / |expected|` (1.0 if a question has no expected targets — vacuous); returns the macro mean.
- Runner path (`eval/runner.py` or a focused helper): build an index over the eval-suite library (FakeBackend deterministic embed in tests; real model live), then per non-abstention question compute the embedding top-N shortlist via `accelerated_candidates` (page_ids) and emit `{expected, shortlist}`.
- Surfaced through the eval report when an index is available; gate at `recall_at_k >= EMBEDDING_RECALL_AT_K`. This proves the discovery prefilter at N=20 rarely drops a page the reasoned `select` would have needed.

## §6 Components & isolation

| File | Responsibility |
|---|---|
| `scripts/embeddings.py` (modify) | `chunk_pages` gains `section_threshold`; oversized → `##`-section rows |
| `scripts/retrieval.py` (new) | `accelerated_candidates` (discover → reduced shelf) |
| `scripts/pipeline.py` (modify) | `select` gains optional `shelf_text` |
| `scripts/graphs/query_graph.py` (modify) | `n_select` accelerate branch (fresh-index check + reduced-shelf path + fallback) |
| `scripts/kb_offline_cli.py` (modify) | `query --accelerate [--accelerate-k]` |
| `scripts/eval/thresholds.py` (modify) | `EMBEDDING_RECALL_AT_K = 0.95` |
| `scripts/eval/harness.py` (modify) | `recall_at_k` scorer |
| `scripts/eval/runner.py` (modify) | recall@k measurement path (build index + per-question shortlist) |
| Tests | `test_kb_offline_embeddings.py` (section chunking), `test_kb_offline_retrieval.py` (accelerated_candidates), `test_kb_offline_query_pipeline.py` (select shelf_text), `test_kb_offline_query_graph.py` + `test_kb_offline_cli.py` (--accelerate + fallback), `test_kb_offline_eval_scorers.py` (recall_at_k), `test_kb_offline_ollama_smoke.py` (live --accelerate) |

## Out of scope (deferred)

- **Federation accelerated discovery** + the privacy-preserving shareable-embeddings "find who to ask" capability → M3c.
- RRF cross-library merge + index-compat rejection → M3c.
- Semantic cross-library conflict lint → M3d.
- Embedding the query with a different model than the index (index-compat is M3c's concern; M3b assumes the same backend embed model as the index, and the fresh-index check already guards corpus drift).

## Decisions log (M3b delta)

1. Reduced-shelf accelerated path (discover → reduced shelf → reasoned select); default path unchanged.
2. N=20 default, `--accelerate-k` override, gate-validated.
3. recall@k gate = absolute mean recall@N of expected_routing_targets ≥ 0.95 (`EMBEDDING_RECALL_AT_K`).
4. section-fallback chunking included: >2000 chars → `##`-section rows (parent page_id), section hit resolves to page.
5. `--accelerate` opt-in; missing/stale (corpus_hash mismatch) index → warn + full-shelf fallback, never fail.
6. `select` gains optional `shelf_text` (None = read file, backward-compatible); `--layer`/`--min-confidence` still honored on the accelerated candidate set.
7. single-library; federation-discovery + shareable-embedding "find who to ask" → M3c.

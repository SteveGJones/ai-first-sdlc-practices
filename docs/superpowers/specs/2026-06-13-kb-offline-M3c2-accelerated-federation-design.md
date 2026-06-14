# kb-offline M3c-2 — accelerated federated query design

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph`. **Builds on:** M2b (`federation_query_graph`, `query_one_library`, `merge_answers`, `render_federated`, `_resolve_libraries`, `build_priming_bundle`), M3a (`EmbeddingStore`, `Provenance`, `corpus_hash`, `chunk_pages`), M3b (`_reduce_shelf`, `select(shelf_text=)`), M3c-1 (`fusion.fuse_compatible`/`compatible`/`rrf_fuse`). **Parent:** §Index compatibility + federation merge. See memory `feedback_embeddings_discovery_vs_reasoning`.

**Goal:** `query --libraries a,b,c --accelerate` — embed the question **once**, RRF-fuse each library's embedding shortlist into ONE cross-library candidate list, hand it to a single reasoned `select` over a cross-library reduced shelf, then read/synthesize/verify across libraries with clean per-library attribution. Embeddings discover; the shelf reasons. Enables **comparative claims across libraries** (one synthesis over multi-library pages) that M2b's per-library-then-merge cannot.

**Decomposition note:** M3c = M3c-1 (RRF+compat, DONE) / **M3c-2 (accelerated federated query, this spec)** / M3c-3 ("find who to ask" discovery).

---

## Decisions (Model B + spec-review hardening)

1. **Model B**: fused cross-library shortlist → ONE reasoned `select` → cross-lib synthesize/verify (the federated simplification; comparative claims).
2. **Linear function, NOT a graph.** The per-library work before reasoning is just fast embedding-search; the expensive reasoning is a single select/synthesize/verify. A linear `accelerated_federation_query(...)` (load+validate all stores once, embed once, search in library order) is correct — and resolves embed-once, completion-order determinism, and the gate/worker TOCTOU at once (single load, no reload).
3. **Qualified-id boundary** `qualify`/`split_qualified`; opaque through the pipeline, canonicalized to attribution after verify.
4. **RRF here = rank-interleaving** (disjoint handle-qualified keys); deterministic library-input-order tie-break, guaranteed by fusing the per-library results **in `library_specs` order** (not search-completion order). Documented + tested.
5. **All-or-nothing, no TOCTOU**: the single load+validate (present + fresh `corpus_hash` + `compatible` with local reference + backend `embedding_model_id()` == reference model) happens once, in the function, and the validated stores are used directly (no reload). Any failure → return a fallback sentinel; the CLI runs the full M2b federation (never drop a library's coverage).
6. **Per-library `--layer`/`--min-confidence` honored**: each library's ranked shortlist is `filter_pages`-filtered (that lib's frontmatter) BEFORE fusion — matching M2b.
7. **Coverage-preserving width**: separate per-library `search_k` (each store.search width) and the fused reduced-shelf cut; a **minimum-one-candidate-per-library** rule so no gate-passing library is silently dropped by truncation.
8. **Priming preserved**: one local priming bundle is passed into the cross-library `select` (M2b primes external reasoning with local vocabulary).
9. **`Span.library`** optional + post-verify `canonicalize_attribution`; attributed publication derives `handle_sets` from each claim's canonicalized `cited_pages`.

---

## §1 Qualified-id helpers (`scripts/fusion.py`)

```python
def qualify(handle: str, page_id: str) -> str:
    """'handle/page_id'. Safe: handles match ^[a-z][a-z0-9-]*$ (no '/'), so the handle is
    recoverable by splitting on the FIRST '/' even when page_id is nested (e.g. 'sub/x.md')."""
    return f"{handle}/{page_id}"

def split_qualified(qid: str) -> tuple:
    handle, _, page_id = qid.partition("/")
    return handle, page_id
```
Opaque page-key through reduced shelf → `select` → read → `synthesize` → `verify_entailment` (all treat ids as opaque strings).

## §2 RRF-is-interleaving + deterministic order

Each fused item `(handle, page_id)` belongs to exactly one library, so **no item appears in two ranked lists** — `fuse_compatible`'s RRF does not reinforce duplicates; it **interleaves by rank** (all libs' rank-1 first, each scoring `1/(k+1)`, then rank-2, …). The tie-break is M3c-1's first-appearance order, so the per-library results MUST be assembled **in `library_specs` order** before fusion — NOT in search-completion order (which a parallel accumulator would give). The linear function (§5) loops libraries in `library_specs` order, so order is deterministic by construction. Documented in `federation_accel.py` + a test asserts the interleave + library-order tie-break.

## §3 All-or-nothing gate (no TOCTOU)

The linear function validates EVERY resolved library **once**, before searching, and uses the loaded stores directly (no later reload — closes the gate/worker TOCTOU):
- local reference index exists (`EmbeddingStore.load(local_lib)` not None → reference provenance);
- each library index loads;
- each is **fresh** (`store.provenance.corpus_hash == corpus_hash(chunk_pages(lib) pairs)`);
- each is **compatible** with the local reference (`fusion.compatible(local_prov, lib_prov)`);
- backend `embedding_model_id()` == local reference `provenance.model`.

All pass → proceed with the in-hand stores. Any fail → return `None` (fallback sentinel) with the reason(s) on stderr; the CLI runs the M2b `federation_query_graph` (queries every library — full coverage). Because the stores are loaded once and reused, no index can change between validation and use within the call. (A library re-indexed mid-call is out of scope — single-process offline tool; the manifest-generation immutability from M3a further bounds it.)

## §4 `Span.library` + post-verify canonicalization

- **Contract (backward-compatible):** add `library: str | None = None` to `Span` in `contracts.py`. Existing `Span(page=, text=)` unaffected.
- Pipeline uses qualified ids; `verify_entailment` grounds each claim against the read page keyed by its qualified id (sound).
- **After verify**, `canonicalize_attribution(answer)` rewrites each claim: `cited_pages` → `PageRef(library=handle, page=page_id)` and `evidence_spans` → `Span(library=handle, page=page_id, text=…)` via `split_qualified`.

## §5 `scripts/federation_accel.py` (new) — the linear accelerated path

```python
def accelerated_federation_query(local_lib, library_specs, question, *, backend,
                                 search_k=20, layer=None, min_confidence=None,
                                 audit=True):
    """library_specs = [(handle, path), ...] (first = local). Returns a result dict
    {rendered_text, rejected_claims, _answer, queried, fused, ...} on success, or None if the
    all-or-nothing gate fails (caller falls back to M2b). Read-only; no graph."""
```
Steps (sequential, library order):
1. **Gate (§3)** — load every library's store once; validate all; on any failure print reason + `return None`.
2. **Embed once** — `qvec = backend.embed([question])[0]` (one call; reused for every library).
3. **Per-library search + filter** — for each `(handle, path)` in `library_specs` order: `hits = store.search(qvec, k=search_k)`; `ranked = filter_pages(path, [pid for pid,_ in hits], layer=layer, min_confidence=min_confidence)` (honors --layer/--min-confidence per library). Audit one `cross_library_query` event per NON-local library (reuse M2b's pattern).
4. **Fuse (deterministic + coverage)** — `fused, rejected = fuse_compatible(local_prov, [(handle, prov, ranked) ...in library_specs order...])` (rejected is empty — gate already ensured compatibility). Build the reduced-shelf id list = fused order, then **enforce minimum-one-per-library**: if any gate-passing library has no item in the cut, append its top-ranked fused item (so truncation never drops a library). Final cut width = `max(search_k, len(library_specs))` so every library's rank-1 survives.
5. **Cross-library reduced shelf** — entries are `qualify(handle, page_id)` for each id in the fused-cut order; each entry's descriptor is that page's line from its own library's shelf (reuse M3b `_reduce_shelf` per library to fetch the descriptor), header once. Known set = the qualified ids.
6. **Priming** — `priming = build_priming_bundle(question, <local project dir = local_lib.parent>)` (M2b semantics).
7. **One reasoned select** — `select(question, None, backend=backend, known_pages=set(qualified_ids), priming=priming, shelf_text=reduced_shelf)`.
8. **Read across libraries** — for each chosen qualified id: `handle, page_id = split_qualified(qid)`; read `<path_for_handle>/<page_id>`; pages keyed by the qualified id.
9. **Synthesize + verify** — `synthesize(question, pages, backend)` → `verify_entailment(answer, {qid: content}, backend)` → `canonicalize_attribution(...)`.
10. **Attributed publish** — `handle_sets` per claim = ordered-unique library handles from its canonicalized `cited_pages`; `render_federated(canonical_answer, handle_sets)` (reuse M2b's renderer + publication policy).

## §6 CLI routing + width

- `query "<q>" --libraries a,b,c --accelerate [--accelerate-k 20]`:
  - `--libraries` + `--accelerate` → `accelerated_federation_query(...)`; if it returns `None` (gate failed) → run M2b `federation_query_graph` (warn). `search_k = accelerate_k`.
  - `--libraries`, no `--accelerate` → M2b (unchanged).
  - `--accelerate` only → M3b single-lib (unchanged).
  - neither → M1c-1 single-lib (unchanged).
- `library_specs_override` test seam (as M2b/M3b) keeps tests hermetic.

## §7 Components & isolation

| File | Responsibility |
|---|---|
| `scripts/fusion.py` (modify) | `qualify`, `split_qualified` |
| `scripts/contracts.py` (modify) | `Span.library: str|None = None` |
| `scripts/federation.py` (modify) | `canonicalize_attribution(answer)` |
| `scripts/federation_accel.py` (new) | `accelerated_federation_query` (linear: gate→embed-once→search+filter→fuse+coverage→reduced shelf→prime→select→read→synth/verify→attributed publish) |
| `scripts/kb_offline_cli.py` (modify) | route `--libraries --accelerate` → accel fn, fallback to M2b on `None` |
| Tests | `test_kb_offline_fusion.py` (qualify/split + interleave-in-order), `test_kb_offline_federation.py` (canonicalize), `test_kb_offline_federation_accel.py` (e2e + gate→M2b fallback + min-one-per-library + comparative claim + layer filter), `test_kb_offline_cli.py` (routing), existing contracts test (`Span.library` default), `test_kb_offline_ollama_smoke.py` (live) |

## Out of scope (deferred)

- "Find who to ask" privacy-preserving discovery → M3c-3.
- Semantic cross-library conflict lint → M3d.
- Mid-call re-index handling (single-process offline tool; generation immutability bounds it).

## Decisions log (M3c-2 delta)

1. Model B; linear function (no graph) — resolves embed-once + completion-order + TOCTOU.
2. `qualify`/`split_qualified`; first-`/` split.
3. RRF = rank-interleave; deterministic by fusing in `library_specs` order (documented + tested).
4. Single load+validate gate, stores reused (no TOCTOU); any failure → `None` → M2b fallback + stderr reason.
5. Per-library `--layer`/`--min-confidence` applied to each shortlist before fusion.
6. `search_k` (per-lib) vs fused cut `max(search_k, n_libs)` + minimum-one-per-library coverage rule.
7. One local priming bundle into the cross-library select.
8. `Span.library` optional + post-verify `canonicalize_attribution`; `handle_sets` from canonicalized `cited_pages`.
9. Embed once before searching; reused across libraries.

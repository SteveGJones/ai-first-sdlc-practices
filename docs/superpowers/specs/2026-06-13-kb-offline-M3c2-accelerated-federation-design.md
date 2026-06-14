# kb-offline M3c-2 — accelerated federated query design

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph`. **Builds on:** M2b (`federation_query_graph`, `query_one_library`, `merge_answers`, `render_federated`, `_resolve_libraries`), M3a (`EmbeddingStore`, `Provenance`, `corpus_hash`, `chunk_pages`), M3b (`accelerated_candidates`/`_reduce_shelf`, `select(shelf_text=)`), M3c-1 (`fusion.fuse_compatible`/`compatible`/`rrf_fuse`). **Parent:** §Index compatibility + federation merge ("rank fusion across libraries… the fused shortlist with source attribution is handed to the librarian for reasoned selection"). See memory `feedback_embeddings_discovery_vs_reasoning`.

**Goal:** `query --libraries a,b,c --accelerate` — embed once, RRF-fuse each library's embedding shortlist into ONE cross-library candidate list, hand it to a single reasoned `select` over a cross-library reduced shelf, then read/synthesize/verify across libraries with clean per-library attribution. Embeddings discover; the shelf reasons. Enables **comparative claims across libraries** (one synthesis over multi-library pages) that M2b's per-library-then-merge cannot.

**Decomposition note:** M3c = M3c-1 (RRF+compat primitive, DONE) / **M3c-2 (accelerated federated query, this spec)** / M3c-3 ("find who to ask" discovery). M3c-2 is the reasoned-query consumer of M3c-1.

---

## Decisions (from brainstorm — Model B + 6 contracts)

1. **Model B**: fused cross-library shortlist → ONE reasoned `select` (matches the spec; the federated simplification; one synthesis enables comparative claims).
2. **Qualified-id formal boundary**: `qualify(handle, page_id)`/`split_qualified(qid)`; ids opaque through the pipeline, canonicalized to attribution after verify.
3. **RRF-is-interleaving here**: handle-qualified keys never collide across lists, so fusion interleaves by rank with library-input-order tie-break — documented + tested (not score reinforcement).
4. **All-or-nothing gate + M2b fallback**: accelerate only if EVERY resolved library has a fresh, compatible index + matching backend embed model; any failure → fall back to full M2b federation (never silently drop a library's coverage).
5. **`Span.library`** optional field + post-verify canonicalization (disambiguate same-named pages across libraries).
6. **Dedicated accelerated-federation graph**; CLI routes `--libraries --accelerate` to it.

---

## §1 Qualified-id helpers (`scripts/fusion.py`)

```python
def qualify(handle: str, page_id: str) -> str:
    """Library-qualified page id 'handle/page_id'. Safe: handles match ^[a-z][a-z0-9-]*$
    (no '/'), so the handle is always recoverable by splitting on the FIRST '/' even when
    page_id is a nested POSIX path (e.g. 'sub/x.md')."""
    return f"{handle}/{page_id}"

def split_qualified(qid: str) -> tuple:
    """('handle', 'page_id') — splits on the first '/'."""
    handle, _, page_id = qid.partition("/")
    return handle, page_id
```
These are the opaque page-key used through the reduced shelf, `select`, read, `synthesize`, and `verify_entailment` (all of which treat page ids as opaque strings).

## §2 RRF-is-interleaving (behavior to document + test)

Because each fused item is `(handle, page_id)` (M3c-1) and a page belongs to exactly one library, **no item appears in more than one library's ranked list**. So `fuse_compatible`'s RRF here does NOT reinforce duplicates; it **interleaves by rank**: all libraries' rank-1 items (each scoring `1/(k_const+1)`) come first, ordered by library input order (the deterministic first-appearance tie-break from M3c-1), then all rank-2 items, etc. This is the intended round-robin-by-rank cross-library ordering. The accelerated-federation module documents this and a test asserts the interleave + library-order tie-break, so no consumer expects cross-list score reinforcement that cannot occur with disjoint keys.

## §3 All-or-nothing gate + M2b fallback

Before running accelerated federation, check **every** resolved library `(handle, path)`:
- a local reference index exists (`EmbeddingStore.load(local_lib)` not None) — it provides the reference provenance;
- each library has an index (`EmbeddingStore.load(lib)` not None);
- each library's index is **fresh** (`store.provenance.corpus_hash == corpus_hash(chunk_pages(lib) pairs)`);
- each library's index is **compatible** with the local reference (`fusion.compatible(local_prov, lib_prov)`);
- the active backend's `embedding_model_id()` == the local reference `provenance.model`.

If **all** pass → accelerated-federation graph. If **any** fails → print the reason(s) to stderr (`[query] accelerate-federation: <handle> <reason>; falling back to full federation`) and run the **M2b non-accelerated `federation_query_graph`** (queries every library — full coverage preserved). Never silently exclude a library from a federated query.

## §4 `Span.library` + post-verify canonicalization

- **Contract change (backward-compatible):** add `library: str | None = None` to `Span` in `contracts.py`. Existing `Span(page=, text=)` construction unaffected.
- During the accelerated-federation pipeline, page ids are qualified strings (`handle/page_id`); `synthesize`'s claims cite them; `verify_entailment` grounds against the read pages keyed by qualified id (sound — each claim grounded against its exact `handle/page_id` content).
- **After `verify_entailment`**, a `canonicalize_attribution(answer)` step rewrites each claim: every `cited_pages` `PageRef` → `PageRef(library=handle, page=page_id)` and every `evidence_spans` `Span` → `Span(library=handle, page=page_id, text=…)`, via `split_qualified`. So same-named pages across libraries are unambiguous in both citations and evidence.

## §5 Dedicated accelerated-federation graph (`scripts/graphs/federation_accel_graph.py`)

`build_federation_accel_graph(backend, *, checkpoint_path=None)` — read-only, mirrors the offline-guard import discipline:
- **`n_resolve`** — pass through `library_specs` `[[handle, path], ...]` (resolved by CLI), `question`, `accelerate_k`, `local_lib`.
- **`Send` fan-out `search_one`** — one worker per library: `EmbeddingStore.load(path)`; `qvec = backend.embed([question])[0]`; `store.search(qvec, accelerate_k)` → `{handle, provenance(model/dims/normalization), ranked_page_ids}` accumulated via `Annotated[list, add]`. (Gate already guaranteed indexes are present/fresh/compatible before this graph runs, so search never falls back here.)
- **`n_fuse`** — `fuse_compatible(local_reference_prov, [(handle, prov, ranked_page_ids)], k_const=60)` → fused `[((handle, page_id), score)]`; take top-`accelerate_k`; build ONE cross-library **reduced shelf** whose entries are the qualified ids (`handle/page_id`) drawn rank-ordered from each library's shelf (reuse M3b `_reduce_shelf` per library, then concatenate header-once + the fused-ranked entries; qualified-id entries). Audit one `cross_library_query` event per non-local library (reuse M2b's audit pattern).
- **`n_select`** — `select(question, shelf_path=None, backend=backend, known_pages=set(qualified_ids), shelf_text=fused_reduced_shelf)` → chosen qualified ids.
- **`n_read`** — for each chosen `qid`: `handle, page_id = split_qualified(qid)`; read `<lib_path_for_handle>/<page_id>`; pages keyed by `qid`.
- **`n_synth_verify`** — `synthesize(question, pages, backend)` → `verify_entailment(answer, pages_by_qid, backend)` → `canonicalize_attribution` → `render_federated`-style attributed publish (`rendered_text`, `rejected_claims`, `_answer` with `library`-carrying PageRefs/Spans, `queried`, plus the fused/reject stats).
- Read-only — no lock/journal. Verification grounds each claim against the exact qualified page read.

## §6 CLI routing + width

- `query "<q>" --libraries a,b,c --accelerate [--accelerate-k 20]`:
  - `--libraries` present + `--accelerate` → run the **gate** (§3); pass → accelerated-federation graph; fail → M2b `federation_query_graph` (warn).
  - `--libraries` present, no `--accelerate` → M2b (unchanged).
  - `--accelerate` only (no `--libraries`) → M3b single-library accelerate (unchanged).
  - neither → M1c-1 single-library (unchanged).
- Fused shortlist feeds the reduced shelf at top-`accelerate_k` (default 20).
- A `library_specs_override` + a reference-provenance test seam (as M2b/M3b) keep tests hermetic (no `~/.sdlc/global-libraries.json`).

## §7 Components & isolation

| File | Responsibility |
|---|---|
| `scripts/fusion.py` (modify) | `qualify`, `split_qualified` |
| `scripts/contracts.py` (modify) | `Span.library: str|None = None` |
| `scripts/federation.py` (modify) | `canonicalize_attribution(answer)` post-verify; accel-federation gate helper |
| `scripts/graphs/federation_accel_graph.py` (new) | `build_federation_accel_graph` (resolve→search→fuse→select→read→synth/verify→publish) |
| `scripts/kb_offline_cli.py` (modify) | route `--libraries --accelerate` (gate → accel graph or M2b fallback) |
| Tests | `test_kb_offline_fusion.py` (qualify/split + interleave), `test_kb_offline_federation.py` (canonicalize), `test_kb_offline_federation_accel.py` (graph e2e + gate fallback + comparative claim), `test_kb_offline_cli.py` (routing), `test_kb_offline_contracts`/existing (Span.library default), `test_kb_offline_ollama_smoke.py` (live) |

## Out of scope (deferred)

- "Find who to ask" privacy-preserving discovery (shareable fingerprints, coverage query) → M3c-3.
- Semantic cross-library conflict lint → M3d.
- Per-library section-fallback differences in fusion (chunking is M3b's concern; the gate ensures consistent indexes).

## Decisions log (M3c-2 delta)

1. Model B: fused shortlist → one reasoned select → cross-lib synthesize/verify (comparative claims).
2. `qualify`/`split_qualified` formal boundary; first-`/` split (handles are `/`-free).
3. RRF is rank-interleaving with library-order tie-break for disjoint handle-qualified keys (documented + tested).
4. All-or-nothing gate (present+fresh+compatible+backend-model-match for ALL libs); any failure → full M2b fallback + stderr reason; never drop coverage.
5. `Span.library` optional + post-verify `canonicalize_attribution` (PageRef.library + Span.library from split_qualified).
6. Dedicated `federation_accel_graph` (parallel search-only fan-out → single reasoning pipeline); read-only; per-non-local audit event.
7. CLI routes the four query modes (single / single-accel / federated / federated-accel); fused width = `accelerate_k` default 20.

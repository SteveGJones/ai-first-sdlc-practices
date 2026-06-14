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
- **backend is embedding-capable** — `getattr(backend, "embedding_model_id", None)` is not None (AnthropicBackend, the query CLI default, intentionally OMITS it → this is a GATE FAILURE returning `None`, NOT an AttributeError; the CLI then runs M2b, which is LLM-based and needs no embeddings);
- local reference index exists (`EmbeddingStore.load(local_lib)` not None → reference provenance);
- each library index loads;
- each is **fresh** (`store.provenance.corpus_hash == corpus_hash(chunk_pages(lib) pairs)`);
- each is **compatible** with the local reference (`fusion.compatible(local_prov, lib_prov)`);
- backend `embedding_model_id()` == local reference `provenance.model`.

All pass → proceed with the in-hand stores. Any fail → return `None` (fallback sentinel) with the reason(s) on stderr; the CLI runs the M2b `federation_query_graph` (queries every library — full coverage). Because the stores are loaded once and reused, no index can change between validation and use within the call. (A library re-indexed mid-call is out of scope — single-process offline tool; the manifest-generation immutability from M3a further bounds it.)

**Query-vector validity** (after embedding, before any `store.search`): the single `backend.embed([question])` must return exactly one vector, all-finite, of length == the reference `provenance.dims`. Otherwise → `return None` (M2b fallback) — so a malformed embedding fails cleanly up front, not mid-query in a matrix multiply.

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
2. **Embed once + validate** — `qvec = backend.embed([question])[0]` (one call; reused for every library), after the query-vector validity check (§3: exactly one finite vector, dim == reference dims; else `return None`).
3. **Per-library search + filter, with a coverage guard** — for each `(handle, path)` in `library_specs` order: `hits = store.search(qvec, k=search_k)`; `ranked = filter_pages(path, [pid for pid,_ in hits], layer=layer, min_confidence=min_confidence)`. **Coverage guard:** if `ranked` is empty BUT the library has eligible pages (`filter_pages(path, <all the lib's content page_ids>, layer, min_confidence)` is non-empty), the embedding cut (`search_k`) missed this library's eligible pages — accelerated federation cannot preserve its coverage, so **`return None` (M2b fallback)**. (If a library has NO eligible pages under the filter, it legitimately contributes nothing — not a coverage loss.)
3a. **Audit only AFTER the commit point** — do NOT write audit events during step 3. A later library can trip the coverage guard and `return None`, after which the M2b fallback audits the same external libraries; auditing in-loop would double-log them. Write one `cross_library_query` event per NON-local library only once ALL fallback-producing checks (gate §3, qvec validity, per-library coverage) have passed — i.e. immediately before fusion, when accelerated federation is committed.
4. **Fuse (deterministic, in library order)** — `fused, _ = fuse_compatible(local_prov, [(handle, prov, ranked) ...in library_specs order...])` (rejected is empty — gate ensured compatibility). Take the fused top-`max(search_k, len(library_specs))` so every library's rank-1 (interleaved first, §2) survives the cut; the step-3 coverage guard already guarantees every eligible library has ≥1 fused item, so this width preserves the per-library coverage promise.
5. **Cross-library reduced shelf** — entries built from the REAL shelf entry blocks (not bullets): for each fused qualified id, `handle, page_id = split_qualified(qid)`; `block = build_shelf_index.extract_entry_block(<handle's shelf text>, page_id)` (the `## N. page_id` block via `_ENTRY_PATH_RE`); **rewrite the block's `## N. page_id` header to `## N. handle/page_id`** (the qualified id, so `select`'s reasoning + return are over qualified ids); if no block is found, synthesize `## N. handle/page_id`. Concatenate a one-line header + the rewritten blocks in fused-cut order. Known set = the qualified ids.
6. **Priming** — `priming = build_priming_bundle(question, <local project dir = local_lib.parent>)` (M2b semantics).
7. **One reasoned select** — `select(question, None, backend=backend, known_pages=set(qualified_ids), priming=priming, shelf_text=reduced_shelf)`.
8. **Read across libraries** — for each chosen qualified id: `handle, page_id = split_qualified(qid)`; read `<path_for_handle>/<page_id>`; pages keyed by the qualified id.
9. **Synthesize + verify** — `synthesize(question, pages, backend)` → `verify_entailment(answer, {qid: content}, backend)` → `canonicalize_attribution(...)`.
10. **Attributed publish** — `handle_sets` per claim = ordered-unique library handles from its canonicalized `cited_pages`; `render_federated(canonical_answer, handle_sets)` (reuse M2b's renderer + publication policy).

## §5.1 `extract_entry_block` contract + M3b `_reduce_shelf` adoption

`extract_entry_block(shelf_text, file_path) -> str | None`:
- Scan `shelf_text` with `_ENTRY_PATH_RE` (`^## \d+\.\s+(.+)$`); a header matches only when its captured path **equals `file_path` exactly** (string equality — `a.md` must NOT match `data.md`; nested paths like `sub/x.md` compared whole).
- The returned block runs **from the matched header line up to (but not including) the next entry header that matches `_ENTRY_PATH_RE`, or EOF** — so the block carries that entry's Hash/Layer/Confidence/Terms/Facts.
- Returns `None` if no exact match.

**M3b `_reduce_shelf` adoption (in scope):** `retrieval._reduce_shelf` is updated to, per page, try `extract_entry_block` (real `## N.` generated format) first, then the existing `- <path> —` bullet line (legacy/fixture format, preserved so existing tests stay green), and only synthesize `- <page_id>` when neither is found. This fixes M3b's single-library accelerate path, which on real generated shelves currently strips all Terms/Facts/Layer/Confidence before the "reasoned" select — undermining its own contract. Two boundary contracts the adoption MUST get right:

- **Header boundary (P1):** `_reduce_shelf`'s current header detection ends at the first `- ` bullet — but in a generated shelf the first `- ` is a *fact bullet inside entry 1*, so that logic leaks part of the first entry into every reduced shelf. Redefine: the header ends **before the first real `_ENTRY_PATH_RE` (`## N. <path>`) header**; fall back to "before the first `- ` bullet" ONLY when the shelf has no real entry headers (a pure-legacy bullet shelf). A test asserts an UNSELECTED first generated entry is **entirely absent** from the reduced shelf.
- **Bullet-fallback matching (P2):** the legacy bullet match must require **exact `page_id`** equality, and may fall back to **basename** match **only when the candidate `page_id` is flat** (no `/`). Otherwise candidate `sub/a.md` could wrongly match a root `a.md` bullet. (`extract_entry_block` already matches the real header by exact id, §5.1 above.)

A test using an actual `build_shelf_index`-generated shelf is added. The M3c-2 cross-library builder uses `extract_entry_block` directly and rewrites the header to the qualified id (§5 step 5); M3b's `_reduce_shelf` uses the block unqualified. One shared parser, two consumers.

## §6 CLI routing + width

- `query "<q>" --libraries a,b,c --accelerate [--accelerate-k 20]`:
  - `--libraries` + `--accelerate` → `accelerated_federation_query(...)`; if it returns `None` (gate failed) → run M2b `federation_query_graph` (warn). `search_k = accelerate_k`.
  - `--libraries`, no `--accelerate` → M2b (unchanged).
  - `--accelerate` only → M3b single-lib (unchanged).
  - neither → M1c-1 single-lib (unchanged).
- **`--accelerate-k` validated `>= 1`** (argparse custom type rejecting `< 1`, on the shared flag used by M3b + M3c-2); `accelerated_federation_query` also guards `search_k >= 1` defensively — prevents an invalid `argpartition`/width.
- `library_specs_override` test seam (as M2b/M3b) keeps tests hermetic.

## §7 Components & isolation

| File | Responsibility |
|---|---|
| `scripts/fusion.py` (modify) | `qualify`, `split_qualified` |
| `scripts/contracts.py` (modify) | `Span.library: str|None = None` |
| `scripts/build_shelf_index.py` (modify) | `extract_entry_block(shelf_text, file_path) -> str|None` (exact-id `## N. <path>` block; see §5.1) |
| `scripts/retrieval.py` (modify, M3b touch-up — in scope) | `_reduce_shelf` uses `extract_entry_block` (real `## N.` format) with the existing `- ` bullet format preserved as a fallback; synthetic entry only when neither matches |
| `scripts/federation.py` (modify) | `canonicalize_attribution(answer)` |
| `scripts/federation_accel.py` (new) | `accelerated_federation_query` (linear: gate→embed-once→search+filter→fuse+coverage→reduced shelf→prime→select→read→synth/verify→attributed publish) |
| `scripts/kb_offline_cli.py` (modify) | route `--libraries --accelerate` → accel fn, fallback to M2b on `None` |
| Tests | `test_kb_offline_fusion.py` (qualify/split + interleave-in-order), `test_kb_offline_embeddings.py` or a shelf test (`extract_entry_block` exact-id match incl. nested paths + `a.md`/`data.md` prefix collision; block boundary to next header/EOF), `test_kb_offline_retrieval.py` (`_reduce_shelf` over a REAL generated shelf keeps Layer/Facts; bullet-format still works; synthetic fallback), `test_kb_offline_federation.py` (canonicalize), `test_kb_offline_federation_accel.py` (e2e + gate→M2b fallback incl. anthropic-backend + filtered-empty-but-eligible + min-one-per-library + comparative claim + layer filter + qvec-invalid fallback), `test_kb_offline_cli.py` (routing + `--accelerate-k < 1` rejected), existing contracts test (`Span.library` default), `test_kb_offline_ollama_smoke.py` (live) |

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

### Spec-review round-2 resolutions

- **[P1] reduced shelf vs real shelf format** → `build_shelf_index.extract_entry_block` parses the REAL `## N. <path>` blocks (M3b's `_reduce_shelf` only matched hand-written `- ` bullets); rewrite each block's header to the qualified id, emit in fused order, synthesize if absent. **M3b's own `_reduce_shelf` is ALSO fixed in this slice** (round-3) to adopt the shared parser — see §5.1.
- **[P1] min-one-per-library impossible after filtering empties a shortlist** → step-3 coverage guard: a library whose filtered shortlist is empty BUT which has eligible pages (filter over ALL its pages non-empty) → `return None` → M2b fallback (embedding cut missed eligible pages). A library with zero eligible pages contributes nothing legitimately.
- **[P1] embedding-less backend** → gate checks `getattr(backend, "embedding_model_id", None)`; missing → gate failure → `None` → M2b fallback (not AttributeError). `--backend anthropic --accelerate` cleanly falls back to LLM-based M2b.
- **[P2] query-vector validity** → after the one embed, require exactly one finite vector of dim == reference dims; else `None` → M2b fallback (no mid-query matrix-mult failure).

### Spec-review round-3 resolutions

- **[P1] M3b real-shelf fix in scope** → `retrieval._reduce_shelf` adopts the shared `extract_entry_block` (real `## N.` format) with bullet-format fallback + synthetic only when neither matches; a real-generated-shelf test added. One parser, two consumers — no two-implementations divergence (§5.1).
- **[P2] `extract_entry_block` exact contract** → exact-id header match (no `a.md`/`data.md` substring collision; nested paths whole), block = header → next entry header or EOF; nested + prefix-collision tests (§5.1).
- **[P2] `search_k` validation** → `--accelerate-k` argparse-validated `>= 1` + a defensive `search_k >= 1` guard in `accelerated_federation_query` (§6).

### Spec-review round-4 resolutions

- **[P1] reduced-shelf header boundary** → `_reduce_shelf` header ends before the first real `## N.` entry header (fall back to first `- ` bullet only when there are NO real entry headers), so no part of the first generated entry leaks into the header. Test: an unselected first generated entry is entirely absent from the reduced shelf (§5.1).
- **[P2] audit double-logging on late fallback** → defer all accelerated-path `cross_library_query` audit writes until AFTER every fallback-producing check passes (gate + qvec + per-library coverage), i.e. at the commit point before fusion (§5 step 3a) — so a late `return None` doesn't audit libraries that the M2b fallback re-audits.
- **[P2] legacy bullet basename over-match** → bullet fallback requires exact `page_id`; basename match allowed only when the candidate is flat (no `/`), so `sub/a.md` can't match a root `a.md` bullet (§5.1).

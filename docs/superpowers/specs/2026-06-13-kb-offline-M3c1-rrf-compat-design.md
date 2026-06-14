# kb-offline M3c-1 — RRF fusion + index-compatibility primitive design

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph`. **Builds on:** M3a `Provenance` (model/dims/normalization/corpus_hash). **Consumed by:** M3c-2 (accelerated federated query) and M3c-3 ("find who to ask" discovery). **Parent:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (§Index compatibility + federation merge — "rank fusion (RRF) across libraries rather than raw-score merging"). See memory `feedback_embeddings_discovery_vs_reasoning`.

**Goal:** The pure, foundational federation-fusion primitive — Reciprocal Rank Fusion across multiple libraries' embedding shortlists (rank-based, so non-comparable cross-index raw scores don't matter) plus an index-compatibility predicate, with a composing helper that fuses only compatible indexes and reports the rejected ones. Model-free, no graph, no I/O.

**Decomposition note:** M3c = **M3c-1 (RRF + compat primitive, this spec)** / M3c-2 (accelerated federated query) / M3c-3 ("find who to ask" discovery). M3c-1 is pure primitives; the reject/warn UX + query wiring are M3c-2.

---

## Decisions (from brainstorm)

1. **Handle-qualified item keys** `(handle, page_id)` — cross-library same-named pages stay distinct and carry source attribution.
2. **Compat reference = the local library's index** — external indexes federate only if built with the same embedding model as local (vectors must be comparable to mine).
3. **`k_const = 60`** (the standard Cormack et al. RRF constant), parameterized.
4. **Compat fields = `model` + `dims` + `normalization`** (`corpus_hash` excluded — different corpora federate fine; it's content, not comparability).

---

## §1 `scripts/fusion.py` (new) — RRF

```python
def rrf_fuse(ranked_lists, *, k_const: int = 60) -> list:
    """Reciprocal Rank Fusion. Each input in `ranked_lists` is a best-first list of item keys.
    Fused score(item) = sum over the lists it appears in of 1/(k_const + rank), rank 1-based.
    Returns [(item, fused_score)] sorted by fused_score DESC, ties broken by first appearance
    across the inputs. Uses RANKS not raw scores, so non-comparable cross-index scores are fine."""
```
- Item keys are opaque to `rrf_fuse` (it hashes/compares them); federation passes `(handle, page_id)` tuples.
- Rank is 1-based (first item in a list → rank 1 → `1/(k_const+1)`). An item absent from a list contributes nothing from that list.
- Tie-break: stable on first-appearance order (iterate lists in order, items in order; preserve first-seen index as the secondary sort key) so the result is deterministic.
- Empty `ranked_lists` or all-empty lists → `[]`.

## §2 index-compatibility (`scripts/fusion.py`)

```python
def compatible(prov_a, prov_b) -> bool:
    """True iff two index provenances are vector-comparable: same model, dims, normalization.
    corpus_hash is deliberately NOT compared (different corpora federate fine)."""
    return (prov_a.model == prov_b.model and prov_a.dims == prov_b.dims
            and prov_a.normalization == prov_b.normalization)


def fuse_compatible(reference_prov, entries, *, k_const: int = 60) -> tuple:
    """entries = [(handle, provenance, ranked_page_ids)]. Keep entries whose provenance is
    compatible(reference_prov, ·); RRF-fuse the survivors over handle-qualified (handle, page_id)
    keys; return (fused, rejected_handles) where fused = [((handle, page_id), score)] best-first
    and rejected_handles = [handle] of the incompatible (skipped) entries, in input order.
    Reference = the local library's index provenance (M3c-2 supplies it)."""
```
- `fuse_compatible` builds, for each compatible entry, the ranked list `[(handle, pid) for pid in ranked_page_ids]`, then calls `rrf_fuse` over those lists.
- The reject/warn UX (printing which handles were skipped, falling back) is **M3c-2's** concern; `fuse_compatible` only returns the rejected handles.

## §3 Testing + scope

Pure unit tests (`tests/test_kb_offline_fusion.py`), no model/graph/I/O:
- **`rrf_fuse`:** an item ranked high in TWO lists outranks one ranked high in only one; `k_const` effect (smaller k → sharper rank weighting); 1-based rank math on a hand-computed example; tie-break by first appearance is deterministic; empty/all-empty → `[]`.
- **`compatible`:** identical provenance → True; differing `model`/`dims`/`normalization` each → False; differing `corpus_hash` only → **True** (corpora differ, still comparable).
- **`fuse_compatible`:** incompatible entries excluded from the fusion AND listed in `rejected_handles`; survivors fused with handle-qualified keys; a cross-library same-named page (`a.md` in two libs) yields two distinct fused items.

Scope: primitives only. M3c-2 wires RRF over real per-library `accelerated_candidates` shortlists into the federation query (reject/warn UX, reasoned select over fused candidates with attribution); M3c-3 uses the same primitives for the privacy-preserving "find who to ask" discovery.

## Components & isolation

| File | Responsibility |
|---|---|
| `scripts/fusion.py` (new) | `rrf_fuse`, `compatible`, `fuse_compatible` (pure) |
| Tests | `tests/test_kb_offline_fusion.py` |

## Out of scope (deferred)

- Wiring RRF into the federation query path + reject/warn UX → M3c-2.
- Reasoned select over fused cross-library candidates + attribution rendering → M3c-2.
- "Find who to ask" privacy-preserving discovery (shareable fingerprints, coverage query) → M3c-3.

## Decisions log (M3c-1 delta)

1. `rrf_fuse(ranked_lists, *, k_const=60)` — 1-based rank, `1/(k+rank)`, sort desc, first-appearance tie-break.
2. Item keys handle-qualified `(handle, page_id)` (federation supplies them).
3. `compatible` = model + dims + normalization (corpus_hash excluded).
4. `fuse_compatible(reference_prov, entries)` filters to compatible + fuses + returns `rejected_handles`; reference = local index provenance; reject/warn UX deferred to M3c-2.
5. Pure module, model-free; M3c-2/M3c-3 consume it.

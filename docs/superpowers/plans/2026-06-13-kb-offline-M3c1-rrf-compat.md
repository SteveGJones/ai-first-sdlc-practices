# kb-offline M3c-1 — RRF fusion + index-compat primitive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The pure federation-fusion primitive — Reciprocal Rank Fusion across libraries' embedding shortlists + an index-compatibility predicate + a composing helper that fuses only compatible indexes and reports the rejected ones.

**Architecture:** A new `scripts/fusion.py` with three pure functions: `rrf_fuse` (rank-based merge, robust to non-comparable cross-index scores), `compatible` (model/dims/normalization match), `fuse_compatible` (filter-to-compatible + fuse + report rejects). Model-free, no graph, no I/O. Consumed by M3c-2 (accelerated federated query) and M3c-3 ("find who to ask").

**Tech Stack:** Python 3.9+, the project `.venv`, pytest. No new deps. Spec: `docs/superpowers/specs/2026-06-13-kb-offline-M3c1-rrf-compat-design.md`.

---

## Environment & scope

- **`.venv` for everything**; flake8@127; commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **In scope:** `rrf_fuse`, `compatible`, `fuse_compatible` (pure).
- **Out of scope:** wiring into the federation query + reject/warn UX (M3c-2); "find who to ask" discovery (M3c-3).

## Reused APIs

- `embeddings.Provenance(model: str, dims: int, normalization: str, corpus_hash: str, schema_version: int=1)` — `compatible`/`fuse_compatible` read `.model`/`.dims`/`.normalization` (duck-typed; `fusion.py` need not import `Provenance`; tests construct it).

## File structure (M3c-1)

| File | Responsibility |
|---|---|
| `scripts/fusion.py` (new) | `rrf_fuse`, `compatible`, `fuse_compatible` (pure) |
| Tests | `tests/test_kb_offline_fusion.py` |

---

## Task 1: `rrf_fuse` + `compatible`

**Files:** Create `scripts/fusion.py`; Test `tests/test_kb_offline_fusion.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_fusion.py`:
```python
"""RRF fusion + index-compat primitive tests (pure). kb-offline M3c-1 (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.embeddings import Provenance
from sdlc_knowledge_base_scripts.fusion import compatible, rrf_fuse


def test_rrf_item_in_two_lists_outranks_item_in_one():
    # A is rank-1 in both lists; B/C are rank-2 in one each -> A wins
    fused = rrf_fuse([["A", "B"], ["A", "C"]])
    items = [it for it, _ in fused]
    assert items[0] == "A"
    assert set(items) == {"A", "B", "C"}


def test_rrf_one_based_rank_math():
    # single list [X] -> score 1/(60+1)
    fused = rrf_fuse([["X"]])
    assert fused == [("X", 1.0 / 61)]


def test_rrf_k_const_effect():
    # smaller k_const sharpens the rank-1 vs rank-2 gap
    [(_, a1), (_, a2)] = rrf_fuse([["A", "B"]], k_const=1)      # 1/2 vs 1/3
    [(_, b1), (_, b2)] = rrf_fuse([["A", "B"]], k_const=1000)   # ~1/1001 vs ~1/1002
    assert (a1 - a2) > (b1 - b2)


def test_rrf_tiebreak_by_first_appearance():
    # P and Q each appear once at rank 1 in separate lists -> equal score -> first-seen first
    fused = rrf_fuse([["P"], ["Q"]])
    assert [it for it, _ in fused] == ["P", "Q"]
    assert fused[0][1] == fused[1][1]


def test_rrf_empty():
    assert rrf_fuse([]) == []
    assert rrf_fuse([[], []]) == []


def test_compatible_matrix():
    base = Provenance(model="nomic", dims=768, normalization="l2", corpus_hash="c1")
    assert compatible(base, Provenance(model="nomic", dims=768, normalization="l2", corpus_hash="c2")) is True
    assert compatible(base, Provenance(model="other", dims=768, normalization="l2", corpus_hash="c1")) is False
    assert compatible(base, Provenance(model="nomic", dims=512, normalization="l2", corpus_hash="c1")) is False
    assert compatible(base, Provenance(model="nomic", dims=768, normalization="none", corpus_hash="c1")) is False
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fusion.py -k "rrf or compatible_matrix" -v`
Expected: FAIL (ModuleNotFoundError: fusion).

- [ ] **Step 3: Implement `rrf_fuse` + `compatible`**

Create `scripts/fusion.py`:
```python
"""Federation fusion primitives (#211, M3c-1) — pure, model-free. Reciprocal Rank Fusion across
libraries' embedding shortlists (rank-based, so non-comparable cross-index raw scores don't
matter) + index-compatibility. Consumed by M3c-2 (accelerated federated query) and M3c-3
(find-who-to-ask discovery)."""
from __future__ import annotations


def rrf_fuse(ranked_lists, *, k_const: int = 60) -> list:
    """Reciprocal Rank Fusion. Each input in `ranked_lists` is a best-first list of (hashable)
    item keys. Fused score(item) = sum over the lists it appears in of 1/(k_const + rank),
    rank 1-based. Returns [(item, fused_score)] sorted by fused_score DESC, ties broken by
    first appearance across the inputs (deterministic). Uses RANKS, not raw scores."""
    scores: dict = {}
    first_seen: dict = {}
    order = 0
    for lst in ranked_lists:
        for rank, item in enumerate(lst, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k_const + rank)
            if item not in first_seen:
                first_seen[item] = order
                order += 1
    return sorted(scores.items(), key=lambda kv: (-kv[1], first_seen[kv[0]]))


def compatible(prov_a, prov_b) -> bool:
    """True iff two index provenances are vector-comparable: same model, dims, normalization.
    corpus_hash is deliberately NOT compared (different corpora federate fine)."""
    return (prov_a.model == prov_b.model and prov_a.dims == prov_b.dims
            and prov_a.normalization == prov_b.normalization)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fusion.py -k "rrf or compatible_matrix" -v` → 6 passed. flake8 clean on `scripts/fusion.py tests/test_kb_offline_fusion.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fusion.py tests/test_kb_offline_fusion.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fusion.rrf_fuse + compatible (RRF + index-compat primitives) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `fuse_compatible`

**Files:** Modify `scripts/fusion.py`; Test append to `tests/test_kb_offline_fusion.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
from sdlc_knowledge_base_scripts.fusion import fuse_compatible


def _prov(model="nomic", dims=768, norm="l2"):
    return Provenance(model=model, dims=dims, normalization=norm, corpus_hash="c")


def test_fuse_compatible_rejects_incompatible_and_fuses_survivors():
    ref = _prov()
    entries = [
        ("local", _prov(), ["a.md", "b.md"]),
        ("acme-kb", _prov(), ["a.md", "c.md"]),       # compatible
        ("legacy", _prov(model="old-embed"), ["z.md"]),  # incompatible -> rejected
    ]
    fused, rejected = fuse_compatible(ref, entries)
    assert rejected == ["legacy"]
    # legacy's z.md never appears
    assert all(handle != "legacy" for (handle, _), _ in fused)
    # handle-qualified keys: (local, a.md) and (acme-kb, a.md) are DISTINCT items
    keys = {item for item, _ in fused}
    assert ("local", "a.md") in keys and ("acme-kb", "a.md") in keys


def test_fuse_compatible_all_rejected_yields_empty_fusion():
    ref = _prov()
    entries = [("x", _prov(dims=1), ["a.md"]), ("y", _prov(model="z"), ["b.md"])]
    fused, rejected = fuse_compatible(ref, entries)
    assert fused == [] and set(rejected) == {"x", "y"}


def test_fuse_compatible_ranks_cross_library():
    ref = _prov()
    # a.md is rank-1 in BOTH libs (as distinct handle-qualified items); both should be top-tier
    entries = [("l1", _prov(), ["a.md", "b.md"]), ("l2", _prov(), ["a.md", "c.md"])]
    fused, rejected = fuse_compatible(ref, entries)
    assert rejected == []
    top2 = {item for item, _ in fused[:2]}
    assert top2 == {("l1", "a.md"), ("l2", "a.md")}   # both rank-1 items lead
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fusion.py -k fuse_compatible -v`
Expected: FAIL (ImportError: fuse_compatible).

- [ ] **Step 3: Implement `fuse_compatible`**

Append to `scripts/fusion.py`:
```python
def fuse_compatible(reference_prov, entries, *, k_const: int = 60) -> tuple:
    """entries = [(handle, provenance, ranked_page_ids)]. Keep entries whose provenance is
    compatible(reference_prov, ·); RRF-fuse the survivors over handle-qualified (handle, page_id)
    keys. Returns (fused, rejected_handles): fused = [((handle, page_id), score)] best-first;
    rejected_handles = the incompatible (skipped) handles, in input order. The reject/warn UX is
    the caller's (M3c-2); this only reports which handles were skipped."""
    ranked_lists = []
    rejected = []
    for handle, prov, ranked_page_ids in entries:
        if compatible(reference_prov, prov):
            ranked_lists.append([(handle, pid) for pid in ranked_page_ids])
        else:
            rejected.append(handle)
    return rrf_fuse(ranked_lists, k_const=k_const), rejected
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fusion.py -v` → all pass. Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions — new module, nothing else touched) + flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fusion.py tests/test_kb_offline_fusion.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fusion.fuse_compatible — filter-to-compatible + RRF-fuse + report rejects (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** §1 `rrf_fuse` → Task 1; §2 `compatible` → Task 1, `fuse_compatible` → Task 2. Decisions log 1-5 covered (1-based rank + first-appearance tie-break; handle-qualified keys; model/dims/normalization compat; fuse_compatible reports rejects; pure module).
- **Type/name consistency:** `rrf_fuse(ranked_lists, *, k_const=60) -> [(item, score)]`; `compatible(prov_a, prov_b) -> bool`; `fuse_compatible(reference_prov, entries, *, k_const=60) -> (fused, rejected_handles)` where `entries = [(handle, prov, ranked_page_ids)]` and fused items = `(handle, page_id)` — consistent across tasks + the consuming M3c-2/M3c-3 contracts in the spec.
- **Pure / no deps:** `fusion.py` imports nothing (Provenance is duck-typed; only tests import it). Model-free, no graph, no I/O.
- **RRF math sanity:** 1-based rank, `1/(k+rank)`; the `test_rrf_one_based_rank_math` pins the exact `1/61` value; tie-break determinism pinned by `test_rrf_tiebreak_by_first_appearance`.
- **No silent caps:** `fuse_compatible` returns every rejected handle (caller surfaces them in M3c-2).

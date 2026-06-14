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


def qualify(handle: str, page_id: str) -> str:
    """'handle/page_id'. Handles match ^[a-z][a-z0-9-]*$ (no '/'), so the handle is recoverable
    by splitting on the FIRST '/' even when page_id is nested (e.g. 'sub/x.md')."""
    return f"{handle}/{page_id}"


def split_qualified(qid: str) -> tuple:
    """Inverse of qualify: split on the first '/'. Returns (handle, page_id)."""
    handle, _, page_id = qid.partition("/")
    return handle, page_id

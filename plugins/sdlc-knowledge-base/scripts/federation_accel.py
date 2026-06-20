"""Accelerated federated query (#211, M3c-2). Linear (no graph): load+validate every store once
(closes the gate/worker TOCTOU), embed the question once, search each library in library_specs
order, filter, coverage-guard, RRF-interleave into ONE cross-library candidate list, hand it to a
single reasoned select over a cross-library reduced shelf, then read/synthesize/verify across
libraries with canonical per-library attribution. Embeddings discover; the shelf reasons. Returns
None (all-or-nothing) so the CLI falls back to the M2b federation, never dropping coverage."""
from __future__ import annotations

import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from .audit import AuditEvent, log_event
from .build_shelf_index import extract_entry_block
from .contracts import Answer
from .embeddings import EmbeddingStore, chunk_pages, corpus_hash
from .entailment import verify_entailment
from .federation import _norm, canonicalize_attribution, render_federated
from .fusion import compatible, fuse_compatible, qualify, split_qualified
from .pipeline import select, synthesize
from .priming import build_priming_bundle
from .provenance import filter_pages
from .publication import finalize_answer


def _dedupe_specs(library_specs):
    """Drop duplicate handles (first-appearance kept) with a stderr warning. Required so the
    RRF one-list-per-item invariant holds and external libraries are not double-audited."""
    seen, out = set(), []
    for handle, path in library_specs:
        if handle in seen:
            print(f"accelerate: duplicate library handle {handle!r} dropped", file=sys.stderr)
            continue
        seen.add(handle)
        out.append((handle, path))
    return out


def _resolve_in_root(root_dir: Path, page_id: str):
    """Resolve page_id under root_dir, following symlinks, and require the resolved target to be
    contained by the resolved root (root in target.parents). Returns the resolved Path or None
    for traversal / symlink escape."""
    root = root_dir.resolve()
    target = (root_dir / page_id).resolve()
    if root not in target.parents:
        return None
    return target


def _cross_library_shelf(fused_qids, shelf_texts):
    """Concatenate, in fused order, each fused qid's real shelf block with its header rewritten to
    the qualified id ('## i. handle/page_id'); synthesize a bare header when no block is found."""
    parts = ["# Cross-library reduced shelf\n"]
    for i, qid in enumerate(fused_qids, 1):
        handle, page_id = split_qualified(qid)
        block = extract_entry_block(shelf_texts.get(handle, ""), page_id)
        if block is None:
            parts.append(f"## {i}. {qid}\n")
            continue
        rest = block.split("\n", 1)[1] if "\n" in block else ""
        parts.append(f"## {i}. {qid}\n{rest}")
    return "\n".join(parts).rstrip("\n") + "\n"


def accelerated_federation_query(local_lib, library_specs, question, *, backend,
                                 search_k=20, layer=None, min_confidence=None, audit=True):
    """library_specs = [(handle, path), ...] (first = local). Returns a result dict on success,
    or None if the all-or-nothing gate / query-vector validity / per-library coverage check fails
    (caller falls back to M2b). Read-only; no graph.

    Fallback is by design narrow: None is returned ONLY for gate / query-vector / coverage
    failures. Genuine backend or I/O faults (embed/generate raising, an unreadable index) are
    left to propagate to the CLI wrapper — they are hard environment failures, not coverage
    gaps, and must NOT be silently converted into an M2b fallback."""
    if search_k < 1:
        return None
    specs = _dedupe_specs(library_specs)
    if not specs:
        return None

    # --- Gate (§3): embedding-capable backend ---
    model_fn = getattr(backend, "embedding_model_id", None)
    if model_fn is None:
        print("accelerate: backend has no embedding model — falling back to federation", file=sys.stderr)
        return None
    ref_model = model_fn()

    # local reference index
    local_path = Path(specs[0][1])
    ref_store = EmbeddingStore.load(local_path)
    if ref_store is None:
        print("accelerate: local embedding index missing — falling back", file=sys.stderr)
        return None
    local_prov = ref_store.provenance
    if ref_model != local_prov.model:
        print("accelerate: backend model != local index model — falling back", file=sys.stderr)
        return None

    # load + validate every library once (no later reload — closes TOCTOU); cache each
    # library's chunk rows so the search loop reuses them instead of re-reading+re-hashing.
    stores = {}
    live_ids_by_handle = {}
    for handle, path in specs:
        st = EmbeddingStore.load(Path(path))
        if st is None:
            print(f"accelerate: library {handle!r} has no index — falling back", file=sys.stderr)
            return None
        rows = chunk_pages(path)
        fresh = corpus_hash([(pid, h) for pid, _, h in rows])
        if st.provenance.corpus_hash != fresh:
            print(f"accelerate: library {handle!r} index stale — falling back", file=sys.stderr)
            return None
        if not compatible(local_prov, st.provenance):
            print(f"accelerate: library {handle!r} index incompatible — falling back", file=sys.stderr)
            return None
        stores[handle] = st
        live_ids_by_handle[handle] = {pid for pid, _, _ in rows}

    # --- Embed once + validate (§3) ---
    qvecs = backend.embed([question])
    if len(qvecs) != 1:
        print("accelerate: embedding did not return exactly one vector — falling back", file=sys.stderr)
        return None
    qvec = list(qvecs[0])
    if len(qvec) != local_prov.dims or not all(math.isfinite(x) for x in qvec):
        print("accelerate: query vector invalid — falling back", file=sys.stderr)
        return None

    # --- Per-library search + filter + coverage guard (§5 step 3) ---
    per_lib_ranked = []   # (handle, prov, ranked) in library_specs order
    for handle, path in specs:
        st = stores[handle]
        live_ids = live_ids_by_handle[handle]
        hits = st.search(qvec, k=search_k)
        cand = [pid for pid, _ in hits if pid in live_ids]   # drop tampered/stale/deleted rows
        ranked = filter_pages(Path(path), cand, layer=layer, min_confidence=min_confidence)
        if not ranked:
            eligible = filter_pages(Path(path), sorted(live_ids), layer=layer,
                                    min_confidence=min_confidence)
            if eligible:
                print(f"accelerate: embedding cut missed eligible pages in {handle!r} — falling back",
                      file=sys.stderr)
                return None
        per_lib_ranked.append((handle, st.provenance, ranked))

    # --- 3a: audit ONLY at the commit point (after every fallback-producing check) ---
    if audit:
        audit_log = Path(specs[0][1]) / ".kb-offline" / "audit.log"
        for handle, path in specs[1:]:
            log_event(audit_log, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="cross_library_query", query=question,
                source_handle=handle, reason="accelerated federated query",
                detail={"path": path}))

    # --- Fuse (deterministic, library order) ---
    fused, _ = fuse_compatible(local_prov, per_lib_ranked, k_const=60)
    cut = max(search_k, len(specs))
    fused_qids = [qualify(handle, page_id) for (handle, page_id), _ in fused[:cut]]

    # --- Cross-library reduced shelf ---
    shelf_texts = {}
    for handle, path in specs:
        sp = Path(path) / "_shelf-index.md"
        shelf_texts[handle] = sp.read_text(encoding="utf-8") if sp.is_file() else ""
    reduced = _cross_library_shelf(fused_qids, shelf_texts)

    # --- Priming + one reasoned select ---
    priming = build_priming_bundle(question, Path(specs[0][1]).parent)
    sel = select(question, None, backend=backend, known_pages=set(fused_qids),
                 priming=priming, shelf_text=reduced)

    # Fused cross-library select abstained / returned nothing: no library has a relevant page.
    # Short-circuit to an abstained merged Answer WITHOUT synthesizing (spec §7/§6d). The merged
    # reason is always the generic federated reason (per-library reasons are not surfaced here).
    if sel.no_relevant_page or not sel.page_ids:
        reason = "no library produced a supported answer"
        abstained = Answer(abstained=True, abstention_reason=reason)
        return {"rendered_text": "", "rejected_claims": [],
                "_answer": abstained.model_dump(), "queried": len(specs),
                "fused": len(fused_qids), "deduped": 0,
                "abstained": True, "abstention_reason": reason}

    # --- Read across libraries (path-containment enforced; symlinks resolved) ---
    path_for = {handle: Path(path) for handle, path in specs}
    pages = []
    for qid in sel.page_ids:
        handle, page_id = split_qualified(qid)
        root_dir = path_for.get(handle)
        if root_dir is None:
            continue
        target = _resolve_in_root(root_dir, page_id)
        if target is None or not target.is_file():
            continue
        pages.append({"page": qid, "content": target.read_text(encoding="utf-8")})

    # --- Synthesize + verify + canonicalize ---
    ans = synthesize(question, pages, backend=backend)
    pages_by_name = {p["page"]: p["content"] for p in pages}
    verified = verify_entailment(ans, pages_by_name, backend=backend)
    canonical = canonicalize_attribution(verified)

    # --- Attributed publish (handle_sets per claim from canonicalized cited_pages) ---
    handle_sets = {}
    for c in canonical.claims:
        key = _norm(c.text)
        hs = handle_sets.setdefault(key, [])
        for r in c.cited_pages:
            if r.library not in hs:
                hs.append(r.library)
    rendered, rejected = render_federated(canonical, handle_sets)
    finalize_answer(canonical, rendered, abstain_reason="no library produced a supported answer")
    return {"rendered_text": canonical.rendered_text, "rejected_claims": rejected,
            "_answer": canonical.model_dump(), "queried": len(specs),
            # single cross-library synthesis (not per-library merge), so no claims are deduped;
            # reported for output-shape parity with the M2b federation result.
            "fused": len(fused_qids), "deduped": 0,
            "abstained": canonical.abstained, "abstention_reason": canonical.abstention_reason}

"""Federated query: per-library worker + merge/attribution. kb-offline M2b (#211).
Read-only — runs the M1c-1 query pipeline per library and merges VERIFIED answers with
per-claim source-library attribution. RRF score-fusion is deferred to M3."""
from __future__ import annotations

from pathlib import Path

from .contracts import Answer, PageRef, Span
from .fusion import split_qualified
from .entailment import verify_entailment
from .pipeline import select, synthesize
from .provenance import filter_pages
from .publication import finalize_answer, publish, published_line
from .retrieval import reduce_shelf

_META = {"_shelf-index.md", "log.md", "_index.md"}


def query_one_library(library_path, question, *, backend, priming, layer=None, min_confidence=None):
    """Run select->read->synthesize->verify for ONE library. Returns (verified Answer, page_ids).
    Verification is against THIS library's pages only. If select abstains (no relevant page) the
    library short-circuits to an abstained Answer WITHOUT synthesizing."""
    lib = Path(library_path)
    shelf = lib / "_shelf-index.md"
    known = {p.name for p in lib.glob("*.md") if p.name not in _META}
    candidates = filter_pages(lib, sorted(known), layer=layer, min_confidence=min_confidence)
    sel = select(question, shelf, backend=backend, known_pages=set(candidates), priming=priming,
                 shelf_text=reduce_shelf(shelf, sorted(candidates)))
    if sel.no_relevant_page or not sel.page_ids:
        return Answer(abstained=True, abstention_reason=sel.abstention_reason), list(sel.page_ids)
    pages = [{"page": pid, "content": (lib / pid).read_text(encoding="utf-8")}
             for pid in sel.page_ids if (lib / pid).is_file()]
    ans = synthesize(question, pages, backend=backend)
    pages_by_name = {p["page"]: p["content"] for p in pages}
    verified = verify_entailment(ans, pages_by_name, backend=backend)
    rendered, _ = publish(verified)
    finalize_answer(verified, rendered, abstain_reason="no supported claims")
    return verified, list(sel.page_ids)


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def merge_answers(per_library):
    """per_library = [(handle, verified Answer)]. Returns (merged Answer, handle_sets). Claims
    with identical normalized text dedupe to one entry whose cited_pages carry the union of
    source handles; handle_sets maps NORMALIZED claim text -> ordered-unique source handles.
    Never re-grades."""
    order, by_key, handle_sets = [], {}, {}
    for handle, ans in per_library:
        for c in ans.claims:
            key = _norm(c.text)
            handles = handle_sets.setdefault(key, [])
            if handle not in handles:
                handles.append(handle)
            if key not in by_key:
                merged = c.model_copy(deep=True)
                merged.cited_pages = [PageRef(library=handle, page=r.page) for r in c.cited_pages]
                by_key[key] = merged
                order.append(key)
            else:
                existing = by_key[key]
                existing.cited_pages = existing.cited_pages + [
                    PageRef(library=handle, page=r.page) for r in c.cited_pages
                ]
    return Answer(claims=[by_key[k] for k in order], rendered_text=""), handle_sets


def render_federated(merged, handle_sets):
    """Apply the publication policy with a per-claim source-attribution suffix (e.g.
    '  [dora-corp, acme-kb]'). Returns (rendered_text, rejected_claims)."""
    lines, rejected = [], []
    for c in merged.claims:
        suffix = f"  [{', '.join(handle_sets.get(_norm(c.text), []))}]"
        line, rej = published_line(c, suffix=suffix)
        if line is not None:
            lines.append(line)
        if rej is not None:
            rejected.append(rej)
    return "\n".join(lines), rejected


def canonicalize_attribution(answer):
    """Rewrite each claim's qualified-id references to per-library attribution: cited_pages ->
    PageRef(library=handle, page=page_id) and evidence_spans -> Span(library=handle, page=page_id,
    text=...), splitting each 'handle/page_id' on the first '/'. Verifier grading is preserved.
    Precondition: every cited_pages/evidence_spans page must be a qualified id; a bare id (no '/')
    splits to (handle=id, page_id='') and would be mis-attributed (the accelerated path guarantees
    qualified ids end-to-end, so this only matters for callers outside that pipeline)."""
    out_claims = []
    for c in answer.claims:
        nc = c.model_copy(deep=True)
        nc.cited_pages = []
        for r in c.cited_pages:
            handle, page_id = split_qualified(r.page)
            nc.cited_pages.append(PageRef(library=handle, page=page_id))
        nc.evidence_spans = []
        for s in c.evidence_spans:
            handle, page_id = split_qualified(s.page)
            nc.evidence_spans.append(Span(library=handle, page=page_id, text=s.text))
        out_claims.append(nc)
    return Answer(claims=out_claims, rendered_text=answer.rendered_text,
                  abstained=answer.abstained, abstention_reason=answer.abstention_reason)

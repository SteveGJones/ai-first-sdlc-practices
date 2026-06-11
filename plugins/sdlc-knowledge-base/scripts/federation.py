"""Federated query: per-library worker + merge/attribution. kb-offline M2b (#211).
Read-only — runs the M1c-1 query pipeline per library and merges VERIFIED answers with
per-claim source-library attribution. RRF score-fusion is deferred to M3."""
from __future__ import annotations

from pathlib import Path

from .contracts import Answer, PageRef
from .entailment import verify_entailment
from .pipeline import select, synthesize
from .provenance import filter_pages
from .publication import published_line

_META = {"_shelf-index.md", "log.md", "_index.md"}


def query_one_library(library_path, question, *, backend, priming, layer=None, min_confidence=None):
    """Run select->read->synthesize->verify for ONE library. Returns (verified Answer, page_ids).
    Verification is against THIS library's pages only (no cross-library collision)."""
    lib = Path(library_path)
    shelf = lib / "_shelf-index.md"
    known = {p.name for p in lib.glob("*.md") if p.name not in _META}
    candidates = filter_pages(lib, sorted(known), layer=layer, min_confidence=min_confidence)
    sel = select(question, shelf, backend=backend, known_pages=set(candidates), priming=priming)
    pages = [{"page": pid, "content": (lib / pid).read_text(encoding="utf-8")}
             for pid in sel.page_ids if (lib / pid).is_file()]
    ans = synthesize(question, pages, backend=backend)
    pages_by_name = {p["page"]: p["content"] for p in pages}
    verified = verify_entailment(ans, pages_by_name, backend=backend)
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

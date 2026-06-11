"""Federated query: per-library worker + merge/attribution. kb-offline M2b (#211).
Read-only — runs the M1c-1 query pipeline per library and merges VERIFIED answers with
per-claim source-library attribution. RRF score-fusion is deferred to M3."""
from __future__ import annotations

from pathlib import Path

from .entailment import verify_entailment
from .pipeline import select, synthesize
from .provenance import filter_pages

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

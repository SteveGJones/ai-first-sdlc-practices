"""Accelerated discovery (#211, M3b): embeddings discover a top-N candidate shortlist; build a
REDUCED shelf of just those entries for the reasoned `select` to read. OFF by default — the
query path opts in via --accelerate. Single-library; federation discovery is M3c."""
from __future__ import annotations

from pathlib import Path


def _reduce_shelf(shelf_path: Path, page_ids: list) -> str:
    """Header (lines before the first '- ' bullet) + the matching entry line for each candidate
    in discovery-rank order (synthetic '- <page_id>' if the shelf has no entry for it)."""
    text = shelf_path.read_text(encoding="utf-8") if shelf_path.is_file() else ""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].lstrip().startswith("- "):
        i += 1
    header, entries = lines[:i], lines[i:]
    chosen = []
    for pid in page_ids:
        base = pid.rsplit("/", 1)[-1]
        match = next((ln for ln in entries if pid in ln or base in ln), None)
        chosen.append(match if match is not None else f"- {pid}")
    return "\n".join(header + chosen) + "\n"


def accelerated_candidates(question, library_path, store, *, backend, k: int = 20) -> tuple:
    """Discovery: embed(question) -> store.search top-k -> (page_ids best-first, reduced_shelf)."""
    qvec = backend.embed([question])[0]
    hits = store.search(qvec, k=k)
    page_ids = [pid for pid, _ in hits]
    reduced = _reduce_shelf(Path(library_path) / "_shelf-index.md", page_ids)
    return page_ids, reduced

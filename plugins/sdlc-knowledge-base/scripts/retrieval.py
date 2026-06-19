"""Accelerated discovery (#211, M3b): embeddings discover a top-N candidate shortlist; build a
REDUCED shelf of just those entries for the reasoned `select` to read. OFF by default — the
query path opts in via --accelerate. Single-library; federation discovery is M3c."""
from __future__ import annotations

from pathlib import Path

from .build_shelf_index import _ENTRY_PATH_RE, extract_entry_block


def _entry_id(line: str) -> str | None:
    """The page-id token of a shelf bullet line ('- <id> — desc' / '- <id>: desc' / '- <id>'),
    or None if the line isn't a bullet."""
    s = line.lstrip()
    if not s.startswith("- "):
        return None
    return s[2:].split(" ", 1)[0].rstrip(" \t—-:")


def reduce_shelf(shelf, ordered_ids: list[str]) -> str:
    """Header + the matching entry for each candidate in ordered_ids (order preserved).

    Per page: a real '## N. <id>' block (via extract_entry_block, keeping Hash/Layer/
    Confidence/Terms/Facts), else the legacy '- <id>' bullet line, else a synthetic
    '- <page_id>'. Header runs up to the first real '## N.' entry header; on a pure-legacy
    bullet shelf (no real headers) up to the first '- ' bullet instead.

    ``shelf`` is either a :class:`~pathlib.Path` / path string pointing to a shelf-index
    file **or** the shelf text itself (detected by the presence of a newline in the value).
    """
    if isinstance(shelf, str) and "\n" in shelf:
        text = shelf
    else:
        p = Path(shelf)
        text = p.read_text(encoding="utf-8") if p.is_file() else ""
    lines = text.splitlines()
    hdr_end = next((i for i, ln in enumerate(lines) if _ENTRY_PATH_RE.match(ln)), None)
    if hdr_end is None:
        hdr_end = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("- ")), len(lines))
    header, entries = lines[:hdr_end], lines[hdr_end:]
    chosen = []
    for pid in ordered_ids:
        block = extract_entry_block(text, pid)
        if block is not None:
            chosen.append(block.rstrip("\n"))
            continue
        # nested pid must match its whole path; a flat root pid may also match by basename
        # (base == pid there, so this is a no-op for flat ids and load-bearing for nested ones)
        base = pid.rsplit("/", 1)[-1]
        allowed = {pid} if "/" in pid else {pid, base}
        match = next((ln for ln in entries if _entry_id(ln) in allowed), None)
        chosen.append(match if match is not None else f"- {pid}")
    return "\n".join(header + chosen) + "\n"


def _reduce_shelf(shelf_path: Path, page_ids: list[str]) -> str:
    """Back-compat wrapper — delegates to :func:`reduce_shelf`."""
    return reduce_shelf(shelf_path, page_ids)


def accelerated_candidates(question, library_path, store, *, backend, k: int = 20) -> tuple:
    """Discovery: embed(question) -> store.search top-k -> (page_ids best-first, reduced_shelf)."""
    qvec = backend.embed([question])[0]
    hits = store.search(qvec, k=k)
    page_ids = [pid for pid, _ in hits]
    reduced = _reduce_shelf(Path(library_path) / "_shelf-index.md", page_ids)
    return page_ids, reduced

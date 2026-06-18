"""Provenance/layer filtering for query candidate pages (#211, M1c-1)."""
from __future__ import annotations

import re
import yaml
from pathlib import Path

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)  # assumes LF-terminated, framework-generated frontmatter
_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
_INDEX_FILES = {"_shelf-index.md", "log.md", "_index.md"}


def known_page_ids(lib) -> set[str]:
    """The set of routable library page ids: root-level *.md minus the index/log files.
    Single source of truth shared by the query graph's select node and the eval trace
    (root glob only — nested files are not routable). (#211)"""
    return {p.name for p in Path(lib).glob("*.md") if p.name not in _INDEX_FILES}


def page_frontmatter(library_path: Path, page_name: str) -> dict:
    """Return the page's YAML frontmatter as a dict (empty if absent/unreadable)."""
    p = Path(library_path) / page_name
    if not p.is_file():
        return {}
    m = _FRONTMATTER.match(p.read_text(encoding="utf-8"))
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def filter_pages(
    library_path: Path,
    page_names: list[str],
    *,
    layer: str | None = None,
    min_confidence: str | None = None,
) -> list[str]:
    """Keep pages whose frontmatter satisfies the layer and min-confidence filters.
    Pages missing the relevant field are dropped when a filter is active."""
    min_rank = _CONFIDENCE_RANK.get(min_confidence) if min_confidence else None
    kept = []
    for name in page_names:
        fm = page_frontmatter(library_path, name)
        if layer is not None and fm.get("layer") != layer:
            continue
        # -1: missing/unknown confidence sorts below 'low'
        if min_rank is not None and _CONFIDENCE_RANK.get(fm.get("confidence"), -1) < min_rank:
            continue
        kept.append(name)
    return kept

"""Parse the `<!-- format_version: N -->` breadcrumb from a shelf-index.

The header is primarily a hint to the librarian LLM about what to expect.
LLM-flexible parsing handles mild format drift gracefully; this function
exists so Python-side tooling can also respond to the version (e.g.,
kb-rebuild-indexes could warn when rebuilding a legacy shelf-index).

Phase A of EPIC #164 — see spec §5.3.
"""
from __future__ import annotations

import re
from pathlib import Path


CURRENT_FORMAT_VERSION = 1

_HEADER_RE = re.compile(r"^<!--\s*format_version:\s*(\d+)\s*-->\s*$")


def parse_format_version(shelf_index_path: Path) -> int:
    """Return the format_version from the first line of the shelf-index.

    Missing header → treated as CURRENT_FORMAT_VERSION silently (legacy).
    Malformed header → treated as CURRENT_FORMAT_VERSION silently.
    The header must be on the first line to be recognised.
    """
    if not shelf_index_path.exists():
        return CURRENT_FORMAT_VERSION

    with shelf_index_path.open("r") as fh:
        first_line = fh.readline().rstrip("\n")

    match = _HEADER_RE.match(first_line)
    if not match:
        return CURRENT_FORMAT_VERSION

    try:
        return int(match.group(1))
    except ValueError:
        return CURRENT_FORMAT_VERSION

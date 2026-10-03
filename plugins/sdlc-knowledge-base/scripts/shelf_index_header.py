"""Parse the shelf-index HTML-comment header block.

The header is the source of library-evolution metadata: format version,
last rebuild timestamp, library handle, and human-readable description.
All four fields are optional for backwards compatibility with libraries
predating the rich header.

Phase D of EPIC #164 (sub-9, #175) — see spec §5.3 (originally narrower
format_version-only mechanism, now expanded for library evolution).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


CURRENT_FORMAT_VERSION = 1

_HEADER_FIELD_RE = re.compile(r"^<!--\s*(\w+):\s*(.+?)\s*-->\s*$")


@dataclass
class ShelfIndexHeader:
    format_version: int = CURRENT_FORMAT_VERSION
    last_rebuilt: Optional[str] = None  # ISO 8601 string; None if absent or malformed
    library_handle: Optional[str] = None
    library_description: Optional[str] = None


def parse_shelf_index_header(shelf_index_path: Path) -> ShelfIndexHeader:
    """Parse the HTML-comment header block at the top of a shelf-index file.

    Reads consecutive lines starting with `<!-- ` until a non-comment line
    is encountered. Supports four field names: format_version, last_rebuilt,
    library_handle, library_description. Other field names are ignored.

    Missing or malformed fields default to CURRENT_FORMAT_VERSION (for
    format_version) or None (for the others).
    """
    header = ShelfIndexHeader()
    if not shelf_index_path.exists():
        return header

    with shelf_index_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.rstrip("\n").rstrip("\r")
            if not stripped.startswith("<!--"):
                break
            match = _HEADER_FIELD_RE.match(stripped)
            if not match:
                continue
            field_name, value = match.group(1), match.group(2).strip()
            if field_name == "format_version":
                try:
                    header.format_version = int(value)
                except ValueError:
                    header.format_version = CURRENT_FORMAT_VERSION
            elif field_name == "last_rebuilt":
                header.last_rebuilt = value
            elif field_name == "library_handle":
                header.library_handle = value
            elif field_name == "library_description":
                header.library_description = value
    return header

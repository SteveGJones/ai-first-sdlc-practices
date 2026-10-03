"""Manage the project's layer vocabulary in CLAUDE.md Knowledge Base section."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TypedDict

from .kb_config import (
    _extract_kb_section,
    _parse_layers_from_section,
    allowed_layers,
)


class LayerListResult(TypedDict):
    mode: str
    allowed: list[str]
    usage: dict[str, int]
    uncategorized_count: int


_LAYER_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_KB_HEADING_RE = re.compile(r"^##\s+Knowledge Base\s*$", re.IGNORECASE)
_ANY_HEADING_RE = re.compile(r"^##\s+")
_LAYER_ENTRY_RE = re.compile(r"^\*\*Layer:\*\*\s+(\S+)\s*$", re.MULTILINE)
_LIST_ITEM_RE = re.compile(r"^\s*-\s+")


class LayerOperationError(Exception):
    pass


def _count_layer_usage(shelf_index_path: Path) -> dict[str, int]:
    """Return count of each layer value found in shelf-index **Layer:** entries."""
    if not shelf_index_path.exists():
        return {}
    content = shelf_index_path.read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for m in _LAYER_ENTRY_RE.finditer(content):
        val = m.group(1).strip().lower()
        counts[val] = counts.get(val, 0) + 1
    return counts


def _write_claude_md_atomic(project_dir: Path, content: str) -> None:
    """Write CLAUDE.md atomically via temp file + rename."""
    claude_md = project_dir / "CLAUDE.md"
    tmp = project_dir / "CLAUDE.md.tmp"
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(claude_md)


def _locate_layers_block(
    lines: list[str],
) -> tuple[int, int, int, int]:
    """Return (section_start, section_end, layers_start, layers_end) for the KB section."""
    in_section = False
    section_start = -1
    section_end = len(lines)
    layers_start = -1
    layers_end = -1
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n").rstrip("\r")
        if _KB_HEADING_RE.match(line):
            in_section = True
            section_start = i
            i += 1
            continue
        if in_section and _ANY_HEADING_RE.match(line):
            section_end = i
            break
        if in_section and re.match(r"^layers:\s*$", line):
            layers_start = i
            j = i + 1
            while j < section_end and (
                _LIST_ITEM_RE.match(lines[j]) or not lines[j].strip()
            ):
                j += 1
            layers_end = j
        i += 1
    return section_start, section_end, layers_start, layers_end


def _materialise_layers_in_claude_md(project_dir: Path, new_layers: list[str]) -> None:
    """Write the layers: list into the ## Knowledge Base section of CLAUDE.md.

    If layers: already exists, replaces it. If absent, inserts it.
    If the KB section is missing entirely, appends it.
    """
    claude_md = project_dir / "CLAUDE.md"
    text = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    lines = text.splitlines(keepends=True)

    layers_block = "layers:\n" + "".join(f"  - {layer}\n" for layer in new_layers)

    section_start, section_end, layers_start, layers_end = _locate_layers_block(lines)

    if section_start == -1:
        # No KB section — append one
        new_text = text.rstrip("\n") + "\n\n## Knowledge Base\n\n" + layers_block
        _write_claude_md_atomic(project_dir, new_text)
        return

    new_lines = list(lines)
    if layers_start != -1:
        # Replace existing layers: block
        new_lines[layers_start:layers_end] = [layers_block]
    else:
        # Insert before the next heading (or at end of section)
        insert_idx = section_end
        new_lines.insert(insert_idx, layers_block)

    _write_claude_md_atomic(project_dir, "".join(new_lines))


def _has_explicit_layers(project_dir: Path) -> bool:
    """Return True if CLAUDE.md has an explicit layers: list in the KB section."""
    claude_md = project_dir / "CLAUDE.md"
    if not claude_md.is_file():
        return False
    text = claude_md.read_text(encoding="utf-8")
    section = _extract_kb_section(text)
    if not section.strip():
        return False
    return _parse_layers_from_section(section) is not None


def list_layers(project_dir: Path, shelf_index_path: Path) -> LayerListResult:
    """Return dict with mode, allowed layers, usage counts, and uncategorized count."""
    has_explicit = _has_explicit_layers(project_dir)
    current: list[str] = allowed_layers(project_dir)

    usage = _count_layer_usage(shelf_index_path)
    uncategorized = usage.pop("uncategorized", 0)

    return {
        "mode": "project-defined" if has_explicit else "defaults",
        "allowed": current,
        "usage": {layer: usage.get(layer, 0) for layer in current},
        "uncategorized_count": uncategorized,
    }


def add_layer(project_dir: Path, layer: str) -> str:
    """Add a layer to the project's allowed set. Returns confirmation message.

    Raises LayerOperationError if the layer name is invalid.
    Is idempotent: adding an existing layer returns a no-op message.
    """
    if not _LAYER_RE.match(layer):
        raise LayerOperationError(
            f"invalid layer name '{layer}': must match ^[a-z][a-z0-9-]*$"
        )
    current = allowed_layers(project_dir)
    if layer in current:
        return f"no-op: '{layer}' is already in the allowed set"

    new_layers = current + [layer]
    _materialise_layers_in_claude_md(project_dir, new_layers)
    return f"added '{layer}' to the allowed layer set"


def remove_layer(
    project_dir: Path, shelf_index_path: Path, layer: str, force: bool = False
) -> str:
    """Remove a layer from the project's allowed set.

    Raises LayerOperationError if the layer is in use (unless force=True) or is the last layer.
    Returns a confirmation message on success.
    """
    current = allowed_layers(project_dir)
    if layer not in current:
        return f"no-op: '{layer}' is not in the current allowed set"

    if len(current) == 1:
        raise LayerOperationError(
            f"cannot remove '{layer}': it is the last remaining layer. "
            "The KB requires at least one valid layer value."
        )

    if not force:
        usage = _count_layer_usage(shelf_index_path)
        count = usage.get(layer, 0)
        if count > 0:
            raise LayerOperationError(
                f"cannot remove '{layer}': in use by {count} file(s) in the shelf-index. "
                "Use --force to bypass (kb-lint will report dangling layer references)."
            )

    new_layers = [lay for lay in current if lay != layer]
    _materialise_layers_in_claude_md(project_dir, new_layers)
    return f"removed '{layer}' from the allowed layer set"


def main(args: list[str] | None = None) -> int:
    """CLI entry point for the kb-layers skill."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage KB layer vocabulary.")
    parser.add_argument(
        "--project-dir", default=".", help="Project root containing CLAUDE.md"
    )
    parser.add_argument("--shelf-index-path", default=None, help="Path to shelf-index")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--add", metavar="LAYER", help="Add a layer to the allowed set")
    group.add_argument(
        "--remove", metavar="LAYER", help="Remove a layer from the allowed set"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass usage check on --remove"
    )
    parsed = parser.parse_args(args)

    project_dir = Path(parsed.project_dir)
    shelf_path = (
        Path(parsed.shelf_index_path)
        if parsed.shelf_index_path
        else project_dir / "library" / "_shelf-index.md"
    )

    try:
        if parsed.add:
            msg = add_layer(project_dir, parsed.add)
            print(msg)
            return 0
        elif parsed.remove:
            msg = remove_layer(
                project_dir, shelf_path, parsed.remove, force=parsed.force
            )
            print(msg)
            return 0
        else:
            result = list_layers(project_dir, shelf_path)
            print("# Project layer set\n")
            print(f"Mode: {result['mode']}")
            print("\nAllowed layers:")
            for layer in result["allowed"]:
                count = result["usage"].get(layer, 0)
                print(f"  - {layer:<20} ({count} files)")
            ucount = result["uncategorized_count"]
            if ucount > 0:
                print(f"\nFiles with 'uncategorized' layer: {ucount}")
            return 0
    except LayerOperationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

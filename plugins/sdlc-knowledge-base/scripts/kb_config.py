"""Layer configuration helpers for sdlc-knowledge-base (EPIC #197, issue #154).

Exposes:
  - DEFAULT_LAYERS: list[str]        — project-agnostic defaults
  - allowed_layers(project_dir)      — parse project CLAUDE.md for layers: override
  - check_layer_compliance(lib, allowed) — scan library .md files for layer violations
  - main(args)                       — CLI entry-point

CLI usage:
    python -m sdlc_knowledge_base_scripts.kb_config <library_path> [--project-dir DIR]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_LAYERS: list[str] = ["methodology", "evidence", "domain", "development"]

_EXCLUDED_NAMES: frozenset[str] = frozenset({"_shelf-index.md", "_index.md", "log.md"})
_EXCLUDED_DIRS: frozenset[str] = frozenset({"raw"})

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LIST_ITEM_RE = re.compile(r"^\s*-\s+")

# ---------------------------------------------------------------------------
# CLAUDE.md parser
# ---------------------------------------------------------------------------


def _read_claude_md(project_dir: Path) -> Optional[str]:
    """Return text of CLAUDE.md in project_dir, or None if absent."""
    candidate = project_dir / "CLAUDE.md"
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8")
    return None


def _extract_kb_section(text: str) -> str:
    """Return the body of the ## Knowledge Base section, or empty string."""
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if line.startswith("## Knowledge Base"):
            in_section = True
            continue
        if in_section:
            # Stop at the next ## heading
            if line.startswith("## "):
                break
            section_lines.append(line)
    return "\n".join(section_lines)


def _parse_layers_from_section(section: str) -> Optional[list[str]]:
    """Parse the layers: block from a KB section body.

    Returns a list of layer names when found, or None when the key is absent.
    Inline # comments are stripped from each item.
    """
    lines = section.splitlines()
    layers: list[str] = []
    collecting = False

    for line in lines:
        stripped = line.strip()

        if collecting:
            # Skip blank lines while collecting
            if not stripped:
                continue
            # Check for a list item under layers:
            if _LIST_ITEM_RE.match(line):
                # Strip the leading "- " and any inline comment
                item = re.sub(r"^\s*-\s+", "", line)
                item = item.split("#")[0].strip()
                if item:
                    layers.append(item)
            else:
                # Non-list line — done collecting
                break

        elif stripped == "layers:":
            collecting = True

    if collecting and layers:
        return layers
    return None


def allowed_layers(project_dir: Path) -> list[str]:
    """Return the allowed layer values for project_dir.

    Reads ``project_dir/CLAUDE.md`` and looks for a ``layers:`` key inside the
    ``## Knowledge Base`` section.  Falls back to DEFAULT_LAYERS if:
    - CLAUDE.md does not exist
    - No ``## Knowledge Base`` section is present
    - Section exists but has no ``layers:`` key
    """
    text = _read_claude_md(project_dir)
    if text is None:
        return list(DEFAULT_LAYERS)

    section = _extract_kb_section(text)
    if not section.strip():
        return list(DEFAULT_LAYERS)

    project_layers = _parse_layers_from_section(section)
    if project_layers is None:
        return list(DEFAULT_LAYERS)

    return project_layers


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict[str, object]:
    """Extract YAML frontmatter dict from a markdown file's text.

    Returns an empty dict when frontmatter is absent or malformed.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


# ---------------------------------------------------------------------------
# Compliance checker
# ---------------------------------------------------------------------------


def _is_excluded(path: Path, library_path: Path) -> bool:
    """Return True if path should be skipped during compliance checking."""
    if path.name in _EXCLUDED_NAMES:
        return True
    # Check if top-level directory (relative to library_path) is in _EXCLUDED_DIRS
    try:
        rel = path.relative_to(library_path)
    except ValueError:
        return False
    if rel.parts[0] in _EXCLUDED_DIRS:
        return True
    return False


def check_layer_compliance(
    library_path: Path,
    allowed: list[str],
) -> list[tuple[str, str]]:
    """Scan library .md files for layer: frontmatter violations.

    Excluded files: _shelf-index.md, log.md, _index.md, any file under raw/.

    Returns a list of (relative_path, error_message) tuples, one per violation.
    A violation is either:
    - missing layer: field (absent frontmatter, malformed YAML, or no layer key)
    - invalid layer: value not in allowed list
    """
    violations: list[tuple[str, str]] = []

    for md_file in sorted(library_path.rglob("*.md")):
        if _is_excluded(md_file, library_path):
            continue

        rel = str(md_file.relative_to(library_path))
        text = md_file.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)

        if "layer" not in fm:
            violations.append((rel, "missing layer: frontmatter field"))
            continue

        layer_value = fm["layer"]
        if layer_value not in allowed:
            violations.append(
                (rel, f"invalid layer: '{layer_value}' not in allowed set {allowed}")
            )

    return violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(args: Optional[list[str]] = None) -> int:
    """CLI entry-point.

    Usage:
        kb_config <library_path> [--project-dir DIR]

    Exit 0 if no violations, exit 1 if any violations found.
    """
    parser = argparse.ArgumentParser(
        description="Check layer: frontmatter compliance in a KB library."
    )
    parser.add_argument("library_path", type=Path, help="Path to the library directory")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Project root containing CLAUDE.md (default: current directory)",
    )
    parsed = parser.parse_args(args)

    library_path: Path = parsed.library_path
    project_dir: Path = parsed.project_dir

    if not library_path.is_dir():
        print(f"ERROR: library_path is not a directory: {library_path}", file=sys.stderr)
        return 1

    allowed = allowed_layers(project_dir)
    violations = check_layer_compliance(library_path, allowed)

    if not violations:
        print(f"OK: all files in {library_path} have valid layer: tags")
        return 0

    print(f"VIOLATIONS ({len(violations)}):")
    for rel_path, msg in violations:
        print(f"  {rel_path}: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

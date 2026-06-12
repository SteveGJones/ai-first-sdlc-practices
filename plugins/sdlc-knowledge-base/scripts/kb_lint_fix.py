"""Mechanical auto-fix for missing required frontmatter fields in KB library files.

Fixes three structural defects requiring no judgment:
  missing layer:             -> layer: uncategorized
  missing confidence:        -> confidence: medium
  missing cross_references:  -> cross_references: []

Files with no frontmatter at all receive a stub block with confidence: low
and status: draft (no source metadata to calibrate from).

No LLM invocation. Read-only when dry_run=True. Atomic writes via .tmp + rename.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r"^(---[ \t]*\r?\n)(.*?)(\r?\n---[ \t]*\r?\n)", re.DOTALL)
_EXCLUDED_NAMES = frozenset({"_shelf-index.md", "_index.md", "log.md"})
_EXCLUDED_DIRS = frozenset({"raw"})

# Required frontmatter fields on a page that ALREADY has a frontmatter block. Shared with
# lint.check_frontmatter so the read-only lint and the fixer never disagree on completeness.
REQUIRED_EXISTING_FIELDS = ("layer", "confidence", "cross_references")


@dataclass
class FixResult:
    files_fixed: int = 0
    fields_added: int = 0
    files_skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _is_library_file(path: Path, library_path: Path) -> bool:
    if path.name in _EXCLUDED_NAMES:
        return False
    try:
        rel = path.relative_to(library_path)
    except ValueError:
        return False
    if not rel.parts:
        return False
    if rel.parts[0] in _EXCLUDED_DIRS:
        return False
    return path.suffix == ".md"


def _write_atomic(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(path)


def _derive_title(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def _fix_existing_frontmatter(text: str, path: Path) -> tuple[str, list[str]]:
    """Add missing fields to an existing frontmatter block.

    Returns (new_text, list_of_added_field_names). Returns (text, []) if nothing to add.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return text, []

    try:
        fm = yaml.safe_load(m.group(2))
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        return text, []

    additions: list[str] = []
    new_field_lines: list[str] = []

    _DEFAULTS = {"layer": "uncategorized", "confidence": "medium", "cross_references": "[]"}
    for fieldname in REQUIRED_EXISTING_FIELDS:
        if fieldname not in fm:
            new_field_lines.append(f"{fieldname}: {_DEFAULTS[fieldname]}")
            additions.append(fieldname)

    if not new_field_lines:
        return text, []

    insertion = "\n" + "\n".join(new_field_lines)
    new_text = m.group(1) + m.group(2) + insertion + m.group(3) + text[m.end() :]
    return new_text, additions


def _create_stub_frontmatter(text: str, path: Path) -> tuple[str, list[str]]:
    """Prepend stub frontmatter to a file that has none."""
    title = _derive_title(path)
    stub = (
        "---\n"
        f"title: {title}\n"
        "domain: unknown\n"
        "layer: uncategorized\n"
        "confidence: low\n"
        "status: draft\n"
        "cross_references: []\n"
        "---\n\n"
    )
    additions = ["title", "domain", "layer", "confidence", "status", "cross_references"]
    return stub + text, additions


def fix_missing_fields(library_path: Path, dry_run: bool = False) -> FixResult:
    """Fix missing required frontmatter fields across all library files.

    When dry_run=True, reports what would change without writing.
    """
    result = FixResult()

    for md_file in sorted(library_path.rglob("*.md")):
        if not _is_library_file(md_file, library_path):
            continue

        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            result.errors.append(f"{md_file.name}: unreadable ({exc})")
            continue

        if _FRONTMATTER_RE.match(text):
            new_text, additions = _fix_existing_frontmatter(text, md_file)
            if not additions:
                result.files_skipped += 1
                continue
            if not dry_run:
                _write_atomic(md_file, new_text)
            result.files_fixed += 1
            result.fields_added += len(additions)
        else:
            new_text, additions = _create_stub_frontmatter(text, md_file)
            if not dry_run:
                _write_atomic(md_file, new_text)
            result.files_fixed += 1
            result.fields_added += len(additions)

    return result


def main(args: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-fix missing required frontmatter fields in KB library files."
    )
    parser.add_argument("library_path", help="Path to the library directory")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report changes without writing"
    )
    parsed = parser.parse_args(args)

    library_path = Path(parsed.library_path)
    if not library_path.is_dir():
        print(f"Error: '{library_path}' does not exist.", file=sys.stderr)
        return 1

    result = fix_missing_fields(library_path, dry_run=parsed.dry_run)

    mode = "Would fix" if parsed.dry_run else "Fixed"
    print(
        f"\n{mode}: {result.files_fixed} file(s), {result.fields_added} field(s) added"
    )
    if result.files_skipped:
        print(f"Already complete: {result.files_skipped} file(s) skipped")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for err in result.errors:
            print(f"  {err}")
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())

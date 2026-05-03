"""Deterministic shelf-index rebuild for sdlc-knowledge-base.

Replaces the LLM extraction pass in kb-rebuild-indexes (EPIC #197, issue #155).
Full rebuild of 500 files < 1 second. No LLM invocation.

Importable as a package module:
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index

CLI via the package (used by kb-rebuild-indexes skill):
    python3 -c "from sdlc_knowledge_base_scripts.build_shelf_index import main; import sys; sys.exit(main())" library/
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

_EXCLUDED_NAMES = frozenset({"_shelf-index.md", "_index.md", "log.md"})
_EXCLUDED_DIRS = frozenset({"raw"})

CURRENT_FORMAT_VERSION = 1

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_FINDING_RE = re.compile(r"\*\*Finding\*\*:\s*(.+?)(?=\n|$)")
_NUMBERED_CORE_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*", re.MULTILINE)
_ENTRY_PATH_RE = re.compile(r"^## \d+\.\s+(.+)$", re.MULTILINE)
_ENTRY_HASH_RE = re.compile(r"^\*\*Hash:\*\*\s+([a-f0-9]{64})\s*$", re.MULTILINE)
_HEADER_FIELD_RE = re.compile(r"^<!--\s*(\w+):\s*(.+?)\s*-->\s*$")


@dataclass
class IndexEntry:
    file_path: str
    hash: str
    terms: list[str]
    facts: list[str]
    links: list[str]


@dataclass
class RebuildStats:
    unchanged: int = 0
    modified: int = 0
    added: int = 0
    removed: int = 0
    failed: list[str] = field(default_factory=list)


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter delimited by --- from a Markdown file.

    Returns an empty dict if no frontmatter is found or if YAML is malformed.
    Non-dict YAML (e.g. a bare list) also returns empty dict.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    try:
        result = yaml.safe_load(match.group(1))
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}


def extract_terms(frontmatter: dict, content: str) -> list[str]:
    """Extract up to 30 terms from frontmatter fields and ## headings.

    Sources, in order of priority:
      1. frontmatter 'title' (split on whitespace/commas, lowercased)
      2. frontmatter 'domain' (comma-separated string or list, lowercased)
      3. frontmatter 'tags' (list, lowercased)
      4. '## ' headings from Markdown body (lowercased)

    Deduplication is order-preserving (first-seen wins). Result capped at 30.
    """
    raw: list[str] = []

    title = frontmatter.get("title", "")
    if title:
        raw.extend(t.lower() for t in re.split(r"[\s,]+", str(title)) if t.strip())

    domain = frontmatter.get("domain", "")
    if isinstance(domain, list):
        raw.extend(str(d).strip().lower() for d in domain if d)
    elif domain:
        raw.extend(t.strip().lower() for t in str(domain).split(",") if t.strip())

    tags = frontmatter.get("tags", [])
    if isinstance(tags, list):
        raw.extend(str(t).strip().lower() for t in tags if t)

    for heading in _HEADING_RE.findall(content):
        raw.append(heading.strip().lower())

    seen: set[str] = set()
    result: list[str] = []
    for term in raw:
        if term and term not in seen:
            seen.add(term)
            result.append(term)
            if len(result) == 30:
                break
    return result


def extract_facts(content: str) -> list[str]:
    """Extract up to 5 key findings from the file.

    Primary: lines matching '**Finding**: <text>' (up to 5).
    Fallback: numbered bold items in '## Core Findings' section (up to 5).
    Returns empty list when neither is found.
    """
    findings = _FINDING_RE.findall(content)
    if findings:
        return [f.strip() for f in findings[:5]]

    core_match = re.search(
        r"## Core Findings\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
    )
    if core_match:
        items = _NUMBERED_CORE_RE.findall(core_match.group(1))
        if items:
            return [item.strip() for item in items[:5]]

    return []


def extract_links(frontmatter: dict) -> list[str]:
    """Extract cross-reference links from frontmatter 'cross_references' list."""
    cross_refs = frontmatter.get("cross_references", [])
    if isinstance(cross_refs, list):
        return [str(ref).strip() for ref in cross_refs if ref]
    return []


def compute_hash(path: Path) -> str:
    """Compute SHA-256 of a file's raw bytes; return 64-char lowercase hex string."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_existing_header(shelf_index_path: Path) -> tuple[str, str]:
    """Return (library_handle, library_description) from an existing shelf-index.

    Reads only the leading HTML-comment header lines. Returns ("", "") when the
    file is absent or the fields are not set.
    """
    if not shelf_index_path.exists():
        return "", ""
    handle = ""
    description = ""
    with shelf_index_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            if not stripped:
                continue  # skip blank lines within the header block
            if not stripped.startswith("<!--"):
                break
            match = _HEADER_FIELD_RE.match(stripped)
            if not match:
                continue
            name, value = match.group(1), match.group(2).strip()
            if name == "library_handle":
                handle = value
            elif name == "library_description":
                description = value
    return handle, description


def parse_existing_index(index_path: Path) -> dict[str, str]:
    """Parse an existing shelf-index; return mapping of file_path -> SHA-256 hash.

    Returns an empty dict if the file does not exist or has no parseable entries.
    Scans for '## N. <path>' headers followed by '**Hash:** <hex>' lines.
    """
    if not index_path.exists():
        return {}
    content = index_path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    current_path: Optional[str] = None
    for line in content.splitlines():
        path_match = _ENTRY_PATH_RE.match(line)
        if path_match:
            current_path = path_match.group(1).strip()
            continue
        if current_path:
            hash_match = _ENTRY_HASH_RE.match(line)
            if hash_match:
                result[current_path] = hash_match.group(1)
    return result


def build_entry(file_path: Path, library_root: Path) -> IndexEntry:
    """Parse one library file and return its shelf-index entry."""
    text = file_path.read_text(encoding="utf-8")
    rel_path = str(file_path.relative_to(library_root))
    frontmatter = parse_frontmatter(text)
    return IndexEntry(
        file_path=rel_path,
        hash=compute_hash(file_path),
        terms=extract_terms(frontmatter, text),
        facts=extract_facts(text),
        links=extract_links(frontmatter),
    )


def _discover_library_files(library_path: Path) -> list[Path]:
    """Find all .md files in library_path excluding special files and raw/."""
    files: list[Path] = []
    for p in library_path.rglob("*.md"):
        if p.name in _EXCLUDED_NAMES:
            continue
        try:
            rel = p.relative_to(library_path)
        except ValueError:
            continue
        if rel.parts[0] in _EXCLUDED_DIRS:
            continue
        files.append(p)
    return sorted(files)


def _render_entry(n: int, entry: IndexEntry) -> str:
    facts_block = (
        "\n".join(f"- {f}" for f in entry.facts)
        if entry.facts
        else "- (no structured findings)"
    )
    links_str = ", ".join(entry.links) if entry.links else ""
    return (
        f"## {n}. {entry.file_path}\n\n"
        f"**Hash:** {entry.hash}\n"
        f"**Terms:** {', '.join(entry.terms)}\n"
        f"**Facts:**\n{facts_block}\n"
        f"**Links:** {links_str}\n"
    )


def _build_index_content(
    entries: list[IndexEntry],
    library_handle: str,
    library_description: str,
) -> str:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    header = (
        f"<!-- format_version: {CURRENT_FORMAT_VERSION} -->\n"
        f"<!-- last_rebuilt: {now} -->\n"
        f"<!-- library_handle: {library_handle} -->\n"
        f"<!-- library_description: {library_description} -->\n"
        "# Knowledge Base Shelf-Index\n\n"
        "Generated by `/sdlc-knowledge-base:kb-rebuild-indexes`. "
        "This file is the librarian agent's first-read on every query "
        "— it identifies which library files are relevant before deep-reading them.\n\n"
        "**Do not edit this file by hand.** "
        "Run `/sdlc-knowledge-base:kb-rebuild-indexes` after editing library files to update.\n\n"
        "---\n\n"
    )
    entries_block = "\n".join(_render_entry(n, e) for n, e in enumerate(entries, 1))
    return header + entries_block


def _append_to_log(log_path: Path, stats: RebuildStats, full: bool) -> None:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mode = "full" if full else "incremental"
    summary = f"{stats.unchanged}/{stats.modified}/{stats.added}/{stats.removed}"
    entry = (
        f"\n## [{date}] rebuild-indexes | {summary}\n\n"
        f"Mode: {mode}\n"
        f"Files unchanged: {stats.unchanged}\n"
        f"Files updated: {stats.modified}\n"
        f"Files added: {stats.added}\n"
        f"Files removed: {stats.removed}\n"
    )
    existing = log_path.read_text(encoding="utf-8")
    log_path.write_text(existing + entry, encoding="utf-8")


def rebuild_shelf_index(
    library_path: Path,
    shelf_index_path: Path,
    full: bool = False,
    log_path: Optional[Path] = None,
) -> RebuildStats:
    """Rebuild the shelf-index for library_path.

    Incremental (default): re-extracts only files whose hash changed.
    Full (full=True): re-extracts all files regardless of hash.
    Hash comparison is used for change-detection reporting only —
    build_entry is always called (pure Python, <2ms per file).
    """
    stats = RebuildStats()
    existing_hashes = parse_existing_index(shelf_index_path)
    library_handle, library_description = _read_existing_header(shelf_index_path)

    all_files = _discover_library_files(library_path)
    current_paths = {str(f.relative_to(library_path)) for f in all_files}

    entries: list[IndexEntry] = []
    for file_path in all_files:
        rel = str(file_path.relative_to(library_path))
        current_hash = compute_hash(file_path)
        recorded_hash = existing_hashes.get(rel)

        try:
            entries.append(build_entry(file_path, library_path))
            # Only increment stats after successful extraction
            if not full and recorded_hash == current_hash:
                stats.unchanged += 1
            elif recorded_hash is None:
                stats.added += 1
            else:
                stats.modified += 1
        except Exception as exc:
            stats.failed.append(f"{rel}: {exc}")

    for path in existing_hashes:
        if path not in current_paths:
            stats.removed += 1

    shelf_index_path.parent.mkdir(parents=True, exist_ok=True)
    shelf_index_path.write_text(
        _build_index_content(entries, library_handle, library_description),
        encoding="utf-8",
    )

    if log_path is not None and log_path.exists():
        try:
            _append_to_log(log_path, stats, full=full)
        except OSError as exc:
            stats.failed.append(f"log append failed: {exc}")

    return stats


def main(args: Optional[list[str]] = None) -> int:
    """CLI entry point; returns exit code (0 = success, 1 = error)."""
    parser = argparse.ArgumentParser(
        description="Rebuild the knowledge base shelf-index deterministically."
    )
    parser.add_argument("library_path", help="Path to the library directory")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Force full rebuild (re-extract all files regardless of hash)",
    )
    parser.add_argument(
        "--shelf-index-path",
        default=None,
        metavar="PATH",
        help="Override shelf-index path (default: <library_path>/_shelf-index.md)",
    )
    parser.add_argument(
        "--log-path",
        default=None,
        metavar="PATH",
        help="Override log.md path (default: <library_path>/log.md; skipped if absent)",
    )
    parsed = parser.parse_args(args)

    library_path = Path(parsed.library_path)
    if not library_path.is_dir():
        print(
            f"Error: library path '{library_path}' does not exist or is not a directory.",
            file=sys.stderr,
        )
        return 1

    shelf_index_path = (
        Path(parsed.shelf_index_path)
        if parsed.shelf_index_path
        else library_path / "_shelf-index.md"
    )
    log_path = (
        Path(parsed.log_path) if parsed.log_path else library_path / "log.md"
    )

    stats = rebuild_shelf_index(
        library_path=library_path,
        shelf_index_path=shelf_index_path,
        full=parsed.full,
        log_path=log_path,
    )

    mode = "full" if parsed.full else "incremental"
    total = stats.unchanged + stats.modified + stats.added
    print(f"Shelf-index rebuilt: {shelf_index_path}")
    print()
    print(f"  Mode: {mode}")
    print(f"  Files scanned: {total}")
    print(f"  Unchanged:    {stats.unchanged}  (skipped)")
    print(f"  Modified:     {stats.modified}  (re-extracted)")
    print(f"  Added:        {stats.added}  (new entries)")
    print(f"  Removed:      {stats.removed}  (entries dropped)")
    print()
    print(f"  Index entries: {total}")
    if stats.failed:
        print(f"\nWarnings — {len(stats.failed)} file(s) failed extraction:")
        for msg in stats.failed:
            print(f"  - {msg}")
    return 0

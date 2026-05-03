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

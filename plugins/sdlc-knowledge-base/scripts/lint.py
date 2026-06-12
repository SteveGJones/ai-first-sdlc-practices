"""Federation-aware hygiene lint (read-only). kb-offline M2c (#211). Model-free: per-library
frontmatter completeness + cross-library staleness. Semantic conflict detection is deferred
to M3 (needs embeddings for reliable same-claim matching)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .kb_lint_fix import REQUIRED_EXISTING_FIELDS, _FRONTMATTER_RE, _is_library_file


@dataclass
class FrontmatterIssue:
    page: str
    detail: str


def check_frontmatter(library_path) -> list:
    """Read-only frontmatter completeness scan. Reports pages missing a frontmatter block, or
    missing any REQUIRED_EXISTING_FIELDS. Reuses the fixer's file-exclusion + required-field
    definitions so lint and fix agree. Writes nothing."""
    lib = Path(library_path)
    issues = []
    for md in sorted(lib.rglob("*.md")):
        if not _is_library_file(md, lib):
            continue
        text = md.read_text(encoding="utf-8")
        m = _FRONTMATTER_RE.match(text)
        if not m:
            issues.append(FrontmatterIssue(page=md.name, detail="missing frontmatter block"))
            continue
        try:
            fm = yaml.safe_load(m.group(2))
            if not isinstance(fm, dict):
                fm = {}
        except yaml.YAMLError:
            issues.append(FrontmatterIssue(page=md.name, detail="malformed frontmatter YAML"))
            continue
        missing = [f for f in REQUIRED_EXISTING_FIELDS if f not in fm]
        if missing:
            issues.append(FrontmatterIssue(page=md.name, detail=f"missing fields: {', '.join(missing)}"))
    return issues

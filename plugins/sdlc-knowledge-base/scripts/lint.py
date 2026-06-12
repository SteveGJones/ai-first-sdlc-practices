"""Federation-aware hygiene lint (read-only). kb-offline M2c (#211). Model-free: per-library
frontmatter completeness + cross-library staleness. Semantic conflict detection is deferred
to M3 (needs embeddings for reliable same-claim matching)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from .kb_lint_fix import REQUIRED_EXISTING_FIELDS, _FRONTMATTER_RE, _is_library_file
from .registry import staleness_threshold_for
from .shelf_index_header import parse_shelf_index_header


@dataclass
class StalenessResult:
    handle: str
    state: str          # "fresh" | "stale" | "unknown"
    age_days: Optional[int]
    threshold_days: int
    last_rebuilt: Optional[str]


def _parse_iso_utc(value: str) -> datetime:
    """Parse an ISO 8601 string to tz-aware UTC; naive inputs assumed UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_staleness(source, *, now=None) -> StalenessResult:
    """Compare the library's shelf-index last_rebuilt against staleness_threshold_for(source).
    last_rebuilt absent/malformed -> state 'unknown' (reported, non-failing)."""
    now = now or datetime.now(timezone.utc)
    threshold = staleness_threshold_for(source)
    shelf = Path(source.path) / "_shelf-index.md"
    last = parse_shelf_index_header(shelf).last_rebuilt if shelf.is_file() else None
    if not last:
        return StalenessResult(handle=source.name, state="unknown", age_days=None,
                               threshold_days=threshold, last_rebuilt=None)
    try:
        age_days = (now - _parse_iso_utc(last)).days
    except (ValueError, TypeError):
        return StalenessResult(handle=source.name, state="unknown", age_days=None,
                               threshold_days=threshold, last_rebuilt=last)
    state = "stale" if age_days > threshold else "fresh"
    return StalenessResult(handle=source.name, state=state, age_days=age_days,
                           threshold_days=threshold, last_rebuilt=last)


@dataclass
class FrontmatterIssue:
    page: str
    detail: str


@dataclass
class LibraryLintResult:
    handle: str
    path: str
    frontmatter_issues: list = field(default_factory=list)
    staleness: StalenessResult = None


@dataclass
class LintReport:
    libraries: list = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(r.frontmatter_issues or r.staleness.state == "stale" for r in self.libraries)


def lint_libraries(sources, *, now=None) -> LintReport:
    """Per source: frontmatter issues + staleness. now injected for determinism."""
    now = now or datetime.now(timezone.utc)
    results = []
    for src in sources:
        results.append(LibraryLintResult(
            handle=src.name, path=src.path,
            frontmatter_issues=check_frontmatter(src.path),
            staleness=check_staleness(src, now=now)))
    return LintReport(libraries=results)


def render_lint_report(report) -> tuple:
    """Markdown report + has_issues, with a summary line."""
    lines = ["# kb-offline lint report", ""]
    n_fm = n_stale = 0
    for r in report.libraries:
        s = r.staleness
        if r.frontmatter_issues:
            n_fm += 1
        if s.state == "stale":
            n_stale += 1
        stale_desc = {
            "fresh": f"fresh ({s.age_days}d / {s.threshold_days}d)",
            "stale": f"STALE ({s.age_days}d > {s.threshold_days}d threshold)",
            "unknown": "unknown (no last_rebuilt header)",
        }[s.state]
        lines.append(f"## {r.handle}  ({r.path})")
        lines.append(f"- staleness: {stale_desc}")
        if r.frontmatter_issues:
            lines.append(f"- frontmatter: {len(r.frontmatter_issues)} issue(s)")
            for iss in r.frontmatter_issues:
                lines.append(f"    - {iss.page}: {iss.detail}")
        else:
            lines.append("- frontmatter: clean")
        lines.append("")
    lines.append(f"## Summary: {len(report.libraries)} libraries, "
                 f"{n_fm} with frontmatter issues, {n_stale} stale")
    return "\n".join(lines) + "\n", report.has_issues


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

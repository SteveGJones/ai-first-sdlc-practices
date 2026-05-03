"""Pure-Python knowledge base statistics dashboard for sdlc-knowledge-base.

Reads shelf-index and log.md; emits a markdown report with 5 sections:
  - Inventory
  - Distribution by layer
  - Distribution by domain
  - Recent activity
  - Staleness

No LLM invocation. Read-only.

CLI usage (via package module):
    python3 -c "from sdlc_knowledge_base_scripts.kb_stats import main; import sys; sys.exit(main())" \\
        --library-path library/ \\
        --shelf-index-path library/_shelf-index.md \\
        --log-path library/log.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_HEADER_FIELD_RE = re.compile(r"^<!--\s*(\w+):\s*(.+?)\s*-->\s*$")
_ENTRY_SPLIT_RE = re.compile(r"^## \d+\.", re.MULTILINE)
_LAYER_RE = re.compile(r"^\*\*Layer:\*\*\s+(\S+)\s*$", re.MULTILINE)
_TERMS_RE = re.compile(r"^\*\*Terms:\*\*\s+(.+)$", re.MULTILINE)
_FACTS_BULLET_RE = re.compile(r"^\s*-\s+.+", re.MULTILINE)
_FACTS_SECTION_RE = re.compile(r"\*\*Facts:\*\*\s*\n(.*?)(?=\n\*\*|\Z)", re.DOTALL)
_NO_FINDINGS_RE = re.compile(r"no structured findings", re.IGNORECASE)
_LOG_ENTRY_RE = re.compile(
    r"^## \[(\d{4}-\d{2}-\d{2})\]\s+(\S+)\s*\|?\s*(.*?)\s*$", re.MULTILINE
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class _ShelfEntry:
    file_path: str
    layer: str
    domains: list[str]
    facts_count: int
    links: list[str] = field(default_factory=list)


@dataclass
class _LogEntry:
    date: date
    operation: str
    subject: str


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_header_fields(content: str) -> dict[str, str]:
    """Extract <!-- key: value --> header comment fields from shelf-index."""
    fields: dict[str, str] = {}
    for line in content.splitlines():
        m = _HEADER_FIELD_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
        elif line.startswith("#"):
            # Past the header block once we hit a Markdown heading
            break
    return fields


def _count_facts_in_block(block: str) -> int:
    """Count bullet-item findings in a **Facts:** block.

    Returns 0 for the 'no structured findings' sentinel.
    """
    facts_match = _FACTS_SECTION_RE.search(block)
    if not facts_match:
        return 0
    facts_text = facts_match.group(1)
    if _NO_FINDINGS_RE.search(facts_text):
        return 0
    bullets = _FACTS_BULLET_RE.findall(facts_text)
    return len(bullets)


def _parse_domains_from_terms(terms_line: str) -> list[str]:
    """Split a **Terms:** line into individual domain tokens."""
    return [t.strip().lower() for t in terms_line.split(",") if t.strip()]


def _parse_shelf_index(content: str) -> list[_ShelfEntry]:
    """Parse all entries from shelf-index content."""
    # Split on '## N.' headings; first element is the preamble (skip it)
    raw_sections = _ENTRY_SPLIT_RE.split(content)
    entries: list[_ShelfEntry] = []
    for section in raw_sections[1:]:
        # First non-empty line carries the filename
        lines = section.lstrip("\n").splitlines()
        if not lines:
            continue
        file_path = lines[0].strip().rstrip(".")

        layer_match = _LAYER_RE.search(section)
        layer = layer_match.group(1).strip().lower() if layer_match else "uncategorized"

        terms_match = _TERMS_RE.search(section)
        domains = _parse_domains_from_terms(terms_match.group(1)) if terms_match else []

        facts_count = _count_facts_in_block(section)

        # Parse **Links:** — comma-separated list on same line
        links_match = re.search(r"^\*\*Links:\*\*\s*(.*)", section, re.MULTILINE)
        links: list[str] = []
        if links_match:
            raw_links = links_match.group(1).strip()
            if raw_links:
                links = [lnk.strip() for lnk in raw_links.split(",") if lnk.strip()]

        entries.append(
            _ShelfEntry(
                file_path=file_path,
                layer=layer,
                domains=domains,
                facts_count=facts_count,
                links=links,
            )
        )
    return entries


def _parse_log(content: str, since: date | None = None) -> list[_LogEntry]:
    """Parse log.md entries, optionally filtering to those on/after `since`."""
    log_entries: list[_LogEntry] = []
    for m in _LOG_ENTRY_RE.finditer(content):
        entry_date = date.fromisoformat(m.group(1))
        if since is not None and entry_date < since:
            continue
        log_entries.append(
            _LogEntry(
                date=entry_date,
                operation=m.group(2).lower(),
                subject=m.group(3).strip(),
            )
        )
    return log_entries


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_inventory_section(entries: list[_ShelfEntry]) -> list[str]:
    """Render the Inventory section lines."""
    total_files = len(entries)
    total_facts = sum(e.facts_count for e in entries)
    no_layer = sum(1 for e in entries if e.layer == "uncategorized")
    orphans = sum(1 for e in entries if not e.links)
    lines: list[str] = []
    lines.append("## Inventory")
    lines.append("")
    lines.append(f"- Total files: {total_files}")
    lines.append(f"- Total findings: {total_facts}")
    lines.append(f"- Files lacking layer tag: {no_layer}")
    lines.append(f"- Files lacking cross-references (orphans): {orphans}")
    lines.append("")
    return lines


def _render_layer_section(entries: list[_ShelfEntry]) -> list[str]:
    """Render the Distribution by layer section as a markdown table."""
    layer_files: dict[str, int] = {}
    layer_facts: dict[str, int] = {}
    for e in entries:
        layer_files[e.layer] = layer_files.get(e.layer, 0) + 1
        layer_facts[e.layer] = layer_facts.get(e.layer, 0) + e.facts_count

    lines: list[str] = []
    lines.append("## Distribution by layer")
    lines.append("")
    if layer_files:
        lines.append("| Layer | Files | Findings | Avg findings/file |")
        lines.append("|---|---|---|---|")
        for layer, count in sorted(layer_files.items(), key=lambda x: -x[1]):
            facts = layer_facts.get(layer, 0)
            avg = f"{facts / count:.1f}" if count else "-"
            lines.append(f"| {layer} | {count} | {facts} | {avg} |")
    else:
        lines.append("_No entries in shelf-index._")
    lines.append("")
    return lines


def _render_domain_section(entries: list[_ShelfEntry]) -> list[str]:
    """Render the Distribution by domain section as a markdown table."""
    domain_counts: dict[str, int] = {}
    for e in entries:
        for d in e.domains:
            domain_counts[d] = domain_counts.get(d, 0) + 1

    lines: list[str] = []
    lines.append("## Distribution by domain")
    lines.append("")
    if domain_counts:
        top_domains = sorted(domain_counts.items(), key=lambda x: -x[1])[:15]
        lines.append("| Domain | Files |")
        lines.append("|---|---|")
        for domain, count in top_domains:
            lines.append(f"| {domain} | {count} |")
    else:
        lines.append("_No domain terms found._")
    lines.append("")
    return lines


def _render_activity_section(
    log_entries: list[_LogEntry], since_days: int
) -> list[str]:
    """Render the Recent activity section lines."""
    lines: list[str] = []
    lines.append("## Recent activity")
    lines.append("")
    window_label = f"last {since_days} days"
    if log_entries:
        # Group by operation
        op_counts: dict[str, int] = {}
        for entry in log_entries:
            op_counts[entry.operation] = op_counts.get(entry.operation, 0) + 1
        lines.append(f"- Total operations: {len(log_entries)}")
        for op, cnt in sorted(op_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  - {op}: {cnt}")
        lines.append("")
        # Show up to 10 most recent entries
        lines.append("### Most recent entries")
        lines.append("")
        for entry in sorted(log_entries, key=lambda e: e.date, reverse=True)[:10]:
            subject = entry.subject or "(no subject)"
            lines.append(f"- [{entry.date}] {entry.operation} | {subject}")
    else:
        lines.append(f"_No log entries in the {window_label} window._")
    lines.append("")
    return lines


def _render_staleness_section(last_rebuilt_raw: str) -> list[str]:
    """Render the Staleness section lines."""
    lines: list[str] = []
    lines.append("## Staleness")
    lines.append("")
    if last_rebuilt_raw:
        lines.append(f"- Last rebuilt: {last_rebuilt_raw}")
        try:
            rebuilt_dt = datetime.fromisoformat(last_rebuilt_raw.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )
            age_days = (datetime.now(timezone.utc) - rebuilt_dt).days
            lines.append(f"- Age: {age_days} day(s)")
            if age_days > 7:
                lines.append(
                    "- Status: STALE — consider running `/sdlc-knowledge-base:kb-rebuild-indexes`"
                )
            else:
                lines.append("- Status: FRESH")
        except ValueError:
            lines.append("- Status: unknown (could not parse last_rebuilt timestamp)")
    else:
        lines.append("- Last rebuilt: unknown")
        lines.append(
            "- Status: unknown — run `/sdlc-knowledge-base:kb-rebuild-indexes` to generate shelf-index"
        )
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_stats(
    library_path: Path,
    shelf_index_path: Path,
    log_path: Path,
    since_days: int = 30,
) -> str:
    """Generate a markdown statistics report for the knowledge base.

    Args:
        library_path: Root directory of the library.
        shelf_index_path: Path to _shelf-index.md.
        log_path: Path to log.md (may be absent — handled gracefully).
        since_days: Number of days to include in Recent activity window.

    Returns:
        Markdown string with 5 sections: Inventory, Distribution by layer,
        Distribution by domain, Recent activity, Staleness.
    """
    # --- Shelf-index ---
    shelf_content = ""
    if shelf_index_path.exists():
        shelf_content = shelf_index_path.read_text(encoding="utf-8")

    header_fields = _parse_header_fields(shelf_content)
    entries = _parse_shelf_index(shelf_content) if shelf_content else []

    # --- Log ---
    today = date.today()
    since_date = today - timedelta(days=since_days)
    log_content = ""
    if log_path.exists():
        log_content = log_path.read_text(encoding="utf-8")
    recent_log = _parse_log(log_content, since=since_date)

    # --- Build report ---
    lines: list[str] = []

    # Title
    lines.append("# Knowledge Base Statistics")
    lines.append("")
    lines.append(
        f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_"
    )
    lines.append("")

    lines.extend(_render_inventory_section(entries))
    lines.extend(_render_layer_section(entries))
    lines.extend(_render_domain_section(entries))
    lines.extend(_render_activity_section(recent_log, since_days))
    lines.extend(_render_staleness_section(header_fields.get("last_rebuilt", "")))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(args: list[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="Generate knowledge base statistics dashboard."
    )
    parser.add_argument(
        "--library-path",
        required=True,
        help="Root directory of the library (must exist).",
    )
    parser.add_argument(
        "--shelf-index-path",
        required=True,
        help="Path to _shelf-index.md.",
    )
    parser.add_argument(
        "--log-path",
        required=True,
        help="Path to log.md (missing log is tolerated).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write report to this file instead of stdout.",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Override recent-activity window start (ISO date, e.g. 2026-01-01).",
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=30,
        help="Number of days back for recent-activity window (default: 30).",
    )

    parsed = parser.parse_args(args)

    library_path = Path(parsed.library_path)
    shelf_index_path = Path(parsed.shelf_index_path)
    log_path = Path(parsed.log_path)

    if not library_path.exists():
        sys.stderr.write(
            f"[kb-stats] ERROR: library directory not found: {library_path}\n"
        )
        sys.stderr.write(
            "  Run /sdlc-knowledge-base:kb-init to initialise the library first.\n"
        )
        return 1

    # Resolve since_days from --since flag if provided
    since_days = parsed.since_days
    if parsed.since:
        try:
            since_date = date.fromisoformat(parsed.since)
            since_days = (date.today() - since_date).days
        except ValueError:
            sys.stderr.write(
                f"[kb-stats] ERROR: --since value is not a valid ISO date: {parsed.since}\n"
            )
            return 1

    report = generate_stats(
        library_path, shelf_index_path, log_path, since_days=since_days
    )

    if parsed.output:
        output_path = Path(parsed.output)
        output_path.write_text(report, encoding="utf-8")
        sys.stdout.write(f"[kb-stats] Report written to {output_path}\n")
    else:
        sys.stdout.write(report)
        if not report.endswith("\n"):
            sys.stdout.write("\n")

    return 0

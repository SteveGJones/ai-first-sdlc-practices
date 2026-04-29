"""Module-scoped traceability render and module-dependency-graph for the Assured bundle."""

from __future__ import annotations

from typing import List

from .code_index import CodeIndexEntry
from .ids import IdRecord


def render_module_scope(
    module_id: str,
    records: List[IdRecord],
    code_entries: List[CodeIndexEntry],
    spec_module_lookup: dict[str, str],
) -> str:
    """Render the REQ → DES → TEST → CODE chain for a single module."""
    in_module = [r for r in records if spec_module_lookup.get(r.id) == module_id]
    reqs = [r for r in in_module if r.kind == "REQ"]
    deses = [r for r in in_module if r.kind == "DES"]
    tests = [r for r in in_module if r.kind == "TEST"]
    in_module_code = [
        c
        for c in code_entries
        if any(spec_module_lookup.get(cid) == module_id for cid in c.cited_ids)
    ]
    orphan_code = [
        c
        for c in code_entries
        if c not in in_module_code
        and not any(cid in spec_module_lookup for cid in c.cited_ids)
    ]
    lines = [
        f"# Module: {module_id}",
        "",
        "## Requirements",
        "",
    ]
    for r in reqs:
        lines.append(f"- **{r.id}** — [{r.source}](../../{r.source})")
    if not reqs:
        lines.append("_(no requirements)_")
    lines.extend(["", "## Designs", ""])
    for d in deses:
        sat = ", ".join(d.satisfies) if d.satisfies else "(no satisfies)"
        lines.append(f"- **{d.id}** satisfies {sat} — [{d.source}](../../{d.source})")
    if not deses:
        lines.append("_(no designs)_")
    lines.extend(["", "## Tests", ""])
    for t in tests:
        sat = ", ".join(t.satisfies) if t.satisfies else "(no satisfies)"
        lines.append(f"- **{t.id}** satisfies {sat} — [{t.source}](../../{t.source})")
    if not tests:
        lines.append("_(no tests)_")
    lines.extend(["", "## Code", ""])
    for c in in_module_code:
        cited = ", ".join(c.cited_ids)
        lines.append(f"- `{c.file_path}:{c.line}` implements {cited}")
    if not in_module_code:
        lines.append("_(no code annotations)_")
    if orphan_code:
        lines.extend(
            [
                "",
                "## Orphan code",
                "",
                "Code citing IDs that do not exist in the registry:",
            ]
        )
        for c in orphan_code:
            cited = ", ".join(c.cited_ids)
            lines.append(f"- `{c.file_path}:{c.line}` cites missing {cited}")
    return "\n".join(lines) + "\n"

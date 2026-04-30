"""Module-scoped traceability render and module-dependency-graph for the Assured bundle."""

from __future__ import annotations

from typing import List

from .code_index import CodeIndexEntry
from .decomposition import Decomposition, ImportEdge
from .ids import IdRecord


def render_module_scope(
    module_id: str,
    records: List[IdRecord],
    code_entries: List[CodeIndexEntry],
    spec_module_lookup: dict[str, str],
) -> str:
    # implements: DES-assured-render-001
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


def render_module_dependency_graph(
    decomp: Decomposition, actual_edges: List[ImportEdge]
) -> str:
    # implements: DES-assured-render-002
    """Render the module-dependency graph as a markdown edge-list (Q1 v0.1.0 format)."""
    declared: dict[str, set[str]] = {}
    for v in decomp.visibility:
        declared[v.from_module] = set(v.to_modules)
    lines = [
        "# Module Dependency Graph",
        "",
        "Each row represents one observed cross-module edge."
        ' "Allowed?" reflects the project\'s `programs.yaml` visibility block.',
        "",
    ]
    if not actual_edges:
        lines.append("_(no module-to-module dependencies detected)_")
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "| From | → | To | Allowed? |",
            "|------|---|----|----------|",
        ]
    )
    sorted_edges = sorted({(e.from_module, e.to_module) for e in actual_edges})
    for from_, to_ in sorted_edges:
        allowed = "yes" if to_ in declared.get(from_, set()) else "NO"
        lines.append(f"| {from_} | → | {to_} | {allowed} |")
    return "\n".join(lines) + "\n"

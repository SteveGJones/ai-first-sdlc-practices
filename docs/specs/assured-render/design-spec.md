---
feature_id: assured-render
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-render

**Feature-id:** assured-render
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Two design units implement the public render functions. Both accept pre-computed in-memory data structures (lists of `IdRecord`, `CodeIndexEntry`, `ImportEdge`, and the `Decomposition` object) and produce a single markdown string. Neither performs file I/O or validation.

---

## Design

### DES-assured-render-001

`render_module_scope(module_id, records, code_entries, spec_module_lookup)` partitions the input records into three typed lists — REQs, DESes, and TESTs — by filtering on `spec_module_lookup.get(r.id) == module_id`. It partitions `code_entries` into in-module code (any cited ID maps to the target module) and orphan code (all cited IDs are absent from `spec_module_lookup` entirely). It emits six sections in order:

1. `# Module: {module_id}` title.
2. `## Requirements` — one bullet per REQ as `**{id}** — [source](../../source)`; sentinel `_(no requirements)_` when empty.
3. `## Designs` — one bullet per DES as `**{id}** satisfies {satisfies} — [source](../../source)`; sentinel when empty.
4. `## Tests` — one bullet per TEST with the same satisfies/source pattern; sentinel when empty.
5. `## Code` — one bullet per in-module code entry as `` `file_path:line` implements {cited_ids} ``; sentinel when empty.
6. `## Orphan code` — present only when orphan_code is non-empty; lists each orphan entry as `` `file_path:line` cites missing {cited_ids} `` with an explanatory header line.

The function returns `"\n".join(lines) + "\n"`.

**satisfies:** REQ-assured-render-001

### DES-assured-render-002

`render_module_dependency_graph(decomp, actual_edges)` extracts the declared visibility mapping from `decomp.visibility` as a `dict[str, set[str]]` (from_module → allowed to_modules). It emits:

1. `# Module Dependency Graph` title.
2. A prose banner explaining that "Allowed?" reflects the project's `programs.yaml` visibility block.
3. If `actual_edges` is empty: the sentinel `_(no module-to-module dependencies detected)_` and returns immediately.
4. Otherwise: a GFM pipe table with header `| From | → | To | Allowed? |` and one row per unique `(from_module, to_module)` pair. Pairs are deduplicated by converting to a set and sorted lexicographically. The `Allowed?` cell is `yes` if `to_module` is in the declared set for `from_module`, otherwise `NO` (uppercase, signalling a policy violation).

The function returns `"\n".join(lines) + "\n"`.

**satisfies:** REQ-assured-render-002

---

## Out of scope

- Sorting or grouping artefacts within a section by anything other than input list order.
- Escaping of pipe characters or special markdown characters within record IDs or source paths.
- Combining both renderers into a single unified document — each renderer is invoked separately by the caller.

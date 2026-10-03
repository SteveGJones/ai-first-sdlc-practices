---
feature_id: assured-render
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-render

**Feature-id:** assured-render
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option must provide human-readable renderings of the traceability graph so that teams can inspect the state of a module's artefacts at a glance. Two render functions serve this need: one produces a full module-scope document (REQ → DES → TEST → CODE chain, plus an orphan-code section for broken citations), and one produces a markdown edge-list showing the module dependency graph with an Allowed? column derived from the project's visibility block. Both return strings so that callers control where output is written.

## Requirements

### REQ-assured-render-001

A team member or auditor MUST be able to produce a human-readable module-scope document listing all REQ, DES, and TEST artefacts assigned to a given module together with their citing code annotations, plus an "Orphan code" section for annotations whose cited IDs do not exist in the registry — so that the full traceability state of a module is visible at a glance.

**Module:** P1.SP1.M2

### REQ-assured-render-002

A team member or auditor MUST be able to produce a markdown edge-list showing every observed cross-module dependency with an Allowed?/yes/NO column derived from the project's declared visibility block — so that undeclared module boundaries can be identified at a glance.

**Module:** P1.SP1.M2

## Out of scope

- File I/O — both render functions return a string; writing to disk is the caller's responsibility.
- Filtering or sorting of artefacts by anything other than module assignment — records are rendered in the iteration order of the input lists.
- Validation of input records or edges — malformed or missing fields are rendered as-is; validation is the responsibility of `traceability_validators` and `decomposition_validators`.
- Rendering partial cross-module subgraphs — `render_module_dependency_graph` always renders the full observed edge set.

## Success criteria

- `render_module_scope("P1.SP1.M1", records, code_entries, lookup)` returns a string with `# Module: P1.SP1.M1` as the first line, followed by `## Requirements`, `## Designs`, `## Tests`, `## Code` sections, each listing the artefacts assigned to that module; and when code entries cite IDs absent from `lookup`, an `## Orphan code` section appears listing those entries.
- `render_module_dependency_graph(decomp, actual_edges)` returns a string beginning with `# Module Dependency Graph`, containing a GFM pipe table with columns `From`, `→`, `To`, `Allowed?`; edges declared in the visibility block show `yes` and undeclared edges show `NO`; when `actual_edges` is empty the output contains `_(no module-to-module dependencies detected)_` and no table.

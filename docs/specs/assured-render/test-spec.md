---
feature_id: assured-render
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-render

**Feature-id:** assured-render
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, using in-memory `IdRecord`, `CodeIndexEntry`, `ImportEdge`, and `Decomposition` fixtures with no file I/O. Each test exercises the public API and asserts both structural and content properties of the returned string.

---

## Tests

### TEST-assured-render-001

**Title:** `render_module_scope` section structure, artefact listing, and orphan-code detection

**Description:** (a) Construct a minimal fixture with `spec_module_lookup = {"REQ-foo-001": "P1.SP1.M1", "DES-foo-001": "P1.SP1.M1", "TEST-foo-001": "P1.SP1.M1"}`. Create one `IdRecord` of each kind (REQ, DES, TEST), each with `id` in the lookup and `source="specs/foo/requirements-spec.md"` (or equivalent). Create one `CodeIndexEntry` citing `REQ-foo-001` at `src/foo.py:5`. Call `render_module_scope("P1.SP1.M1", [req, des, test], [code], lookup)` and assert: the string starts with `# Module: P1.SP1.M1`; it contains `## Requirements`, `## Designs`, `## Tests`, `## Code` sections in that order; `REQ-foo-001` appears in Requirements; `DES-foo-001` appears in Designs; `TEST-foo-001` appears in Tests; `` `src/foo.py:5` implements REQ-foo-001 `` appears in Code; `## Orphan code` is absent. (b) Add a second `CodeIndexEntry` citing `MISSING-999` (not in lookup) and call again: assert `## Orphan code` is now present and the entry for `MISSING-999` appears under it. (c) Call with `records=[]` and `code_entries=[]`: assert all four content sections emit their respective `_(no …)_` sentinels and `## Orphan code` is absent.

**satisfies:** REQ-assured-render-001 via DES-assured-render-001

---

### TEST-assured-render-002

**Title:** `render_module_dependency_graph` table structure, Allowed? classification, and empty-edge sentinel

**Description:** (a) Construct a `Decomposition` with one `VisibilityRule` declaring `from_module="P1.SP1.M1"` and `to_modules=["P1.SP1.M2"]`. Create two `ImportEdge` objects: one allowed (`from_module="P1.SP1.M1"`, `to_module="P1.SP1.M2"`) and one disallowed (`from_module="P1.SP1.M1"`, `to_module="P1.SP1.M3"`). Call `render_module_dependency_graph(decomp, [edge_allowed, edge_disallowed])` and assert: the string starts with `# Module Dependency Graph`; it contains `| From | → | To | Allowed? |`; the row for `P1.SP1.M1 → P1.SP1.M2` shows `yes`; the row for `P1.SP1.M1 → P1.SP1.M3` shows `NO`. (b) Add a duplicate of `edge_allowed` to the edge list and call again: assert only one row for `P1.SP1.M1 → P1.SP1.M2` appears (deduplication). (c) Call `render_module_dependency_graph(decomp, [])` with an empty edge list and assert: the string contains `_(no module-to-module dependencies detected)_` and does not contain a pipe-table row.

**satisfies:** REQ-assured-render-002 via DES-assured-render-002

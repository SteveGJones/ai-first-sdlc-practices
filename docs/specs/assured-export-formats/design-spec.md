---
feature_id: assured-export-formats
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-export-formats

**Feature-id:** assured-export-formats
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Four design units implement the regulator-facing exporters; a fifth shared helper (`_build_rows`) supports the two generic non-regulatory exporters which are bundled under DES-004 as non-regulatory companions. Two private index helpers (`_index_by_satisfies`, `_code_by_cited`) are shared infrastructure used across all design units but are not individually traceable — they have no REQ of their own.

---

## Design

### DES-assured-export-formats-001

`export_do178c_rtm(records, code)` builds a GFM pipe table with a four-column header (HLR | LLR | Source code | Test case) preceded by a `# Requirements Traceability Matrix (DO-178C)` title and a prose banner identifying the generation command. It iterates REQ records; for each REQ it resolves DES children via `_index_by_satisfies`, then for each DES resolves TEST children and merges code locations from `_code_by_cited` at both the REQ and DES level. Rows without a DES child emit a stub row. Source code locations are formatted as `file_path:line`; absent values render as the em-dash character `—`.

**satisfies:** REQ-assured-export-formats-001

### DES-assured-export-formats-002

`export_iec_62304_matrix(records, code, software_safety_class)` builds a GFM pipe table with a three-column header (Software requirement | Software unit | Verification activity) preceded by a `# IEC 62304 Software Traceability Matrix` title and a `Software safety class: {class}` line. It iterates REQ records; for each REQ it collects code units from `_code_by_cited` at both REQ and DES level, and collects TEST children via `_index_by_satisfies` on the DES layer. One row is emitted per REQ regardless of how many DES children exist; absent values render as `—`. The `software_safety_class` parameter defaults to `"A"`.

**satisfies:** REQ-assured-export-formats-002

### DES-assured-export-formats-003

`export_iso_26262_asil_matrix(records, code, asil_level)` builds a GFM pipe table with a four-column header (Safety requirement | Architectural element | Implementation | Verification) preceded by a `# ISO 26262 ASIL Traceability Matrix` title and an `ASIL: {level}` line. It iterates REQ records; for each REQ it resolves DES children via `_index_by_satisfies`, then for each DES resolves TEST children and merges code locations at both REQ and DES level. Rows without a DES child emit a stub row. The `asil_level` parameter defaults to `"B"`.

**satisfies:** REQ-assured-export-formats-003

### DES-assured-export-formats-004

`export_fda_dhf_structure(records, code)` emits a structured markdown document with four `##`-level sections, each citing its regulatory clause:

- **Design inputs** (§820.30(c)): lists all REQ records as `- **{id}**: see {source}`.
- **Design outputs** (§820.30(d)): lists all DES records as `- **{id}** satisfies {satisfies}: see {source}`, followed by all code entries as `- Source code: \`{file}:{line}\` implements {cited_ids}`.
- **Design verification** (§820.30(f)): lists all TEST records as `- **{id}** verifies {satisfies}: see {source}`.
- **Design validation** (§820.30(g)): emits a fixed human-attestation placeholder; the framework does not auto-populate this section.

Empty sections emit an `_(no … declared)_` sentinel rather than a blank list.

The two generic non-regulatory exporters are bundled here as non-regulatory companions sharing the same four-column REQ/DES/TEST/CODE schema:

- `export_csv(records, code)` delegates to `_build_rows` and emits a CSV string with header `REQ,DES,TEST,CODE`. Commas within cell values are replaced with semicolons to avoid breaking the CSV structure.
- `export_markdown(records, code)` delegates to `_build_rows` and emits a GFM pipe table under a `# Traceability Matrix` title with columns REQ | DES | TEST | CODE.

Both generic exporters use `_build_rows`, a shared helper that iterates REQ records, resolves DES/TEST/code via the two private index helpers, and yields one `(req_id, des_id, test_str, code_str)` tuple per (REQ, DES) combination (stub tuple for REQs with no DES).

**satisfies:** REQ-assured-export-formats-004

---

## Out of scope

- Incremental or cached export — each exporter rebuilds its index on every call; caching is the caller's responsibility.
- Column sorting or ordering by ID number — rows are emitted in the iteration order of the input `records` list.
- Escaping of pipe characters within cell values for GFM tables — cell values are rendered as-is; inputs are expected to be pipe-free.

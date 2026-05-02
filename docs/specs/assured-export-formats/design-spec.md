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

`export_do178c_rtm(records: List[IdRecord], evidence: List[EvidenceIndexEntry], metadata: Mapping[str, RequirementMetadata]) -> str` builds a GFM pipe table with a four-column header (HLR | LLR | Source code | Test case) preceded by a `# Requirements Traceability Matrix (DO-178C)` title and a prose banner identifying the generation command. It iterates REQ records; for each REQ it resolves DES children via `_index_by_satisfies`, then for each DES resolves TEST children and merges evidence locations from `_evidence_by_cited` at both the REQ and DES level. The Source-code cell is rendered by `_format_source_cell`, which consults `metadata` to render typed `EvidenceStatus` values (LINKED/MISSING/NOT_APPLICABLE/MANUAL_EVIDENCE_REQUIRED/CONFIGURATION_ARTIFACT) when no direct evidence is present, replacing the v0.1.0 bare em-dash placeholder.

**satisfies:** REQ-assured-export-formats-001

### DES-assured-export-formats-002

`export_iec_62304_matrix(records: List[IdRecord], evidence: List[EvidenceIndexEntry], metadata: Mapping[str, RequirementMetadata], software_safety_class: str = "A") -> str` builds a GFM pipe table with a three-column header (Software requirement | Software unit | Verification activity) preceded by a `# IEC 62304 Software Traceability Matrix` title and a `Software safety class: {class}` line. It iterates REQ records; for each REQ it collects evidence units from `_evidence_by_cited` at both REQ and DES level, and collects TEST children via `_index_by_satisfies` on the DES layer. One row is emitted per REQ regardless of how many DES children exist; the Source-code cell uses `_format_source_cell` for typed-status rendering when no direct evidence is present.

**satisfies:** REQ-assured-export-formats-002

### DES-assured-export-formats-003

`export_iso_26262_asil_matrix(records: List[IdRecord], evidence: List[EvidenceIndexEntry], metadata: Mapping[str, RequirementMetadata], asil_level: str = "B") -> str` builds a GFM pipe table with a four-column header (Safety requirement | Architectural element | Implementation | Verification) preceded by a `# ISO 26262 ASIL Traceability Matrix` title and an `ASIL: {level}` line. It iterates REQ records; for each REQ it resolves DES children via `_index_by_satisfies`, then for each DES resolves TEST children and merges evidence locations at both REQ and DES level. Rows without a DES child emit a stub row. The Implementation cell uses `_format_source_cell` for typed-status rendering.

**satisfies:** REQ-assured-export-formats-003

### DES-assured-export-formats-004

`export_fda_dhf_structure(records: List[IdRecord], evidence: List[EvidenceIndexEntry], metadata: Mapping[str, RequirementMetadata]) -> str` emits a structured markdown document with four `##`-level sections, each citing its regulatory clause:

- **Design inputs** (§820.30(c)): lists all REQ records as `- **{id}**: see {source}`.
- **Design outputs** (§820.30(d)): lists all DES records as `- **{id}** satisfies {satisfies}: see {source}`, followed by all `EvidenceIndexEntry` instances as `- Source code: \`{source}:{line}\` implements {cited_ids}` (kind-agnostic — Python comments, markdown HTML comments, YAML frontmatter, and satisfies-by-existence all render via the same iterator).
- **Design verification** (§820.30(f)): lists all TEST records as `- **{id}** verifies {satisfies}: see {source}`.
- **Design validation** (§820.30(g)): emits a fixed human-attestation placeholder; the framework does not auto-populate this section.

Empty sections emit an `_(no … declared)_` sentinel rather than a blank list.

The two generic non-regulatory exporters are bundled here as non-regulatory companions sharing the same four-column REQ/DES/TEST/CODE schema:

- `export_csv(records: List[IdRecord], evidence: List[EvidenceIndexEntry], metadata: Mapping[str, RequirementMetadata]) -> str` delegates to `_build_rows` and emits a CSV string with header `REQ,DES,TEST,CODE`. Commas within cell values are replaced with semicolons to avoid breaking the CSV structure.
- `export_markdown(records: List[IdRecord], evidence: List[EvidenceIndexEntry], metadata: Mapping[str, RequirementMetadata]) -> str` delegates to `_build_rows` and emits a GFM pipe table under a `# Traceability Matrix` title with columns REQ | DES | TEST | CODE.

Both generic exporters use `_build_rows`, a shared helper that iterates REQ records, resolves DES/TEST/evidence via the two private index helpers, and yields one `(req_id, des_id, test_str, code_str)` tuple per (REQ, DES) combination (stub tuple for REQs with no DES). The CODE cell uses `_format_source_cell` for typed-status rendering.

**satisfies:** REQ-assured-export-formats-004

### Type contract

All six exporters consume the v0.2.0 evidence model:

- `EvidenceIndexEntry` (defined in `plugins/sdlc-assured/scripts/assured/evidence_index.py`): a single annotation entry with `kind: EvidenceKind`, `source: str`, `line: int | None`, `cited_ids: list[str]`, optional `terms` and `facts`. Replaces the v0.1.0 `CodeIndexEntry`-only model so markdown HTML comments, YAML frontmatter, and satisfies-by-existence evidence all flow into the RTM.
- `RequirementMetadata` (defined in `plugins/sdlc-assured/scripts/assured/requirement_metadata.py`): per-REQ `evidence_status: EvidenceStatus | None`, `justification: str | None`, `related: list[str]`. Parsed from inline `**Evidence-Status:**`, `**Justification:**`, `**Related:**` fields in `requirements-spec.md`.
- `_format_source_cell(req_id, evidence_for_req, metadata)`: shared helper that renders `LINKED`, `MISSING`, `NOT_APPLICABLE`, `MANUAL_EVIDENCE_REQUIRED`, `CONFIGURATION_ARTIFACT`, or a list of `file:line` evidence locations. Surfaces `LINKED-NO-EVIDENCE` as a contradiction marker when metadata says LINKED but no `EvidenceIndexEntry` is found.

---

## Out of scope

- Incremental or cached export — each exporter rebuilds its index on every call; caching is the caller's responsibility.
- Column sorting or ordering by ID number — rows are emitted in the iteration order of the input `records` list.
- Escaping of pipe characters within cell values for GFM tables — cell values are rendered as-is; inputs are expected to be pipe-free.

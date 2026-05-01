---
feature_id: assured-export-formats
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-export-formats

**Feature-id:** assured-export-formats
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option must produce traceability artefacts that satisfy the documentary expectations of major regulatory bodies. Four standard-specific exporters produce regulator-facing matrices; two generic exporters (CSV and Markdown) cover non-regulatory consumers. All six public export functions share the same input contract (`List[IdRecord]`, `List[CodeIndexEntry]`) so that tooling can invoke any exporter without format-specific setup.

## Requirements

### REQ-assured-export-formats-001

`export_do178c_rtm` SHALL produce a Requirements Traceability Matrix conformant to DO-178C's expected column structure — HLR (high-level requirement) | LLR (low-level requirement / design) | Source code | Test case — with a document header identifying the standard.

**Module:** P1.SP1.M2

### REQ-assured-export-formats-002

`export_iec_62304_matrix` SHALL emit a Software Traceability Matrix with columns Software requirement | Software unit | Verification activity, and SHALL declare the software safety class (A, B, or C) in the document header.

**Module:** P1.SP1.M2

### REQ-assured-export-formats-003

`export_iso_26262_asil_matrix` SHALL emit an ASIL-tagged traceability matrix with columns Safety requirement | Architectural element | Implementation | Verification, and SHALL declare the declared ASIL level (A, B, C, or D) in the document header.

**Module:** P1.SP1.M2

### REQ-assured-export-formats-004

`export_fda_dhf_structure` SHALL organise traceability artefacts under the four design-control sections of 21 CFR §820.30 — Design inputs (§820.30(c)) | Design outputs (§820.30(d)) | Design verification (§820.30(f)) | Design validation (§820.30(g)) — with each section citing the relevant regulatory clause. Generic non-regulatory exporters (`export_csv`, `export_markdown`) SHALL produce a four-column REQ | DES | TEST | CODE matrix in their respective formats using the same record set, collapsing under this design element as non-regulatory companions.

**Module:** P1.SP1.M2

## Out of scope

- Schema validation of the input `IdRecord` or `CodeIndexEntry` lists — malformed records are rendered as-is; validation is the responsibility of `traceability_validators`.
- File I/O — all exporters return a string; writing to disk is the caller's responsibility.
- Human-attested validation evidence for the FDA DHF Design Validation section — the exporter emits a placeholder; population is a manual process.
- Regulatory compliance certification of the output documents — the exporters produce structurally conformant artefacts; final regulatory review is out of scope.

## Success criteria

- `export_do178c_rtm(records, code)` returns a string beginning with `# Requirements Traceability Matrix (DO-178C)` and containing a GFM table with four columns: HLR, LLR, Source code, Test case.
- `export_iec_62304_matrix(records, code, software_safety_class="B")` returns a string containing `Software safety class: B` in the header and a GFM table with columns: Software requirement, Software unit, Verification activity.
- `export_iso_26262_asil_matrix(records, code, asil_level="D")` returns a string containing `ASIL: D` in the header and a GFM table with columns: Safety requirement, Architectural element, Implementation, Verification.
- `export_fda_dhf_structure(records, code)` returns a string with four `##`-level sections citing §820.30(c), §820.30(d), §820.30(f), and §820.30(g) respectively.
- `export_csv(records, code)` returns a string whose first line is `REQ,DES,TEST,CODE` and subsequent lines contain comma-separated fields.
- `export_markdown(records, code)` returns a string beginning with `# Traceability Matrix` and containing a GFM pipe table with columns REQ, DES, TEST, CODE.

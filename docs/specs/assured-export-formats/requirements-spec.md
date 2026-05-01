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

Auditors working under DO-178C MUST be able to produce a Requirements Traceability Matrix from project artefacts in the standard-prescribed four-column format (HLR | LLR | Source code | Test case) with a document header that identifies the DO-178C standard, so that the matrix can be submitted without manual reformatting.

**Module:** P1.SP1.M2
**Evidence-Status:** MISSING
**Justification:** `export_do178c_rtm` in `export.py` implements DES-assured-export-formats-001 but lacks an `# implements:` annotation; the annotation must be added to close this cell.

### REQ-assured-export-formats-002

Auditors working under IEC 62304 MUST be able to produce a Software Traceability Matrix from project artefacts with columns (Software requirement | Software unit | Verification activity) and a document header that declares the software safety class (A, B, or C), so that the matrix meets the IEC 62304 documentary expectation without post-processing.

**Module:** P1.SP1.M2
**Evidence-Status:** MISSING
**Justification:** `export_iec_62304_matrix` in `export.py` implements DES-assured-export-formats-002 but lacks an `# implements:` annotation; the annotation must be added to close this cell.

### REQ-assured-export-formats-003

Auditors working under ISO 26262 MUST be able to produce an ASIL-tagged traceability matrix from project artefacts with columns (Safety requirement | Architectural element | Implementation | Verification) and a document header that declares the ASIL level (A, B, C, or D), so that the matrix satisfies the ISO 26262 evidence expectation without manual annotation.

**Module:** P1.SP1.M2
**Evidence-Status:** MISSING
**Justification:** `export_iso_26262_asil_matrix` in `export.py` implements DES-assured-export-formats-003 but lacks an `# implements:` annotation; the annotation must be added to close this cell.

### REQ-assured-export-formats-004

Auditors working under FDA 21 CFR §820.30 MUST be able to produce a Design History File structure from project artefacts organised under the four design-control sections (Design inputs §820.30(c) | Design outputs §820.30(d) | Design verification §820.30(f) | Design validation §820.30(g)), each citing the relevant regulatory clause. Non-regulatory consumers MUST be able to obtain the same artefact set as a four-column REQ | DES | TEST | CODE matrix in both CSV and Markdown formats.

**Module:** P1.SP1.M2
**Evidence-Status:** MISSING
**Justification:** `export_fda_dhf_structure`, `export_csv`, and `export_markdown` in `export.py` implement DES-assured-export-formats-004 but lack `# implements:` annotations; the annotations must be added to close this cell.

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

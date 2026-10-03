---
feature_id: assured-export-formats
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-export-formats

**Feature-id:** assured-export-formats
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, using in-memory `IdRecord` and `CodeIndexEntry` fixtures with no file I/O. Each test exercises the public API of the relevant exporter(s) and asserts both structural and content properties of the returned string.

---

## Tests

### TEST-assured-export-formats-001

**Title:** `export_do178c_rtm` column structure, stub-row behaviour, and typed-status rendering

**Description:** (a) Construct a minimal fixture: one REQ record (`REQ-widget-001`), one DES record that satisfies it (`DES-widget-001`, `satisfies=["REQ-widget-001"]`), one TEST record that satisfies the DES (`TEST-widget-001`, `satisfies=["DES-widget-001"]`), and one `EvidenceIndexEntry` of `kind=PYTHON_COMMENT` citing `REQ-widget-001` at `src/widget.py:10`. Call `export_do178c_rtm(records=[req, des, test], evidence=[ev], metadata={})` and assert: the returned string starts with `# Requirements Traceability Matrix (DO-178C)`; it contains `| HLR | LLR | Source code | Test case |`; the data row contains `REQ-widget-001`, `DES-widget-001`, `src/widget.py:10`, and `TEST-widget-001` in the correct column positions. (b) Call with a REQ that has no DES children and assert the output contains a stub row with `MISSING` (or the configured typed status) in the Source code column. (c) Construct a fixture where `metadata={"REQ-widget-001": RequirementMetadata(req_id="REQ-widget-001", evidence_status=EvidenceStatus.MANUAL_EVIDENCE_REQUIRED, justification="...")}` and no evidence entry; assert the Source-code cell renders `MANUAL_EVIDENCE_REQUIRED` (or the configured display form), proving typed-status flows through `_format_source_cell`.

**satisfies:** REQ-assured-export-formats-001 via DES-assured-export-formats-001

---

### TEST-assured-export-formats-002

**Title:** `export_iec_62304_matrix` safety-class header, single-row-per-REQ behaviour, and typed-status rendering

**Description:** (a) Using the same minimal fixture as TEST-001 (REQ + DES + TEST + `EvidenceIndexEntry`), call `export_iec_62304_matrix(records=records, evidence=[ev], metadata={}, software_safety_class="C")` and assert: the returned string starts with `# IEC 62304 Software Traceability Matrix`; it contains the line `Software safety class: C`; it contains `| Software requirement | Software unit | Verification activity |`; the data row contains `REQ-widget-001` in the Software requirement column, `src/widget.py:10` in Software unit, and `TEST-widget-001` in Verification activity. (b) Call with `software_safety_class="A"` (default) and assert the header line reads `Software safety class: A`. (c) Call with a REQ that has no DES and `metadata` empty: assert the row appears with `MISSING` for absent unit and activity values. (d) Call with `metadata={"REQ-widget-001": RequirementMetadata(..., evidence_status=EvidenceStatus.NOT_APPLICABLE, justification="…")}` and no evidence: assert the Software-unit cell renders `NOT_APPLICABLE`.

**satisfies:** REQ-assured-export-formats-002 via DES-assured-export-formats-002

---

### TEST-assured-export-formats-003

**Title:** `export_iso_26262_asil_matrix` ASIL header, stub-row behaviour, and typed-status rendering

**Description:** (a) Using the minimal fixture, call `export_iso_26262_asil_matrix(records=records, evidence=[ev], metadata={}, asil_level="D")` and assert: the returned string starts with `# ISO 26262 ASIL Traceability Matrix`; it contains the line `ASIL: D`; it contains `| Safety requirement | Architectural element | Implementation | Verification |`; the data row contains `REQ-widget-001`, `DES-widget-001`, `src/widget.py:10`, and `TEST-widget-001` in the correct columns. (b) Call with `asil_level="B"` (default) and assert the header reads `ASIL: B`. (c) Call with a REQ that has no DES and `metadata` empty: assert a stub row appears with `MISSING` in Architectural element, Implementation, and Verification columns. (d) Call with `metadata={"REQ-widget-001": RequirementMetadata(..., evidence_status=EvidenceStatus.CONFIGURATION_ARTIFACT, justification="…")}`: assert the Implementation cell renders `CONFIGURATION_ARTIFACT`.

**satisfies:** REQ-assured-export-formats-003 via DES-assured-export-formats-003

---

### TEST-assured-export-formats-004

**Title:** `export_fda_dhf_structure`, `export_csv`, and `export_markdown` output structure with typed evidence

**Description:** (a) Using the minimal fixture, call `export_fda_dhf_structure(records=[req, des, test], evidence=[ev], metadata={})` and assert: the string contains four `##`-level section headings — `## Design inputs`, `## Design outputs`, `## Design verification`, `## Design validation`; each section cites its regulatory clause (e.g., `§820.30(c)`); the Design inputs section lists `REQ-widget-001`; the Design outputs section lists `DES-widget-001` and `src/widget.py:10`; the Design verification section lists `TEST-widget-001`; the Design validation section contains the human-attestation placeholder text and does not list any record IDs. (b) Construct a fixture with one `EvidenceIndexEntry` of `kind=MARKDOWN_HTML_COMMENT` (e.g., from a SKILL.md `<!-- implements: -->`); call `export_fda_dhf_structure` and assert the markdown evidence appears in the Design outputs section alongside Python-comment evidence — proving the kind-agnostic iteration. (c) Call `export_fda_dhf_structure(records=[], evidence=[], metadata={})` and assert empty-list sections emit the `_(no … declared)_` sentinel. (d) Call `export_csv(records=[req, des, test], evidence=[ev], metadata={})` and assert: the first line is `REQ,DES,TEST,CODE`; the data row contains `REQ-widget-001` and `DES-widget-001` in the first two fields. (e) Call `export_markdown(records=[req, des, test], evidence=[ev], metadata={})` and assert: the first line is `# Traceability Matrix`; the output contains `| REQ | DES | TEST | CODE |`; the data row contains `REQ-widget-001` and `DES-widget-001`.

**satisfies:** REQ-assured-export-formats-004 via DES-assured-export-formats-004

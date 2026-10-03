---
feature_id: assured-code-index
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-code-index

**Feature-id:** assured-code-index
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, exercising the public API in isolation using temporary files and in-memory fixture data. No network access or filesystem side effects beyond temporary directories are permitted.

---

## Tests

### TEST-assured-code-index-001

**Title:** `parse_code_annotations` extraction correctness and missing-file safety

**Description:** (a) Write a temporary Python source file containing two `# implements:` lines — one citing `DES-assured-code-index-001` and one citing `REQ-assured-code-index-001, DES-assured-code-index-002` — plus several non-annotation lines. Call `parse_code_annotations([tmp_file], project_root=tmp_dir)` and assert: (1) exactly two `CodeIndexEntry` objects are returned; (2) the first entry has `cited_ids == ["DES-assured-code-index-001"]` and the correct 1-based line number; (3) the second entry has `cited_ids == ["REQ-assured-code-index-001", "DES-assured-code-index-002"]`; (4) both entries have `file_path` that is relative (does not contain the absolute tmp_dir prefix). (b) Call `parse_code_annotations([Path("/nonexistent/file.py")], project_root=tmp_dir)` and assert the result is an empty list without any exception being raised. (c) Write a source file with no `# implements:` lines and assert the result is an empty list.

**satisfies:** REQ-assured-code-index-001 via DES-assured-code-index-001

---

### TEST-assured-code-index-002

**Title:** `render_code_index` and `render_spec_findings` shelf-index format compliance

**Description:** (a) Construct two `CodeIndexEntry` objects with known `file_path`, `line`, `cited_ids`, `terms`, and `facts`. Call `render_code_index(entries, library_handle="test-lib")` and assert: (1) the output starts with `<!-- format_version: 1 -->`; (2) the output contains `<!-- library_handle: test-lib -->`; (3) the output does NOT contain `last_rebuilt` when `timestamp=None`; (4) the output contains `## 1.` and `## 2.` sections; (5) each section contains `**Links:**` with the expected cited IDs. (b) Call `render_code_index(entries, library_handle="test-lib", timestamp="2026-01-01T00:00:00Z")` and assert the output contains `<!-- last_rebuilt: 2026-01-01T00:00:00Z -->`. (c) Assert that two calls to `render_code_index` with the same inputs and `timestamp=None` return byte-identical strings. (d) Construct two `IdRecord` objects (one with `satisfies` set, one without). Call `render_spec_findings(records, library_handle="spec-lib")` and assert: (1) the output starts with `<!-- format_version: 1 -->`; (2) the output contains `<!-- library_handle: spec-lib -->`; (3) each section contains `**Terms:**` populated from `kind` and the feature segment; (4) `**Links:**` for the record with `satisfies` uses the `satisfies` value, and for the record without `satisfies` uses `source`.

**satisfies:** REQ-assured-code-index-002 via DES-assured-code-index-002

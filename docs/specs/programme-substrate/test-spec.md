---
feature_id: programme-substrate
module: P1.SP1.M1
granularity: test
---

# Test Specification: Programme-substrate (Assured)

**Feature-id:** programme-substrate
**Module:** P1.SP1.M1
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, exercising the public API in isolation using in-memory fixture files.

---

## Tests

### TEST-programme-substrate-001

**Title:** `parse_spec` happy-path and error paths

**Description:** Given a well-formed requirements-spec.md fixture containing one `**Feature-id:** foo` line and two `### REQ-foo-001` / `### REQ-foo-002` H3 headings, assert `parse_spec(path, "requirements")` returns a `ParsedSpec` with `feature_id == "foo"` and `declared_ids == {"REQ-foo-001", "REQ-foo-002"}`. Separately, assert that calling `parse_spec` on a file missing the `**Feature-id:**` line raises `SpecParseError` whose string representation contains the fixture file path. Assert that passing an unrecognised `phase` value raises `SpecParseError`.

**satisfies:** REQ-programme-substrate-001 via DES-programme-substrate-001

---

### TEST-programme-substrate-002

**Title:** `build_matrix`, `export_csv`, and `export_markdown` on a three-artefact fixture

**Description:** Given a temporary feature directory containing minimal requirements-spec.md (REQ-fixture-001), design-spec.md (DES-fixture-001 satisfying REQ-fixture-001), and test-spec.md (TEST-fixture-001 satisfying REQ-fixture-001 via DES-fixture-001), assert `build_matrix` returns exactly one `TraceabilityRow` with `req_id == "REQ-fixture-001"`, non-empty `des_ids`, and non-empty `test_ids`. Assert `export_csv(...)` returns a string whose first line is `REQ,DES,TEST` and whose second line contains `REQ-fixture-001`. Assert `export_markdown(...)` returns a string whose first line is `| REQ | DES | TEST |` and whose second line is `| --- | --- | --- |`.

**satisfies:** REQ-programme-substrate-002 via DES-programme-substrate-002

---

### TEST-programme-substrate-003

**Title:** Constitution Articles 12-14 content verification

**Description:** Read `plugins/sdlc-programme/CONSTITUTION.md` and assert: (1) the text contains `## Article 12` with a phrase referencing phase artefacts or phase-gate; (2) the text contains `## Article 13` with a phrase referencing cross-phase reference integrity or citations; (3) the text contains `## Article 14` with a phrase referencing review records. This test verifies that the governance document required by the Programme bundle is present and contains the prescribed headings — it does not re-validate prose quality, which is the domain of phase-review.

**satisfies:** REQ-programme-substrate-003 via DES-programme-substrate-003

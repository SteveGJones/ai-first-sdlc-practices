---
feature_id: assured-traceability-validators
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-traceability-validators

**Feature-id:** assured-traceability-validators
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, using in-memory `IdRecord` fixtures and temporary directories. No network I/O; no filesystem access beyond what the validators themselves require when testing `index_regenerability` and `annotation_format_integrity`.

---

## Tests

### TEST-assured-traceability-validators-001

**Title:** Reference-integrity validators — uniqueness, resolution, and orphan detection

**Description:**
(a) `id_uniqueness` — given two `IdRecord` objects with the same `id` in different `source` paths, assert `passed=False` and that the error string contains both source paths. Given a list with all distinct IDs, assert `passed=True` with no errors.

(b) `cited_ids_resolve` — given a record whose `satisfies` list contains `"REQ-missing-001"` and no record with that ID exists in the list, assert `passed=False` and that the error mentions `"REQ-missing-001"`. Given a fully-declared set, assert `passed=True`.

(c) `orphan_ids` — given a REQ record that does not appear in any `satisfies` list, assert `passed=True` (not a blocking failure) and that `warnings` is non-empty and contains the orphan ID. Given a record that IS cited, assert `passed=True` with an empty `warnings` list. Assert that a TEST-kind record that is never cited does NOT appear in `warnings` (TEST and CODE are leaves).

**satisfies:** REQ-assured-traceability-validators-001 via DES-assured-traceability-validators-001

---

### TEST-assured-traceability-validators-002

**Title:** Directional-coverage validators — forward links and backward coverage

**Description:**
(a) `forward_link_integrity` — given a DES record with `satisfies=[]`, assert `passed=False` and that the error mentions "no satisfies links". Given a TEST record with `satisfies=[]`, assert `passed=False`. Given a record whose `satisfies` list references an ID not in the registry, assert `passed=False` with an error mentioning "missing target". Given a fully-linked REQ→DES→TEST chain, assert `passed=True`.

(b) `backward_coverage` — given a REQ record that has no DES record citing it, assert `passed=False` and that the error mentions the REQ ID. Given a DES record that has no TEST record citing it, assert `passed=False` and that the error mentions the DES ID. Given a fully-covered chain where a DES cites the REQ and a TEST cites the DES, assert `passed=True`.

**satisfies:** REQ-assured-traceability-validators-002 via DES-assured-traceability-validators-002

---

### TEST-assured-traceability-validators-003

**Title:** `index_regenerability` — idempotency and missing-file detection

**Description:**
(a) Given a temporary file whose content matches the string returned by the regenerate callable, assert `passed=True` with no errors.

(b) Given a temporary file whose content differs from the regenerate callable's return value by one character, assert `passed=False` and that the error mentions `"not idempotent"` and the file path.

(c) Given a path that does not name an existing file, assert `passed=False` and that the error mentions `"does not exist"` and the path.

The `regenerate` callable should be a plain lambda returning a string for all three cases — the test does not invoke any registry-building logic.

**satisfies:** REQ-assured-traceability-validators-003 via DES-assured-traceability-validators-003

---

### TEST-assured-traceability-validators-004

**Title:** `annotation_format_integrity` — malformed tokens and undeclared IDs

**Description:**
(a) Given a temporary Python file containing the line `# implements: REQ-my-feat-001` and a `declared_ids` set that includes `"REQ-my-feat-001"`, assert `passed=True` with no errors.

(b) Given the same file but `declared_ids` is empty (does not contain `"REQ-my-feat-001"`), assert `passed=False` and that the error mentions `"REQ-my-feat-001"` and `"not declared"`.

(c) Given a file containing `# implements: NOTANID!!!`, assert `passed=False` and that the error mentions `"malformed annotation token"`.

(d) Given a file with no `# implements:` lines at all, assert `passed=True` with no errors regardless of the `declared_ids` set.

(e) Given a path that does not exist on disk, assert the function returns `passed=True` without raising (non-existent files are silently skipped).

**satisfies:** REQ-assured-traceability-validators-004 via DES-assured-traceability-validators-004

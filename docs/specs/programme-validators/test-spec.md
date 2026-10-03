---
feature_id: programme-validators
module: P1.SP1.M1
granularity: test
---

# Test Specification: Programme-validators (Assured)

**Feature-id:** programme-validators
**Module:** P1.SP1.M1
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, exercising the public gate API via
temporary fixture directories created in-memory using `tmp_path`.

---

## Tests

### TEST-programme-validators-001

**Title:** `requirements_gate` happy-path and failure paths

**Description:** Given a temporary feature directory containing a well-formed
`requirements-spec.md` fixture with `feature_id=test-feat` and one
`### REQ-test-feat-001` heading, assert `requirements_gate(tmp, "test-feat")` returns
`GateResult(passed=True, errors=[])`. Separately: (a) given a missing spec file, assert
the gate returns `passed=False` with an error mentioning `requirements-spec.md`; (b)
given a spec with `feature_id=wrong`, assert the gate returns `passed=False` with a
feature-id mismatch error; (c) given a spec with no REQ-ID headings, assert the gate
returns `passed=False` with a "no REQ-IDs" error.

**satisfies:** REQ-programme-validators-001 via DES-programme-validators-001

---

### TEST-programme-validators-002

**Title:** `design_gate` cross-reference validation and review-record check

**Description:** Given a temporary feature directory with valid `requirements-spec.md`
(REQ-tf-001) and `design-spec.md` (DES-tf-001 satisfying REQ-tf-001) and a
`reviews/design-review-alice.md` file, assert `design_gate(tmp, "tf")` returns
`GateResult(passed=True)`. Separately: (a) given a `design-spec.md` that references
`REQ-tf-999` (absent from requirements-spec.md), assert the gate returns `passed=False`
with an unresolved-reference error; (b) given a feature directory with no
`reviews/design-review-*.md` file, assert the gate returns `passed=False` with a
review-record error; (c) given a missing `requirements-spec.md`, assert the gate
returns `passed=False` immediately with a prerequisite error.

**satisfies:** REQ-programme-validators-002 via DES-programme-validators-002

---

### TEST-programme-validators-003

**Title:** `test_gate` cross-reference validation and review-record check

**Description:** Given a temporary feature directory with valid `requirements-spec.md`
(REQ-tf-001), `design-spec.md` (DES-tf-001 satisfying REQ-tf-001), `test-spec.md`
(TEST-tf-001 satisfying REQ-tf-001 via DES-tf-001), and a
`reviews/test-review-alice.md` file, assert `test_gate(tmp, "tf")` returns
`GateResult(passed=True)`. Separately: (a) given a `test-spec.md` referencing
`DES-tf-999` (absent), assert the gate returns `passed=False` with an
unresolved-DES-reference error; (b) given a `test-spec.md` referencing `REQ-tf-999`
(absent), assert the gate returns `passed=False` with an unresolved-REQ-reference
error; (c) given a feature directory with no `reviews/test-review-*.md` file, assert
the gate returns `passed=False` with a review-record error.

**satisfies:** REQ-programme-validators-003 via DES-programme-validators-003

---

### TEST-programme-validators-004

**Title:** `code_gate` annotation presence and TEST-ID resolution

**Description:** Given a temporary feature directory with valid `test-spec.md`
(TEST-tf-001) and `code_text = "# implements: TEST-tf-001\ndef foo(): pass"`, assert
`code_gate(tmp, "tf", code_text)` returns `GateResult(passed=True)`. Separately: (a)
given `code_text` with no `# implements:` line, assert the gate returns `passed=False`
with a "no annotation" error; (b) given `code_text` with
`# implements: TEST-tf-999` (absent from test-spec.md), assert the gate returns
`passed=False` with an unresolved-TEST-ID error; (c) given a missing `test-spec.md`,
assert the gate returns `passed=False` immediately with a prerequisite error.

**satisfies:** REQ-programme-validators-004 via DES-programme-validators-004

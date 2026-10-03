---
feature_id: programme-validators
module: P1.SP1.M1
granularity: design
---

# Design Specification: Programme-validators (Assured)

**Feature-id:** programme-validators
**Module:** P1.SP1.M1
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Four design units correspond to the four phase-gate functions in
`plugins/sdlc-programme/scripts/programme/gates.py`. Each unit describes the logic
applied by one gate function to determine pass/fail and populate the `GateResult`
errors list.

---

## Design

### DES-programme-validators-001

`requirements_gate(feature_dir, feature_id)` calls `_try_parse` on
`requirements-spec.md` with `phase="requirements"`. A parse failure immediately sets
`passed=False` with the parse error message. On successful parse the function checks
two conditions: (a) `parsed.feature_id` matches the supplied `feature_id`; (b)
`parsed.declared_ids` is non-empty. Each failing condition appends a distinct error
string. The gate returns the `GateResult` after evaluating both conditions regardless
of which failed first.

**satisfies:** REQ-programme-validators-001

### DES-programme-validators-002

`design_gate(feature_dir, feature_id)` calls `_try_parse` on both
`requirements-spec.md` (prerequisite) and `design-spec.md`. If either parse fails the
function returns immediately with `passed=False`. On successful parse the function
checks: (a) DES spec `feature_id` matches supplied `feature_id`; (b) DES spec declares
at least one DES-ID; (c) every reference in `des_parsed.references` that starts with
`"REQ-"` resolves to a declared ID in `req_parsed.declared_ids`; (d) a review record
exists at `<feature_dir>/reviews/design-review-*.md` (checked via
`_has_review_record(feature_dir, "design")`). Each failing condition appends a distinct
error string. All four conditions are evaluated before returning.

**satisfies:** REQ-programme-validators-002

### DES-programme-validators-003

`test_gate(feature_dir, feature_id)` calls `_try_parse` on all three prerequisite
specs: `requirements-spec.md`, `design-spec.md`, and `test-spec.md`. If any parse
fails the function returns immediately. On successful parse the function checks: (a)
TEST spec `feature_id` matches supplied `feature_id`; (b) TEST spec declares at least
one TEST-ID; (c) every `"REQ-"` reference in `test_parsed.references` resolves in
`req_parsed.declared_ids`; (d) every `"DES-"` reference in `test_parsed.references`
resolves in `des_parsed.declared_ids`; (e) a review record exists at
`<feature_dir>/reviews/test-review-*.md` (checked via
`_has_review_record(feature_dir, "test")`). All conditions are evaluated before
returning.

**satisfies:** REQ-programme-validators-003

### DES-programme-validators-004

`code_gate(feature_dir, feature_id, code_text)` calls `_try_parse` on
`test-spec.md`. A parse failure returns immediately. The function then scans
`code_text` using `_TEST_ID_REF_RE` to locate `# implements:` lines and
`_TEST_ID_RE` to extract TEST-IDs from each match. If `cited_test_ids` is empty the
gate fails with a "no annotation" error. Otherwise every cited TEST-ID is checked
against `test_parsed.declared_ids`; any unresolved ID appends an error and sets
`passed=False`.

**satisfies:** REQ-programme-validators-004

---

## Out of scope

- Caching parsed specs across gate invocations — specs are re-parsed on every call;
  build tooling is responsible for call frequency.
- Cross-gate state sharing — each gate function is stateless and self-contained.

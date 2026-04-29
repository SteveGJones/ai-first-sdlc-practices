# Test Specification: <Feature Title>

**Feature-id:** <feature-id>
**Status:** Draft
**Author:** <Your name>
**Created:** <YYYY-MM-DD>
**Requirements-spec:** [requirements-spec.md](requirements-spec.md)
**Design-spec:** [design-spec.md](design-spec.md)

---

## Testing approach

<!-- HOW the feature will be verified. Describe the test pyramid balance: unit tests, integration tests, end-to-end. Cite the relevant DESs by ID. -->

## Test cases

<!-- Each test case is a discrete verifiable statement with a stable ID. Numbering: TEST-<feature-id>-NNN starting at 001. The "satisfies" line is mandatory and references one or more REQ-IDs and DES-IDs. -->

### TEST-<feature-id>-001 — <short title>
**satisfies:** REQ-<feature-id>-001 via DES-<feature-id>-001

**Setup:** <prerequisite state>

**Action:** <what the test does>

**Expected result:** <what passes>

### TEST-<feature-id>-002 — <short title>
**satisfies:** REQ-<feature-id>-002 via DES-<feature-id>-002

**Setup:** <prerequisite state>

**Action:** <what the test does>

**Expected result:** <what passes>

<!-- Add more test cases. Each must satisfy at least one REQ + DES. Code annotations will reference these TEST-IDs via "# implements: TEST-..." -->

## Test data and fixtures

<!-- Any fixtures, mocks, or test data required. -->

## Out of scope (this test plan)

<!-- Verification deliberately not part of this test plan — e.g., manual QA passes that the team performs separately. -->

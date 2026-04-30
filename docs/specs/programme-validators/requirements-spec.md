---
feature_id: programme-validators
module: P1.SP1.M1
granularity: requirement
---

# Requirements Specification: Programme-validators (Assured)

**Feature-id:** programme-validators
**Module:** P1.SP1.M1
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Programme SDLC option enforces a formal waterfall phase-gate sequence. Four gate
functions enforce passage criteria at each phase boundary: requirements, design, test,
and code. Without these validators a Programme-commissioned project cannot demonstrate
that each phase artefact is structurally sound and properly reviewed before downstream
work begins.

## Requirements

### REQ-programme-validators-001

The requirements gate SHALL pass if and only if the REQ spec file parses without error
and contains at least one non-stub requirement entry (i.e. at least one declared
REQ-ID heading).

**Module:** P1.SP1.M1

### REQ-programme-validators-002

The design gate SHALL pass if and only if the DES spec file parses without error, every
REQ-ID cited in the DES spec exists in the REQ spec, and a design-phase review record
exists in the feature directory.

**Module:** P1.SP1.M1

### REQ-programme-validators-003

The test gate SHALL pass if and only if the TEST spec file parses without error, every
DES-ID cited in the TEST spec exists in the DES spec, every REQ-ID cited in the TEST
spec exists in the REQ spec, and a test-phase review record exists in the feature
directory.

**Module:** P1.SP1.M1

### REQ-programme-validators-004

The code gate SHALL pass if and only if the supplied code text contains at least one
`# implements:` annotation referencing a TEST-ID, and every TEST-ID cited in those
annotations exists in the TEST spec file.

**Module:** P1.SP1.M1

## Out of scope

- Weak or vague reference detection (prose-quality checks) — handled by the
  `phase-review` skill, not the gate validators.
- Remote artefact retrieval — all phase artefacts are local filesystem files.
- Partial-pass or warning states — each gate returns a binary pass/fail with a
  structured error list; graduated severity is out of scope.

## Success criteria

- `requirements_gate` on a feature directory containing a valid requirements-spec.md
  with at least one REQ-ID heading returns `GateResult(passed=True)`.
- `requirements_gate` on a feature directory with a missing or malformed
  requirements-spec.md returns `GateResult(passed=False)` with a non-empty errors list.
- `design_gate` on a feature directory where design-spec.md cites a REQ-ID not present
  in requirements-spec.md returns `GateResult(passed=False)`.
- `design_gate` on a feature directory lacking a `reviews/design-review-*.md` file
  returns `GateResult(passed=False)`.
- `test_gate` on a feature directory where test-spec.md cites a DES-ID not present in
  design-spec.md returns `GateResult(passed=False)`.
- `test_gate` on a feature directory lacking a `reviews/test-review-*.md` file returns
  `GateResult(passed=False)`.
- `code_gate` on code text with no `# implements:` annotation returns
  `GateResult(passed=False)`.
- `code_gate` on code text referencing a TEST-ID absent from test-spec.md returns
  `GateResult(passed=False)`.

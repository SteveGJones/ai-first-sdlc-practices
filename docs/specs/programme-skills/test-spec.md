---
feature_id: programme-skills
module: P1.SP1.M1
granularity: test
---

# Test Specification: Programme-skills (Assured)

**Feature-id:** programme-skills
**Module:** P1.SP1.M1
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are integration-level: each test exercises the SKILL.md
script logic by inspecting its documented step sequence and the contracts it delegates
to (gate functions, bundle installer, traceability exporters). Where the skill
orchestrates agent dispatch (phase-review), the test verifies the dispatch contract
rather than the agent's output content.

---

## Tests

### TEST-programme-skills-001

**Title:** `commission-programme` installs bundle and writes commissioning record

**Description:** Given a temporary project directory and a bundle directory containing
a valid `manifest.yaml`, invoke the `commission-programme` skill steps with `--level
production`. Assert: (a) `install_bundle` is called with the correct bundle directory,
project directory, and manifest; (b) a `CommissioningRecord` is written to
`.sdlc/team-config.json` with `sdlc_option="programme"`, `sdlc_level="production"`,
and a non-empty `commissioned_at` timestamp; (c) the skill prints a Done report
containing installed file count and the commissioning record path; (d) given an invalid
level value (e.g. `solo`), the skill exits non-zero before calling `install_bundle`.

**satisfies:** REQ-programme-skills-001 via DES-programme-skills-001

---

### TEST-programme-skills-002

**Title:** `phase-init` creates spec from template and refuses to overwrite

**Description:** Given a temporary feature directory and a plugin template for
`requirements`, invoke the `phase-init` skill steps with `requirements <feature-id>`.
Assert: (a) `docs/specs/<feature-id>/requirements-spec.md` is created and its content
contains the feature-id substituted in place of `<feature-id>` placeholders; (b)
invoking the same skill steps a second time exits non-zero and does not modify the
existing file; (c) given a `<phase>` value of `code` (invalid), the skill exits
non-zero; (d) given a `<feature-id>` value containing uppercase letters (invalid
format), the skill exits non-zero.

**satisfies:** REQ-programme-skills-002 via DES-programme-skills-002

---

### TEST-programme-skills-003

**Title:** `phase-gate` delegates to correct gate function and surfaces pass/fail

**Description:** Mock `sdlc_programme_scripts.programme.gates`. Invoke `phase-gate`
steps with `requirements <feature-id>` against a feature directory where
`requirements_gate` is mocked to return `GateResult(passed=True, errors=[])`. Assert:
(a) the skill prints a PASS line containing the gate name and feature-id; (b) the skill
exits zero. Separately: (a) mock `requirements_gate` to return
`GateResult(passed=False, errors=["missing REQ-IDs"])`, assert the skill prints a FAIL
line and the error text and exits non-zero; (b) invoke with `phase=code` and no
code-file-glob argument, assert the skill exits non-zero before dispatching the gate;
(c) invoke with an invalid phase value, assert the skill exits non-zero.

**satisfies:** REQ-programme-skills-003 via DES-programme-skills-003

---

### TEST-programme-skills-004

**Title:** `phase-review` verifies spec existence, dispatches agent, and checks output

**Description:** Given a feature directory containing
`docs/specs/<feature-id>/design-spec.md`, invoke the `phase-review` skill steps with
`design <feature-id>`. Assert: (a) the reviewer agent dispatched is
`sdlc-team-common:solution-architect`; (b) the prompt includes `coverage`, `soundness`,
`completeness`, and `out-of-scope concerns` as review dimensions; (c) after the
dispatch, if `reviews/design-review-solution-architect.md` exists the skill exits zero
and stages the file; (d) if the review file is absent after dispatch, the skill exits
non-zero with an error. Separately: given a feature directory with no
`design-spec.md`, assert the skill exits non-zero before dispatching the agent.

**satisfies:** REQ-programme-skills-004 via DES-programme-skills-004

---

### TEST-programme-skills-005

**Title:** `traceability-export` produces matrix with no silent omissions

**Description:** Given a temporary feature directory with `requirements-spec.md`
(REQ-tf-001, REQ-tf-002), `design-spec.md` (DES-tf-001 satisfying REQ-tf-001;
REQ-tf-002 has no satisfying DES entry), and `test-spec.md` (TEST-tf-001 satisfying
REQ-tf-001 via DES-tf-001). Invoke `traceability-export csv tf`. Assert: (a) the
output file at `docs/specs/tf/traceability.csv` contains a `REQ,DES,TEST` header; (b)
REQ-tf-001 appears with DES-tf-001 and TEST-tf-001 in its row; (c) REQ-tf-002 appears
with `—` (or empty) in DES and TEST columns — it is not omitted; (d) no other rows
appear. Separately: mock `export_csv` to raise `TraceabilityError("broken")`, assert
the skill exits non-zero and prints the error text.

**satisfies:** REQ-programme-skills-005 via DES-programme-skills-005

---
feature_id: assured-decomposition-validators
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-decomposition-validators

**Feature-id:** assured-decomposition-validators
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, using in-memory `SpecArtefact`, `CodeAnnotation`, `ImportEdge`, and `Decomposition` fixtures constructed programmatically. No network I/O; no filesystem access. All five validators must be deterministic given the same inputs.

---

## Tests

### TEST-assured-decomposition-validators-001

**Title:** `req_has_module_assignment` — missing assignment and undeclared module

**Description:**

(a) Given a `SpecArtefact` with `ids=["REQ-auth-001"]`, `module=None`, `path="docs/specs/auth/requirements-spec.md"`, and a `Decomposition` declaring one module `P1.SP1.M1` at path `src/auth/`, assert `passed=False` and that the error mentions `"REQ-auth-001"`, `"requirements-spec.md"`, and `"no module assignment"`.

(b) Given a `SpecArtefact` with `ids=["P1.SP1.M9.REQ-auth-001"]` (positional prefix resolving to `P1.SP1.M9`) and a `Decomposition` that does not declare `P1.SP1.M9`, assert `passed=False` and that the error mentions `"P1.SP1.M9"` and `"not declared in programs.yaml"`.

(c) Given a `SpecArtefact` with `ids=["REQ-auth-001"]`, `module="P1.SP1.M1"`, and a `Decomposition` that declares `P1.SP1.M1`, assert `passed=True` with no errors.

(d) Given a `SpecArtefact` with `ids=["DES-auth-001"]` (not a REQ), assert `passed=True` with no errors regardless of module assignment — non-REQ IDs are skipped.

**satisfies:** REQ-assured-decomposition-validators-001 via DES-assured-decomposition-validators-001

---

### TEST-assured-decomposition-validators-002

**Title:** `code_annotation_maps_to_module` — out-of-module and in-module annotations

**Description:**

(a) Given a `CodeAnnotation(file_path="src/api/handler.py", line=10, cited_ids=["DES-auth-001"])`, a `spec_module_lookup={"DES-auth-001": "P1.SP1.M1"}`, and a `Decomposition` declaring `P1.SP1.M1` with `paths=["src/core/"]`, assert `passed=False` and that the error mentions `"src/api/handler.py"`, `"DES-auth-001"`, and `"src/core/"`.

(b) Given the same annotation but with `paths=["src/api/"]` declared for `P1.SP1.M1`, assert `passed=True` with no errors.

(c) Given a `CodeAnnotation` whose `cited_ids` contains an ID absent from `spec_module_lookup`, assert `passed=True` with no errors — unresolved citations are out of scope for this validator (they are caught by `cited_ids_resolve`).

(d) Given an empty `annotations` list, assert `passed=True` with no errors.

**satisfies:** REQ-assured-decomposition-validators-002 via DES-assured-decomposition-validators-002

---

### TEST-assured-decomposition-validators-003

**Title:** `visibility_rule_enforcement` — strict mode blocking, advisory mode warning, self-edges ignored

**Description:**

(a) `mode="strict"` — given an `ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")` and a `Decomposition` whose visibility block declares `P1.SP1.M1` may only import `P1.SP1.M3`, assert `passed=False` and that the error mentions `"P1.SP1.M1 → P1.SP1.M2"`.

(b) `mode="advisory"` — given the same undeclared edge, assert `passed=True` with a warning mentioning `"P1.SP1.M1 → P1.SP1.M2"` and an empty `errors` list.

(c) Given a declared edge `P1.SP1.M1 → P1.SP1.M3` in both modes, assert `passed=True` with no errors and no warnings.

(d) Given a self-edge `ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M1")`, assert `passed=True` with no errors and no warnings in either mode — self-edges are unconditionally skipped.

(e) Given an empty `edges` list, assert `passed=True` with no errors and no warnings.

**satisfies:** REQ-assured-decomposition-validators-003 via DES-assured-decomposition-validators-003

---

### TEST-assured-decomposition-validators-004

**Title:** `anaemic_context_detection` — scatter threshold enforcement and evidence reporting

**Description:**

(a) High scatter (fires) — given a module `P1.SP1.M1` with `paths=["src/core/"]`, and 3 annotations on `src/api/x.py` (out-of-module) and 1 annotation on `src/core/y.py` (in-module), all citing IDs in `P1.SP1.M1`, assert `passed=False` and that the error mentions `"P1.SP1.M1"`, the scatter percentage (75%), the counts (3/4), and at least one of the out-of-module file paths as evidence.

(b) Low scatter (does not fire) — given the same module with 1 out-of-module annotation and 9 in-module annotations (10% scatter, below default 20% threshold), assert `passed=True` with no errors.

(c) Threshold boundary — given exactly 20% scatter (1 out of 5), assert `passed=True` (the condition is `>` threshold, not `>=`).

(d) Given an empty `annotations` list, assert `passed=True` with no errors.

(e) Given annotations whose cited IDs are absent from `spec_module_lookup`, assert `passed=True` with no errors — unknown IDs are skipped.

**satisfies:** REQ-assured-decomposition-validators-004 via DES-assured-decomposition-validators-004

---

### TEST-assured-decomposition-validators-005

**Title:** `granularity_match` — unannotated REQs in requirement-granularity modules warned; others not

**Description:**

(a) Given `declared_reqs=["REQ-auth-001"]`, no annotations citing `"REQ-auth-001"`, `spec_module_lookup={"REQ-auth-001": "P1.SP1.M1"}`, and a `Decomposition` where `P1.SP1.M1` has `granularity="requirement"`, assert `passed=True` (non-blocking) and that `warnings` is non-empty and contains `"REQ-auth-001"`.

(b) Given the same setup but one annotation whose `cited_ids` includes `"REQ-auth-001"`, assert `passed=True` with an empty `warnings` list.

(c) Given `P1.SP1.M1` has `granularity="subsystem"` (not `"requirement"`), assert `passed=True` with an empty `warnings` list — the validator is scoped to `granularity=requirement` modules only.

(d) Given a REQ whose module is absent from `spec_module_lookup`, assert `passed=True` with an empty `warnings` list — unresolved REQs are skipped.

(e) Given an empty `declared_reqs` list, assert `passed=True` with no warnings.

**satisfies:** REQ-assured-decomposition-validators-005 via DES-assured-decomposition-validators-005

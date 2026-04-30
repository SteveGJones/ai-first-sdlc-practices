---
feature_id: assured-decomposition-validators
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-decomposition-validators

**Feature-id:** assured-decomposition-validators
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option declares a module decomposition in `programs.yaml`. Five validators in `decomposition.py` enforce the structural integrity of that declaration: they verify REQ module assignments, code annotation locality, cross-module visibility, bounded-context concentration, and granularity coverage. Without these validators, the decomposition declaration is aspirational rather than enforced — an auditor cannot mechanically confirm that source artefacts respect the declared module boundaries.

## Requirements

### REQ-assured-decomposition-validators-001

`req_has_module_assignment` SHALL report a blocking error for any REQ ID that has no module assignment (neither a positional prefix nor an explicit `module` field in its enclosing spec artefact) AND SHALL report a blocking error for any REQ ID whose resolved module is not declared in `programs.yaml`.

**Module:** P1.SP1.M2

### REQ-assured-decomposition-validators-002

`code_annotation_maps_to_module` SHALL report a blocking error for each `# implements:` annotation whose annotating file path is not under any of the cited spec ID's declared module paths as listed in `programs.yaml`.

**Module:** P1.SP1.M2

### REQ-assured-decomposition-validators-003

`visibility_rule_enforcement` SHALL emit blocking errors (when `mode="strict"`) or non-blocking warnings (when `mode="advisory"`) for every cross-module import edge whose target module is not listed in the `from_module`'s declared `visibility:` block in `programs.yaml`; self-edges (same source and target module) SHALL be ignored.

**Module:** P1.SP1.M2

### REQ-assured-decomposition-validators-004

`anaemic_context_detection` SHALL emit a blocking error for any module whose proportion of `# implements:` annotations that fall outside its declared paths exceeds the configured scatter threshold (default 20%), including evidence of which annotations are out-of-module; modules whose scatter proportion is at or below the threshold SHALL produce no error for that module.

**Module:** P1.SP1.M2

### REQ-assured-decomposition-validators-005

`granularity_match` SHALL emit a non-blocking warning for every declared REQ ID whose enclosing module has `granularity=requirement` and which has no `# implements:` annotation in any code file; REQs in modules with other granularity values SHALL NOT trigger this warning.

**Module:** P1.SP1.M2

## Out of scope

- Parsing `programs.yaml` from disk — that is the responsibility of `parse_programs_yaml` (infrastructure, not directly REQ'd here).
- Providing a default decomposition when no `programs.yaml` exists — that is the responsibility of `default_decomposition` (infrastructure, not directly REQ'd here).
- Determining which source files contain annotations — callers are responsible for supplying `CodeAnnotation` lists; the validators do not scan the filesystem.
- Cross-repository or remote module resolution — all validators operate only on the `Decomposition` object supplied by the caller.

## Success criteria

- `req_has_module_assignment` given a `SpecArtefact` carrying `"REQ-auth-001"` with no module field and no positional prefix returns `passed=False` with an error mentioning the ID and the path.
- `req_has_module_assignment` given a REQ ID whose positional prefix resolves to a module not in `programs.yaml` returns `passed=False` with an error mentioning the undeclared module name.
- `code_annotation_maps_to_module` given an annotation on `src/api/auth.py` citing a DES whose module declares `paths: [src/core/]` returns `passed=False` with an error mentioning the file path and the allowed paths.
- `visibility_rule_enforcement` given `mode="strict"` and an edge from M1 to M2 where M1's visibility block does not include M2 returns `passed=False` with a blocking error; given `mode="advisory"` the same edge returns `passed=True` with a warning.
- `anaemic_context_detection` given a module with 3 out-of-module annotations and 1 in-module annotation (75% scatter, above default 20% threshold) returns `passed=False` with an error; given a module with 1 out-of-module annotation and 9 in-module annotations (10% scatter, below threshold) returns `passed=True`.
- `granularity_match` given a REQ in a `granularity=requirement` module with no annotation returns `passed=True` (non-blocking) with a warning; given the same REQ with one annotation returns `passed=True` with no warning.

---
feature_id: assured-decomposition-validators
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-decomposition-validators

**Feature-id:** assured-decomposition-validators
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Five design units map to the five requirements. All five validators accept typed input dataclasses (`SpecArtefact`, `CodeAnnotation`, `ImportEdge`, `Decomposition`) and return `DecompositionValidatorResult(passed: bool, errors: List[str], warnings: List[str])`. None perform filesystem I/O beyond what is passed through their arguments.

`parse_programs_yaml` and `default_decomposition` are infrastructure functions used by callers to produce the `Decomposition` object passed to these validators; they are not design units for this feature.

Note: DES-002 (`code_annotation_maps_to_module`) and DES-004 (`anaemic_context_detection`) address related but distinct failure modes: DES-002 is a per-annotation locality check (every out-of-module annotation is a blocking error), while DES-004 is a module-level concentration check (only when the module's scatter ratio exceeds the threshold does it fire). See F-006 in `research/phase-f-dogfood-findings.md` for a recorded finding on the absence of a "see also" cross-reference mechanism between related REQs.

---

## Design

### DES-assured-decomposition-validators-001

`req_has_module_assignment(specs: List[SpecArtefact], decomp: Decomposition) -> DecompositionValidatorResult`

1. Build `declared = _all_module_ids(decomp)` — the set of all `"P.SP.M"` strings across the decomposition.
2. For each `spec` in `specs`, for each `id_` in `spec.ids`:
   a. Skip IDs that do not begin with `"REQ"` (other artefact types do not require explicit module assignment at this level).
   b. Resolve module: try `_module_from_positional_id(id_)` first; fall back to `spec.module`.
   c. If the resolved module is `None`, append an error: `"<id_> (in <spec.path>) has no module assignment"`.
   d. If the resolved module is not in `declared`, append an error: `"<id_> (in <spec.path>) is assigned to module '<module>' which is not declared in programs.yaml"`.
3. Return `DecompositionValidatorResult(passed=not errors, errors=errors)`.

**satisfies:** REQ-assured-decomposition-validators-001

### DES-assured-decomposition-validators-002

`code_annotation_maps_to_module(annotations: List[CodeAnnotation], decomp: Decomposition, spec_module_lookup: dict) -> DecompositionValidatorResult`

`spec_module_lookup` maps spec IDs (REQ, DES, TEST) to their declared module string.

1. Build `paths_by_module = _module_paths(decomp)` — a dict mapping module ID to its list of path prefixes.
2. For each `ann` in `annotations`, for each `cited` in `ann.cited_ids`:
   a. Look up `module = spec_module_lookup.get(cited)`. If `None`, skip (unresolved citations are caught by `cited_ids_resolve`).
   b. Look up `allowed_paths = paths_by_module.get(module, [])`.
   c. Call `_file_under_paths(ann.file_path, allowed_paths)`. If `False`, append an error: `"<ann.file_path>:<ann.line> cites <cited> (module <module>) but file is not under any declared path: <allowed_paths>"`.
3. Return `DecompositionValidatorResult(passed=not errors, errors=errors)`.

**satisfies:** REQ-assured-decomposition-validators-002

### DES-assured-decomposition-validators-003

`visibility_rule_enforcement(edges: List[ImportEdge], decomp: Decomposition, mode: str = "advisory") -> DecompositionValidatorResult`

1. Build `declared: dict[str, set[str]]` from `decomp.visibility`: `declared[v.from_module] = set(v.to_modules)` for each `VisibilityRule`.
2. For each `edge` in `edges`:
   a. If `edge.from_module == edge.to_module`, skip (self-edges are not cross-module).
   b. Look up `allowed = declared.get(edge.from_module, set())`.
   c. If `edge.to_module not in allowed`, append to `issues`: `"undeclared visibility: <from> → <to>"`.
3. If `mode == "strict"`: return `DecompositionValidatorResult(passed=not issues, errors=issues)`.
4. Otherwise (advisory): return `DecompositionValidatorResult(passed=True, warnings=issues)`.

**satisfies:** REQ-assured-decomposition-validators-003

### DES-assured-decomposition-validators-004

`anaemic_context_detection(annotations: List[CodeAnnotation], decomp: Decomposition, spec_module_lookup: dict, scatter_threshold: float = 0.20) -> DecompositionValidatorResult`

This validator operates at the module level, accumulating counts across all annotations before deciding whether to fire. It differs from DES-002 in that a single out-of-module annotation does not produce an error; only a module-wide scatter ratio exceeding `scatter_threshold` does.

1. Build `paths_by_module = _module_paths(decomp)`.
2. For each `ann` in `annotations`, for each `cited` in `ann.cited_ids`:
   a. Look up `module = spec_module_lookup.get(cited)`. If `None`, skip.
   b. Look up `allowed_paths = paths_by_module.get(module, [])`.
   c. If `_file_under_paths(ann.file_path, allowed_paths)` is `True`: increment `inside[module]`.
   d. Otherwise: append `(ann.file_path, ann.line, cited)` to `outside[module]`.
3. For each `module` in `outside`:
   a. Compute `stray_count = len(outside[module])`, `total = inside.get(module, 0) + stray_count`, `ratio = stray_count / total` (use `1.0` if `total == 0`).
   b. If `ratio > scatter_threshold`, append an error: `"anaemic context: module <module> has <pct>% of its annotations (<stray>/<total>) outside its declared paths — evidence: <file>:<line> implements <id>; ..."`.
4. Return `DecompositionValidatorResult(passed=not errors, errors=errors)`.

**satisfies:** REQ-assured-decomposition-validators-004

### DES-assured-decomposition-validators-005

`granularity_match(declared_reqs: List[str], annotations: List[CodeAnnotation], decomp: Decomposition, spec_module_lookup: dict[str, str]) -> DecompositionValidatorResult`

1. Build `cited: set[str]` — the union of all `ann.cited_ids` across all annotations.
2. Build `granularity_by_module: dict[str, str]` mapping each module's fully-qualified ID to its `granularity` field.
3. For each `req` in `declared_reqs`:
   a. Look up `module = spec_module_lookup.get(req)`. If `None`, skip (unresolved; caught by other validators).
   b. If `granularity_by_module.get(module) != "requirement"`, skip (not in scope for this validator).
   c. If `req not in cited`, append a warning: `"under-specified: <req> (module <module>) has no `# implements:` annotation"`.
4. Return `DecompositionValidatorResult(passed=True, warnings=warnings)` — this validator is always non-blocking.

**satisfies:** REQ-assured-decomposition-validators-005

---

## Out of scope

- Configurable severity overrides for individual validators — the block/warn distinction is fixed per validator; no per-caller configuration knob is provided in this design.
- Aggregation or de-duplication of results across multiple validator calls — callers are responsible for combining `DecompositionValidatorResult` objects.
- Detection of annotations in non-Python files — `CodeAnnotation` objects are produced by the caller's scanner; the validators only consume the pre-parsed list. (See F-001 in `research/phase-f-dogfood-findings.md`.)
- Sub-file path scoping (line ranges or section anchors within a file) — the `paths` field in `programs.yaml` covers directory prefixes only. (See F-002 in `research/phase-f-dogfood-findings.md`.)

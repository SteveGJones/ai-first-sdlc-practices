---
feature_id: assured-skills
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-skills

**Feature-id:** assured-skills
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option ships eight skills that form the day-to-day working surface for teams operating under Method 2. Seven of those skills — `req-add`, `req-link`, `code-annotate`, `module-bound-check`, `kb-codeindex`, `change-impact-annotate`, and `traceability-render` — handle the full lifecycle of requirement capture, cross-artefact linking, code annotation, decomposition validation, code indexing, change-impact documentation, and traceability rendering. Without well-defined behavioural contracts for these skills, the Assured guarantee of end-to-end traceability integrity cannot be verified by an auditor. This spec captures the observable obligations that each skill must satisfy.

## Requirements

### REQ-assured-skills-001

A user adding a requirement to an existing feature MUST be able to invoke a skill that mints a unique, sequential REQ-ID, prompts for the requirement statement, and persists the new requirement to the canonical spec file — with no risk of duplicate IDs even when invoked concurrently in different terminals on the same project.

**Module:** P1.SP1.M2

### REQ-assured-skills-002

The `req-link` skill SHALL verify that both the source ID and every target ID resolve in `library/_ids.md` before inserting the `**satisfies:**` link, and SHALL abort with a structured error message if any target ID is not found in the registry.

**Module:** P1.SP1.M2

### REQ-assured-skills-003

The `code-annotate` skill SHALL detect the comment syntax for the file's language (Python: `#`, JavaScript/TypeScript/Go/Rust: `//`, defaulting to `#` if the extension is unrecognised) and insert the `<comment-prefix> implements: <artefact-id>` annotation in a syntactically-valid position (first line of the function body, immediately after the opening delimiter), then run `annotation_format_integrity` to confirm the annotation parses correctly.

**Module:** P1.SP1.M2

### REQ-assured-skills-004

The `module-bound-check` skill SHALL run all five decomposition validators (`req_has_module_assignment`, `code_annotation_maps_to_module`, `visibility_rule_enforcement`, `anaemic_context_detection`, `granularity_match`) and SHALL report a per-validator pass/fail summary table with error and warning counts; exit code SHALL be 0 if all validators pass (or produce only warnings) and 1 if any validator reports at least one error.

**Module:** P1.SP1.M2

### REQ-assured-skills-005

The `kb-codeindex` skill SHALL be idempotent: re-running it on a project whose source annotations have not changed since the last run SHALL produce byte-identical output in `library/_code-index.md` (i.e., the file content SHALL NOT differ in any byte between two successive runs with identical inputs).

**Module:** P1.SP1.M2

### REQ-assured-skills-006

The `change-impact-annotate` skill SHALL scaffold a `CHG-NNN` record from the staged or unstaged diff returned by `git diff`, pre-filling the impacted-artefacts sections by parsing existing `# implements:` annotations on the touched functions, and SHALL produce a record where every touched code file is cited before writing to `docs/change-impacts/CHG-<NNN>.md`.

**Module:** P1.SP1.M2

### REQ-assured-skills-007

The `traceability-render` skill SHALL write a file to `docs/traceability/<module-id>.md` containing the module-scope render (all REQs, DESs, TESTs, and code locations assigned to the module) and the module dependency graph (as a markdown edge-list derived from source-file imports), and SHALL be idempotent — re-running with unchanged inputs SHALL produce a byte-identical output file.

**Module:** P1.SP1.M2

## Out of scope

- The underlying Python implementations of `parse_code_annotations`, `render_code_index`, `render_module_scope`, `render_module_dependency_graph` — covered by `assured-code-index` and `assured-render` feature directories.
- The five decomposition validator implementations — covered by `assured-decomposition-validators`.
- The `change_impact_gate` pre-push validator that consumes CHG records — covered by `assured-substrate`.
- The `commission-assured` skill — covered by `assured-substrate`.
- Export-format variants (HTML, PDF) for traceability documents — covered by `assured-export-formats`.

## Success criteria

- `req-add` appends a valid REQ section and never modifies existing IDs.
- `req-link` inserts no link when any target ID is absent from `library/_ids.md`.
- `code-annotate` inserts language-correct comment syntax and passes `annotation_format_integrity` on all supported extensions.
- `module-bound-check` prints a five-row table and exits 1 when any row reports errors.
- Running `kb-codeindex` twice in succession on an unchanged project produces no diff in `library/_code-index.md`.
- `change-impact-annotate` produces a CHG record that cites every touched code file.
- `traceability-render` writes to the correct path and two successive runs with unchanged input produce identical files.

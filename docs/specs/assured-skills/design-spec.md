---
feature_id: assured-skills
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-skills

**Feature-id:** assured-skills
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Seven design units correspond to the seven non-commission skills in the Assured bundle. Each unit describes the observable behaviour contract that the skill's `## Steps` section must honour — not the implementation internals (which live in the `assured-code-index`, `assured-render`, and `assured-decomposition-validators` feature directories).

---

## Design

### DES-assured-skills-001

<!-- implements: DES-assured-skills-001 -->

`req_add_skill(feature_id: str, spec_path: Path, requirement_text: str, module_id: str) -> str` is the operation performed by the `req-add` skill after the user confirms. It:

1. Reads `spec_path` and scans all `### REQ-<feature_id>-<NNN>` headings to find `max_n` (0 if none exist).
2. Computes `new_id = f"REQ-{feature_id}-{max_n + 1:03d}"`.
3. Appends the following block to the end of the file (preceded by a blank line if the file does not already end with one):
   ```markdown
   ### REQ-<feature-id>-<NNN>

   <requirement_text>

   **Module:** <module_id>
   ```
4. Returns `new_id`.

The function MUST NOT modify any existing heading or paragraph. If `spec_path` does not exist, it raises `SpecNotFoundError(f"requirements-spec.md not found at {spec_path}")`.

**satisfies:** REQ-assured-skills-001

### DES-assured-skills-002

<!-- implements: DES-assured-skills-002 -->

`req_link_skill(source_id: str, target_ids: list[str], registry_path: Path, artefact_path: Path) -> None` is the operation performed by the `req-link` skill before inserting any link. It:

1. Reads `registry_path` (`library/_ids.md`) and collects all declared IDs into a set `known_ids`.
2. For each `tid` in `target_ids`, checks `tid in known_ids`. If any are absent, raises `UnresolvedIDError(f"Target ID(s) not found in registry: {missing}")` without writing any file.
3. Verifies `source_id in known_ids`; raises `UnresolvedIDError` if absent.
4. Opens `artefact_path`, locates the `### <source_id>` heading, and inserts `**satisfies:** <comma-joined target_ids>` immediately after the heading line (on the next non-blank line, or as the first line after the heading if none exists).
5. Runs `cited_ids_resolve` validator on the modified file and raises `ValidationError` if it fails.

**satisfies:** REQ-assured-skills-002

### DES-assured-skills-003

<!-- implements: DES-assured-skills-003 -->

`code_annotate_skill(artefact_id: str, file_path: Path, function_name: str, registry_path: Path) -> None` is the core operation of the `code-annotate` skill:

1. Verifies `artefact_id` exists in `library/_ids.md`; raises `UnresolvedIDError` if absent.
2. Detects comment prefix from `file_path.suffix`:
   - `.py` → `#`
   - `.js`, `.ts`, `.go`, `.rs` → `//`
   - anything else → `#` (default)
3. Constructs the annotation line: `f"{prefix} implements: {artefact_id}"`.
4. Locates `function_name` in `file_path` (AST for Python; regex for JS/TS/Go/Rust). Finds the first line of the function body (line after `:` for Python; line after `{` for C-style).
5. Inserts the annotation line at that position.
6. Runs `annotation_format_integrity` on the modified file; if it fails, reverts the insertion and raises `AnnotationError`.

**satisfies:** REQ-assured-skills-003

### DES-assured-skills-004

<!-- implements: DES-assured-skills-004 -->

`module_bound_check_skill(project_root: Path) -> ModuleBoundCheckResult` is the aggregation function called by the `module-bound-check` skill:

1. Loads `programs.yaml` from `project_root` (or uses `default_decomposition` if absent).
2. Builds `spec_module_lookup` by walking `docs/specs/**/*.md` and reading declared ID → module mappings.
3. Builds `import_edge_graph` by walking source files and mapping imports to from-module / to-module pairs.
4. Runs all five validators in order:
   - `req_has_module_assignment(spec_module_lookup)`
   - `code_annotation_maps_to_module(spec_module_lookup, project_root)`
   - `visibility_rule_enforcement(import_edge_graph, programs_yaml, mode)`
   - `anaemic_context_detection(spec_module_lookup, project_root)`
   - `granularity_match(spec_module_lookup)`
5. Returns `ModuleBoundCheckResult` containing a list of five `ValidatorResult(name, status, errors, warnings)` entries.
6. The `module-bound-check` skill renders the result as a markdown table and exits with code 1 if `any(r.errors for r in result.validators)`.

**satisfies:** REQ-assured-skills-004

### DES-assured-skills-005

<!-- implements: DES-assured-skills-005 -->

`kb_codeindex_idempotency` is the contract enforced by the `kb-codeindex` skill's step 6:

After `render_code_index` produces the new content string, the skill reads the existing `library/_code-index.md` (if it exists) and compares it byte-for-byte with the new content. The write is skipped if and only if the content is identical (`existing_bytes == new_bytes`). The comparison uses raw bytes (UTF-8 encoded), not decoded strings, to prevent line-ending normalisation from introducing false differences. The skill reports `"No changes — index is up to date."` when the write is skipped.

This means: if the source tree has not changed since the last run (same annotations, same function names, same IDs), `render_code_index` MUST be a pure function of its inputs so that two calls with the same inputs produce the same bytes. Any non-determinism (e.g., dict insertion order in Python < 3.7, floating-point timestamps, random UUIDs) is forbidden in the render path.

**satisfies:** REQ-assured-skills-005

### DES-assured-skills-006

<!-- implements: DES-assured-skills-006 -->

`change_impact_annotate_skill(diff_text: str, project_root: Path) -> Path` is the scaffolding function called by the `change-impact-annotate` skill:

1. Parses `diff_text` (output of `git diff`) to extract touched file paths and touched function names (best-effort via unified diff header parsing).
2. Maps each file path to a module ID using `programs.yaml`.
3. For each touched function name, reads the corresponding source file and parses `# implements:` annotations to collect cited artefact IDs (REQs, DESs, TESTs).
4. Computes `next_chg_n` by scanning `docs/change-impacts/CHG-*.md`; new ID = `f"CHG-{next_chg_n:03d}"`.
5. Renders a draft record from the `change-impact.md` template, substituting:
   - All discovered REQs, DESs, TESTs, code file paths, and module IDs into the impacted-artefacts section.
   - Placeholder text for: change summary, downstream effects, verification approach, approver.
6. Asserts that every touched code file appears at least once in the rendered record; raises `CoverageError` if any file is absent.
7. Writes to `docs/change-impacts/CHG-<NNN>.md` and returns the written path.

**satisfies:** REQ-assured-skills-006

### DES-assured-skills-007

<!-- implements: DES-assured-skills-007 -->

`traceability_render_skill(module_id: str, project_root: Path) -> Path` is the function called by the `traceability-render` skill:

1. Validates `module_id` exists in `programs.yaml`; raises `ModuleNotFoundError` if absent.
2. Loads `library/_ids.md` and `library/_code-index.md`.
3. Filters to IDs whose module assignment matches `module_id`.
4. Calls `render_module_scope(module_id, filtered_ids, code_index)` → `scope_md: str`.
5. Derives `actual_edges` by walking source-file imports and mapping to module pairs; calls `render_module_dependency_graph(module_id, actual_edges)` → `graph_md: str`.
6. Concatenates `scope_md + "\n\n" + graph_md` into `final_content: str`.
7. Writes `final_content` to `docs/traceability/<module_id>.md`. Like `kb-codeindex`, the write is byte-gated: if the file exists and its content is byte-identical to `final_content`, the write is skipped and `"No changes."` is reported.
8. Returns the path `docs/traceability/<module_id>.md`.

**satisfies:** REQ-assured-skills-007

---

## Out of scope

- The `render_module_scope` and `render_module_dependency_graph` function implementations — covered in `assured-render`.
- The five validator implementations — covered in `assured-decomposition-validators`.
- The `parse_code_annotations` and `render_code_index` implementations — covered in `assured-code-index`.
- The `commission-assured` skill design — covered in `assured-substrate`.
- Concurrent or incremental update strategies for the code index or traceability documents.

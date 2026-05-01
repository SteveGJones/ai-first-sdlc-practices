---
feature_id: assured-skills
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-skills

**Feature-id:** assured-skills
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, exercising the public API in isolation using temporary directories and in-memory fixture data. No live git commands are required — `git diff` output is supplied as fixture strings.

---

## Tests

### TEST-assured-skills-001

**Title:** `req_add_skill` happy-path and sequential ID minting

**Description:** Given a temporary `requirements-spec.md` containing two existing headings `### REQ-auth-001` and `### REQ-auth-002`, call `req_add_skill("auth", spec_path, "The system SHALL do X.", "P1.SP1.M1")` and assert: (1) the returned ID is `"REQ-auth-003"`; (2) the file now contains `### REQ-auth-003`; (3) the requirement text `"The system SHALL do X."` appears in the new section; (4) `**Module:** P1.SP1.M1` is present in the new section; (5) the original headings `REQ-auth-001` and `REQ-auth-002` are unchanged. Separately, call `req_add_skill` on a path that does not exist and assert `SpecNotFoundError` is raised.

**satisfies:** REQ-assured-skills-001 via DES-assured-skills-001

---

### TEST-assured-skills-002

**Title:** `req_link_skill` validates target IDs before inserting

**Description:** Given a temporary `library/_ids.md` containing `REQ-auth-001` and `DES-auth-001`, and a temporary `design-spec.md` with a `### DES-auth-001` heading: (a) call `req_link_skill("DES-auth-001", ["REQ-auth-001"], registry_path, artefact_path)` and assert `**satisfies:** REQ-auth-001` is inserted after the heading without error; (b) call `req_link_skill("DES-auth-001", ["REQ-auth-999"], ...)` where `REQ-auth-999` is absent from the registry and assert `UnresolvedIDError` is raised and the file is NOT modified; (c) call `req_link_skill("DES-auth-999", ["REQ-auth-001"], ...)` where the source ID is absent and assert `UnresolvedIDError` is raised.

**satisfies:** REQ-assured-skills-002 via DES-assured-skills-002

---

### TEST-assured-skills-003

**Title:** `code_annotate_skill` language detection and annotation insertion

**Description:** For each of the following (suffix, expected_prefix) pairs: `(".py", "#")`, `(".js", "//")`, `(".ts", "//")`, `(".go", "//")`, `(".rs", "//")`, `(".sh", "#")` (default): (a) create a temporary file with a minimal function body, call `code_annotate_skill("REQ-auth-001", file_path, "my_function", registry_path)`, and assert the first line of the function body is `f"{expected_prefix} implements: REQ-auth-001"`; (b) assert `annotation_format_integrity` passes on the modified file. Separately, call `code_annotate_skill` with an artefact ID absent from the registry and assert `UnresolvedIDError` is raised and the file is not modified.

**satisfies:** REQ-assured-skills-003 via DES-assured-skills-003

---

### TEST-assured-skills-004

**Title:** `module_bound_check_skill` five-validator aggregation and exit code

**Description:** Given a temporary project root with a minimal `programs.yaml`, a `docs/specs/` tree containing one REQ without a `**Module:**` field (to trigger `req_has_module_assignment` failure), and otherwise clean source files: (a) call `module_bound_check_skill(project_root)` and assert the returned `ModuleBoundCheckResult` contains exactly five `ValidatorResult` entries; (b) assert the `req_has_module_assignment` entry has `status == "FAIL"` and `errors >= 1`; (c) assert all other four validators return `status == "PASS"`. Separately, given a fully valid project (all REQs have module fields, all annotations map correctly), assert all five validators return `status == "PASS"` and that the exit code would be 0 (i.e., `any(r.errors for r in result.validators)` is False).

**satisfies:** REQ-assured-skills-004 via DES-assured-skills-004

---

### TEST-assured-skills-005

**Title:** `kb-codeindex` idempotency — byte-identical output on unchanged source

**Description:** Given a temporary project root containing two Python source files with `# implements:` annotations, and a populated `library/_ids.md`: (a) call the `kb-codeindex` logic to produce `library/_code-index.md` (first run); (b) capture the raw bytes of the written file; (c) call the same logic again without modifying any source file (second run); (d) assert that `library/_code-index.md` byte content is identical after the second run (`content_after == content_before`); (e) assert the second run reports `"No changes — index is up to date."` (or equivalent). Separately, modify one annotation in a source file and assert the second run DOES update the file.

**satisfies:** REQ-assured-skills-005 via DES-assured-skills-005

---

### TEST-assured-skills-006

**Title:** `change_impact_annotate_skill` scaffolds CHG record from diff with full coverage

**Description:** Given a fixture `diff_text` representing two modified files (`src/auth.py` with a touched function `login()` that has `# implements: REQ-auth-001` in the fixture source, and `src/token.py` with a touched function `generate()` that has `# implements: DES-auth-002`), and a `programs.yaml` mapping both files to module `P1.SP1.M1`: (a) call `change_impact_annotate_skill(diff_text, project_root)` and assert `docs/change-impacts/CHG-001.md` is created; (b) assert the record cites both `src/auth.py` and `src/token.py`; (c) assert the record contains `REQ-auth-001` and `DES-auth-002`; (d) assert module `P1.SP1.M1` appears in the record. Separately, construct a `diff_text` that touches `src/missing.py` (with no `# implements:` annotations) and assert the function still includes `src/missing.py` in the impacted-artefacts section (as an unannotated file, not silently dropped).

**satisfies:** REQ-assured-skills-006 via DES-assured-skills-006

---

### TEST-assured-skills-007

**Title:** `traceability_render_skill` writes correct path and is idempotent

**Description:** Given a temporary project with `programs.yaml` declaring module `P1.SP1.M1`, a `library/_ids.md` with two IDs assigned to that module, and a `library/_code-index.md` with corresponding code entries: (a) call `traceability_render_skill("P1.SP1.M1", project_root)` and assert the returned path is `docs/traceability/P1.SP1.M1.md`; (b) assert the file exists and contains `P1.SP1.M1` in its content; (c) assert the file contains both the module-scope REQ/DES sections and a dependency graph section. For idempotency: (d) capture the raw bytes; (e) call the skill again with no source changes; (f) assert bytes are identical after the second call; (g) assert the second call reports no-change. Separately, call `traceability_render_skill("P1.SP9.M9", project_root)` where the module is not declared in `programs.yaml` and assert `ModuleNotFoundError` is raised.

**satisfies:** REQ-assured-skills-007 via DES-assured-skills-007

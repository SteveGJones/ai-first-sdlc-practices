---
name: module-bound-check
description: Run all 5 decomposition validators (req-has-module, code-annotation-maps-to-module, visibility-rule-enforcement, anaemic-context-detection, granularity-match) on the project, reporting violations.
---

# Skill: module-bound-check

**Use this skill** to verify the project's decomposition is sound. Aggregates results from all 5 module-bound validators and reports a single pass/fail with per-validator detail. Run this before pushing a substantial change to a regulated-context project.

## Steps

1. **Load the decomposition.** Read `programs.yaml` (or use `default_decomposition` if absent).

2. **Build the spec_module_lookup.** Walk all `docs/specs/**/*.md` artefacts; map each declared ID → module (from frontmatter or positional ID prefix).

3. **Build the import-edge graph.** Walk source files; for each import, determine the from-module and to-module by mapping the file path to declared module paths.

4. **Run each validator.**
    - `req_has_module_assignment`
    - `code_annotation_maps_to_module`
    - `visibility_rule_enforcement` (mode from team-config: strict for regulated, advisory otherwise)
    - `anaemic_context_detection`
    - `granularity_match`

5. **Aggregate results.** Print a table:
    ```
    Validator                          Status   Errors  Warnings
    req_has_module_assignment          PASS     0       0
    code_annotation_maps_to_module     FAIL     2       0
    visibility_rule_enforcement        PASS     0       1
    anaemic_context_detection          PASS     0       0
    granularity_match                  PASS     0       3
    ```

6. **Report each error and warning** with file path and line number.

## Done criteria

- All 5 validators ran.
- Result table printed.
- Exit code: 0 if all pass; 1 if any error; 0 if only warnings (warnings don't block).

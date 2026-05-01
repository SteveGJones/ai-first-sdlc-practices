# Assured Bundle Review (Phase E) -- Independent Critical Review

**Reviewer:** Claude Opus 4.6 (automated)
**Date:** 2026-04-30
**Scope:** plugins/sdlc-assured/ as Phase E deliverable of EPIC #178
**Documents reviewed:** option-bundle-contract.md, programme-assured-bundles-design.md (Section 4), METHODS.md (Section 4), all files under plugins/sdlc-assured/, all tests/test_assured_*.py, plugins/sdlc-programme/ (for comparison), plugins/sdlc-knowledge-base/agents/synthesis-librarian.md

---

## 1. Constitution overlay soundness (Articles 15-17)

**Verdict: AGREE-WITH-CONCERNS**

Articles 15-17 extend articles 1-14 cleanly. The numbering is correct (Programme adds 12-14; Assured adds 15-17; no gaps, no collisions). The semantic layering is sound: Article 15 (traceability) adds ID-system obligations that Programme's Article 13 (cross-phase reference integrity) does not cover. Article 16 (decomposition) introduces module-assignment obligations that have no Programme equivalent. Article 17 (KB-for-code annotations) is genuinely new.

**Concerns:**

- **Gap between constitution and validators on orphan IDs.** Article 15 says "No orphan IDs: every declared ID is cited at least once (warn, not block -- orphans are a smell, not always a defect)." The `orphan_ids` validator correctly warns-not-blocks, but it only checks REQ and DES kinds (lines 59-60 of `traceability_validators.py`). This means a DES that is never cited by a TEST is caught by `backward_coverage` (which blocks), but an orphan DES that IS cited by a TEST yet never cited by any CODE annotation is invisible to `orphan_ids`. This is not a bug per se -- `backward_coverage` catches the DES-has-no-TEST case -- but the Article 15 text's phrasing "every declared ID is cited at least once" is broader than what the validator actually checks. The constitution should either narrow the claim or the validator should widen.

- **Article 17 says "each non-trivial function or module-level entry point" MUST carry an annotation, but no validator actually enforces annotation completeness** (only `annotation_format_integrity` validates that existing annotations parse cleanly and resolve). The `granularity_match` validator checks that each REQ has at least one `# implements:` annotation in `requirement` mode, which is a backward check from REQ to code -- but it does not check that all non-trivial functions have annotations (forward check from code to REQ). This is a gap between constitution promise and validator coverage. Article 17 promises more than the validators deliver. For v0.1.0 this is acceptable if documented as a known limitation.

- **Constitution says "Renames happen via decomposition refactoring (`kb-rebuild-indexes` remaps old paths to new paths while preserving the ID), never by editing the ID itself."** The `remap_ids` function correctly preserves IDs and only remaps source paths. However, there is no validator that detects whether someone manually edited an ID. This is an enforcement gap, though arguably one that Git history can police and that a v0.1.0 can defer.

## 2. ID system fitness

**Verdict: AGREE-WITH-CONCERNS**

The dual ID formats (flat `REQ-feature-NNN` and positional `P1.SP2.M3.REQ-NNN`) coexist cleanly in the parser. The regexes in `ids.py` are mutually exclusive and well-constructed. `parse_id` correctly distinguishes the two forms. `format_id` round-trips correctly (tested). The `build_id_registry` regex `_HEADING_RE` accepts both forms in markdown headings.

**`remap_ids` traceability preservation:** The implementation is correct for its scope -- it remaps source paths, not IDs. However, it only handles prefix-based remapping. Edge cases that worry me:

- **Multiple prefix matches.** `remap_ids` breaks on the first matching prefix (line 157). If a source path matches two old prefixes (e.g., `docs/specs/legacy/auth/` matching both `docs/specs/legacy/` and `docs/specs/legacy/auth/`), the result depends on dict iteration order. This is fragile. For v0.1.0 this is acceptable since decomposition refactoring is a rare operation, but it should be documented.

- **Flat-to-positional migration.** When a project starts with flat IDs (`REQ-auth-001`) and later adopts decomposition, the IDs themselves are immutable per constitution. This means the project has a permanent mixed-format ID space. The validators handle this correctly (both forms resolve through `parse_id`), but the `_module_from_positional_id` function returns `None` for flat IDs (line 158 of `decomposition.py`), falling back to the spec's explicit `module` field. This fallback works but means flat-ID projects MUST add `module:` frontmatter to every spec after decomposition -- there is no automatic derivation. This is correct behaviour but is not documented anywhere in the constitution or commission-assured skill.

- **Positional ID numbers are zero-padded to 3 digits** (`format_id` uses `{:03d}`), but the parser accepts any number of digits. A project could have `REQ-001` and `REQ-1` as distinct IDs if hand-edited. The `id_uniqueness` validator would catch true duplicates, but visual confusion is possible.

## 3. Traceability validator coverage

**Verdict: AGREE**

The 4 mandatory validators + 1 optional validator cover the broken-reference cases regulated-industry teams care about:

- **Forward link integrity:** `forward_link_integrity` correctly blocks when a DES has no `satisfies` links (DES with no REQ) and when a TEST has no `satisfies` links (TEST with no DES). It also blocks when cited targets are missing. This covers the "DES with no satisfies, TEST with no satisfies" case. Tested at lines 99-149 of `test_assured_traceability_validators.py`.

- **Backward coverage:** `backward_coverage` correctly blocks when a REQ has no DES covering it and when a DES has no TEST covering it. The implementation uses the satisfies index to check backward, not just forward. Tested at lines 152-187.

- **Idempotency:** `index_regenerability` correctly does a byte-for-byte comparison. Tested at lines 189-209.

- **Annotation format:** `annotation_format_integrity` correctly blocks on malformed annotation tokens (via `parse_id`) and on citations to undeclared IDs. Tested at lines 212-233.

- **Change-impact gate (optional):** Correctly no-ops when disabled. When enabled, correctly requires change-impact records that cite the changed file. The implementation's file-matching logic (lines 153-161 of `traceability_validators.py`) is fragile -- it uses string containment (`"src/" in line`) to identify code paths in change-impact records, which could produce false positives on non-code lines that happen to contain `src/`. For v0.1.0 this is acceptable.

The test suite for traceability validators has 16 tests covering all happy and failure paths. Coverage is solid.

## 4. Decomposition validator coverage

**Verdict: AGREE-WITH-CONCERNS**

The 5 module-bound validators model the DDD bounded-context + Bazel visibility-rule discipline adequately for v0.1.0:

- **`req_has_module_assignment`:** Correctly validates both positional-prefix and frontmatter-based module assignment. Falls back from positional prefix to spec's `module` field. Blocks on missing or undeclared modules. Tested with 3 test cases.

- **`code_annotation_maps_to_module`:** Correctly validates that annotated code files live under the declared module's paths. Uses `startswith` path matching. Tested with 2 test cases (in-module and out-of-module).

- **`visibility_rule_enforcement`:** Correctly implements advisory vs strict modes. Advisory mode warns; strict mode blocks. Skips self-edges. Tested with 3 test cases. The implementation correctly builds a declared-visibility lookup from the decomposition's visibility rules.

- **`anaemic_context_detection`:** This IS functionally identical to `code_annotation_maps_to_module` -- both check `_file_under_paths` for the same condition (code implementing a spec ID outside the module's declared paths). The difference is that `code_annotation_maps_to_module` is described as "each annotation's file path must lie under its cited spec's module path" and `anaemic_context_detection` is described as "flag when code implementing a module's REQs/DESs lives outside the module's paths." These are the same check. The anaemic-context validator will always produce the same errors as `code_annotation_maps_to_module`. **This is a concern:** either the two validators should be merged, or `anaemic_context_detection` should add logic beyond path co-location (e.g., checking for concentration patterns -- does most of a module's logic live in one place, or is it scattered across many?). As implemented, running both produces duplicate error messages for the same violations.

- **`granularity_match`:** Correctly warns (not blocks) when a REQ in a `requirement`-granularity module has no `# implements:` annotation. Only applies to modules with `granularity: requirement`. Tested with 2 test cases. The `function` and `module` granularity levels are not checked (they're accepted silently) -- this means declaring `granularity: function` has no validator effect, which should be documented.

**Additional concerns:**

- The validators do not check for circular dependencies between programs (the design spec says "circular dependencies between programs block, between sub-programs warn"). The `visibility_rule_enforcement` validator only checks whether edges are declared in the visibility block, not whether the resulting graph is acyclic.

- The hexagonal architecture `structure: hexagonal` field is parsed and stored but never validated. No validator checks `core` vs `adapter` directory tagging. This is fine for v0.1.0 if acknowledged.

## 5. KB integration realism

**Verdict: AGREE-WITH-CONCERNS**

The `SYNTHESISE-ACROSS-SPEC-TYPES` mode is implemented as a section in the existing `synthesis-librarian.md` agent file (lines 136-158 of `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md`). It extends the existing agent with a new mode rather than creating a separate agent. The `valid_handles` whitelist extends to accept `req`, `des`, `test`, `code` as pseudo-handles. This is the correct composition approach.

**Concerns:**

- **The `_code-index.md` shelf-shape includes a timestamp** (`last_rebuilt` in the header comment, line 110 of `code_index.py`). This timestamp changes on every run, which means `render_code_index` is NOT idempotent -- two runs produce different output because the timestamps differ. This directly contradicts the `index_regenerability` validator's byte-identical requirement. The `kb-codeindex` SKILL.md says "Idempotent -- re-running produces byte-identical output if no annotations changed" but the implementation breaks this promise due to the embedded timestamp. **This is a bug.** The `render_spec_findings` function has the same problem.

- **The Assured bundle does not ship any Assured-specific code in the KB plugin.** The `SYNTHESISE-ACROSS-SPEC-TYPES` mode lives in the KB plugin's `synthesis-librarian.md`, not in the Assured bundle. The `render_spec_findings` and `render_code_index` functions in the Assured bundle emit shelf-index-shaped content, but the KB plugin's `research-librarian` agent has no special awareness of `_code-index.md`. The design spec says "existing `research-librarian` queries against this without modification" -- this works because the shelf-index shape is the same, but it requires the user to manually configure the `_code-index.md` as a library source. There is no documented wiring step in `commission-assured`. This is a gap in the commissioning skill.

- **The `render_spec_findings` function emits terms like `REQ, auth`** (line 149 of `code_index.py`), extracting the feature name from flat IDs. For positional IDs, the terms are just the kind (e.g., `REQ`). This means librarian term-matching will be weak for positional-ID projects -- queries on topic keywords won't hit spec findings unless the user searches by kind. This is a v0.1.0 limitation, not a blocker.

## 6. Bundle layout vs Phase C contract

**Verdict: AGREE**

The Assured bundle layout matches the Phase C contract:

| Contract requirement | Actual |
|---|---|
| `.claude-plugin/plugin.json` | Present, correct metadata |
| `manifest.yaml` | Present, `schema_version: 1`, correct fields |
| `README.md` | Present |
| `CONSTITUTION.md` | Present at bundle root |
| `agents/` | Empty (manifest declares `agents: []`) -- acceptable |
| `skills/` | 8 skill subdirectories, each with SKILL.md |
| `templates/` | 6 templates present, matching manifest's `templates:` list |
| `scripts/` | Present, mirroring sdlc-knowledge-base pattern |
| `pyproject.toml` | Present with correct package name |

**Reserved Phase E fields in manifest:**

The contract defines 5 reserved Phase E fields: `decomposition_support`, `id_format`, `paths_split_supported`, `known_violations_field`, `anaemic_context_opt_out`. **None of these fields appear in the Assured bundle's `manifest.yaml`.** The contract says "bundles MAY include them" and "Phase E implements full validator support." The Assured bundle implicitly supports all of these features through its validators and constitution, but it does not declare them as manifest flags. This is technically compliant (MAY, not MUST), but it means there is no machine-readable way for tooling to determine whether a bundle supports decomposition without reading the validators list. For v0.1.0 this is acceptable -- the fields were reserved for future use and the contract does not require them.

**Validator identifiers:** The manifest's `validators:` block lists 15 validators at `pre_push` level. All 7 traceability validators and all 5 decomposition validators from the implementation are represented. The mapping from identifier to Python function is implicit (bundle-defined identifiers per contract), which is correct.

**`depends_on`:** The manifest declares `[sdlc-core, sdlc-programme, sdlc-team-common, sdlc-team-fullstack, sdlc-knowledge-base]`. This is correct -- Assured layers on Programme, and the KB dependency is needed for the shelf-index integration.

---

## Summary

The Assured bundle is **good enough to ship as v0.1.0**. The architecture is sound: clean constitution layering, correct ID parsing with round-trip fidelity, comprehensive traceability validators with good test coverage (7 test files, 50+ test cases), a working decomposition model, shelf-index-compatible code-index emission, and standard-specific export templates for all four targeted regulatory standards.

**Three issues should be addressed before Phase F (dogfood) proceeds without retrofit risk:**

1. **Timestamp in `render_code_index` / `render_spec_findings` breaks idempotency.** This is a real bug: the `index_regenerability` validator will fail on every re-run because the `last_rebuilt` timestamp changes. Fix: either strip the timestamp from the generated output or make the `index_regenerability` validator timestamp-aware. This is a small fix but it blocks the idempotency guarantee that the constitution promises.

2. **`anaemic_context_detection` is functionally identical to `code_annotation_maps_to_module`.** Both perform the same path-co-location check. Either merge them (and update the manifest and module-bound-check skill to reference 4 validators, not 5) or add genuine concentration-analysis logic to `anaemic_context_detection` so it catches a different class of violations (e.g., a module where 80% of its REQ implementations are co-located but 20% are scattered -- the scatter is the anaemic smell, not just a single outlier). This is not a blocker but will cause confusion in Phase F when both validators fire the same errors.

3. **`commission-assured` skill does not document the KB wiring step** for `_code-index.md` and `_spec-findings.md` as library sources queryable by the research-librarian. Without this step, the "spec-as-KB-finding" integration described in the design spec will not work out of the box.

**Phase F can proceed** with these three items noted as known issues, as long as the team is prepared to patch the idempotency bug when they hit it during dogfood. None of the issues are architectural -- they are implementation-level fixes that do not require design changes.

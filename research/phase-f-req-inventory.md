# Phase F — REQ Inventory Checklist

Planning artefact for Tasks 4-16. Each row is one component; the REQ-intent column is a one-line draft of what the corresponding REQ artefact should assert. Actual REQ artefacts (with full ID strings, acceptance criteria, links) are authored in Tasks 4-16.

Total: **44 REQs** across **11 feature directories**.

---

## M1 programme-bundle (~12 REQs)

### `programme-skills` — 5 REQs

| Component | REQ-intent |
|---|---|
| `commission-programme` skill | The commission-programme skill SHALL scaffold a feature directory containing a REQ spec, populate it with stub entries derived from `programs.yaml` module decomposition, and record the commissioning event in an audit log. |
| `phase-init` skill | The phase-init skill SHALL create the phase-appropriate spec file (design, test, or code) in the feature directory, copying the correct template from the plugin, and refuse to proceed if the prerequisite phase gate has not been passed. |
| `phase-gate` skill | The phase-gate skill SHALL invoke the corresponding gate function (requirements, design, test, or code), surface pass/fail with per-failure rationale, and block progression when the gate fails. |
| `phase-review` skill | The phase-review skill SHALL record a dated review entry in the feature directory, update the phase status, and make no structural mutations beyond the review record. |
| `traceability-export` skill | The traceability-export skill SHALL produce a REQ→DES→TEST→CODE traceability matrix in both CSV and Markdown formats from the artefacts in the feature directory, with no rows silently omitted. |

### `programme-validators` — 4 REQs

| Component | REQ-intent |
|---|---|
| `requirements_gate` | The requirements gate SHALL pass if and only if the REQ spec parses without error and contains at least one non-stub requirement entry. |
| `design_gate` | The design gate SHALL pass if and only if the DES spec parses without error, every REQ ID cited in DES is present in the REQ spec, and a review record exists for the same phase (i.e., design). |
| `test_gate` | The test gate SHALL pass if and only if the TEST spec parses without error, every DES ID cited in TEST is present in the DES spec, and a review record exists for the same phase (i.e., test). |
| `code_gate` | The code gate SHALL pass if and only if code annotations reference only IDs present in the TEST spec and a review record exists for the test phase. |

### `programme-substrate` — 3 REQs

| Component | REQ-intent |
|---|---|
| `spec_parser` (`parse_spec`) | The spec parser SHALL deserialise a phase spec file into a structured `ParsedSpec` object, raise a typed `SpecParseError` on any malformed input, and preserve the original file path for error reporting. |
| `traceability` (`build_matrix`, `export_csv`, `export_markdown`) | The traceability matrix builder SHALL produce one row per REQ ID covering its satisfaction chain through DES, TEST, and CODE artefacts, and the export functions SHALL emit the matrix in RFC-4180 CSV and CommonMark Markdown without data loss. |
| Constitution Articles 12-14 (programme rules) | The Constitution SHALL define Articles 12-14 prescribing the mandatory four-phase gate sequence, the spec-file naming convention, and the review-record format required by the programme-bundle. |

---

## M2 assured-bundle (~30 REQs)

### `assured-id-system` — 2 REQs

| Component | REQ-intent |
|---|---|
| `parse_id`, `format_id`, `is_positional` | The ID parser SHALL accept the canonical `<type>-<feature>-<seq>` format, round-trip through `format_id` without loss, and classify positional (seq-bearing) vs. symbolic IDs via `is_positional`. |
| `build_id_registry`, `render_id_registry`, `remap_ids` | The ID registry SHALL scan all spec artefacts under the project root to build a de-duplicated `IdRecord` list, render it as a human-readable table, and remap legacy ID strings to their canonical form without modifying artefacts in place. |

### `assured-traceability-validators` — 4 REQs

| Component | REQ-intent |
|---|---|
| `id_uniqueness`, `cited_ids_resolve`, `orphan_ids` | The identity validators SHALL reject any registry containing duplicate IDs, unresolvable citation targets, or IDs that appear in no citation chain. |
| `forward_link_integrity`, `backward_coverage` | The coverage validators SHALL verify that every REQ has at least one DES link (forward) and that every DES entry is covered by at least one TEST entry (backward). |
| `index_regenerability`, `annotation_format_integrity` | The index validators SHALL confirm that the code-index can be regenerated from source annotations without diff and that all annotations conform to the prescribed `@assured:<id>` syntax. |
| `change_impact_gate` | The change-impact gate SHALL block any commit that modifies a spec entry without a corresponding `change-impact-annotate` annotation referencing the affected downstream IDs. |

### `assured-decomposition-validators` — 5 REQs

| Component | REQ-intent |
|---|---|
| `parse_programs_yaml`, `default_decomposition` | The decomposition loader SHALL parse `programs.yaml` into a `Decomposition` object and fall back to a single-module default when the file is absent, with no silent data loss. |
| `req_has_module_assignment` | The module-assignment validator SHALL reject any REQ entry that lacks an explicit module assignment when the project has a multi-module decomposition defined in `programs.yaml`. |
| `code_annotation_maps_to_module` | The annotation-module validator SHALL verify that every `@assured:<id>` code annotation references an ID whose module assignment covers the annotated source file's directory. |
| `visibility_rule_enforcement` | The visibility validator SHALL reject any cross-module dependency that violates the visibility rules declared in `programs.yaml` (e.g. a lower-layer module citing a higher-layer REQ). |
| `anaemic_context_detection`, `granularity_match` | The quality validators SHALL flag REQ entries whose description text is below the minimum word threshold (anaemic) and DES entries whose granularity level does not match the REQ they satisfy. |

### `assured-export-formats` — 4 REQs

| Component | REQ-intent |
|---|---|
| `export_do178c_rtm` | The DO-178C export SHALL produce a Requirements Traceability Matrix conforming to the DO-178C table structure, with one row per software requirement and columns for design, test, and code coverage evidence. |
| `export_iec_62304_matrix` | The IEC 62304 export SHALL produce a software requirements traceability matrix mapping each requirement to its verification activity and safety class designation. |
| `export_iso_26262_asil_matrix` | The ISO 26262 export SHALL produce an ASIL-decomposed traceability matrix including ASIL rating per requirement and the allocation rationale. |
| `export_fda_dhf_structure` | The FDA DHF export SHALL produce a Design History File structure document listing requirements, design outputs, and verification records in the sequence mandated by 21 CFR 820.30. |

> Note: `export_csv` and `export_markdown` are general-purpose utilities shared with M1; they are covered by `programme-substrate` REQ 2 and are not counted separately here.

### `assured-render` — 2 REQs

| Component | REQ-intent |
|---|---|
| `render_module_scope` | The module-scope renderer SHALL produce a human-readable summary of each module's REQ/DES/TEST/CODE counts, boundary paths, and visibility rules as declared in the decomposition. |
| `render_module_dependency_graph` | The dependency-graph renderer SHALL emit a directed-acyclic-graph representation (DOT or Mermaid) of the inter-module dependency relationships with no cycles permitted. |

### `assured-code-index` — 2 REQs

| Component | REQ-intent |
|---|---|
| `parse_code_annotations` | The code-annotation parser SHALL scan source files for `@assured:<id>` annotations, resolve each annotation to its `IdRecord`, and raise a typed error for any annotation whose ID is absent from the registry. |
| `render_code_index`, `render_spec_findings` | The code-index renderer SHALL produce a cross-reference table mapping each source file to its cited spec IDs, and the spec-findings renderer SHALL list, per spec ID, every source location that carries an annotation for it. |

### `assured-skills` — 8 REQs

| Component | REQ-intent |
|---|---|
| `commission-assured` skill | The commission-assured skill SHALL scaffold a compliant feature directory, install the decomposition from `programs.yaml`, and record the commissioning event with timestamp and operator identity. |
| `req-add` skill | The req-add skill SHALL append a new REQ entry to the active feature's REQ spec, assign a positional ID that is unique within the registry, and refuse to add a duplicate. |
| `req-link` skill | The req-link skill SHALL insert a `satisfies` citation from a DES, TEST, or CODE spec entry to a target REQ ID, validate that the target ID exists in the registry, and update the traceability matrix in place. |
| `code-annotate` skill | The code-annotate skill SHALL insert `@assured:<id>` annotations at the designated source location, verify the ID resolves in the registry, and fail with a structured error if the annotation would create a cross-module violation. |
| `change-impact-annotate` skill | The change-impact-annotate skill SHALL produce a change-impact annotation block listing all downstream IDs affected by a stated spec change, validate that every cited downstream ID resolves, and emit the block in the format expected by `change_impact_gate`. |
| `module-bound-check` skill | The module-bound-check skill SHALL run all decomposition validators against the current registry and decomposition, report per-validator pass/fail with line-level citations, and exit non-zero when any validator fails. |
| `traceability-render` skill | The traceability-render skill SHALL invoke the appropriate export format function(s) as directed by the user, write the output to the designated file, and print a summary of row counts to stdout. |
| `kb-codeindex` skill | The kb-codeindex skill SHALL ingest the code index produced by `render_code_index` into the active knowledge-base library, enabling kb-query to surface spec-to-code linkage findings in query responses. |

### `assured-substrate` — 3 REQs

| Component | REQ-intent |
|---|---|
| Commissioning contract | The assured commissioning contract SHALL define the minimum artefact set that `commission-assured` must create, the required `programs.yaml` fields, and the acceptance criteria for a valid initial REQ spec. |
| Constitution Articles 15-17 (assured rules) | The Constitution SHALL define Articles 15-17 prescribing the ID format, the mandatory decomposition declaration, and the cross-module visibility rule enforced by the assured-bundle. |
| `change_impact_gate` configuration schema | The change-impact gate configuration schema SHALL define the fields for gate strictness level, exempted ID prefixes, and bypass-approval workflow, and the schema SHALL be validated on load. |

---

## M3 kb-bridge (~2 REQs)

### `kb-bridge-mode` — 2 REQs

| Component | REQ-intent |
|---|---|
| `SYNTHESISE-ACROSS-SPEC-TYPES` mode | The synthesis-librarian SYNTHESISE-ACROSS-SPEC-TYPES mode SHALL produce an attributed cross-spec argument that cites findings from REQ, DES, TEST, and CODE spec handles, enforces inline `[<handle>]` attribution on every supporting-evidence claim, and aborts with a structured error block when attribution post-check fails. |
| `valid_handles` extension for spec pseudo-handles | When operating in SYNTHESISE-ACROSS-SPEC-TYPES mode, the synthesis-librarian SHALL accept `req`, `des`, `test`, and `code` as valid pseudo-handles in addition to the project's registered library handles, and SHALL reject any citation that uses a handle outside this extended set. |

---

## Summary

| Feature directory | REQ count |
|---|---|
| `programme-skills` | 5 |
| `programme-validators` | 4 |
| `programme-substrate` | 3 |
| `assured-id-system` | 2 |
| `assured-traceability-validators` | 4 |
| `assured-decomposition-validators` | 5 |
| `assured-export-formats` | 4 |
| `assured-render` | 2 |
| `assured-code-index` | 2 |
| `assured-skills` | 8 |
| `assured-substrate` | 3 |
| `kb-bridge-mode` | 2 |
| **Total** | **44** |

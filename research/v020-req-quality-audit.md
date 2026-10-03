# v0.2.0 REQ-quality audit (F-010)

**Date:** 2026-05-01
**Author:** Phase E task 28
**Corpus:** docs/specs/*/requirements-spec.md (44 REQs across 12 features)
**Excluded from audit:**
- REQ-assured-decomposition-validators-001 (rewritten in task 25)
- REQ-assured-traceability-validators-003 (rewritten in task 26)
- REQ-assured-skills-001 (rewritten in task 27)
- REQ-assured-traceability-validators-005 (new in task 23, already capability-shaped)

## Summary

- **GOOD:** 20
- **DRIFTER:** 16
- **BORDERLINE:** 4

Budget applied: 10 inline rewrites (R7 cap). 6 deferred to v0.3.0.

## Audit table

| Spec | REQ ID | First sentence (truncated) | Verdict | Action |
|------|--------|----------------------------|---------|--------|
| assured-code-index | REQ-assured-code-index-001 | `` `parse_code_annotations` SHALL extract every `# implements:`...`` | DRIFTER | **Rewritten** |
| assured-code-index | REQ-assured-code-index-002 | `` `render_code_index` and `render_spec_findings` SHALL each emit...`` | DRIFTER | **Rewritten** |
| assured-decomposition-validators | REQ-assured-decomposition-validators-001 | *(excluded — rewritten task 25)* | — | Excluded |
| assured-decomposition-validators | REQ-assured-decomposition-validators-002 | `` `code_annotation_maps_to_module` SHALL report a blocking error...`` | DRIFTER | Deferred v0.3.0 |
| assured-decomposition-validators | REQ-assured-decomposition-validators-003 | `` `visibility_rule_enforcement` SHALL emit blocking errors...`` | DRIFTER | Deferred v0.3.0 |
| assured-decomposition-validators | REQ-assured-decomposition-validators-004 | `` `anaemic_context_detection` SHALL emit a blocking error...`` | DRIFTER | Deferred v0.3.0 |
| assured-decomposition-validators | REQ-assured-decomposition-validators-005 | `` `granularity_match` SHALL emit a non-blocking warning...`` | DRIFTER | Deferred v0.3.0 |
| assured-export-formats | REQ-assured-export-formats-001 | `` `export_do178c_rtm` SHALL produce a Requirements Traceability Matrix...`` | DRIFTER | **Rewritten** |
| assured-export-formats | REQ-assured-export-formats-002 | `` `export_iec_62304_matrix` SHALL emit a Software Traceability Matrix...`` | DRIFTER | **Rewritten** |
| assured-export-formats | REQ-assured-export-formats-003 | `` `export_iso_26262_asil_matrix` SHALL emit an ASIL-tagged traceability matrix...`` | DRIFTER | **Rewritten** |
| assured-export-formats | REQ-assured-export-formats-004 | `` `export_fda_dhf_structure` SHALL organise traceability artefacts...`` | DRIFTER | **Rewritten** |
| assured-id-system | REQ-assured-id-system-001 | `The ID parser SHALL parse both flat ... and positional ... namespace forms...` | GOOD | None |
| assured-id-system | REQ-assured-id-system-002 | `The ID registry SHALL be regenerable byte-identically from project artefacts...` | GOOD | None |
| assured-render | REQ-assured-render-001 | `` `render_module_scope` SHALL produce markdown containing all REQ, DES, TEST...`` | DRIFTER | **Rewritten** |
| assured-render | REQ-assured-render-002 | `` `render_module_dependency_graph` SHALL emit a markdown edge-list...`` | DRIFTER | **Rewritten** |
| assured-skills | REQ-assured-skills-001 | *(excluded — rewritten task 27)* | — | Excluded |
| assured-skills | REQ-assured-skills-002 | `The \`req-link\` skill SHALL verify that both the source ID and every target ID...` | BORDERLINE | None |
| assured-skills | REQ-assured-skills-003 | `The \`code-annotate\` skill SHALL detect the comment syntax for the file's language...` | BORDERLINE | None |
| assured-skills | REQ-assured-skills-004 | `The \`module-bound-check\` skill SHALL run all five decomposition validators...` | BORDERLINE | None |
| assured-skills | REQ-assured-skills-005 | `The \`kb-codeindex\` skill SHALL be idempotent: re-running it on a project...` | BORDERLINE | None |
| assured-skills | REQ-assured-skills-006 | `The \`change-impact-annotate\` skill SHALL scaffold a \`CHG-NNN\` record...` | GOOD | None |
| assured-skills | REQ-assured-skills-007 | `The \`traceability-render\` skill SHALL write a file to \`docs/traceability/...` | GOOD | None |
| assured-substrate | REQ-assured-substrate-001 | `The \`commission-assured\` skill SHALL scaffold \`programs.yaml\`, \`library/\`...` | BORDERLINE | None |
| assured-substrate | REQ-assured-substrate-002 | `The Assured Constitution articles 15-17 SHALL overlay articles 1-14 cleanly...` | GOOD | None |
| assured-substrate | REQ-assured-substrate-003 | `The \`change_impact_gate\` validator SHALL be opt-in (default disabled)...` | DRIFTER | **Rewritten** |
| assured-traceability-validators | REQ-assured-traceability-validators-001 | `The reference-integrity validators (\`id_uniqueness\`, \`cited_ids_resolve\`) SHALL...` | BORDERLINE | None |
| assured-traceability-validators | REQ-assured-traceability-validators-002 | `The directional-coverage validators (\`forward_link_integrity\`, \`backward_coverage\`)...` | BORDERLINE | None |
| assured-traceability-validators | REQ-assured-traceability-validators-003 | *(excluded — rewritten task 26)* | — | Excluded |
| assured-traceability-validators | REQ-assured-traceability-validators-004 | `` `annotation_format_integrity` SHALL scan source files for `# implements:`...`` | DRIFTER | **Rewritten** |
| assured-traceability-validators | REQ-assured-traceability-validators-005 | *(excluded — new task 23, already capability-shaped)* | — | Excluded |
| kb-bridge-mode | REQ-kb-bridge-mode-001 | `The synthesis-librarian agent MUST recognise a \`mode: synthesise-across-spec-types\`...` | GOOD | None |
| kb-bridge-mode | REQ-kb-bridge-mode-002 | `When the SYNTHESISE-ACROSS-SPEC-TYPES mode is active, the agent's \`valid_handles\`...` | BORDERLINE | None |
| programme-skills | REQ-programme-skills-001 | `The \`commission-programme\` skill SHALL scaffold a feature directory...` | BORDERLINE | None |
| programme-skills | REQ-programme-skills-002 | `The \`phase-init\` skill SHALL create the phase-appropriate spec file...` | BORDERLINE | None |
| programme-skills | REQ-programme-skills-003 | `The \`phase-gate\` skill SHALL invoke the corresponding gate function...` | DRIFTER | Deferred v0.3.0 |
| programme-skills | REQ-programme-skills-004 | `The \`phase-review\` skill SHALL record a dated review entry in the feature directory...` | GOOD | None |
| programme-skills | REQ-programme-skills-005 | `The \`traceability-export\` skill SHALL produce a REQ→DES→TEST→CODE traceability matrix...` | GOOD | None |
| programme-substrate | REQ-programme-substrate-001 | `The spec parser SHALL deserialise a phase spec file into a structured \`ParsedSpec\`...` | DRIFTER | Deferred v0.3.0 |
| programme-substrate | REQ-programme-substrate-002 | `The traceability matrix builder SHALL produce one row per REQ-ID covering its...` | GOOD | None |
| programme-substrate | REQ-programme-substrate-003 | `The Constitution SHALL define Articles 12-14 prescribing the mandatory four-phase...` | GOOD | None |
| programme-validators | REQ-programme-validators-001 | `The requirements gate SHALL pass if and only if the REQ spec file parses...` | GOOD | None |
| programme-validators | REQ-programme-validators-002 | `The design gate SHALL pass if and only if the DES spec file parses without error...` | GOOD | None |
| programme-validators | REQ-programme-validators-003 | `The test gate SHALL pass if and only if the TEST spec file parses without error...` | GOOD | None |
| programme-validators | REQ-programme-validators-004 | `The code gate SHALL pass if and only if the supplied code text contains...` | GOOD | None |

*Borderline note: BORDERLINE REQs name a skill in the subject position but the bulk of the requirement is a user-visible behavioural contract. Skill names in Programme-skills and assured-skills REQs are analogous to naming a user-facing command — they do not cross into implementation detail. Not counted as DRIFTERs.*

## Rewrites applied (in this commit)

10 DRIFTERs rewritten inline (at or within the R7 cap of 10).

### 1. REQ-assured-export-formats-001

**Old:** `` `export_do178c_rtm` SHALL produce a Requirements Traceability Matrix conformant to DO-178C's expected column structure — HLR ... | LLR ... | Source code | Test case — with a document header identifying the standard.``

**New:** `Auditors working under DO-178C MUST be able to produce a Requirements Traceability Matrix from project artefacts in the standard-prescribed four-column format (HLR | LLR | Source code | Test case) with a document header that identifies the DO-178C standard, so that the matrix can be submitted without manual reformatting.`

### 2. REQ-assured-export-formats-002

**Old:** `` `export_iec_62304_matrix` SHALL emit a Software Traceability Matrix with columns Software requirement | Software unit | Verification activity, and SHALL declare the software safety class (A, B, or C) in the document header.``

**New:** `Auditors working under IEC 62304 MUST be able to produce a Software Traceability Matrix from project artefacts with columns (Software requirement | Software unit | Verification activity) and a document header that declares the software safety class (A, B, or C), so that the matrix meets the IEC 62304 documentary expectation without post-processing.`

### 3. REQ-assured-export-formats-003

**Old:** `` `export_iso_26262_asil_matrix` SHALL emit an ASIL-tagged traceability matrix with columns Safety requirement | Architectural element | Implementation | Verification, and SHALL declare the declared ASIL level (A, B, C, or D) in the document header.``

**New:** `Auditors working under ISO 26262 MUST be able to produce an ASIL-tagged traceability matrix from project artefacts with columns (Safety requirement | Architectural element | Implementation | Verification) and a document header that declares the ASIL level (A, B, C, or D), so that the matrix satisfies the ISO 26262 evidence expectation without manual annotation.`

### 4. REQ-assured-export-formats-004

**Old:** `` `export_fda_dhf_structure` SHALL organise traceability artefacts under the four design-control sections of 21 CFR §820.30 ... with each section citing the relevant regulatory clause. Generic non-regulatory exporters (`export_csv`, `export_markdown`) SHALL produce a four-column REQ | DES | TEST | CODE matrix ...``

**New:** `Auditors working under FDA 21 CFR §820.30 MUST be able to produce a Design History File structure from project artefacts organised under the four design-control sections (Design inputs §820.30(c) | Design outputs §820.30(d) | Design verification §820.30(f) | Design validation §820.30(g)), each citing the relevant regulatory clause. Non-regulatory consumers MUST be able to obtain the same artefact set as a four-column REQ | DES | TEST | CODE matrix in both CSV and Markdown formats.`

### 5. REQ-assured-traceability-validators-004

**Old:** `` `annotation_format_integrity` SHALL scan source files for `# implements:` annotation lines and report a blocking error for each token that fails the ID format parse AND a separate blocking error for each well-formed token that cites an ID not present in the caller-supplied declared set.``

**New:** `The Assured bundle MUST detect malformed or dangling \`# implements:\` annotations before a phase gate, reporting a blocking error for each annotation token that fails the ID format rule and a separate blocking error for each well-formed token that cites an ID absent from the declared set — so that broken annotations cannot silently corrupt the traceability graph.`

### 6. REQ-assured-code-index-001

**Old:** `` `parse_code_annotations` SHALL extract every `# implements:` annotation from the supplied list of source files, returning each as a `CodeIndexEntry` with the relative file path, the line number, and the list of cited IDs parsed from the annotation; files that do not exist SHALL be silently skipped; ID tokens SHALL conform to the pattern recognised by `_ID_TOKEN_RE` (flat `KIND-feature-NNN` or positional `P1.SP1.M1.KIND-NNN`).``

**New:** `The Assured bundle MUST be able to extract every \`# implements:\` annotation from a supplied list of source files, capturing for each the relative file path, the line number, and the cited IDs in both flat (\`KIND-feature-NNN\`) and positional (\`P1.SP1.M1.KIND-NNN\`) forms — so that callers can build a complete code-index without implementing annotation parsing themselves. Non-existent files in the list MUST be silently skipped rather than raising an error.`

### 7. REQ-assured-code-index-002

**Old:** `` `render_code_index` and `render_spec_findings` SHALL each emit a shelf-index-shaped Markdown document — beginning with the standard four-field header comment block ... such that the document is directly queryable by the existing `research-librarian` agent without modification to the agent or the librarian dispatch layer.``

**New:** `The Assured bundle MUST produce code-index and spec-findings documents in the shelf-index Markdown format (standard four-field header comment block followed by numbered \`## N. <title>\` sections with \`**Terms:**\`, \`**Facts:**\`, and \`**Links:**\` fields) so that the \`research-librarian\` agent can query them without any modification to the agent or the librarian dispatch layer.`

### 8. REQ-assured-render-001

**Old:** `` `render_module_scope` SHALL produce markdown containing all REQ, DES, and TEST artefacts assigned to the given module, plus their citing code annotations, plus an "Orphan code" section listing code annotations whose cited IDs do not exist in the registry.``

**New:** `A team member or auditor MUST be able to produce a human-readable module-scope document listing all REQ, DES, and TEST artefacts assigned to a given module together with their citing code annotations, plus an "Orphan code" section for annotations whose cited IDs do not exist in the registry — so that the full traceability state of a module is visible at a glance.`

### 9. REQ-assured-render-002

**Old:** `` `render_module_dependency_graph` SHALL emit a markdown edge-list (Q1 v0.1.0 format) showing every observed cross-module edge with an Allowed?/yes/NO column derived from the visibility block in the project decomposition.``

**New:** `A team member or auditor MUST be able to produce a markdown edge-list showing every observed cross-module dependency with an Allowed?/yes/NO column derived from the project's declared visibility block — so that undeclared module boundaries can be identified at a glance.`

### 10. REQ-assured-substrate-003

**Old:** `The \`change_impact_gate\` validator SHALL be opt-in (default disabled) and SHALL be configurable via \`.sdlc/team-config.json\` using the key \`assured.change_impact_gate\` with permitted values \`enabled\` and \`disabled\`; the validator SHALL read the configuration on every invocation and apply the gate only when the value is \`enabled\`.`

**New:** `Teams operating in regulated contexts MUST be able to opt in to a change-impact gate that blocks commits lacking a CHG record, configured via \`.sdlc/team-config.json\` using the key \`assured.change_impact_gate\` (\`enabled\` | \`disabled\`, default \`disabled\`) — so that the gate is never imposed silently on projects that have not explicitly requested it.`

## Deferred to v0.3.0

6 DRIFTERs deferred (budget cap R7: ≤10 inline rewrites per release):

| REQ ID | Rationale for deferral |
|--------|------------------------|
| REQ-assured-decomposition-validators-002 | Opens with `code_annotation_maps_to_module` function name; lower audit-readiness priority than export formatters |
| REQ-assured-decomposition-validators-003 | Opens with `visibility_rule_enforcement` function name; same group, batch with -002 |
| REQ-assured-decomposition-validators-004 | Opens with `anaemic_context_detection` function name; same group |
| REQ-assured-decomposition-validators-005 | Opens with `granularity_match` function name; same group |
| REQ-programme-skills-003 | Opens with `` `phase-gate` skill SHALL invoke the corresponding gate function`` — "invoke the gate function" reveals internal dispatch; less critical than regulated exporters |
| REQ-programme-substrate-001 | Opens with "The spec parser SHALL deserialise ... into a structured `ParsedSpec` object" — implementation type leak; lower regulatory exposure than Assured |

## Validator integrity check (post-rewrite)

```
id_uniqueness: True
cited_ids_resolve: True
forward_link_integrity: True
```

All three validators passed on the post-rewrite registry. REQ IDs unchanged; no new REQs added; `**Module:**` and `**Related:**` fields preserved on all edited REQs.

## Conclusion

The v0.1.0 REQ corpus was authored in a single Phase F dogfood session where speed was prioritised over authoring discipline. Of the 40 audited REQs, 16 (40%) opened with a Python function name or return-type identifier rather than a user-visible capability statement — a clear F-010 pattern. The most severe cases were the four regulated-industry export formatters (DO-178C, IEC 62304, ISO 26262, FDA DHF), whose REQs read as function docstrings rather than auditor-facing obligations; these were the highest-priority rewrites since they are the REQs most likely to be read by a regulator. Within the R7 budget cap of 10 inline rewrites, the 10 highest-impact DRIFTERs were rewritten to open with WHO (auditor / team member / the Assured bundle) does WHAT and WHY. Six lower-priority DRIFTERs — the four `assured-decomposition-validators` function-named REQs plus two programme-bundle REQs — are deferred to v0.3.0 as a coherent batch rewrite. The 20 GOOD REQs and 4 BORDERLINE REQs needed no changes; BORDERLINEs name user-facing skill commands in subject position, which is analogous to naming a CLI tool — not an implementation detail.

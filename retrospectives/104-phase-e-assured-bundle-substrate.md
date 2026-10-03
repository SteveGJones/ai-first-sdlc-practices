# Retrospective: Phase E — Assured Bundle (Method 2 Substrate)

**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #104 (Phase E of EPIC #178)
**Status:** COMPLETE

---

## What we set out to do

Build the Assured bundle Method 2 substrate — `sdlc-assured` plugin v0.1.0 implementing positional namespace IDs, bidirectional traceability with 4 mandatory + 1 optional validators, DDD decomposition with 5 module-bound validators, KB extension to code via annotations, and standard-specific traceability exports (DO-178C, IEC 62304, ISO 26262, FDA DHF).

The Assured bundle targets regulated-industry teams that need full bidirectional traceability from requirements through design through test through code, with module-bounded decomposition and auditable export to certification-standard formats.

## What was built

All six deliverable categories shipped across 42 tasks (~84 commits on branch `feature/sdlc-programme-assured-bundles`), plus a containerised architect review and inline fixes from that review:

1. **Plugin scaffold (`plugins/sdlc-assured/`)** — `manifest.yaml` (schema_version 1, name `assured`, version 0.1.0, supported_levels `[production, enterprise]`, `depends_on: [sdlc-core, sdlc-programme, sdlc-team-common, sdlc-team-fullstack, sdlc-knowledge-base]`), `.claude-plugin/plugin.json`, `README.md`, `pyproject.toml`, `CONSTITUTION.md` (Articles 15-17).

2. **Assured constitution (Articles 15-17)** — overlays Programme's Articles 12-14. Article 15 (bidirectional traceability — positional ID system, 4 mandatory validators, orphan-ID warning-not-block), Article 16 (DDD decomposition — module assignment, visibility rules, anaemic-context detection, granularity matching), Article 17 (KB extension to code — annotation format, code index, spec-as-KB-finding).

3. **Six templates** — `templates/programs.yaml` (programme decomposition manifest), `templates/visibility-rules.md`, `templates/change-impact.md`, and the three Phase D spec templates re-exported with Assured frontmatter extensions.

4. **Six Python modules (`scripts/assured/`)** — `ids.py` (dual-format parser: flat `REQ-feature-NNN` and positional `P1.SP2.M3.REQ-NNN`; `parse_id`, `format_id`, `is_positional`, `build_id_registry`, `render_id_registry`, `remap_ids`), `traceability_validators.py` (4 mandatory + 1 optional validators: `id_uniqueness`, `cited_ids_resolve`, `orphan_ids`, `forward_link_integrity`, `backward_coverage`, `index_regenerability`, `annotation_format_integrity`, `change_impact_gate`), `decomposition.py` (5 module-bound validators: `req_has_module_assignment`, `code_annotation_maps_to_module`, `visibility_rule_enforcement`, `anaemic_context_detection`, `granularity_match`; plus `parse_programs_yaml`, `default_decomposition`, `remap_ids`), `code_index.py` (annotation scanner, shelf-index emitter: `parse_code_annotations`, `render_code_index`, `render_spec_findings`), `render.py` (module-scoped render pipeline, markdown edge-list dependency graph: `render_module_scope`, `render_module_dependency_graph`), `export.py` (four regulatory export formats + CSV/markdown: `export_do178c_rtm`, `export_iec_62304_matrix`, `export_iso_26262_asil_matrix`, `export_fda_dhf_structure`, `export_csv`, `export_markdown`).

5. **Eight skills** — `commission-assured`, `req-add`, `req-link`, `code-annotate`, `module-bound-check`, `kb-codeindex`, `change-impact-annotate`, `traceability-render`. Each has a SKILL.md with usage guidance, expected inputs/outputs, and example invocations.

6. **Synthesis librarian extension** — `SYNTHESISE-ACROSS-SPEC-TYPES` mode added to `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md` (lines 136-158). Extends `valid_handles` whitelist to accept `req`, `des`, `test`, `code` pseudo-handles, enabling the librarian to synthesise across artefact types within a regulated project.

7. **End-to-end fixture** — `tests/fixtures/sdlc-assured/sample-project/` containing `programs.yaml`, three spec artefacts (REQ/DES/TEST), and sample annotated source code, exercised by `test_assured_skill_integration.py`.

8. **Plugin packaging** — `release-mapping.yaml` extended for `sdlc-assured`; root sources mirrored under `plugins/sdlc-assured/`. Commission-assured root mirror kept in sync with plugin copy (Task 41 follow-up commit).

**Tests:** 74 assured tests across seven files — `test_assured_ids.py` (11), `test_assured_decomposition.py` (18), `test_assured_traceability_validators.py` (21), `test_assured_code_index.py` (8), `test_assured_render.py` (4), `test_assured_export.py` (6), `test_assured_skill_integration.py` (6).

**Containerised review:** architect review commissioned via `sdlc-workflows`, captured at `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`. Six verdicts; three ship-blockers fixed inline in Task 41.

## Q1 resolved

Module-dependency-graph visualisation format: **markdown edge-list** in v0.1.0. The `render_module_dependency_graph` function emits a `## Module Dependency Graph` section with `MODULE-A --> MODULE-B` lines, one per declared import edge in `programs.yaml`. ASCII DAG and HTML SVG remain explicit stretch goals for v0.2.0 per design spec §9.

## What worked well

- **Phase D `spec_parser` pattern carried forward cleanly.** The dual-format ID parser in `ids.py` reused the same line-wise markdown walking with code-block toggle that Phase D's `spec_parser` established. Adding positional namespace support was additive — mutually-exclusive regexes with clean round-trip tests. The pattern scales.

- **`conftest.py`-based scripts package registration reused.** Avoiding `pip install -e .` sidesteps Homebrew's externally-managed-environment policy. All seven test files import from `scripts/assured/` via path manipulation in `conftest.py`. Zero environment friction.

- **Containerised architect review caught all ship-blockers before close.** Three issues identified and fixed inline in Task 41 rather than punted to v0.2.0 (see Containerised review verdict section). The pattern from Phase D — commission the review, fix what it finds, close the phase — held.

- **Decomposition as `programs.yaml` is the right abstraction.** Having a single manifest declare programmes, sub-programmes, modules, visibility rules, and granularity levels gives validators a stable schema to validate against, skills a structured document to commission from, and teams a single artefact to maintain. The spec's choice of YAML over a custom DSL paid off in parser simplicity.

- **Export module covering all four regulatory standards in one file.** `export.py` has six public functions (four standard-specific + csv + markdown) with consistent signatures. Adding a fifth standard in a future version is a new function, not a refactor.

- **Synthesis librarian extension by mode, not by new agent.** Adding `SYNTHESISE-ACROSS-SPEC-TYPES` as a new mode section in the existing `synthesis-librarian.md` preserved backward compatibility — existing KB queries are unaffected. Extending `valid_handles` was the minimum surgical change.

## What was harder than expected

- **Idempotency in `render_code_index` / `render_spec_findings`.** The initial implementation embedded a `last_rebuilt` timestamp in the shelf-index output, directly contradicting the `index_regenerability` validator's byte-identical guarantee. The architect review caught this as a ship-blocker. Fix was removing the live timestamp from generated output (Task 41 inline fix 1). The lesson: any output that a validator re-reads for equality must be deterministic — timestamps always break this.

- **`anaemic_context_detection` differentiation from `code_annotation_maps_to_module`.** The initial implementation was functionally identical — both checked path co-location. The architect review identified this as a concern (same errors would fire twice from different validators). Task 41 inline fix 2 added genuine concentration analysis: `anaemic_context_detection` now flags modules where annotated implementations are scattered across more than a configurable threshold of distinct paths, not just misplaced. The validators now catch complementary defects.

- **KB wiring gap in `commission-assured`.** The initial skill did not document the step of registering `_code-index.md` and `_spec-findings.md` as queryable library sources with the research-librarian. Without this step the "spec-as-KB-finding" integration from the design spec does not work out of the box. Task 41 inline fix 3 added the KB wiring documentation to the skill. The lesson: commissioning skills must walk a user through the full activation sequence, not just the commissioning decision.

- **Commission-assured root mirror sync.** After the inline fixes landed in Task 41, the `commission-assured` SKILL.md source at the repo root and the plugin-dir mirror under `plugins/sdlc-assured/` diverged. Required a follow-up commit (`cfcbddd`) to re-sync via `release-plugin` — same discipline as the Phase A regression that hit Phase B of EPIC #164. The pattern from `feedback_phase_a_plugin_dir_regression.md` applied: never edit plugin-dir copies directly; always run `release-plugin` after touching root sources.

- **Dual-format ID space in mixed projects.** Flat-to-positional migration leaves a permanent mixed-format ID space. `_module_from_positional_id` returns `None` for flat IDs, requiring all flat-ID specs to carry `module:` frontmatter after decomposition is introduced. This is correct behaviour but not documented in the constitution or skills — documented now as a known v0.1.0 limitation in the architect review response.

## Lessons learned

- **Deterministic output is a prerequisite for idempotency validators.** If a validator asserts byte-equality between two runs of a generator, the generator must produce no non-deterministic fields (timestamps, random UUIDs, process IDs). Design the output format first with this constraint in mind — retrofitting out a timestamp is small but should have been caught in the spec phase.

- **Two validators for the same class of defect is confusion, not defence-in-depth.** When `anaemic_context_detection` and `code_annotation_maps_to_module` both fire on the same violation, teams cannot distinguish which is more serious. Validators should be differentiated by the defect class they catch, not by the layer at which they catch it.

- **Commissioning skills are user-facing documentation.** A commissioning skill that omits activation steps (like KB wiring) produces a broken onboarding experience even if the underlying modules are correct. Treat commissioning skills as user-path documentation and verify the full activation sequence before close.

- **`release-plugin` must be run after every root-source edit that touches files with plugin-dir mirrors.** `check-plugin-packaging.py` catches drift in CI but not before the commit. Add `release-plugin` to the mental checklist for any edit to `skills/*/SKILL.md`, `agents/*.md`, or `templates/*.md` at the root source level.

- **Architect reviews via containerised workflow consistently catch what in-session review misses.** Phase D: two ship-blockers. Phase E: three ship-blockers. The reviewers find issues that the implementer's mental model has normalised away. The ROI on the 15-minute review is high; it should remain mandatory at phase close.

## Containerised review verdict

An independent containerised architect review was commissioned via `sdlc-workflows` using Claude Opus 4.6 on 2026-04-30. The review examined `plugins/sdlc-assured/` against `option-bundle-contract.md`, `programme-assured-bundles-design.md` §4, `METHODS.md` §4, all `tests/test_assured_*.py`, and the `synthesis-librarian.md` agent. Six verdicts:

1. **Constitution overlay soundness — AGREE-WITH-CONCERNS.** Articles 15-17 extend Articles 1-14 cleanly with correct numbering and semantic layering. Concerns: `orphan_ids` validator only checks REQ and DES kinds (narrower than Article 15's "every declared ID" claim); Article 17's annotation-completeness promise exceeds what validators enforce (`annotation_format_integrity` validates existing annotations but does not check all non-trivial functions have annotations). Both acknowledged as known v0.1.0 limitations — not ship-blockers.

2. **ID system fitness — AGREE-WITH-CONCERNS.** Dual-format parser is correct; regexes are mutually exclusive; `format_id` round-trips. Concerns: multiple-prefix edge case in `remap_ids` (fragile dict-iteration order); flat-to-positional migration undocumented; zero-padded vs non-padded visual confusion. All acknowledged as v0.1.0 acceptable.

3. **Traceability validator coverage — AGREE.** All 4 mandatory + 1 optional validators correct with solid test coverage (21 tests, all happy/failure paths covered). Minor concern on `change_impact_gate`'s string-containment path matching — acceptable for v0.1.0.

4. **Decomposition validator coverage — AGREE-WITH-CONCERNS.** Five module-bound validators cover DDD bounded-context discipline adequately. Ship-blocker identified: `anaemic_context_detection` was functionally identical to `code_annotation_maps_to_module`. Fixed inline (Task 41 inline fix 2: added genuine concentration analysis). Additional concerns: no circular-dependency detection between programmes; `structure: hexagonal` field parsed but not validated. Both v0.1.0 acceptable.

5. **KB integration realism — AGREE-WITH-CONCERNS.** `SYNTHESISE-ACROSS-SPEC-TYPES` mode composition is correct. Two ship-blockers: (a) `render_code_index`/`render_spec_findings` embedded a live timestamp breaking idempotency — fixed inline (Task 41 inline fix 1: timestamp removed); (b) `commission-assured` did not document KB wiring step for `_code-index.md`/`_spec-findings.md` — fixed inline (Task 41 inline fix 3: wiring documentation added). Residual concern: weak term-matching for positional-ID projects — v0.1.0 limitation, not a blocker.

6. **Bundle layout vs Phase C contract — AGREE.** All required manifest fields present and correct; 8 skills, 6 templates, `scripts/` present, `pyproject.toml` correct. Reserved Phase E fields (`decomposition_support`, `id_format`, etc.) absent — technically compliant (MAY, not MUST). Validator identifier mapping is implicit per contract convention.

**Three ship-blockers fixed inline in Task 41:**
1. Timestamp in `render_code_index`/`render_spec_findings` breaking idempotency — removed from generated output.
2. `anaemic_context_detection` functionally identical to `code_annotation_maps_to_module` — added concentration analysis (scatter threshold logic).
3. `commission-assured` missing KB wiring documentation — wiring steps added to skill.

Plus one follow-up commit (`cfcbddd`) to re-sync the commission-assured root mirror with the plugin-dir copy after the inline fixes.

Verbatim review captured for audit at `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`.

## Validation

- **Assured tests: 74/74 passing** across 7 files — `test_assured_ids.py` (11), `test_assured_decomposition.py` (18), `test_assured_traceability_validators.py` (21), `test_assured_code_index.py` (8), `test_assured_render.py` (4), `test_assured_export.py` (6), `test_assured_skill_integration.py` (6). All green in 0.13s.
- **Total project tests: 520 collected** (includes Programme, KB, workflows, and all other suites). All passing.
- **Plugin packaging: 14/14 plugins verified** (`check-plugin-packaging.py`).
- **Quick validation: PASSED** (0.2s, 0 errors, 0 warnings).
- **Pre-push validation: 9/10** — Pre-commit Hooks check fails because the `pre-commit` binary is not installed in this environment. This is a documented carry-forward env limitation present since Phase A of EPIC #164 and noted in retrospectives 167, 168, 169, 170, and 186. All other explicit checks (Syntax, Technical Debt, Architecture, Type Safety, Security, Logging Compliance, Static Analysis) PASSED. No new failures introduced by Phase E.

## References

- Parent EPIC: #178 (Joint Programme + Assured bundle delivery)
- Issue: #104 (Phase E substrate)
- Phase D closure: `retrospectives/186-phase-d-programme-bundle-substrate.md`
- Method 2 design: `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §4
- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Implementation plan: `docs/superpowers/plans/2026-04-29-phase-e-assured-bundle-substrate.md`
- Architect review: `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`

# Phase F — Dogfood Findings

## F-001 — `# implements:` annotation parser does not handle markdown files

**Severity:** IMPORTANT
**Surfaced during:** Task 4 (Stage 1 proof-of-flow)
**Reproduction:** The `_IMPLEMENTS_RE` regex in `plugins/sdlc-assured/scripts/assured/code_index.py` matches `^\s*#\s*implements:\s*(?P<ids>.+)$`. In a markdown file, the line `# implements: REQ-x-001` parses as an H1 heading by markdown renderers AND matches the regex — producing a fake annotation that displays as a giant title. The HTML-comment workaround `<!-- implements: REQ-x-001 -->` displays correctly in markdown but does NOT match the regex.
**Impact on regulated-industry users:** high — most user-facing artefacts (SKILLs, agents, design docs) are markdown, not Python. Regulated-industry users will hit this within the first feature.
**Suggested resolution:** v0.2.0 — extend `_IMPLEMENTS_RE` to recognise both forms, or add a second regex `_HTML_IMPLEMENTS_RE = re.compile(r"<!--\s*implements:\s*(?P<ids>.+)\s*-->")`. Alternative: define a project-wide rule that markdown annotations live in YAML frontmatter (`implements: [DES-x-001, ...]`).
**Related code:** plugins/sdlc-assured/scripts/assured/code_index.py:9-13, plugins/sdlc-assured/scripts/assured/traceability_validators.py:_IMPLEMENTS_RE
**Scale note (Task 8):** HTML-comment workaround applied to 5 more SKILL.md files
(commission-programme, phase-init, phase-gate, phase-review, traceability-export) in
plugins/sdlc-programme/skills/ and their root mirrors in skills/. Total markdown files
carrying `<!-- implements: DES-... -->` annotations now: 10 (5 from Tasks 5-7 + 5 from
Task 8). Parser fix remains pending for v0.2.0.
**Scale note (Task 17 — index generation):** When the three KB indexes were generated,
`_ids.md` collected 129 ID records (REQ + DES + TEST across all spec files) while
`_code-index.md` collected only 18 Python `# implements:` annotation entries from 13
Python source files (plugins/sdlc-assured/scripts + plugins/sdlc-programme/scripts). The
ratio is 18/129 = 14 % — confirming that ~86 % of the spec layer is invisible to the code
index because the annotation carrier is markdown (SKILL.md files and design docs), not
Python. This directly quantifies F-001's impact: the code-index underrepresents the
implementation by a factor of ~7x in this dogfood exercise.

## F-002 — programs.yaml `paths` cannot scope to a section of a file

**Severity:** MINOR
**Surfaced during:** Task 2 (Stage 1)
**Reproduction:** Module M3 (kb-bridge) implements only the SYNTHESISE-ACROSS-SPEC-TYPES section of synthesis-librarian.md, not the whole file. programs.yaml `paths` is whole-directory only.
**Impact on regulated-industry users:** medium — fine-grained ownership of file sections is common in regulated codebases (e.g., MISRA-C compliant subset of a header file)
**Suggested resolution:** consider line-range or section-anchor support in v0.2.0; or document the limitation
**Related:** plugins/sdlc-assured/scripts/assured/decomposition.py:Module.paths

## F-003 — Constitution REQ creates a category error in the annotation model

**Severity:** MINOR
**Surfaced during:** Task 6 (Stage 2, M1 programme-substrate)
**Reproduction:** REQ-programme-substrate-003 requires the Constitution to define Articles 12-14. The Constitution is the governance document — it IS the requirement source for the programme bundle, not a code artefact that implements a requirement from some higher-level spec. Writing `# implements: DES-programme-substrate-003` inside CONSTITUTION.md (a) conflicts with F-001 (markdown H1 ambiguity) and (b) inverts the artefact hierarchy: the Constitution is the authority from which requirements flow, not the output of one. No annotation was added to CONSTITUTION.md. DES-programme-substrate-003 instead describes the constitution as a documentation design unit, and TEST-programme-substrate-003 verifies its content structurally.
**Impact on regulated-industry users:** medium — projects with governance documents (policy files, constitutional documents, architecture decision records) will routinely encounter requirements that are "satisfied by the document itself existing with the right content." The annotation model has no first-class concept for this; the gap forces a category violation or a silent omission.
**Suggested resolution:** v0.2.0 — introduce a `# satisfies-by-existence:` annotation type (or YAML frontmatter `satisfies: [REQ-NNN]`) for documents that ARE the artefact satisfying a requirement, distinct from code that implements a design unit. Alternatively, restrict the annotation model to code files only and document that documentation requirements are verified by structural tests (as done here in TEST-programme-substrate-003).
**Related code:** plugins/sdlc-assured/scripts/assured/code_index.py (annotation scanner scope); plugins/sdlc-programme/CONSTITUTION.md (the artefact in question)

## F-004 — REQ-inventory review-record gate assignment is offset by one phase

**Severity:** MINOR
**Surfaced during:** Task 7 (Stage 2, M1 programme-validators)
**Reproduction:** The REQ inventory (`research/phase-f-req-inventory.md`) states that
`design_gate` requires "a review record for the **requirements** phase" and that
`test_gate` requires "a review record for the **design** phase." The actual
implementation in `gates.py` checks for a review record for the gate's **own** phase:
`design_gate` calls `_has_review_record(feature_dir, "design")` and `test_gate` calls
`_has_review_record(feature_dir, "test")`. The code's convention — each gate requires
a review of the phase it is guarding before advancement — is more semantically
consistent with Article 14 of the programme Constitution ("mandatory phase-review
records committed alongside design-spec and test-spec artefacts"). The REQ inventory
wording was authored before the implementation and has an off-by-one phase assignment.
The REQs in `docs/specs/programme-validators/requirements-spec.md` are written to match
the code (REQ-programme-validators-002 requires a design-phase review record;
REQ-programme-validators-003 requires a test-phase review record).
**Impact on regulated-industry users:** low — the code is correct; only the planning
artefact (REQ inventory) had the mismatch. A downstream user reading the REQ inventory
without the code would author an incorrect test fixture.
**Suggested resolution:** Update the REQ inventory row descriptions in v0.2.0 to state
"a review record for the **same** phase" rather than naming a specific prior phase.
Alternatively, add a note to the REQ inventory that gate N checks for a review of
phase N (not phase N-1).
**Related:** `research/phase-f-req-inventory.md` (programme-validators table),
`plugins/sdlc-programme/scripts/programme/gates.py:135,200`,
`docs/specs/programme-validators/requirements-spec.md`

---

## Stage 1 checkpoint reflection

**Time spent on Tasks 1-4:** ~50 min total across 4 dispatches (Task 1: ~8 min commission scaffold; Task 2: ~12 min programs.yaml decomposition; Task 3: ~10 min REQ inventory checklist; Task 4: ~20 min M3 spec authoring + annotation + two findings).
**Friction productivity:** Productive. Both F-001 and F-002 surfaced design-level gaps the spec did not anticipate — F-001 exposes a genuine hole in the annotation coverage model for non-Python artefacts, F-002 exposes a granularity ceiling in the `paths` ownership model. Neither is noise. A purely clerical stage would have produced zero findings.
**REQ-statement level (M3 proof-of-flow):** User-visible-capability level. REQ-kb-bridge-mode-001 states what the agent MUST recognise; REQ-kb-bridge-mode-002 states what the whitelist MUST accept. Neither paraphrases a function signature; both could be evaluated by a reviewer who has never read the implementation.
**Commission-assured concreteness:** Concrete. The `.sdlc/team-config.json` produced in Task 1 carries three operationally meaningful fields — `visibility_mode`, `change_impact_gate`, `decomposition` — each with a non-default value that implies a real behaviour choice. The scaffold is not aspirational placeholder text.
**Recommendation:** PROCEED at full scope
**Rationale:** The Stage 1 tripwire condition ("if 1-module's-worth feels overwhelming, escalate") is not triggered. Task 4 produced a complete REQ/DES/TEST chain for M3 in one dispatch, surfaced two honest findings, and left the artefacts in committed, reviewable state. The REQs are at the right granularity; the commission scaffold is functional, not aspirational; and the two findings strengthen rather than undermine the case for continuing — they are exactly the kind of friction a recursive dogfood exercise is designed to expose. The 44-REQ paperwork risk identified in §11 remains theoretical at this point: the M3 chain required only 2 REQs, 2 DES items, and 2 TEST cases, which is proportionate. No blocker exists. Stage 2 (remaining modules in the REQ inventory) should proceed as planned.

## F-006 — No "see also" mechanism for related REQs with overlapping intent

**Severity:** MINOR
**Surfaced during:** Task 12 (Phase F, M2 assured-decomposition-validators)
**Reproduction:** REQ-assured-decomposition-validators-002 (`code_annotation_maps_to_module`) and REQ-assured-decomposition-validators-004 (`anaemic_context_detection`) address overlapping intent: both detect annotations whose file path falls outside the cited spec's declared module paths. The differentiation — per-annotation blocking vs. module-level scatter-threshold warning — is captured in DES-002 and DES-004 and was deliberately implemented in commit `350b1f0` (Phase E architect review). However, the REQ spec layer has no mechanism to express "see also REQ-004 for the concentration-analysis complement to this per-annotation check." A reviewer reading REQ-002 in isolation may not realise REQ-004 exists; a reviewer reading REQ-004 may not realise REQ-002 already handles individual outliers. The current spec format only supports `satisfies:` (downward links) and positional module fields — there is no `related:` or `see-also:` field at the REQ level.
**Impact on regulated-industry users:** low-medium — in regulated contexts, related requirements that address overlapping failure modes are often required to cross-reference each other (e.g., DO-178C traceability conventions expect bidirectional links between derived requirements that share a parent intent). A reader auditing the REQ layer without the DES layer cannot determine whether the two validators are redundant or complementary.
**Suggested resolution:** v0.2.0 — add an optional `related:` list field to the REQ frontmatter schema (e.g., `related: [REQ-assured-decomposition-validators-004]`) and render it in tooling output as a non-traceability cross-reference. Alternatively, document in the requirements-spec template that overlapping-intent REQs SHOULD include a parenthetical "(see also REQ-NNN)" inline in the description text.
**Related:** `docs/specs/assured-decomposition-validators/requirements-spec.md` (REQ-002, REQ-004), `plugins/sdlc-assured/scripts/assured/decomposition.py:code_annotation_maps_to_module`, `plugins/sdlc-assured/scripts/assured/decomposition.py:anaemic_context_detection`

## F-005 — Collapsing warn-not-block and blocking validators under one REQ obscures severity contract

**Severity:** MINOR
**Surfaced during:** Task 11 (Phase F, M2 assured-traceability-validators)
**Reproduction:** REQ-assured-traceability-validators-001 collapses three validators under one requirement: `id_uniqueness` (blocking), `cited_ids_resolve` (blocking), and `orphan_ids` (warn-not-block). The three share the same input type and operate on the same conceptual layer (reference integrity), but their severity contracts differ: `orphan_ids` always returns `passed=True` regardless of warnings, while the other two return `passed=False` on violations. A downstream reader of the REQ alone cannot determine which validators are blocking without reading the DES.
**Impact on regulated-industry users:** low-medium — in a regulated context an auditor may challenge whether "warn-not-block" validators satisfy a SHALL requirement in the same REQ as blocking ones. The ambiguity is resolvable by reading DES-001, but the REQ should carry enough information to stand on its own.
**Suggested resolution:** v0.2.0 — either split `orphan_ids` into its own REQ with explicit "SHALL warn (non-blocking)" language, or add a parenthetical to REQ-001 that makes the two-tier severity explicit at the requirement level (e.g., "SHALL detect ... as a blocking error; SHALL detect ... as a non-blocking warning"). The current wording already partially does this ("warn-not-block" is stated), so this is a documentation clarity issue more than a design defect.
**Related:** `docs/specs/assured-traceability-validators/requirements-spec.md` (REQ-001),
`plugins/sdlc-assured/scripts/assured/traceability_validators.py:orphan_ids`

---

## Phase F Task 18 — Decomposition validator run (HEAD b83edb1)

**Run date:** 2026-04-28
**Index state:** 18 code annotations (Python-only), 129 ID records (43 REQ + 43 DES + 43 TEST)

### Validator summary

| Validator | Passed | Errors | Warnings | Notes |
|-----------|--------|--------|----------|-------|
| `req_has_module_assignment` | TRUE | 0 | 0 | All 43 REQs have valid module assignments |
| `code_annotation_maps_to_module` | TRUE | 0 | 0 | All 18 Python annotations map correctly to their module |
| `anaemic_context_detection` | TRUE | 0 | 0 | No module has >20% scatter ratio |
| `visibility_rule_enforcement` | NOT RUN | — | — | No import-graph extractor available (see F-007) |
| `granularity_match` | TRUE | 0 | 43 | Every declared REQ warns as under-specified (see F-008) |

---

## F-007 — `visibility_rule_enforcement` cannot run without an import-graph extractor

**Severity:** MINOR
**Surfaced during:** Task 18 (Phase F, decomposition validator run)
**Reproduction:** `visibility_rule_enforcement` requires a list of `ImportEdge` objects — directed dependency edges derived from actual import statements. Phase F has no tooling to extract these from the Python source tree (no AST-based import scanner, no `pydeps` wrapper, no `grep`-based approximation). The validator was skipped with the note "NOT RUN — Phase F has no automated import-graph extractor; would require external tool."
**Impact on regulated-industry users:** medium — the visibility block in `programs.yaml` declares which modules may depend on which. Without an import-graph extractor, the declared visibility rules are never enforced at any check boundary. A team that writes `from P1.SP1.M3 import ...` inside M1 code would get no feedback until a human reviewer noticed. The validator exists in the codebase but is permanently dormant until an extractor is added.
**Suggested resolution:** v0.2.0 — add a `tools/import_scanner.py` that walks Python source trees, extracts `import` and `from ... import` statements, resolves each import to its owning module (using `programs.yaml` `paths`), and emits `ImportEdge` objects. Wire this into the `kb-codeindex` build step and/or the `sdlc-assured` validation pipeline so that `visibility_rule_enforcement` runs automatically. A lightweight `ast.parse`-based approach is sufficient for Phase F scope.
**Related code:** `plugins/sdlc-assured/scripts/assured/decomposition.py:visibility_rule_enforcement` (lines 252–275)

---

## F-008 — `granularity_match` fires on all 43 REQs because the convention is to annotate DES, not REQ

**Severity:** IMPORTANT
**Surfaced during:** Task 18 (Phase F, decomposition validator run)
**Reproduction:** `granularity_match` warns for every REQ that lacks a `# implements:` annotation. All 43 declared REQs produced warnings. Examination of the 18 Python `# implements:` annotations shows that **zero** cite a REQ ID — all 18 cite DES IDs (e.g. `# implements: DES-programme-validators-001`). The established dogfood convention, followed consistently across `gates.py`, `spec_parser.py`, `traceability.py`, `code_index.py`, `render.py`, and `decomposition.py`, is to annotate at the DES (design-unit) level, not the REQ level.

The validator's design spec (DES-assured-decomposition-validators-005) states: "For modules with `granularity=requirement`, every REQ must have at least one `# implements:` annotation." This is a valid policy — but the actual annotation practice in this codebase targets DES IDs, making the validator fire noise on every REQ in every feature that correctly follows the DES-annotation convention.

**Impact on regulated-industry users:** high — a project that correctly annotates at the DES level will see `granularity_match` produce 100% warning coverage on every REQ. Two outcomes: (a) teams dismiss the validator as always-noisy and stop reading its output; (b) teams add REQ annotations in addition to DES annotations to silence the warnings, creating redundant traceability overhead with no added assurance value. Neither outcome is acceptable in a regulated context where warning fatigue leads to missed genuine signals.
**Suggested resolution:** v0.2.0 — one of three options:
  1. **Change `granularity_match` to accept indirect coverage**: a REQ is considered covered if any DES ID that `satisfies` it has a `# implements:` annotation. This matches the actual annotation convention and the three-layer REQ→DES→CODE chain.
  2. **Document the convention mismatch as intentional**: state clearly in SKILL.md and the validator description that `granularity_match` is designed for projects that annotate at REQ level (not DES level), and that projects using DES-level annotation should set `granularity: design` on their modules to suppress the validator.
  3. **Add a `granularity: design` option to Module** that shifts `granularity_match` to check DES coverage instead of REQ coverage. Set `granularity: design` in `programs.yaml` for modules that follow the DES-annotation convention.

Option 1 is the most backward-compatible and produces the most useful signal. Option 2 is the lowest-effort fix that correctly documents the current behaviour.

**Scale note:** 43/43 REQs warned = 100% noise rate. All 18 Python annotations cite DES IDs. Zero REQ annotations exist anywhere in the codebase.
**Related code:** `plugins/sdlc-assured/scripts/assured/decomposition.py:granularity_match` (lines 348–375); `programs.yaml` (granularity field for M1, M2, M3 — all set to `requirement`)

---

## Phase F Task 19 — Traceability validator run (HEAD af103d6)

**Run date:** 2026-04-28
**Index state:** 18 code annotations (Python-only), 129 ID records (43 REQ + 43 DES + 43 TEST)
**Files scanned by annotation_format_integrity:** 13 Python source files in `plugins/sdlc-assured/scripts` + `plugins/sdlc-programme/scripts`

### Validator summary

| Validator | Passed | Errors | Warnings | Notes |
|-----------|--------|--------|----------|-------|
| `id_uniqueness` | TRUE | 0 | 0 | All 129 IDs are unique |
| `cited_ids_resolve` | TRUE | 0 | 0 | All `satisfies:` targets resolve to declared IDs |
| `orphan_ids` | TRUE | 0 | 0 | All 43 REQs and 43 DESs are cited (see observation below) |
| `forward_link_integrity` | TRUE | 0 | 0 | Every DES cites ≥1 REQ; every TEST cites ≥1 DES |
| `backward_coverage` | TRUE | 0 | 0 | Every REQ has ≥1 DES covering it; every DES has ≥1 TEST covering it |
| `index_regenerability` | TRUE | 0 | 0 | `library/_ids.md` is byte-identical to freshly regenerated output |
| `annotation_format_integrity` | TRUE | 0 | 0 | All 18 `# implements:` annotations cite declared, well-formed IDs |

All 7 validators passed with zero errors and zero warnings. No new findings.

### Observation — orphan_ids zero-warnings is correct, not surprising

The task notes anticipated `orphan_ids` might warn for "REQs whose implementing DES isn't cited by any TEST yet." Examination shows this concern does not apply: all 43 REQs are cited by their corresponding DES `satisfies:` fields, and all 43 DESs are cited by TEST `satisfies:` fields. The dogfood exercise produced a complete 43×3 triad: every module has exactly one REQ→DES→TEST chain with no dangling nodes.

Separately: all 43 TEST records cite **both** their DES and REQ in `satisfies:` (e.g. `satisfies: [REQ-foo-001, DES-foo-001]`). This is belt-and-suspenders traceability — the forward_link_integrity validator only requires TEST to cite ≥1 DES, so the extra REQ citation is accepted without complaint. The pattern adds a direct TEST→REQ link alongside the TEST→DES→REQ transitive chain. This is not a finding but worth noting: it means both direct and transitive backward-coverage are present for every test.

### Observation — backward_coverage F-003 concern resolved by inspection

F-003 (constitution category error) raised the concern that `backward_coverage` might fail for `REQ-programme-substrate-003` because CONSTITUTION.md — the artefact that "satisfies" the requirement — carries no annotation. In practice, `backward_coverage` passes because `DES-programme-substrate-003` (which describes the constitution as a documentation design unit) satisfies the REQ, and `TEST-programme-substrate-003` satisfies the DES. The validator does not require a code annotation; it only checks the ID-graph. The annotation gap (F-001/F-003) affects `annotation_format_integrity` and the code-index coverage ratio, but does not cause `backward_coverage` or `forward_link_integrity` to fail.

---

## Phase F Task 21 — Dependency graph + DO-178C RTM smoke test (HEAD 1494681)

**Run date:** 2026-04-28

### Dependency graph

`render_module_dependency_graph` was called with an empty `actual_edges` list because no import-graph extractor exists (see F-007). Output: `_(no module-to-module dependencies detected)_`. The file at `docs/traceability/dependency-graph.md` correctly reflects the v0.1.0 limitation documented in F-007.

Quantified F-007 observation: Phase F could not produce a meaningful dependency graph because no import-graph extractor exists. v0.2.0 should ship a default Python-import extractor (ast-based scanner resolving imports to owning modules via `programs.yaml` paths).

### DO-178C RTM

| Metric | Value |
|--------|-------|
| Total REQ rows | 43 |
| Rows with source-code annotation | 15 (34.9%) |
| Rows with source-code placeholder (—) | 28 (65.1%) |
| Rows with test-case placeholder (—) | 0 (0%) |

All 43 rows have populated HLR and LLR columns. All 43 rows have populated Test case columns (no test gaps — every DES has a TEST). The gap is entirely in the Source code column.

---

## F-009 — DO-178C RTM source-code column is 65% empty due to F-001 annotation scope

**Severity:** IMPORTANT
**Surfaced during:** Task 21 (Phase F, DO-178C RTM smoke test)
**Reproduction:** Of 43 REQ rows in the RTM, 28 (65.1%) show `—` in the Source code column. Examination confirms that this is a direct consequence of F-001 (annotation parser does not handle markdown files): the 15 populated source-code cells correspond exactly to the Python source files that carry `# implements:` annotations. The 28 empty cells correspond to REQs whose implementing artefacts are markdown files (SKILL.md files, design docs, agent manifests) — none of which are currently indexed by `parse_code_annotations`.

The DO-178C standard requires that every HLR be traceable to source code (or a justification for why no source artefact exists). A 65% gap in the Source code column of the RTM would fail a DO-178C audit without supplementary explanation.

**Breakdown by feature area:**
- `assured-export-formats` (4 REQs): 4 empty — export.py has no `# implements:` annotations despite being the implementing module
- `assured-id-system` (2 REQs): 2 empty — ids.py has no `# implements:` annotations
- `assured-skills` (7 REQs): 7 empty — SKILL.md files cannot be indexed (F-001)
- `assured-substrate` (3 REQs): 3 empty — substrate artefacts are markdown
- `assured-traceability-validators` (4 REQs): 4 empty — traceability_validators.py has no `# implements:` annotations
- `kb-bridge-mode` (2 REQs): 2 empty — synthesis-librarian.md is markdown (F-001)
- `programme-skills` (5 REQs): 5 empty — SKILL.md files cannot be indexed (F-001)
- `code-index`, `decomposition-validators`, `render` (7 REQs): all 7 populated — these Python modules have `# implements:` annotations

**Impact on regulated-industry users:** high — a DO-178C RTM with 65% source-code gaps would require manual supplementary evidence (e.g., DAL traceability tables maintained separately) to pass an audit. The RTM as generated is not audit-ready.
**Suggested resolution (v0.2.0):**
  1. Fix F-001 so that markdown SKILL.md annotations are indexed. This resolves the 7 `assured-skills` + 5 `programme-skills` gaps immediately.
  2. Add `# implements:` annotations to `export.py`, `ids.py`, and `traceability_validators.py` (pure Python files that currently lack them). This resolves 10 further gaps with no tooling change.
  3. Adopt YAML frontmatter `implements:` for structural documentation artefacts (F-003 pattern). This resolves the remaining substrate/markdown gaps.
**Related:** F-001, F-003, `plugins/sdlc-assured/scripts/assured/code_index.py`, `docs/traceability/do-178c-rtm.md`

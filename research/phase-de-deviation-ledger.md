# Phase D-F Implementer Deviation Ledger

**Purpose:** auditable list of deviations from the implementation plan that the controller (Claude, this session) accepted from implementer subagents during EPIC #178 Phases D-F.

**Why this exists:** the 2026-05-01 iOS architect review (`reviews/2026-05-01-ios-location-services-architect-review.md` §3.6) recommended a deviation ledger to make accepted deviations auditable rather than buried in commit messages or implementer reports. The session meta-retrospective §3.4 acknowledged that "the aggregate of small accepted deviations may have moved the artefacts in directions I didn't fully audit." This ledger lets a reviewer reconstruct which deviations were intentional design evolution vs. expedient acceptance.

**Scope:** Phase D Tasks 14-15 + all of Phase E (42 tasks) + all of Phase F (22 tasks). Phases A-C deviations were tracked in their own retros and not re-audited here.

**Format per entry:**
- **Phase / Task:** which task surfaced the deviation
- **Commit:** the SHA where the deviation landed
- **What the plan said:** the original prescription
- **What the implementer did instead:** the actual change
- **Controller's decision:** accept / reject / fix-and-merge
- **Rationale:** why the controller decided as it did
- **Reviewer-verifiable:** whether a future reviewer can confirm correctness without controller knowledge
- **Aggregate effect:** any accumulated risk this deviation carries

---

## D1 — Phase D Task 14 review fixed two ship-blockers inline rather than deferring to v0.2.0

**Phase / Task:** Phase D Task 14 (containerised architect review)
**Commit:** `545cc1b`
**What the plan said:** Task 14 captured the architect review output; ship-blockers identified by the review were to be considered as v0.2.0 candidates.
**What the implementer did instead:** Two ship-blockers were fixed inline within Task 14 — Article 14 review-record enforcement gap (gates.py did not actually check for review records despite the constitution promising they would) and missing `depends_on` declarations for sdlc-team-common and sdlc-team-fullstack.
**Controller's decision:** accept.
**Rationale:** the architect review's two ship-blockers were constitutional contract violations (the constitution promised behaviour the code did not deliver). Documenting these as known limitations would have meant shipping a bundle whose constitution actively misrepresented its behaviour. Inline fix avoided shipping a misleading v0.1.0.
**Reviewer-verifiable:** yes — the fix is a discrete diff in `545cc1b`; the architect review output at `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md` describes both findings independently.
**Aggregate effect:** none.

---

## E1 — Phase E Task 1 added `plugins/sdlc-assured/scripts/__init__.py` (not in plan)

**Phase / Task:** Phase E Task 4 (where the missing file was first noticed)
**Commit:** `418a749`
**What the plan said:** Task 1 prescribed 5 specific files (manifest, plugin.json, README, pyproject, scripts/assured/__init__.py).
**What the implementer did instead:** Task 4 implementer found that the conftest.py `_register_scripts_package` call needed an empty `scripts/__init__.py` at the parent directory level (matching the existing pattern in sdlc-programme). Added it within the Task 4 commit.
**Controller's decision:** accept.
**Rationale:** matched established pattern in sdlc-programme/scripts/__init__.py; without it, the conftest registration raised FileNotFoundError before any test could run. The Task 1 plan had a real omission; Task 4 implementer caught and fixed it.
**Reviewer-verifiable:** yes — diff `ls plugins/sdlc-programme/scripts/` and `ls plugins/sdlc-assured/scripts/` shows both directories have the same shape.
**Aggregate effect:** none — but suggests Task 1 plan should have included the parent `__init__.py` in its file list.

---

## E2 — Phase E Task 1 review fixed manifest validator-name divergence

**Phase / Task:** Phase E Task 1 + review fix
**Commits:** `eb75715` (original) + `7ac65af` (fix)
**What the plan said:** Task 1 manifest used names like `req_module_assignment_validator`, `code_module_mapping_validator`, `visibility_rule_validator` for the pre_push validator list.
**What the implementer did instead:** First implementation matched the plan literally. Code review surfaced that those manifest names did not match the function names later tasks would implement (`req_has_module_assignment`, `code_annotation_maps_to_module`, `visibility_rule_enforcement`). Implementer fixed the manifest to use exact function names.
**Controller's decision:** accept (the plan had a defect — manifest validator names didn't match the function names the same plan later prescribed).
**Rationale:** the plan was internally inconsistent. Phase D's manifest used bare function names directly (`requirements_gate`, `design_gate`, etc.); Phase E's manifest invented a `_validator` suffix scheme that did not align with later tasks. The fix removed the divergence and made the manifest consistent with both Phase D's pattern and Phase E's actual function definitions.
**Reviewer-verifiable:** yes — `cat plugins/sdlc-assured/manifest.yaml | grep -A 20 pre_push:` shows function-name-exact entries; `grep "^def " plugins/sdlc-assured/scripts/assured/*.py` shows the matching function names.
**Aggregate effect:** none — but suggests writing-plans-skill should add a self-review check for "manifest validator names match later task function names."

---

## E3 — Phase E Task 5 hoisted test-file imports to satisfy flake8 E402

**Phase / Task:** Phase E Task 5
**Commit:** `977bcb4`
**What the plan said:** Step 1 prescribed appending tests to existing `tests/test_assured_ids.py` with imports immediately before each test function.
**What the implementer did instead:** consolidated all imports at the top of the file (rather than mid-file before specific test functions) to satisfy flake8 E402 (module-level import not at top of file). The plan's literal "append" instruction would have produced a flake8 violation.
**Controller's decision:** accept.
**Rationale:** the plan's prescription literally violated the project's lint rules. Hoisting was the correct fix; the deviation made the test file PEP 8 compliant. Pattern was repeated in Tasks 6-19 for the same reason — implementers consistently hoisted imports rather than re-violating E402.
**Reviewer-verifiable:** yes — `head -15 tests/test_assured_ids.py` shows a single consolidated import block; flake8 returns clean.
**Aggregate effect:** none — but the plan's literal "append imports mid-file" instruction was wrong throughout Phase E; implementers corrected it consistently.

---

## E4 — Phase E Task 6 dropped unused `Path` and `pytest` imports

**Phase / Task:** Phase E Task 6
**Commit:** `3daa1d6`
**What the plan said:** Step 1 test-file imports included `from pathlib import Path` and `import pytest`.
**What the implementer did instead:** dropped those imports because the 2 Task 6 tests didn't use them; flake8 F401 would have flagged them as unused.
**Controller's decision:** accept.
**Rationale:** unused imports are flake8 violations. The plan included these imports anticipating later test patterns that didn't appear in Task 6. The implementer added them back when later tasks needed them.
**Reviewer-verifiable:** yes — `grep -E "^(from pathlib|import pytest)" tests/test_assured_traceability_validators.py` shows imports added back when first needed.
**Aggregate effect:** none.

---

## E5 — Phase E Task 11 used bare `set` rather than `set[str]` annotation

**Phase / Task:** Phase E Task 11
**Commit:** `4aa73d3`
**What the plan said:** `_all_module_ids(decomp: Decomposition) -> set[str]` (Python 3.9+ builtin generic syntax).
**What the implementer did instead:** used `_all_module_ids(decomp: Decomposition) -> set` (no type parameter); also used `out: set = set()` rather than `out: set[str] = set()`.
**Controller's decision:** accept (cosmetic, functionally identical).
**Rationale:** with `from __future__ import annotations` (which the module has), both forms are valid annotation strings. Either passes flake8/black. The deviation is cosmetic and produces no behavioural difference.
**Reviewer-verifiable:** yes — `grep "_all_module_ids" plugins/sdlc-assured/scripts/assured/decomposition.py` shows the actual signature.
**Aggregate effect:** mild — generic-typed annotations are the project's stated preference; sample of bare-set form persisted into related functions in Tasks 12-15. v0.2.0 cleanup task could normalise.

---

## E6 — Phase E Task 12 rewrote `parse_programs_yaml_inline` test helper to fix file-handle bug in plan

**Phase / Task:** Phase E Task 12
**Commit:** `e119b4d`
**What the plan said:** Plan included a `parse_programs_yaml_inline(content)` helper that called `parse_programs_yaml` *inside* a `with tempfile.NamedTemporaryFile(...)` block.
**What the implementer did instead:** restructured to save the temp path, exit the `with` block (closing the file), then call `parse_programs_yaml` on the saved path. Also added `Decomposition` to imports because the plan's signature used a forward-reference string (`-> "Decomposition"`) that flake8 F821 rejected.
**Controller's decision:** accept (two real bugs in the plan).
**Rationale:** on macOS, calling `yaml.safe_load` on a path while the file is still open in a `with` block returns `None` (empty file read) because the buffered write hadn't flushed. The plan's literal helper was broken. The forward-reference string failed flake8 F821 because `Decomposition` wasn't imported in the test scope. Both are plan defects, not stylistic choices.
**Reviewer-verifiable:** yes — `grep -A 10 "def parse_programs_yaml_inline" tests/test_assured_decomposition.py` shows the close-then-parse pattern.
**Aggregate effect:** none — the helper is reused in Tasks 13-15 with the corrected pattern.

---

## E7 — Phase E Task 41 review fixed three architect-surfaced ship-blockers inline

**Phase / Task:** Phase E Task 41 (containerised architect review)
**Commits:** `2451a70` (review artefacts) + `119a770` (idempotency fix) + `350b1f0` (anaemic-context differentiation) + `cfcbddd` (skill mirror sync follow-up)
**What the plan said:** Task 41 captured the architect review output; ship-blockers were to be considered for inline fix vs. v0.2.0 deferral case-by-case.
**What the implementer did instead:** Three ship-blockers were fixed inline:
1. `render_code_index` and `render_spec_findings` embedded a live `datetime.now()` timestamp, breaking `index_regenerability` validator (idempotency requires byte-identical output). Fix: timestamp made an optional caller-provided parameter.
2. `anaemic_context_detection` was functionally identical to `code_annotation_maps_to_module`. Fix: rewrote with per-module concentration ratio (>20% threshold).
3. `commission-assured` SKILL.md was missing the `kb-register-library` wiring step; without it, KB queries return empty results.
**Controller's decision:** accept all three.
**Rationale:** all three were either constitutional contract violations (validator promised idempotency but produced non-idempotent output), validator design defects (two indistinguishable validators waste audit effort), or documentation gaps that would silently break the user's KB integration. None were acceptable to defer to v0.2.0.
**Reviewer-verifiable:** yes — the architect review at `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md` describes all three independently; the three fix commits are isolated diffs.
**Aggregate effect:** none.

---

## E8 — Phase E Task 41 follow-up: skill mirror drift after fix #3

**Phase / Task:** Phase E Task 41 follow-up
**Commit:** `cfcbddd`
**What the plan said:** the byte-identical mirror discipline (root `skills/` ↔ plugin `plugins/sdlc-assured/skills/`) had been established across Phase E.
**What the implementer did instead:** Fix #3 in Task 41 modified `plugins/sdlc-assured/skills/commission-assured/SKILL.md` but did not update the root mirror at `skills/commission-assured/SKILL.md`. The controller (not the original implementer) noticed the drift, dispatched a follow-up commit to sync.
**Controller's decision:** accept (the controller did the sync directly).
**Rationale:** the mirror discipline is byte-identical; the fix had to be re-applied to the root copy. This was the controller catching a sub-implementer's oversight, not the implementer's deviation. Mentioned here for completeness of the audit trail.
**Reviewer-verifiable:** yes — `diff plugins/sdlc-assured/skills/commission-assured/SKILL.md skills/commission-assured/SKILL.md` returns empty.
**Aggregate effect:** none.

---

## E9 — Phase E Task 40 plugin packaging used in-plugin `source:` paths rather than root paths

**Phase / Task:** Phase E Task 40
**Commit:** `2ca9c0f`
**What the plan said:** plan body used `source: skills/<name>/SKILL.md` (root path) for skill source declarations in `release-mapping.yaml`.
**What the implementer did instead:** used `source: plugins/sdlc-assured/skills/<name>/SKILL.md` (in-plugin path).
**Controller's decision:** accept.
**Rationale:** `release-mapping.yaml` declares the source-of-truth and target. For Phase D's `sdlc-programme`, sources lived in root `skills/` and were copied INTO `plugins/sdlc-programme/skills/` by `release-plugin.py`. For Phase E we authored everything in the plugin directory directly (in-plugin authoring), so the in-plugin path is the source-of-truth. Both patterns are accepted by `release-plugin.py`; the choice depends on where the authoritative source lives. `check-plugin-packaging.py` returns 14/14 verified with the in-plugin form.
**Reviewer-verifiable:** yes — `grep -A 12 "^sdlc-assured:" release-mapping.yaml` shows the in-plugin form; `python3 tools/validation/check-plugin-packaging.py` returns PASSED.
**Aggregate effect:** mild — two plugins now use different source-of-truth conventions. v0.2.0 should pick one and document.

---

## E10 — Phase E Task 40 caught and fixed pre-existing root-mirror drift on synthesis-librarian

**Phase / Task:** Phase E Task 40
**Commit:** `2ca9c0f`
**What the plan said:** Task 40 was packaging-only (release-mapping + marketplace).
**What the implementer did instead:** caught that Task 23 (synthesis-librarian SYNTHESISE-ACROSS-SPEC-TYPES mode) had edited only `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md`, missing the root mirror at `agents/knowledge-base/synthesis-librarian.md`. Implementer synced the root mirror within Task 40's commit.
**Controller's decision:** accept (drift fix in scope-adjacent task).
**Rationale:** the drift was a real defect introduced by Task 23 implementer (who confirmed `agents/synthesis-librarian.md` did not exist at root, but did not check the `agents/knowledge-base/` subdirectory). Task 40 implementer's bonus catch fixed the drift before PR. Pattern repeated in Phase F: the controller (not implementer) caught a similar drift on commission-assured after Task 41 fix #3 (E8 above).
**Reviewer-verifiable:** yes — `diff plugins/sdlc-knowledge-base/agents/synthesis-librarian.md agents/knowledge-base/synthesis-librarian.md` returns empty.
**Aggregate effect:** medium — Phase E had 2 distinct mirror-drift incidents (Task 23 surfaced in Task 40, and Task 41-fix surfaced post-merge by controller). v0.2.0 should add a CI check (or pre-commit hook) for byte-identical mirrors between `skills/`, `agents/`, `agents/knowledge-base/` and their plugin copies.

---

## F1 — Phase F Task 9 placed `<!-- implements: -->` annotation INSIDE design-spec.md design element

**Phase / Task:** Phase F Task 9
**Commit:** `02e596a`
**What the plan said:** annotations go on the implementing artefact (the SKILL.md or the Python function), not on the design-spec.
**What the implementer did instead:** added a `<!-- implements: DES-assured-substrate-001 -->` annotation INSIDE the DES-001 section of `docs/specs/assured-substrate/design-spec.md`, in addition to the annotation on `commission-assured/SKILL.md`.
**Controller's decision:** accept with note ("not sure that was intended").
**Rationale:** the implementer's interpretation was creative — annotating a DES with `# implements:` could be read as "this DES is what implements REQ-001" — but it blurs the spec/implementation boundary. The convention is that DES `**satisfies:**` REQ (downward link in spec graph), and `# implements:` is the upward link from CODE to DES. The implementer's annotation does not match either direction.
**Reviewer-verifiable:** yes — `grep -A 1 "DES-assured-substrate-001" docs/specs/assured-substrate/design-spec.md` shows the inline annotation.
**Aggregate effect:** **flagged for reviewer attention** — this is the deviation most likely to be wrong. iOS architect review §"Assessment of the Retrospective's Challenge List" rated this as "Acceptable only if the convention says design documents can be implementation evidence; otherwise it blurs spec and implementation layers." A reviewer should decide whether to remove the inline annotation in the design-spec or formalise the convention in v0.2.0.

---

## F2 — Phase F Task 13 bundled csv+markdown exporters under DES-004 (FDA DHF) rather than separate REQ

**Phase / Task:** Phase F Task 13
**Commit:** `410fbc7`
**What the plan said:** "csv+markdown collapsed" — implementer's call on bundling.
**What the implementer did instead:** bundled `export_csv` and `export_markdown` annotations under `DES-assured-export-formats-004` (the FDA DHF DES) with the rationale that both generic exporters are non-regulatory companions and adding a 5th REQ would misrepresent the module's normative scope.
**Controller's decision:** accept.
**Rationale:** the plan explicitly delegated this choice to the implementer ("collapse under a 5th REQ or under DES-001 as 'regulator-facing exporters' + 'non-regulator exporters'. Either is acceptable"). The implementer chose the lower-overhead option with documented rationale. The choice is reasonable but creates a minor semantic stretch — csv/markdown exporters are not specifically FDA-aligned.
**Reviewer-verifiable:** yes — `grep -B 1 "implements" plugins/sdlc-assured/scripts/assured/export.py | head -30` shows the annotation pattern.
**Aggregate effect:** mild — the FDA DHF feature contains REQ statements that don't quite cover csv/markdown's actual purpose. v0.2.0 could split this into a 5th REQ "non-regulatory exporters for triage and team review."

---

## F3 — Phase F Task 12 noted overlap between code_annotation_maps_to_module and anaemic_context_detection

**Phase / Task:** Phase F Task 12
**Commit:** `86610bf`
**What the plan said:** REQ inventory listed both validators as separate REQs (REQ-002 and REQ-004) with overlapping intent.
**What the implementer did instead:** authored both REQs as planned but added a cross-reference note in design-spec.md about the intentional differentiation (per-annotation blocking vs. module-level scatter-threshold), which Phase E architect review had already established and the implementation in `350b1f0` had already differentiated.
**Controller's decision:** accept; logged as F-006 (no "see also" mechanism).
**Rationale:** the implementer flagged a real tension — two REQs with overlapping intent that are differentiated only by reading the DES layer. The cross-reference note in design-spec was a reasonable workaround. The underlying tension was logged as F-006 for v0.2.0.
**Reviewer-verifiable:** yes — F-006 in `research/phase-f-dogfood-findings.md` describes the tension.
**Aggregate effect:** none.

---

## F4 — Two timeout-recovery commits made by the controller on behalf of timed-out subagents

**Phase / Task:** Phase E Task 11 + Phase F Task 39
**Commits:** `4aa73d3` (Phase E Task 11) + `dbff56c` (Phase F Task 39)
**What the plan said:** subagent does the work and commits.
**What the implementer did instead:** subagent's API connection dropped before commit. Working tree had staged work from the subagent. Controller verified the work matched the plan, ran lint and tests, and committed on the subagent's behalf.
**Controller's decision:** accept (no alternative — the work was correct and present in the working tree).
**Rationale:** the recoveries were not deviations from the plan content — they were recoveries from infrastructure (API timeout) failures. The work itself was correct. iOS architect review §2.4 recommended "transactional rollback on timeout" as the alternative; controller's analysis judged this technically infeasible at the subagent layer (subagents share the parent's git tree) AND wrong-direction (rollback would have discarded correct work). Controller's response was preserved and the architect's prescription was not adopted (see PR-body discussion of which review recommendations are NOT incorporated).
**Reviewer-verifiable:** yes — both commits are isolated diffs; their content matches the corresponding tasks' plan prescriptions byte-for-byte (modulo black/flake8 formatting). A reviewer can `git show <SHA>` each one and confirm.
**Aggregate effect:** **flagged for reviewer attention** — Review 1 and Review 2 both raised this as a fragility. Reviewer should sample both commits to verify the recovery preserved correct work and didn't smuggle in any partially-completed or invented content.

---

## F4 — Re-audit verdict (v0.2.0 Phase F closure)

**Audit date:** 2026-05-01
**Verdict:** CONFIRMED CLEAN

### Commit `4aa73d3` — req_has_module_assignment validator

Both dataclasses (`SpecArtefact`, `DecompositionValidatorResult`), both private helpers (`_all_module_ids`, `_module_from_positional_id`), and the public `req_has_module_assignment` function match the plan's Step 3 prescription (plan lines 1655–1714) line-for-line with one within-tolerance difference: the plan used `set[str]` (Python 3.9+ generic syntax) while the commit used bare `set` — already logged as deviation E5 and accepted as cosmetic. All three tests match the plan's Step 1 prescription (plan lines 1604–1638) exactly; the commit also hoisted the imports to satisfy flake8 E402, consistent with the E3 pattern. No substantive drift found.

### Commit `dbff56c` — integration tests + fixture

All five fixture files (`programs.yaml`, `requirements-spec.md`, `design-spec.md`, `test-spec.md`, `src/auth/oauth/login.py`) match the plan's Steps 1–3 (plan lines 4446–4559) byte-for-byte. The integration test file (`test_assured_skill_integration.py`) contains the same six test functions with identical bodies (plan lines 4608–4662); the commit correctly dropped eight unused imports that the plan prescribed but that flake8 F401 would have rejected (`pytest`, `render_code_index`, `render_spec_findings`, `Decomposition`, `Module`, `Program`, `SubProgram`, `VisibilityRule`, `render_id_registry`, `req_has_module_assignment`, `SpecArtefact`) — this is the same pattern as deviation E4 and within formatting tolerance. No substantive drift found.

### Action

None. Both commits deliver exactly what the plan prescribed, and the only differences are lint-driven import reductions consistent with the project's established deviation pattern (E3, E4). Validators confirmed: `id_uniqueness`, `cited_ids_resolve`, `forward_link_integrity` all True after re-audit.

---

## Summary statistics

| Category | Count |
|---|---|
| Total deviations logged | 15 (D1, E1-E10, F1-F4) |
| Accepted as plan defects (plan was wrong) | 5 (E2, E3, E4, E6, F4-mechanism) |
| Accepted as architect-review-driven inline fixes | 4 (D1, E7 = 3 fixes, E8) |
| Accepted as reasonable interpretation | 3 (E5, F2, F3) |
| Flagged for reviewer attention | 2 (F1, F4) |
| Pattern-of-discipline issues | 1 (E10 — mirror drift, recurring) |

## Patterns worth noting

1. **The plan had real defects.** E2, E3, E4, E6 are all cases where the implementer corrected something the plan got wrong (manifest naming inconsistency, mid-file imports violating E402, unused imports, broken `with`-block file-handle scope). The controller accepting these is correct; the lesson is that writing-plans-skill self-review should catch these (validate manifest names match function names, run flake8 dry-run on test fixtures, etc.).

2. **Mirror drift recurs.** E10 caught Task 23's drift; E8 caught Task 41-fix's drift. Both recovered, but the pattern repeats. v0.2.0 should add a byte-identical-mirror CI check or pre-commit hook.

3. **Two deviations need explicit reviewer judgment.** F1 (annotation inside design-spec) and F4 (timeout-recovery commits). Neither is wrong-on-its-face; both are choices a reviewer might decide differently than the controller did.

4. **No deviations were accepted purely for expedience.** Every accepted deviation has an articulable reason (plan defect, architect-review-driven, lint compliance, mechanism-required). Controller's review-rigour-drift documented in the session meta-retrospective applied to *batched reviews of bulk-content tasks* (E11 Tasks 31-38), not to deviation acceptance per se.

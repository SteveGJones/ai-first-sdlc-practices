# Retrospective: Phase D — Programme Bundle (Method 1 Substrate)

**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #186 (Phase D of EPIC #178)
**Status:** COMPLETE

---

## What we set out to do

Build the **Programme bundle Method 1 substrate** — `sdlc-programme` plugin v0.1.0 implementing formal waterfall phase gates per METHODS.md §3.

Six categories of deliverable per the spec at `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md`:

1. Plugin manifest + metadata (`manifest.yaml`, `plugin.json`, `README.md`)
2. Programme constitution (overlays Single-team's foundations with Programme-specific articles)
3. Phase artefact templates (req-spec / design-spec / test-spec)
4. Phase gate validators (4 validators + shared spec parser)
5. Skills (commission-programme, phase-init, phase-gate, phase-review, traceability-export)
6. Plugin packaging (release-mapping, marketplace.json)

Plus tests (validator tests + skill integration tests + minimal feature fixture) and a containerised architect review before close.

## What was built

All six deliverable categories shipped, plus tests and a containerised architect review:

1. **Plugin scaffold (`plugins/sdlc-programme/`)** — `manifest.yaml` (schema_version 1, name `programme`, version 0.1.0, supported_levels `[production, enterprise]`, `depends_on: [sdlc-core, sdlc-team-common, sdlc-team-fullstack]`), `.claude-plugin/plugin.json`, `README.md`, `pyproject.toml`, `CONSTITUTION.md`. Marketplace entry registered.
2. **Programme constitution (Articles 12-14)** — overlays Single-team's foundations. Article 12 (formal phase-gate discipline), Article 13 (cross-phase reference integrity), Article 14 (mandatory phase-review with review records at `<feature-dir>/reviews/<phase>-review-*.md`).
3. **Three phase artefact templates** — `templates/requirements-spec.md`, `templates/design-spec.md`, `templates/test-spec.md`. Each has a `<feature-id>` placeholder substituted by `phase-init` via `sed`, declared-ID headings (REQ/DES/TEST), and `**satisfies:**` lines for cross-phase references.
4. **Four gate validators on a shared spec_parser** — `scripts/programme/spec_parser.py` provides line-wise markdown parsing with code-block toggle (skips fenced ``` blocks), `_FEATURE_ID_RE`, `_HEADING_ID_RE`, `_SATISFIES_RE`, `_REF_ID_RE`, and `_TEST_ID_REF_RE`. `scripts/programme/gates.py` provides `requirements_gate`, `design_gate`, `test_gate`, `code_gate`. Design and test gates additionally check for review records via `_has_review_record`.
5. **Five skills** — `commission-programme` (selection skill), `phase-init` (template instantiation), `phase-gate` (gate dispatch), `phase-review` (mandatory review dispatch — design→solution-architect, test→backend-architect), `traceability-export` (CSV/markdown matrix).
6. **Plugin packaging** — `release-mapping.yaml` updated for `sdlc-programme`; mirrored source under `plugins/sdlc-programme/`. Verified by `check-plugin-packaging.py` (13/13).

**Tests:** 29 programme tests across four files — `test_programme_spec_parser.py` (7), `test_programme_gates.py` (13, including 2 review-record enforcement tests added in Task 14), `test_programme_traceability.py` (5), `test_programme_skill_integration.py` (4).

**Containerised review:** architect review captured at `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md` with five verdicts; both ship-blockers fixed inline in Task 14.

## What worked well

- **Lessons-learned discipline applied across tasks** — formatted with black before commit, no unused imports, exception-type discipline (raised the right exception classes from `spec_parser`), plugin-dir mirror discipline (Phase A taught us never to edit the plugin-dir copy when a root source exists; held throughout Phase D).
- **`spec_parser` as a shared regex foundation** — one parser, four gate validators reusing it. Adding a new gate is a few lines of orchestration, not a re-implementation of markdown traversal. Code-block skipping is implemented once and inherited by every gate.
- **Mock-fixture pattern from Phase C reused** — the sample feature fixture under `tests/fixtures/sdlc-programme/sample-feature/` exercises the gates end-to-end without needing a real project. Same pattern that worked for kb tests in Phase C of EPIC #164.
- **Containerised architect review caught real ship-blockers** — both ship-blockers (Article 14 review-record enforcement gap, and missing `depends_on` declarations) were caught by the containerised reviewer and fixed inline in Task 14 rather than punted to v0.2.0.

## What was harder than expected

- **phase-review reviewer-agent dispatch** — the natural choice for test-spec review was a `test-architect` agent, but no such agent exists in the family. Settled on `sdlc-team-fullstack:backend-architect` as a pragmatic proxy. The architect review flagged this as semantically imprecise (correctly), but for v0.1.0 it is acceptable.
- **Bundle layout convergence with the Phase C contract** — the Phase C bundle contract dropped the `validators/` directory; rather than house gates under a top-level `validators/`, they live in `scripts/programme/` and are surfaced via the `phase-gate` skill. Took a re-read of `docs/architecture/option-bundle-contract.md` to settle this without retrofit.
- **pytest auto-collection conflict on the `test_gate` symbol** — pytest tried to collect the `test_gate` *function* from `gates.py` as a test. Worked around by importing it under a different alias (`from scripts.programme.gates import test_gate as run_test_gate`) inside the test module.
- **release-mapping `bundle:`/`templates:` categories not recognised by the validator** — `check-plugin-packaging.py` validates against a fixed set of mapping categories. The Programme plugin has templates and a CONSTITUTION.md that did not fit the existing categories cleanly. Worked around by using the `files:` category (the precedent set by `sdlc-workflows`), which packages arbitrary files without requiring schema extension.
- **Broad `.gitignore reviews/` rule hiding fixture review records** — to test that review-record enforcement works, a fixture review file under `tests/fixtures/sdlc-programme/sample-feature/reviews/` must be committed. The repo-wide `reviews/` ignore rule swallowed it. Added a negation pattern `!tests/fixtures/**/reviews/` so fixture review records are tracked while real top-level `reviews/` files remain ignored.

## Lessons learned

- **`spec_parser` pattern (shared regex foundation for multiple validators) is reusable for Phase E.** Method 2 / Assured needs coverage validators, decomposition checks, and KB-for-code annotations — all of which can layer on top of `spec_parser` without retrofit. The `_REF_ID_RE` regex would need extension to support Method 2's positional namespace IDs (`P1.SP2.M3.REQ-007`), but that is additive.
- **Line-wise markdown parsing with a code-block toggle works well.** Walking lines with a `in_code_block` flag is simple, fast, and correctly handles the most common false-positive source (IDs inside ```` ``` ```` fences). Confirmed by `test_parse_spec_ignores_ids_in_code_blocks`.
- **`conftest.py`-based scripts package registration avoids PEP 668 issues with Homebrew Python.** Rather than `pip install -e .` the plugin (which fights with Homebrew's externally-managed-environment policy), tests import from `scripts/programme/` via path manipulation in `conftest.py`. Same pattern as previous phases.

## Programme bundle assessment

The substrate genuinely serves a programme audience — regulated-industry teams that need formal phase-gate enforcement with auditable cross-phase references. The constitution articles are concrete (not aspirational): Article 12's gate discipline is enforced by `phase-gate`; Article 13's cross-phase reference integrity is enforced by `gates.py`; Article 14's mandatory review is enforced by both `phase-review` (skill) and `_has_review_record` (gate check). A team commissioning to Programme cannot ship code that fails any of these articles.

The layout matches the Phase C bundle contract exactly (architect verdict: AGREE on Section 5). It leaves room for #103's SAFe-Lite multi-team scope to layer on without retrofit — multi-team coordination, programme-level epics, and PI planning can all be added as additional skills/agents without touching the Method 1 spec parser, gates, or templates.

## Phase gate assessment

The gates catch the regulated-industry-relevant broken-reference cases:

- **Missing REQ-X-999** (DES references a non-existent REQ) — caught by `design_gate`. Tested by `test_design_gate_fails_on_broken_satisfies_reference`.
- **Missing `**satisfies:**` line on DES** — caught by `design_gate`. Tested.
- **Broken DES references in TEST** — caught by `test_gate`. Tested by `test_test_gate_fails_on_broken_des_reference` and `test_test_gate_fails_on_broken_req_reference`.
- **Missing `# implements:` annotation in code** — caught by `code_gate`. Tested by `test_code_gate_fails_when_code_has_no_implements_annotation`.

Fenced code blocks are correctly skipped (tested by `test_parse_spec_ignores_ids_in_code_blocks`).

**Minor concerns acknowledged** (per the architect review, Section 3):
- No blockquote skipping — IDs inside `>` blockquotes are extracted. In practice, blockquoted IDs are likely intentional.
- No inline-code skipping — IDs inside `` `backticks` `` are extracted. Same caveat.
- No coverage-completeness check — the gates do not flag a REQ with no DES coverage or a DES with no TEST coverage. This is an Assured-level concern (METHODS.md) and is surfaced by `traceability-export` so a team can find orphans manually. Phase E will add the validator.

## phase-review skill assessment

- **`design-spec → sdlc-team-common:solution-architect`** is the right architectural choice — solution architects are the natural reviewers for design decisions. Architect review verdict: AGREE.
- **`test-spec → sdlc-team-fullstack:backend-architect`** is a pragmatic proxy. No `test-architect` agent exists in the family. Architect review flagged this as semantically imprecise but acceptable for v0.1.0; can be revisited if/when a `test-architect` agent is added.
- **Manifest declares both plugin dependencies in `depends_on`** — fixed in Task 14 in response to the architect's "agent dependency gap" finding. `manifest.yaml` now declares `[sdlc-core, sdlc-team-common, sdlc-team-fullstack]`. Teams installing the Programme bundle will be prompted to install the dependent plugins.

## Containerised review verdict

A containerised independent architect review was commissioned via `sdlc-workflows` and captured at `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md`. Five verdicts:

1. **Constitution overlay soundness — AGREE-WITH-CONCERNS.** Articles 12-14 are well-bounded and consistent with articles 1-11. Concerns: Article 12 ambiguity on "incomplete" (parser does not check non-empty content); Article 14 review-record enforcement gap (gates did not check for review records). The latter was a ship-blocker.
2. **Phase artefact templates fitness — AGREE.** Templates produce artefacts the gates can validate. `<feature-id>` substitution flow is correct, and the `_REF_ID_RE.findall()` approach correctly handles comma-separated multi-REQ satisfies lines.
3. **Gate validator robustness — AGREE-WITH-CONCERNS.** Validators handle the core cases correctly. Minor concerns on blockquote/inline-code/HTML-comment handling and absence of coverage-completeness check (Assured-level concern).
4. **Phase-review skill realism — AGREE-WITH-CONCERNS.** Architectural choices are reasonable; `test-architect` doesn't exist so `backend-architect` is a pragmatic proxy. Ship-blocker: missing `depends_on` declarations for `sdlc-team-common` and `sdlc-team-fullstack`.
5. **Bundle layout vs Phase C contract — AGREE.** All required manifest fields present and correct; layout matches the contract; reserved Phase E fields correctly absent for a Method 1 bundle.

The architect identified two ship-blockers; both fixed inline in Task 14 rather than deferred to v0.2.0:

1. **Article 14 review-record enforcement gap.** Added `_has_review_record` helper to `gates.py`. `design_gate` and `test_gate` now check for `<feature-dir>/reviews/<phase>-review-*.md` before passing. Two new tests (`test_design_gate_fails_when_review_record_missing`, `test_test_gate_fails_when_review_record_missing`) cover the new behaviour.
2. **Agent dependency gap.** `manifest.yaml`'s `depends_on` extended to declare `sdlc-team-common` and `sdlc-team-fullstack` so teams commissioning to Programme are prompted to install the agent plugins.

Verbatim review captured for audit at `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md`.

## Validation

- **Programme tests:** **29/29 passing** (`tests/test_programme_*.py`) — 7 spec_parser + 13 gates + 5 traceability + 4 skill integration. All green in 0.07s.
- **Plugin packaging:** **13/13 plugins verified** (`check-plugin-packaging.py`).
- **Quick validation:** **PASSED** (0.2s, 0 errors, 0 warnings).
- **Pre-push validation:** **9/10** — Pre-commit Hooks check fails because the `pre-commit` binary is not installed in this environment (documented carry-forward env limitation, present since Phase A of EPIC #164 and noted in retrospectives 167, 168, 169, 170). All other 7 explicit checks (Syntax, Technical Debt, Architecture, Type Safety, Security, Logging Compliance, Static Analysis) PASSED. No new failures introduced by Phase D.

## References

- Parent EPIC: #178 (Joint Programme + Assured bundle delivery)
- Issue: #186 (Phase D substrate)
- Larger future scope: #103 (full SAFe-Lite Programme bundle, deferred)
- Feature proposal: `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md`
- Phase C closure: `retrospectives/98-phase-c-commissioning-infrastructure.md`
- Method 1 design: `research/sdlc-bundles/METHODS.md` §3
- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Implementation plan: `docs/superpowers/plans/2026-04-27-phase-d-programme-bundle-substrate.md`

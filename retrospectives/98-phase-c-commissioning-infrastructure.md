# Retrospective: Phase C — Commissioning Infrastructure (#98)

**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #98 (absorbed into EPIC #178 as Phase C)
**Status:** COMPLETE

---

## What we set out to do

Build the foundational infrastructure that lets the framework commission a fixed SDLC bundle per project. Four deliverables:

1. **Bundle contract** documented at `docs/architecture/option-bundle-contract.md` — manifest schema, file layout, plugin packaging shape, versioning, plus reserved schema fields for Phase E (source/derived paths, known-violations, anaemic-context-detection, ID format)
2. **Commission skill** at `skills/commission/SKILL.md` — context detection, structured questions, recommendation, user override, bundle installation
3. **`.sdlc/team-config.json` schema extension** — five required commissioning fields + commissioning history + reserved Phase E fields (decomposition, commissioning_options)
4. **sdlc-enforcer awareness** — reads the commissioning record and adapts behaviour based on `sdlc_option`

Originally filed as standalone sub-feature #98 of EPIC #97 on 2026-04-07. Absorbed into EPIC #178 as Phase C on 2026-04-27 because Programme (Phase D) and Assured (Phase E) both depend on commissioning infrastructure being in place.

## What was built

11 tasks executed via subagent-driven-development across ~12 hours. Each task: implementer dispatch → spec compliance review → code quality review → fix loop where reviewers surfaced issues. All tasks landed with proof-of-completion artefacts (tests, validation, packaging checks). Total commits on Phase C: 11 (one per task) plus the scaffold commit.

**Four deliverables** per the spec:

1. **Bundle contract** at `docs/architecture/option-bundle-contract.md` — 152 lines, manifest schema, file layout, reserved Phase E fields, validator configuration, backward compatibility, out-of-scope. Refined twice via containerised architect review (Phase C task 10).

2. **Commission skill** at `skills/commission/SKILL.md` (+ plugin mirror) — context detect, structured questions, recommendation logic, user override, bundle install, record write. `disable-model-invocation: true` because commissioning is a high-stakes operation.

3. **`.sdlc/team-config.json` schema extension** — documented in `CLAUDE-CORE.md` (5 required commissioning fields + commissioning_history array + 2 reserved Phase E fields). Read/write helpers in `recorder.py`.

4. **sdlc-enforcer awareness** — `agents/core/sdlc-enforcer.md` (+ plugin mirror) reads the commissioning record on every invocation, defaults to single-team for uncommissioned projects, includes `sdlc_option` in compliance reports.

**Python helpers** (`plugins/sdlc-core/scripts/commission/`):
- `manifest.py` — `BundleManifest` dataclass, `parse_manifest`, `ManifestValidationError` (7 unit tests)
- `recorder.py` — `CommissioningRecord`, `read_record`, `write_record`, `is_commissioned`, `default_option_for_uncommissioned` (7 unit tests)
- `installer.py` — `install_bundle`, `BundleInstallationError`, `InstallationResult`, `_validate_safe_dst` + `_validate_manifest_entry_name` security guards (11 unit tests)

**Mock fixture**: `skills/commission/templates/sample-bundle/` — minimal valid bundle for installer testing (1 manifest + 1 constitution + 1 agent + 1 skill + 1 template).

**Integration tests**: 3 tests at `tests/test_commission_skill_integration.py` exercising the full flow against fixtures (empty-project, existing-project).

**Total Phase C test count: 28** (all passing).

**Containerised review** (Phase C task 10): re-ran the architect review of the bundle contract via `sdlc-workflows` using the team image built in Phase B (`sdlc-worker:decomposition-review`). Verdicts: 1 DISAGREE (file layout — `validators/` directory described infrastructure that doesn't exist anywhere), 3 AGREE-WITH-CONCERNS, 1 AGREE. 5 fixes integrated inline.

## What worked well

- **Subagent-driven discipline scaled cleanly across 11 tasks.** The implementer-dispatch + two-stage review pattern (spec compliance, then code quality) caught real issues in 4 of 11 tasks (Tasks 1, 2, 5, 10). Fixes landed in amended commits keeping history clean.
- **Lessons-learned-applied paid off after Task 2.** Task 3 onward shipped lint-clean on first attempt because Tasks 2's review surfaced patterns (unused imports, tuple formatting, exception wrapping) that I forwarded to subsequent implementer dispatches. Fix-loop overhead dropped from 1-2 cycles per task in Tasks 1-2 to 0 cycles in Tasks 3-4.
- **Mock sample-bundle fixture pattern**: building the test fixture (Task 4) BEFORE the installer (Task 5) gave the installer a real artefact to install against. The installer's tests run against the same fixture used by the integration tests, so the fixture is reused twice for cost of building once.
- **Security guards driven by the code review.** Task 5's first implementation passed unit tests but failed code-quality review on path-traversal vulnerability. The reviewer's specific patterns (`Path.resolve()` comparison, manifest-entry-name safety floor) became the fix. The framework now ships defence-in-depth on a security-relevant code path that initial testing didn't exercise. *Validates the two-stage review pattern.*
- **Containerised review surfaced a load-bearing finding** that in-session review would have missed. The `validators/` directory issue (described infrastructure that doesn't exist) — only visible by walking the existing 12-plugin family. Container's clean state forced the agent to ground claims in actual repo content rather than the spec author's mental model. Confirms `feedback_containerised_review_for_design_artefacts.md` from Phase B.

## What was harder than expected

- **`pip install -e plugins/sdlc-core/` failed under Homebrew Python's PEP 668 externally-managed env.** Worked around by extending `tests/conftest.py` to register `sdlc_core_scripts` via importlib (consistent with how `sdlc-knowledge-base` and `sdlc-workflows` are already registered). Single-line additive change. Worth capturing as a note for any future Phase D/E plugin: prefer the conftest registration pattern over editable installs.
- **`release-mapping.yaml` shape required some attention.** New `scripts:` sub-key under `sdlc-core` needed adding (mirroring `sdlc-knowledge-base.scripts` shape). The `check-plugin-packaging.py` validator caught any drift immediately.
- **The bundle contract's `validators/` directory described infrastructure that doesn't exist.** I (the controller) wrote that part of the contract from imagined design, not from walking the existing plugin family. The containerised architect caught it because their fresh-context dispatch had to verify claims against actual repo contents. **Lesson**: when documenting "MUST contain" infrastructure, walk the existing implementation first; aspirational specs that don't match reality are spec defects.

## Lessons learned

- **For Phase D-E onwards**: every "MUST contain" or "MUST follow" claim in design documents should be grounded in either (a) actual existing code, or (b) a clearly-flagged "new convention" with explicit acknowledgement that it doesn't exist yet. Aspirational layouts that look like they describe reality but don't are footguns.
- **Containerised review is now the default for design artefacts.** Phase B was the first dogfood; Phase C task 10 re-confirmed the value (1 DISAGREE finding that materially shaped the contract). For Phase D-E, every load-bearing design doc goes through containerised review by default.
- **Two-stage review pattern catches different kinds of issue.** Spec compliance reviewer is excellent at "did you build the right thing"; code quality reviewer is excellent at "did you build the thing right" — particularly security guards, lint compliance, exception discipline. Skipping either review type loses signal.
- **Test-fixture-before-implementation sequencing works.** Task 4 (mock fixture) before Task 5 (installer) was the right call. Phase D and E should consider similar sequencing: ship the test substrate before the code under test.

No new durable feedback memory written this phase — the lessons reaffirm existing memories (`feedback_containerised_review_for_design_artefacts.md`, `feedback_test_proves_completion.md`, `feedback_phase_a_plugin_dir_regression.md`).

## Bundle contract assessment

The contract held up under independent containerised review with one DISAGREE that turned out to be load-bearing (the `validators/` directory issue), three AGREE-WITH-CONCERNS findings (manifest schema permissiveness, Phase E reserved fields adequacy, regulated-industry adoption gap) all addressable by additive fixes, and one AGREE (backward compatibility). 5 fixes integrated; contract ready for Phase D and Phase E plan-writing.

**Reserved Phase E fields** appear sufficient: 4 of 5 spike gaps covered by dedicated capability flags; Gap 3 (cross-module-mutation validator) absorbed by the extensible `validators:` object with a clarifying note added in F3.

## Commission skill assessment

The 5-question discipline held. Recommendation logic is a deterministic table lookup (no model reasoning required). Override path is documented (warn + proceed; never block). The skill is `disable-model-invocation: true` because commissioning is high-stakes (writes to project root, replaces CONSTITUTION.md). End-to-end tested via Task 8's integration tests (3 tests covering fresh project, existing-keys-preservation, re-commissioning history).

## Containerised review verdict

Phase C task 10 ran the bundle contract through `sdlc-workflows` with the `sdlc-worker:decomposition-review` team image (built in Phase B, reused here). Workflow + command artefacts at `research/sdlc-bundles/dogfood-workflows/bundle-contract-review.{md,yaml}`; verbatim review output at `bundle-contract-review-output.md`; run log at `bundle-contract-review-run.log`. Reproducibility: anyone with the repo + Docker can re-run the review against the same contract state.

**The DISAGREE on file layout was the load-bearing finding** that justified the containerised round-trip. In-session review would have missed it because the validator names (`python_ast`, `check_technical_debt`) sound real and the dispatcher pattern sounds plausible — only walking the actual 12-plugin family reveals that no plugin has a `validators/` directory or a YAML registry + run.sh dispatcher.

## Validation

- 28 commission tests passing (7 manifest + 7 recorder + 11 installer + 3 integration)
- Plugin packaging: 12/12 verified
- Pre-push --quick: PASSED (0 errors, 0 warnings)
- Black + flake8: clean across all commission scripts and tests
- Branch state: 19 commits on `feature/sdlc-programme-assured-bundles`
- Phase C-specific commits: 12 (1 scaffold + 11 tasks)

## References

- Parent EPIC: #178 (Joint Programme + Assured bundle delivery)
- Issue: #98
- Feature proposal: `docs/feature-proposals/98-sdlc-commissioning-infrastructure.md`
- Phase A spec: `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md`
- Phase B spike: `research/sdlc-bundles/decomposition-spike.md`
- Memory: `feedback_containerised_review_for_design_artefacts.md`

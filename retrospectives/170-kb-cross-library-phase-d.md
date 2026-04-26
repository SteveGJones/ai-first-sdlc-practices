# Retrospective: Cross-Library KB Query — Phase D Operational Maturity

**Issue:** #170 (umbrella for sub-features #170-#176 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** Complete — EPIC #164 v1 feature-complete; ready for PR

## What went well

- **HARD GATE (Task 10) passed** — priming demonstrably changes file selection. Q1 and Q2
  cleared cleanly; Q3 borderline but acceptable given fixture design constraints. The EPIC's
  core differentiator (priming as interpretive lens) was validated empirically, not just
  asserted in prose.
- **Five-reviewer assessment after Phases A+B+C surfaced real gaps.** Phase D addresses every
  finding from that review — nothing was deferred or dismissed. The review-driven scope
  expansion was well-targeted.
- **synthesis-librarian as a separate agent with `tools: []`** makes the §7.1 no-side-effects
  invariant structural rather than prompt-only. Future maintainers cannot accidentally grant it
  write access without editing the agent manifest explicitly.
- **Audit log + kb-audit-query** gives the consulting team the durable trust signal needed to
  answer "show me all attribution drops in the last 90 days" — a question that previously
  required re-running every query.
- **Library evolution mechanism** (4-field shelf-index header + staleness caveat) replaces the
  bare `format_version` stub with a proper surface. The fields (`format_version`,
  `last_rebuilt`, `library_handle`, `domain`) give future maintainers room to evolve the
  format without breaking existing libraries.
- **Onboarding skill (kb-setup-consulting)** replaces the hand-walked 4-step setup described in
  the spec with one skill invocation. The `--verify-only` mode lets teams audit an existing
  setup without risk.
- **Plugin-dir vs root-source pattern** was applied consistently throughout Phase D. No
  regression in any of the 97 tests.
- **Black + flake8 clean** at closure — caught and fixed 8 formatting issues and 10 lint
  violations (unused imports, mid-file imports, unused variables) as part of the final
  validation pass.

## What was harder than expected

- **`format_version` → `shelf_index_header` rename** touched multiple files; the importlib-based
  skill bash snippets required a different approach from naive `sys.path.insert` patterns used
  earlier in the codebase.
- **HARD GATE fixture design** needed deliberate term-overlap gradient design to give priming
  a chance to discriminate. A naive fixture with identical terminology across all libraries
  would make priming irrelevant and the gate trivially fail.
- **Local source validation in `resolve_dispatch_list`** was missed in the initial Task 3
  implementation and caught only in the Task 4 review pass, requiring a correction commit.
- **Mid-file imports in test_kb_orchestrator.py** — the audit and datetime imports were added
  at their point-of-use rather than at the top of file, requiring cleanup at final validation.

## What surprised us

- **The team-quality reframe (Steve's pushback on "ships without breaking" framing)** reshaped
  the entire Phase D scope. The original framing treated Phase D as polishing Phase A's edges.
  The reframe — "Phase D is what makes this production-worthy for a consulting practice" — was
  correct, and Phase D ended up being approximately the same size as Phase A (~25 commits each).
- **HARD GATE evidence showed Rule 1 (term-overlap) was not actually exercised.** Rule 2
  (KB config excerpt as interpretive lens) carried all of the discrimination in the validated
  fixture. Both pathways theoretically work, but only Rule 2 was empirically validated in this
  EPIC. Rule 1 would require a fixture where one library shares query terms with another —
  a harder fixture design problem deferred to future work.
- **97 tests at EPIC close** — the suite grew from 52 (Phase A) to 57 (Phase B) to 72 (Phase C)
  to 97 (Phase D), a net +25 in Phase D alone. Phase D added more tests than any prior phase.

## What we'd do differently next time

- **Build the multi-reviewer assessment into the EPIC plan, not after-the-fact.** Phase A's
  "ship clean per reviewer findings" only became Phase D's full scope after the post-A-B-C
  review. Scheduling a structured review after the first feature-complete phase would have
  surfaced these gaps earlier and allowed better sequencing.
- **Set up the HARD GATE explicitly in the EPIC plan.** The HARD GATE pattern (empirically
  validate the EPIC's differentiator before merging) was the right pattern. Future EPICs with
  operational claims should define their gate condition and fixture requirements in the spec,
  not discover them mid-implementation.
- **Commit black/flake8 hygiene incrementally.** Final pass cleaned 8 files; smaller hygiene
  commits after each task would have distributed the noise and caught issues sooner.

## Metrics

- **Implementation time:** 1 session 2026-04-26 (Phases A+B+C completed in 2026-04-24 session)
- **Tests added in Phase D:** 25 (registry charset/path/resolver: 7; audit: 8; audit
  instrumentation in orchestrator: 5; staleness: 3; shelf-index-header: 6; net = 25 across
  the new test files and additions to existing files)
- **Total test count at close:** 97 (Phase A: 52, Phase B: +5 = 57, Phase C: +15 = 72,
  Phase D: +25 = 97)
- **Commits on branch for Phase D:** ~25 task commits + plan + retrospective = ~27
- **Validation pipeline:** 9/10 PASS (`--pre-push` fails check 2 only — `pre-commit` binary
  not installed in this environment; same known issue as Phases A/B/C). All other 9 checks
  pass. `--syntax` and `--quick` both report PASS.
- **Reviewer findings caught vs missed:** Phase D addressed all 5 categories surfaced by the
  post-A-B-C reviewer assessment (code quality + security, HARD GATE, audit log,
  transparency, onboarding). Zero finding categories deferred.

## Decisions worth capturing in memory

- **`synthesis-librarian` with `tools: []`** is the canonical pattern for "structurally
  guaranteed no side effects" agents — applicable beyond synthesis to any agent that should
  be read-only by contract.
- **4-field shelf-index header** (`format_version`, `last_rebuilt`, `library_handle`,
  `domain`) is the right surface for library evolution. The bare `format_version` field
  was undersized for real operational needs.
- **Audit log project-scope** (`library/audit.log`) is the correct boundary. User-scope
  would mix engagements and create privacy/confidentiality risks.
- **Onboarding flow + verify-only mode in one skill** is cleaner than two separate skills.
  The `--verify-only` flag lets the same skill serve both first-time and audit use cases.
- **HARD GATE pattern:** define gate condition + fixture in spec; run gate mid-EPIC (not at
  close); accept borderline pass only when the mechanism is demonstrably exercised.
- **Phase D = operational maturity, not polish.** Framing a phase as "operational maturity"
  explicitly scopes it correctly; "polish" implies cosmetic fixes and understates the work.

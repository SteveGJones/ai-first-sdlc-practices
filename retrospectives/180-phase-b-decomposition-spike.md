# Retrospective: Phase B — Decomposition Spike

**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #180 (Phase B of EPIC #178)
**Status:** COMPLETE

---

## What we set out to do

Propose a candidate `programs` block decomposition for `ai-first-sdlc-practices` itself. Output: `research/sdlc-bundles/decomposition-spike.md` containing the decomposition, DDD bounded-context analysis, visibility rules, granularity targets, a worked example against an existing skill or agent, and an honest failure-mode assessment.

The spike's purpose is to derisk Phases D-E by establishing whether declared decomposition is workable on a real codebase before validators are built.

## What was built

`research/sdlc-bundles/decomposition-spike.md` — 639-line spike output containing:

1. Verdict (Section 0) — outcome (a) plausible-with-revision-required-before-Phase-E
2. Repo character analysis (Section 1) — repo is two co-located domains (framework + framework-meta-SDLC) with structural source-vs-distribution doubling
3. Candidate `programs` block (Section 2) — 1 program, 5 sub-programs, 14 modules in YAML form
4. Per-module DDD analysis (Section 3) — domain model + ubiquitous language + team scope + boundary per module
5. Visibility-rule DAG (Section 4) — source-code DAG holds; runtime data-flow cycle surfaced between framework-research and kb-skills-and-orchestration
6. Granularity targets (Section 5) — mixed `requirement | function | module` per module
7. Worked example (Section 6) — real annotations on `kb-query` cross-library synthesis, with namespaced IDs (`aisp.kb.kbsk.REQ-NNN`) matching METHODS.md schema
8. Failure-mode honest assessment (Section 7) — three anaemic-context risks with mitigations; one structural complexity (source-vs-distribution doubling)
9. Critical review by `sdlc-team-common:solution-architect` and response (Section 9) — verbatim verdicts plus inline fixes applied + four schema gaps deferred to Phase E

## What worked well

- **Dogfooding the `solution-architect` agent for review surfaced four schema gaps the spike author had missed.** Specifically: `release-packaging` mis-classified as consumer (it's a producer); `paths:` schema needs source/derived split; `kb-skills-and-orchestration` granularity should be `requirement` not `function`; ID format in worked example didn't match METHODS.md namespace schema. Without that review, those issues would have shipped to Phase E plan-writing and produced incorrect validator behaviour.
- **The architect-review-and-response loop is itself a small Method 2 dogfood signal.** The spike was written, peer-reviewed by a shipped specialist agent, revised in response, and shipped. That round-trip is the same shape Method 2 enables on customer engagements.
- **Picking real existing code for the worked example (PR #177's cross-library synthesis) made the example tractable.** Annotations against hypothetical features are easy; annotations against code that exists and ships forced honesty about coverage gaps and ID formats.
- **The `library/` entries from Phase A's prep paid off again** — the spike's anaemic-context detection rationale could draw on `library/decomposition-failure-modes.md` and `library/decomposition-ddd-bazel.md` directly, with citations preserved.

## What was harder than expected

- **The architect's review was rigorous and surfaced more issues than expected.** Six concrete revision items, two deferred to Phase E. The first-draft spike was over-claiming DDD discipline ("team-agent-library is a bounded context") in places where the truth was "directory grouping with a ubiquitous-language field attached". Took ~30 minutes to integrate fixes, but the result is materially better.
- **`release-packaging` being a cross-cutting producer (not consumer) was a blind spot.** The spike author conflated "reads paths" with "doesn't mutate" — release-packaging both reads sources from every other sub-program AND writes plugin-dir mirrors. That asymmetry has real validator implications the original spike missed.
- **The framework-research ↔ kb-skills-and-orchestration data-flow cycle was a genuine surprise.** Source-code imports form a DAG; runtime data-flow doesn't. Method 2's validators must explicitly handle this distinction; the spike now documents it but Phase E plan-writing must close the design call.

## Lessons learned

- **Dogfood specialist agents on design-judgment work**, not just on review of finished code. The architect agent's review of an in-progress design surfaced issues earlier and cheaper than discovering them during Phase E validator design. This generalises: invoke `sdlc-team-common:solution-architect` on architectural deliverables before they freeze; invoke `claude-plugin-security-risk:security-reviewer` on plugin contracts; invoke `sdlc-team-fullstack:backend-architect` on data-layer designs.
- **DDD discipline is harder to apply than it looks.** The spike author had real DDD knowledge (Evans, Vernon) but still produced "directory groupings with a ubiquitous-language field attached" in two places. The fix is to actually try writing the per-module ubiquitous-language entries side-by-side and ask: "do any two modules share half their language?" If yes, they may not be separate bounded contexts. Add this as a self-check during decomposition exercises.
- **`paths:` is more than a path list.** It's a contract about which paths the module owns vs derives. The spike's first draft conflated these. METHODS.md's `programs` block schema needs the source/derived split for plugin-mirror-doubling repos to work correctly under Method 2 validators.
- **Method 2's value proposition is reinforced by this exercise.** The worked example forced explicit decomposition of "kb-query does cross-library synthesis" into 5 named requirements with bidirectional traceability to 4 design elements, 3 tests, and 5 code locations — and that exercise itself surfaced a coverage gap (REQ-005 has no dedicated test) that nobody had noticed before. Method 2 isn't just bookkeeping; the discipline produces signal.

No new durable feedback memory captured this phase — the lessons above reaffirm `feedback_use_shipped_skills_and_agents.md` (which the architect-review dispatch directly applies) and `feedback_test_proves_completion.md` (the architect's review IS the proof-of-completion artefact for Phase B).

## Decomposition verdict

**(a) plausible decomposition** for the four content sub-programs (`framework-core`, `knowledge-base-system`, `workflows-system`, `framework-meta-sdlc`) — these have defensible DDD bounded-context boundaries.

**Reclassification required** for two cross-cutting / catalog sub-programs:
- `release-packaging` → `classification: cross-cutting-producer` (now declared inline)
- `team-agent-library` → `classification: pragmatic-grouping` with `anaemic-context-detection: suppressed` (now declared inline)

**Four schema gaps deferred to Phase E** as plan-writing inputs (not blocking Phase D):
1. `source-paths` / `derived-paths` distinction in `programs` block
2. `known-violation` field for declared exceptions (e.g. framework-research↔kb-skills data-flow cycle)
3. Cross-module-mutation validator
4. Formal `anaemic-context-detection` opt-out semantics

## Worked example assessment

`kb-query` cross-library synthesis (PR #177 code) annotated under proposed decomposition. Pattern works: namespaced IDs (`aisp.kb.kbsk.REQ-NNN`) per METHODS.md schema; `implements:` annotations on 5 functions; structural traceability from REQ → DES → TEST → CODE held throughout; `traceability-render` output is realistic.

Surfaced one real coverage gap during the exercise: `REQ-005` (canonical prompt formatting) has no dedicated test (covered indirectly via DES-001/DES-002 tests). That's exactly the kind of signal Method 2's `traceability-render` should produce — and the granularity raise from `function` to `requirement` (per architect review §5) is what makes the gap visible.

## Failure modes encountered

- **Anaemic-context risks (3)**: release-plugin skill cross-boundary, framework-research dogfood loop, team-agent-library coarse modules. Each has an explicit mitigation declared inline (validator support required for #1, accepted-as-known-violation for #2, declared `anaemic-context-detection: suppressed` for #3).
- **Boundary leak (1)**: source-vs-distribution doubling. Acknowledged as a Method 2 schema gap (per architect review §7), not just a policy concern. Phase E must close.
- **No premature-decomposition signal** identified beyond the slightly-over-decomposed `release-packaging` two-module split (could collapse to one if Phase F dogfood shows no value in keeping them separate).

## Validation

- Pre-push (--quick): **PASSED**, 0 errors, 0 warnings
- Plugin packaging: not affected (documentation-only changes)
- Technical debt: no new debt introduced
- Architect review: **dispatched and integrated** — six fixes applied inline, four deferred to Phase E with concrete plan-writing actions

## Phase verdict

Phase B complete. The decomposition spike is shippable as Phase B output. Phase D plan-writing (roadmap sequencing, skill inventory, commissioning flow) can use the spike as-is. Phase E plan-writing must close the four schema gaps (source/derived paths split, known-violation field, cross-module-mutation validator, anaemic-context-detection opt-out semantics) **plus a fifth gap (positional-vs-named ID format) surfaced by the containerised re-run** as part of its scope before validator design proceeds against this `programs` block.

## Phase B addendum (2026-04-27) — containerised re-run of the architect review

After Steve flagged that the in-session architect dispatch had no isolation, we re-ran the same architect review in a Docker container via `sdlc-workflows`:

- **Authored**: `.archon/teams/decomposition-review.yaml` team manifest + workflow YAML at `research/sdlc-bundles/dogfood-workflows/architect-review-spike.yaml` + command at `architect-review-spike.md`
- **Built**: `sdlc-worker:decomposition-review` team image via `/sdlc-workflows:deploy-team` mechanism (running `bash docker/build-team.sh decomposition-review`)
- **Ran**: `archon workflow run architect-review-spike --no-worktree` from a fresh git-seeded workspace, image-preprocessed via `preprocess_workflow.py`, ~3 minutes wall-clock
- **Output**: `research/sdlc-bundles/dogfood-workflows/architect-review-spike-output.md` (13.8KB independent review) + `architect-review-spike-run.log` (Archon CLI output)
- **Findings**: 3 NEW issues the in-session review missed:
  1. Material `paths:` coverage gap — six agent source directories not covered by any module's `paths:` (would have caused Phase D plan-writing scope errors)
  2. Positional-vs-named ID format divergence (fifth Phase E schema gap)
  3. `release-packaging` derived-path ownership subtlety in validator design

**This validated the dogfood case directly**: containerised re-runs produce material additional signal compared to in-session dispatch. The workflow YAML + command + team manifest are now reusable artefacts under `research/sdlc-bundles/dogfood-workflows/` for Phase D-E onwards.

**First-run failure honesty**: the first containerised run failed in 0.3 sec because we used `sdlc-worker:full` directly (the source image, not a runnable team image). The deploy-team mechanism rejected it correctly with `ERROR: sdlc-worker:full is a source image. Build a team image instead.` Iterated: built the team manifest, deployed the team image, re-ran successfully. Captured as a procedural lesson for Phase D-E.

**New durable feedback memory** captured at `memory/feedback_containerised_review_for_design_artefacts.md` — when a design review is load-bearing (architectural decompositions, security models, data schemas, API contracts), use the containerised mechanism by default; in-session dispatch is for quick-turnaround work where reproducibility doesn't matter.

## Phase B updated artefact list

- `research/sdlc-bundles/decomposition-spike.md` (724 lines now, with Section 10 capturing the containerised re-run findings)
- `research/sdlc-bundles/dogfood-workflows/architect-review-spike.md` — workflow command file
- `research/sdlc-bundles/dogfood-workflows/architect-review-spike.yaml` — workflow YAML
- `research/sdlc-bundles/dogfood-workflows/architect-review-spike-output.md` — independent containerised review verbatim (13.8KB)
- `research/sdlc-bundles/dogfood-workflows/architect-review-spike-run.log` — Archon CLI output for reproducibility
- `.archon/teams/decomposition-review.yaml` — team manifest
- `.archon/teams/.generated/decomposition-review-CLAUDE.md` — generated team CLAUDE.md (gitignored if .archon/teams/.generated/ is)

## References

- Parent EPIC: #178
- Issue: #180
- Feature proposal: `docs/feature-proposals/180-phase-b-decomposition-spike.md`
- Inputs: `library/decomposition-ddd-bazel.md`, `library/decomposition-failure-modes.md`, `research/sdlc-bundles/synthesis/overall-scope-update.md` Section 5
- Output: `research/sdlc-bundles/decomposition-spike.md`

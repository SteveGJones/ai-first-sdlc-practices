# Retrospective: EPIC #178 — Joint Programme + Assured Bundle Delivery

**Branch:** `feature/sdlc-programme-assured-bundles`
**EPIC:** #178 (subsumes #103 + #104; absorbs #98 as Phase C)
**Status:** COMPLETE — Phase G closure

---

## What we set out to do

Deliver Programme bundle (Method 1 — waterfall phase gates) and Assured bundle (Method 2 — agent-first specs with traceability + decomposition + KB-for-code) as a single coordinated EPIC. Subsumes existing sub-features #103 and #104. Built on top of EPIC #164's KB substrate (PR #177, merged 2026-04-26).

Phase model:

- **A — Design spec update** (#179) — incorporate 14 scope changes from research synthesis
- **B — Decomposition spike** (#180) — candidate `programs` block for this repo
- **C — Commissioning infrastructure** (#98) — bundle-installing skill + config schema
- **D — Programme bundle** (#103) — phase artefacts, gates, templates, reviews
- **E — Assured bundle** (#104) — IDs, decomposition, KB-for-code, change-impact, render
- **F — Real dogfood** — apply Assured to a real EPIC
- **G — Closure + PR**

## What was built

### Phase A — Design spec update (#179)

Incorporated 14 scope changes from the research synthesis (`research/sdlc-bundles/synthesis/`) into the canonical design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md`. Resolved cross-line evidence conflicts. Established Method 1 (Programme) and Method 2 (Assured) as joint deliverables under one EPIC rather than separate branches per sub-feature.

### Phase B — Decomposition spike (#180)

Produced the candidate `programs.yaml` for this repo and validated the decomposition primitive: **DDD bounded contexts as the primary unit, layered with Bazel-style visibility rules, with optional hexagonal architecture for within-module structure.** Containerised architect review (re-run after in-session review missed gaps) surfaced 3 issues that were resolved before Phase C. Worked example: 3 modules / 1 program for the bundle family. Failure modes captured: anaemic contexts (logic scattered across modules), premature decomposition (over-eager program splitting).

### Phase C — Commissioning infrastructure (#98)

Bundle contract specification at `docs/architecture/option-bundle-contract.md`. Three Python modules under `tools/commissioning/`: bundle manifest parser, commissioning record reader/writer, bundle installer. `commission` skill (root + plugin mirror). `.sdlc/team-config.json` schema documented. `sdlc-enforcer` agent extended to read commissioning record. End-to-end skill integration tests + mock-bundle fixture pattern. 11 tasks across the phase; containerised architect review at task 10.

### Phase D — Programme bundle (#103) — `sdlc-programme` v0.1.0

Method 1 substrate: 4 phase-gate validators (`requirements_gate`, `design_gate`, `test_gate`, `code_gate`); 5 skills (`commission-programme`, `phase-init`, `phase-gate`, `phase-review`, `traceability-export`); shared `spec_parser` for ID extraction; traceability matrix builder with csv + markdown exports; Articles 12-14 constitution overlay. 29 programme tests. Plugin packaging 13/13. Containerised architect review at task 14 surfaced 2 ship-blockers, fixed inline (Article 14 review-record enforcement gap; manifest `depends_on` missing two declarations). 15 tasks total.

### Phase E — Assured bundle (#104) — `sdlc-assured` v0.1.0

Method 2 substrate: 6 Python modules (`ids`, `traceability_validators`, `decomposition`, `code_index`, `render`, `export`); 8 skills (`commission-assured`, `req-add`, `req-link`, `code-annotate`, `module-bound-check`, `kb-codeindex`, `change-impact-annotate`, `traceability-render`); Articles 15-17 constitution overlay. KB integration via `synthesis-librarian`'s new `SYNTHESISE-ACROSS-SPEC-TYPES` mode. 6 export formats (DO-178C RTM, IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF, csv, markdown). End-to-end fixture + 74 assured tests. Plugin packaging 14/14. Containerised architect review at task 41 surfaced 3 ship-blockers, fixed inline (idempotency timestamp leak; `anaemic_context_detection` indistinguishable from `code_annotation_maps_to_module`; commission-assured KB-wiring documentation gap). 42 tasks total. Q1 (module-dependency-graph format) resolved as markdown edge-list in v0.1.0.

### Phase F — Real dogfood

Recursive application of Assured to EPIC #178 itself. Stale-recommendation reroute: design spec recommended #142 sub-features 3-8 but those merged 2026-04-10 (3 weeks before the spec was written); reselected to apply Method 2 to the bundles themselves for densest signal-per-day. Decomposition: 1 program / 3 modules (M1=programme-bundle, M2=assured-bundle, M3=kb-bridge); visibility M2→M1, M2→M3. Approach 3 (full coverage) explicitly chosen by the user with "you should absolutely not be cutting things down".

Delivered: 44 REQ/DES/TEST chains across 12 feature directories; 18 Python `# implements:` annotations + ~21 markdown HTML-comment annotations; 3 KB indexes (`library/_ids.md` 129 records, `library/_code-index.md` 18 entries, `library/_spec-findings.md`); 3 module-scope renders; dependency-graph render; DO-178C RTM smoke test (43 REQ rows, 65% empty source-code column); **9 findings (F-001 through F-009)** captured for v0.2.0. 22 tasks total.

### Phase G — Closure + PR

This retrospective; final pre-push validation; EPIC #178 PR opened.

## What worked well

- **The no-PR-until-EPIC-complete branch model** (precedent set by EPIC #164 / PR #177). 109 commits across 6 phases consolidated into one coherent merge. No partial-state surprises in CI, no branch coordination overhead, no premature reviews.
- **Containerised architect review** at every load-bearing handoff (Phase B, C, D, E). Each one surfaced ship-blockers that in-session review missed. The pattern is now durable: containerised review is the structural backstop for design integrity, not a nice-to-have.
- **Subagent-driven-development** with two-stage review per task scaled to 42 (Phase E) and 22 (Phase F) tasks without human-in-the-loop fatigue. Spec compliance review caught real missing-test-case gaps; code quality review caught manifest-vs-function-name divergence and validator-collapse issues.
- **Stage 1 tripwire pattern** (Phase F task 5) — proof-of-flow on the smallest module before scaling to the full plan caught F-001 (markdown annotation gap) at task 4 instead of task 16. Saved cascading re-work.
- **Findings file as a first-class artefact** (Phase F). Severities + reproduction + impact + suggested resolution made the v0.2.0 backlog auditable rather than buried in commit messages.
- **Q1 resolution discipline.** Open questions in design specs got marked "deferred to plan-writing" or "stretch in v0.2.0" with explicit format choices (markdown edge-list for module-dependency-graph) — kept v0.1.0 scope honest.
- **Recursive dogfood as test** — Phase F producing 9 substantive findings about Method 2 in 1 phase of work proves the approach generates signal that purely-internal review doesn't.

## What was harder than expected

- **Stale recommendation in the design spec** (Phase F target). The Phase E spec recommended #142 sub-features 3-8 as Phase F's dogfood target; those had already merged. Lesson: when designing a downstream phase that depends on upstream state, name the dependency at design time and re-verify at start.
- **Validator-vs-convention mismatches surfaced only by recursive dogfood.** `granularity_match` was specified expecting REQ-level annotations but the convention is DES-level — produced 100% noise (43/43 false-positives on the dogfood project). Unit tests passed because they tested REQ-level annotations specifically. Real-use convention diverged and only Phase F's recursive application revealed it (F-008).
- **Markdown annotation gap (F-001).** `_IMPLEMENTS_RE` regex matches Python comment syntax (`# implements:`) but not HTML-comment form (`<!-- implements: -->`). Result on the dogfood: only 18 of 129 annotations (14%) captured. `_IMPLEMENTS_RE` also has the surprising property that `# implements:` in markdown renders as an H1 heading. Method 2 v0.1.0 silently assumes Python-style comment syntax.
- **DO-178C RTM 65% gap (F-009).** The smoke-test export revealed how much real-use coverage Method 2 actually delivers: 65% of source-code column rows are placeholders. A regulator would not accept this. F-001 and F-008 cluster as the root cause.
- **Constitution-as-code category error (F-003).** Authoring a REQ that describes an Assured constitution article doesn't have a clean implementation target — the constitution IS the spec. Method 2's annotation discipline assumes everything has a code referent.
- **`visibility_rule_enforcement` is dormant without tooling** (F-007). The validator runs only against `ImportEdge` objects; nothing in v0.1.0 produces them from a real codebase. Validator only exercised via fixtures, not real Python source trees.
- **Containerised review's value is large but the pattern needs explicit choice.** When in-session Agent dispatch is convenient, the temptation is high. Phase B's first review missed gaps; the re-run via `sdlc-workflows` containers caught them. The discipline-feedback memory (`feedback_containerised_review_for_design_artefacts.md`) was paying off by Phase E.

## Lessons learned

- **Method 2 v0.1.0 is for Python-comment-syntax codebases.** Markdown-driven projects (skills, agents, structural docs) need a separate annotation story. The `<!-- implements: -->` HTML-comment form is the natural extension; v0.2.0 must support it.
- **Recursive dogfood is the highest-yield validation per hour.** 9 findings in 22 tasks, including 3 IMPORTANT findings that root-cause to a single fix. Internal architectural review and unit tests would not have surfaced F-008 (validator-vs-convention mismatch) — only real use did.
- **Containerised architect review is structural, not stylistic.** Treat it as a required gate at design-handoff boundaries (Phase B → C, D close, E close). The pattern is feedback-memory durable now.
- **Phase F's "spec recommends X / X was done" failure** is a class of error. Adding a "verify dependencies still apply" step to the plan-writing self-review prevents recurrence.
- **REQ-vs-docstring-paraphrase tension** is real. Method 2 doesn't have built-in safeguards against degenerate REQ writing ("function X exists"). Stage 1 tripwire (Phase F task 5) is the human-in-the-loop check that catches it. v0.2.0 should consider a REQ-quality lint rule (e.g., banned phrases like "exists", "is implemented").
- **Validators that share intent need disambiguation in the spec.** `code_annotation_maps_to_module` and `anaemic_context_detection` were functionally identical until Phase E architect review forced differentiation. Phase F architect review's lesson generalised: "if two validators report the same defect, one of them is wasted."
- **Findings cluster.** F-001, F-008, F-009 are 3 IMPORTANT-severity findings with one root cause (Python-only annotation parser + REQ-vs-DES granularity expectation). v0.2.0 fix scope is narrower than the finding count suggests.

## Test totals

At Phase G closure:

- **74 assured tests** (Phase E + Phase E architect-review-driven additions)
- **29 programme tests** (Phase D + Phase D task 14 review-record additions)
- **109 kb tests** (from EPIC #164, all still passing)
- **520 total project tests** all passing (no regressions through Phase F annotations)
- **Plugin packaging:** 14/14 verified
- **Pre-push validation:** 9/10 (the missing 1 is the documented pre-commit binary env limitation, pre-existing since EPIC #164)

## Branch state at PR

- **Commits ahead of main:** 109
- **Phases shipped:** A (#179), B (#180), C (#98), D (#103/#186), E (#104), F (no separate issue), G (this closure)
- **Plugins added:** `sdlc-programme` (v0.1.0), `sdlc-assured` (v0.1.0). Marketplace 12 → 14 plugins.
- **New skills:** 13 total — 5 in `sdlc-programme`, 8 in `sdlc-assured`.
- **New Python modules:** 11 total — 3 in `sdlc-programme/scripts/programme/`, 6 in `sdlc-assured/scripts/assured/`, plus shared support files.
- **New constitution articles:** 6 total (12-14 Programme, 15-17 Assured).
- **New templates:** 9 total (3 Programme + 6 Assured).
- **Containerised reviews:** 4 (Phase B re-run, Phase C task 10, Phase D task 14, Phase E task 41), all via `sdlc-worker:decomposition-review` Docker image, evidence in `~/.archon/archon.db` and `research/sdlc-bundles/dogfood-workflows/*-output.md`.

## What we deferred

Items considered and consciously deferred to future EPICs / v0.2.0:

- **Multi-program decomposition coordination** — design spec §8 lists this as out of scope; v0.1.0 supports one program per project. Multi-team SAFe-Lite is a future EPIC.
- **Bidirectional ReqIF sync** — one-way export only via `traceability-export`; ReqIF parser is plugin-shaped if anyone needs it.
- **Migration of pre-Assured projects' un-annotated code** — Method 2 is greenfield-friendly only.
- **Decomposition suggestion** — we validate declarations, never propose them.
- **Industry certification artefacts beyond one worked example** — v0.1.0 ships DO-178C, IEC 62304, ISO 26262, FDA DHF as templates. Compliance evidence and audit-trail tooling are out of scope.
- **AST-level code intelligence** — explicitly out per design spec §8. Comments, not semantics.
- **Automatic semantic change-impact detection** — `change-impact-annotate` is human-guided.

Items the dogfood (Phase F) surfaced as v0.2.0 priorities (the 9 findings):

1. **F-001 (IMPORTANT):** Extend `_IMPLEMENTS_RE` to accept HTML-comment form OR define markdown annotations as YAML frontmatter (`implements: [...]`).
2. **F-002 (MINOR):** Consider line-range or section-anchor support in `programs.yaml` `paths`.
3. **F-003 (MINOR):** Define `satisfies-by-existence` annotation concept for governance documents.
4. **F-004 (MINOR):** No code change — REQ inventory was corrected during authoring.
5. **F-005 (MINOR):** Strengthen REQ-001 of traceability-validators to make severity contract unambiguous, OR split warn-vs-block validators into separate REQs.
6. **F-006 (MINOR):** Consider a "see also" / "related-to" mechanism in the REQ format for overlapping intents.
7. **F-007 (MINOR):** Ship a Python-import extractor (`tools/import_scanner.py`) so `visibility_rule_enforcement` runs on real codebases.
8. **F-008 (IMPORTANT):** Extend `granularity_match` to accept indirect coverage (REQ covered if any `satisfies`-linked DES has an annotation), OR add `granularity: design` as a module option.
9. **F-009 (IMPORTANT):** Combined fix of F-001 + F-008 is the primary remediation; supplementary tooling for source-code column completeness checks is the secondary remediation.

The 3 IMPORTANT findings (F-001, F-008, F-009) cluster on a single root cause — Python-only annotation parser combined with REQ-vs-DES granularity expectation. A focused v0.2.0 EPIC can resolve all three.

## References

- Parent EPIC: #97 (Multi-Option Commissioned SDLC)
- This EPIC: #178
- Feature proposal: `docs/feature-proposals/178-programme-assured-bundles-epic.md`
- Research artefacts: `research/sdlc-bundles/`
- Library navigation hub: `library/sdlc-bundle-research-overview.md`
- Branch model precedent: EPIC #164 / PR #177
- Discipline precedent: `memory/feedback_test_proves_completion.md`, `memory/feedback_containerised_review_for_design_artefacts.md`

## Phase retrospectives

- Phase A: `retrospectives/179-phase-a-design-spec.md`
- Phase B: `retrospectives/180-phase-b-decomposition-spike.md`
- Phase C: `retrospectives/98-phase-c-commissioning-infrastructure.md`
- Phase D: `retrospectives/186-phase-d-programme-bundle-substrate.md`
- Phase E: `retrospectives/104-phase-e-assured-bundle-substrate.md`
- Phase F: `retrospectives/178-phase-f-dogfood.md`

This EPIC retrospective consolidates findings from each phase retro. The 9 findings from Phase F seed the v0.2.0 backlog.

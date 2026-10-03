# Feature Proposal: Joint Programme + Assured Bundle Delivery

**Proposal Number:** 178
**Status:** In Progress
**Author:** Steve Jones (commissioning), Claude (drafting)
**Created:** 2026-04-26
**Target Branch:** `feature/sdlc-programme-assured-bundles`
**EPIC:** #178 (Joint Programme + Assured bundle delivery, subsumes #103 + #104)
**Parent EPIC:** #97 (Multi-Option Commissioned SDLC)

---

## Summary

Deliver Programme bundle (Method 1 — waterfall phase gates) and Assured bundle (Method 2 — agent-first specs with traceability + decomposition + KB-for-code) as a single coordinated EPIC, on a single long-lived branch, following the proof-of-completion discipline established by EPIC #164. Subsumes existing sub-features #103 (Programme) and #104 (Assured) and absorbs #98 (commissioning infrastructure) as a Phase C dependency.

## Sub-features

This EPIC's scope is delivered as 7 phases, tracked via dedicated GitHub issues:

| Phase | Issue | Phase deliverable |
|---|---|---|
| A | #179 | Design spec update — incorporate 14 scope changes from research synthesis |
| B | #180 | Decomposition spike — candidate `programs` block for this repo |
| C | #98 | Commissioning infrastructure (existing) |
| D | #103 | Programme bundle implementation (existing) |
| E | #104 | Assured bundle implementation (existing) |
| F | (file at start) | Real dogfood — apply Assured to a candidate EPIC |
| G | (covered by retrospective) | Closure + PR |

Each phase ships its own feature proposal, its own retrospective, and incremental commits on the shared branch.

## Motivation

### Why this EPIC exists

The framework supports a "good enough for most product teams" SDLC today. It does not yet support two distinct shapes that mature engineering organisations need:

1. **Method 1 — formal waterfall phase gates** with explicit phase boundaries (requirements → design → test → code), each producing a reviewable specification artefact, and gates between phases enforcing prior-phase completion. Normal at programme-of-work scale and in regulated industries.
2. **Method 2 — agent-first specifications with end-to-end traceability**, where requirements, design elements, tests, and code are individually identified, bidirectionally linked, and queryable through the same knowledge-base substrate the framework already uses for findings. Decomposition is declared up-front so any agent works with a small, scoped slice rather than the whole system in context.

Method 1 fits the **Programme** option in EPIC #97's commissioning model. Method 2 fits the **Assured** option (regulated-industry-grade, traceability mandatory).

### Why joint delivery

A three-stage research campaign (Stage 1 plan, Stage 2 deep research on Claude Desktop, Stage 3 synthesis in Claude Code) produced 61,061 words across 14 artefacts. The campaign established that Method 2 is Method 1 with a richer underlying data model — they share substrate (templates, gates, cross-phase reviews); building Method 1 alone would be the half-step. The framework author's call (2026-04-26) is that Method 2 is more state-of-the-art and immediately useful for moving practice forwards, so they ship together.

The research artefacts live in `research/sdlc-bundles/`. The library entries are in `library/` for librarian retrieval.

### Why now

The cross-library KB query work (EPIC #164, PR #177 merged 2026-04-26) shipped the substrate — `research-librarian`, `synthesis-librarian` with attribution post-check, `kb-rebuild-indexes` regenerable indexes — that Method 2 builds directly on top of. Method 2's KB extension to code is a thin annotation-driven addition to existing infrastructure, not new infrastructure. The timing is right: KB substrate is mature and merged.

### User stories

- As a regulated-industry team commissioning the Assured bundle, I get a defensible bidirectional-traceability substrate satisfying ISO 26262, DO-178C, IEC 62304, IEC 61508, and FDA 21 CFR Part 820 simultaneously.
- As a programme-of-work team commissioning the Programme bundle, I get formal phase gates with cross-phase review enforcement, blocking commits where required artefacts are missing.
- As an AI agent dispatched into a decomposed Method 2 project, I work with a bounded scope (one module's REQs / DESs / TESTs / CODE) and the librarian retrieves only what's relevant to my current task — context window stays focused.
- As a framework author, I can dogfood Method 2 on this repo's own EPIC #142 sub-features 3-8 work, validating the design holds up before recommending it externally.

---

## Proposed Solution

The phase model is the proposal. Each phase is independently scoped, has its own feature proposal, and ships its own retrospective. The full set ships together at PR time on `feature/sdlc-programme-assured-bundles`.

### Phase A — Design spec update (#179)

Incorporate the 14 scope changes from `research/sdlc-bundles/synthesis/overall-scope-update.md` into:

- METHODS.md (the campaign reference document)
- A new design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md`

Each change must trace back to a specific synthesis citation in the form `[Line N: Section X entry Y]`. This is editorial work over a converged design; small (~half day) but high-discipline.

### Phase B — Decomposition spike (#180)

Propose a candidate `programs` block for `ai-first-sdlc-practices` itself. Output is `research/sdlc-bundles/decomposition-spike.md` containing the decomposition, DDD bounded-context analysis, visibility rules, granularity targets, a worked example, and an honest failure-mode assessment.

Why before Phase D-E: Method 2's promise depends on someone declaring a sensible decomposition; we don't have one for our own repo yet, and Phase F will require it. Doing the spike now derisks the whole back half of the EPIC.

### Phase C — Commissioning infrastructure (#98)

The pre-existing scope of #98: bundle contract, commission skill, `.sdlc/team-config.json` schema extension, sdlc-enforcer awareness. Required prerequisite for Programme + Assured to install via `/sdlc-core:commission`. Absorbed into this EPIC rather than landed separately to avoid coordination overhead.

### Phase D — Programme bundle implementation (#103)

Phase artefacts (req-spec, design-spec, test-spec), phase gates, templates, `phase-review` skill, `traceability-export` skill (basic format). Delivered as the `sdlc-programme` plugin.

### Phase E — Assured bundle implementation (#104)

ID registry, decomposition validators, KB extension to code (`kb-codeindex`), librarian extensions for spec-as-finding and synthesis-across-spec-types, `change-impact-annotate` skill, optional `change-impact-gate` validator, `traceability-render` skill, `traceability-export` skill (standard-specific formats), `code-annotate` skill. Delivered as the `sdlc-assured` plugin.

### Phase F — Real dogfood

Apply Assured (and where appropriate Programme) to a real EPIC on this repo. Candidate per CLOSEOUT recommendation: EPIC #142 sub-features 3-8 (technology registry work). Validates design in practice; surfaces gaps before external recommendation.

### Phase G — Closure

Retrospective consolidating all phase retros; PR drafting; merge.

## Success Criteria

- [ ] Phase A spec update committed; 14 scope changes traceable to synthesis citations
- [ ] Phase B decomposition spike committed; candidate `programs` block proposed
- [ ] Phase C commissioning skill operational; bundles install via `/sdlc-core:commission`
- [ ] Phase D Programme bundle plugin packaged and installable
- [ ] Phase E Assured bundle plugin packaged and installable
- [ ] Phase F dogfood applied to one real EPIC; lessons captured in retrospective
- [ ] Phase G retrospective consolidates findings; PR opened with clean CI
- [ ] All 109+ existing kb tests still pass; new tests added per the proof-of-completion discipline (`feedback_test_proves_completion.md`)
- [ ] Plugin packaging passes (12+ plugins; new ones added to marketplace.json)
- [ ] Pre-push validation passes (or 9/10 with documented pre-commit env limitation)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Decomposition declaration is non-trivial; we may discover the framework can't sensibly decompose its own repo | Phase B finding undermines Method 2's premise | Phase B's "good enough" definition includes the negative outcome — if decomposition shows the repo isn't decomposable under the primitive, that's a finding that reshapes Method 2's commissioning guidance |
| `kb-rebuild-indexes` byte-idempotence is now load-bearing; current implementation may not guarantee it | Tool-neutrality promise broken | Phase D acceptance test: regenerability test that runs `kb-rebuild-indexes` twice and asserts byte-identical output |
| Branch grows huge (80-120 commits projected) | Review difficulty at PR time | Same mitigation as #164 — phased commits, feature proposals per phase, retrospectives per phase, closure retrospective consolidates |
| Phase F dogfood reveals fundamental design issues | Rework required late in EPIC | Phase B spike is meant to surface this earlier; if Phase F reveals serious issues, we either iterate or land what we have with documented limitations |
| Constitution Article additions needed | Framework-level change scope creep | Phase A includes Constitution review; defer authoring of new articles to a separate proposal if needed |
| #98 commissioning scope drifts | Phase C delay blocks D-E | #98 has its own scope per existing proposal; we work within it without re-scoping |

## Out of scope

- **AST-level code intelligence.** No call graphs, no semantic search.
- **IDE integration.** Filesystem-first.
- **Full ALM database.** Markdown + Git only.
- **Industry certification itself.** Substrate that helps reach assurance; not certification.
- **Decomposition suggestion.** Framework enforces declared decomposition; doesn't suggest where edges go.
- **Bidirectional ReqIF sync.** One-way export only.
- **Migration of pre-existing projects' un-annotated code.** Ship a coverage checker; not an auto-annotator.
- **Single-team bundle (#99) and Solo bundle (#100).** Separate EPIC #97 sub-features; this EPIC is Programme + Assured only.

## Dependencies

- **#98** (Commissioning infrastructure) — absorbed as Phase C
- **EPIC #164** (Cross-library KB query) — ✅ merged on PR #177; provides the KB substrate Method 2 builds on
- **`sdlc-knowledge-base` plugin v0.2.0** — ✅ shipped on PR #177

## Implementation plan

Phase-by-phase commits on `feature/sdlc-programme-assured-bundles`. Each phase has:

1. Feature proposal (`docs/feature-proposals/<n>-phase-<x>-<slug>.md`)
2. Retrospective scaffold (`retrospectives/<n>-phase-<x>-<slug>.md` — created at phase start, completed at phase end)
3. Sub-feature plan (`docs/superpowers/plans/...` — created via writing-plans skill)
4. Implementation commits with the proof-of-completion discipline
5. Phase retrospective at completion

Final EPIC retrospective at Phase G consolidates all phase retros and any framework-level lessons.

## Closing the EPIC

PR opened on `feature/sdlc-programme-assured-bundles` against main at Phase G completion. Same model as PR #177 (EPIC #164):

- Comprehensive PR body with phase-by-phase summary
- Test plan with each phase's acceptance criteria reproduced
- CI fully green (or 9/10 with documented env limitation)
- Plugin packaging verified
- Library entries committed for retrieval discipline

## References

- Parent EPIC: #97 (Multi-Option Commissioned SDLC)
- This EPIC: #178 (Joint Programme + Assured delivery)
- Phase A: #179
- Phase B: #180
- Subsumed sub-features: #103 (Programme), #104 (Assured)
- Absorbed sub-feature: #98 (Commissioning infrastructure)
- Research artefacts: `research/sdlc-bundles/PLAN.md`, `METHODS.md`, `synthesis/overall-scope-update.md`, `CLOSEOUT.md`
- Library navigation hub: `library/sdlc-bundle-research-overview.md`
- Branch model precedent: EPIC #164 (PR #177)
- Discipline precedent: `memory/feedback_test_proves_completion.md`

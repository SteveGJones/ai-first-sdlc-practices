# Feature Proposal: Phase A — Design Spec Update

**Proposal Number:** 179
**Status:** In Progress
**Author:** Steve Jones (commissioning), Claude (drafting)
**Created:** 2026-04-26
**Target Branch:** `feature/sdlc-programme-assured-bundles`
**EPIC:** #178 (Joint Programme + Assured bundle delivery)
**Sub-feature:** #179 (Phase A of #178)

---

## Summary

Incorporate the 14 scope changes from `research/sdlc-bundles/synthesis/overall-scope-update.md` Sections 3 and 4 into:

1. `research/sdlc-bundles/METHODS.md` — the campaign reference document, updated section-by-section without losing existing content
2. A new authoritative design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` — the spec used for plan-writing in subsequent phases

Each scope change must trace back to a specific synthesis citation in the form `[Line N: Section X entry Y]`. This is editorial work over a converged design; high-discipline, expected effort half a day.

## Sub-features

None — Phase A is a single deliverable.

## Motivation

The research synthesis has converged on 14 specific scope changes (4 for Method 1 / Programme bundle, 10 for Method 2 / Assured bundle). They are not yet reflected in METHODS.md (which is the design document the Stage-2/3 prompts referenced). Without this update:

- Plan-writing in subsequent phases would draw from a stale METHODS.md that doesn't include research-confirmed decisions
- The traceability discipline the framework values (every claim cited; every design decision linkable to research) would be broken at the framework's own design layer
- Future agents working on Phases D-E would re-discover decisions already made

This phase makes the synthesis decisions canonical.

## Proposed Solution

### Two deliverables

**1. `research/sdlc-bundles/METHODS.md` — section-by-section update**

For each scope change, locate the affected METHODS.md section (synthesis Sections 3-4 cite specific lines; e.g. "METHODS.md Section 4, 'Bidirectional traceability' subsection (lines 156-164)"), apply the proposed-replacement text, and add inline `[Line N: Section X entry Y]` citations to the synthesis source.

The 14 changes:

**Method 1 — Programme bundle (4 changes)**

| # | Section | Change type | Source |
|---|---|---|---|
| 1 | Phase gates (lines 73-82) | Clarify | Line 1 §3 Claims 1, 5; Line 3 §3 Claims 1-3 |
| 2 | Skills shipped (lines 96-101) | Add `traceability-export` skill | Line 1 §3 Claim 6 |
| 3 | Model selection hints (lines 103-105) | Clarify | Cross-line agreement 1 |
| 4 | Skills shipped (lines 96-101) | Make `phase-review` mandatory | Cross-line agreement 1 |

**Method 2 — Assured bundle (10 changes)**

| # | Section | Change type | Source |
|---|---|---|---|
| 1 | Decomposition (lines 166-180) | Enrich with DDD + Bazel | Cross-line agreements 1, 5; Line 2 §3 Claims 1, 2, 4, 7 |
| 2 | ID registry (lines 139-146) | Refactor support without ID loss | Line 2 §3 Claim 6 |
| 3 | Bidirectional traceability + Skills | Strengthen annotation validation; add `code-annotate` | Cross-line agreement 4; Line 2 §3 Claim 5; Line 1 §3 Claim 2 |
| 4 | KB extension to code (lines 182-194) | Optional hexagonal tagging | Line 2 §3 Claim 3 |
| 5 | Skills + new optional validators | Add `change-impact-annotate` + optional gate | Cross-line agreement 6; Line 1 §3 Claims 2, 5 |
| 6 | Skills shipped (lines 202-208) | Add `traceability-export` with standard formats | Line 1 §3 Claim 6 |
| 7 | Decomposition | Add granularity validation | Cross-line agreement 7; Line 1 §3 Claim 3 |
| 8 | New subsection after Skills shipped | Commissioning guidance | Line 2 §3 Claim 7; Line 1 §3 Claims 1, 5 |
| 9 | Out of scope (lines 232-240) | Strengthen certification disclaimer + add ReqIF disclaimer | Line 1 §3 Claim 7; Line 3 §3 Claim 7 |
| 10 | New subsection after Decomposition | Organisational metadata stays optional | Line 3 §4 Rejection C |

**2. `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` — new design spec**

Authoritative design spec for plan-writing in subsequent phases. References METHODS.md as the scope document; includes:

- Executive summary
- The two methods at a glance (drawn from METHODS.md §2)
- Method 1 detail (METHODS.md §3 + Phase A scope changes)
- Method 2 detail (METHODS.md §4 + Phase A scope changes)
- Decomposition primitive — final call (Section 5 from synthesis)
- Traceability rigour calibration — final call (Section 6 from synthesis)
- sphinx-needs adoption boundary (Section 7 from synthesis)
- Out of scope (METHODS.md §6 + scope changes)
- Open questions deferred to plan-writing (synthesis Section 9)
- Reference list

Sized so a writing-plans subagent can use it standalone (the spec is self-sufficient context for plan-writing).

## Success Criteria

- [ ] All 14 scope changes incorporated into METHODS.md with inline `[Line N: Section X entry Y]` citations
- [ ] New design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` exists and is plan-writing-ready
- [ ] Each section of the design spec cites METHODS.md or research synthesis as source
- [ ] Open questions from synthesis Section 9 listed in spec's "deferred to plan-writing" section
- [ ] Pre-push validation passes (documentation-only changes; no new technical debt)
- [ ] Phase A retrospective captures lessons (if any) from translating synthesis findings into spec form
- [ ] Commits use heredoc-form messages with co-author trailer per repo convention

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| METHODS.md edit conflicts with section line numbers (synthesis cites exact lines, but lines shift as changes are applied) | Citation pointers go stale | Apply changes section-by-section; recompute line numbers after each insertion; or shift to anchor-based references (e.g. "the Bidirectional traceability subsection") |
| Design spec duplicates METHODS.md content rather than referencing it | Future maintenance burden — two documents to keep in sync | Spec should reference METHODS.md as the scope source; spec includes its own narrative but defers detail to METHODS.md sections |
| Open questions from synthesis Section 9 are not addressable in spec; need plan-time resolution | Spec is incomplete | List open questions explicitly under "deferred to plan-writing" section with each open question's resolution path; this is the synthesis's already-recommended treatment |

## Out of scope (this phase)

- Implementation of any skill or validator (Phases D, E)
- Commissioning skill design (Phase C)
- Repo decomposition spike (Phase B)
- Plan-writing (deferred until both A and B complete)

## Dependencies

- Research synthesis at `research/sdlc-bundles/synthesis/overall-scope-update.md` — ✅ committed
- METHODS.md — ✅ exists at `research/sdlc-bundles/METHODS.md`

## Implementation plan

Single phase, executed inline (no subagent dispatch needed for this scope of editorial work):

1. Read METHODS.md fully
2. Apply Method 1's 4 changes section-by-section
3. Apply Method 2's 10 changes section-by-section
4. Verify every change has an inline citation
5. Write the new design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md`
6. Run pre-push validation
7. Commit METHODS.md + new design spec in a single commit
8. Complete Phase A retrospective

## Closing the phase

When all Success Criteria are checked, mark issue #179 closed and reference the commit SHA(s). Phase B (#180) starts independently.

## References

- Parent EPIC: #178
- Research synthesis: `research/sdlc-bundles/synthesis/overall-scope-update.md`
- METHODS.md: `research/sdlc-bundles/METHODS.md`
- Library navigation hub: `library/sdlc-bundle-research-overview.md`

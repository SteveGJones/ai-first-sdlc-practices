# Retrospective: Phase A — Design Spec Update

**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #179 (Phase A of EPIC #178)
**Status:** COMPLETE

---

## What we set out to do

Incorporate the 14 scope changes from `research/sdlc-bundles/synthesis/overall-scope-update.md` Sections 3 and 4 into:

1. METHODS.md (campaign reference document)
2. New design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md`

Each scope change traceable to a specific synthesis citation.

## What was built

Two deliverables, both committed:

1. **METHODS.md updated** — 14 scope changes from `research/sdlc-bundles/synthesis/overall-scope-update.md` Sections 3-4 incorporated section-by-section. 26 inline citations added in `[Line N: §X Claim Y]` and `[Cross-line agreement N]` and `[Phase A change N]` form. Existing content preserved; new content woven into the original sections.

2. **New design spec** at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` (287 lines, 10 sections). Authoritative source for plan-writing in subsequent phases. References METHODS.md as the scope document; integrates the headline final-call sections (decomposition primitive, traceability rigour, sphinx-needs adoption boundary) directly.

## What worked well

- **Anchor-based search-and-replace via Edit tool** worked cleanly — no line-number drift problems despite multiple sequential edits. The synthesis cited specific subsections by name as well as line ranges, so anchoring on subsection headers and verbatim original text was precise.
- **Citation discipline scales naturally**. Adding `[Line N: §X Claim Y]` references inline preserved traceability without breaking readability. The pattern from research synthesis maps cleanly onto framework documentation — the framework now models the discipline it teaches.
- **Library entries from previous step were genuinely useful** — when applying scope changes, having `library/decomposition-ddd-bazel.md` and `library/regulatory-traceability-baseline.md` already curated gave precise paragraph-shaped content to drop into METHODS.md.
- **The new design spec is plan-writing-ready**: all five Method 2 final-call sections (Section 5, 6, 7) are self-contained enough that a writing-plans subagent can use it standalone, without re-reading the full synthesis chain.

## What was harder than expected

- **Method 2 changes Are deeply interconnected.** Decomposition (change 1), refactoring-without-ID-loss (change 2), granularity validation (change 7), and commissioning guidance (change 8) all reshape the same decomposition story. Applied as separate edits in order, they read coherently in the result, but the order matters — applying change 8 before change 1 would have created stale guidance referencing pre-change decomposition language.
- **Out-of-scope (change 9) needed two distinct additions** — strengthening the certification disclaimer AND adding a new ReqIF bullet — applied in one Edit.
- **No technical debt impact, no logging compliance impact, no plugin packaging changes** — pure documentation scope as expected. Quick validation passed clean.

## Lessons learned

- **Citation form `[Line N: §X Claim Y]` works as a portable, traceable citation across documents.** The synthesis used this form; METHODS.md now uses it; the design spec uses it. Future plan-writing should preserve the form so claims trace all the way back to research output.
- **Library entries written *before* applying scope changes paid off twice** — once for librarian retrieval (the original purpose) and once as paragraph-shaped content for METHODS.md edits. Worth doing earlier in any future research → spec cycle.
- **The "Wright way" sequence (issues → spec → spike) gave each step clear inputs.** Issues filed with explicit scope; feature proposals committed; retrospective scaffolds in place; then the spec work had clear rails. Discipline as scaffolding — not bureaucracy.

No durable feedback memory captured this phase — patterns above are all reaffirmations of existing memories (`feedback_test_proves_completion`, citation discipline, library curation discipline).

## Validation

- Pre-push (--quick): **PASSED**, 0 errors, 0 warnings
- Plugin packaging: not affected (documentation-only changes)
- Technical debt scan: no new debt introduced
- Logging compliance: not affected
- All 109 kb tests still pass (no code changes)

## Phase verdict

Phase A complete. METHODS.md and the new design spec are ready inputs for Phase B (decomposition spike) and Phase C-G plan-writing. No follow-up work blocks Phase B.

## References

- Parent EPIC: #178
- Issue: #179
- Feature proposal: `docs/feature-proposals/179-phase-a-design-spec.md`
- Inputs: `research/sdlc-bundles/synthesis/overall-scope-update.md`, `research/sdlc-bundles/METHODS.md`
- Outputs: METHODS.md (updated), `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` (new)

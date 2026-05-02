# Retrospective #190 — v0.2.0 Adoption Surface

**Issue:** [#190](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/190)
**Branch:** `feature/190-v020-adoption-surface`
**Proposal:** [`docs/feature-proposals/190-v020-adoption-surface.md`](../docs/feature-proposals/190-v020-adoption-surface.md)
**Status:** SKELETON (filled in throughout implementation; finalised before PR)
**Started:** 2026-05-02

---

## What we set out to do

Close the adoption-surface gap left by EPICs #178 and #188: documentation, version metadata, and the `setup-team` onboarding skill did not surface the new `sdlc-programme` and `sdlc-assured` bundles to fresh users, even though the underlying capability (and the four-option commission infrastructure) was complete in `main`.

See [feature proposal section 1](../docs/feature-proposals/190-v020-adoption-surface.md#1-problem-statement) for the gap analysis.

## What we shipped

_(to be filled in commit-by-commit)_

- **Tier 1 — version metadata:** _(pending)_
- **Tier 2 — fresh-user discovery:** _(pending)_
- **Tier 3 — setup-team gating:** _(pending)_
- **Tier 4 — bundle self-documentation:** _(pending)_
- **Tier 5 — METHODS-GUIDE + secondary surfaces:** _(pending)_

## What went well

_(to be filled in)_

## What was harder than expected

_(to be filled in)_

## What we learned

_(to be filled in — particularly: any feedback memories worth distilling for future sessions)_

## What we deferred

_(to be filled in — should align with proposal Section 5 "Out of scope" plus anything discovered during implementation)_

## Validation evidence

_(to be filled in — pre-push run output, dogfood notes from running `setup-team` with each of the four method answers, screenshots/captures of the README's new method-selection section if useful)_

## Follow-up issues opened

_(to be filled in — likely zero if scope held)_

## Sign-off checklist

- [ ] All 13 acceptance criteria from proposal Section 6 met
- [ ] `python tools/validation/local-validation.py --pre-push` passes (10/10)
- [ ] `python tools/validation/check-plugin-packaging.py` passes
- [ ] `python tools/validation/check-broken-references.py` passes
- [ ] In-session `superpowers:code-reviewer` review complete
- [ ] In-session `sdlc-team-docs:technical-writer` review complete on METHODS-GUIDE.md and audit-readiness section
- [ ] Dogfood: `/sdlc-core:setup-team` walked through with each of solo / single-team / programme / assured answers; observed expected install recommendations
- [ ] Dogfood: cold re-read of `README.md` → `METHODS-GUIDE.md` → bundle READMEs confirms a coherent path for fresh users
- [ ] CHANGELOG.md v0.2.0 entry reviewed against EPIC #188 retrospective for accuracy
- [ ] PR body summarises the 13 acceptance criteria and links to this retrospective

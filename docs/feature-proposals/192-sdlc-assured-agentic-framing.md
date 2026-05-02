# Feature Proposal: sdlc-assured Agentic-Delivery Use Case

**Proposal Number:** 192
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-05-02
**Target Branch:** `feature/192-sdlc-assured-agentic-framing`

---

## Executive Summary

The sdlc-assured docs currently frame the bundle almost exclusively as "for regulated industries" (DO-178C, IEC 62304, ISO 26262, FDA DHF). The original design intent (METHODS.md §2) included a second, equally valid use case: complex agentic systems with bounded-context decomposition needs. This fix adds a parallel use-case block to the README and METHODS-GUIDE so that agentic-delivery teams self-select correctly instead of skipping the bundle.

---

## Motivation

### Problem Statement

The METHODS.md design doc (research/sdlc-bundles/METHODS.md §2) states two motivations for Method 2 (Assured):

1. Regulated-industries traceability — "individual identification of requirements, design elements etc to give full traceability of code back to requirements"
2. Agentic delivery at scale — "uses similar approaches to our knowledge base to enable access to those requirements... optimising the context window... a smaller context [for the agent], and be less prone to misimplementing requirements because it 'knows too much'"

PR #191 (v0.2.0 adoption surface) positioned the bundle almost entirely on motivation 1. A reader of `plugins/sdlc-assured/README.md` or `docs/METHODS-GUIDE.md` today would conclude "this is for medical-device / avionics / automotive teams" and skip it if building a non-regulated agentic system — even though the bundle was designed with that use case in mind. The docs aren't wrong; they're just narrowly framed.

### User Stories

- As a team building a complex multi-agent platform (non-regulated), I want to understand whether sdlc-assured applies to me so that I can make an informed SDLC method choice.
- As a solo developer building a large agentic system with hundreds of bounded contexts, I want to know that sdlc-assured's positional IDs + KB-for-code + decomposition validators exist for context-window management — not just audit trail — so that I can evaluate the bundle on its merits for my use case.

---

## Proposed Solution

1. Add a "Use Assured when" block in `plugins/sdlc-assured/README.md` that lists both use cases side by side: (a) regulated industries and (b) complex agentic systems with bounded-context decomposition needs. Explain the underlying value prop — "give each agent a small scoped slice rather than the whole system in context" — in plain terms.

2. Update `docs/METHODS-GUIDE.md` in the Method 2 section to mirror the same dual framing, so the decision tree steers agentic teams toward Assured where appropriate.

3. No renaming, no API changes, no new validators. Doc-only change.

### Acceptance Criteria

Given a reader building a complex non-regulated agentic system  
When they read `plugins/sdlc-assured/README.md`  
Then they see a clear "use Assured for: agentic systems at scale" block alongside the regulated-industries block

Given a reader using `docs/METHODS-GUIDE.md` to pick an SDLC method  
When they reach the Method 2 / Assured entry  
Then the description names both regulated-industries AND agentic-scale as trigger conditions

---

## Success Criteria

- [ ] `plugins/sdlc-assured/README.md` has a "Use Assured when" or equivalent section that explicitly names the agentic-delivery use case
- [ ] `docs/METHODS-GUIDE.md` Method 2 description names both use cases
- [ ] All existing tests still pass (`pytest`)
- [ ] `check-broken-references.py` passes (no new broken links)
- [ ] Docs reviewed and approved

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-broadening — making Assured sound like the default for all projects | Low adoption of simpler methods | Keep framing conditional ("if you have 10+ bounded contexts…") |
| Inconsistency with CLAUDE.md / AGENT-INDEX.md descriptions | Reader confusion | Update CLAUDE.md and AGENT-INDEX.md descriptions if they repeat the narrow framing |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `plugins/sdlc-assured/README.md` |
| Modify | `docs/METHODS-GUIDE.md` |
| Modify | `CLAUDE.md` (if sdlc-assured description repeats narrow framing) |

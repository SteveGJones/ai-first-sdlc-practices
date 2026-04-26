# Feature Proposal: Cross-Library KB Query — Phase C Synthesis

**Proposal Number:** 169
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-24
**Target Branch:** `feature/164-cross-library-kb-query` (continues from Phases A + B)
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-feature:** #169 (sub-3 of 3 in v1)

## Summary

Activate cross-library synthesis. When the user asks a synthesis question and findings span multiple libraries, kb-query produces a connected argument with mandatory inline `[handle]` attribution on every supporting-evidence claim, validated by the structural post-check from Phase A.

## Motivation

See EPIC #164 body and design spec §3.3 (synthesis as architectural property), §6.2 (data flow), §7.1 (attribution integrity hard invariant). Phases A and B delivered the foundation and priming respectively; Phase C is the third leg of the v1 deliverable. Without it, the EPIC ships per-source retrieval only — the user has to draw cross-library connections manually.

## Proposed Solution

Full design in `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`.

Phase C implementation per spec §6.2 (synthesis flow) and §7.1 (attribution invariant). Adds three orchestrator helpers (`is_synthesis_query`, `format_synthesis_prompt`, `run_synthesis_query`) and one new dataclass (`SynthesisQueryResult`). Reuses the Phase A `check_synthesis_attribution` validator with the registry's known handles passed as the `valid_handles` whitelist. The librarian agent prompt gains a "synthesise-across-sources" mode section.

## Success Criteria

Per issue #169 acceptance criteria:

- [x] `is_synthesis_query(question)` heuristic detects synthesis intent via phrase matching
- [x] `format_synthesis_prompt` renders the synthesis dispatch message including PRIMING_CONTEXT, per-source findings, and explicit instructions forbidding file reads
- [x] `run_synthesis_query` skips synthesis when the question is retrieval-shaped or fewer than 2 sources have findings
- [x] `run_synthesis_query` aborts and falls back to retrieval-with-error-block when attribution post-check fails or dispatcher raises
- [x] Librarian agent prompt has a SYNTHESISE-ACROSS-SOURCES mode section covering the input format, attribution requirements, and the no-evidence rule
- [x] kb-query skill Step 6 dispatches a real synthesis call (not a placeholder) when conditions are met
- [x] All Phase A and B tests still pass; `check-plugin-packaging.py` reports 12 plugins verified
- [ ] `python tools/validation/local-validation.py --pre-push` passes (modulo pre-commit env issue) — verified in Task 7

## Out of scope (phase C)

- RemoteAgentSource (deferred EPIC)
- E2E tests with real librarian dispatch (deferred — would require live agent runs)
- Tuning the synthesis heuristic (`is_synthesis_query`) based on real usage data
- Synthesis ingest, lint, staleness-check (kb-* skills remain local-only in v1)

## Dependencies

- Blocked by: #167 (Phase A) — **complete**
- Benefits from: #168 (Phase B) — **complete**

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-c.md`

## Closing the EPIC

When Phase C ships, EPIC #164 v1 is complete: foundation + priming + synthesis. Phase D (RemoteAgentSource) becomes a separate future EPIC.

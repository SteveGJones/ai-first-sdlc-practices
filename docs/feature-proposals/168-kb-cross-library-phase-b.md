# Feature Proposal: Cross-Library KB Query — Phase B Priming

**Proposal Number:** 168
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-24
**Target Branch:** `feature/164-cross-library-kb-query` (continues from Phase A)
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-feature:** #168 (sub-2 of 3 in v1)

## Summary

Activate the priming bundle scaffolded in Phase A. The local project's CLAUDE.md `[Knowledge Base]` section and shelf-index terms now actively bias external librarian queries — files whose vocabulary overlaps with the local project's terms rank higher; the KB config excerpt names the lens under which findings are interpreted.

## Motivation

See EPIC #164 body and design spec §3.3 (priming as a key architectural property), §6.1 step 2 (data flow). Phase A built the scaffold (PrimingBundle dataclass, builder, orchestrator pass-through). Phase B is the activation layer — without it, the EPIC's differentiator ("local context frames how global libraries are interrogated") is unrealised.

## Design

Full design in `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`.

Phase B implementation per spec §6.1 step 2 (priming bundle construction) and the librarian's PRIMING_CONTEXT consumption rules in spec §3.3. Adds one helper (`format_dispatch_prompt`), updates the librarian prompt's PRIMING_CONTEXT bullet to active-use semantics, and DRYs the kb-query skill's Step 3 to call the helper instead of inline templating.

## Success Criteria

Per issue #168 acceptance criteria:

- [x] `format_dispatch_prompt` helper renders SCOPE / SOURCE_HANDLE / PRIMING_CONTEXT in the exact shape the librarian agent expects
- [x] Librarian agent prompt has active-use PRIMING_CONTEXT instructions (no more "optional, phase B will activate" caveat)
- [x] kb-query skill Step 3 uses `format_dispatch_prompt` instead of inline templating
- [x] Integration test proves priming bundle flows from `build_priming_bundle` through `run_retrieval_query` to every dispatcher invocation
- [x] All Phase A tests still pass; `check-plugin-packaging.py` reports 12 plugins verified
- [ ] `python tools/validation/local-validation.py --pre-push` passes (verified in Task 7)

## Out of scope (phase B)

- Cross-library synthesis (phase C, #169)
- RemoteAgentSource (deferred EPIC)
- E2E tests with real librarian dispatch (deferred — they exist in spec §8.3 but require live agent runs)
- Tuning the librarian's biasing heuristics based on real usage data (a future hardening pass)

## Dependencies

- Blocked by: #167 (Phase A) — **complete** as of 2026-04-24

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-b.md`

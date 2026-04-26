# Feature Proposal: Cross-Library KB Query — Phase D Operational Maturity

**Proposal Number:** 170 (umbrella for sub-features #170-#176)
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-26
**Target Branch:** `feature/164-cross-library-kb-query` (continues from Phases A+B+C)
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-features:** #170-#176 (the 7 Phase D sub-features)

## Summary

Operational maturity layer for EPIC #164 v1. Turns "matches the spec" into "consulting team can rely on this for client engagements." Surfaced by the multi-reviewer assessment after Phases A+B+C identified gaps that turn the v1 from "works" into "trustworthy for real use": no proof priming actually changes behaviour, no audit trail for confidentiality events, no path for local findings to compound into corporate libraries, no transparency about why the librarian picked the files it picked, no onboarding workflow, no mechanism for libraries to evolve safely.

## Sub-features

| # | Title | Status |
|---|---|---|
| #170 (sub-4) | Code quality + security cleanup | Done |
| #171 (sub-5) | Validate priming actually works (HARD GATE) | Done — PASS |
| #172 (sub-6) | Audit log of confidentiality events | Done |
| #173 (sub-7) | Librarian transparency in retrieval AND synthesis output | Done |
| #174 (sub-8) | Local→corporate finding promotion path | Done |
| #175 (sub-9) | Library evolution mechanism (richer header + staleness) | Done |
| #176 (sub-10) | Onboarding skill — consulting practice setup | Done |

## Motivation

See EPIC #164 body. The five-reviewer assessment after Phases A+B+C concluded that the architecture was sound and the §7.1 confidentiality invariant was structurally enforced — but the operational layer needed to make this useful for real consulting engagements was not yet built. Steve explicitly noted: "I was reviewing for 'ships without breaking' — pre-commit hooks, spec-text-to-code matching, easy-to-fix gaps. That's not the same as 'high quality for a team that lives in this system every day.'"

The Phase D commitment was to do this work BEFORE merging EPIC #164. Larger PR, fuller delivery.

## Proposed Solution

Plan: `docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-d-operational-maturity.md`

Each sub-feature has its own plan-level task block with verbatim implementation, tests, and commit guidance. The plan opens with the Phase A regression lesson (edit root sources first, mirror to plugin-dir, verify with check-plugin-packaging.py before commit) — Phase D adheres to this for every plugin-file edit.

## Success Criteria

- [x] Phase A-C tests still pass (97 → still passing after Phase D additions)
- [x] black + flake8 clean (regression closed by Task 1)
- [x] Library `name` charset validated; library `path` validated with denylist
- [x] `valid_handles` parameter required in synthesis attribution check
- [x] synthesis-librarian is a separate agent with `tools: []` (structural "no file reads")
- [x] Skill bash snippets resolve sys.path via CLAUDE_PLUGIN_ROOT
- [x] Priming demonstrably changes file selection (HARD GATE PASS, 2 of 3 queries)
- [x] Audit module (AuditEvent + log_event + read_log) with 8 tests
- [x] Orchestrator instrumented for 4 confidentiality event types
- [x] kb-audit-query skill for filtering audit log
- [x] Retrieval Selection rationale + synthesis priming-influence Caveats verified on 5 queries
- [x] kb-promote-answer-to-library `--target` for cross-library promotion
- [x] Cross-library promotion writes `cross_library_promotion` audit event
- [x] Shelf-index header is 4-field (format_version, last_rebuilt, library_handle, library_description)
- [x] Query-time staleness caveat for sources older than threshold
- [x] kb-setup-consulting skill (covers --verify-only / kb-verify functionality)
- [ ] `python tools/validation/local-validation.py --pre-push` passes (verified in Task 25)

## Out of scope (Phase D)

- Cross-library contradiction detection (kb-lint --cross-library) — future EPIC
- Coverage queries (kb-coverage) — future EPIC
- Sophisticated per-finding staleness analysis — future EPIC
- RemoteAgentSource (originally "Phase D" before reframing) — separate future EPIC
- LibrarySource shape ADR + refactor for Phase D's needs — to be addressed when RemoteAgentSource is implemented

## Dependencies

- Blocked by: #167 (Phase A), #168 (Phase B), #169 (Phase C) — all complete

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-d-operational-maturity.md`

## Closing the EPIC

When Phase D ships, EPIC #164 v1 is feature-complete: foundation + priming + synthesis + operational maturity. Phase E (RemoteAgentSource as originally framed) becomes a separate future EPIC.

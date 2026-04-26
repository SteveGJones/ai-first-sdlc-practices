# Feature Proposal: Cross-Library KB Query — Phase A Foundation

**Proposal Number:** 167
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-24
**Target Branch:** `feature/164-cross-library-kb-query`
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-feature:** #167 (sub-1 of 3 in v1)

## Summary

Foundation layer for cross-library knowledge base query. Delivers the LibrarySource abstraction, user-scope + project-scope library registries, FilesystemSource dispatcher, `kb-query` orchestration with parallel librarian dispatch, and mandatory source attribution. Does not include priming (phase B, #168) or cross-library synthesis (phase C, #169).

## Motivation

See EPIC #164 body and design spec §1 (Context). Amkor AI Strategy engagement feedback (2026-04-23) identified that the research-librarian cannot query prior engagement libraries. Corporate asset libraries, reusable across engagements, need a registration + activation model and multi-source dispatch.

## Proposed Solution

Full design in `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md` (branch `feature/164-cross-library-kb-query`, commit 9ca9de5).

Seven design questions resolved during brainstorming (listed in spec §2). Phase A implements the foundation layer per spec §4 (Components), §5 (Configuration schemas), §6.1 (Retrieval data flow), and §7 (Error handling).

## Success Criteria

Per issue #167 acceptance criteria:

- [x] Plugin has importable Python scripts package (mirrors sdlc-workflows pattern)
- [x] `~/.sdlc/global-libraries.json` schema + loader with graceful degradation
- [x] `.sdlc/libraries.json` schema + loader with graceful degradation
- [x] Activation resolution prepends implicit local source, skips unknowns and remote-agent types with warnings
- [x] Priming bundle scaffold (used actively in phase B)
- [x] Attribution post-check enforces source library tags structurally
- [x] `format_version: 1` breadcrumb emitted by kb-rebuild-indexes
- [x] research-librarian prompt extended for SCOPE, PRIMING_CONTEXT, SOURCE_HANDLE
- [x] kb-register-library skill registers new entries in the user-scope registry
- [x] kb-query orchestration dispatches librarians in parallel, collects, post-checks, and renders
- [x] kb-init CLAUDE.md template documents external-library registration and activation
- [x] Unit test coverage: registry, priming, attribution, format_version, orchestrator (mock dispatcher)
- [ ] `check-plugin-packaging.py` passes after release-mapping update (verified in Task 14)
- [ ] `python tools/validation/local-validation.py --pre-push` passes (verified in Task 17)

## Out of scope (phase A)

- Active use of priming bundle by librarians (phase B, #168)
- Cross-library synthesis (phase C, #169)
- RemoteAgentSource (deferred EPIC)
- Cross-library ingest, lint, staleness-check, citation validation
- Registry corruption auto-recovery
- `kb-deregister-library`, `kb-list-libraries` helpers

## Dependencies

- None at phase A level.

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-a.md`

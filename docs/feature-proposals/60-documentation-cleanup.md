# Feature Proposal: Documentation Cleanup and Reorganisation

**Branch**: feature/documentation-review
**Target Branch:** `main`

## Motivation

A full-team documentation review (4 specialist agents) identified severe documentation debt from multiple framework paradigm shifts (V2 to V3, Billy Wright coaching addition, agent expansion from 27 to 65). The repository had 45 root-level .md files (should be ~25), 65 unorganised files in docs/, ~200 KB of contradictory instruction files loaded per session, 5 references to non-existent scripts, and 13 contradictory entry points for new users.

## Proposed Solution

1. Create `docs/archive/` structure with subdirectories for meeting-notes, historical-records, vision-documents
2. Delete 3 session artifacts (REBOOT-CONTEXT, CONTINUATION-CONTEXT, GIT_OPERATIONS_MANUAL)
3. Archive 32 files from root and docs/ to docs/archive/ (preserving git history via git mv)
4. Delete 2 redundant team-first enforcement files (keeping 1 canonical version)
5. Gut CLAUDE.md from 856 lines to 10-line redirect to CLAUDE-CORE.md
6. Update docs/README.md links to point to archived file locations
7. Remove non-existent script references from SDLC-RULES-SUMMARY.md
8. Remove archived file from setup-smart.py ESSENTIAL_FILES list
9. Delete orphaned feature proposal stub (20250809-project-kickoff.md)

## Success Criteria

- Root .md files reduced from 45 to ~25
- docs/ top-level files reduced from 65 to ~48
- Zero references to non-existent scripts
- CLAUDE.md no longer contains contradictory 856-line instruction set
- All archived files accessible at docs/archive/ with git history preserved
- All CI checks pass (CLAUDE.md still exists for CI compatibility)

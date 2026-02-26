# Feature Proposal: Fix Broken File References

**Proposal Number:** 68
**Status:** Complete
**Author:** Claude (AI Agent)
**Created:** 2026-02-10
**Target Branch:** `feature/fix-broken-references`

---

## Executive Summary

Fix all broken file references found by `check-broken-references.py` (106 initial, 72 after Phase 1-5 doc fixes), and improve the checker to eliminate false positives, reaching zero broken references.

---

## Motivation

### Problem Statement

Feature #67 created `check-broken-references.py` which found 106 broken references across 31 files. These included genuinely broken doc links, incomplete file paths, references to deleted files, and false positives from template/runtime content.

### User Stories

- As a developer clicking doc links, I want every link to resolve to an existing file
- As a maintainer running validation, I want the checker to report zero false positives

---

## Proposed Solution

1. Fix `docs/README.md` — remove 13 broken links to never-created documentation
2. Fix `docs/FRESH-AI-TO-LEGENDARY-TEAM-SYSTEM.md` — remove references to nonexistent coaching scripts
3. Fix `docs/FRESH-AI-ONBOARDING.md` — remove broken anchor references
4. Fix `docs/HARSH-ENFORCEMENT-IMPLEMENTATION.md` — update deleted SDLC-RULES-SUMMARY.md reference to CONSTITUTION.md
5. Fix `docs/A2A-SYSTEM-SUMMARY.md` — update path to archived tactical discussion
6. Fix `agents/core/agent-builder.md` and `docs/AGENT-CREATION-GUIDE.md` — add full `templates/reference-agents/` prefix to archetype references
7. Fix `CONTRIBUTING.md` and `docs/FRAMEWORK-COMPLIANCE-POLICY.md` — remove references to nonexistent files
8. Improve `check-broken-references.py` — strip anchor fragments, exclude setup-smart.py and .github/coaching/, add SDLC level filenames, add .sdlc/.claude/ path exclusions

### Acceptance Criteria

Given 106 broken references initially reported
When all fixes and checker improvements are applied
Then the checker reports zero broken references

Given the checker produces false positives for user-project files
When SDLC level filenames and runtime paths are excluded
Then only genuinely broken references are reported

---

## Success Criteria

- [x] `check-broken-references.py` reports zero broken references
- [x] All Python files compile (`local-validation.py --syntax` passes)
- [x] `docs/README.md` has no dead links
- [x] Reference agent paths include full `templates/reference-agents/` prefix
- [x] SDLC-RULES-SUMMARY.md references updated to CONSTITUTION.md

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-excluding may hide real breaks | Medium | Exclusions are narrow and well-categorized |
| Anchor-stripping may hide broken anchors | Low | Anchor validation is a separate concern |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `docs/README.md` |
| Modify | `docs/FRESH-AI-TO-LEGENDARY-TEAM-SYSTEM.md` |
| Modify | `docs/FRESH-AI-ONBOARDING.md` |
| Modify | `docs/HARSH-ENFORCEMENT-IMPLEMENTATION.md` |
| Modify | `docs/A2A-SYSTEM-SUMMARY.md` |
| Modify | `agents/core/agent-builder.md` |
| Modify | `docs/AGENT-CREATION-GUIDE.md` |
| Modify | `CONTRIBUTING.md` |
| Modify | `docs/FRAMEWORK-COMPLIANCE-POLICY.md` |
| Modify | `tools/validation/check-broken-references.py` |

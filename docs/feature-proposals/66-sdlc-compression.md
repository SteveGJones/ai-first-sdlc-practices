# Feature Proposal: SDLC Compression & Spec-Kit Inspired Revision

**Proposal Number:** 66
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-02-10
**Target Branch:** `feature/sdlc-compression`
**Implementation Type:** Documentation|Process|Infrastructure

---

## Executive Summary

Compress the AI-First SDLC framework by consolidating 37 scattered rules into a single CONSTITUTION.md, removing all enforcement rhetoric, compressing CLAUDE-CORE.md by 54%, and adding spec-kit patterns (Given/When/Then, [P] markers, lite templates). Inspired by GitHub's spec-kit methodology.

---

## Motivation

### Problem Statement

- Rules are scattered across 4 files (911 lines) with 17% enforcement rhetoric
- CLAUDE-CORE.md contains 16 "DEATH PENALTY" mentions that add zero value
- SDLC-RULES-SUMMARY.md is 90% redundant with CLAUDE-CORE.md
- Templates are enterprise-heavy (888 lines total) for a framework used mainly by small teams
- 23 validation scripts with ~30% redundancy
- 11 CI workflows with overlapping validation jobs

### User Stories

- As a developer adopting the SDLC, I want to find all rules in one place so I don't miss scattered requirements
- As a small team, I want lightweight templates so I don't spend more time on process than on code
- As a CI maintainer, I want consolidated workflows so failures are easier to diagnose

---

## Proposed Solution

### High-Level Approach

1. Create CONSTITUTION.md as single rules source with numbered articles and level annotations
2. Compress CLAUDE-CORE.md by removing rhetoric and pointing at CONSTITUTION.md
3. Add spec-kit patterns to templates and create lite variants
4. Merge redundant validation scripts (23 to 17)
5. Merge overlapping CI workflows (11 to 8)

### Acceptance Criteria

Given the current CLAUDE-CORE.md has 328 lines
When Phase 2 is complete
Then CLAUDE-CORE.md has fewer than 160 lines with zero "DEATH PENALTY" mentions

Given rules are in 4 separate files
When CONSTITUTION.md is created
Then all rules exist in a single numbered document under 160 lines

Given templates total 888 lines
When templates are compressed
Then standard templates total under 350 lines and lite variants exist under 50 lines each

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CI breaks from deleted scripts | High | Update all references before deleting; test with --syntax |
| Rules lost during consolidation | Medium | Cross-check all 37 rules against CONSTITUTION.md |
| Users referencing old files | Low | Grep for all deleted filenames; update docs |

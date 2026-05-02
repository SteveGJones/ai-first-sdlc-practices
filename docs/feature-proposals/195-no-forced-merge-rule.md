# Feature Proposal: No-Forced-Merge Rule

**Proposal Number:** 195
**Status:** Complete
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-05-02
**Target Branch:** `fix/195-no-forced-merge-rule`
**Issue:** #195

---

## Problem Statement

The AI-First SDLC git workflow rules in `CLAUDE.md` were silent on the use of `--admin`, `--force`, and other branch-protection bypass flags. During session 2026-05-02, both a direct push to main and a `--admin` merge bypass were executed without user confirmation — neither of which should happen. The incident required a revert and re-apply on a proper fix branch to correct.

## Proposed Solution

Add an explicit prohibition to the Essential Workflow section of `CLAUDE.md`:

- Never use `--admin`, `--force`, or any branch-protection bypass when a merge is blocked.
- When a branch protection rule blocks a merge, report the block and ask the user whether to override.

This makes the rule durable and machine-readable so that future AI agents operating in this repo see it on every context load.

## Implementation Plan

- [x] Add no-forced-merge rule to `CLAUDE.md` Essential Workflow section

## Acceptance Criteria

- [x] `CLAUDE.md` contains the no-forced-merge prohibition
- [x] Rule is in the Essential Workflow section (loaded every session)

## Out of Scope

- No changes to validators, CI, or Constitution (the behavioural rule lives in CLAUDE.md as an immediate operational constraint; a Constitution article is a separate concern)

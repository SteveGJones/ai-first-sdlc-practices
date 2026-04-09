# Feature Proposal: Enable Model Invocation on SDLC Skills

**Proposal Number:** 139
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-09
**Target Branch:** `fix/enable-model-invocation`, `fix/enable-commit-model-invocation`
**Issue:** #139
**Type:** Enhancement

---

## Executive Summary

Flip `disable-model-invocation` from `true` to `false` on 13 of 15 SDLC framework skills so Claude can auto-invoke them in the natural flow of work.

---

## Motivation

All 15 SDLC skills have `disable-model-invocation: true`, meaning Claude cannot auto-invoke any of them — users must type the slash command explicitly for every workflow step. This undermines the framework's value proposition: the whole point of skills is that models invoke them proactively.

The highest-impact case is `kb-query`: with the flag true, every user research question gets answered from Claude's training data (possibly hallucinating) unless the user remembers to type `/sdlc-knowledge-base:kb-query`. With the flag false, Claude auto-queries the library when a research question matches — the library's "grounded in evidence" value is delivered automatically.

Similar for `validate` (should auto-run after edits per CLAUDE.md workflow), `new-feature` (should enforce "create proposal before coding"), and `setup-team` (should auto-invoke when a user is clearly configuring a new project).

The previous rationale for keeping the flag true ("these skills take real actions") didn't hold up to examination: almost all of them are either read-only or additive-idempotent. Only `commit` (git commit) and `pr` (remote PR creation) have real destructive consequences and should stay explicit.

---

## Proposed Solution

Flip `disable-model-invocation` from `true` to `false` on 13 source skill files and their 13 plugin copies. Keep `commit` and `pr` as `true`. Pure frontmatter change — one line per file.

---

## Success Criteria

- [ ] 13 source skill files have `disable-model-invocation: false`
- [ ] 13 plugin copies match the source
- [ ] `commit` and `pr` retain `disable-model-invocation: true`
- [ ] `python3 tools/validation/check-plugin-packaging.py` passes
- [ ] CI passes

---

## Changes Made

| Action | File |
|--------|------|
| Modify | 14 source skill files under `skills/` (one line each — 13 in PR #140 + `commit` in follow-up PR) |
| Modify | 14 plugin copy files under `plugins/sdlc-core/skills/` and `plugins/sdlc-knowledge-base/skills/` |
| Create | `docs/feature-proposals/139-enable-model-invocation.md` (this file) |

**Note:** The initial PR (#140) flipped 13 skills but kept `commit` as explicit-only. Steve challenged this: "a commit is a local checkpoint, not a publication — it doesn't overwrite anything, it just means better history." He was right. A follow-up PR flips `commit` to `false` as well. Only `pr` remains `disable-model-invocation: true`.

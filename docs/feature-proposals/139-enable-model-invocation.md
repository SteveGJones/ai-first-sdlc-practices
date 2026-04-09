# Feature Proposal: Enable Model Invocation on SDLC Skills

**Proposal Number:** 139
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-09
**Target Branch:** `fix/enable-model-invocation`
**Issue:** #139
**Type:** Enhancement

---

## Executive Summary

Flip `disable-model-invocation` from `true` to `false` on 13 of 15 SDLC framework skills. The whole point of skills is that models invoke them proactively in the natural flow of work. With the flag true on every skill, Claude cannot auto-invoke any of them and users must remember to type the slash command for every workflow step. This undermines the framework's value proposition — particularly for `kb-query`, where auto-invocation means the library's "grounded in evidence" value is delivered automatically rather than requiring the user to type `/sdlc-knowledge-base:kb-query` every time.

Keep `commit` and `pr` as explicit-only because they create git commits and remote PRs — real actions visible to others that should always be explicit user intent. All other skills are either read-only or additive-idempotent and safe for model invocation.

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
| Modify | 13 source skill files under `skills/` (one line each) |
| Modify | 13 plugin copy files under `plugins/sdlc-core/skills/` and `plugins/sdlc-knowledge-base/skills/` |
| Create | `docs/feature-proposals/139-enable-model-invocation.md` (this file) |

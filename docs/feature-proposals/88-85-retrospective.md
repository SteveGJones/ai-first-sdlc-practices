# Feature Proposal: Retrospective for #85 Docker Smoke Test

**Proposal Number:** 88
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-06
**Target Branch:** `feature/85-retrospective-and-memory-cleanup`

---

## Executive Summary

Add the missing retrospective for feature #85 (Docker setup smoke test). PR #87 was merged without `retrospectives/85-docker-smoke-test.md`, which is a process violation under the AI-First SDLC framework. This proposal tracks the catch-up work to bring #85 into compliance.

---

## Motivation

### Problem Statement

The AI-First SDLC framework requires every feature to ship with a retrospective in `retrospectives/`. Feature #85 (Docker setup smoke test) was implemented and merged via PR #87 without one. This means:

- Lessons learned during the smoke test build (OAuth in Docker, named volume permissions, Ralph's silent failures, UID collisions in `node:22-slim`) aren't captured anywhere durable
- The "what went well / what could improve" reflection that the framework relies on for continuous improvement is missing
- We're out of compliance with our own process, and the team-progress-tracker has no record of #85's outcomes

### User Stories

- As a future contributor, I want to read the #85 retrospective so I understand the non-obvious blockers and don't repeat them when extending the smoke test
- As a maintainer, I want every shipped feature to have a retrospective so the framework's process integrity holds
- As the AI agent driving this work, I want to record an honest assessment of where I jumped to conclusions (twice — proposing to abandon Ralph and then host bind mounts when the right answer was to follow the standard Docker pattern) so future sessions avoid the same mistake

---

## Proposed Solution

A focused, docs-only PR that:

1. Adds `retrospectives/85-docker-smoke-test.md` following the same structure as recent retrospectives (#71, #70)
2. Documents what went well, what could improve, lessons learned, changes made, metrics, and open follow-up
3. Honestly captures the harder parts of the journey (Docker OAuth, Ralph debugging, premature tool replacement)
4. Cross-references the side-effect PRs (#88 dev environment script, #89 CONTRIBUTING.md) that this work spawned
5. Lists open follow-up that is **explicitly NOT** part of #85 (CI integration, more fixtures, caching, local plugin testing flag)

### Acceptance Criteria

Given a future contributor reading the retrospective
When they look for #85's lessons
Then they find the seven Docker/Ralph blockers documented with fixes
And they understand which open work is in scope for new issues, not for #85

---

## Success Criteria

- [ ] `retrospectives/85-docker-smoke-test.md` exists and follows the framework template
- [ ] All seven blockers from `tests/integration/setup-smoke/README.md` "Lessons Learned" section are referenced
- [ ] Metrics match the actual last run (1 iteration, 348s, 10/10 PASS, 14 plugins)
- [ ] Open follow-up clearly marked as out of scope for #85
- [ ] PR passes SDLC compliance check (this proposal exists, retrospective exists)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Retrospective drifts from what was actually built | Misleading future debugging | Cross-reference the README's "Lessons Learned" section verbatim |
| Future-tense items get marked as in scope for #85 | Scope creep on a closed issue | Explicit "Open Follow-Up" section flagging items as NOT part of #85 |

---

## Changes Made

| Action | File |
|--------|------|
| Create | `retrospectives/85-docker-smoke-test.md` |
| Create | `docs/feature-proposals/88-85-retrospective.md` |

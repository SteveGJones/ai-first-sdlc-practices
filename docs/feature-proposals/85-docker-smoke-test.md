# Feature Proposal: Docker Setup Smoke Test

**Proposal Number:** 85
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-06
**Target Branch:** `feature/docker-smoke-test`

---

## Executive Summary

Docker-based smoke test for the SDLC plugin ecosystem. Verifies plugin installation from GitHub, setup-team tech detection and discovery, tool installation, and output file correctness in a clean, reproducible environment using Claude Code Max subscription.

---

## Motivation

### Problem Statement

No fast way to verify plugin installation and setup-team work correctly after changes. The full integration test takes 45-60 minutes. We need a ~5-10 minute test in a reproducible Docker environment that proves the setup flow works end-to-end.

### User Stories

- As a framework developer, I want to verify my plugin changes work in a clean environment
- As a framework developer, I want a fast test that catches setup regressions

---

## Proposed Solution

Docker image with Claude Code + Ralph + Python + git. Mounts host Claude Code Max credentials at runtime. Installs plugins from public GitHub, runs setup-team on EventFlow fixture, installs recommended tools, verifies outputs with 10-point checklist.

### Acceptance Criteria

Given a built Docker image and authenticated host
When `./run.sh` is executed
Then all 10 verification checks pass

---

## Success Criteria

- [ ] Docker image builds from Dockerfile
- [ ] Plugins install from public GitHub marketplace
- [ ] Setup-team detects EventFlow tech stack
- [ ] Recommended tools install successfully
- [ ] Output files pass 10-point verification

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Claude Code Max session expires | Test fails on auth | Re-authenticate on host, re-run |
| npm package names change | Tool install fails | Test reports specific failures, easy to update |
| Docker image grows too large | Slow initial build | Cached base image, rebuild only on dep changes |

---

## Changes Made

| Action | File |
|--------|------|
| Create | `tests/integration/setup-smoke/Dockerfile` |
| Create | `tests/integration/setup-smoke/build.sh` |
| Create | `tests/integration/setup-smoke/run.sh` |
| Create | `tests/integration/setup-smoke/entrypoint.sh` |
| Create | `tests/integration/setup-smoke/PROMPT.md` |
| Create | `tests/integration/setup-smoke/ralph.yml` |
| Create | `tests/integration/setup-smoke/fixtures/eventflow/README.md` |
| Create | `tests/integration/setup-smoke/README.md` |

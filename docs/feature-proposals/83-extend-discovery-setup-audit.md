# Feature Proposal: Extend Discovery to Project Setup and Audit

**Proposal Number:** 83
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-05
**Target Branch:** `feature/extend-discovery-setup-audit`

---

## Executive Summary

Extend 1st-party tool discovery (#82) to three additional contexts: project setup (setup-team skill), existing agent audit, and project plugin library.

---

## Motivation

### Problem Statement

The setup-team skill recommends SDLC plugins but doesn't search for official vendor tooling. Users miss MCP servers, agent skills, and other tools that their tech stack has available. The existing agent base was built without discovery and may have official alternatives.

### User Stories

- As a developer, I want setup to recommend PostgreSQL's MCP server alongside the SDLC plugins
- As a framework maintainer, I want to audit existing agents for official alternatives
- As a team, I want a project-level list of all recommended tools

---

## Proposed Solution

Three parts, implemented sequentially on one branch:
1. Setup-team discovery — scan tech stack, discover tools, three-section recommendation
2. Agent base audit — search for alternatives to existing agents
3. Plugin library — `.sdlc/recommended-plugins.json`

### Acceptance Criteria

Given a project using PostgreSQL and Redis
When `/sdlc-core:setup-team` is run
Then the recommendation includes both SDLC plugins and official vendor tools in separate sections

---

## Success Criteria

- [ ] Setup-team scans tech stack and presents three-section recommendation
- [ ] Existing agents audited for 1st-party alternatives
- [ ] Plugin library file maintained per project

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Discovery adds latency to setup | Slower first-run experience | Cache results, skip if user presses Enter |
| Official tools found are abandoned | User installs non-maintained tooling | Check last activity date in discovery |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` |
| Sync | `skills/setup-team/SKILL.md` |
| Create | `docs/superpowers/specs/2026-04-05-setup-team-discovery-design.md` |
| Create | `docs/superpowers/plans/2026-04-05-setup-team-discovery.md` |

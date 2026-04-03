# Feature Proposal: Plugin Migration Phase 1

**Proposal Number:** 70
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-03
**Target Branch:** `feature/plugin-migration`

---

## Executive Summary

Package the AI-First SDLC framework as a Claude Code plugin family. Phase 1 delivers the core plugin (`sdlc-core`) with skills, agents, hooks, and a marketplace for distributing team-specific plugins.

---

## Motivation

### Problem Statement

The framework (63 agents, 18 validators, 42 automation tools) is distributed by cloning a repo and reading documentation. This requires manual setup and has no versioning, team distribution, or namespace isolation. Claude Code now supports plugins — the framework should use them.

### User Stories

- As a team lead, I want one-command installation so new team members can onboard instantly
- As a developer, I want `/sdlc-core:validate` instead of memorizing `python tools/validation/local-validation.py --pre-push`
- As a framework maintainer, I want versioned releases so teams get stable, tested updates

---

## Proposed Solution

1. Create a plugin family: `sdlc-core` + team plugins + language plugins
2. Build a source-to-release pipeline: develop in `tools/`/`agents/`/`skills/`, package into `plugins/` via `release-mapping.yaml`
3. Create 7 skills wrapping core workflows (validate, new-feature, commit, pr, rules, setup-team, release-plugin)
4. Ship 3 gateway agents with core (sdlc-enforcer, critical-goal-reviewer, code-review-specialist)
5. Add hooks for session startup and post-edit validation
6. Create stub plugins for 4 team types + 2 languages
7. Build marketplace for distribution

### Acceptance Criteria

- Plugin installs via `/plugin marketplace add` + `/plugin install sdlc-core`
- All 7 skills invoke correctly
- 3 agents discoverable via plugin
- Hooks fire on session start and post-edit
- Stub team plugins installable
- Existing `tools/` workflow unchanged

---

## Success Criteria

- [ ] `sdlc-core` plugin installs and works
- [ ] All skills invoke via `/sdlc-core:<name>`
- [ ] Agents are discoverable
- [ ] Hooks fire correctly
- [ ] Setup-team recommends and records team plugins
- [ ] Release-plugin packages source into plugins
- [ ] Existing tooling continues working

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Plugin system behavior differences | Medium | Test each skill individually after packaging |
| Agent frontmatter compatibility | Low | Agents already use YAML frontmatter matching plugin format |
| Hook timing issues | Low | Test SessionStart and PostToolUse independently |

---

## Changes Made

| Action | File |
|--------|------|
| Create | `plugins/` directory structure (marketplace + 7 plugins) |
| Create | `skills/` directory (7 skill source files) |
| Create | `release-mapping.yaml` |
| Modify | `CLAUDE.md` (add plugin install instructions) |

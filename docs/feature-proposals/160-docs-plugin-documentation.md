# Feature Proposal: Public-Facing Plugin Documentation Spike

**Proposal Number:** 160
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-21
**Target Branch:** `feature/docs-plugin-documentation`

---

## Executive Summary

Comprehensive update of all public-facing documentation to reflect the current plugin ecosystem. The README.md was incomplete (listed 10 of 12 plugins, 7 of 22 skills), 10 of 12 plugins shipped without READMEs, and the primary user guides (HOWTO.md, QUICK-REFERENCE.md) described a superseded pre-plugin workflow. Scope expanded from the initial 11/16 target after EPIC #96 (sdlc-workflows) merged to main during branch creation.

---

## Motivation

### Problem Statement

A documentation audit found 38 gaps across the public-facing docs. New users encounter four competing getting-started paths, only one of which is current. Plugin consumers cannot discover what agents or skills a plugin provides without reading raw .md source files. The two most-linked user guides (HOWTO.md, QUICK-REFERENCE.md) reference incorrect tool paths and a legacy workflow.

### User Stories

- As a new user, I want the README to list all available plugins and skills so I can evaluate the framework
- As a plugin consumer, I want each plugin to have a README so I can understand what agents it provides and when to use them
- As an existing user, I want the HOWTO and QUICK-REFERENCE to describe the current plugin/skill workflow
- As a potential contributor, I want clear prerequisites and a consumer guide so I can get started

---

## Proposed Solution

1. **Update README.md** — Add sdlc-knowledge-base and sdlc-workflows to plugin table, add all 22 skills, fix agent count (56), add prerequisites section, add per-plugin agent counts, link CHANGELOG.md
2. **Write 10 plugin READMEs** — Model on sdlc-knowledge-base README (agent table, skill table, usage, when to use). sdlc-knowledge-base and sdlc-workflows already had READMEs.
3. **Rewrite docs/HOWTO.md** — Replace legacy setup-smart.py workflow with plugin/skill-based workflow
4. **Rewrite docs/QUICK-REFERENCE.md** — Fix tool paths, add slash command equivalents
5. **Write Plugin Consumer Guide** — New doc: how agents/skills/validation work for end users
6. **Archive legacy docs** — Move START-HERE.md, quick-start.md, Billy Wright docs to docs/archive/
7. **Regenerate AGENT-INDEX.md** — From current source + plugin structure, with explanatory note on 128 source vs 56 published agents
8. **Fix CLAUDE.md** — Update EPIC #96 to merged, correct plugin/agent counts, add rules skill

### Acceptance Criteria

Given the documentation spike is complete
When a new user reads the README and plugin docs
Then they can discover all 12 plugins, 56 agents, and 22 skills without reading source files

---

## Success Criteria

- [ ] README.md lists all 12 plugins with accurate agent counts
- [ ] README.md lists all 22 skills across sdlc-core, sdlc-knowledge-base, and sdlc-workflows
- [ ] All 12 plugins have a README.md with agent/skill tables
- [ ] HOWTO.md describes the plugin/skill workflow (no legacy references)
- [ ] QUICK-REFERENCE.md has correct paths and slash command equivalents
- [ ] Plugin Consumer Guide exists and covers installation through daily use
- [ ] Legacy docs archived with deprecation notices
- [ ] AGENT-INDEX.md regenerated from plugin structure
- [ ] Syntax validation passes

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Docs drift from code again | Medium | Add doc-freshness check to PR review checklist |
| Archive breaks external links | Low | Add redirect notices in archived files |
| Large diff obscures review | Medium | Logical commits per task area |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `README.md` |
| Create | `plugins/sdlc-core/README.md` |
| Create | `plugins/sdlc-lang-javascript/README.md` |
| Create | `plugins/sdlc-lang-python/README.md` |
| Create | `plugins/sdlc-team-ai/README.md` |
| Create | `plugins/sdlc-team-cloud/README.md` |
| Create | `plugins/sdlc-team-common/README.md` |
| Create | `plugins/sdlc-team-docs/README.md` |
| Create | `plugins/sdlc-team-fullstack/README.md` |
| Create | `plugins/sdlc-team-pm/README.md` |
| Create | `plugins/sdlc-team-security/README.md` |
| Modify | `docs/HOWTO.md` |
| Modify | `docs/QUICK-REFERENCE.md` |
| Create | `docs/PLUGIN-CONSUMER-GUIDE.md` |
| Move | `docs/START-HERE.md` -> `docs/archive/` |
| Move | `docs/quick-start.md` -> `docs/archive/` |
| Move | Legacy Billy Wright docs -> `docs/archive/` |
| Modify | `AGENT-INDEX.md` |
| Modify | `CLAUDE.md` |

# Feature Proposal: Team Plugin Population (Phase 2)

**Proposal Number:** 71
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-03
**Target Branch:** `feature/team-plugin-population`

---

## Executive Summary

Populate all team plugins with production agents, normalize agent frontmatter to Claude Code plugin schema, and release v1.0.0 of the plugin family.

---

## Motivation

### Problem Statement

Phase 1 created the plugin family with stub team plugins. Teams can install but get no specialist agents. 52 production agents exist in source but aren't distributed through the plugin system.

### User Stories

- As a developer, I want to install sdlc-team-ai and immediately get AI specialist agents
- As a team lead, I want setup-team to show which agents each plugin provides
- As a framework maintainer, I want all agents normalized to a consistent format

---

## Proposed Solution

1. Create 3 new plugins: sdlc-team-common, sdlc-team-pm, sdlc-team-docs
2. Normalize all 52 agent files to Claude Code plugin schema
3. Extend release-mapping.yaml with all agent-to-plugin mappings
4. Copy agents into plugin directories
5. Update setup-team skill with agent rosters
6. Bump all versions to 1.0.0

### Acceptance Criteria

- All 10 plugins contain their assigned agents
- All agent frontmatter normalized
- setup-team shows agent rosters per plugin
- All plugins at v1.0.0

---

## Success Criteria

- All 10 plugins contain their assigned agents (verified by file listing)
- All 52 agent frontmatter fields normalized to Claude Code plugin schema
- setup-team skill shows agent rosters with counts per plugin
- All plugins bumped to v1.0.0
- Agent Template Compliance Check passes (all agents have required fields)
- Plugin marketplace.json updated with all 10 plugins

---

## Changes Made

| Action | File |
|--------|------|
| Create | plugins/sdlc-team-common/, plugins/sdlc-team-pm/, plugins/sdlc-team-docs/ |
| Create | tools/automation/normalize-agent-frontmatter.py |
| Modify | 52 agent files (frontmatter normalization) |
| Modify | release-mapping.yaml (all agent mappings) |
| Modify | skills/setup-team/SKILL.md (rosters, common/pm/docs) |
| Modify | plugins/.claude-plugin/marketplace.json (versions, new plugins) |

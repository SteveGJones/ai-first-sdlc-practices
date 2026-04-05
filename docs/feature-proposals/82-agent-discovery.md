# Feature Proposal: 1st-Party Agent Discovery

**Proposal Number:** 82
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-05
**Target Branch:** `feature/agent-discovery`

---

## Executive Summary

Add a discovery phase to the agent creation pipeline that searches for official vendor tooling (MCP servers, agent skills, Claude plugins, GitHub Actions) before building custom agents from scratch.

---

## Motivation

### Problem Statement

The agent creation pipeline always builds domain agents from scratch via research + construction. It doesn't check whether the vendor already publishes official tooling — for example, MongoDB has both an official MCP server and agent skills at github.com/mongodb/agent-skills. A vendor-maintained tool with direct system access will always outperform a generated agent built from documentation.

### User Stories

- As a developer, I want the pipeline to find official MongoDB tools so I don't build an inferior custom agent
- As a developer, I want to choose between using official tools as-is, building a hybrid, or building custom
- As a developer, I want discovery results cached so future runs don't re-search

---

## Proposed Solution

1. New Phase 0 (Discovery) in pipeline-orchestrator — searches 4 registries + web before routing to build
2. Agent-builder adds `first_party_alternatives` metadata when official tools exist
3. User chooses: use-as-is, hybrid (complement official tools), or build custom

### Acceptance Criteria

Given the pipeline receives a request for a domain agent
When official vendor tooling exists for that domain
Then the pipeline presents the findings before building

---

## Success Criteria

- [ ] Pipeline-orchestrator has Phase 0 with 4 registry sources
- [ ] Agent-builder supports first_party_alternatives frontmatter
- [ ] Discovery results cached in project memory
- [ ] User can skip discovery with explicit flag

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Web search finds outdated or abandoned tools | User installs non-maintained tooling | Check "last activity" date in discovery report |
| Discovery adds latency to every pipeline run | Slower agent creation | Cache results in memory, skip on re-run |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `agents/core/pipeline-orchestrator.md` |
| Modify | `agents/core/agent-builder.md` |
| Sync | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` |
| Sync | `plugins/sdlc-team-common/agents/agent-builder.md` |
| Create | `docs/superpowers/specs/2026-04-05-agent-discovery-design.md` |
| Create | `docs/superpowers/plans/2026-04-05-agent-discovery.md` |

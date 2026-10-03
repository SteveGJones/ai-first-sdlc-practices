# Team Plugin Population — Design Spec (Phase 2)

**Date**: 2026-04-03
**Status**: Draft
**Feature**: #71
**Branch**: `feature/team-plugin-population`
**Depends on**: Phase 1 (PR #73) merged

## Problem

Phase 1 created the plugin family structure with `sdlc-core` and 6 stub plugins. The stubs have no agents — they're empty shells. 52 production agents sit in `agents/` but aren't distributed through the plugin system. Teams can install plugins but get no specialist agents.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cross-cutting agents | New `sdlc-team-common` plugin | Core stays lean (enforcement only); common is optional when specialist teams cover same capabilities |
| Project management agents | New `sdlc-team-pm` plugin | PM is cross-cutting but distinct from technical common agents; some projects need PM without common architects |
| Documentation agents | New `sdlc-team-docs` plugin | Docs needs vary by project; separate plugin allows targeted install |
| v1.0.0 threshold | All team plugins populated | Complete offering, not partial |
| Non-production agents | Excluded from plugins | Templates, examples, variants stay source-only |
| Frontmatter normalization | Yes, during migration | Standardize to Claude Code plugin agent schema; strip non-standard fields |

## Agent-to-Plugin Mapping

### sdlc-core (3 agents — already done in Phase 1)

| Agent | Source Path |
|-------|------------|
| sdlc-enforcer | agents/core/sdlc-enforcer.md |
| critical-goal-reviewer | agents/core/critical-goal-reviewer.md |
| code-review-specialist | agents/testing/code-review-specialist.md |

### sdlc-team-common (8 agents — new plugin)

| Agent | Source Path |
|-------|------------|
| solution-architect | agents/core/solution-architect.md |
| deep-research-agent | agents/core/deep-research-agent.md |
| performance-engineer | agents/testing/performance-engineer.md |
| observability-specialist | agents/core/observability-specialist.md |
| database-architect | agents/core/database-architect.md |
| agent-builder | agents/core/agent-builder.md |
| pipeline-orchestrator | agents/core/pipeline-orchestrator.md |
| repo-knowledge-distiller | agents/core/repo-knowledge-distiller.md |

### sdlc-team-ai (14 agents)

| Agent | Source Path |
|-------|------------|
| ai-solution-architect | agents/ai-development/ai-solution-architect.md |
| prompt-engineer | agents/ai-development/prompt-engineer.md |
| mcp-server-architect | agents/ai-development/mcp-server-architect.md |
| rag-system-designer | agents/ai-builders/rag-system-designer.md |
| context-engineer | agents/ai-builders/context-engineer.md |
| orchestration-architect | agents/ai-builders/orchestration-architect.md |
| ai-devops-engineer | agents/ai-builders/ai-devops-engineer.md |
| ai-team-transformer | agents/ai-builders/ai-team-transformer.md |
| a2a-architect | agents/ai-development/a2a-architect.md |
| agent-developer | agents/ai-development/agent-developer.md |
| langchain-architect | agents/ai-development/langchain-architect.md |
| mcp-quality-assurance | agents/ai-development/mcp-quality-assurance.md |
| mcp-test-agent | agents/ai-development/mcp-test-agent.md |
| ai-test-engineer | agents/testing/ai-test-engineer.md |

### sdlc-team-fullstack (10 agents)

| Agent | Source Path |
|-------|------------|
| frontend-architect | agents/core/frontend-architect.md |
| backend-architect | agents/core/backend-architect.md |
| api-architect | agents/core/api-architect.md |
| devops-specialist | agents/core/devops-specialist.md |
| ux-ui-architect | agents/core/ux-ui-architect.md |
| mobile-architect | agents/core/mobile-architect.md |
| frontend-security-specialist | agents/core/frontend-security-specialist.md |
| data-architect | agents/core/data-architect.md |
| integration-orchestrator | agents/testing/integration-orchestrator.md |
| github-integration-specialist | agents/core/github-integration-specialist.md |

### sdlc-team-cloud (3 agents)

| Agent | Source Path |
|-------|------------|
| cloud-architect | agents/core/cloud-architect.md |
| container-platform-specialist | agents/core/container-platform-specialist.md |
| sre-specialist | agents/core/sre-specialist.md |

### sdlc-team-security (5 agents)

| Agent | Source Path |
|-------|------------|
| security-architect | agents/core/security-architect.md |
| compliance-auditor | agents/core/compliance-auditor.md |
| compliance-report-generator | agents/core/compliance-report-generator.md |
| enforcement-strategy-advisor | agents/core/enforcement-strategy-advisor.md |
| data-privacy-officer | agents/core/data-privacy-officer.md |

### sdlc-team-pm (5 agents — new plugin)

| Agent | Source Path |
|-------|------------|
| agile-coach | agents/project-management/agile-coach.md |
| delivery-manager | agents/project-management/delivery-manager.md |
| project-plan-tracker | agents/project-management/project-plan-tracker.md |
| team-progress-tracker | agents/project-management/team-progress-tracker.md |
| retrospective-miner | agents/sdlc/retrospective-miner.md |

### sdlc-team-docs (2 agents — new plugin)

| Agent | Source Path |
|-------|------------|
| technical-writer | agents/documentation/technical-writer.md |
| documentation-architect | agents/documentation/documentation-architect.md |

### sdlc-lang-python (1 agent)

| Agent | Source Path |
|-------|------------|
| language-python-expert | agents/sdlc/language-python-expert.md |

### sdlc-lang-javascript (1 agent)

| Agent | Source Path |
|-------|------------|
| language-javascript-expert | agents/sdlc/language-javascript-expert.md |

### Source-only (not shipped in any plugin)

| Agent | Reason |
|-------|--------|
| agent-template.md | Template, not a real agent |
| example-security-architect.md | Example |
| example-python-expert.md | Example |
| v3-setup-orchestrator.md | Experimental variant |
| v3-setup-orchestrator-enhanced.md | Experimental variant |
| v3-setup-orchestrator-no-creation.md | Experimental variant |
| v3-setup-orchestrator-team-first.md | Experimental variant |
| sdlc-setup-specialist.md | Superseded by setup-team skill |
| junior-ai-solution-architect.md | Conflicts with ai-solution-architect (per compositions exclusion rule) |
| sdlc-coach.md | Framework internal |
| sdlc-knowledge-curator.md | Framework internal |
| framework-validator.md | Setup tool |
| project-bootstrapper.md | Setup tool |
| ai-first-kick-starter.md | Setup tool |
| language-go-expert.md | No Go plugin yet |
| test-manager.md | Subsumed by ai-test-engineer and performance-engineer |

**Total: 52 agents across 10 plugins. 16 agents stay source-only.**

## Frontmatter Normalization

### Target Schema (Claude Code plugin agent format)

```yaml
---
name: agent-name
description: Concise description for plugin discovery and Claude auto-matching
model: sonnet
tools: Read, Glob, Grep, Bash
---
```

### Fields to strip (non-standard, ignored by plugin system)

- `color` — visual identifier, not used by plugins
- `maturity` — internal classification, not used by plugins
- `examples` — discovery examples, not used by plugins (description handles matching)

### Fields to add where missing

- `model` — default to `sonnet` if absent
- `tools` — default to `Read, Glob, Grep, Bash` if absent
- `description` — must be present; condense multi-line to single line for plugin discovery

### Normalization rules

1. Keep `name` exactly as-is
2. Condense `description` to a single line (max 250 chars) for plugin skill matching
3. Move any multi-line description content into the agent body (below frontmatter)
4. Set `model: sonnet` if missing
5. Set `tools` to existing value, or `Read, Glob, Grep, Bash` if missing
6. Remove `color`, `maturity`, `examples` fields
7. Preserve all body content below frontmatter unchanged

## Updated setup-team Skill

### New project type recommendations

Update the recommendation table in `skills/setup-team/SKILL.md`:

| Selection | Plugins |
|-----------|---------|
| A. Full-stack | `sdlc-team-common`, `sdlc-team-fullstack` |
| B. AI/ML | `sdlc-team-common`, `sdlc-team-ai`, `sdlc-lang-python` |
| C. Cloud | `sdlc-team-common`, `sdlc-team-cloud` |
| D. API | `sdlc-team-common`, `sdlc-team-fullstack`, `sdlc-team-cloud` |
| E. Security | `sdlc-team-common`, `sdlc-team-security` |
| F. Custom | User picks from list |

### Additional questions after project type

After project type selection, ask:

- "Do you need project management support (sprints, delivery tracking)?" → recommend `sdlc-team-pm`
- "Do you need documentation architecture?" → recommend `sdlc-team-docs`

### Agent roster display

When recommending a plugin, show its agent roster:

```
○ sdlc-team-ai — 14 agents:
  ai-solution-architect, prompt-engineer, mcp-server-architect,
  rag-system-designer, context-engineer, orchestration-architect,
  ai-devops-engineer, ai-team-transformer, a2a-architect,
  agent-developer, langchain-architect, mcp-quality-assurance,
  mcp-test-agent, ai-test-engineer
```

## Updated Marketplace

Add 3 new plugins to `plugins/.claude-plugin/marketplace.json`:

```json
{
  "name": "sdlc-team-common",
  "source": "./sdlc-team-common",
  "description": "Cross-cutting specialist agents — architects, researchers, performance engineers",
  "version": "1.0.0"
},
{
  "name": "sdlc-team-pm",
  "source": "./sdlc-team-pm",
  "description": "Project management agents — agile coach, delivery manager, progress tracking",
  "version": "1.0.0"
},
{
  "name": "sdlc-team-docs",
  "source": "./sdlc-team-docs",
  "description": "Documentation agents — technical writer, documentation architect",
  "version": "1.0.0"
}
```

All existing plugins update from `0.1.0-stub` to `1.0.0`.

## Deliverables

1. **Create 3 new plugin directories**: `sdlc-team-common`, `sdlc-team-pm`, `sdlc-team-docs` (plugin.json for each)
2. **Normalize frontmatter** on all 52 agents in `agents/` source directory
3. **Extend `release-mapping.yaml`** with all 52 agent-to-plugin mappings
4. **Update marketplace.json** — add 3 new plugins, update all versions to 1.0.0
5. **Run release** — copy all agents into their plugin directories
6. **Update `setup-team` skill** — common/pm/docs recommendations, agent rosters
7. **Update core plugin.json** — version to 1.0.0
8. **Validate** — all plugins install, all agents discoverable
9. **Feature proposal and retrospective**
10. **Tag `v1.0.0`**

## Success Criteria

- [ ] All 10 plugins have real agents (no more stubs)
- [ ] All 52 agent frontmatter normalized to plugin schema
- [ ] `release-mapping.yaml` maps all 52 agents to correct plugins
- [ ] Marketplace lists 10 plugins at v1.0.0
- [ ] `setup-team` recommends common/pm/docs and shows agent rosters
- [ ] Each plugin installs independently without errors
- [ ] Agents are discoverable and usable after plugin install
- [ ] Existing `agents/` source workflow continues working
- [ ] `v1.0.0` tag created on main after merge

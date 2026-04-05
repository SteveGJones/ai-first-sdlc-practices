# Agent Creation Pipeline: 1st-Party Discovery

**Date**: 2026-04-05
**Status**: Approved
**Issue**: #82

## Problem

The agent creation pipeline (pipeline-orchestrator → deep-research-agent → agent-builder) always builds domain agents from scratch. It doesn't check whether the domain already has official tooling — MCP servers, agent skills, Claude plugins, or CI/CD actions — published by the technology vendor. This means users get a generated agent when a better, officially-maintained one already exists.

Examples:
- MongoDB publishes an official MCP server AND agent skills (`github.com/mongodb/agent-skills`)
- Stripe has official SDK integrations
- GitHub has built-in CLI tools and Claude Code integration
- AWS, GCP, Azure all publish official GitHub Actions

## Solution

Add a Discovery phase to the pipeline-orchestrator that searches for 1st-party tools before routing to the build pipeline. Discovery checks registries and runs targeted web searches. If official tooling is found, the user chooses: use as-is, build a hybrid agent that complements the tools, or build from scratch anyway.

## Pipeline Flow

Current:
```
User request → Route (web research or repo analysis) → Research → Build → Validate
```

New:
```
User request → Check skip flag → Discovery (registry + web search) → Present findings
  → If tools found: ask user
    → "use as-is": recommend install, record in memory, STOP
    → "hybrid": pass discovery to research, build agent that complements official tools
    → "build custom": full research campaign → build (existing pipeline)
  → If nothing found: full research campaign → build (existing pipeline)
  → If --skip-discovery: bypass discovery, go straight to existing pipeline
```

## Discovery Phase

### Search Strategy

**Step 1: Registry checks + targeted web search** (always runs, 5-10 minutes)

| Source | Search Method | Looking For |
|--------|--------------|-------------|
| MCP server registries | WebSearch `"{vendor} mcp server" site:npmjs.com` and `site:pypi.org` | Official MCP servers |
| Vendor GitHub org | WebSearch `"github.com/{vendor}"` then look for repos named `*mcp*`, `*agent*`, `*skills*`, `*claude*` | Agent skills, MCP servers, Claude integrations |
| Claude plugin marketplace | Check marketplace for existing domain plugins | Claude Code plugins |
| GitHub Actions marketplace | WebSearch `"{vendor} github action" site:github.com/marketplace` | Official CI/CD actions |
| Targeted web search | `"{vendor} official mcp server"`, `"{vendor} agent skills"`, `"{vendor} ai integration"` | Anything not in registries |

**Step 2: Full research campaign** (only if Step 1 finds nothing)

If registry checks and web search find no official tooling, the pipeline proceeds to the existing deep-research-agent flow — a full research campaign to build the agent from documentation and best practices. This is the current behaviour, unchanged.

### Discovery Report Format

```markdown
## Discovery Report: {Domain}

### 1st-Party Tools Found

| Tool | Type | Source | Capabilities | Maintained? |
|------|------|--------|-------------|-------------|
| {name} | MCP Server / Agent Skills / Plugin / Action | {url} | {what it does} | {last activity} |

### Not Found
- {source}: {what was searched, no results}

### Recommendation
{summary of what was found and whether it covers the user's use case}

Options:
1. **Use official tools** — {install commands}
2. **Hybrid** — install official tools, build agent that orchestrates/extends them
3. **Build from scratch** — ignore official tools, run full research campaign
```

### User Decision Handling

**Option 1: Use as-is**
- Present install commands for each discovered tool
- Record discovery results in project memory
- Pipeline stops — no agent is built

**Option 2: Hybrid**
- Install official tools
- Pass discovery report as context to the research phase
- Research focuses on: what does the official tool NOT cover? What domain knowledge should the agent add on top?
- Agent-builder creates an agent that references the official tools: "use the MongoDB MCP server for direct queries, use this agent for schema design patterns and query optimization guidance"
- Agent frontmatter includes `first_party_alternatives` metadata

**Option 3: Build from scratch**
- Proceed to existing pipeline (full research campaign → build)
- Agent frontmatter still includes `first_party_alternatives` so future users know what exists
- Discovery report saved to memory for future reference

## Changes to Existing Agents

### pipeline-orchestrator.md

Add new **Phase 0: Discovery** before the existing Phase 1 (Input Analysis). Existing phases shift by one number.

Phase 0 content:
1. Accept user request, extract domain/technology name
2. Check for skip flag (explicit request, project config, or request wording like "build from scratch")
3. Check project memory for prior discovery results for this domain — if found, present cached results
4. If not skipped and no cached results: run registry checks + web search
5. Parse results into discovery report format
6. If tools found: present report with three options, wait for user decision
7. Route based on decision (use-as-is → stop, hybrid → research with context, build-custom → existing pipeline)
8. If nothing found: proceed to existing Phase 1 (triggers full research campaign)

### agent-builder.md

When building an agent that has discovery results (hybrid or build-custom mode):

**Frontmatter addition:**
```yaml
first_party_alternatives:
  - name: "@mongodb/mcp-server"
    type: mcp-server
    url: "https://npmjs.com/package/@mongodb/mcp-server"
  - name: "mongodb/agent-skills"
    type: agent-skills
    url: "https://github.com/mongodb/agent-skills"
```

**Body addition** — a "Related Official Tools" section in the agent body noting:
- What official tools exist
- What they cover
- Why a custom agent was still built (what gap it fills)

For hybrid agents specifically:
- Agent instructions should reference the official tools by name
- Describe when to use the official tool vs when to use this agent
- Example: "For direct MongoDB queries and schema inspection, use the MongoDB MCP server. This agent provides architectural guidance: schema design patterns, index optimization strategy, and migration planning."

### deep-research-agent.md

No changes. Only invoked when discovery finds nothing (existing path).

### repo-knowledge-distiller.md

No changes. Repo analysis is orthogonal to discovery.

## Storage

### Project Memory

When discovery finds official tools, write a memory file:

```markdown
---
name: discovery_{domain}
description: Official 1st-party tools discovered for {domain} — MCP servers, agent skills, plugins, actions
type: reference
---

## {Domain} Official Tooling

Discovered: {date}

| Tool | Type | Source | Install |
|------|------|--------|---------|
| @mongodb/mcp-server | MCP Server | npmjs.com | npm install @mongodb/mcp-server |
| mongodb/agent-skills | Agent Skills | github.com/mongodb/agent-skills | clone + install |

User decision: {use-as-is / hybrid / build-custom}
```

Future pipeline runs for the same domain check memory first — skip re-discovery if recent results exist.

### Agent Frontmatter

`first_party_alternatives` field added to any custom agent built when official tools were discovered. See agent-builder changes above.

## User Control

Three ways to skip discovery, checked in priority order:

1. **Explicit in request**: "Build a MongoDB agent, skip discovery" or "Build from scratch — I know about the official tools but need custom behaviour"
2. **Project config**: `.sdlc/pipeline-config.json` with `"discover_first_party": false`
3. **Default**: Discovery is ON

The pipeline-orchestrator checks these in order: explicit request > project config > default.

## Files Changed

| File | Change |
|------|--------|
| `agents/core/pipeline-orchestrator.md` | Add Phase 0 (Discovery) with registry search, web search, report generation, user decision handling |
| `agents/core/agent-builder.md` | Add `first_party_alternatives` frontmatter support, "Related Official Tools" body section, hybrid agent instruction patterns |
| `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Sync from source |
| `plugins/sdlc-team-common/agents/agent-builder.md` | Sync from source |

## Success Criteria

1. Pipeline-orchestrator checks for 1st-party tools before building
2. Discovery searches all 4 categories: MCP servers, agent skills, Claude plugins, GitHub Actions
3. Findings presented with clear recommendation and three options (use-as-is / hybrid / build-custom)
4. User can skip discovery with explicit flag or project config
5. Discovery results stored in project memory (prevents re-discovery)
6. Custom agents built after discovery include `first_party_alternatives` in frontmatter
7. Hybrid agents reference official tools in their instructions

## What This Does NOT Change

- The deep-research-agent (only invoked when no official tools found)
- The repo-knowledge-distiller (orthogonal to discovery)
- The agent-builder's 6-phase construction pipeline (unchanged, just receives additional context)
- The validation pipeline for built agents
- Existing agents already in the system

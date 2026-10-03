# Agent Base Audit — Part 2 of #83

**Date**: 2026-04-05
**Status**: Approved
**Issue**: #83 (Part 2 of 3)
**Branch**: `feature/extend-discovery-setup-audit`

## Problem

The 50+ agents in this repo were built without 1st-party discovery (#82 was implemented after them). Some agents may have official alternatives — vendor-published MCP servers, agent skills, Claude plugins, or GitHub Actions — that didn't exist when the agents were created, or that were simply not checked for. The agent base needs an audit to identify these alternatives and record them in agent frontmatter.

## Solution

A one-time audit of all agents in `agents/`, executed as batched subagent dispatches by category directory. Each batch runs discovery for its agents, returns findings. A coordinator compiles the report and applies frontmatter updates.

**This is a repo-level audit for framework maintainers, not a project-level tool for users.** A project-level audit skill (`/sdlc-core:audit-tools`) is Part 3's concern and will live in the plugin.

## Execution Approach

### Category Batches

Agents are organized in these directories:

| Directory | Approx. Count | Example Agents |
|-----------|--------------|----------------|
| `agents/core/` | ~20 | solution-architect, backend-architect, verification-enforcer |
| `agents/ai-development/` | ~9 | ai-solution-architect, prompt-engineer, mcp-server-architect |
| `agents/ai-builders/` | ~5 | rag-system-designer, context-engineer, orchestration-architect |
| `agents/testing/` | ~4 | code-review-specialist, performance-engineer |
| `agents/documentation/` | ~2 | technical-writer, documentation-architect |
| `agents/project-management/` | ~4 | agile-coach, delivery-manager |
| `agents/sdlc/` | ~8 | language-python-expert, retrospective-miner |

One subagent per batch. Each subagent:
1. Lists all `.md` files in its assigned directory
2. For each agent, reads the name and description from YAML frontmatter
3. Runs discovery using the same strategy as pipeline-orchestrator Phase 0:
   - MCP server registries (npm, PyPI)
   - Vendor/technology GitHub org search
   - Claude plugin marketplace
   - GitHub Actions marketplace
   - Targeted web search
4. Returns a structured finding per agent: alternatives found (or "None"), tool details (name, type, URL, maintained), and a recommendation (keep / review / reposition)

### Discovery Logic Per Agent

Extract the agent's domain from its name and description:
- `mcp-server-architect` → search for "MCP server" official tools
- `langchain-architect` → search for "LangChain" official tools
- `database-architect` → search for generic database MCP tools (broader search)
- `solution-architect` → search for "architecture" and "system design" AI tools, including Anthropic's own offerings
- `code-review-specialist` → search for "code review" AI tools, GitHub Copilot review, etc.

Every agent gets searched — no fast-skipping. Some generic agents (solution-architect, code-review-specialist) may have official alternatives from Anthropic or platform vendors.

### Frontmatter Updates

For agents where alternatives are found, add `first_party_alternatives` to the YAML frontmatter:

```yaml
first_party_alternatives:
  - name: "LangChain MCP Integration"
    type: agent-skills
    url: "https://github.com/langchain-ai/langchain-mcp"
  - name: "LangGraph Agent Framework"
    type: agent-skills
    url: "https://github.com/langchain-ai/langgraph"
```

This metadata is informational — it doesn't change agent behaviour. It tells future users and maintainers that official alternatives exist.

### Report Format

Saved to `docs/audits/2026-04-05-agent-base-audit.md`:

```markdown
# Agent Base Audit Report

**Date**: 2026-04-05
**Agents audited**: <N>
**Alternatives found**: <N agents with at least one alternative>
**Frontmatter updated**: <N>

## Summary

| Category | Agents | Alternatives Found | Frontmatter Updated |
|----------|--------|-------------------|-------------------|
| core | N | N | N |
| ai-development | N | N | N |
| ai-builders | N | N | N |
| testing | N | N | N |
| documentation | N | N | N |
| project-management | N | N | N |
| sdlc | N | N | N |
| **Total** | **N** | **N** | **N** |

## Findings by Agent

### <agent-name>
- **Category**: <directory>
- **Alternatives found**: <count>
  - <tool name> (<type>) — <url> — <capabilities> — Maintained: <Yes/No>
- **Action**: <Added first_party_alternatives to frontmatter / No change>
- **Recommendation**: <Keep / Review — may substantially overlap / Reposition as complement to official tools>
- **Rationale**: <Why this recommendation — what does the agent provide that the official tool doesn't, or vice versa>

(Repeated for every agent, including those with no alternatives found)
```

### Plugin Copy Sync

After frontmatter updates, sync changed agents to their plugin copies:
- `agents/core/*.md` → `plugins/sdlc-core/agents/`
- `agents/core/*.md` → `plugins/sdlc-team-common/agents/` (for agents in that plugin)
- `agents/ai-development/*.md` → `plugins/sdlc-team-ai/agents/`
- etc.

The `release-mapping.yaml` defines which source agents map to which plugins.

## Files Changed

| File | Change |
|------|--------|
| `docs/audits/2026-04-05-agent-base-audit.md` | New — audit report |
| `agents/{category}/*.md` | Frontmatter updates where alternatives found |
| `plugins/sdlc-team-*/agents/*.md` | Synced from source where frontmatter changed |

## Success Criteria

1. Every agent in `agents/` is audited (no agents skipped)
2. Discovery runs for all agents, including domain-agnostic ones
3. Report includes summary table and per-agent findings
4. `first_party_alternatives` added to frontmatter where alternatives found
5. Plugin copies synced for any changed agents
6. Report saved to `docs/audits/` for quarterly record

## What This Does NOT Do

- Deprecate or delete any agents — the report recommends, humans decide
- Create a project-level audit skill — that's Part 3
- Modify agent behaviour — frontmatter metadata is informational only
- Re-run periodically — this is a one-time execution. A quarterly repeat follows the same plan.

## Repeat Schedule

This audit should be repeated quarterly. To re-run:
1. Re-read this spec
2. Execute the implementation plan tasks
3. Save the new report as `docs/audits/YYYY-MM-DD-agent-base-audit.md`
4. Compare with the previous audit to identify what's changed

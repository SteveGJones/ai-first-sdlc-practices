---
title: "Claude Code Native Parallelism — Capabilities, Ceilings & Isolation Gaps"
domain: claude-code, parallelism, subagents, worktrees, headless, agent-sdk, isolation
status: active
tags: [claude-code, subagents, worktree-isolation, agent-sdk, headless-mode, agent-teams, permission-modes, mcp, gap-analysis, epic-96]
source: agent_prompts/campaign-96-containerized-workers/research/R1-output.md
cross_references:
  - library/archon-workflow-engine.md
  - library/containerised-worker-economics.md
  - library/containerised-worker-recommendations.md
  - library/multi-agent-framework-landscape.md
  - agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md
---

## Key Question

What can Claude Code do natively for parallel and headless operation, what are the hard ceilings, and exactly what gaps do containers fill?

## Core Findings

1. **Practical subagent ceiling is 5-7 concurrent agents.** No documented hard cap exists, but beyond 10 subagents resource exhaustion, API rate limits, and context window depletion create instability. One team spawned 24 subagent processes in 2 minutes and caused system lockup. -- GitHub issue #15487, R1 sec 2.1
2. **Worktree isolation is file-level only.** Git worktrees provide separate branch/directory and staging area, but share process (Node.js event loop), environment variables, database instances, network interfaces, and port space. CPU-bound work in one agent blocks others. -- R1 sec 2.3, GitHub issue #24177
3. **Context window is shared across subagents.** All subagents share the parent session's 200K token budget (1M available on Sonnet/Opus 4.6). When 5+ subagents complete simultaneously, result aggregation can exhaust the context window, triggering "Context low" errors. -- GitHub issue #10212, R1 sec 2.2
4. **Agent SDK (Python/TypeScript) provides full programmatic multi-agent control.** Same tools, agent loop, context management as CLI, plus hooks (PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd), native subagent spawning, MCP integration, and async parallel coroutines. -- Anthropic Agent SDK docs (CRAAP 24), R1 sec 5
5. **Headless modes cover all automation needs.** CLI `-p` flag (text/JSON/streaming output), `--bare` mode (skips hooks/plugins/MCP/memory for deterministic runs), `--output-format json` with `--json-schema` for structured output. All tools (Read/Write/Edit/Bash/Glob/Grep/WebSearch/WebFetch/Agent) work in headless. -- R1 sec 3
6. **Agent Teams (experimental) enable independent context windows.** One session acts as team lead; teammates work independently with own context windows and direct teammate-to-teammate communication. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var. Limited to 2-8 teammates. Not production-documented. -- R1 sec 10, Claude Code docs
7. **Five permission modes span interactive to fully unattended.** default (reads only), acceptEdits (reads + file edits), dontAsk (pre-approved tools only), auto (classifier-based, beta, Sonnet 4.6+), bypassPermissions (skip all prompts except protected paths). `--allowedTools` flag scopes per-run approvals. -- R1 sec 4.2
8. **GitHub Actions integration is official, mature, and cost-effective.** `anthropics/claude-code-action@v1` supports Anthropic, Bedrock, Vertex, Foundry auth at approximately $5 per 50 PRs/month. -- R1 sec 4.1
9. **Seven isolation gaps exist that containers resolve.** Process isolation (shared event loop), environment variables (shared globally), database isolation (shared instance), port management (EADDRINUSE conflicts), file permissions (same user), resource limits (no CPU/memory caps), credential isolation (global keychain). All have workarounds but containers offer native, zero-config enforcement. -- R1 sec 7.1
10. **Three capabilities remain unsolved as of April 2026.** Subagent inter-communication (parent-child only, no peer-to-peer), automatic maxParallelAgents enforcement (requested in #15487, not shipped), per-subagent context windows (all share parent's budget). -- R1 sec 12

## Frameworks Reviewed

| Framework | Evidence Base | Limitations |
|---|---|---|
| Claude Code CLI (headless) | Official docs (CRAAP 24), 18 sources scored 20+ | Slash commands unavailable in `-p` mode; auth regression in v2.0.37+ (issue #11631) |
| Claude Agent SDK (Python/TS) | Official docs (CRAAP 24), GitHub examples | Dependency on both Anthropic SDK and Claude Code runtime |
| Claude Code Agent Teams | Official docs, Medium article | Experimental; no custom delegation logic, no result aggregation patterns, no failure escalation |
| Git Worktree Isolation | Community guides (CRAAP 22-23), GitHub issues | File-level only; no process/env/DB/port isolation; max ~7 parallel |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Practical subagent ceiling | 5-7 agents | R1 sec 2.1, community reports | Beyond this, resource exhaustion risk without containers |
| System lockup risk | 10+ subagents | GitHub #15487 (24 agents caused lockup) | Hard signal to containerize |
| Context window saturation | 5+ simultaneous completions | GitHub #10212 | Triggers "Context low" errors; independent windows needed |
| Agent Teams limit | 2-8 teammates | Claude Code docs | Experimental cap; not scalable beyond 8 |
| Permission mode for containers | bypassPermissions | R1 sec 4.3 | Only suitable in isolated environments (containers, VMs) |

## Design Principles

1. **Native first, containerize on evidence.** Use Agent SDK + `--bare` + `dontAsk` for CI/CD; containerize only when you need 10+ parallel agents, isolated databases, or strict resource limits.
2. **Worktrees isolate code, not environment.** Git worktrees prevent file conflicts but share everything else (env, DB, ports, processes). This is by design, not a bug.
3. **Context is the real bottleneck, not compute.** Shared token budgets across subagents mean adding agents past 5-7 creates diminishing returns unless each gets an independent context window (Agent Teams or containers).
4. **Headless + bare is the automation baseline.** `--bare` mode skips all local config pollution (CLAUDE.md, MCP, hooks, plugins, OAuth, keychain) for deterministic, reproducible agent behavior.
5. **Permission scoping is layered defence.** `--allowedTools` (per-run) + `--permission-mode dontAsk` (policy) + protected paths (safety net) compose to create a controlled execution envelope.

## Key References

1. Anthropic Agent SDK Overview (CRAAP 24) -- https://code.claude.com/docs/en/agent-sdk/overview
2. Headless Mode Documentation (CRAAP 24) -- https://code.claude.com/docs/en/headless
3. Permission Modes Documentation (CRAAP 24) -- https://code.claude.com/docs/en/permission-modes
4. GitHub Issue #15487: Uncontrolled subagent spawning (CRAAP 23) -- https://github.com/anthropics/claude-code/issues/15487
5. GitHub Issue #10212: Context window depletion (CRAAP 22) -- https://github.com/anthropics/claude-code/issues/10212
6. GitHub Issue #24177: Process isolation request (CRAAP 22) -- https://github.com/anthropics/claude-code/issues/24177
7. Claude Code Agent Teams docs -- https://code.claude.com/docs/en/agent-teams
8. Database isolation patterns (CRAAP 22) -- https://www.damiangalarza.com/posts/2026-03-10-extending-claude-code-worktrees-for-true-database-isolation/
9. DEV Community: Worktrees infrastructure gap (CRAAP 22) -- https://dev.to/augusto_chirico/claude-code-loves-worktrees-your-infrastructure-doesnt-kfi

## Programme Relevance

**EPIC #96 (Containerised Claude Code Workers):**
- Establishes the native parallelism baseline: what you get for free (5-7 agents, file isolation, headless automation) and what requires infrastructure investment (process isolation, env isolation, resource limits, credential scoping).
- The 7 isolation gaps (finding 9) are the specific requirements a container architecture must solve. Each gap has a documented production incident validating the need.
- Agent Teams (finding 6) may reduce the container use case if the feature reaches stable and raises the teammate limit, but currently does not address env/DB/port isolation.
- The Agent SDK (finding 4) is the programmatic integration point for any containerised worker system -- use it inside containers, not the CLI.

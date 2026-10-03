---
title: "Archon Workflow Engine — Architecture & EPIC #96 Relevance"
domain: containerisation, orchestration, multi-agent, workflow-engine, claude-code
status: active
tags: [archon, dag-executor, worktree-isolation, claude-agent-sdk, container-provider, parallel-execution, ralph, epic-96]
source: library/raw/archon-analysis-2026-04-10.md
cross_references:
  - library/agentic-sdlc-options.md
  - agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md
  - retrospectives/85-docker-smoke-test.md
---

## Key Question

What is Archon, how does its architecture relate to our containerised worker delegation goals (EPIC #96), and what should we build on top of vs. build ourselves?

## Core Findings

1. Archon is an open-source workflow engine (15.5k stars, MIT, TypeScript/Bun) that defines AI coding workflows as YAML DAGs and executes them with Claude Code via `@anthropic-ai/claude-agent-sdk` — coleam00/Archon, inspected 2026-04-10
2. Independent DAG nodes run concurrently via `Promise.allSettled` in topological order — the `idea-to-pr` workflow fans out 5 parallel review agents then synthesises results — `packages/workflows/src/dag-executor.ts`
3. Isolation type system explicitly declares `'worktree' | 'container' | 'vm' | 'remote'` provider types, but **only worktree is implemented** — `packages/isolation/src/types.ts`, line: `export type IsolationProviderType = 'worktree' | 'container' | 'vm' | 'remote'`
4. Fresh context per iteration (`fresh_context: true`) prevents context window bloat — state persists via disk files (prd.json, progress.txt), not conversation history — `archon-ralph-dag.yaml` loop config
5. Production Dockerfile uses `oven/bun:1.3.11-slim`, non-root user `appuser` (UID 1001), gosu for privilege dropping, git safe.directory for workspace paths — matches our smoke test pattern from retrospective #85
6. Claude Code SDK integration handles global auth, explicit tokens, non-root safety, environment sanitisation, and embedded CLI entry point for binary builds — `packages/core/src/clients/claude.ts`
7. The `IIsolationProvider` interface (create/destroy/get/list/adopt/healthCheck) is clean and extensible — implementing a `ContainerProvider` wrapping Docker is architecturally straightforward
8. Per-node configuration supports: model override, fallback model, effort level, thinking mode, cost cap (`maxBudgetUsd`), sandbox settings, MCP servers, skills, hooks, retry, idle timeout — `packages/workflows/src/schemas/dag-node.ts`
9. Archon and our SDLC plugins operate at different layers (process vs team) — Archon orchestrates containers that run Claude Code sessions with our plugins installed; no command-format bridge needed, the Docker image is the integration point — architectural insight from brainstorming 2026-04-10
10. Archon's bundled prompts are generic process steps ("review code", "implement feature"); our 68+ specialist agents provide the domain expertise (architecture, security, performance, compliance) that makes each session effective — the two systems compose, not compete

## Frameworks Reviewed

| Framework | Evidence Base | Limitations |
|---|---|---|
| Archon DAG Executor | Source code inspection, 20 bundled workflows, `idea-to-pr` parallel review pattern verified | Container/VM/remote providers not yet implemented; only worktree isolation tested |
| Archon Isolation System | `IIsolationProvider` interface with WorktreeProvider implementation, IsolationResolver for lifecycle | ContainerProvider is declared in types but has zero implementation — would need to be built |
| Claude Agent SDK | Used by Archon's Claude client; `query()` function with streaming, auth, env sanitisation | SDK is Anthropic's, not Archon's — dependency on both projects |
| Archon Ralph DAG | Full implementation of story-driven development loop with fresh context per iteration | Overlap/conflict with our existing Ralph usage needs investigation |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Archon stars | 15,525 (2026-04-10) | GitHub API | Community validation — significant adoption for AI coding tool |
| Provider type coverage | 1 of 4 types implemented | Source inspection | Container isolation is planned but unbuilt — we'd be early contributors |
| Bundled workflows | 20 defaults | .archon/workflows/defaults/ | Mature workflow library covering common development patterns |
| Parallel review agents | 5 concurrent | archon-idea-to-pr.yaml | Production-tested fan-out/fan-in with `trigger_rule: one_success` |
| UID convention | 1001 (appuser) | Dockerfile | Matches our smoke test's `sdlc` user UID — compatibility signal |

## Design Principles

1. **DAG-first orchestration**: Workflows are YAML DAGs, not imperative scripts. Parallelism emerges from the dependency graph — no explicit "run in parallel" instruction needed.
2. **Disk as state bus**: Workers communicate via filesystem (output files, prd.json, progress.txt), not conversation context. This decouples workers and enables `fresh_context` per iteration.
3. **Provider-based isolation**: The isolation system is an interface, not an implementation. New providers (container, VM, remote) plug in without changing the executor.
4. **Graduated sandboxing**: Three layers — worktree isolation (git), Claude SDK sandbox (filesystem/network restrictions), future container isolation (OS-level). Layers compose, don't replace.
5. **Commands as units**: Archon commands (`.archon/commands/*.md`) are the atomic units of work. Workflows compose commands. This maps to our agents/skills model but with different packaging.

## Key References

1. coleam00/Archon GitHub repository — https://github.com/coleam00/Archon (inspected 2026-04-10, dev branch)
2. Archon documentation — https://archon.diy
3. `packages/workflows/src/dag-executor.ts` — DAG executor with concurrent node execution
4. `packages/isolation/src/types.ts` — Isolation provider type system (worktree/container/vm/remote)
5. `packages/isolation/src/providers/worktree.ts` — WorktreeProvider implementation
6. `packages/core/src/clients/claude.ts` — Claude Agent SDK wrapper
7. `.archon/workflows/defaults/archon-idea-to-pr.yaml` — Fan-out/fan-in parallel review workflow
8. `.archon/workflows/defaults/archon-ralph-dag.yaml` — Story-driven implementation loop with fresh context
9. `Dockerfile` — Production multi-stage build with non-root user pattern

## Integration Model: Archon as Orchestrator, Our Plugins as the Team

The key insight (established 2026-04-10 during brainstorming) is that Archon and our SDLC plugins operate at **different layers** — they compose, not compete:

```
Archon (process layer)
  └── spawns Claude Code sessions (each session is a team member)
        └── each session has our SDLC plugins installed
              └── plugins provide the specialist agents (architect, security, performance, etc.)
```

**Archon provides process**: DAG execution, parallelism, isolation, retry, approval gates, lifecycle management. It knows *when* to run things and *how* to isolate them. It does not provide domain expertise — its bundled prompts are generic ("review this code", "implement this feature").

**Our plugins provide the team**: 68+ specialist agents with deep domain knowledge. Solution architects, security specialists, performance engineers, compliance auditors, language experts. The intelligence that makes each Claude Code session effective at its specific task.

**How it works in practice**: An Archon workflow node contains a prompt like "Use the security-architect agent to review this for OWASP Top 10 vulnerabilities." Archon spawns a containerised Claude Code session. That session loads our `CLAUDE.md`, has our plugins installed, and the security-architect agent is available via the `Agent` tool. The agent does the real work; Archon just managed the container, the worktree, the context, and the retry logic.

**No bridge layer needed**: Archon commands (`.archon/commands/`) are just prompt files. They can reference our agents by name. Our plugins install into the Claude Code environment inside the container. Archon doesn't need to understand our plugin format — it just needs the container image to have them pre-installed.

**The Docker image is the integration point**: A single image containing Archon + Claude Code + our SDLC plugins = a fully equipped team member ready to receive any role assignment from the DAG.

## Programme Relevance

**EPIC #96 (Containerised Claude Code Workers)**:
- Archon is the orchestration layer; we provide the specialist agents that run inside its containers
- The `IIsolationProvider` interface with `container` type is the extension point for Docker-based execution
- The fan-out/fan-in pattern in `idea-to-pr` validates our A2A supervisor/worker design
- Integration is simpler than initially assessed: Docker image with Archon + our plugins, not a command-format bridge
- Prototype: build a Docker image with Archon + SDLC plugins, define one workflow that uses our agents, validate the model

**EPIC #97 (Commissioned SDLC)**:
- Archon's workflow YAML format could be the execution format for commissioned SDLC options
- Each SDLC option's workflow (specify → architect → implement → review) maps naturally to an Archon DAG
- The `approval` node type provides the human-in-the-loop gates our commissioning system needs
- Different SDLC options = different Archon workflow YAMLs, all using the same team of specialist agents

**EPIC #142 (Technology Registry)**:
- Archon's per-node model override, sandbox settings, and MCP server config could be informed by our technology registry
- The registry could recommend which agents to invoke in which workflow nodes

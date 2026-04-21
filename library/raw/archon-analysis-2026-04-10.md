# Archon (coleam00/Archon) — Source Analysis for EPIC #96

**Date**: 2026-04-10
**Repo**: https://github.com/coleam00/Archon
**Version analysed**: dev branch (commit at 2026-04-10)
**Stars**: 15,525 | **Forks**: 2,542 | **License**: MIT | **Language**: TypeScript (Bun)

## What Archon Is

Archon is a workflow engine for AI coding agents. It lets you define multi-step development processes as YAML DAGs (directed acyclic graphs) and execute them with Claude Code (via `@anthropic-ai/claude-agent-sdk`) or Codex as the underlying AI engine. Self-described as "what Dockerfiles did for infrastructure and GitHub Actions did for CI/CD — Archon does for AI coding workflows."

## Architecture (from source code inspection)

### Monorepo Packages

```
packages/
├── adapters/    # Platform adapters (chat, community/forge integrations)
├── cli/         # CLI binary
├── core/        # Orchestrator, clients (Claude SDK, Codex), DB, services, state
├── docs-web/    # Documentation site (archon.diy)
├── git/         # Git operations library
├── isolation/   # Worktree isolation provider (extensible to container/VM/remote)
├── paths/       # Path resolution, logger
├── server/      # HTTP server, auth, API
├── web/         # React web UI
├── workflows/   # DAG executor, schemas, validators, loaders
```

### Claude Code Integration

Uses `@anthropic-ai/claude-agent-sdk` directly (`packages/core/src/clients/claude.ts`). Wraps the SDK's `query()` function with:
- Async generator interface for streaming
- Global auth support (`CLAUDE_USE_GLOBAL_AUTH=true` for `claude /login` tokens)
- Explicit token support via env vars
- Non-root safety check (refuses to run as root without `IS_SANDBOX=1`)
- Environment sanitisation (prevents credential leakage via `buildCleanSubprocessEnv`)
- Embedded CLI entry point (`@anthropic-ai/claude-agent-sdk/embed`) for binary builds

Also supports Codex (`packages/core/src/clients/codex.ts`) as an alternative provider.

### Workflow DAG Executor

`packages/workflows/src/dag-executor.ts` — The core engine:

- Executes nodes in **topological order**
- **Independent nodes within the same layer run concurrently** via `Promise.allSettled`
- Output captured via `$node_id.output` variable substitution
- Node types: `command`, `prompt`, `bash`, `loop`, `approval`, `cancel`
- Conditional execution via `when:` expressions
- `trigger_rule`: `all_success`, `one_success`, `none_failed_min_one_success`, `all_done`
- Per-node retry with configurable `max_attempts`, `delay_ms`, `on_error: transient|all`
- `fresh_context: true` option — each node/loop-iteration starts a new Claude session
- Idle timeout detection (`idle_timeout` per node)
- Cost tracking per node with `maxBudgetUsd` cap
- Cancel check throttling (10s intervals)
- Activity heartbeat (60s intervals)

### Isolation System

`packages/isolation/` — Provider-based abstraction:

**Type system** (from `types.ts`):
```typescript
type IsolationProviderType = 'worktree' | 'container' | 'vm' | 'remote';
```

**Currently implemented**: `worktree` only (via `WorktreeProvider`).
**Planned but not implemented**: `container`, `vm`, `remote`.

The isolation interface (`IIsolationProvider`) has methods:
- `create(request)` → creates isolated environment
- `destroy(envId, options)` → best-effort cleanup with partial-failure reporting
- `get(envId)` / `list(codebaseId)` → query
- `adopt?(path)` → take ownership of externally-created environments
- `healthCheck(envId)` → verify environment is live

Worktree types: `issue`, `pr`, `review`, `thread`, `task` — each with specific branch naming conventions.

The `IsolationResolver` handles: reuse of existing environments, stale cleanup, linked issue/PR adoption, auto-cleanup when capacity is exceeded.

### Sandbox Settings (Claude SDK)

Per-node or workflow-level OS-level isolation via Claude Agent SDK sandbox:
```yaml
sandbox:
  enabled: true
  autoAllowBashIfSandboxed: true
  network:
    allowedDomains: [...]
    allowManagedDomainsOnly: true
```

This is Claude Code's own sandboxing (filesystem/network restrictions on the subprocess), not container isolation.

### Dockerfile (Production Deployment)

Multi-stage build:
1. **deps**: `oven/bun:1.3.11-slim`, install all dependencies
2. **web-build**: Build React web UI (Vite)
3. **production**: `oven/bun:1.3.11-slim` + system deps (git, bash, gh, chromium, gosu, postgresql-client, agent-browser)

Key patterns:
- Non-root user `appuser` (UID 1001) — matches our smoke test pattern
- `gosu` for privilege dropping in entrypoint
- Archon directories at `/.archon/workspaces` and `/.archon/worktrees`
- Git safe.directory configured for workspace paths
- Agent-browser (Vercel Labs) for E2E testing with headless Chromium

### Bundled Workflows (20 defaults)

```
archon-adversarial-dev.yaml       archon-interactive-prd.yaml
archon-architect.yaml             archon-issue-review-full.yaml
archon-assist.yaml                archon-piv-loop.yaml
archon-comprehensive-pr-review    archon-plan-to-pr.yaml
archon-create-issue.yaml          archon-ralph-dag.yaml
archon-feature-development.yaml   archon-refactor-safely.yaml
archon-fix-github-issue.yaml      archon-remotion-generate.yaml
archon-idea-to-pr.yaml            archon-resolve-conflicts.yaml
archon-smart-pr-review.yaml       archon-test-loop-dag.yaml
archon-validate-pr.yaml           archon-workflow-builder.yaml
```

### Platform Adapters

Multi-platform delivery: CLI, Web UI, Slack, Telegram, Discord, GitHub (via adapters package).

## Key Patterns Relevant to EPIC #96

### 1. DAG-Based Parallel Execution

The `idea-to-pr` workflow demonstrates fan-out/fan-in:
- Phase 6 (code review) fans out 5 parallel agents: `code-review`, `error-handling`, `test-coverage`, `comment-quality`, `docs-impact`
- All 5 depend on `sync` (same upstream)
- `synthesize` node depends on all 5, with `trigger_rule: one_success` (resilient to individual failures)
- `implement-fixes` runs after synthesis

This is exactly the supervisor/worker pattern we designed in our A2A system.

### 2. Fresh Context Per Iteration

The Ralph DAG loop uses `fresh_context: true` — each iteration starts a completely new Claude session. State persists via disk (prd.json, progress.txt), not conversation context. This prevents context window bloat and ensures each worker starts clean.

### 3. Worktree Isolation with Extensibility Hooks

The isolation type system already declares `container`, `vm`, `remote` as future providers. The `IIsolationProvider` interface is clean enough that implementing a `ContainerProvider` that wraps Docker would be straightforward.

### 4. Structured Output Between Nodes

Nodes can declare `output_format` (JSON Schema) and downstream nodes reference `$node_id.output`. This is the communication protocol between supervisor and workers.

### 5. Auto-Cleanup and Lifecycle

The `IsolationResolver` handles stale worktree cleanup, capacity management, and adoption of externally-created environments. This lifecycle management would transfer directly to container lifecycle.

## What Archon Provides vs What We'd Need to Build

### Archon Already Provides

| Capability | Implementation |
|---|---|
| Parallel node execution | DAG executor with Promise.allSettled |
| Git worktree isolation | WorktreeProvider with full lifecycle |
| Claude Code SDK integration | Claude client with auth, streaming, env sanitisation |
| YAML workflow definitions | Schema-validated DAGs with conditions, loops, retries |
| Output passing between nodes | `$node_id.output` substitution |
| Fresh context management | `fresh_context: true` per node/iteration |
| Cost tracking | Per-node `maxBudgetUsd` cap |
| Failure handling | Retry config, trigger rules, idle timeout, cancel checks |
| Multi-platform delivery | CLI, Web UI, Slack, Telegram, Discord, GitHub |
| Approval gates | Human-in-the-loop pause/resume |
| Model routing | Per-node model override, fallback models |

### We'd Need to Build / Integrate

| Capability | Status | Notes |
|---|---|---|
| Container isolation provider | Interface exists, not implemented | Implement `IIsolationProvider` for Docker |
| Remote/cloud execution | Type declared (`remote`), not implemented | ECS/Fargate/K8s worker dispatch |
| SDLC plugin integration | Not applicable to Archon's model | Our 68+ agents as Archon commands |
| SDLC validation pipeline | Archon has `bash:` nodes for validation | Wire our 10-check pipeline as bash nodes |
| Credential management at scale | Docker entrypoint handles single instance | Multi-container credential sharing |
| Ralph integration | Archon has `archon-ralph-dag.yaml` | May replace our Ralph usage or complement it |

## Strategic Assessment

### Option A: Adopt Archon as Our Workflow Engine

**What this means**: Use Archon's DAG executor, isolation system, and Claude SDK integration as the orchestration layer. Package our SDLC agents as Archon commands. Define our workflows (feature development, PR review, validation) as Archon YAML DAGs. Contribute a `ContainerProvider` to the Archon isolation system.

**Pros**: Mature DAG executor (tested, edge cases handled), existing multi-platform delivery, active community (15k stars), MIT license, extensible isolation architecture.
**Cons**: Dependency on external project, our plugin architecture doesn't map 1:1 to Archon's command model, would need to adapt our skills/agents to Archon's format, potential friction between Archon's opinions and ours.

### Option B: Learn From Archon, Build Our Own

**What this means**: Extract the architectural patterns (DAG execution, worktree isolation, fresh context, output substitution) and implement them in our existing plugin system. Build our own container isolation from scratch.

**Pros**: Full control, fits our existing architecture, no external dependency.
**Cons**: Significant engineering effort to replicate what Archon already provides, risk of re-inventing solved problems.

### Option C: Hybrid — Archon for Orchestration, Our Plugins for Intelligence

**What this means**: Use Archon as the "workflow runtime" that manages execution, isolation, and lifecycle. Our SDLC plugins provide the agent prompts, validation logic, and domain knowledge that Archon nodes execute. Contribute a ContainerProvider upstream for mutual benefit.

**Pros**: Best of both worlds, contribute to open source, reduce our maintenance burden for orchestration, keep our domain expertise as the differentiator.
**Cons**: Integration complexity, two systems to understand, potential version conflicts.

## Key Risks

1. **Archon is evolving rapidly** — the codebase is actively developed, APIs may change
2. **Container isolation is not yet implemented** — we'd be building on a planned-but-unbuilt extension point
3. **Ralph DAG overlap** — Archon includes its own Ralph integration; unclear how this relates to our Ralph usage
4. **Plugin model mismatch** — Archon uses `.archon/commands/` and `.archon/workflows/`; we use `.claude/plugins/` with agents/skills/hooks structure
5. **The isolation interface is clean but untested for containers** — implementing ContainerProvider may surface design assumptions baked into the worktree path

# Design Spec: Containerised Claude Code Worker Delegation (EPIC #96)

**Date**: 2026-04-10
**Status**: Draft — pending review
**EPIC**: #96 — Containerised Claude Code Workers
**Related**: EPIC #97 (Commissioned SDLC), EPIC #142 (Technology Registry)

## 1. Problem Statement

All work in the AI-First SDLC framework runs sequentially in a single Claude Code session — one agent, one task, one session. This blocks four use cases:

1. **Parallel feature development** — implementing multiple features concurrently in isolated environments
2. **Autonomous SDLC pipelines** — fire-and-forget commissioned workflows (specify → architect → implement → review) that run end-to-end without supervision
3. **Cloud-hosted worker fleet** — remote workers dispatched from Slack, GitHub, or web UI
4. **Secure sandboxed execution** — Ralph loops and autonomous agents confined to containers where runaway behaviour can't cause damage

Native Claude Code subagents (5-7 practical ceiling) and worktree isolation (file-level only — no process, environment, database, or port isolation) are insufficient for these use cases.

## 2. Architecture

### 2.1 Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: THE TEAM (this repo)                          │
│  68+ specialist agents, 11 plugins, validation pipeline,│
│  knowledge base, rules (CONSTITUTION.md)                │
│  Ships as: Claude Code plugins via marketplace          │
└────────────────────────┬────────────────────────────────┘
                         │ installed into
┌────────────────────────▼────────────────────────────────┐
│  Layer 2: THE PROCESS ENGINE (Archon — external)        │
│  DAG executor, worktree/container lifecycle, retry,     │
│  output passing, cost caps, approval gates,             │
│  multi-platform delivery (CLI/web/Slack/Discord/GitHub) │
│  Ships as: Archon CLI binary                            │
└────────────────────────┬────────────────────────────────┘
                         │ configured by
┌────────────────────────▼────────────────────────────────┐
│  Layer 3: THE WIRING (sdlc-workflows plugin — NEW)      │
│  Archon workflow YAMLs, command prompts (PROMPT.md      │
│  briefs), Docker image, setup/run/status skills         │
│  Ships as: another plugin in this repo                  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Integration Model

Archon orchestrates containers. Each container runs a Claude Code session with our SDLC plugins installed. Node prompts in Archon workflows reference our agents by name. The Docker image is the integration point — no command-format bridge needed.

```
Archon DAG Executor
  ├── Node: "plan"        → spawns Claude Code session → plugins loaded → uses solution-architect agent
  ├── Node: "implement"   → spawns Claude Code session → plugins loaded → uses language-python-expert
  ├── Node: "security"    → spawns Claude Code session → plugins loaded → uses security-architect
  ├── Node: "review"      → spawns Claude Code session → plugins loaded → uses code-review-specialist
  └── Node: "validate"    → bash node → runs python tools/validation/local-validation.py --pre-push
```

### 2.3 Key Architectural Decisions

1. **Archon is an external runtime dependency**, like Claude Code itself. We don't fork or embed it. We contribute upstream where possible (ContainerProvider).
2. **Workflows ship as a plugin** (`sdlc-workflows`), following existing plugin conventions. Users opt in by installing the plugin.
3. **The Docker image is built by the user**, not shipped as a pre-built binary. The Dockerfile and build scripts are in the plugin.
4. **Setup-team detects delegation needs** and recommends Archon installation. Always explicit — never hidden.
5. **Deterministic DAGs, not AI-driven decomposition.** Research shows spec-driven decomposition prevents 90% of agent collisions. Archon's YAML DAG model enforces this.

## 3. The `sdlc-workflows` Plugin

### 3.1 Plugin Structure

```
plugins/sdlc-workflows/
├── README.md
├── workflows/                            # Archon YAML DAGs
│   ├── sdlc-feature-development.yaml     # specify → architect → implement → review
│   ├── sdlc-parallel-review.yaml         # fan-out 5 review agents, synthesise
│   ├── sdlc-bulk-refactor.yaml           # file-partitioned parallel refactor
│   └── sdlc-commissioned-pipeline.yaml   # full autonomous SDLC (EPIC #97 tie-in)
├── commands/                             # Archon command prompts
│   ├── sdlc-plan.md
│   ├── sdlc-implement.md
│   ├── sdlc-security-review.md
│   ├── sdlc-architecture-review.md
│   ├── sdlc-performance-review.md
│   ├── sdlc-code-quality-review.md
│   ├── sdlc-test-coverage-review.md
│   ├── sdlc-validate.md
│   ├── sdlc-synthesise-reviews.md
│   └── sdlc-merge-results.md
├── docker/
│   ├── Dockerfile                        # sdlc-worker image
│   ├── build.sh
│   ├── entrypoint.sh
│   └── docker-compose.yml                # Local dev setup
├── skills/
│   ├── workflows-setup/SKILL.md          # Install Archon + configure
│   ├── workflows-run/SKILL.md            # Run a workflow
│   └── workflows-status/SKILL.md         # Check running workflow
└── agents/
    └── delegation-coordinator.md          # Task decomposition specialist
```

### 3.2 Command Prompt Quality Standard

Each command in `commands/` is a substantial PROMPT.md-style brief, not a one-liner. Every command follows this structure:

1. **Role framing** — who the agent is, what parallel specialists are doing alongside it, what its exclusive focus area is
2. **Context loading** — how to discover the change set, load project rules, understand scope
3. **Step-by-step process** — numbered actions with specific commands, tools, and agent references
4. **Output format** — structured output template (usually JSON or Markdown with defined sections)
5. **Constraints** — what NOT to do, time budget, scope boundaries

Example: the security review command instructs the worker to discover the change set via `git diff`, threat model each component, review against OWASP Top 10, invoke the security-architect agent for deep analysis, run the security validation pipeline, and output structured findings with severity ratings, confidence assessment, and evidence of what was verified clean.

### 3.3 Workflow YAML Design Patterns

**Pattern 1: Fan-out / Fan-in** (parallel review)
- Multiple independent review nodes, all `context: fresh`
- Synthesis node with `trigger_rule: one_success` (resilient to individual failures)
- Used by: `sdlc-parallel-review.yaml`

**Pattern 2: Sequential Pipeline** (feature development)
- Linear chain: plan → implement → validate → review → merge
- Each node depends on prior, `context: fresh` to prevent context bloat
- `implement` node uses `loop:` with `until:` signal for iterate-until-tests-pass
- Used by: `sdlc-feature-development.yaml`

**Pattern 3: File-Partitioned Parallel** (bulk refactor)
- Decomposition node splits work into non-overlapping file sets
- N implementation nodes run in parallel, each assigned a file set
- Sequential merge node combines results with conflict detection
- Used by: `sdlc-bulk-refactor.yaml`

**Pattern 4: Commissioned Autonomous** (full SDLC pipeline)
- Complete specify → architect → implement → review cycle
- Approval gates at key decision points
- Connects to EPIC #97 commissioned SDLC options
- Used by: `sdlc-commissioned-pipeline.yaml`

## 4. Docker Image

### 4.1 Image Definition

Based on `node:22-slim` (matching existing smoke test). Contains:
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Archon CLI (`curl -fsSL https://archon.diy/install | bash`)
- Python 3, Git, system dependencies
- Non-root user `sdlc` (UID 1001, matching smoke test convention)
- Pre-created `/home/sdlc/.claude` and `/home/sdlc/.archon` owned by `sdlc`

### 4.2 Plugin Installation Strategy

Build arg controls timing:
- `INSTALL_PLUGINS_AT_BUILD=true` — production (fast startup, version-pinned)
- `INSTALL_PLUGINS_AT_BUILD=false` — development (always latest, slower startup)

Default: runtime install (development mode) for simplicity in MVP.

### 4.3 Entrypoint Responsibilities

1. Restore auth — `.claude.json` from backup in named volume (pattern from `retrospectives/85-docker-smoke-test.md`)
2. Install SDLC plugins (if not baked into image)
3. Execute assigned work — Archon workflow node or direct Claude Code command

### 4.4 Local Development (docker-compose.yml)

Single-service Compose file runs Archon server with:
- Named volume for Claude credentials
- Project directory mounted as workspace
- Workflow YAMLs mounted into `.archon/workflows/`
- Port 3000 exposed for Archon web UI

## 5. Setup-Team Integration

### 5.1 Delegation Detection Signals

| Signal | Weight | Detection Method |
|--------|--------|-----------------|
| Large codebase (>50k LOC) | Medium | Line count via find + wc |
| Multiple services/modules | Medium | Count of independent package manifests (>3) |
| Existing CI/CD | Low | `.github/workflows/` or `.gitlab-ci.yml` exists |
| Monorepo structure | High | Multiple top-level service dirs with independent deps |
| Existing `.archon/` directory | High | Already using Archon |
| Ralph configs present | Medium | `ralph.yml` or `.ralph/` exists |
| User explicitly requests | High | "yes" to the delegation question |

### 5.2 Recommendation Flow

After plugin recommendations, before install, if delegation signals are present:

```
Your project shows signals that could benefit from delegated parallel
execution (multiple services, large codebase, CI/CD present).

Delegation lets you run multiple specialist agents in parallel — for
example, 5 review agents simultaneously checking security, architecture,
performance, code quality, and test coverage.

This requires Archon (https://archon.diy), an open-source workflow
engine that orchestrates Claude Code sessions. It will be installed
alongside your SDLC plugins.

Would you like to enable delegated workflows?
  (a) Yes — install Archon + sdlc-workflows plugin
  (b) Not now — I can add this later with /sdlc-workflows:setup
  (c) Tell me more — explain what delegation provides
```

If signals are absent, the question is not asked. Users can always discover delegation via `/sdlc-workflows:setup`.

### 5.3 Transparency Principle

Every recommendation that involves Archon names it explicitly, links to its repo, and explains what it does. Archon is never installed silently. This is consistent with how setup-team already handles external tool recommendations in Section A of discovery output.

## 6. Delegation Smoke Test

### 6.1 Structure

```
tests/integration/delegation-smoke/
├── Dockerfile              # Extends sdlc-worker image with test fixtures
├── build.sh
├── login.sh                # Reuses sdlc-smoke-claude-creds volume
├── run.sh
├── entrypoint.sh
├── PROMPT.md               # Outer supervisory prompt
├── ralph.yml
├── workflows/
│   └── smoke-parallel-review.yaml  # 2-node parallel + synthesis
├── commands/
│   ├── smoke-review-a.md           # Structure review
│   └── smoke-review-b.md           # Test coverage review
└── fixtures/
    └── miniproject/                 # Tiny project with deliberate issues
        ├── README.md
        ├── src/app.py
        └── tests/test_app.py
```

### 6.2 The Smoke Workflow

Minimal 2-node parallel workflow:
- `review-structure` and `review-tests` run concurrently (`context: fresh`)
- `synthesise` node depends on both, `trigger_rule: one_success`
- Synthesise produces structured JSON output with `output_format` schema

### 6.3 Success Criteria (9 checks)

1. Archon CLI installed and on PATH
2. `archon workflow list` shows `smoke-parallel-review`
3. SDLC plugins installed (sdlc-core minimum)
4. Workflow starts without error
5. Node `review-structure` completes with output captured
6. Node `review-tests` completes with output captured
7. Both nodes ran concurrently (start times within 5s, verified from Archon logs)
8. `synthesise` node produces valid JSON with all required fields
9. Total workflow duration < 10 minutes

### 6.4 Shared Infrastructure

- Reuses credential volume `sdlc-smoke-claude-creds` from existing setup smoke test
- Same Docker patterns: node:22-slim, UID 1001, named volume mount
- Login script shared or symlinked from `setup-smoke/login.sh`

## 7. ContainerProvider (Archon Contribution)

### 7.1 Scope

Implement the `IIsolationProvider` interface for Docker containers in Archon's `packages/isolation/` package. The type `'container'` is already declared in Archon's type system but has zero implementation.

### 7.2 Interface Methods

- `create(request)` — `docker run` with appropriate mounts, env, resource limits
- `destroy(envId, options)` — `docker rm` with best-effort cleanup
- `get(envId)` — `docker inspect` to retrieve container state
- `list(codebaseId)` — `docker ps --filter` to find related containers
- `healthCheck(envId)` — heartbeat file `mtime` check or `docker inspect` status
- `adopt(path)` — take ownership of externally-created containers (optional)

### 7.3 Delivery Path

Preferred: upstream PR to `coleam00/Archon`. The interface is clean and the type is already declared — this is a planned extension, not a hack. If upstream is unresponsive or the PR takes too long, local extension via Archon's plugin/config mechanism.

### 7.4 Development Independence

This sub-feature develops in Archon's codebase (TypeScript), not ours. It can proceed in parallel with sub-features 0-5 which are all in our repo.

## 8. Sub-Feature Decomposition & Phasing

| Sub-feature | Scope | Depends On | Deliverable |
|---|---|---|---|
| **0: Plugin skeleton + delegation detection** | Create `plugins/sdlc-workflows/` structure, add delegation signals to setup-team | None | Plugin dir, modified setup-team SKILL.md |
| **1: Docker image** | Dockerfile, build.sh, entrypoint.sh, docker-compose.yml | None | Buildable sdlc-worker image |
| **2: Command prompts** | Full PROMPT.md briefs for all commands | None | 10 command files in `commands/` |
| **3: Workflow YAMLs** | Archon DAG definitions for 4 workflows | Sub-feature 2 | 4 workflow files in `workflows/` |
| **4: Skills** | workflows-setup, workflows-run, workflows-status | Sub-features 2, 3 | 3 skills in `skills/` |
| **5: Delegation smoke test** | Test fixture, smoke workflow, success criteria | Sub-features 1-4 | `tests/integration/delegation-smoke/` |
| **6: ContainerProvider** | Archon upstream contribution | None (parallel) | PR to coleam00/Archon |

**Execution order**: 0 → 1 → 2 → 3 → 4 → 5 (sequential). Sub-feature 6 in parallel.

Sub-features 0, 1, and 2 have no dependencies and could run in parallel if multiple contributors are available, but are ordered for solo developer flow.

## 9. Out of Scope

These are explicitly deferred to future EPICs:

- **Cloud deployment** (K8s Jobs, ECS Fargate, Workload Identity) — separate EPIC when Docker Compose MVP is validated
- **Queue-based dispatch** (NATS, RabbitMQ) — separate EPIC at 10+ agent scale
- **Auto-scaling** — separate EPIC at production fleet scale
- **EPIC #97 commissioned SDLC workflows** — consumes this EPIC's infrastructure, separate implementation
- **Rate limit optimisation** (prompt caching, model routing) — separate concern, applicable with or without containers
- **gVisor / Firecracker isolation** — upgrade path from Docker if security requirements demand it

## 10. Research Foundation

This design is informed by a systematic research campaign (`agent_prompts/campaign-96-containerized-workers/`):
- 5 parallel research missions (R1-R5) covering Claude Code capabilities, multi-agent frameworks, container patterns, task delegation, and cost/performance
- 3 sequential syntheses (S1-S3) producing landscape map, architecture patterns, and recommendations
- All findings ingested into the knowledge base at `library/`

Key research findings that shaped this design:
- Rate limits cap parallelism at 2-4 agents on current plans (R5) — start simple
- Token costs dominate infrastructure 100:1 (R5) — don't over-engineer containers
- Spec-driven decomposition prevents 90% of collisions (R4) — deterministic DAGs, not AI decomposition
- File-level partitioning achieves 95%+ merge success (R4) — partition commands by file ownership
- Archon's isolation type system declares `container` but hasn't implemented it (R2/Archon analysis) — we fill the gap
- No framework provides Claude Code + containers + multi-agent natively (R2) — we assemble from Archon + our plugins

## 11. Success Metrics

| Metric | Target | Measured When |
|---|---|---|
| Delegation smoke test passes | 9/9 criteria | Sub-feature 5 complete |
| Parallel review speedup | >1.5x vs sequential | Smoke test timing |
| Plugin install path works | setup-team recommends + installs cleanly | Sub-feature 0 complete |
| Docker image builds | < 5 minutes, < 1GB | Sub-feature 1 complete |
| Command prompts produce quality output | Agent specialist output matches manual invocation quality | Sub-feature 2 review |
| Workflows execute end-to-end | All 4 workflow patterns complete without error | Sub-feature 3-4 complete |

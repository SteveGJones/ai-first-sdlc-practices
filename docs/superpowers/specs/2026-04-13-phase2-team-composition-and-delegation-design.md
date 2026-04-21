# Design Spec: Phase 2 — Team Composition and Delegation Infrastructure (EPIC #96)

**Date**: 2026-04-13
**Status**: Draft — pending review
**EPIC**: #96 — Containerised Claude Code Workers
**Phase**: 2 of 4 (Team Experience)
**Depends on**: Phase 1 (Infrastructure) — complete, 22 commits on `feature/96-sdlc-workflows`
**Related**: EPIC #97 (Commissioned SDLC), EPIC #142 (Technology Registry)

## 1. Problem Statement

Phase 1 proved that Archon can orchestrate containerised Claude Code sessions with our SDLC plugins. But every container starts from scratch — plugins install at runtime (30-60s per node), there's no team identity, and the user has no way to control which agents and skills each node has access to.

This creates four problems:

1. **No team enforcement** — every node has access to everything (or nothing, if plugins haven't installed yet). A security review node could invoke development agents. An implementation node could skip validation. Prompt guidance alone doesn't enforce boundaries.
2. **Runtime install tax** — each Archon node installs plugins on startup. For a 6-node parallel review workflow, that's 6 redundant installs. Slow and wasteful.
3. **No persistent team context** — `fresh_context: true` (required to prevent context bloat) wipes everything. Each node starts with no understanding of its role, the project's rules, or its team's scope.
4. **No pre-flight verification** — if Archon has a bug, or auth is broken, or images are missing, the user discovers this mid-workflow when nodes fail. There's no health check before committing to a workflow run.

Additionally, two known Archon bugs affect workflow reliability:
- **ARM64 subprocess hang** — already patched conditionally in Phase 1
- **Loop completion signal not detected** (Archon bug #1126) — `until:` signals are emitted but Archon reports `max_iterations_reached`, causing dependent nodes to skip

## 2. Design Philosophy

The SDLC framework is an **agentic workforce program management solution**. It coaches project teams through composing, evolving, and managing their delegation structure — not as a one-time setup, but as an ongoing practice throughout the project lifecycle.

A project might choose:
- One large Claude session with 100 agents and 200 skills — no delegation at all
- A central coordinator with 5 agents, delegating to 100 sub-teams of 2-3 agents each
- Five equally-sized specialist teams running in parallel
- Any combination that solves the project's problem
- A structure that changes week to week as the project's needs evolve

**The SDLC provides:**
- **Coaching** — guided Q&A experiences that help project leads think through team composition decisions, understand trade-offs, and evolve teams as the project changes
- **Governance** — a formal way to define, validate, and version-control team compositions with full lifecycle management (create, update, audit, decommission)
- **Tooling** — infrastructure to build team-specific container images from those definitions
- **Visibility** — a fleet-level view of all teams, their composition, staleness, and usage across workflows
- **Validation** — verification that team definitions are consistent, complete, and buildable

**The project decides:**
- How many teams to create
- What goes in each team (SDLC agents, 3rd party plugins, local agents — any source)
- How large or small each team should be
- Which workflows reference which teams
- When to evolve, merge, split, or decommission teams
- Whether to use the same team structure for every task or compose dynamically per task

**Key principle:** For each task, the SDLC supports bringing the best teams, in the best structure, in the best way to deliver the managed outcomes required. The framework enables this — the project lead directs it.

**The American Football model:** The SDLC helps at two levels — roster construction and play calling.

**Roster construction** is the programme-level decision: what teams does this project need across its lifetime? A Python web app with MongoDB and compliance requirements might build a roster of 6-8 teams — planning, development, testing, security review, code review, performance, compliance, database. The roster is built from the full pool of available talent: SDLC agents, 3rd party plugins (MongoDB, BSA, Stripe), and local project specialists. `manage-teams` coaches the project lead through building and evolving this roster over time — adding teams as needs emerge, decommissioning teams that have served their purpose, updating teams as the tech stack evolves.

**Play calling** is the task-level decision: given this specific task, which teams from the roster do we put on the field, and in what formation? Just as a football team doesn't send every player onto the field for every play, a delegated project doesn't use every team for every task:

- Task A (implement a new API endpoint) might use: planning-team → python-dev-team → testing-team → code-review-team
- Task B (security audit before release) might use: security-review-team + compliance-team in parallel, then synthesis-team
- Task C (bulk refactor across 50 files) might use: architecture-team → 5 parallel refactor-teams → merge-team

These are different plays, different formations, different teams — even though they draw from the same roster. The SDLC coaches both: building the right roster for the programme, then calling the right play for each task.

## 3. Three-Tier Docker Image Model

```
┌──────────────────────────────────────────────────┐
│  Tier 1: sdlc-worker:base                        │
│  Claude Code + Archon + Python + Git + Ralph      │
│  No plugins at all. Built once, cached.           │
└──────────────────┬───────────────────────────────┘
                   │ extends
┌──────────────────▼───────────────────────────────┐
│  Tier 2: sdlc-worker:full                        │
│  Base + the project's ENTIRE plugin ecosystem:   │
│  • SDLC plugins (sdlc-core, sdlc-team-security…) │
│  • 3rd party plugins (MongoDB, BSA, Stripe…)     │
│  • Local project agents and skills               │
│  Mirrors the host's Claude Code environment.      │
│  Source layer for team builds. Never run directly.│
└──────────────────┬───────────────────────────────┘
                   │ cherry-picks from
┌──────────────────▼───────────────────────────────┐
│  Tier 3: sdlc-worker:<team-name>                 │
│  Base + only the plugins/agents/skills listed    │
│  in the team manifest — from any source.         │
│  Plus any local project agents/skills.           │
│  This is what Archon actually runs.              │
└──────────────────────────────────────────────────┘
```

### 3.1 Tier 1: Base Image (`sdlc-worker:base`)

The existing Phase 1 Dockerfile, stripped of plugin installation. Contains:
- `node:22-slim` base
- Claude Code CLI
- Archon (from source, with ARM64 conditional patch)
- Python 3, Git, curl, system dependencies
- Ralph CLI
- Non-root user `sdlc` (UID 1001)
- Entrypoint script

Changes rarely. Rebuilt only when Claude Code, Archon, or system dependencies update.

### 3.2 Tier 2: Full Image (`sdlc-worker:full`)

Extends the base image with the project's complete plugin ecosystem. This is a snapshot of the host machine's `~/.claude/plugins/` directory — everything the user has installed locally, regardless of source:

- SDLC plugins installed via the marketplace
- 3rd party plugins (MongoDB, BSA, framework-specific, etc.)
- Local project agents and skills

The full image is a build-time cache. It is never run directly as a container. Its sole purpose is to be the source layer that team images cherry-pick from via `COPY --from=sdlc-worker:full`.

Rebuilt when the local plugin environment changes (new plugin installed, plugin updated, etc.).

### 3.3 Tier 3: Team Images (`sdlc-worker:<team-name>`)

Built from a team manifest (Section 4). The build process:

1. Start from `sdlc-worker:base`
2. `COPY --from=sdlc-worker:full` the plugins listed in the manifest
3. Within each copied plugin, remove agent and skill files NOT listed in the manifest
4. Copy in any `local:` agents and skills from the project directory
5. Generate a team-specific CLAUDE.md (Section 7)
6. Tag as `sdlc-worker:<team-name>`

The resulting image contains exactly what the manifest specifies — no more, no less. An agent or skill not in the manifest is not installed. This is enforcement, not guidance.

## 4. Team Manifest Format

Team manifests are governed artifacts that live in `.archon/teams/` within the project. Each manifest maps a team name to its members.

### 4.1 Schema

```yaml
schema_version: "1.0"
name: <team-name>
description: >
  Human-readable description of the team's purpose and scope.

status: active                   # active | ephemeral | inactive | decommissioned
created: <ISO-8601 date>         # Set automatically on creation
updated: <ISO-8601 date>         # Set automatically on any modification
image_built: <ISO-8601 date>     # Set by deploy-team after successful build

plugins:
  - <plugin-name>              # Copied from full image
  - <plugin-name>              # Can be SDLC, 3rd party, or any installed plugin

agents:
  - <plugin-name>:<agent-name>                    # Specific agent from a plugin
  - local:<relative-path-to-agent.md>             # Project-specific agent

skills:
  - <plugin-name>:<skill-name>                    # Specific skill from a plugin
  - local:<relative-path-to-skill-dir>/SKILL.md   # Project-specific skill

context:
  - <filename>                 # Files loaded into the team's CLAUDE.md
  - <filename>                 # e.g., CONSTITUTION.md, CLAUDE-CONTEXT-security.md
```

**Lifecycle fields:**
- `status` — `active` teams are available for workflows. `inactive` teams are preserved but not built or referenced. `decommissioned` teams are retained for audit history but cannot be reactivated without explicit review.
- `created` / `updated` — timestamps for tracking when the team was established and last modified. Set automatically by the tooling.
- `image_built` — timestamp of the last successful `deploy-team` build. Used for staleness detection: if `updated` is newer than `image_built`, the image is stale and needs rebuilding.

### 4.2 Example: Security Review Team

```yaml
name: security-review-team
description: >
  Specialist team for security-focused code review.
  Runs OWASP Top 10 analysis, threat modelling, and compliance checks.

plugins:
  - sdlc-core
  - sdlc-team-security
  - sdlc-team-common

agents:
  - sdlc-team-security:security-architect
  - sdlc-team-security:compliance-auditor
  - sdlc-team-common:solution-architect
  - local:.archon/agents/project-security-policy.md

skills:
  - sdlc-core:validate
  - sdlc-core:rules

context:
  - CONSTITUTION.md
  - CLAUDE-CONTEXT-security.md
```

### 4.3 Example: Python Development Team

```yaml
name: python-dev-team
description: >
  Implementation team for Python services with MongoDB.
  Handles feature development, testing, and local validation.

plugins:
  - sdlc-core
  - sdlc-lang-python
  - sdlc-team-common
  - mongodb-plugin

agents:
  - sdlc-lang-python:language-python-expert
  - sdlc-team-common:solution-architect
  - sdlc-team-common:performance-engineer
  - mongodb-plugin:mongodb-specialist

skills:
  - sdlc-core:validate
  - sdlc-core:commit
  - sdlc-lang-python:python-lint
  - local:.archon/skills/run-integration-tests/SKILL.md

context:
  - CONSTITUTION.md
  - CLAUDE-CONTEXT-architecture.md
```

### 4.4 Validation Rules

Team manifests are validated by the SDLC:

1. Every agent listed must belong to a plugin that is also listed (no orphan agents)
2. Every skill listed must belong to a plugin that is also listed (no orphan skills)
3. Every plugin listed must exist in the full image (detectable at build time)
4. Every `local:` path must resolve to an existing file in the project
5. `name` must be a valid Docker tag component (lowercase, alphanumeric, hyphens)
6. `context` files must exist in the project root

Validation runs at two points:
- **At manifest creation/edit time** — immediate feedback
- **At image build time** — hard gate, build fails if validation fails

## 5. Tooling: Four Skills

The tooling is split by concern: coaching (manage-teams), building (deploy-team), visibility (teams-status), and the health check (enhanced workflows-setup). The coaching skill is the primary interface for project leads; the others are infrastructure that the coaching skill orchestrates or that can be invoked independently.

### 5.1 `manage-teams` — The Coach (Guided Experience)

```
/sdlc-workflows:manage-teams [--create | --update <team> | --decommission <team> | --review]
```

The primary interface for team lifecycle management. Uses a guided Q&A approach — the same pattern as setup-team — to walk the project lead through decisions.

**5.1.1 Create a New Team (`--create`)**

Guided conversation:

```
Let's create a new delegation team.

What is this team's purpose?
  (a) Code review (security, architecture, quality, etc.)
  (b) Implementation (feature development, bug fixes)
  (c) Testing (test coverage, integration testing)
  (d) Validation (linting, compliance, CI checks)
  (e) Something else — describe it
```

Then, based on the purpose:

```
For a security review team, here's what's available in your
plugin environment:

  Agents:
    sdlc-team-security:security-architect     — OWASP, threat modelling
    sdlc-team-security:compliance-auditor     — regulatory compliance
    sdlc-team-security:data-privacy-officer   — PII/GDPR analysis
    sdlc-team-common:solution-architect       — architectural context
    acme-corp:penetration-tester              — 3rd party, pen testing

  Skills:
    sdlc-core:validate                        — validation pipeline
    sdlc-core:rules                           — compliance rules
    sdlc-team-security:security-audit         — security-specific audit

  Which agents should be on this team?
    (a) All security-related agents (4 agents — recommended)
    (b) Let me pick individually
    (c) Start minimal and I'll add more later
```

Continues through skills, context files, and naming. On completion, writes the manifest to `.archon/teams/`, validates it, and offers to build the image immediately.

**5.1.2 Update an Existing Team (`--update <team>`)**

```
Updating team: security-review-team
  Current: 3 agents, 2 skills (image built 2026-04-10)

  What would you like to change?
    (a) Add agents or skills
    (b) Remove agents or skills
    (c) Change context files
    (d) Show me what's available that isn't on this team
    (e) Review the full manifest
```

Option (d) is the key coaching moment — it shows the project lead what they're missing based on the current plugin environment. If a new plugin has been installed since the team was last updated, it surfaces here.

After changes, updates the manifest's `updated` timestamp and warns if the image is now stale:

```
Manifest updated. The team image was built on 2026-04-10 but
the manifest has changed. Rebuild now?
  (a) Yes — run deploy-team
  (b) Later — I'll rebuild when I'm ready
```

**5.1.3 Decommission a Team (`--decommission <team>`)**

```
Decommissioning team: legacy-review-team

  This team is referenced by 1 workflow:
    sdlc-parallel-review.yaml (node: legacy-check)

  Decommissioning will:
    - Set the manifest status to 'decommissioned'
    - Remove the Docker image
    - NOT delete the manifest file (retained for audit)

  You will need to update the workflow to remove or replace
  the reference.

  Proceed?
    (a) Yes — decommission and show me the workflow references to fix
    (b) No — keep the team active
```

**5.1.4 Review All Teams (`--review`)**

Triggers a coaching review of the entire delegation workforce:

```
Delegation workforce review:

  Your project has 4 active teams and 8 workflows.

  Observations:
    1. security-review-team — image is stale (manifest updated
       3 days after last build)
    2. dev-team-python — mongodb-plugin was updated since last
       build (new agents available)
    3. test-coverage-team — not referenced by any workflow.
       Consider decommissioning or assigning to a workflow.
    4. No team covers performance review, but you have
       sdlc-team-common:performance-engineer available.

  Would you like to address any of these?
    (a) Rebuild stale images
    (b) Update dev-team-python with new mongodb agents
    (c) Decommission unused test-coverage-team
    (d) Create a performance review team
    (e) Skip for now
```

This is the ongoing coaching loop — not a one-time recommendation, but a periodic health check on the delegation workforce that surfaces what's changed and what might need attention.

### 5.2 `deploy-team` — The Builder (Infrastructure, No Opinion)

```
/sdlc-workflows:deploy-team --name <team-name> [--image <registry/path>]
```

Pure machinery. Reads a team manifest, builds the image. Can be invoked directly by users who know exactly what they want, or orchestrated by `manage-teams` after a guided session.

**Process:**

1. Read `.archon/teams/<team-name>.yaml`
2. Check manifest `status` is `active` (refuse to build `inactive` or `decommissioned` teams)
3. Validate the manifest (Section 4.4 rules)
4. Verify `sdlc-worker:base` and `sdlc-worker:full` images exist (prompt to build if not)
5. Generate a Dockerfile:
   ```dockerfile
   FROM sdlc-worker:full AS plugin-source
   FROM sdlc-worker:base

   # Copy listed plugins
   COPY --from=plugin-source /home/sdlc/.claude/plugins/sdlc-core \
        /home/sdlc/.claude/plugins/sdlc-core
   COPY --from=plugin-source /home/sdlc/.claude/plugins/sdlc-team-security \
        /home/sdlc/.claude/plugins/sdlc-team-security

   # Copy only listed agents (additive, no prune)
   COPY --from=plugin-source /path/to/sdlc-team-security/agents/security-architect.md \
        /home/sdlc/.claude/plugins/.../agents/security-architect.md
   COPY --from=plugin-source /path/to/sdlc-team-security/agents/compliance-auditor.md \
        /home/sdlc/.claude/plugins/.../agents/compliance-auditor.md

   # Make plugins read-only (blocks runtime plugin installation)
   RUN chmod -R a-w /home/sdlc/.claude/plugins/

   # Copy local agents and skills
   COPY .archon/agents/project-security-policy.md \
        /home/sdlc/.claude/agents/project-security-policy.md

   # Generated team CLAUDE.md
   COPY .archon/teams/.generated/security-review-team-CLAUDE.md \
        /workspace/CLAUDE.md
   ```
6. Build and tag as `sdlc-worker:<team-name>` (or `--image` override)
7. Update `image_built` timestamp in the manifest
8. Report: image name, size, agent count, skill count

**Optional `--image` flag** allows pushing to a registry for cloud/CI use:
```
/sdlc-workflows:deploy-team --name security-review-team --image ghcr.io/myorg/sdlc-worker:security-review-team
```

### 5.3 `teams-status` — The Fleet View (Visibility)

```
/sdlc-workflows:teams-status [--team <name>]
```

Provides workforce-level visibility across all delegation teams.

**Fleet view (no arguments):**

```
Delegation workforce: 4 teams, 3 workflows

  Team                        Status   Agents  Skills  Image     Workflows
  ─────────────────────────── ──────── ─────── ─────── ───────── ─────────
  security-review-team        active   3       2       current   2
  architecture-review-team    active   2       2       stale     1
  dev-team-python             active   4       6       current   3
  legacy-review-team          inactive 2       1       none      0

  Issues:
    ! architecture-review-team image is stale (manifest updated 2026-04-12,
      image built 2026-04-10)
    ! legacy-review-team has no image and is inactive — consider decommissioning

  Plugin environment changes since last full image build:
    + mongodb-plugin updated (v1.2.0 → v1.3.0, 1 new agent)
    + sdlc-team-security updated (v1.1.0 → v1.2.0, new skill: threat-model)

  Run /sdlc-workflows:manage-teams --review for guided resolution.
```

**Single team detail (`--team <name>`):**

```
Team: security-review-team
  Status:      active
  Created:     2026-04-08
  Updated:     2026-04-12
  Image built: 2026-04-12 (current)

  Plugins (3):
    sdlc-core, sdlc-team-security, sdlc-team-common

  Agents (3):
    sdlc-team-security:security-architect
    sdlc-team-security:compliance-auditor
    sdlc-team-common:solution-architect

  Skills (2):
    sdlc-core:validate
    sdlc-core:rules

  Context:
    CONSTITUTION.md, CLAUDE-CONTEXT-security.md

  Used by workflows:
    sdlc-parallel-review.yaml → node: security-review
    sdlc-commissioned-pipeline.yaml → node: security-gate

  Available but not included (from installed plugins):
    sdlc-team-security:data-privacy-officer
    sdlc-team-security:enforcement-strategy-advisor
    sdlc-team-security:compliance-report-generator
```

The "available but not included" line is coaching — it reminds the project lead what else exists without pushing them to add it.

### 5.4 Supporting Commands

**Build base and full images:**

```bash
# Build base image (rarely needed — cached)
docker build -t sdlc-worker:base -f plugins/sdlc-workflows/docker/Dockerfile.base .

# Build full image (mirrors local plugin environment)
docker build -t sdlc-worker:full -f plugins/sdlc-workflows/docker/Dockerfile.full .
```

These are prerequisites for `deploy-team`. The skill checks for their existence and prompts the user to build them if missing.

## 6. Health Check

Enhanced `workflows-setup` skill. Before a project attempts any delegated workflow, verify the infrastructure works.

### 6.1 Checks

| Check | Method | Pass | Fail |
|-------|--------|------|------|
| Archon installed | `archon --version` | Version reported | Not found — offer install |
| Archon can start | Start and stop a minimal workflow | Clean exit | Error — report details |
| Claude Code auth | `claude -p "say ok"` inside container | Response received | Auth failure — point to login |
| ARM64 patch status | `grep 'executable:' claude.ts` | Fix present (upstream or our patch) | Neither — apply patch |
| Loop signal bug | Run minimal loop workflow with known signal | Signal detected | Bug present — activate workaround |
| Team images exist | `docker images` for each team in workflows | All present | Missing — list what needs building |
| Team image contents | Inspect image for expected agents/skills | All declared members present | Mismatch — report discrepancy |

### 6.2 Report Format

```
Delegation health check:
  Archon:           OK (v0.4.2)
  Auth:             OK (Max subscription)
  ARM64 patch:      applied (upstream fix not yet merged)
  Loop workaround:  active (Archon #1126 not yet fixed)
  Team images:      3/3 present
    sdlc-worker:security-review-team   OK (3 agents, 2 skills)
    sdlc-worker:dev-team-python        OK (4 agents, 6 skills)
    sdlc-worker:validation-team        OK (1 agent, 2 skills)

  Ready for delegation.
```

### 6.3 When to Run

- Automatically as part of `workflows-setup` (first-time setup)
- On demand via `/sdlc-workflows:workflows-setup --health-check`
- Automatically before the first `workflows-run` in a session (cached result, re-run if stale)

## 7. Persistent Team Context

Each team image gets a generated CLAUDE.md that establishes the team's identity and scope. Generated by `deploy-team` from the manifest.

### 7.1 Generated CLAUDE.md Structure

```markdown
# Team: <team-name>

<description from manifest>

## Role

You are operating as part of the **<team-name>** delegation team.
Your available specialists and capabilities are listed below.
Stay within your team's scope — do not attempt to use agents
or skills not listed here.

## Available Agents

- <agent-name> — <description from agent file>
- <agent-name> — <description from agent file>

## Available Skills

- <skill-name> — <description from skill file>
- <skill-name> — <description from skill file>

## Project Context

<contents of context files listed in manifest, or instructions to load them>

## Constraints

- Focus on your team's domain. Do not produce recommendations
  outside your scope.
- Use the agents and skills listed above. They are your team.
- Follow the project rules in CONSTITUTION.md.
```

### 7.2 Context Inheritance

The generated CLAUDE.md is baked into the team image at `/workspace/CLAUDE.md`. When Archon starts a node with `context: fresh`, the Claude Code session loads this CLAUDE.md automatically — the team identity survives the fresh context reset.

If the project has its own CLAUDE.md, the generated team CLAUDE.md is concatenated below the project's CLAUDE.md into a single file. The project's base rules appear first and take precedence; the team context section follows, adding role-specific framing. This concatenation happens at image build time in `deploy-team`, not at runtime.

## 8. Loop Signal Workaround

Conditional workaround for Archon bug #1126 (loop completion signal not detected). Follows the same pattern as the ARM64 fix: detect, patch if needed, self-deactivate when upstream fixes.

### 8.1 The Bug

Archon's `until:` directive checks for a completion signal in the node's output. The signal IS emitted by the Claude Code session, but Archon's signal detection fails to match it. Result: loops always run to `max_iterations` and report `max_iterations_reached`, causing dependent nodes with strict `trigger_rule` to skip.

### 8.2 The Workaround

A wrapper script injected into the entrypoint of team images that use loop workflows:

1. **Detection** — at container start, run a minimal loop test (single iteration with a known signal). If Archon detects the signal correctly, the workaround is unnecessary — skip it.
2. **If bug is present** — after each loop iteration:
   - Scan the node's output directory for the completion signal pattern
   - If found, write a sentinel file (`.archon-loop-complete`) and exit the loop cleanly
   - The sentinel file acts as the completion signal that Archon's native detection missed
3. **Self-deactivating** — the detection step runs on every container start. When Archon ships the fix, the detection test passes and the workaround stops applying automatically.

### 8.3 Workflow Compatibility

Workflows that use loops (`sdlc-feature-development.yaml` with its implement-until-tests-pass loop) work correctly whether the bug is present or not:
- Bug present: workaround catches the signal, exits cleanly, dependent nodes proceed
- Bug absent: Archon catches the signal natively, workaround detection skips it

Workflows without loops (`sdlc-parallel-review.yaml`, `sdlc-bulk-refactor.yaml`) are unaffected — the workaround only activates for loop nodes.

## 9. Workflow Integration

### 9.1 Team References in Workflow YAMLs

Workflow nodes declare which team image they run on:

```yaml
nodes:
  - id: security-review
    command: sdlc-security-review
    image: sdlc-worker:security-review-team
    context: fresh
    effort: high

  - id: implement
    command: sdlc-implement
    image: sdlc-worker:python-dev-team
    context: fresh
    loop:
      until: "ALL_TESTS_PASSING"
      max_iterations: 5
```

### 9.2 Validation

The SDLC validates workflow-to-team references:

1. Every `image:` reference in a workflow YAML must correspond to a team manifest in `.archon/teams/`
2. Every command referenced by a node must have its skill available in the team image (the skill is listed in the team manifest)
3. Health check (Section 6) verifies images are actually built before workflow execution

### 9.3 Archon Per-Node Image Support — SDLC Patch

Archon does not currently support per-node Docker image selection. Its node schema (`dag-node.ts`) has no `image:` field, and its isolation system only implements the `worktree` provider — `container` is declared in the type system but has zero implementation. Without per-node images, all nodes in a workflow share the same environment and team enforcement between nodes is impossible.

**Our approach: patch Archon at build time, contribute upstream in parallel.** This is the same proven pattern used for the ARM64 workaround — a conditional local patch that self-deactivates when upstream merges the fix.

**The patch has three components:**

1. **ContainerProvider implementation** (new file, purely additive)
   - `packages/isolation/src/providers/container.ts` implementing `IIsolationProvider`
   - Wraps Docker CLI: `docker run` (create), `docker rm` (destroy), `docker inspect` (get/healthCheck), `docker ps --filter` (list)
   - Supports per-node image selection via the node's `image:` field
   - COPY'd into Archon source during Docker build — no modification of existing files

2. **Node schema extension** (small patch to existing file)
   - Adds optional `image?: string` field to the node schema in `dag-node.ts`
   - Conditional: checks if the field already exists before patching
   - When present, the executor routes that node to ContainerProvider instead of WorktreeProvider

3. **Executor wiring** (small patch to existing file)
   - Extends the DAG executor to check for `image:` on each node
   - If present and ContainerProvider is available, spawn the node in a Docker container with the specified image
   - If absent, fall back to the existing worktree isolation (no behaviour change for workflows that don't use images)

**Conditional application:**
```dockerfile
# Per-node image support — conditional, self-deactivating
# Adds ContainerProvider + image field to Archon's node schema.
# When Archon implements this natively, the checks detect the
# existing implementation and skip the patches.

# 1. ContainerProvider (additive — only if not already present)
RUN if [ ! -f /opt/archon/packages/isolation/src/providers/container.ts ]; then \
      echo "Adding ContainerProvider patch"; \
      cp /opt/sdlc-patches/container-provider.ts \
         /opt/archon/packages/isolation/src/providers/container.ts; \
    fi

# 2. Node schema image field (conditional — only if not already present)
RUN if ! grep -q 'image\?:' /opt/archon/packages/workflows/src/schemas/dag-node.ts; then \
      echo "Adding image field to node schema"; \
      <patch command>; \
    fi

# 3. Executor container routing (conditional — only if not already present)
RUN if ! grep -q 'ContainerProvider' /opt/archon/packages/workflows/src/dag-executor.ts; then \
      echo "Adding container routing to executor"; \
      <patch command>; \
    fi
```

**Upstream contribution in parallel:**
- Submit the same ContainerProvider implementation + schema extension + executor wiring as a PR to `coleam00/Archon`
- The PR benefits the Archon community (container isolation is a planned feature — the type is already declared)
- When merged, our build-time patches detect the native implementation and become no-ops

**This gives us per-node team enforcement from day one** without waiting for an upstream timeline we don't control.

## 10. Per-Task Team and Workflow Selection

Every delegated task starts with a play-calling step: **given this task, what teams and workflow structure will deliver the best outcome?** This is not optional — it's the core of the agentic workforce management model. A project that always uses the same teams in the same arrangement for every task is under-utilising its roster.

### 10.1 The Play-Calling Flow

When a new task arrives in a delegated project, the SDLC coaches the project lead through team selection:

```
New task: "Add OAuth2 authentication to the API"

Based on your roster and this task, here's a recommended formation:

  Workflow: sdlc-feature-development (sequential pipeline)

  ┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
  │ planning-team│──▶ │ python-dev-team   │──▶ │ testing-team │
  │ (architect,  │    │ (python-expert,   │    │ (test-expert,│
  │  security)   │    │  security-arch)   │    │  coverage)   │
  └─────────────┘    └──────────────────┘    └──────┬───────┘
                                                     │
                     ┌──────────────────┐    ┌──────▼───────┐
                     │ security-review  │◀── │ code-review  │
                     │ (security-arch,  │    │ (reviewer,   │
                     │  compliance)     │    │  quality)    │
                     └──────────────────┘    └──────────────┘

  This task involves authentication, so I've included the
  security-architect on both the planning team and the
  security review team.

  (a) Accept this formation
  (b) Modify — change teams or workflow structure
  (c) Show me alternative formations
  (d) I'll compose this myself
```

### 10.2 What the Play-Calling Step Considers

The recommendation engine analyses:

| Factor | Example | Impact on Formation |
|--------|---------|---------------------|
| **Task description** | "Add OAuth2 auth" | Security agents included in more teams than usual |
| **Available roster** | 6 standing teams, 2 ephemeral | Only propose teams that exist and are active |
| **Workflow patterns** | 4 workflow templates available | Select the template that fits the task shape |
| **Recent history** | Last 3 tasks needed database-architect | Surface if this task might too |
| **Team staleness** | dev-team image built 2 weeks ago | Warn before selecting a stale team |
| **Plugin updates** | security plugin updated since last build | Flag that security teams may benefit from rebuild |

### 10.3 Task Plans as Governed Artifacts

Each task's formation — the selected teams and workflow — is recorded as a **task plan** in `.archon/tasks/`:

```yaml
task: add-oauth2-authentication
created: 2026-04-13
workflow: sdlc-feature-development
formation:
  - node: plan
    team: planning-team
  - node: implement
    team: python-dev-team
    team_extend:
      agents:
        - sdlc-team-security:security-architect
  - node: test
    team: testing-team
  - node: review
    team: code-review-team
  - node: security-review
    team: security-review-team
```

This provides:
- **Traceability** — which teams worked on which task
- **Learning** — patterns emerge over time ("security tasks always add the security-architect to the dev team — should it be a standing member?")
- **Reproducibility** — re-run the same formation if the task needs rework
- **Coaching data** — `manage-teams --review` can analyse task plans to suggest roster optimisations

### 10.4 Integration with manage-teams

The play-calling step is a mode of `manage-teams`:

```
/sdlc-workflows:manage-teams --plan-task "Add OAuth2 authentication to the API"
```

It can also be triggered automatically when a new delegated workflow run is requested, before the workflow actually starts. The project lead always reviews and approves the formation before execution begins.

For projects that prefer to compose manually, the play-calling step can be skipped — the project lead writes the task plan YAML directly and runs the workflow with explicit team assignments.

## 11. Dynamic Team Composition

Team manifests define standing teams — persistent compositions built into Docker images. But projects also need the ability to compose dynamically for specific tasks without permanently changing a team's manifest.

### 11.1 Workflow-Level Team Overrides

A workflow YAML can extend a standing team for a specific run:

```yaml
nodes:
  - id: implement
    command: sdlc-implement
    image: sdlc-worker:dev-team-python
    context: fresh
    team_extend:
      agents:
        - sdlc-team-common:database-architect    # Add for this node only
      skills:
        - local:.archon/skills/migrate-db/SKILL.md
```

The `team_extend` block does not modify the team manifest or the team image. Instead, at workflow execution time, the extended agents/skills are injected into the node's session via the command prompt context. This is a soft extension — the base image enforces the standing team, and the override adds to it for this run only.

**Constraints:**
- `team_extend` can only ADD to the team, not remove. The standing team is the minimum; overrides expand it.
- Extended agents/skills must exist in the full image (validated at workflow execution time).
- Overrides are logged so `teams-status` can report: "dev-team-python was extended with database-architect in 3 of the last 5 runs — consider adding it to the standing team."

### 11.2 One-Off Team Composition

For tasks that don't fit any standing team, a project lead can compose a one-off team directly from the coaching interface:

```
/sdlc-workflows:manage-teams --create --ephemeral
```

Ephemeral teams follow the same manifest format but are tagged `status: ephemeral`. They are:
- Built as a Docker image like any team
- Used for one or a few workflow runs
- Automatically flagged by `teams-status` if they persist beyond a configurable age
- Candidates for promotion to standing teams if used repeatedly

This supports the pattern where a project lead says "for this particular feature, I need a team that doesn't exist yet" without committing to a permanent team structure.

### 11.3 Coaching Signals

The `manage-teams --review` coaching loop watches for patterns that suggest team evolution:

| Signal | Coaching Response |
|--------|-------------------|
| Same `team_extend` override used 3+ times | "This agent keeps being added — consider promoting to the standing team" |
| Ephemeral team used in 3+ workflow runs | "This team keeps being needed — promote to a standing team?" |
| Standing team not used in 30+ days | "This team hasn't been used recently — still needed, or decommission?" |
| Plugin updated with new agents/skills | "New capabilities available — review which teams should get them" |
| Workflow node fails consistently | "This node keeps failing — review if the team has the right specialists" |

These signals surface in `manage-teams --review` and `teams-status`. They are advisory — the project lead decides whether to act.

## 12. Team Lifecycle

Teams are not static. They are created, evolved, and retired as the project's needs change. The SDLC provides governance for each lifecycle stage.

### 12.1 Lifecycle States

```
                    ┌───────────┐
         create ──▶ │  active   │ ◀── reactivate
                    └─────┬─────┘
                          │ ▲
                 deactivate  promote
                          │ │
   create ──▶ ┌───────────┤ │
  --ephemeral │           │ │
              ▼           ▼ │
        ┌───────────┐ ┌────▼────┐
        │ ephemeral │ │ inactive│
        └─────┬─────┘ └────┬────┘
              │             │
              │      decommission
              │             │
              └─────────────▼
                    ┌───────────────┐
                    │ decommissioned│
                    └───────────────┘
```

- **active** — the team has a manifest, can be built into an image, and can be referenced by workflows
- **ephemeral** — a temporary team created for a specific task or short-lived need. Functions like `active` but is automatically flagged by `teams-status` if it persists beyond a configurable age. Can be promoted to `active` (standing team) or decommissioned.
- **inactive** — the team's manifest is preserved but no image is maintained. Workflows referencing an inactive team fail validation with a clear message. Used for teams that are temporarily stood down (e.g., between project phases).
- **decommissioned** — the team's manifest is retained for audit history but marked as terminal. Cannot be reactivated without explicit review (the `manage-teams` coaching flow asks why and whether a new team should be created instead). The Docker image is removed.

### 12.2 Lifecycle Operations

| Operation | Trigger | What Happens |
|-----------|---------|--------------|
| **Create** | `manage-teams --create` or manual manifest creation | New manifest written, validated, optional immediate image build |
| **Update** | `manage-teams --update <team>` or manual manifest edit | Manifest modified, `updated` timestamp set, image marked stale |
| **Build** | `deploy-team --name <team>` | Image built from manifest, `image_built` timestamp set |
| **Deactivate** | `manage-teams --deactivate <team>` | Status set to `inactive`, image optionally removed, workflow references flagged |
| **Reactivate** | `manage-teams --reactivate <team>` | Status set back to `active`, coaching review of whether the manifest is still appropriate |
| **Decommission** | `manage-teams --decommission <team>` | Status set to `decommissioned`, image removed, workflow references must be resolved |
| **Review** | `manage-teams --review` or periodic prompt | Full workforce assessment with coaching signals |

### 12.3 Version History

Team manifests are version-controlled via git (they live in `.archon/teams/`). This provides:
- Full history of team composition changes via `git log`
- Ability to diff what changed between two versions of a team
- Rollback if a team change causes workflow failures
- Audit trail for compliance: who changed what team and when

No custom versioning system needed — git is the version control mechanism.

## 13. Review Findings Incorporated

This spec was reviewed by five specialists (solution architect, DevOps specialist, security architect, agile coach, lead critical review). The following changes address Priority 0 and Priority 1 findings. Full reviews are in `reviews/2026-04-13-*.md`.

### 13.1 Archon Patch for Per-Node Images (was a critical gap)

Section 9.3 now specifies a build-time SDLC patch (same pattern as ARM64 fix) that implements ContainerProvider + per-node image support. This eliminates the upstream dependency that all reviewers flagged as the biggest architectural risk.

### 13.2 Plugin Path Resolution (was a critical blocker)

The DevOps review found that installed plugins live at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, not the flat structure the spec originally assumed. The `deploy-team` build process must parse `installed_plugins.json` to resolve plugin names to actual install paths. This is a P2-2 implementation detail, not an architecture change.

### 13.3 Credential Volume Scoping (was a critical blocker)

The credential volume mount (`/home/sdlc/.claude`) masks baked-in plugins because they live under the same directory. The mount must be scoped to specific auth files only (e.g., `~/.claude/credentials.json`), not the entire `.claude/` tree. This is a P2-0 deliverable.

### 13.4 Additive Copy Over Prune (security + DevOps consensus)

Both the solution architect and DevOps specialist recommended replacing the "copy plugin, prune unlisted files" approach with additive copy-only: copy only the specific agent and skill files listed in the manifest. This is deterministic, fails explicitly on missing files, and has no silent failure mode. Section 3.3 and 5.2 are updated accordingly.

### 13.5 Security Hardening (security review)

The following hardening measures are incorporated into the base image and team image builds:
- `chmod -R a-w /home/sdlc/.claude/plugins/` after build — blocks runtime plugin installation (CVSS ~7.1 bypass vector)
- Credential volume mounted read-only
- Manifest descriptions sanitised before CLAUDE.md generation (prompt injection mitigation)
- `.archon/teams/` mounted read-only in workflow containers

### 13.6 Schema Version (solution architect + lead review)

`schema_version: "1.0"` added to the manifest format (Section 4.1) for forward compatibility.

### 13.7 Phase 2 / Phase 3 Split (agile coach + lead review consensus)

The agile coach and lead reviews both recommended splitting the spec's scope. Phase 2 delivers infrastructure (manifests, images, enforcement, health check). Phase 3 delivers workforce management (coaching UX, fleet visibility, dynamic composition, play-calling). The sub-feature decomposition below reflects this split.

## 14. Sub-Feature Decomposition

### Phase 2: Team Infrastructure (this phase)

| Sub-feature | Scope | Depends On | Deliverable |
|---|---|---|---|
| **P2-0: Dockerfile refactor — base + full split** | Split existing Dockerfile into Dockerfile.base and Dockerfile.full. Base has no plugins. Full extends base with plugin copy from host. Scope credential volume to auth files only (not all of `~/.claude/`). | Phase 1 complete | Two Dockerfiles, build scripts, credential mount fix |
| **P2-1: Team manifest schema + validation** | Define YAML schema with `schema_version: "1.0"`, lifecycle fields (status, created, updated, image_built), write manifest validator using `installed_plugins.json` for path resolution, add to validation pipeline | None | Schema doc, validator script, test manifests |
| **P2-2: deploy-team skill** | Reads manifest, resolves plugin paths via `installed_plugins.json`, generates Dockerfile with additive copy-only (no prune), makes plugins read-only (`chmod -R a-w`), sanitises descriptions for CLAUDE.md, builds team image, updates image_built timestamp | P2-0, P2-1 | Skill YAML, Dockerfile generator, additive copy logic |
| **P2-3: Team CLAUDE.md generator** | Generates team-specific CLAUDE.md from manifest with sanitised descriptions, bakes into image, concatenated below project CLAUDE.md | P2-1 | Generator script, template, sanitisation rules |
| **P2-4: Archon ContainerProvider + per-node image patch** | Implement ContainerProvider (Docker wrapper), add `image:` field to node schema, wire executor routing. Applied as conditional build-time patches. Submit upstream PR to Archon in parallel. | P2-0 | container.ts, schema patch, executor patch, upstream PR |
| **P2-5: Health check enhancement** | Archon connectivity, auth, bug detection, ContainerProvider verification, team image verification | P2-0, P2-4 | Enhanced workflows-setup skill |
| **P2-6: Loop signal workaround** | Detection, conditional wrapper, self-deactivating patch | Phase 1 entrypoint | Wrapper script, detection test |
| **P2-7: Workflow-team validation** | Validate image references in workflow YAMLs against team manifests | P2-1, P2-2 | Validator addition |

### Phase 3: Workforce Management (next phase — designed here, built later)

| Sub-feature | Scope | Depends On | Deliverable |
|---|---|---|---|
| **P3-0: manage-teams skill** | Guided Q&A coaching for team lifecycle: create, update, decommission, review. Plugin inventory, available-agent discovery, staleness detection, coaching signals. | Phase 2 complete | Skill YAML, coaching flow, lifecycle operations |
| **P3-1: teams-status skill** | Fleet-level visibility: team roster, staleness detection, usage mapping, plugin update detection, available-but-not-included reporting | Phase 2 complete | Skill YAML, status reporting |
| **P3-2: Dynamic composition** | team_extend in workflow YAMLs, ephemeral team support, override logging for coaching signals | P3-0, P3-1 | Workflow schema extension, override mechanism |
| **P3-3: Per-task play-calling** | `manage-teams --plan-task` coaching flow, task plan schema, formation recommender, workflows-run pre-flight integration | P3-0, P3-2 | Play-calling skill, task plan schema |

**Phase 2 execution order:**

```
P2-0 (Dockerfile split) ──────┐
                               ├── P2-2 (deploy-team) ── P2-7 (workflow-team validation)
P2-1 (manifest schema) ───────┤
                               └── P2-3 (CLAUDE.md gen)

P2-0 ── P2-4 (Archon patch) ── P2-5 (health check)

Phase 1 entrypoint ── P2-6 (loop workaround)
```

**Suggested implementation waves:**

- **Wave 1** (foundations): P2-0, P2-1, P2-6 — can all run in parallel
- **Wave 2** (core build + Archon patch): P2-2, P2-3, P2-4 — depend on Wave 1. P2-4 can run in parallel with P2-2/P2-3.
- **Wave 3** (verification): P2-5, P2-7 — depend on Wave 2

## 15. What Phase 2 Does NOT Do

Explicitly deferred:

- **Prescribe team structures** — the framework enables, the project decides
- **Coaching UX for team lifecycle** — Phase 3 (`manage-teams` skill with guided Q&A)
- **Fleet visibility** — Phase 3 (`teams-status` skill)
- **Dynamic composition** — Phase 3 (`team_extend`, ephemeral teams, coaching signals)
- **Per-task play-calling** — Phase 3 (formation selection per task)
- **Cloud registry push automation** — `--image` flag supports it, but CI/CD integration is Phase 4
- **Workflow authoring** — Phase 3 (how to create workflows that use teams effectively)
- **Git coordination between nodes** — Phase 3 (branch-per-node, merge strategies)
- **Cost tracking** — Phase 4
- **Automated team rebalancing** — coaching signals are advisory; automatic restructuring is future work

## 16. Success Metrics

| Metric | Target | Measured When |
|---|---|---|
| Team manifest validates correctly | Schema validation passes for all test manifests including lifecycle fields and schema_version | P2-1 complete |
| Plugin paths resolve correctly | Validator resolves manifest plugin names to real install paths via `installed_plugins.json` | P2-1 complete |
| Team image builds from manifest | `deploy-team` produces a runnable image using additive copy-only, updates image_built | P2-2 complete |
| Team image contains only listed members | Agents/skills not in manifest are absent from image; plugins directory is read-only | P2-2 complete |
| Generated CLAUDE.md loads correctly | Team identity survives `fresh_context` reset; descriptions are sanitised | P2-3 complete |
| Archon ContainerProvider works | Archon can spawn a Claude Code session in a Docker container via the SDLC patch | P2-4 complete |
| Per-node image selection works | Different nodes in a workflow run different team images | P2-4 complete |
| Archon patch is conditional | Patch detection skips application when feature already exists in Archon | P2-4 complete |
| Health check catches known bugs | ARM64, loop signal, ContainerProvider status all detected and reported | P2-5 complete |
| Loop workaround self-deactivates | Workaround skips when bug is absent | P2-6 complete |
| Workflow-team validation catches errors | Missing image reference flagged before workflow run | P2-7 complete |
| Credential volume is scoped | Auth files only, mounted read-only; plugins not masked | P2-0 complete |
| End-to-end: manifest → image → per-node workflow | A workflow runs with different team images per node, agents enforced per team | All sub-features complete |

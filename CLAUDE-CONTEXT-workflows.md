# CLAUDE-CONTEXT-workflows.md

Containerised Claude Code workers reference. Load this when authoring workflows, creating teams, or debugging container execution.

## Workflow YAML Schema

Workflows live in `.archon/workflows/` and define a DAG of nodes that Archon executes.

```yaml
name: <workflow-name>           # Required. Archon resolves workflows by this field, not filename.
description: |                  # Required. Multi-line description of purpose, inputs, outputs.
  What this workflow does.
provider: claude                # Required. Always "claude" for Claude Code workflows.

nodes:                          # Required. List of execution nodes.
  - id: <node-id>              # Required. Unique within workflow. Used in depends_on references.
    command: <command-name>     # Required (unless prompt: is set). Name of .md file in .archon/commands/ (without .md extension).
    image: <docker-image>       # Optional. Team Docker image (e.g., sdlc-worker:dev-team). If set, node runs inside this container. If omitted, runs on host.
    depends_on: [<node-id>, ...]  # Optional. Nodes that must complete before this one starts. Omit for root nodes.
    trigger_rule: all_success | one_success  # Optional. Default: all_success. When to trigger after dependencies complete.
    context: fresh              # Optional. "fresh" starts with clean context. Default behaviour.
    model: <model-id>          # Optional. Override the Claude model for this node (e.g., claude-opus-4-6[1m]).
    effort: high | medium | low # Optional. Hint for token budget allocation.
    timeout: <milliseconds>      # Optional. Per-node timeout in MILLISECONDS. Default: 120000 (2 min).
                                # Use: 600000 (10 min) for reviews, 1800000 (30 min) for implementation.
                                # Also passed as CLAUDE_TIMEOUT (seconds) env var to container.
    loop:                       # Optional. Repeat until a signal is detected.
      until: <signal-string>    # String to grep for in output to stop the loop.
      max_iterations: <int>     # Maximum iterations before forced stop. Default: 5.
      fresh_context: true       # Whether to restart context each iteration.
      prompt: <text>            # Optional. Inline prompt used by every iteration
                                # (single-image loops only).
      stages:                   # Optional. Multi-stage loop — each iteration runs
        - id: <stage-id>        # every stage in sequence inside ONE loop node.
          image: <docker-image> # Per-stage image (REQUIRED when stages: is used —
          command: <cmd-name>   # the node-level image: is ignored).
          prompt: <text>        # Each stage: command OR prompt (same rules as nodes).
          timeout: <milliseconds> # Optional. Falls back to the node's timeout.
          model: <model-id>     # Optional. Falls back to the node's model.
        # (see the "Cycles" section below for the full pattern)
    prompt: |                   # Optional. Inline prompt instead of command file. Use command: for anything non-trivial.
      Inline prompt text.
    team_extend:                # Optional. List of qualified agent names to add to the team for this node.
      - sdlc-team-security:security-architect
      - sdlc-team-common:api-architect
```

> **Schema strictness:** Archon rejects unknown fields on nodes.
> Adding non-standard fields (e.g. `name:`, `label:`) causes the
> workflow to fail validation and breaks the web UI graph renderer.
> Only use the fields listed above.

> **`team_extend` status in v1:** the field is schema-validated (entries
> must be qualified `plugin:agent` references that resolve to installed
> plugins), but the **runtime injection mechanism is deferred to a
> future phase**. In v1 the field is a **silent no-op at runtime** —
> the team container is built from the team manifest only; extended
> agents are *not* actually made available to Claude inside the
> container. The validator logs a warning when the field is non-empty
> so authors discover this at validation time, not by surprise at
> runtime. Use team_extend today only as a forward-compatible
> declaration of intent.

### DAG Rules

- Nodes with no `depends_on` run first (root layer).
- Nodes sharing the same dependencies and no dependency on each other run in parallel.
- `trigger_rule: all_success` (default) requires ALL dependencies to succeed.
- `trigger_rule: one_success` requires at least ONE dependency to succeed.
- Archon resolves workflows by the `name:` field, not the filename. The filename can differ from the name.

### Parallel Execution Semantics (v1)

**Contract — shared workspace, last-writer-wins.** When two or more nodes
share a parent via `depends_on` (a *fan-out*), Archon may execute them
concurrently. In v1 those parallel nodes **share the same host workspace
mount** — the same directory is bind-mounted into every container:

```
-v "<host-workspace>:/workspace"   # same <host-workspace> for every branch
```

Consequences:

- Writes to the **same path** from parallel branches race; the last
  writer wins and intervening state may be lost.
- Writes to **disjoint paths** (e.g. each branch writes
  `review-<id>.md`) are safe.
- Reads of files created *before* the fan-out are always safe.

**Preprocessor behaviour.** `preprocess_workflow.py` detects fan-out
topologies and emits a structured warning log (one per parent with
2+ children). The warning cites this section so workflow authors get
feedback at preprocess time, not after a race manifests at runtime.

#### The git-index single-writer rule

The workspace is a git repository. Its `.git/index` is a
**single-writer resource**: concurrent `git add` / `git commit` /
`git push` from parallel branches race on `.git/index.lock` and the
loser's work is silently dropped. This is not a theoretical hazard —
it surfaced during Phase A bring-up (fork-a and fork-b both trying to
commit, fork-b's commit lost to `fatal: Unable to create '.git/index.lock'`).

**Rule.** Parallel branches MUST NOT run `git add`, `git commit`, or
`git push`. Only nodes that run alone (the initial node, fan-in
nodes, sequential chain nodes) may write to the git index.

**Enforcement.** `preprocess_workflow.py` refuses to emit bash for any
workflow whose parallel-branch command brief contains
`git commit` / `git add` / `git push`. The error
(`ParallelGitWriteError`, exit code 3) lists the offending nodes and
points at this section. This is a build-time failure, not a runtime
surprise.

#### Per-node subdirectory pattern (the documented fix)

When you need parallel branches to produce artefacts that a later
node consumes, use **per-node subdirectories** plus a **single
fan-in commit**:

```yaml
nodes:
  - id: review-a
    depends_on: [plan]
    command: sdlc-review-a         # writes /workspace/reports/review-a/review.md
                                   # no git add/commit

  - id: review-b
    depends_on: [plan]
    command: sdlc-review-b         # writes /workspace/reports/review-b/review.md
                                   # no git add/commit

  - id: synthesise
    depends_on: [review-a, review-b]
    command: sdlc-synthesise       # reads /workspace/reports/*/review.md
                                   # then: git add -A && git commit -m "reviews + synthesis"
```

Inside each parallel command brief, tell the model explicitly:

> This node runs in parallel with other reviewers. Do NOT commit —
> the workspace git index is a single-writer resource and concurrent
> committers race on `.git/index.lock`. Write your findings to
> your own subdirectory:
>
>     mkdir -p /workspace/reports/<your-node-id>
>     # write review to /workspace/reports/<your-node-id>/review.md
>
> The downstream synthesise node reads every `reports/*/review.md`
> and produces the single commit covering all reviews.

The fan-in command brief does the single commit:

```
cd /workspace && git add -A && git commit -m "reviews + synthesis"
```

**Design for isolation in v1 (general rule).** Even for non-git
writes, workflow authors should:

1. Make each parallel branch write to a **branch-scoped path** using
   the node id: `reports/<node-id>/`, `logs/<node-id>.log`, etc.
2. Reserve shared filenames (e.g. `report.md`, `summary.txt`) for the
   sequential merge/synthesis node that runs *after* the fan-in.
3. Avoid in-place edits to files read by sibling branches.

**Future work.** Full branch-merge workspace isolation — per-branch
overlay directories with a structured merge on fan-in — is tracked for
v2. The v1 contract is deliberately conservative and explicitly
surfaced, not silently assumed.

### Preprocessing

When a workflow has `image:` nodes, the preprocessor (`preprocess_workflow.py`) transforms them before Archon execution:

1. Each `image:` node becomes a bash node with a `docker run` command.
2. The `command:` field is resolved to a shell expression: `cat <commands_dir>/<name>.md` (where `commands_dir` defaults to `.archon/commands` relative to the workspace, but the preprocessor uses the absolute path passed via `--commands-dir`).
3. The prompt is passed via `CLAUDE_PROMPT` env var (not inline bash — avoids quoting issues).
4. Preserved fields: `id`, `depends_on`, `trigger_rule`, `when`, `timeout`, `retry`.
5. `model:` is extracted into `-e CLAUDE_MODEL=<value>`; the container entrypoint forwards it to `claude --model`.
6. Removed fields: `image`, `command`, `context`, `effort`, `prompt`.
7. `loop:` nodes become bash for-loops with signal detection.
8. The preprocessed YAML replaces the original file (Archon resolves by `name:` — must not have duplicates).

## Team Manifest Schema (v1.0)

Team manifests live in `.archon/teams/` and define which plugins, agents, and skills are available inside a team container.

```yaml
schema_version: "1.0"          # Required. Always "1.0".
name: <team-name>              # Required. Valid Docker tag component: lowercase, digits, dots, hyphens.
description: >                 # Optional. What this team does.
  Human-readable description.
status: active                 # Required. One of: active, ephemeral, inactive, decommissioned.
created: "YYYY-MM-DDTHH:MM:SS"  # Optional. ISO timestamp.
updated: "YYYY-MM-DDTHH:MM:SS"  # Optional. ISO timestamp.
image_built: "YYYY-MM-DDTHH:MM:SS"  # Optional. When the Docker image was last built.

plugins:                       # Required. List of plugin names to include.
  - <plugin-name>              # Must exist in installed_plugins.json on the host.

agents:                        # Optional. Specific agents to include from the listed plugins.
  - <plugin>:<agent>           # Plugin must be in the plugins list above.
  - local:<path>               # Local agent file (relative to project root). Copied into container.

skills:                        # Optional. Specific skills to include.
  - <plugin>:<skill>           # Plugin must be in the plugins list above.

context:                       # Optional. Project files to bake into the container.
  - <filename>                 # Must exist in project root (e.g., CONSTITUTION.md).

group: <group-name>            # Optional (reserved). Forward-compatible team-grouping label
                               # for future fleet-wide operations. Accepted by the validator
                               # but has NO runtime effect in v1 — the validator emits a
                               # warning when set. Safe to declare today as intent.
```

### Build Pipeline

1. `validate_team_manifest.py` validates the manifest against the schema *(run separately or before build)*.
2. `generate_team_claude_md.py` generates a team-specific CLAUDE.md with role framing and agent list.
3. `generate_team_dockerfile.py` generates a Dockerfile that:
   - Uses `sdlc-worker:full` as a source layer (COPY --from).
   - Uses `sdlc-worker:base` as the runtime base.
   - Copies ONLY the listed agent/skill files (additive, no prune).
   - Copies `installed_plugins.json` with paths rewritten for the container.
   - Makes plugins read-only (`chmod -R a-w`).
   - Bakes in the generated team CLAUDE.md.
4. `build-team.sh` runs the full pipeline: validate → generate CLAUDE.md → generate Dockerfile → docker build.

### Enforcement

Each team container only has access to its listed agents and skills. The `installed_plugins.json` inside the container only references the plugins in the manifest. Claude Code inside the container cannot use agents from plugins not in the manifest — they simply don't exist in the container's filesystem.

## Command Prompt Format

Command prompts live in `.archon/commands/` as Markdown files. The filename (without `.md`) must match the `command:` field in workflow nodes.

### Structure

```markdown
You are performing <role description> on a <project description> at /workspace.

<Context about what exists in the project — files, structure, current state.>

<Specific task instructions — numbered steps.>

Write your output to /workspace/<output-file>. Use these sections:
## Section 1
## Section 2

Then commit: cd /workspace && git add -A && git commit -m "<commit message>"
```

### Rules

- Always reference `/workspace` as the working directory (that's where the volume mount is).
- Be specific about output file paths — Claude needs to know exactly where to write.
- Include a commit instruction — each node should commit its work so the next node sees it.
- Commit messages should be descriptive (e.g., `"review: security findings"` not `"update"`).
- Keep prompts focused — one task per command prompt. Complex work should be split across nodes.

## Credential Model

Three-tier fallback resolved by `resolve_credentials.py`:

| Tier | Source | Setup | Best for |
|------|--------|-------|----------|
| 1 (Keychain) | macOS Keychain `"Claude Code-credentials"` | Automatic — Claude Code stores here on Mac | Mac developers (zero-config) |
| 2 (Volume) | Docker volume `sdlc-claude-credentials` | Run `login.sh` | Linux, headless, CI |
| 3 (Config) | `.archon/credentials.yaml` → `credential_path:` | Manual file creation | Custom/enterprise setups |

The resolver returns `mount_args` — a bare Docker volume spec (e.g., `/path/to/creds.json:/home/sdlc/.claude-creds/.credentials.json:ro`). The caller adds `-v` when constructing the docker run command.

All tiers mount credentials to `/home/sdlc/.claude-creds/.credentials.json` (a staging path outside the tmpfs). The entrypoint copies from the staging path to `/home/sdlc/.claude/.credentials.json` at startup. This avoids the tmpfs at `/home/sdlc/.claude` shadowing the credential bind mount.

In `--json` mode, the resolver does NOT clean up temporary files (the caller manages the lifecycle). In interactive mode, temp files are cleaned up after display.

## Docker Execution Model

### Image Tiers

| Image | Size | Purpose |
|-------|------|---------|
| `sdlc-worker:base` | ~3.5 GB | Toolchain: Node.js 22, Claude Code CLI, Archon, Bun, Python 3, git |
| `sdlc-worker:full` | ~3.9 GB | Base + all host plugins. Source layer for team COPY --from — not sized or configured for direct execution. |
| `sdlc-worker:*-team` | ~3.5 GB | Base + manifest-scoped plugin subset. This is what runs. |

Note: Sizes above are approximate (measured before Phase 5 optimizations). Actual sizes should be remeasured after rebuilding with the updated Dockerfile.base (xz-utils removal and Archon .git pruning may reduce base image size).

### Container Execution

Each container runs with these flags:

```
docker run --rm \
    --cap-drop ALL \
    -v "<workspace>:/workspace" \
    -v "<credential-mount>" \
    -e "CLAUDE_PROMPT=<prompt>" \
    -e "CLAUDE_TIMEOUT=<seconds>" \
    <image>
```

- `--cap-drop ALL`: No Linux capabilities. Containers only run Claude Code and git.
- `/workspace`: Volume mount to the host project directory. This is where all work happens.
- Credential mount: Read-only bind mount to `/home/sdlc/.claude-creds/.credentials.json`. The entrypoint copies to `~/.claude/` at startup.
- `CLAUDE_PROMPT`: The task for Claude to execute. Set by the preprocessor from command files.
- `CLAUDE_TIMEOUT`: Seconds before forced exit. Default: 300. Prevents hung containers.

Note: `--read-only` is NOT used. Claude Code requires a writable `~/.claude/` directory for plugins (baked into the image at build time) and runtime state (sessions, backups, config). Plugin enforcement is handled by `chmod -R a-w` on the plugins directory at build time, not by filesystem-level read-only restrictions.

### Entrypoint Flow

1. Unset `ANTHROPIC_API_KEY` (prevents API key override of Max subscription).
2. Copy credentials from mount points to `~/.claude/` if present.
3. Verify Claude Code authentication (quick `claude -p "say ok"` test).
4. Initialize git repo if `/workspace` doesn't have one.
5. Activate loop workaround if Archon bug #1126 is detected.
6. Execute: if `ARCHON_WORKFLOW` is set, run Archon; if `CLAUDE_PROMPT` is set, run Claude with timeout; otherwise exit with usage.
7. On SIGTERM/SIGINT/EXIT: clean up credential temp files, kill child processes.

## Tiered Termination Model

Three independent kill mechanisms prevent both runaway work and lost output:

| Tier | Mechanism | Catches | YAML Field | Default |
|---|---|---|---|---|
| 1. **Budget** | `--max-budget-usd` via `CLAUDE_MAX_BUDGET` env | Model spiralling / burning tokens without progress | `budget: 2.0` (dollars) | No cap |
| 2. **Inner timeout** | `timeout $CLAUDE_TIMEOUT claude ...` in entrypoint | Work exceeding expected duration — Claude gets SIGTERM, can write partial output | Computed: `(timeout_ms / 1000) - 60` | 300s |
| 3. **Outer timeout** | Archon bash node `timeout:` (milliseconds) | Container hung, inner timeout failed | `timeout: 600000` (ms) | 120000 (2 min) |

**Save window**: Tier 2 fires 60 seconds before Tier 3. Claude gets
SIGTERM and has a window to write partial results to `/workspace/reports/`
before Archon kills the container. The floor is 60s — Claude always gets
at least one minute of work time even on short nodes.

**Incremental output**: Command prompts instruct agents to write findings
to `/workspace/reports/<node-id>/findings.md` after each phase, not hold
everything until the end. If any tier fires, partial output is on disk.
The synthesise node checks these files as a fallback when Archon
variables are empty (reviewer timed out).

**Recommended values for workflow authoring:**

| Node type | `timeout:` (ms) | `budget:` ($) |
|---|---|---|
| Review / synthesis | 600000 (10 min) | 2.0 |
| Validation | 300000 (5 min) | 1.0 |
| Implementation / planning | 1800000 (30 min) | 5.0 |
| Long-running cycles | 3600000 (1 hr) | 10.0 |

**Empirical data (dogfood on this repo, 170+ files):**

| Node | Normal run ($2 budget) | $0.01 budget (spiral test) |
|---|---|---|
| security-review | 2m8s | 15.5s (killed by budget) |
| architecture-review | 2m10s | 15.3s (killed by budget) |
| synthesise | 6m8s | — (never reached) |

The budget cap fires after one API round-trip (~15s) when set absurdly low.
At $2, reviews complete normally in 1.5-2.5 min. A spiralling model would
be killed after ~$2 of token burn regardless of how much wall time remains
on the outer timeout — this is why budget is the primary spiral defence and
the outer timeout can be generous (10-30 min) without fear.

**Diagnosing which tier fired:**

| Symptom | Tier | Fix |
|---|---|---|
| Node exit code 1, output includes partial findings | Tier 1 (budget) | Raise `budget:` if work was legitimate |
| Node exit code 124 (timeout utility), partial output on disk | Tier 2 (inner timeout) | Raise `timeout:` — work needs more time |
| Archon reports "timed out after Nms", SIGPIPE, no output | Tier 3 (outer timeout) | Something hung — check Docker logs |
| Node completed successfully | No tier fired | Working as intended |

## Security Model

- **Non-root**: Containers run as `sdlc` user (UID 1001).
- **No capabilities**: `--cap-drop ALL` — no privilege escalation possible.
- **Plugin enforcement**: Team images only contain manifest-listed plugins. Plugins are `chmod -R a-w` (read-only via permissions, not filesystem flag).
- **Credential staging**: Credentials mount to `/home/sdlc/.claude-creds/` (read-only). Entrypoint copies to `~/.claude/` at startup.
- **Credential cleanup**: Entrypoint trap removes `~/.claude/.credentials.json` on exit.
- **No secrets in images**: Credentials are injected at runtime via volume mounts, never baked into images.

## Skills

The `sdlc-workflows` plugin ships six user-invocable skills. Each is the canonical entry point for the listed task — prefer them over bespoke commands.

| Skill | Invoke with | When to use |
|-------|-------------|-------------|
| workflows-setup | `/sdlc-workflows:workflows-setup` | First-time install: patches Archon, builds base/full images, scaffolds `.archon/` dirs |
| workflows-run | `/sdlc-workflows:workflows-run <name>` | Execute a workflow by name — preprocesses `image:` nodes, resolves credentials, delegates to Archon |
| workflows-status | `/sdlc-workflows:workflows-status` | Inspect running/recent workflow runs (containers, exit codes, durations) |
| author-workflow | `/sdlc-workflows:author-workflow --for-task "<desc>" \| --new` | Recommend an existing workflow + team formation for a task, or author a new one |
| deploy-team | `/sdlc-workflows:deploy-team <name>` | Validate a team manifest, generate its Dockerfile and CLAUDE.md, build the team image |
| manage-teams | `/sdlc-workflows:manage-teams` | Lifecycle coaching for teams: create / update / delete / review. `--review` gives the fleet report (roster, staleness, coaching signals, workflow usage); `--review --team <name>` gives single-team detail |

## Long-Running Workflows, Cycles, and Monitoring

The workforce is built around the Archon DAG executor, which shapes what
is easy, what requires work, and what is not possible without an outer
driver.

### Long-running nodes

Nodes can run for hours if the task requires it. There is **no
wall-clock ceiling imposed by Archon or by the preprocessor** — only
the per-node timeout.

```yaml
- id: big-refactor
  command: implement
  image: sdlc-worker:dev-team
  timeout: 7200     # 2 hours; forwarded as CLAUDE_TIMEOUT into the container
```

The default `timeout:` is 300 s (5 min), which is right for smoke tests
and wrong for real work. Authors of long-running workflows **must** set
it explicitly on every long node — there is no inherited default beyond
the 5-min safety net.

Cost is linear in runtime: a 2-hour node running Opus burns real
tokens. There is no built-in cost meter in v1 (see *Monitoring gaps*
below).

### Multi-stage pipelines (linear, no cycling)

A `designer → developer → reviewer → qa` pipeline is just a longer
linear DAG. It is a natural fit for Archon and already proven by
Phase C (parallel fan-out with synthesise fan-in).

```yaml
nodes:
  - { id: design,   command: design,    image: sdlc-worker:design-team }
  - { id: develop,  command: implement, image: sdlc-worker:dev-team,
      depends_on: [design] }
  - { id: review,   command: review,    image: sdlc-worker:review-team,
      depends_on: [develop] }
  - { id: qa,       command: qa,        image: sdlc-worker:qa-team,
      depends_on: [review] }
```

### Cycles — three options, pick the one that matches your problem

Archon executes a **directed acyclic graph**. A single workflow cannot
express `designer → dev → review → designer` as a literal cycle in the
DAG. Three workable patterns, in rising order of cost:

**1. Multi-stage `loop.stages:` (primary pattern).** The cleanest way to
do `designer → developer → reviewer → designer …` is a single loop
node with a `stages:` list. Our preprocessor generates a bash
`for`-loop that runs each stage's `docker run` sequentially per
iteration, checks the `until:` signal on each stage's output, and
breaks when found or `max_iterations` is reached.

```yaml
- id: build-review-cycle
  loop:
    stages:
      - id: design
        image: sdlc-worker:design-team
        command: sdlc-design
      - id: develop
        image: sdlc-worker:dev-team
        command: sdlc-implement
      - id: review
        image: sdlc-worker:review-team
        command: sdlc-review   # brief ends with: output READY_TO_SHIP on approval
    until: "READY_TO_SHIP"
    max_iterations: 10
```

Why this is the primary pattern:

- One DAG node — Archon sees it as a single unit with normal `depends_on` / `trigger_rule` semantics.
- State flows naturally through the shared workspace — each stage commits, the next stage sees the commits.
- Signal detection is ours (our `grep`, not Archon's native `loop:`) so upstream Archon loop-completion bugs never surface.
- Different specialist containers per stage — unlike single-image `loop:`, the whole point is preserved.

**2. Per-node single-image `loop:`.** When only one team is needed — "keep refining this artefact until a signal appears" — use the simpler form. Archon still sees a bash for-loop; all iterations reuse the same image.

```yaml
- id: refine
  command: refine
  image: sdlc-worker:dev-team
  loop:
    until: "READY_FOR_REVIEW"
    max_iterations: 10
```

**3. Unrolled iterations in the DAG.** When iteration count is fixed and small, just author the nodes by hand (`design-v1 → dev-v1 → review-v1 → design-v2 → …`). Every iteration is fully visible in the DAG. Use when you specifically want per-iteration branching or fan-out.

| Shape of your problem | Use |
|---|---|
| Multi-team cycle, signal-driven termination | **Multi-stage `loop.stages:`** |
| Refine one artefact with one team | Per-node single-image `loop:` |
| Fixed small iteration count with per-iter branching | Unrolled iterations |

Outer-loop wrappers (re-invoking `archon workflow run`) are no longer
necessary for the common case — they remain possible if a workflow
needs to survive process death between iterations, but plain
`loop.stages:` covers the "run attended cycles for hours" use case.

### Monitoring — what Archon provides

> **Archon UI clickthrough is degraded for CLI-launched runs — read
> this first.** `archon serve`'s rich per-run views (DAG graph,
> conversation thread, live SSE dashboard at `/api/stream/__dashboard__`)
> only render for workflows launched *through* the HTTP API. Runs
> started by the CLI (`archon workflow run …`, which is what
> `/sdlc-workflows:workflows-run` invokes by default) write to
> `~/.archon/archon.db` and are listed by `archon workflow status`,
> but their UI detail pages and the SSE dashboard stay empty.
> `/sdlc-workflows:workflows-status` reads both REST and SQLite, so it
> works for either launch path and is the authoritative view for CLI
> runs. Use `docker logs -f <container>` for per-node detail. This is
> how Archon 1.x scopes the server — not a bug on our side.

Archon's CLI is only the surface layer. `archon serve` starts a full
HTTP server with a REST API and Server-Sent Events streaming — this
is the observability foundation worth building on.

| Surface | Endpoint / location | Use for |
|---|---|---|
| Workflow status (CLI) | `archon workflow status` | "What's currently running?" at a glance |
| Worktree inventory (CLI) | `archon isolation list` | Per-run worktrees / environments |
| **REST API — runs list** | `GET /api/workflows/runs` | List all runs (historical + active) |
| **REST API — run detail** | `GET /api/workflows/runs/{runId}` | Full state of a specific run |
| **REST API — dashboard** | `GET /api/dashboard/runs` | Enriched view used by the web UI |
| **Run control** | `POST /api/workflows/runs/{runId}/{cancel,resume,abandon,approve,reject}` | Programmatic lifecycle control |
| **SSE — dashboard stream** | `GET /api/stream/__dashboard__` | Multiplexed live stream of ALL workflow events |
| **SSE — conversation stream** | `GET /api/stream/{conversationId}` | Per-run event stream |
| Web UI | `archon serve` — downloads web UI on first run | Local dashboard (built on the API above) |
| State DB | `~/.archon/archon.db` (SQLite) | Direct historical queries if the API is insufficient |
| Structured logs | pino JSON on stdout | Ship to Loki / ELK / Splunk |
| Resume | `archon workflow run <name> --resume` | Pick up the most recent failed run |

The **SSE dashboard stream** is the key primitive for live monitoring
— one subscription surfaces every node start/complete/fail event
across every run in real time. Anything else (metrics exporters, live
terminal feedback, dashboards) can be built on top of it.

### Monitoring — what we add on top

The preprocessor wraps node execution in `docker run`, so the standard
Docker observability surface applies:

- `docker events --since <epoch>` — lifecycle events for every node container. Survives `--rm` removal. We already rely on this for E2E test verification.
- `docker logs -f <container>` — live output from a currently-running node.
- `docker stats` — CPU/memory per container.

The `workflows-status` skill is the intended entry point — it
combines `archon workflow status` with Docker-level visibility.

### Monitoring gaps (v1 — tracked for a follow-up PR)

These are real limitations of the current experience, not defects:

1. **No `/metrics` endpoint.** Archon exposes a REST API + SSE stream but not Prometheus format. A small exporter that subscribes to `/api/stream/__dashboard__` (live events) + `docker events` (container lifecycle) and emits Prometheus metrics is the planned follow-up. All required data is already exposed by `archon serve` — no upstream changes needed.
2. **No structured-event stream for CLI-launched runs.** `archon workflow run` already streams per-node events to stderr (`[node] Started`, `[node] Completed (duration)`), so `workflows-run` shows live progress by default. What we do *not* have — because `archon serve`'s SSE stream only covers server-launched runs — is a structured-event feed that a metrics exporter or a separate watch terminal can consume for our default CLI launch path. The observability follow-up will choose the approach: either `workflows-run --server` (co-launch `archon serve` + `archon workflow run` so SSE becomes available), or a polling exporter against the SQLite schema.
3. **No cost meter.** Claude API spend per node/workflow is not tracked anywhere — it has to come from Claude's own usage reporting. A future exporter could estimate from token-count logs if Claude Code emits them.
4. **No interrupt test coverage.** Ctrl-C at the Archon CLI level has not been shakedown-tested against our containerised runs. Containers themselves handle SIGTERM cleanly (entrypoint trap) but the Archon → container signal path is unproven.
5. **No long-run soak test.** The E2E test runs nodes that complete in seconds. A deliberate slow-node test (≥20 min per node, multi-cycle) would shake out credential expiry, resource leaks, and workspace corruption. Small script, large confidence boost.

The "observability" follow-up PR should bundle at least items 1 + 2 (Prometheus exporter + live streaming). Items 3-5 are optional additions once the data plane exists.

### Recommended follow-up issue

> **feat(workflows): Prometheus/Grafana monitoring for long-running workforce runs**
>
> **Data sources (already present in Archon — no upstream changes required):**
> - `archon serve` HTTP API: `GET /api/workflows/runs`, `GET /api/dashboard/runs`, `GET /api/workflows/runs/{id}`
> - SSE stream: `GET /api/stream/__dashboard__` — live per-node events across all runs
> - Docker events: `docker events` for per-team container lifecycle
>
> **Scope:**
> 1. New package `plugins/sdlc-workflows/exporter/` — a small Node/Python process that
>    (a) subscribes to `/api/stream/__dashboard__`,
>    (b) polls `/api/dashboard/runs` for initial state on startup,
>    (c) subscribes to `docker events` for node-container lifecycle,
>    (d) exposes Prometheus metrics at `:9100/metrics`:
>      - `sdlc_workflow_runs_active{workflow=…}`
>      - `sdlc_workflow_run_duration_seconds_bucket{workflow=…,status=…}`
>      - `sdlc_workflow_node_duration_seconds_bucket{workflow=…,node=…,team=…}`
>      - `sdlc_team_container_starts_total{team=…}`
>      - `sdlc_team_container_failures_total{team=…}`
> 2. Sample Grafana dashboard JSON in `plugins/sdlc-workflows/dashboards/workforce.json`.
> 3. Live streaming in `workflows-run` — the current CLI path already emits per-node events to stderr; the follow-up adds a **server mode** (`workflows-run --server`) that launches `archon serve` + `archon workflow run` in concert so SSE is available without a second terminal, or equivalently a SQLite-polling exporter if server mode proves too heavy. Either way the client helper is written when the server mode lands — we are not shipping an orphan consumer helper ahead of it.
> 4. Optional: `sdlc-workflows:workflows-watch <runId>` — a skill that subscribes to the per-run SSE stream for an already-running workflow, for when the user launched something long and wants to reattach later.
>
> **Out of scope for the first monitoring PR (defer to follow-ups):**
> - Cost / token metering (needs Claude API usage data, not Archon's)
> - OTLP exporter (start with Prometheus; add OTLP if users ask)
> - Alert rule packs (ship dashboard only; let teams write their own alerts)

## Archon Coupling Points

The plugin depends on specific Archon behaviours.  This table is the
canonical reference for what we rely on, what breaks if it changes, and
the current mitigation.  Reviewed and verified against Archon v0.3.6
(SHA `6be5c61`, pinned in `Dockerfile.base`).

| Coupling Point | Risk | What Breaks | Mitigation |
|---|---|---|---|
| `bash:` node type in workflow YAML | GREEN | Archon renames/drops `bash:` → preprocessor output rejected. Failure is immediate and loud. | `bash:` is a documented first-class node type. Low risk. |
| SQLite schema (`remote_agent_workflow_runs`, `remote_agent_workflow_events`) | AMBER | Column rename/drop → `workflows-status` returns empty or raises. | `PRAGMA table_info` schema probe on startup emits a diagnostic warning instead of a silent empty result. 3 integration tests lock the expected columns. |
| REST API shape (`/api/workflows/runs`) | AMBER | Wrapper shape change → detail rows blank. Falls back to SQLite. | Discriminating assertion on the REST wrapper; SQLite fallback is the primary path for CLI-launched runs. |
| Archon binary PATH (`~/.bun/bin/archon`) | GREEN | Install location changes → "not installed" error. | Skills distinguish "not installed" from "installed but not on PATH" and give the user a fix. |

When Archon is upgraded, re-run `tests/test_workflows_status_query_sqlite_integration.py`
to catch schema drift before it reaches users.

## Further Reading

- **Quickstart** — `plugins/sdlc-workflows/docs/quickstart.md` — first-run flow for a developer getting containers going end-to-end.
- **Troubleshooting** — `plugins/sdlc-workflows/docs/troubleshooting.md` — symptom → cause → fix table for auth, container, workflow, image-build, and credential errors.
- **Phase 4 design spec** — `docs/superpowers/specs/2026-04-16-phase4-archon-orchestration-design.md` — rationale for bash-node preprocessing and the three-tier credential resolver.
- **Phase 5 design spec** — `docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md` — security hardening scope, the `--read-only` deviation, signal handling, healthcheck.
- **Reference implementation** — `tests/integration/workforce-smoke/run-e2e.sh` — a working parallel-review run against a miniproject fixture. Copy-paste friendly.
- **Plugin README** — `plugins/sdlc-workflows/README.md` — plugin-scoped surface listing and Apple Silicon ARM64 notes.

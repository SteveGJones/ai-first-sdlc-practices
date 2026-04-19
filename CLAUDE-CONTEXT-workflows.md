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
    timeout: <seconds>          # Optional. Per-node timeout in seconds. Passed as CLAUDE_TIMEOUT env var to container. Default: 300.
    loop:                       # Optional. Repeat this node until a signal is detected.
      until: <signal-string>    # String to grep for in output to stop the loop.
      max_iterations: <int>     # Maximum iterations before forced stop. Default: 5.
      fresh_context: true       # Whether to restart context each iteration.
    prompt: |                   # Optional. Inline prompt instead of command file. Use command: for anything non-trivial.
      Inline prompt text.
    team_extend:                # Optional. List of qualified agent names to add to the team for this node.
      - sdlc-team-security:security-architect
      - sdlc-team-common:api-architect
```

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

**Design for isolation in v1.** Workflow authors should:

1. Make each parallel branch write to a **branch-scoped path** using
   the node id: `output/<node-id>.md`, `logs/<node-id>.log`, etc.
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

## Security Model

- **Non-root**: Containers run as `sdlc` user (UID 1001).
- **No capabilities**: `--cap-drop ALL` — no privilege escalation possible.
- **Plugin enforcement**: Team images only contain manifest-listed plugins. Plugins are `chmod -R a-w` (read-only via permissions, not filesystem flag).
- **Credential staging**: Credentials mount to `/home/sdlc/.claude-creds/` (read-only). Entrypoint copies to `~/.claude/` at startup.
- **Credential cleanup**: Entrypoint trap removes `~/.claude/.credentials.json` on exit.
- **No secrets in images**: Credentials are injected at runtime via volume mounts, never baked into images.

## Skills

The `sdlc-workflows` plugin ships seven user-invocable skills. Each is the canonical entry point for the listed task — prefer them over bespoke commands.

| Skill | Invoke with | When to use |
|-------|-------------|-------------|
| workflows-setup | `/sdlc-workflows:workflows-setup` | First-time install: patches Archon, builds base/full images, scaffolds `.archon/` dirs |
| workflows-run | `/sdlc-workflows:workflows-run <name>` | Execute a workflow by name — preprocesses `image:` nodes, resolves credentials, delegates to Archon |
| workflows-status | `/sdlc-workflows:workflows-status` | Inspect running/recent workflow runs (containers, exit codes, durations) |
| author-workflow | `/sdlc-workflows:author-workflow` | Create a new workflow YAML + its command `.md` briefs interactively |
| deploy-team | `/sdlc-workflows:deploy-team <name>` | Validate a team manifest, generate its Dockerfile and CLAUDE.md, build the team image |
| manage-teams | `/sdlc-workflows:manage-teams` | Lifecycle coaching for teams: create / update / deactivate / review / plan-task |
| teams-status | `/sdlc-workflows:teams-status` | Fleet report: roster, staleness, coaching signals, workflow usage |

## Further Reading

- **Quickstart** — `plugins/sdlc-workflows/docs/quickstart.md` — first-run flow for a developer getting containers going end-to-end.
- **Troubleshooting** — `plugins/sdlc-workflows/docs/troubleshooting.md` — symptom → cause → fix table for auth, container, workflow, image-build, and credential errors.
- **Phase 4 design spec** — `docs/superpowers/specs/2026-04-16-phase4-archon-orchestration-design.md` — rationale for bash-node preprocessing and the three-tier credential resolver.
- **Phase 5 design spec** — `docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md` — security hardening scope, the `--read-only` deviation, signal handling, healthcheck.
- **Reference implementation** — `tests/integration/workforce-smoke/run-e2e.sh` — a working parallel-review run against a miniproject fixture. Copy-paste friendly.
- **Plugin README** — `plugins/sdlc-workflows/README.md` — plugin-scoped surface listing and Apple Silicon ARM64 notes.

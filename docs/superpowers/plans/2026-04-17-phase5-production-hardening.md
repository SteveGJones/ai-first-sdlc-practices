# Phase 5: Production Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden containerised Claude Code workers for local workstation use with security defaults, entrypoint robustness, image optimizations, and a full documentation suite written for Claude Code as primary consumer.

**Architecture:** Interleaved document-then-implement cycles — each sub-feature writes/updates the CLAUDE-CONTEXT reference first, then implements the change, then verifies docs match reality. Documentation targets Claude Code as the primary reader (it generates workflows, manifests, and commands — humans don't write them by hand).

**Tech Stack:** Bash, Python 3, Docker CLI, YAML, Markdown

**Branch:** `feature/96-sdlc-workflows` (worktree at `.worktrees/feature-96-sdlc-workflows`)

**Spec:** `docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md`

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `CLAUDE-CONTEXT-workflows.md` | Machine-readable reference for workflow YAML schema, team manifests, command prompts, credential model, Docker execution model, security model, image architecture |
| `plugins/sdlc-workflows/docs/quickstart.md` | First-5-minutes guide for developers (and Claude Code) to get containerised workers running |
| `plugins/sdlc-workflows/docs/troubleshooting.md` | Symptom → cause → fix reference for Claude Code to pattern-match error messages |
| `plugins/sdlc-workflows/skills/author-workflow/SKILL.md` | Interactive skill for Claude Code to generate workflow YAML + command prompts |

### Modified files

| File | Change |
|------|--------|
| `plugins/sdlc-workflows/docker/entrypoint.sh` | Signal handling (trap), configurable timeout (CLAUDE_TIMEOUT), credential cleanup on exit |
| `plugins/sdlc-workflows/docker/Dockerfile.base` | HEALTHCHECK instruction, pin CLI versions, remove xz-utils after use, prune Archon .git |
| `plugins/sdlc-workflows/scripts/preprocess_workflow.py` | Add `--read-only`, `--cap-drop ALL`, tmpfs flags to generated docker run commands; pass `CLAUDE_TIMEOUT` env var |
| `plugins/sdlc-workflows/scripts/login.sh` | Moved from `tests/integration/workforce-smoke/login.sh`; volume name already correct (`sdlc-claude-credentials`) |
| `tests/integration/workforce-smoke/run-e2e.sh` | Update docker run commands with security flags |
| `tests/integration/workforce-smoke/run-acceptance.sh` | Update docker run commands with security flags; update login.sh path |
| `tests/integration/workforce-smoke/run-containers.sh` | Add read-only filesystem test |
| `CLAUDE-CORE.md` | Add CLAUDE-CONTEXT-workflows.md to context loading table |

---

## Task 1: CLAUDE-CONTEXT-workflows.md (Initial Draft)

Write the authoritative reference that Claude Code loads when authoring or debugging containerised workflows. This is the foundation — every other task updates it.

**Files:**
- Create: `CLAUDE-CONTEXT-workflows.md`
- Modify: `CLAUDE-CORE.md:129-141`

- [ ] **Step 1: Write CLAUDE-CONTEXT-workflows.md**

```markdown
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
```

### DAG Rules

- Nodes with no `depends_on` run first (root layer).
- Nodes sharing the same dependencies and no dependency on each other run in parallel.
- `trigger_rule: all_success` (default) requires ALL dependencies to succeed.
- `trigger_rule: one_success` requires at least ONE dependency to succeed.
- Archon resolves workflows by the `name:` field, not the filename. The filename can differ from the name.

### Preprocessing

When a workflow has `image:` nodes, the preprocessor (`preprocess_workflow.py`) transforms them before Archon execution:

1. Each `image:` node becomes a bash node with a `docker run` command.
2. The `command:` field is resolved to a shell expression: `cat .archon/commands/<name>.md`.
3. The prompt is passed via `CLAUDE_PROMPT` env var (not inline bash — avoids quoting issues).
4. Preserved fields: `id`, `depends_on`, `trigger_rule`, `when`, `timeout`, `retry`.
5. Removed fields: `image`, `command`, `context`, `model`, `effort`, `prompt`.
6. `loop:` nodes become bash for-loops with signal detection.
7. The preprocessed YAML replaces the original file (Archon resolves by `name:` — must not have duplicates).

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
```

### Build Pipeline

1. `validate_team_manifest.py` validates the manifest against the schema.
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

The resolver returns `mount_args` — a bare Docker volume spec (e.g., `/path/to/creds.json:/home/sdlc/.claude/.credentials.json:ro`). The caller adds `-v` when constructing the docker run command.

In `--json` mode, the resolver does NOT clean up temporary files (the caller manages the lifecycle). In interactive mode, temp files are cleaned up after display.

## Docker Execution Model

### Image Tiers

| Image | Size | Purpose |
|-------|------|---------|
| `sdlc-worker:base` | ~3.5 GB | Toolchain: Node.js 22, Claude Code CLI, Archon, Bun, Python 3, git |
| `sdlc-worker:full` | ~3.9 GB | Base + all host plugins. Source layer only — not run directly. |
| `sdlc-worker:*-team` | ~3.5 GB | Base + manifest-scoped plugin subset. This is what runs. |

### Container Execution

Each container runs with these flags:

```
docker run --rm \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid \
    --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
    --cap-drop ALL \
    -v "<workspace>:/workspace" \
    -v "<credential-mount>" \
    -e "CLAUDE_PROMPT=<prompt>" \
    -e "CLAUDE_TIMEOUT=<seconds>" \
    <image>
```

- `--read-only`: Container filesystem is read-only. Only `/workspace`, `/tmp`, and `/home/sdlc/.claude` are writable.
- `--cap-drop ALL`: No Linux capabilities. Containers only run Claude Code and git.
- `/workspace`: Volume mount to the host project directory. This is where all work happens.
- Credential mount: Read-only bind mount of credentials to `/home/sdlc/.claude/.credentials.json`.
- `CLAUDE_PROMPT`: The task for Claude to execute. Set by the preprocessor from command files.
- `CLAUDE_TIMEOUT`: Seconds before forced exit. Default: 300. Prevents hung containers.

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
- **Read-only filesystem**: `--read-only` flag. Only `/workspace`, `/tmp`, `/home/sdlc/.claude` are writable via tmpfs/volume.
- **No capabilities**: `--cap-drop ALL`.
- **Plugin enforcement**: Team images only contain manifest-listed plugins. Read-only (`chmod -R a-w`).
- **Credential cleanup**: Entrypoint trap removes `~/.claude/.credentials.json` on exit.
- **No secrets in images**: Credentials are injected at runtime via volume mounts, never baked into images.
```

Save to: `CLAUDE-CONTEXT-workflows.md` at the repo root.

- [ ] **Step 2: Add to context loading table in CLAUDE-CORE.md**

In `CLAUDE-CORE.md`, add a row to the context loading table (after line 140):

```markdown
| Containerised workflows | CLAUDE-CONTEXT-workflows.md |
```

- [ ] **Step 3: Run syntax validation**

Run: `python tools/validation/local-validation.py --syntax`
Expected: PASS (new .md files don't affect Python syntax checks)

- [ ] **Step 4: Commit**

```bash
git add CLAUDE-CONTEXT-workflows.md CLAUDE-CORE.md
git commit -m "docs: add CLAUDE-CONTEXT-workflows.md — containerised worker reference for Claude Code"
```

---

## Task 2: Security Hardening

Add `--read-only`, `--cap-drop ALL`, tmpfs mounts, and credential cleanup to all Docker execution paths.

**Files:**
- Modify: `plugins/sdlc-workflows/scripts/preprocess_workflow.py:37-65`
- Modify: `plugins/sdlc-workflows/docker/entrypoint.sh`
- Modify: `tests/integration/workforce-smoke/run-e2e.sh`
- Modify: `tests/integration/workforce-smoke/run-acceptance.sh`
- Test: `tests/test_preprocess_workflow.py`

- [ ] **Step 1: Write failing test for security flags in preprocessor output**

Add to `tests/test_preprocess_workflow.py`:

```python
class TestSecurityFlags:
    def test_docker_run_has_read_only(self) -> None:
        """Generated docker run command includes --read-only flag."""
        node = {
            "id": "impl",
            "command": "sdlc-implement",
            "image": "sdlc-worker:dev-team",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount="/tmp/c.json:/home/sdlc/.claude/.credentials.json:ro",
            commands_dir=".archon/commands",
        )
        assert "--read-only" in result["bash"]

    def test_docker_run_has_cap_drop(self) -> None:
        """Generated docker run command drops all capabilities."""
        node = {
            "id": "impl",
            "command": "sdlc-implement",
            "image": "sdlc-worker:dev-team",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount="/tmp/c.json:/home/sdlc/.claude/.credentials.json:ro",
            commands_dir=".archon/commands",
        )
        assert "--cap-drop ALL" in result["bash"]

    def test_docker_run_has_tmpfs_mounts(self) -> None:
        """Generated docker run command has tmpfs for writable paths."""
        node = {
            "id": "impl",
            "command": "sdlc-implement",
            "image": "sdlc-worker:dev-team",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount="/tmp/c.json:/home/sdlc/.claude/.credentials.json:ro",
            commands_dir=".archon/commands",
        )
        assert "--tmpfs /tmp:rw,noexec,nosuid" in result["bash"]
        assert "--tmpfs /home/sdlc/.claude:rw,noexec,nosuid" in result["bash"]

    def test_timeout_env_passed(self) -> None:
        """Nodes with timeout: field pass CLAUDE_TIMEOUT env var."""
        node = {
            "id": "impl",
            "command": "sdlc-implement",
            "image": "sdlc-worker:dev-team",
            "timeout": 600,
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount="/tmp/c.json:/home/sdlc/.claude/.credentials.json:ro",
            commands_dir=".archon/commands",
        )
        assert 'CLAUDE_TIMEOUT=600' in result["bash"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_preprocess_workflow.py::TestSecurityFlags -v`
Expected: FAIL (flags not present in current output)

- [ ] **Step 3: Update `_build_docker_run()` in preprocess_workflow.py**

Replace the `_build_docker_run` function in `plugins/sdlc-workflows/scripts/preprocess_workflow.py`:

```python
def _build_docker_run(
    image: str,
    workspace: str,
    cred_mount: str,
    prompt_source: str,
    timeout: int | None = None,
) -> str:
    """Build a ``docker run`` command string.

    *prompt_source* is a shell expression that produces the prompt text.
    For command nodes: ``cat /workspace/.archon/commands/X.md``
    For inline prompts: a heredoc or echo statement.
    """
    timeout_env = f' -e "CLAUDE_TIMEOUT={timeout}"' if timeout else ""
    lines = [
        "PROMPT=$(" + prompt_source + ")",
        (
            "docker run --rm"
            " --read-only"
            " --tmpfs /tmp:rw,noexec,nosuid"
            " --tmpfs /home/sdlc/.claude:rw,noexec,nosuid"
            " --cap-drop ALL"
            f' -v "{workspace}:/workspace"'
            f' -v "{cred_mount}"'
            ' -e "CLAUDE_PROMPT=$PROMPT"'
            f"{timeout_env}"
            f" {image}"
        ),
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Update `transform_node()` to pass timeout**

In `plugins/sdlc-workflows/scripts/preprocess_workflow.py`, update the `transform_node` function to extract `timeout` from the node and pass it to `_build_docker_run`:

In the non-loop branch (around line 134):
```python
    prompt_source = _resolve_prompt_source(node, commands_dir)
    docker_cmd = _build_docker_run(
        image=image,
        workspace=workspace,
        cred_mount=cred_mount,
        prompt_source=prompt_source,
        timeout=node.get("timeout"),
    )
    result["bash"] = docker_cmd
    return result
```

And in the loop branch (around line 114):
```python
        docker_cmd = _build_docker_run(
            image=image,
            workspace=workspace,
            cred_mount=cred_mount,
            prompt_source=prompt_source,
            timeout=node.get("timeout"),
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_preprocess_workflow.py -v`
Expected: ALL PASS (existing + new tests)

- [ ] **Step 6: Update entrypoint.sh with signal handling and credential cleanup**

Replace `plugins/sdlc-workflows/docker/entrypoint.sh` with:

```bash
#!/bin/bash
set -e

echo "=== SDLC Worker Container ==="

# ---------------------------------------------------------------------------
# Cleanup trap: remove credentials and kill children on exit
# ---------------------------------------------------------------------------
cleanup() {
    echo ""
    echo "=== Cleanup ==="
    rm -f /home/sdlc/.claude/.credentials.json
    # Kill child process group (claude, git, archon) on signal
    kill -- -$$ 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT EXIT

# Step 1: Ensure no API key overrides Max subscription
unset ANTHROPIC_API_KEY

# Step 1b: Link scoped credential mount to where Claude Code expects it
if [ -d /home/sdlc/.claude-auth ] && [ "$(ls -A /home/sdlc/.claude-auth 2>/dev/null)" ]; then
    for auth_file in /home/sdlc/.claude-auth/*; do
        if [ -f "$auth_file" ]; then
            cp "$auth_file" /home/sdlc/.claude/"$(basename "$auth_file")"
            chmod 600 /home/sdlc/.claude/"$(basename "$auth_file")"
        fi
    done
    echo "Auth: credentials loaded from scoped mount"
fi

# Step 2: Verify Claude Code is available
echo "Claude Code version: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Archon version: $(archon --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python version: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 3: Check Claude Code authentication
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code is not authenticated."
    echo ""
    echo "Run the login script first to populate the credential volume:"
    echo "  ./login.sh"
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 4: Initialize git repo if needed (Archon needs a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "sdlc-worker@example.com"
    git config user.name "SDLC Worker"
    git add -A 2>/dev/null || true
    git commit -m "initial" --allow-empty 2>/dev/null || true
fi

# Step 4.5: Activate loop signal workaround if needed
# Conditional — same pattern as the ARM64 fix. Self-deactivating when
# Archon fixes bug #1126.
LOOP_WORKAROUND_ACTIVE=false
if [ -f /opt/sdlc-scripts/detect-loop-bug.sh ]; then
    if bash /opt/sdlc-scripts/detect-loop-bug.sh >/dev/null 2>&1; then
        if [ -f /opt/sdlc-scripts/loop-workaround.sh ]; then
            source /opt/sdlc-scripts/loop-workaround.sh
            LOOP_WORKAROUND_ACTIVE=true
            echo "Loop workaround: active"
            cleanup_sentinel
        fi
    else
        echo "Loop workaround: not needed (bug not detected)"
    fi
fi

# Step 5: Execute the assigned work
# CLAUDE_TIMEOUT (default 300s) prevents hung containers.
TIMEOUT="${CLAUDE_TIMEOUT:-300}"

if [ -n "$ARCHON_WORKFLOW" ]; then
    echo "Running Archon workflow: $ARCHON_WORKFLOW"
    echo "Arguments: ${ARCHON_ARGS:-<none>}"
    echo ""
    timeout "$TIMEOUT" archon run "$ARCHON_WORKFLOW" ${ARCHON_ARGS:+"$ARCHON_ARGS"}
elif [ -n "$CLAUDE_PROMPT" ]; then
    echo "Running Claude Code with prompt (timeout: ${TIMEOUT}s)..."
    timeout "$TIMEOUT" claude --dangerously-skip-permissions -p "$CLAUDE_PROMPT"
else
    echo "No ARCHON_WORKFLOW or CLAUDE_PROMPT set."
    echo "Usage:"
    echo "  ARCHON_WORKFLOW=sdlc-parallel-review  — run an Archon workflow"
    echo "  CLAUDE_PROMPT='fix the bug in app.py'  — run a direct Claude prompt"
    exit 1
fi

echo ""
echo "=== SDLC Worker Complete ==="
```

- [ ] **Step 7: Update run-acceptance.sh docker run commands with security flags**

In `tests/integration/workforce-smoke/run-acceptance.sh`, update the `run_claude()` function:

```bash
run_claude() {
    local image="$1"
    local prompt_file="$2"
    local timeout="${3:-180}"

    docker run --rm \
        --read-only \
        --tmpfs /tmp:rw,noexec,nosuid \
        --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
        --cap-drop ALL \
        -v "$CRED_MOUNT" \
        -v "${WORKSPACE}:/workspace" \
        -v "${prompt_file}:/tmp/prompt.txt:ro" \
        --entrypoint /bin/bash \
        "$image" \
        -c '
            unset ANTHROPIC_API_KEY
            if [ ! -d /workspace/.git ]; then
                cd /workspace && git init -q && git config user.email "test@test.com" && git config user.name "Test" && git add -A && git commit -q -m initial 2>/dev/null || true
            fi
            cd /workspace
            claude --dangerously-skip-permissions -p "$(cat /tmp/prompt.txt)"
        ' 2>&1
}
```

Also update the auth check docker run (check 1):

```bash
AUTH_OUTPUT=$(docker run --rm \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid \
    --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
    --cap-drop ALL \
    -v "$CRED_MOUNT" \
    --entrypoint /bin/bash \
    sdlc-worker:dev-team \
    -c '
        unset ANTHROPIC_API_KEY
        claude -p "say OK" 2>&1 | head -1
    ' 2>&1) || true
```

- [ ] **Step 8: Update run-e2e.sh docker run commands with security flags**

In the `run_nodes_direct()` function in `tests/integration/workforce-smoke/run-e2e.sh`, update the docker run command:

```bash
        NODE_OUTPUT=$(docker run --rm \
            --read-only \
            --tmpfs /tmp:rw,noexec,nosuid \
            --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
            --cap-drop ALL \
            -v "$WORKSPACE:/workspace" \
            -v "$CRED_MOUNT" \
            -e "CLAUDE_PROMPT=$PROMPT" \
            "$NODE_IMAGE" 2>&1) || true
```

- [ ] **Step 9: Run unit tests**

Run: `python -m pytest tests/ --ignore=tests/integration -q`
Expected: 155+ PASS

- [ ] **Step 10: Run container smoke test to verify read-only works**

Run: `bash tests/integration/workforce-smoke/run-containers.sh`
Expected: 16/16 PASS (containers still function with read-only filesystem)

- [ ] **Step 11: Update CLAUDE-CONTEXT-workflows.md security model section**

Verify the security model section in CLAUDE-CONTEXT-workflows.md matches the implemented flags. Update if any paths needed adjustment during testing.

- [ ] **Step 12: Commit**

```bash
git add plugins/sdlc-workflows/scripts/preprocess_workflow.py \
        plugins/sdlc-workflows/docker/entrypoint.sh \
        tests/integration/workforce-smoke/run-e2e.sh \
        tests/integration/workforce-smoke/run-acceptance.sh \
        tests/test_preprocess_workflow.py \
        CLAUDE-CONTEXT-workflows.md
git commit -m "feat(security): add read-only filesystem, cap-drop, signal handling, credential cleanup"
```

---

## Task 3: Docker HEALTHCHECK and Timeout

Add HEALTHCHECK instruction to Dockerfile.base and verify timeout behaviour.

**Files:**
- Modify: `plugins/sdlc-workflows/docker/Dockerfile.base:86-88`

- [ ] **Step 1: Add HEALTHCHECK to Dockerfile.base**

Before the `USER sdlc` line (line 85), add:

```dockerfile
# Health check: verify Claude Code binary is available
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD test -x /usr/local/bin/claude || exit 1
```

- [ ] **Step 2: Rebuild base image and verify healthcheck**

```bash
bash plugins/sdlc-workflows/docker/build-base.sh
docker inspect --format='{{json .Config.Healthcheck}}' sdlc-worker:base
```

Expected output includes: `"Test":["CMD-SHELL","test -x /usr/local/bin/claude || exit 1"]`

- [ ] **Step 3: Rebuild full image (depends on base)**

```bash
bash plugins/sdlc-workflows/docker/build-full.sh
```

- [ ] **Step 4: Update CLAUDE-CONTEXT-workflows.md entrypoint flow section**

Verify the entrypoint flow section documents the timeout behaviour:
- `CLAUDE_TIMEOUT` env var (default 300s)
- `timeout` command wraps Claude invocation
- On timeout: container exits with code 124

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-workflows/docker/Dockerfile.base CLAUDE-CONTEXT-workflows.md
git commit -m "feat(docker): add HEALTHCHECK instruction and document timeout behaviour"
```

---

## Task 4: Image Optimization (Quick Wins)

Record baselines, apply low-effort optimizations, record results.

**Files:**
- Modify: `plugins/sdlc-workflows/docker/Dockerfile.base`

- [ ] **Step 1: Record baseline image sizes**

```bash
echo "=== Image Size Baseline ==="
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | grep sdlc-worker
echo ""
echo "=== Layer Breakdown (base) ==="
docker history sdlc-worker:base --format 'table {{.Size}}\t{{.CreatedBy}}' | head -20
```

Record the output — it will be documented in CLAUDE-CONTEXT-workflows.md.

- [ ] **Step 2: Pin Claude Code CLI version**

In `Dockerfile.base`, change:

```dockerfile
RUN npm install -g @anthropic-ai/claude-code
```

To (use the version currently installed):

```bash
# Get the current version
docker run --rm sdlc-worker:base claude --version
```

Then pin it:

```dockerfile
RUN npm install -g @anthropic-ai/claude-code@<version>
```

- [ ] **Step 3: Pin Ralph CLI version**

Same pattern:

```bash
docker run --rm sdlc-worker:base ralph --version 2>/dev/null || echo "check npm"
```

Then pin in Dockerfile.base:

```dockerfile
RUN npm install -g @ralph-orchestrator/ralph-cli@<version>
```

- [ ] **Step 4: Remove xz-utils after Bun extraction and prune Archon .git**

In `Dockerfile.base`, the xz-utils package is installed for Bun but not needed at runtime. Add cleanup after the Archon source copy:

After the line `COPY --from=archon-deps /opt/archon /opt/archon`, add:

```dockerfile
# Clean up build-only dependencies and artifacts
RUN apt-get purge -y --auto-remove xz-utils && \
    rm -rf /var/lib/apt/lists/* /opt/archon/.git
```

- [ ] **Step 5: Rebuild and record new sizes**

```bash
bash plugins/sdlc-workflows/docker/build-base.sh
bash plugins/sdlc-workflows/docker/build-full.sh
echo "=== Image Size After Optimization ==="
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | grep sdlc-worker
```

- [ ] **Step 6: Update CLAUDE-CONTEXT-workflows.md image architecture section**

Update the image size table with actual measured values (before and after).

- [ ] **Step 7: Run Phase 2 smoke test to verify images still work**

Run: `bash tests/integration/team-smoke/run.sh`
Expected: 7/7 PASS

- [ ] **Step 8: Commit**

```bash
git add plugins/sdlc-workflows/docker/Dockerfile.base CLAUDE-CONTEXT-workflows.md
git commit -m "feat(docker): pin CLI versions, remove build-only deps, prune Archon .git"
```

---

## Task 5: login.sh Alignment

Move login.sh to the plugin directory and update all references.

**Files:**
- Move: `tests/integration/workforce-smoke/login.sh` → `plugins/sdlc-workflows/scripts/login.sh`
- Modify: `tests/integration/workforce-smoke/run-acceptance.sh`
- Modify: `tests/integration/workforce-smoke/run-e2e.sh`

- [ ] **Step 1: Move login.sh**

```bash
mv tests/integration/workforce-smoke/login.sh plugins/sdlc-workflows/scripts/login.sh
```

- [ ] **Step 2: Update login.sh**

The script already creates the `sdlc-claude-credentials` volume (confirmed by reading it). Update the help text at the bottom to reflect its new location and remove the old test-specific `sdlc-workforce-smoke-creds` intermediate volume name:

In `plugins/sdlc-workflows/scripts/login.sh`, update:

```bash
CRED_VOLUME="sdlc-login-temp"
SCOPED_VOLUME="sdlc-claude-credentials"
```

And update the final echo:

```bash
echo ""
echo "Done. Credentials stored in volume: $SCOPED_VOLUME"
echo "This volume is automatically detected by the credential resolver (tier 2)."
```

- [ ] **Step 3: Update run-acceptance.sh error message**

In `tests/integration/workforce-smoke/run-acceptance.sh`, find the credential failure message and update the login.sh path:

```bash
    echo "Ensure Claude Code is authenticated on this Mac, or run: $PLUGIN_DIR/scripts/login.sh"
```

- [ ] **Step 4: Update run-e2e.sh error message**

In `tests/integration/workforce-smoke/run-e2e.sh`, find the credential failure message and update:

```bash
    echo "Run $PLUGIN_DIR/scripts/login.sh first, or ensure Claude Code is authenticated on this Mac."
```

- [ ] **Step 5: Verify acceptance test still works**

Run: `bash tests/integration/workforce-smoke/run-acceptance.sh`
Expected: 7/7 PASS (uses credential resolver, not login.sh directly — path change only affects error messages)

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-workflows/scripts/login.sh \
        tests/integration/workforce-smoke/run-acceptance.sh \
        tests/integration/workforce-smoke/run-e2e.sh
git rm tests/integration/workforce-smoke/login.sh
git commit -m "refactor: move login.sh to plugin, align volume names with credential resolver"
```

---

## Task 6: Quickstart Guide

Write the first-5-minutes guide for getting containerised workers running.

**Files:**
- Create: `plugins/sdlc-workflows/docs/quickstart.md`

- [ ] **Step 1: Write quickstart.md**

```markdown
# Containerised Workers — Quickstart

Get from zero to a working containerised workflow in 5 minutes.

## Prerequisites

- **Docker Desktop** running (verify: `docker info`)
- **Claude Code** authenticated on this machine (verify: `claude -p "say ok"`)
- **This repository** cloned with the sdlc-workflows plugin installed

## Step 1: Build Base Images

```bash
# From the repository root:
bash plugins/sdlc-workflows/docker/build-base.sh
bash plugins/sdlc-workflows/docker/build-full.sh
```

This builds two images:
- `sdlc-worker:base` — toolchain (Node.js, Claude Code, Archon, Python, git)
- `sdlc-worker:full` — base + all installed plugins (source layer for team images)

Build takes ~3-5 minutes on first run, seconds on rebuild.

## Step 2: Create a Team

Teams are defined by manifests in `.archon/teams/`. Each manifest specifies which plugins, agents, and skills the team has access to.

Create `.archon/teams/my-team.yaml`:

```yaml
schema_version: "1.0"
name: my-team
description: >
  My first team — has access to code review and enforcement agents.
status: active

plugins:
  - sdlc-core

agents:
  - sdlc-core:verification-enforcer
  - sdlc-core:sdlc-enforcer

skills:
  - sdlc-core:validate

context:
  - CONSTITUTION.md
```

Build the team image:

```bash
bash plugins/sdlc-workflows/docker/build-team.sh my-team
```

This validates the manifest, generates a team-specific CLAUDE.md with role framing, and builds `sdlc-worker:my-team`.

## Step 3: Create a Workflow

Workflows define a DAG of nodes. Each node runs in a container with the specified team image.

Create `.archon/workflows/my-pipeline.yaml`:

```yaml
name: my-pipeline
description: |
  Simple implement-then-review pipeline.

provider: claude

nodes:
  - id: implement
    command: my-implement
    image: sdlc-worker:my-team

  - id: review
    command: my-review
    image: sdlc-worker:my-team
    depends_on: [implement]
```

Create the command prompts in `.archon/commands/`:

**`.archon/commands/my-implement.md`**:
```markdown
You are implementing a change at /workspace.

<Describe the task here — what to read, what to change, what to create.>

After making changes, commit:
  cd /workspace && git add -A && git commit -m "feat: description"
```

**`.archon/commands/my-review.md`**:
```markdown
You are reviewing changes at /workspace.

Read the recent commits: cd /workspace && git log --oneline -5

Review for correctness, edge cases, and test coverage.

Write your review to /workspace/review.md with ## Summary, ## Issues, ## Recommendation.
Then commit: cd /workspace && git add -A && git commit -m "review: findings"
```

## Step 4: Run the Workflow

Use the skill:

```
/sdlc-workflows:workflows-run my-pipeline
```

Or use the CLI directly:

```bash
# Resolve credentials
CRED_JSON=$(python3 plugins/sdlc-workflows/scripts/resolve_credentials.py --json)
CRED_MOUNT=$(echo "$CRED_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['mount_args'])")

# Preprocess workflow (transforms image: nodes to docker run commands)
python3 plugins/sdlc-workflows/scripts/preprocess_workflow.py \
    .archon/workflows/my-pipeline.yaml \
    --output .archon/workflows/my-pipeline.yaml \
    --workspace "$(pwd)" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir "$(pwd)/.archon/commands"

# Run via Archon
archon workflow run my-pipeline --no-worktree
```

## Step 5: Verify Results

```bash
git log --oneline -5       # See commits from each container
ls *.md                     # See generated review files
```

## Credential Tiers

| Environment | Setup | How it works |
|-------------|-------|-------------|
| **Mac** | None (automatic) | Credentials extracted from macOS Keychain |
| **Linux** | Run `plugins/sdlc-workflows/scripts/login.sh` | Creates Docker volume `sdlc-claude-credentials` |
| **Custom** | Create `.archon/credentials.yaml` | Point to credential file path |

Check your current tier:
```bash
python3 plugins/sdlc-workflows/scripts/resolve_credentials.py
```

## Or Use the Authoring Skill

Instead of writing workflow YAML by hand, ask Claude Code:

```
/sdlc-workflows:author-workflow
```

This interactive skill asks what you want to build, generates the workflow YAML, command prompts, and validates everything.

## Next Steps

- Read `CLAUDE-CONTEXT-workflows.md` for the full schema reference
- Use `/sdlc-workflows:manage-teams` to manage team lifecycle
- Use `/sdlc-workflows:teams-status` for fleet visibility
- See `plugins/sdlc-workflows/docs/troubleshooting.md` if something goes wrong
```

Save to: `plugins/sdlc-workflows/docs/quickstart.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-workflows/docs/quickstart.md
git commit -m "docs: add quickstart guide for containerised workers"
```

---

## Task 7: Author-Workflow Skill

Interactive skill for Claude Code to generate workflow YAML and command prompts.

**Files:**
- Create: `plugins/sdlc-workflows/skills/author-workflow/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: author-workflow
description: Create a new containerised workflow — generates workflow YAML, command prompts, and validates team references.
disable-model-invocation: false
argument-hint: "[workflow description]"
---

# Author Workflow

Create a new containerised team workflow. This skill generates the workflow YAML, command prompt files, and validates everything against existing teams.

## Context

Load `CLAUDE-CONTEXT-workflows.md` before proceeding — it contains the workflow YAML schema, team manifest schema, command prompt format, and all validation rules.

## Steps

### 1. Understand the Goal

If the user provided a description as an argument, use it. Otherwise ask:

> What should this workflow accomplish? Describe the pipeline: what work needs to happen, in what order, and which teams should do it.

### 2. Discover Existing Teams

List available team manifests:

```bash
ls .archon/teams/*.yaml 2>/dev/null
```

For each manifest, show the team name, description, and available agents:

```bash
for f in .archon/teams/*.yaml; do
    python3 -c "
import yaml
m = yaml.safe_load(open('$f'))
print(f\"  {m['name']}: {m.get('description', 'no description').strip()}\")
print(f\"    agents: {', '.join(m.get('agents', []))}\")
"
done
```

If no teams exist, suggest creating them first:

> No team manifests found in `.archon/teams/`. Create teams first with `/sdlc-workflows:manage-teams --create`.

### 3. Design the DAG

Based on the user's description and available teams, design the workflow DAG:

- Identify distinct stages (implement, review, validate, etc.)
- Assign each stage to a team image
- Determine dependencies (what must complete before what)
- Identify parallel opportunities (nodes that can run concurrently)

Present the DAG to the user for approval:

```
Proposed pipeline:
  1. implement (sdlc-worker:dev-team) — no deps
  2. security-review (sdlc-worker:review-team) — after implement
  3. architecture-review (sdlc-worker:review-team) — after implement
  4. synthesise (sdlc-worker:dev-team) — after both reviews

Nodes 2 and 3 run in parallel.
```

### 4. Generate Workflow YAML

Create `.archon/workflows/<name>.yaml` following the schema in CLAUDE-CONTEXT-workflows.md:

- `name:` must be unique across all workflows in the directory
- `description:` should explain purpose, inputs, and outputs
- `provider: claude` always
- Each node needs: `id`, `command`, `image`, and `depends_on` where applicable
- Use `trigger_rule: all_success` (default) unless the user specifies otherwise
- Add `timeout:` to long-running nodes (default 300s is fine for most)

### 5. Generate Command Prompts

For each node, create `.archon/commands/<command-name>.md` following the format in CLAUDE-CONTEXT-workflows.md:

- Role framing: "You are performing X on a Y at /workspace."
- Context: what files exist, what state to expect
- Task: numbered steps of what to do
- Output: where to write results
- Commit: `cd /workspace && git add -A && git commit -m "<message>"`

### 6. Validate

Run validation checks:

```bash
# Validate that referenced team images have manifests
for team in <list of unique images>; do
    team_name="${team#sdlc-worker:}"
    if [ ! -f ".archon/teams/${team_name}.yaml" ]; then
        echo "WARNING: No manifest for $team_name — run build-team.sh after creating one"
    fi
done

# Check command files exist
for cmd in <list of unique commands>; do
    if [ ! -f ".archon/commands/${cmd}.md" ]; then
        echo "ERROR: Missing command file: .archon/commands/${cmd}.md"
    fi
done

# Validate workflow YAML structure
python3 -c "
import yaml
wf = yaml.safe_load(open('.archon/workflows/<name>.yaml'))
assert 'name' in wf, 'Missing name field'
assert 'nodes' in wf, 'Missing nodes field'
for node in wf['nodes']:
    assert 'id' in node, f'Node missing id'
    assert 'command' in node or 'prompt' in node, f'Node {node[\"id\"]} needs command or prompt'
print('Workflow YAML valid')
"
```

### 7. Commit

```bash
git add .archon/workflows/<name>.yaml .archon/commands/<command-files>
git commit -m "feat(workflow): add <name> workflow with <N> nodes"
```

### 8. Report

```
Workflow created:
  File: .archon/workflows/<name>.yaml
  Nodes: <count>
  Teams: <list>
  Commands: <list of .md files>

To build team images:   bash plugins/sdlc-workflows/docker/build-team.sh <team>
To run the workflow:     /sdlc-workflows:workflows-run <name>
```
```

Save to: `plugins/sdlc-workflows/skills/author-workflow/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-workflows/skills/author-workflow/SKILL.md
git commit -m "feat(skill): add author-workflow skill for Claude Code to generate workflows"
```

---

## Task 8: Troubleshooting Guide

Symptom → cause → fix reference for Claude Code to pattern-match errors.

**Files:**
- Create: `plugins/sdlc-workflows/docs/troubleshooting.md`

- [ ] **Step 1: Write troubleshooting.md**

```markdown
# Containerised Workers — Troubleshooting

Symptom-based troubleshooting guide. When a containerised workflow fails, match the error to find the fix.

## Authentication Errors

### `authentication_error` / HTTP 401

**Cause:** Credentials expired or not available to the container.

**Diagnosis:**
```bash
python3 plugins/sdlc-workflows/scripts/resolve_credentials.py
```

**Fixes:**
- **Tier shows "none"**: Claude Code is not authenticated on this machine. Run `claude auth login` in a terminal, then retry.
- **Tier shows "keychain" but container fails**: The Keychain credential may have expired. Re-authenticate Claude Code (`claude auth login`), then retry.
- **Tier shows "volume"**: The Docker volume credential may be stale. Re-run `plugins/sdlc-workflows/scripts/login.sh`.
- **Tier shows "config"**: Check that the file at the `credential_path` in `.archon/credentials.yaml` exists and contains valid JSON with a `claudeAiOauth` key.

### `not logged in` / `please run /login`

**Cause:** The entrypoint's auth check (`claude -p "say ok"`) failed. Same fixes as above.

## Container Execution Errors

### Container hangs — no output for >5 minutes

**Cause:** Claude may be in a prompt loop, or there's a network issue.

**Diagnosis:**
```bash
docker ps  # Check health status
docker logs <container-id>  # Check output
```

**Fixes:**
- `docker stop <container-id>` — triggers graceful cleanup via SIGTERM trap.
- If CLAUDE_TIMEOUT is set (default 300s), the container auto-exits after that duration.
- To increase timeout for long-running tasks, set `timeout: 600` on the workflow node.

### `read-only file system` error

**Cause:** Container attempting to write outside allowed paths.

**Allowed writable paths:**
- `/workspace` (volume mount — project files)
- `/tmp` (tmpfs — temporary files)
- `/home/sdlc/.claude` (tmpfs — Claude runtime state)

**Fixes:**
- Ensure your command prompt writes to `/workspace/`, not elsewhere.
- If a tool needs to write to a custom path, it must be under `/workspace` or `/tmp`.
- Check the entrypoint — `npm install -g` and similar commands will fail on read-only filesystem (they should be done at image build time, not runtime).

### Exit code 124 (timeout)

**Cause:** CLAUDE_TIMEOUT expired before Claude finished.

**Fixes:**
- Increase timeout: add `timeout: 600` (or higher) to the workflow node.
- Simplify the command prompt — break complex work into multiple nodes.
- Check if the prompt is causing Claude to loop (open-ended instructions without clear completion criteria).

### `OCI runtime create failed` / `permission denied`

**Cause:** Capability or filesystem restriction blocking an operation.

**Fixes:**
- Containers run with `--cap-drop ALL`. If a tool truly needs a capability (unlikely for Claude Code), check if the tool can be run differently.
- Check file permissions on the workspace mount — the sdlc user (UID 1001) must be able to read/write.

## Workflow Errors

### `workflow not found`

**Cause:** Archon can't find the workflow by name.

**Diagnosis:**
```bash
archon workflow list  # Shows available workflows
```

**Fixes:**
- Check the `name:` field inside the YAML matches what you're requesting (Archon resolves by name, not filename).
- Verify the workflow file is in `.archon/workflows/`.
- Check for YAML syntax errors: `python3 -c "import yaml; yaml.safe_load(open('.archon/workflows/<file>.yaml'))"`.

### `no commits produced` after workflow run

**Cause:** The container ran but Claude didn't follow the commit instruction.

**Fixes:**
- Check the command prompt — does it end with an explicit `git add -A && git commit -m "..."` instruction?
- Check the workspace had a git repo (the entrypoint creates one if missing).
- Run the workflow again — LLM output is non-deterministic and may follow instructions more closely on retry.

### Review files missing after parallel workflow

**Cause:** Parallel containers writing to the same workspace may have git lock contention, or Claude didn't follow the file output instruction.

**Fixes:**
- Check git log — if commits exist but files are missing, the commit may have been made before the file was written.
- Check the command prompt — be explicit about the output file path (e.g., `/workspace/security-review.md`, not just "write a review").
- If git lock contention: the containers write different files, so minor timing differences usually resolve this naturally.

## Image Build Errors

### `sdlc-worker:full is a source image`

**Cause:** Attempting to run the full image directly. It's a source layer, not a runnable container.

**Fix:** Build a team image: `bash plugins/sdlc-workflows/docker/build-team.sh <team-name>`

### `manifest not found` during build

**Cause:** The team manifest YAML doesn't exist in `.archon/teams/`.

**Fix:** Create the manifest. Use `/sdlc-workflows:manage-teams --create` or see the quickstart guide.

### `plugin not found in installed_plugins.json`

**Cause:** The team manifest references a plugin that isn't installed on the host.

**Fix:** Install the plugin first, then rebuild the full image (`build-full.sh`), then rebuild the team image.

## Credential Volume Errors

### `volume not found` when running login.sh

**Cause:** Docker volume doesn't exist yet.

**Fix:** `login.sh` creates the volume automatically. Just run it: `bash plugins/sdlc-workflows/scripts/login.sh`

### Stale credentials in volume

**Cause:** OAuth token in the Docker volume has expired.

**Fix:** Re-run `plugins/sdlc-workflows/scripts/login.sh` to refresh credentials.

### `mount_args` has spaces or special characters

**Cause:** The credential file path contains spaces.

**Fix:** Check `resolve_credentials.py --json` output. Move credential files to a path without spaces.
```

Save to: `plugins/sdlc-workflows/docs/troubleshooting.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-workflows/docs/troubleshooting.md
git commit -m "docs: add troubleshooting guide for containerised worker failures"
```

---

## Task 9: Final Verification

Full test pyramid run + documentation consistency check.

**Files:**
- Modify: `CLAUDE.md` (update Phase 5 status)
- Modify: `CLAUDE-CONTEXT-workflows.md` (final consistency pass)

- [ ] **Step 1: Run unit tests**

Run: `python -m pytest tests/ --ignore=tests/integration -q`
Expected: 155+ PASS (original + new security flag tests)

- [ ] **Step 2: Run Phase 2 smoke**

Run: `bash tests/integration/team-smoke/run.sh`
Expected: 7/7 PASS

- [ ] **Step 3: Run Phase 3 Python smoke**

Run: `bash tests/integration/workforce-smoke/run.sh`
Expected: 8/8 PASS

- [ ] **Step 4: Run Phase 3 container smoke**

Run: `bash tests/integration/workforce-smoke/run-containers.sh`
Expected: 16/16 PASS

- [ ] **Step 5: Run acceptance test**

Run: `bash tests/integration/workforce-smoke/run-acceptance.sh`
Expected: 7/7 PASS

- [ ] **Step 6: Run E2E parallel test**

Run: `export BUN_INSTALL="$HOME/.bun" && export PATH="$BUN_INSTALL/bin:$PATH" && bash tests/integration/workforce-smoke/run-e2e.sh --parallel`
Expected: 8/8 PASS

- [ ] **Step 7: Documentation consistency check**

Verify all cross-references are correct:
```bash
# Check CLAUDE-CONTEXT-workflows.md is in context loading table
grep -q "CLAUDE-CONTEXT-workflows" CLAUDE-CORE.md

# Check quickstart references exist
grep -q "quickstart" plugins/sdlc-workflows/docs/quickstart.md

# Check troubleshooting references actual flag names
grep -q "read-only" plugins/sdlc-workflows/docs/troubleshooting.md
grep -q "CLAUDE_TIMEOUT" plugins/sdlc-workflows/docs/troubleshooting.md

# Check author-workflow skill references CLAUDE-CONTEXT
grep -q "CLAUDE-CONTEXT-workflows" plugins/sdlc-workflows/skills/author-workflow/SKILL.md
```

- [ ] **Step 8: Update CLAUDE.md**

Update the EPIC #96 bullet in CLAUDE.md:

```markdown
- **EPIC #96** — Containerised Claude Code workers. Phases 1-5 complete. Hardened for local workstation use: read-only filesystem, capability dropping, signal handling, configurable timeout, Docker healthcheck. Full documentation suite (CLAUDE-CONTEXT reference, quickstart, author-workflow skill, troubleshooting). Branch `feature/96-sdlc-workflows`.
```

- [ ] **Step 9: Commit**

```bash
git add CLAUDE.md CLAUDE-CONTEXT-workflows.md
git commit -m "docs: Phase 5 complete — update CLAUDE.md with production hardening status"
```

---

## Summary

| Task | Component | New/Modified | Commits |
|------|-----------|-------------|---------|
| 1 | CLAUDE-CONTEXT-workflows.md | 1 new, 1 modified | 1 |
| 2 | Security hardening | 5 modified, 1 test | 1 |
| 3 | HEALTHCHECK + timeout | 1 modified | 1 |
| 4 | Image optimization | 1 modified | 1 |
| 5 | login.sh alignment | 1 moved, 2 modified | 1 |
| 6 | Quickstart guide | 1 new | 1 |
| 7 | Author-workflow skill | 1 new | 1 |
| 8 | Troubleshooting guide | 1 new | 1 |
| 9 | Final verification | 2 modified | 1 |
| **Total** | **4 new, ~10 modified** | **4 new tests** | **~9 commits** |

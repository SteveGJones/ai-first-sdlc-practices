# Design Spec: Phase 4 — Archon Orchestration (EPIC #96)

**Date**: 2026-04-16
**Status**: Approved
**EPIC**: #96 �� Containerised Claude Code Workers
**Phase**: 4 of 5 (Orchestration)
**Depends on**: Phase 3 (Workforce Management) — complete, 20 commits on `feature/96-sdlc-workflows`
**Next**: Phase 5 (Production Hardening) — not yet scoped

## 1. Problem Statement

Phases 1-3 proved that team containers can do real work with enforcement. The acceptance test runs real Claude Code inside `sdlc-worker:dev-team` and `sdlc-worker:review-team`, implements features, reviews changes, and proves agent isolation. But the test manages containers manually via `docker run` — it is the orchestrator.

In production, Archon is the orchestrator. It reads workflow YAML, manages node dependencies, handles parallel execution, and coordinates output. Phase 4 proves that Archon can orchestrate containerised team nodes.

### What's proven (Phases 1-3)

- Three-tier Docker image model builds correctly
- Team manifests define and enforce agent boundaries
- Different containers see different agents
- Claude Code authenticates and does real work inside team containers
- Management scripts (inventory, status, coaching, overrides) work inside containers
- Sequential handoff via shared filesystem works (manual docker run)
- Ralph runs inside team containers (delegation smoke test)

### What's not proven

- Archon orchestrating workflow nodes that run in separate Docker containers
- Parallel containers with workspace isolation and merge
- Credential injection automated (not manual mount)
- Loop signal workaround with containerised nodes
- Any Archon workflow running end-to-end with per-node team images

### Upstream status (checked 2026-04-16)

- **Issue #1197** (ContainerProvider): open, zero comments, no PR, no upstream work
- **Issue #1126** (loop signal bug): open, 3 comments, no fix
- **Archon codebase**: no `image` field in node schema, no ContainerProvider, no Docker references in executor. Only WorktreeProvider exists.

### Architecture discovery

Analysis of Archon's `dag-executor.ts` (3036 lines) revealed that isolation happens **once at workflow level** (a single worktree created by the CLI command), not per-node. The executor passes one shared `cwd` to all nodes. There is no per-node isolation dispatch point.

This means the original Phase 4 approach (patching the executor to route `image:` nodes to ContainerProvider) doesn't match Archon's architecture. The ContainerProvider interface in `packages/isolation/src/types.ts` is designed for workflow-level isolation, not per-node dispatch.

## 2. Revised Approach: Workflow Preprocessing

Instead of patching Archon's executor, we **preprocess** the workflow YAML. Archon already supports **bash nodes** — nodes that run a shell command instead of spawning Claude. The DAG executor handles them natively (`executeBashNode` at line 1305). Topology, dependencies, parallel execution, trigger rules — all work with bash nodes.

### How it works

1. User writes workflow YAML with `image:` fields (the format established in Phase 2)
2. A preprocessor script transforms each `image:` node into a bash node that runs `docker run sdlc-worker:<team>` with the appropriate workspace mount, credential injection, and command/prompt
3. Nodes without `image:` pass through unchanged (Archon runs them locally)
4. Archon executes the transformed YAML natively — no patches needed
5. Each bash node spawns its own Docker container with the correct team image
6. The container's existing entrypoint handles credentials, git init, loop workaround, and execution

### Example transform

```yaml
# User writes (team-aware):
nodes:
  - id: implement
    command: sdlc-implement
    image: sdlc-worker:dev-team
    context: fresh

  - id: review
    command: sdlc-review
    image: sdlc-worker:review-team
    depends_on: [implement]
    context: fresh

# Preprocessor generates (Archon-native):
nodes:
  - id: implement
    bash: |
      docker run --rm \
        -v "${SDLC_RUN_WORKSPACE}:/workspace" \
        -v "${SDLC_CREDENTIALS}:/home/sdlc/.claude/.credentials.json:ro" \
        -e "CLAUDE_PROMPT=$(cat .archon/commands/sdlc-implement.md)" \
        sdlc-worker:dev-team
    depends_on: []

  - id: review
    bash: |
      docker run --rm \
        -v "${SDLC_RUN_WORKSPACE}:/workspace" \
        -v "${SDLC_CREDENTIALS}:/home/sdlc/.claude/.credentials.json:ro" \
        -e "CLAUDE_PROMPT=$(cat .archon/commands/sdlc-review.md)" \
        sdlc-worker:review-team
    depends_on: [implement]
```

### Why this works

- **Archon handles the DAG** — dependencies, parallel layers, trigger rules, timeout, retry. All native.
- **Each bash node spawns its own container** — different team image per node = per-node enforcement.
- **The entrypoint handles everything inside the container** — credential setup, git init, loop workaround, Claude/Ralph execution. Already proven in acceptance test.
- **Ralph works inside containers** — the delegation smoke test already runs `ralph run` inside Docker. Bash nodes that `docker run` team images with Ralph get the full orchestration chain.
- **No Archon patches needed** — bash nodes are a standard feature. The node schema `image?` patch and ContainerProvider are no longer required for Phase 4.
- **Output capture** — bash node stdout is captured by Archon and available via `$node.output` references in downstream nodes.

### What about the existing ContainerProvider patch?

The `container-provider.ts`, node schema patch, and executor import patch (from Phase 2) remain in the Docker image as forward-looking work for Archon's eventual native container support. They don't interfere with the bash-node approach and will self-deactivate if Archon implements native per-node containers. Phase 4 does not depend on them.

## 3. Scope

Phase 4 is four things:

1. **Workflow preprocessor** — transforms `image:` nodes into bash nodes that `docker run` team containers
2. **Hybrid workspace management** — shared volume for sequential, git branch/merge for parallel
3. **Credential injection** — three-tier fallback (Keychain → volume → config), automated by preprocessor
4. **End-to-end Archon proof** — run the miniproject workflow through Archon with team containers

Phase 4 is NOT:
- Workflow authoring (creating custom workflow YAMLs)
- Level 1 onramp (single command to first delegated run)
- Production hardening (network policies, image size, security)
- CI/CD integration or cloud registry push

Those are Phase 5+.

## 4. Workflow Preprocessor

### 4.1 Script: `preprocess_workflow.py`

A Python script that reads a workflow YAML with `image:` fields and produces an Archon-native YAML with bash nodes.

**Input:** workflow YAML with optional `image:` field on nodes
**Output:** transformed workflow YAML where `image:` nodes become bash nodes

**Location:** `plugins/sdlc-workflows/scripts/preprocess_workflow.py`

**Transform rules:**

| Original field | Bash node equivalent |
|----------------|---------------------|
| `command: X` | `cat .archon/commands/X.md` piped as `CLAUDE_PROMPT` |
| `prompt: "..."` | Literal string passed as `CLAUDE_PROMPT` |
| `image: sdlc-worker:team` | `docker run --rm sdlc-worker:team` |
| `context: fresh` | Container always starts fresh (inherent) |
| `model: X` | `-e "CLAUDE_MODEL=X"` passed to container |
| `loop: {...}` | Container runs with `ARCHON_WORKFLOW` pointing to a single-node loop workflow inside the container |
| `depends_on` | Preserved as-is (Archon handles) |
| `trigger_rule` | Preserved as-is (Archon handles) |
| No `image:` | Node passes through unchanged |

**Preserved fields** (passed through to Archon): `id`, `depends_on`, `trigger_rule`, `when`, `timeout`, `idle_timeout`, `retry`.

### 4.2 Loop node handling

Loop nodes (`until:`, `max_iterations:`) are more complex because Archon's loop executor manages iteration state internally. For `image:` loop nodes, the preprocessor generates a bash node that runs a simple iteration loop:

```bash
for i in $(seq 1 $MAX_ITERATIONS); do
    OUTPUT=$(docker run --rm \
        -v "$WORKSPACE:/workspace" \
        -v "$CREDS:/home/sdlc/.claude/.credentials.json:ro" \
        sdlc-worker:dev-team \
        claude --dangerously-skip-permissions -p "$PROMPT")
    echo "$OUTPUT"
    if echo "$OUTPUT" | grep -q "$UNTIL_SIGNAL"; then
        echo "LOOP_COMPLETE: signal detected at iteration $i"
        break
    fi
done
```

This replaces Archon's loop executor for containerised nodes. The loop runs on the host, each iteration spawns a fresh container (matching `fresh_context: true`).

### 4.3 Integration with `workflows-run` skill

The existing `workflows-run` skill calls `archon workflow run`. Updated flow:

1. Skill reads the requested workflow YAML
2. If any node has `image:`, run `preprocess_workflow.py` to produce a transformed YAML in `.archon/workflows/.generated/`
3. Call `archon workflow run` against the transformed YAML
4. If no nodes have `image:`, call Archon directly (no transformation needed)

## 5. Hybrid Workspace Management

### 5.1 Sequential nodes — shared volume

The preprocessor creates a Docker volume for each workflow run:

```bash
SDLC_RUN_WORKSPACE=$(mktemp -d)  # or docker volume
```

Each bash node mounts this directory at `/workspace`. Sequential nodes see each other's changes because they share the same filesystem. This is the same pattern the acceptance test proved.

### 5.2 Parallel nodes — branch-per-node with merge

When the preprocessor detects parallel nodes (multiple nodes with the same `depends_on`), it generates:

1. **Pre-fork bash node** — commits current state, creates per-node branches:
   ```bash
   cd $WORKSPACE && git add -A && git commit -m "pre-fork" --allow-empty
   git branch archon/$RUN_ID/security-review
   git branch archon/$RUN_ID/architecture-review
   ```

2. **Per-node bash nodes** — each parallel node checks out its branch before running:
   ```bash
   cd $WORKSPACE && git checkout archon/$RUN_ID/security-review
   docker run --rm -v $WORKSPACE:/workspace ... sdlc-worker:review-team
   cd $WORKSPACE && git add -A && git commit -m "node: security-review"
   ```

3. **Post-merge bash node** — merges all parallel branches:
   ```bash
   cd $WORKSPACE && git checkout main
   git merge archon/$RUN_ID/security-review -X theirs -m "merge: security-review"
   git merge archon/$RUN_ID/architecture-review -X theirs -m "merge: architecture-review"
   git branch -d archon/$RUN_ID/security-review archon/$RUN_ID/architecture-review
   ```

The merge node is injected by the preprocessor between the parallel layer and the downstream node. The user's workflow YAML is unchanged.

### 5.3 Workspace cleanup

The workspace directory is cleaned up after the workflow completes. If `--keep-workspace` is passed to `workflows-run`, it is preserved for debugging.

## 6. Credential Injection

### 6.1 Three-tier fallback (b→a→c)

The preprocessor resolves credentials before generating bash nodes. The credential path is injected into every `docker run` command as a volume mount.

**Tier 1 — macOS Keychain (zero-config):**
- Run `security find-generic-password -s "Claude Code-credentials" -w` on the host
- If found, write to a temp file with mode 600, owned by current user
- Mount into containers at `/home/sdlc/.claude/.credentials.json:ro`
- Temp file cleaned up after workflow run

**Tier 2 — Credential volume:**
- Check for Docker volume `sdlc-claude-credentials`
- If exists and contains `.credentials.json`, use it
- Mount into containers at `/home/sdlc/.claude-creds/:ro`
- Container entrypoint copies to correct location

**Tier 3 — Explicit config:**
- Check for `.archon/credentials.yaml`:
  ```yaml
  credential_path: /path/to/.credentials.json
  ```
- Mount the specified file into containers

### 6.2 Credential resolver script

`plugins/sdlc-workflows/scripts/resolve_credentials.py` — resolves which tier to use, returns the mount argument for `docker run`.

### 6.3 Health check integration

`workflows-setup --health-check` tests the fallback chain and reports which tier is active.

### 6.4 Login script fix

Fix `login.sh` so Tier 2 works reliably:
- Interactive terminal detection (fail with clear message if not TTY)
- Clean volume creation on each run
- Extract credential file with correct ownership (UID 1001)
- Verify auth works before declaring success

## 7. End-to-End Proof

### 7.1 Sequential test

Run the miniproject's `feature-pipeline.yaml` through Archon:

1. `workflows-run` detects `image:` nodes, runs preprocessor
2. Preprocessor generates bash-node YAML in `.archon/workflows/.generated/`
3. `archon workflow run` executes the transformed workflow
4. Node `implement` — bash node spawns `sdlc-worker:dev-team` container, Claude implements priority feature
5. Node `review` — bash node spawns `sdlc-worker:review-team` container, Claude reviews changes
6. Verify: Archon reports completion, both nodes produced output, workspace has commits + review

### 7.2 Parallel test

Extended miniproject workflow (`parallel-review-pipeline.yaml`):

```yaml
name: parallel-review-pipeline
nodes:
  - id: implement
    command: sdlc-implement
    image: sdlc-worker:dev-team

  - id: security-review
    command: sdlc-security-review
    image: sdlc-worker:review-team
    depends_on: [implement]

  - id: architecture-review
    command: sdlc-architecture-review
    image: sdlc-worker:review-team
    depends_on: [implement]

  - id: synthesise
    prompt: |
      Synthesise the security and architecture reviews.
      Security: $security-review.output
      Architecture: $architecture-review.output
    image: sdlc-worker:dev-team
    depends_on: [security-review, architecture-review]
    trigger_rule: all_success
```

Proves: parallel fork, concurrent containers, branch merge, downstream node sees both outputs.

### 7.3 Test pyramid (final)

| Layer | Count | Duration | What it proves |
|-------|-------|----------|---------------|
| Unit tests | 138+ | <1s | Scripts work as Python functions |
| Phase 2 smoke | 7 | ~10s | Docker build pipeline, read-only enforcement |
| Phase 3 Python smoke | 8 | <1s | Management scripts together |
| Phase 3 container smoke | 16 | ~30s | Scripts inside containers with miniproject |
| Acceptance test | 7 | ~3 min | Real Claude Code in manual containers |
| **E2E sequential** | **~6** | **~5 min** | **Archon orchestrates sequential containerised workflow** |
| **E2E parallel** | **~8** | **~5 min** | **Archon orchestrates parallel fork/merge workflow** |

## 8. Sub-Feature Decomposition

| Sub-feature | Scope | Depends On | Deliverable |
|---|---|---|---|
| **P4-0: Workflow preprocessor** | Transform `image:` nodes to bash nodes. Handle command resolution, prompt passthrough, model override, environment variables. | Phase 3 | `preprocess_workflow.py`, tests |
| **P4-1: Loop node preprocessing** | Handle `image:` + `loop:` nodes with bash iteration wrapper. | P4-0 | Loop handling in preprocessor |
| **P4-2: Credential resolver** | Three-tier fallback (Keychain → volume → config). Returns docker mount argument. | None | `resolve_credentials.py`, tests |
| **P4-3: Login script fix** | Fix TTY handling, clean volume creation, ownership. | None | Updated `login.sh` |
| **P4-4: Workspace management** | Shared directory for sequential. Branch/merge injection for parallel. Cleanup. | P4-0 | Workspace logic in preprocessor |
| **P4-5: workflows-run integration** | Update skill to detect `image:` nodes, preprocess, run transformed YAML. | P4-0, P4-2 | Updated `workflows-run/SKILL.md` |
| **P4-6: Health check update** | Add credential tier reporting to `workflows-setup --health-check`. | P4-2 | Updated `workflows-setup/SKILL.md` |
| **P4-7: E2E sequential proof** | Run feature-pipeline through Archon against miniproject. | P4-0 through P4-5 | `run-e2e.sh`, test results |
| **P4-8: E2E parallel proof** | Run parallel-review-pipeline through Archon. Verify fork, merge, synthesise. | P4-4, P4-7 | Parallel workflow, extended `run-e2e.sh` |

### Execution order

```
P4-2 (credentials) ─────────────┐
P4-3 (login fix) ───────────────┤
                                 ├─── P4-5 (workflows-run) ─── P4-7 (E2E sequential)
P4-0 (preprocessor) ── P4-1 ────┤                                     │
                       (loops)   │                              P4-8 (E2E parallel)
                                 │
P4-4 (workspace mgmt) ──────────┘
                                 
P4-6 (health check) ── standalone, can run anytime after P4-2
```

P4-2, P4-3, P4-0, and P4-4 can all start in parallel.

## 9. What Phase 4 Does NOT Do

- **Patch Archon's executor** — the bash-node preprocessing approach means no Archon patches are needed
- **Workflow authoring** — no skill for creating custom workflow YAMLs (Phase 5+)
- **Level 1 onramp** — no single-command first-run experience (Phase 5+)
- **Network policies** — no outbound restriction on containers (Phase 5)
- **Image size optimisation** — 3.5 GB base image stays as-is (Phase 5)
- **CI/CD integration** — no GitHub Actions workflow for containerised runs (Phase 5)

## 10. Success Metrics

| Metric | Target | When |
|---|---|---|
| Preprocessor transforms image nodes | Single-node workflow with `image:` produces valid bash-node YAML | P4-0 |
| Credential resolver works | Health check reports active tier on macOS and volume fallback | P4-2 |
| Login script works | Interactive login creates valid credential volume | P4-3 |
| Sequential workflow runs | Two-node feature-pipeline completes through Archon, both nodes produce output | P4-7 |
| Agent enforcement under Archon | Dev container has dev agents, review container has review agents | P4-7 |
| Parallel workflow runs | Two parallel review nodes complete, synthesise sees both outputs | P4-8 |
| Branch merge works | Parallel branches created, merged, downstream node sees merged state | P4-8 |
| No regression | All existing tests (138+ unit, 7+8+16 smoke, 7 acceptance) still pass | All |

# Design Spec: Phase 4 — Archon Orchestration (EPIC #96)

**Date**: 2026-04-16
**Status**: Draft — pending review
**EPIC**: #96 — Containerised Claude Code Workers
**Phase**: 4 of 5 (Orchestration)
**Depends on**: Phase 3 (Workforce Management) — complete, 20 commits on `feature/96-sdlc-workflows`
**Next**: Phase 5 (Production Hardening) — not yet scoped

## 1. Problem Statement

Phases 1-3 proved that team containers can do real work with enforcement. The acceptance test runs real Claude Code inside `sdlc-worker:dev-team` and `sdlc-worker:review-team`, implements features, reviews changes, and proves agent isolation. But the test manages containers manually via `docker run` — it is the orchestrator.

In production, Archon is the orchestrator. It reads workflow YAML, manages node dependencies, handles parallel execution, and coordinates output. Phase 4 proves that Archon can do what the acceptance test does manually.

### What's proven (Phases 1-3)

- Three-tier Docker image model builds correctly
- Team manifests define and enforce agent boundaries
- Different containers see different agents
- Claude Code authenticates and does real work inside team containers
- Management scripts (inventory, status, coaching, overrides) work inside containers
- Sequential handoff via shared filesystem works (manual docker run)

### What's not proven

- Archon's executor routing `image:` nodes to Docker containers
- Parallel containers with workspace isolation and merge
- Credential injection managed by ContainerProvider (not manual mount)
- Loop signal workaround with containerised nodes
- Any Archon workflow running end-to-end with team images

### Upstream status (checked 2026-04-16)

- **Issue #1197** (ContainerProvider): open, zero comments, no PR, no upstream work
- **Issue #1126** (loop signal bug): open, 3 comments, no fix
- **Archon codebase**: no `image` field in node schema, no ContainerProvider, no Docker references in executor. Only WorktreeProvider exists.
- **Both our patches are still needed.** Nothing has changed upstream.

## 2. Scope

Phase 4 is four things:

1. Complete the ContainerProvider executor wiring
2. Hybrid workspace management (shared volume sequential, git fork/merge parallel)
3. Credential injection with three-tier fallback
4. End-to-end Archon workflow proof against the miniproject

Phase 4 is NOT:
- Workflow authoring (creating custom workflow YAMLs)
- Level 1 onramp (single command to first delegated run)
- Production hardening (network policies, image size, security)
- CI/CD integration or cloud registry push

Those are Phase 5+.

## 3. ContainerProvider Completion

### 3.1 Current State

Three patches applied at Docker build time in `plugins/sdlc-workflows/patches/apply-patches.sh`:

1. `container-provider.ts` — Docker CLI wrapper implementing create/destroy/exec/healthCheck. **Complete.**
2. Node schema patch — adds `image?: string` to `dag-node.ts`. **Complete.**
3. Executor routing — imports ContainerProvider. **Incomplete — only adds the import, no routing logic.**

### 3.2 What Needs to Change

Extend patch 3 (`apply-patches.sh` step 3) to inject routing logic into the DAG executor. When the executor processes a node:

```
if node.image is set:
    use ContainerProvider.create({ image: node.image, workdir, env })
else:
    use WorktreeProvider.create({ workdir, codebaseId }) [existing behavior]
```

The routing check is inserted before the existing `WorktreeProvider.create()` call. Nodes without `image:` are completely unaffected — zero behavior change for non-containerised workflows.

### 3.3 ContainerProvider Lifecycle per Node

1. **Create** — `docker run -d` with the node's image, run volume mounted at `/workspace`, credential file mounted at `/home/sdlc/.claude/.credentials.json`, environment variables from workflow config
2. **Execute** — `docker exec` to run `claude --dangerously-skip-permissions -p "<node prompt>"` inside the container. Capture stdout/stderr for Archon's output handling.
3. **Commit** — After claude exits, `docker exec git add -A && git commit` to persist workspace changes
4. **Destroy** — `docker rm -f` to clean up the container

### 3.4 Self-Deactivation

Same pattern as the ARM64 patch. `apply-patches.sh` checks:
- If `ContainerProvider` already exists in the executor source, skip patch 3
- If `image` field already exists in the node schema, skip patch 2
- If `container.ts` already exists in the providers directory, skip patch 1

When Archon implements native container support, our patches become no-ops.

## 4. Hybrid Workspace Management

### 4.1 Design Principle

Sequential nodes share a workspace. Parallel nodes fork and merge. This matches how real development works — sequential steps build on each other, parallel steps work independently and integrate.

### 4.2 Sequential Nodes — Shared Volume

ContainerProvider creates a Docker volume for each workflow run:

```
docker volume create archon-run-<run-id>
```

Every sequential node mounts this volume at `/workspace`. When a node completes, its changes are committed to git inside the volume. The next node starts, sees the previous node's commits, and continues.

This is exactly what the acceptance test proved — managed by ContainerProvider instead of manual `docker run`.

### 4.3 Parallel Nodes — Branch-per-Node with Merge

When the executor encounters a parallel fork (multiple nodes sharing the same `depends_on`):

1. **Fork** — ContainerProvider creates a branch per parallel node from the current HEAD:
   ```
   archon/<run-id>/<node-id>
   ```
2. **Clone** — Each parallel node gets its own volume, cloned from the run volume at the fork point:
   ```
   docker volume create archon-run-<run-id>-<node-id>
   docker run --rm -v archon-run-<run-id>:/source:ro -v archon-run-<run-id>-<node-id>:/dest alpine cp -a /source/. /dest/
   ```
3. **Execute** — Parallel containers run concurrently, each working on its own branch in its own volume
4. **Merge** — When all parallel nodes complete, ContainerProvider merges their branches back to the run branch:
   ```
   git checkout main-run-branch
   git merge archon/<run-id>/security-review
   git merge archon/<run-id>/architecture-review
   ```
   Sequential merge in dependency order. Conflicts resolved with `git merge -X theirs` (the later merge takes precedence on conflicting lines). Conflict occurrence logged to Archon output so the synthesise node can flag it.
5. **Cleanup** — Parallel volumes destroyed after successful merge

### 4.4 Volume Lifecycle

| Event | Action |
|-------|--------|
| Workflow starts | Create `archon-run-<run-id>` volume, init git repo |
| Sequential node starts | Mount run volume at `/workspace` |
| Parallel fork | Clone run volume to per-node volumes, create branches |
| Parallel node completes | Commit changes to node branch |
| All parallel nodes complete | Merge branches back to run branch, destroy node volumes |
| Workflow completes | Destroy run volume (or preserve with `--keep-workspace`) |

## 5. Credential Injection

### 5.1 Three-Tier Fallback (b→a→c)

ContainerProvider tries each tier in order. The first that succeeds is used for all containers in the run.

**Tier 1 — macOS Keychain (zero-config):**
- Run `security find-generic-password -s "Claude Code-credentials" -w` on the host
- If found, write the JSON to a temp file with mode 600, owned by UID 1001
- Mount the temp file at `/home/sdlc/.claude/.credentials.json:ro` in every container
- Temp file cleaned up when the workflow run completes
- Only works on macOS with Claude Code desktop installed

**Tier 2 — Credential volume:**
- Check for Docker volume `sdlc-claude-credentials`
- If exists and contains `.credentials.json`, mount it read-only at `/home/sdlc/.claude-creds/`
- Container startup copies the file into `.claude/` with correct ownership (UID 1001, mode 600)
- Volume created by `login.sh` (interactive, requires TTY)

**Tier 3 — Explicit config:**
- Check for `.archon/credentials.yaml` in the project directory:
  ```yaml
  credential_path: /path/to/.credentials.json
  ```
- Mount the specified file at `/home/sdlc/.claude/.credentials.json:ro`
- Covers CI/CD and Linux environments

### 5.2 Health Check Integration

`workflows-setup --health-check` tests the fallback chain:

```
Credential injection:
  Tier 1 (Keychain):     OK — Claude Code credentials found
  Tier 2 (Volume):       SKIP — Keychain succeeded
  Tier 3 (Config):       SKIP — Keychain succeeded
  Active tier:           Keychain
```

Or when Keychain fails:

```
Credential injection:
  Tier 1 (Keychain):     FAIL — not macOS or no keychain entry
  Tier 2 (Volume):       OK — sdlc-claude-credentials volume found
  Active tier:           Volume
```

Or when nothing works:

```
Credential injection:
  Tier 1 (Keychain):     FAIL — not macOS
  Tier 2 (Volume):       FAIL — volume not found
  Tier 3 (Config):       FAIL — .archon/credentials.yaml not found
  Active tier:           NONE

  Run: tests/integration/workforce-smoke/login.sh
  Or create: .archon/credentials.yaml with credential_path
```

### 5.3 Security

- Credential files mounted read-only into containers
- Temp files from Keychain extraction: mode 600, cleaned up after run
- No credentials baked into images or written to logs
- Credential source reported in health check output (tier name only, not content)

## 6. End-to-End Proof

### 6.1 Test Structure

New test script: `tests/integration/workforce-smoke/run-e2e.sh`

This test runs the miniproject's workflow through Archon — not manual `docker run`. It proves the full orchestration path: Archon reads the workflow, ContainerProvider spawns team containers, workspace hands off between nodes, credentials are injected, real work happens.

### 6.2 Sequential Test (feature-pipeline)

Using the existing miniproject workflow (`feature-pipeline.yaml`):

1. Archon starts workflow `feature-pipeline`
2. Node `implement` — Archon routes to ContainerProvider, spawns `sdlc-worker:dev-team`, injects credentials, mounts run volume. Claude implements the priority feature. Container exits, changes committed.
3. Node `review` — ContainerProvider spawns `sdlc-worker:review-team`, same run volume. Claude reviews changes, writes `review-output.md`. Container exits.
4. Verify:
   - Archon reports workflow completed
   - Git log shows commits from both nodes
   - `src/app.py` has priority field
   - `review-output.md` exists with structured content
   - Agent enforcement: dev container had dev agents, review container had review agents

### 6.3 Parallel Test (extended workflow)

Extend the miniproject with a parallel review workflow (`parallel-review-pipeline.yaml`):

```yaml
name: parallel-review-pipeline
nodes:
  - id: implement
    command: implement
    image: sdlc-worker:dev-team
    context: fresh

  - id: security-review
    command: security-review
    image: sdlc-worker:review-team
    depends_on: [implement]
    context: fresh

  - id: architecture-review
    command: architecture-review
    image: sdlc-worker:review-team
    depends_on: [implement]
    context: fresh

  - id: synthesise
    command: synthesise
    image: sdlc-worker:dev-team
    depends_on: [security-review, architecture-review]
    trigger_rule: all_success
    context: fresh
```

This proves:
- Parallel fork: security-review and architecture-review run concurrently in separate containers
- Branch-per-node: each parallel node works on its own branch
- Merge: synthesise node sees output from both reviews after branch merge
- The full diamond pattern: sequential → parallel fork → merge → sequential

### 6.4 Test Pyramid (Final)

| Layer | Count | Duration | What it proves |
|-------|-------|----------|---------------|
| Unit tests | 138+ | <1s | Scripts work as Python functions |
| Phase 2 smoke | 7 | ~10s | Docker build pipeline, read-only enforcement |
| Phase 3 Python smoke | 8 | <1s | Management scripts together |
| Phase 3 container smoke | 16 | ~30s | Scripts inside containers with miniproject |
| Acceptance test | 7 | ~3 min | Real Claude Code in manual containers |
| **E2E sequential** | **~6** | **~5 min** | **Archon orchestrates sequential team workflow** |
| **E2E parallel** | **~8** | **~5 min** | **Archon orchestrates parallel fork/merge workflow** |

## 7. Sub-Feature Decomposition

| Sub-feature | Scope | Depends On | Deliverable |
|---|---|---|---|
| **P4-0: Complete executor routing patch** | Extend apply-patches.sh to inject ContainerProvider routing logic into the DAG executor. Add unit test for patch detection. | Phase 3 | Updated apply-patches.sh, routing logic |
| **P4-1: ContainerProvider node lifecycle** | Implement create/execute/commit/destroy flow for a single node. Test with a one-node workflow. | P4-0 | Updated container-provider.ts |
| **P4-2: Shared volume for sequential nodes** | Create/mount/cleanup run volumes. Test with two sequential nodes. | P4-1 | Volume management in ContainerProvider |
| **P4-3: Credential injection fallback chain** | Implement b→a→c credential detection. Mount credentials into spawned containers. Update health check. | P4-1 | Credential resolver, health check update |
| **P4-4: E2E sequential proof** | Run feature-pipeline through Archon against miniproject. Verify implementation + review + enforcement. | P4-2, P4-3 | run-e2e.sh (sequential), test results |
| **P4-5: Branch-per-node for parallel execution** | Fork branches at parallel points, clone volumes, merge after completion. | P4-2 | Branch/merge logic in ContainerProvider |
| **P4-6: E2E parallel proof** | Run parallel-review-pipeline through Archon. Verify fork, concurrent execution, merge, synthesise. | P4-4, P4-5 | run-e2e.sh (parallel), parallel-review-pipeline.yaml |
| **P4-7: Login script fix** | Fix login.sh TTY handling so Tier 2 credential volume works reliably from interactive terminals. | None | Updated login.sh |

### Execution Order

```
P4-0 (executor patch) → P4-1 (node lifecycle) → P4-2 (sequential volumes)
                                                       ↓
P4-7 (login fix) → P4-3 (credential injection) ───────→ P4-4 (E2E sequential)
                                                              ↓
                                               P4-5 (parallel branches) → P4-6 (E2E parallel)
```

P4-7 (login fix) can run in parallel with everything — it's independent.

## 8. What Phase 4 Does NOT Do

- **Workflow authoring** — no skill for creating custom workflow YAMLs (Phase 5+)
- **Level 1 onramp** — no single-command first-run experience (Phase 5+)
- **Network policies** — no outbound restriction on containers (Phase 5)
- **Image size optimisation** — 3.5 GB base image stays as-is (Phase 5)
- **Plugin allowlist** — no supply chain gating (Phase 5)
- **Multi-architecture images** — ARM64/AMD64 only via Docker Desktop's built-in emulation (Phase 5)
- **CI/CD integration** — no GitHub Actions workflow for containerised runs (Phase 5)
- **Cost tracking** — no token/time accounting per node (Phase 5+)

## 9. Success Metrics

| Metric | Target | When |
|---|---|---|
| Single-node container workflow | Archon spawns one container, claude runs, output captured | P4-1 |
| Credential injection works | Health check reports active tier, container authenticates | P4-3 |
| Sequential two-node workflow | implement → review via shared volume, both produce output | P4-4 |
| Agent enforcement under Archon | Different team images have different agent inventories | P4-4 |
| Parallel fork/merge | Two review nodes run concurrently, synthesise sees both outputs | P4-6 |
| Loop workaround in containers | Loop node with `until:` completes correctly (not max_iterations) | P4-4 |
| No regression | All existing tests (138 unit, 7+8+16 smoke, 7 acceptance) still pass | All |

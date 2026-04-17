# Phase 5: Production Hardening — Design Spec

**EPIC**: #96 — Containerised Claude Code Workers
**Phase**: 5 of 5
**Branch**: `feature/96-sdlc-workflows`
**Prerequisite**: Phases 1-4 complete (sequential + parallel E2E proven)

## Goal

Harden containerised Claude Code workers for local developer workstation use. Establish security defaults, entrypoint robustness, image optimizations, and a full documentation suite written for Claude Code as the primary consumer. CI/CD automation (image registry, scanning, multi-arch builds) is explicitly out of scope — that will be a separate issue/PR after this branch merges.

## Design Principles

1. **Interleaved document-then-implement cycles** — each sub-feature follows: document how it should work in CLAUDE-CONTEXT → implement the change → verify docs match reality → iterate. Documentation and implementation co-evolve so neither drifts.

2. **Documentation targets Claude Code** — the CLAUDE-CONTEXT reference, authoring skill, and troubleshooting guide are written so Claude Code can generate correct workflows, manifests, and command prompts on the first try. Humans benefit too, but Claude is the primary consumer.

3. **Workstation-first** — all changes target `docker run` on Mac/Linux developer machines. No Kubernetes manifests, no registry push, no SBOM generation.

## Sub-Feature 1: CLAUDE-CONTEXT Reference File

**Deliverable**: `CLAUDE-CONTEXT-workflows.md` at the repo root.

The single source of truth for the containerised worker system. Every other document and skill references this file rather than duplicating schema details.

**Contents**:

| Section | What it covers |
|---------|---------------|
| Workflow YAML schema | All fields: `name`, `description`, `provider`, `nodes[]`. Node fields: `id`, `command`, `image`, `depends_on`, `trigger_rule`, `context`, `loop`, `timeout`. Valid values, required vs optional. |
| Team manifest schema | All fields: `name`, `base_image`, `plugins[]`, `agents[]`, `skills[]`, `team_extend[]`. Validation rules and constraints. |
| Command prompt format | What goes in `.archon/commands/*.md`. Expected structure: role framing, task description, output location, commit instruction. |
| Preprocessing rules | How `image:` nodes become bash nodes. What fields are preserved (`id`, `depends_on`, `trigger_rule`, `when`, `timeout`, `retry`). How `CLAUDE_PROMPT` env var is passed. Loop node transformation. |
| Credential model | Three-tier fallback: Keychain (tier 1, Mac zero-config) → Docker volume `sdlc-claude-credentials` (tier 2, login.sh) → `.archon/credentials.yaml` config (tier 3). Mount args format. |
| Docker execution model | Workspace mount at `/workspace`, credential mount at `/home/sdlc/.claude/.credentials.json`, plugin read-only enforcement, entrypoint flow (auth setup → git init → loop workaround → Claude execution). |
| Security model | Non-root user (UID 1001), read-only filesystem with tmpfs writable paths, dropped capabilities, credential cleanup on exit. |
| Image architecture | Three-tier model: base (toolchain) → full (all plugins) → team (manifest-scoped subset). Layer structure, baseline sizes. |

**Integration**: Add to the context loading table in `CLAUDE-CORE.md` so Claude loads it when working with workflows, teams, or containers.

## Sub-Feature 2: Security Hardening

**2a. Read-only filesystem + tmpfs writable paths**

All `docker run` invocations add:
```
--read-only
--tmpfs /tmp:rw,noexec,nosuid
--tmpfs /home/sdlc/.claude:rw,noexec,nosuid
```

`/workspace` remains writable via the existing volume mount. Plugins at `/home/sdlc/.claude/plugins/` are already `chmod -R a-w` from the team Dockerfile build.

**Changes to**:
- `preprocess_workflow.py` — `_build_docker_run()` adds the flags to generated commands
- E2E test and acceptance test — update direct docker run invocations
- CLAUDE-CONTEXT — document writable paths and why

**2b. Capability dropping**

All `docker run` invocations add `--cap-drop ALL`. No capabilities are needed — containers only run Claude Code CLI and git.

**Changes to**: same files as 2a.

**2c. Credential cleanup on exit**

Entrypoint adds a trap:
```bash
cleanup() {
    rm -f /home/sdlc/.claude/.credentials.json
    # kill child processes
    kill -- -$$ 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT EXIT
```

Ensures credentials don't persist if a container exits abnormally.

## Sub-Feature 3: Entrypoint Robustness

**3a. Signal handling + graceful shutdown**

The `trap cleanup SIGTERM SIGINT EXIT` from 2c also handles graceful shutdown: kills child processes (Claude, git) and exits with appropriate code. `docker stop` sends SIGTERM → trap fires → clean exit.

**3b. Configurable timeout**

New `CLAUDE_TIMEOUT` env var (default: 300 seconds).

```bash
timeout "${CLAUDE_TIMEOUT:-300}" claude --dangerously-skip-permissions -p "$CLAUDE_PROMPT"
```

If Claude hangs, the container exits rather than consuming resources indefinitely. Overridable per-node: workflow preprocessor passes `CLAUDE_TIMEOUT` as env var if the node has a `timeout:` field.

**3c. Docker HEALTHCHECK**

Added to `Dockerfile.base`:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD test -x /usr/local/bin/claude || exit 1
```

Makes `docker ps` show health state during workflow runs.

## Sub-Feature 4: Image Optimization (Quick Wins)

**4a. Baseline recording**

Record image sizes (`docker images --format`) for base, full, and a typical team image. Record layer breakdown with `docker history`. Document in CLAUDE-CONTEXT.

**4b. Quick-win optimizations**

| Optimization | Rationale |
|-------------|-----------|
| Pin Claude Code CLI version | Reproducible builds, prevents drift |
| Pin Ralph CLI version | Same |
| Remove xz-utils after Bun extraction | Not needed at runtime, saves ~10MB |
| Remove Archon .git directory after install | Not needed at runtime, saves ~5MB |
| Verify apt layer consolidation | Ensure update+install+cleanup is single RUN |

**Not doing**: BuildKit cache mounts, major build restructuring, image size budgets.

## Sub-Feature 5: Documentation Suite

**5a. CLAUDE-CONTEXT-workflows.md** — covered in Sub-Feature 1.

**5b. Quickstart guide**

`plugins/sdlc-workflows/docs/quickstart.md`

Audience: a developer (or Claude Code acting on their behalf) getting started for the first time.

Contents:
- Prerequisites: Docker running, Claude Code authenticated
- Build images: `build-base.sh`, `build-full.sh`
- Create a team: manifest YAML + `build-team.sh`
- Run a workflow: `/sdlc-workflows:workflows-run`
- Verify results
- Credential tiers: Mac (automatic), Linux (`login.sh`), custom (config)
- Each step has exact commands and expected output

**5c. Workflow authoring skill**

`plugins/sdlc-workflows/skills/author-workflow/SKILL.md`

Interactive skill invoked when a user says "create a workflow for X":
- Loads CLAUDE-CONTEXT-workflows.md for schema knowledge
- Asks: what teams are involved, what's the DAG structure, what each node should do
- Generates: workflow YAML, command prompt `.md` files
- Validates: checks referenced teams have manifests, checks command files exist
- Commits the artifacts

This is how workflows get created — not by hand.

**5d. Troubleshooting guide**

`plugins/sdlc-workflows/docs/troubleshooting.md`

Structured as symptom → cause → fix. Written so Claude Code can pattern-match error messages to known solutions.

| Symptom | Cause | Fix |
|---------|-------|-----|
| `authentication_error` / 401 | Expired or missing credentials | Check `resolve_credentials.py --json` output; re-auth Claude Code or run login.sh |
| Container hangs, no output | Claude prompt loop or network issue | Check `CLAUDE_TIMEOUT` env var; `docker stop` triggers graceful cleanup |
| `read-only file system` error | Attempting to write outside allowed paths | Write to `/workspace`, `/tmp`, or `/home/sdlc/.claude` only |
| `no review files found` | Review container ran but Claude didn't follow commit instruction | Check command prompt wording; verify workspace mount |
| `image not found` | Team image not built | Run `build-team.sh <team-name>` |
| `workflow_count` mismatch | New workflows added but test assertions not updated | Update test assertion count |
| `mount_args` errors | Credential path has spaces or special characters | Check resolver output; ensure path is quoted |

## Sub-Feature 6: login.sh Alignment

**6a. Rename volume**

`login.sh` currently creates `sdlc-workforce-smoke-auth`. Change to `sdlc-claude-credentials` — the volume name that `resolve_credentials.py` tier 2 checks. This makes `login.sh` directly feed the resolver with no special config.

**6b. Move to plugin**

Move from `tests/integration/workforce-smoke/login.sh` to `plugins/sdlc-workflows/scripts/login.sh`. It's a user-facing tool, not a test fixture. Update all references.

**6c. Document as fallback**

Quickstart and CLAUDE-CONTEXT document: "On Mac, credentials work automatically via Keychain (tier 1). On Linux or headless environments, run `login.sh` to create a Docker credential volume (tier 2). For custom setups, create `.archon/credentials.yaml` (tier 3)."

## Implementation Order (Interleaved Cycles)

The interleaved approach means each sub-feature cycles through document → implement → verify:

| Order | Sub-Feature | Cycle |
|-------|------------|-------|
| 1 | CLAUDE-CONTEXT (initial draft) | Write schema sections for workflow, manifest, commands, credential model |
| 2 | Security hardening | Update CLAUDE-CONTEXT security section → implement --read-only, --cap-drop, cleanup trap → verify tests pass → update docs |
| 3 | Entrypoint robustness | Update CLAUDE-CONTEXT entrypoint section → implement signal handling, timeout, healthcheck → verify → update docs |
| 4 | Image optimization | Record baselines → apply quick wins → record new sizes → document in CLAUDE-CONTEXT |
| 5 | login.sh alignment | Move + rename volume → verify acceptance test → document credential tiers |
| 6 | Quickstart guide | Write using final commands and flags from steps 2-5 |
| 7 | Author-workflow skill | Write using stable CLAUDE-CONTEXT schema |
| 8 | Troubleshooting guide | Write last — needs knowledge of all failure modes from steps 2-5 |
| 9 | Final verification | Full test pyramid + doc consistency check |

## Test Strategy

Existing test pyramid continues to validate each change:

| Layer | What it catches |
|-------|----------------|
| Unit tests (155) | Script logic regressions |
| Phase 2 smoke (7) | Docker build pipeline breaks |
| Phase 3 Python smoke (8) | Management script regressions |
| Phase 3 container smoke (16) | In-container script failures, including read-only enforcement |
| Acceptance test (7) | Real Claude Code auth/execution failures |
| E2E sequential (6) | Archon orchestration regressions |
| E2E parallel (8) | Parallel fork/merge regressions |

New tests added as needed for:
- Read-only filesystem enforcement (container smoke)
- Timeout behaviour (unit test for entrypoint timeout wrapper)
- Healthcheck pass/fail (container smoke)

## Out of Scope (Future Issue/PR)

- CI/CD image build automation
- Image registry push (ECR, GCR, Docker Hub)
- Multi-arch builds (ARM64 + x86_64)
- Image scanning (Trivy, Snyk)
- SBOM generation
- Image signing (cosign)
- Kubernetes security contexts / network policies
- Performance regression benchmarks

# Feature Proposal: Containerised Claude Code Workers

**Proposal Number:** 96
**Status:** Ready for Review
**Author:** Claude (AI Agent) — with human co-direction
**Created:** 2026-04-06 (feature branch cut); 2026-04-18 (this document, post-implementation)
**Target Branch:** `feature/96-sdlc-workflows`
**Related Issue:** #96

---

## Executive Summary

Deliver a containerised execution model for Claude Code workflows so that an Archon-orchestrated DAG can launch team-scoped Claude Code agents in isolated Docker containers. Each container carries only the plugins, agents, and skills declared in a team manifest — enforcement is at the filesystem level, not via prompt guidance. Credentials are staged at runtime, wiped on exit, and never baked into images. The Archon integration uses bash-node preprocessing rather than executor patching so the coupling to Archon internals stays thin.

This is delivered in five phases across one feature branch:

1. **Phase 1** — Containerised delegation design and single-image execution baseline
2. **Phase 2** — Three-tier Docker image model (base → full → team) and team manifest schema v1.0
3. **Phase 3** — Workforce management (coaching signals, override logging, team validation, fleet reporting)
4. **Phase 4** — Archon orchestration via bash-node preprocessing (sequential + parallel)
5. **Phase 5** — Production hardening (cap-drop, signal handling, timeout, healthcheck, credential staging + cleanup, documentation suite)

---

## Motivation

### Problem Statement

Prior to this EPIC, delegating multi-agent work from Claude Code had four concrete problems:

1. **No enforcement of team composition.** A skill or workflow could declare "use only the X, Y, Z agents" but any agent installed on the local machine remained loadable. This is prompt-level guidance, not policy.
2. **No credential isolation between workflow executions.** Any agent spawned by a delegation shared the top-level user's credentials and plugin installation.
3. **No clean way to run multiple specialist teams from the same machine.** Different teams wanted different plugin sets; swapping them was manual and error-prone.
4. **No orchestration layer.** Multi-step, multi-agent pipelines had to be scripted ad-hoc; there was no DAG executor with parallelism, retries, and trigger-rule semantics.

### User Stories

- As a **workflow author**, I want to declare a team's agents and skills in a manifest and have a container that *cannot* load anything else, so that my pipeline is reproducible.
- As a **workflow runner**, I want to run an Archon DAG that dispatches nodes to team containers so I get parallelism and trigger rules without hand-rolling.
- As a **security-conscious operator**, I want each container to drop all Linux capabilities, refuse privilege escalation, and wipe credentials on exit so a compromised agent cannot escape the container.
- As a **plugin consumer**, I want `/plugin install sdlc-workflows@ai-first-sdlc` to give me working skills, scripts, and Docker assets without manual setup.

---

## Proposed Solution (delivered)

### Architecture overview

Three-tier Docker image inheritance:

- `sdlc-worker:base` — Ubuntu + Node + pinned Claude Code CLI + pinned Ralph + Archon cloned at build time
- `sdlc-worker:full` — base + every plugin (for superset-team scenarios)
- `sdlc-worker:team-<name>` — base + additive `COPY --from=full` of only manifest-listed plugins, agents, and skills

Team manifests (`.archon/teams/<name>.yaml`) declare:

- `schema_version: "1.0"` (required)
- `plugins[]`, `agent_descriptions{}`, `skill_descriptions{}`
- Optional `base_image`, `team_extend[]` (validated but prompt-level only in v1.0)
- `image_built` and `updated` timestamps for staleness detection

Archon integration via `preprocess_workflow.py`:

- Transforms any node with an `image:` field into a `bash:` node running `docker run <flags> <image> <command>`
- Preserves Archon's DAG engine unchanged (topology, parallelism, trigger rules, retries)
- Generated flags include `--cap-drop ALL`, credential mounts, workspace mount, environment, working directory

Credential resolver — three-tier precedence:

1. macOS Keychain (zero-config) — extracted to an ephemeral temp file per run
2. Docker volume (`sdlc-claude-credentials`) — for non-macOS or shared environments
3. Explicit config (`.archon/credentials.yaml`) — last resort

### Acceptance criteria

Given a repo with a Docker daemon running,
When I author a workflow YAML with `image: sdlc-worker:team-example` nodes, deploy the team (`/sdlc-workflows:deploy-team example`), and run the workflow (`/sdlc-workflows:workflows-run my-wf`),
Then the team container launches with only the declared plugins, runs the requested work, and exits with credentials wiped.

Given a parallel fan-out node in a workflow,
When Archon dispatches the fan-out,
Then each branch runs in its own container and the DAG rejoins correctly at fan-in.

Given an attempt to install a plugin at runtime inside a container,
When the container tries to write to `~/.claude/plugins/`,
Then the write fails because the directory is `chmod -R a-w`.

---

## Success Criteria

- [x] Three-tier Docker model builds reproducibly on Apple Silicon and Linux
- [x] Team manifest schema documented and validated
- [x] `/sdlc-workflows:workflows-setup --health-check` reports green on a clean install
- [x] Archon-orchestrated sequential E2E passes (6/6)
- [x] Archon-orchestrated parallel E2E passes (8/8)
- [x] Acceptance test (real Claude Code in team container with real credentials) passes (7/7)
- [x] Credential cleanup trap fires on SIGTERM, SIGINT, EXIT
- [x] `--cap-drop ALL` applied to every generated `docker run`
- [x] 10-check `--pre-push` validation pipeline green
- [x] Plugin install delivers 7 skills, all scripts, docker assets, and docs (see §1.2 of the pre-PR remediation plan)

## Explicit Deferrals (out of scope for this EPIC)

Declared in the Phase 5 design spec and reaffirmed in the pre-PR reviews:

- **CI workflow for Docker image build + Trivy scan** — will be a separate issue
- **SBOM generation + image signing (cosign)** — separate issue
- **Replace `--dangerously-skip-permissions` with a settings-based allowlist** — separate issue
- **`team_extend` runtime injection mechanism** — statically validated in v1.0, runtime contract deferred to a future phase
- **Legacy `.claude-auth` shim removal** — separate migration issue
- **Codebase-index plugin (#118)** — orthogonal, already future-dated

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Archon upstream reshape breaks bash-node preprocessing | High | Preprocessor treats `bash:` as the stable Archon contract; Archon is pinned to a specific commit SHA; patches are skip-marker-guarded |
| Claude Code CLI version drift | Medium | CLI pinned to 2.1.107 in `Dockerfile.base`; upgrade path documented |
| Credential leakage through container filesystem | High | `.claude-creds/` mount is read-only; entrypoint copies to `~/.claude/` and trap wipes on all exit paths; cap-drop ALL + no-new-privileges limit blast radius |
| 18,450-line single PR too large to review | Medium | Phase-indexed PR body with commit ranges, per-dimension reviews archived under `reviews/`, traceability table |
| Test flakiness from shell/docker boundary | Medium | Integration suite isolated per-layer; fix-to-test commit ratio 27:6 logged in retrospective as a known weak point |

---

## Changes Made

Summary — full diff: `git diff --stat main..HEAD` (133 files, +18,450/-28).

| Area | Files |
|---|---|
| Plugin skills (7) | `skills/{workflows-setup,workflows-run,workflows-status,author-workflow,deploy-team,manage-teams,teams-status}/SKILL.md` + plugin copies |
| Workflow templates (4) | `workflows/sdlc-{feature-development,bulk-refactor,commissioned-pipeline,parallel-review}.yaml` |
| Commands (10) | `commands/sdlc-*.md` |
| Plugin scripts (14) | `plugins/sdlc-workflows/scripts/*.py` + shell scripts |
| Docker assets (8) | `plugins/sdlc-workflows/docker/Dockerfile.{base,full}`, `entrypoint.sh`, `build-*.sh`, `docker-compose.yml` |
| Documentation | `CLAUDE-CONTEXT-workflows.md`, `plugins/sdlc-workflows/docs/{quickstart,troubleshooting}.md` |
| Design specs | `docs/superpowers/specs/2026-04-{10,13,16,17}-*.md` |
| Phase plans | `docs/superpowers/plans/2026-04-{10,13,14,16,17}-*.md` |
| Unit tests | `tests/test_*.py` (12 new files, ~128 new tests) |
| Integration tests | `tests/integration/{workforce-smoke,team-smoke}/*` |

---

## References

- Design specs (all checked into this branch): `docs/superpowers/specs/2026-04-10-containerised-delegation-design.md`, `2026-04-13-phase2-team-composition-and-delegation-design.md`, `2026-04-16-phase4-archon-orchestration-design.md`, `2026-04-17-phase5-production-hardening-design.md`
- Phase plans: `docs/superpowers/plans/2026-04-10-containerised-delegation.md` → `2026-04-17-phase5-production-hardening.md`
- Pre-PR multi-dimensional reviews: `reviews/2026-04-17-{security-architect,solution-architect,devops-specialist,code-review-specialist,documentation-architect,agile-coach,swot-synthesis}.md`
- Pre-PR remediation plan: `docs/superpowers/plans/2026-04-17-pre-pr-remediation.md`
- Retrospective: `retrospectives/96-containerised-workers.md`

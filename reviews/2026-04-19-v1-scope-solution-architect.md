# Architecture Review: sdlc-workflows v1 Scope
## Solution Architect — 2026-04-19

---

## 1. Architectural Verdict

**Ship "Status Quo Refined": keep the bash-node preprocessor as the integration
mechanism, cut the workforce-management surface entirely, and rework
`workflows-status` to a single-source SQLite reader — reducing the plugin to
the three capabilities a first-time user actually needs.**

Rationale in one paragraph: the bash-node preprocessing approach is
architecturally correct given Archon's design. Archon has no per-node
executor dispatch; its isolation model is workflow-scoped, not node-scoped
(phase4 design spec, section "Architecture discovery"). Preprocessing `image:`
nodes into `bash: docker run` commands at dispatch time is the minimum viable
adapter that keeps Archon as DAG runner while giving us container-level
isolation per node. The problem is not the core mechanism — it is what we
built around it. The workforce-management layer (team manifests, coaching
signals, fleet reporting) solves a problem that first-time users do not yet
have, and the `sse_stream_follow.py` helper solves a problem (server-launched
runs) that the CLI path does not even exercise. Cutting these two layers
removes roughly 60% of the custom code surface with zero regression to the
user's Day 1 experience.

---

## 2. Coupling Analysis

Evidence base: Archon v0.3.6 capability inventory in the brief (2026-04-19
verified); `workflows_status_query.py` (full file read); `preprocess_workflow.py`
(full file read); Phase 4 design spec section "Architecture discovery".

| Coupling Point | Why It Exists | Risk | What Breaks if Archon Changes | How to Eliminate or Reduce |
|---|---|---|---|---|
| **`bash:` node type in workflow YAML** | Preprocessor rewrites `image:` nodes to `bash:` because Archon has no per-node executor dispatch (dag-executor.ts analysed in Phase 4 spec, section 2). This is a load-bearing fact about Archon's architecture. | GREEN | If Archon renames or drops `bash:` node support, `archon workflow run` rejects every preprocessed workflow. Failure is immediate and loud (Archon validation error), not silent. Mitigation: Archon's `bash:` node is documented in their sample workflows and is a first-class node type, not an internal detail. | File an Archon issue requesting a stable `bash:` node guarantee. The alternative — contributing a `ContainerProvider` upstream (per original plan) — is the right long-term fix but has zero traction (issue #1197, zero comments, no PR). |
| **SQLite schema: `remote_agent_workflow_runs`, `remote_agent_workflow_events` column names** | `workflows_status_query.py` reads these columns directly when `archon serve` is not running (`workflows_status_query.py` line 129, 182-196). The schema is not versioned or documented externally. | AMBER | An Archon schema migration drops or renames a column → `workflows-status` raises `sqlite3.OperationalError` silently swallowed into an empty result set. The user sees "(no workflow runs found)" instead of an error. | Rework (see section 3): issue a `PRAGMA table_info` check on startup and fail fast with a named-version error rather than silently returning empty. This converts a silent failure into a diagnosable one. Longer term: remove the SQLite path and accept that `workflows-status` requires `archon serve`. |
| **REST API shape: `/api/workflows/runs` wrapper** | `fetch_run_detail_via_rest` unwraps `{"run": {...}, "events": [...]}` shape explicitly (`workflows_status_query.py` lines 94-102). The PR body notes this shape broke in dogfood and was fixed mid-EPIC. | AMBER | Archon changes the REST wrapper shape → detail rows show blank. Failure is silent (returns `None`, falls back to SQLite). | Add a discriminating assertion on the REST response shape and log a warning if the known wrapper is absent. Low-effort defensive code. |
| **Archon binary PATH assumption** | `workflows-run` SKILL.md and `workflows-setup` check for `~/.bun/bin/archon` as the canonical install location. Hardcoded in two skill files. | GREEN | Archon changes its install target directory → PATH check misses it. Failure is explicit ("Archon is not installed") rather than silent; user can still find the binary manually. | Already handled correctly in the skills: the skills distinguish "not installed" from "installed but not on PATH" and give the user a fix. No change needed. |
| **SSE endpoint: `/api/stream/__dashboard__`** | `sse_stream_follow.py` (line 1, description) subscribes to this endpoint. Per the brief: "SSE stream only observes runs launched *through the server*" — CLI-launched runs never appear. | RED (scope mismatch) | The endpoint is an internal implementation detail of `archon serve`. If Archon changes the path, `sse_stream_follow.py` breaks silently (fails to connect). More importantly: the script does not help the user observe CLI-launched runs, which is the only run path `workflows-run` uses. | CUT `sse_stream_follow.py`. Its stated use case (server-launched runs, Prometheus exporter foundation) does not apply to v1. The monitoring story for CLI runs is already complete: stderr progress lines + `docker logs -f`. |
| **Archon's `discoverWorkflowsWithConfig(cwd, ...)` walk** | `workflows-run` SKILL.md (step 2b, step 4) seeds a git repo in `$WORKSPACE` and `cd`s into it before calling `archon workflow run`. This is load-bearing: Archon walks to the enclosing git root for `.archon/workflows/` discovery. | AMBER | If Archon changes its discovery root logic (e.g. stops walking to git root, or uses config-file override), workflow discovery breaks in the workspace. Failure: "Workflow not found." | Already mitigated by the workspace git-init pattern, which is documented in the skill. File an Archon issue requesting a `--workflows-dir` flag to make discovery explicit. |

Summary: two RED/AMBER couplings are worth fixing before PR (SQLite schema
probe, SSE scope mismatch). The others are either already mitigated or
acceptably low risk.

---

## 3. Scope Inventory

Reference: "What we currently ship" table in the brief.

### `workflows-setup` skill
**REWORK — simplify health check, keep core setup.**

Real problem solved: first-time user has no Archon, no Docker images, no
`.archon/` scaffold. This is the true Day 1 blocker.

Archon equivalent: `archon setup` installs Archon and does credential
configuration but does not build Docker images or scaffold `.archon/workflows/`.
Our skill fills a genuine gap.

Simplest shape: remove the `--with-docker` / `--workflows-only` flag split.
Default path installs Archon, builds base image, scaffolds `.archon/`. The
flag split is pre-emptive for a user who "already has the base image" — a
case that does not exist on Day 1 and can be added back when it appears.
Remove the Archon PATH workaround from the health check (it is already
handled correctly in `workflows-run` — having it in two places risks drift).

User-visible change: simpler flag surface. No capability loss.

---

### `deploy-team` skill
**CUT.**

Real problem it was solving: build a custom team image from a manifest for
per-node agent enforcement.

Problem with shipping it now: it only makes sense after a user has learned
(a) that default `sdlc-worker:base` runs all agents, (b) that they want
per-node restriction, and (c) how to write a team manifest. No first-time
user reaches this point before they have run at least one workflow. Shipping
it in v1 adds surface the user must read and understand before they can
ignore it.

What the user loses: the ability to create specialist teams from the CLI.
They can still edit Dockerfiles manually (the Dockerfile templates ship with
the plugin). The skill can be restored in v1.1 once the base workflow story
is validated.

---

### `author-workflow` skill
**KEEP AS-IS.**

Real problem solved: workflow YAML authoring is non-trivial. The `image:`,
`loop.stages:`, `depends_on`, `trigger_rule` fields have non-obvious
interactions. An interactive generator that knows the plugin's contract is
meaningfully better than pointing users at Archon's YAML docs.

Archon equivalent: none. Archon has 13 bundled workflows but no authoring
assistant.

Already the minimum viable shape: the skill is a conversational Q&A guide,
not a code generator. No rework needed.

---

### `workflows-run` skill
**KEEP AS-IS (with one targeted rework).**

Real problem solved: dispatching a containerised workflow requires (1) detecting
`image:` nodes, (2) resolving credentials, (3) building a workspace with a
git root, (4) preprocessing, (5) running Archon, (6) surface artefacts and
offer to cherry-pick. None of these steps are trivial for a first-time user.

Archon equivalent: `archon workflow run` covers step 5 only.

The skill is already tightly scoped. The workspace git-seed, rsync exclude
list, cherry-pick replay, and credential cleanup trap are all load-bearing.
Do not thin this further.

One rework: step 2 (workflow existence check via `archon workflow list`) is
a round-trip that can fail if Archon is not on PATH. Already handled, but
the inline Python YAML check for `image:` nodes (step 2b) duplicates logic
from `preprocess_workflow.py::has_image_nodes`. Remove the inline Python
and call `preprocess_workflow.py --check` instead. Single implementation,
single place to update when the detection logic changes.

User-visible change: no change to user experience.

---

### `workflows-status` skill
**REWORK — cut REST path, keep SQLite, add schema-version probe.**

Real problem solved: `archon workflow status` only shows active runs. A user
who launched a workflow yesterday and wants to check what happened has no
native Archon CLI surface. Our SQLite reader fills the gap.

Archon equivalent: `archon workflow status` (active runs only). No historical
view.

Problem with the current shape: the REST-then-SQLite dual-source design
(`workflows_status_query.py` lines 64-103) was built on the assumption that
`archon serve` would be the primary path for CLI-launched runs. The brief
documents the contrary: "CLI-launched runs write to SQLite but don't emit
SSE." REST and SQLite now contain the same data; REST adds an HTTP dependency
on `archon serve` being up. For a first-time user who is not running
`archon serve` (the common case), the REST path always times out and the 1s
default timeout (`--timeout 1.0`, line 279) is the only thing keeping the
skill fast.

Simplest shape: make SQLite the primary path. REST becomes opt-in via
`--rest` flag for users who know they have `archon serve` running. Add a
`PRAGMA table_info(remote_agent_workflow_runs)` schema probe on startup that
emits a named warning if expected columns are absent — converts the silent
AMBER failure mode from the coupling analysis into a diagnosable error.

User-visible change: faster response (no REST timeout on first invocation),
clearer failure message if Archon schema changes.

---

### `manage-teams` skill
**CUT.**

Real problem it was solving: team lifecycle coaching for users who have
progressed to per-team agent isolation.

Same problem as `deploy-team`: this is Level 2 adoption. No first-time user
has teams to manage before they have run their first workflow. The coaching
content is well-written but is solving a future problem.

User-visible change: users who want to create a custom team will write a
manifest manually (a YAML file with documented schema) rather than using
guided Q&A. The schema is documented in `CLAUDE-CONTEXT-workflows.md`. This
is acceptable for v1.

Can be restored in v1.1 when base workflow adoption is measurable.

---

### `teams-status` skill
**CUT.**

Same rationale as `manage-teams`. Fleet reporting for zero teams returns
"No delegation teams configured." This skill exists to serve a user who has
already shipped `deploy-team` and created teams. Without `deploy-team` the
fleet is always empty and `teams-status` is a no-op.

User-visible change: none on Day 1. Users who want fleet visibility will use
`docker ps` directly.

---

### `preprocess_workflow.py`
**KEEP AS-IS.**

This script is the load-bearing integration mechanism. Its shape is correct:
pure transform function, no Archon dependency, fully unit tested (276 pass).
The `ParallelGitWriteError` guardrail is genuinely helpful — catches a class
of authoring mistake before the container even starts. The `_fresh_heredoc_sentinel()`
nonce (line 58) is the right fix for the prompt-injection-via-heredoc-collision
risk. No rework.

---

### `resolve_credentials.py`
**KEEP AS-IS.**

Three-tier fallback (Keychain → volume → config) is a real user problem: macOS
Keychain is the right default, but users on Linux or in CI need the volume
fallback. The EXIT/INT/TERM cleanup trap in `workflows-run` SKILL.md correctly
removes the Keychain-derived temp file. No simpler shape exists that still
serves the three real scenarios.

---

### `workflows_status_query.py`
**REWORK — as described above (SQLite primary, REST opt-in, schema probe).**

---

### `sse_stream_follow.py`
**CUT.**

The brief confirms: CLI-launched runs do not appear in the SSE stream
(confirmed gap, 2026-04-19). This script's only use case is server-launched
runs. We have no server-launch path in v1. The script is a foundation for a
Prometheus exporter that is explicitly deferred. Shipping it creates the
impression of a monitoring surface that does not work for the user's actual
run path.

User-visible change: the "SSE monitoring" reference in `CLAUDE-CONTEXT-workflows.md`
becomes a one-line forward reference ("planned for v2, requires `archon serve`
and server-launched runs"). The `workflows-run` skill already names the four
working monitoring surfaces (stderr lines, web UI, CLI snapshot, `docker logs`).

---

### Three-tier Docker image model (base / dev-team / review-team / full)
**REWORK — ship base and full only; drop the team-specific images.**

The team images (`dev-team`, `review-team`) exist to enforce per-team agent
boundaries. That enforcement requires team manifests, `deploy-team`, and
`manage-teams` — all cut above. Without those skills the team images have no
provisioning path.

Simpler shape: `sdlc-worker:base` for everything. First-time users run all
four bundled workflows using `sdlc-worker:base`. Per-team restriction is
achievable manually (edit Dockerfile, rebuild) and will be surfaced through
`deploy-team` in v1.1.

User-visible change: `workflows-setup` builds one image instead of three.
Build time drops proportionally. The full image (`sdlc-worker:full`) can
stay as an opt-in for users who want plugins pre-baked.

---

### Team manifest schema (v1.0)
**DEFER.**

The schema is well-designed and documented. Defer it as a spec artefact in
`CLAUDE-CONTEXT-workflows.md` — present, readable, but not yet backed by
tooling. When `deploy-team` returns in v1.1, the schema ships with it.

User-visible change: none. The schema YAML format stays documented.

---

### `loop.stages:` primitive
**KEEP AS-IS.**

This is the correct shape for multi-team cycles (designer → dev → review →
designer). It is the only pattern that avoids the Archon loop signal bug
(issue #1126, open, no fix). The implementation in `preprocess_workflow.py`
(`_transform_multistage_loop`, lines 308-405) is self-contained and well
tested. Cutting it would leave iterative workflows broken.

---

### Bundled workflow YAMLs (feature-pipeline, parallel-review, etc.)
**KEEP AS-IS.**

These are the user's Day 1 entry point. They demonstrate the `image:`,
`loop:`, `loop.stages:`, and `depends_on` patterns concretely. Without them
the user stares at a blank `.archon/workflows/` directory. The `author-workflow`
skill teaches by example using these files.

---

### Delegation coordinator specialist agent
**DEFER.**

The agent provides coaching on task decomposition. Useful once the user is
designing custom workflows, not on Day 1. Its absence does not make v1
harmful; `author-workflow` covers the interactive design path.

User-visible change: the agent does not appear in `sdlc-team-*` discovery.
Can ship in v1.1 alongside `deploy-team`.

---

## 4. Recommended v1 Shape

What an SDLC practitioner who installs `sdlc-workflows` tomorrow gets,
readable in 60 seconds:

**Skills (4, down from 7):**

| Skill | Purpose |
|---|---|
| `workflows-setup` | Install Archon, build `sdlc-worker:base`, scaffold `.archon/`. Run once. |
| `author-workflow` | Interactive YAML generator. Produces workflow files ready to run. |
| `workflows-run` | Dispatch a named workflow. Handles credentials, workspace, preprocessing, Archon. Returns artefacts. |
| `workflows-status` | Show recent and running workflow runs. SQLite-backed; works without `archon serve`. |

**Scripts (2, down from 9):**

| Script | Purpose |
|---|---|
| `preprocess_workflow.py` | Transforms `image:` nodes to `bash: docker run` nodes. Called by `workflows-run`. |
| `resolve_credentials.py` | Three-tier credential resolver (Keychain → volume → config). Called by `workflows-run`. |

**Docker (2 images, down from 3+ with team variants):**

| Image | Purpose |
|---|---|
| `sdlc-worker:base` | Claude Code + SDLC plugins. Used for all workflow nodes in v1. |
| `sdlc-worker:full` | Same as base with plugins pre-baked. Opt-in for faster startup. |

**Workflows (4, unchanged):**

`sdlc-feature-development.yaml`, `sdlc-parallel-review.yaml`,
`sdlc-bulk-refactor.yaml`, `sdlc-commissioned-pipeline.yaml`

**Commands (9, unchanged):**

All `.archon/commands/sdlc-*.md` briefs. These are the content the
agent reads inside the container. No cuts here.

**Total user-visible surface:** install plugin → `workflows-setup` → `author-workflow` (or use a bundled one) → `workflows-run` → `workflows-status`. Five steps. No team management, no fleet view, no SSE.

---

## 5. What Gets Deleted

Specific files and capabilities to remove:

**Skills (cut entirely):**
- `plugins/sdlc-workflows/skills/deploy-team/SKILL.md`
- `plugins/sdlc-workflows/skills/manage-teams/SKILL.md`
- `plugins/sdlc-workflows/skills/teams-status/SKILL.md`

**Scripts (cut entirely):**
- `plugins/sdlc-workflows/scripts/sse_stream_follow.py`
- `plugins/sdlc-workflows/scripts/team_inventory.py`
- `plugins/sdlc-workflows/scripts/teams_status_report.py`
- `plugins/sdlc-workflows/scripts/coaching_signals.py`
- `plugins/sdlc-workflows/scripts/override_logger.py`
- `plugins/sdlc-workflows/scripts/generate_team_claude_md.py`
- `plugins/sdlc-workflows/scripts/generate_team_dockerfile.py`
- `plugins/sdlc-workflows/scripts/validate_team_manifest.py`
- `plugins/sdlc-workflows/scripts/resolve_plugin_paths.py`
- `plugins/sdlc-workflows/scripts/detect-loop-bug.sh`
- `plugins/sdlc-workflows/scripts/loop-workaround.sh`

**Docker (remove team-specific Dockerfiles and build scripts):**
- Remove `Dockerfile.full` if the full image is opt-in and not built by default
  in `workflows-setup`. Keep the file; just remove it from the default build path.
- `plugins/sdlc-workflows/docker/build-team.sh` (team image builder — no teams in v1)
- Remove references to `dev-team`, `review-team` image names from
  `docker-compose.yml`, `build.sh`, and documentation.

**Agent:**
- `plugins/sdlc-workflows/agents/delegation-coordinator.md` — deferred, remove
  from plugin index until `deploy-team` returns.

**Tests (associated with cut scripts):**
- All unit tests that exercise `team_inventory`, `teams_status_report`,
  `coaching_signals`, `override_logger`, `generate_team_claude_md`,
  `generate_team_dockerfile`, `validate_team_manifest`, `resolve_plugin_paths`.
  These are the tests supporting the cut workforce-management layer.
  Exact file paths in `tests/` match the script names above.
- Container smoke tests that depend on team manifests (`run-containers.sh`
  checks that reference team counts, coaching signal output, override logger).

**Note on `loop-workaround.sh` and `detect-loop-bug.sh`:** These exist to
work around Archon issue #1126 (loop signal bug). The `loop.stages:` primitive
already sidesteps this bug by running the loop on the host, not through
Archon's loop executor. The shell workaround scripts are therefore inert in
the current design. Cut them to avoid confusion about whether they are in the
execution path.

---

## 6. Disclosure Updates

### `.pr-body-phase-f.md`

**Over-claimed:**
- "7 skills" — after cuts, this is 4 skills. Update the TL;DR and Summary section bullet.
- "Three-tier Docker image model (sdlc-worker:base → dev-team / review-team / full)" — team images are not part of the v1 default setup. Rephrase: "Two Docker images: `sdlc-worker:base` (standard) and `sdlc-worker:full` (plugins pre-baked). Per-team specialist images are defined and documented for v1.1."
- The "Honest pivots" section should add a fifth pivot: "Workforce management layer cut from v1 scope after team review. Skills `deploy-team`, `manage-teams`, `teams-status` and their backing scripts are deferred to v1.1 so v1 focuses on the core run path."

**Under-disclosed:**
- The PR body mentions SSE monitoring but does not state plainly that `sse_stream_follow.py` only works for server-launched runs, which `workflows-run` does not produce. After cutting the script, remove the SSE monitoring reference from the test matrix and summary.
- The deferred failure modes ("credential temp file leak", "silent content clobber at fan-in") should note their severity honestly: "silent content clobber" in a parallel fan-in is data loss for the user, not a minor gap. The PR body calls it "uncaptured" — it should be "known limitation, documented in CLAUDE-CONTEXT-workflows.md with the required authoring pattern to avoid it."

**Test matrix:**
- Remove the `run-containers.sh` 20/20 row if the cut scripts eliminate the container smoke tests that supported workforce management. Re-run and update the count after cuts.
- The PR body should not cite test counts from prior sessions. Commit to running every cited suite immediately before opening.

### `CLAUDE-CONTEXT-workflows.md`

- Remove the SSE streaming section or reduce it to: "SSE monitoring requires `archon serve` and server-launched runs. `workflows-run` uses the CLI path; use `docker logs -f` and `archon workflow status` for live observation."
- Remove references to `deploy-team`, `manage-teams`, `teams-status` skills from the "Available skills" section. Add a forward-reference: "Per-team agent isolation (specialist team images, team manifests) ships in v1.1."
- Remove the team manifest schema section or move it to an appendix labelled "v1.1 preview — not yet backed by tooling."
- The Prometheus/Grafana exporter design can stay as a forward reference but should be labelled "v2 roadmap."

### Skill docs

- `workflows-run/SKILL.md`: the SSE monitoring reference in the "Long-running or multi-cycle workflows" section ("python3 sse_stream_follow.py") should be removed, since `sse_stream_follow.py` is cut. The four monitoring surfaces already listed (stderr, web UI, CLI snapshot, docker logs) are correct and complete. Remove the SSE paragraph only.
- `workflows-setup/SKILL.md`: remove `--with-docker` / `--workflows-only` flag split. Default builds base image. Document the full image as a manual opt-in for users who want faster container startup.

---

## Summary Decision Table

| Component | Decision | Primary Reason |
|---|---|---|
| `workflows-setup` skill | REWORK (simplify flags) | Flag split solves no Day 1 problem |
| `deploy-team` skill | CUT | Level 2 adoption, no first-time user need |
| `author-workflow` skill | KEEP AS-IS | Genuine gap vs Archon native |
| `workflows-run` skill | KEEP AS-IS (minor) | Load-bearing; already minimum shape |
| `workflows-status` skill | REWORK (SQLite primary) | REST path adds latency for no gain |
| `manage-teams` skill | CUT | Level 2 adoption |
| `teams-status` skill | CUT | No teams → always empty |
| `preprocess_workflow.py` | KEEP AS-IS | Load-bearing integration mechanism |
| `resolve_credentials.py` | KEEP AS-IS | Solves a real three-platform problem |
| `workflows_status_query.py` | REWORK (schema probe + SQLite primary) | Amber coupling → diagnosable |
| `sse_stream_follow.py` | CUT | Wrong run path; solves server-launched runs only |
| `team_inventory.py` | CUT | Workforce management layer |
| `teams_status_report.py` | CUT | Workforce management layer |
| `coaching_signals.py` | CUT | Workforce management layer |
| `override_logger.py` | CUT | Workforce management layer |
| `generate_team_claude_md.py` | CUT | Workforce management layer |
| `generate_team_dockerfile.py` | CUT | Team images not in v1 default |
| `validate_team_manifest.py` | CUT | Team manifests not in v1 |
| `resolve_plugin_paths.py` | CUT | Only used by cut scripts |
| `loop-workaround.sh` | CUT | Inert in current design (loop.stages sidesteps Archon bug) |
| `detect-loop-bug.sh` | CUT | Diagnostic for a bug we work around, not fix |
| Three-tier Docker model | REWORK (base + full only) | Team images need deploy-team tooling |
| Team manifest schema | DEFER (docs only) | Forward reference for v1.1 |
| `loop.stages:` primitive | KEEP AS-IS | Only working iterative workflow pattern |
| Bundled workflow YAMLs | KEEP AS-IS | Day 1 entry point |
| `delegation-coordinator` agent | DEFER | Level 2 adoption |
| `workflows-run` workspace pattern | KEEP AS-IS | Load-bearing for Archon discovery |
| Credential cleanup traps | KEEP AS-IS | Security-critical |
| rsync exclude list | KEEP AS-IS | Security-critical |

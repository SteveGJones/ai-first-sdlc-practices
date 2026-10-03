# Solution Architect Review — EPIC #96 Containerised Claude Code Workers

**Date**: 2026-04-19
**Reviewer**: Solution Architect (sdlc-team-common)
**Branch**: feature/96-sdlc-workflows
**Verdict**: Ship with caveats (three explicit v2 commitments required in PR body)

---

## Verdict Rationale

The architecture is internally consistent and the trade-offs are deliberately chosen rather than stumbled into. Five phases of incremental proof, 261 passing tests, and a documented deviation log (the `--read-only` drop, the ContainerProvider retirement) demonstrate the kind of design hygiene that makes a v1 safe to ship. The caveats below are not blockers; they are risks that must be named in the PR so future contributors know what contract they are inheriting.

---

## Coupling-Risk Analysis: Archon Dependency

Archon is a small OSS project with no governance body, a single active maintainer visible in the commit history, and two open bugs that directly affected this EPIC (loop signal #1126, ContainerProvider absence). The coupling risk has three distinct faces:

**Schema coupling** is the most immediate. The preprocessor reads and writes Archon workflow YAML, the status query reads `remote_agent_workflow_runs` and `remote_agent_workflow_events` directly from `archon.db`, and the bash-node approach depends on `executeBashNode` remaining a first-class node type. Any Archon release that renames those tables, changes the bash-node contract, or drops the `/api/workflows/runs` REST shape will silently break `workflows-status` and `workflows-run` without a compile-time signal. The SQLite fallback path in `workflows_status_query.py` hardcodes six column names; that is the highest-brittleness point in the codebase.

**Abandonment risk** is acceptable for v1 but must be acknowledged. The preprocessor pivot was the correct response to discovering that Archon's isolation model is workflow-level, not node-level. It decouples the plugin from Archon's internal executor architecture at the cost of owning the bash-node generation layer ourselves. If Archon is abandoned, the bash nodes still run because they are plain `docker run` shell commands — the plugin degrades gracefully to a YAML templating layer with no orchestration. That is a reasonable worst-case posture.

**Upgrade friction** is the real operational cost. Users must pin an Archon version because the plugin has no compatibility matrix, no version probe, and no minimum-version guard in `workflows-setup`. A breaking Archon release will produce confusing container startup failures rather than a clear version mismatch error.

**Verdict on Archon coupling**: Acceptable for v1, provided the PR body names the three coupling points (YAML schema, SQLite columns, REST endpoint shape) and commits to a compatibility probe in v2.

---

## Three Failure Modes the Design Has Not Captured

**1. Credential staging race under parallel fan-out.** The Tier 1 credential path (macOS Keychain) writes a temp file on the host, mounts it read-only into every container, then cleans it up after the workflow run. The cleanup is workflow-scoped, not node-scoped. When three parallel nodes mount the same temp file path simultaneously, the first node to finish cannot clean up without racing the still-running siblings. If the host process that spawned Archon dies mid-workflow (OOM, Ctrl-C, signal), the cleanup trap may not fire, leaving the credential temp file on disk with mode 600. The Phase 5 spec documents credential cleanup on exit via a trap; it does not address the parallel-sibling scenario. A leaked credential file is not catastrophic (600 permissions, same user) but is a recoverable security gap that should be documented as a known limitation.

**2. Last-writer-wins is not surfaced to the synthesise node.** The preprocessor emits a warning when it detects fan-out, which is correct. But the synthesise node — the fan-in consumer — receives a merged workspace built by `git merge -X theirs` strategy in sequence. If two parallel review nodes both write to `output/report.md` (violating the per-node subdirectory convention) and one overwrites the other, the synthesise node has no signal that content was lost. The warning is build-time (preprocessor) but the failure is run-time (container output). No mechanism exists to diff the pre-merge and post-merge workspace to detect clobbers. This is explicitly deferred to v2, but it should be named in the PR body as a known data integrity gap rather than left implicit in the spec.

**3. Loop iteration orphan containers on timeout or signal.** The loop node handler runs a `for` loop on the host that spawns successive `docker run` calls. If Archon kills the enclosing bash node (via `timeout` or `idle_timeout`) partway through an iteration, the `docker run` child process may continue running — Docker does not receive the kill signal through the bash parent by default unless the entrypoint is PID 1 and the shell propagates signals correctly. The Phase 5 spec adds `trap SIGTERM/SIGINT/EXIT` inside the container entrypoint. It does not add signal forwarding from the host bash loop to the active `docker run` child. A timed-out workflow could leave a detached Claude Code container consuming API credits indefinitely. This is the highest-severity uncaptured failure mode.

---

## Recommendations for v2 (Not Blockers)

**Archon version probe.** Add a `--min-archon-version` check to `workflows-setup` that runs `archon --version`, parses the semver, and fails with a clear message if below the tested floor. This eliminates silent schema-drift failures.

**Per-branch overlay workspace.** The v1 shared-workspace contract is honest and documented, but it makes parallel fan-out workflows fragile for any team that forgets the per-node subdirectory convention. The v2 overlay design (per-branch directories, structured fan-in merge node) is already sketched in the Phase 4 spec. Promote it to a tracked issue with the parallel E2E test suite as the acceptance criterion.

**SQLite schema version guard.** The `workflows_status_query.py` SQLite path should verify the presence of the six expected columns before querying, and exit with a diagnostic message rather than a generic SQL error if columns are missing. One `PRAGMA table_info(remote_agent_workflow_runs)` call at startup achieves this.

# Feature Proposal: Complete Epic #75 — Plugin Ecosystem Tier 2/3 Items

**Proposal Number:** 89
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-06
**Target Branch:** `feature/75-epic-completion`

---

## Executive Summary

Bundle the four remaining sub-issues of epic #75 into a single feature branch and PR. Each issue is small but distinct; bundling them avoids four separate CI runs, four review contexts, and four merge ceremonies for related cleanup work that all touches the `sdlc-core` plugin and `release-mapping.yaml`.

**Issues addressed:**
- #91 — Clean up orphaned validation scripts in sdlc-core plugin
- #92 — Ship JavaScript and Go CI templates in setup-ci skill
- #93 — Automate constitution sync between source and plugin copy
- #94 — Build sdlc-core:integration-test reusable skill

---

## Motivation

### Problem Statement

The Tier 2/3 work in epic #75 has been audited and re-scoped. Four focused sub-issues remain. They share the same subsystem (`plugins/sdlc-core/`), the same source-to-release mechanic (`release-mapping.yaml`), and overlapping concerns (the script cleanup in #91 affects what the constitution sync in #93 has to enforce). Doing them together avoids merge churn between branches and gives reviewers a single coherent change.

### User Stories

- As an external user installing sdlc-core for the first time, I want the agent recommendations to point at working entry points (`/sdlc-core:validate`), not legacy script paths that don't exist in my project
- As a JavaScript or Go project maintainer, I want `setup-ci` to actually generate my workflow, not fail with a missing template
- As a contributor editing `CONSTITUTION.md`, I want CI to catch any drift between the source and the plugin copy before the PR merges
- As anyone wanting to test the SDLC plugins end-to-end, I want a single skill (`/sdlc-core:integration-test`) that runs the smoke harness without requiring me to remember Docker volumes, Ralph configs, or fixture paths

---

## Proposed Solution

Sequential commits on a single branch, one per issue:

### Commit 1 — #91: Orphan cleanup + agent doc updates

**Audit finding:** Two of the seven `plugins/sdlc-core/scripts/` files are NOT orphaned — `session-banner.sh` and `check-tmp-usage.py` are actively used by `plugins/sdlc-core/hooks/hooks.json` via `${CLAUDE_PLUGIN_ROOT}`. They stay.

The other five (`local-validation.py`, `check-broken-references.py`, `check-logging-compliance.py`, `check-technical-debt.py`, `validate-architecture.py`) are unreferenced by any plugin code. They have stale text references in source agent files and `CONSTITUTION.md` that point at `tools/validation/...` paths which don't exist for plugin consumers.

**Changes:**
- Remove the 5 orphan entries from `release-mapping.yaml` `sdlc-core.scripts:`
- Update **source** files (release-mapping copies them into `plugins/`):
  - `agents/core/sdlc-enforcer.md` — replace legacy script paths with `/sdlc-core:validate --pre-push`
  - `agents/team-security/compliance-auditor.md` (or wherever this lives in the source tree) — same
  - `agents/core/devops-specialist.md` — same
  - `CONSTITUTION.md` — same
  - `skills/release-plugin/SKILL.md` — same
- Re-run release-plugin to regenerate `plugins/sdlc-core/`. The 5 deleted scripts disappear; agent and constitution copies update.
- Verify nothing in `plugins/` still references the deleted scripts by path

### Commit 2 — #92: JavaScript and Go CI templates

**Changes:**
- Create `skills/setup-ci/templates/javascript.yml` (Node 22, eslint, tsc, npm test, npm audit)
- Create `skills/setup-ci/templates/go.yml` (Go 1.22+, go vet, staticcheck, go test -race, gosec)
- Add both templates to `release-mapping.yaml` `sdlc-core.skills:` block
- Re-run release-plugin
- Verify `plugins/sdlc-core/skills/setup-ci/templates/` contains all three templates

### Commit 3 — #93: Constitution sync CI check

**Changes:**
- Add a job to existing `.github/workflows/ai-sdlc-validation.yml` (or extend the documentation workflow) that runs:
  ```bash
  diff CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md
  ```
- On non-zero exit, fail with: `Constitution drift detected — run /sdlc-core:release-plugin to sync`
- Verify the check passes against the current state (if it doesn't, run release-plugin first to bring the plugin copy in sync, which will be automatic since commit 1 already touched CONSTITUTION.md)
- Update `CONTRIBUTING.md` with a one-line note about the check

### Commit 4 — #94: Integration-test skill

**Changes:**
- Create `skills/integration-test/SKILL.md` with `--smoke` (default) and `--full` modes plus `--fixture <name>` argument
- Skill body wraps `tests/integration/setup-smoke/run.sh` for `--smoke` mode
- Skill body wraps `tests/integration/PROMPT.md` for `--full` mode (or documents that the full mode is wired only loosely if the harness needs more work)
- Preflight checks: Docker running for smoke mode, auth volume present, fixture directory exists
- Add to `release-mapping.yaml` `sdlc-core.skills:` block
- Update `tests/integration/setup-smoke/README.md` and `tests/integration/PROMPT.md` README to point at the skill as the canonical entry point

---

## Acceptance Criteria

### #91
- [ ] `plugins/sdlc-core/scripts/` contains only `session-banner.sh` and `check-tmp-usage.py`
- [ ] No file in `plugins/` references the deleted scripts by name
- [ ] All references in agent files and `CONSTITUTION.md` point at `/sdlc-core:validate` instead of legacy script paths
- [ ] Hooks (SessionStart banner, PostToolUse tmp check) still work after the cleanup

### #92
- [ ] `plugins/sdlc-core/skills/setup-ci/templates/javascript.yml` exists and is valid GitHub Actions YAML
- [ ] `plugins/sdlc-core/skills/setup-ci/templates/go.yml` exists and is valid GitHub Actions YAML
- [ ] Both templates ship via `release-mapping.yaml`
- [ ] `actionlint` passes on both (if available locally; otherwise structural validation via `python -c 'import yaml; yaml.safe_load(open(...))'`)

### #93
- [ ] CI fails on a PR that modifies `CONSTITUTION.md` without running release-plugin
- [ ] Failure message tells the contributor exactly which command to run
- [ ] Existing repo state passes the check

### #94
- [ ] `plugins/sdlc-core/skills/integration-test/SKILL.md` exists
- [ ] `--smoke` mode invokes the existing Docker harness
- [ ] Skill ships via `release-mapping.yaml`
- [ ] Test READMEs point at the skill as the canonical entry point

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Updating CONSTITUTION.md affects rules that downstream agents rely on | Could change behaviour | Only the script-path text references change, not any rule semantics. Diff carefully before commit. |
| Removing scripts from release-mapping might delete files release-plugin doesn't manage | Orphan files left behind | Run release-plugin and `git status` after to confirm the deletions |
| CI sync check trips on legitimate CONSTITUTION.md edits | Annoyance | The error message tells the contributor how to fix it (run release-plugin) — that IS the fix |
| Integration-test skill `--full` mode might not actually wire into PROMPT.md cleanly | Incomplete coverage | Document in skill body that `--full` is "loosely wired" and the harness needs more work; full integration is deferred |
| `actionlint` not available locally | Can't validate templates | Fall back to YAML structural parse; CI will catch real issues |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `release-mapping.yaml` (remove 5 scripts from sdlc-core.scripts; add 2 CI templates and 1 skill to sdlc-core.skills) |
| Modify | `agents/core/sdlc-enforcer.md` |
| Modify | `agents/core/devops-specialist.md` |
| Modify | `agents/team-security/compliance-auditor.md` (or actual source path) |
| Modify | `CONSTITUTION.md` |
| Modify | `skills/release-plugin/SKILL.md` |
| Delete | `plugins/sdlc-core/scripts/local-validation.py` |
| Delete | `plugins/sdlc-core/scripts/check-broken-references.py` |
| Delete | `plugins/sdlc-core/scripts/check-logging-compliance.py` |
| Delete | `plugins/sdlc-core/scripts/check-technical-debt.py` |
| Delete | `plugins/sdlc-core/scripts/validate-architecture.py` |
| Create | `skills/setup-ci/templates/javascript.yml` |
| Create | `skills/setup-ci/templates/go.yml` |
| Create | `skills/integration-test/SKILL.md` |
| Modify | `.github/workflows/ai-sdlc-validation.yml` (constitution sync check) |
| Modify | `CONTRIBUTING.md` (one-line note about sync check) |
| Modify | `tests/integration/setup-smoke/README.md` |
| Create | `docs/feature-proposals/89-75-epic-completion.md` |

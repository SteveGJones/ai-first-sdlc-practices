---
name: teams-status
description: Fleet-level visibility for delegation teams. Shows roster, staleness, workflow usage, and coaching signals.
disable-model-invocation: false
argument-hint: "[--team <name>]"
---

# Delegation Teams Status

Show the status of all delegation teams or a single team in detail.

## Arguments

- (no arguments) — fleet view of all teams
- `--team <name>` — detailed view of a single team

## Steps

### 1. Load team data

Read all manifests from `.archon/teams/`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teams_status_report.py --teams-dir .archon/teams --workflows-dir .archon/workflows
```

If no manifests exist:
```
No delegation teams configured.
Create a team: /sdlc-workflows:manage-teams --create
```

### 2. Fleet view (no arguments)

Display a summary table of all teams:

```
Delegation workforce: N teams, M workflows

  Team                        Status   Agents  Skills  Image     Workflows
  ─────────────────────────── ──────── ─────── ─────── ───────── ─────────
  security-review-team        active   3       2       current   2
  dev-team-python             active   4       6       stale     3
  test-team                   active   1       2       not built 0
```

### 3. Coaching signals

After the table, display tiered coaching signals:

**Critical** (action required):
```
  ✗ test-team has no image built
```

**Advisory** (worth reviewing):
```
  ! dev-team-python image is stale (manifest updated 2026-04-12, image built 2026-04-10)
  ! test-team is not referenced by any workflow
```

**Informational** (patterns):
```
  ℹ sec:security-architect has been added via team_extend 5 times — consider promoting
```

Read override signals from `.archon/logs/overrides.jsonl` if it exists.

### 4. Plugin environment changes

Check if any installed plugins have been updated since the last full image build by comparing plugin directory modification times against the full image build timestamp.

```
  Plugin environment changes:
    + mongodb-plugin updated since last full image build
```

### 5. Single team detail (`--team <name>`)

Read `.archon/teams/<name>.yaml` and display:

```
Team: security-review-team
  Status:      active
  Updated:     2026-04-12
  Image built: 2026-04-12 (current)

  Plugins (3):
    sdlc-core, sdlc-team-security, sdlc-team-common

  Agents (3):
    sdlc-team-security:security-architect
    sdlc-team-security:compliance-auditor
    sdlc-team-common:solution-architect

  Skills (2):
    sdlc-core:validate
    sdlc-core:rules

  Context:
    CONSTITUTION.md, CLAUDE-CONTEXT-security.md

  Used by workflows:
    sdlc-parallel-review.yaml → node: security-review
    sdlc-commissioned-pipeline.yaml → node: security-gate

  Available but not included (from installed plugins):
    sdlc-team-security:data-privacy-officer
    sdlc-team-security:enforcement-strategy-advisor
```

Use `team_inventory.py` to compute the "available but not included" section:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/team_inventory.py --installed-json ~/.claude/plugins/installed_plugins.json --team-manifest .archon/teams/<name>.yaml
```

### 6. Footer

```
Run /sdlc-workflows:manage-teams --review for guided resolution.
```

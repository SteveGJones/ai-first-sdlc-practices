---
name: manage-teams
description: Guided coaching for delegation team lifecycle — create, update, delete, or review the workforce. The primary interface for team management and fleet-level visibility.
disable-model-invocation: false
argument-hint: "--create | --update <team> | --delete <team> | --review [--team <name>]"
---

# Manage Delegation Teams

Guided Q&A coaching for team lifecycle management. Follows the same
interactive pattern as `/sdlc-core:setup-team`.

## Modes (pass exactly one flag)

This skill has four modes. Argument autocomplete does not show flag
variants, so the mode menu is always in the body — pick one before
proceeding.

- `--create` — create a new team with guided coaching (default choice
  when the user says "I need a team")
- `--update <team>` — update an existing team's roster or description
- `--delete <team>` — delete a team (removes manifest + image)
- `--review` — audit the entire delegation workforce (fleet table,
  staleness, workflow usage, coaching signals). Add `--team <name>`
  for a single-team detail view.

For task-to-workflow recommendation ("I have a task, which workflow and
team formation should I use?") use `/sdlc-workflows:author-workflow
--for-task "<description>"` — that skill owns workflow+formation planning.

## Lifecycle Model

Teams have a simple lifecycle:
- **Create** → manifest written to `.archon/teams/<name>.yaml` with `status: active`
- **Update** → manifest modified, `updated` timestamp set, image marked stale
- **Delete** → manifest file removed, Docker image removed, git history provides audit trail

There are no intermediate states. A manifest exists and is active, or it has been deleted. Git history provides the full audit trail for compliance.

## Mode: `--create`

### Step 1: Right-sizing check

Before creating a team, assess the project's delegation maturity:

```bash
ls .archon/teams/*.yaml 2>/dev/null | wc -l
ls .archon/workflows/*.yaml 2>/dev/null | wc -l
```

**If no teams exist (Level 1 adoption):**

```
You don't have any delegation teams yet.

For your first team, I recommend a general-purpose team that mirrors
your current Claude Code environment — all your installed plugins,
agents, and skills.

This gets you to your first delegated workflow run with one command.
You can specialise into multiple teams later as your needs become
clearer.

  (a) Create a general-purpose team (recommended for first-time setup)
  (b) Create a specialist team (I know what I want)
```

If (a): generate a manifest that includes ALL installed plugins, agents, and skills. Name it `general-purpose`. Skip the Q&A flow — go straight to manifest generation and offer to build the image.

**If teams exist but fewer teams than workflows:**

```
You have N team(s) and M workflow(s). Creating another team gives
you more granular control over which agents each workflow node uses.
```

Proceed to step 2.

**If teams >= 2x workflows:**

```
You have N team(s) but only M workflow(s). Consider whether you need
another team — more teams means more images to build and maintain.

  (a) Create the team anyway
  (b) Show me my current teams first (/sdlc-workflows:manage-teams --review)
```

### Step 2: Team purpose

```
What is this team's purpose?
  (a) Code review (security, architecture, quality)
  (b) Implementation (feature development, bug fixes)
  (c) Testing (test coverage, integration testing)
  (d) Validation (linting, compliance, CI checks)
  (e) Something else — describe it
```

### Step 3: Agent selection

Based on the purpose, show available agents from installed plugins. Use `team_inventory.py` to discover what's installed:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/team_inventory.py \
    --installed-json "${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}/installed_plugins.json"
```

Present agents relevant to the chosen purpose:

```
For a security review team, here are the available agents:

  From sdlc-team-security:
    security-architect     — OWASP, threat modelling
    compliance-auditor     — regulatory compliance
    data-privacy-officer   — PII/GDPR analysis

  From sdlc-team-common:
    solution-architect     — architectural context

  Which agents should be on this team?
    (a) All recommended (4 agents)
    (b) Let me pick individually
    (c) Start minimal — I'll add more later
```

Frame as "commonly paired with" rather than "everything available" — curated recommendations, not a full inventory.

### Step 4: Skill selection

Same pattern as agents. Show skills relevant to the team's purpose:

```
  Which skills should this team have?
    (a) Standard set: validate, rules (recommended)
    (b) Let me pick individually
    (c) Start minimal
```

### Step 5: Context files

```
  Which context files should this team load?
    (a) Standard: CONSTITUTION.md (recommended for all teams)
    (b) Add domain-specific context (show available CLAUDE-CONTEXT-*.md files)
    (c) None
```

### Step 6: Name the team

```
  Team name (lowercase, hyphens ok): security-review-team
```

Validate: must match `^[a-z0-9]+(?:[._-][a-z0-9]+)*$` (Docker tag component).

### Step 7: Write manifest and offer to build

Write the manifest to `.archon/teams/<name>.yaml`:

```yaml
schema_version: "1.0"
name: <name>
description: >
  <generated from purpose + selected agents>
status: active
created: <ISO-8601 now>
updated: <ISO-8601 now>

plugins:
  - <inferred from selected agents and skills>

agents:
  - <selected agents>

skills:
  - <selected skills>

context:
  - <selected context files>
```

Validate the manifest:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_team_manifest.py \
    .archon/teams/<name>.yaml \
    --installed-plugins "${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}/installed_plugins.json" \
    --project-root .
```

Then offer to build:

```
Manifest written: .archon/teams/<name>.yaml

Build the team image now?
  (a) Yes — run /sdlc-workflows:deploy-team --name <name>
  (b) Later — I'll build when I'm ready
```

## Mode: `--update <team>`

### Step 1: Load current state

Read `.archon/teams/<team>.yaml`. Display current composition:

```
Updating team: security-review-team
  Current: 3 agents, 2 skills (image built 2026-04-10)

  What would you like to change?
    (a) Add agents or skills
    (b) Remove agents or skills
    (c) Change context files
    (d) Show commonly paired agents not on this team
    (e) Review the full manifest
```

### Step 2: Apply changes

For option (d), use `team_inventory.py` to find available agents in the team's plugins that aren't currently on the team.

After changes, update the manifest's `updated` timestamp and warn about staleness:

```
Manifest updated. The team image was built on 2026-04-10 but
the manifest has changed. Rebuild now?
  (a) Yes — run /sdlc-workflows:deploy-team --name <team>
  (b) Later
```

## Mode: `--delete <team>`

### Step 1: Check workflow references

Scan all workflow YAMLs in `.archon/workflows/` for references to `sdlc-worker:<team>`.

### Step 2: Confirm and delete

```
Deleting team: legacy-review-team

  This team is referenced by 1 workflow:
    sdlc-parallel-review.yaml → node: legacy-check

  Deleting will:
    - Remove the manifest file (.archon/teams/legacy-review-team.yaml)
    - Remove the Docker image (sdlc-worker:legacy-review-team)
    - Git history retains the full audit trail

  You will need to update the workflow to remove or replace the reference.

  Proceed?
    (a) Yes — delete and show workflow references to fix
    (b) No — keep the team
```

If confirmed:
```bash
rm .archon/teams/<team>.yaml
rm -rf .archon/teams/.generated/<team>*
docker rmi sdlc-worker:<team> 2>/dev/null || true
```

## Mode: `--review`

Fleet-level visibility and guided resolution. Runs the underlying
status report and coaching-signal analysis, then offers actions on
anything worth fixing. With `--team <name>`, shows a single team in
detail instead of the fleet view.

### Step 1: Load team data

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teams_status_report.py \
    --teams-dir .archon/teams --workflows-dir .archon/workflows
```

If no manifests exist:

```
No delegation teams configured.
Create a team: /sdlc-workflows:manage-teams --create
```

### Step 2: Fleet view (no `--team` argument)

Display a summary table of all teams:

```
Delegation workforce: N teams, M workflows

  Team                        Status   Agents  Skills  Image     Workflows
  ─────────────────────────── ──────── ─────── ─────── ───────── ─────────
  security-review-team        active   3       2       current   2
  dev-team-python             active   4       6       stale     3
  test-team                   active   1       2       not built 0
```

### Step 3: Coaching signals

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

### Step 4: Plugin environment changes

Check whether any installed plugins have been updated since the last
full image build, by comparing plugin directory modification times
against the full image build timestamp.

```
  Plugin environment changes:
    + mongodb-plugin updated since last full image build
```

### Step 5: Single-team detail (`--team <name>`)

When invoked with `--team <name>`, read `.archon/teams/<name>.yaml` and
display:

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
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/team_inventory.py \
    --installed-json ~/.claude/plugins/installed_plugins.json \
    --team-manifest .archon/teams/<name>.yaml
```

### Step 6: Offer guided resolution (fleet view only)

After the fleet table, signals, and plugin-environment section, offer
actions on what the signals flagged:

```
Would you like to address any of these?
  (a) Rebuild stale images
  (b) Delete unused test-team
  (c) Add security-architect to dev-team-python
  (d) Skip for now
```

Selecting (a) hands off to `/sdlc-workflows:deploy-team`; (b) hands off
to `/sdlc-workflows:manage-teams --delete`; (c) hands off to
`/sdlc-workflows:manage-teams --update`. Each keeps the user in the
same coaching loop instead of silently mutating state.

<!-- --plan-task mode removed on 2026-04-19 v1 scope review. The
recommendation flow (analyse task, recommend workflow + team formation,
offer to run) now lives in /sdlc-workflows:author-workflow --for-task,
where workflow+formation planning already belongs. The previous mode
also wrote a .archon/tasks/<slug>.yaml file that had no consumer. See
reviews/2026-04-19-v1-scope-critical-goal.md §4.4. -->


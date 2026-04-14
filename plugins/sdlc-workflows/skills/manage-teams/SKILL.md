---
name: manage-teams
description: Guided coaching for delegation team lifecycle — create, update, delete, review, and plan task formations. The primary interface for team management.
disable-model-invocation: false
argument-hint: "--create | --update <team> | --delete <team> | --review | --plan-task <description>"
---

# Manage Delegation Teams

Guided Q&A coaching for team lifecycle management. Follows the same
interactive pattern as `/sdlc-core:setup-team`.

## Arguments

- `--create` — create a new team with guided coaching
- `--update <team>` — update an existing team
- `--delete <team>` — delete a team (removes manifest + image)
- `--review` — review the entire delegation workforce with coaching signals
- `--plan-task "<description>"` — recommend a workflow + team formation for a task

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
  (b) Show me my current teams first (/sdlc-workflows:teams-status)
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
    --installed-json ~/.claude/plugins/installed_plugins.json
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
    --installed-plugins ~/.claude/plugins/installed_plugins.json \
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

### Step 1: Run fleet analysis

Run fleet report and coaching signals:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teams_status_report.py \
    --teams-dir .archon/teams --workflows-dir .archon/workflows --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/coaching_signals.py \
    --teams-dir .archon/teams --workflows-dir .archon/workflows \
    --overrides .archon/logs/overrides.jsonl --json
```

### Step 2: Present coaching observations

```
Delegation workforce review:

  Your project has 4 active teams and 3 workflows.

  Observations:
    1. dev-team-python — image is stale (manifest updated 3 days
       after last build)
    2. test-team — not referenced by any workflow. Delete or assign?
    3. sec:security-architect was extended via team_extend 5 times
       on dev-team — consider adding to the standing team.

  Would you like to address any of these?
    (a) Rebuild stale images
    (b) Delete unused test-team
    (c) Add security-architect to dev-team-python
    (d) Skip for now
```

## Mode: `--plan-task "<description>"`

### Step 1: Analyse the task

Read the task description and the current roster (all manifests in `.archon/teams/`).

### Step 2: Recommend a formation

Recommend a workflow template + which teams map to which nodes:

```
Task: "Add OAuth2 authentication to the API"

Recommended formation:

  Workflow: sdlc-feature-development

  Node          Team                     Notes
  ──────────── ──────────────────────── ────────────────────
  plan          general-purpose          architecture + planning
  implement     dev-team-python          primary dev team
  validate      dev-team-python          validation pipeline
  security      security-review-team     auth = security-sensitive
  architecture  general-purpose          architecture review
  quality       general-purpose          code quality review
  synthesise    general-purpose          unified summary

  This task involves authentication, so I've included the
  security-review-team for the security review node.

  (a) Accept this formation
  (b) Modify — change team assignments
  (c) Show alternative workflow templates
  (d) Skip — I'll assign teams myself
```

### Step 3: Record the task plan

If accepted, write to `.archon/tasks/<slug>.yaml`:

```yaml
task: add-oauth2-authentication
created: 2026-04-14T10:00:00Z
workflow: sdlc-feature-development
formation:
  - node: plan
    team: general-purpose
  - node: implement
    team: dev-team-python
  - node: validate
    team: dev-team-python
  - node: security-review
    team: security-review-team
  - node: architecture-review
    team: general-purpose
  - node: code-quality-review
    team: general-purpose
  - node: synthesise
    team: general-purpose
```

```bash
mkdir -p .archon/tasks
```

### Step 4: Offer to run

```
Task plan saved: .archon/tasks/add-oauth2-authentication.yaml

Run this workflow now?
  (a) Yes — /sdlc-workflows:workflows-run sdlc-feature-development
  (b) Not yet
```

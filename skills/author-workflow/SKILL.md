---
name: author-workflow
description: Pick an existing workflow for a task or author a new one — recommends workflow + team formation, or generates a fresh workflow YAML with command prompts and team validation.
disable-model-invocation: false
argument-hint: "--for-task \"<description>\" | --new [description]"
---

# Author Workflow

This skill owns workflow + team-formation decisions for a task. Use it
both when the user has a concrete task ("add OAuth2 auth") and needs a
recommendation, and when they want to build a brand-new workflow.

## Modes (pass exactly one flag)

Argument autocomplete does not show flag variants, so the mode menu is
always in the body — pick one before proceeding.

- `--for-task "<description>"` — **start here when the user describes
  a task, not a pipeline.** Recommend which existing workflow fits and
  which teams should be on which nodes; fall back to `--new` only if
  nothing fits. No files written unless you actually author a workflow.
- `--new [description]` — **start here when the user wants a pipeline
  that does not yet exist.** Guided authoring: DAG design, workflow
  YAML, command prompts, validation, commit.

If invoked with no flag and no clear signal, ask the user which mode
fits. Defaulting silently to `--new` has the user author a workflow
when an existing one would have done the job.

## Context

Load `CLAUDE-CONTEXT-workflows.md` before either mode proceeds — it
contains the workflow YAML schema, team manifest schema, command
prompt format, and all validation rules.

## Mode: `--for-task "<description>"`

### Step 1: Analyse the task

Read the task description. List current teams and workflows:

```bash
ls .archon/teams/*.yaml 2>/dev/null
ls .archon/workflows/*.yaml 2>/dev/null
```

For each existing workflow, extract its purpose (the `description:`
field) and its node list (the `nodes:` array). For each team, extract
its agent roster.

### Step 2: Recommend a formation

Recommend a workflow + team-to-node mapping. Worked example:

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
  security-review-team on the security review node.

  (a) Accept and run this now
  (b) Modify — change team assignments
  (c) Show alternative workflow templates
  (d) No existing workflow fits — switch to --new mode
  (e) Skip — I'll assign teams myself
```

### Step 3: Offer to run

If the user picks (a), hand off directly:

```
/sdlc-workflows:workflows-run <workflow-name>
```

No file is written — this recommendation flow exists to route the user
to the right existing workflow, not to persist task plans. The git
commit of the run itself (via `workflows-run`) captures the record.

If (b), loop back to step 2 with the adjusted mapping. If (c), list the
available workflows and restart step 2 against the chosen one. If (d),
switch to `--new` mode below with the task description carried through.
If (e), end the skill.

## Mode: `--new [description]`

### Step 0. Load the schema reference

Do not rely on memory. Explicitly read the canonical schema reference before
drafting any YAML:

```
Read CLAUDE-CONTEXT-workflows.md
```

This file lives at the repo root and defines every field used in the workflow
and manifest YAML, plus the command-prompt format. Skipping this step produces
workflows that silently drift from the current schema.

### 1. Understand the Goal

If the user provided a description as an argument, use it. Otherwise ask:

> What should this workflow accomplish? Describe the pipeline: what work needs to happen, in what order, and which teams should do it.

### 2. Discover Existing Teams

List available team manifests:

```bash
ls .archon/teams/*.yaml 2>/dev/null
```

For each manifest, show the team name, description, and available agents:

```bash
for f in .archon/teams/*.yaml; do
    python3 -c "
import yaml
m = yaml.safe_load(open('$f'))
print(f\"  {m['name']}: {m.get('description', 'no description').strip()}\")
print(f\"    agents: {', '.join(m.get('agents', []))}\")
"
done
```

If no teams exist, suggest creating them first:

> No team manifests found in `.archon/teams/`. Create teams first with `/sdlc-workflows:manage-teams --create`.

### 3. Design the DAG

Based on the user's description and available teams, design the workflow DAG:

- Identify distinct stages (implement, review, validate, etc.)
- Assign each stage to a team image
- Determine dependencies (what must complete before what)
- Identify parallel opportunities (nodes that can run concurrently)

Present the DAG to the user for approval:

```
Proposed pipeline:
  1. implement (sdlc-worker:dev-team) — no deps
  2. security-review (sdlc-worker:review-team) — after implement
  3. architecture-review (sdlc-worker:review-team) — after implement
  4. synthesise (sdlc-worker:dev-team) — after both reviews

Nodes 2 and 3 run in parallel.
```

### 4. Generate Workflow YAML

Create `.archon/workflows/<name>.yaml` following the schema in CLAUDE-CONTEXT-workflows.md:

- `name:` must be unique across all workflows in the directory
- `description:` should explain purpose, inputs, and outputs
- `provider: claude` always
- Each node needs: `id`, `command`, `image`, and `depends_on` where applicable
- Use `trigger_rule: all_success` (default) unless the user specifies otherwise
- **`timeout:` is in milliseconds.** Archon's default is 120000ms (2 min) —
  too short for real work. Set explicitly on every node:
  review/synthesis `600000` (10 min), validation `300000` (5 min),
  implementation/planning `1800000` (30 min)
- Do not add non-standard fields to nodes (e.g. `name:`, `label:`) —
  Archon's schema is strict and unknown fields break the graph renderer

Starter template (copy, rename, adjust):

```yaml
name: <workflow-name>
description: <one-line purpose>
provider: claude
nodes:
  - id: implement
    command: implement
    image: sdlc-worker:dev-team
  - id: review
    command: review
    image: sdlc-worker:review-team
    depends_on: [implement]
```

### 5. Generate Command Prompts

For each node, create `.archon/commands/<command-name>.md` following the format in CLAUDE-CONTEXT-workflows.md:

- Role framing: "You are performing X on a Y at /workspace."
- Context: what files exist, what state to expect
- Task: numbered steps of what to do
- Output: where to write results
- Commit: `cd /workspace && git add -A && git commit -m "<message>"`

### 6. Validate

Run validation checks:

```bash
# Name-collision check — refuse to overwrite an existing workflow
if [ -f ".archon/workflows/<name>.yaml" ]; then
    echo "ERROR: Workflow '<name>' already exists at .archon/workflows/<name>.yaml"
    echo "Choose a different name or remove the existing file first."
    exit 1
fi

# Validate that referenced team images have manifests
for team in <list of unique images>; do
    team_name="${team#sdlc-worker:}"
    if [ ! -f ".archon/teams/${team_name}.yaml" ]; then
        echo "WARNING: No manifest for $team_name — run build-team.sh after creating one"
    fi
done

# Check command files exist
for cmd in <list of unique commands>; do
    if [ ! -f ".archon/commands/${cmd}.md" ]; then
        echo "ERROR: Missing command file: .archon/commands/${cmd}.md"
    fi
done

# Validate workflow YAML structure
python3 -c "
import yaml
wf = yaml.safe_load(open('.archon/workflows/<name>.yaml'))
assert 'name' in wf, 'Missing name field'
assert 'nodes' in wf, 'Missing nodes field'
for node in wf['nodes']:
    assert 'id' in node, f'Node missing id'
    assert 'command' in node or 'prompt' in node, f'Node {node[\"id\"]} needs command or prompt'
print('Workflow YAML valid')
"

# Repository-wide cross-reference check — only runs if the validator is present
if [ -f "tools/validation/check_workflow_teams.py" ]; then
    python3 tools/validation/check_workflow_teams.py
fi
```

### 7. Commit

```bash
git add .archon/workflows/<name>.yaml .archon/commands/<command-files>
git commit -m "feat(workflow): add <name> workflow with <N> nodes"
```

### 8. Report

```
Workflow created:
  File: .archon/workflows/<name>.yaml
  Nodes: <count>
  Teams: <list>
  Commands: <list of .md files>

To build team images:    /sdlc-workflows:deploy-team --name <team>
To run the workflow:     /sdlc-workflows:workflows-run <name>
```

## Designing long-running or cyclical workflows

Authors regularly want pipelines like `designer → developer → reviewer
→ designer …` running for hours or days. Before choosing a shape, ask
the user these questions and design accordingly:

1. **How long will each node actually take?** Real implementation or review work is often 20-60 min, not the 2-min default. Set `timeout:` **in milliseconds** explicitly on every node — Archon's default is 120000ms (2 min) which kills real work. Use `600000` (10 min) for reviews, `1800000` (30 min) for implementation. Proven by dogfood: security-review on a 170-file repo took 1m44s and would have been killed at the 2-min default.
2. **Is the iteration count known up front?** If yes (e.g. "three review rounds"), unroll as distinct nodes (`review-v1`, `review-v2`, `review-v3`). If no (open-ended "until approved"), the workflow alone cannot express it — you will need an outer-loop wrapper that re-invokes `archon workflow run` until a signal is detected.
3. **Does the cycle need different specialists each pass?** If yes, unrolled iterations or an outer loop are the only options — a single `loop:` node keeps one team running the whole cycle.
4. **Does the user want live feedback during long nodes?** Flag the monitoring gap — `workflows-run` does not stream live output in v1. They will need a second terminal with `docker logs -f` or `tail -f` the archon log.
5. **Is the token cost acceptable?** A 30-min node × 4 stages × 5 iterations on Opus can run to serious dollars. Warn the user before shipping the workflow. Set `budget:` on each node to cap cost if the model spirals.
6. **Tiered termination — always set both `timeout:` and `budget:`.** Three independent kill mechanisms protect against both runaway work and lost output:
   - **Tier 1: Budget** (`budget: 2.0`) — kills if the model burns >$2 of tokens (spiral detection)
   - **Tier 2: Inner timeout** (computed automatically: timeout_ms/1000 - 60s) — Claude gets SIGTERM, writes partial output
   - **Tier 3: Outer timeout** (`timeout: 600000`) — hard kill if inner timeout failed
   
   The save window (60s between tier 2 and 3) means partial output survives.
   Command prompts instruct agents to write findings incrementally to
   `/workspace/reports/<node-id>/findings.md`.

Full discussion of each option (per-node `loop:`, unrolled iterations,
outer-loop wrapper) and the current monitoring surface is in
*Long-Running Workflows, Cycles, and Monitoring* in
`CLAUDE-CONTEXT-workflows.md`. Read that section whenever the user's
pipeline is non-trivial.

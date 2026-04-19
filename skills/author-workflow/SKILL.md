---
name: author-workflow
description: Create a new containerised workflow — generates workflow YAML, command prompts, and validates team references.
disable-model-invocation: false
argument-hint: "[workflow description]"
---

# Author Workflow

Create a new containerised team workflow. This skill generates the workflow YAML, command prompt files, and validates everything against existing teams.

## Context

Load `CLAUDE-CONTEXT-workflows.md` before proceeding — it contains the workflow YAML schema, team manifest schema, command prompt format, and all validation rules.

## Steps

### 0. Load the schema reference

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
- Add `timeout:` to long-running nodes (default 300s is fine for most)

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

To build team images:   bash plugins/sdlc-workflows/docker/build-team.sh <team>
To run the workflow:     /sdlc-workflows:workflows-run <name>
```

# Containerised Workers — Quickstart

Get from zero to a working containerised workflow in 5 minutes.

## Prerequisites

- **Docker Desktop** running (verify: `docker info`)
- **Claude Code** authenticated on this machine (verify: `claude -p "say ok"`)
- **This repository** cloned with the sdlc-workflows plugin installed

## Step 1: Build Base Images

```bash
# From the repository root:
bash plugins/sdlc-workflows/docker/build-base.sh
bash plugins/sdlc-workflows/docker/build-full.sh
```

This builds two images:
- `sdlc-worker:base` — toolchain (Node.js, Claude Code, Archon, Python, git)
- `sdlc-worker:full` — base + all installed plugins (source layer for team images)

Build takes ~3-5 minutes on first run, seconds on rebuild.

## Step 2: Create a Team

Teams are defined by manifests in `.archon/teams/`. Each manifest specifies which plugins, agents, and skills the team has access to.

Create `.archon/teams/my-team.yaml`:

```yaml
schema_version: "1.0"
name: my-team
description: >
  My first team — has access to code review and enforcement agents.
status: active

plugins:
  - sdlc-core

agents:
  - sdlc-core:verification-enforcer
  - sdlc-core:sdlc-enforcer

skills:
  - sdlc-core:validate

context:
  - CONSTITUTION.md
```

Build the team image:

```bash
bash plugins/sdlc-workflows/docker/build-team.sh my-team
```

This validates the manifest, generates a team-specific CLAUDE.md with role framing, and builds `sdlc-worker:my-team`.

## Step 3: Create a Workflow

Workflows define a DAG of nodes. Each node runs in a container with the specified team image.

Create `.archon/workflows/my-pipeline.yaml`:

```yaml
name: my-pipeline
description: |
  Simple implement-then-review pipeline.

provider: claude

nodes:
  - id: implement
    command: my-implement
    image: sdlc-worker:my-team

  - id: review
    command: my-review
    image: sdlc-worker:my-team
    depends_on: [implement]
```

Create the command prompts in `.archon/commands/`:

**`.archon/commands/my-implement.md`**:
```markdown
You are implementing a change at /workspace.

<Describe the task here — what to read, what to change, what to create.>

After making changes, commit:
  cd /workspace && git add -A && git commit -m "feat: description"
```

**`.archon/commands/my-review.md`**:
```markdown
You are reviewing changes at /workspace.

Read the recent commits: cd /workspace && git log --oneline -5

Review for correctness, edge cases, and test coverage.

Write your review to /workspace/review.md with ## Summary, ## Issues, ## Recommendation.
Then commit: cd /workspace && git add -A && git commit -m "review: findings"
```

## Step 4: Run the Workflow

Use the skill:

```
/sdlc-workflows:workflows-run my-pipeline
```

Or use the CLI directly:

```bash
# Resolve credentials
CRED_JSON=$(python3 plugins/sdlc-workflows/scripts/resolve_credentials.py --json)
CRED_MOUNT=$(echo "$CRED_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['mount_args'])")

# Preprocess workflow (transforms image: nodes to docker run commands).
# Writes the preprocessed copy to .generated/ -- the source YAML is never
# overwritten, so the run is idempotent (repeat safely).
mkdir -p .archon/workflows/.generated
python3 plugins/sdlc-workflows/scripts/preprocess_workflow.py \
    .archon/workflows/my-pipeline.yaml \
    --output .archon/workflows/.generated/my-pipeline.yaml \
    --workspace "$(pwd)" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir "$(pwd)/.archon/commands"

# Run via Archon. Archon resolves workflows by the `name:` field and
# scans `.archon/workflows/.generated/` for preprocessed copies — the
# source YAML under `.archon/workflows/` is left untouched, so repeat
# runs are idempotent.
archon workflow run my-pipeline --no-worktree
```

## Step 5: Verify Results

```bash
git log --oneline -5       # See commits from each container
ls *.md                     # See generated review files
```

## Credential Tiers

| Environment | Setup | How it works |
|-------------|-------|-------------|
| **Mac** | None (automatic) | Credentials extracted from macOS Keychain |
| **Linux** | Run `plugins/sdlc-workflows/scripts/login.sh` | Creates Docker volume `sdlc-claude-credentials` |
| **Custom** | Create `.archon/credentials.yaml` | Point to credential file path |

Check your current tier:
```bash
python3 plugins/sdlc-workflows/scripts/resolve_credentials.py
```

## Or Use the Authoring Skill

Instead of writing workflow YAML by hand, ask Claude Code:

```
/sdlc-workflows:author-workflow
```

This interactive skill asks what you want to build, generates the workflow YAML, command prompts, and validates everything.

## Reference Implementation

Want to see every step above wired together and actually executed? The
end-to-end smoke test is a working reference implementation:

```
tests/integration/workforce-smoke/run-e2e.sh
```

It builds base + full + team images, resolves credentials, patches Archon,
launches team containers through a real workflow (parallel fan-out +
synthesis), and asserts the expected commits landed in the workspace. Treat
it as the canonical "how should this look when it works" — when something in
the quickstart diverges, diff against this script.

## Next Steps

- Read `CLAUDE-CONTEXT-workflows.md` for the full schema reference
- Use `/sdlc-workflows:manage-teams` to manage team lifecycle
- Use `/sdlc-workflows:teams-status` for fleet visibility
- See `plugins/sdlc-workflows/docs/troubleshooting.md` if something goes wrong

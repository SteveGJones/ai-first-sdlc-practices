# Docker Setup Smoke Test

**Date**: 2026-04-06
**Status**: Approved
**Issue**: #85
**Branch**: `feature/docker-smoke-test`

## Problem

The full integration test (`tests/integration/PROMPT.md`) takes 45-60 minutes and builds a complete web app. We have no fast, reproducible way to verify that the plugin installation and setup-team flow works correctly. When we change plugins, agents, or skills, we need a quick test that proves setup still produces the right outputs.

## Solution

A Docker-based smoke test that installs plugins from the public GitHub repo, runs setup-team on a realistic project fixture, installs all recommended tools, and verifies the outputs. Uses the developer's Claude Code Max subscription via mounted credentials. Completes in ~5 minutes.

## Architecture

### Two-layer approach

**Base image** (`sdlc-smoke-base:latest`):
- `node:22-slim` with Claude Code CLI, Ralph, Python 3, git
- No plugins, no auth, no project-specific content
- Built once, cached locally. Rebuild only when tooling versions change.

**Runtime container** (disposable):
- Mounts host `~/.claude` and `~/.claude.json` for Claude Code Max auth
- Loop installs plugins from the **public GitHub marketplace** (not local)
- Runs the smoke test phases
- Disposed after test completes

### Auth

Claude Code Max uses OAuth stored in `~/.claude.json` (session token) and `~/.claude/` (session state, statsig). The container mounts both read-only from the host.

The `ANTHROPIC_API_KEY` environment variable must NOT be set — if present, Claude Code switches to pay-per-token billing instead of using the Max subscription.

To authenticate for the first time (or if session expires):
1. Run `claude` or `claude /login` inside the container
2. Browser won't open in headless container — press `c` to copy the login URL
3. Paste URL in host browser, complete login
4. Container session updates automatically

For ongoing use: authenticate once on the host, then the mounted credentials work in the container.

## Test Fixture: EventFlow

A realistic project README that exercises broad tech stack detection and discovery.

`fixtures/eventflow/README.md`:

```markdown
# EventFlow

Real-time event analytics platform for e-commerce. Ingests customer events
via Apache Kafka, stores in MongoDB for flexible schema, processes with
Python workers, serves dashboards via React frontend backed by a FastAPI
REST API. Uses Redis for caching and session management. Deployed to AWS
with Terraform. Business reporting exported as PowerPoint presentations
for stakeholder reviews.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Celery workers
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Database**: MongoDB Atlas (primary store), Redis (cache + sessions)
- **Messaging**: Apache Kafka (event streaming)
- **Infrastructure**: AWS (ECS, S3, CloudWatch), Terraform
- **Reporting**: Python-pptx for automated PowerPoint generation
- **CI/CD**: GitHub Actions
- **Monitoring**: Grafana + Prometheus
```

This should trigger discovery for: MongoDB MCP, Kafka tools, Redis MCP, React/TypeScript tooling, AWS MCP, Terraform MCP, Grafana tools, GitHub Actions, and potentially PowerPoint/document tools.

## Smoke Test Phases

### Phase 0: Install & Verify Plugins

Install the SDLC plugins from the public GitHub marketplace:

```
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
/plugin install sdlc-team-common@ai-first-sdlc
/plugin install sdlc-team-fullstack@ai-first-sdlc
/plugin install sdlc-team-pm@ai-first-sdlc
/plugin install sdlc-team-docs@ai-first-sdlc
/plugin install sdlc-lang-python@ai-first-sdlc
```

Verify with `/plugin list`. All 6 should be present.

If any fail, record the error and stop.

### Phase 1: Run Setup-Team

Execute the setup-team flow:
- Detect tech stack from the EventFlow README.md
- Present findings and confirm (auto-accept in loop context)
- Run discovery for each detected technology
- Produce the three-section recommendation (SDLC Framework / Technology-Specific Tools / Project Support)
- Write `.sdlc/team-config.json` and `.sdlc/recommended-plugins.json`

### Phase 2: Install Recommended Tools

For every tool in `.sdlc/recommended-plugins.json`, attempt to install it:
- MCP servers: `npm install -g <package>` or `pip install <package>`
- GitHub Actions: verify the action exists (no install needed, just verify URL resolves)
- Agent skills: `git clone` the repo if it's a GitHub URL

Record success/failure for each tool.

### Phase 3: Verify Outputs

Check:
1. `.sdlc/team-config.json` exists and contains:
   - `project_type` is set
   - `formation` is set
   - `installed_plugins` is a non-empty array
   - `technologies_detected` includes at least: mongodb, redis, kafka, react, aws, terraform
2. `.sdlc/recommended-plugins.json` exists and contains:
   - `version` is "1.0"
   - `plugins` is a non-empty array
   - At least one entry has `type: "mcp-server"`
   - At least one entry has `installed: true`
3. All tools from Phase 2 that were marked `installed: true` are actually available:
   - MCP servers: `which <binary>` or `npm list -g <package>`
   - Python packages: `pip show <package>`

Report pass/fail for each check.

LOOP_COMPLETE after all checks reported.

## Files in Repo (checked in)

```
tests/integration/setup-smoke/
  Dockerfile                 — Base image definition
  build.sh                   — Builds sdlc-smoke-base:latest
  run.sh                     — Mounts auth, runs test, reports results
  entrypoint.sh              — Container entrypoint (copies auth, runs ralph)
  PROMPT.md                  — 4-phase setup smoke test
  ralph.yml                  — 10 iteration limit
  fixtures/
    eventflow/
      README.md              — EventFlow project description
  README.md                  — How to build and run the smoke test
```

## NOT Checked In

- The Docker image itself (built locally, cached)
- Any credentials or auth tokens
- Test output files

## Dockerfile

```dockerfile
FROM node:22-slim

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv git curl && \
    rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Install Ralph
RUN npm install -g @ralph-orchestrator/ralph-cli

WORKDIR /workspace

COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
```

## build.sh

```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
docker build -t sdlc-smoke-base:latest "$SCRIPT_DIR"
echo "Built sdlc-smoke-base:latest"
```

## run.sh

```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify auth exists
if [ ! -f "$HOME/.claude.json" ]; then
    echo "ERROR: ~/.claude.json not found. Authenticate Claude Code on your host first."
    exit 1
fi

# Ensure ANTHROPIC_API_KEY is NOT set (would override Max subscription)
unset ANTHROPIC_API_KEY

docker run --rm \
    -v "$HOME/.claude:/host-claude:ro" \
    -v "$HOME/.claude.json:/host-claude.json:ro" \
    -v "$SCRIPT_DIR/PROMPT.md:/workspace/PROMPT.md:ro" \
    -v "$SCRIPT_DIR/ralph.yml:/workspace/ralph.yml:ro" \
    -v "$SCRIPT_DIR/fixtures/eventflow/README.md:/workspace/README.md:ro" \
    sdlc-smoke-base:latest
```

## entrypoint.sh

```bash
#!/bin/bash
set -e

# Copy auth from read-only mounts to writable locations
cp -r /host-claude /root/.claude
cp /host-claude.json /root/.claude.json

# Ensure no API key (use Max subscription)
unset ANTHROPIC_API_KEY

# Run the smoke test
cd /workspace
ralph run
```

## ralph.yml

```yaml
cli:
  backend: "claude"

event_loop:
  prompt_file: "PROMPT.md"
  completion_promise: "LOOP_COMPLETE"
  max_iterations: 10
```

## Success Criteria

1. `build.sh` produces `sdlc-smoke-base:latest` from the Dockerfile
2. `run.sh` starts a container with mounted auth, no API key
3. Plugins install from public GitHub marketplace
4. Setup-team detects the EventFlow tech stack
5. Discovery finds real tools for MongoDB, Redis, Kafka, AWS, etc.
6. All recommended tools install successfully
7. `.sdlc/team-config.json` and `.sdlc/recommended-plugins.json` are valid
8. Test completes in under 10 minutes
9. No credentials in git, no image in git

## Future: Local Plugin Testing

For development (testing unpublished plugin changes), add an optional flag:
```bash
./run.sh --local /path/to/ai-first-sdlc-practices
```

This would mount the local repo and configure the marketplace to read from it instead of GitHub. Not in scope for this issue.

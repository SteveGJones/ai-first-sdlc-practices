# Docker Setup Smoke Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Docker-based smoke test that installs SDLC plugins from GitHub, runs setup-team on a realistic project fixture, installs all recommended tools, and verifies outputs — using the developer's Claude Code Max subscription.

**Architecture:** A base Docker image (`sdlc-smoke-base:latest`) with Claude Code + Ralph + Python + git, cached locally. At runtime, auth credentials are mounted from the host. A Ralph loop runs through 4 phases: plugin install, setup-team, tool install, output verification.

**Tech Stack:** Docker, node:22-slim base, Claude Code CLI, Ralph orchestrator, Bash scripts

---

### Task 1: Create the Dockerfile

**Files:**
- Create: `tests/integration/setup-smoke/Dockerfile`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p tests/integration/setup-smoke/fixtures/eventflow
```

- [ ] **Step 2: Write the Dockerfile**

Create `tests/integration/setup-smoke/Dockerfile`:

```dockerfile
FROM node:22-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Install Ralph orchestrator
RUN npm install -g @ralph-orchestrator/ralph-cli

WORKDIR /workspace

# Copy entrypoint script
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
```

- [ ] **Step 3: Commit**

```bash
git add tests/integration/setup-smoke/Dockerfile
git commit -m "feat: add Dockerfile for setup smoke test (#85)

node:22-slim base with Claude Code CLI, Ralph, Python 3, git.
No plugins or auth baked in — mounted at runtime."
```

---

### Task 2: Create the entrypoint script

**Files:**
- Create: `tests/integration/setup-smoke/entrypoint.sh`

- [ ] **Step 1: Write entrypoint.sh**

Create `tests/integration/setup-smoke/entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "=== SDLC Setup Smoke Test ==="
echo ""

# Step 1: Copy auth from read-only mounts to writable locations
if [ -d /host-claude ]; then
    echo "Copying Claude credentials from host..."
    cp -r /host-claude /root/.claude
else
    echo "WARNING: /host-claude not mounted. Auth may fail."
    mkdir -p /root/.claude
fi

if [ -f /host-claude.json ]; then
    cp /host-claude.json /root/.claude.json
else
    echo "WARNING: /host-claude.json not mounted. OAuth session may be missing."
fi

# Step 2: Ensure no API key set (use Max subscription)
unset ANTHROPIC_API_KEY

# Step 3: Verify Claude Code is available
echo "Claude Code version: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Ralph version: $(ralph --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python version: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 4: Initialize git repo (Ralph needs a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "smoke-test@example.com"
    git config user.name "Smoke Test"
    git add -A
    git commit -m "initial" --allow-empty
fi

# Step 5: Run the smoke test via Ralph
echo "Starting Ralph loop..."
ralph run

echo ""
echo "=== Smoke Test Complete ==="

# Step 6: Report results
if [ -f .sdlc/team-config.json ]; then
    echo "PASS: .sdlc/team-config.json exists"
    echo "Contents:"
    cat .sdlc/team-config.json | python -m json.tool
else
    echo "FAIL: .sdlc/team-config.json not found"
    exit 1
fi

echo ""

if [ -f .sdlc/recommended-plugins.json ]; then
    echo "PASS: .sdlc/recommended-plugins.json exists"
    echo "Plugins found: $(python -c "import json; d=json.load(open('.sdlc/recommended-plugins.json')); print(len(d.get('plugins',[])))")"
else
    echo "FAIL: .sdlc/recommended-plugins.json not found"
    exit 1
fi
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/setup-smoke/entrypoint.sh
git commit -m "feat: add entrypoint.sh for smoke test container (#85)

Copies auth from host mounts, verifies tooling, inits git repo,
runs Ralph, reports pass/fail on output files."
```

---

### Task 3: Create build.sh and run.sh

**Files:**
- Create: `tests/integration/setup-smoke/build.sh`
- Create: `tests/integration/setup-smoke/run.sh`

- [ ] **Step 1: Write build.sh**

Create `tests/integration/setup-smoke/build.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building sdlc-smoke-base:latest..."
docker build -t sdlc-smoke-base:latest "$SCRIPT_DIR"
echo ""
echo "Done. Image: sdlc-smoke-base:latest"
echo "Run the smoke test with: $SCRIPT_DIR/run.sh"
```

- [ ] **Step 2: Write run.sh**

Create `tests/integration/setup-smoke/run.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify auth exists on host
if [ ! -f "$HOME/.claude.json" ]; then
    echo "ERROR: ~/.claude.json not found."
    echo "Authenticate Claude Code on your host first: run 'claude' and log in."
    exit 1
fi

if [ ! -d "$HOME/.claude" ]; then
    echo "ERROR: ~/.claude/ directory not found."
    echo "Authenticate Claude Code on your host first: run 'claude' and log in."
    exit 1
fi

# Verify base image exists
if ! docker image inspect sdlc-smoke-base:latest >/dev/null 2>&1; then
    echo "Base image not found. Building..."
    "$SCRIPT_DIR/build.sh"
fi

# Ensure ANTHROPIC_API_KEY is NOT set (would override Max subscription)
unset ANTHROPIC_API_KEY

echo "=== Running SDLC Setup Smoke Test ==="
echo "Auth: Claude Code Max subscription (from host)"
echo "Plugins: installed from public GitHub during test"
echo ""

docker run --rm \
    -v "$HOME/.claude:/host-claude:ro" \
    -v "$HOME/.claude.json:/host-claude.json:ro" \
    -v "$SCRIPT_DIR/PROMPT.md:/workspace/PROMPT.md:ro" \
    -v "$SCRIPT_DIR/ralph.yml:/workspace/ralph.yml:ro" \
    -v "$SCRIPT_DIR/fixtures/eventflow/README.md:/workspace/README.md:ro" \
    sdlc-smoke-base:latest

echo ""
echo "=== Smoke Test Finished ==="
```

- [ ] **Step 3: Make both executable**

```bash
chmod +x tests/integration/setup-smoke/build.sh
chmod +x tests/integration/setup-smoke/run.sh
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/setup-smoke/build.sh tests/integration/setup-smoke/run.sh
git commit -m "feat: add build.sh and run.sh for smoke test (#85)

build.sh creates sdlc-smoke-base:latest Docker image.
run.sh mounts host Claude credentials and runs the test."
```

---

### Task 4: Create the EventFlow fixture

**Files:**
- Create: `tests/integration/setup-smoke/fixtures/eventflow/README.md`

- [ ] **Step 1: Write the EventFlow README**

Create `tests/integration/setup-smoke/fixtures/eventflow/README.md`:

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

## Architecture

Events flow from client SDKs → Kafka topics → Python Celery workers →
MongoDB collections. The FastAPI backend serves both the React dashboard
and the REST API for external integrations. Redis handles session state
and hot-path caching. Terraform manages all AWS infrastructure as code.

Weekly stakeholder reports are generated automatically as PowerPoint
presentations from MongoDB aggregation queries.
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/setup-smoke/fixtures/eventflow/README.md
git commit -m "feat: add EventFlow fixture for smoke test (#85)

Realistic project README exercising broad tech stack detection:
MongoDB, Kafka, Redis, React, FastAPI, AWS, Terraform, Grafana."
```

---

### Task 5: Create PROMPT.md and ralph.yml

**Files:**
- Create: `tests/integration/setup-smoke/PROMPT.md`
- Create: `tests/integration/setup-smoke/ralph.yml`

- [ ] **Step 1: Write ralph.yml**

Create `tests/integration/setup-smoke/ralph.yml`:

```yaml
# SDLC Setup Smoke Test
# Tests plugin installation + setup-team flow in a Docker container

cli:
  backend: "claude"

event_loop:
  prompt_file: "PROMPT.md"
  completion_promise: "LOOP_COMPLETE"
  max_iterations: 10
```

- [ ] **Step 2: Write PROMPT.md**

Create `tests/integration/setup-smoke/PROMPT.md`:

```markdown
# Setup Smoke Test

You are running inside a Docker container. Your job is to install the SDLC plugins, run setup-team on this project, install all recommended tools, and verify everything works.

The project README.md describes an EventFlow analytics platform. Read it to understand the tech stack.

## Phase 0: Install Plugins

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

Verify with `/plugin list`. All 6 should appear.

If any install fails, record the error and stop.

## Phase 1: Run Setup-Team

Read the project README.md to understand the tech stack.

Run the setup-team flow:
1. Select **A. Full-stack web application** as the project type
2. When asked about technologies, confirm the detected stack and add any that were missed
3. Accept the three-section recommendation (SDLC Framework / Technology-Specific Tools / Project Support)
4. Confirm installation of all recommended items

The setup-team skill should:
- Detect from README.md: MongoDB, Redis, Kafka, React, FastAPI, AWS, Terraform, Grafana, GitHub Actions
- Run discovery for each technology
- Write `.sdlc/team-config.json` and `.sdlc/recommended-plugins.json`

## Phase 2: Install Recommended Tools

Read `.sdlc/recommended-plugins.json`. For every tool listed:

**MCP servers** (type: mcp-server):
```bash
npm install -g <package-name>
```

**Python packages**:
```bash
pip install <package-name>
```

**Agent skills** (type: agent-skills, GitHub URLs):
```bash
git clone <url> /opt/agent-skills/<name>
```

**GitHub Actions** (type: action):
No install needed — just verify the URL resolves with curl.

Record success/failure for each tool. If a tool fails to install, note the error but continue with the remaining tools.

## Phase 3: Verify Outputs

Check the following. Report PASS or FAIL for each:

1. `.sdlc/team-config.json` exists
2. `team-config.json` has `project_type` set
3. `team-config.json` has `formation` set
4. `team-config.json` has `installed_plugins` as a non-empty array
5. `team-config.json` has `technologies_detected` with at least 5 entries
6. `.sdlc/recommended-plugins.json` exists
7. `recommended-plugins.json` has `plugins` as a non-empty array
8. At least one plugin has `type: "mcp-server"`
9. At least one plugin has `installed: true`
10. All tools marked `installed: true` are actually available:
    - For npm packages: `npm list -g <package> 2>/dev/null`
    - For pip packages: `pip show <package> 2>/dev/null`
    - For cloned repos: `ls /opt/agent-skills/<name> 2>/dev/null`

Print a summary:

```
=== Smoke Test Results ===
Check 1 (team-config exists):       PASS/FAIL
Check 2 (project_type set):         PASS/FAIL
Check 3 (formation set):            PASS/FAIL
Check 4 (installed_plugins):        PASS/FAIL
Check 5 (technologies_detected):    PASS/FAIL
Check 6 (recommended-plugins exists): PASS/FAIL
Check 7 (plugins array):            PASS/FAIL
Check 8 (has mcp-server):           PASS/FAIL
Check 9 (has installed tool):       PASS/FAIL
Check 10 (tools actually work):     PASS/FAIL

Result: X/10 PASS
```

Output `LOOP_COMPLETE`.
```

- [ ] **Step 3: Commit**

```bash
git add tests/integration/setup-smoke/PROMPT.md tests/integration/setup-smoke/ralph.yml
git commit -m "feat: add PROMPT.md and ralph.yml for smoke test (#85)

4-phase test: install plugins from GitHub, run setup-team,
install all recommended tools, verify 10 output checks."
```

---

### Task 6: Create the README

**Files:**
- Create: `tests/integration/setup-smoke/README.md`

- [ ] **Step 1: Write the README**

Create `tests/integration/setup-smoke/README.md`:

```markdown
# SDLC Setup Smoke Test

Fast Docker-based test that verifies plugin installation and setup-team work correctly. Uses your Claude Code Max subscription — no API costs.

> **This is a developer smoke test, not a user workflow.** It tests the public plugin install path in a clean, reproducible Docker environment.

## Prerequisites

- Docker installed and running
- Claude Code authenticated on your host machine (`~/.claude.json` exists)
- Claude Code Max subscription (not API key — the test uses your subscription)

## Quick Start

```bash
# Build the base image (first time only, ~2 min)
./build.sh

# Run the smoke test (~5-10 min)
./run.sh
```

## What It Tests

1. **Plugin installation** — installs all 6 SDLC plugins from the public GitHub marketplace
2. **Tech stack detection** — reads the EventFlow README (MongoDB, Kafka, Redis, React, AWS, Terraform, etc.)
3. **1st-party discovery** — searches for official MCP servers, agent skills, plugins, actions for each technology
4. **Tool installation** — actually installs all recommended tools to verify they exist
5. **Output verification** — checks `.sdlc/team-config.json` and `.sdlc/recommended-plugins.json` structure

## How It Works

- `build.sh` creates `sdlc-smoke-base:latest` — a Docker image with Claude Code, Ralph, Python, and git
- `run.sh` mounts your Claude credentials (read-only) and starts the test
- Inside the container, Ralph drives Claude through 4 phases
- The entrypoint script reports pass/fail on output files

## Auth

The container uses your Claude Code Max subscription via mounted credentials:
- `~/.claude` mounted read-only at `/host-claude`
- `~/.claude.json` mounted read-only at `/host-claude.json`
- `ANTHROPIC_API_KEY` is explicitly unset to prevent pay-per-token billing

If your auth session expires, re-authenticate on your host (`claude` → log in) and re-run.

## The Fixture

The test uses "EventFlow" — a realistic e-commerce event analytics platform with:
- MongoDB, Redis, Kafka, FastAPI, React, TypeScript
- AWS, Terraform, Grafana, Prometheus
- GitHub Actions, Python-pptx

This exercises broad tech stack detection and discovery across multiple vendor ecosystems.

## Rebuilding the Base Image

Rebuild when Claude Code, Ralph, or system dependencies change:

```bash
./build.sh
```

Day-to-day test runs reuse the cached base image.

## Troubleshooting

**"~/.claude.json not found"**: Authenticate Claude Code on your host first. Run `claude` in a terminal and complete the login.

**"Base image not found"**: Run `./build.sh` first.

**Auth fails inside container**: Your session may have expired. Re-authenticate on the host and re-run.

**Test times out (10 iterations)**: Check the Ralph logs inside the container. The setup-team discovery may be hitting rate limits on web searches.
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/setup-smoke/README.md
git commit -m "docs: add README for setup smoke test (#85)

Prerequisites, quick start, how it works, auth, fixture,
troubleshooting."
```

---

### Task 7: Feature Proposal and Push

**Files:**
- Create: `docs/feature-proposals/85-docker-smoke-test.md`

- [ ] **Step 1: Create the feature proposal**

Create `docs/feature-proposals/85-docker-smoke-test.md`:

```markdown
# Feature Proposal: Docker Setup Smoke Test

**Proposal Number:** 85
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-06
**Target Branch:** `feature/docker-smoke-test`

---

## Executive Summary

Docker-based smoke test for the SDLC plugin ecosystem. Verifies plugin installation from GitHub, setup-team tech detection and discovery, tool installation, and output file correctness in a clean, reproducible environment.

---

## Motivation

### Problem Statement

No fast way to verify plugin installation and setup-team work correctly after changes. The full integration test takes 45-60 minutes. We need a ~5 minute test in a reproducible environment.

### User Stories

- As a framework developer, I want to verify my plugin changes work in a clean environment
- As a framework developer, I want a fast test that catches setup regressions

---

## Proposed Solution

Docker image with Claude Code + Ralph + Python + git. Mounts host Claude Code Max credentials. Installs plugins from public GitHub, runs setup-team on EventFlow fixture, installs recommended tools, verifies outputs.

### Acceptance Criteria

Given a built Docker image and authenticated host
When `./run.sh` is executed
Then all 10 verification checks pass

---

## Success Criteria

- [ ] Docker image builds
- [ ] Plugins install from public GitHub
- [ ] Setup-team detects EventFlow tech stack
- [ ] Recommended tools install successfully
- [ ] Output files pass 10-point verification

---

## Changes Made

| Action | File |
|--------|------|
| Create | `tests/integration/setup-smoke/Dockerfile` |
| Create | `tests/integration/setup-smoke/build.sh` |
| Create | `tests/integration/setup-smoke/run.sh` |
| Create | `tests/integration/setup-smoke/entrypoint.sh` |
| Create | `tests/integration/setup-smoke/PROMPT.md` |
| Create | `tests/integration/setup-smoke/ralph.yml` |
| Create | `tests/integration/setup-smoke/fixtures/eventflow/README.md` |
| Create | `tests/integration/setup-smoke/README.md` |
```

- [ ] **Step 2: Commit**

```bash
git add docs/feature-proposals/85-docker-smoke-test.md
git commit -m "docs: add feature proposal for #85"
```

- [ ] **Step 3: Push branch**

```bash
git push -u origin feature/docker-smoke-test
```

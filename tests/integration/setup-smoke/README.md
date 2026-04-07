# SDLC Setup Smoke Test

Fast Docker-based test that verifies plugin installation and setup-team work correctly. Uses your Claude Code Max subscription — no API costs, no API key.

> **This is a developer smoke test, not a user workflow.** It tests the public plugin install path in a clean, reproducible Docker environment.

## What It Does (Verified)

A single test run takes ~5-6 minutes and verifies:

1. **Plugin installation** — installs all 6 SDLC plugins from the public GitHub marketplace via Claude Code's `/plugin install`
2. **Tech stack detection** — reads the EventFlow README, detects ~14 technologies (MongoDB, Kafka, Redis, React, FastAPI, AWS, Terraform, Grafana, Python, Celery, TypeScript, Prometheus, Tailwind, GitHub Actions)
3. **1st-party discovery** — runs web searches for each technology, finds official MCP servers (`mongodb-mcp-server`, `terraform-mcp-server`, `mcp-grafana`, `awslabs-mcp`, `@modelcontextprotocol/server-redis`, etc.)
4. **Tool installation** — actually `npm install`s, `pip install`s, and `git clone`s the discovered tools
5. **Output verification** — 10-point check on `.sdlc/team-config.json` and `.sdlc/recommended-plugins.json`

Last successful run: 1 Ralph iteration, 348 seconds, 10/10 PASS, 14 plugins recommended and installed.

## Prerequisites

- Docker installed and running
- Claude Code Max subscription (the test uses your subscription, not an API key)
- This repo cloned locally

## Quick Start

```bash
cd tests/integration/setup-smoke

# 1. Build the base image (first time only, ~2 min)
./build.sh

# 2. Authenticate Claude Code inside the container (first time only)
./login.sh
# Follow the prompts: paste the OAuth URL into your host browser,
# complete login, paste the code back. Credentials are stored in
# the named Docker volume 'sdlc-smoke-claude-creds'.

# 3. Run the smoke test (~5-6 min)
./run.sh
```

Before running, the script assumes:

- Docker is running (check: `docker info`)
- Auth volume exists (check: `docker volume ls --filter name=sdlc-smoke-claude-creds`) — created by `./login.sh`
- Base image exists (check: `docker image inspect sdlc-smoke-base:latest`) — created by `./build.sh`
- Fixture directory exists at `fixtures/eventflow/` (the only fixture currently shipped)

If any of those is missing, run the corresponding setup step.

## How It Works

### The four scripts

| Script | Purpose | Run as |
|--------|---------|--------|
| `build.sh` | Builds `sdlc-smoke-base:latest` Docker image | One-time + when deps change |
| `login.sh` | Interactive Claude Code OAuth login, stores credentials in named volume | One-time + when session expires |
| `run.sh` | Runs the smoke test against the EventFlow fixture | Every time |
| `entrypoint.sh` | Container entrypoint — runs Ralph, reports output file checks | Auto (called by run.sh) |

### The Docker image

- **Base**: `node:22-slim` (Claude Code is a Node.js package)
- **Tooling**: Python 3, git, curl, xz-utils
- **CLI tools**: `@anthropic-ai/claude-code` (npm), `@ralph-orchestrator/ralph-cli` (npm)
- **User**: Non-root `sdlc` user (UID 1001) — required because `--dangerously-skip-permissions` refuses to run as root
- **Pre-created `/home/sdlc/.claude`** — owned by sdlc, so the named volume inherits the right ownership on first mount

### Auth flow

The container uses your Claude Code Max subscription via a **named Docker volume**, NOT a host bind mount. Here's why and how:

1. **Why not a bind mount?** Claude Code's OAuth credentials don't transfer cleanly across host bind mounts. The auth state has multiple components (`.claude.json`, `.claude/.credentials.json`, session tokens) that need to be writable by the in-container user. Mounting `~/.claude` from the host runs into permission and path-mismatch issues.

2. **Named volume approach**: `login.sh` runs Claude Code interactively inside a container with `sdlc-smoke-claude-creds` mounted at `/home/sdlc/.claude`. The OAuth login writes credentials directly into the volume. Future runs of `run.sh` mount the same volume — credentials persist between runs.

3. **`.claude.json` restoration**: Claude Code writes a parallel `~/.claude.json` (config file) outside the `.claude/` directory. Since our volume only mounts `.claude/`, the entrypoint restores `.claude.json` from a backup inside the volume on every run.

4. **No API key**: The entrypoint explicitly `unset ANTHROPIC_API_KEY` because if it's set, Claude Code switches to pay-per-token API billing instead of using your Max subscription.

## What This Doesn't Touch

- **No host filesystem writes** — the test runs entirely inside Docker
- **No credentials in git** — `.claude/` and `.claude.json` are gitignored, but they never reach the working directory anyway
- **No host `~/.claude` modification** — the container has its own credential volume, isolated from your host Claude Code installation
- **No global plugin install on host** — plugins install inside the container only

## Lessons Learned (the hard way)

When we built this, we hit several non-obvious blockers. Documenting them here so future Docker integrations don't repeat the journey.

### 1. `--dangerously-skip-permissions` blocks running as root

Ralph orchestrator invokes Claude with `--dangerously-skip-permissions` (so the loop doesn't pause for permission prompts). Claude Code refuses this flag when running as root for security reasons:

```
--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons
```

**Fix**: Add a non-root user to the Dockerfile and `USER` switch before the entrypoint:
```dockerfile
RUN useradd -m -s /bin/bash -u 1001 sdlc && \
    mkdir -p /workspace /home/sdlc/.claude && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.claude
USER sdlc
```

### 2. Named volume permissions are inherited from the image directory

When Docker mounts a named volume at a path that contains content in the image, the volume **inherits the ownership of that directory**. If the directory doesn't exist in the image, the volume is created with **root ownership**, and the non-root user can't write to it.

**Fix**: Pre-create `/home/sdlc/.claude` (owned by `sdlc`) in the Dockerfile before the `USER` switch. Docker copies the ownership when the volume is first attached.

### 3. UID 1000 is taken in `node:22-slim`

The official Node.js base image already has a `node` user at UID 1000. Trying to `useradd -u 1000 sdlc` fails with exit code 4.

**Fix**: Use UID 1001 for the smoke test user.

### 4. `.claude.json` lives outside `.claude/`

Claude Code's config file is at `~/.claude.json` (parallel to `~/.claude/`), not inside `.claude/`. A named volume mounted at `/home/sdlc/.claude` only persists the directory contents — `.claude.json` is lost between runs.

**Fix**: After login, Claude Code writes a backup of `.claude.json` to `~/.claude/backups/`. The entrypoint script restores from the latest backup on every run:
```bash
LATEST_BACKUP=$(ls -t /home/sdlc/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
[ -n "$LATEST_BACKUP" ] && cp "$LATEST_BACKUP" /home/sdlc/.claude.json
```

### 5. Ralph needs `xz-utils` to extract its binary

Ralph's npm package downloads a pre-built binary from GitHub releases as a `.tar.xz` archive. The npm install fails on `node:22-slim` because `xz` isn't installed:

```
npm error tar (child): xz: Cannot exec: No such file or directory
```

**Fix**: Add `xz-utils` to the apt install in the Dockerfile.

### 6. Ralph silently runs zero iterations on auth failures

When Claude Code fails to start (e.g., the root permission issue above), Ralph doesn't report a clear error. Instead, the loop completes in milliseconds with output like:

```
ITERATION 1 | ralph | 0s elapsed | 1/10
ITERATION 2 | ralph | 0s elapsed | 2/10
...
Loop terminated: Too many consecutive failures
```

**The 0-second iterations are the giveaway** — Ralph isn't actually waiting for Claude. Check the diagnostics log at `.ralph/diagnostics/logs/` for the real error, or run the exact ralph command manually to see Claude's stderr.

The exact command Ralph runs (helpful for debugging):
```bash
echo "$(cat PROMPT.md)" | claude --dangerously-skip-permissions --verbose --output-format stream-json --print --disallowedTools=TodoWrite,TaskCreate,TaskUpdate,TaskList,TaskGet
```

### 7. The completion sigil should be unique

If your `PROMPT.md` includes the completion sigil (e.g., `LOOP_COMPLETE`) inside example output blocks or instructions, Ralph may see it echoed in Claude's response and terminate prematurely. Use a sigil that won't appear naturally — e.g., `<promise>SMOKE_TEST_DONE</promise>` instead of plain `LOOP_COMPLETE`.

(In our case, we kept `LOOP_COMPLETE` because Ralph was correctly detecting it only at the end of Claude's output, but it's a known footgun documented in ralph-orchestrator issue #139.)

## Troubleshooting

**"Base image not found"**: Run `./build.sh` first.

**"Credential volume 'sdlc-smoke-claude-creds' not found"**: Run `./login.sh` first.

**Login script completes but credentials don't work**: Check that the volume is owned by `sdlc:sdlc`, not `root:root`:
```bash
docker run --rm -v sdlc-smoke-claude-creds:/check alpine ls -la /check
```
If it's root-owned, delete the volume (`docker volume rm sdlc-smoke-claude-creds`), rebuild the image (`./build.sh`), and re-run `./login.sh`.

**Auth session expired**: Delete the volume and re-run `login.sh`:
```bash
docker volume rm sdlc-smoke-claude-creds
./login.sh
```

**Ralph terminates with "Too many consecutive failures" in <5 seconds**: Claude Code is failing to start. Most likely cause: image was rebuilt without the non-root user fix. Verify with:
```bash
docker run --rm --entrypoint /bin/bash sdlc-smoke-base:latest -c "id"
```
Should show `uid=1001(sdlc)`. If it shows root, rebuild the image.

**Test takes >10 minutes**: Setup-team discovery may be hitting rate limits on web searches. Check `.ralph/diagnostics/logs/` for details.

## The Fixture

The test uses "EventFlow" — a realistic e-commerce event analytics platform with:
- **Backend**: Python 3.12, FastAPI, Celery
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Data**: MongoDB Atlas, Redis, Apache Kafka
- **Infrastructure**: AWS (ECS, S3), Terraform
- **Reporting**: Python-pptx
- **Monitoring**: Grafana, Prometheus
- **CI/CD**: GitHub Actions

This fixture exercises broad tech stack detection and discovery across multiple vendor ecosystems. The README at `fixtures/eventflow/README.md` is what setup-team reads to detect the stack.

## Security Notes

- **Credentials never touch the working directory** — they live in a Docker named volume managed by Docker
- **`.claude/` and `.claude.json` are gitignored** — even if they accidentally appeared in the working directory, they wouldn't be committed
- **The Docker image is built locally and never published** — it contains tooling but no credentials
- **Add to `.gitignore` if not already present**:
  ```
  .claude/
  .claude.json
  ```

## Future Work

- **CI integration**: To run this in CI, the auth model needs to change. CI runners can't use OAuth interactively. Options: use an API key (costs money), use a long-lived OAuth refresh token (security risk), or run a one-time setup that records the credentials as a CI secret. See [#85](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/85) for the design rationale.
- **Multiple fixtures**: Currently tests only EventFlow. Could add fixtures for AI/ML projects, cloud-native, security-focused, etc.
- **Faster iteration**: The 5-6 minute runtime is dominated by web searches in the discovery phase. Caching discovery results would make subsequent runs instant.

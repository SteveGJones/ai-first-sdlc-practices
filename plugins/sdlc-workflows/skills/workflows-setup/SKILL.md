---
name: workflows-setup
description: Install Archon, build the sdlc-worker Docker images, and configure SDLC workflows. Run once after installing the sdlc-workflows plugin.
disable-model-invocation: false
argument-hint: "[--with-docker | --workflows-only | --health-check]"
---

# Set Up SDLC Delegated Workflows

Install Archon, build the `sdlc-worker:base` + `sdlc-worker:full`
Docker images, and copy SDLC workflow templates and command prompts
into the project.

## Arguments

- *(no argument)* or `--with-docker` (default) — full setup:
  host Archon + workflows + Docker images. Recommended — this is
  the state in which `/sdlc-workflows:workflows-run` will actually
  work.
- `--workflows-only` — host Archon + workflows, **no Docker build**.
  Only use this when you know you already have `sdlc-worker:base`
  and `:full` from an earlier setup; a fresh project that picks
  this will see `workflows-run` fail at the first node with
  "image not found".
- `--health-check` — run diagnostic checks only (skip steps 1-8).

When `--health-check` is passed, skip steps 1-8 and go directly to
step 9.

Default behaviour (no args) is `--with-docker` so a first-time
user ends up in a working state without having to know which flags
to pass.

## Steps

### 1. Check if Archon is already installed

The upstream installer (`curl -fsSL https://archon.diy/install | bash`)
drops the binary at `~/.bun/bin/archon` because Archon is a Bun
runtime app. On macOS this directory is **not on the default shell
PATH** — so the binary exists but `command -v archon` returns nothing
unless the user already has `~/.bun/bin` on PATH.

Detect both cases, because "not on PATH" is very different from "not
installed" (running the installer again is wasted work):

```bash
if command -v archon >/dev/null 2>&1; then
    ARCHON_STATUS=on-path
    ARCHON_BIN=$(command -v archon)
elif [ -x "$HOME/.bun/bin/archon" ]; then
    ARCHON_STATUS=installed-not-on-path
    ARCHON_BIN="$HOME/.bun/bin/archon"
else
    ARCHON_STATUS=missing
fi
```

**If `on-path`:** report and skip to step 3:
```
Archon is already installed and on PATH (version X.Y.Z).
```

**If `installed-not-on-path`:** the binary exists but won't be found
by `/sdlc-workflows:workflows-run`. Do NOT re-run the installer —
that's wasted work. Tell the user explicitly and have them choose:

```
Archon is already installed at ~/.bun/bin/archon but that directory
is NOT on your PATH. /sdlc-workflows:workflows-run will fail to
find it unless you do ONE of the following:

  (a) Add ~/.bun/bin to your shell PATH (permanent fix — recommended):
        echo 'export BUN_INSTALL="$HOME/.bun"' >> ~/.zshrc
        echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.zshrc
        # then open a new terminal

  (b) Run this session with a prefixed PATH (one-shot):
        export PATH="$HOME/.bun/bin:$PATH"

Which would you like?
```

Do NOT edit the user's shell init files without confirmation.

**If `missing`:** proceed to step 2.

### 2. Install Archon

If Archon is not installed, inform the user and install:

```
Archon is not installed. Installing from https://archon.diy...
This will drop the binary at ~/.bun/bin/archon.
```

Run the installer:
```bash
curl -fsSL https://archon.diy/install | bash
```

Verify installation — in that order, both forms must be tried because
the installer typically puts entries in `~/.zshrc` / `~/.bashrc` that
do not take effect until a new shell is spawned:

```bash
if command -v archon >/dev/null 2>&1; then
    archon --version
    POST_INSTALL_STATE=on-path
elif [ -x "$HOME/.bun/bin/archon" ]; then
    "$HOME/.bun/bin/archon" --version
    POST_INSTALL_STATE=installed-not-on-path
else
    POST_INSTALL_STATE=installer-failed
fi
```

**If `on-path`:** all good, proceed.

**If `installed-not-on-path`:** this is the common case right after a
fresh install — the installer added the PATH entry to the shell init
file but the current shell hasn't reloaded it. Tell the user
explicitly:

```
Archon installed at ~/.bun/bin/archon (version X.Y.Z).

IMPORTANT: the installer added ~/.bun/bin to your shell PATH, but the
change only takes effect in NEW shells. To use archon immediately in
THIS session, run:

  export PATH="$HOME/.bun/bin:$PATH"

Or open a new terminal. /sdlc-workflows:workflows-run will fail with
"archon not found" until you do one of these.
```

**If `installer-failed`:** report the error and suggest manual
installation:

```
Archon installation failed. Please install manually:
  macOS/Linux: curl -fsSL https://archon.diy/install | bash
  Homebrew:    brew install coleam00/archon/archon
  See: https://archon.diy for other options

Then re-run this skill.
```

### 3. Create .archon directories

```bash
mkdir -p .archon/workflows .archon/commands
```

### 4. Copy SDLC workflows

Copy workflow YAML files from the plugin install directory into `.archon/workflows/`:

For each file in `${CLAUDE_PLUGIN_ROOT}/workflows/`:
- Check if destination exists in `.archon/workflows/`
- If exists, skip (don't overwrite user customisations)
- If not, copy

Report:
```
Copied SDLC workflows:
  copied: sdlc-parallel-review.yaml
  copied: sdlc-feature-development.yaml
  copied: sdlc-bulk-refactor.yaml
  copied: sdlc-commissioned-pipeline.yaml
  skipped: sdlc-parallel-review.yaml (already exists)
```

### 5. Copy SDLC command prompts

Copy command Markdown files from `${CLAUDE_PLUGIN_ROOT}/commands/` into `.archon/commands/`:

Same skip-if-exists logic as step 4.

Report:
```
Copied SDLC commands:
  copied: sdlc-security-review.md
  copied: sdlc-plan.md
  ... (list all)
```

### 6. Verify workflow discovery

Run: `archon workflow list 2>/dev/null`

Check that SDLC workflows appear in the output. If they don't, check that `.archon/workflows/` is in Archon's workflow discovery path.

Report:
```
Archon workflow discovery:
  found: sdlc-parallel-review
  found: sdlc-feature-development
  found: sdlc-bulk-refactor
  found: sdlc-commissioned-pipeline
```

### 7. Build Docker images (--with-docker only)

If `--with-docker` argument was provided:

Check if Docker is available:
```bash
docker --version 2>/dev/null && docker info >/dev/null 2>&1
```

If Docker is not available:
```
Docker is not installed or not running. Skipping Docker image build.

IMPORTANT: the sdlc-workflows delivery is container-based. Every
workflow node runs inside sdlc-worker:<team> containers. Without
the images, /sdlc-workflows:workflows-run will fail at the first
node.

To finish setup later:
  1. Install and start Docker Desktop: https://docker.com/products/docker-desktop
  2. Re-run: /sdlc-workflows:workflows-setup --with-docker
```

If Docker is available, build the base and full images:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/docker/build-base.sh
bash ${CLAUDE_PLUGIN_ROOT}/docker/build-full.sh
```

The base build includes a CLI verification step — a broken archon
inside the image fails the build immediately (repair plan phase B2).
Report the final image sizes so the user can sanity-check:

```bash
docker image inspect sdlc-worker:base --format '{{.Size}}' | \
  awk '{printf "sdlc-worker:base  %.1f GB\n", $1/1024/1024/1024}'
docker image inspect sdlc-worker:full --format '{{.Size}}' | \
  awk '{printf "sdlc-worker:full  %.1f GB\n", $1/1024/1024/1024}'
```

Then verify end-to-end that the runtime archon inside the image
also works (defence in depth — the build-time check plus this
runtime check together ensure a released image is never broken):

```bash
docker run --rm --entrypoint archon sdlc-worker:base --help \
  >/dev/null 2>&1 && echo OK || echo FAIL
```

If FAIL, the image is corrupt — report to the user and ask them
to rebuild.

### 8. Report next steps

Before telling the user setup is done, verify the three things
`workflows-run` will actually need, so the "next steps" list is
honest:

```bash
# a. Host archon reachable
archon --version >/dev/null 2>&1 && echo HOST_ARCHON=ok || echo HOST_ARCHON=missing

# b. Base image present and its archon CLI works
if docker image inspect sdlc-worker:base >/dev/null 2>&1 && \
   docker run --rm --entrypoint archon sdlc-worker:base --help >/dev/null 2>&1; then
    echo BASE_IMAGE=ok
else
    echo BASE_IMAGE=missing-or-broken
fi

# c. Workflows visible
test -d .archon/workflows && \
   ls .archon/workflows/sdlc-*.yaml >/dev/null 2>&1 && \
   echo WORKFLOWS=ok || echo WORKFLOWS=missing
```

If all three report `ok`, tell the user:

```
SDLC delegated workflows are configured and verified.

Next steps:
  1. Run a parallel review:
       /sdlc-workflows:workflows-run sdlc-parallel-review
  2. View available workflows:
       archon workflow list
  3. Customise workflows:
       edit .archon/workflows/sdlc-*.yaml
  4. Re-check health anytime:
       /sdlc-workflows:workflows-setup --health-check
  5. Watch workflows run (Archon-native monitoring):
       archon workflow status            # live CLI snapshot
       archon serve                       # start web UI on :3090
       open http://localhost:3090         # full dashboard
       /sdlc-workflows:workflows-status   # REST + SQLite, works either way

For the full design, see:
  docs/superpowers/specs/2026-04-10-containerised-delegation-design.md
```

If any check failed, tell the user exactly what to fix — do NOT
leave them to discover the broken state via a failing workflow
run. Example:

```
SDLC setup is incomplete:
  HOST_ARCHON:  missing    → re-run this skill without --workflows-only
  BASE_IMAGE:   missing    → /sdlc-workflows:workflows-setup --with-docker
  WORKFLOWS:    ok

Resolve the above before running /sdlc-workflows:workflows-run.
```

### 9. Delegation health check

Run a comprehensive health check to verify all delegation infrastructure is ready.

#### 9a. Archon status

```bash
if command -v archon >/dev/null 2>&1; then
    archon --version
    echo "Archon: OK (on PATH at $(command -v archon))"
elif [ -x "$HOME/.bun/bin/archon" ]; then
    "$HOME/.bun/bin/archon" --version
    echo "Archon: INSTALLED BUT NOT ON PATH"
    echo "  Binary: $HOME/.bun/bin/archon"
    echo "  Fix:    export PATH=\"\$HOME/.bun/bin:\$PATH\""
    echo "          (persist in ~/.zshrc for future shells)"
else
    echo "Archon: NOT INSTALLED"
    echo "  Fix:    re-run /sdlc-workflows:workflows-setup (step 2)"
fi
```

Include the "installed but not on PATH" state in the final summary —
it is the most common failure mode right after a fresh install, and
silencing it sets the user up for "archon not found" the next time
they try to run a workflow.

#### 9b. Docker connectivity

```bash
docker info >/dev/null 2>&1
```

If Docker is not running or not installed, report:
```
Docker: NOT AVAILABLE
  Container-based delegation requires Docker.
  Install Docker Desktop: https://docker.com/products/docker-desktop
```

#### 9c. Image CLI health

We do NOT patch Archon's schema. The preprocessor
(`preprocess_workflow.py`) rewrites `image:` nodes into
`bash: docker run ...` nodes before Archon ever sees the workflow,
so Archon only processes its native field set. The earlier
sed-based ContainerProvider patch was both wrong (wrong insertion
point) and unnecessary — it has been removed (repair plan phase B).

What we DO verify: that the archon CLI inside
`sdlc-worker:base` actually runs. A broken install would silently
degrade the super-smoke to direct-docker-run mode without archon,
which is how earlier "all green" runs hid real regressions. The
image build itself now fails if `archon --help` does not work, and
this check is the runtime counterpart.

```bash
docker run --rm --entrypoint archon sdlc-worker:base --help \
  >/dev/null 2>&1 && echo OK || echo FAIL
docker run --rm --entrypoint archon sdlc-worker:base workflow --help \
  >/dev/null 2>&1 && echo OK || echo FAIL
```

Report:
```
Archon CLI in image:  OK | FAIL (rebuild sdlc-worker:base)
Archon workflow CMD:  OK | FAIL (rebuild sdlc-worker:base)
```

#### 9d. ARM64 patch status

```bash
docker run --rm sdlc-worker:base grep -q 'executable:' /opt/archon/packages/core/src/clients/claude.ts 2>/dev/null
```

Report:
```
ARM64 patch: applied (upstream fix not yet merged) | not needed
```

#### 9e. Loop signal workaround

```bash
docker run --rm sdlc-worker:base bash /opt/sdlc-scripts/detect-loop-bug.sh 2>/dev/null
```

Report:
```
Loop workaround: active (Archon #1126 not yet fixed) | not needed (bug fixed)
```

#### 9f. Team image verification

For each YAML file in `.archon/teams/`:
1. Read the manifest
2. Check if the corresponding Docker image exists: `docker image inspect sdlc-worker:<team-name>`
3. If the manifest has `image_built` and `updated` timestamps, check for staleness
4. Report agent and skill count from the manifest

```
Team images:
  sdlc-worker:security-review-team   OK (3 agents, 2 skills)
  sdlc-worker:dev-team-python        STALE (manifest updated after last build)
  sdlc-worker:test-team              NOT BUILT
```

If no team manifests exist:
```
Team images: none configured
  Create a team manifest in .archon/teams/ and run /sdlc-workflows:deploy-team
```

#### 9g. Credential injection

Check which credential tier is available for containerised workflow execution:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_credentials.py --project-dir . --json
```

Parse the JSON output and report:

```
Credential injection:
  Tier 1 (Keychain):     OK — Claude Code credentials found
  Tier 2 (Volume):       SKIP — Keychain succeeded
  Tier 3 (Config):       SKIP — Keychain succeeded
  Active tier:           Keychain
```

Or when Keychain fails:

```
Credential injection:
  Tier 1 (Keychain):     FAIL — not macOS or no keychain entry
  Tier 2 (Volume):       OK — sdlc-claude-credentials volume found
  Active tier:           Volume
```

Or when nothing works:

```
Credential injection:
  Tier 1 (Keychain):     FAIL — not macOS
  Tier 2 (Volume):       FAIL — volume not found
  Tier 3 (Config):       FAIL — .archon/credentials.yaml not found
  Active tier:           NONE

  Run: tests/integration/workforce-smoke/login.sh
  Or create: .archon/credentials.yaml with credential_path
```

Include the active tier in the summary report (step 9h).

#### 9h. Summary report

Combine all checks into a single report:

```
Delegation health check:
  Archon (host):       OK (v0.4.2)
  Docker:              OK
  Archon CLI in image: OK
  ARM64 patch:         applied
  Loop workaround:     active
  Team images:         N/N present (M stale)
  Credentials:         OK (tier: Keychain)

  Ready for delegation.
```

Or if issues found:
```
Delegation health check:
  Archon (host):       OK (v0.4.2)
  Docker:              NOT AVAILABLE
  Archon CLI in image: FAIL (rebuild sdlc-worker:base)
  ...
  Credentials:         NONE

  Issues found. Resolve above before running delegated workflows.
```

## Idempotency

This skill is safe to run multiple times. On second invocation:
- Archon already installed: skipped
- Existing workflow files: not overwritten
- Docker image: rebuilt if requested — note that since the default is
  now `--with-docker`, a re-run with no args will rebuild the images.
  Pass `--workflows-only` to skip the Docker step when you only want
  to refresh the workflow YAML copies.

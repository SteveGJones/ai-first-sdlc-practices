---
name: workflows-setup
description: Install Archon, configure SDLC workflows, and optionally build the Docker image. Run once after installing sdlc-workflows plugin.
disable-model-invocation: false
argument-hint: "[--with-docker | --workflows-only]"
---

# Set Up SDLC Delegated Workflows

Install Archon, copy SDLC workflow templates and command prompts into the project, and optionally build the sdlc-worker Docker image.

## Arguments

- `--with-docker` — Install Archon + copy workflows + build Docker image (full setup)
- `--workflows-only` (default) — Install Archon + copy workflows (no Docker build)

## Steps

### 1. Check if Archon is already installed

Run `archon --version 2>/dev/null`.

If Archon is installed, report:
```
Archon is already installed (version X.Y.Z).
```
Skip to step 3.

### 2. Install Archon

If Archon is not installed, inform the user and install:

```
Archon is not installed. Installing from https://archon.diy...
```

Run the installer:
```bash
curl -fsSL https://archon.diy/install | bash
```

Verify installation:
```bash
archon --version
```

If installation fails, report the error and suggest manual installation:
```
Archon installation failed. Please install manually:
  macOS/Linux: curl -fsSL https://archon.diy/install | bash
  Homebrew: brew install coleam00/archon/archon
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

### 7. Optionally build Docker image (--with-docker only)

If `--with-docker` argument was provided:

Check if Docker is available:
```bash
docker --version 2>/dev/null
```

If Docker is not available:
```
Docker is not installed. Skipping Docker image build.
The Docker image is optional — Archon works with worktree isolation
without Docker. To build the image later:
  cd ${CLAUDE_PLUGIN_ROOT}/docker && bash build.sh
```

If Docker is available, build the image:
```bash
cd ${CLAUDE_PLUGIN_ROOT}/docker && bash build.sh
```

Report result.

### 8. Report next steps

```
SDLC delegated workflows are configured.

Next steps:
  1. Run a parallel review: /sdlc-workflows:workflows-run sdlc-parallel-review
  2. View available workflows: archon workflow list
  3. Customise workflows: edit .archon/workflows/sdlc-*.yaml
  4. Build Docker image (if not done): see plugin docker/ directory

For the full design, see:
  docs/superpowers/specs/2026-04-10-containerised-delegation-design.md
```

## Idempotency

This skill is safe to run multiple times. On second invocation:
- Archon already installed: skipped
- Existing workflow files: not overwritten
- Docker image: rebuilt if requested

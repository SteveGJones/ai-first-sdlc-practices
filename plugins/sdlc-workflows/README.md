# sdlc-workflows

Archon workflow templates for delegated parallel execution of SDLC processes. Ships YAML DAGs, command prompts (PROMPT.md-style briefs), a Docker image definition, and setup/run/status skills.

## Prerequisites

- Claude Code CLI
- Archon CLI (https://archon.diy) — installed via `/sdlc-workflows:workflows-setup` or manually

## What This Plugin Provides

- **Workflows** — Archon YAML DAGs for parallel review, feature development, bulk refactor, and commissioned pipelines
- **Commands** — Substantial PROMPT.md-style briefs that frame each worker's role, process, and output format
- **Docker** — Dockerfile and Compose config for building `sdlc-worker` containers with Archon + Claude Code + SDLC plugins
- **Skills** — `workflows-setup` (install Archon + configure), `workflows-run` (execute a workflow), `workflows-status` (check progress)

## Usage

```bash
# Install the plugin
/plugin install sdlc-workflows@ai-first-sdlc

# Set up Archon and configure workflows
/sdlc-workflows:workflows-setup

# Run a parallel review
/sdlc-workflows:workflows-run sdlc-parallel-review
```

## Architecture

Archon orchestrates containers or worktrees. Each execution environment runs a Claude Code session with SDLC plugins installed. Workflow nodes reference our specialist agents by name. The Docker image is the integration point.

See `docs/superpowers/specs/2026-04-10-containerised-delegation-design.md` for full design.

## Docker on Apple Silicon (ARM64)

The Docker image includes a conditional patch for Archon's Claude client that forces the Claude Agent SDK subprocess to run on Node.js instead of Bun. This is needed because Bun's `child_process` stdin pipe handling hangs on ARM64 Linux when the SDK spawns `cli.js` in stream-json mode.

**The patch is conditional**: it checks whether Archon already sets `executable:` in its SDK options. If Archon has merged the upstream fix, the patch is skipped automatically. No action is needed from you — `docker build` handles it.

**Upstream issue**: See `docs/issues/archon-arm64-sdk-executable.md` for the issue filed with Archon.

**Affected platforms**: Only ARM64 Linux containers (Docker Desktop on Apple Silicon Macs). x86_64 Linux (CI runners, cloud VMs) is not affected — Bun works correctly there.

**What it does**: Archon itself runs on Bun (for `bun:sqlite` and `.md` import support). The Claude Agent SDK subprocess — which calls the Claude API — runs on Node.js. Both runtimes are present in the image. The patch adds one line: `executable: "node"` to Archon's SDK options.

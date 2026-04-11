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

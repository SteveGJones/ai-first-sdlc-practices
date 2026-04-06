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

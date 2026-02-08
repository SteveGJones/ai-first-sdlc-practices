# Agent Directory Structure

This document explains the three agent directories in this repository and how they relate to each other.

## Directories

### `agents/` — Authoritative Source

The organized, categorized agent catalog. **All changes go here first.**

```
agents/
├── ai-builders/         # AI infrastructure agents (RAG, orchestration, context)
├── ai-development/      # AI/ML development agents (MCP, prompt engineering)
├── core/                # Core framework agents (enforcer, architect, reviewer)
├── documentation/       # Documentation specialists
├── future/              # Planned agents not yet fully built
├── languages/           # Language-specific expert agents
├── project-management/  # Project tracking and delivery agents
├── sdlc/                # SDLC workflow agents (validator, bootstrapper)
├── templates/           # Orchestrator templates
└── testing/             # Testing and QA specialists
```

### `.claude/agents/` — Runtime Installation

Flat directory used by Claude Code for **this repository's own development**. Contains a subset of agents from `agents/` that are actively used when developing the framework itself.

These files are **copies** of their `agents/` counterparts. They must not diverge.

### `release/agents/` — Distribution Snapshot

Used by `agent-installer.py` to install agents into downstream user projects. Contains the release-ready subset of agents packaged for distribution.

## Sync Rules

1. **Edit in `agents/` only** — never edit `.claude/agents/` or `release/agents/` directly
2. **Propagate to `.claude/agents/`** — copy updated files after editing the source
3. **`agent-installer.py`** handles `agents/` → user project `.claude/agents/` installation
4. **Verify sync** with: `for f in .claude/agents/*.md; do diff -q "$f" "$(find agents/ -name "$(basename $f)" | head -1)"; done`

## Adding a New Agent to `.claude/agents/`

When a new agent in `agents/` should be available for framework development:

```bash
cp agents/category/new-agent.md .claude/agents/new-agent.md
```

Then restart Claude Code to load the new agent.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Plugin Consumer Guide](#plugin-consumer-guide)
  - [What the plugins provide](#what-the-plugins-provide)
    - [Skills (slash commands)](#skills-slash-commands)
    - [Agents (specialist roles)](#agents-specialist-roles)
    - [Rules and enforcement](#rules-and-enforcement)
  - [Installation](#installation)
    - [Step 1: Add the marketplace](#step-1-add-the-marketplace)
    - [Step 2: Install the core plugin](#step-2-install-the-core-plugin)
    - [Step 3: Configure your team](#step-3-configure-your-team)
  - [Which plugins to install](#which-plugins-to-install)
    - [Always install](#always-install)
    - [Recommended for most projects](#recommended-for-most-projects)
    - [By project type](#by-project-type)
    - [Optional](#optional)
  - [Daily workflow](#daily-workflow)
  - [Customisation](#customisation)
    - [Adding or removing plugins](#adding-or-removing-plugins)
    - [Plugin cache](#plugin-cache)
  - [Troubleshooting](#troubleshooting)
    - [Skill not found](#skill-not-found)
    - [Validation fails](#validation-fails)
    - [Agent not responding](#agent-not-responding)
    - [`.claude/` write protection](#claude-write-protection)
  - [Further reading](#further-reading)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Plugin Consumer Guide

This guide explains how the AI-First SDLC plugin ecosystem works for end users. If you've installed the plugins and want to understand what you've got, start here.

## What the plugins provide

The framework has three types of capability:

### Skills (slash commands)

Skills are invoked with `/plugin-name:skill-name`. They are step-by-step workflows that Claude Code follows when you invoke them. Think of them as recipes.

```bash
/sdlc-core:validate --pre-push     # Run the full validation pipeline
/sdlc-core:new-feature 1 auth      # Create a feature with all artifacts
/sdlc-knowledge-base:kb-query "What does research say about caching?"
```

Skills are interactive — Claude reads the skill definition and follows the steps, adapting to your project context. Some skills write files, some run commands, some do both.

### Agents (specialist roles)

Agents are specialist personas that Claude Code can adopt. Each agent has deep expertise in a specific domain — security architecture, database design, prompt engineering, etc.

Agents are invoked in three ways:

1. **Automatically** — Claude Code recognises when a task matches an agent's expertise and invokes it
2. **By name** — "Use the solution-architect agent to review this design"
3. **Via the Agent tool** — dispatched as subagents for parallel work

Agents don't require any special syntax. They're available as soon as their plugin is installed.

### Rules and enforcement

The `sdlc-core` plugin includes:
- **CONSTITUTION.md** — 11 articles of rules covering git workflow, code quality, validation, security, and more
- **Validation pipeline** — 10 automated checks (syntax, lint, format, debt, tests, imports, types, security, static analysis, smoke test)
- **Hooks** — session start banner showing active rules

These enforce zero technical debt from day one.

---

## Installation

### Step 1: Add the marketplace

```bash
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
```

### Step 2: Install the core plugin

```bash
/plugin install sdlc-core@ai-first-sdlc
```

This is the only required plugin. It provides validation, enforcement, and the workflow skills.

### Step 3: Configure your team

```bash
/sdlc-core:setup-team
```

This presents project type options (Full-stack, AI/ML, Cloud, API, Security, Custom) and installs the matching team plugins. You can also install plugins individually.

---

## Which plugins to install

### Always install

- **sdlc-core** — rules, validation, enforcement, workflow skills

### Recommended for most projects

- **sdlc-team-common** — solution architect, database architect, performance engineer, deep-research agent. This is the universal default — it fills architectural gaps that domain-specific plugins don't cover.

### By project type

| Project type | Recommended plugins |
|-------------|-------------------|
| Full-stack web app | `sdlc-team-fullstack`, `sdlc-team-common` |
| AI/ML project | `sdlc-team-ai`, `sdlc-team-common` |
| Cloud-native / SRE | `sdlc-team-cloud`, `sdlc-team-common` |
| Security-sensitive | `sdlc-team-security`, `sdlc-team-common` |
| Python project | `sdlc-lang-python` |
| JS/TS project | `sdlc-lang-javascript` |
| Research-heavy | `sdlc-knowledge-base` |
| Containerised delegation | `sdlc-workflows` |

### Optional

- **sdlc-team-pm** — agile coaching, delivery tracking, retrospective analysis
- **sdlc-team-docs** — technical writing, documentation architecture

---

## Daily workflow

For the step-by-step development workflow (feature creation through PR), see the [HOWTO guide](HOWTO.md#core-workflow).

The short version:

```bash
/sdlc-core:new-feature <num> <name> "<title>"   # Start feature
/sdlc-core:validate --syntax                      # After writing code
/sdlc-core:validate --quick                       # Before commits
/sdlc-core:commit                                 # Validated commit
/sdlc-core:validate --pre-push                    # Before PR
/sdlc-core:pr                                     # Create PR
```

Specialist agents activate automatically when their expertise matches your request — "Review this API design" triggers `api-architect`, "Check for security issues" triggers `security-architect`, etc.

---

## Customisation

### Adding or removing plugins

```bash
# Install a plugin
/plugin install sdlc-team-security@ai-first-sdlc

# List installed plugins
/plugin list

# Re-run setup to get new recommendations
/sdlc-core:setup-team
```

### Plugin cache

Plugins are cached globally at `~/.claude/plugins/cache/`. If a plugin seems outdated:

```bash
rm -rf ~/.claude/plugins/cache/ai-first-sdlc/
```

Then restart Claude Code and reinstall.

---

## Troubleshooting

### Skill not found

The plugin providing that skill isn't installed. Run `/plugin list` to see what you have, then install the missing plugin.

### Validation fails

Run the full validation to see detailed output:

```bash
/sdlc-core:validate --pre-push
```

Each check reports pass/fail/skip with explanations. Skipped checks include install instructions for missing tools.

### Agent not responding

Agents activate automatically when their plugin is installed. If an agent doesn't respond:
1. Verify the plugin is installed (`/plugin list`)
2. Clear the plugin cache and reinstall
3. Restart Claude Code

### `.claude/` write protection

Claude Code blocks writes to `.claude/` in project directories (security feature). This is a known platform limitation — see [issue #81](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/81).

---

## Further reading

- [README.md](../README.md) — Project overview
- [HOWTO.md](HOWTO.md) — Step-by-step usage guide
- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) — Command cheat sheet
- [CONSTITUTION.md](../CONSTITUTION.md) — All rules (11 articles)
- [AGENT-INDEX.md](../AGENT-INDEX.md) — Full catalog of all 56 agents
- Each plugin's README — detailed agent/skill documentation

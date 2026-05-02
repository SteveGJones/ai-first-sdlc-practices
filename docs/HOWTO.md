<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Framework - HOWTO Guide](#ai-first-sdlc-framework---howto-guide)
  - [Quick Start](#quick-start)
    - [1. Install the Core Plugin (2 minutes)](#1-install-the-core-plugin-2-minutes)
    - [2. Configure Your Team](#2-configure-your-team)
    - [3. Create Your First Feature](#3-create-your-first-feature)
  - [Core Workflow](#core-workflow)
    - [Step-by-Step Process](#step-by-step-process)
      - [1. Start a New Feature](#1-start-a-new-feature)
      - [2. Architect Your Solution](#2-architect-your-solution)
      - [3. Implement with Continuous Validation](#3-implement-with-continuous-validation)
      - [4. Commit Your Work](#4-commit-your-work)
      - [5. Complete the Retrospective](#5-complete-the-retrospective)
      - [6. Create a Pull Request](#6-create-a-pull-request)
  - [Using Specialist Agents](#using-specialist-agents)
    - [Architecture and Design](#architecture-and-design)
    - [Code Review](#code-review)
    - [Domain-Specific](#domain-specific)
    - [Research](#research)
  - [Plugin Management](#plugin-management)
    - [Installing Additional Plugins](#installing-additional-plugins)
    - [Available Plugins](#available-plugins)
    - [Clearing Plugin Cache](#clearing-plugin-cache)
  - [The Rules](#the-rules)
  - [Common Scenarios](#common-scenarios)
    - [Starting a New Project](#starting-a-new-project)
    - [Adding a Knowledge Base](#adding-a-knowledge-base)
    - [Setting Up Containerised Workflows](#setting-up-containerised-workflows)
    - [Setting Up a Multi-Team Programme (Method 1)](#setting-up-a-multi-team-programme-method-1)
    - [Setting Up Regulated-Industry Traceability (Method 2)](#setting-up-regulated-industry-traceability-method-2)
  - [Troubleshooting](#troubleshooting)
    - ["Skill not found"](#skill-not-found)
    - [Validation failures](#validation-failures)
    - [Plugin cache issues](#plugin-cache-issues)
    - [`.claude/` write protection](#claude-write-protection)
    - [Pre-commit hooks failing](#pre-commit-hooks-failing)
  - [Best Practices](#best-practices)
  - [Further Reading](#further-reading)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Framework - HOWTO Guide

This guide explains how to use the AI-First SDLC Framework in your daily development workflow using the plugin ecosystem.

## Quick Start

### 1. Install the Core Plugin (2 minutes)

```bash
# Add the marketplace and install sdlc-core
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
```

### 2. Configure Your Team

```bash
/sdlc-core:setup-team
```

This interviews you about your project type and installs the matching team plugins. For example, a full-stack web app gets `sdlc-core`, `sdlc-team-common`, and `sdlc-team-fullstack`.

### 3. Create Your First Feature

```bash
/sdlc-core:new-feature 1 user-authentication "User Authentication System"
```

This creates:
- A feature proposal at `docs/feature-proposals/01-user-authentication.md`
- A retrospective at `retrospectives/01-user-authentication.md`
- A feature branch `feature/user-authentication`

---

## Core Workflow

```
specify → architect → implement → review → ship
```

### Step-by-Step Process

#### 1. Start a New Feature

```bash
/sdlc-core:new-feature <number> <name> "<title>"
```

Edit the generated feature proposal with your requirements, acceptance criteria, and risks.

#### 2. Architect Your Solution

Use specialist agents from your installed team plugins. Claude Code automatically invokes the right agents based on your request:

- "Design the database schema" — invokes `database-architect`
- "Review the API design" — invokes `api-architect`
- "Check for security concerns" — invokes `security-architect`

#### 3. Implement with Continuous Validation

Write code and validate continuously:

```bash
/sdlc-core:validate --syntax      # After writing code
/sdlc-core:validate --quick       # Before commits
```

The validation pipeline checks:
1. **Python AST syntax** — parse all .py files
2. **Ruff syntax errors** — fast syntax-level lint
3. **Ruff full lint** — complete ruff linting
4. **Ruff format check** — formatting compliance
5. **Technical debt scan** — no TODOs, FIXMEs, commented code, `any` types
6. **Test execution** — pytest
7. **Import smoke test** — no missing imports
8. **Type checking** — mypy strict typing
9. **Security scan** — bandit vulnerability detection
10. **Smoke test** — app starts and responds

#### 4. Commit Your Work

```bash
/sdlc-core:commit
```

This runs validation before committing. If checks fail, fix the issues and try again.

#### 5. Complete the Retrospective

Before creating a PR, fill out the retrospective that was generated with your feature:

```
retrospectives/<number>-<name>.md
```

Document what went well, what could improve, and lessons learned.

#### 6. Create a Pull Request

```bash
/sdlc-core:validate --pre-push    # Full 10-check validation
/sdlc-core:pr                     # Creates the PR with validation results
```

---

## Using Specialist Agents

Agents are invoked automatically by Claude Code when their expertise is needed. You can also request them directly:

### Architecture and Design

- "Use the solution-architect agent to design the system" — `sdlc-team-common`
- "Have the database-architect review the schema" — `sdlc-team-common`
- "Get a performance review from the performance-engineer" — `sdlc-team-common`

### Code Review

- "Review this code for quality" — `code-review-specialist` (sdlc-core)
- "Verify this meets the requirements" — `critical-goal-reviewer` (sdlc-core)
- "Check docs-code fidelity" — `verification-enforcer` (sdlc-core)

### Domain-Specific

- "Design the frontend component" — `frontend-architect` (sdlc-team-fullstack)
- "Review the API contract" — `api-architect` (sdlc-team-fullstack)
- "Audit for security vulnerabilities" — `security-architect` (sdlc-team-security)
- "Design the ML pipeline" — `ai-solution-architect` (sdlc-team-ai)

### Research

- "Research best practices for X" — `deep-research-agent` (sdlc-team-common)

See each plugin's README for the full list of agents and their capabilities.

---

## Plugin Management

### Installing Additional Plugins

```bash
# Install a specific plugin
/plugin install sdlc-team-security@ai-first-sdlc

# Re-run setup-team to get recommendations
/sdlc-core:setup-team
```

### Available Plugins

See the [full plugin table in README.md](../README.md#available-plugins) for all 12 plugins with agent and skill counts.

### Clearing Plugin Cache

If plugins seem outdated after an update:

```bash
rm -rf ~/.claude/plugins/cache/ai-first-sdlc/
```

Then restart Claude Code and reinstall.

---

## The Rules

All rules are in [CONSTITUTION.md](../CONSTITUTION.md) — 11 articles covering:

1. Git workflow (feature branches, never commit to main)
2. Documentation (proposals required before implementation)
3. Architecture (design before code)
4. Code quality (no TODOs, no `any` types, no commented code)
5. Validation (10-check pipeline)
6. Agent collaboration (use specialist agents)
7. Logging (10 mandatory logging points for app code)
8. Security (no secrets in code, no PII in logs)
9. Self-review (verify before claiming done)
10. Verification (runtime proof required)
11. Progressive levels (Prototype → Production → Enterprise)

---

## Common Scenarios

### Starting a New Project

```bash
# 1. Install and configure
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
/sdlc-core:setup-team

# 2. Optionally set up CI
/sdlc-core:setup-ci

# 3. Start your first feature
/sdlc-core:new-feature 1 initial-setup "Project Initial Setup"
```

### Adding a Knowledge Base

```bash
/plugin install sdlc-knowledge-base@ai-first-sdlc
/sdlc-knowledge-base:kb-init
/sdlc-knowledge-base:kb-query "What does research say about X?"
```

### Setting Up Containerised Workflows

```bash
/plugin install sdlc-workflows@ai-first-sdlc
/sdlc-workflows:workflows-setup
/sdlc-workflows:deploy-team dev-team
/sdlc-workflows:workflows-run sdlc-parallel-review
```

### Setting Up a Multi-Team Programme (Method 1)

For teams of 11–50 across 2–5 sub-teams that need formal phase gates (requirements → design → test → code) with mandatory cross-phase review:

```bash
# 1. Install and commission
/plugin install sdlc-programme@ai-first-sdlc
/sdlc-core:commission --option programme --level production
# (or: /sdlc-programme:commission-programme)

# 2. For each feature, walk the phases:
/sdlc-programme:phase-init requirements FEAT-123
# Edit the generated requirements-spec.md
/sdlc-programme:phase-gate requirements FEAT-123

/sdlc-programme:phase-init design FEAT-123
# Edit the generated design-spec.md
/sdlc-programme:phase-review design FEAT-123     # Mandatory cross-team review
/sdlc-programme:phase-gate design FEAT-123

/sdlc-programme:phase-init test FEAT-123
# Edit the generated test-spec.md
/sdlc-programme:phase-review test FEAT-123        # Mandatory
/sdlc-programme:phase-gate test FEAT-123

# 3. Code phase uses the standard sdlc-core flow:
/sdlc-core:new-feature 123 feature-name "Description"
# Implement against test-spec
/sdlc-core:pr

# 4. Export traceability for audit:
/sdlc-programme:traceability-export csv
/sdlc-programme:traceability-export markdown
```

See [`plugins/sdlc-programme/README.md`](../plugins/sdlc-programme/README.md) for phase contract details and [METHODS-GUIDE.md](METHODS-GUIDE.md) for when Method 1 is the right choice.

### Setting Up Regulated-Industry Traceability (Method 2)

For projects targeting DO-178C (avionics), IEC 62304 (medical devices), ISO 26262 (automotive), or FDA 21 CFR Part 820:

```bash
# 1. Install and commission
/plugin install sdlc-assured@ai-first-sdlc
/sdlc-core:commission --option assured --level production
/sdlc-assured:commission-assured
# This scaffolds programmes.yaml (DDD bounded contexts), visibility-rules.md, and base specification templates.

# 2. Edit programmes.yaml to declare your modules (bounded contexts) with parent + visibility rules.

# 3. For each requirement, mint a positional ID and link bidirectionally:
/sdlc-assured:req-add <module> <feature> "System SHALL authenticate users via OAuth 2.0"
# → mints e.g. P1.REQ-001
/sdlc-assured:req-link P1.REQ-001 design-spec.md "Section 3.2 OAuth flow"
/sdlc-assured:req-link P1.REQ-001 test-spec.md "Test 4.1.3 valid token exchange"

# 4. As you implement, annotate functions and rebuild the code index:
/sdlc-assured:code-annotate src/auth/login.py::authenticate_user
# → auto-generates "# implements: P1.REQ-001"
/sdlc-assured:kb-codeindex
# → parses all annotations into library/_code-index.md

# 5. Validate decomposition before commit:
/sdlc-assured:module-bound-check    # Visibility, scatter, anaemic-context checks

# 6. For IEC 62304 / FDA change-impact tracking:
/sdlc-assured:change-impact-annotate

# 7. Generate audit-ready artefacts:
/sdlc-assured:traceability-render
```

For what "audit-ready at the tooling layer" actually means in v0.2.0 (what's automated, what's manual evidence, what an auditor can regenerate, what's deferred to v0.3.0), see [`plugins/sdlc-assured/README.md`](../plugins/sdlc-assured/README.md).

For decision criteria between Method 1 and Method 2, see [METHODS-GUIDE.md](METHODS-GUIDE.md).

---

## Troubleshooting

### "Skill not found"

The plugin providing the skill is not installed. Check with:

```bash
/plugin list
```

Then install the missing plugin.

### Validation failures

Run validation with verbose output to see what failed:

```bash
/sdlc-core:validate --pre-push
```

Each check reports what passed, failed, and was skipped (with install instructions for missing tools).

### Plugin cache issues

```bash
rm -rf ~/.claude/plugins/cache/ai-first-sdlc/
```

Restart Claude Code, then reinstall plugins.

### `.claude/` write protection

Claude Code blocks writes to `.claude/` in project directories. This is a platform security feature. Plugin installation and project-scoped memory both use workarounds. See [issue #81](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/81).

### Pre-commit hooks failing

```bash
# Run hooks manually to see specific errors
pre-commit run --all-files

# Check what hooks are configured
cat .pre-commit-config.yaml
```

---

## Best Practices

1. **Always work in feature branches** — never commit to main
2. **Create proposals before implementation** — design first
3. **Validate continuously** — `--syntax` after writing, `--quick` before commits
4. **Use specialist agents** — they catch issues you might miss
5. **Complete retrospectives** — required before PR creation
6. **Run pre-push validation** — the full 10-check pipeline before PRs

---

## Further Reading

- [README.md](../README.md) — Project overview and setup
- [CONSTITUTION.md](../CONSTITUTION.md) — All rules (11 articles)
- [METHODS-GUIDE.md](METHODS-GUIDE.md) — Decision tree for the four SDLC methods (solo / single-team / programme / assured) — when to use each, comparison, trade-offs, migration notes
- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) — Command cheat sheet
- [PLUGIN-CONSUMER-GUIDE.md](PLUGIN-CONSUMER-GUIDE.md) — How the plugin ecosystem works
- [AGENT-INDEX.md](../AGENT-INDEX.md) — Full catalog of all agents

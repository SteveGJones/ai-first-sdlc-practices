# sdlc-core

Gateway plugin for the AI-First SDLC framework. Rules, validation, enforcement, and workflow skills that every project installs first.

This plugin provides the foundation: four enforcement agents that guard process compliance, code quality, requirements alignment, and runtime verification; eight skills covering the full development lifecycle from feature creation through PR submission; a curated technology registry for tooling discovery; and hooks that surface framework context at session start.

## Quick start

```bash
# Install the plugin
/plugin install sdlc-core@ai-first-sdlc

# Configure your team (recommends and installs team plugins)
/sdlc-core:setup-team

# Run your first validation
/sdlc-core:validate --syntax
```

After `setup-team`, the recommended next step is `/sdlc-core:validate --pre-push` on your first feature branch to see the full 10-check pipeline in action.

## What this plugin provides

### Agents (4)

| Agent | Purpose |
|---|---|
| `sdlc-enforcer` | SDLC compliance enforcement with progressive quality gates (Prototype/Production/Enterprise). Validates branch protection, documentation, technical debt, and workflow adherence. Combines firm enforcement with coaching. |
| `critical-goal-reviewer` | Post-implementation validation against original requirements. Systematic gap analysis, requirements traceability, risk assessment with RPN scoring, and structured review reports with APPROVE/REQUEST CHANGES verdicts. |
| `code-review-specialist` | Code quality and security review covering OWASP Top 10, language-specific patterns (Python/JS/Go/Java/Rust), performance anti-patterns, and automated tool integration. Structured PR reviews with severity classification. |
| `verification-enforcer` | Three-check verification gate: documentation-code fidelity, test existence and execution, and runtime smoke testing. Blocks progress until evidence is provided. The last gate before shipping. |

### Skills (8)

| Skill | Purpose |
|---|---|
| `/sdlc-core:validate` | Run the 10-check validation pipeline at three levels: `--syntax` (after edits), `--quick` (before commits), `--pre-push` (before PRs). Checks syntax, lint, format, technical debt, tests, imports, type safety, security, and smoke test. |
| `/sdlc-core:new-feature` | Create a feature proposal, retrospective, and branch in one step. Scaffolds all required artifacts from templates and runs syntax validation. |
| `/sdlc-core:commit` | Validated commit workflow. Runs `--quick` validation and tests before committing. Stops if checks fail. Uses conventional commit format. |
| `/sdlc-core:pr` | Full pre-push validation, artifact verification (proposal + retrospective exist), push, and PR creation via `gh`. Re-verifies all test counts cited in the PR body. |
| `/sdlc-core:release-plugin` | Package source files into plugin directories using `release-mapping.yaml`. Bumps version (patch/minor/major) in `plugin.json` and `marketplace.json`. |
| `/sdlc-core:rules` | Quick reference for AI-First SDLC compliance rules: zero technical debt policy, 10 mandatory logging points, and the specify-architect-implement-review workflow. Links to the full CONSTITUTION.md. |
| `/sdlc-core:setup-ci` | Generate a GitHub Actions workflow for SDLC validation. Auto-detects project language (Python, JavaScript, Go) and generates the matching CI pipeline. |
| `/sdlc-core:setup-team` | Interactive team configuration. Scans installed plugins, detects project type and language, discovers 1st-party tools via the technology registry, identifies coverage gaps, and recommends team plugins to install. |

## When to use this plugin

Always. This is the core plugin that every project installs. It provides the rules engine, the validation pipeline, and the enforcement agents that the rest of the plugin family depends on. Team plugins (`sdlc-team-common`, `sdlc-team-fullstack`, `sdlc-team-ai`, etc.) add domain specialists, but `sdlc-core` is the foundation they build on.

Install `sdlc-core` first, run `setup-team` to configure your formation, then install the team plugins it recommends.

## Validation pipeline

The `validate` skill runs up to 10 checks depending on the level:

| # | Check | `--syntax` | `--quick` | `--pre-push` |
|---|-------|:---:|:---:|:---:|
| 1 | Python AST syntax | x | x | x |
| 2 | Ruff syntax errors | x | x | x |
| 3 | Ruff full lint | | x | x |
| 4 | Ruff format check | | x | x |
| 5 | Technical debt scan | | x | x |
| 6 | Test execution (pytest) | | x | x |
| 7 | Import smoke test | | x | x |
| 8 | Type checking (mypy) | | | x |
| 9 | Security scan (bandit) | | | x |
| 10 | Application smoke test | | | x |

Language detection is automatic. Python is the primary implementation; JavaScript/TypeScript and Go follow the same structure with equivalent tools.

## Technology registry

The plugin ships a curated technology registry (`data/technology-registry/`) containing 32 YAML files plus an `_index.yaml` that maps package names, Docker images, and environment variables to technology keys. Covered technologies include databases (PostgreSQL, MongoDB, Redis, Elasticsearch), cloud providers (AWS, GCP, Azure), payment systems (Stripe), messaging (Kafka, RabbitMQ), and more.

Each registry file provides:
- **Section A**: Claude Code environment tools (MCP servers, plugins, GitHub Actions) with install instructions
- **Section B**: Project libraries with package manager commands
- **Section C**: Coverage gaps worth custom agents
- **our_agents**: Cross-references to framework agents relevant to that technology
- **trusted_sources**: Official documentation URLs for grounded recommendations

The registry is consumed by `/sdlc-core:setup-team` during technology discovery. Technologies in the registry get instant, offline recommendations. Technologies not in the registry fall back to web search.

## Hooks

The plugin registers two automated hooks via `hooks/hooks.json`:

- **SessionStart**: Runs `session-banner.sh` to display framework context (version, active branch, validation reminders) at the start of every Claude Code session. This ensures the agent is aware of the SDLC framework from the first prompt.
- **PostToolUse** (on Write/Edit): Runs `check-tmp-usage.py` after every file write or edit to catch uses of `/tmp/` (system temp) instead of the project-local `./tmp/` directory. This enforces CONSTITUTION.md Article 3 (Zero Technical Debt) for temporary file paths.

## Relationship to other plugins

| Plugin | Relationship |
|---|---|
| `sdlc-team-common` | Near-universal companion. Provides the research-and-agent-creation pipeline and cross-cutting architects. Recommended by `setup-team` for every project type. |
| `sdlc-team-*` | Domain specialist teams (fullstack, AI, cloud, security, PM, docs). Install alongside core based on project type. |
| `sdlc-lang-*` | Language-specific validation and patterns. Auto-detected and recommended by `setup-team`. |
| `sdlc-knowledge-base` | Research library for evidence-grounded decisions. Orthogonal to core; install when decisions need citations. |

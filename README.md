# AI-First SDLC Practices

A framework for integrating AI agents as primary developers while maintaining quality and process compliance. Provides specialist agents, validation tools, enforcement rules, and workflow skills for zero-technical-debt development.

## Setup

### Plugin Install (Recommended)

Install the plugin family from the Claude Code marketplace. This is the standard approach for using the framework in your projects.

**Step 1: Add the marketplace and install the core plugin**
```
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
```

**Step 2: Configure your team**
```
/sdlc-core:setup-team
```

This presents project types (Full-stack, AI/ML, Cloud, API, Security, Custom) and installs the matching team plugins. For example, a full-stack web app installs:

| Plugin | Description |
|--------|-------------|
| `sdlc-core` | Rules, validators, enforcement, workflows (always installed) |
| `sdlc-team-common` | Solution architect, research agent, performance engineer, database architect |
| `sdlc-team-fullstack` | Frontend, backend, API, DevOps architects |

**Step 3: Start working**
```
/sdlc-core:new-feature 1 my-feature "Description of the feature"
```

### Available Plugins

| Plugin | Description |
|--------|-------------|
| `sdlc-core` | Rules, validators, enforcement, workflows (always install) |
| `sdlc-team-common` | Cross-cutting architects, researchers, performance engineers |
| `sdlc-team-ai` | AI/ML specialists — architects, prompt engineers, RAG designers |
| `sdlc-team-fullstack` | Frontend, backend, API, DevOps architects |
| `sdlc-team-cloud` | Cloud, container, SRE specialists |
| `sdlc-team-security` | Security, compliance, privacy specialists |
| `sdlc-team-pm` | Agile coach, delivery manager, progress tracking |
| `sdlc-team-docs` | Technical writer, documentation architect |
| `sdlc-lang-python` | Python-specific validation, patterns, expert agent |
| `sdlc-lang-javascript` | JavaScript/TypeScript validation and patterns |

### Available Skills

| Skill | Description |
|-------|-------------|
| `/sdlc-core:validate` | Run validation pipeline (--syntax, --quick, --pre-push) |
| `/sdlc-core:new-feature` | Create feature proposal, retrospective, and branch |
| `/sdlc-core:commit` | Validated commit with test execution |
| `/sdlc-core:pr` | Full validation + PR creation |
| `/sdlc-core:setup-team` | Configure team formation for your project |
| `/sdlc-core:setup-ci` | Generate GitHub Actions workflow |
| `/sdlc-core:release-plugin` | Package source into plugins |

### Agent-Based Setup (Pre-release / Development)

For testing unreleased agents or contributing to the framework, install agents directly from the repository. This approach gives you access to agents before they're published as plugins.

```bash
# Download the setup orchestrator
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents/v3-setup-orchestrator.md > v3-setup-orchestrator.md
mkdir -p .claude/agents && mv v3-setup-orchestrator.md .claude/agents/

# Restart Claude Code, then:
# "Use the v3-setup-orchestrator agent to set up AI-First SDLC for my project"
```

The orchestrator interviews you about your project and downloads only the agents you need. Use this approach when:
- You want agents that haven't been released as plugins yet
- You're contributing to the framework and testing changes
- You need a custom agent selection not covered by the plugin team presets

### Script-Based Setup (Legacy)

The original Python script approach. Still functional but superseded by the plugin system.

```bash
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
python setup-smart.py "describe your project" --non-interactive
```

## How It Works

The framework enforces a specify-architect-implement-review workflow:

1. **Feature proposal** (`docs/feature-proposals/XX-name.md`) documents what and why
2. **Architecture** designed with specialist agents before coding
3. **Implementation** with continuous testing and validation
4. **Review** by code-review-specialist and verification-enforcer agents
5. **Ship** with full validation passing

### Rules

All rules are in [CONSTITUTION.md](CONSTITUTION.md) — 11 articles covering git workflow, documentation, architecture, code quality, validation, agent collaboration, logging, security, self-review, verification, and progressive levels (Prototype/Production/Enterprise).

### Validation

```bash
/sdlc-core:validate --syntax      # After writing code
/sdlc-core:validate --quick       # Before commits
/sdlc-core:validate --pre-push    # Before PRs
```

The validation pipeline runs up to 10 checks: syntax, lint, format, technical debt, tests, import check, type safety, security, and smoke test. Each check includes a preflight gate that reports missing tools with install instructions.

### Agents

The framework provides 50+ specialist agents across 10 categories. Key agents in `sdlc-core`:

| Agent | Role |
|-------|------|
| `sdlc-enforcer` | Process compliance and quality gates |
| `critical-goal-reviewer` | Requirements verification and gap analysis |
| `code-review-specialist` | Code quality, security (OWASP), patterns |
| `verification-enforcer` | Docs-code fidelity, test coverage, runtime proof |

## Documentation

| Document | Description |
|----------|-------------|
| [CONSTITUTION.md](CONSTITUTION.md) | All rules — single source of truth (11 articles) |
| [CLAUDE-CORE.md](CLAUDE-CORE.md) | Operational instructions, commands, context loading |
| [CLAUDE.md](CLAUDE.md) | Gateway file — concise entry point for Claude Code |
| [docs/HOWTO.md](docs/HOWTO.md) | Comprehensive usage guide |
| [docs/QUICK-REFERENCE.md](docs/QUICK-REFERENCE.md) | Command cheat sheet |

### Agent Development

| Document | Description |
|----------|-------------|
| [Agent Creation Guide](docs/AGENT-CREATION-GUIDE.md) | How to write effective agents |
| [Agent Format Spec](docs/AGENT-FORMAT-SPEC.md) | Technical specification |
| [AGENT-INDEX.md](AGENT-INDEX.md) | Full catalog of all agents |

## Integration Testing

The framework includes an automated integration test at `tests/integration/`. It uses Ralph to drive Claude through 10 phases — from blank repo to running app — producing a Build Journal Web App that documents its own construction. The build journal serves as both a demo and a framework quality report.

See [tests/integration/README.md](tests/integration/README.md) for how to run it.

## Known Limitations

1. **`.claude/` write protection**: Claude Code blocks writes to `.claude/` in project directories (security feature). Project-scoped plugin installation and project-scoped memory both require workarounds. See [#81](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/81).

2. **Slash commands in automated loops**: Skills like `/sdlc-core:new-feature` and `/sdlc-core:validate` require an interactive Claude Code session. They cannot be invoked from Ralph loops or CI scripts. The loop can read the skill's SKILL.md and execute the steps manually.

3. **Plugin cache**: Claude Code caches plugins globally at `~/.claude/plugins/cache/`. When testing new plugin versions, clear the cache first: `rm -rf ~/.claude/plugins/cache/ai-first-sdlc/`

## Zero Technical Debt Policy

The framework enforces architecture-first development:

1. No code without architecture — design documents required before implementation
2. No TODOs, FIXMEs, commented code, or `any` types
3. Type safety mandatory — strict typing in all languages
4. Tests mandatory — written alongside implementation, not after
5. Smoke test mandatory — the app must start and respond before committing
6. Automated enforcement via pre-commit hooks and CI/CD validation

See [CONSTITUTION.md](CONSTITUTION.md) Articles 4, 5, and 10 for the complete rules.

## Development

### Using the Framework (Your Project)

Install the plugins, run setup-team, and follow the workflow. The framework tools validate your code, the agents assist your design, and the skills enforce the process.

### Developing the Framework (This Repo)

This repo dogfoods its own practices. Key development conventions:

- Branch naming: `feature/`, `fix/`, `docs/`
- Feature proposals required before implementation
- Retrospective required before PR
- Plugin source lives in `skills/`, `agents/`, `tools/` — packaged to `plugins/` via `release-mapping.yaml`
- Run `/sdlc-core:release-plugin` to package source into plugins

### Current Version: 1.8.0

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

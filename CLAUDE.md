# CLAUDE.md

AI-First SDLC Practices framework (v1.8.0). Rules: **CONSTITUTION.md**. Full instructions: **CLAUDE-CORE.md**.

## Essential Workflow

```
specify → architect → implement → review
```

1. Feature proposal (`docs/feature-proposals/XX-name.md`) + retrospective (`retrospectives/XX-name.md`)
2. Feature branch (`feature/name`) — never commit to main directly
3. Implement with zero technical debt, validate continuously
4. PR with complete retrospective — CI must pass

## Validation (run after every change)

```bash
python tools/validation/local-validation.py --syntax       # After writing code
python tools/validation/local-validation.py --quick        # Before commits
python tools/validation/local-validation.py --pre-push     # Before PR
```

Pre-push runs 8 checks: syntax, pre-commit, technical debt, architecture, type safety, security, logging compliance, static analysis.

## Key Validators

```bash
python tools/validation/check-technical-debt.py --threshold 0
python tools/validation/check-logging-compliance.py . --threshold 0
python tools/validation/validate-architecture.py --strict
python tools/validation/check-broken-references.py
```

## Code Quality

No TODOs, no `any` types, no commented-out code. Use `./tmp/` not `/tmp/`. 10 mandatory logging points for application code (see CONSTITUTION.md Article 7). Never log secrets or PII.

## Context Loading

Load additional context per task — see table in CLAUDE-CORE.md. Key modules:
- CONSTITUTION.md — all rules (10 articles, progressive levels)
- CLAUDE-CONTEXT-logging.md — logging standards
- CLAUDE-CONTEXT-architecture.md — architecture docs
- AGENT-INDEX.md — 63+ specialist agents

## Plugin Installation (Recommended)

Install the SDLC plugin family for skills, agents, and automated enforcement:

```bash
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
```

Then configure your team: `/sdlc-core:setup-team`

### Plugin Family

| Plugin | Description |
|--------|-------------|
| `sdlc-core` | Rules, validators, enforcement, workflows (always install) |
| `sdlc-team-common` | Cross-cutting architects, researchers, performance engineers |
| `sdlc-team-ai` | AI/ML specialists (14 agents) |
| `sdlc-team-fullstack` | Frontend, backend, API, DevOps (10 agents) |
| `sdlc-team-cloud` | Cloud, containers, SRE (3 agents) |
| `sdlc-team-security` | Security, compliance, privacy (5 agents) |
| `sdlc-team-pm` | Agile coach, delivery manager, tracking (5 agents) |
| `sdlc-team-docs` | Technical writer, documentation architect |
| `sdlc-lang-*` | Language-specific validation and patterns (Python, JS, Go, Java, Rust) |

### Available Skills

| Skill | Description |
|-------|-------------|
| `/sdlc-core:validate` | Run 8-check validation pipeline |
| `/sdlc-core:new-feature` | Create feature proposal, retrospective, and branch |
| `/sdlc-core:commit` | Validated commit with quick checks |
| `/sdlc-core:pr` | Full validation + PR creation |
| `/sdlc-core:setup-team` | Configure team formation |
| `/sdlc-core:release-plugin` | Package source into plugins |

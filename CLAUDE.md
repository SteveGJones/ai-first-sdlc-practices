# CLAUDE.md

AI-First SDLC Practices framework (v1.8.0). Rules: **CONSTITUTION.md**. Full instructions: **CLAUDE-CORE.md**.

## Active Work

- **EPIC #97** — Multi-Option Commissioned SDLC. Branch `feature/sdlc-commissioning` has the feature proposal for sub-feature #98 (commissioning infrastructure). Implementation pending. See `docs/feature-proposals/98-sdlc-commissioning-infrastructure.md`.
- **EPIC #142** — Curated technology registry + plugin recommendation improvements. Sub-features 0-2 merged (#151, #143, #144 — pre/post check, kb recommendation, language detection). Sub-features 3-8 pending (registry schema, population, wiring, maintenance). See issue #142 for the full inventory.
- **EPIC #96** — Containerized Claude Code workers. Design phase, deferred.
- **EPIC #105** — sdlc-knowledge-base plugin. **Merged.** Plugin is live and installable. Sub-feature 13 (#118 codebase-index) is future work.

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
python tools/validation/local-validation.py --syntax       # After writing code (this repo)
python tools/validation/local-validation.py --quick        # Before commits (this repo)
python tools/validation/local-validation.py --pre-push     # Before PR (this repo)
```

For plugin consumers (projects using the plugins, not this repo):
```
/sdlc-core:validate --syntax       # After writing code
/sdlc-core:validate --quick        # Before commits
/sdlc-core:validate --pre-push     # Before PR
```

Pre-push runs 10 checks: syntax, ruff lint, ruff format, technical debt, tests, import check, type safety, security, smoke test.

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
- CONSTITUTION.md — all rules (11 articles, progressive levels)
- CLAUDE-CONTEXT-logging.md — logging standards
- CLAUDE-CONTEXT-architecture.md — architecture docs
- AGENT-INDEX.md — 50+ specialist agents across 10 plugins

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
| `sdlc-knowledge-base` | Filesystem-based project knowledge base — librarian agent, hash-tracked indexes, ingest/query/lint operations. Orthogonal to SDLC option choice. |
| `sdlc-lang-*` | Language-specific validation and patterns (Python, JS, Go, Java, Rust) |

### Available Skills

| Skill | Description |
|-------|-------------|
| `/sdlc-core:validate` | Run 10-check validation pipeline (syntax/lint/tests/security/smoke) |
| `/sdlc-core:new-feature` | Create feature proposal, retrospective, and branch |
| `/sdlc-core:commit` | Validated commit with test execution |
| `/sdlc-core:pr` | Full validation + PR creation |
| `/sdlc-core:setup-team` | Configure team formation |
| `/sdlc-core:setup-ci` | Generate GitHub Actions workflow |
| `/sdlc-core:release-plugin` | Package source into plugins |
| `/sdlc-knowledge-base:kb-*` | Knowledge base operations (init, ingest, query, lint, rebuild-indexes, validate-citations, promote-answer, staleness-check) — installed by `sdlc-knowledge-base` plugin |

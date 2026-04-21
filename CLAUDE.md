# CLAUDE.md

AI-First SDLC Practices framework (v1.8.0). Rules: **CONSTITUTION.md**. Full instructions: **CLAUDE-CORE.md**.

## Active Work

- **EPIC #97** — Multi-Option Commissioned SDLC. Branch `feature/sdlc-commissioning` has the feature proposal for sub-feature #98 (commissioning infrastructure). Implementation pending. See `docs/feature-proposals/98-sdlc-commissioning-infrastructure.md`.
- **EPIC #142** — Curated technology registry + plugin recommendation improvements. Sub-features 0-2 merged (#151, #143, #144 — pre/post check, kb recommendation, language detection). Sub-features 3-8 pending (registry schema, population, wiring, maintenance). See issue #142 for the full inventory.
- **EPIC #96** — Containerised Claude Code workers. **Merged.** Plugin `sdlc-workflows` is live and installable. CI/CD automation deferred to separate issue.
- **EPIC #105** — sdlc-knowledge-base plugin. **Merged.** Plugin is live and installable. Sub-feature 13 (#118 codebase-index) is future work.

## Working in this repo — dogfood the skills we ship

This repo *is* the plugin family. When working here, treat the skills
and agents we ship as tools in your toolbox, not output artefacts:

- **Before scope decisions** → invoke `superpowers:brainstorming`.
  Do this especially when a task description might be wrong ("SSE
  live streaming in workflows-run" turned out to be mis-scoped on
  2026-04-19 because the CLI already streams to stderr).
- **Before multi-file implementation** → invoke
  `superpowers:writing-plans-and-specs` or the `Plan` subagent.
- **When writing new code with tests** → invoke
  `superpowers:test-driven-development`. Tests first, not after.
- **After any logical chunk lands** → invoke
  `superpowers:code-reviewer` or `sdlc-core:code-review-specialist`
  on the commit before moving on.
- **Independent subtasks (different files, different subsystems)** →
  dispatch them in parallel via `superpowers:dispatching-parallel-agents`.
  Don't serialise work that shares nothing.
- **Design-level decisions** → dispatch to specialist agents:
  - `sdlc-team-common:solution-architect` for architecture choices
  - `sdlc-team-fullstack:backend-architect` for data-layer decisions
  - `sdlc-team-common:observability-specialist` for monitoring design
  - `sdlc-team-security:security-architect` for auth/secrets/hardening
- **Dogfood the shipping skills** — if you just wrote
  `/sdlc-workflows:workflows-status`, actually invoke it on this
  session's runs before claiming it works. Same for every skill in
  the plugin family.

If this list feels long, that's the point: these tools exist so we
don't keep making the same mistakes, and we only know they work if
we use them ourselves.

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
- AGENT-INDEX.md — 56 specialist agents across 12 plugins

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
| `sdlc-lang-python` | Python language expert agent |
| `sdlc-lang-javascript` | JavaScript/TypeScript language expert agent |
| `sdlc-workflows` | Containerised delegation — Archon-orchestrated DAG workflows in isolated Docker containers (6 skills) |

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
| `/sdlc-core:rules` | AI-First SDLC compliance rules and standards |
| `/sdlc-knowledge-base:kb-*` | Knowledge base operations (init, ingest, query, lint, rebuild-indexes, validate-citations, promote-answer, staleness-check) — installed by `sdlc-knowledge-base` plugin |
| `/sdlc-workflows:workflows-setup` | First-time setup: install Archon, build sdlc-worker base + full Docker images, scaffold `.archon/` dirs |
| `/sdlc-workflows:deploy-team` | Build a team image from a manifest YAML |
| `/sdlc-workflows:author-workflow` | Interactive workflow author — generates workflow YAML + command briefs |
| `/sdlc-workflows:workflows-run` | Execute a named SDLC workflow via Archon |
| `/sdlc-workflows:workflows-status` | Check running/recent workflow status |
| `/sdlc-workflows:manage-teams` | Guided coaching for team lifecycle (create, update, delete, review — fleet and single-team views) |

# CLAUDE.md

AI-First SDLC Practices framework (v1.8.0). Rules: **CONSTITUTION.md**. Full instructions: **CLAUDE-CORE.md**.

## Active Work

- **EPIC #188** — sdlc-assured v0.2.0 audit-readiness + carry-forward closure. **Merged** (PR #189, merge commit `1356ff3`, 2026-05-02). 7 phases A-G shipped on `feature/sdlc-assured-v020`. Closes F-001/F-007/F-008/F-009/F-010 + carry-forward items (F1/F4/D1/D2/D3/E1/E2/E3). All 6 Phase G hard gates PASS: granularity_match noise 0%, RTM gap 4.55% (was 68.18%), gap-typing 30/30, FAC FPR 0%, visibility runs cleanly, 594/594 tests. Architect review: AGREE-WITH-CONCERNS (no blockers; 4 v0.3.0 carry-forward items). **`sdlc-assured` is now audit-ready at the tooling layer** — corpus-policy formalisation (MANUAL_EVIDENCE_REQUIRED) and CI integration of REQ-quality linter are v0.3.0 work. See `retrospectives/188-v020-assured-improvements.md`.
- **EPIC #178** — Joint Programme + Assured bundle delivery. **Merged** (PR #187, merge commit `e05e446`, 2026-05-01). 6 phases A-F plus G closure shipped on `feature/sdlc-programme-assured-bundles`. `sdlc-programme` v0.1.0 (Method 1) and `sdlc-assured` v0.1.0 (Method 2) are live and installable. Marketplace 12 → 14 plugins. Phase F recursive dogfood produced 10 findings (5 IMPORTANT + 5 MINOR) — all closed in EPIC #188.
- **EPIC #164** — Cross-library query support for sdlc-knowledge-base. **Merged** (PR #177).
- **EPIC #97** — Multi-Option Commissioned SDLC. Phase C (commissioning infrastructure #98) shipped as part of #178. Sub-features for Single-team / Solo bundles still pending.
- **EPIC #142** — Curated technology registry. **Merged** (sub-features 0-8 all complete via PRs #152 + #153).
- **EPIC #96** — Containerised Claude Code workers. **Merged.**
- **EPIC #105** — sdlc-knowledge-base plugin. **Merged.** Sub-feature 13 (#118 codebase-index) is future work.
- **KB feedback issues** — From Amkor engagement feedback (2026-04-23): #161 (batch ingestion), #162 (kb-stats), #163 (confidence metadata), #165 (lint auto-fix). Plus #166 (named plugin bundles for setup-team on sdlc-core).

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
- AGENT-INDEX.md — 56 specialist agents across 14 plugins (sdlc-programme + sdlc-assured added in EPIC #178; both ship 0 agents in v0.1.0 — they are skill+validator bundles)

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
| `sdlc-programme` | Method 1 SDLC bundle for multi-team programme work — formal waterfall phase gates (requirements/design/test/code), 4 phase-gate validators, mandatory cross-phase review (5 skills, EPIC #178 v0.1.0) |
| `sdlc-assured` | Method 2 SDLC bundle for regulated-industry work — positional namespace IDs, bidirectional traceability, DDD decomposition with visibility rules, KB-for-code annotations, standard-specific exports (DO-178C / IEC 62304 / ISO 26262 / FDA DHF). 8 skills. **v0.2.0 audit-ready at tooling layer** (EPIC #188) — typed evidence statuses, multi-format evidence model (Python/markdown/YAML/satisfies-by-existence), platform-neutral dependency extractor, indirect DES-mediated coverage, REQ-quality lint candidate. |

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

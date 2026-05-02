<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC - Quick Reference Card](#ai-first-sdlc---quick-reference-card)
  - [Essential Skills](#essential-skills)
    - [Starting Work](#starting-work)
    - [During Development](#during-development)
    - [Shipping](#shipping)
  - [All Skills by Plugin](#all-skills-by-plugin)
    - [sdlc-core (always installed)](#sdlc-core-always-installed)
    - [sdlc-knowledge-base](#sdlc-knowledge-base)
    - [sdlc-workflows](#sdlc-workflows)
    - [sdlc-programme (Method 1 — multi-team phase gates)](#sdlc-programme-method-1--multi-team-phase-gates)
    - [sdlc-assured (Method 2 — regulated-industry traceability, v0.2.0 audit-ready)](#sdlc-assured-method-2--regulated-industry-traceability-v020-audit-ready)
  - [Validation Pipeline (10 Checks)](#validation-pipeline-10-checks)
  - [Direct Validators (Framework Development)](#direct-validators-framework-development)
  - [Branch Naming](#branch-naming)
  - [Common Workflows](#common-workflows)
    - [New Project Setup](#new-project-setup)
    - [Add Knowledge Base](#add-knowledge-base)
    - [Add Containerised Workflows](#add-containerised-workflows)
    - [Install All Plugins](#install-all-plugins)
  - [Things to NEVER Do](#things-to-never-do)
  - [Quick Fixes](#quick-fixes)
  - [Further Reading](#further-reading)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC - Quick Reference Card

## Essential Skills

### Starting Work
```bash
/sdlc-core:setup-team                                  # First-time team setup
/sdlc-core:new-feature <num> <name> "<title>"          # Create feature + branch
```

### During Development
```bash
/sdlc-core:validate --syntax                           # After writing code
/sdlc-core:validate --quick                            # Before commits
```

### Shipping
```bash
/sdlc-core:commit                                      # Validated commit
/sdlc-core:validate --pre-push                         # Full 10-check validation
/sdlc-core:pr                                          # Create PR
```

---

## All Skills by Plugin

### sdlc-core (always installed)

| Skill | Purpose |
|-------|---------|
| `/sdlc-core:validate` | Run validation (`--syntax`, `--quick`, `--pre-push`) |
| `/sdlc-core:new-feature` | Create feature proposal, retrospective, branch |
| `/sdlc-core:commit` | Validated commit with test execution |
| `/sdlc-core:pr` | Full validation + PR creation |
| `/sdlc-core:setup-team` | Configure team formation; asks the four-option SDLC method question |
| `/sdlc-core:commission` | Commission a project to one of the four SDLC options (solo / single-team / programme / assured) |
| `/sdlc-core:setup-ci` | Generate GitHub Actions workflow |
| `/sdlc-core:release-plugin` | Package source into plugins |
| `/sdlc-core:rules` | SDLC compliance rules and standards |

### sdlc-knowledge-base

| Skill | Purpose |
|-------|---------|
| `/sdlc-knowledge-base:kb-init` | Initialise knowledge base |
| `/sdlc-knowledge-base:kb-ingest <source>` | Integrate new source |
| `/sdlc-knowledge-base:kb-query "<question>"` | Query library for evidence |
| `/sdlc-knowledge-base:kb-lint` | Six-check health report |
| `/sdlc-knowledge-base:kb-rebuild-indexes` | Rebuild shelf-index |
| `/sdlc-knowledge-base:kb-validate-citations` | Check citation accuracy |
| `/sdlc-knowledge-base:kb-promote-answer-to-library` | File query result as library page |
| `/sdlc-knowledge-base:kb-staleness-check` | Check for shelf-index drift |

### sdlc-workflows

| Skill | Purpose |
|-------|---------|
| `/sdlc-workflows:workflows-setup` | Install Archon, build images |
| `/sdlc-workflows:workflows-run <name>` | Execute workflow |
| `/sdlc-workflows:workflows-status` | Show running/recent workflows |
| `/sdlc-workflows:author-workflow` | Recommend or create workflows |
| `/sdlc-workflows:deploy-team <name>` | Build team image from manifest |
| `/sdlc-workflows:manage-teams` | Team lifecycle coaching |

### sdlc-programme (Method 1 — multi-team phase gates)

Install with `/plugin install sdlc-programme@ai-first-sdlc`, then commission with `/sdlc-core:commission --option programme --level production` (or `/sdlc-programme:commission-programme`).

| Skill | Purpose |
|-------|---------|
| `/sdlc-programme:commission-programme` | Install Method 1 bundle and scaffold phase templates (delegates to `/sdlc-core:commission`) |
| `/sdlc-programme:phase-init <phase> <id>` | Initialise requirements / design / test phase artefact |
| `/sdlc-programme:phase-gate <phase> <id>` | Validate phase artefact and gate entry to next phase |
| `/sdlc-programme:phase-review <phase> <id>` | Mandatory cross-phase review (design + test phases) |
| `/sdlc-programme:traceability-export <format>` | Export cross-phase traceability (csv / markdown) for audit |

### sdlc-assured (Method 2 — regulated-industry traceability, v0.2.0 audit-ready)

Install with `/plugin install sdlc-assured@ai-first-sdlc`, then commission with `/sdlc-core:commission --option assured --level production` (or `/sdlc-assured:commission-assured`).

| Skill | Purpose |
|-------|---------|
| `/sdlc-assured:commission-assured` | Install Method 2 bundle and scaffold programmes.yaml + visibility-rules.md (delegates to `/sdlc-core:commission`) |
| `/sdlc-assured:req-add <module> <feature>` | Mint positional-namespace REQ ID with module assignment |
| `/sdlc-assured:req-link <req-id> <artefact>` | Add satisfies link (bidirectional traceability) |
| `/sdlc-assured:code-annotate <function>` | Generate `# implements: <REQ-ID>` boilerplate annotation |
| `/sdlc-assured:module-bound-check` | Run 5 decomposition validators (visibility, anaemia, scatter) |
| `/sdlc-assured:kb-codeindex` | Parse `# implements:` annotations into `library/_code-index.md` |
| `/sdlc-assured:change-impact-annotate` | Guide change-impact declaration (IEC 62304 / FDA tracking) |
| `/sdlc-assured:traceability-render` | Generate module-scoped audit-ready traceability document |

---

## Validation Pipeline (10 Checks)

```bash
/sdlc-core:validate --pre-push    # Runs all 10
```

| # | Check | What it validates |
|---|-------|-------------------|
| 1 | Python AST syntax | Parse all .py files |
| 2 | Ruff syntax errors | Fast syntax-level lint |
| 3 | Ruff full lint | Complete ruff linting |
| 4 | Ruff format check | Formatting compliance |
| 5 | Technical debt scan | No TODOs, FIXMEs, commented code, `any` types |
| 6 | Test execution | pytest |
| 7 | Import smoke test | No missing imports |
| 8 | Type checking | mypy strict typing |
| 9 | Security scan | bandit vulnerability detection |
| 10 | Smoke test | App starts and responds |

For framework development (this repo), use the direct scripts:
```bash
python tools/validation/local-validation.py --syntax      # After writing code
python tools/validation/local-validation.py --quick        # Before commits
python tools/validation/local-validation.py --pre-push     # Before PR
```

---

## Direct Validators (Framework Development)

```bash
python tools/validation/check-technical-debt.py --threshold 0
python tools/validation/check-logging-compliance.py . --threshold 0
python tools/validation/validate-architecture.py --strict
python tools/validation/check-broken-references.py
python tools/validation/check-plugin-packaging.py
```

---

## Branch Naming

```
feature/<name>     # New features
fix/<name>         # Bug fixes
docs/<name>        # Documentation changes
```

---

## Common Workflows

### New Project Setup
```bash
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
/sdlc-core:setup-team
/sdlc-core:setup-ci
/sdlc-core:new-feature 1 initial-setup "Project Setup"
```

### Add Knowledge Base
```bash
/plugin install sdlc-knowledge-base@ai-first-sdlc
/sdlc-knowledge-base:kb-init
```

### Add Containerised Workflows
```bash
/plugin install sdlc-workflows@ai-first-sdlc
/sdlc-workflows:workflows-setup
```

### Install All Plugins
```bash
/plugin install sdlc-core@ai-first-sdlc
/plugin install sdlc-team-common@ai-first-sdlc
/plugin install sdlc-team-fullstack@ai-first-sdlc
/plugin install sdlc-team-ai@ai-first-sdlc
/plugin install sdlc-team-cloud@ai-first-sdlc
/plugin install sdlc-team-security@ai-first-sdlc
/plugin install sdlc-team-pm@ai-first-sdlc
/plugin install sdlc-team-docs@ai-first-sdlc
/plugin install sdlc-lang-python@ai-first-sdlc
/plugin install sdlc-lang-javascript@ai-first-sdlc
/plugin install sdlc-knowledge-base@ai-first-sdlc
/plugin install sdlc-workflows@ai-first-sdlc
```

---

## Things to NEVER Do

1. Push to main directly
2. Skip feature proposals
3. Leave TODOs, FIXMEs, or commented-out code
4. Use `any` types
5. Ship without running `--pre-push` validation
6. Log secrets or PII

---

## Quick Fixes

**Plugin not found?**
```bash
/plugin list                                    # Check installed plugins
/plugin install <plugin>@ai-first-sdlc         # Install missing plugin
```

**Plugin cache stale?**
```bash
rm -rf ~/.claude/plugins/cache/ai-first-sdlc/  # Clear cache
```

**On wrong branch?**
```bash
git stash && git checkout -b feature/correct-name && git stash pop
```

---

## Further Reading

- [README.md](../README.md) — Project overview
- [HOWTO.md](HOWTO.md) — Comprehensive usage guide
- [METHODS-GUIDE.md](METHODS-GUIDE.md) — SDLC method decision tree (solo / single-team / programme / assured)
- [PLUGIN-CONSUMER-GUIDE.md](PLUGIN-CONSUMER-GUIDE.md) — How the plugin ecosystem works
- [CONSTITUTION.md](../CONSTITUTION.md) — All rules (11 articles)
- [AGENT-INDEX.md](../AGENT-INDEX.md) — Full agent catalog

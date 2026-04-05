# AI-First SDLC Plugin Migration — Design Spec

**Date**: 2026-04-03
**Status**: Draft
**Feature**: #70 (Phase 1), #71-73 (subsequent phases)
**Branch**: `feature/plugin-migration`

## Problem

The AI-First SDLC framework (v1.8.0) contains 63 agents, 18 validators, and 42 automation tools distributed by cloning a repo and reading documentation. This approach requires manual setup (git hooks, context loading, agent discovery) and has no versioning, team distribution, or namespace isolation.

Claude Code now supports plugins — self-contained, versioned, distributable packages of skills, agents, hooks, and tools. The framework should be packaged as a plugin family to enable one-command team onboarding, automatic updates, and orchestrated team assembly.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Plugin location | Same repo (`plugins/` directory) | Plugin is tightly coupled to framework source; avoids sync overhead |
| Plugin model | Plugin family (core + team + lang) | Different projects need different agent teams; lean installs |
| Team assembly | Orchestrated via `/sdlc:setup-team` skill | Mirrors existing v3-orchestrator; native to plugin system |
| Source of truth | `tools/`, `agents/`, `skills/` directories | Plugin is a release artifact built from source, not the source itself |
| Release model | Beta (main branch) + Stable (tagged releases) | SDLC discipline: develop, test, release |

## Architecture

### Plugin Family

```
sdlc-core              — Rules, validators, enforcement, base workflows (always installed)
sdlc-team-ai           — AI architects, prompt engineers, RAG designers
sdlc-team-fullstack    — Frontend, backend, API, DevOps architects
sdlc-team-cloud        — Cloud, container, SRE specialists
sdlc-team-security     — Security, compliance, privacy specialists
sdlc-lang-python       — Python-specific validation and patterns
sdlc-lang-javascript   — JS/TS-specific validation and patterns
sdlc-lang-go           — Go-specific validation and patterns
```

### Source-to-Release Pipeline

```
Source (develop here)              Release Mapping              Plugin (release artifact)
─────────────────────              ───────────────              ────────────────────────
agents/*.md                  ─┐
tools/validation/*.py         ├─→  release-mapping.yaml  ─→  plugins/sdlc-core/
skills/*/SKILL.md             │       (defines what           plugins/sdlc-team-ai/
CONSTITUTION.md              ─┘        goes where)            plugins/sdlc-team-*/
```

- Develop in `tools/`, `agents/`, `skills/` as normal
- Run `/sdlc:release-plugin` to package source into plugin directories
- Tag for stable release, or point beta users at main branch

### Repository Structure

```
ai-first-sdlc-practices/
├── plugins/
│   ├── .claude-plugin/
│   │   └── marketplace.json              # Family marketplace
│   ├── sdlc-core/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json               # name, version, description, userConfig
│   │   ├── skills/
│   │   │   ├── validate/SKILL.md         # 8-check validation pipeline
│   │   │   ├── new-feature/
│   │   │   │   ├── SKILL.md              # Feature workflow automation
│   │   │   │   └── templates/
│   │   │   │       ├── proposal.md       # Feature proposal template
│   │   │   │       └── retrospective.md  # Retrospective template
│   │   │   ├── commit/SKILL.md           # Validated commit workflow
│   │   │   ├── pr/SKILL.md               # PR creation workflow
│   │   │   ├── rules/
│   │   │   │   ├── SKILL.md              # Auto-loaded compliance rules
│   │   │   │   └── constitution.md       # Full rules reference
│   │   │   ├── setup-team/SKILL.md       # Team plugin orchestrator
│   │   │   └── release-plugin/SKILL.md   # Build & version plugins
│   │   ├── agents/
│   │   │   ├── sdlc-enforcer.md
│   │   │   ├── critical-goal-reviewer.md
│   │   │   └── code-review-specialist.md
│   │   ├── hooks/
│   │   │   └── hooks.json                # SessionStart, PostToolUse
│   │   └── scripts/
│   │       ├── check-technical-debt.py
│   │       ├── check-logging-compliance.py
│   │       ├── validate-architecture.py
│   │       ├── check-broken-references.py
│   │       ├── check-tmp-usage.py
│   │       └── local-validation.py
│   ├── sdlc-team-ai/                     # Stub in Phase 1
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   ├── sdlc-team-fullstack/              # Stub in Phase 1
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   ├── sdlc-team-cloud/                  # Stub in Phase 1
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   ├── sdlc-team-security/               # Stub in Phase 1
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   ├── sdlc-lang-python/                 # Stub in Phase 3
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   └── sdlc-lang-javascript/             # Stub in Phase 3
│       └── .claude-plugin/
│           └── plugin.json
├── skills/                                # NEW: skill source directory
│   ├── validate/SKILL.md
│   ├── new-feature/
│   │   ├── SKILL.md
│   │   └── templates/
│   ├── commit/SKILL.md
│   ├── pr/SKILL.md
│   ├── rules/
│   │   ├── SKILL.md
│   │   └── constitution.md
│   ├── setup-team/SKILL.md
│   └── release-plugin/SKILL.md
├── release-mapping.yaml                   # NEW: source-to-plugin mapping
├── agents/                                # Existing (unchanged, remains source)
├── tools/                                 # Existing (unchanged, remains source)
├── CLAUDE.md                              # Stays — project gateway
├── CONSTITUTION.md                        # Stays — project rules
└── CLAUDE-CORE.md                         # Stays — operational instructions
```

## Phase 1: Foundation (Feature #70)

### Deliverables

1. **`release-mapping.yaml`** — Mapping file defining source → plugin assignments
2. **Marketplace** — `plugins/.claude-plugin/marketplace.json` listing all plugins
3. **`sdlc-core` plugin** — Full plugin with skills, agents, hooks, scripts
4. **Stub team plugins** — `plugin.json` only for 4 team plugins + 2 language plugins
5. **`skills/` source directory** — 7 skill source files (validate, new-feature, commit, pr, rules, setup-team, release-plugin)
6. **Release skill** — `/sdlc:release-plugin` that packages from source into plugins
7. **Documentation** — Updated CLAUDE.md referencing plugin installation

### Skill Specifications

#### `/sdlc:validate`
- **Type**: Manual (`disable-model-invocation: true`)
- **Arguments**: Optional `--syntax`, `--quick`, `--pre-push` (default: `--pre-push`)
- **Behavior**: Runs `local-validation.py` with specified flag, reports results
- **Wraps**: `tools/validation/local-validation.py`

#### `/sdlc:new-feature`
- **Type**: Manual (`disable-model-invocation: true`)
- **Arguments**: `<number> <name>` (e.g., `70 plugin-migration`)
- **Behavior**:
  1. Creates `docs/feature-proposals/XX-name.md` from template
  2. Creates `retrospectives/XX-name.md` from template
  3. Creates branch `feature/name`
  4. Runs syntax validation
- **Templates**: Bundled in `skills/new-feature/templates/`

#### `/sdlc:commit`
- **Type**: Manual (`disable-model-invocation: true`)
- **Behavior**:
  1. Runs `local-validation.py --quick`
  2. If clean: stages changes, creates commit with proper format
  3. If failures: reports issues, does not commit

#### `/sdlc:pr`
- **Type**: Manual (`disable-model-invocation: true`)
- **Behavior**:
  1. Runs `local-validation.py --pre-push`
  2. If clean: pushes branch, creates PR with template
  3. Verifies feature proposal and retrospective exist
  4. If failures: reports issues, does not push

#### `/sdlc:rules`
- **Type**: Auto (Claude loads when making compliance decisions)
- **Content**: Condensed CONSTITUTION.md — the 10 articles, progressive levels, mandatory logging points
- **No side effects**: Pure reference material

#### `/sdlc:setup-team`
- **Type**: Manual (`disable-model-invocation: true`)
- **Behavior**:
  1. Asks project type (full-stack, AI/ML, cloud, API, mobile, custom)
  2. Recommends team + language plugins
  3. Installs selected plugins
  4. Writes `.claude/team-config.json` recording selection
- **Phase 1**: Installs stub plugins, records config. Stubs have metadata but no agents yet.

#### `/sdlc:release-plugin`
- **Type**: Manual (`disable-model-invocation: true`)
- **Arguments**: Optional version bump type (`patch`, `minor`, `major`)
- **Behavior**:
  1. Reads `release-mapping.yaml`
  2. Copies source files into plugin directories per mapping
  3. Bumps version in `plugin.json` files
  4. Validates plugin structure
  5. Reports what changed

### Agent Specifications

Three "gateway" agents ship with core:

#### `sdlc-enforcer`
- **Source**: `agents/sdlc-enforcer.md`
- **Purpose**: Comprehensive SDLC compliance checking
- **Model**: Default (inherits session)

#### `critical-goal-reviewer`
- **Source**: `agents/critical-goal-reviewer.md`
- **Purpose**: Requirements verification and gap analysis
- **Model**: Default

#### `code-review-specialist`
- **Source**: `agents/code-review-specialist.md`
- **Purpose**: Code quality, security, patterns review
- **Model**: Default

### Hook Specifications

`plugins/sdlc-core/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cat ${CLAUDE_PLUGIN_ROOT}/scripts/session-banner.sh | bash"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/check-tmp-usage.py"
          }
        ]
      }
    ]
  }
}
```

**SessionStart banner** displays:
- Installed SDLC plugins and versions
- Active team formation (from `.claude/team-config.json`)
- Suggestion to run `/sdlc:setup-team` if no team configured

### Marketplace Specification

`plugins/.claude-plugin/marketplace.json`:

```json
{
  "name": "ai-first-sdlc",
  "owner": {
    "name": "SteveGJones",
    "email": ""
  },
  "metadata": {
    "description": "AI-First SDLC Practices — plugin family for zero-debt development",
    "version": "0.1.0"
  },
  "plugins": [
    {
      "name": "sdlc-core",
      "source": "./sdlc-core",
      "description": "Core SDLC rules, validators, enforcement, and workflows",
      "version": "0.1.0"
    },
    {
      "name": "sdlc-team-ai",
      "source": "./sdlc-team-ai",
      "description": "AI/ML specialist agents — architects, prompt engineers, RAG designers",
      "version": "0.1.0-stub"
    },
    {
      "name": "sdlc-team-fullstack",
      "source": "./sdlc-team-fullstack",
      "description": "Full-stack agents — frontend, backend, API, DevOps architects",
      "version": "0.1.0-stub"
    },
    {
      "name": "sdlc-team-cloud",
      "source": "./sdlc-team-cloud",
      "description": "Cloud infrastructure agents — cloud, container, SRE specialists",
      "version": "0.1.0-stub"
    },
    {
      "name": "sdlc-team-security",
      "source": "./sdlc-team-security",
      "description": "Security agents — security, compliance, privacy specialists",
      "version": "0.1.0-stub"
    },
    {
      "name": "sdlc-lang-python",
      "source": "./sdlc-lang-python",
      "description": "Python-specific validation, patterns, and expert agents",
      "version": "0.1.0-stub"
    },
    {
      "name": "sdlc-lang-javascript",
      "source": "./sdlc-lang-javascript",
      "description": "JavaScript/TypeScript-specific validation and patterns",
      "version": "0.1.0-stub"
    }
  ]
}
```

### Plugin Manifest (`sdlc-core/plugin.json`)

```json
{
  "name": "sdlc-core",
  "version": "0.1.0",
  "description": "AI-First SDLC — zero-debt development with validators, enforcement, and workflows",
  "author": {
    "name": "SteveGJones"
  },
  "repository": "https://github.com/SteveGJones/ai-first-sdlc-practices",
  "license": "MIT",
  "keywords": ["sdlc", "ai-first", "zero-debt", "validation", "enforcement"]
}
```

### Stub Plugin Manifest (example: `sdlc-team-ai/plugin.json`)

```json
{
  "name": "sdlc-team-ai",
  "version": "0.1.0-stub",
  "description": "AI/ML specialist agents — coming in Phase 2",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "ai", "ml", "agents"]
}
```

### Team Config Schema (`.claude/team-config.json`)

Written by `/sdlc:setup-team`, read by SessionStart hook:

```json
{
  "project_type": "ai-ml",
  "formation": "ai-system-expert",
  "installed_plugins": [
    "sdlc-core@ai-first-sdlc",
    "sdlc-team-ai@ai-first-sdlc",
    "sdlc-lang-python@ai-first-sdlc"
  ],
  "configured_at": "2026-04-03",
  "configured_by": "sdlc:setup-team"
}
```

### Release Channels

Two marketplace configurations via git refs:

| Channel | Git Ref | Audience | Auto-update |
|---------|---------|----------|-------------|
| Beta | `main` branch | Contributors, early adopters | Yes (tracks HEAD) |
| Stable | Tagged release (e.g., `v1.0.0`) | GA teams | Manual (pin to tag) |

Users add the marketplace once:
```
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
```

Beta users: default (follows main).
Stable users: pin to a tag in their settings.

### What Does NOT Change in Phase 1

| Artifact | Status |
|----------|--------|
| `agents/` directory | Unchanged — remains source of truth |
| `tools/` directory | Unchanged — remains source of truth |
| `CLAUDE.md` | Minor update — add plugin install instructions |
| `CONSTITUTION.md` | Unchanged |
| `CLAUDE-CORE.md` | Unchanged |
| `.github/workflows/` | Unchanged |
| `.pre-commit-config.yaml` | Unchanged |
| Existing git hooks setup | Unchanged — plugin hooks are additive |

### Success Criteria

- [ ] `sdlc-core` plugin installs via `/plugin marketplace add` + `/plugin install sdlc-core`
- [ ] All 6 skills invoke correctly via `/sdlc-core:skill-name`
- [ ] 3 agents discoverable and usable via plugin
- [ ] SessionStart hook displays team status banner
- [ ] PostToolUse hook catches `/tmp` usage
- [ ] `/sdlc-core:setup-team` installs stub team plugins and writes team config
- [ ] `/sdlc-core:release-plugin` packages from source into plugins correctly
- [ ] Stub team plugins install without errors
- [ ] `release-mapping.yaml` accurately maps all Phase 1 source → plugin paths
- [ ] Existing `tools/` and `agents/` workflow continues working unchanged

## Phase 2: Team Plugin Population (Feature #71)

### Scope
- Migrate production-maturity agents (50 of 63) into team plugins via `release-mapping.yaml`
- Port `agent-compositions.yaml` into plugin-native agent definitions
- Update `setup-team` skill to show actual agent rosters per team plugin
- Tag `v1.0.0` as first stable release

### Key Work
- Extend `release-mapping.yaml` with all 50 agent mappings
- Validate agent markdown works as plugin agents (frontmatter compatibility)
- Test agent compositions: does installing `sdlc-team-ai` give Claude access to all AI agents?
- Update marketplace.json versions from `0.1.0-stub` to `1.0.0`
- Release pipeline: first real `/sdlc:release-plugin` run for tagged release

### Success Criteria
- All 50 production agents distributed across correct team plugins
- Agent compositions work via plugin discovery
- `setup-team` shows real agent rosters
- Stable `v1.0.0` release tagged and installable

## Phase 3: Language & Domain Plugins (Feature #72)

### Scope
- Build `sdlc-lang-python`, `sdlc-lang-javascript`, `sdlc-lang-go` with real content
- Language-specific validators and patterns
- `paths:` frontmatter for auto-loading skills by file extension
- Extended `setup-team` with language auto-detection

### Key Work
- Extract language-specific logic from existing validators (e.g., framework detection from `check-logging-compliance.py`)
- Create language expert skills with `paths: "**/*.py"` scoping
- Add language detection to `setup-team` (scan file extensions, recommend language plugins)
- Test that skills auto-load only when working in matching files

### Success Criteria
- Language plugins contain language-specific validators and expert agents
- Skills auto-load based on file patterns
- `setup-team` auto-detects project language and recommends plugins

## Phase 4: Distribution & Automation (Feature #73)

### Scope
- CI-driven release automation
- MCP server option for validators (evaluate ROI)
- Managed settings for enterprise lockdown
- Deprecate direct `tools/` usage in favor of plugin skills

### Key Work
- GitHub Action that runs release-plugin on tagged commits
- Evaluate MCP server for validators — are Bash-wrapped scripts sufficient?
- `strictKnownMarketplaces` configuration for enterprise teams
- Update CLAUDE.md to point to plugin installation as primary method
- Migration guide: "moving from direct tool usage to plugin skills"

### Success Criteria
- Tagging a release auto-publishes updated plugins
- Enterprise teams can lock down to approved marketplace only
- CLAUDE.md presents plugin installation as the default setup method
- Legacy direct-tool workflow still works but is documented as advanced/source usage

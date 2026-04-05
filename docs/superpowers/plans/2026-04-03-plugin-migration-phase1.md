# Plugin Migration Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the AI-First SDLC framework as a Claude Code plugin family with a core plugin, marketplace, stub team plugins, and orchestrated setup.

**Architecture:** Source files live in `skills/`, `agents/`, and `tools/`. A `release-mapping.yaml` defines how source maps to plugin directories under `plugins/`. The `/sdlc:release-plugin` skill copies source into plugins, and a marketplace enables distribution. Skills are the user-facing interface; scripts are the implementation.

**Tech Stack:** Claude Code plugins (markdown skills, YAML frontmatter, JSON manifests), Python (validators), Bash (hooks), YAML (release mapping)

**Spec:** `docs/superpowers/specs/2026-04-03-plugin-migration-design.md`

---

### Task 1: Create Feature Branch and Scaffolding

**Files:**
- Create: `plugins/.claude-plugin/marketplace.json`
- Create: `plugins/sdlc-core/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-team-ai/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-team-fullstack/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-team-cloud/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-team-security/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-lang-python/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-lang-javascript/.claude-plugin/plugin.json`
- Create: `release-mapping.yaml`

- [ ] **Step 1: Create feature branch**

```bash
git checkout main
git pull
git checkout -b feature/plugin-migration
```

- [ ] **Step 2: Create the marketplace directory and manifest**

Create `plugins/.claude-plugin/marketplace.json`:

```json
{
  "name": "ai-first-sdlc",
  "owner": {
    "name": "SteveGJones"
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

- [ ] **Step 3: Create core plugin manifest**

Create `plugins/sdlc-core/.claude-plugin/plugin.json`:

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

- [ ] **Step 4: Create stub team plugin manifests**

Create `plugins/sdlc-team-ai/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-ai",
  "version": "0.1.0-stub",
  "description": "AI/ML specialist agents — architects, prompt engineers, RAG designers. Coming in Phase 2.",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "ai", "ml", "agents"]
}
```

Create `plugins/sdlc-team-fullstack/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-fullstack",
  "version": "0.1.0-stub",
  "description": "Full-stack agents — frontend, backend, API, DevOps architects. Coming in Phase 2.",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "fullstack", "frontend", "backend", "agents"]
}
```

Create `plugins/sdlc-team-cloud/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-cloud",
  "version": "0.1.0-stub",
  "description": "Cloud infrastructure agents — cloud, container, SRE specialists. Coming in Phase 2.",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "cloud", "infrastructure", "kubernetes", "agents"]
}
```

Create `plugins/sdlc-team-security/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-security",
  "version": "0.1.0-stub",
  "description": "Security agents — security, compliance, privacy specialists. Coming in Phase 2.",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "security", "compliance", "privacy", "agents"]
}
```

Create `plugins/sdlc-lang-python/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-lang-python",
  "version": "0.1.0-stub",
  "description": "Python-specific validation, patterns, and expert agents. Coming in Phase 3.",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "python", "validation", "patterns"]
}
```

Create `plugins/sdlc-lang-javascript/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-lang-javascript",
  "version": "0.1.0-stub",
  "description": "JavaScript/TypeScript-specific validation and patterns. Coming in Phase 3.",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "javascript", "typescript", "validation"]
}
```

- [ ] **Step 5: Create release-mapping.yaml**

Create `release-mapping.yaml` at repo root:

```yaml
# Release Mapping — defines how source files map to plugin directories
# Used by /sdlc:release-plugin to package source into distributable plugins
#
# Structure:
#   <plugin-name>:
#     <component-type>:
#       - source: <path relative to repo root>
#         dest: <path relative to plugin root> (optional, inferred from source basename)

sdlc-core:
  skills:
    - source: skills/validate/SKILL.md
    - source: skills/new-feature/SKILL.md
    - source: skills/new-feature/templates/proposal.md
    - source: skills/new-feature/templates/retrospective.md
    - source: skills/commit/SKILL.md
    - source: skills/pr/SKILL.md
    - source: skills/rules/SKILL.md
    - source: skills/rules/constitution.md
    - source: skills/setup-team/SKILL.md
    - source: skills/release-plugin/SKILL.md
  agents:
    - source: agents/core/sdlc-enforcer.md
    - source: agents/core/critical-goal-reviewer.md
    - source: agents/testing/code-review-specialist.md
  scripts:
    - source: tools/validation/local-validation.py
    - source: tools/validation/check-technical-debt.py
    - source: tools/validation/check-logging-compliance.py
    - source: tools/validation/validate-architecture.py
    - source: tools/validation/check-broken-references.py
    - source: tools/validation/check-tmp-usage.py
  hooks:
    - source: plugins/sdlc-core/hooks/hooks.json

# Stub plugins — agents mapped here will be populated in Phase 2
sdlc-team-ai:
  agents: []
  # Future:
  # - source: agents/ai-development/ai-solution-architect.md
  # - source: agents/ai-development/prompt-engineer.md
  # - source: agents/ai-development/mcp-server-architect.md
  # - source: agents/ai-builders/rag-system-designer.md
  # - source: agents/ai-builders/context-engineer.md
  # - source: agents/ai-builders/orchestration-architect.md

sdlc-team-fullstack:
  agents: []
  # Future:
  # - source: agents/core/frontend-architect.md
  # - source: agents/core/backend-architect.md
  # - source: agents/core/api-architect.md
  # - source: agents/core/devops-specialist.md

sdlc-team-cloud:
  agents: []
  # Future:
  # - source: agents/core/cloud-architect.md
  # - source: agents/core/container-platform-specialist.md
  # - source: agents/core/sre-specialist.md
  # - source: agents/ai-builders/ai-devops-engineer.md

sdlc-team-security:
  agents: []
  # Future:
  # - source: agents/core/security-architect.md
  # - source: agents/core/compliance-auditor.md
  # - source: agents/core/data-privacy-officer.md

sdlc-lang-python:
  agents: []
  skills: []
  # Future:
  # - source: agents/sdlc/language-python-expert.md

sdlc-lang-javascript:
  agents: []
  skills: []
  # Future:
  # - source: agents/sdlc/language-javascript-expert.md
```

- [ ] **Step 6: Verify directory structure**

```bash
find plugins -type f | sort
ls release-mapping.yaml
```

Expected output shows all 8 plugin.json files, marketplace.json, and release-mapping.yaml.

- [ ] **Step 7: Commit scaffolding**

```bash
git add plugins/ release-mapping.yaml
git commit -m "feat(plugins): scaffold plugin family with marketplace and release mapping

Create plugin directory structure with:
- Marketplace manifest listing 7 plugins (1 core + 4 team + 2 language)
- Core plugin manifest (sdlc-core v0.1.0)
- 6 stub plugin manifests (team-ai, team-fullstack, team-cloud, team-security, lang-python, lang-javascript)
- release-mapping.yaml defining source-to-plugin file mapping

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 2: Create the `rules` Skill (Auto-loaded Reference)

**Files:**
- Create: `skills/rules/SKILL.md`
- Create: `skills/rules/constitution.md`

This is the simplest skill — pure reference material with no side effects. Claude auto-loads it when making compliance decisions.

- [ ] **Step 1: Create the rules SKILL.md**

Create `skills/rules/SKILL.md`:

```markdown
---
name: rules
description: AI-First SDLC compliance rules and standards. Use when checking code quality, validating architecture, enforcing zero technical debt, or making any compliance decision.
---

# AI-First SDLC Rules

You are operating under the AI-First SDLC framework. All code must comply with these rules.

For the complete rules reference, see [constitution.md](constitution.md).

## Quick Reference

### Validation Commands

- After writing code: `python tools/validation/local-validation.py --syntax`
- Before commits: `python tools/validation/local-validation.py --quick`
- Before PR: `python tools/validation/local-validation.py --pre-push`

### Zero Technical Debt Policy

- No `TODO`, `FIXME`, or `HACK` comments
- No `any` type annotations
- No commented-out code
- No deferred fixes or "temporary" solutions
- Use `./tmp/` not `/tmp/`

### 10 Mandatory Logging Points (Application Code)

1. Function entry/exit with context
2. Error handling with stack traces
3. External API/DB calls
4. State mutations
5. Security events
6. Business milestones
7. Performance anomalies
8. Configuration changes
9. Validation failures
10. Resource limits

**Never log:** passwords, tokens, PII, biometrics, encryption keys.

### Workflow

1. Feature proposal (`docs/feature-proposals/XX-name.md`)
2. Feature branch (`feature/name`) — never commit to main
3. Implement with continuous validation
4. Retrospective (`retrospectives/XX-name.md`)
5. PR — CI must pass
```

- [ ] **Step 2: Create the constitution reference**

Copy `CONSTITUTION.md` content into the skill's reference file:

```bash
cp CONSTITUTION.md skills/rules/constitution.md
```

- [ ] **Step 3: Verify skill structure**

```bash
ls -la skills/rules/
cat skills/rules/SKILL.md | head -5
```

Expected: SKILL.md and constitution.md present. First line shows `---` (frontmatter start).

- [ ] **Step 4: Commit**

```bash
git add skills/rules/
git commit -m "feat(skills): add rules skill — auto-loaded SDLC compliance reference

Condensed CONSTITUTION.md into a skill that Claude auto-loads when
making compliance decisions. Full rules available as supporting file.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 3: Create the `validate` Skill

**Files:**
- Create: `skills/validate/SKILL.md`

Wraps `local-validation.py` with a user-friendly skill interface.

- [ ] **Step 1: Create the validate SKILL.md**

Create `skills/validate/SKILL.md`:

```markdown
---
name: validate
description: Run the SDLC validation pipeline. Use when checking code quality before commits or PRs.
disable-model-invocation: true
argument-hint: "[--syntax | --quick | --pre-push]"
---

# SDLC Validation

Run the validation pipeline with the specified level. Default is `--pre-push` (full 8-check pipeline).

## Arguments

- `--syntax` — Syntax checking only (fast, run after every edit)
- `--quick` — Quick validation (syntax + technical debt, run before commits)
- `--pre-push` — Full 8-check pipeline (run before PRs). This is the default.

## Execution

Run the validation script. The script path is relative to the project root:

```bash
python tools/validation/local-validation.py $ARGUMENTS
```

If no arguments are provided, default to `--pre-push`:

```bash
python tools/validation/local-validation.py --pre-push
```

## Pipeline Checks (--pre-push)

The full pipeline runs 8 checks in sequence:

1. **Syntax Check** — Python AST validation
2. **Pre-commit Hooks** — Black formatting, flake8 linting
3. **Technical Debt** — Zero-debt policy enforcement
4. **Architecture** — Required docs validation
5. **Type Safety** — mypy/pyright checks
6. **Security** — Bandit, dependency scanning
7. **Logging Compliance** — 10 mandatory logging points
8. **Static Analysis** — Code quality metrics

## On Failure

If any check fails:
1. Report which checks failed and why
2. Show the specific violations
3. Suggest fixes for each violation
4. Do NOT proceed with commits or PRs until all checks pass
```

- [ ] **Step 2: Verify skill**

```bash
cat skills/validate/SKILL.md | head -5
```

Expected: frontmatter with `name: validate` and `disable-model-invocation: true`.

- [ ] **Step 3: Commit**

```bash
git add skills/validate/
git commit -m "feat(skills): add validate skill — wraps 8-check validation pipeline

Manual skill (/sdlc-core:validate) that runs local-validation.py
with --syntax, --quick, or --pre-push flags.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 4: Create the `new-feature` Skill with Templates

**Files:**
- Create: `skills/new-feature/SKILL.md`
- Create: `skills/new-feature/templates/proposal.md`
- Create: `skills/new-feature/templates/retrospective.md`

- [ ] **Step 1: Create the proposal template**

Create `skills/new-feature/templates/proposal.md`:

```markdown
# Feature Proposal: FEATURE_TITLE

**Proposal Number:** FEATURE_NUMBER
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** CREATED_DATE
**Target Branch:** `feature/FEATURE_NAME`

---

## Executive Summary

_Brief description of what this feature does and why._

---

## Motivation

### Problem Statement

_What problem does this solve?_

### User Stories

- As a developer, I want _X_ so that _Y_

---

## Proposed Solution

_Numbered steps describing the implementation approach._

### Acceptance Criteria

Given _precondition_
When _action_
Then _expected result_

---

## Success Criteria

- [ ] _Criterion 1_
- [ ] _Criterion 2_

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| _Risk 1_ | _Impact_ | _Mitigation_ |

---

## Changes Made

| Action | File |
|--------|------|
| Create/Modify | `path/to/file` |
```

- [ ] **Step 2: Create the retrospective template**

Create `skills/new-feature/templates/retrospective.md`:

```markdown
# Retrospective: Feature #FEATURE_NUMBER — FEATURE_TITLE

**Branch**: `feature/FEATURE_NAME`
**Date**: CREATED_DATE

## What Went Well

- _Key achievement or insight_

## What Could Improve

- _Process improvement opportunity_

## Lessons Learned

1. _Lesson applicable to future work_

## Changes Made

- `path/to/file`: _Description of change_

## Metrics

- **Files modified**: _N_
- **Files created**: _N_
```

- [ ] **Step 3: Create the new-feature SKILL.md**

Create `skills/new-feature/SKILL.md`:

```markdown
---
name: new-feature
description: Create a new feature with proposal, retrospective, and branch. Use when starting new development work.
disable-model-invocation: true
argument-hint: "<number> <name> [title]"
---

# New Feature Setup

Create a new feature with all required artifacts. Arguments:

- `$0` — Feature number (e.g., `70`)
- `$1` — Feature name for branch (e.g., `plugin-migration`)
- `$2+` — Optional title (defaults to name with spaces)

## Steps

1. **Create the feature proposal** at `docs/feature-proposals/$0-$1.md`
   - Use the template from [templates/proposal.md](templates/proposal.md)
   - Replace placeholders:
     - `FEATURE_NUMBER` → `$0`
     - `FEATURE_NAME` → `$1`
     - `FEATURE_TITLE` → `$2` (or derive from `$1` by replacing hyphens with spaces)
     - `CREATED_DATE` → today's date (YYYY-MM-DD)

2. **Create the retrospective** at `retrospectives/$0-$1.md`
   - Use the template from [templates/retrospective.md](templates/retrospective.md)
   - Replace the same placeholders

3. **Create the feature branch**

```bash
git checkout main
git pull
git checkout -b feature/$1
```

4. **Run syntax validation**

```bash
python tools/validation/local-validation.py --syntax
```

5. **Report** the created files and branch name to the user.
```

- [ ] **Step 4: Verify templates and skill**

```bash
find skills/new-feature -type f | sort
```

Expected: `SKILL.md`, `templates/proposal.md`, `templates/retrospective.md`.

- [ ] **Step 5: Commit**

```bash
git add skills/new-feature/
git commit -m "feat(skills): add new-feature skill — automated feature setup workflow

Creates feature proposal, retrospective from templates, and branch.
Replaces manual 5-step workflow from CLAUDE.md.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 5: Create the `commit` and `pr` Skills

**Files:**
- Create: `skills/commit/SKILL.md`
- Create: `skills/pr/SKILL.md`

- [ ] **Step 1: Create the commit SKILL.md**

Create `skills/commit/SKILL.md`:

```markdown
---
name: commit
description: Validated commit — runs quick checks before committing. Use when ready to commit changes.
disable-model-invocation: true
argument-hint: "[commit message]"
---

# Validated Commit

Run quick validation, then commit if clean.

## Steps

1. **Run quick validation**

```bash
python tools/validation/local-validation.py --quick
```

2. **If validation fails**, report the issues and stop. Do NOT commit.

3. **If validation passes**, proceed:
   - Review all changed files with `git status` and `git diff`
   - Stage the relevant files (prefer specific files over `git add -A`)
   - If `$ARGUMENTS` is provided, use it as the commit message
   - If no message provided, draft a concise commit message based on the changes
   - Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

4. **Commit** using a heredoc for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
<type>: <description>

<optional body>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

5. **Run git status** after commit to verify success.
```

- [ ] **Step 2: Create the pr SKILL.md**

Create `skills/pr/SKILL.md`:

```markdown
---
name: pr
description: Create a pull request with full validation. Use when ready to submit work for review.
disable-model-invocation: true
argument-hint: "[base-branch]"
---

# Create Pull Request

Run full validation, then create a PR if clean.

## Steps

1. **Run pre-push validation**

```bash
python tools/validation/local-validation.py --pre-push
```

2. **If validation fails**, report the issues and stop. Do NOT push or create PR.

3. **Verify required artifacts exist:**
   - Feature proposal in `docs/feature-proposals/`
   - Retrospective in `retrospectives/`
   - If either is missing, warn the user and ask whether to proceed.

4. **If validation passes**, proceed:
   - Check if the branch tracks a remote: `git branch -vv`
   - Push to remote with tracking: `git push -u origin <branch>`
   - Base branch defaults to `main` unless `$ARGUMENTS` specifies otherwise

5. **Create the PR** using `gh pr create`:

```bash
gh pr create --title "<short title under 70 chars>" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points summarizing the changes>

## Changes
<List of files modified/created>

## Test plan
- [ ] `python tools/validation/local-validation.py --pre-push` passes
- [ ] CI pipeline passes
<additional test steps as needed>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

6. **Report** the PR URL to the user.
```

- [ ] **Step 3: Verify both skills**

```bash
cat skills/commit/SKILL.md | head -5
cat skills/pr/SKILL.md | head -5
```

Expected: both show frontmatter with `disable-model-invocation: true`.

- [ ] **Step 4: Commit**

```bash
git add skills/commit/ skills/pr/
git commit -m "feat(skills): add commit and pr skills — validated git workflows

commit skill: runs quick validation before staging and committing.
pr skill: runs full pre-push validation, verifies artifacts, creates PR.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 6: Create the `setup-team` Skill

**Files:**
- Create: `skills/setup-team/SKILL.md`

This is the orchestrator skill that makes the plugin family work.

- [ ] **Step 1: Create the setup-team SKILL.md**

Create `skills/setup-team/SKILL.md`:

```markdown
---
name: setup-team
description: Configure SDLC team formation for this project. Recommends and installs team plugins based on project type.
disable-model-invocation: true
---

# SDLC Team Setup

Configure the right agent team for this project by selecting a project type and installing the matching team plugins.

## Steps

1. **Check current team configuration**

Look for `.claude/team-config.json` in the project root. If it exists, display the current formation and ask if the user wants to reconfigure.

2. **Ask the user what kind of project this is** (present as multiple choice):

   - **A. Full-stack web application** — frontend + backend + API + DevOps
   - **B. AI/ML system** — AI architects + prompt engineers + RAG designers
   - **C. Cloud infrastructure** — cloud + containers + SRE + observability
   - **D. API/microservices** — API + backend + integration + performance
   - **E. Security-focused** — security + compliance + privacy
   - **F. Custom** — pick individual team plugins

3. **Map selection to recommended plugins:**

   | Selection | Plugins |
   |-----------|---------|
   | A. Full-stack | `sdlc-team-fullstack` |
   | B. AI/ML | `sdlc-team-ai`, `sdlc-lang-python` |
   | C. Cloud | `sdlc-team-cloud` |
   | D. API | `sdlc-team-fullstack`, `sdlc-team-cloud` |
   | E. Security | `sdlc-team-security` |
   | F. Custom | User picks from list |

4. **Auto-detect language** by scanning file extensions in the project:
   - `.py` files dominant → also recommend `sdlc-lang-python`
   - `.js`/`.ts` files dominant → also recommend `sdlc-lang-javascript`

5. **Present the recommendation** to the user:

   ```
   Recommended team for this project:

   ✓ sdlc-core (already installed)
   ○ sdlc-team-ai — AI architects, prompt engineers, RAG designers
   ○ sdlc-lang-python — Python-specific validation and patterns

   Install these plugins? [Y/n]
   ```

6. **If confirmed, install the plugins.** Tell the user to run:

   ```
   /plugin install <plugin-name>@ai-first-sdlc
   ```

   for each recommended plugin. Note: skill cannot programmatically install plugins — it provides the commands for the user to run.

7. **Write `.claude/team-config.json`** to record the selection:

   ```json
   {
     "project_type": "<selection>",
     "formation": "<formation-name>",
     "installed_plugins": [
       "sdlc-core@ai-first-sdlc",
       "<team-plugin>@ai-first-sdlc"
     ],
     "configured_at": "<YYYY-MM-DD>",
     "configured_by": "sdlc:setup-team"
   }
   ```

   The formation name maps from `agents/agent-compositions.yaml`:
   - Full-stack → `full-stack-developer`
   - AI/ML → `ai-system-expert`
   - Cloud → `cloud-native-architect`
   - API → `enterprise-architect`
   - Security → `compliance-specialist`

8. **Report** the configured formation and installed plugins.
```

- [ ] **Step 2: Verify skill**

```bash
cat skills/setup-team/SKILL.md | head -5
```

Expected: frontmatter with `name: setup-team` and `disable-model-invocation: true`.

- [ ] **Step 3: Commit**

```bash
git add skills/setup-team/
git commit -m "feat(skills): add setup-team skill — orchestrated team assembly

Interactive skill that asks project type, recommends team plugins,
and writes team-config.json. Maps to agent-compositions.yaml formations.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 7: Create the `release-plugin` Skill

**Files:**
- Create: `skills/release-plugin/SKILL.md`

This skill reads `release-mapping.yaml` and packages source into plugin directories.

- [ ] **Step 1: Create the release-plugin SKILL.md**

Create `skills/release-plugin/SKILL.md`:

```markdown
---
name: release-plugin
description: Package source files into plugin directories using release-mapping.yaml. Use when preparing a plugin release.
disable-model-invocation: true
argument-hint: "[patch | minor | major]"
---

# Release Plugin

Package source files into plugin directories based on `release-mapping.yaml`.

## Arguments

- `patch` — Bump patch version (0.1.0 → 0.1.1). Default if no argument.
- `minor` — Bump minor version (0.1.0 → 0.2.0).
- `major` — Bump major version (0.1.0 → 1.0.0).

## Steps

1. **Read `release-mapping.yaml`** from the repository root. This file defines which source files map to which plugin directories.

2. **For each plugin in the mapping**, process each component type:

   **Skills** — for each skill entry:
   - Read the source file (e.g., `skills/validate/SKILL.md`)
   - Determine the destination path in the plugin: `plugins/<plugin>/skills/<skill-name>/SKILL.md`
   - The skill directory name comes from the source path (e.g., `skills/validate/SKILL.md` → `skills/validate/SKILL.md`)
   - Copy the file, preserving directory structure
   - For skills with supporting files (templates, references), copy the entire skill directory

   **Agents** — for each agent entry:
   - Read the source file (e.g., `agents/core/sdlc-enforcer.md`)
   - Copy to `plugins/<plugin>/agents/<filename>`

   **Scripts** — for each script entry:
   - Read the source file (e.g., `tools/validation/check-technical-debt.py`)
   - Copy to `plugins/<plugin>/scripts/<filename>`

   **Hooks** — hooks are plugin-native, no copy needed (they reference `${CLAUDE_PLUGIN_ROOT}`)

3. **Bump version** in each non-stub plugin's `plugin.json`:
   - Read the current version from `.claude-plugin/plugin.json`
   - Apply the version bump (patch/minor/major)
   - Write the updated version back
   - Also update the version in `plugins/.claude-plugin/marketplace.json` for this plugin

4. **Validate the result:**
   - Verify every source file in the mapping exists
   - Verify every destination file was written
   - Check that `plugin.json` is valid JSON for each plugin
   - Report any missing source files as errors

5. **Report** what was packaged:
   ```
   Release packaged:
     sdlc-core v0.1.1:
       Skills: 7 (validate, new-feature, commit, pr, rules, setup-team, release-plugin)
       Agents: 3 (sdlc-enforcer, critical-goal-reviewer, code-review-specialist)
       Scripts: 6
       Hooks: 1

     Stub plugins unchanged:
       sdlc-team-ai (0.1.0-stub)
       sdlc-team-fullstack (0.1.0-stub)
       ...

   Next steps:
     1. Review changes: git diff plugins/
     2. Commit: git add plugins/ && git commit -m "release: sdlc-core v0.1.1"
     3. Tag for stable: git tag v0.1.1
   ```
```

- [ ] **Step 2: Verify skill**

```bash
cat skills/release-plugin/SKILL.md | head -5
```

Expected: frontmatter with `name: release-plugin` and `disable-model-invocation: true`.

- [ ] **Step 3: Commit**

```bash
git add skills/release-plugin/
git commit -m "feat(skills): add release-plugin skill — source-to-plugin packaging

Reads release-mapping.yaml, copies source files into plugin directories,
bumps versions, validates structure. Implements the source-to-release pipeline.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 8: Create Plugin Hooks and Session Banner

**Files:**
- Create: `plugins/sdlc-core/hooks/hooks.json`
- Create: `plugins/sdlc-core/scripts/session-banner.sh`

- [ ] **Step 1: Create the hooks configuration**

Create `plugins/sdlc-core/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/session-banner.sh"
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

- [ ] **Step 2: Create the session banner script**

Create `plugins/sdlc-core/scripts/session-banner.sh`:

```bash
#!/bin/bash
# SDLC Core — Session Start Banner
# Displays installed team plugins and formation status

TEAM_CONFIG=".claude/team-config.json"

echo "--- AI-First SDLC ---"

# Show core version
CORE_VERSION=$(python3 -c "
import json, os
p = os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'), '.claude-plugin', 'plugin.json')
if os.path.exists(p):
    print(json.load(open(p))['version'])
else:
    print('unknown')
" 2>/dev/null || echo "unknown")
echo "sdlc-core v${CORE_VERSION}"

# Show team formation if configured
if [ -f "$TEAM_CONFIG" ]; then
    FORMATION=$(python3 -c "import json; print(json.load(open('$TEAM_CONFIG')).get('formation', 'none'))" 2>/dev/null)
    PROJECT_TYPE=$(python3 -c "import json; print(json.load(open('$TEAM_CONFIG')).get('project_type', 'unknown'))" 2>/dev/null)
    echo "Formation: ${FORMATION} (${PROJECT_TYPE})"
else
    echo "No team configured. Run /sdlc-core:setup-team to set up."
fi

echo "---"
```

- [ ] **Step 3: Make banner executable**

```bash
chmod +x plugins/sdlc-core/scripts/session-banner.sh
```

- [ ] **Step 4: Verify hooks and banner**

```bash
python3 -c "import json; json.load(open('plugins/sdlc-core/hooks/hooks.json'))"
echo "hooks.json is valid JSON"
bash plugins/sdlc-core/scripts/session-banner.sh
```

Expected: "hooks.json is valid JSON" followed by the banner output (showing "No team configured").

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-core/hooks/ plugins/sdlc-core/scripts/session-banner.sh
git commit -m "feat(plugins): add SessionStart banner and PostToolUse hooks

SessionStart: displays installed SDLC plugins and team formation.
PostToolUse: runs check-tmp-usage.py on Write/Edit operations.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 9: Run First Release — Dog-food the Release Skill

**Files:**
- Modify: Various files in `plugins/sdlc-core/` (populated by release)

This task manually executes what the `release-plugin` skill describes, since the skill itself is just instructions — Claude follows them.

- [ ] **Step 1: Copy skills into the core plugin**

```bash
# Copy each skill directory into the plugin
cp -r skills/validate plugins/sdlc-core/skills/
cp -r skills/new-feature plugins/sdlc-core/skills/
cp -r skills/commit plugins/sdlc-core/skills/
cp -r skills/pr plugins/sdlc-core/skills/
cp -r skills/rules plugins/sdlc-core/skills/
cp -r skills/setup-team plugins/sdlc-core/skills/
cp -r skills/release-plugin plugins/sdlc-core/skills/
```

- [ ] **Step 2: Copy agents into the core plugin**

```bash
mkdir -p plugins/sdlc-core/agents
cp agents/core/sdlc-enforcer.md plugins/sdlc-core/agents/
cp agents/core/critical-goal-reviewer.md plugins/sdlc-core/agents/
cp agents/testing/code-review-specialist.md plugins/sdlc-core/agents/
```

- [ ] **Step 3: Copy validator scripts into the core plugin**

```bash
# scripts/ dir already has session-banner.sh, add validators
cp tools/validation/local-validation.py plugins/sdlc-core/scripts/
cp tools/validation/check-technical-debt.py plugins/sdlc-core/scripts/
cp tools/validation/check-logging-compliance.py plugins/sdlc-core/scripts/
cp tools/validation/validate-architecture.py plugins/sdlc-core/scripts/
cp tools/validation/check-broken-references.py plugins/sdlc-core/scripts/
cp tools/validation/check-tmp-usage.py plugins/sdlc-core/scripts/
```

- [ ] **Step 4: Verify the complete plugin structure**

```bash
find plugins/sdlc-core -type f | sort
```

Expected output:

```
plugins/sdlc-core/.claude-plugin/plugin.json
plugins/sdlc-core/agents/code-review-specialist.md
plugins/sdlc-core/agents/critical-goal-reviewer.md
plugins/sdlc-core/agents/sdlc-enforcer.md
plugins/sdlc-core/hooks/hooks.json
plugins/sdlc-core/scripts/check-broken-references.py
plugins/sdlc-core/scripts/check-logging-compliance.py
plugins/sdlc-core/scripts/check-technical-debt.py
plugins/sdlc-core/scripts/check-tmp-usage.py
plugins/sdlc-core/scripts/local-validation.py
plugins/sdlc-core/scripts/session-banner.sh
plugins/sdlc-core/scripts/validate-architecture.py
plugins/sdlc-core/skills/commit/SKILL.md
plugins/sdlc-core/skills/new-feature/SKILL.md
plugins/sdlc-core/skills/new-feature/templates/proposal.md
plugins/sdlc-core/skills/new-feature/templates/retrospective.md
plugins/sdlc-core/skills/pr/SKILL.md
plugins/sdlc-core/skills/release-plugin/SKILL.md
plugins/sdlc-core/skills/rules/SKILL.md
plugins/sdlc-core/skills/rules/constitution.md
plugins/sdlc-core/skills/setup-team/SKILL.md
plugins/sdlc-core/skills/validate/SKILL.md
```

- [ ] **Step 5: Validate all JSON files**

```bash
python3 -c "
import json, glob
for f in glob.glob('plugins/**/*.json', recursive=True):
    try:
        json.load(open(f))
        print(f'OK: {f}')
    except Exception as e:
        print(f'FAIL: {f} — {e}')
"
```

Expected: all JSON files report OK.

- [ ] **Step 6: Commit the first release**

```bash
git add plugins/sdlc-core/skills/ plugins/sdlc-core/agents/ plugins/sdlc-core/scripts/
git commit -m "release: sdlc-core v0.1.0 — first plugin release

Package source files into sdlc-core plugin:
- 7 skills: validate, new-feature, commit, pr, rules, setup-team, release-plugin
- 3 agents: sdlc-enforcer, critical-goal-reviewer, code-review-specialist
- 6 validator scripts + session banner
- Hooks: SessionStart (banner), PostToolUse (tmp check)

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 10: Create Feature Proposal and Retrospective

**Files:**
- Create: `docs/feature-proposals/70-plugin-migration.md`
- Create: `retrospectives/70-plugin-migration.md`

- [ ] **Step 1: Create the feature proposal**

Create `docs/feature-proposals/70-plugin-migration.md`:

```markdown
# Feature Proposal: Plugin Migration Phase 1

**Proposal Number:** 70
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-03
**Target Branch:** `feature/plugin-migration`

---

## Executive Summary

Package the AI-First SDLC framework as a Claude Code plugin family. Phase 1 delivers the core plugin (`sdlc-core`) with skills, agents, hooks, and a marketplace for distributing team-specific plugins.

---

## Motivation

### Problem Statement

The framework (63 agents, 18 validators, 42 automation tools) is distributed by cloning a repo and reading documentation. This requires manual setup and has no versioning, team distribution, or namespace isolation. Claude Code now supports plugins — the framework should use them.

### User Stories

- As a team lead, I want one-command installation so new team members can onboard instantly
- As a developer, I want `/sdlc-core:validate` instead of memorizing `python tools/validation/local-validation.py --pre-push`
- As a framework maintainer, I want versioned releases so teams get stable, tested updates

---

## Proposed Solution

1. Create a plugin family: `sdlc-core` + team plugins + language plugins
2. Build a source-to-release pipeline: develop in `tools/`/`agents/`/`skills/`, package into `plugins/` via `release-mapping.yaml`
3. Create 7 skills wrapping core workflows (validate, new-feature, commit, pr, rules, setup-team, release-plugin)
4. Ship 3 gateway agents with core (sdlc-enforcer, critical-goal-reviewer, code-review-specialist)
5. Add hooks for session startup and post-edit validation
6. Create stub plugins for 4 team types + 2 languages
7. Build marketplace for distribution

### Acceptance Criteria

- Plugin installs via `/plugin marketplace add` + `/plugin install sdlc-core`
- All 7 skills invoke correctly
- 3 agents discoverable via plugin
- Hooks fire on session start and post-edit
- Stub team plugins installable
- Existing `tools/` workflow unchanged

---

## Success Criteria

- [ ] `sdlc-core` plugin installs and works
- [ ] All skills invoke via `/sdlc-core:<name>`
- [ ] Agents are discoverable
- [ ] Hooks fire correctly
- [ ] Setup-team recommends and records team plugins
- [ ] Release-plugin packages source into plugins
- [ ] Existing tooling continues working

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Plugin system behavior differences | Medium | Test each skill individually after packaging |
| Agent frontmatter compatibility | Low | Agents already use YAML frontmatter matching plugin format |
| Hook timing issues | Low | Test SessionStart and PostToolUse independently |

---

## Changes Made

| Action | File |
|--------|------|
| Create | `plugins/` directory structure (marketplace + 7 plugins) |
| Create | `skills/` directory (7 skill source files) |
| Create | `release-mapping.yaml` |
| Modify | `CLAUDE.md` (add plugin install instructions) |
```

- [ ] **Step 2: Create the retrospective**

Create `retrospectives/70-plugin-migration.md`:

```markdown
# Retrospective: Feature #70 — Plugin Migration Phase 1

**Branch**: `feature/plugin-migration`
**Date**: 2026-04-03

## What Went Well

- _To be completed after implementation_

## What Could Improve

- _To be completed after implementation_

## Lessons Learned

1. _To be completed after implementation_

## Changes Made

- _To be completed after implementation_

## Metrics

- **Skills created**: 7
- **Agents packaged**: 3
- **Plugins created**: 7 (1 core + 6 stubs)
- **New source directories**: 2 (`skills/`, `plugins/`)
```

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/70-plugin-migration.md retrospectives/70-plugin-migration.md
git commit -m "docs: add feature proposal and retrospective for plugin migration (#70)

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 11: Update CLAUDE.md with Plugin Instructions

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read current CLAUDE.md**

```bash
cat CLAUDE.md
```

- [ ] **Step 2: Add plugin installation section**

Add a new section after the existing content. The exact edit depends on current content, but add:

```markdown
## Plugin Installation (Recommended)

Install the SDLC plugin family for skills, agents, and automated enforcement:

```bash
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
```

Then configure your team: `/sdlc-core:setup-team`

### Available Skills

| Skill | Description |
|-------|-------------|
| `/sdlc-core:validate` | Run 8-check validation pipeline |
| `/sdlc-core:new-feature` | Create feature proposal, retrospective, and branch |
| `/sdlc-core:commit` | Validated commit with quick checks |
| `/sdlc-core:pr` | Full validation + PR creation |
| `/sdlc-core:setup-team` | Configure team formation |
| `/sdlc-core:release-plugin` | Package source into plugins |
```

- [ ] **Step 3: Verify the update reads well**

Read the updated CLAUDE.md and verify it's concise and doesn't duplicate existing content.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add plugin installation instructions to CLAUDE.md

Add recommended plugin install path and available skills table.
Existing validation commands remain as the direct-tool alternative.

Part of Feature #70: Plugin Migration Phase 1"
```

---

### Task 12: Verify Plugin Installation Locally

**Files:** None (verification only)

- [ ] **Step 1: Validate all plugin manifests**

```bash
python3 -c "
import json, os

errors = []
for root, dirs, files in os.walk('plugins'):
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                data = json.load(open(path))
                if 'plugin.json' in f:
                    assert 'name' in data, 'missing name field'
                    assert 'version' in data, 'missing version field'
                    assert 'description' in data, 'missing description field'
                    print(f'OK: {path} ({data[\"name\"]} v{data[\"version\"]})')
                elif 'marketplace.json' in f:
                    assert 'name' in data, 'missing name field'
                    assert 'plugins' in data, 'missing plugins field'
                    print(f'OK: {path} (marketplace: {data[\"name\"]}, {len(data[\"plugins\"])} plugins)')
                else:
                    print(f'OK: {path}')
            except Exception as e:
                errors.append(f'FAIL: {path} — {e}')

if errors:
    print()
    for e in errors:
        print(e)
    exit(1)
else:
    print()
    print('All plugin manifests valid.')
"
```

Expected: all manifests valid, 7 plugins listed, marketplace has 7 entries.

- [ ] **Step 2: Verify skill frontmatter**

```bash
python3 -c "
import os, re

skills_dir = 'plugins/sdlc-core/skills'
for skill_dir in sorted(os.listdir(skills_dir)):
    skill_path = os.path.join(skills_dir, skill_dir, 'SKILL.md')
    if os.path.exists(skill_path):
        content = open(skill_path).read()
        if content.startswith('---'):
            # Extract frontmatter
            end = content.index('---', 3)
            fm = content[3:end]
            name = re.search(r'name:\s*(.+)', fm)
            desc = re.search(r'description:\s*(.+)', fm)
            dmi = 'disable-model-invocation: true' in fm
            print(f'OK: {skill_dir} (name={name.group(1).strip() if name else \"MISSING\"}, auto={not dmi})')
        else:
            print(f'WARN: {skill_dir} — no frontmatter')
"
```

Expected: 7 skills listed, `rules` shows `auto=True`, all others show `auto=False`.

- [ ] **Step 3: Verify agent files have valid frontmatter**

```bash
python3 -c "
import os

agents_dir = 'plugins/sdlc-core/agents'
for f in sorted(os.listdir(agents_dir)):
    path = os.path.join(agents_dir, f)
    content = open(path).read()
    if content.startswith('---'):
        print(f'OK: {f} (has frontmatter)')
    else:
        print(f'WARN: {f} — no frontmatter')
"
```

Expected: all 3 agents show "has frontmatter".

- [ ] **Step 4: Verify scripts are present**

```bash
ls -la plugins/sdlc-core/scripts/
```

Expected: 7 files (6 validators + session-banner.sh).

- [ ] **Step 5: Run existing validation to confirm nothing is broken**

```bash
python tools/validation/local-validation.py --syntax
```

Expected: syntax check passes — existing tooling unaffected.

- [ ] **Step 6: Commit verification results (if any fixes needed)**

If any fixes were made during verification, commit them:

```bash
git add -A
git commit -m "fix(plugins): address issues found during plugin verification

Part of Feature #70: Plugin Migration Phase 1"
```

If no fixes needed, skip this step.

---

### Task 13: Complete Retrospective and Final Commit

**Files:**
- Modify: `retrospectives/70-plugin-migration.md`

- [ ] **Step 1: Update the retrospective with actual results**

Edit `retrospectives/70-plugin-migration.md` to replace the placeholder sections with actual observations from the implementation. Include:

- What went well (plugin structure, skill design, etc.)
- What could improve (any pain points discovered)
- Lessons learned (differences between plugin skills and standalone tools, etc.)
- Actual changes made (list all files)
- Updated metrics

- [ ] **Step 2: Commit the completed retrospective**

```bash
git add retrospectives/70-plugin-migration.md
git commit -m "docs: complete retrospective for plugin migration (#70)

Part of Feature #70: Plugin Migration Phase 1"
```

- [ ] **Step 3: Run final pre-push validation**

```bash
python tools/validation/local-validation.py --pre-push
```

Expected: all 8 checks pass.

- [ ] **Step 4: Push and create PR**

```bash
git push -u origin feature/plugin-migration
```

Then create PR targeting `main` with summary of all Phase 1 deliverables.

---

## Phase 2-4 Outlines (Not Detailed Plans — To Be Written When Starting Each Phase)

### Phase 2: Team Plugin Population (Feature #71)

**Prerequisite:** Phase 1 merged to main.

**High-level tasks:**
1. Triage all 63 agents by maturity — identify the ~50 `production` agents
2. Extend `release-mapping.yaml` with agent-to-team-plugin mappings
3. Validate agent frontmatter compatibility with Claude Code plugin agent format
4. Port `agent-compositions.yaml` concepts into plugin agent descriptions
5. Run `/sdlc-core:release-plugin` to populate team plugins
6. Update `setup-team` skill to show real agent rosters per plugin
7. Update marketplace versions from `0.1.0-stub` to `1.0.0`
8. Tag `v1.0.0` as first stable release
9. Test: install each team plugin, verify agents are discoverable and functional

### Phase 3: Language & Domain Plugins (Feature #72)

**Prerequisite:** Phase 2 merged.

**High-level tasks:**
1. Extract language-specific logic from `check-logging-compliance.py` (framework detection for Flask/FastAPI/Django)
2. Create Python-specific skill with `paths: "**/*.py"` for auto-loading
3. Create JavaScript/TypeScript skill with `paths: "**/*.{js,ts,tsx}"`
4. Add language expert agents to language plugins
5. Add language auto-detection to `setup-team` (scan file extensions)
6. Test: verify skills auto-load by file pattern, verify language detection works

### Phase 4: Distribution & Automation (Feature #73)

**Prerequisite:** Phase 3 merged.

**High-level tasks:**
1. Create GitHub Action for CI-driven release (runs `release-plugin` on tagged commits)
2. Evaluate MCP server for validators (compare vs Bash-wrapped scripts)
3. Add `strictKnownMarketplaces` config for enterprise lockdown
4. Update CLAUDE.md to present plugin installation as primary method
5. Write migration guide: "from direct tool usage to plugin skills"
6. Mark legacy direct-tool docs as "advanced/source usage"

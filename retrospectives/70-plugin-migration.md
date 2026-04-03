# Retrospective: Feature #70 — Plugin Migration Phase 1

**Branch**: `feature/plugin-migration`
**Date**: 2026-04-03

## What Went Well

- **Source-to-release pipeline design**: The decision to keep `tools/` and `agents/` as source with `plugins/` as release artifact avoided a destructive migration. Both old and new workflows work simultaneously.
- **Plugin family model**: Decomposing into core + team + language plugins gives lean installs. The stub plugin pattern lets us prove the marketplace architecture without migrating all 63 agents upfront.
- **Skill design mapped cleanly to existing workflows**: Each skill wraps an existing tool or procedure. No new logic was needed — skills are instruction layers over proven validators.
- **Subagent-driven execution**: 13 tasks executed via fresh subagents with spec compliance review kept implementation focused and context-clean.

## What Could Improve

- **Skills are instruction-only, not executable**: Skills tell Claude what commands to run but cannot execute autonomously. A future MCP server wrapping the validators would give Claude native tool access without Bash.
- **Release process is manual**: The release-plugin skill describes a copy workflow but doesn't automate it with a script. Phase 4 should add a Python script or GitHub Action for CI-driven releases.

## Lessons Learned

1. **Plugin skills and repo agents coexist**: The plugin's agents directory mirrors `.claude/agents/` — both work. This means migration can be gradual, not all-or-nothing.
2. **`disable-model-invocation: true` is essential for workflow skills**: Skills with side effects (commit, PR, deploy) must be manual-only. Auto-loaded skills should be pure reference (like `rules`).
3. **Marketplace source paths must be relative**: Plugins within a marketplace use `./sdlc-core` relative paths. This enables same-repo hosting without external infrastructure.
4. **SessionStart hooks are the team onboarding entry point**: The banner displays formation status and suggests setup-team, creating a natural discovery flow for new users.

## Changes Made

- `plugins/` — Plugin family directory (marketplace + 7 plugins)
- `skills/` — Skill source directory (7 skills with templates)
- `release-mapping.yaml` — Source-to-plugin mapping configuration
- `CLAUDE.md` — Added plugin installation section
- `docs/feature-proposals/70-plugin-migration.md` — Feature proposal
- `retrospectives/70-plugin-migration.md` — This retrospective

## Metrics

- **Commits**: 11
- **Files created**: 43
- **Lines added**: 6,707
- **Skills created**: 7 (validate, new-feature, commit, pr, rules, setup-team, release-plugin)
- **Agents packaged**: 3 (sdlc-enforcer, critical-goal-reviewer, code-review-specialist)
- **Plugins created**: 7 (1 core + 4 team stubs + 2 language stubs)
- **Hooks configured**: 2 (SessionStart, PostToolUse)
- **New source directories**: 2 (`skills/`, `plugins/`)

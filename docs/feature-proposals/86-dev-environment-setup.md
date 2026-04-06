# Feature Proposal: Local Dev Environment Setup Script

**Proposal Number:** 86
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-06
**Target Branch:** `feature/dev-environment-setup`

---

## Executive Summary

A `scripts/setup-dev-environment.sh` script that symlinks shipped skills and agents (per `release-mapping.yaml`) into `.claude/skills/` and `.claude/agents/` so the local Claude Code session uses the source code we are actively editing — not a stale published version.

---

## Motivation

### Problem Statement

When developing the SDLC plugin family, we need to test changes to skills and agents locally before publishing. Currently:

- Editing `skills/validate/SKILL.md` has no effect on the local Claude Code session — it uses the published version from the GitHub marketplace
- Adding a new agent at `agents/core/foo.md` requires publishing before we can use it
- Bug fixes can't be verified until merged
- The smoke test (#85) only validates `main` branch, not feature branches

This means we develop blind: we can't dogfood our own changes during development.

### User Stories

- As a framework developer, I want my local Claude Code session to use my edited skills so I can test changes immediately
- As a framework developer, I want a consistent agent set across the team so we all work with the same tools
- As a framework developer, I don't want to publish broken code just to test it

---

## Proposed Solution

A bash script (`scripts/setup-dev-environment.sh`) that:

1. Reads `release-mapping.yaml` to find every skill and agent we ship
2. Creates symlinks in `.claude/skills/` and `.claude/agents/` pointing to the source files
3. Skills get directory symlinks (covering SKILL.md + templates + references)
4. Agents get file symlinks
5. Is idempotent — re-run after `release-mapping.yaml` changes
6. Has a `--force` flag to replace pre-existing real files
7. Documents the rule: "only use shipped skills and agents during development"

### Acceptance Criteria

Given a fresh clone of the repo
When I run `./scripts/setup-dev-environment.sh`
Then `.claude/skills/` and `.claude/agents/` contain symlinks to all shipped items
And editing a source file is immediately visible in the next Claude Code session

---

## Success Criteria

- [ ] Script reads release-mapping.yaml correctly
- [ ] Symlinks resolve to source files in `skills/` and `agents/`
- [ ] Idempotent — safe to re-run
- [ ] `--force` flag replaces pre-existing real files
- [ ] Non-shipped skills/agents unaffected
- [ ] Developer documentation clear about the "shipped only" rule

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Script accidentally deletes real files | Lost work | Symlinks only by default; `--force` is opt-in |
| BSD vs GNU sed differences | Script breaks on Linux/macOS | Use POSIX character classes `[[:space:]]` |
| .claude/ becomes committed | Credentials leak | .claude/ is gitignored, verified |
| Developers create local skills outside the script | State drift | Documented rule + scripts/README.md |

---

## Changes Made

| Action | File |
|--------|------|
| Create | `scripts/setup-dev-environment.sh` |
| Create | `scripts/README.md` |
| Create | `docs/feature-proposals/86-dev-environment-setup.md` |

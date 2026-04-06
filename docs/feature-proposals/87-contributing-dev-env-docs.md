# Feature Proposal: Document Dev Environment Setup in CONTRIBUTING.md

**Proposal Number:** 87
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-06
**Target Branch:** `feature/contributing-dev-env-docs`

---

## Executive Summary

Update `CONTRIBUTING.md` to document the `./scripts/setup-dev-environment.sh` script (delivered in #86) so contributors discover the local symlink workflow when they first read the contribution guide. Replace the stale `setup-smart.py` reference in the Getting Started section.

---

## Motivation

### Problem Statement

The dev environment setup script shipped in #86 lives in `scripts/README.md`, but most new contributors won't read that file before they start. The first place a contributor looks is `CONTRIBUTING.md`, and right now that file:

- Tells contributors to run `python setup-smart.py "contributing to framework"` — a stale command from a much older version of the framework
- Says nothing about the symlink workflow for local skill/agent development
- Doesn't capture the "shipped only" rule that prevents state drift across the team

This means new contributors either start with the wrong tooling or test against stale published versions of skills and agents.

### User Stories

- As a new contributor, I want CONTRIBUTING.md to tell me how to set up my local dev environment so I'm not following stale instructions
- As a maintainer, I want the "shipped only" rule documented in the contribution guide so it's discoverable, not buried in `scripts/README.md`

---

## Proposed Solution

A focused edit to `CONTRIBUTING.md` that:

1. Replaces the stale `setup-smart.py` line with a pointer to the new dev environment setup section
2. Adds a "Dev Environment Setup" section after Getting Started with:
   - The quick start command (`./scripts/setup-dev-environment.sh`)
   - The `--force` flag for replacing pre-existing real files
   - The "shipped only" rule (verbatim from `scripts/README.md` so the wording stays consistent)
   - What the script touches (8 shipped skills, 53 shipped agents) and what it leaves alone
3. Points to `scripts/README.md` for the full documentation

### Acceptance Criteria

Given a contributor reading `CONTRIBUTING.md` for the first time
When they reach the Getting Started section
Then they discover the dev environment setup script
And they understand the "shipped only" rule before they touch `.claude/`

---

## Success Criteria

- [ ] Stale `setup-smart.py` reference removed from Getting Started
- [ ] New "Dev Environment Setup" section added with the quick start command
- [ ] `--force` flag documented
- [ ] "Shipped only" rule captured verbatim from `scripts/README.md`
- [ ] Touched/doesn't-touch list matches `release-mapping.yaml`
- [ ] Reference to `scripts/README.md` for full docs

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wording drifts from `scripts/README.md` | Inconsistent guidance | Quote the rule verbatim |
| Skill/agent counts go stale | Confused contributors | Counts derived from `release-mapping.yaml`; recheck on each PR that changes the mapping |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `CONTRIBUTING.md` |
| Create | `docs/feature-proposals/87-contributing-dev-env-docs.md` |

# Feature Proposal: Fix Marketplace JSON Location

**Proposal Number:** 120
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `fix/marketplace-json-location`
**Issue:** #120
**Type:** Critical bug fix

---

## Executive Summary

`/plugin marketplace add SteveGJones/ai-first-sdlc-practices` has been broken since the plugin family launched (#73, plugin migration Phase 1). Claude Code's marketplace add command clones the repository and looks for `.claude-plugin/marketplace.json` at the **repository root**, but ours has always been at `plugins/.claude-plugin/marketplace.json`. The result: no user has ever successfully installed the plugin family from the public marketplace. The bug went undetected for ~3 weeks because CI never tested the actual marketplace install path.

This proposal moves the marketplace manifest to the correct location, updates the source paths inside it to point at the plugin sub-directories, and updates the two source files that referenced the old location. Reproduced on two separate machines per the issue.

---

## Motivation

### Problem statement

When a user runs the documented install command:

```
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
```

Claude Code clones the repository to `~/.claude/plugins/marketplaces/SteveGJones-ai-first-sdlc-practices/` and immediately fails with:

```
Error: Marketplace file not found at /Users/<user>/.claude/plugins/marketplaces/SteveGJones-ai-first-sdlc-practices/.claude-plugin/marketplace.json.
```

This is the **first** thing a new user does when adopting the framework. It has never worked. The plugin family has been functionally undiscoverable through the public install path since day one.

### Root cause

The original plugin migration design (PR #73) treated `plugins/` as the conceptual root of the plugin family and placed the marketplace manifest at `plugins/.claude-plugin/marketplace.json`. This was wrong: Claude Code's marketplace discovery convention is fixed at `.claude-plugin/marketplace.json` relative to the cloned repository root, regardless of where the actual plugin code lives.

The mistake propagated through three subsequent EPICs (#71 team plugin population, #82-83 agent discovery, #105 knowledge base) because every PR that touched marketplace.json edited the same wrong-location file. None of those PRs surfaced the bug because none of them tested the real install path against a fresh client.

### Why this slipped through

- CI never tested `/plugin marketplace add` against the repo. CI runs validators on file contents, not Claude Code commands.
- The Docker smoke test (#85) does test plugin install but uses `/plugin install --scope project` from a local clone of the repo, which bypasses the marketplace add step.
- Local development uses `scripts/setup-dev-environment.sh` to symlink shipped plugins into `.claude/`, also bypassing marketplace add.
- No human tried the documented public install path because everyone working on the framework already had the plugins in their dev environment.

### User stories

- As a new user discovering the framework, I want `/plugin marketplace add SteveGJones/ai-first-sdlc-practices` to actually work so I can install the plugin family
- As a future contributor running CI, I want a regression test for the marketplace install path so this can never break silently again
- As a user who tried to install last month and gave up, I want a clear answer in the issue tracker about when this was fixed

---

## Proposed Solution

Three fixes plus a regression test recommendation.

### Fix 1: Move marketplace.json to the repo root

Move `plugins/.claude-plugin/marketplace.json` → `.claude-plugin/marketplace.json`. Delete the now-empty `plugins/.claude-plugin/` directory.

### Fix 2: Update source paths inside marketplace.json

Each plugin entry's `source` field is interpreted relative to the marketplace.json file location. Before, with the marketplace at `plugins/.claude-plugin/marketplace.json`, the paths `./sdlc-core` resolved to `plugins/sdlc-core` — correct. After moving to the repo root, the paths must be `./plugins/sdlc-core` to resolve to the same location.

All eleven plugin entries get this update:
- `./sdlc-core` → `./plugins/sdlc-core`
- `./sdlc-team-common` → `./plugins/sdlc-team-common`
- (and so on for all 11)

### Fix 3: Update active source files that reference the old location

Two active source files reference the old path and must be updated:

1. **`skills/release-plugin/SKILL.md`** — line 46, the version-bump step references the marketplace location for in-place updates. Change to `.claude-plugin/marketplace.json (at the repo root)`.
2. **`agents/core/pipeline-orchestrator.md`** — line 73, the 1st-party tool discovery workflow searches the marketplace for existing plugins. Change to `.claude-plugin/marketplace.json (at the repo root)`.

Both files have plugin copies under `plugins/sdlc-core/skills/release-plugin/SKILL.md` and `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` that also need updating. Normally these would be regenerated by `release-plugin` from source — but since release-plugin is itself one of the files being updated, the simplest path is to update both source and plugin copies in the same commit.

Historical references in `docs/feature-proposals/71-*`, `docs/superpowers/plans/*`, `docs/superpowers/specs/*`, `retrospectives/71-*` and `retrospectives/105-*` are intentionally **not** updated. They captured what was true at the time and rewriting them would erase the history of how the bug got introduced and went undetected.

### Recommendation: regression test (separate follow-on)

Add an end-to-end marketplace install test to the Docker smoke harness in `tests/integration/setup-smoke/`. The test should:

1. Spin up a fresh container with no `.claude/plugins/marketplaces/` cache
2. Run `/plugin marketplace add SteveGJones/ai-first-sdlc-practices` against the local repo (or origin if CI)
3. Verify the marketplace is found and listed
4. Run `/plugin install sdlc-core@ai-first-sdlc`
5. Verify the install succeeded and the plugin is enabled

This is a follow-on issue (not in scope for this fix). The fix here just unblocks users; the test ensures regression prevention.

---

## Success Criteria

- [ ] `.claude-plugin/marketplace.json` exists at the repository root
- [ ] All 11 plugin source paths inside the marketplace.json point to `./plugins/<plugin-name>`
- [ ] All 11 source paths resolve to existing directories
- [ ] `plugins/.claude-plugin/` directory is removed (file deleted from git)
- [ ] `skills/release-plugin/SKILL.md` references the new location
- [ ] `agents/core/pipeline-orchestrator.md` references the new location
- [ ] The plugin copies of both source files (`plugins/sdlc-core/skills/release-plugin/SKILL.md` and `plugins/sdlc-team-common/agents/pipeline-orchestrator.md`) match the source
- [ ] No remaining references to `plugins/.claude-plugin/marketplace.json` in active source files (historical proposals/specs/retros are not touched)
- [ ] Marketplace.json is valid JSON
- [ ] CI passes
- [ ] Pre-push validation passes

---

## Manual verification (post-merge)

After this lands on main, the install path should work for the first time:

```bash
# Clear any stale cache from previous failed attempts
rm -rf ~/.claude/plugins/marketplaces/SteveGJones-ai-first-sdlc-practices

# Try the documented install
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
# Expected: marketplace added, lists 11 plugins

/plugin install sdlc-core@ai-first-sdlc
# Expected: sdlc-core installed and enabled
```

This verification cannot run in CI because CI doesn't run Claude Code commands. It requires a manual check on a fresh client environment after merge.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Existing users who have already cached the broken marketplace at the old path will need to clear their cache | Inconvenience for early adopters who tried and gave up | Document the cache-clear command in the issue and the retrospective |
| The plugin copies of release-plugin and pipeline-orchestrator drift from source if release-plugin is run after manual edit | Potential for the fix to be partially overwritten | Update both source and plugin copies in the same commit; the next release-plugin run will see no diff |
| The historical references in proposals/specs/retros could mislead future contributors looking for the marketplace | Low — anyone reading those docs is reading them as history, not reference | Don't rewrite history; the issue body and the retrospective for this fix capture the fix-at-a-point-in-time |
| Breaking change for anyone who was working around the bug by manually editing `plugins/.claude-plugin/marketplace.json` | Very low — no documented workaround | Issue body documents the fix path clearly |

---

## Out of scope

- Adding the regression test to the Docker smoke harness (filed as a recommendation for a follow-on issue, not in this PR)
- Rewriting historical proposals/specs/retros that reference the old path
- Re-running release-plugin to regenerate every plugin file (the only files that needed updating are touched directly in this fix)
- Adding any new validation rule about marketplace.json location (out of scope; the location is fixed by Claude Code's convention, not by us)

---

## Changes Made

| Action | File |
|--------|------|
| Create | `.claude-plugin/marketplace.json` (with `./plugins/<name>` source paths) |
| Delete | `plugins/.claude-plugin/marketplace.json` (and the directory) |
| Modify | `skills/release-plugin/SKILL.md` (reference the new location) |
| Modify | `plugins/sdlc-core/skills/release-plugin/SKILL.md` (plugin copy) |
| Modify | `agents/core/pipeline-orchestrator.md` (reference the new location) |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` (plugin copy) |
| Create | `docs/feature-proposals/120-marketplace-json-location-fix.md` (this file) |
| Create | `retrospectives/120-marketplace-json-location-fix.md` |

---

## References

- Issue: #120
- Original plugin migration that introduced the bug: PR #73 (#70)
- Subsequent PRs that touched marketplace.json without spotting the bug: #74 (#71), #84 (#82), #86 (#83), #119 (#105)
- Docker smoke test that didn't catch it: #87 (#85)

# Retrospective: Fix #120 — Marketplace JSON Location

**Branch**: `fix/marketplace-json-location`
**Date**: 2026-04-08
**Issue**: #120
**Type**: Critical bug fix

## Context

Steve attempted to install the plugin family on two separate machines and got the same error both times:

```
Error: Marketplace file not found at /Users/<user>/.claude/plugins/marketplaces/SteveGJones-ai-first-sdlc-practices/.claude-plugin/marketplace.json.
```

The marketplace manifest had been at `plugins/.claude-plugin/marketplace.json` since the plugin family launched in #73, but Claude Code's marketplace add command looks for `.claude-plugin/marketplace.json` at the **repository root**. The documented public install path had never worked. The bug went undetected for ~3 weeks across four EPICs that all touched the marketplace.json file without anyone noticing.

## What Went Well

- **Steve identified the defect immediately and gave a clear reproduction.** Two separate machines, the exact error message pasted in chat. No ambiguity about what was broken.
- **The fix was structurally simple once identified.** Move one file, update the source paths inside it, update two source references, delete the old location. About a dozen file operations total.
- **All eleven plugin source paths verified to resolve.** A quick `for d in plugins/sdlc-*; do test -d "$d" && echo OK; done` confirmed the new `./plugins/<name>` paths land on existing directories before commit.
- **The plugin copies of source files were updated in the same commit as the source.** Normally release-plugin regenerates the plugin copies from source, but since release-plugin is itself one of the files being updated, doing both in one commit avoids a chicken-and-egg state.
- **Historical references intentionally preserved.** The proposals, specs, and retrospectives from #71 and #105 still reference `plugins/.claude-plugin/marketplace.json`. They captured what was true at the time and rewriting them would erase the history of how the bug went undetected. The active source files are the only ones updated.

## What Could Improve

- **The bug existed for ~3 weeks across four merged EPICs.** PRs #73, #74, #84, #86, and #119 all touched marketplace.json. None of them caught it because none of them tested the marketplace add path against a fresh client environment. This is a process gap as much as a code gap.
- **CI doesn't and can't test `/plugin marketplace add` directly.** GitHub Actions runs validators against file contents, not Claude Code commands. The Docker smoke test (#85) tests plugin install but uses the project-scoped install path, not marketplace add. There's no automated check for "does the marketplace install path actually work" anywhere in the framework.
- **The original plugin migration design (#70 spec) explicitly placed the marketplace.json at `plugins/.claude-plugin/`.** I checked the spec — the design diagram literally shows `plugins/.claude-plugin/marketplace.json` as "Family marketplace". This was an authoring error in the original design that propagated through every subsequent change without anyone questioning it. Lesson: when adopting an external convention (Claude Code's marketplace discovery), reference the actual upstream documentation rather than inferring the layout from analogies.
- **No human had tried the public install path on a fresh machine.** Everyone working on the framework already had the plugins symlinked into `.claude/` via `scripts/setup-dev-environment.sh`. The dogfooding gap was: developers used the dev path; only end users would hit the marketplace path; no end users existed yet because the plugin family was still being built.
- **The fix's manual verification cannot be automated.** I've documented the post-merge verification steps in the feature proposal, but they require Steve (or another user) to actually run the commands on a fresh client. The fix lands; verification happens out-of-band.

## Lessons Learned

1. **External convention bugs are silent killers.** When adopting a tool's convention (Claude Code marketplace discovery, in this case), reference the actual upstream documentation explicitly in the design doc with a citation. "We assume the marketplace lives at `plugins/.claude-plugin/`" with no source citation is exactly the kind of unchecked assumption that breaks everything for everyone, silently.

2. **Internal dev paths can hide bugs in the public path.** Dogfooding via `scripts/setup-dev-environment.sh` worked perfectly and gave us false confidence. The setup script bypassed the marketplace add step entirely. Lesson: always run the documented public install path at least once on a fresh client during PR review for any plugin-touching change. "Dev path works" ≠ "user path works."

3. **Bugs that span multiple PRs need their own discovery moment.** This bug existed in #73, was unchanged in #74, #84, #86, and #119. Each PR added something to marketplace.json, none of them questioned where it lived. The discovery moment was when Steve actually tried to install the plugin on a clean machine. That moment should have happened at the end of #73, not weeks later. Add "verify install on a fresh client" to the plugin-PR checklist.

4. **Don't rewrite history when fixing structural bugs.** The old proposals and retrospectives reference the broken path. They should stay as-is. Future contributors reading the history need to know the bug existed and how it slipped through. Rewriting those docs would erase the institutional memory of the failure mode.

5. **Critical fixes deserve their own focused branch and PR.** Bundling this with EPIC #97 work would have buried it in unrelated commits and slowed the fix. A standalone fix branch (this one) gets the change in front of reviewers immediately and lets the regression test work happen as a separate follow-on without coupling.

## Changes Made

| Action | File | Change |
|---|---|---|
| Create | `.claude-plugin/marketplace.json` | New marketplace manifest at the repo root with `./plugins/<name>` source paths for all 11 plugins |
| Delete | `plugins/.claude-plugin/marketplace.json` | Remove the old wrong-location manifest |
| Modify | `skills/release-plugin/SKILL.md` | Update the version-bump step to reference `.claude-plugin/marketplace.json` (at the repo root) |
| Modify | `plugins/sdlc-core/skills/release-plugin/SKILL.md` | Plugin copy of release-plugin updated to match source |
| Modify | `agents/core/pipeline-orchestrator.md` | Update the 1st-party plugin marketplace search to reference the new location |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Plugin copy of pipeline-orchestrator updated to match source |
| Create | `docs/feature-proposals/120-marketplace-json-location-fix.md` | Feature proposal documenting the defect and the fix |
| Create | `retrospectives/120-marketplace-json-location-fix.md` | This file |

## Follow-on issues

1. **Add marketplace install regression test.** Extend the Docker smoke test (`tests/integration/setup-smoke/`) to actually run `/plugin marketplace add SteveGJones/ai-first-sdlc-practices` against the local repo (or origin in CI) and verify it succeeds. This is the test that would have caught the bug at PR time. File as a new issue after this fix merges.

2. **Plugin-PR checklist update.** Add "verified marketplace install on a fresh client environment" to the checklist for any PR that touches `marketplace.json` or plugin layout. Add to `CONTRIBUTING.md`.

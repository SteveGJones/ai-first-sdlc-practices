# Retrospective: Fix #137 — sdlc-knowledge-base Empty Plugin + Slash Command References + Packaging Validator

**Branch**: `fix/kb-plugin-packaging-and-references`
**Date**: 2026-04-08
**Issue**: #137
**Type**: Critical bug fix + preventive infrastructure
**Context**: fifth discovery-related bug pattern fix in two sessions; this is the one that finally produced a structural check

## Context

Steve asked how to run the `kb-init` skill. I gave the wrong invocation (`/sdlc-core:kb-init`) and then caught myself — the plugin is `sdlc-knowledge-base`, not `sdlc-core`, so the correct invocation is `/sdlc-knowledge-base:kb-init`. That triggered a discovery that I'd been writing `/sdlc-core:kb-*` everywhere throughout EPIC #105 — in the skill bodies, the starter pack files, the CLAUDE.md template that gets installed into user projects, the plugin README, CLAUDE.md itself.

Then Steve reported that `plugins/sdlc-knowledge-base/` was empty on a fresh machine (issue #137 from his team). Investigation revealed the actual scope of the bug: the plugin directory only had the manifest and README. All 2 agents + 15 skill/template files from EPIC #105 existed in source but had never been copied to the plugin directory, because `release-plugin` was never run during the EPIC's twelve sub-features. The plugin shipped to main completely non-functional.

And then, when I wrote a validator to check the sdlc-knowledge-base packaging, running it against the whole repo revealed nine additional pre-existing drifts across five other plugins — source and plugin copies silently out of sync from work done before this session even started.

This is the fifth instance of "user-facing path bug pattern" in two sessions (after #120, #122, #124, #129), and the first one that finally produced a structural check rather than another point fix.

## What Went Well

- **Steve's question exposed the bug immediately.** "How do I run the kb-init skill?" is an innocuous question, but the answer required me to look at the plugin name, which is where I caught the slash command mistake, which led to investigating the plugin directory state, which exposed the empty plugin. One natural question; full cascade of findings.
- **The validator surfaced drift I wasn't looking for.** I wrote `check-plugin-packaging.py` specifically to catch the sdlc-knowledge-base case. Running it for the first time found nine additional drifts in five other plugins. That's exactly what a structural check is supposed to do — catch the bugs you didn't know existed.
- **The fix + prevention were bundled into one PR.** Every previous discovery fix (#120, #122, #124, #129) was "fix the specific bug" without adding structural prevention. This PR fixes the specific bug AND adds the check that would have caught it AND fixes the nine other silent drifts AND documents the lesson in CONTRIBUTING.md AND saves it as a feedback memory. The cumulative prevention is significant.
- **The constitution-sync.yml pattern (#93) was a clear precedent.** I didn't have to invent a new CI workflow shape. Constitution-sync already solved the same problem for a narrow case (`CONSTITUTION.md` ↔ its plugin copy); this PR generalises it to all source-to-plugin sync. Same structure, same failure message pattern, same path-filter approach. Consistency compounds.
- **The validator is language-agnostic and reads release-mapping.yaml directly.** No hardcoded plugin list, no hardcoded file paths. If a new plugin is added to release-mapping.yaml, the validator checks it automatically. If a plugin is removed, the validator no longer checks it. The check evolves with the repo without any maintenance.
- **Historical references intentionally preserved.** Retrospectives, feature proposals, and EPIC issue comments from this session (and earlier) still reference `/sdlc-core:kb-*`. Rewriting them would erase how the bug got introduced and where it was discovered. The fix goes in the files consumers actually read, not in the institutional memory. Same lesson as #120, #122, #124, #129 — consistent pattern across all the fix cycles.

## What Could Improve

- **This bug existed since EPIC #105 merged on 2026-04-08 morning.** The plugin shipped empty for roughly 12 hours before Steve's team hit it on a fresh machine. The #128 review mandated user-path verification on a fresh client before merge, but the rule hasn't been authored into the Constitution yet (#132 is filed but not done) and there's no automated enforcement yet (#134 is filed but not done). #137 is the kind of bug those two issues are designed to prevent — and they would have if they'd landed before EPIC #105 merged.
- **Nine pre-existing drifts had been sitting in main invisible.** That's not a new bug; that's a nine-month-old accumulation of work where people (including me earlier today) updated source files and forgot to sync the plugin copies. Without this validator, we'd have kept shipping silently-drifted plugin copies indefinitely. Every time a user installs a plugin, they'd be getting a stale version. The validator's first run is essentially a "clean up the accumulated debt and prevent new debt" moment.
- **I can't verify the plugin actually works end-to-end without a fresh client.** This session can populate the plugin directory and confirm the validator passes, but verifying that `/plugin install sdlc-knowledge-base@ai-first-sdlc` on a fresh machine actually produces a functional plugin requires a fresh environment I don't have access to. Post-merge verification by Steve on a fresh machine is essential.
- **The `[Knowledge Base]` CLAUDE.md template is installed into user projects.** Any user who already ran `/sdlc-knowledge-base:kb-init --with-starter-pack` (if they somehow did — the skill wasn't actually installed, but speculatively) would have the wrong `/sdlc-core:kb-*` references in their project's CLAUDE.md. This PR fixes the template for future installs, but existing installs stay broken until the user re-runs kb-init or manually updates their CLAUDE.md. Worth calling out in a migration note if the bug ever went live.
- **I made the slash command mistake in the first place because I didn't test the skill invocation.** All through EPIC #105, I wrote `/sdlc-core:kb-init` without ever actually invoking it to check whether Claude Code would recognize it. The mistake would have been caught by a single `/sdlc-knowledge-base:kb-init` vs `/sdlc-core:kb-init` trial. Same pattern as the previous four discovery bugs: "wrote it, shipped it, didn't exercise it."

## Lessons Learned

1. **"How do I run this?" is a test question in disguise.** When a user asks how to invoke something, the answer exposes the bug if there is one. Anytime I write documentation or instructions for how to run something, I should mentally rehearse the answer "if the user asked me how to run this right now, could I give them a correct answer without looking up the plugin name?" Most of the time I've been assuming the plugin name without checking.

2. **A manifest is not a sync.** `release-mapping.yaml` describes what *should* be in each plugin, but nothing actively copies files unless `release-plugin` is explicitly run. Adding a file to the manifest is only half the work — the other half is actually running the skill that packages it. Every future EPIC that touches `release-mapping.yaml` should end with a "run release-plugin + verify with the validator" step. Now that the validator exists, the verification step is automatic in CI.

3. **Write the structural check when you find the second instance of a pattern.** I wrote five point fixes (#120, #122, #124, #129, #137) before building a structural check. Writing the validator after the first or second fix would have caught the third and fourth at PR time and saved the effort of the fourth and fifth. Lesson: when the same pattern recurs, stop fixing instances and build the check. Don't wait for a fifth instance.

4. **"Pre-existing drift" is a silent liability multiplier.** The nine drifts I found were all pre-existing — work done weeks or months before this session. They had been sitting in main invisible, shipping to every user who installed a plugin. Without a check, every edit to a source file that misses its plugin copy adds to the liability. With a check, the liability is paid down to zero at PR time and stays there.

5. **The "pre-Article 12" user-path verification template is already paying off.** This PR includes a structured verification block in the description even though Article 12 isn't authored yet. Writing it forces me to articulate the limitation ("N/A with limitation — in-session tool constraint") and the post-merge recommendation explicitly. That's better than silently skipping verification, even when full verification isn't possible. The pattern is strong enough that I should keep using it until Article 12 lands and makes it mandatory.

6. **CONTRIBUTING.md is underused for enforcement discoverability.** Both #93 (constitution sync) and this PR add CI checks that contributors need to know about. The CI error message explains what to do if they hit the failure, but ideally contributors would read CONTRIBUTING.md first and avoid the failure entirely. Adding a short section explaining each check makes it discoverable without requiring a failure to trigger it. Worth doing this consistently for every new check.

## Changes Made

| Action | File | Change |
|---|---|---|
| Create | 17 files under `plugins/sdlc-knowledge-base/` | Populate the empty plugin directory per release-mapping.yaml |
| Modify | Multiple `skills/kb-*/`, `plugins/sdlc-knowledge-base/**`, `agents/knowledge-base/agent-knowledge-updater.md`, `CLAUDE.md` | Replace `/sdlc-core:kb-*` with `/sdlc-knowledge-base:kb-*` throughout active (non-historical) files |
| Create | `tools/validation/check-plugin-packaging.py` | Structural validator: reads release-mapping.yaml, verifies every source file has a matching plugin copy |
| Create | `.github/workflows/plugin-packaging-sync.yml` | CI workflow that runs the validator on every PR touching plugin-related paths |
| Modify | 9 files under `plugins/` | Resync pre-existing drifts so the validator passes on the full repo |
| Modify | `CONTRIBUTING.md` | New subsection documenting the plugin packaging sync check and failure mode |
| Create | Memory file `feedback_release_plugin_sync.md` (outside git) | Captures the lesson for future sessions |
| Modify | `MEMORY.md` (outside git) | References the new memory file |
| Create | `docs/feature-proposals/137-kb-plugin-packaging-and-references.md` | Feature proposal |
| Create | `retrospectives/137-kb-plugin-packaging-and-references.md` | This file |

## Follow-on considerations (notes, not new issues)

- **Post-merge manual verification by Steve.** Needs to run `/plugin marketplace update ai-first-sdlc` + `/plugin install sdlc-knowledge-base@ai-first-sdlc` on a fresh client and confirm the plugin is actually functional. Any gaps are new fix issues.
- **Consider adding `check-plugin-packaging.py` to `local-validation.py --pre-push`.** The CI check catches drift at PR time; a pre-push hook would catch it before the push even happens. Contributor experience improvement; trade-off is adding ~1 second to the pre-push run. Not in scope for this PR.
- **`release-plugin` could auto-run on pre-commit.** A git hook that runs `release-plugin` automatically when `release-mapping.yaml` or any source file with a plugin copy changes would eliminate the manual step entirely. Design question: auto-sync vs manual-sync-with-check. For now, manual with the new check is the safer choice because it's explicit; auto-sync could mask other issues. Revisit if the manual approach keeps producing misses.
- **Issue #133 (test harness convention) should add a test that runs `check-plugin-packaging.py` as part of the user-path test suite.** The validator is a user-path test for "can the user install this plugin at all." Worth adding to the test harness as a categorised check.

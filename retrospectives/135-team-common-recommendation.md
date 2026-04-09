# Retrospective: Fix #135 — sdlc-team-common Near-Universal Recommendation

**Branch**: `fix/team-common-recommendation`
**Date**: 2026-04-08
**Issue**: #135
**Type**: Enhancement

## Context

Steve asked where `pipeline-orchestrator`, `deep-research-agent`, and `agent-builder` live in the plugin family. Answer: they're in `sdlc-team-common`, not `sdlc-core`. He agreed with the placement but pointed out they should be **almost always recommended** and **always recommended when custom agents are suggested** (i.e., when discovery's Section C has entries).

The framing revealed a real implicit dependency: `setup-team`'s discovery step runs via `pipeline-orchestrator`, and Section C of the discovery output tells users to `@pipeline-orchestrator create a <topic> agent` — but nothing checks whether team-common is actually installed. A user who runs option F (Custom) without team-common and then has Section C gaps will be told to use agents that don't exist.

## What Went Well

- **The fix shape was clear from the ask.** Steve's "almost always recommended, always required for Section C" maps cleanly onto a near-universal default (★ marker) plus an escalation step (5e). No design exploration needed — the policy was specified.
- **Consistent pattern with recent fixes.** The MANDATORY-with-fallback pattern from #124 (install field) and the three-section structure from #124/#129 are reused here: team-common gets a prominent marker, a clear default, and an escalation rule. Pattern reuse makes the codebase coherent.
- **Good citizenship ahead of Constitution Article 12.** This PR touches user-facing surfaces (`setup-team`, `pipeline-orchestrator`) and includes a user-path verification block in the PR description even though Article 12 isn't authored yet (#132). Starting to live by the rule before it's mandatory.
- **Source + plugin copies updated in the same commit.** Consistent with the lesson from #120, #122, #124, #129. No drift between source and shipped plugin.
- **No new categories or concepts invented.** The fix reuses the existing Section A/B/C structure and the existing plugin family taxonomy. The only new thing is the `★` marker for "universal default."

## What Could Improve

- **The verification is structural, not live.** This session can't run `/sdlc-core:setup-team` against a fresh project because the skill requires interactive Claude Code invocation in a new session, not the one currently running the skill. The PR description documents this limitation honestly and flags the manual check for post-merge. But it's not a full user-path verification per the rule from #128 — it's the first instance of the "N/A with limitation" exemption the rule allows for, and worth watching to see whether that exemption gets abused.
- **The escalation block prompt (5e) is text-only.** The user sees a warning and chooses 1/2/3. There's no automatic plugin install on selecting option 1 — the user still has to run `/plugin install sdlc-team-common@ai-first-sdlc` themselves after confirming. Setup-team produces install commands for the user to run; it doesn't install on their behalf. That's consistent with existing framework behaviour but it means the escalation is advisory-at-block, not automated enforcement. Flagged here because the block is only as strong as the user's willingness to follow the instructions.
- **No automated test for the escalation behaviour.** Section C gap count > 0 triggering the required mark is a logic branch that should be tested. This would fall under #126 (automated discovery output testing, extended scope per #128) and #133 (test harness convention). For now, the escalation is documented but not automatically verified.
- **The `★` marker is new and might confuse users expecting the standard `✓` / `○` pattern.** The skill body documents it inline (`★ = universal default; ✓ = always installed; ○ = optional/selected`) but a user scanning the output for the first time might miss the marker key. If feedback shows confusion, simplify to two markers or move team-common under the `✓` (always installed) bucket with a note that it's technically separable.

## Lessons Learned

1. **Implicit dependencies between plugins surface as user-facing path bugs.** The dependency between `setup-team`'s discovery output and the agents in `sdlc-team-common` was never explicit in the framework's documentation or code. It took Steve asking "what plugin are they part of?" to expose that a user could end up with discovery recommendations they couldn't act on. Lesson: when skill A invokes agent B, the plugin containing A should declare the plugin containing B as a dependency somewhere the user can see — not just in the developer's head.

2. **Near-universal defaults need visible markers.** Making team-common "recommended" in the documentation does nothing if the recommendation output doesn't visually distinguish it from optional plugins. The `★` marker does the work that text descriptions couldn't.

3. **Escalation patterns work across domains.** The "required for X condition" pattern is identical to the Section C / Section A mandatory-install-field pattern from #124. Same shape, different content. When a user's choices create an implicit requirement, the skill should detect and enforce it, not silently fail later.

4. **User-path verification has edge cases the rule needs to handle.** This PR is the first test of "the skill I'm modifying requires interactive invocation I can't produce from inside the session where I'm modifying it." The verification block uses "N/A with limitation" but the rule from #128 doesn't formally list this as an exemption. Worth surfacing when Article 12 (#132) is authored — there should be an explicit carve-out for "in-session tool limitation" with a documented post-merge verification requirement.

## Changes Made

| Action | File | Change |
|---|---|---|
| Modify | `skills/setup-team/SKILL.md` | Updated step 3 (project types table + team-common rationale + option F warning), added step 5e (escalation when Section C gaps exist), updated step 7 recommendation output (★ marker + agent list), updated Section C prerequisite note |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` | Plugin copy updated to match source |
| Modify | `agents/core/pipeline-orchestrator.md` | Added prerequisite paragraph at top of Section C in report template (discovery output seen by users invoking pipeline-orchestrator directly) |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Plugin copy updated to match source |
| Create | `docs/feature-proposals/135-team-common-recommendation.md` | Feature proposal |
| Create | `retrospectives/135-team-common-recommendation.md` | This file |

## Follow-on considerations (not new issues, just notes)

- **When Article 12 lands (#132)**, revisit whether "in-session tool limitation" should be added as an explicit exemption in section 12.5. This PR's verification was honest about the limitation but technically exercises a gap in the rule.
- **When the test harness convention lands (#133)**, add a test at `tests/user-path/setup-team-escalation/` that mocks a discovery output with Section C gaps and verifies the escalation step kicks in correctly. This is a natural extension of the Section C behaviour tests.
- **Commissioning (EPIC #97) will inherit this pattern.** When sub-feature 2 (Single-team bundle) or sub-feature 3 (Solo bundle) lands, the commission skill should apply the same near-universal default + escalation pattern for whatever plugins are required for the chosen option. The `★` marker convention should propagate.

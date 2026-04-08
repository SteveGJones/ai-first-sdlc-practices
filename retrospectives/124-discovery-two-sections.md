# Retrospective: Fix #124 — Discovery Output Two Sections + Mandatory Install

**Branch**: `fix/discovery-two-sections`
**Date**: 2026-04-08
**Issue**: #124
**Type**: Bug fix (follow-up to #122/#123)
**Session**: third discovery-related fix in one day (after #120 and #122)

## Context

Steve updated the marketplace, reloaded plugins, and ran discovery to verify the #123 fix. Two problems surfaced:

1. The install instructions were still missing from the normal discovery flow — he had to ask explicitly
2. The tool recommendations mixed Claude Code environment tools with project libraries (`@modelcontextprotocol/sdk` etc.) without distinguishing them

Both problems were real and both were caused by the #122/#123 fix being incomplete. The install-instructions fix used descriptive template language ("every tool gets an install instruction") that an agent under pressure could skip. The category taxonomy included `library-framework` but kept it in the same output section as the others, so the distinction between "install in Claude Code" and "add to your project's package.json" was invisible.

## What Went Well

- **Steve's verification caught both defects immediately.** The manual post-merge verification path we flagged in #122's retrospective (the "run the user path on a fresh client" process gap) caught this right on the next iteration. That's exactly how it's supposed to work when the gap is closed.
- **Both defects had the same root cause at different levels.** The instructions for the agent weren't prescriptive enough (Install field skipped) and the output structure conflated different user actions (Section A vs Section B). Both are instances of "the agent's instructions describe shape but not rules." The fix applies prescriptive rules to both.
- **The Section A / Section B split surfaced naturally.** Once Steve framed it as "Claude elements vs project libraries", the split was obvious and the existing seven-category taxonomy maps cleanly: six categories go to Section A, one goes to Section B. No new categories needed.
- **Concrete examples in the agent body are more effective than rules.** I added the `@modelcontextprotocol/server-filesystem` vs `@modelcontextprotocol/sdk` distinction as a concrete example, not just a rule. Agents (and humans reading the agent file) can pattern-match on "is this like X or like Y?" faster than they can apply abstract classification criteria.
- **The MANDATORY framing with an explicit fallback is a better pattern than just saying "every tool should have".** The difference between:
  - Before: "Every tool gets an install instruction" (descriptive, skippable)
  - After: "You MUST populate the Install field. If you cannot determine the install path, write exactly: `Manual setup required. See <url>/README.md.` — never omit the field." (mandatory, with defined fallback)
  The fallback removes the agent's excuse for skipping.

## What Could Improve

- **The #122 fix should have been this fix.** Both problems were knowable at #122 time if I'd pushed harder on the "make it prescriptive" angle and thought about whether libraries belonged in the same list as Claude Code tools. I fixed the symptom (add an install column) without fully understanding the shape (what kinds of tools need what kinds of install instructions). Lesson: when fixing an output-format bug, check whether the output *structure* also has problems, not just missing fields.
- **Still no automated test for discovery output.** Both #122 and #124 are bugs that would be caught by an automated test that runs discovery on a known tech stack and verifies the output format (sections present, install fields populated, categories classified correctly). We keep saying "add this as a follow-on issue" and then not filing it. After this fix lands, actually file it.
- **Three fixes in one day on the same surface suggests the original discovery design needed more thought.** #120 (marketplace location), #122 (install instructions missing), #124 (install still missing + sections mixed) — all in ~24 hours, all on the onboarding/setup path. The discovery agent and setup-team skill are core to user onboarding and they had three serious defects that shipped undetected across multiple EPICs. A design review of this surface area would be valuable. Not doing it now because we're in mid-session fix mode, but it should be the follow-on after this.
- **The retrospective pattern is becoming "file follow-on issues in retros, never get to them."** Both #122 and now #124 flag the same follow-ons: (a) automated discovery output testing, (b) PR review checklist for user-facing paths, (c) design review of onboarding surface. None of these got filed as real issues after #122. If I don't file them at the end of #124, the pattern repeats.
- **The MANDATORY emphasis in markdown is a hope, not a guarantee.** Writing "**MANDATORY**" in the agent file doesn't literally force the agent to follow it — agents interpret markdown emphasis semantically, not structurally. If the agent still skips the Install field after this fix, the next escalation is either (a) a structural check in a wrapper skill that refuses to return discovery output without an Install field per tool, or (b) a specific adversarial test that runs after discovery and verifies the output shape. I'm documenting this as a known residual risk.

## Lessons Learned

1. **Prescriptive rules beat descriptive templates.** When an agent's instructions describe what good output looks like ("every tool gets an install instruction"), the agent treats that as aspirational. When the instructions mandate an explicit check ("verify every tool has an Install field; if missing, regenerate"), the agent treats it as a rule. The difference is the checklist phrasing — something the agent can evaluate as a yes/no gate before presenting.

2. **Output structure is part of the bug, not just output content.** When fixing an output format defect, ask two questions: (a) is the output missing information? and (b) is the output conflating different things that should be separated? #122 only fixed (a). #124 had to fix (b) as well. Next time, check both up front.

3. **Concrete examples in agent files are more effective than abstract rules.** The `@modelcontextprotocol/server-filesystem` (pre-built server → Section A) vs `@modelcontextprotocol/sdk` (library for building → Section B) example does more work than the rule table. Agents pattern-match on examples faster than they apply classification criteria. Include a concrete example for any non-obvious distinction.

4. **Mandatory fallbacks remove the agent's excuse to skip.** "Never omit the field. If you don't know, write this exact string." leaves no room for "well I couldn't find the install command so I left it out". The fallback ("Manual setup required, see README") is always applicable and always trivially available. The agent cannot claim it didn't know what to do.

5. **Three fixes in one day on the same surface is a design signal.** If we're fixing the same surface repeatedly in a short window, the original design isn't holding up. Either the requirements were incomplete or the implementation shortcut the structure. Discovery is clearly in this state. After this fix stabilises, a focused design review of discovery + setup-team + onboarding is warranted.

6. **Retrospectives that file follow-on work need to actually file the follow-on work.** I've now flagged "add automated discovery output tests" as a follow-on in two retrospectives without actually filing the issue. The pattern is self-defeating. At the end of this fix, file the issues immediately, not later.

## Changes Made

| Action | File | Change |
|---|---|---|
| Modify | `agents/core/pipeline-orchestrator.md` | Two-section report structure, mandatory Install field with fallback, `library-framework` → Section B, concrete `mcp-server-npm` vs `library-framework` example, updated frontmatter example showing both sections populated |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Plugin copy of pipeline-orchestrator updated to match source |
| Modify | `skills/setup-team/SKILL.md` | Two-section classification rules in step 5c, two-section output format in step 7 with mandatory Install field |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` | Plugin copy of setup-team updated to match source |
| Create | `docs/feature-proposals/124-discovery-two-sections.md` | Feature proposal |
| Create | `retrospectives/124-discovery-two-sections.md` | This file |

## Follow-on issues (FILE THESE IMMEDIATELY after merge)

1. **Automated discovery output testing.** Extend the Docker smoke test or add a new test that runs discovery on a known tech stack (e.g., MongoDB, which has both a pre-built MCP server and a well-known client library) and verifies the output shape: Section A and B headings present, Install field populated per tool, `library-framework` items in Section B. Would have caught all three of #120, #122, and #124. **Must file after merge, not leave as a retrospective note.**

2. **PR review checklist for user-facing paths.** Update `CONTRIBUTING.md` with a required check: "For any PR that touches discovery, setup-team, commissioning, or install paths, the reviewer MUST manually run the user-facing path on a fresh client and verify the output is actionable." Makes the verification gap explicit.

3. **Design review of onboarding surface.** Three fixes on the same surface in one day is a design signal. File an issue to do a focused review of the discovery + setup-team + install path, looking for structural problems rather than point fixes.

4. **Eighth tool category: hosted SaaS APIs.** Flagged in #122's retrospective, still not filed. Tools like "set $STRIPE_API_KEY and use the API directly" don't fit any of the seven categories cleanly. A `saas-api` category with a "no install, set env var, see docs" template would cover these.

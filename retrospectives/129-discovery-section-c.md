# Retrospective: Fix #129 — Discovery Section C (Coverage Gaps)

**Branch**: `fix/discovery-section-c`
**Date**: 2026-04-08
**Issue**: #129
**Type**: Enhancement (follow-up to #124)
**Session**: fourth discovery-related change in one day

## Context

Fresh on the heels of #124 (which introduced Sections A and B), Steve pointed out the missing third section: "There should be a section C which is then doing specific research to create project specific agents for those topics, which should be a choice the user can make."

He was right. #124 split the output into "install off-the-shelf tools" (Section A) and "add libraries to your own project" (Section B), but left the "there's no good off-the-shelf tool, would a custom agent be worth building?" case as a vague end-of-report "(c) Build custom" choice. That framing is whole-report rather than per-topic, and the user has to reason about which topics actually need custom agents themselves.

Section C makes custom agent creation a first-class per-topic decision. For each topic where discovery found no adequate coverage, Section C presents a specific gap entry with five mandatory fields (why / what the agent would know / research scope / duration / create command) and lets the user opt in per gap. Selected gaps route back into the pipeline-orchestrator's existing research → synthesis → agent-builder flow.

## What Went Well

- **Steve spotted the gap immediately after #124 merged.** One user-path run through discovery surfaced the structural problem. This is exactly how the "manually verify user-facing paths" discipline is supposed to work (even though we haven't formally adopted the process change yet — that's #127).
- **Section C maps cleanly onto infrastructure that already existed.** The pipeline-orchestrator's core workflow is research → synthesis → agent-builder. That's precisely what Section C offers per gap. No new infrastructure needed; we just surface an existing capability in the discovery output as an explicit option.
- **The coverage → Section C mapping (High/Medium/Low) is simple and defensible.** High coverage = no Section C entry, Medium = optional, Low = recommended. Three cases, obvious signals, no ambiguity. Compare to some taxonomies I've written recently that need much more detail to resolve edge cases.
- **Per-section decisions are cleaner than one whole-report choice.** The old (a)/(b)/(c) framing forced the user to pick a single strategy across the whole discovery. The new per-section flow lets them install some tools, note some libraries, and commission some custom agents — all in one discovery. Matches how real projects actually work.
- **Mandatory five fields per Section C entry echoes the mandatory Install field from #124.** Same prescriptive pattern: explicit required fields, explicit fallback ("omit the entry if you can't justify it"), no wiggle room for vague output.
- **The fix used the concrete MongoDB example as a dry run.** The example in the frontmatter shows @mongodb/mcp-server in Section A (operational tool), mongodb driver in Section B (project library), and "MongoDB schema design patterns" in Section C (architectural expertise the MCP server doesn't provide). The three-section structure is immediately legible from the example.

## What Could Improve

- **This is the fourth discovery fix in one day.** #120 (marketplace location), #122 (install instructions), #124 (two sections + mandatory install), #129 (Section C). Each fix was correct but incomplete. The cumulative pattern is: discovery was under-designed and we keep discovering new gaps as users actually try to use it. The design review (#128) is now overdue.
- **The old step 9 "three options" framing has been in the pipeline-orchestrator since #82 (agent discovery).** It survived four EPICs and didn't match how users actually make decisions. Lesson: abstract UX decisions like "present N options to the user" need testing against real user workflows, not just designing in the abstract. The three-option framing looked clean on paper and was wrong in practice.
- **No automated verification that Section C entries actually have all five fields.** This is the same gap as #124's "install field might still be skipped" — we rely on the agent following the MANDATORY directive, but nothing structurally enforces it. #126 (automated discovery output testing) would catch missing Section C fields but it's not filed as work yet, just as an issue.
- **Setup-team's Section C is informational-only and points at pipeline-orchestrator for agent creation.** This is the right responsibility boundary but it creates a context handoff: the user reads setup-team's output, closes setup-team, then runs a separate pipeline-orchestrator command with the gap's topic slug. In practice users might forget to come back and fill the gap later. A future improvement: setup-team could offer to *schedule* the agent creation as a task to do during project work, or chain directly to pipeline-orchestrator with the selected gaps if the user confirms.
- **The Section C example is MongoDB, which already has Section A coverage (the official MCP server).** I used MongoDB because it's a good Section A/B example, and added a plausible schema-design gap as the Section C entry. A more compelling example would be a technology with *no* Section A — something specialised where Section C is the only sensible next step. Edge cases in the example should be clearer.
- **The fourth fix in a day suggests I'm iterating on symptoms without addressing the design.** Each fix is narrow and correct. None of them stepped back to ask "what should discovery actually look like as a complete design?" That's what #128 is for, but I keep deferring it in favor of point fixes.

## Lessons Learned

1. **Every fix should check whether it completes the surface or just extends a pattern that still has gaps.** #124 added Sections A and B but didn't ask "is two sections enough?" The answer was no — Section C was missing and should have been part of #124. Lesson for next time: when fixing an output format, walk through every plausible user intent and ask whether the format supports it.

2. **Surface existing capabilities as explicit options rather than hiding them behind vague choices.** The pipeline-orchestrator could already do research-driven agent creation — the capability existed. The old (c) option mentioned it but didn't say what would happen or when it'd be worth it. Section C turns that existing capability into a visible, decidable option with concrete fields. The principle generalises: if you have a capability users would benefit from, make it visible in the output at the point of decision, not hidden behind a menu item.

3. **Per-item decisions beat whole-report decisions when the items are independent.** The old "(a) use as-is, (b) hybrid, (c) custom" forced one choice across potentially dozens of tools. Per-section + per-tool/per-gap decisions let the user make good choices on each item without bundling. Same principle as "configurable components" in the knowledge base pattern from #105.

4. **Four fixes on the same surface in one day is an invitation to do the design review.** I keep filing it as a follow-on and keep not doing it. After this PR merges, if discovery needs a fifth fix, I need to stop and do #128 first. Otherwise the pattern repeats indefinitely.

5. **Mandatory-field patterns from one fix carry forward.** #124 established MANDATORY phrasing for the Install field. #129 uses the same pattern for Section C's five fields. The agent is learning a general rule: "fields marked MANDATORY have a defined fallback and cannot be omitted." Consistency compounds.

## Changes Made

| Action | File | Change |
|---|---|---|
| Modify | `agents/core/pipeline-orchestrator.md` | Added Section C definition (step 7), coverage-to-C mapping and Section C field requirements (step 8), updated report template (step 9), replaced three-option framing with per-section decisions (step 10), added Section C routing to research pipeline (step 11), renumbered subsequent steps, updated frontmatter example with all three sections populated |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Plugin copy updated to match source |
| Modify | `skills/setup-team/SKILL.md` | Added Section C to recommendation output format; Section C is informational-only in setup-team (points at pipeline-orchestrator for agent creation) |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` | Plugin copy updated to match source |
| Create | `docs/feature-proposals/129-discovery-section-c.md` | Feature proposal |
| Create | `retrospectives/129-discovery-section-c.md` | This file |

## Follow-on issues

None new. The outstanding follow-on work from #124 still applies:

1. **#126** — Automated discovery output testing (should now verify Section C structure too)
2. **#127** — PR review checklist update for user-facing paths
3. **#128** — Design review of onboarding surface (now overdue — four fixes in one day is well past the "design signal" threshold)

If this Section C fix lands and discovery needs a fifth correction, I'm stopping and doing #128 before any more point fixes.

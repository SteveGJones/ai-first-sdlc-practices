# Feature Proposal: sdlc-team-common Near-Universal Recommendation + Section C Escalation

**Proposal Number:** 135
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `fix/team-common-recommendation`
**Issue:** #135
**Type:** Enhancement

---

## Executive Summary

`sdlc-team-common` contains the research-and-agent-creation pipeline (`pipeline-orchestrator`, `deep-research-agent`, `agent-builder`, `repo-knowledge-distiller`) plus cross-cutting specialists. Today, `setup-team` recommends it for project types A-E but option F (Custom) allows the user to deselect it without warning, and there's no enforcement when discovery identifies Section C coverage gaps that require these agents to act on.

This proposal makes `sdlc-team-common` a **near-universal default** that every project gets unless explicitly opted out with a warning, and **escalates it to required** when discovery identifies Section C gaps. The pipeline-orchestrator's Section C output also gains a prerequisite note explaining the dependency, so users who invoke discovery directly see the same information.

---

## Motivation

### Problem statement

Today's `setup-team` flow:

1. Project types A-E include `sdlc-team-common` in their recommended plugin list — it's always there, but framed as part of the bundle rather than called out
2. Option F (Custom) lets the user pick plugins freely — no default, no warning if team-common is excluded
3. When discovery (step 5c) identifies Section C gaps (topics needing custom agents), the output tells the user to run `@pipeline-orchestrator create a <topic> agent` — but nothing checks whether team-common is actually in the user's plugin selection
4. A user who runs option F without team-common and then has Section C gaps in their discovery output will be told to use agents that aren't installed

Meanwhile, `pipeline-orchestrator`'s discovery output (when run directly, not via `setup-team`) tells users "run `@pipeline-orchestrator create a <topic>` agent" as the create command for Section C gaps — but doesn't mention that this requires `sdlc-team-common` installed.

### Why this matters

- **Discovery is part of normal setup.** Users running `setup-team` get discovery as part of the flow (step 5c). Discovery depends on pipeline-orchestrator. If team-common isn't installed, discovery behaviour becomes undefined.
- **Section C is explicitly designed to use these agents.** The three new issues from the onboarding surface review (#132, #133, #134) all assume Section C recommendations lead to agent creation via the pipeline. That only works if the pipeline is installed.
- **The plugin is already included in 5 of 6 project types.** The change isn't really "add team-common to the recommendation"; it's "make the existing default explicit and prevent accidental exclusion."

### User stories

- As a user running `setup-team` with option F (Custom), I want the skill to pre-select `sdlc-team-common` and warn me if I try to deselect it, so I don't accidentally end up without the research pipeline
- As a user whose discovery surfaces Section C gaps, I want `sdlc-team-common` to be treated as required (not just recommended) so I can actually act on those gaps without a separate plugin install step
- As a user invoking `@pipeline-orchestrator` directly and seeing Section C gaps in the output, I want the prerequisite dependency stated clearly so I know what plugin to install before running the Create commands
- As the framework, I want the implicit dependency between discovery output and installed plugins to be explicit so it doesn't break silently

---

## Proposed Solution

Three changes across four files (two source + two plugin copies).

### Change 1: `setup-team` step 3 — promote team-common to a near-universal default

The project types table gets an updated description for option F: `sdlc-team-common` is pre-selected, and the table is followed by an explanation of why team-common is the default and a deselection warning with a [y/N] prompt (default N).

### Change 2: `setup-team` new step 5e — escalate team-common to required when Section C gaps exist

After discovery (step 5c/5d), a new step 5e counts Section C gaps. If count > 0:

- Mark team-common as **required** in the plugin selection
- If the user previously deselected team-common in option F, block progression with a three-option resolution prompt (include team-common / remove Section C gaps / abort setup)
- Record `required_by: "section-c-gaps"` in `.sdlc/team-config.json` so the dependency is traceable

### Change 3: `setup-team` step 7 — update the recommendation output to mark plugin status

The recommendation output's SDLC Framework section gains a dedicated entry for `sdlc-team-common` with three status markers:
- `★` = universal default (the new marker for team-common)
- `✓` = always installed (sdlc-core)
- `○` = optional/selected (other team plugins, language plugins)

The team-common entry lists its agents explicitly so the user sees what they're getting.

### Change 4: `pipeline-orchestrator` Section C output — prerequisite note

Add a prerequisite paragraph at the top of Section C in the report template:

> **Prerequisite**: the `Create` commands in this section require `sdlc-team-common@ai-first-sdlc` installed. This plugin provides the agents that execute the research → synthesis → agent-builder pipeline (`pipeline-orchestrator`, `deep-research-agent`, `agent-builder`). If not already installed:
>
> ```
> /plugin install sdlc-team-common@ai-first-sdlc
> ```
>
> Without this plugin, the Section C entries below are informational only — the `Create` commands will fail because the underlying agents won't exist.

So users hitting discovery directly (not via setup-team) see the dependency immediately.

### Files modified

- `skills/setup-team/SKILL.md` (source)
- `plugins/sdlc-core/skills/setup-team/SKILL.md` (plugin copy)
- `agents/core/pipeline-orchestrator.md` (source)
- `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` (plugin copy)

---

## Success Criteria

- [ ] `setup-team` step 3 presents team-common as near-universal default with rationale
- [ ] Option F (Custom) pre-selects team-common with deselection warning (default N)
- [ ] New step 5e escalates team-common to required when Section C gap count > 0
- [ ] Escalation blocks deselection with three-option resolution prompt
- [ ] `.sdlc/team-config.json` records `required_by: "section-c-gaps"` when applicable
- [ ] Recommendation output (step 7) uses `★` marker for team-common with explicit agent list
- [ ] `pipeline-orchestrator` Section C output includes the prerequisite paragraph
- [ ] Plugin copies updated to match source
- [ ] Feature proposal + retrospective written
- [ ] PR description includes user-path verification block (good citizenship ahead of Constitution Article 12)
- [ ] CI passes

---

## Verification (user-path per #128 rule)

This change touches two user-facing surfaces: `setup-team` output and `pipeline-orchestrator` discovery output. Per the user-path verification rule from the #128 review, this PR should be verified on a fresh client.

**Limitation**: this session cannot run `/sdlc-core:setup-team` against a fresh project because the skill requires interactive Claude Code invocation and I'm inside the session running it. The verification is limited to:

- **Structural check**: confirm the edits to the skill and agent files produce the expected output shape when read (not when invoked)
- **Consistency check**: source files and plugin copies match
- **Documentation check**: the new behaviour is documented in the proposal and PR description

**Post-merge verification recommendation**: after merge, run `/sdlc-core:setup-team` on a fresh project. Verify:
1. Project type selection presents team-common as universal default
2. Option F (Custom) pre-selects team-common
3. Deselecting team-common in F produces the warning, defaulting to N
4. If discovery produces Section C gaps, the escalation step kicks in and team-common becomes required
5. The recommendation output shows the ★ marker for team-common

This follows the honesty pattern proposed in the #128 review's 2.4(a) verification template — "Fresh client used: N/A with exemption reason (in-session tooling limitation)" — while flagging the recommended post-merge manual check.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Users who genuinely don't want team-common (e.g., projects that will never create custom agents) are annoyed by the warning | Friction | The warning is informational with default N; users can still opt out by explicitly confirming Y. The rationale is clear so informed opt-out is possible. |
| Escalation to required blocks users who legitimately want Section C gaps identified but not acted on | Friction | Option 2 of the escalation prompt lets the user remove Section C gaps if they genuinely don't want custom agent creation. The prompt is not a hard block. |
| Users running `@pipeline-orchestrator` directly without team-common won't see the prerequisite note because they can't invoke the agent at all | Null case | If the agent isn't installed, running it fails immediately; there's no Section C output to contain the prerequisite note. The note is aimed at users who HAVE team-common and want to know they need it, or users with partial discovery output from older sessions. |
| Plugin copies drift from source | Stale behaviour | Same pattern from #120, #122, #124, #129: update both in the same commit. |

---

## Out of scope

- Moving pipeline-orchestrator / deep-research-agent / agent-builder to `sdlc-core`. The placement in team-common is correct; this fix is recommendation logic, not placement change.
- Auto-installing team-common without user consent. The rule is "strongly recommend and escalate to required with a block"; it is not "silently install without asking."
- Extending the pattern to other team plugins. Only team-common gets the ★ marker because only team-common contains the foundational agent-creation pipeline.

---

## Changes Made

| Action | File |
|---|---|
| Modify | `skills/setup-team/SKILL.md` |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` |
| Modify | `agents/core/pipeline-orchestrator.md` |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` |
| Create | `docs/feature-proposals/135-team-common-recommendation.md` (this file) |
| Create | `retrospectives/135-team-common-recommendation.md` |

---

## References

- Issue: #135
- Related: #128 (onboarding surface design review) — established the user-path verification rule this PR follows
- Related: #132 (Constitution Article 12) — once authored, will make user-path verification mandatory; this PR anticipates the rule
- Related: EPIC #97 (commissioning) — commissioning will inherit this logic for per-option plugin selection once sub-features 2-3 land

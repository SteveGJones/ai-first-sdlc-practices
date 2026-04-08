# Retrospective: Fix #122 — Discovery Install Instructions

**Branch**: `fix/discovery-install-instructions`
**Date**: 2026-04-08
**Issue**: #122
**Type**: Bug fix

## Context

Steve ran a discovery and got back a useful list of tools — five of them, all relevant to the project — but the discovery output had no installation instructions. Each of the five tools had a different install path (Claude Code plugin, MCP server, GitHub Action, standalone CLI, library framework). The user had to visit each repo, read each README, figure out the category, and construct the right install command themselves. That's exactly the friction discovery is supposed to remove.

This was a gap in both `pipeline-orchestrator` (the agent that runs discovery during agent creation) and `setup-team` (the skill that runs discovery during project setup). Both had the same defect: they recorded tool metadata (name, URL, type, maintenance status) but never produced install snippets.

The timing was significant: we just merged #120/#121 (the marketplace.json location fix), which finally makes plugin install actually work for new users. Discovery is now the natural next step in onboarding. If discovery doesn't tell users how to install what it finds, the install path stays broken in spirit even after we fixed it mechanically.

## What Went Well

- **Steve's defect report was concrete and actionable.** He pasted the actual table he got back, with all five tool URLs visible. I didn't have to guess what was missing — I could see the format gap directly. Reproducing the issue was free.
- **The fix had a clear shape from the start.** Once I read both source files, the gap was obvious: a metadata table with no Install column. The fix was equally obvious: add the column, plus the rules to populate it correctly.
- **Tool category classification turned out to be the right organising principle.** I started thinking about "install instructions per tool" but realised quickly that "per tool" is wrong — it's "per tool category." Seven categories cover everything: claude-plugin, mcp-server-npm, mcp-server-pip, mcp-server-binary, github-action, standalone-cli, library-framework. Each has a fixed install snippet shape. Classification is simple and the snippet is mechanical from the category.
- **The "never invent install commands" rule was important to add explicitly.** Without it, an agent under pressure to produce a complete output might guess at install commands for tools it doesn't fully understand. The explicit fallback ("Manual setup required, see README") gives the agent permission to defer rather than fabricate.
- **The reference tables ship in the agent/skill bodies.** Anyone updating an install format (e.g., when Claude Code's MCP config schema changes) updates one place per file. No code, no separate schema, no validator — just markdown the agent reads each time.

## What Could Improve

- **The defect existed since the discovery agent was first introduced (#82, ~3 weeks ago).** Five different EPICs/PRs touched discovery without anyone noticing the install instructions were missing. Like #120 (the marketplace.json path), this is a process gap: nobody actually ran discovery as a new user and tried to act on the output. Dogfooding the user-facing path catches this kind of bug; we keep skipping that step.
- **The fix is in markdown agent/skill bodies, which means there's no automated test that the install snippets are correct.** I can describe the per-category formats, but I can't verify that a snippet actually works against a real tool. If Claude Code's `.mcp.json` schema changes or a plugin marketplace renames its `name` field, the snippets become stale silently. A future improvement would be example files with actual install snippets that get validated against current schemas in CI.
- **Seven categories may not cover everything.** I picked the categories from observation of the kinds of tools that show up in discovery, but there are edge cases I haven't thought of: hosted SaaS APIs with no install (just an API key), tools distributed via Homebrew/winget, MCP servers behind enterprise gateways, etc. The "Manual setup required" fallback catches these but doesn't help the user. If I see a recurring uncategorised case, that's a signal to add a new category.
- **The example output in the agent's frontmatter only demonstrates two of the seven categories.** I showed `mcp-server-npm` and `claude-plugin`, which are probably the most common. Showing all seven would clutter the example, but a separate "examples by category" file or section would help future contributors understand the patterns.
- **No update to the broader documentation about discovery.** The README, the plugin docs, the CLAUDE.md skills table — none of them were updated to reflect that discovery now produces install instructions. The change is real but only visible if you actually run discovery and see the output. Future improvement: add a sentence to the discovery section of CLAUDE-CORE.md explaining what users should expect.

## Lessons Learned

1. **Discovery without action is half a discovery.** A list of tools without install instructions just shifts work from the discovery agent to the user. The agent should produce complete, actionable output — not just structured data. Completeness includes "what do I do with this?"

2. **Categories beat per-tool customisation.** I started thinking about per-tool install logic and quickly realised it doesn't scale — there are too many tools, and they fall into a small number of patterns. Classifying tools into categories first, then applying a per-category template, gives O(categories) complexity instead of O(tools). Seven categories cover all the cases I can think of.

3. **"Never invent" rules are as important as "always produce" rules.** The agent could fabricate plausible-looking install commands for any tool — and they'd often be wrong. The explicit "if uncertain, say so" fallback is what prevents the agent from producing confidently-wrong output. Same principle as the librarian's anti-hallucination rules in #105.

4. **Plugin copies of agents/skills must be updated in the same commit as source.** I keep hitting this — if I update only the source and rely on release-plugin to regenerate, the plugin copy goes stale until someone runs release-plugin. For fixes that need to ship immediately, edit both source and plugin copy in the same commit. The next release-plugin run will see no diff. (Same lesson from #120.)

5. **User-facing paths need user-facing testing.** Both #120 and #122 are bugs that existed for weeks because nobody actually ran the user-facing path on a fresh client. CI tests file contents; it doesn't test the *experience* of using the framework. The Docker smoke test runs a happy path but doesn't surface "is this output actually useful to a human?" questions. Adding "did I run the user path and look at the output critically" to the PR checklist would catch both classes of bug.

## Changes Made

| Action | File | Change |
|---|---|---|
| Modify | `agents/core/pipeline-orchestrator.md` | Added classification step (7), restructured report template (8) with per-tool entries including Install field, added per-category install instruction reference table, renumbered subsequent steps, updated example to demonstrate two categories |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Plugin copy of pipeline-orchestrator updated to match source |
| Modify | `skills/setup-team/SKILL.md` | Added classification rules to step 5c, added new step 5c.1 with the per-category install reference table, updated step 7 recommendation output to include install snippets per discovered tool |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` | Plugin copy of setup-team updated to match source |
| Create | `docs/feature-proposals/122-discovery-install-instructions.md` | Feature proposal documenting the defect and fix |
| Create | `retrospectives/122-discovery-install-instructions.md` | This file |

## Follow-on issues

1. **User-facing path verification in PR review.** Both #120 and #122 would have been caught if anyone had actually run the user path before merging the PRs that introduced them. Add to CONTRIBUTING.md: "For any PR that touches user-facing output (discovery, setup-team, install paths), the reviewer must run the path manually and verify the output is actionable." File as a process improvement issue.

2. **Install snippet schema validation.** Future improvement: ship example install snippets per category as test fixtures, validate them against current Claude Code schemas (`.mcp.json` schema, plugin manifest schema, GitHub Actions schema) in CI. Catches the "schema changed, snippets are stale" failure mode.

3. **Add an eighth category for hosted SaaS APIs.** Some tools have no install at all — they're just an API endpoint plus an API key. Currently these would fall under "Manual setup required, see README", but they're common enough to warrant their own category with a standard "set $TOOL_API_KEY env var, no install needed" snippet.

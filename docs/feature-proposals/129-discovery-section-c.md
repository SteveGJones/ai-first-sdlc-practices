# Feature Proposal: Discovery Section C — Coverage Gaps Worth Custom Agents

**Proposal Number:** 129
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `fix/discovery-section-c`
**Issue:** #129
**Type:** Enhancement (follow-up to #124)

---

## Executive Summary

#124 introduced Sections A (Claude Code environment tools) and B (project dependencies) in the discovery output. The split handles "there's an off-the-shelf tool" cleanly but leaves the "there's no good off-the-shelf option, would a custom agent be worth building?" case as an implicit end-of-report choice. This proposal adds **Section C**: per-topic coverage gaps where discovery recommends commissioning research and building a project-specific custom agent via the existing pipeline-orchestrator research flow (deep-research-agent → synthesis → agent-builder).

Section C makes custom agent creation a first-class per-topic decision rather than a whole-report "choose (a) / (b) / (c)" choice at the end. The user sees which topics actually need custom agents, what each agent would know, and can selectively commission them.

---

## Motivation

### Problem statement

Before this change, the discovery report tells the user what pre-built tools exist (Section A) and what libraries they could use in their own code (Section B). It doesn't tell them: "for these topics, neither approach gives you what you need — a custom agent would be worth building." That information is currently buried as a vague "(c) Build custom agent from scratch" option at the end of the flow, which has three problems:

1. **It's whole-report, not per-topic.** The user has to choose "custom or not" across the entire discovery rather than per technology. Most real projects want some pre-built tools AND some custom agents for different parts of the stack, which the three-option framing doesn't support cleanly.

2. **It doesn't surface which topics actually need custom agents.** The user has to reason about "where are the gaps?" themselves. The discovery agent already knows this (it evaluated coverage per technology) but doesn't tell the user.

3. **It doesn't say what a custom agent would *do*.** The (c) choice is abstract. The user can't tell whether a custom agent would be high-value (fills a real gap) or low-value (duplicates existing tooling) without thinking it through themselves.

### User stories

- As a user reviewing discovery output, I want to see which specific topics need custom agents so I can make an informed per-topic decision rather than a blanket choice
- As a user who sees a gap described, I want to know what the custom agent would know, what research would be commissioned, and how long it would take before I commit
- As a user with multiple gaps identified, I want to selectively pick which gaps to fill rather than all-or-nothing
- As the pipeline-orchestrator, I want the Section C decisions to route directly into the existing research → synthesis → agent-builder flow I already own

---

## Proposed Solution

### Change 1: Add Section C to the discovery report template

Both `pipeline-orchestrator` and `setup-team` get a new Section C in their discovery report templates, appearing after Section B and before the Coverage Assessment summary:

```markdown
## Section C: Gaps Worth Custom Agents

These are topics where discovery found no suitable pre-built Claude Code tools (Section A) and no library approach alone would give you an expert collaborator (Section B). For each, you can choose to commission research and build a project-specific custom agent via the agent creation pipeline (deep-research-agent → synthesis → agent-builder).

### Gap 1: {Topic}
- **Why a custom agent**: {what's missing that a custom agent would provide}
- **What the agent would know**: {1-2 sentence description of the intended expertise}
- **Research scope**: {topics the research campaign would cover}
- **Estimated pipeline duration**: 2-3 hours (web research + synthesis + construction)
- **Create** (if you want it): `@pipeline-orchestrator create a {topic-slug} agent`

### Gap 2: {Topic}
...
```

Five mandatory fields per gap, same prescriptive pattern as the `Install` field in Sections A and B. If the agent cannot justify a gap with a specific "why", it omits the entry rather than producing a vague one.

### Change 2: Coverage → Section C mapping

Each technology in the discovery pool gets a coverage assessment that drives whether it becomes a Section C entry:

| Coverage level | Signal | Section C entry |
|---|---|---|
| **High** | Section A has a pre-built tool that directly serves the need | No entry |
| **Medium** | Section A partially covers, Section B can fill gaps with the user's own code | OPTIONAL — include only if a custom agent would add architectural guidance or domain expertise beyond libraries alone |
| **Low / None** | No Section A tools, Section B alone doesn't substitute for expertise | RECOMMENDED |

### Change 3: Replace the old (a)/(b)/(c) framing with per-section decisions

The old `pipeline-orchestrator` step 9 asked the user to pick one of three options (use as-is / hybrid / build custom) across the whole report. This gets replaced with a per-section decision flow:

1. **Section A decision**: which tools (if any) to install (user runs the install snippets themselves)
2. **Section B decision**: informational only (no action from the agent — Section B libraries are for the user's own project code)
3. **Section C decision**: which gaps (if any) to fill with custom agents (agent routes each selection into the full research → synthesis → agent-builder pipeline)

### Change 4: Section C decisions route back into the existing pipeline

The pipeline-orchestrator already has the full research → build flow (Phase 1 routes to deep-research-agent, Phase 5 delegates to agent-builder). Section C is simply offering that core workflow as the response to each gap. For each selected gap, the orchestrator:

- Runs `deep-research-agent` with the Research Scope from the Section C entry as the campaign prompt
- Stores the synthesis at `agent_prompts/research-output-<topic-slug>.md`
- Delegates to `agent-builder` to construct the agent from the synthesis
- Writes the agent file to `agents/<category>/<topic-slug>.md`

If the user selected multiple gaps with no dependencies between them, the orchestrator dispatches them as parallel pipelines using the `dispatching-parallel-agents` skill.

### Change 5: setup-team surfaces Section C but doesn't own it

`setup-team` is the project setup skill — it discovers tools for the project as part of configuring a team. Setup-team's role for Section C is informational: it presents the gaps and points at pipeline-orchestrator for actual agent creation. The user's next action for a Section C item from setup-team is: "run `@pipeline-orchestrator create a <topic-slug> agent` when you want to fill this gap."

This keeps the responsibility boundary clean:
- `pipeline-orchestrator` owns agent creation (can act on Section C directly)
- `setup-team` owns project configuration (surfaces Section C as recommendations, doesn't create agents)

### Files modified

- `agents/core/pipeline-orchestrator.md` (source) — Section C in report template, coverage-to-C mapping table, new step 8 (coverage assessment), updated step 10 (per-section decisions), updated step 11 (Section C routing), updated frontmatter example with all three sections populated
- `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` (plugin copy) — same
- `skills/setup-team/SKILL.md` (source) — Section C in recommendation output format
- `plugins/sdlc-core/skills/setup-team/SKILL.md` (plugin copy) — same

---

## Success Criteria

- [ ] Both `pipeline-orchestrator.md` files include Section C in the report template
- [ ] Both files include the coverage-to-Section-C mapping table
- [ ] The pipeline-orchestrator has a new step 8 for coverage assessment
- [ ] Step 10 replaces the old (a)/(b)/(c) framing with per-section decisions
- [ ] Step 11 routes Section C selections through the existing research → build pipeline
- [ ] Both `setup-team/SKILL.md` files include Section C in the recommendation output
- [ ] Setup-team's Section C points at pipeline-orchestrator for actual agent creation (doesn't attempt to create agents itself)
- [ ] The pipeline-orchestrator example demonstrates a full three-section report (A + B + C)
- [ ] Every Section C entry has all five mandatory fields
- [ ] Plugin copies updated to match source
- [ ] CI passes
- [ ] Pre-push validation passes

---

## Manual verification (post-merge)

Run discovery on a tech stack that has at least one gap:

1. `/plugin marketplace update ai-first-sdlc`
2. `/reload-plugins`
3. Run discovery: `@pipeline-orchestrator find tools for working with <a specialised technology with no MCP server>`
4. Verify the output has three sections:
   - Section A with any found tools (or `_No Section A tools found_` note)
   - Section B with any found libraries (or `_No Section B libraries found_` note)
   - Section C with at least one gap entry containing all five fields
5. Verify the decision flow:
   - User is asked per section what they want
   - Selecting a Section C gap routes into the research pipeline
   - Declining all Section C gaps ends the flow cleanly

A tech stack like "internal legacy Oracle Forms" or "a niche protobuf service mesh" would reliably produce a Section C entry.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| The agent produces weak/vague Section C entries with generic justifications ("might be useful") | Section C becomes noise; users ignore it | Mandatory five fields per entry; explicit instruction that vague entries must be omitted; the "Why a custom agent" field must be specific |
| The per-section decision flow confuses users who expected a single choice | User friction | The three-decision flow is clearly structured; the example in the frontmatter demonstrates the format; the old (a)/(b)/(c) was also three choices, just less structured |
| Users click "yes" on too many Section C gaps and commit to multiple multi-hour pipelines | Unexpected compute cost / time | Each gap entry has the 2-3 hour duration estimate; the agent confirms before dispatching parallel pipelines |
| Section C becomes a dumping ground for every technology | Report noise | Coverage assessment gates entries: High coverage = no entry, Medium coverage = optional, only Low/None = recommended. The `mcp-server-npm` vs `library-framework` distinction from #124 stays |
| Plugin copies drift from source | Stale behaviour in installed plugins | Both updated in same commit; same lesson from #120, #122, #124 |

---

## Out of scope

- Automated testing of Section C (will be covered by #126 automated discovery output testing when that lands)
- Changes to deep-research-agent or agent-builder themselves (they're invoked as-is by the orchestrator's existing pipeline)
- Caching Section C research results across sessions (each invocation is fresh)
- Section C for non-technology topics (e.g., process gaps, documentation gaps) — scope is technical tool gaps only for now

---

## Changes Made

| Action | File |
|---|---|
| Modify | `agents/core/pipeline-orchestrator.md` |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` |
| Modify | `skills/setup-team/SKILL.md` |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` |
| Create | `docs/feature-proposals/129-discovery-section-c.md` (this file) |
| Create | `retrospectives/129-discovery-section-c.md` |

---

## References

- Issue: #129
- Prior fix: #124 — introduced Sections A and B but left the custom-agent option as a vague end-of-report choice
- Prior fix: #122/#123 — introduced install instructions per category
- Prior fix: #120/#121 — marketplace location
- Related: #126 — automated discovery output testing (should cover Section C when filed)

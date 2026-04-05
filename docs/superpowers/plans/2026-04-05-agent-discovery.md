# Agent Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 1st-party discovery phase to the agent creation pipeline so it finds official MCP servers, agent skills, Claude plugins, and GitHub Actions before building custom agents from scratch.

**Architecture:** New Phase 0 (Discovery) added to pipeline-orchestrator before existing Phase 1. Searches 4 registries + web, presents findings with three options (use-as-is / hybrid / build-custom). Agent-builder updated to include `first_party_alternatives` metadata when official tools exist. Discovery results stored in project memory.

**Tech Stack:** Markdown agent files (no code — these are LLM instruction documents)

---

### Task 1: Add Discovery Phase to Pipeline Orchestrator

**Files:**
- Modify: `agents/core/pipeline-orchestrator.md`

- [ ] **Step 1: Add a discovery example to the frontmatter**

In `agents/core/pipeline-orchestrator.md`, add a third example after the existing two examples (after line 18, before `color: green`):

```yaml
- '<example>
Context: User requests a MongoDB agent and the pipeline discovers official tooling.
  user: "We need a MongoDB expert agent for our team."
  assistant: "Before building a custom agent, I will check for official MongoDB tooling. Discovery found: (1) @mongodb/mcp-server on npm — official MCP server with query, schema inspection, and index management capabilities, actively maintained. (2) mongodb/agent-skills on GitHub — pre-built agent skills for CRUD, aggregation, and vector search. These official tools cover the core MongoDB use case. Options: (a) Use the official MCP server and agent skills as-is — install and configure them. (b) Hybrid — install the official tools and build a lightweight agent that adds architectural guidance (schema design patterns, index optimization, migration planning). (c) Build a custom agent from scratch, ignoring official tools. Which approach?"
  <commentary>The Pipeline Orchestrator discovers 1st-party tools before building from scratch, presenting the user with options to use official tooling, build a hybrid, or proceed with custom construction.</commentary>
</example>'
```

- [ ] **Step 2: Update the orchestrator's role description**

Replace the first paragraph of the agent body (line 24, starting "You are the Pipeline Orchestrator") with:

```markdown
You are the Pipeline Orchestrator, the unified entry point for the entire agent creation pipeline. You coordinate the full end-to-end lifecycle: **discovery of official tools** → need identification → research/distillation → building → validation → deployment. Your first action on any request is to search for 1st-party tooling (MCP servers, agent skills, Claude plugins, GitHub Actions) published by the technology vendor. Only if no suitable official tools exist — or the user explicitly wants a custom agent — do you proceed to research and build. Your approach is systematic and fault-tolerant -- you verify exit criteria at every phase, stop on failures, and report progress transparently.
```

- [ ] **Step 3: Add "1st-Party Discovery" to Core Competencies**

Insert as the new competency #1 (before existing "Input Type Detection"), shifting all other numbers up by 1:

```markdown
1. **1st-Party Tool Discovery**: Searching MCP server registries (npm, PyPI), vendor GitHub organizations, Claude Code plugin marketplace, and GitHub Actions marketplace for official tooling before building custom agents. Running targeted web searches when registry checks are insufficient. Presenting discovery findings with three options: use as-is, hybrid (complement official tools), or build custom.
```

This makes existing competencies numbered 2-8.

- [ ] **Step 4: Add Phase 0: Discovery**

Insert the following new phase BEFORE the existing "Phase 1: Input Analysis and Need Identification" section (before line 38):

```markdown
### Phase 0: 1st-Party Tool Discovery

**Entry**: User request describing the agent they want to create

**Skip conditions** (check in order):
1. User explicitly says "skip discovery", "build from scratch", or "build custom" → skip to Phase 1
2. `.sdlc/pipeline-config.json` exists and contains `"discover_first_party": false` → skip to Phase 1
3. Project memory contains a recent discovery result for this domain (check memory files for `discovery_{domain}`) → present cached results, ask user to confirm or re-discover

**Actions**:
1. Extract the technology/domain name from the user request (e.g., "MongoDB", "Stripe", "Kubernetes", "GraphQL")

2. Check project memory for cached discovery results:
   - Search memory files for `discovery_{domain}`
   - If found and less than 30 days old: present cached results, ask user "Use these results or re-discover?"
   - If user says use cached: skip to step 6

3. Run registry checks (search all 4 sources):

   **MCP Server registries:**
   - WebSearch: `"{domain} mcp server" site:npmjs.com`
   - WebSearch: `"{domain} mcp server" site:pypi.org`
   - WebSearch: `"{domain} mcp" site:github.com` (look for official org repos)

   **Vendor GitHub organization:**
   - WebSearch: `"github.com/{vendor}" mcp OR agent OR skills OR claude`
   - Look for repos named `*mcp*`, `*agent*`, `*skills*`, `*claude*` in the vendor's GitHub org

   **Claude plugin marketplace:**
   - WebSearch: `"{domain} claude code plugin"`
   - Check if a plugin already exists for this domain

   **GitHub Actions marketplace:**
   - WebSearch: `"{domain} github action" site:github.com/marketplace`

4. Run targeted web search (alongside or after registry checks):
   - `"{vendor} official mcp server"`
   - `"{vendor} agent skills" OR "{vendor} claude agent"`
   - `"{vendor} ai integration" OR "{vendor} llm tools"`

5. Compile findings into a Discovery Report:

   ```markdown
   ## Discovery Report: {Domain}

   ### 1st-Party Tools Found

   | Tool | Type | Source | Capabilities | Maintained? |
   |------|------|--------|-------------|-------------|
   | {name} | MCP Server / Agent Skills / Plugin / Action | {url} | {description} | {last activity} |

   ### Not Found
   - {source}: {what was searched, no results}

   ### Recommendation
   {summary and recommendation}
   ```

6. Present findings to user with three options:

   **If tools found:**
   ```
   Discovery found official tooling for {domain}:
   {discovery report}

   Options:
   1. Use official tools — I'll provide install/setup instructions. No custom agent needed.
   2. Hybrid — install official tools AND build a custom agent that complements them.
   3. Build from scratch — ignore official tools, run full research campaign.

   Which approach?
   ```

   **If nothing found:**
   ```
   No official 1st-party tools found for {domain}. Searched: MCP registries, {vendor} GitHub org, Claude marketplace, GitHub Actions.
   Proceeding to build a custom agent via full research campaign.
   ```

7. Route based on user decision:
   - **"Use as-is" (option 1)**: Present install commands, save discovery to memory, STOP pipeline. No agent is built.
   - **"Hybrid" (option 2)**: Save discovery to memory. Proceed to Phase 1 with discovery context — research should focus on what the official tools DON'T cover. Pass discovery report to Phase 4 and Phase 5.
   - **"Build custom" (option 3)**: Save discovery to memory. Proceed to Phase 1 as normal (full research campaign). Discovery report still recorded for `first_party_alternatives` metadata.
   - **Nothing found**: Proceed to Phase 1 as normal.

8. Save discovery results to project memory:
   ```markdown
   ---
   name: discovery_{domain}
   description: Official 1st-party tools discovered for {domain}
   type: reference
   ---

   ## {Domain} Official Tooling

   Discovered: {date}

   | Tool | Type | Source | Install |
   |------|------|--------|---------|
   | {name} | {type} | {url} | {install command} |

   User decision: {use-as-is / hybrid / build-custom / nothing-found}
   ```

**Exit criteria**:
- Discovery search completed (all 4 registries + web search)
- Discovery report compiled
- User decision recorded (or skip condition met)
- Discovery results saved to project memory
- Pipeline routing decided: STOP (use-as-is), Phase 1 with context (hybrid), Phase 1 normal (build-custom or nothing found)
```

- [ ] **Step 5: Update existing Phase 1 header**

Rename the existing "Phase 1" heading from:
```markdown
### Phase 1: Input Analysis and Need Identification
```
to:
```markdown
### Phase 1: Input Analysis and Need Identification

**Entry**: Phase 0 complete (discovery done, skipped, or cached results used)
```

Replace the existing Entry line (`**Entry**: User request describing the agent they want to create`) since Phase 0 now handles the initial user request.

- [ ] **Step 6: Update Phase 5 to pass discovery context to agent-builder**

In Phase 5 (Agent Construction), step 1 ("Prepare agent-builder inputs"), add after the existing bullet about portable artifacts:

```markdown
   - If discovery found 1st-party tools (from Phase 0): pass the discovery report and user decision. Tell agent-builder: "Discovery found these official tools: {list}. User chose {decision}. Add first_party_alternatives to frontmatter and a Related Official Tools section to the agent body."
   - If hybrid mode: tell agent-builder: "This agent complements official tools. The agent's instructions should reference when to use the official tool vs when to use this agent."
```

- [ ] **Step 7: Add discovery-related rule**

In the "Rules (Enforced - Never Violate)" section, add as rule 9:

```markdown
9. **ALWAYS run discovery before building** (Phase 0) -- check for official MCP servers, agent skills, plugins, and GitHub Actions before investing in custom agent creation. Skip only when user explicitly requests it or project config disables discovery.
```

- [ ] **Step 8: Add discovery-related common mistake**

In the "Common Mistakes" section, add:

```markdown
**Building From Scratch When Official Tools Exist**: Pipeline skips discovery and builds a custom MongoDB/Stripe/AWS agent when the vendor publishes an official MCP server or agent skills that are maintained and better integrated. ALWAYS run Phase 0 discovery first. A vendor-maintained tool with direct system access will always outperform a generated agent built from documentation.
```

- [ ] **Step 9: Update Pipeline Completion Report format**

In the "Pipeline Completion Report Format" section, add after "Pipeline Summary":

```markdown
### Discovery Results
- **Domain**: {domain/technology name}
- **1st-Party Tools Found**: {count} ({list of names})
- **User Decision**: use-as-is / hybrid / build-custom / nothing-found / discovery-skipped
- **Discovery cached**: Yes/No (memory file: discovery_{domain})
```

- [ ] **Step 10: Commit**

```bash
git add agents/core/pipeline-orchestrator.md
git commit -m "feat: add 1st-party discovery phase to pipeline-orchestrator (#82)

New Phase 0 searches MCP registries, vendor GitHub orgs, Claude marketplace,
and GitHub Actions for official tooling before building custom agents.
User chooses: use as-is, hybrid, or build custom."
```

---

### Task 2: Update Agent Builder for Discovery Metadata

**Files:**
- Modify: `agents/core/agent-builder.md`

- [ ] **Step 1: Add first_party_alternatives to YAML frontmatter guidance**

In `agents/core/agent-builder.md`, find the "YAML Frontmatter Engineering" competency (competency #4) and add to its description:

```markdown
4. **YAML Frontmatter Engineering**: Writing discoverable agent metadata with effective semantic trigger examples that follow the format spec constraints. When discovery found official tools, includes `first_party_alternatives` field listing the tools with name, type, and URL.
```

- [ ] **Step 2: Add first_party_alternatives to the frontmatter construction phase**

Find the section where agent-builder constructs the YAML frontmatter (in the Phase 2 or Phase 3 workflow). Add after the existing frontmatter fields:

```markdown
**If discovery results were provided by the pipeline-orchestrator:**

Add `first_party_alternatives` to the YAML frontmatter:

```yaml
first_party_alternatives:
  - name: "@mongodb/mcp-server"
    type: mcp-server
    url: "https://npmjs.com/package/@mongodb/mcp-server"
  - name: "mongodb/agent-skills"
    type: agent-skills
    url: "https://github.com/mongodb/agent-skills"
```

This field tells future users: "official alternatives exist for this domain." Include all tools from the discovery report, regardless of the user's decision (use-as-is, hybrid, or build-custom).
```

- [ ] **Step 3: Add "Related Official Tools" section guidance**

Find the section where agent-builder constructs the agent body content. Add a new subsection:

```markdown
### Related Official Tools Section

**When to include**: When the pipeline-orchestrator passed discovery results showing 1st-party tools exist.

**Where to place**: After the "Collaboration" section, before "Scope & When to Use".

**Content pattern:**

```markdown
## Related Official Tools

The following official tools exist for this domain:

| Tool | Type | What it provides |
|------|------|-----------------|
| @mongodb/mcp-server | MCP Server | Direct database queries, schema inspection, index management |
| mongodb/agent-skills | Agent Skills | Pre-built CRUD, aggregation, and vector search capabilities |

**When to use official tools vs this agent:**
- Use the MCP server for: direct database operations, schema queries, index management
- Use this agent for: schema design guidance, query optimization patterns, migration planning, architectural decisions
- The official tools handle execution; this agent handles design and strategy
```

**For hybrid agents** (user chose option 2): The agent's core instructions should explicitly reference the official tools. Example phrasing: "For direct MongoDB queries and schema inspection, defer to the MongoDB MCP server. This agent provides architectural guidance that complements the official tools: schema design patterns, index optimization strategy, and migration planning."

**For build-custom agents** (user chose option 3): Include the section but note: "These official tools were available at the time of agent creation. The user chose to build a custom agent because: {reason from user}."
```

- [ ] **Step 4: Commit**

```bash
git add agents/core/agent-builder.md
git commit -m "feat: add first_party_alternatives metadata to agent-builder (#82)

Agent-builder now includes first_party_alternatives in YAML frontmatter
and a Related Official Tools section in agent body when discovery found
official tooling. Hybrid agents reference official tools in instructions."
```

---

### Task 3: Sync Plugin Copies

**Files:**
- Sync: `plugins/sdlc-team-common/agents/pipeline-orchestrator.md`
- Sync: `plugins/sdlc-team-common/agents/agent-builder.md`

- [ ] **Step 1: Copy source to plugin**

```bash
cp agents/core/pipeline-orchestrator.md plugins/sdlc-team-common/agents/pipeline-orchestrator.md
cp agents/core/agent-builder.md plugins/sdlc-team-common/agents/agent-builder.md
```

- [ ] **Step 2: Verify sync**

```bash
diff agents/core/pipeline-orchestrator.md plugins/sdlc-team-common/agents/pipeline-orchestrator.md
diff agents/core/agent-builder.md plugins/sdlc-team-common/agents/agent-builder.md
```

Expected: no output (files identical).

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-team-common/agents/pipeline-orchestrator.md plugins/sdlc-team-common/agents/agent-builder.md
git commit -m "chore: sync pipeline-orchestrator and agent-builder to plugin copies"
```

---

### Task 4: Update Issue and Push

**Files:** None (GitHub only)

- [ ] **Step 1: Push changes**

```bash
git push origin main
```

- [ ] **Step 2: Close issue with summary**

```bash
gh issue close 82 --comment "Implemented: pipeline-orchestrator now runs Phase 0 (Discovery) before building.

- Searches 4 registries: MCP servers (npm/PyPI), vendor GitHub org, Claude marketplace, GitHub Actions
- Targeted web search when registries insufficient
- Presents findings with 3 options: use-as-is, hybrid, build-custom
- Discovery results cached in project memory (prevents re-discovery)
- Agent-builder adds first_party_alternatives frontmatter + Related Official Tools section
- Skippable via explicit request or .sdlc/pipeline-config.json

Source and plugin copies synced."
```

# Agent Base Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit all 62 agents in `agents/` for official 1st-party alternatives, update frontmatter where alternatives are found, and produce a comprehensive audit report.

**Architecture:** One subagent per category directory (7 batches). Each subagent reads agent frontmatter, runs discovery (4 registries + web search), and returns structured findings. A coordinator compiles the report, applies frontmatter updates, and syncs plugin copies.

**Tech Stack:** Markdown agent files, WebSearch for discovery, YAML frontmatter editing

---

### Task 1: Audit `agents/core/` (30 agents)

**Files:**
- Read: all 30 `.md` files in `agents/core/`
- Modify: agents where alternatives are found (add `first_party_alternatives` to YAML frontmatter)

Agents to audit:
```
agent-builder, api-architect, backend-architect, cloud-architect,
compliance-auditor, compliance-report-generator, container-platform-specialist,
critical-goal-reviewer, data-architect, data-privacy-officer, database-architect,
deep-research-agent, devops-specialist, enforcement-strategy-advisor,
example-security-architect, frontend-architect, frontend-security-specialist,
github-integration-specialist, mobile-architect, observability-specialist,
pipeline-orchestrator, repo-knowledge-distiller, sdlc-coach, sdlc-enforcer,
security-architect, solution-architect, sre-specialist, test-manager,
ux-ui-architect, verification-enforcer
```

- [ ] **Step 1: For each agent, read name and description from YAML frontmatter**

Read each `.md` file's frontmatter. Extract `name` and `description` fields. These determine what to search for.

- [ ] **Step 2: Run discovery for each agent**

For each agent, extract the domain/technology from its name and description, then search:

- WebSearch: `"{domain}" mcp server site:npmjs.com`
- WebSearch: `"{domain}" mcp server site:pypi.org`
- WebSearch: `"github.com/{likely-vendor}" mcp OR agent OR skills OR claude`
- WebSearch: `"{domain}" claude code plugin`
- WebSearch: `"{domain}" github action site:github.com/marketplace`
- WebSearch: `"{domain}" official AI agent OR assistant OR tool`

Examples of domain extraction:
- `api-architect` → "API design", "OpenAPI", "REST API tools"
- `cloud-architect` → "cloud architecture", "AWS architect", "Azure architect", "GCP architect"
- `database-architect` → "database", "SQL", "PostgreSQL MCP", "MongoDB MCP"
- `github-integration-specialist` → "GitHub", search github.com directly
- `solution-architect` → "system architecture AI tool", "Anthropic architect"
- `sdlc-enforcer` → "SDLC enforcement", "code quality AI", "Anthropic code review"
- `verification-enforcer` → "verification AI tool", "testing enforcement"

- [ ] **Step 3: Record findings**

For each agent, produce a structured finding:

```markdown
### <agent-name>
- **Category**: core
- **Alternatives found**: <count>
  - <tool name> (<type>) — <url> — <capabilities> — Maintained: <Yes/No>
- **Action**: <Added first_party_alternatives to frontmatter / No change>
- **Recommendation**: <Keep / Review — may substantially overlap / Reposition as complement to official tools>
- **Rationale**: <Why — what does the agent provide that the official tool doesn't, or vice versa>
```

If no alternatives found:
```markdown
### <agent-name>
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: No official 1st-party alternatives discovered
```

- [ ] **Step 4: Update frontmatter for agents with alternatives**

For each agent where alternatives were found, add `first_party_alternatives` to the YAML frontmatter. Insert after the existing fields (after `color` or `examples`, before the closing `---`):

```yaml
first_party_alternatives:
  - name: "<tool name>"
    type: "<mcp-server/agent-skills/plugin/action>"
    url: "<url>"
```

- [ ] **Step 5: Save findings to a temporary file**

Write the findings for all 30 agents to `./tmp/audit-core.md`. This will be compiled into the final report in Task 8.

- [ ] **Step 6: Commit frontmatter changes**

```bash
git add agents/core/*.md
git commit -m "feat: add first_party_alternatives to core agents (audit #83)

Agents with alternatives found: <list names>
Agents with no alternatives: <count>"
```

If no agents had alternatives found, skip this commit.

---

### Task 2: Audit `agents/ai-development/` (9 agents)

**Files:**
- Read: all 9 `.md` files in `agents/ai-development/`
- Modify: agents where alternatives are found

Agents to audit:
```
a2a-architect, agent-developer, ai-solution-architect,
junior-ai-solution-architect, langchain-architect, mcp-quality-assurance,
mcp-server-architect, mcp-test-agent, prompt-engineer
```

- [ ] **Step 1: Read frontmatter for all 9 agents**

- [ ] **Step 2: Run discovery for each agent**

Domain extraction examples:
- `langchain-architect` → "LangChain", search github.com/langchain-ai
- `mcp-server-architect` → "MCP server", search Anthropic MCP docs, official MCP SDK
- `mcp-test-agent` → "MCP testing", search for MCP inspector/debugging tools
- `a2a-architect` → "agent-to-agent", "A2A protocol", search Google A2A
- `prompt-engineer` → "prompt engineering tools", "Anthropic prompt tools"

- [ ] **Step 3: Record findings** (same format as Task 1 Step 3)

- [ ] **Step 4: Update frontmatter** (same approach as Task 1 Step 4)

- [ ] **Step 5: Save findings to `./tmp/audit-ai-development.md`**

- [ ] **Step 6: Commit**

```bash
git add agents/ai-development/*.md
git commit -m "feat: add first_party_alternatives to ai-development agents (audit #83)"
```

---

### Task 3: Audit `agents/ai-builders/` (5 agents)

**Files:**
- Read: all 5 `.md` files in `agents/ai-builders/`
- Modify: agents where alternatives are found

Agents to audit:
```
ai-devops-engineer, ai-team-transformer, context-engineer,
orchestration-architect, rag-system-designer
```

- [ ] **Step 1: Read frontmatter for all 5 agents**

- [ ] **Step 2: Run discovery for each agent**

Domain extraction examples:
- `rag-system-designer` → "RAG", "retrieval augmented generation", search for LlamaIndex, LangChain RAG tools
- `orchestration-architect` → "agent orchestration", "LangGraph", "CrewAI", "AutoGen"
- `context-engineer` → "context window", "context management AI tools"
- `ai-devops-engineer` → "MLOps", "AI deployment", "ML pipeline tools"

- [ ] **Step 3: Record findings** (same format as Task 1 Step 3)

- [ ] **Step 4: Update frontmatter** (same approach as Task 1 Step 4)

- [ ] **Step 5: Save findings to `./tmp/audit-ai-builders.md`**

- [ ] **Step 6: Commit**

```bash
git add agents/ai-builders/*.md
git commit -m "feat: add first_party_alternatives to ai-builders agents (audit #83)"
```

---

### Task 4: Audit `agents/testing/` (4 agents)

**Files:**
- Read: all 4 `.md` files in `agents/testing/`
- Modify: agents where alternatives are found

Agents to audit:
```
ai-test-engineer, code-review-specialist,
integration-orchestrator, performance-engineer
```

- [ ] **Step 1: Read frontmatter for all 4 agents**

- [ ] **Step 2: Run discovery for each agent**

Domain extraction examples:
- `code-review-specialist` → "code review AI", "GitHub Copilot code review", "Anthropic code review"
- `performance-engineer` → "performance testing AI", "load testing tools", "k6", "Grafana"
- `ai-test-engineer` → "AI testing", "LLM testing tools", "promptfoo", "deepeval"

- [ ] **Step 3: Record findings** (same format as Task 1 Step 3)

- [ ] **Step 4: Update frontmatter** (same approach as Task 1 Step 4)

- [ ] **Step 5: Save findings to `./tmp/audit-testing.md`**

- [ ] **Step 6: Commit**

```bash
git add agents/testing/*.md
git commit -m "feat: add first_party_alternatives to testing agents (audit #83)"
```

---

### Task 5: Audit `agents/documentation/` (2 agents)

**Files:**
- Read: all 2 `.md` files in `agents/documentation/`
- Modify: agents where alternatives are found

Agents to audit:
```
documentation-architect, technical-writer
```

- [ ] **Step 1: Read frontmatter for both agents**

- [ ] **Step 2: Run discovery for each agent**

Domain extraction:
- `documentation-architect` → "documentation AI", "docs-as-code tools", "Anthropic documentation"
- `technical-writer` → "technical writing AI", "documentation generation"

- [ ] **Step 3: Record findings** (same format as Task 1 Step 3)

- [ ] **Step 4: Update frontmatter** (same approach as Task 1 Step 4)

- [ ] **Step 5: Save findings to `./tmp/audit-documentation.md`**

- [ ] **Step 6: Commit**

```bash
git add agents/documentation/*.md
git commit -m "feat: add first_party_alternatives to documentation agents (audit #83)"
```

---

### Task 6: Audit `agents/project-management/` (4 agents)

**Files:**
- Read: all 4 `.md` files in `agents/project-management/`
- Modify: agents where alternatives are found

Agents to audit:
```
agile-coach, delivery-manager, project-plan-tracker, team-progress-tracker
```

- [ ] **Step 1: Read frontmatter for all 4 agents**

- [ ] **Step 2: Run discovery for each agent**

Domain extraction:
- `agile-coach` → "agile AI", "scrum tools", "Jira AI", "Linear AI"
- `delivery-manager` → "delivery management AI", "release management tools"
- `project-plan-tracker` → "project tracking AI", "GitHub Projects", "Linear"

- [ ] **Step 3: Record findings** (same format as Task 1 Step 3)

- [ ] **Step 4: Update frontmatter** (same approach as Task 1 Step 4)

- [ ] **Step 5: Save findings to `./tmp/audit-project-management.md`**

- [ ] **Step 6: Commit**

```bash
git add agents/project-management/*.md
git commit -m "feat: add first_party_alternatives to project-management agents (audit #83)"
```

---

### Task 7: Audit `agents/sdlc/` (8 agents)

**Files:**
- Read: all 8 `.md` files in `agents/sdlc/`
- Modify: agents where alternatives are found

Agents to audit:
```
ai-first-kick-starter, framework-validator, language-go-expert,
language-javascript-expert, language-python-expert,
project-bootstrapper, retrospective-miner, sdlc-knowledge-curator
```

- [ ] **Step 1: Read frontmatter for all 8 agents**

- [ ] **Step 2: Run discovery for each agent**

Domain extraction:
- `language-python-expert` → "Python AI tools", "Ruff", "mypy", "Python MCP server"
- `language-javascript-expert` → "JavaScript AI tools", "ESLint AI", "TypeScript tools"
- `language-go-expert` → "Go AI tools", "Go MCP server", "golangci-lint"
- `retrospective-miner` → "retrospective AI", "agile retrospective tools"
- `project-bootstrapper` → "project scaffolding AI", "create-app tools", "cookiecutter"

- [ ] **Step 3: Record findings** (same format as Task 1 Step 3)

- [ ] **Step 4: Update frontmatter** (same approach as Task 1 Step 4)

- [ ] **Step 5: Save findings to `./tmp/audit-sdlc.md`**

- [ ] **Step 6: Commit**

```bash
git add agents/sdlc/*.md
git commit -m "feat: add first_party_alternatives to sdlc agents (audit #83)"
```

---

### Task 8: Compile Audit Report

**Files:**
- Create: `docs/audits/2026-04-05-agent-base-audit.md`
- Read: `./tmp/audit-*.md` (7 batch result files)

- [ ] **Step 1: Create the audits directory**

```bash
mkdir -p docs/audits
```

- [ ] **Step 2: Compile the report**

Read all 7 batch files from `./tmp/audit-*.md`. Compile into a single report at `docs/audits/2026-04-05-agent-base-audit.md` with this structure:

```markdown
# Agent Base Audit Report

**Date**: 2026-04-05
**Agents audited**: 62
**Alternatives found**: <N agents with at least one alternative>
**Frontmatter updated**: <N>

## Summary

| Category | Agents | Alternatives Found | Frontmatter Updated |
|----------|--------|-------------------|-------------------|
| core | 30 | <N> | <N> |
| ai-development | 9 | <N> | <N> |
| ai-builders | 5 | <N> | <N> |
| testing | 4 | <N> | <N> |
| documentation | 2 | <N> | <N> |
| project-management | 4 | <N> | <N> |
| sdlc | 8 | <N> | <N> |
| **Total** | **62** | **<N>** | **<N>** |

## Findings by Agent

<paste all findings from the 7 batch files, in category order>
```

Fill in all `<N>` values by counting the actual findings.

- [ ] **Step 3: Clean up temp files**

```bash
rm -rf ./tmp/audit-*.md
```

- [ ] **Step 4: Commit the report**

```bash
git add docs/audits/2026-04-05-agent-base-audit.md
git commit -m "docs: add agent base audit report (#83)

62 agents audited across 7 categories.
<N> agents have 1st-party alternatives recorded in frontmatter."
```

---

### Task 9: Sync Plugin Copies

**Files:**
- Sync: modified agents from `agents/` to their plugin copies in `plugins/sdlc-team-*/agents/`

- [ ] **Step 1: Identify which agents were modified**

```bash
git diff --name-only HEAD~8 -- agents/ | grep -v "audit"
```

This lists all agent files modified in the audit commits.

- [ ] **Step 2: For each modified agent, find its plugin copy using release-mapping.yaml**

Read `release-mapping.yaml` to find the source → plugin mapping. For each modified agent, copy it to the corresponding plugin directory:

- `agents/core/solution-architect.md` → `plugins/sdlc-team-common/agents/solution-architect.md`
- `agents/core/sdlc-enforcer.md` → `plugins/sdlc-core/agents/sdlc-enforcer.md`
- `agents/ai-development/mcp-server-architect.md` → `plugins/sdlc-team-ai/agents/mcp-server-architect.md`
- etc.

Not all agents have plugin copies (some are source-only). Only copy agents that appear in `release-mapping.yaml`.

- [ ] **Step 3: Verify sync**

For each copied agent:
```bash
diff agents/<category>/<agent>.md plugins/<plugin>/agents/<agent>.md
```

Expected: no output for each (files identical).

- [ ] **Step 4: Commit**

```bash
git add plugins/
git commit -m "chore: sync audited agents to plugin copies (#83)"
```

If no plugin copies needed updating, skip this commit.

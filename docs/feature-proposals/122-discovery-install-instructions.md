# Feature Proposal: Discovery Output — Add Installation Instructions

**Proposal Number:** 122
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `fix/discovery-install-instructions`
**Issue:** #122
**Type:** Bug fix

---

## Executive Summary

The 1st-party tool discovery process — used by both `pipeline-orchestrator` (during agent creation) and `setup-team` (during project setup) — finds relevant tools (Claude Code plugins, MCP servers, GitHub Actions, standalone repositories, libraries) and presents them in a tidy table. The table contains tool name + URL + description, but **no installation instructions**. The user is left to figure out how to install each tool, which is non-trivial because different tool types require completely different install paths (slash command for plugins, JSON snippet for MCP servers, YAML for GitHub Actions, clone+run for standalone tools, package manager for libraries).

This proposal classifies each found tool by category during discovery, then generates per-category installation instructions inline in the report. The user gets ready-to-copy install snippets per tool — no guessing, no additional research required.

---

## Motivation

### Problem statement

Steve ran a discovery and got back a perfectly useful list of tools:

```
| Tool                                                                                  | Why it matters here                                            |
|---------------------------------------------------------------------------------------|----------------------------------------------------------------|
| https://github.com/tdccccc/claude-security-audit                                      | Audits for malicious hooks/MCP/commands                        |
| https://github.com/HarmonicSecurity/claudit-sec                                       | macOS audit for MCP servers, plugins, scheduled tasks          |
| https://github.com/anthropics/claude-plugins-official/tree/main/plugins/mcp-server-dev | Official Anthropic MCP scaffolding plugin                      |
| https://gofastmcp.com/integrations/claude-code                                        | Python MCP framework for the planned server                    |
| https://github.com/anthropics/claude-code-action                                      | Official GitHub Action — relevant to the toggle workflow       |
```

Five tools, five different install paths:
- `claude-security-audit` → standalone repo, clone + run
- `claudit-sec` → standalone repo, clone + run
- `mcp-server-dev` → Claude Code plugin in `anthropics/claude-plugins-official`
- `gofastmcp` → Python library/framework
- `claude-code-action` → GitHub Action

The discovery report tells the user nothing about how to actually install or use any of them. To act on the discovery output, the user has to:
1. Visit each URL
2. Read the README
3. Figure out the tool category
4. Apply the right install pattern
5. Construct the right command/config/YAML themselves

That's exactly the friction the discovery is supposed to remove. Discovery without install instructions is discovery half-done.

### Root cause

The discovery report templates in both `pipeline-orchestrator.md` (line 88-100, before this fix) and `setup-team/SKILL.md` (line 110-140, before this fix) define columns/fields for tool *metadata* (Source / Tool / Publisher / Description / Status / Last Updated) but **no Install column or section**. The pipeline-orchestrator's step 9 says "Provide installation instructions" if the user picks "use as-is", but the format isn't specified anywhere and doesn't appear to be produced consistently.

### Why this matters now

We just merged the marketplace.json location fix (#120, PR #121) which finally makes plugin install actually work for new users. Discovery is now the *right* next step in onboarding — it's how a user with a project finds the tools they need. If discovery doesn't tell them how to install what it finds, the install path stays broken in spirit even if it works mechanically.

### User stories

- As a new user running setup-team, I want the discovered tools to come with copy-paste install commands so I can act on the discovery without further research
- As an experienced user invoking pipeline-orchestrator for agent creation, I want the discovery report to spell out exactly how to install each tool by category so I'm not reverse-engineering each one
- As the framework, I want to never invent install commands — if the right command is unknown, I want the agent to say "see README" rather than guessing

---

## Proposed Solution

Three changes to two files (plus their plugin copies):

### Change 1: Add tool category classification during discovery

Both `pipeline-orchestrator` and `setup-team` get a new step that classifies each found tool into one of seven categories:

| Category | Identifying signal |
|---|---|
| `claude-plugin` | Lives in a Claude Code plugin marketplace (has `.claude-plugin/marketplace.json`) |
| `mcp-server-npm` | npm package, runnable via `npx`, exposes MCP |
| `mcp-server-pip` | PyPI package, runnable via `python -m`, exposes MCP |
| `mcp-server-binary` | Pre-built binary distributed via GitHub releases, exposes MCP |
| `github-action` | GitHub Actions marketplace, used via `uses:` in workflow YAML |
| `standalone-cli` | Standalone repository, clone-and-run |
| `library-framework` | Foundation library used to build other tools (FastMCP, Anthropic SDK, etc.) |

### Change 2: Per-category installation instruction reference table

Both files get a reference table showing the exact install snippet format for each category. The agent/skill is instructed to:
- Use the exact format per category
- Never invent install commands
- If the install path is unknown or undocumented, write `Manual setup required. See <url>/README.md.`

The seven install formats:

- **`claude-plugin`** in `anthropics/claude-plugins-official`: `/plugin marketplace add` + `/plugin install` (with `claude-plugins-official` as the marketplace name)
- **`claude-plugin`** in another marketplace: same shape, marketplace name read from the repo's `.claude-plugin/marketplace.json` `name` field
- **`mcp-server-npm`**: JSON snippet for `.mcp.json` with `command: "npx"`, args `[-y, <package>]`, plus any required env vars
- **`mcp-server-pip`**: `pip install <package>` plus JSON snippet with `command: "python"`, `args: [-m, <module>]`
- **`mcp-server-binary`**: download instructions plus JSON snippet pointing at the binary path
- **`github-action`**: workflow YAML snippet with `uses: <owner>/<repo>@<version>` (pin to specific version, not @main)
- **`standalone-cli`**: `git clone` + `cd` + run command from README
- **`library-framework`**: `pip install` / `npm install` + docs link (with note that it's a foundation library, not a directly-invoked tool)

### Change 3: Update the discovery report template to include install instructions

The report template changes from a flat metadata table to a per-tool entry that includes:

```markdown
### {Tool Name}
- **Source**: {url}
- **Publisher**: {publisher}
- **Type**: {category}
- **Description**: {what it does}
- **Why it matters here**: {project relevance}
- **Status**: {Active | Stale | Archived}
- **Install**:
  ```
  {category-appropriate install snippet}
  ```
```

Same structure in both `pipeline-orchestrator` and `setup-team`.

### Files modified

1. `agents/core/pipeline-orchestrator.md` (source) — classification step + report template + reference table + example output
2. `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` (plugin copy) — same
3. `skills/setup-team/SKILL.md` (source) — classification rules in step 5c + reference table in new step 5c.1 + recommendation output format in step 7
4. `plugins/sdlc-core/skills/setup-team/SKILL.md` (plugin copy) — same

The example block in the pipeline-orchestrator's frontmatter is updated to demonstrate a discovery report with install instructions for two different tool categories (MCP server + Claude plugin), showing the user what they should expect.

---

## Success Criteria

- [ ] Both `pipeline-orchestrator.md` files include the seven-category classification step
- [ ] Both files include the per-category install instruction reference table
- [ ] Both files' discovery report templates include an Install field per tool
- [ ] Both `setup-team/SKILL.md` files include the same classification + reference + output format updates
- [ ] The example in pipeline-orchestrator demonstrates two tool categories with install snippets
- [ ] No active source files reference the old metadata-only output format
- [ ] CI passes
- [ ] Pre-push validation passes

---

## Manual verification (post-merge)

Run discovery against a real technology and verify the output includes install instructions:

```
# Via setup-team (project setup)
/sdlc-core:setup-team
# Provide a tech stack including, e.g., MongoDB
# Verify the recommended tools section shows install snippets per tool

# Via pipeline-orchestrator (agent creation)
@pipeline-orchestrator create a Stripe payments agent
# Verify the discovery report shows install snippets for any found Stripe tools
```

Each tool in the discovery output should have a copy-pasteable install snippet that the user can act on directly.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Agent classifies a tool into the wrong category and produces a wrong install snippet | User runs wrong commands; potential confusion or harm | Classification rules are explicit (in the agent body); the "if uncertain, say so" fallback prevents fabrication |
| Install snippets become outdated as tools evolve (e.g., npm package renamed) | User gets stale instructions | Discovery is always live (WebSearch + WebFetch); the agent reads current package names from current sources |
| The install snippet format itself becomes outdated as Claude Code's plugin/MCP/etc. systems evolve | All discovery outputs become wrong simultaneously | Snippets are in the agent body and can be updated in one place; future framework changes should update both files together |
| New tool categories emerge that don't fit the seven-category taxonomy | Future-proof gap | The "Manual setup required, see README" fallback handles unknown categories; new categories can be added to the reference table incrementally |
| Plugin copies of agents/skills drift from source | Stale install instructions in the shipped plugin | Both source and plugin copies are updated in the same commit; release-plugin keeps them in sync going forward |

---

## Out of scope

- Validating that any specific install snippet *actually* works against a real tool (the agent isn't a CI runner)
- Auto-installing tools on the user's behalf (the user always reviews and runs install commands themselves)
- Adding new tool categories beyond the seven listed (can be added later as needed)
- Updating historical retrospectives or feature proposals that mention the old discovery output format

---

## Changes Made

| Action | File |
|---|---|
| Modify | `agents/core/pipeline-orchestrator.md` |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` |
| Modify | `skills/setup-team/SKILL.md` |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` |
| Create | `docs/feature-proposals/122-discovery-install-instructions.md` (this file) |
| Create | `retrospectives/122-discovery-install-instructions.md` |

---

## References

- Issue: #122
- Related: #120 (the marketplace install path bug, fixed in PR #121) — discovery is the next step in onboarding once install works
- Related: pipeline-orchestrator agent (the discovery agent), setup-team skill (project-time discovery)

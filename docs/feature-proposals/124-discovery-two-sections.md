# Feature Proposal: Discovery Output — Two Sections and Mandatory Install Field

**Proposal Number:** 124
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `fix/discovery-two-sections`
**Issue:** #124
**Type:** Bug fix (follow-up to #122/#123)

---

## Executive Summary

Two related defects in the discovery output, discovered during post-merge verification of #123:

1. **The Install field is still not reliably produced** in the normal discovery flow. The #122/#123 fix added the instruction that every tool should have an install snippet, but phrased as template guidance — the agent could and did skip it. This fix makes the Install field an explicit MANDATORY requirement with a defined fallback.

2. **Project libraries are mixed with Claude Code environment tools** in one undifferentiated list. A library like `@modelcontextprotocol/sdk` (for *building* MCP servers) appears alongside a pre-built MCP server like `@mongodb/mcp-server` (which you install *into* Claude Code). These are fundamentally different — the user's action differs (edit `package.json` vs add `.mcp.json` entry) — but the output doesn't flag the difference. This fix splits the output into two explicit sections.

---

## Motivation

### Problem 1: Install field skipped

After #123 merged and plugins were reloaded (`/plugin marketplace update ai-first-sdlc` + `/reload-plugins`), Steve ran a discovery. The output was a list of tools with URLs and descriptions but no install instructions. He had to ask the agent explicitly to produce install commands — precisely the friction #122/#123 was supposed to remove.

Why did the fix not take effect? Root cause analysis:

- The #122/#123 instruction said: "Every tool gets an install instruction generated from its category using the reference formats below". That's **descriptive guidance** — it describes what the report should look like, but doesn't mark the Install field as mandatory. An agent producing output under context pressure can skip the field and still feel like it followed the instructions.
- There was no checklist item like "verify every tool has an Install field before presenting".
- There was no explicit fallback for "I don't know how to install this" — leaving the agent to either guess or omit.

### Problem 2: Project libraries mixed with environment tools

Steve's discovery output recommended `@modelcontextprotocol/sdk` ("Inside your Node MCP server project: `npm install @modelcontextprotocol/sdk`"). This is a valid recommendation — if you're building a custom MCP server, that's the library you use — but it doesn't belong in the same list as tools you install into Claude Code. The user's action is fundamentally different:

| Type | Where the install happens | Example |
|---|---|---|
| Claude Code environment tool | Claude Code itself (slash command, `.mcp.json`, workflow YAML, alongside-Claude-Code CLI) | Install `@mongodb/mcp-server` via `.mcp.json` |
| Project library | User's own project source code (`package.json`, `requirements.txt`, `pyproject.toml`) | Add `@modelcontextprotocol/sdk` to a new MCP server project |

Mixing them produces three failure modes:
1. Users try to install a project library in Claude Code and it fails
2. Users think they've completed setup when they've only added project libraries (Claude Code is still unconfigured)
3. Users skip useful recommendations because they can't tell which ones apply to their situation

The #122/#123 fix had `library-framework` as a category but left it in the same output section as the others. That was wrong. It needs its own section with clear framing.

### User stories

- As a user running discovery, I want Claude Code environment tools and project libraries clearly separated so I know which ones to install in Claude Code vs which to add to my project's code
- As a user who just got a discovery report, I want install instructions for every recommendation without having to ask — the report is the deliverable, not a list to follow up on
- As the framework, I want the agent's output format to be enforced by explicit mandatory rules, not by descriptive templates the agent can skip under pressure

---

## Proposed Solution

Three changes to both `pipeline-orchestrator` and `setup-team` (source + plugin copies).

### Change 1: Two-section report structure

The discovery output splits into two explicit sections, each with its own heading and framing text:

```markdown
## Discovery Report: {Technology}

## Section A: Claude Code Environment Tools

Install these INTO Claude Code to extend its capabilities.

### {Tool 1 Name}
- (fields including mandatory Install)
...

## Section B: Project Dependencies

These are libraries and frameworks you would add to your OWN project's source code if you're building something (custom MCP server, custom agent, app calling Claude). They are NOT installed in Claude Code.

### {Library 1 Name}
- (fields including mandatory Install with explicit "(in your project, not in Claude Code)" framing)
...

## Coverage Assessment
...
```

If either section has no entries, the section heading still appears with a one-line note (`_No Section A tools found for {technology}._`). Sections are always visible so the structure is consistent.

### Change 2: Category → section mapping

The seven categories from #122 each map to exactly one section:

| Category | Section |
|---|---|
| `claude-plugin` | A |
| `mcp-server-npm` | A |
| `mcp-server-pip` | A |
| `mcp-server-binary` | A |
| `github-action` | A (Claude Code-specific, e.g. `anthropics/claude-code-action`) |
| `standalone-cli` | A |
| `library-framework` | **B** |

The critical distinction between `mcp-server-npm` (Section A) and `library-framework` (Section B) is made explicit with a concrete example:

- `@modelcontextprotocol/server-filesystem` → pre-built MCP server → Section A, install via `.mcp.json`
- `@modelcontextprotocol/sdk` → library for *building* MCP servers → Section B, `npm install` in the user's own project

The agent is told to ask: "Does the user run this as-is alongside Claude Code, or do they import it in code they're writing themselves?" Running as-is = A. Importing in their own code = B.

### Change 3: Mandatory Install field with explicit fallback

The instruction changes from template guidance to an explicit mandatory rule:

> **MANDATORY PER TOOL**: You MUST populate the `Install` field for every tool in both Section A and Section B. If you cannot determine the install path with confidence, write exactly: `Manual setup required. See <url>/README.md.` — never omit the field. A discovery report with any missing `Install` field is incomplete and must be regenerated before presenting to the user.

The phrasing is designed to be checklist-style: the agent should be able to verify "does every tool have an Install field?" as a yes/no check before presenting the output.

### Files modified

- `agents/core/pipeline-orchestrator.md` (source)
- `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` (plugin copy)
- `skills/setup-team/SKILL.md` (source)
- `plugins/sdlc-core/skills/setup-team/SKILL.md` (plugin copy)

The example block in `pipeline-orchestrator`'s frontmatter is updated to demonstrate a report with both Section A and Section B populated (one Claude Code tool + one project library), so the agent has a concrete reference for the expected output shape.

---

## Success Criteria

- [ ] Both `pipeline-orchestrator.md` files have the two-section report structure
- [ ] Both `setup-team/SKILL.md` files have the same two-section structure
- [ ] The Install field is explicitly marked MANDATORY with the "Manual setup required, see README" fallback
- [ ] `library-framework` category routes to Section B in all four files
- [ ] The example in pipeline-orchestrator demonstrates both sections with real tools
- [ ] The `mcp-server-npm` vs `library-framework` distinction is explicit with a concrete example
- [ ] Plugin copies updated to match source
- [ ] CI passes
- [ ] Pre-push validation passes

---

## Manual verification (post-merge)

This is the verification that #123 lacked. After merge:

1. Refresh plugins: `/plugin marketplace update ai-first-sdlc` + `/reload-plugins`
2. Run discovery on a real tech stack: `@pipeline-orchestrator find tools for working with MongoDB` (or any technology with both pre-built MCP servers and popular client libraries)
3. Verify the output:
   - [ ] Has both Section A and Section B headings (even if one is empty)
   - [ ] Every tool in Section A has a populated Install field
   - [ ] Every library in Section B has a populated Install field, explicitly framed as "in your project, not in Claude Code"
   - [ ] A library like `mongodb` (the Node.js driver) lands in Section B, not Section A
   - [ ] A pre-built MCP server like `@mongodb/mcp-server` lands in Section A
4. If any tool is missing an Install field, the fix is incomplete and needs another iteration

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| The agent still skips the Install field despite the MANDATORY phrasing | Third attempt at the same bug | Adversarial testing — run discovery on multiple tech stacks, verify no missing Install fields. If it still happens, the fix is structural (the agent reads the file but doesn't treat markdown emphasis as binding) and we need a different approach. |
| The Section A vs Section B distinction is unclear for edge cases (e.g., a CLI that's also a library) | User confusion | The "Does the user run this as-is or import it in their own code?" rule resolves most cases. Edge cases get classified by the "primary use" heuristic. If common tools consistently fall between, add a third section. |
| Users who only want Claude Code tools get distracted by Section B | Minor friction | Section B has explicit framing ("These are NOT installed in Claude Code"). Users who don't care can skip the section. |
| Plugin copies drift from source | Stale behaviour in installed plugins | Both source and plugin copies updated in the same commit. Same lesson from #120 and #122. |

---

## Out of scope

- Adding an eighth category for hosted SaaS APIs (flagged in #122's retrospective; still out of scope here)
- Automating adversarial testing of discovery output (would require a test harness that runs discovery against known tech stacks and verifies the output format — valuable but separate work)
- Updating historical retrospectives or feature proposals

---

## Changes Made

| Action | File |
|---|---|
| Modify | `agents/core/pipeline-orchestrator.md` |
| Modify | `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` |
| Modify | `skills/setup-team/SKILL.md` |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` |
| Create | `docs/feature-proposals/124-discovery-two-sections.md` (this file) |
| Create | `retrospectives/124-discovery-two-sections.md` |

---

## References

- Issue: #124
- Prior fix: #122/#123 (added install instructions category/format but left them optional and mixed the sections)
- Prior fix: #120/#121 (marketplace.json location — the broader pattern of user-facing path bugs surviving merge)

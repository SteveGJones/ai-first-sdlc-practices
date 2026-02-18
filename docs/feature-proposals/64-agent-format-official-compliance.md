# Feature Proposal: Agent Format Official Claude Code Compliance (#64)

**Target Branch:** `feature/agent-format-official-compliance`
**Date:** 2026-02-10
**Author:** AI Investigation Team (with specialist consultation from solution-architect, sdlc-enforcer, and code-review-specialist agents)

## Motivation

A collaborative team audit of all 71 agent files against the official Claude Code sub-agent specification (https://code.claude.com/docs/en/sub-agents) revealed significant format divergence. Our agents use custom fields (`examples`, `color`, `maturity`) that aren't in the official spec, the `tools` field uses YAML lists instead of the documented comma-separated string format, and we're missing 7 official optional fields entirely.

This directly caused the download validity failures investigated in PR #63 — when agents are installed in external projects, non-standard frontmatter fields can cause validation failures.

## Investigation Findings

### Format Compliance Audit Results

| Metric | Value |
|--------|-------|
| Total agents audited | 71 |
| Agents with non-standard `tools` format | 29 (26 YAML list, 2 comma-sep, 1 JSON array) |
| Agents with `examples` (not official) | 71/71 |
| Agents with `color` (not official frontmatter) | 71/71 |
| Agents with `maturity` (not official) | 70/71 |
| Agents missing `tools` (intentional inherit) | 42/71 |
| Official fields we don't support | 7 (`disallowedTools`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`) |

### Key Gaps

1. **tools format**: Official spec uses comma-separated strings (`tools: Read, Glob, Grep, Bash`), we use YAML lists
2. **Custom fields**: `examples`, `color`, `maturity`, `version`, `category`, `priority`, `tags` are not in the official spec
3. **Missing official fields**: No support for `disallowedTools`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`
4. **model values**: Official includes `inherit` (the default); our validator rejects it

## Proposed Solution

### 1. New Official Compliance Validator
Create `tools/validation/validate-agent-official.py` with dual-mode validation:
- `--mode official`: Validates against official Claude Code spec only (for agents being exported)
- `--mode project`: Validates official spec plus project extension fields (for this repo)

### 2. Restructure AGENT-FORMAT-SPEC.md
Clearly separate "Official Claude Code Frontmatter" from "Project Extension Fields" so users understand which fields are standard and which are our additions.

### 3. Reformat All 71 Agents
- Reorder frontmatter: official fields first, then project extensions
- Convert `tools` to comma-separated string format
- No content changes — frontmatter only

### 4. Automatic Validation Hook
Create a PostToolUse hook that validates agent files when created/edited, catching format errors before CI.

### 5. Update CI Workflow
Replace inline validation Python in `template-compliance.yml` with the new validator.

## Success Criteria

- [ ] All 71 agents pass official-mode validation
- [ ] All 71 agents pass project-mode validation
- [ ] New validator supports --audit, --fix, --json modes
- [ ] AGENT-FORMAT-SPEC.md clearly documents official vs project fields
- [ ] Canonical agent template created matching official format
- [ ] PostToolUse hook validates agent files automatically
- [ ] CI workflow uses new validator
- [ ] Feature proposal and retrospective created

## Impact Assessment

**Risk**: Low — frontmatter-only changes to agents, no prompt content modified
**Effort**: Medium — 71 files to reformat, new validator to build
**Value**: High — ensures agents work correctly when downloaded to any Claude Code project

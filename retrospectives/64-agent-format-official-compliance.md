# Retrospective: Agent Format Official Claude Code Compliance (#64)

**Branch:** `feature/agent-format-official-compliance`
**Date:** 2026-02-10
**Feature:** Full audit of all agents against the official Claude Code sub-agent specification, with automatic enforcement via a new validator and PostToolUse hook. Collaborative investigation with specialist consultation from solution-architect, sdlc-enforcer, and code-review-specialist agents.

## What Went Well

1. **Official spec research was decisive**: Fetching the official Claude Code documentation (https://code.claude.com/docs/en/sub-agents) provided the definitive source of truth, ending speculation about which fields are standard vs custom.

2. **Dual-mode validation design**: Creating `--mode official` and `--mode project` in the validator lets us validate for different contexts — strict Claude Code compliance for export, and extended validation for this repository.

3. **Auto-fix tooling**: The `--fix` flag on the new validator converted all 27 YAML-list `tools` fields to comma-separated strings in one command, avoiding manual edits across 27 files.

4. **Zero breakage**: All 72 agents pass both official and project validation after the format changes. The legacy validator (`validate-agent-format.py`) was updated to accept both tools formats so it remains backwards-compatible.

5. **PostToolUse hook for proactive enforcement**: The hook validates agent files at write-time, not just at CI time, catching format errors immediately when agents are created or modified.

## What Could Be Improved

1. **Frontmatter reorder was abandoned**: The initial plan included reordering frontmatter fields (official first, then project extensions). The reorder script failed on agents with the old `<example>` string format because it confused top-level fields with content inside multi-line YAML strings. This is cosmetic and doesn't affect functionality, but it means field ordering is inconsistent across agents.

2. **Three tools format variants existed**: We discovered comma-separated (2), YAML list (26), and JSON array (1) formats in use. This inconsistency should have been caught when the `tools` field was first introduced.

3. **Hook is documented but not auto-installed**: The PostToolUse hook requires manual addition to `.claude/settings.local.json`. A future enhancement could have the setup scripts configure this automatically.

## Lessons Learned

1. **Official documentation is the single source of truth**: Our `AGENT-FORMAT-SPEC.md` had diverged from the actual Claude Code specification over time. Regular alignment checks against upstream docs prevent specification drift.

2. **Custom fields should be clearly labeled as extensions**: By separating "Official Claude Code Fields" from "Project Extension Fields" in the spec, it's immediately clear which fields are portable and which are project-specific.

3. **Auto-fix tools save time and reduce errors**: The `--fix` flag converted 27 files without manual intervention. Building fix capabilities into validators pays off when operating at scale.

4. **YAML string parsing is fragile**: The `<example>` format used in some agents creates multi-line YAML strings that look like top-level fields to naive parsers. This is why the reorder script failed and had to be abandoned.

## Key Metrics

| Metric | Value |
|--------|-------|
| Agents audited | 72 |
| Agents passing official-mode | 72/72 (100%) |
| Agents passing project-mode | 72/72 (100%) |
| Tools format fixed (YAML list → comma-sep) | 27 |
| Invalid color values fixed | 2 (gold → yellow) |
| Invalid maturity values fixed | 1 (research → beta) |
| New validator created | validate-agent-official.py |
| PostToolUse hook created | validate-agent-hook.py |
| Official fields added to spec | 7 (disallowedTools, permissionMode, maxTurns, skills, mcpServers, hooks, memory) |
| Spec version | v1.4.0 → v2.0.0 |
| CI workflow modernized | Inline Python → dedicated validator |

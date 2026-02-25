# Feature Proposal: Catalog Generator Fixes & Tooling

**Proposal Number:** 67
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-02-10
**Target Branch:** `feature/catalog-and-sync-fixes`

---

## Executive Summary

Fix the AGENT-INDEX.md generator to produce clean capabilities and exclude template agents, create an agent sync script for `.claude/agents/`, add a broken-reference checker, and update the CLAUDE.md redirect.

---

## Motivation

### Problem Statement

- AGENT-INDEX.md capabilities contain raw markdown (`'<example>`, backtick commands) from regex-based extraction
- Template agents (`project-strategy-orchestrator`, `team-assembly-orchestrator`) appear in the catalog as real agents
- No automated way to sync `.claude/agents/` with `agents/` source tree
- No tooling to detect broken file references after deletions

### User Stories

- As a developer browsing agents, I want clean capability descriptions without markdown artifacts
- As a maintainer deleting files, I want to find all broken references before pushing

---

## Proposed Solution

1. Fix `build-agent-catalog.py` to extract capabilities from YAML frontmatter examples
2. Add `"templates" not in f.parts` to template filter
3. Create `sync-claude-agents.py` for automated agent sync
4. Create `check-broken-references.py` for reference validation
5. Update `CLAUDE.md` to mention CONSTITUTION.md

### Acceptance Criteria

Given the AGENT-INDEX.md contains raw markdown in capabilities
When the catalog generator is fixed and regenerated
Then no capabilities contain `'<example>`, raw backtick commands, or multi-sentence prose

Given template agents appear in the catalog
When the filter is fixed
Then agent count drops from 70 to 68 with no template agents listed

Given no sync tooling exists
When sync-claude-agents.py is created
Then running it with --dry-run shows sync status without modifying files

---

## Success Criteria

- [ ] AGENT-INDEX.md has clean capabilities from YAML examples
- [ ] No template agents in catalog (68 agents, not 70)
- [ ] sync-claude-agents.py works with --dry-run flag
- [ ] check-broken-references.py reports zero broken refs in active files
- [ ] CLAUDE.md mentions CONSTITUTION.md
- [ ] All Python files compile

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Some agents lack YAML examples | Low | Falls back to cleaned regex extraction |
| Broken-ref checker false positives | Medium | Exclude historical directories |

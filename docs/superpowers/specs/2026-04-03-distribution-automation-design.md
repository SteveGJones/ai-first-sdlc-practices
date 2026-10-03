# Distribution & Automation — Design Spec (Phase 4)

**Date**: 2026-04-03
**Status**: Draft
**Feature**: #73
**Branch**: `feature/distribution-automation`
**Depends on**: Phase 3 (Feature #72) merged

## Problem

The release pipeline requires manual execution of the release-plugin skill. Documentation still presents direct tool usage as the primary method. There's no CI automation for publishing plugin releases.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope | CI release + documentation deprecation only | MCP server and enterprise lockdown are premature |
| Release trigger | Git tag (v*) | Standard release workflow, aligns with SemVer |
| Release script | Python (not skill) | CI needs executable script, not Claude skill |
| Documentation approach | Plugin-first, tools as "advanced" | Gradual deprecation, not removal |

## CI-Driven Release

### Release Script

`tools/automation/release-plugins.py` — Python script that:
1. Reads `release-mapping.yaml`
2. Copies source files into plugin directories (same logic as release-plugin skill)
3. Validates all plugin manifests
4. Reports what changed

This is the executable version of the release-plugin skill. The skill remains for interactive use; the script is for CI.

### GitHub Action

`.github/workflows/plugin-release.yml`:
- **Trigger**: Push of tag matching `v*`
- **Steps**:
  1. Checkout repo
  2. Run `python tools/automation/release-plugins.py`
  3. Validate all plugin manifests (JSON valid, required fields present)
  4. Verify agent counts match release-mapping.yaml
  5. Create GitHub release with auto-generated changelog
- **Does NOT push changes** — the release script verifies that plugins are already up-to-date (they should be committed before tagging)

### Release Workflow

```
Developer: update source files (agents/, skills/, tools/)
Developer: run /sdlc-core:release-plugin (interactive) or script (CLI)
Developer: commit plugin changes
Developer: git tag v1.1.0
CI: validates plugins match source, creates GitHub release
```

## Documentation Updates

### CLAUDE.md Changes

- Move "Plugin Installation (Recommended)" section above "Validation" section
- Rename "Validation" section to "Validation (Direct Tool Access)"
- Add note: "If you have sdlc-core installed, use `/sdlc-core:validate` instead"
- Keep all direct tool commands (they're still valid for source-level development)

### CLAUDE-CORE.md Changes

- Add plugin skill equivalents alongside each manual command
- Add "Plugin Skills" column to the context loading table

### Migration Guide

Create `docs/guides/migrating-to-plugins.md`:
- Why plugins (versioning, distribution, auto-loading)
- How to install (marketplace add, plugin install)
- Skill equivalents for each manual command
- When to use direct tools (framework development, source-level work)

## Deliverables

1. `tools/automation/release-plugins.py` — release script
2. `.github/workflows/plugin-release.yml` — CI workflow
3. Updated CLAUDE.md — plugin-first documentation
4. Updated CLAUDE-CORE.md — skill equivalents
5. `docs/guides/migrating-to-plugins.md` — migration guide
6. Feature proposal + retrospective

## Success Criteria

- [ ] `python tools/automation/release-plugins.py` packages plugins correctly
- [ ] GitHub Action runs on tag push and validates plugins
- [ ] CLAUDE.md presents plugins as primary installation method
- [ ] Migration guide explains transition from direct tools to skills
- [ ] Direct tool workflow still documented and functional

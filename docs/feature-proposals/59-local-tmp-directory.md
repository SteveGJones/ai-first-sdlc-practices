# Feature Proposal: Replace /tmp with ./tmp for Claude Code Compatibility

## Problem Statement
Claude Code requires additional user permissions to access `/tmp` (system temp directory) but not `./tmp` (project-local). Using `/tmp` also risks cross-session file collisions when two Claude Code sessions write to the same temp path.

## Proposed Solution
Replace all `/tmp/` references in agent files with `./tmp/` (project-local), add `tmp/` to `.gitignore`, and create enforcement via pre-commit hook and CI check to prevent `/tmp/` from creeping back in.

## Changes Required
1. Add `tmp/` to `.gitignore`
2. Create `tools/validation/check-tmp-usage.py` enforcement script
3. Replace `/tmp/` with `./tmp/` in `agents/v3-setup-orchestrator.md` (~30 occurrences)
4. Replace `/tmp/` with `./tmp/` in `agents/core/pipeline-orchestrator.md` (6 occurrences)
5. Wire enforcement into `.pre-commit-config.yaml` and CI workflows
6. Document the rule in `CLAUDE-CORE.md`

## Success Criteria
- Zero `/tmp/` references in agent/template files (enforced by check-tmp-usage.py)
- Pre-commit hook and CI check prevent future violations
- Rule documented in CLAUDE-CORE.md FORBIDDEN section

# Retrospective: Feature #67 — Catalog Generator Fixes & Tooling

**Branch**: `feature/catalog-and-sync-fixes`
**Date**: 2026-02-10

## What Went Well

- **YAML frontmatter for capabilities**: Extracting `examples[].context` from YAML produces clean, human-readable capabilities — far better than the regex approach that captured raw markdown
- **Template filter was a one-liner**: Adding `"templates" not in f.parts` cleanly excluded the templates directory
- **Sync script is minimal**: 60 lines, does exactly one thing, supports --dry-run
- **Broken-reference checker is useful**: Even at v1, it found 106 real broken references across 31 files (aspirational doc links, setup-script path mismatches)

## What Could Improve

- **False positive tuning took iteration**: The broken-reference checker needed 3 rounds of refinement — initial run found 868 "broken" refs, mostly false positives from template/example content and Python scripts referencing runtime files
- **User-project file exclusion list is large**: The exclusion set grew to 60+ filenames — a pattern-based approach (e.g., skip all `.json` refs in Python files) might be cleaner

## Lessons Learned

1. **YAML frontmatter is the right data source**: Agent files already have structured metadata — parsing it is always better than regex extraction from prose
2. **Reference checking in a framework repo is hard**: This repo describes how to set up *other* projects, so most file references are to files that exist at runtime in user projects, not in this repo
3. **Incremental exclusion lists work**: Starting with zero exclusions and adding categories based on actual false positives produces a well-tuned checker

## Changes Made

- `tools/automation/build-agent-catalog.py`: Extract capabilities from YAML examples, exclude templates directory
- `AGENT-INDEX.md` + `AGENT-CATALOG.json`: Regenerated with clean data (68 agents)
- `tools/automation/sync-claude-agents.py`: New — syncs agents/ to .claude/agents/
- `tools/validation/check-broken-references.py`: New — detects broken file references
- `CLAUDE.md`: Updated redirect to mention CONSTITUTION.md

## Action Items

- [ ] Address the 106 real broken references found by the checker (separate feature)
- [ ] Consider adding check-broken-references.py to CI pipeline

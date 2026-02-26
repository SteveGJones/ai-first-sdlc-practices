# Retrospective: Feature #68 — Fix Broken File References

**Branch**: `feature/fix-broken-references`
**Date**: 2026-02-10

## What Went Well

- **Systematic approach**: Running the checker first, categorizing all 106 refs, then fixing by category made the work clean and predictable
- **Most fixes were straightforward**: Removing links to never-created docs, updating paths to archived files, and adding full path prefixes were all simple edits
- **Checker improvements were highly effective**: Went from 72 remaining (after doc fixes) to 0 with well-targeted exclusion categories
- **Anchor fragment stripping** was a key fix — the checker was failing on valid links like `file.md#section` because it tried to resolve the full string as a filename

## What Could Improve

- **The initial checker (Feature #67) should have handled these categories from the start**: setup-smart.py exclusion, .sdlc/ paths, SDLC level filenames — these were predictable false-positive categories
- **Some "broken" refs were aspirational docs** (HALL-OF-FAME.md, celebration-guide.md) that represent planned features — the framework needs a convention for marking planned-but-not-yet-created content

## Lessons Learned

1. **Framework repos have unique reference challenges**: This repo describes how to set up OTHER projects, so many file references point to files that exist at runtime in user projects, not in this repo
2. **Exclusion lists need categories, not just filenames**: Grouping exclusions into USER_PROJECT_FILES, SDLC_LEVEL_FILES, EXCLUDED_FILES, etc. makes the checker maintainable
3. **Strip anchors before resolution**: Always normalize references before attempting filesystem resolution — `file.md#section` should resolve against `file.md`
4. **setup-smart.py is a special case**: As a bootstrap script that creates files, nearly every string reference in it points to a file it will create, not one that exists now

## Changes Made

- `docs/README.md`: Removed 13 broken links to never-created docs (SETUP-GUIDE.md, FAQ.md, TROUBLESHOOTING.md, etc.)
- `docs/FRESH-AI-TO-LEGENDARY-TEAM-SYSTEM.md`: Removed references to 4 nonexistent coaching scripts
- `docs/FRESH-AI-ONBOARDING.md`: Fixed anchor fragment references
- `docs/HARSH-ENFORCEMENT-IMPLEMENTATION.md`: Updated SDLC-RULES-SUMMARY.md → CONSTITUTION.md
- `docs/A2A-SYSTEM-SUMMARY.md`: Updated path to archived tactical discussion
- `agents/core/agent-builder.md`: Added `templates/reference-agents/` prefix to 7 archetype references
- `docs/AGENT-CREATION-GUIDE.md`: Same prefix fix for 5 archetype references
- `CONTRIBUTING.md`: Removed reference to nonexistent test file
- `docs/FRAMEWORK-COMPLIANCE-POLICY.md`: Removed reference to deleted utility script
- `tools/validation/check-broken-references.py`: Major improvements — anchor stripping, setup-smart.py exclusion, SDLC level files, .sdlc/.claude/ paths, broader search paths

## Metrics

- **Before**: 106 broken references across 31 files (initial Feature #67 finding)
- **After doc fixes**: 72 remaining (34 genuinely fixed)
- **After checker improvements**: 0 remaining
- **False positive reduction**: 72 → 0 through 6 new exclusion categories

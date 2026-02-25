# Retrospective: Documentation Cleanup and Reorganisation

**Branch**: feature/documentation-review

## What Went Well

- Full-team review approach (4 parallel specialist agents) provided comprehensive coverage across root files, docs/ structure, instruction files, and user onboarding
- CI constraint analysis before planning prevented potential failures (CLAUDE.md required by comprehensive-validation.yml, check-instruction-size.py dependencies)
- Using `git mv` for archival preserves file history while cleaning up the directory structure
- Review files created in ./tmp/reviews/ provided clear evidence base for every decision

## What Could Improve

- Documentation debt should be addressed incrementally during each PR, not allowed to accumulate across 45+ root files
- Session artifact files (REBOOT-CONTEXT, CONTINUATION-CONTEXT) should have enforcement to prevent committing temporary handoff files
- Feature proposal numbering conflicts (6 duplicate numbers) were identified but deferred — should be addressed in a follow-up PR

## Lessons Learned

- Framework evolution through multiple paradigm shifts requires explicit deprecation and cleanup at each transition
- CI validation scripts create hidden dependencies on specific files — always check before deleting
- A deprecated file that still contains content creates confusion regardless of how prominent the deprecation warning is
- References to non-existent scripts erode trust in documentation — either implement or remove

## Changes Made

### Phase 1 (Prior Session)
- Created `docs/archive/` directory structure (4 subdirectories)
- Deleted 6 files (3 session artifacts, 2 redundant team-first, 1 orphaned proposal stub)
- Archived 32 files to docs/archive/ via git mv (15 from root, 17 from docs/)
- Gutted CLAUDE.md from 856 lines to 10-line redirect
- Updated docs/README.md with 4 corrected archive links
- Removed CLAUDE-CONTEXT-agents.md from setup-smart.py ESSENTIAL_FILES
- Removed 3 non-existent script references from SDLC-RULES-SUMMARY.md

### Phase 2 (Current Session)
- Deleted CLAUDE-CONTEXT-language-validators.md (99% duplicate of LANGUAGE-SPECIFIC-VALIDATORS.md)
- Updated setup-smart.py, migrate-to-hierarchical.py, check-instruction-size.py references
- Fixed 3 broken template links in docs/README.md (design-doc-template, feature-proposal-template, retrospective-template)
- Fixed phantom reference to CLAUDE-CONTEXT-agents.md in CLAUDE-CORE.md and CLAUDE-CORE-PROGRESSIVE.md (now points to AGENT-INDEX.md)
- Archived CLAUDE-TEAM-FIRST.md (70% overlap with CLAUDE-CORE.md)
- Merged AGENTIC-SDLC-TEAM-PRINCIPLES.md + AGENTIC-TEAM-COLLABORATION-PROTOCOLS.md into AGENTIC-TEAM-STANDARDS.md
- Updated 4 files referencing old AGENTIC filenames
- Archived AGENT-INSTRUCTION-UPDATES.md (zero references)
- Moved AGENT-INSTALLATION-GUIDE.md, AI-AUTONOMY.md, AGENT-MEMORY-BANK.md to docs/
- Moved START-HERE.md to docs/ (coaching doc, not a true quickstart)
- Updated README.md and docs/README.md path references
- Root-level .md files reduced from 26 to 18 (31% reduction)

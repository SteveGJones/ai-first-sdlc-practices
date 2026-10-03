# Retrospective: Cross-Library KB Query — Phase B Priming

**Issue:** #168 (sub-2 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** Complete

## What went well

- Smaller scope than Phase A (7 tasks vs 17). All 7 tasks completed without rework loops.
- The `format_dispatch_prompt` helper cleanly DRYed the prompt format across orchestrator, kb-query skill, and librarian agent — three places that previously duplicated the format are now consistent.
- Phase A regression caught at the start of Phase B (commit 557d521). Restored both root and plugin-dir versions of all 6 affected files before any new work began.
- Code reviewer caught the Step 4 leftover (`priming=None` artifact) during Task 3 review; addressed it as part of Task 4 rather than letting it ship.
- Active-use librarian instructions are concrete and actionable (3 numbered rules, with backwards-compatibility fallback).

## What was harder than expected

- Phase A's plugin-dir vs root-source confusion caused a regression that almost shipped silently. Discovering it required spot-checking the post-Phase-A state at the start of Phase B.
- Updating the kb-query skill's Step 3 with the helper-based form required preserving Step 4's reference to `priming` (which was previously `None`). Caught and fixed during Task 4.

## What surprised us

- The `feedback_release_plugin_sync.md` memory entry already captured the exact lesson Phase A violated. Memory exists for a reason — reading it before starting work is on the worker.
- The `format_dispatch_prompt` extraction was easier than expected because Phase A's PrimingBundle dataclass was clean and json.dumps handled multi-line/special-character content without escaping issues.

## What we'd do differently next time

- Add a pre-task checklist for any plugin-file edit: "Is this file in release-mapping.yaml? If yes, edit root source first, then mirror to plugin-dir, then run check-plugin-packaging.py before commit."
- Consider running `check-plugin-packaging.py` at the END of every task involving plugin files, not just at packaging-related tasks.

## Metrics

- Implementation time: 1 session (2026-04-24)
- Tests added: 5 new (4 in Task 1, 1 in Task 5) → 57 total kb tests passing
- Commits on branch for this sub-feature: 7 task commits + 1 plan commit + 1 regression-fix commit = 9 commits for Phase B
- Validation pipeline pass status: 9/10 — pre-commit binary missing (env issue only; same pattern as Phase A); all code-quality checks pass

## Decisions worth capturing in memory

- `format_dispatch_prompt` is the single source of truth for the librarian dispatch format — orchestrator tests, kb-query skill, and librarian agent prompt must all stay aligned with it. Future format changes should hit this helper first.
- Plugin-dir vs root-source pattern: NEVER edit `plugins/<plugin>/<file>` directly when the same file is in `release-mapping.yaml` with a separate root source. Edit the root, mirror, verify with check-plugin-packaging.py.

# Feature Proposal: sdlc-knowledge-base v0.3.0 — Operator Experience + Scale

**Proposal Number:** 197
**Status:** Complete
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-05-03
**Target Branch:** `feature/kb-v030-operator-experience`
**EPIC:** #197 (sdlc-knowledge-base v0.3.0 operator experience + scale)
**Sub-issues:** #154, #155, #161, #162, #163, #165, #196

## Summary

Closes seven sub-issues across three phases that address operator experience gaps surfaced by the Amkor AI Strategy engagement. Phase A hardened the indexing infrastructure (programmatic rebuild, agent-only enforcement). Phase B added layer taxonomy management, batch ingestion, and a statistics dashboard. Phase C added two-dimensional confidence metadata and auto-fix for mechanical lint violations.

## Sub-features by Phase

### Phase A (PR #198 initial scope)
| # | Title | Status |
|---|---|---|
| #155 | Programmatic index rebuild (`build_shelf_index.py`) | Done |
| #196 | Agent-only enforcement for kb-* skills | Done |

### Phase B
| # | Title | Status |
|---|---|---|
| #154 | Layer tags + project-configurable layer set + `kb-layers` skill | Done |
| #161 | `kb-prepare-batch` + `kb-ingest-batch` batch ingestion pipeline | Done |
| #162 | `kb-stats` library statistics dashboard | Done |

### Phase C
| # | Title | Status |
|---|---|---|
| #163 | Confidence metadata (two-dimensional: source quality × query relevance) | Done |
| #165 | `kb-lint --auto-fix` for mechanical violations | Done |

## Motivation

Amkor AI Strategy engagement surfaced six operator experience gaps (#161–#166). The sdlc-knowledge-base plugin worked for individual developers but lacked the tooling for teams managing larger libraries: no programmatic index rebuild (required LLM), no taxonomy governance, no bulk ingestion, no quality signals, no statistics. v0.3.0 closes these gaps.

## Proposed Solution

### Phase A
- `build_shelf_index.py`: pure-Python script (no LLM invocation) with hash-tracking
- `kb-rebuild-indexes`: rewritten as thin Bash wrapper over the Python script
- `CLAUDE-CONTEXT-knowledge-base.md`: agent-only rule + routing table
- 8 kb-* skills: guardrails added so only agents dispatch them

### Phase B
- `kb_config.py`: `allowed_layers()` reads `layers:` from CLAUDE.md `[Knowledge Base]` section
- `kb_layers.py`: list/add/remove operations with atomic CLAUDE.md write and safety guards
- `kb_stats.py`: reads shelf-index + log.md, outputs 5 sections with markdown tables
- `kb_prepare_batch.py`: stages files into `library/raw/` with markitdown/pandoc conversion
- `kb_ingest_batch.py`: resume-capable batch dispatch with `BATCH_MODE: create-only`
- `build_shelf_index.py` extended: `layer` field + `**Layer:**` in rendered index entries

### Phase C
- `confidence.py`: `combine_confidence()` combination table, `check_confidence_compliance()`
- `kb_lint_fix.py`: mechanical auto-fix (missing layer/confidence/cross_references, stub frontmatter)
- `build_shelf_index.py` extended: `confidence` field + `**Confidence:**` in rendered entries
- `kb_stats.py` extended: confidence distribution section
- `kb-lint`: `--strict-confidence` + `--auto-fix` flags
- CI: `kb-compliance` job checks both layer and confidence compliance against starter-pack library

## Success Criteria

- [x] Phase A: 34 new tests (594 → 628), `build_shelf_index.py` pure-Python with full test coverage
- [x] Phase B: 86 new tests (628 → 714), all 4 new skills operational, layer compliance in CI
- [x] Phase C: 43 new tests (714 → 757), confidence metadata end-to-end, auto-fix operational
- [x] Plugin packaging verified: `check-plugin-packaging.py` passes
- [x] Retrospective complete: `retrospectives/197-kb-v030-operator-experience.md`

## Plans

- Phase B: `docs/superpowers/plans/2026-05-03-kb-v030-phase-b.md`
- Phase C: `docs/superpowers/plans/2026-05-06-kb-v030-phase-c.md`

## Design Specs

- Phase B: `docs/superpowers/specs/2026-05-03-kb-v030-phase-b-design.md`
- Phase C: `docs/superpowers/specs/2026-05-06-kb-v030-phase-c-design.md`

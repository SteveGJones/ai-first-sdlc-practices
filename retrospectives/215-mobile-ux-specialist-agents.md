# Retrospective: Mobile-UX Specialist Agents

**Branch:** `feature/material-design-3-agent` (UX-specialist coverage work; continues #214)
**Date:** 2026-07-22
**Duration:** ~1 session (assessment + parallel research + authoring + wiring)

---

## Summary

Added two specialist agents — `apple-hig-architect` (iOS/iPadOS UX to Apple's Human Interface
Guidelines) and `mobile-ux-architect` (platform-agnostic mobile-native interaction UX) — to
`sdlc-team-fullstack`, closing the mobile-UX gaps found after #214, and fixed the `ux-designer`
dangling reference in `mobile-architect`. The suite now has a clean, non-overlapping five-agent
UX/mobile set. Delivered with all format/official validators passing, technical-debt COMPLIANT, no
broken references, and 50 registry+setup tests green.

## What Went Well

- **Assessment before building**: verified the actual gap (iOS had no design specialist — only
  architecture-level HIG notes; no owner for cross-platform mobile-interaction UX; a dangling
  `ux-designer` reference) rather than assuming it. The scope came from evidence.
- **Parallel deep research paid off again**: three streams (HIG foundations, iOS interaction/platform,
  cross-platform mobile UX) ran concurrently and returned current, well-sourced material — notably
  **Liquid Glass / iOS 26** captured accurately with new-in-2025 flags, and the HIG content pulled
  from Apple's DocC JSON endpoints (the public HIG pages are JS SPAs that return only a title).
- **Clean scope split**: the five agents (ux-ui / material-design-3 / apple-hig / mobile-ux /
  mobile-architect) each own a distinct slice with bidirectional cross-references, so advice routes
  rather than overlaps.
- **Reused the #214 playbook**: same agent structure (validated) and same registry-based setup
  awareness, so authoring and wiring were fast and consistent.
- **Caught the color-enum constraint pre-emptively**: chose `blue`/`green` from the allowed set for
  the new agents (learned from #214's `teal` rejection), so both passed format validation first try.

## What Could Improve

- **Broken-reference false positives from prose**:
  - What happened: research files described Apple's `.../<page>.json` endpoint pattern in prose;
    `check-broken-references.py` read `<page>.json` as a local file link and flagged 3 files.
  - Root cause: the checker treats any `X.json`/`X.md` token as a candidate link, including inside
    backticked prose.
  - Improvement: avoid bare `filename.ext` tokens in prose; write "the `tutorials/data/...` paths"
    instead. (Same class of issue as #214's `Motion.md`.)

- **AGENT-INDEX header note dropped by the generator (again)**:
  - What happened: regenerating the catalog wiped the manual SDLC-bundle note and source/published split.
  - Root cause: AGENT-INDEX.md mixes generated body with hand-maintained header notes.
  - Improvement: re-added the note with counts verified by counting files (source 138 / published 61).
    Standing action item from #214 still applies — generate the header counts/notes.

- **Registry detection for native iOS is inherently weak**:
  - What happened: iOS uses SPM/CocoaPods/Xcode, which the npm/pip-oriented registry can't scan.
  - Root cause: registry detection covers pip/npm/docker/env/go/gem only.
  - Improvement: leaned on aliases (ios/swiftui/hig/…) and cross-platform JS signals (react-native/
    expo) for detection, and documented the native-toolchain gap in the entry — same honest approach
    as M3's Gradle/pubspec note.

## Lessons Learned

1. **Fetch the data endpoint when the docs are an SPA.** Apple's HIG (like m3.material.io) returns
   only a title to fetchers; the DocC `tutorials/data/...json` endpoints hold the real content. This
   is what let the research be Apple's own text with exact values, not paraphrase.
2. **A coverage audit is a legitimate feature trigger.** The strongest scoping came from auditing what
   the existing agents actually said (grep), not from guessing what was missing.
3. **Split specialists by "pattern vs expression."** `mobile-ux-architect` owns the cross-platform
   pattern; `apple-hig-architect` / `material-design-3-architect` own its platform expression. That
   boundary keeps three mobile-facing agents from overlapping.

## Changes Made

### Files Created
- `docs/feature-proposals/215-mobile-ux-specialist-agents.md`; `retrospectives/215-mobile-ux-specialist-agents.md`
- `research/apple-hig/{README,01-foundations-navigation-components,02-interaction-platform-accessibility}.md`
- `research/mobile-ux/{README,01-mobile-native-interaction-ux}.md`
- `agents/core/apple-hig-architect.md`, `agents/core/mobile-ux-architect.md` (+ released plugin copies)
- `data/technology-registry/apple-hig.yaml` (+ sdlc-core plugin copy)

### Files Modified
- `agents/core/mobile-architect.md` — fixed `ux-designer` dangling reference → the four real specialists
- `agents/core/ux-ui-architect.md`, `agents/core/material-design-3-architect.md` — cross-references to the new agents
- `data/technology-registry/_index.yaml` (+ plugin copy) — apple-hig detection + aliases
- `release-mapping.yaml` — register both agents + the apple-hig registry entry
- `plugins/sdlc-team-fullstack/.claude-plugin/plugin.json` — version 1.1.0 → 1.2.0
- `AGENT-INDEX.md` + `AGENT-CATALOG.json` — regenerated (fullstack 11 → 13 agents)
- `CLAUDE.md`, `README.md`, `plugins/sdlc-team-fullstack/README.md` — agent-count / description updates

### Validation
- `validate-agent-format.py` — PASS (both); `validate-agent-official.py` — PASS with warnings (same accepted `first_party_alternatives` info as siblings)
- `check-technical-debt.py --threshold 0` — COMPLIANT
- `check-broken-references.py` — no broken refs in any new/changed file (after fixing 3 prose false positives)
- `pytest` registry + setup_smart — 50 passed

## Action Items

- [ ] (Optional follow-up) Ingest `research/apple-hig/` + `research/mobile-ux/` into a project KB via `/sdlc-knowledge-base:kb-ingest` (deferred, as with #214).
- [ ] (Housekeeping, carried from #214) Generate AGENT-INDEX header counts/notes instead of hand-maintaining them — Owner: framework author.
- [ ] (Doc hygiene) Consider a lint rule to allow bare `filename.ext` tokens inside backticked prose in `check-broken-references.py` — Owner: framework author.

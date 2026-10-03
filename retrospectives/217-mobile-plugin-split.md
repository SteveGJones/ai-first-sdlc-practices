# Retrospective: Split mobile plugins out of sdlc-team-fullstack

**Branch:** `feature/mobile-plugin-split`
**Date:** 2026-07-23
**Duration:** ~1 session (Phase 1 of EPIC #217)

---

## Summary

Phase 1 of EPIC #217: split the four mobile agents out of the noisy 13-agent `sdlc-team-fullstack`
into focused plugins — `sdlc-team-mobile` (shared base), `sdlc-team-ios`, `sdlc-team-android` — and
slimmed fullstack to a 9-agent web bundle (2.0.0). Structural split only; no new agents. Delivered
with all validators green and 77 setup/registry/plugin tests passing.

## What Went Well

- **Decisions settled before building.** Naming (`sdlc-team-*`), migration (clean cut → 2.0.0), and
  scope (structural split only) were locked via an explicit question, so implementation had no rework.
- **Fable's advice shaped the right structure.** Two independent Fable advisors both landed on the
  shared-base pattern (don't duplicate `mobile-architect`/`mobile-ux-architect` into both platform
  plugins), which this phase implemented directly. The verification step confirmed no agent is
  registered twice.
- **Cheap because of the release model.** Agent *sources* never moved (`agents/core/`); the split was a
  `release-mapping.yaml` re-map + plugin-dir population + manifest edits. No content duplication, no
  agent-body edits (agents are invoked by name, so cross-references kept resolving).
- **Caught the source-vs-plugin sync trap early.** The `setup-team` skill has a source at
  `skills/setup-team/SKILL.md`; edited the plugin copy first, then synced source and bumped `sdlc-core`.

## What Could Improve

- **Two version records per plugin, by hand.** Every plugin version lives in both `plugin.json` and
  `marketplace.json`; I bumped `sdlc-core`, `sdlc-team-fullstack`, and added three new plugins across
  both. Verified with a scripted equality check, but this is error-prone (bit us on #216 when
  marketplace lagged plugin.json). Standing candidate for a version-consistency validator.
- **AGENT-INDEX header note dropped again** by the catalog generator; re-added with counts verified by
  counting files (61 published across 17 plugins, 15 ship agents). Third time this session — the
  header counts/notes should be generated, not hand-maintained (carried-forward action item).
- **Option lettering in setup-team** now reads A,B,C,D,E,G,H,I,F (inserted mobile types before
  Custom). Cosmetic; the matrix maps each letter correctly, but a future cleanup could re-letter.

## Lessons Learned

1. **Split by "shared vs platform-specific," not by platform.** The cross-platform agents needed a
   base plugin; forcing them into iOS/Android would have duplicated them and re-created the noise.
2. **A refactor of packaging is mostly a manifest exercise here.** Because `release-mapping.yaml` fans
   one source into N plugins, "move an agent between plugins" = edit mappings + re-populate dirs. Know
   the release model before estimating the work.
3. **Verify the invariant, don't assume it.** "No agent registered twice" was made an explicit
   scripted check, not a hope — exactly the property the whole design hinges on.

## Changes Made

### Files Created
- `docs/feature-proposals/217-mobile-plugin-split.md`, `retrospectives/217-mobile-plugin-split.md`
- `plugins/sdlc-team-mobile/` (plugin.json, agents/{mobile-architect,mobile-ux-architect}, README)
- `plugins/sdlc-team-ios/` (plugin.json, agents/apple-hig-architect, README)
- `plugins/sdlc-team-android/` (plugin.json, agents/material-design-3-architect, README)

### Files Modified
- `release-mapping.yaml` — removed 4 mobile agents from fullstack; added 3 new plugin sections
- `plugins/sdlc-team-fullstack/` — removed 4 mobile agent files; plugin.json 1.2.0 → **2.0.0** + new description; README rewritten (9 web agents + migration note)
- `.claude-plugin/marketplace.json` — added 3 plugins; fullstack → 2.0.0; sdlc-core → 1.2.0
- `plugins/sdlc-core/.claude-plugin/plugin.json` — 1.1.0 → **1.2.0**
- `skills/setup-team/SKILL.md` (+ plugin copy) — iOS/Android/cross-platform project types + recommendation matrix
- `AGENT-INDEX.md` + `AGENT-CATALOG.json` — regenerated (fullstack 13→9; +3 plugins)
- `CLAUDE.md`, `README.md` — plugin tables + counts
- `CHANGELOG.md` — breaking-change migration entry under [Unreleased]

### Not changed (deliberately)
- Agent source files (`agents/core/*`) — unmoved; cross-references resolve by name
- `release/agent-manifest.json` — category-scoped dated build snapshot, not plugin-scoped

### Validation
- No agent registered twice (each moved agent in exactly one plugin) — scripted check ✓
- marketplace ↔ plugin.json versions agree for all touched plugins ✓
- `check-broken-references.py` clean; `check-technical-debt.py --threshold 0` COMPLIANT
- `check-feature-proposal.py` — properly formatted; 77 setup/registry/plugin tests pass

## Action Items

- [ ] EPIC #217 follow-on phases: iOS agents (swiftui-architect, ios-release-engineer, ios-performance-specialist), Android agents (kotlin, jetpack-compose, app-architect, gradle, play-store, performance), + skills/validators — Owner: TBD
- [ ] (Carried) Generate AGENT-INDEX header counts/notes instead of hand-maintaining — Owner: framework author
- [ ] (New) Add a version-consistency validator (plugin.json ↔ marketplace.json) — Owner: framework author

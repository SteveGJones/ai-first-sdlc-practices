# Retrospective: sdlc-team-ios platform agents

**Branch:** `feature/ios-platform-agents`
**Date:** 2026-07-23
**Duration:** ~1 session (parallel research + authoring + wiring)

---

## Summary

Built three research-grounded iOS platform agents — `swiftui-architect`, `ios-release-engineer`,
`ios-performance-specialist` — into `sdlc-team-ios` (0.1.0 → 0.2.0), the first content phase of
EPIC #217 after the structural split (#218). `sdlc-team-ios` now covers the iOS lifecycle
**design → architecture → release → performance**. All format/official validators green,
technical-debt COMPLIANT, no broken refs, 77 plugin/registry/setup tests passing.

## What Went Well

- **The playbook is now routine**: parallel deep research (3 streams) → validated authoring → wire →
  regenerate catalog → validate → PR. Fourth time this session; fast and consistent.
- **Current, high-quality research**: all three references landed on the 2025/2026 baseline
  (iOS 26 / Xcode 26 / Swift 6.2, Instruments 27, privacy-manifest enforcement, no-rollback reality),
  with community patterns (TCA, fastlane) clearly labelled and version-sensitive facts flagged `[VERIFY]`.
- **Clean seam design**: the three agents plus `apple-hig-architect` split the iOS lifecycle without
  overlap (design / architecture / release / performance), with bidirectional cross-references added
  to the HIG agent so routing is explicit.
- **Scope discipline held**: deferred the Swift language expert (D2) and iOS skills/validators, keeping
  the PR to three reviewable agents.

## What Could Improve

- **A stray non-ASCII character slipped into an agent body** (`Choosing/ු structuring`): an accidental
  Sinhala codepoint. Caught by a `grep -P '[^\x00-\x7F]'` scan before commit and fixed.
  - Improvement: run the non-ASCII scan as a standard pre-commit step for authored agents (added to
    my checklist); a repo lint rule allowing only a typography allowlist would catch it in CI.
- **Description length limit bit again** (`ios-performance-specialist` was 513/500 chars): trimmed.
  - Same class as #214's color-enum surprise — the agent-format constraints (≤500 desc, color enum)
    aren't obvious from the template. Improvement: check `validate-agent-format.py` limits before writing.
- **AGENT-INDEX header counts remain hand-maintained** and the generator's `total_agents` (144) mixes
  source + plugin categories, so the "source directory" figure needed manual computation from the
  category breakdown (80 source / 64 published). Carried-forward action item to generate these.

## Lessons Learned

1. **One platform per PR keeps content reviewable.** Three agents + research is already a substantial
   diff; folding in Android's six would have been unreviewable. Phase by platform.
2. **Label Apple-native vs community explicitly.** iOS has strong third-party patterns (TCA, fastlane,
   Factory); the research and agents mark them so advice is honest about dependencies.
3. **Version-sensitivity is a first-class property for platform agents.** Apple renames/renumbers
   constantly; the agents instruct themselves to flag and re-verify rather than assert timeless facts.

## Changes Made

### Files Created
- `docs/feature-proposals/219-ios-platform-agents.md`, `retrospectives/219-ios-platform-agents.md`
- `agents/core/{swiftui-architect,ios-release-engineer,ios-performance-specialist}.md` (+ plugin copies)
- `research/ios-swiftui-architecture/`, `research/ios-release-engineering/`, `research/ios-performance/` (README + reference each)

### Files Modified
- `agents/core/apple-hig-architect.md` (+ plugin copy) — cross-references + boundaries to the 3 new agents
- `release-mapping.yaml` — add 3 agents under sdlc-team-ios
- `plugins/sdlc-team-ios/.claude-plugin/plugin.json` — 0.1.0 → 0.2.0 + description; `marketplace.json` synced
- `AGENT-INDEX.md` + `AGENT-CATALOG.json` — regenerated (sdlc-team-ios 1 → 4 agents)
- `plugins/sdlc-team-ios/README.md`, `CLAUDE.md`, `README.md` — counts/descriptions

### Validation
- `validate-agent-format.py` PASS (all 3, after a description trim); `validate-agent-official.py` PASS
- `check-technical-debt.py --threshold 0` COMPLIANT; `check-broken-references.py` clean for new files
- `check-feature-proposal.py` properly formatted; 77 plugin/registry/setup tests pass; plugin↔marketplace versions agree

## Action Items

- [ ] Next EPIC #217 phase: **Android platform agents** (kotlin-android/jetpack-compose/app-architect/gradle/play-store/performance) — separate PR
- [ ] EPIC #217 follow-ups: iOS skills (signing-doctor, testflight-release, appstore-submit, ios-ci) + validators (purpose-strings, privacy-manifest, entitlements, deployment-target)
- [ ] EPIC #217 D2: Swift language expert placement (`sdlc-lang-swift` vs bundled)
- [ ] (Carried) Generate AGENT-INDEX header counts/notes; add non-ASCII lint for authored agents

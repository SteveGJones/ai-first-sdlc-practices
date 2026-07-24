# Feature Proposal: Android platform agents

**Proposal Number:** 226
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/android-platform-agents`
**GitHub Issue:** #226 (Phase 1 of Android sub-epic #225; part of EPIC #217)

---

## Motivation

The structural split (#218) created a focused `sdlc-team-android` plugin, but it ships only one agent —
`material-design-3-architect` (design). The iOS side is now fully built out (design → architecture →
release → performance + a language plugin). Android needs the same depth: an Android team needs Compose
UI architecture, app architecture, Gradle/build, Play Store release, and performance — none of which the
Material 3 design agent or the cross-platform `mobile-architect` (framework-selection altitude) covers.

This is **Phase 1 of the Android sub-epic (#225)**: the five platform agents. Later phases add the
Kotlin language plugin (`sdlc-lang-kotlin`) and Android skills/validators. Built research-grounded on
official Google sources, the same playbook as the iOS agents (#220).

## User Stories

- As an **Android/Compose developer**, I want a `jetpack-compose-architect` that knows recomposition,
  stability/strong-skipping, state hoisting, and Compose performance — distinct from Material 3 tokens.
- As an **Android engineer**, I want an `android-app-architect` for the recommended architecture,
  process-death survival, Hilt, Room/DataStore, and WorkManager.
- As anyone **fighting the build**, I want a `gradle-build-specialist` for version catalogs, convention
  plugins, build caching, KSP, variants, and R8.
- As a **release owner**, I want a `play-store-release-specialist` for Play App Signing, app bundles,
  staged rollout, Data Safety, the target-API mandate, and Play publishing automation.
- As someone **chasing jank/ANRs/Vitals**, I want an `android-performance-specialist` for Baseline
  Profiles, Macrobenchmark, ANR diagnosis, and the Play Vitals thresholds that affect store visibility.

## Proposed Solution

### High-Level Approach

Add five agents to `sdlc-team-android`, each grounded in a dedicated deep-research reference under
`research/`. Follow the established agent contract (validated frontmatter with ≥2 examples, allowed
color, `first_party_alternatives`; competencies, process, decision guidance, boundaries, collaboration).
Clean, non-overlapping boundaries mirroring iOS (design / Compose-UI / app-architecture / build /
release / performance), with cross-references to `material-design-3-architect`, the shared mobile
agents, and (Phase 2) `language-kotlin-expert`.

### Technical Approach

1. **Research references** (`research/android-*`) — official-Google-source-grounded, Sources lists.
2. **Five source agents** in `agents/core/`: `jetpack-compose-architect.md`, `android-app-architect.md`,
   `gradle-build-specialist.md`, `play-store-release-specialist.md`, `android-performance-specialist.md`.
3. **Wiring**: add to `release-mapping.yaml` under `sdlc-team-android`; populate the plugin `agents/`;
   bump `sdlc-team-android` 0.1.0 → **0.2.0** (plugin.json + marketplace); regenerate AGENT-INDEX/CATALOG;
   update the plugin README, CLAUDE.md, README counts; cross-reference `material-design-3-architect`.
4. **Validation**: `validate-agent-format`, `validate-agent-official`, technical-debt, broken-references,
   packaging, tests.

### Alternatives Considered

1. **Fewer/bigger agents.** Rejected — build (Gradle), release (Play), and performance are distinct,
   deep toolchains; merging dilutes them. Five matches the real seams (same reasoning as iOS).
2. **Bundle Kotlin here.** Deferred to Phase 2 as a separate `sdlc-lang-kotlin` plugin, for symmetry with
   `sdlc-lang-swift` (sub-epic #225 decision).
3. **Skills/validators in this PR.** Deferred to Phase 3 — agents first, to keep this PR reviewable.

---

## Implementation Plan

### Phase 1: Research
- [ ] [P] Jetpack Compose architecture · app architecture · Gradle/AGP · Play release · performance
- [ ] Persist references under `research/android-*`

### Phase 2: Agents
- [ ] Write the five agents; cross-reference material-design-3-architect / mobile agents

### Phase 3: Wiring, validation & release
- [ ] release-mapping + populate plugin; bump sdlc-team-android 0.1.0 → 0.2.0 (both manifests)
- [ ] Regenerate AGENT-INDEX/CATALOG; READMEs + CLAUDE.md/README counts
- [ ] Validators + tests; retrospective; PR

**Dependencies:** none new. Builds on #218 (sdlc-team-android exists).

---

## Success Criteria

```
Given a user asks jetpack-compose-architect why a screen recomposes too often
When it responds
Then it explains stability/skippability/strong-skipping and deferred reads correctly, distinct from
     Material 3 design advice
```

```
Given a user asks play-store-release-specialist how to roll back a bad release
When it responds
Then it correctly explains halting a staged rollout / rolling back to a previous release on Play
     (contrasting with iOS's no-rollback constraint)
```

```
Given the five new agent files
When CI agent-format / official validation runs
Then all pass (valid frontmatter, >=2 examples, allowed color, no technical debt, no broken refs)
```

```
Given sdlc-team-android after this change
When its agents are listed
Then it contains material-design-3-architect + the 5 new agents (6 total); version is 0.2.0; catalog regenerated
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Android APIs / Play policies date fast | Med | Med | Ground in official sources; date-stamp; flag version-sensitive (target-API mandate, Vitals thresholds) |
| Overlap with material-design-3-architect / mobile-architect | Med | Low | Explicit boundaries + cross-references (design vs Compose-UI vs app-arch vs build vs release vs perf) |
| Five agents is a large PR | Med | Low | Consistent structure; validate each; split only if review demands |
| Broken-ref false positives from prose (`file.ext`) | Med | Low | Avoid bare `filename.ext` in prose (learned earlier this EPIC) |

## Open Questions

- [ ] Kotlin plugin (`sdlc-lang-kotlin`) — Phase 2 of #225 (separate plugin, per the Swift precedent).
- [ ] Android skills/validators — Phase 3 of #225.

## Security & Privacy

N/A. Static agent definitions + research references. No code execution, auth, data handling, or secrets.

---

**Retrospective**: `retrospectives/226-android-platform-agents.md` (link after implementation)

# Feature Proposal: Android skills + Play pre-flight checks

**Proposal Number:** 230
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/android-skills-validators`
**GitHub Issue:** #230 (Phase 3 of Android sub-epic #225; part of EPIC #217)

---

## Motivation

`sdlc-team-android` has its six platform agents (#227) and Kotlin has its language plugin (#229), but
Android has no **operational tooling** for the part that most often goes wrong: getting a build through
Play submission and building it safely. This mirrors the iOS toolkit (#222/#224): a pre-flight checker
plus scaffolding/signing/release/CI skills. Building them completes the Android sub-epic and EPIC #217's
mobile build-out — both platforms end with identical shape (agents + language plugin + skills + checks).

The checks encode Google's Play policy/release blockers: the annual **target-API mandate**, **background
location** and other sensitive-permission declarations, **unguarded exported components**, and
release-config issues (no R8, debug signing, committed secrets).

## User Stories

- As an **Android developer**, I want a pre-flight check that fails fast on a targetSdk below the Play
  minimum or an unguarded exported component, before an upload round-trip.
- As a **release owner**, I want an `android-play-release` skill that sequences internal→production with
  a staged rollout and the halt/roll-forward lever.
- As someone **setting up signing**, I want `android-signing-setup` to wire Play App Signing without
  committing secrets.
- As a team setting up **CI**, I want `android-ci` to gate on the pre-flight checks + `./gradlew lint`.

## Proposed Solution

### High-Level Approach

Add a **pre-flight checker** (Python, in-plugin per the `ios_preflight` / sdlc-programme pattern) plus
four **skills** to `sdlc-team-android`, and reference them from `play-store-release-specialist`.

### Technical Approach

1. **`plugins/sdlc-team-android/scripts/android_preflight`** — pure check functions + a CLI:
   `check_manifest` (permissions/exported components/manifest flags), `check_sdk_policy` (target-API
   mandate + SDK consistency), `check_release_config` (R8/debug-signing/secrets). CLI parses
   AndroidManifest.xml (ElementTree) and Gradle files (regex). Full pytest suite; registered in
   `tests/conftest.py`.
2. **Skills** (`skills/android-*`, released to the plugin): `android-scaffold`, `android-signing-setup`,
   `android-play-release`, `android-ci` — each encoding the corresponding lessons and invoking the
   checker; the pipeline shells out to `./gradlew lint` rather than reimplementing Android Lint.
3. **Agent update**: `play-store-release-specialist` gains a Skills reference.
4. **Wiring**: `release-mapping.yaml` (skills + scripts under sdlc-team-android), bump 0.2.0 → **0.3.0**
   (plugin.json + marketplace.json), plugin README + CLAUDE.md/README counts.

### Alternatives Considered

1. **Checks as agent prose only.** Rejected — a deterministic, tested checker catches config regressions
   in CI and doesn't depend on the model remembering Play's rules.
2. **A Material-3/accessibility validator in Python.** Rejected — Android Lint already owns those; the
   pipeline shells out to `./gradlew lint` instead of duplicating it (per the Fable recommendation).

---

## Implementation Plan

### Phase 1: Checker (test-first)
- [ ] Write `tests/test_android_preflight.py`, then `android_preflight/{checks,cli}.py`; register in conftest

### Phase 2: Skills + agent
- [ ] Author `android-scaffold`, `android-signing-setup`, `android-play-release`, `android-ci`
- [ ] Update `play-store-release-specialist` with skill references

### Phase 3: Wiring, validation & release
- [ ] `release-mapping.yaml` (skills + scripts); package skills; bump 0.2.0 → 0.3.0 (both manifests)
- [ ] Update marketplace, plugin README, CLAUDE.md/README
- [ ] ruff lint/format, packaging check, technical-debt, broken-references, full test suite; retrospective; PR

**Dependencies:** none new. Builds on #227 (agents exist).

---

## Success Criteria

```
Given an Android project with targetSdk below the Play minimum
When android_preflight.cli runs
Then it reports a target-sdk-too-low ERROR and exits non-zero
```

```
Given a manifest declaring ACCESS_BACKGROUND_LOCATION without justification
When android_preflight.cli runs
Then it flags a sensitive-permission ERROR citing the one-core-feature + demo-video requirement
```

```
Given the pre-flight check module
When the test suite runs
Then all android_preflight tests pass and ruff lint/format are clean
```

```
Given sdlc-team-android after this change
When the plugin is packaged
Then it ships 6 agents + 4 skills + the android_preflight scripts; version is 0.3.0; packaging check passes
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Play policy / target-API mandate goes stale | Med | Low | `--play-min-target` configurable; skills flag version-sensitivity; easy to update the default |
| Regex Gradle parsing misses dynamically-set values | Med | Low | Checker is a fast pre-filter, not a guarantee; findings additive; skills prompt manual review |
| Over-flagging annoys users | Low | Low | Background location is ERROR only when present; most manifest flags are WARNING/INFO |
| Test-annotation technical-debt gate (as in #222) | Low | Med | Annotate all test functions `-> None` (learned this EPIC) |

## Open Questions

- [ ] `baseline-profile` / `target-sdk-migrate` fast-follow skills? Deferred.

## Security & Privacy

N/A for data handling. The checker reads local project files read-only and emits findings; no network,
no secrets, no writes. The skills explicitly warn against committing keystores/secrets.

---

**Retrospective**: `retrospectives/230-android-skills-validators.md` (link after implementation)

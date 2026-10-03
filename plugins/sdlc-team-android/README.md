# sdlc-team-android

Focused **Android development** plugin. Contains only Android-relevant design expertise, so an Android
team isn't wading through web, backend, or data specialists.

## Agents (6)

Covering the Android lifecycle: **design → Compose UI → app architecture → build → release → performance**.

- **`material-design-3-architect`** — Material Design 3 / Material You: HCT/dynamic colour, the
  `md.sys.*` token system, components, tonal elevation, Compose Material3 / Flutter, M2→M3, Expressive.
- **`jetpack-compose-architect`** — Compose UI architecture: recomposition/stability/strong-skipping,
  state hoisting & UDF, side-effect APIs, custom layout/`Modifier.Node`, lazy lists, type-safe
  Navigation-Compose, Compose performance & testing.
- **`android-app-architect`** — the recommended architecture (UI/domain/data + UDF), lifecycle &
  process-death survival (ViewModel/SavedStateHandle), Hilt DI, Room/DataStore/Paging, WorkManager &
  foreground services, multi-module strategy, events-as-state, testing with fakes.
- **`gradle-build-specialist`** — Gradle/AGP (Kotlin DSL), version catalogs, convention plugins
  (build-logic), build performance (configuration/build cache), KSP, variants, dependency management, R8.
- **`play-store-release-specialist`** — Play App Signing, app bundles (`.aab`)/bundletool, tracks &
  staged rollout (halt/roll-forward), Data Safety, the target-API mandate, sensitive-permission
  declarations, in-app updates/review, publishing automation (Play Developer API / GPP / fastlane).
- **`android-performance-specialist`** — startup (Baseline Profiles, Macrobenchmark, TTID/TTFD),
  rendering/jank (JankStats, frozen frames), ANRs (ApplicationExitInfo), memory (LeakCanary), Perfetto,
  and the **Play Vitals thresholds** that gate store discoverability.

> For **Kotlin the language** (coroutines/Flow, null-safety, sealed types, KSP), install the companion
> **`sdlc-lang-kotlin`** plugin (`language-kotlin-expert`) — `/sdlc-core:setup-team` recommends it for
> Android projects.

## Skills (4)

Operational workflows for scaffolding and the Play release flow:

- **`/sdlc-team-android:android-scaffold`** — new Kotlin/Compose project with Play-safe defaults
  (version catalog, convention plugins, targetSdk at the Play minimum, R8, git-ignored signing) so it
  passes the pre-flight checker from day one.
- **`/sdlc-team-android:android-signing-setup`** — generate an upload keystore, enroll in Play App
  Signing, and wire a Gradle release `signingConfig` reading secrets from a git-ignored file / CI.
- **`/sdlc-team-android:android-play-release`** — pre-flight + Play policy gates → signed `.aab` →
  track upload → staged rollout (with **halt/roll-forward**).
- **`/sdlc-team-android:android-ci`** — Android GitHub Actions (Gradle caching, tests, lint, pre-flight
  gate, optional signed Play upload).

## Pre-flight checker

`scripts/android_preflight` is a static checker the release skills invoke — it catches the config that
most often blocks a Play submission or is a release-quality defect: sensitive permissions (background
location), unguarded exported components, **targetSdk below the Play minimum**, and release-config
issues (no R8, debug signing config, committed secrets). It shells out to `./gradlew lint` rather than
reimplementing Android Lint.

```bash
python -m android_preflight.cli <android-project-dir> [--play-min-target N]
```

## Install with the mobile base

Android work also needs cross-platform mobile expertise, which lives in **`sdlc-team-mobile`**
(`mobile-architect`, `mobile-ux-architect`). Install both together — `/sdlc-core:setup-team`
recommends them as a unit when you select an Android project type.

## Part of the SDLC plugin family

Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` for personalized recommendations.

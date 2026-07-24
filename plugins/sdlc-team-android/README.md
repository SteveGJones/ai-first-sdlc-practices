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
> `sdlc-lang-kotlin` plugin (planned — sub-epic #225). Android **skills + validators** (scaffold,
> signing, play-release, CI; manifest/SDK-policy/release-config checks) are a later phase.

## Install with the mobile base

Android work also needs cross-platform mobile expertise, which lives in **`sdlc-team-mobile`**
(`mobile-architect`, `mobile-ux-architect`). Install both together — `/sdlc-core:setup-team`
recommends them as a unit when you select an Android project type.

## Part of the SDLC plugin family

Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` for personalized recommendations.

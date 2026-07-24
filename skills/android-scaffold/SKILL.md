---
name: android-scaffold
description: Scaffold a new Android app with SDLC and Play-safe defaults — Kotlin/Compose Gradle project with version catalog, convention plugins, module layout, a targetSdk that meets the Play mandate, R8 on release, and git-ignored signing so it passes the pre-flight checker from day one. Use when starting a new Android project.
disable-model-invocation: false
argument-hint: "[app-name]"
---

# Android Scaffold

Create a new Android app project that is **Play-safe and build-fast from the first commit** — so it
doesn't hit the submission/build issues `android-play-release` and the pre-flight checker exist to
catch. Belongs to the **`sdlc-team-android`** plugin; pairs with `jetpack-compose-architect` (UI),
`android-app-architect` (structure), `gradle-build-specialist` (build), and `language-kotlin-expert`.

## Arguments

- `app-name` — the app / applicationId (defaults to asking).

## Steps

### 1. Project shape

- **Kotlin + Jetpack Compose** app module + a unit-test source set + optional instrumented tests.
- A **multi-module** layout if non-trivial (`app` + `feature:*` + `core:*` + `data:*`; features depend
  on core/data, never other features) — see `android-app-architect`.
- `.gitignore` covering `/build`, `.gradle`, `local.properties`, `*.jks`/`*.keystore`,
  `keystore.properties`, `.idea` (except shared), `*.iml`.

### 2. Build setup (the point of the skill)

- **Kotlin DSL** (`build.gradle.kts`), a **version catalog** (`gradle/libs.versions.toml`) as the single
  source of truth, and **convention plugins** in a `build-logic` included build for shared `android {}`
  config (à la Now in Android). See `gradle-build-specialist`.
- **`namespace`** + **`applicationId`** set; **`compileSdk` = latest stable**; **`targetSdk` = the
  current Play minimum** (the pre-flight checker's `--play-min-target`) so the app isn't hidden on new
  devices; a sensible `minSdk`.
- **Version numbers**: `versionName` fixed pre-1.0; **`versionCode` stamped from
  `git rev-list --count HEAD`** (unique & monotonic — every upload needs this) in a Gradle snippet.
- Enable the **configuration cache** + **build cache** + **KSP** (not kapt) in `gradle.properties`.

### 3. Release-safe defaults

- **Release build type**: `isMinifyEnabled = true` + `isShrinkResources = true` (R8) with a
  `proguard-rules.pro`; a **release `signingConfig`** reading secrets from a **git-ignored
  `keystore.properties`** / CI (never the debug keystore, never committed secrets) — see
  `android-signing-setup`.
- Gate debug menus, verbose logging, and staging endpoints behind a build type / `BuildConfig` flag
  that is **off in release**.

### 4. Manifest hygiene

- Request only permissions you use; keep exported components guarded (permission or intent-filter, or
  `android:exported=false`); avoid `usesCleartextTraffic` (use a network-security-config allowlist if
  genuinely needed).

### 5. CI + lint

- Offer to run `android-ci` to generate the GitHub Actions workflow (gates on the pre-flight checker +
  `./gradlew lint`).

### 6. Verify

- `./gradlew assembleDebug` once; run the unit-test source set; and run the pre-flight checker
  (`python -m android_preflight.cli <project>`) — it should be clean (or only INFO) on a fresh scaffold.

### 7. Report

Summarise what was generated, the module layout, the versionCode policy, and confirm the pre-flight
checker is clean. Note anything the user must fill in (real keystore, Data Safety, privacy policy).

## Notes

- The goal is a project that passes `android-play-release` pre-flight on day one — don't leave targetSdk,
  R8, or signing "for later".
- For UI structure hand off to `jetpack-compose-architect`; for app architecture to
  `android-app-architect`; for idiomatic Kotlin to `language-kotlin-expert`.

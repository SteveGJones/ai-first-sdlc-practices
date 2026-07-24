---
name: android-ci
description: Generate a GitHub Actions workflow for Android — JDK + Gradle caching, build, unit + instrumented tests, Android Lint, run the Android pre-flight checks, and (optionally) sign + upload a signed app bundle to a Play track. Use when setting up CI for an Android app.
disable-model-invocation: false
argument-hint: "[path-to-android-project]"
---

# Android CI

Generate a GitHub Actions workflow for an Android app. Complements (does not replace)
`/sdlc-core:setup-ci` — this adds the Android-specific pieces (JDK/Gradle caching, emulators, Play
upload). Belongs to the **`sdlc-team-android`** / **`play-store-release-specialist`** disciplines.

## Arguments

- `path-to-android-project` — the project directory (defaults to the current directory).

## Steps

### 1. Establish the project shape

- The Gradle wrapper version, the AGP/Kotlin/JDK versions (must move together — JDK 17 floor for AGP
  9.x), the module/variant layout, and whether it uses version catalogs (it should).

### 2. Generate the workflow

Produce an Android CI workflow file under `.github/workflows/` with:

- **Runner**: `ubuntu-latest` for build/unit tests; a macOS runner or a Gradle-managed device / AVD
  action for instrumented tests. Set JDK 17 (`actions/setup-java`, temurin).
- **Gradle caching**: `gradle/actions/setup-gradle` (caches the Gradle user home + configuration cache);
  enable `org.gradle.configuration-cache` and `org.gradle.caching`.
- **Build & test**: `./gradlew assembleDebug testDebugUnitTest lint`; instrumented tests via
  Gradle-managed devices or `reactivecircus/android-emulator-runner`. Upload `lint`/test reports.
- **Android pre-flight**: run `python -m android_preflight.cli .` so config regressions (target-SDK below
  the Play minimum, unguarded exported components, missing R8, committed secrets, background-location
  without justification) fail CI before a release ever reaches Play.

### 3. (Optional) Signing + Play upload job

Only if the project releases from CI:

- **Secrets**: base64-encoded upload keystore, keystore/key passwords, and the **Play service-account
  JSON** — all in GitHub Actions encrypted secrets, never in the repo.
- **Signing**: decode the keystore, write a `keystore.properties` (or pass via env), sign the release —
  see `android-signing-setup`.
- **Build + upload**: `./gradlew bundleRelease` → a signed `.aab`; upload with **Gradle Play Publisher**,
  **fastlane `supply`**, or the `r0adkll/upload-google-play` action to the **`internal`** track (draft or
  a small `inProgress` %), then promote after smoke-testing.
- **versionCode**: stamp from `git rev-list --count HEAD` so every CI build is unique, monotonic, and
  traceable to a commit.

### 4. Report

Summarise the workflow: triggers, the test matrix, whether it gates on the pre-flight checker + lint, and
whether it uploads to Play. Note any secrets the user must add before it will run.

## Notes

- Keep build/test (no secrets, runs on every PR) separate from the signing/upload job so PRs stay fast.
- Gradle-managed devices give reproducible instrumented tests without an external emulator matrix.

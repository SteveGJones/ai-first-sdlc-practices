---
name: android-play-release
description: Validated Google Play release — runs the pre-flight checks and clears the Play policy gates, builds a signed app bundle with a git-stamped versionCode, uploads to a track, and walks staged rollout (with halt/roll-forward). Use when releasing an Android app to Play.
disable-model-invocation: false
argument-hint: "[path-to-android-project]"
---

# Android Play Release

Get an Android build onto Google Play without the classic policy/upload blockers, and release it with a
safety lever. Belongs to the **`play-store-release-specialist`** discipline. Run it before every Play
upload; the checks are cheap and the failures are expensive (rejection or a bad rollout).

## Arguments

- `path-to-android-project` — the project directory to check (defaults to the current directory).

## Steps

### 1. Run the pre-flight checks

```bash
python -m android_preflight.cli <project-dir> [--play-min-target N]
```

Resolve every **ERROR** before uploading, and run `./gradlew lint` (the checker doesn't reimplement
Android Lint). The checker flags:
- **Sensitive permissions** — background location is an ERROR (needs a Play declaration with one core
  feature + demo video); other restricted permissions are warnings.
- **Exported components** with no permission/intent-filter (any app can invoke them).
- **targetSdk below the Play minimum** (blocks new apps/updates; hidden on new devices — version-sensitive).
- **Release config** — no R8 (`minifyEnabled`), debug signing config, or committed secrets.
- `debuggable`/`usesCleartextTraffic` in the manifest.

### 2. Clear the Play policy/console gates

- **Data Safety** form completed and **matching app + third-party-SDK behaviour** (mismatch = rejection).
- **Account deletion** (in-app + web URL) if the app has accounts; **privacy policy URL** live; **content
  rating** (IARC); ads/target-audience declarations.
- **Sensitive-permission declarations** with justification + demo video where required.

### 3. Build a signed app bundle

- **`versionCode` unique & monotonic** — stamp from `git rev-list --count HEAD` (or CI build number).
- `./gradlew bundleRelease` → a **signed `.aab`** (Play requires the bundle format). Verify locally with
  **bundletool** (`build-apks` / `install-apks`) — the exact split APKs Play will serve.

### 4. Upload to a track and roll out deliberately

- Upload to **internal testing first** (available in minutes, no review) to smoke-test; then **closed/
  open** (external needs the metadata above); then **production**.
- On production, use a **staged (percentage) rollout** starting small (e.g. 5–10%), and watch **Android
  vitals** (user-perceived crash ≥1.09% overall / ≥8% per-device, ANR ≥0.47% / ≥8% gate discoverability).
- Automate via the **Play Developer API** (edits flow: insert → bundles.upload → tracks.update →
  commit), **Gradle Play Publisher** (`com.github.triplet.play`), or **fastlane `supply`** — all with
  service-account JSON auth.

### 5. Halt / roll forward on regression (the Play advantage)

- If vitals regress mid-rollout, **Halt rollout** (the kill switch iOS lacks). Recover by **rolling
  forward**: publish a **higher-versionCode** fixed release to the same track (there is no literal byte
  revert — versionCode is monotonic). Consider an **immediate in-app update** for critical fixes.

### 6. Report

Summarise: pre-flight result (errors fixed), the versionCode and the commit it maps to, the track it
went to, the rollout percentage, and the policy gates cleared. State anything outstanding (e.g. Data
Safety not yet complete) rather than implying the release is ready.

## Notes

- Play policy dates/API levels/vitals thresholds are **version-sensitive** — re-verify against the live
  Google docs.
- Always ship production behind a **staged rollout** so you retain the halt lever.

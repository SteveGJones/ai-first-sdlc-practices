---
name: ios-ci
description: Generate a GitHub Actions workflow for iOS — macOS runner, SPM/DerivedData caching, build, test on a simulator matrix, run the iOS pre-flight checks, and (optionally) sign + upload to TestFlight. Use when setting up CI for an iOS app.
disable-model-invocation: false
argument-hint: "[path-to-ios-project]"
---

# iOS CI

Generate a GitHub Actions workflow for an iOS app. Complements (does not replace)
`/sdlc-core:setup-ci` — this adds the iOS-specific pieces (macOS runners, simulators, signing).
Belongs to the **`ios-release-engineer`** discipline.

## Arguments

- `path-to-ios-project` — the project directory (defaults to the current directory).

## Steps

### 1. Establish the project shape

- Workspace vs project, the scheme name, the deployment target, and whether it uses SwiftPM,
  CocoaPods, or Carthage (affects caching and the resolve step). Confirm the Xcode version to pin.

### 2. Generate the workflow

Produce an iOS CI workflow file under the `.github/workflows/` directory with:

- **Runner**: `runs-on: macos-14` (or the current macOS runner); select Xcode with
  `xcodes select` / `sudo xcode-select -s` pinned to the project's Xcode version.
- **Caching**: cache SwiftPM (`~/Library/Caches/org.swift.swiftpm`, `.build`) and/or CocoaPods
  (`Pods`, `~/Library/Caches/CocoaPods`); keyed on the lockfile.
- **Build & test**: `xcodebuild build test -scheme <Scheme> -destination
  'platform=iOS Simulator,name=iPhone 16,OS=latest'` — use a **simulator matrix** across the OS
  versions you support; pass `-resultBundlePath` and surface failures.
- **Lint/format**: SwiftLint / swift-format if the project uses them.
- **iOS pre-flight**: run `python -m ios_preflight.cli .` so config regressions (missing purpose
  strings, export compliance, entitlements) fail CI before a release ever reaches App Store Connect.

### 3. (Optional) Signing + TestFlight upload job

Only if the project releases from CI:

- **Secrets**: base64-encoded `.p12`, the `.mobileprovision`, keychain + `.p12` passwords, and the
  **App Store Connect API key** (`.p8` + key ID + issuer ID) — all in GitHub Actions encrypted secrets,
  never in the repo.
- **Signing**: create + unlock a temporary keychain, import the `.p12`, run
  `security set-key-partition-list`, install the profile; prefer **manual signing** or
  `fastlane match --readonly`.
- **Archive + upload**: `xcodebuild archive`/`-exportArchive` (Release + distribution profile) then
  upload via `fastlane pilot`, `xcrun altool`, or the App Store Connect API.
- **Build number**: stamp `CFBundleVersion` from `git rev-list --count HEAD` (+ short SHA) so every
  CI build is unique, monotonic, and traceable to a commit.
- **Sandboxing**: if a build-phase script reads git/env, that target may need
  `ENABLE_USER_SCRIPT_SANDBOXING = NO`.

### 4. Report

Summarise the workflow: what triggers it, the test matrix, whether it gates on pre-flight, and whether
it uploads to TestFlight. Note any secrets the user must add before it will run.

## Notes

- Xcode Cloud is the first-party alternative (managed signing, no `.p12` juggling) — mention it if the
  team is all-in on Apple tooling and doesn't need cross-platform CI steps.
- Keep the signing/upload job separate from build/test so PRs run fast without secrets.

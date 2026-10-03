# sdlc-team-ios

Focused **iOS/iPadOS development** plugin. Contains only iOS-relevant design expertise, so an iOS
team isn't wading through web, backend, or data specialists.

## Agents (4)

- **`apple-hig-architect`** — Apple Human Interface Guidelines / **design**: Liquid Glass (iOS 26),
  navigation & modality, SF typography & Dynamic Type, semantic colours & materials, SF Symbols,
  gestures/haptics, iOS platform features (permissions/ATT, notifications, Widgets, Live
  Activities/Dynamic Island, share sheet, Sign in with Apple), accessibility, App Store UX.
- **`swiftui-architect`** — SwiftUI **app architecture**: the Observation framework (`@Observable`),
  MV vs MVVM vs TCA, `NavigationStack` & deep linking, SwiftData persistence, structured concurrency
  & Swift 6 isolation, dependency injection & SwiftPM modularization, UIKit interop, Swift Testing.
- **`ios-release-engineer`** — **release & distribution**: code signing & provisioning, entitlements,
  the three privacy surfaces (nutrition labels / `PrivacyInfo.xcprivacy` / required-reason APIs),
  App Store Connect & TestFlight, App Review compliance, fastlane / Xcode Cloud / ASC API, versioning
  & the no-rollback release strategy.
- **`ios-performance-specialist`** — **performance**: Instruments (Time Profiler, Allocations/Leaks,
  Animation Hitches, SwiftUI & Swift Concurrency instruments), app launch, hitches/hangs, memory,
  energy/battery, MetricKit field metrics, app size/thinning, and XCTest performance regression gating.

The four cover the iOS lifecycle: **design → architecture → release → performance**.

## Skills (5)

Operational workflows for scaffolding and the release/distribution flow, encoding real TestFlight/App
Store incidents:

- **`/sdlc-team-ios:ios-scaffold`** — scaffold a new iOS app with submission-safe defaults (diffable
  project files, app + test targets, git-stamped build number, and the Info.plist keys the pre-flight
  checker wants) so the project passes TestFlight from day one.
- **`/sdlc-team-ios:ios-testflight-release`** — pre-flight checks → upload → confirm the build actually
  processed → internal-then-external beta distribution (with the metadata external Beta App Review needs).
- **`/sdlc-team-ios:ios-appstore-submit`** — pre-submission audit across the three privacy surfaces and
  the high-frequency App Review rejection guidelines.
- **`/sdlc-team-ios:ios-signing-doctor`** — diagnose and fix the signing/provisioning/entitlement
  failure family (`codesign`/`security` inspection + a symptom→cause table).
- **`/sdlc-team-ios:ios-ci`** — generate an iOS GitHub Actions workflow (macOS runner, simulator matrix,
  pre-flight gate, optional signed TestFlight upload).

## Pre-flight checker

`scripts/ios_preflight` is a static checker the release skills invoke — it catches the config that most
often blocks uploads: missing usage descriptions (the CoreMotion→`NSMotionUsageDescription` /
ITMS-90683 class), missing `ITSAppUsesNonExemptEncryption` (export-questionnaire stalls), missing
`PrivacyInfo.xcprivacy` when required, and `get-task-allow` in a release build.

```bash
python -m ios_preflight.cli <ios-project-dir> [--uses-push]
```

For **Swift the language** (concurrency/`Sendable`, value semantics, generics, macros, SwiftPM),
install the companion **`sdlc-lang-swift`** plugin (`language-swift-expert`) — `/sdlc-core:setup-team`
recommends it for iOS projects.

## Install with the mobile base

iOS work also needs cross-platform mobile expertise, which lives in **`sdlc-team-mobile`**
(`mobile-architect`, `mobile-ux-architect`). Install both together — `/sdlc-core:setup-team`
recommends them as a unit when you select an iOS project type.

## Part of the SDLC plugin family

Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` for personalized recommendations.

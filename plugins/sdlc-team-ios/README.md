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

The four cover the iOS lifecycle: **design → architecture → release → performance**. A Swift language
expert and iOS skills/validators are planned — see EPIC #217.

## Install with the mobile base

iOS work also needs cross-platform mobile expertise, which lives in **`sdlc-team-mobile`**
(`mobile-architect`, `mobile-ux-architect`). Install both together — `/sdlc-core:setup-team`
recommends them as a unit when you select an iOS project type.

## Part of the SDLC plugin family

Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` for personalized recommendations.

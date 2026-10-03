# iOS SwiftUI App Architecture — Research Reference

Authoritative reference on **modern iOS app architecture with SwiftUI** (iOS 26 / Xcode 26 /
Swift 6.2), gathered to ground the
[`swiftui-architect`](../../agents/core/swiftui-architect.md) agent (feature #219, EPIC #217).

**Compiled:** 2026-07-23. API availability is called out per feature (Observation iOS 17,
NavigationStack iOS 16, SwiftData iOS 17+) because most apps back-deploy. Community patterns (TCA,
swift-dependencies, Factory) are labelled non-Apple. Version-sensitive API details should be
re-checked against Apple's documentation. Sourcing note: Apple's doc pages are JS-rendered, so
content was grounded in WebSearch surfacing Apple/WWDC pages + verified API knowledge — see the file's
Sources list (official Apple separated from community).

## Contents

| File | Covers |
|------|--------|
| [`01-swiftui-architecture.md`](01-swiftui-architecture.md) | Observation (`@Observable`) & property wrappers, MV vs MVVM vs TCA, NavigationStack & value-based navigation/deep linking, SwiftData (+ CloudKit constraints) & Core Data interop, structured concurrency & Swift 6 isolation, DI & SwiftPM modularization, UIKit interop, Swift Testing, anti-patterns |

## Key facts at a glance

- **`@Observable` (iOS 17)** replaced `ObservableObject`/`@Published`/`@StateObject`; per-property invalidation. Own with `@State`, vend bindings with `@Bindable`, share via `@Environment(Type.self)`. Doesn't mix with legacy wrappers.
- **Architecture**: default **MV** (no per-view ViewModels) → targeted ViewModel where logic warrants → **TCA** (community) for large determinism-critical apps.
- **Navigation**: `NavigationStack` + `NavigationLink(value:)` + `.navigationDestination(for:)` + `NavigationPath`/typed routes (Router-owned); deep links = data mutations.
- **Persistence**: SwiftData (`@Model`/`ModelContainer`/`@Query`) default; CloudKit needs optional/defaulted props, no `.unique`, no `.deny`; Core Data for gaps/legacy; Keychain for secrets.
- **Concurrency**: `.task` for lifecycle-bound async; `@MainActor` models; `actor`s for shared state; Swift 6.2 default main-actor isolation.
- **Testing**: Swift Testing (`@Test`/`#expect`/`#require`) for logic; XCTest for UI + performance.

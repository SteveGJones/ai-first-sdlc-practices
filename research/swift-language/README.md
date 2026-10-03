# Swift Language — Research Reference

Authoritative reference on **the Swift language** (Swift 6.2, released 15 September 2025), gathered to
ground the [`language-swift-expert`](../../agents/sdlc/language-swift-expert.md) agent (feature #223,
EPIC #217).

**Compiled:** 2026-07-23. Features are tagged with the introducing Swift version and Swift Evolution
proposal (`SE-NNNN`). Version-sensitive concurrency details (6.2 is recent and evolving) should be
re-checked against swift.org. Scope is the **language**, not UI frameworks (SwiftUI/UIKit →
`swiftui-architect` / `apple-hig-architect`).

## Contents

| File | Covers |
|------|--------|
| [`01-swift-language.md`](01-swift-language.md) | Concurrency (async/await, structured concurrency, actors, `Sendable`, global actors, region-based isolation, Swift 6 strict concurrency, Swift 6.2 approachable concurrency), value semantics & noncopyable types, error handling (typed throws), optionals/safety, generics & protocols (opaque vs existential, primary associated types, parameter packs), macros, ARC, expressive features, SwiftPM, the API Design Guidelines, Swift Testing, C/Obj-C/C++ interop, and idioms/anti-patterns/"language debt" + Swift 6 migration |

## Key facts at a glance

- **Language mode vs compiler version**: mode 6 turns on complete data-race checking as errors; a 6.2 compiler can still build mode 5. Migrate incrementally (`-strict-concurrency=complete` → mode 6).
- **Swift 6.2 "approachable concurrency"** (the big recent shift): default `MainActor` isolation (SE-0466) + `nonisolated async` runs on the caller's actor with `@concurrent` as the explicit background opt-out (SE-0461). Review guidance becomes "add `@MainActor`/`@concurrent`", not "sprinkle `@unchecked Sendable`."
- **Value types by default**; classes only for identity/inheritance/shared mutable state. Noncopyable `~Copyable` + `consuming`/`borrowing` for unique-ownership resources.
- **Typed throws** (SE-0413) — use for exhaustive local handling / generic error propagation; untyped `throws` still preferred for most public APIs.
- **`some` (opaque) over `any` (existential)** unless heterogeneity is needed; spell `any` explicitly.
- **Swift Testing** (`@Test`/`#expect`/`#require`, parameterized, parallel) for unit tests; XCTest for UI + performance.
- **Top review smells**: force-unwrap/`try!` density, `fatalError` on live paths, `@unchecked Sendable`/`nonisolated(unsafe)` overuse, `Task.detached`, ignored cancellation, reference-where-value-fits, stringly-typed code.

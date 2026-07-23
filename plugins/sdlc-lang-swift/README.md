# sdlc-lang-swift

Swift **language** expertise — idiomatic Swift 6.2, grounded in swift.org. A language plugin in the
family alongside `sdlc-lang-python` and `sdlc-lang-javascript`.

## Agents (1)

- **`language-swift-expert`** — the Swift language: strict concurrency (async/await, actors,
  `Sendable`, Swift 6 data-race safety, Swift 6.2 default main-actor isolation), value semantics &
  noncopyable types, error handling (typed throws), optionals & safety, generics & protocols (opaque
  `some` vs existential `any`, parameter packs), macros, ARC & capture lists, result builders &
  property wrappers, SwiftPM, the API Design Guidelines, Swift Testing, C/Obj-C/C++ interop, and
  idiomatic-vs-anti-pattern review (force-unwrap/`try!` density, `fatalError` in production,
  `@unchecked Sendable` overuse). Covers the *language*, not app/UI frameworks.

## Relationship to other plugins

Swift is the language behind Apple-platform apps but is also used server-side and on other Apple
platforms, so it lives in its own language plugin rather than inside `sdlc-team-ios`. For iOS work,
install it **alongside** `sdlc-team-ios` (`/sdlc-core:setup-team` recommends the pair for iOS
projects):

- **`sdlc-team-ios`** — Apple HIG design, SwiftUI app architecture, release engineering, performance
- **`sdlc-team-mobile`** — cross-platform mobile architecture + interaction UX

Scope split: `language-swift-expert` owns Swift-the-language; `swiftui-architect` (in `sdlc-team-ios`)
owns SwiftUI app architecture; `apple-hig-architect` owns visual/HIG design.

## Part of the SDLC plugin family

Install `sdlc-core` first, then add plugins matching your project. Run `/sdlc-core:setup-team` for
personalized recommendations.

# sdlc-lang-kotlin

Kotlin **language** expertise — idiomatic Kotlin 2.x, grounded in kotlinlang.org. A language plugin in
the family alongside `sdlc-lang-python`, `sdlc-lang-javascript`, and `sdlc-lang-swift`.

## Agents (1)

- **`language-kotlin-expert`** — the Kotlin language: null-safety & scope functions, **coroutines &
  structured concurrency** (dispatchers, cancellation, exception handling), **Flow**
  (`StateFlow`/`SharedFlow`, operators, `flowOn`, `stateIn`), the type system (data/sealed/value
  classes, delegation, K2 `when` guards), functions (`inline`/`reified`, extensions, higher-order),
  generics & variance, stdlib idioms (collections/sequences, `require`/`check`, `Result`), KSP at the
  language level, Java interop, Kotlin Multiplatform basics, and an idiomatic-vs-anti-pattern review
  checklist (`!!` density, `GlobalScope`, blocking in coroutines, swallowed cancellation,
  stringly-typed code). Covers the *language*, not the Android framework.

## Relationship to other plugins

Kotlin is the language behind Android but is also used for server-side, KMP, and multiplatform, so it
lives in its own language plugin rather than inside `sdlc-team-android`. For Android work, install it
**alongside** `sdlc-team-android` (`/sdlc-core:setup-team` recommends the pair for Android projects):

- **`sdlc-team-android`** — Material Design 3, Jetpack Compose, app architecture, Gradle, Play release, performance
- **`sdlc-team-mobile`** — cross-platform mobile architecture + interaction UX

Scope split: `language-kotlin-expert` owns Kotlin-the-language; `android-app-architect` and
`jetpack-compose-architect` (in `sdlc-team-android`) own the Android framework; `gradle-build-specialist`
owns the build (including Kotlin/KSP version coupling).

## Part of the SDLC plugin family

Install `sdlc-core` first, then add plugins matching your project. Run `/sdlc-core:setup-team` for
personalized recommendations.

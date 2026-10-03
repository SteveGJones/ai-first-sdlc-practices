# Jetpack Compose UI Architecture — Research Reference

Grounds the [`jetpack-compose-architect`](../../agents/core/jetpack-compose-architect.md) agent
(feature #226, Android sub-epic #225). Compiled 2026-07-23 from official Android sources
(developer.android.com + Android Developers blog). Compose evolves fast — version-sensitive facts are
flagged in the file; confirm against the consumer's Compose BOM / Kotlin version.

| File | Covers |
|------|--------|
| [`01-jetpack-compose.md`](01-jetpack-compose.md) | Composition/recomposition, stability & strong skipping, `remember`/state, hoisting & UDF, side-effect APIs, layout & `Modifier.Node`, lazy lists, type-safe Navigation-Compose (+ Nav3 alpha), architecture patterns, performance (phases/deferred reads/compiler metrics), testing, View interop |

**At a glance:** strong skipping is default on Kotlin 2.0.20+; `List`/`Map`/cross-module types are unstable; defer reads to layout/draw via lambda modifiers; type-safe Navigation is stable since Navigation 2.8 (Navigation 3 is alpha); measure on release + Baseline Profile builds.

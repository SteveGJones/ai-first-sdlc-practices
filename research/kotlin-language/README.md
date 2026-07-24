# Kotlin Language — Research Reference

Grounds the [`language-kotlin-expert`](../../agents/sdlc/language-kotlin-expert.md) agent (feature #228,
Android sub-epic #225). Compiled 2026-07-23 from kotlinlang.org / JetBrains. Kotlin ships an incremental
release train (2.0 May 2024, 2.1 Nov 2024, 2.2 mid-2025); every Preview/Beta/Experimental feature is
tagged with its opt-in flag and first-availability version — re-check against the target project's exact
Kotlin version. Scope is the **language + coroutines/stdlib**, not the Android framework. Community tools
(Turbine) are labelled non-JetBrains.

| File | Covers |
|------|--------|
| [`01-kotlin-language.md`](01-kotlin-language.md) | K2 compiler & 2.x feature-availability matrix, null-safety & scope functions, coroutines & structured concurrency (dispatchers/cancellation/exception handling), Flow (StateFlow/SharedFlow, operators, flowOn, stateIn), type system (data/sealed/value classes, delegation), functions (inline/reified, extensions), generics/variance, stdlib idioms, KSP (KSP2), Java interop, KMP basics, idioms/anti-patterns/"language debt" |

**At a glance:** K2 is default since 2.0 (wider smart-casts); guard conditions / non-local break-continue / multi-dollar interpolation are Stable in 2.2 (preview in 2.1); context parameters are 2.2 Preview (replace deprecated context receivers); never swallow `CancellationException`; `CoroutineExceptionHandler` fires only for roots; Flow exception transparency + `flowOn` context-preservation; KSP2 default (KSP1 deprecated from 2.2); top review smells — `!!` density, `GlobalScope`, blocking a dispatcher, stringly-typed code, non-sealed closed hierarchies.

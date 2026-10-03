# Feature Proposal: sdlc-lang-kotlin (language-kotlin-expert)

**Proposal Number:** 228
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/sdlc-lang-kotlin`
**GitHub Issue:** #228 (Phase 2 of Android sub-epic #225; part of EPIC #217)

---

## Motivation

The Android sub-epic (#225) added the five platform agents (#227), but nobody owns **Kotlin the
language**. `android-app-architect` and `jetpack-compose-architect` own the Android framework;
`gradle-build-specialist` owns the build — but coroutines/Flow semantics, null-safety, sealed/value
classes, generics, and idiomatic-Kotlin review sit beneath all of them and belong to a language
specialist. This mirrors iOS, where `swiftui-architect` (framework) is paired with `language-swift-expert`
(language, in `sdlc-lang-swift`).

This proposal adds `sdlc-lang-kotlin` with `language-kotlin-expert`, completing the language-plugin
family (`sdlc-lang-python` / `-javascript` / `-swift` / **`-kotlin`**) and resolving the Kotlin-placement
question the same way as Swift: a **dedicated language plugin** (Kotlin is also server-side / KMP, so it
shouldn't be trapped inside `sdlc-team-android`).

## User Stories

- As a **Kotlin developer**, I want a `language-kotlin-expert` that reviews idiomatic Kotlin 2.x —
  coroutines & structured concurrency, Flow, null-safety, sealed/value classes — distinct from Android
  framework advice.
- As someone **fighting coroutine bugs** (leaked scopes, swallowed cancellation, blocking a dispatcher),
  I want authoritative guidance grounded in the official coroutines model.
- As an **Android team**, I want `/sdlc-core:setup-team` to recommend `sdlc-lang-kotlin` alongside
  `sdlc-team-android`.

## Proposed Solution

### High-Level Approach

Add one language plugin following the family pattern (agent-only,
`agents/sdlc/language-<lang>-expert.md`), grounded in deep research on Kotlin 2.x (K2 compiler).

### Technical Approach

1. **`sdlc-lang-kotlin` plugin (0.1.0)** — plugin.json + README + the agent.
2. **`language-kotlin-expert`** (`agents/sdlc/`) — null-safety & scope functions, coroutines &
   structured concurrency, Flow (StateFlow/SharedFlow), the type system (data/sealed/value classes,
   delegation), functions (inline/reified, extensions), generics/variance, stdlib idioms, KSP at the
   language level, Java interop, Kotlin Multiplatform basics, K2/2.x specifics, and an idiomatic/
   anti-pattern review checklist. Scope is the language, not the Android framework.
3. **Wiring**: `release-mapping.yaml` (new plugin); `marketplace.json` (+plugin); `setup-team` matrix
   recommends `sdlc-lang-kotlin` for Android / cross-platform (→ `sdlc-core` 1.3.0 → 1.4.0);
   cross-reference from the Android agents; AGENT-INDEX/CATALOG; plugin READMEs + CLAUDE.md/README.
4. **Validation**: `validate-agent-format`, `validate-agent-official`, technical-debt, broken-references,
   packaging, tests.

### Alternatives Considered

1. **Bundle Kotlin into `sdlc-team-android`** (Fable's Android advisor's original take). Rejected for
   symmetry with `sdlc-lang-swift` and because Kotlin is used well beyond Android (server-side, KMP).
2. **Defer Kotlin entirely.** Rejected — it leaves an obvious gap directly parallel to the Swift plugin
   that already shipped.

---

## Implementation Plan

### Phase 1: Plugin scaffolding + research
- [ ] Create `sdlc-lang-kotlin` plugin (plugin.json, README) + release-mapping + marketplace entries
- [ ] Research Kotlin 2.x; persist under `research/kotlin-language/`

### Phase 2: Agent
- [ ] Write `agents/sdlc/language-kotlin-expert.md`; package into the plugin

### Phase 3: Wiring, validation & release
- [ ] setup-team matrix (+ sdlc-core 1.3.0 → 1.4.0); docs/counts; regenerate AGENT-INDEX/CATALOG
- [ ] Validators + tests; retrospective; PR

**Dependencies:** none new. Builds on #227 (Android agents exist).

---

## Success Criteria

```
Given a user asks language-kotlin-expert about a leaked coroutine / swallowed cancellation
When it responds
Then it explains structured concurrency, scope/Job/Dispatchers, and cooperative cancellation correctly
     for Kotlin 2.x — distinct from Android app-architecture advice
```

```
Given a user asks about StateFlow vs SharedFlow or cold vs hot Flow
When it responds
Then it gives the correct semantics and when to use each, grounded in the official Flow model
```

```
Given the new agent file
When CI agent-format / official validation runs
Then it passes (valid frontmatter, >=2 examples, allowed color, no technical debt, no broken refs)
```

```
Given /sdlc-core:setup-team with an "Android app" project type
When recommendations are produced
Then sdlc-lang-kotlin is recommended alongside sdlc-team-android and sdlc-team-mobile
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Kotlin 2.x details date (context params/receivers evolving) | Med | Low | Ground in kotlinlang.org; flag experimental/version-sensitive; note availability per feature |
| Overlap with android-app-architect / jetpack-compose-architect | Med | Low | Explicit split: language vs framework; cross-reference |
| Marketplace reformatting / broken-ref prose false positives | Low | Low | Edit compact JSON one-liners; avoid bare `filename.ext` in prose (learned this EPIC) |

## Open Questions

- [ ] Kotlin lint/debt validators later (as the Python plugin implies)? Deferred.
- [ ] Android skills + validators — Phase 3 of #225.

## Security & Privacy

N/A. Static agent definition + research reference. No code execution, auth, data handling, or secrets.

---

**Retrospective**: `retrospectives/228-sdlc-lang-kotlin.md` (link after implementation)

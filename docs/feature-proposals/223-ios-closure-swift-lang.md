# Feature Proposal: iOS closure — ios-scaffold skill + sdlc-lang-swift

**Proposal Number:** 223
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/ios-closure-swift-lang`
**GitHub Issue:** #223 (phase of EPIC #217; resolves decision D2)

---

## Motivation

The iOS work in EPIC #217 has agents (#220) and release skills + pre-flight checks (#222). Two gaps
remain before iOS is "done" and Android can start as a sub-epic:

1. **No scaffold path.** A new iOS project should start *submission-safe* — with the export-compliance
   key, a git-stamped build number, the `ENABLE_USER_SCRIPT_SANDBOXING` handling, and usage-string
   placeholders already wired — so it doesn't hit the TestFlight blockers `ios-testflight-release` and
   the pre-flight checker exist to catch. Today there's no skill that produces that.
2. **No Swift language expert.** `swiftui-architect` owns app architecture and `apple-hig-architect`
   owns design, but nobody owns **Swift the language** (concurrency/Sendable, value semantics, typed
   throws, generics, macros, SwiftPM, API design). EPIC #217 left this as decision **D2**.

This proposal closes both, resolving **D2 in favour of a dedicated `sdlc-lang-swift` plugin**,
consistent with the existing `sdlc-lang-python` / `sdlc-lang-javascript` language plugins (Swift is
also used server-side and on other Apple platforms, so it shouldn't be trapped inside `sdlc-team-ios`).

## User Stories

- As an **iOS developer starting a project**, I want `ios-scaffold` to produce a project that passes
  the pre-flight checker on day one, so submission config isn't an afterthought.
- As a **Swift developer**, I want a `language-swift-expert` that reviews idiomatic Swift 6.2 —
  strict concurrency, `Sendable`, value semantics, generics, macros — distinct from SwiftUI/app
  architecture.
- As someone setting up an **iOS project**, I want `/sdlc-core:setup-team` to recommend the Swift
  language plugin alongside `sdlc-team-ios`.

## Proposed Solution

### High-Level Approach

Add one skill to `sdlc-team-ios` and one new language plugin, following the family's established
patterns (skill = SKILL.md; language plugin = agent-only, `agents/sdlc/language-<lang>-expert.md`).

### Technical Approach

1. **`ios-scaffold` skill** (`skills/ios-scaffold`, released to `sdlc-team-ios`) — generate a project
   with diffable project files (SwiftPM/Tuist/XcodeGen), app + test targets, `.gitignore`,
   deployment-target policy, submission-safe Info.plist defaults (`ITSAppUsesNonExemptEncryption`,
   usage-string placeholders), a git-stamped `CFBundleVersion` build phase with
   `ENABLE_USER_SCRIPT_SANDBOXING = NO`, release-default-safe flags, and a pre-flight verification step.
2. **`sdlc-lang-swift` plugin** with **`language-swift-expert`** agent (`agents/sdlc/`), grounded in
   deep research on Swift 6.2 (concurrency/actors/Sendable & strict concurrency, value semantics &
   noncopyable types, typed throws, optionals, generics/protocols [opaque vs existential, parameter
   packs], macros, ARC, result builders/property wrappers, SwiftPM, API Design Guidelines, Swift
   Testing, interop, and idiomatic/anti-pattern review).
3. **Wiring**: `release-mapping.yaml` (scaffold skill + the new plugin), `marketplace.json` (+ plugin,
   bumps), `setup-team` matrix (recommend `sdlc-lang-swift` for iOS / cross-platform → `sdlc-core`
   1.2.0 → 1.3.0), `sdlc-team-ios` 0.3.0 → 0.4.0, `sdlc-lang-swift` 0.1.0, plugin READMEs +
   CLAUDE.md/README, regenerate AGENT-INDEX/CATALOG.

### Alternatives Considered

1. **Bundle the Swift expert into `sdlc-team-ios`** (Android advisor's take for Kotlin). Rejected for
   Swift — the two existing language plugins set a strong precedent, and Swift's use beyond iOS argues
   for a language plugin. (D2 resolved: separate plugin.)
2. **No scaffold skill** (leave project setup to the developer). Rejected — the submission-safe defaults
   are exactly the recurring pain the release phase (#222) was built to prevent; baking them into a
   scaffold is the highest-leverage prevention.

---

## Implementation Plan

### Phase 1: Scaffold + plugin scaffolding
- [ ] Author `ios-scaffold` skill; add to release-mapping + package into sdlc-team-ios
- [ ] Create `sdlc-lang-swift` plugin (plugin.json, README) + release-mapping + marketplace entries

### Phase 2: Swift research + agent
- [ ] Research Swift 6.2 language; persist under `research/swift-language/`
- [ ] Write `agents/sdlc/language-swift-expert.md`; package into the plugin

### Phase 3: Wiring, validation & release
- [ ] setup-team matrix (+ sdlc-core 1.2.0 → 1.3.0); sdlc-team-ios → 0.4.0; docs/counts
- [ ] Regenerate AGENT-INDEX/CATALOG; ruff/format, packaging, technical-debt, broken-references, tests
- [ ] Retrospective; PR

**Dependencies:** none new. Builds on #222 (iOS plugin exists).

---

## Success Criteria

```
Given a user runs ios-scaffold for a new app
When the scaffold completes
Then the project has ITSAppUsesNonExemptEncryption set, a git-stamped build number with
     ENABLE_USER_SCRIPT_SANDBOXING=NO on that target, and passes the pre-flight checker (no ERRORs)
```

```
Given a user asks language-swift-expert about a Swift 6 data-race / Sendable error
When it responds
Then it explains actor isolation / Sendable correctly for Swift 6.2 (incl. default main-actor
     isolation), distinct from SwiftUI app-architecture advice
```

```
Given the new agent file
When CI agent-format / official validation runs
Then it passes (valid frontmatter, >=2 examples, allowed color, no technical debt, no broken refs)
```

```
Given /sdlc-core:setup-team with an "iOS app" project type
When recommendations are produced
Then sdlc-lang-swift is recommended alongside sdlc-team-ios and sdlc-team-mobile
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Swift language details date fast (6.2 concurrency evolving) | Med | Low | Ground in swift.org + evolution proposals; flag version-sensitive items; note availability per feature |
| Overlap between language-swift-expert and swiftui-architect | Med | Low | Explicit split: language vs app architecture; cross-reference |
| Marketplace reformatting regressions | Low | Low | Edit compact one-line entries directly, not via bulk JSON rewrite (learned this session) |
| Agent-format CI (desc length / color enum) | Low | Med | Mirror validated agents; check limits before authoring |

## Open Questions

- [ ] Should `sdlc-lang-swift` later gain Swift lint/debt validators (as the Python plugin implies)? Deferred.
- [ ] `fastlane-setup` skill — optional follow-up.

## Security & Privacy

N/A. Static agent definition + a scaffold skill (workflow guidance) + research reference. The scaffold
skill explicitly instructs against committing secrets/keys. No code execution, auth, or data handling.

---

**Retrospective**: `retrospectives/223-ios-closure-swift-lang.md` (link after implementation)

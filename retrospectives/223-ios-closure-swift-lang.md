# Retrospective: iOS closure — ios-scaffold skill + sdlc-lang-swift

**Branch:** `feature/ios-closure-swift-lang`
**Date:** 2026-07-23
**Duration:** ~1 session (scaffold skill + Swift research + agent + wiring)

---

## Summary

Closing out the iOS story in EPIC #217: adding an `ios-scaffold` skill (submission-safe project
defaults) and a `sdlc-lang-swift` plugin with `language-swift-expert` — resolving decision D2 in
favour of a dedicated language plugin (consistent with `sdlc-lang-python`/`-javascript`). Living
document, completed before PR.

## What Went Well

- **D2 resolved by convention, not debate**: the two existing language plugins made "separate
  `sdlc-lang-swift`" the obvious, consistent choice.
- **ios-scaffold encodes prevention**: it pre-wires exactly the config the #222 pre-flight checker
  looks for (export compliance, git-stamped build number, sandboxing), so new projects start clean.
- **Current, SE-tagged Swift research**: the reference tagged every feature with its Swift version +
  evolution proposal and led with Swift 6.2 "approachable concurrency" — so the agent's guidance is
  accurate about language-mode-vs-compiler-version, not folklore.

## What Could Improve

- **Marketplace JSON reformatting**: a `json.dump` bulk-rewrite reflowed the compact one-line-per-plugin
  format to indented multi-line + `—` escapes. Caught immediately; reverted with `git checkout`
  and re-applied as minimal one-line Edits. Lesson: **edit the compact JSON entries directly; never
  round-trip the whole file through `json.dump`.** (Two later version bumps were done with `json.dump`
  on the individual `plugin.json` files — those are already pretty-printed, so that's fine; only the
  hand-formatted `marketplace.json` needs targeted edits.)
- **Two broken-reference false positives from prose** (`project.yml`, and earlier `.github/...yml`) —
  the checker reads bare `filename.ext` tokens in backticked prose as links. Reworded. Same recurring
  class as `Motion.md`/`<page>.json`; a prose-allowlist in the checker would end it.

## Lessons Learned

1. **Prefer targeted text edits over full-file re-serialization** for hand-formatted config (marketplace.json).
2. **Convention beats deliberation for well-precedented decisions.** D2 (Swift language plugin placement)
   was open for several phases; the two existing `sdlc-lang-*` plugins made "separate plugin" the
   obvious answer once it was time to build.
3. **Scaffolding-as-prevention closes the loop with the checker.** `ios-scaffold` and the #222
   pre-flight checker are two halves of one idea — generate config that passes, then verify it stays passing.

## Changes Made

### Files Created
- `docs/feature-proposals/223-ios-closure-swift-lang.md`, `retrospectives/223-ios-closure-swift-lang.md`
- `skills/ios-scaffold/SKILL.md` (+ plugin copy)
- `plugins/sdlc-lang-swift/` (plugin.json, README, agents/) + `agents/sdlc/language-swift-expert.md` _(pending research)_
- `research/swift-language/` _(pending)_

### Files Modified
- `release-mapping.yaml` — ios-scaffold skill + sdlc-lang-swift section
- `.claude-plugin/marketplace.json` — +sdlc-lang-swift; sdlc-team-ios → 0.4.0; sdlc-core → 1.3.0
- `plugins/sdlc-team-ios/.claude-plugin/plugin.json` → 0.4.0; `plugins/sdlc-core/.claude-plugin/plugin.json` → 1.3.0
- `skills/setup-team/SKILL.md` (+ plugin copy) — recommend sdlc-lang-swift for iOS/cross-platform
- `plugins/sdlc-team-ios/README.md`, `CLAUDE.md`, `README.md` — counts/tables

## Action Items

- [ ] Complete `language-swift-expert` from research; regenerate catalog; validate; PR
- [ ] **Android platform agents — the next sub-epic** (kotlin-android, jetpack-compose, app-architect, gradle, play-store, performance)
- [ ] Optional iOS: `fastlane-setup` skill; Swift lint/debt validators in sdlc-lang-swift

# Retrospective: sdlc-lang-kotlin (language-kotlin-expert)

**Branch:** `feature/sdlc-lang-kotlin`
**Date:** 2026-07-23
**Duration:** ~1 session (research + agent + wiring)

---

## Summary

Phase 2 of the Android sub-epic (#225): adding the `sdlc-lang-kotlin` plugin with `language-kotlin-expert`,
completing the language-plugin family (`python`/`javascript`/`swift`/`kotlin`) and mirroring
`sdlc-lang-swift`. Delivered with all validators green and 815 tests passing.

## What Went Well

- **Direct Swift precedent**: `sdlc-lang-swift` made the plugin shape, boundary split, and setup-team
  wiring mechanical — scaffolding was done while research ran, and the marketplace edits were clean
  one-liners (no json.dump reformat this time).
- **Current, version-tagged research**: the Kotlin reference tagged every 2.x feature Stable/Preview with
  its opt-in flag (guard conditions Stable in 2.2, context parameters 2.2 preview replacing deprecated
  context receivers), so the agent's guidance is precise about K2/version status.
- **The Android agents already referenced it**: I''d written the Android platform agents to route
  "Kotlin-the-language → language-kotlin-expert", so those cross-references resolved the moment the agent
  landed — no back-edits needed.

## What Could Improve

- Nothing notable — the language-plugin playbook (Swift → Kotlin) is now fully routine: research → agent
  → wire → validate → PR, clean first pass.

## Lessons Learned

1. **Forward-referencing pays off.** Writing the Android agents'' boundaries to name the not-yet-built
   `language-kotlin-expert` meant zero rework when it shipped.
2. **Symmetry compounds.** Each language plugin (swift, now kotlin) gets faster because the shape,
   boundaries, setup-team wiring, and docs are identical to the last.

## Changes Made

### Files Created
- `docs/feature-proposals/228-sdlc-lang-kotlin.md`, `retrospectives/228-sdlc-lang-kotlin.md`
- `plugins/sdlc-lang-kotlin/` (plugin.json, README, agents/) + `agents/sdlc/language-kotlin-expert.md`
- `research/kotlin-language/` (reference + README)

### Files Modified
- `release-mapping.yaml` — sdlc-lang-kotlin section
- `.claude-plugin/marketplace.json` — +sdlc-lang-kotlin; sdlc-core → 1.4.0
- `plugins/sdlc-core/.claude-plugin/plugin.json` → 1.4.0
- `skills/setup-team/SKILL.md` (+ plugin copy) — recommend sdlc-lang-kotlin for Android/cross-platform
- `CLAUDE.md`, `README.md` — plugin tables/counts

## Action Items

- [ ] Complete `language-kotlin-expert` from research; cross-reference Android agents; regenerate catalog; validate; PR
- [ ] Phase 3 of #225: Android skills (scaffold/signing/play-release/ci) + validators

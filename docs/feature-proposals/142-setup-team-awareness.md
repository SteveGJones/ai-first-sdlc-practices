# Feature Proposal: Setup-Team Awareness — Pre/Post Check + Knowledge Base + Language Detection

**Proposal Number:** 142
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-09
**Target Branch:** `feature/142-setup-team-awareness`
**EPIC:** #142
**Sub-features:** #151 (pre/post check), #143 (knowledge-base recommendation), #144 (language auto-detection)

---

## Motivation

Setup-team has three related gaps:

1. **No awareness of what's already installed.** Recommends plugins the user already has. Never verifies whether recommendations were acted on. The user gets a blind list every time.
2. **`sdlc-knowledge-base` is invisible during setup.** Never mentioned, never recommended. Users only discover it by browsing the marketplace.
3. **Language auto-detection only covers Python and JavaScript.** Go, Java, Rust, Ruby are detected by the tech stack scanner but no language plugin recommendation follows.

---

## Proposed Solution

Three changes to setup-team, bundled into one branch because they all modify the same file and compose well:

### Sub-feature 0 (#151): Pre/post check

- **New step 0** before anything else: read `enabledPlugins` from global and project settings, report what's already installed, record the state for later filtering
- **Updated steps 4, 7, 8**: already-installed plugins get `✓ (already installed)` marker instead of install commands; install list only shows what's new
- **New step 12** at the end: re-check `enabledPlugins`, compare against recommendations, report what landed vs what's still pending, re-present pending install commands

### Sub-feature 1 (#143): `sdlc-knowledge-base` in step 6

- Added as a third option alongside `sdlc-team-pm` and `sdlc-team-docs`: "Do you need evidence-grounded decisions?"
- Brief description + when-to-use/when-not-to guidance
- Added to the recommendation output's Project Support section

### Sub-feature 2 (#144): Language auto-detection extension

- Step 4 extended: `.go` → `sdlc-lang-go` (if available), `.java` → `sdlc-lang-java`, `.rs` → `sdlc-lang-rust`, `.rb` → "detected but no plugin available"
- Checks marketplace availability before recommending; notes unavailable plugins honestly
- Pre-check aware: skips already-installed language plugins

---

## Success Criteria

- [ ] Step 0 pre-check reads global + project `enabledPlugins` and reports current state
- [ ] Recommendation output marks already-installed plugins with `✓` instead of install commands
- [ ] Install command list in step 8 excludes already-installed plugins
- [ ] Step 12 post-check re-reads state and reports what landed
- [ ] `sdlc-knowledge-base` mentioned in step 6 with description and guidance
- [ ] `sdlc-knowledge-base` appears in the Project Support section of step 7 output
- [ ] Language auto-detection covers Go, Java, Rust, Ruby (with honest "not available" for missing plugins)
- [ ] Both source and plugin copy of setup-team updated
- [ ] `check-plugin-packaging.py` passes
- [ ] CI passes

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `skills/setup-team/SKILL.md` (new step 0, updated steps 4/6/7/8, new step 12) |
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` (plugin copy) |
| Create | `docs/feature-proposals/142-setup-team-awareness.md` (this file) |

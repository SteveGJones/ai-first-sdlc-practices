# Retrospective: Android skills + Play pre-flight checks

**Branch:** `feature/android-skills-validators`
**Date:** 2026-07-23
**Duration:** ~1 session (EPIC #217 / sub-epic #225 final phase)

---

## Summary

Phase 3 (final) of the Android sub-epic: a tested Android **pre-flight checker** and four **release
skills** into `sdlc-team-android` (0.2.0 → 0.3.0), mirroring the iOS toolkit. The plugin now ships
6 agents + 4 skills + the checker. Test-first; 26 pre-flight tests pass, ruff/format clean, packaging
passes. **Completes the Android sub-epic and EPIC #217's mobile build-out — both platforms end with
identical shape** (agents + language plugin + skills + pre-flight checks).

## What Went Well

- **Direct iOS precedent (`ios_preflight`)** made the checker structure, conftest registration, and
  release-mapping wiring mechanical — and I applied the two banked lessons up front: test functions
  annotated `-> None` (technical-debt gate) and marketplace edited as one-liners (no json.dump reformat).
- **Real Play blockers as tests**: the background-location ERROR, the target-API mandate, unguarded
  exported components, and debug-signed/secret-committing releases each became a concrete test case.
- **Right division of labour**: the checker owns statically-checkable config; skills own the workflow
  sequencing (internal→production, staged rollout, halt/roll-forward); `./gradlew lint` owns a11y/M3
  (not reimplemented in Python, per the Fable steer).

## What Could Improve

- Nothing notable — the platform-toolkit playbook (iOS → Android) ran clean first pass. The recurring
  broken-reference-in-prose class didn't bite this time (no bare `filename.ext` tokens in the skills).

## Lessons Learned

1. **The second platform is much cheaper.** Every artefact (checker shape, skill structure, conftest
   registration, version-bump discipline) was a direct analogue of iOS — symmetry compounds.
2. **Encode the policy that dates, but make it configurable.** The Play target-API minimum is
   `--play-min-target` (default 35) so the check survives the annual bump without a code change.

## Changes Made

### Files Created
- `docs/feature-proposals/230-android-skills-validators.md`, `retrospectives/230-android-skills-validators.md`
- `plugins/sdlc-team-android/scripts/{__init__.py,android_preflight/{__init__,checks,cli}.py}` (+ `tests/test_android_preflight.py`)
- `skills/android-{scaffold,signing-setup,play-release,ci}/SKILL.md` (+ plugin copies)

### Files Modified
- `agents/core/play-store-release-specialist.md` (+ plugin copy) — Skills references
- `tests/conftest.py` — register `sdlc_team_android_scripts`
- `release-mapping.yaml` — skills + scripts under sdlc-team-android
- `plugins/sdlc-team-android/.claude-plugin/plugin.json` — 0.2.0 → 0.3.0 + description; `marketplace.json` synced
- `plugins/sdlc-team-android/README.md`, `CLAUDE.md`, `README.md` — skills/counts

### Validation
- `pytest tests/test_android_preflight.py` — 26 passed; `uvx ruff check` + `ruff format --check` clean
- `check-plugin-packaging.py` PASSED (19 plugins); `check-technical-debt .` COMPLIANT
- `check-feature-proposal.py` properly formatted; `check-broken-references.py` clean for new files

## Action Items

- [ ] EPIC #217 / sub-epic #225 **complete** — summarize the full mobile build-out for the maintainer.
- [ ] Optional fast-follow: `baseline-profile` / `target-sdk-migrate` Android skills; Kotlin lint/debt validators.

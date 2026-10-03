# Retrospective: sdlc-team-ios release skills + submission pre-flight checks

**Branch:** `feature/ios-skills-validators`
**Date:** 2026-07-23
**Duration:** ~1 session (EPIC #217 phase)

---

## Summary

Added a tested iOS **pre-flight checker** and four **release skills** to `sdlc-team-ios` (0.2.0 →
0.3.0), directly encoding real TestFlight/App Store failures a team reported (notably the ITMS-90683
CoreMotion / missing-motion-string rejection). The plugin now ships 4 agents + 4 skills + the checker.
Test-first; 28 pre-flight tests pass, ruff/format clean, packaging check passes.

## What Went Well

- **Real feedback → concrete, tested checks.** The team's incidents (missing purpose string, export
  compliance, build silently not processing, sandboxing gotcha) became a deterministic checker with
  unit tests and skills that sequence the workflow — not just prose.
- **Test-driven, per the repo rule.** Wrote `test_ios_preflight.py` alongside the module; 28 tests
  cover every check + the CLI heuristics, including the exact ITMS-90683 case.
- **Reused the established in-plugin script pattern** (sdlc-programme): `scripts/` package + conftest
  registration + release-mapping `scripts:` list, so packaging and tests "just worked".
- **Skills encode sequencing, not just facts** — internal-first-then-external, confirm-the-build-
  processed, the Beta App Review metadata checklist — the parts that trip up otherwise-simple apps.

## What Could Improve

- **ruff wasn't in the venv** (only `pip install -r requirements.txt` deps); used `uvx ruff`.
  - Two auto-fixes: `UP035` (`typing.Iterable`→`collections.abc`) and a format reflow. Caught before
    commit. Improvement: run `uvx ruff check/format` as a standard step for new Python in this repo.
- **Left a dead constant** (`ALWAYS_HUMAN_KEYS`) that ruff didn't flag (module-level) but was unused;
  removed it to honour zero-technical-debt. Improvement: self-review for unused module constants.
- **Scope was large for one PR** (checker + tests + 4 skills + agent update + wiring). Held it together
  by keeping the checker consolidated (one module, four functions) rather than five separate validators.

## Lessons Learned

1. **Turn war stories into gates.** The most valuable spec for a validator is a real rejection someone
   hit; the CoreMotion/ITMS-90683 incident became the flagship test case and the checker's headline rule.
2. **Skills own sequencing; checkers own config; agents own judgement.** The three layers compose: the
   agent explains *why*, the skill runs the *flow*, the checker gives a deterministic *gate*.
3. **Encode "confirm it worked."** The subtle failure (upload silently never becomes a build) is now an
   explicit skill step — a reminder that verification belongs in the workflow, not the developer's memory.

## Changes Made

### Files Created
- `docs/feature-proposals/221-ios-skills-validators.md`, `retrospectives/221-ios-skills-validators.md`
- `plugins/sdlc-team-ios/scripts/{__init__.py,ios_preflight/{__init__,checks,cli}.py}` (+ `tests/test_ios_preflight.py`)
- `skills/ios-{testflight-release,appstore-submit,signing-doctor,ci}/SKILL.md` (+ plugin copies)

### Files Modified
- `agents/core/ios-release-engineer.md` (+ plugin copy) — export compliance, confirm-build-processed, build-number-from-git, release-default safety, `ENABLE_USER_SCRIPT_SANDBOXING`, Skills references
- `tests/conftest.py` — register `sdlc_team_ios_scripts`
- `release-mapping.yaml` — skills + scripts under sdlc-team-ios
- `plugins/sdlc-team-ios/.claude-plugin/plugin.json` — 0.2.0 → 0.3.0 + description; `marketplace.json` synced
- `plugins/sdlc-team-ios/README.md`, `CLAUDE.md`, `README.md` — skills/counts

### Validation
- `pytest tests/test_ios_preflight.py` — 28 passed; `uvx ruff check` + `ruff format --check` clean
- `check-plugin-packaging.py` PASSED (17 plugins); `check-technical-debt.py --threshold 0` COMPLIANT
- `check-feature-proposal.py` properly formatted; `check-broken-references.py` clean for new files

## Action Items

- [ ] Next EPIC #217 phase: **Android platform agents** (kotlin-android, jetpack-compose, app-architect, gradle, play-store, performance) — separate PR
- [ ] Optional iOS follow-ups: `ios-scaffold` / `fastlane-setup` skills; accessibility lint; wire pre-flight into a plugin-level validate step
- [ ] EPIC #217 D2: Swift language expert placement

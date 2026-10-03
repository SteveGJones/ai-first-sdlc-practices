# Feature Proposal: sdlc-team-ios release skills + submission pre-flight checks

**Proposal Number:** 221
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/ios-skills-validators`
**GitHub Issue:** #221 (phase of EPIC #217)

---

## Motivation

`sdlc-team-ios` has the platform agents (#220) but no **operational tooling** for the part of iOS
work that most often goes wrong: getting a build onto TestFlight and through App Review. A team
sharing real experience listed the exact configuration mistakes that block uploads — most notably a
build that **silently never processed** because CoreMotion was used without an
`NSMotionUsageDescription` (ITMS-90683), plus export-compliance stalls, missing privacy manifests,
build-number collisions, and a build-phase-script sandboxing failure.

These are **statically checkable config problems** and **repeatable workflows** — exactly what skills
and a validator should own, so the failures are caught before an upload round-trip rather than after.
This proposal adds them to `sdlc-team-ios`, grounded in that team feedback plus the existing
release-engineering research.

## User Stories

- As an **iOS developer**, I want a pre-flight check that fails fast on a missing purpose string or
  export-compliance key so my TestFlight upload doesn't silently never become a build.
- As a **release owner**, I want a `ios-testflight-release` skill that sequences internal→external
  correctly and reminds me of the Beta App Review metadata, so external testing isn't blocked.
- As someone hitting a **signing failure**, I want a `ios-signing-doctor` that inspects what's actually
  signed and maps the symptom to the fix.
- As a team setting up **CI**, I want an `ios-ci` skill that gates on the pre-flight checks so config
  regressions fail CI, not App Store Connect.

## Proposed Solution

### High-Level Approach

Add a small **pre-flight checker** (Python, in-plugin per the sdlc-programme pattern) plus four
**skills** to `sdlc-team-ios`, and fold the team's lessons into the `ios-release-engineer` agent.
Agents advise; skills execute; the checker gives the skills a deterministic gate.

### Technical Approach

1. **`plugins/sdlc-team-ios/scripts/ios_preflight`** — pure check functions + a CLI:
   - `check_usage_descriptions` (framework→`NS…UsageDescription` map incl. CoreMotion; placeholder
     detection), `check_export_compliance` (`ITSAppUsesNonExemptEncryption`), `check_privacy_manifest`
     (required when required-reason APIs / SDKs present), `check_entitlements` (`get-task-allow`,
     `aps-environment`). CLI scans source for used frameworks / required-reason APIs / SDK markers.
   - Full pytest suite (`tests/test_ios_preflight.py`); registered via `tests/conftest.py`.
2. **Skills** (`skills/ios-*`, released to the plugin): `ios-testflight-release`, `ios-appstore-submit`,
   `ios-signing-doctor`, `ios-ci` — each encoding the corresponding lessons and invoking the checker.
3. **Agent update**: `ios-release-engineer` gains export-compliance, confirm-build-processed,
   build-number-from-git, release-default-safety, and the `ENABLE_USER_SCRIPT_SANDBOXING` gotcha, plus
   a Skills reference.
4. **Wiring**: `release-mapping.yaml` (skills + scripts under sdlc-team-ios), bump 0.2.0 → **0.3.0**
   (plugin.json + marketplace.json), plugin README + CLAUDE.md/README counts.

### Alternatives Considered

1. **Checks as agent prose only.** Rejected — a deterministic, tested checker catches config
   regressions in CI and doesn't depend on the model remembering the framework→key map.
2. **A standalone validator in `tools/validation/`.** Rejected — this is iOS-plugin-specific; the
   in-plugin `scripts/` pattern (as sdlc-programme uses) keeps it with the plugin that owns it.
3. **All six Fable skills + five validators at once.** Deferred — shipped the four highest-value skills
   and one consolidated checker; scaffold/fastlane-setup and an accessibility lint can follow.

---

## Implementation Plan

### Phase 1: Checker (test-first)
- [ ] Write `tests/test_ios_preflight.py`, then `ios_preflight/{checks,cli}.py`; register in conftest

### Phase 2: Skills + agent
- [ ] Author `ios-testflight-release`, `ios-appstore-submit`, `ios-signing-doctor`, `ios-ci`
- [ ] Update `ios-release-engineer` with the new lessons + skill references

### Phase 3: Wiring, validation & release
- [ ] `release-mapping.yaml` (skills + scripts); package skills into the plugin; bump 0.2.0 → 0.3.0
- [ ] Update marketplace, plugin README, CLAUDE.md/README
- [ ] ruff lint/format, packaging check, technical-debt, broken-references, full test suite; retrospective; PR

**Dependencies:** none new. Builds on #220 (agents exist).

---

## Success Criteria

```
Given an iOS project that uses CoreMotion but has no NSMotionUsageDescription
When ios_preflight.cli runs
Then it reports a missing-usage-description ERROR citing the ITMS-90683 class and exits non-zero
```

```
Given an Info.plist with no ITSAppUsesNonExemptEncryption
When ios_preflight.cli runs
Then it warns that every upload will stall on the export-compliance questionnaire
```

```
Given the pre-flight check module
When the test suite runs
Then all ios_preflight tests pass and ruff lint/format are clean
```

```
Given sdlc-team-ios after this change
When the plugin is packaged
Then it ships 4 agents + 4 skills + the ios_preflight scripts; version is 0.3.0; packaging check passes
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Framework→key map or reason codes go stale | Med | Low | Map covers the common cases; skills flag guideline/ITMS numbers as version-sensitive; easy to extend |
| Source-scan heuristics miss a framework (false negative) | Med | Low | Checker is a fast pre-filter, not a guarantee; skills also prompt manual review; findings are additive |
| Over-flagging (false positive) annoys users | Low | Low | Missing-key is ERROR only when the framework is detected; placeholder/export are WARNING/INFO |

## Open Questions

- [ ] Add `ios-scaffold` / `fastlane-setup` skills and an accessibility lint later? (Deferred.)
- [ ] Should the checker be wired into a plugin-level validate pipeline, or stay skill-invoked? (Skill-invoked for now.)

## Security & Privacy

N/A for data handling. The checker reads local project files read-only and emits findings; no network,
no secrets, no writes. The skills explicitly warn against committing secrets/keys into the bundle.

---

**Retrospective**: `retrospectives/221-ios-skills-validators.md` (link after implementation)

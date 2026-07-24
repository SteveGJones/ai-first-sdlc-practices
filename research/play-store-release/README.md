# Google Play Release & Distribution — Research Reference

Grounds the [`play-store-release-specialist`](../../agents/core/play-store-release-specialist.md) agent
(feature #226, sub-epic #225). Compiled 2026-07-23 from official Google properties. **Play policies
change frequently — every date, API level, size limit, and vitals threshold is version-sensitive;
re-verify against the live docs.**

| File | Covers |
|------|--------|
| [`01-play-store-release.md`](01-play-store-release.md) | Play App Signing (two-key), app bundles (`.aab`)/bundletool/dynamic delivery, tracks & staged rollout (halt/roll-forward), Data Safety, the annual target-API mandate, sensitive-permission declarations, pre-launch reports, in-app updates/review, Play Integrity, Play Billing, publishing automation (Play Developer API / Gradle Play Publisher / fastlane supply), versioning & vitals thresholds, rejection pitfalls |

**At a glance:** `.aab` mandatory; Play *can* halt + roll-forward (unlike iOS), versionCode is unique/monotonic; the gating gates are policy/console (Data Safety, target-API, sensitive permissions); vitals thresholds crash ≥1.09%/≥8%, ANR ≥0.47%/≥8% affect discoverability.

# iOS Release Engineering — Research Reference

Authoritative reference on **iOS release engineering, code signing, and App Store distribution**,
gathered to ground the [`ios-release-engineer`](../../agents/core/ios-release-engineer.md) agent
(feature #219, EPIC #217).

**Compiled:** 2026-07-23. Apple renames tooling and renumbers guidelines often — items in the source
file marked **[VERIFY]** (App Review guideline numbers, required-reason reason codes, ITMS codes,
ExportOptions `method` names, "build with SDK N" rule, TestFlight limits, download caps) must be
re-checked against developer.apple.com before being relied on as exact.

## Contents

| File | Covers |
|------|--------|
| [`01-ios-release-engineering.md`](01-ios-release-engineering.md) | Code signing & provisioning (the 4-part binding, cert/profile types, CI signing, failure diagnosis), capabilities→entitlements, the three privacy surfaces (nutrition labels / `PrivacyInfo.xcprivacy` / required-reason APIs) + ATT, App Store Connect & TestFlight, App Review guidelines, build/archive/export, fastlane / Xcode Cloud / ASC API, versioning & the no-rollback release strategy |

## Key facts at a glance

- **Store build invariants**: `get-task-allow` absent, `aps-environment=production`, distribution profile, Release config, no bitcode (removed).
- **Three privacy surfaces** all gate submission: nutrition labels (ASC), `PrivacyInfo.xcprivacy` (bundle; enforced since May 2024), required-reason API declarations; keep them consistent (tracking especially).
- **TestFlight**: internal 100 (no review), external 10,000 (beta review), builds expire 90 days.
- **Phased release**: 1/2/5/10/20/50/100% over 7 days, pausable, not adjustable.
- **Auth**: App Store Connect API key (`.p8` → ES256 JWT, no Apple-ID/2FA) preferred everywhere; `match` for shared team signing.
- **No rollback**: pause phased release / remove-from-sale / roll forward (expedited) / server-side kill switch — design for roll-forward.
- Common rejections: 2.1 completeness, 5.1.1(v) account deletion, 3.1.1 IAP, 4.2 min functionality, 4.8 login parity, 2.3 metadata.

---
name: ios-appstore-submit
description: Pre-submission audit for an App Store release — runs the pre-flight checks and walks the three privacy surfaces, the high-frequency App Review rejection guidelines, and metadata/release-option choices. Use before submitting an iOS app for App Review.
disable-model-invocation: false
argument-hint: "[path-to-ios-project]"
---

# iOS App Store Submit

A pre-submission audit that catches the issues most likely to get an App Store submission rejected,
before you hit "Submit for Review". Belongs to the **`ios-release-engineer`** discipline. Run it once
the build is on TestFlight and you're preparing the public release.

## Arguments

- `path-to-ios-project` — the project directory to check (defaults to the current directory).

## Steps

### 1. Run the pre-flight checks

```bash
python -m ios_preflight.cli <project-dir> [--uses-push]
```

Resolve every **ERROR** (missing usage descriptions, missing privacy manifest when required,
`get-task-allow` in release). Address **WARNING**s (export compliance, placeholder purpose strings)
too — they cause stalled uploads and review friction.

### 2. Clear the three privacy surfaces (all can block the submission)

- **App Privacy nutrition labels** (declared in App Store Connect) — data types collected, whether
  linked to identity, used for tracking, and purpose. **Must include data collected by third-party
  SDKs.** A new version can't ship with this incomplete.
- **Privacy manifest** (`PrivacyInfo.xcprivacy` in the bundle) — tracking flag, tracking domains,
  collected data types, and **required-reason API** declarations with approved reason codes. Enforced
  at upload.
- **Purpose strings + ATT** — every `NS…UsageDescription` present and human-readable; call ATT before
  touching the IDFA, and keep it consistent with the nutrition label / manifest tracking declaration.
- A **privacy policy URL** must be live and reachable.

### 3. Check the high-frequency rejection guidelines

*(Guideline numbers change — re-verify against the live App Review Guidelines.)*

- **2.1 Completeness** — no crashes on review, no placeholder content, no broken links; **provide a
  demo account** if there's a login.
- **2.3 Accurate metadata** — screenshots/description match the app; no misleading keywords.
- **3.1.1 In-App Purchase** — digital goods/content sold through IAP, not external payment.
- **4.2 Minimum functionality** — not a thin web-wrapper with no native value.
- **4.8 Login services** — if you offer social/third-party login, offer a privacy-preserving option
  (e.g. Sign in with Apple) where required; on account deletion, revoke SiwA tokens via the REST API.
- **5.1.1(v) Account deletion** — if the app supports account creation, it must offer **in-app account
  deletion** (delete, not just deactivate), easy to find.
- **5.1.1 / 5.1.2 Data** — request only data you need, with justification.

### 4. Metadata, versioning, and release option

- **Version vs build**: `CFBundleShortVersionString` is the marketing version (one App Store version
  per value); `CFBundleVersion` is the build (monotonic & unique).
- Fill metadata: name, subtitle, description, keywords, screenshots per required device size, support
  and marketing URLs, age rating, category, price/availability, and export-compliance answers.
- **Release option**: **Automatically on approval**, **Manually**, or **Scheduled**; consider a
  **phased release** (1/2/5/10/20/50/100% over 7 days, pausable) paired with crash monitoring.

### 5. Design for roll-forward (there is no rollback)

- You **cannot** roll back a live iOS version. Remedies are: pause phased release, remove-from-sale
  (doesn't help already-updated users), roll **forward** with an expedited fix, or a pre-built
  **server-side kill switch / feature flag**. Confirm risky changes are feature-flagged before you ship.

### 6. Report

Produce a pass/fail checklist across §2–§5. State clearly what's ready and what's outstanding; never
imply the submission is ready if a privacy surface or required guideline item is unresolved.

## Notes

- This is an audit, not a substitute for reading the current App Review Guidelines — treat specific
  numbers as version-sensitive.
- The three privacy surfaces are the most common stumbling block for otherwise-simple apps; give them
  the most attention.

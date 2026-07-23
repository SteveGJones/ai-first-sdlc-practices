---
name: ios-testflight-release
description: Prepare and ship an iOS build to TestFlight — runs the submission pre-flight checks, fixes the config that blocks uploads/processing, then walks internal→external beta review. Use when releasing an iOS build to testers.
disable-model-invocation: false
argument-hint: "[path-to-ios-project]"
---

# iOS TestFlight Release

Get an iOS build onto TestFlight without the classic upload/processing/beta-review blockers. This
skill encodes real incidents (e.g. a build silently never processed because of a missing
`NSMotionUsageDescription` — ITMS-90683) into a **pre-flight → upload → confirm → distribute** flow.

Belongs to the **`ios-release-engineer`** discipline. Run it before every TestFlight upload; the
config checks are cheap and the failures are expensive (a rejected/stalled upload costs a round-trip).

## Arguments

- `path-to-ios-project` — the project directory to check (defaults to the current directory).

## Steps

### 1. Run the pre-flight checks (config that blocks uploads)

Run the bundled checker from the plugin's scripts directory:

```bash
python -m ios_preflight.cli <project-dir> [--uses-push]
```

(Set `PYTHONPATH` to the plugin's `scripts/` dir, or run `python plugins/sdlc-team-ios/scripts/ -m
ios_preflight.cli` from a checkout.) It reports, and you must resolve every **ERROR** before uploading:

- **Missing usage descriptions** — every sensitive framework the app links/uses needs its
  `NS…UsageDescription` purpose string, or App Store Connect rejects the build **in processing**
  (ITMS-90683). The check maps frameworks to keys (CoreMotion→`NSMotionUsageDescription`,
  AVFoundation→`NSCameraUsageDescription`, CoreLocation→`NSLocationWhenInUseUsageDescription`,
  Contacts, Photos, Speech, HealthKit, …). **Rule of thumb: if a permission dialog could appear, the
  string must exist — and be a real human sentence** (Apple rejects placeholder text).
- **Export compliance** — set `ITSAppUsesNonExemptEncryption = false` in Info.plist if the app uses
  only exempt encryption (standard HTTPS). This skips the export-compliance questionnaire on **every**
  upload; without it each build stalls waiting for an answer in ASC.
- **Privacy manifest** — add a `PrivacyInfo.xcprivacy` if you use required-reason APIs (UserDefaults,
  file/disk timestamps, system boot time, disk space) or bundle third-party SDKs; Apple flags builds
  without it.
- **Entitlements** — no `get-task-allow` in a release build; `aps-environment = production` for push.

### 2. Verify release-default safety and versioning (not caught by the plist checks)

- **Build number**: every TestFlight upload needs a **unique, monotonically increasing**
  `CFBundleVersion`, or it's rejected. Adopt a policy and automate it — pre-1.0, keep
  `MARKETING_VERSION` fixed (e.g. `1.0.0`) and stamp `CFBundleVersion` from
  `git rev-list --count HEAD` (optionally plus the short SHA and date) so every tester build is
  **traceable to an exact commit**.
- **Release-default safety**: confirm debug menus, feature flags, verbose logging, staging endpoints,
  and experiment toggles **default OFF in Release** (gate them behind a build config or a flag that's
  off unless explicitly enabled). No secrets/API keys in the bundle — use xcconfig/build settings and
  confirm nothing sensitive is in the archived Info.plist.
- **Build-stamp script gotcha**: if a build-phase script reads git or the environment (e.g. to stamp
  the build number), that target may need `ENABLE_USER_SCRIPT_SANDBOXING = NO` (leave it `YES`
  elsewhere), or the archive fails.

### 3. Confirm signing & capabilities

- Bundle ID, team, and signing are set; **only capabilities you actually use** are enabled (a stray
  entitlement with no matching provisioning profile fails the archive). See `ios-signing-doctor` if
  the archive/signing fails.

### 4. Archive, upload, and **confirm the build actually processes**

- Archive with the Release configuration + distribution profile; upload via Xcode Organizer,
  Transporter, `xcrun altool`/`notarytool` path, the App Store Connect API, or fastlane `pilot`.
- **Do not assume the upload became a build.** Confirm the build appears and finishes processing in
  App Store Connect (TestFlight tab). A processing failure (e.g. a missing purpose string) can leave
  the upload silently never becoming a build — check, don't assume.

### 5. Distribute: internal first, then external + Beta App Review

- **Internal testing first** (up to 100 team members with an ASC role) — **no review**, available
  immediately after processing. This is the fastest first loop; shake out the obvious here.
- **External testing** (up to 10,000 testers) requires **Beta App Review** for the first build of a
  version. Before submitting externally, ensure:
  - **App Privacy** ("nutrition label") is filled in ASC (external review bounces without it),
  - a **privacy policy URL** is live (a public Gist is fine for a simple app),
  - **Beta App Review info**: App Review contact (name/email/phone), a **demo/test account** if there
    is any login, and clear **"What to Test"** notes,
  - a stable way for testers to reach you (feedback email or TestFlight's built-in feedback).
- Builds **expire 90 days** after upload.

### 6. Report

Summarise: pre-flight result (errors fixed), build number + the commit it maps to, whether the build
processed, and which testing track it went to. If anything is unresolved (e.g. App Privacy not yet
filled), say so explicitly rather than implying the external release is ready.

## Notes

- Apple renames tooling and renumbers guidelines often — treat exact ITMS/guideline numbers as
  version-sensitive and re-verify against developer.apple.com if a message doesn't match.
- Internal vs external is the key sequencing lever: internal is instant (no review); external needs the
  metadata above. Get internal working first.

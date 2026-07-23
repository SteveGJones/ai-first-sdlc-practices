---
name: ios-signing-doctor
description: Diagnose and fix iOS code-signing, provisioning, and entitlement failures — the "no signing certificate / no profiles / doesn't match / get-task-allow" family, using codesign/security to inspect what's actually signed. Use when an archive, upload, or CI build fails on signing.
disable-model-invocation: false
argument-hint: "[error-message-or-log-path]"
---

# iOS Signing Doctor

Diagnose the code-signing / provisioning failure family — the single most common iOS release blocker —
and fix it, rather than guessing. Belongs to the **`ios-release-engineer`** discipline.

## Arguments

- `error-message-or-log-path` — paste the signing error or point at the build log (optional).

## The mental model (why signing fails)

A build installs/runs only if four things agree: **signing certificate** (identity; private key in
Keychain, `.p12` = cert+key) + **App ID** (bundle ID + capabilities) + **provisioning profile** (ties
cert + App ID + devices + entitlements, Apple-signed) + **entitlements** (must be a subset the App
ID/profile authorize). Most failures are a mismatch among these.

## Steps

### 1. Inspect what is actually signed (don't guess)

```bash
security find-identity -v -p codesigning          # usable signing identities
security cms -D -i embedded.mobileprovision        # dump the profile plist
codesign -dv --entitlements :- MyApp.app           # embedded entitlements (incl. get-task-allow, aps-environment)
codesign --verify --deep --strict MyApp.app        # verify the signature
```

### 2. Match the symptom to the cause

| Symptom / error | Likely cause | Fix |
|-----------------|--------------|-----|
| "No signing certificate 'Apple Distribution' found" | Cert/private key not in keychain, or wrong team | Import the `.p12`; verify with `security find-identity` |
| "No profiles for 'com.acme.MyApp' were found" | No profile for that bundle ID + cert | Regenerate the profile (or `fastlane match`); check the exact bundle ID |
| "Provisioning profile doesn't include signing certificate" | Profile built against a different cert | Regenerate the profile with the current cert |
| "doesn't support the … capability" / "entitlements don't match" | Entitlement in the binary not enabled on the App ID / not in the profile | Enable the capability on the App ID, regenerate the profile — or remove the **stray entitlement** you don't actually use |
| "Provisioning profile has expired" | Dev/Ad Hoc profile past expiry | Regenerate |
| `errSecInternalComponent` on CI codesign | Keychain locked / partition list not set | `security set-key-partition-list -S apple-tool:,apple: -s -k <pw> <keychain>` |
| Upload rejected: "Invalid Provisioning Profile … get-task-allow" | Debug entitlement in a store build | Archive with **Release** config + **distribution** profile (see below) |
| Bundle ID mismatch | Info.plist `CFBundleIdentifier` ≠ App ID | Align exactly (case-sensitive) |

### 3. Common root fixes

- **`get-task-allow=true` in a store build** (the #1 upload rejection): it's set implicitly by the
  **profile type** — archive with the Release configuration and an **App Store distribution profile**,
  not a development profile. Verify it's gone with the `codesign -dv --entitlements` command.
- **Only enable capabilities you use**: a stray capability (Push, iCloud, App Groups, Background
  Modes) adds an entitlement that needs matching App ID/profile support, or the archive fails. Remove
  what you don't use.
- **Push works in debug but not TestFlight**: `aps-environment` must be `production` for App Store /
  TestFlight builds (they always use production APNs).
- **CI**: prefer **manual signing** (or `fastlane match --readonly`) for reproducibility; set up a
  temporary keychain, import the `.p12`, run `set-key-partition-list`, install the profile. Auth to
  Apple via an **App Store Connect API key** (`.p8`), not Apple-ID/password.
- **Build-script sandboxing**: a build-phase script that reads git/the environment may need
  `ENABLE_USER_SCRIPT_SANDBOXING = NO` on that target (leave `YES` elsewhere), or the archive fails.

### 4. Report

State the identified cause, the exact fix applied, and the verification command output proving it's
resolved (e.g. `get-task-allow` now absent). Re-run the archive/upload to confirm.

## Notes

- Automatic signing is fine for solo/local work but non-deterministic for teams/CI — prefer manual or
  `match` there.
- For a full pre-submission audit (privacy surfaces, guidelines), use `ios-appstore-submit`; for the
  TestFlight flow, `ios-testflight-release`.

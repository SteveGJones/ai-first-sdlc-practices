# iOS Release Engineering, Code Signing & App Store Distribution

Reference knowledge base for the `ios-release-engineer` specialist agent.
Current as of mid-2026 (Xcode 16 era, iOS 18/26 SDK). Apple changes tooling
and guideline numbering frequently — items flagged **[VERIFY]** are
version-sensitive and should be re-checked against `developer.apple.com`
before being treated as authoritative.

> Terminology note: Apple renamed its OS versioning in 2025 to year-based
> numbers (iOS 26 = the 2025/2026 release). "iOS 18" and "iOS 26" both appear
> in current docs depending on age. The signing/distribution mechanics below
> are stable across that rename.

---

## 1. Code Signing & Provisioning

### The mental model

iOS code signing binds four things together. A build only installs/runs if all
four agree:

1. **Signing certificate** (identity) — proves *who* built it. Backed by a
   public/private keypair; the private key lives in your Keychain, the public
   half is in the cert Apple issues.
2. **App ID** (in the Developer portal) — the bundle identifier
   (`com.acme.MyApp`) plus the set of **capabilities** enabled for it.
3. **Provisioning profile** — the glue file that ties *this certificate* +
   *this App ID* + (for non-store builds) *these devices* + *these
   entitlements* together, signed by Apple.
4. **Entitlements** — the specific permissions compiled into the binary's code
   signature; must be a subset of what the App ID/profile authorize.

### Certificates: Development vs Distribution

| Type | Purpose | Portal name |
|------|---------|-------------|
| **Apple Development** | Run/debug on registered devices | "Apple Development" (unified iOS/macOS since ~2019; older "iOS Development") |
| **Apple Distribution** | Sign builds for App Store, Ad Hoc, Enterprise | "Apple Distribution" (older "iOS Distribution / Production") |
| **Developer ID** | macOS notarized distribution outside the App Store | (macOS only — not iOS) |

- Certificates are per-**team**, tied to a private key. If you lose the private
  key you cannot re-download a usable cert — you must revoke and reissue.
- Free (personal) Apple IDs get only development signing, 7-day profile expiry,
  and no distribution.
- A **`.p12`** file = certificate + private key exported together (password
  protected). This is the portable artifact you feed to CI. Export it from
  Keychain Access; it's what fastlane `match` stores encrypted.
- Certs expire (Development ~1 year, Distribution ~1 year). Expired cert →
  builds still validate if already signed, but new signing fails.

### App IDs

- **Explicit App ID** — exact bundle ID (`com.acme.MyApp`). Required for most
  capabilities (Push, App Groups, iCloud, etc.).
- **Wildcard App ID** — `com.acme.*`. Cannot use capabilities that require a
  registered App ID (Push, associated domains…). Fine for simple apps.
- The App ID's capability set must be a superset of what your entitlements
  request, or signing/validation fails.

### Provisioning profiles (`.mobileprovision` / `.provisionprofile`)

| Profile type | Signs with | Installs on | Use |
|--------------|-----------|-------------|-----|
| **Development** | Apple Development cert | Explicitly registered UDIDs | Debug on device |
| **Ad Hoc** | Apple Distribution cert | Up to **100 registered devices** per device type per membership year | Beta/QA outside TestFlight |
| **App Store** | Apple Distribution cert | No device list — Apple installs | App Store & TestFlight |
| **Enterprise (In-House)** | Enterprise Distribution cert (Apple Developer **Enterprise** Program, separate ~$299/yr) | Any device, no UDID list | Internal-only distribution; MUST NOT be used for public/App Store apps |

- Profiles embed: allowed certs, the App ID + entitlements, device list (dev/ad
  hoc), expiry (dev/ad hoc typically 1 year; the profile itself, not the cert).
- The profile is embedded in the `.ipa` as `embedded.mobileprovision`.
- Device UDID limit for dev/ad hoc is **100 per device class** (iPhone, iPad,
  Mac, Apple Watch, Apple TV, Vision) per membership year; devices can only be
  *removed* (resetting the count) once per year at renewal.

### Xcode "Automatically manage signing" vs manual

- **Automatic** — Xcode creates/updates a matching development profile and
  managed distribution profile ("Xcode Managed Profile"), registers the device,
  and picks certs. Great for solo/local; unreliable and non-deterministic for
  CI and teams (races on cert creation, can hit the 3-cert limit, opaque).
- **Manual** — you select an explicit provisioning profile + signing identity
  per configuration. Deterministic; required for reproducible CI. This is what
  `fastlane match` + `gym` use.
- **Cloud managed distribution certificate** — Xcode/Xcode Cloud can use an
  Apple-managed distribution cert whose private key you never see. Simplifies
  Xcode Cloud but is not exportable for other CI.

### How signing works in CI

The core problem: CI machines have no Keychain, no certs, no profiles. Standard
recipe:

1. Import the `.p12` into a **temporary keychain** you create and unlock
   (`security create-keychain`, `security import`, `security set-key-partition-list`
   to avoid the `codesign` UI password prompt — the classic CI gotcha).
2. Install the `.mobileprovision` into
   `~/Library/MobileDevice/Provisioning Profiles/`.
3. Build/archive with **manual signing**, passing
   `CODE_SIGN_IDENTITY`, `PROVISIONING_PROFILE_SPECIFIER`,
   `DEVELOPMENT_TEAM`, `CODE_SIGN_STYLE=Manual`.
4. Store secrets (base64-encoded `.p12`, profile, keychain password) in CI
   secret storage — never in the repo.

`fastlane match` automates steps 1–2 by keeping encrypted certs/profiles in a
shared git repo / S3 / Google Cloud bucket. Xcode Cloud handles it internally
via App Store Connect.

### Common signing failures & diagnosis

| Symptom / error | Likely cause | Fix |
|-----------------|--------------|-----|
| "No signing certificate 'Apple Distribution' found" | Cert/private key not in keychain, or wrong team | Import `.p12`; check `security find-identity -p codesigning -v` |
| "No profiles for 'com.acme.MyApp' were found" | No profile for that bundle ID / cert combo | Regenerate profile, or `match`; check exact bundle ID |
| "Provisioning profile doesn't include signing certificate" | Profile built against a different cert | Regenerate profile with current cert |
| "doesn't support the … capability" / "entitlements … don't match" | Entitlement in binary not enabled on App ID / not in profile | Enable capability on App ID, regenerate profile |
| "Provisioning profile … has expired" | Dev/Ad Hoc profile past expiry | Regenerate |
| `errSecInternalComponent` on CI codesign | Keychain locked / partition list not set | `security set-key-partition-list -S apple-tool:,apple: -s -k <pw> <keychain>` |
| Upload rejected: "Invalid Provisioning Profile … get-task-allow" | Debug entitlement in a store build | Archive with Release config / distribution profile (see §2) |
| Bundle ID mismatch | Info.plist `CFBundleIdentifier` ≠ App ID | Align exactly (case-sensitive) |

Diagnostic commands:
```bash
security cms -D -i embedded.mobileprovision        # dump profile plist
codesign -dv --entitlements :- MyApp.app           # show embedded entitlements
codesign --verify --deep --strict MyApp.app        # verify signature
security find-identity -v -p codesigning           # list usable signing identities
```

---

## 2. Capabilities & Entitlements

**Capability** (a feature you enable in Xcode / on the App ID) →
**entitlement(s)** (keys compiled into the signature via the `.entitlements`
file) → must be authorized by the **provisioning profile / App ID**.

| Capability | Key entitlement(s) | Notes |
|------------|--------------------|-------|
| Push Notifications | `aps-environment` (`development` / `production`) | Value must be `production` for App Store/TestFlight builds. Requires explicit App ID + APNs key/cert. |
| App Groups | `com.apple.security.application-groups` | Shared container for app + extensions; `group.com.acme.*`. |
| Sign in with Apple | `com.apple.developer.applesignin` | Mandatory if you offer third-party social login only (Guideline 4.8 caveats). |
| iCloud (CloudKit/KV/Docs) | `com.apple.developer.icloud-container-identifiers`, `com.apple.developer.icloud-services`, `com.apple.developer.ubiquity-*` | Container IDs registered on App ID. |
| Associated Domains | `com.apple.developer.associated-domains` | For Universal Links, web credentials (autofill), App Clips. Needs `apple-app-site-association` file on the domain. |
| Keychain Sharing | `keychain-access-groups` | Share keychain items across your apps. |
| Data Protection | `com.apple.developer.default-data-protection` | File encryption class. |
| Background Modes | (Info.plist `UIBackgroundModes`, not an entitlement) | e.g. `remote-notification`, `audio`. |

### `aps-environment`
- `development` = APNs sandbox; `production` = APNs prod.
- App Store / TestFlight builds are always treated as **production** APNs
  regardless — a dev-signed build talks to sandbox. Mismatch is the #1 cause of
  "push works in debug, not in TestFlight."

### `get-task-allow` — the critical release entitlement
- `get-task-allow` (a.k.a. "allow debugging") lets a debugger attach to the
  process. It is **`true`** in Development-signed builds, and **must be `false`
  / absent** in any Distribution (App Store, Ad Hoc, Enterprise) build.
- It is set implicitly by the **provisioning profile type**, not usually by hand
  — sign with a distribution profile and it's stripped/false; sign with a dev
  profile and it's true.
- App Store upload validation **rejects** an archive that has
  `get-task-allow=true`. Symptom: "Invalid Provisioning Profile. The provisioning
  profile … doesn't match" / "ITMS-90xxx … beta entitlement." Root cause is
  almost always archiving with a Development configuration/profile.

### App Transport Security (ATS)
- ATS forces HTTPS with TLS 1.2+ and forward secrecy by default.
- Exceptions declared in Info.plist under `NSAppTransportSecurity`
  (`NSAllowsArbitraryLoads`, per-domain `NSExceptionDomains`).
- Broad exceptions (`NSAllowsArbitraryLoads=true`) can draw App Review scrutiny
  and may require justification. Keep exceptions minimal and per-domain.

---

## 3. Privacy at Submission

Three distinct, often-confused mechanisms. All can block a submission.

### 3a. Privacy Nutrition Labels ("App Privacy" in App Store Connect)
- Declared **in App Store Connect** (not in the binary), under **App Privacy**.
- You declare **data types collected** (Contact Info, Health, Location,
  Identifiers, Usage Data, etc.), whether each is **linked to identity**, used
  for **tracking**, and the **purpose**.
- Displayed on the App Store product page as the privacy "nutrition label."
- Must cover data collected by your code **and by third-party SDKs** you embed.
- Editable independently of a binary submission but a new version can't ship
  with the label incomplete.

### 3b. Privacy Manifest — `PrivacyInfo.xcprivacy` (in the bundle)
- A property list (`PrivacyInfo.xcprivacy`) shipped **inside the app / SDK
  bundle**. Introduced 2023; **enforced at upload since May 1, 2024**. **[VERIFY]**
- Four top-level keys:
  - `NSPrivacyTracking` (Bool) — does this app/SDK track per ATT?
  - `NSPrivacyTrackingDomains` (Array<String>) — domains used for tracking; if
    ATT permission not granted, connections to these are blocked at runtime.
  - `NSPrivacyCollectedDataTypes` (Array<Dict>) — machine-readable mirror of the
    nutrition-label data (type, linked, tracking, purposes).
  - `NSPrivacyAccessedAPITypes` (Array<Dict>) — **required-reason API**
    declarations.
- Xcode aggregates the app manifest + all embedded SDK manifests into a single
  **privacy report** ("App Privacy Report" export from the archive Organizer).

### Required-Reason APIs
Certain APIs that had been abused for fingerprinting now require a declared
approved reason code. The five categories and their keys: **[VERIFY reason codes]**

| Category | `NSPrivacyAccessedAPIType` value | Example approved reason(s) |
|----------|----------------------------------|-----------------------------|
| File timestamp | `NSPrivacyAccessedAPICategoryFileTimestamp` | `C617.1`, `DDA9.1`, `3B52.1`, `0A2A.1` |
| System boot time | `NSPrivacyAccessedAPICategorySystemBootTime` | `35F9.1`, `8FFB.1`, `3D61.1` |
| Disk space | `NSPrivacyAccessedAPICategoryDiskSpace` | `E174.1`, `85F4.1`, `7D9E.1`, `B728.1` |
| Active keyboard | `NSPrivacyAccessedAPICategoryActiveKeyboard` | `3EC4.1`, `54BD.1` |
| User defaults | `NSPrivacyAccessedAPICategoryUserDefaults` | `CA92.1`, `1C8F.1`, `C56D.1`, `AC6B.1` |

Declaration shape:
```xml
<key>NSPrivacyAccessedAPITypes</key>
<array>
  <dict>
    <key>NSPrivacyAccessedAPIType</key>
    <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
    <key>NSPrivacyAccessedAPITypeReasons</key>
    <array><string>CA92.1</string></array>
  </dict>
</array>
```
- Missing/incorrect reasons → Apple emails a warning at upload and, since the
  enforcement date, **rejects** the submission (ITMS-91053 "Missing API
  declaration" family of messages). **[VERIFY exact ITMS codes]**

### 3c. Third-party SDK privacy manifests + signatures
- Apple publishes a list of **"commonly used" SDKs** (e.g. many analytics/ad
  SDKs) that must ship a privacy manifest **and be code-signed** when included.
  **[VERIFY the current SDK list]**
- If a listed SDK lacks a manifest/signature, your app's upload can be rejected.
  Update to a compliant SDK version.

### 3d. Purpose strings (`NS…UsageDescription`)
- Any access to protected resources needs a human-readable purpose string in
  Info.plist, or the app **crashes on first access** (and Review rejects apps
  that request access without a meaningful reason). Common:
  `NSCameraUsageDescription`, `NSPhotoLibraryUsageDescription`,
  `NSLocationWhenInUseUsageDescription`, `NSMicrophoneUsageDescription`,
  `NSContactsUsageDescription`, `NSUserTrackingUsageDescription`.

### 3e. App Tracking Transparency (ATT)
- If you "track" (link user/device data with third-party data for ads, or share
  with data brokers), you must call `ATTrackingManager.requestTrackingAuthorization`
  and show the system prompt **before** accessing the IDFA
  (`ASIdentifierManager`). Requires `NSUserTrackingUsageDescription`.
- Must be consistent with the nutrition label (`Used to Track You`) and privacy
  manifest (`NSPrivacyTracking=true` + tracking domains). Inconsistency is a
  common rejection.

---

## 4. App Store Connect & Submission

### App records, versions, builds
- **App record** — one per app, keyed by bundle ID + Apple ID (numeric ASC ID),
  plus an SKU.
- **Version** (`CFBundleShortVersionString`, e.g. `2.3.0`) — the
  marketing/user-facing version; one App Store version record per value.
- **Build** (`CFBundleVersion`, e.g. `2.3.0.147` or `147`) — an uploaded binary.
  Many builds can attach to one version; the version you submit points at one
  build. Build numbers must be **unique and monotonically increasing** within a
  version train, or upload is rejected ("bundle version … already exists").

### Uploading builds (2025/2026 tooling)
Supported paths: **Xcode Organizer**, **Transporter** app, **App Store Connect
API** (`POST` build upload / Transporter under the hood), **`altool`** (legacy,
still works for App Store uploads though deprecated for macOS notarization since
Nov 2023), and **Xcode Cloud**. After upload the build is **processed**
server-side (minutes to hours); you get an email when it's ready to distribute.
- **[VERIFY]** Apps must currently be **built with the latest-1 Xcode / SDK**
  (as of 2025 Apple required the iOS 18 SDK / Xcode 16 for new submissions).
  This "must build with SDK N" requirement rolls forward each year — always
  re-check.

### TestFlight
| | Internal | External |
|--|----------|----------|
| Who | Up to **100** users with an ASC role on the team | Up to **10,000** testers (email or public link) |
| Review | **None** — build available immediately after processing | **Beta App Review** required for the first build of each version (lighter than App Review) |
| Groups | Internal groups | External groups; public invite links |
| Build life | Expires **90 days** after upload | Expires **90 days** after upload |

- Builds using certain features (e.g. push, new entitlements) still function in
  TestFlight with production APNs.
- TestFlight testers must accept an invite and install the TestFlight app.
- You can attach test notes and enable automatic distribution to a group.

### Submission flow (App Store)
1. Create/select the version record; fill metadata (name, subtitle, description,
   keywords, screenshots per device size, support/marketing URLs, age rating,
   category, price/availability), App Privacy, and export-compliance answers.
2. Select the processed build.
3. Choose release option: **Automatically on approval**, **Manually**, or
   **Scheduled** for a date.
4. Submit for Review. States: *Waiting for Review → In Review → Pending
   Developer Release / Ready for Distribution* (or *Rejected*).

### Phased Release
- Optional 7-day staged rollout to users with **automatic updates** on, at fixed
  daily percentages: **1% → 2% → 5% → 10% → 20% → 50% → 100%** (days 1–7).
- You **cannot** change the percentages. You **can pause** at any time (paused up
  to 30 days), and you can **release to 100% immediately** to end it early.
- Anyone can still manually download the latest version from the store during a
  phased release — it only throttles auto-updaters.
- Applies to updates only (not brand-new apps' first release in the same sense).

### Expedited Review
- Request via the Contact-Us form for critical bug fixes / time-sensitive
  events. Granted at Apple's discretion; overusing it burns goodwill.

### Guidelines that commonly cause rejection **[VERIFY numbers — Apple renumbers]**
| Guideline | Topic | Typical trigger |
|-----------|-------|-----------------|
| **2.1** | App Completeness | Crashes on launch/review, placeholder content, broken links, demo account not provided |
| **2.3.x** | Accurate Metadata | Screenshots/description don't match app; misleading keywords |
| **3.1.1** | In-App Purchase | Selling digital goods/content with anything other than IAP; external purchase links |
| **4.2** | Minimum Functionality | Thin app / web-wrapper with no native value |
| **4.8** | Login Services | Offering third-party social login without an equivalent privacy-preserving option (e.g. Sign in with Apple) where required |
| **5.1.1(v)** | Account Deletion | App supports account creation but offers no in-app account **deletion** (must delete, not just deactivate; enforced since June 30, 2022). If using Sign in with Apple, revoke tokens via the SiwA REST API on deletion. |
| **5.1.1 / 5.1.2** | Data Collection & Storage | Requesting data not needed; permission without justification |

Also frequently hit: **3.2** (business/unacceptable), **1.x** (safety / UGC
moderation & reporting), **2.5.x** (software requirements / private API use).

### Handling rejections & appeals
- Rejection arrives in **Resolution Center** with the cited guideline and often
  screenshots. Reply there for clarification, or upload a fixed build.
- **Appeal** to the App Review Board if you believe the rejection is wrong
  (separate from resubmitting a fix).
- Metadata-only rejections can sometimes be fixed without a new build.
- Repeated similar rejections / manipulative behavior can escalate to account
  warnings.

---

## 5. Build & Archive

### Schemes & configurations
- **Configurations** (Debug/Release, plus custom like Staging) drive build
  settings, `.xcconfig`, and which entitlements/signing apply.
- **Schemes** map actions (Run/Test/Archive) to configurations. **Archive**
  should use a Release configuration with the distribution profile.

### Archive & export (command line)
```bash
xcodebuild -workspace MyApp.xcworkspace -scheme MyApp \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath build/MyApp.xcarchive archive

xcodebuild -exportArchive -archivePath build/MyApp.xcarchive \
  -exportPath build/export -exportOptionsPlist ExportOptions.plist
```

### ExportOptions.plist (key fields)
- `method` — `app-store-connect` (older `app-store`), `release-testing`
  (Ad Hoc), `enterprise`, `debugging` (development). **[VERIFY]** method names
  were revised in Xcode 15/16 (`app-store` → `app-store-connect`, `ad-hoc` →
  `release-testing`, `development` → `debugging`).
- `teamID`, `signingStyle` (`manual`/`automatic`),
  `provisioningProfiles` (bundleID → profile name map for manual),
  `signingCertificate`, `uploadSymbols`, `stripSwiftSymbols`,
  `uploadBitcode` (obsolete — see below), `manageAppVersionAndBuildNumber`.

### `.ipa` generation
- `-exportArchive` produces the `.ipa` (a zip of `Payload/MyApp.app` +
  `embedded.mobileprovision` + resources). This is the artifact you upload.

### Bitcode — removed
- **Bitcode is deprecated and removed.** Xcode 14+ no longer produces bitcode;
  App Store Connect **stopped accepting** bitcode submissions. `ENABLE_BITCODE`
  should be `NO`; `uploadBitcode` in ExportOptions is a no-op. Don't design
  around bitcode-based recompilation anymore.

### App Thinning & on-demand resources (distribution level)
- App Store performs **App Thinning**: slicing (device-specific assets/arch),
  **bitcode** (gone), and **on-demand resources (ODR)**. Users download only the
  variant for their device.
- **On-Demand Resources** — tagged asset bundles fetched at runtime, hosted by
  Apple, keeping initial download small.
- **[VERIFY]** Newer **Apple-hosted background asset packs / "asset packs"**
  (Background Assets framework, expanded 2024–2025) are the modern large-asset
  delivery path — re-check current naming/limits.
- Over-the-cellular download size limits exist (historically ~200 MB, raised
  over time) — **[VERIFY current cap]**.

### Versioning fields
- `CFBundleShortVersionString` — marketing version (`MAJOR.MINOR.PATCH`),
  visible to users, one App Store version per value.
- `CFBundleVersion` — build number, must increase per upload within a version.
- Common CI pattern: set build number from CI run number or a timestamp so it's
  always monotonic and unique.

---

## 6. Automation

### fastlane (Ruby toolchain)
| Tool | Job |
|------|-----|
| `gym` (`build_app`) | Wrap `xcodebuild archive`/`-exportArchive` → `.ipa` |
| `match` | **Shared team code signing**: stores certs + profiles encrypted in a git repo / S3 / GCS; every machine + CI runs `match` to fetch the *same* identities. Solves "everyone generating their own certs." Modes: `development`, `adhoc`, `appstore`, `enterprise`. Read-only mode on CI (`--readonly`) so CI never creates new certs. |
| `sigh` | Create/download/repair individual provisioning profiles (pre-`match` approach) |
| `cert` | Create/download signing certs |
| `pilot` (`upload_to_testflight`) | Upload build to TestFlight, manage testers/groups |
| `deliver` (`upload_to_app_store`) | Upload binary + metadata + screenshots; submit for review |
| `produce` (`create_app_online`) | Create the app record + bundle ID in ASC/portal |
| `snapshot` / `frameit` | Automated localized screenshots |
| `scan` | Run tests |

- `match` + `gym` + `pilot`/`deliver` is the canonical open-source pipeline.
- fastlane authenticates to ASC via the **App Store Connect API key** (preferred,
  2FA-proof) rather than Apple-ID + password/session.

### Xcode Cloud
- Apple's first-party CI/CD, integrated into Xcode and ASC.
- **Workflows** trigger on branch/PR/tag/schedule; run **actions** (build, test,
  analyze, archive) in Apple-managed macOS environments, then **post-actions**
  (notarize/deliver to TestFlight or App Store).
- Handles signing internally with a cloud-managed distribution certificate — no
  `.p12` juggling.
- **Environments** define Xcode version, macOS version, and env vars/secrets.
- Pricing is by compute-hours (a monthly allowance + paid tiers). **[VERIFY]**
- Good default when you're all-in on Apple tooling; less flexible than
  fastlane+GH Actions for cross-platform or custom steps.

### App Store Connect API
- REST API authenticated with **API keys** (issuer ID + key ID + `.p8` private
  key) → you mint a short-lived **JWT (ES256)** per request. No Apple-ID/2FA.
- Key roles: **Admin**, **App Manager**, **Developer**, etc. — scope the key.
- Automates: TestFlight (builds, testers, groups, beta review), app metadata,
  versions, phased release control, provisioning (certs/profiles/devices),
  sales/finance reports, and build upload.
- **`notarytool`** (Xcode 14+) replaced **`altool`** for **macOS notarization**
  (altool notarization stopped being accepted Nov 1, 2023). For **iOS App Store
  uploads**, `altool --upload-app` still works but Transporter / ASC API /
  Xcode are the forward path. `notarytool` is macOS-only — iOS apps aren't
  notarized.
- `xcrun altool --upload-app -f MyApp.ipa -t ios --apiKey KEY --apiIssuer ISS`.

### CI signing setup (GitHub Actions / generic)
1. Base64-encode the `.p12` and `.mobileprovision`; store as encrypted secrets,
   plus keychain and `.p12` passwords, and the ASC API `.p8`/key IDs.
2. On the runner: create + unlock a temp keychain, import the `.p12`, set the
   partition list, install the profile.
3. Build with manual signing (or `match --readonly`).
4. Upload via `pilot`/`deliver`/`altool`/ASC API using the API key.
- Never commit certs/keys; rotate on team-member departure; scope API keys
  minimally.

---

## 7. Versioning & Release Strategy

### Version & build numbers
- User-facing **SemVer-ish** `CFBundleShortVersionString` (MAJOR.MINOR.PATCH).
  MAJOR = breaking UX/redesign, MINOR = features, PATCH = fixes — convention,
  not enforced by Apple.
- **Build number strategy**: monotonic and unique per version train. Common:
  CI build counter, `git rev-list --count HEAD`, or `YYYYMMDDHHMM`. Keep it
  independent of marketing version so hotfix rebuilds don't force a version bump.

### Staged rollout
- Use **Phased Release** (§4) to catch regressions on a small % before full
  exposure. Pair with crash monitoring (Crashlytics/MetricKit/Xcode Organizer
  crash reports) so you can **pause** if crash rate spikes.

### Release notes
- Per-version "What's New" text, localizable. Required-ish for updates; keep
  meaningful (Review dislikes "bug fixes" only for major versions but tolerates
  it generally).

### Rollback — the hard constraint
- **You cannot roll back a live iOS App Store version.** Once a build is
  released, you can't revert users to the previous binary. Options are:
  1. **Pause phased release** (limits blast radius, doesn't help users already
     updated).
  2. **Remove the version from sale** (stops *new* downloads/updates; existing
     users keep the bad build).
  3. Ship a **new higher version** with the fix ASAP (optionally **expedited
     review**). This is the real "rollback" — roll *forward*.
  4. For truly severe regressions, use a **server-side kill switch / feature
     flag** you built in advance — the only way to disable bad behavior instantly
     without an App Store round-trip.
- Implication for the agent: **design for roll-forward** — feature-flag risky
  changes, keep build/release cadence fast, and never treat a release as
  reversible.

---

## Quick-Reference Cheat Sheet

- Store build must have `get-task-allow=false`, `aps-environment=production`,
  distribution profile, Release config, no bitcode.
- Three privacy surfaces: **nutrition label** (ASC) + **privacy manifest**
  (`PrivacyInfo.xcprivacy` in bundle) + **required-reason API** declarations.
- Build number monotonic & unique; marketing version is separate.
- TestFlight: internal 100 (no review), external 10,000 (beta review), builds
  expire 90 days.
- Phased release: 1/2/5/10/20/50/100% over 7 days, pausable, not reversible.
- CI signing = temp keychain + `.p12` + profile + manual signing, or `match`.
- Auth to Apple services via **App Store Connect API key** (`.p8` → ES256 JWT).
- No rollback — roll forward + server kill switches.

---

## Sources

Official Apple (primary):
- App Store Review Guidelines — https://developer.apple.com/app-store/review/guidelines/
- Account deletion requirement (5.1.1(v)) — https://developer.apple.com/news/?id=12m75xbj
- Privacy manifest files — https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
- Adding a privacy manifest to your app or third-party SDK — https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk
- Describing use of required-reason API — https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api
- Privacy updates for App Store submissions (enforcement) — https://developer.apple.com/news/?id=3d8a9yyh
- Upload builds to App Store Connect — https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- Release a version in phases — https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases
- App Store Connect API — https://developer.apple.com/documentation/appstoreconnectapi
- Apple notary service update (altool→notarytool) — https://developer.apple.com/news/?id=y5mjxqmn

Secondary / community (context & corroboration — verify against Apple):
- Bitrise: Enforcement of Apple Privacy Manifest (May 1, 2024) — https://bitrise.io/blog/post/enforcement-of-apple-privacy-manifest-starting-from-may-1-2024
- fastlane discussion: altool deprecation (TN3147) — https://github.com/fastlane/fastlane/discussions/21347
- NextNative: App Store Review Guidelines 2025 checklist — https://nextnative.dev/blog/app-store-review-guidelines
- RevenueCat: ultimate guide to App Store rejections — https://www.revenuecat.com/blog/growth/the-ultimate-guide-to-app-store-rejections
- Gabrielle Earnshaw: phased releases on ASC — https://www.gabrielle-earnshaw.com/posts/phased-releases-for-ios-apps-on-app-store-connect/
- TechConcepts: TestFlight distribution guide — https://techconcepts.org/blog/testflight-guide
- fastlane docs (match/gym/pilot/deliver) — https://docs.fastlane.tools/

**Verification flags in this document:** Apple review-guideline numbers,
required-reason reason codes, ITMS error codes, ExportOptions `method` names,
the current "must build with Xcode N SDK" requirement, TestFlight limits,
Xcode Cloud pricing, and asset-pack/cellular-download limits are all
version-sensitive — re-confirm against developer.apple.com before relying on
exact values.

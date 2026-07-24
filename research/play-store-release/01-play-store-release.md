# Google Play Release Engineering & the Play Console — 2025/2026 Reference

Authoritative reference for the `play-store-release-specialist` agent. Sources are official
Google properties (developer.android.com, play.google.com/console, support.google.com,
developers.google.com/android-publisher) unless flagged. **Play policies change frequently —
every date, API-level, and threshold below is version-sensitive; re-verify against the live
docs before acting on it.** Verified 2026-07.

---

## 1. App Signing

### Play App Signing (the default and effectively mandatory model)

- **Two-key model.** Google holds the **app signing key** (in Google's secure infrastructure /
  KMS) and uses it to sign the APKs actually delivered to users. You hold the **upload key** and
  sign each upload (`.aab`/`.apk`) with it. Play verifies the upload signature, strips it, and
  re-signs with the app signing key.
- **Why it matters:** If you lose the upload key you can **request an upload key reset** via Play
  Console and keep shipping — Google still has the app signing key. If you self-managed the
  signing key and lost it, you could never update the app again. Play App Signing removes that
  single point of failure.
- **Required for new apps** (since Aug 2021, all new apps use Play App Signing because they must
  ship `.aab`). Older apps could enrol via Play Console → **Release → Setup → App signing**
  (uploading the existing signing key with the **PEPK** tool / Play Encrypt Private Key).
- **Upload key ≠ app signing key.** Best practice is for them to be *different* keys. If they're
  the same (e.g. a legacy app that never separated them), a compromise of the upload key is more
  serious. New enrolments can generate a distinct upload certificate.
- **Key rotation / upgrade:** Play supports upgrading the app signing key (Release → Setup → App
  signing) for compromise or crypto migration. Key rotation via APK Signature Scheme **v3** lets
  new key sign installs/updates on **Android 13+ (API 33+)** while the legacy key continues to
  cover Android 12 and earlier. Rotation is limited and not a routine operation.

### Keystores and `keytool`

- Keystore = binary Java KeyStore file, `.jks` or `.keystore` extension, holding certificate(s) +
  private key(s). Protected by a **store password**; each key alias has its own **key password**.
- **Debug keystore** auto-generated at `~/.android/debug.keystore` (self-signed, ~30-yr validity);
  never used for release.
- **Validity:** keys should be valid ≥25 years; Google Play requires the certificate validity to
  extend beyond **22 October 2033**.
- Generate a keystore/key (CLI):
  ```bash
  keytool -genkeypair -v -keystore upload-keystore.jks \
    -keyalg RSA -keysize 2048 -validity 9125 -alias upload
  ```
- Export the upload certificate (e.g. to register the app or reset the upload key):
  ```bash
  keytool -export -rfc -keystore upload-keystore.jks -alias upload -file upload_certificate.pem
  ```
- Inspect signing report from a project: Gradle task **`signingReport`** (shows SHA-1/SHA-256
  fingerprints per variant — needed to register API keys, Google Sign-In, Maps, etc.).

### Gradle `signingConfigs` without committing secrets

- Never hard-code passwords or commit the `.jks`. Externalise into `keystore.properties` (git-
  ignored) or CI environment variables / secret store.
- `keystore.properties`:
  ```properties
  storePassword=...
  keyPassword=...
  keyAlias=upload
  storeFile=/secure/path/upload-keystore.jks
  ```
- `build.gradle.kts`:
  ```kotlin
  val kp = Properties().apply { load(FileInputStream(rootProject.file("keystore.properties"))) }
  android {
    signingConfigs {
      create("release") {
        storeFile = file(kp["storeFile"] as String)
        storePassword = kp["storePassword"] as String
        keyAlias = kp["keyAlias"] as String
        keyPassword = kp["keyPassword"] as String
      }
    }
    buildTypes { getByName("release") { signingConfig = signingConfigs.getByName("release") } }
  }
  ```
- **Add `keystore.properties` and `*.jks` to `.gitignore`.** In CI, inject the keystore as a
  base64 secret decoded at build time, and pass passwords via env vars.

---

## 2. Android App Bundle (`.aab`)

- **`.aab` is the required publishing format for new apps on Play** (since **August 2021**). APKs
  are deprecated for *new* app publishing (existing APK-based apps predating the cutoff may still
  update via APK, but new apps must use `.aab`). TV apps: `.aab` required since **June 2023**.
- The bundle is a **publishing format, not an installable** — it packages all compiled code and
  resources; Google Play generates and signs optimised **split APKs** per device via **Dynamic
  Delivery**. Users download only what their device needs (density, ABI, language).
- **Split APK types:** base APK + configuration APKs (screen density, ABI such as `arm64-v8a`/
  `armeabi-v7a`, language/locale) + optional feature-module APKs.
- **`bundletool`** — Google's standalone CLI (also used internally by Gradle and Play). Builds a
  device-specific APK set (`.apks`) from an `.aab`, installs to a connected device
  (`build-apks` / `install-apks`), and lets you test the exact APKs Play would serve **before**
  uploading. Essential for local verification of a bundle.
- **Size limits (version-sensitive):** compressed download for base + config APKs capped at
  **~4 GB**; on-demand feature modules also subject to the limit. Asset packs are governed
  separately (Play Asset Delivery limits). **`.aab` does NOT support legacy `.obb` APK expansion
  files** — use Play Asset Delivery instead.

### Play Feature Delivery (code modules)

Feature modules declare a delivery mode in their manifest:
- **install-time** — delivered with the base app (can be `removable`).
- **on-demand** — downloaded later at runtime via the Play Feature Delivery / Play Core API.
- **conditional** — installed at install time only if device meets conditions (country, min SDK,
  device features).
- **instant** — available to Google Play Instant.

### Play Asset Delivery (game/large assets)

- Delivers large assets (textures, media) separately from code via **asset packs**, with modes:
  **install-time**, **fast-follow** (downloads right after install, in background), and
  **on-demand**. Supports **texture compression format targeting** (e.g. ASTC vs ETC2) so devices
  fetch only the format they support. Replaces `.obb` for bundle-based games.

---

## 3. Release Tracks & Rollout

### Tracks (Play Console → Release / Testing)

- **Internal testing** — fastest path (available to testers within **minutes**); up to 100
  testers by email list; ideal for QA smoke tests.
- **Closed testing** — limited invited audience (email lists, Google Groups, or an opt-in link);
  can have multiple closed tracks (alpha and custom named tracks). *Note: since 2024 Google
  requires a period of closed testing with a minimum number of testers before a **new personal
  developer account** can publish to production — a version-sensitive policy.*
- **Open testing** — public beta; anyone can join (optionally capped); can target specific
  countries.
- **Production** — general availability.
- **Publishing API track names** map as: `internal`, `alpha` (closed), `beta` (open),
  `production`, plus custom closed-track names.

### Staged (percentage) rollout

- **Update-only:** staged rollout applies to app **updates**, not a first-time publish (first
  release always goes to 100%).
- **Supported on Production, Open testing, and Closed testing** tracks.
- Users are chosen **randomly**; you set an initial percentage and **increase** it over time
  (Production → Releases → **Manage rollout → Update rollout**).
- **Halt:** Manage rollout → **Halt rollout** stops new users receiving the version; users who
  already got it keep it. **Resume** requires specifying a new percentage.
- **Rollback / halting on Play (contrast with iOS):** You **can halt** a staged rollout at any
  percentage — a genuine kill-switch that iOS App Store lacks. The recommended recovery is to
  **halt the bad release and publish a new (higher versionCode) release with the fix** promoted to
  the same track; Google's guidance is that you don't literally "revert" bytes but you re-promote
  a previous good bundle as a new release. Play Console also surfaces a **"resume the previous
  release"** style flow when you halt. Because versionCode must monotonically increase, a rollback
  is technically a new release carrying older-or-fixed code with a higher versionCode.
- Country targeting can be narrowed but **countries can't be removed once a rollout starts**.

### Internal app sharing

- Separate from tracks: upload an `.aab`/`.apk` on the **Internal app sharing** page to get a
  **shareable link** for instant install by teammates/testers. Bypasses track review and
  versionCode-uniqueness rules (great for one-off QA builds). Access restricted to allow-listed
  emails or anyone with the link.

### Pre-registration & managed publishing

- **Pre-registration:** publish the store listing up to **90 days** before launch so users can
  pre-register and be notified at launch (optionally with pre-registration rewards).
- **Managed publishing:** when ON, approved changes/releases stay in a "reviewed, ready to
  publish" state so **you control the exact go-live moment** (publish them together) rather than
  auto-publishing on review completion. Toggle in **Publishing overview**.

---

## 4. Console & Policy Requirements

### Data safety form (Play Console → Policy → App content)

- Mandatory for essentially all apps (narrow exceptions such as internal-test-only). Declares, per
  data type, whether it is **collected** and/or **shared**, the **purpose**, whether collection is
  **required or optional**, and **security practices**.
- Data type categories include: Personal info, Financial info, Health & fitness, Messages,
  Photos/videos, Audio, Files/docs, Calendar, Contacts, App activity, Web browsing, App info &
  performance, Device or other IDs.
- **"Collect"** = transmitted off device (on-device-only processing and end-to-end-encrypted data
  are exempt). **"Share"** = transferred to a third party (service providers, legal, and user-
  initiated transfers are exempt).
- Security section: declare **encryption in transit**, whether users can **request deletion**, and
  eligibility for an independent **security review** badge. Auto-deletion/anonymisation within 90
  days can qualify as "data can be deleted."
- The declaration must reflect the **sum of collection/sharing across all currently-distributed
  versions**. It renders as the public **Data safety** section on the store listing.
- **Account deletion requirement (version-sensitive):** apps that let users create an account must
  offer **in-app account deletion** AND a **web URL** to request account + data deletion; that URL
  is declared in the Data safety form and surfaced on the listing. (Play's analogue to iOS's
  account-deletion rule.)

### Annual target API level requirement

- **Passed deadline:** since **31 August 2025**, new app submissions and updates must target
  **API 35 (Android 15)** (standard apps). (Extension window to ~Nov 1 available on request.)
- **Upcoming (version-sensitive):** by **31 August 2026**, new apps/updates must target
  **API 36 (Android 16)**; **existing** standard apps must target **API 35 (Android 15)** to
  remain available to new users. Extension to **1 November 2026** on request.
- **Form-factor carve-outs (2026):** Wear OS & Android Automotive OS new apps → API 35; Android TV
  & Android XR new apps → API 34.
- **Effect of targeting too low:** the app stays installed for existing users but becomes
  **invisible/unavailable on newer devices** (only offered to devices at or below its target API),
  and eventually can't receive updates. Set via `targetSdk` in Gradle.

### Sensitive/restricted permission declarations

- Declaration forms in **App content** for restricted permissions. **Background location**
  (`ACCESS_BACKGROUND_LOCATION`) is the classic case:
  - Declare **exactly one** core feature that needs background location; **multiple features →
    rejection**. The feature must be core (app "broken" without it) and user-visible.
  - Provide a **demo video** showing the feature and the runtime permission prompt; broken test
    credentials or a video that doesn't reach the feature are common rejection causes.
  - Submission triggers **extended review** (app can sit in "pending publication" for up to
    several weeks).
- Other declaration-gated permissions: `QUERY_ALL_PACKAGES`, SMS/Call Log, `MANAGE_EXTERNAL_
  STORAGE`, exact alarm, full-screen intent, health/AdID, photo/video (`READ_MEDIA_*`), etc.

### Other App-content requirements

- **Privacy policy URL** — required (and mandatory whenever the app handles personal/sensitive
  data or requests sensitive permissions).
- **Content rating** questionnaire (IARC) — required; misdeclaration can pull the listing.
- **Ads declaration**, **target audience & content** (Families/child-directed → Families policy),
  **news / COVID / financial / gambling** declarations as applicable.

### Pre-launch reports (Play Console → Test and release → Pre-launch report)

- Google's crawler robots (**Firebase Test Lab** infrastructure) exercise the app on **real
  devices** across Android versions when you upload to a testing track.
- Surfaces: **stability** (crashes, ANRs, unsupported/non-SDK API use, defective libraries),
  **performance** (CPU, memory, network, FPS over time), **accessibility** (content labels, touch
  target size, contrast), **security/privacy vulnerabilities**, and **screenshots** across devices/
  locales.
- You can supply **test login credentials / robo scripts** so the crawler gets past auth. Pre-
  launch crash data **does not** affect your production crash statistics. Failures don't hard-
  block release but are strong quality signals; a **broken/failed pre-launch report** is a common
  avoidable pitfall.

---

## 5. In-app APIs

### In-app updates — `AppUpdateManager`

- Prompts active users to update. **Two flows:**
  - **Flexible** — background download, user keeps using the app, you complete install when ready
    (good for non-critical updates; user can defer).
  - **Immediate** — full-screen blocking flow; Play handles download, install, and restart (for
    critical updates).
- Library: prefer the **Jetpack `com.google.android.play:app-update` / `app-update-ktx`** artifact
  (the modern replacement for the monolithic Play Core library). Min **Android 5.0 (API 21)**;
  **not** compatible with `.obb` expansion files.
- Flow: `appUpdateManager.appUpdateInfo` → check `updateAvailability()` and
  `isUpdateTypeAllowed(FLEXIBLE|IMMEDIATE)` → `startUpdateFlowForResult(...)`; use **update
  priority** (0–5, set via Publishing API when releasing) and **staleness (days since update
  available)** to decide flexible vs immediate. Test via **internal app sharing**.

### In-app review — `ReviewManager`

- `reviewManager.requestReviewFlow()` → obtain a `ReviewInfo`, then `launchReviewFlow(...)` to show
  the Play in-app review card in-context.
- **No guarantee it displays** — Google enforces a per-user, time-bounded **quota**; calling it
  repeatedly in a short window shows nothing. **Never** wire it to a "Rate us" button (assume it
  may be a no-op) — for user-initiated rating, deep-link to the Play Store listing instead.
- **Don't** precede it with your own "Do you like the app?" gate, and **don't** alter the card's
  size/opacity/position or overlay it. Trigger only after the user has meaningfully used the app.
- Library: Jetpack **`com.google.android.play:review` / `review-ktx`** (Play Core review ≥1.8.0
  originally). Min API 21.

### Play Integrity API (brief)

- Attests that requests come from a genuine, unmodified app binary, on a genuine Play-certified
  device, installed/paid-for via Google Play. Verdicts: **app integrity**
  (`appRecognitionVerdict`), **device integrity** (`deviceIntegrity`), **account/licensing**
  (`appLicensingVerdict`), plus opt-in signals (Play Protect, strong integrity, access-risk).
- **Standard** requests (low latency, on-demand, Play auto-mitigates replay, needs `requestHash`
  binding) vs **Classic** (one-off, developer supplies `nonce`). **Supersedes SafetyNet
  Attestation** (SafetyNet is deprecated/retired).

### Play Billing (brief)

- **Digital goods and services consumed within the app MUST use Google Play's Billing system**
  (Play policy). Physical goods/services use other payment methods. Use **Play Billing Library**
  for one-time products and subscriptions; validate/reconcile server-side via the
  **Subscriptions & In-App Purchases API** and **Real-Time Developer Notifications (RTDN)** rather
  than polling. (Note: external-billing / alternative-billing programs exist in some regions due
  to regulation — version- and region-sensitive.)

---

## 6. Automation

### Google Play Developer API (a.k.a. Android Publisher API, `androidpublisher` v3)

- **Publishing API uses a transactional "edits" model:**
  1. `edits.insert` — open a draft edit.
  2. `edits.bundles.upload` (or `edits.apks.upload`) — upload the `.aab`.
  3. `edits.tracks.update` — assign the uploaded version code(s) to a track (`internal`/`alpha`/
     `beta`/`production`/custom), set `userFraction` for staged rollout and `status`
     (`draft`/`inProgress`/`halted`/`completed`), and release notes.
  4. `edits.commit` — atomically apply. Nothing takes effect until commit.
- Companion APIs: **Reporting API** (`playdeveloperreporting`, Android vitals/metrics; default
  **10 QPS**), **Reply-to-Reviews API**, **Voided Purchases API**, **Permissions/Users API**,
  **Subscriptions & IAP API** (immediate, non-edits). Guidance: don't push more than ~1
  alpha/beta update per day.
- **Auth:** create a **service account** (in Google Cloud / linked in Play Console → Users &
  permissions), download its **JSON key**, grant it the needed Play Console permissions, and use
  OAuth2 service-account (2-legged) auth. Enable the **Google Play Android Developer API** in the
  Cloud project.

### Gradle Play Publisher (GPP) — `com.github.triplet.play` (Triple-T, unofficial)

- Gradle plugin that builds + uploads + promotes `.aab`/`.apk` and metadata. Key config:
  ```kotlin
  play {
    serviceAccountCredentials.set(file("play-sa.json"))
    track.set("internal")                        // or alpha/beta/production/custom
    releaseStatus.set(ReleaseStatus.COMPLETED)   // or IN_PROGRESS / DRAFT / HALTED
    userFraction.set(0.1)                        // staged rollout % when IN_PROGRESS
    resolutionStrategy.set(ResolutionStrategy.AUTO) // auto-bump vs IGNORE/FAIL on version conflict
    defaultToAppBundles.set(true)
  }
  ```
- Tasks: `publishBundle`, `publishApk`, `promoteArtifact`, `publishReleaseNotes`, `publishListing`.
  `resolutionStrategy.AUTO` auto-picks a valid (monotonic) version code.

### fastlane `supply` / `upload_to_play_store`

- Ruby-based. `supply init` bootstraps metadata; `upload_to_play_store` (aliased `supply`) uploads
  the `.aab`/`.apk`, metadata, screenshots, and promotes to a track (`internal`/`alpha`/`beta`/
  `production`). Auth via the **service-account JSON** (`json_key` / `json_key_data`) — supported
  since supply 0.4.0. Params: `track`, `rollout` (staged %), `release_status`,
  `skip_upload_apk`/`aab`.

### CI upload pattern

Typical GitHub Actions / CI flow: decode keystore + service-account JSON from secrets → `./gradlew
bundleRelease` (signed) → upload via GPP/fastlane/`r0adkll/upload-google-play` action to the
`internal` track (draft or 10% inProgress) → smoke-test → promote. **Version code must be unique &
monotonically increasing per upload** — derive it from CI build number or `git rev-list --count`.

---

## 7. Versioning & Release Strategy

- **`versionCode`** — integer, **must be unique and strictly increasing for every upload** to a
  track (Play rejects a re-used or lower code). Not shown to users. Max value 2,100,000,000.
- **`versionName`** — human-readable string (e.g. `3.2.1`); free-form, shown to users, no ordering
  requirement.
- With Play App Signing + `.aab`, a single upload's versionCode covers all generated split APKs.
- **Release strategy:** ship to `internal` → promote to closed/open → **staged rollout** on
  production starting small (e.g. 5–10%), while watching **Android vitals**.
- **Android vitals bad-behaviour thresholds (version-sensitive, affect discoverability):**
  - **User-perceived crash rate:** overall bad-behaviour threshold ≥ **1.09%** of daily active
    users; per-device-model threshold ≥ **8%**.
  - **User-perceived ANR rate:** analogous overall (**0.47%**) and per-device (**8%**) thresholds.
  - Exceeding overall → app less discoverable everywhere; exceeding per-device → less discoverable
    on that model + possible **store-listing warning**.
- **Halt / rollback:** if vitals regress mid-rollout, **halt** immediately, then release a fixed
  higher-versionCode bundle. Unlike iOS you retain a real staged-rollout kill switch.
- **Release notes ("What's new"):** per-language, per-release; supplied in Console or via
  Publishing API `edits.tracks` release `releaseNotes`. Keep concise; localise.

---

## 8. Common Rejection / Policy Pitfalls

1. **Data safety form missing, incomplete, or inaccurate** — mismatched with actual SDK behaviour
   (e.g. an analytics/ads SDK collects an ID you didn't declare) → rejection / removal.
2. **Target API level too low** — blocks new submissions/updates and hides the app on new devices
   after the annual deadline.
3. **Undeclared / over-broad sensitive permissions** — especially **background location**
   (multiple features declared, weak justification, missing/broken demo video, or requesting it
   without a genuine core feature). Also `QUERY_ALL_PACKAGES`, SMS/Call Log, `MANAGE_EXTERNAL_
   STORAGE`.
4. **Failed / broken pre-launch report** — crashes on launch, or the crawler can't get past login
   because no test credentials/robo script were supplied.
5. **Missing privacy policy** or a policy URL that 404s / doesn't match declared data practices.
6. **Missing in-app + web account deletion** for apps with account creation.
7. **Payments policy** — offering digital goods without Play Billing, or steering users to outside
   payment (region-dependent).
8. **Deceptive behaviour / metadata** — misleading store listing, undisclosed functionality,
   fake reviews, keyword stuffing, impersonation.
9. **Privacy/User-data policy** — transmitting personal/sensitive data without prominent
   disclosure + consent, or insecure transmission.
10. **Re-used or non-monotonic versionCode**, or an unsigned/mis-signed bundle → upload rejected by
    Play (not a policy review issue, but a frequent CI failure).

---

## Sources

App signing:
- https://developer.android.com/studio/publish/app-signing

App bundles / delivery:
- https://developer.android.com/guide/app-bundle
- (Play Feature Delivery, Play Asset Delivery, bundletool sections linked from the above)

Target API level:
- https://developer.android.com/google/play/requirements/target-sdk
- https://support.google.com/googleplay/android-developer/answer/11926878

Release tracks & rollout:
- https://support.google.com/googleplay/android-developer/answer/6346149 (staged rollouts)
- https://support.google.com/googleplay/android-developer/answer/9845334 (open/closed/internal tests)
- https://support.google.com/googleplay/android-developer/answer/9859348 (prepare & roll out)
- https://play.google.com/console/about/releasesoverview/
- https://play.google.com/console/about/internalappsharing/
- https://support.google.com/googleplay/android-developer/answer/9844679 (internal app sharing)

Console & policy:
- https://support.google.com/googleplay/android-developer/answer/10787469 (Data safety)
- https://support.google.com/googleplay/android-developer/answer/9799150 (background location)
- https://support.google.com/googleplay/android-developer/answer/16585319 (sensitive permissions/APIs)
- https://support.google.com/googleplay/android-developer/answer/9844487 (pre-launch report)
- https://support.google.com/googleplay/android-developer/answer/9844486 (Android vitals)
- https://developer.android.com/topic/performance/vitals/crash (crash thresholds)

In-app APIs:
- https://developer.android.com/guide/playcore/in-app-updates
- https://developer.android.com/guide/playcore/in-app-review
- https://developer.android.com/google/play/integrity/overview

Automation:
- https://developer.android.com/google/play/developer-api
- https://developers.google.com/android-publisher/edits
- https://developers.google.com/android-publisher/getting_started
- https://github.com/Triple-T/gradle-play-publisher
- https://docs.fastlane.tools/actions/upload_to_play_store/
- https://docs.fastlane.tools/actions/supply/
- https://github.com/r0adkll/upload-google-play

Note: some background/threshold figures were corroborated via search summaries of the official
pages above (Medium/third-party posts appeared in results but were not used as primary authority).
All policy dates, API levels, size limits, and vitals thresholds are **version-sensitive** — verify
against the live Google docs before relying on them.

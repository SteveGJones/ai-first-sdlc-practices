---
name: android-signing-setup
description: Set up Android app signing safely — generate an upload keystore, enroll in Play App Signing, and wire a Gradle release signingConfig that reads secrets from a git-ignored keystore.properties / CI (never committed). Use when configuring signing for a Play release.
disable-model-invocation: false
argument-hint: "[path-to-android-project]"
---

# Android Signing Setup

Configure Android release signing the safe way, under **Play App Signing** (Google holds the app
signing key; you hold the upload key). Belongs to the **`sdlc-team-android`** plugin.

## Arguments

- `path-to-android-project` — the project directory (defaults to the current directory).

## The model (why the two keys matter)

Under Play App Signing, **you sign uploads with an upload key; Google re-signs with the app signing
key** it holds. If you lose the upload key you can request a reset in Play Console and keep shipping —
the single-point-of-failure of self-managed signing is gone. Best practice: the **upload key is
distinct** from the app signing key.

## Steps

### 1. Generate an upload keystore

```bash
keytool -genkeypair -v -keystore upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 9125 -alias upload
```

- Validity ≥25 years (Play requires the certificate to extend beyond 22 Oct 2033).
- Store the `.jks` **outside the repo** (or encrypted); record the store/key passwords in a secret
  manager. Export the upload certificate if you need to register it:
  `keytool -export -rfc -keystore upload-keystore.jks -alias upload -file upload_certificate.pem`.

### 2. Wire the Gradle signingConfig without committing secrets

- Create a **git-ignored `keystore.properties`** (`storePassword`, `keyPassword`, `keyAlias`,
  `storeFile`) and load it in `build.gradle.kts`:

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

- **Add `keystore.properties` and `*.jks`/`*.keystore` to `.gitignore`.** In CI, inject the keystore as
  a base64 secret decoded at build time and pass passwords via env vars. Never commit either.

### 3. Enroll in Play App Signing

- New apps use Play App Signing automatically (they ship an `.aab`). For an existing app, enroll via
  Play Console → **Release → Setup → App signing** (PEPK tool to upload an existing key). Confirm the
  upload key ≠ app signing key.

### 4. Verify

- `./gradlew signingReport` shows the SHA-1/SHA-256 fingerprints per variant (needed to register API
  keys / Maps / Sign-In). Run the pre-flight checker — it flags a release build using the debug signing
  config and any committed secret in Gradle files.

### 5. Report

Confirm the release signingConfig reads from the git-ignored properties/CI, the keystore is out of the
repo, and `signingReport` shows the expected fingerprints. Note the Play App Signing enrollment status.

## Notes

- Losing the **upload** key is recoverable (Console reset); losing a self-managed **app signing** key is
  not — which is exactly why Play App Signing exists.
- For the full release flow (bundle, track, rollout) use `android-play-release`; for signing failures in
  CI, see `gradle-build-specialist` and `play-store-release-specialist`.

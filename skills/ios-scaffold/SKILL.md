---
name: ios-scaffold
description: Scaffold a new iOS app with SDLC and submission-safe defaults — diffable project files, app + test targets, deployment-target policy, a git-stamped build number, and the Info.plist keys the pre-flight checker wants so the project passes TestFlight from day one. Use when starting a new iOS project.
disable-model-invocation: false
argument-hint: "[app-name]"
---

# iOS Scaffold

Create a new iOS app project that is **submission-safe from the first commit** — so it doesn't hit the
TestFlight/App Store blockers `ios-testflight-release` and the pre-flight checker exist to catch.
Belongs to the **`sdlc-team-ios`** plugin; pairs with `swiftui-architect` (structure) and
`swift-language-expert` (language).

## Arguments

- `app-name` — the app / bundle name (defaults to asking).

## Steps

### 1. Choose the project-generation approach

Prefer a **diffable, mergeable** project definition over a hand-managed `.xcodeproj`:

- **Swift Package Manager** (an app built as a package + a thin app target) for library-first / simple apps.
- **Tuist** or **XcodeGen** to generate the `.xcodeproj` from a committed manifest (Tuist's `Project.swift`, or an XcodeGen YAML manifest)
  that *is* committed, so project changes review cleanly and don't cause merge conflicts.

Ask which the team prefers; default to XcodeGen/Tuist for an app that needs a real Xcode project.

### 2. Establish structure

- **App target** + **unit-test target** (Swift Testing) + optional **UI-test target** (XCUITest).
- A **SwiftPM feature-module** layout if the app is non-trivial (feature packages + Core/DesignSystem/
  Models; thin app composition root) — see `swiftui-architect`.
- `.gitignore` covering `*.xcodeproj` (if generated), `DerivedData/`, `.build/`, `*.xcuserstate`,
  `.DS_Store`, and any secrets file.

### 3. Wire submission-safe Info.plist defaults (this is the point of the skill)

Pre-set the keys the pre-flight checker looks for, so uploads don't stall or get rejected later:

- **`ITSAppUsesNonExemptEncryption = false`** (if the app uses only exempt encryption such as standard
  HTTPS) — skips the export-compliance questionnaire on every upload.
- A **`NS…UsageDescription`** placeholder-with-a-real-sentence for each capability the app will use
  (add them as you add frameworks; the pre-flight check maps CoreMotion→`NSMotionUsageDescription`,
  etc.). Leave a comment reminding that these must be real human sentences.
- Set the **deployment target** to the team's minimum-supported iOS per policy (and keep it consistent
  across targets and `Package.swift`).

### 4. Git-stamped, monotonic build number

- Keep `MARKETING_VERSION` fixed pre-1.0 (e.g. `1.0.0`) and stamp **`CFBundleVersion` from
  `git rev-list --count HEAD`** (optionally plus the short SHA and date) in a **build-phase script**,
  so every build is unique, monotonic, and traceable to a commit.
- On the target that runs that script, set **`ENABLE_USER_SCRIPT_SANDBOXING = NO`** (leave it `YES`
  elsewhere) — a script that reads git/the environment fails to archive under the sandbox otherwise.

### 5. Release-default safety

- Gate debug menus, feature flags, verbose logging, and staging endpoints behind a build config or a
  flag that is **OFF in Release** unless explicitly enabled.
- No secrets/API keys in the repo or the bundle — use `.xcconfig`/build settings + a secrets mechanism.

### 6. CI and privacy manifest

- Offer to run `ios-ci` to generate the GitHub Actions workflow (which gates on the pre-flight checks).
- Add a `PrivacyInfo.xcprivacy` stub if the app will use required-reason APIs or bundle third-party SDKs.

### 7. Verify

- Build once; run the unit-test target; and run the pre-flight checker
  (`python -m ios_preflight.cli <project>`) — it should be clean (or only INFO) on a fresh scaffold.

### 8. Report

Summarise what was generated, the generation approach chosen, the build-number policy, and confirm the
pre-flight checker is clean. Note anything the user must fill in (real purpose strings, signing team).

## Notes

- The goal is a project that passes `ios-testflight-release` pre-flight on day one — don't leave the
  export-compliance key or build-number policy "for later".
- For app *architecture* choices (state, navigation, persistence), hand off to `swiftui-architect`; for
  idiomatic Swift, to `swift-language-expert`.

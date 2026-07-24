# Gradle & the Android Gradle Plugin (AGP) — 2025/2026 Reference

Reference material for the `gradle-build-specialist` agent. Scope is the **build
system** (Gradle + AGP), not app architecture or Compose UI.

> **Version-sensitive notice.** Facts here are pinned to the toolchain current as
> of mid-2026. Newest stable at time of writing: **AGP 9.3.0** (requires **Gradle
> 9.5.0**, **JDK 17**, SDK Build Tools 36, max compileSdk API 37). The DSL and
> defaults changed meaningfully across the AGP 8.x → 9.x boundary (see §9 and the
> R8 note in §8). Always re-check the compatibility matrix and release notes
> before quoting a specific minimum-version number — these move on a roughly
> quarterly cadence and Google deprecates aggressively. Anything below tagged
> **[version-sensitive]** should be treated as a moving target.

---

## 1. Project structure & the DSL

An Android Gradle build is a **multi-project (multi-module) build**. Files:

| File | Role |
|------|------|
| `settings.gradle(.kts)` | Initialization phase. Declares which modules are part of the build (`include(...)`), configures plugin + dependency repositories, and (modern) declares the version catalog. |
| Root `build.gradle(.kts)` | Declares plugins for the whole build, usually with `apply false`. Should contain almost no real logic — shared logic belongs in convention plugins (§3). |
| Module `build.gradle(.kts)` | Per-module: applies plugins, configures the `android {}` block, declares dependencies. |
| `gradle.properties` | JVM args, feature flags, performance toggles (§4). |
| `gradle/libs.versions.toml` | Version catalog (§2). |
| `gradle/wrapper/gradle-wrapper.properties` | Pins the Gradle version (the wrapper — always build via `./gradlew`, never a system Gradle). |

### Kotlin DSL vs Groovy DSL

**Kotlin DSL (`.gradle.kts`) is the default and recommended choice** (default for
new projects since Android Studio Giraffe / AGP 8.0-era templates). Benefits:
type-safety, IDE autocomplete, compile-time checking, refactoring, click-through
navigation. Groovy (`.gradle`) is legacy/dynamic-typed. Practical Kotlin-DSL
gotchas the agent should know:

- Property assignment uses `=` (`compileSdk = 36`), not Groovy's space syntax.
- Boolean build-type flags are `is`-prefixed: `isMinifyEnabled`, `isShrinkResources`,
  `isDebuggable`, `isCrunchPngs` (this trips up people copying Groovy snippets).
- Container elements are accessed with `getByName("release")` / `create("staging")`
  rather than Groovy's bare `release { }`.

### `settings.gradle.kts` — canonical shape

```kotlin
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()   // list last — reduces redundant metadata lookups
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)  // repos only here
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "MyApp"
include(":app", ":core:data", ":feature:home")
```

`FAIL_ON_PROJECT_REPOS` centralizes repository declarations in settings and makes
per-module `repositories {}` an error — a good hygiene default.

### The `plugins {}` block

Root build declares versions once, defers application:

```kotlin
// root build.gradle.kts
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library)     apply false
    alias(libs.plugins.kotlin.android)      apply false
    alias(libs.plugins.ksp)                 apply false
}
```

`apply false` = "resolve the plugin for the build, but don't apply it here." Each
module then applies without a version:

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}
```

Core plugin IDs: `com.android.application` (APK/AAB app module),
`com.android.library` (AAR library module), `org.jetbrains.kotlin.android`
(Kotlin), `com.google.devtools.ksp` (annotation processing, §5),
`com.android.test`, `com.android.dynamic-feature`.

### The `android {}` block essentials

```kotlin
android {
    namespace = "com.example.app"   // package for the generated R class + BuildConfig;
                                     // replaced the old manifest `package` attribute (AGP 7+, mandatory AGP 8+)
    compileSdk = 36                  // API level the code COMPILES against (use latest stable)

    defaultConfig {
        applicationId = "com.example.app" // the published Play identity (app modules only; libraries have none)
        minSdk = 24                        // lowest device API the app runs on
        targetSdk = 36                     // API the app is TESTED against; drives runtime behavior opt-ins
        versionCode = 1                    // integer, monotonically increasing — Play ordering
        versionName = "1.0"                // user-visible string
    }
    // buildTypes {}, productFlavors {}, buildFeatures {}, compileOptions {} ...
}
```

Key distinctions the agent must not conflate:
- **`namespace`** = R/BuildConfig package (build-time). **`applicationId`** =
  installed/published identity (runtime + Play). They are independent; namespace
  is set in `android {}`, applicationId in `defaultConfig {}`.
- **`compileSdk`** ≠ **`targetSdk`** ≠ **`minSdk`**. Compile = what you can call;
  target = behavior contract you accept; min = floor of supported devices.
- `buildFeatures {}` toggles generated artifacts, e.g. `buildConfig = true`
  (BuildConfig generation became **opt-in** in AGP 8.0 — a frequent migration
  break), `viewBinding = true`, `compose = true`. **[version-sensitive]**

### Build lifecycle (why it matters for perf)

Gradle runs three phases every invocation: **Initialization** (settings, which
projects) → **Configuration** (evaluate every build script, build the task
graph/DAG) → **Execution** (run the selected tasks). Work done at
**configuration** time is paid on *every* build regardless of which task you run —
this is the root of most performance pitfalls (§4, §10) and what the
configuration cache targets (§4).

---

## 2. Version catalogs — `gradle/libs.versions.toml`

The modern, Google-recommended dependency-management standard. A single TOML file
is the source of truth for versions of libraries and plugins across all modules.
Gradle generates type-safe `libs.*` accessors from it.

```toml
[versions]
agp = "9.3.0"
kotlin = "2.3.4"
ksp = "2.3.4"                 # KSP version is pinned to a Kotlin version — keep in lockstep
coreKtx = "1.13.1"
room = "2.6.1"
composeBom = "2024.09.00"

[libraries]
androidx-core-ktx   = { group = "androidx.core", name = "core-ktx", version.ref = "coreKtx" }
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-compose-ui  = { group = "androidx.compose.ui", name = "ui" }  # version comes from the BOM
room-runtime  = { module = "androidx.room:room-runtime",  version.ref = "room" }
room-compiler = { module = "androidx.room:room-compiler", version.ref = "room" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
android-library     = { id = "com.android.library",     version.ref = "agp" }
kotlin-android      = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
ksp                 = { id = "com.google.devtools.ksp",  version.ref = "ksp" }

[bundles]
compose = ["androidx-compose-ui", "androidx-compose-material3"]
```

Sections:
- **`[versions]`** — named version constants, referenced elsewhere via `version.ref`.
- **`[libraries]`** — dependency coordinates. Use `group`+`name` or `module`
  (`"group:name"`). Version can be `version.ref`, inline `version = "x"`, or omitted
  (BOM-supplied). Use **kebab-case** names; dots/dashes map to nested accessors.
- **`[plugins]`** — plugin coordinates, consumed via `alias(libs.plugins.…)`.
- **`[bundles]`** — named groups of libraries applied in one line.

Accessors (kebab → dotted): `androidx-core-ktx` → `libs.androidx.core.ktx`;
`libs.bundles.compose`; `libs.plugins.ksp`. Usage:

```kotlin
dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.bundles.compose)
    ksp(libs.room.compiler)
}
```

**Why use them:** single source of truth, no drifting/duplicated version strings
across modules, type-safe accessors with autocomplete and refactor support,
shareable across included builds and convention plugins, and Dependabot/Renovate
understand the file. Not having a catalog in a multi-module project is itself a
pitfall (§10).

---

## 3. Convention plugins — `buildSrc` vs `build-logic`

The problem: in a multi-module project, every module's `build.gradle.kts` repeats
the same `android {}` config, compile options, common dependencies. Convention
plugins factor that repetition into reusable plugins each module simply applies.

### `buildSrc` (legacy, avoid for large projects)

`buildSrc/` is an implicit special build compiled before everything else and put on
every build script's classpath. **The problem: any change inside `buildSrc`
invalidates and rebuilds the entire project** (all task outputs), which cripples
incrementality on large codebases. Fine for a handful of constants; poor for
shared build logic at scale.

### `build-logic` composite (included) build — recommended

The pattern used by Google's **Now in Android** sample. `build-logic/` is a
separate **included build** wired in from `settings.gradle.kts`:

```kotlin
// settings.gradle.kts
pluginManagement {
    includeBuild("build-logic")
}
```

Inside it, a `convention` module (`com.android.library` for its own build +
`kotlin-dsl`) defines **precompiled convention plugins**. Two implementation styles:

1. **Precompiled script plugins** — `.gradle.kts` files under
   `build-logic/convention/src/main/kotlin/`. The filename becomes the plugin id
   (e.g. `myproject.android.library.gradle.kts` → id
   `myproject.android.library`). Simplest to start; you write normal build-script
   DSL.
2. **Binary plugins** — real `Plugin<Project>` classes in `.kt`, registered via
   `gradlePlugin { plugins { register(...) } }` in the convention module's build.
   Now in Android uses this style (e.g. `AndroidApplicationConventionPlugin`,
   `AndroidLibraryConventionPlugin`, `AndroidHiltConventionPlugin`). More testable
   and lets you branch logic in Kotlin.

A convention plugin centralizes shared setup:

```kotlin
// build-logic/convention/src/main/kotlin/AndroidLibraryConventionPlugin.kt
class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        with(pluginManager) {
            apply("com.android.library")
            apply("org.jetbrains.kotlin.android")
        }
        extensions.configure<LibraryExtension> {
            compileSdk = 36
            defaultConfig { minSdk = 24 }
            // shared compileOptions, kotlinOptions, lint config, etc.
        }
    }
}
```

Modules then collapse to:

```kotlin
plugins {
    id("myproject.android.library")   // one line replaces dozens
}
```

**Why `build-logic` beats `buildSrc`:** it's a normal included build, so its
plugins are compiled and cached like any other plugin and do **not** force a full
project rebuild when unrelated logic changes; it's independently versionable and
unit-testable; and it plays well with the configuration cache. Convention plugins
can also reference the version catalog (via
`extensions.getByType<VersionCatalogsExtension>().named("libs")`) so versions stay
centralized.

---

## 4. Build performance

Configuration and caching features, roughly in order of impact.

### Configuration cache (biggest single win)

Caches the **result of the configuration phase** — the fully-built task graph and
task state. When configuration inputs are unchanged, Gradle skips configuration
entirely and goes straight to execution. Enable in `gradle.properties`:

```properties
org.gradle.configuration-cache=true
org.gradle.configuration-cache.problems=warn   # report, don't fail, during adoption
```

First run logs "Calculating task graph as no configuration cache is available";
later runs log "Reusing configuration cache." **Since Gradle 9.0 this is the
preferred execution mode** and it is enabled by default in newer AGP/Studio
templates. **[version-sensitive]** Requirements: tasks/plugins must not read live
project state at execution time or hold references to `Project`, `Task`, etc.
Older AGP had known invalidations (fixed across AGP 8.2/8.3). IDE sync does not yet
use it. Distinct from the build cache below.

### Build cache (local + remote)

Caches **task outputs** keyed by task inputs; a cache hit copies outputs instead of
re-running the task. Local cache reuses across builds on one machine; a **remote**
build cache (e.g. Develocity/Gradle Enterprise) shares outputs across a team and
CI so a teammate/CI can reuse compilation you already did.

```properties
org.gradle.caching=true
```

Only tasks that correctly declare inputs/outputs (and are `@CacheableTask`) benefit
— non-cacheable custom tasks are a common pitfall (§10). Mental model:
**configuration cache = skip configuration; build cache = skip execution of
individual tasks.**

### Parallelism & incrementality

```properties
org.gradle.parallel=true    # run tasks of independent modules in parallel
org.gradle.caching=true
```

Parallelism pays off in proportion to how well-modularized the project is — a
monolithic module can't parallelize. Incremental compilation (Kotlin/Java),
incremental annotation processing (KSP), and incremental resource processing all
depend on tasks declaring accurate inputs/outputs.

### JVM heap / daemon memory

```properties
org.gradle.jvmargs=-Xmx6g -XX:MaxMetaspaceSize=1g -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
```

Start around 4–8 GB and tune. The Gradle daemon persists a warm JVM across builds
(≈2–3× speedup on the second build alone). GC: JDK 9+ defaults to G1;
`-XX:+UseParallelGC` is worth benchmarking for build workloads. Android Studio's
**Build Analyzer** flags GC overhead >15% and suggests a larger heap.

### Non-transitive / non-constant R classes

Default since **AGP 8.0**: `android.nonTransitiveRClass=true` (each module's R
class holds only its own resources → smaller R classes, better incrementality) and
non-constant R fields (more precise resource shrinking, better Java-compile
incrementality). **[version-sensitive]** — legacy projects may still carry these
flags explicitly.

### Avoiding configuration-time work

The highest-leverage discipline: keep the configuration phase cheap because it runs
every build. Do not resolve dependency configurations at configuration time, do not
do file I/O / exec / network at configuration time, and register tasks lazily with
`tasks.register(...)` (lazy) instead of `tasks.create(...)` (eager). See §10.

### Build scans — `--scan`

```
./gradlew assembleDebug --scan
```

Uploads a detailed, shareable report (task timings, configuration vs execution
breakdown, cache hit/miss, dependency resolution, deprecations, plugin overhead).
The primary tool for *diagnosing* where build time actually goes rather than
guessing. Android Studio's Build Analyzer is the local equivalent.

### Why AGP upgrades matter for performance

New AGP versions ship faster task implementations, better configuration-cache and
build-cache compatibility, incremental improvements to resource/dexing pipelines,
and new defaults (non-transitive R classes, optimized resource shrinking, R8
improvements). Staying current is itself a perf strategy — and required to move
Gradle/Kotlin/JDK forward (§9).

---

## 5. KSP vs kapt

**kapt** (Kotlin Annotation Processing Tool) runs Java annotation processors on
Kotlin by generating **Java stubs** for the whole module, then invoking `javac`.
The stub generation is the bottleneck.

**KSP** (Kotlin Symbol Processing) processes Kotlin symbols **directly** with no
stub/`javac` round-trip. Google reports it is **up to ~2× faster** on average, and
it understands Kotlin constructs (nullability, etc.) more accurately. **kapt is in
maintenance mode; Google recommends migrating.** KSP2 (the rewritten API, stable
in recent KSP releases) is the current line.

Migration:

```kotlin
// root build.gradle.kts
plugins { alias(libs.plugins.ksp) apply false }   // id = com.google.devtools.ksp

// module build.gradle.kts
plugins {
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.ksp)
}
dependencies {
    implementation(libs.room.runtime)
    ksp(libs.room.compiler)          // was: kapt("androidx.room:room-compiler:…")
}
```

Per-library: **Room** `ksp("androidx.room:room-compiler")`; **Hilt/Dagger**
`ksp("com.google.dagger:hilt-compiler")`; **Moshi**
`ksp("com.squareup.moshi:moshi-kotlin-codegen")` — the artifact usually stays the
same, only the `kapt` configuration becomes `ksp`.

Critical caveats:
- **The KSP plugin version is tied to the Kotlin version** (e.g. `2.3.4-x` tracks
  Kotlin 2.3.x). Keep them in lockstep or the build fails. **[version-sensitive]**
- If *any* kapt processor remains in a module, kapt still generates stubs for the
  **whole module** — you lose the speedup until you migrate every processor in that
  module.
- **Data Binding still requires kapt** (no KSP support planned) — keep kapt in
  modules that use it.
- Processor argument syntax can differ between kapt and KSP.

---

## 6. Build types, flavors, variants

**Build variant = (build type) × (product flavor per dimension).** You configure
build types and flavors; Gradle produces the cross-product of variants.

### Build types — packaging/build settings

Default `debug` and `release`. Debug: `isDebuggable = true`, generic debug
keystore, no shrinking. Release: shrinking + real signing.

```kotlin
android {
    buildTypes {
        getByName("release") {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"),
                          "proguard-rules.pro")
            signingConfig = signingConfigs.getByName("release")
        }
        getByName("debug") {
            applicationIdSuffix = ".debug"   // install alongside release
            versionNameSuffix = "-debug"
            isDebuggable = true
        }
        create("staging") {
            initWith(getByName("release"))   // inherit, then override
            applicationIdSuffix = ".staging"
            matchingFallbacks += listOf("release")
        }
    }
}
```

### Product flavors + flavor dimensions

Every flavor must belong to a declared `flavorDimensions` entry. Multiple
dimensions multiply.

```kotlin
android {
    flavorDimensions += listOf("tier", "env")
    productFlavors {
        create("free") { dimension = "tier"; applicationIdSuffix = ".free" }
        create("paid") { dimension = "tier"; applicationIdSuffix = ".paid" }
        create("prod") { dimension = "env";  buildConfigField("String","API","\"https://api.example.com\"") }
        create("mock") { dimension = "env";  buildConfigField("String","API","\"https://mock.example.com\"") }
    }
}
```

Two dimensions × two flavors each × two build types = **8 variants**
(`freeProdDebug`, `paidMockRelease`, …). The **first-listed dimension has higher
merge priority** for resources/manifests.

### `buildConfigField` / `resValue`

- `buildConfigField("String", "API_URL", "\"https://…\"")` injects a constant into
  the generated `BuildConfig` class (note the escaped inner quotes for String
  values, and require `buildFeatures { buildConfig = true }` on AGP 8+).
- `resValue("string", "app_name", "MyApp Free")` generates a resource value per
  variant (no separate XML file needed).
- `manifestPlaceholders["hostName"] = "…"` substitutes `${hostName}` in the manifest.

### Variant-specific dependencies & source sets

Configuration names are derived: `<flavor|buildType|variant>Implementation`.

```kotlin
dependencies {
    debugImplementation("com.squareup.leakcanary:leakcanary-android:2.14")
    "freeImplementation"(project(":ads"))
    "paidReleaseImplementation"(project(":premium"))
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}
```

Source-set merge priority (highest → lowest): **variant** (`src/freeDebug/`) →
**build type** (`src/debug/`) → **flavor** (`src/free/`) → **main** (`src/main/`).
Put variant-specific code/resources in the matching directory and it overrides/adds
to `main`.

### `matchingFallbacks` and variant-aware matching

AGP matches an app variant to the corresponding variant of each library dependency.
When a library lacks a build type or flavor the app has, resolution fails — declare
fallbacks:

```kotlin
buildTypes {
    create("staging") { matchingFallbacks += listOf("debug", "release") }
}
productFlavors {
    create("free") { dimension = "tier"; matchingFallbacks += listOf("demo") }
}
// When a library has a dimension the app doesn't:
defaultConfig { missingDimensionStrategy("env", "prod", "mock") }
```

### signingConfigs

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("KEYSTORE") ?: "release.jks")
            storePassword = System.getenv("KSTOREPWD")
            keyAlias = "release"
            keyPassword = System.getenv("KEYPWD")
        }
    }
}
```
Never hard-code passwords; pull from env vars / Gradle properties / a secrets file.

---

## 7. Dependency management

### Configurations (compile-time leakage matters for build speed)

| Configuration | On compile classpath | On runtime classpath | Leaks transitively to consumers | Use for |
|---|---|---|---|---|
| `implementation` | yes | yes | **no** | Default. Internal deps — changes only recompile direct consumers. |
| `api` | yes | yes | **yes** | Only when a library deliberately exposes a dep in its **public** API. Costs recompilation of all consumers on change — use sparingly. |
| `compileOnly` | yes | **no** | n/a | Compile-only annotations / provided deps not shipped at runtime. |
| `runtimeOnly` | **no** | yes | n/a | Runtime-only implementations (e.g. a logging backend). Rare on Android. |
| `ksp` / `kapt` / `annotationProcessor` | processing only | no | n/a | Annotation processors (§5). |

Prefer `implementation` by default; reach for `api` only intentionally. Over-using
`api` across modules is a real build-time regression.

### BOM / `platform()` — version alignment

A BOM (Bill of Materials) pins a coherent set of versions for a library family so
you omit individual versions. The canonical case is **Compose**:

```kotlin
dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.09.00")
    implementation(composeBom)
    androidTestImplementation(composeBom)   // apply to test classpath too
    implementation("androidx.compose.ui:ui")            // version from BOM
    implementation("androidx.compose.material3:material3")
}
```

`platform(...)` imports the BOM's version constraints without adding it as a real
dependency. This guarantees the Compose artifacts are mutually compatible.

### Constraints, resolution strategy, alignment

```kotlin
dependencies {
    constraints {
        implementation("com.squareup.okhttp3:okhttp:4.12.0") {
            because("CVE fix / force a floor even if pulled in transitively")
        }
    }
    implementation("com.example:lib:1.0") {
        version { strictly("1.5.0") }          // reject any other resolved version
        exclude(group = "com.unwanted", module = "bloat")
    }
}
configurations.all {
    resolutionStrategy {
        failOnVersionConflict()                // or force("group:name:version")
    }
}
```

Constraints influence versions **without** adding a dependency edge (ideal for
security floors on transitive deps). Prefer static versions; avoid dynamic
selectors (`1.+`, `latest.release`) and SNAPSHOTs — they cause non-reproducible,
slower builds (network checks) and are a listed pitfall.

### Dependency locking / verification (reproducibility)

```
./gradlew dependencies --write-locks     # produce gradle.lockfile(s)
```
Locking pins resolved versions for reproducible CI. Verification metadata
(`gradle/verification-metadata.xml`, `org.gradle.dependency.verification=strict`)
adds checksum/signature checking of downloaded artifacts (supply-chain integrity).

---

## 8. R8 / shrinking

R8 is the default optimizer (replaced ProGuard): **code shrinking** (tree-shake
unreachable code from entry points) + **optimization** (inlining, class merging) +
**obfuscation** (rename to short names) + **resource shrinking**. Enable on
**release only** (it adds build time).

### Enable (legacy DSL — AGP < 9.3, still the common form)

```kotlin
buildTypes {
    getByName("release") {
        isMinifyEnabled = true       // R8 code shrinking + optimization + obfuscation
        isShrinkResources = true     // remove unused resources (requires minify on)
        proguardFiles(
            getDefaultProguardFile("proguard-android-optimize.txt"),  // NOT proguard-android.txt (that has -dontoptimize)
            "proguard-rules.pro"
        )
    }
}
```

### New optimization DSL — AGP 9.3+ **[version-sensitive]**

```kotlin
buildTypes {
    getByName("release") {
        optimization { enable = true }   // combined code + resource optimization
    }
}
```
AGP 9.3 also adds keep rules under `src/<variant>/keepRules/*.keep` and an **R8
Configuration Analyzer** (AGP 9.3.0-alpha05+) that surfaces the broadest, most
optimization-blocking `-keep` rules.

### Keep rules (`proguard-rules.pro`)

Protect code that R8 can't see is used (reflection, JNI, serialization, DI, manifest
entry points):

```proguard
-keep class com.example.model.** { *; }                       # reflected/serialized models
-keepclasseswithmembernames class * { native <methods>; }     # JNI
-keep class * implements android.os.Parcelable {              # Parcelable
    public static final android.os.Parcelable$Creator *;
}
-keepclassmembers enum * { public static **[] values(); public static ** valueOf(java.lang.String); }
-keepattributes Signature,RuntimeVisibleAnnotations,AnnotationDefault   # generics/annotations for Gson/Moshi/Retrofit
```

Most mainstream libraries ship **consumer ProGuard rules** inside their AAR, so you
usually don't hand-write rules for Retrofit/Room/etc. Write your own mainly for
your reflected/serialized types.

### Full-mode R8

Default since AGP 8.0: more aggressive assumptions about reflection → smaller,
faster output but may need extra keep rules. Disable (temporary escape hatch) with
`android.enableR8.fullMode=false` in `gradle.properties`. **[version-sensitive]**

### Obfuscation & `mapping.txt`

Obfuscation renames classes/methods (`com.example.MainActivity.onCreate` → `a.b.c`),
shrinking DEX size but scrambling stack traces. R8 emits the reverse map at
`app/build/outputs/mapping/<variant>/mapping.txt`. **Upload it to Play Console /
your crash reporter** to deobfuscate (retrace) crash reports. Studio Logcat
auto-retraces local crashes using it (AGP 8.6+). Use the `retrace` tool for offline
deobfuscation. Optimized resource shrinking (default when `isShrinkResources=true`
on AGP 9.0+; opt-in `android.r8.optimizedResourceShrinking=true` on 8.12/8.13)
removes resources referenced only by removed code. **[version-sensitive]**

---

## 9. AGP / Gradle / Kotlin / JDK compatibility

These versions form a **matrix that must move together** — AGP requires a minimum
Gradle, a minimum JDK, and specific Build Tools; Kotlin and the Kotlin/KSP plugins
have their own coupling. You cannot bump one arbitrarily.

Current (mid-2026) **[version-sensitive — verify before quoting]**:

| Component | For AGP 9.3.0 |
|---|---|
| Gradle | **9.5.0** minimum & default |
| JDK | **17** (mandatory floor — no fallback) |
| SDK Build Tools | 36.0.0 |
| Max `compileSdk` | API 37 |
| NDK (default) | 28.2.x |

Rules of thumb the agent can rely on even as numbers change:
- Each AGP release names a **minimum Gradle** version; the wrapper
  (`gradle-wrapper.properties`) must be ≥ that.
- AGP has a **hard minimum JDK** (was 11 for AGP 8.x, **17 for AGP 9.x**). Set the
  Studio Gradle JDK accordingly.
- The **Kotlin Gradle plugin** and the **KSP plugin** are coupled to the Kotlin
  language version — bump Kotlin, KSP, and (if used) Compose compiler together.
- `compileSdk` cannot exceed what the AGP version supports.

**AGP Upgrade Assistant** (Android Studio: *Tools → AGP Upgrade Assistant*)
automates version bumps and applies known migration steps/DSL changes between AGP
versions; the **SDK Upgrade Assistant** helps raise `targetSdk`. Upgrading AGP is
also the mechanism that unlocks newer Gradle/Kotlin/JDK — hence "versions move
together."

---

## 10. Common pitfalls

1. **Configuration-time work.** Resolving configurations, file I/O, `exec`, or
   network calls during the configuration phase runs on *every* build (even for
   unrelated tasks) and breaks the configuration cache. Also `tasks.create(...)`
   (eager) vs `tasks.register(...)` (lazy) — eager creation configures tasks you
   never run.
2. **kapt bottleneck.** Any remaining kapt processor forces whole-module Java-stub
   generation; migrate every processor in a module to KSP to get the win (§5).
3. **Non-cacheable tasks.** Custom tasks without declared inputs/outputs (or not
   `@CacheableTask`) never hit the build cache and defeat up-to-date checks.
4. **Dependency resolution at configuration time** (e.g. iterating a configuration's
   files in a `build.gradle.kts` body) forces early resolution and network hits.
5. **Dynamic/SNAPSHOT versions** (`1.+`, `latest.release`) → non-reproducible,
   network-bound, slower builds. Pin static versions (use the catalog).
6. **Over-broad `-keep` rules** (`-keep class com.example.** { *; }` across the app)
   neuter R8 — larger APK, slower runtime. Keep only what's actually reflected;
   lean on libraries' bundled consumer rules; use the R8 Configuration Analyzer.
7. **No version catalog** in a multi-module project → drifting/duplicated versions,
   conflicts, painful upgrades. Adopt `libs.versions.toml` (§2).
8. **`buildSrc` for large shared logic** → full-project rebuild on any change; move
   to a `build-logic` included build with convention plugins (§3).
9. **Under-modularization** → no parallelism, no fine-grained caching, everything
   recompiles. Split into feature/core modules.
10. **Stale AGP/Gradle** → missing configuration-cache fixes, slower task
    implementations, and eventually blocked from newer Kotlin/JDK. Upgrade on a
    cadence via the Upgrade Assistant.
11. **Under-sized heap / cold daemon** → GC thrash and OOM; set `org.gradle.jvmargs`
    and keep the daemon warm. Watch the Build Analyzer's >15% GC warning.
12. **AGP 8.0 migration breaks** — `buildConfig`/`viewBinding`/`aidl` generation
    became opt-in (`buildFeatures {}`) and `namespace` became mandatory (dropped the
    manifest `package`). Common cause of "BuildConfig not found" after upgrade.

---

## Sources

Official (primary):
- Android — Gradle build overview: https://developer.android.com/build/gradle-build-overview
- Android — Migrate to version catalogs: https://developer.android.com/build/migrate-to-catalogs
- Android — Migrate to KSP: https://developer.android.com/build/migrate-to-ksp
- Android — AGP release notes / compatibility: https://developer.android.com/build/releases/gradle-plugin
- Android — Optimize your build: https://developer.android.com/build/optimize-your-build
- Android — Configure build variants: https://developer.android.com/build/build-variants
- Android — Add build dependencies: https://developer.android.com/build/dependencies
- Android — Shrink, obfuscate, optimize (R8): https://developer.android.com/build/shrink-code
- Android — AGP Upgrade Assistant: https://developer.android.com/build/agp-upgrade-assistant
- Gradle — Configuration cache: https://docs.gradle.org/current/userguide/configuration_cache.html
- Gradle — Build performance: https://docs.gradle.org/current/userguide/performance.html
- Gradle — Best practices for tasks: https://docs.gradle.org/current/userguide/best_practices_tasks.html
- Gradle — Solving common caching problems: https://docs.gradle.org/current/userguide/common_caching_problems.html
- Gradle — Sharing build logic between subprojects (convention plugins): https://docs.gradle.org/current/samples/sample_convention_plugins.html
- Google — Now in Android `build-logic`: https://github.com/android/nowinandroid/tree/main/build-logic
- KSP overview (JetBrains): https://kotlinlang.org/docs/ksp-overview.html

Secondary (community, for convention-plugin & pitfall context):
- ProAndroidDev — Gradle Kotlin convention plugins for modularized structure: https://proandroiddev.com/gradle-kotlin-convention-plugins-for-modularized-structure-shared-build-logic-e740e1f07e88
- Medium — Why your Gradle build is slow: top culprits and remedies: https://medium.com/@stefanhebuaa/why-your-gradle-build-is-slow-top-7-culprits-and-their-remedies-58320a794f1b

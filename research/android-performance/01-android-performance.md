# Android App Performance Engineering — Reference (2025)

Authoritative reference for the `android-performance-specialist` agent. Sourced primarily from
developer.android.com and the Android Developers blog. **Version-sensitive facts are flagged with ⚠️** —
Play Vitals thresholds, AGP/library minimums, and per-Android-version behaviour change over time and
must be re-verified against current docs before quoting to users.

---

## 1. App Startup

### Startup states (definitions + Play Vitals "excessive" TTID thresholds ⚠️)
| State | Definition | Excessive TTID threshold |
|-------|-----------|--------------------------|
| **Cold** | Process created from scratch — first launch after boot or after the app was killed. System creates process, Application object, main thread, launches activity, inflates + draws. | **≥ 5 s** |
| **Warm** | A subset of cold work; process may still be alive but the activity is recreated (`onCreate()` runs again). Can benefit from saved instance state. | **≥ 2 s** |
| **Hot** | Activity already in memory; system just brings it to the foreground. Lowest overhead but still shows a blank frame until drawn. | **≥ 1.5 s** |

Optimising **cold start** improves warm and hot automatically. Always test on a physical device with a
real cold start (force-stop the app or reboot).

### Key metrics
- **Time to Initial Display (TTID)** — time to the first drawn frame (process init + activity create + first draw).
  Reported automatically by the framework. Retrieve from Logcat `Displayed` line, e.g.
  `ActivityManager: Displayed com.example/.MainActivity: +3s534ms`, or via
  `adb shell am start -S -W <pkg>/<activity>`. Does **not** capture async content loaded after first frame.
- **Time to Full Display (TTFD)** — time until the app is fully usable including async content (network/disk).
  **The app must signal completion** by calling `reportFullyDrawn()`. Logcat: `Fully drawn <pkg>/.MainActivity: +1s54ms`.

### `reportFullyDrawn()` and friends
- Call `ComponentActivity.reportFullyDrawn()` once the meaningful content (including async data) is on screen.
- For content that loads asynchronously, use **`FullyDrawnReporter`** with `addReporter()` / `removeReporter()`
  around each background task — TTFD is reported when all reporters clear.
- **Jetpack Compose:** `ReportDrawn()` (immediately ready), `ReportDrawnWhen { predicate }` (conditional),
  `ReportDrawnAfter { suspendingWork() }`.

### What slows startup (and fixes)
- **Heavy `Application.onCreate()`** — initializing state for activities not being launched, GC churn (esp. Dalvik),
  concurrent disk I/O. Fix: lazy init, singletons created on first use, dependency injection (Hilt) to defer creation.
- **Content providers used for init** — replace with the **Jetpack App Startup library** (`androidx.startup`),
  which lets multiple components share a single content-provider entry point and sequence `Initializer` components.
- **Heavy `Activity.onCreate()`** — large/complex layout inflation, blocking I/O, bitmap decode, `VectorDrawable`
  rasterization. Fix: flatten the view hierarchy, use `ViewStub` for deferred sub-hierarchies, move resource loading off-main-thread.
- **Splash screens** — On Android 12+ (API 31) use the platform **`SplashScreen` API**; backport with the
  AndroidX `androidx.core:core-splashscreen` **compat library**. Do **not** use a dedicated splash Activity or the
  old `windowDisablePreview` hack. `windowSplashScreenAnimationDuration` controls animation length; the icon
  can be kept on screen while initial data loads.
- Diagnose with the CPU Profiler (`callApplicationOnCreate` → your `Application.onCreate`) and inline tracing;
  in Perfetto, use the "Android App Startups" derived-metric row.

---

## 2. Baseline Profiles, Macrobenchmark & Microbenchmark

### Baseline Profiles
Human-readable rule files (`baseline-prof.txt`) listing hot methods/classes. Compiled to
`assets/dexopt/baseline.prof` (max **1.5 MB**) and shipped in the APK/AAB. ART performs **AOT (ahead-of-time)
compilation** of these paths at install time, avoiding interpretation + JIT warm-up — this is Profile Guided
Optimization (PGO).
- **Improvement figures ⚠️** (Google's cited numbers): ~**30% faster** code execution / startup from first launch;
  an additional ~**15%** runtime gain with R8 profile rewriting (AGP 8.2+). Scroll/navigation performance also improves
  when those journeys are included.
- **Startup Profiles** (`startup-prof.txt`) are a companion that optimizes **DEX layout** (code placement) for
  startup-critical code, ~15% additional startup gain for large apps. Baseline Profiles are a superset of the rules.
- **Cloud Profiles** — Google Play aggregates real-usage profiles (Android 9 / API 28+) and distributes them hours-to-days
  after an update; scales only for large user bases. Baseline Profiles give the immediate, day-one benefit regardless of scale.
- **Compilation behaviour by version ⚠️:** API 21–23 full AOT at install (slow install); API 24–27 partial AOT with
  Baseline Profile on first run; API 28+ Baseline at install + Cloud added later.

**Generating them:**
- `BaselineProfileRule().collect(packageName) { … }` inside a Macrobenchmark test that drives the critical journeys
  (startup, navigation, scrolling) via UiAutomator.
- The **Baseline Profile Gradle plugin** automates it: `./gradlew :app:generateBaselineProfile`. It disables
  obfuscation during collection and rewrites rules for the release build.
- **Build config:** profile-generation variant must set `isMinifyEnabled = false` (rules must match unobfuscated
  signatures); release build uses `isMinifyEnabled = true` (R8 rewrites the rules to obfuscated names).
- **Minimum versions ⚠️:** AGP 8.0+ (app source-set support), AGP 8.2+ (R8 rewriting), AGP 8.3+ (library-provided
  profiles + desugared classes), Macrobenchmark 1.4.1+, ProfileInstaller 1.4.1+.

### Macrobenchmark
Jetpack library (`androidx.benchmark:benchmark-macro-junit4`) for **large use cases** — startup, scrolling, animations.
Runs from a separate `com.android.test` module; target app must be `<profileable android:shell="false"/>` and built
in a release-like, non-debuggable, minified **benchmark** variant.

```kotlin
@get:Rule val benchmarkRule = MacrobenchmarkRule()

@Test fun startup() = benchmarkRule.measureRepeated(
    packageName = TARGET_PACKAGE,
    metrics = listOf(StartupTimingMetric()),
    iterations = 10,
    startupMode = StartupMode.COLD,
    compilationMode = CompilationMode.DEFAULT,
) { uiAutomator { startApp(TARGET_PACKAGE) } }
```

- **Metrics:** `StartupTimingMetric` (launch time incl. TTID/TTFD), `FrameTimingMetric` (frame durations / jank while
  scrolling), `TraceSectionMetric` (custom `Trace` sections), plus power/memory metrics.
- **`CompilationMode`:** `DEFAULT` (uses Baseline Profile if present), `Full`, `Partial`, `None`, `Ignore`.
  Compare `None` vs `DEFAULT`/`Partial` to prove Baseline-Profile impact.
- **`StartupMode`:** `COLD` (kill process between iterations), `WARM`, `HOT`, or `null` (manual `killProcess()`).
- Outputs: console metrics, JSON in `build/outputs/connected_android_test_additional_output/…`, and
  `.perfetto-trace` files. **Run on physical devices, not emulators.**

### Microbenchmark
`androidx.benchmark:benchmark-junit4` — measures **small, hot code** (e.g. a parsing loop) with warmups, looped
iterations, and thermal/clock stabilization. Use for algorithm-level tuning where Macrobenchmark is too coarse.

---

## 3. Rendering & Jank

### Frame budget by refresh rate
| Refresh rate | Frame budget |
|--------------|--------------|
| 60 fps | **16 ms** (16.67) |
| 90 fps | **11 ms** |
| 120 fps | **8 ms** |

Overrunning the budget by even 1 ms causes `Choreographer` to **drop the whole frame** (not display it late).

### Frame classifications (Play Vitals ⚠️)
- **Slow / janky frame:** render time **16 ms – 700 ms** → visible stutter (abrupt scroll, choppy animation).
- **Frozen frame:** render time **700 ms – 5 s** (i.e. **> 700 ms**) → app looks stuck / unresponsive.
- **> 5 s** without input response crosses into ANR territory.
- Priority order for fixes: ANRs → frozen frames → slow frames.
- **Vitals caveat:** frame render statistics are **not** collected for apps rendering via **Vulkan, OpenGL
  (without the View system), Unity, or Unreal** — only Canvas/View-hierarchy rendering is measured.

### Rendering pipeline
1. **UI thread** — `Choreographer#doFrame`: measure/layout pass, then `Record View#draw` (`draw(Canvas)` on invalidated views).
2. **RenderThread** — `DrawFrame`: GPU rendering, texture uploads.

### Overdraw
Pixels drawn multiple times per frame waste GPU. Reduce with "Debug GPU Overdraw" (Developer Options), removing
redundant backgrounds, flattening layouts, and clipping. Avoid `RelativeLayout`/weighted `LinearLayout` nesting.

### JankStats library
`androidx.metrics:metrics-performance` — the first AndroidX library built to capture **per-frame** timing on **real
user devices** (not just dev) and report it.
- **Jank heuristic:** by default a frame is "jank" if it takes **≥ 2× the current refresh interval**. Tune with the
  **`jankHeuristicMultiplier`** property (default 2.0).
- **`PerformanceMetricsState`** API — attach app UI-state key/value pairs (e.g. "screen: feed") so `FrameData`
  reports for a janky frame include *what the app was doing*. Wire the aggregated `FrameData` to your analytics.

### Other tools
- **`FrameTimingMetric`** (Macrobenchmark) for lab measurement; **Perfetto FrameTimeline** to see slow/frozen frames;
  legacy "Profile GPU Rendering" bar overlay (16 ms line).
- Compose-specific jank comes largely from **excessive recomposition** and unstable parameters — see the Compose
  performance reference (cross-ref). Use `LazyColumn` keys, stable types, `@Immutable`/`@Stable`, and
  `derivedStateOf`; measure with `FrameTimingMetric` + a Baseline Profile.

---

## 4. ANRs (Application Not Responding)

### Triggers and timeouts ⚠️
| Trigger | Timeout |
|---------|---------|
| **Input dispatching timed out** (no response to key/touch) — the *user-perceived* ANR type | **5 s** |
| `BroadcastReceiver.onReceive()` not finished (foreground broadcast) | **5 s** (background broadcasts have a longer window) |
| `Service.onCreate`/`onStartCommand`/`onBind` not finished | a few seconds |
| `Context.startForegroundService()` then no `startForeground()` call | **5 s** |
| `JobService.onStartJob`/`onStopJob` not returning; user-initiated job without `setNotification()` | a few seconds (silent on Android ≤13; explicit on Android 14+) |

### Play Vitals ANR metrics & thresholds ⚠️
- **User-perceived ANR rate** (currently only the "Input dispatching timed out" type) is a **Core Vital** affecting
  Play discoverability.
- **Overall bad-behaviour threshold: ≥ 0.47%** of daily active users hitting a user-perceived ANR → less discoverable everywhere.
- **Per-device threshold: ≥ 8%** of daily users on a single device model → less discoverable on that model + store-listing warning.
- Also tracked: overall ANR rate (any type) and multiple-ANR rate (≥ 2 ANRs).

### Common causes
Main-thread I/O (network/disk), long computation on main thread, slow synchronous binder calls, main thread waiting on
a lock held by a worker thread, deadlocks, lock contention, slow `BroadcastReceiver.onReceive()`.

### Diagnosis
- **Play Console → Android vitals → ANRs** for field data.
- **`ApplicationExitInfo`** (API 30+) — `getHistoricalProcessExitReasons()` gives the exit reason
  (`REASON_ANR`, low memory, crash, excessive CPU, etc.) plus a trace for ANRs.
- ANR trace files: `/data/anr/anr_*` (older: `/data/anr/traces.txt`), pull via `adb`.
- **StrictMode** in dev to catch accidental main-thread disk/network I/O; CPU profiler / Perfetto to see whether the
  main thread is `RUNNABLE` vs `BLOCKED`/`MONITOR`.

### Fixes
Move work to worker threads (Coroutines/`ExecutorService`/`WorkManager`); for broadcasts use `goAsync()` (and always
call `PendingResult.finish()`) or hand off to `WorkManager`; minimize lock hold times; eliminate deadlocks; for C/C++
games use `GameActivity` to reduce UI-thread blocking.

---

## 5. Memory

### Managed heap & GC
- Generational, mmapped heap (ART/Dalvik): young → older → permanent generations, each with an upper limit; GC runs
  when a generation fills. A GC pause during animation can push a frame past **16 ms** → jank.
- **The only way to free memory is to drop references** so the GC can reclaim them.
- Per-app heap cap is device-defined (based on RAM); query with `ActivityManager.getMemoryClass()` (MB). Exceeding it
  throws **`OutOfMemoryError`**. Dalvik does not compact the heap; unused pages are returned to the kernel via `madvise()`.
- **PSS (Proportional Set Size)** is the fair-share physical footprint (shared pages counted proportionally). Memory is
  shared via the **Zygote** fork and mmapped `.odex`/resources/`.so` files.

### Memory leaks — LeakCanary
Square's `com.squareup.leakcanary:leakcanary-android` (LeakCanary 2 — full rewrite, ~10× less memory via the **Shark**
heap parser). Hooks the Activity/Fragment/ViewModel lifecycle; destroyed objects are handed to an **`ObjectWatcher`**
holding weak references.
- **Retained-object thresholds:** dumps the heap when **≥ 5** retained objects while the app is **visible**, or **≥ 1**
  when **not visible**. Writes an `.hprof`, parses it with Shark, and reports the **leak trace** (shortest strong
  reference path keeping the object alive).

### OOM / Low Memory Killer
- **Low Memory Killer (LMK):** when RAM is low the system kills cached background processes first, prioritizing those
  holding the most memory — so a smaller cached footprint improves survival and fast resume.
- Detect field kills/OOM via **`ApplicationExitInfo`** (`REASON_LOW_MEMORY`, `REASON_SIGNALED`, etc.).
- **`onTrimMemory(level)`** (and `ComponentCallbacks2`) signals memory pressure — release caches/bitmaps on
  `TRIM_MEMORY_RUNNING_LOW`, `TRIM_MEMORY_UI_HIDDEN`, `TRIM_MEMORY_COMPLETE`, etc. Available since API 16.

### Bitmaps & tools
- Bitmaps are usually the largest allocations — decode at the required sample size (`inSampleSize`), reuse via
  bitmap pools, use hardware bitmaps / `ImageDecoder`, prefer WebP.
- **Android Studio Memory Profiler** — live memory graph correlated with lifecycle/GC events; capture **heap dumps**
  and record **native/Java allocations** to find growth and leaks.
- Background apps get tighter memory limits; keeping cached footprint low avoids LMK termination.

---

## 6. Profiling & Tracing Tools

- **Android Studio Profiler** — CPU, Memory, Energy, and Network profilers. CPU profiler records method/function traces
  and system traces; Memory profiler captures heap dumps + allocation tracking.
- **Perfetto** (recommended, Android 10+) — platform-wide, open-source tracing; records arbitrarily long traces as
  protobuf; viewed in **ui.perfetto.dev**. Superset of the legacy Systrace data sources; `traceconv` converts formats.
- **Systrace** (legacy, all versions) — CLI capturing kernel scheduler/disk/thread activity; openable in Perfetto UI.
- **Custom trace events:** `Trace.beginSection(name)` / `Trace.endSection()` (synchronous) and
  `Trace.beginAsyncSection`/`endAsyncSection` (async) in Java/Kotlin; equivalent `ATrace_beginSection` in native code.
  These sections appear in Perfetto/Systrace and can be measured by Macrobenchmark's `TraceSectionMetric`.
  Note: system tracing shows *where* time goes but not intra-method detail — use the CPU profiler for that.
- **simpleperf** (NDK) — native CPU sampling profiler (`simpleperf record`/`report`, or the `app_profiler` helper script), samples at
  a set frequency and reads hardware perf counters; profiles **both Java and C/C++** code and native processes.

---

## 7. Play Vitals & Field Data

**Android vitals** (Play Console) aggregates field quality data. Two metrics are **Core Vitals** that gate store
discoverability, each with an **overall** and a **per-device** bad-behaviour threshold ⚠️:

| Core Vital | Overall bad-behaviour threshold | Per-device threshold |
|------------|--------------------------------|----------------------|
| **User-perceived crash rate** | **≥ 1.09%** of daily users | **≥ 8%** on a single model |
| **User-perceived ANR rate** | **≥ 0.47%** of daily users | **≥ 8%** on a single model |

Exceeding **overall** → less discoverable on all devices; exceeding **per-device** → less discoverable on those models
plus a possible store-listing warning.

Other tracked vitals: **excessive wake locks** (see §9), **excessive wakeups**, **slow rendering** (16–700 ms frames),
**frozen frames** (> 700 ms), stuck partial wake locks, excessive background Wi-Fi/network usage. A "daily active user"
= one user on one device on one day (multi-device users count once per device).

- **`FirebasePerformance`** (Firebase Performance Monitoring) — SDK for custom traces, automatic screen-render/HTTP
  network metrics, and app-start traces from real users; complements Play vitals with your own custom traces.
- **`ApplicationExitInfo`** (API 30+) — programmatic access to the last exit reasons (ANR/crash/OOM/user-stop), useful
  for your own field telemetry.

---

## 8. App Size

- **Android App Bundle (AAB)** is the required publishing format; Play generates optimized split APKs per device
  (density / language / ABI **configuration splits**) so users download only what they need. **Download-size limits ⚠️:**
  AAB ≈ **200 MB** compressed base; legacy signed APK ≈ **100 MB** (larger via asset packs / Play Asset Delivery).
- **Download vs install size** — download is the compressed per-device delivery; install is uncompressed on-device.
- **R8** (`isMinifyEnabled = true`) — code shrinking, optimization, and obfuscation; removes unused code. Enables enum→int
  conversion (~1–1.4 KB saved per enum; prefer `@IntDef`).
- **Resource shrinking** — `isShrinkResources = true` (requires `minifyEnabled`) strips unused resources after R8;
  `lint` flags unused resources for manual removal. Restrict configs with `resourceConfigurations`.
- **Assets** — convert PNG/JPEG to **WebP**; use **vector drawables** for icons; use `AnimatedVectorDrawable` over
  frame-by-frame `AnimationDrawable`; strip native debug symbols; `useLegacyPackaging = false` to keep `.so` files uncompressed.
- **bundletool** — build APKs from an AAB and estimate per-device download sizes
  (`bundletool build-apks` + `get-size total`). **Split APKs** (`splits { density/language/abi }`) only for non-Play distribution.
- **Play Console → App size** report shows download/install size and the largest components over time.

---

## 9. Battery / Energy

### Doze & App Standby buckets ⚠️
When screen-off + unplugged, the device enters **Doze**: regular jobs and inexact alarms are deferred to maintenance
windows; **while-idle alarms are capped at 7/hour**; network is restricted; normal-priority FCM deferred, high-priority
FCM allowed.

**App Standby buckets** (assigned by usage; higher = fewer restrictions):
| Bucket | Regular jobs | Alarms | Network |
|--------|-------------|--------|---------|
| **Active** | ~20 min / 60 min | no limit | unrestricted |
| **Working set** | ~10 min / 4 h | 10/hour | unrestricted |
| **Frequent** | ~10 min / 12 h | 2/hour | unrestricted |
| **Rare** | ~10 min / 24 h | 1/hour | disabled (deferred) |
| **Restricted** | once/day, ≤10 min | 1/day | disabled |

(Expedited-job quotas are separate; several limits changed in **Android 16**. Manual user "Restricted"/"Unrestricted"
settings override bucket limits.)

### Wake locks — excessive partial wake lock vital ⚠️
- **Excessive partial wake lock threshold: ≥ 2 cumulative hours** of partial wake locks in a rolling **24-hour** period,
  counted only while the app is in the **background** or running a **foreground service**.
- **Store-visibility impact:** if this occurs in **> 5% of app sessions** across all devices over a **28-day** window,
  Play visibility can be affected. Excessive *partial wake locks* affect store visibility **starting March 1, 2026** ⚠️.
- **Exemptions:** wake locks from **audio playback, location, and JobScheduler** APIs are exempt (clear user benefit).
- Best practice: always release every wake lock ASAP; audit third-party libraries for hidden wake locks; debug locally.

### Deferrable work
- **WorkManager** is the recommended API for deferrable/guaranteed background work; it uses **JobScheduler** under the
  hood and is subject to standby-bucket job quotas. Use `Constraints` (charging, network, idle) to batch work efficiently.
- Use `AlarmManager` only for exact user-facing alarms; use FCM high-priority sparingly.
- **Excessive wakeups** vital tracks apps waking the device too often via alarms — batch alarms and defer via WorkManager.

---

## Cross-references
- **Jetpack Compose performance** (recomposition, stability, `LazyColumn` keys) — see the Compose reference; jank in
  Compose apps is measured with the same `FrameTimingMetric` / JankStats / Baseline Profile tooling above.

---

## Sources
- App startup performance & TTID/TTFD — https://developer.android.com/topic/performance/vitals/launch-time
- App Startup library — https://developer.android.com/topic/libraries/app-startup
- Splash screen API — https://developer.android.com/develop/ui/views/launch/splash-screen
- Baseline Profiles overview — https://developer.android.com/topic/performance/baselineprofiles/overview
- Macrobenchmark overview — https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview
- Microbenchmark overview — https://developer.android.com/topic/performance/benchmarking/microbenchmark-overview
- Rendering / jank (slow & frozen frames) — https://developer.android.com/topic/performance/vitals/render
- JankStats library — https://developer.android.com/topic/performance/jankstats
- ANRs — https://developer.android.com/topic/performance/vitals/anr
- Memory allocation & GC overview — https://developer.android.com/topic/performance/memory-overview
- Manage your app's memory — https://developer.android.com/topic/performance/memory
- LeakCanary (how it works) — https://square.github.io/leakcanary/fundamentals-how-leakcanary-works/
- ApplicationExitInfo — https://developer.android.com/reference/android/app/ApplicationExitInfo
- System tracing / Perfetto — https://developer.android.com/topic/performance/tracing
- simpleperf (NDK) — https://developer.android.com/ndk/guides/simpleperf
- Android vitals overview — https://developer.android.com/topic/performance/vitals
- Monitor technical quality with Android vitals (Play Console Help) — https://support.google.com/googleplay/android-developer/answer/9844486
- Raising the bar on technical quality on Google Play (blog; crash 1.09% / ANR 0.47% thresholds) — https://android-developers.googleblog.com/2022/10/raising-bar-on-technical-quality-on-google-play.html
- Excessive partial wake locks vital — https://developer.android.com/topic/performance/vitals/wakelock
- Power / standby-bucket & Doze limits — https://developer.android.com/topic/performance/power/power-details
- Reduce app size — https://developer.android.com/topic/performance/reduce-apk-size
- App Bundle / configuration splits — https://developer.android.com/guide/app-bundle
- WorkManager — https://developer.android.com/develop/background-work/background-tasks/persistent

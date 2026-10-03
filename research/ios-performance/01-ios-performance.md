# iOS App Performance Optimization & Diagnostics — Reference (2025/2026)

Authoritative reference for the `ios-performance-specialist` agent. Prefers official
Apple sources (Instruments, MetricKit, WWDC performance sessions, Xcode docs).
Tooling baseline: **Xcode 26 / Instruments 27** (WWDC25), iOS 18/26, with historical
WWDC context where the concept originated. All numeric targets are Apple's stated
figures unless noted.

---

## 0. Golden numbers (memorize these)

| Target | Value | Source |
|---|---|---|
| First-frame launch budget | **~400 ms** | WWDC19 "Optimizing App Launch" |
| Frame budget @ 60 Hz | **~16.67 ms** | Render loop |
| Frame budget @ 120 Hz ProMotion | **~8.33 ms** | Render loop |
| Hang threshold (default reporting) | **250 ms** | WWDC22/23 hangs |
| "Feels instant" ceiling | **~100 ms** of main-thread work | WWDC23 |
| Micro-hang | **< ~250–400 ms** | WWDC22/23 |
| Memory page size | **16 KB** | WWDC18 Memory Deep Dive |
| Max uncompressed app size | **4 GB** | App Store Connect |
| Max Mach-O `__TEXT` sections | **500 MB** | App Store Connect |
| Cellular over-the-air download limit | **~200 MB** (raised from 150 MB in 2022) | App Store |
| Decoded image cost | `width × height × bytes-per-pixel` (sRGB = 4 B/px), **not** file size | WWDC18 |

**First rule of the specialist:** *Measure, don't estimate.* Profile **release** builds
on **real devices** (Simulator uses Mac CPU/GPU/memory and lies about performance).

---

## 1. Instruments — the toolbox

Instruments is Xcode's tracing/profiling app. Launch via **Product ▸ Profile (⌘I)** or
from the Debug navigator's "Profile in Instruments" action. You pick a **template**
(a bundle of one or more instrument tracks). Traces are recorded, then inspected in the
timeline + detail/call-tree panes.

### Time Profiler (CPU / sampling)
- **What it does:** low-overhead *statistical sampler*. Periodically captures the call
  stack of every thread and attributes time to functions by sample count.
- **Diagnoses:** CPU hot spots, expensive functions, main-thread work causing hangs/hitches.
- **Interpretation:** use the **call tree**; enable **"Invert Call Tree"** to see leaf
  (self-time) functions first, **"Hide System Libraries"** / **"Separate by Thread"** to
  focus on your code. Heaviest self-weight = optimize first.
- **Key limitation:** a sampler cannot tell *one long call* from *many short calls* of the
  same function — pair with the SwiftUI instrument or `os_signpost` intervals to
  disambiguate frequency vs. duration.

### Allocations (memory)
- **What it does:** tracks every heap allocation, live vs. transient objects, allocation
  call stacks, growth over time.
- **Diagnoses:** memory growth, transient allocation spikes, abandoned memory (allocated,
  still referenced, never used again).
- **Interpretation:** use **Generation marks (Mark Generation)** — mark, do an action,
  mark again; "Generation N" shows what survived that cycle → steadily-growing generations
  reveal abandoned memory / unbounded caches. **"Persistent Bytes"** column = still live.

### Leaks (memory)
- **What it does:** periodically scans the heap for blocks with **no references** (true
  leaks / retain cycles the ARC graph can't reach).
- **Diagnoses:** classic leaks, retain cycles.
- **Interpretation:** red leak marks in timeline; each leaked block shows its allocation
  backtrace and a cycle graph. Note: Leaks finds *unreferenced* memory; **abandoned**
  memory (still referenced but useless) is invisible to Leaks — use Allocations
  generations or the Memory Graph Debugger for that.

### Hangs / main-thread stalls
- Modern Instruments (Xcode 14+) surfaces **hangs directly in the Time Profiler / CPU
  Profiler timeline** as flagged regions, plus a dedicated hang analysis workflow
  (WWDC23 "Analyze hangs with Instruments"). See §3 for the hang model.

### Core Animation / Animation Hitches (rendering & FPS)
- **What it does:** measures render-server commit/GPU time and frame delivery; the
  **Animation Hitches** instrument reports hitch time and hitch ratio.
- **On-device debug color overlays** (Xcode Debug ▸ View Debugging, or Simulator Debug menu):
  - **Color Blended Layers** — green→red; red = expensive alpha blending / overdraw (opaque
    views with `alpha < 1` or non-opaque backgrounds). Fix: set `isOpaque = true`, solid
    backgrounds.
  - **Color Offscreen-Rendered Yellow** — layers forced into offscreen passes (shadows,
    masks, `cornerRadius` + `masksToBounds`, `shouldRasterize`). Fix: use `shadowPath`,
    pre-rendered images, avoid unnecessary masking.
  - **Flash Updated Regions** — flashes redrawn areas; large/frequent flashes = wasteful redraw.
  - **Color Hits Green and Misses Red** — for `shouldRasterize`; red = cache misses being
    regenerated each frame (rasterization is hurting, not helping).

### System Trace
- **What it does:** deep OS-level view — thread states, scheduling, VM faults, system calls,
  memory transitions.
- **Diagnoses:** blocked threads, priority inversions, page faults, lock contention,
  context-switch storms. Thread-state color key: **blue = running, red = runnable
  (waiting for CPU), orange = preempted, gray = blocked**.

### Network
- TCP/UDP connection analysis, request timing, throughput. Diagnoses chatty networking,
  redundant requests, connections kept alive too long (also an energy cost).

### Energy Log / Energy Diagnostics
- Energy components: **CPU, GPU, networking, location, display/brightness, Bluetooth**.
  See §5.

### os_signpost / Points of Interest
- **`os_signpost`** (from `os.log` / `OSLog`) lets you mark **intervals** (`.begin`/`.end`)
  and **events** in your own code; they appear in the **Points of Interest** instrument and
  can be measured by `XCTOSSignpostMetric` in tests. Use them to name and time your own
  phases (e.g. "DataLoad", "ImageDecode") so sampled traces become interpretable.
  Signposts are near-zero overhead when not being recorded.

### SwiftUI instrument (view body / update tracking) — *next-gen in Xcode 26*
- Tracks (WWDC25 "Optimize SwiftUI performance with Instruments"):
  - **Update Groups** — when SwiftUI is actively processing an update pass.
  - **Long View Body Updates** — `body` evaluations exceeding safe thresholds
    (color-coded orange/red by hitch risk).
  - **Long Representable Updates** — slow `UIViewRepresentable`/`NSViewRepresentable` bridges.
  - **Other Long Updates** — remaining anomalies.
  - **Cause & Effect graph** — traces interaction → state change → which view bodies
    re-evaluated, exposing over-broad dependencies.
- See §3 for SwiftUI remedies.

### Swift Concurrency / Swift Executors instrument
- Visualizes tasks, actors, continuations, and executor queues (WWDC22 "Visualize and
  optimize Swift concurrency"). Diagnoses **actor congestion** (tasks queued behind a busy
  actor), continuation stalls, thread-pool starvation, and concurrency-related hangs.
  Instruments 27 adds a **Swift Executors** instrument for concurrency responsibility.

### Xcode 26 / Instruments 27 additions (WWDC25)
- **Processor Trace** — captures *every* CPU branch for high-fidelity analysis
  (M4 / iPhone 16 class hardware).
- **CPU Counters** — preset modes for microarchitecture bottleneck analysis.
- Overhauled power/thermal and UI-state-flow tooling; new SwiftUI + Swift Executors instruments.

---

## 2. App launch

### The six launch phases (WWDC19 "Optimizing App Launch")
1. **System Interface / dyld** — dynamic linker maps the executable + shared libraries.
   (`dyld3` caching, from iOS 13, made warm launches ~2× faster; ~6 ms in good cases.)
2. **libSystem init** — low-level runtime bring-up (mostly fixed OS cost).
3. **Static runtime initialization** — Obj-C/Swift runtime setup; **static initializers,
   `+load` methods, and `__attribute__((constructor))`** run here and can silently add
   hundreds of ms.
4. **UIKit initialization** — `UIApplication` + delegate instantiated (~28 ms typical).
5. **Application initialization** — *your* `application(_:didFinishLaunchingWithOptions:)`
   / `UIScene` callbacks. **Biggest developer lever.**
6. **First frame render** — build views, layout, draw, commit initial frame.
7. **(Extended phase)** — optional async data load until first *useful* content.

Budget split: **~100 ms system + ~300 ms your work = ~400 ms** to first frame. The first
frame may contain placeholders; app should be interactive by 400 ms.

### What slows launch
- Too many / unused **dynamically-linked frameworks** (hidden dyld cost) → hard-link,
  merge, or drop unused ones.
- **Static initializers** and heavy `+load`.
- Heavy synchronous work in `didFinishLaunching` — **network/file I/O on the main thread**,
  eager loading of all data (load only what the first frame needs; lazy-load the rest).
- **Priority inversions** (background QoS work blocking the main thread — WWDC demo showed
  754 ms of blockage). Propagate priority with `dispatch_sync`, not async+semaphore.

### Launch types
- **Cold** — after reboot / long idle; process spawned, pages faulted from disk. Slowest, noisiest.
- **Warm** — process gone but pages still cached; more consistent → **use for measurement**.
- **Resume** — app suspended, not a launch; don't count it.
- **Pre-warming** (iOS 15+) — the system may partially launch the app ahead of tap; skews
  naive timers, so prefer MetricKit/`XCTApplicationLaunchMetric` which account for it.

### Measuring launch
- **`DYLD_PRINT_STATISTICS = 1`** (Scheme ▸ Run ▸ Arguments ▸ Environment) prints pre-main
  (dyld) time to console. `DYLD_PRINT_STATISTICS_DETAILS` for a breakdown.
- **Instruments "App Launch" template** — auto-launches, shows all phases on a timeline with
  thread states + stacks.
- **`os_signpost`** around extended-phase work to time it precisely.
- **`XCTApplicationLaunchMetric()`** in an XCUITest (throwaway launch + 5 iterations).
- **MetricKit `MXAppLaunchMetric`** (histogram) and **Xcode Organizer ▸ Launch Time** for
  real-user field data.

---

## 3. Rendering & responsiveness

### The render loop (WWDC21 "Avoid hitches and discover the render loop")
Per display refresh the pipeline runs: **Event → Commit (app: layout, display, prepare,
commit the layer tree to the render server) → Render Prepare (GPU) → Render Execute (GPU)
→ Display**. Work is pipelined across frames; each stage has a deadline.

### Frame budget
- 60 Hz → **16.67 ms/frame**; 120 Hz ProMotion → **8.33 ms/frame** (roughly half — a
  ProMotion device has *less* slack, and variable refresh rate changes the target).

### Hitches
- A **hitch** = a frame shown *later than expected* (missed a commit or render deadline).
- **Hitch time** = ms a frame was late. **Hitch ratio** = ms of hitch per second of
  content (ms/s); higher = worse. ~**10 ms/s** or more is distracting.
- Causes: heavy layout during commit; **overdraw / blending**; **offscreen passes**
  (shadows without `shadowPath`, masks, rounded corners); oversized images; GPU-bound
  effects; too much main-thread work stealing commit time.
- Track with the **Animation Hitches** / Core Animation instrument, and in tests with
  **`XCTHitchMetric`** / `XCTOSSignpostMetric.applicationLaunch`. Field data via
  **MetricKit `MXAnimationHitchTimeMetric`** and Organizer.

### Hangs (WWDC22 "Track down hangs"; WWDC23 "Analyze hangs with Instruments")
- **Hang** = UI unresponsive; default reporting threshold **250 ms**. **≤100 ms** main-thread
  work "feels instant"; **micro-hang** ≈ under ~250–400 ms (accumulate; still worth fixing,
  and larger screens/older devices amplify them).
- **Three hang types:**
  1. **Busy main thread** — main thread doing prolonged CPU work (high CPU). Fix: reduce or
     move work off-main; reduce frequency.
  2. **Blocked main thread** — main thread waiting (low CPU) on a lock / sync I/O / a
     background result. Fix: remove the synchronous wait; don't `dispatch_sync` to slow work.
  3. **Asynchronous / deferred hang** — a main-thread work item queued too long. Fix: move to
     background via Swift Concurrency, right-size QoS.
- **Diagnostic flow:** record Time Profiler capturing the hang → select the flagged hang
  interval → invert/filter to your code → decide *one slow call vs. many calls* (add SwiftUI
  instrument or signposts) → fix (lazy load, background compute, concurrency).

### Off-main-thread strategy
Keep the main thread for UI only. Move parsing, image decode, disk/network I/O, and heavy
computation to background queues / `Task`s with appropriate QoS; hop back to the main actor
only to mutate UI.

### SwiftUI recomputation pitfalls & remedies
- **Expensive `body`** (formatters, sorting, date math built inside `body`) → precompute /
  cache outside `body`.
- **Over-broad dependencies** (a view observing a whole array/collection re-renders on any
  element change) → granular state / per-item view models; observe the narrowest slice.
- **Environment for frequently-changing values** → propagation tax across subscribers; avoid.
- **`AnyView`** and non-stable `ForEach` identity → defeat structural diffing; use stable,
  `Identifiable` IDs and concrete view types.
- Use the **SwiftUI instrument's Cause & Effect graph** to find who re-rendered and why.

### List / scroll & image performance
- Reuse cells (`UITableView`/`UICollectionView` dequeue; SwiftUI `List`/`LazyVStack`).
- **Downsample images to display size** before use (see §4) — decoding full-res images on
  the main thread during scroll is a top hitch cause.
- Avoid synchronous decode on scroll; prefer async decode / prepared thumbnails.

---

## 4. Memory (WWDC18 "iOS Memory Deep Dive", WWDC24 "Analyze heap memory")

### Footprint model
- Memory is paged in **16 KB** pages, classified **Clean** (page-outable: framework code,
  read-only consts, `mmap`-ed files), **Dirty** (non-evictable: malloc heap, decoded image
  buffers, ivars), and **Compressed** (inactive dirty pages squeezed by the memory
  compressor, iOS 7+).
- **Footprint ≈ (Dirty + Compressed) pages** — not virtual address space, not file size.
- Gotcha: compression means `cache.removeAllObjects()` may *decompress* pages (temporary
  spike) before freeing.

### Retain cycles, leaks, abandoned memory
- **Memory Graph Debugger** (Debug bar ▸ memory graph icon): snapshots all live allocations
  + references; exports `.memgraph`; surfaces retain cycles (`!` markers) and shows the
  reference chain keeping an object alive. Command-line: `vmmap`, `leaks`, `heap`,
  `malloc_history` on a `.memgraph` or live process; enable **Malloc Stack Logging** in the
  scheme's Diagnostics tab for allocation backtraces.
- **Retain cycle** → break with `weak`/`unowned` (delegates, closures capturing `self`).
- **Abandoned memory** = still referenced but never used again (unbounded caches, retained
  view controllers) → find with Allocations **generation marks**.

### Jetsam / memory-pressure termination
- iOS has no swap-to-disk for apps; under pressure the kernel **jetsams** (kills) the
  highest-footprint / lowest-priority processes. Foreground apps get more headroom than
  extensions/background.
- **Per-app limits vary widely by device RAM** (approximate jetsam ceilings): iPhone SE-class
  (3 GB RAM) ≈ **~900 MB–1.4 GB**; modern Pro (8 GB RAM) ≈ **~3–4 GB**. Extensions get far
  less (tens–low-hundreds of MB). Exceeding triggers `EXC_RESOURCE`/jetsam. **Don't hardcode
  a limit — respond to pressure.**
- Handle `applicationDidReceiveMemoryWarning` / `.didReceiveMemoryWarningNotification`; drop
  caches, purge offscreen resources.

### Image / asset memory
- **Decoded cost = width × height × bytes-per-pixel**, independent of compressed file size.
  A 2048×1536 JPEG (~590 KB on disk) = ~**10 MB** decoded at 4 B/px (sRGB).
- Bytes-per-pixel by format: **sRGB = 4**, **Wide gamut = 8**, **Luminance+Alpha = 2**,
  **Alpha-8 (masks/text) = 1**.
- **Downsample with ImageIO** (`CGImageSourceCreateThumbnailAtIndex` with
  `kCGImageSourceThumbnailMaxPixelSize`) — decodes directly to target size, avoiding a
  full-res dirty buffer.
- Prefer `UIGraphicsImageRenderer` over `UIGraphicsBeginImageContextWithOptions` (picks an
  optimal pixel format automatically).

### autoreleasepool
- Wrap tight loops that create many autoreleased temporaries (e.g. image processing over
  thousands of items) in `autoreleasepool { }` to cap peak footprint — otherwise temporaries
  accumulate until the run loop drains the pool.

---

## 5. Energy & battery

### Tools
- **Energy Impact gauge** — Xcode Debug navigator, live high-level view while running.
- **Energy Log / Energy Diagnostics template** in Instruments — components: **CPU, GPU,
  networking, location, display/brightness, Bluetooth**; an Energy Usage level scale
  (0–20; occasional spikes are fine, watch for *sustained* high usage).
- **On-device Energy logging:** Settings ▸ Developer ▸ Logging (or Instruments' logging
  profile) → record untethered → **File ▸ Import Logged Data from Device**. (Data lost if
  the battery fully drains.)
- **Location Energy** instrument — measures Core Location request cost/duration.
- Field data: **MetricKit `MXBatteryMetric`, `MXCPUMetric`, location-activity metrics**.

### What drains battery / causes App Review rejection (Guideline 2.x performance)
- **Continuous high-accuracy location** (`kCLLocationAccuracyBest`) in background — one WWDC
  example: ~847 mAh over 2 h. Use **significant-location-change** / **region monitoring** /
  a coarser accuracy (`kCLLocationAccuracyKilometer`) when precision isn't needed.
- Excessive **background execution** / undeclared or unnecessary **background modes** in
  `Info.plist` (Apple rejects apps that keep the device awake or run background work without
  genuine need).
- **Frequent wake-ups / timers**, chatty networking, keeping radios/connections alive, busy
  polling, runaway CPU.
- **Fixes:** batch and defer discretionary work (use `URLSession` background/discretionary,
  `BGTaskScheduler`); coalesce timers; do heavy work while plugged in / on Wi-Fi; only
  request the background modes you truly use.

---

## 6. MetricKit — real-user field metrics & diagnostics

`import MetricKit`. Subscribe a `MXMetricManagerSubscriber` to `MXMetricManager.shared`.

```swift
final class MetricsSubscriber: NSObject, MXMetricManagerSubscriber {
    override init() { super.init(); MXMetricManager.shared.add(self) }
    deinit { MXMetricManager.shared.remove(self) }
    func didReceive(_ payloads: [MXMetricPayload]) { /* aggregated, ~daily */ }
    func didReceive(_ payloads: [MXDiagnosticPayload]) { /* crash/hang/etc. */ } // iOS 14+
}
```

- **Delivery:** `MXMetricPayload` arrives aggregated ~**every 24 h** (privacy-preserving,
  on-device, no SDK). `MXDiagnosticPayload` (iOS 14+) delivered on next launch after the
  event.

### Metrics (`MXMetricPayload` sub-metrics)
- **`MXAppLaunchMetric`** — launch & resume times (histograms; includes time-to-first-draw).
- **`MXHangMetric`** — cumulative hang time (`histogrammedApplicationHangTime`).
- **`MXAnimationHitchTimeMetric` / hitch metrics** — scroll/animation hitch time ratios.
- **`MXMemoryMetric`** — peak & average suspended memory.
- **`MXCPUMetric`** — cumulative CPU time.
- **`MXDiskIOMetric`** — logical disk writes.
- **`MXBatteryMetric`** — cumulative battery drain.
- Plus network transfer, GPU, display (avg pixel luminance), location activity, cellular
  condition metrics. Distributions are represented as **`MXHistogram`** (bucketed).

### Diagnostics (`MXDiagnosticPayload`, iOS 14+) — with call-stack trees (`MXCallStackTree`)
- **`MXCrashDiagnostic`** — crashes (termination reason, exception, signal).
- **`MXHangDiagnostic`** — hang duration + stack.
- **`MXCPUExceptionDiagnostic`** — CPU-usage threshold violations.
- **`MXDiskWriteExceptionDiagnostic`** — excessive disk writes.
- (iOS 16+) app-launch / `MXAppLaunchDiagnostic` for slow launches.

### Xcode Organizer
- **Organizer ▸ Metrics** shows the same field data (Launch, Hang Rate, Disk Writes, Memory,
  Battery, Terminations) aggregated across opted-in users, sliced by app version & device.
  Xcode 26 adds **Trending Insights** charting Hang/Launch regressions across versions.

---

## 7. App size & app thinning

### App Thinning = Slicing + On-Demand Resources (Bitcode is gone)
- **Slicing** — App Store builds device-specific **variants**, delivering only the
  architecture + asset-catalog resources (e.g. correct `@2x`/`@3x`, correct GPU texture set)
  for the user's device. Requires assets in **asset catalogs** to work.
- **On-Demand Resources (ODR)** — tag assets (levels, tutorial media) downloaded on demand
  and purgeable, shrinking initial download.
- **Bitcode** — **deprecated in Xcode 14, removed** in current Xcode; no longer submit or
  rely on it.

### Limits (App Store Connect)
- **Total uncompressed app ≤ 4 GB.**
- **Each Mach-O executable's total `__TEXT` sections ≤ 500 MB.**
- **Cellular download limit ≈ 200 MB** (raised from 150 MB in 2022); above it, users on
  cellular are prompted to switch to Wi-Fi → hurts install-conversion.

### Measuring size — the App Thinning Size Report
- Archive ▸ **Distribute/Export ▸ "All compatible device variants"** → output contains
  **`App Thinning Size Report.txt`** listing **compressed (download) vs. uncompressed
  (install)** size **per device variant**, plus ODR size.
- App Store Connect also reports per-device download/install sizes after processing.
- Reduce size: strip unused frameworks/dead code, compress/right-size assets, adopt asset
  catalogs (enables slicing + optimized formats like HEIC/ASTC), ODR for optional content,
  merge dynamic frameworks, enable dead-code stripping & Swift `-Osize` where appropriate.

---

## 8. Measurement discipline

### XCTest performance tests
```swift
func testScrollPerf() {
    measure(metrics: [XCTClockMetric(), XCTCPUMetric(), XCTMemoryMetric()]) {
        // code under test
    }
}
```
- **`measure { }`** runs the block **multiple times (default ~5–10 iterations)**, reports
  average + standard deviation, and compares against a stored **baseline**; a regression
  beyond the baseline's tolerance **fails the test** (regression gating in CI).
- **Metrics:**
  - **`XCTClockMetric`** — wall-clock time.
  - **`XCTCPUMetric`** — CPU time / instructions.
  - **`XCTMemoryMetric`** — physical memory growth (peak).
  - **`XCTStorageMetric`** — logical disk writes.
  - **`XCTOSSignpostMetric`** — measures intervals you marked with `os_signpost` (custom
    phases); presets exist for app launch (`.applicationLaunch`) and scroll animations.
  - **`XCTApplicationLaunchMetric`** — end-to-end launch time (UI test).
  - **`XCTHitchMetric`** (Xcode 26) / hitch-related signpost metrics — animation hitches &
    UI responsiveness in tests.

### Baselines & regression gating
- Set a baseline per test/device in Xcode's test report; commit it. CI re-runs and fails on
  regression. Baselines are **device-specific** — pin a device class per baseline.

### Release vs debug, device vs simulator
- **Always profile Release builds** — Debug disables optimizations, adds assertions/overflow
  checks; Swift especially is far slower unoptimized. Debug numbers mislead.
- **Real device, not Simulator** — Simulator runs on the Mac's CPU/GPU/memory and thermal
  envelope; it cannot represent frame budgets, memory limits, energy, or launch timing.
  Test the **oldest supported device** to catch worst cases.
- Control the environment: reboot, stable/mock network, measure **warm** launches, consistent
  data sets. Profiling itself adds overhead (a WWDC demo saw 149 ms wall vs 6 ms CPU-clock) —
  compare like-for-like, and trust field data (MetricKit/Organizer) for real-world truth.

---

## Quick diagnostic map (symptom → instrument)

| Symptom | First tool(s) |
|---|---|
| Slow launch | Instruments **App Launch** template, `DYLD_PRINT_STATISTICS`, `MXAppLaunchMetric` |
| UI freezes/beachballs | Hang analysis (Time Profiler flagged hangs), WWDC23 flow |
| Janky scrolling | **Animation Hitches** / Core Animation + blended-layer/offscreen overlays |
| High CPU | **Time Profiler** (invert, hide system libs), CPU Counters |
| Memory growth | **Allocations** (generations) + **Memory Graph Debugger** |
| Leaks / cycles | **Leaks** + Memory Graph Debugger |
| Battery drain | **Energy Log** + Location Energy, `MXBatteryMetric` |
| Slow SwiftUI updates | **SwiftUI instrument** (Cause & Effect, Long View Body) |
| Concurrency stalls | **Swift Concurrency / Swift Executors** instrument, System Trace |
| Real-user regressions | **MetricKit** + **Xcode Organizer** metrics |

---

## Sources

Official Apple:
- [MetricKit — Apple Developer Documentation](https://developer.apple.com/documentation/MetricKit)
- [Optimizing App Launch — WWDC19 (session 423)](https://developer.apple.com/videos/play/wwdc2019/423/)
- [Eliminate animation hitches with XCTest — WWDC20 (10077)](https://developer.apple.com/videos/play/wwdc2020/10077/)
- [Optimize for variable refresh rate displays — WWDC21 (10147)](https://developer.apple.com/videos/play/wwdc2021/10147/)
- [Track down hangs with Xcode and on-device detection — WWDC22 (10082)](https://developer.apple.com/videos/play/wwdc2022/10082/)
- [Power down: Improve battery consumption — WWDC22 (10083)](https://developer.apple.com/videos/play/wwdc2022/10083/)
- [Visualize and optimize Swift concurrency — WWDC22 (110350)](https://developer.apple.com/videos/play/wwdc2022/110350/)
- [Analyze hangs with Instruments — WWDC23 (10248)](https://developer.apple.com/videos/play/wwdc2023/10248/)
- [Analyze heap memory — WWDC24 (10173)](https://developer.apple.com/videos/play/wwdc2024/10173/)
- [What's new in Xcode 26 — WWDC25 (247)](https://developer.apple.com/videos/play/wwdc2025/247/)
- [Optimize SwiftUI performance with Instruments — WWDC25 (306)](https://developer.apple.com/videos/play/wwdc2025/306/)
- [Optimize CPU performance with Instruments — WWDC25 (308)](https://developer.apple.com/videos/play/wwdc2025/308/)
- [Energy Efficiency Guide for iOS Apps — Measure Energy Impact with Instruments](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/EnergyGuide-iOS/MonitorEnergyWithInstruments.html)
- [Signs of Energy Leaks — Energy Efficiency Guide](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/EnergyGuide-iOS/SignsofEnergyLeaks.html)
- [XCTOSSignpostMetric — Apple Developer Documentation](https://developer.apple.com/documentation/xctest/xctossignpostmetric)
- [Maximum build file sizes — App Store Connect Help](https://developer.apple.com/help/app-store-connect/reference/maximum-build-file-sizes/)
- [What is app thinning? — Xcode Help](https://help.apple.com/xcode/mac/current/en.lproj/devbbdc5ce4f.html)

Community / secondary (context & practitioner detail):
- [WWDC18 iOS Memory Deep Dive (session 416) — notes](https://gist.github.com/SheldonWangRJT/5d2ea69f78a905c76e0c36dfc994e85c)
- [WWDC21 Avoid hitches / render loop — a11y-guidelines notes](https://a11y-guidelines.orange.com/en/mobile/ios/wwdc/nota11y/2021/21hitches/)
- [Analyze hangs with Instruments — WWDCNotes](https://wwdcnotes.com/documentation/wwdc23-10248-analyze-hangs-with-instruments/)
- [App Launch Time: 7 tips — SwiftLee](https://www.avanderlee.com/optimization/launch-time-performance-optimization/)
- [Using MetricKit to monitor launch times — SwiftLee](https://www.avanderlee.com/swift/metrickit-launch-time/)
- [Using Xcode Instruments to optimize Swift Concurrency — SwiftLee](https://www.avanderlee.com/concurrency/using-xcode-instruments-to-optimize-swift-concurrency-code/)
- [Performance testing with XCTest — Chime](https://www.chimehq.com/blog/xctest-performance)
- [Performance testing using XCTMetric — Augmented Code](https://augmentedcode.io/2019/12/22/performance-testing-using-xctmetric/)
- [Xcode 26's Instruments overhaul — Medium (Sree Charan)](https://medium.com/@sree.charan/xcode-26s-instruments-gets-a-major-overhaul-2e18c58f5513)
- [WWDC25 Optimize SwiftUI performance — DEV (arshtechpro)](https://dev.to/arshtechpro/wwdc-2025-optimize-swiftui-performance-with-instruments-4o4j)
- [App Thinning: Bitcode, Slicing & ODR (2025) — Medium](https://medium.com/@tanishqarora-ios/app-thinning-in-ios-bitcode-slicing-on-demand-resources-3bada6544f9b)
- [iOS App Size Report and Size Analysis — Medium (Wizeline)](https://medium.com/wizeline-mobile/ios-app-size-report-and-size-analysis-d56c6d3d93f3)
- [Uncovering iOS OOM: kernel mechanics & jetsam — BestHub](https://www.besthub.dev/articles/uncovering-ios-oom-from-kernel-mechanics-to-real-world-monitoring-solutions-e54e1fb1d13a)
- [Core Animation Instrument color overlays — reference notes](https://medium.com/@peteliev/diagnose-and-solve-performance-problem-with-xcode-instruments-5c25c27f21d5)

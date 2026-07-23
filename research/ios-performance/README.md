# iOS Performance Engineering — Research Reference

Authoritative reference on **iOS app performance optimization and diagnostics** (tooling baseline
Xcode 26 / Instruments 27, iOS 18/26), gathered to ground the
[`ios-performance-specialist`](../../agents/core/ios-performance-specialist.md) agent (feature #219,
EPIC #217).

**Compiled:** 2026-07-23. Numeric targets are Apple's stated figures. Grounded in official Apple
sources (Instruments, MetricKit, WWDC performance sessions) — see the file's Sources list.

## Contents

| File | Covers |
|------|--------|
| [`01-ios-performance.md`](01-ios-performance.md) | Golden numbers; Instruments toolbox (Time Profiler, Allocations/Leaks, Animation Hitches + color overlays, System Trace, os_signpost, SwiftUI & Swift Concurrency instruments, Xcode 26 Processor Trace/CPU Counters); app launch phases & measurement; rendering/hitches & the hang model; memory (footprint, jetsam, image decode, autoreleasepool); energy/battery; MetricKit metrics & diagnostics; app size/thinning; XCTest performance tests, baselines & regression gating; measurement discipline |

## Key facts at a glance

- **First rule: measure, don't estimate** — Release build, real oldest-supported device, warm launch (Simulator lies about performance).
- **Golden numbers**: launch ~400ms; frame 16.67ms@60Hz / 8.33ms@120Hz; hang 250ms; "instant" ≤100ms; page 16KB; size 4GB / 500MB `__TEXT` / ~200MB cellular; decoded image = w×h×4B (sRGB).
- **Symptom→instrument map**: launch → App Launch template; freeze → hang analysis; jank → Animation Hitches + overlays; CPU → Time Profiler; memory growth → Allocations generations + Memory Graph; leaks → Leaks; battery → Energy Log; SwiftUI → SwiftUI instrument; concurrency → Swift Executors; field → MetricKit/Organizer.
- **Memory**: Leaks finds unreferenced cycles; abandoned (referenced) memory needs Allocations generations / Memory Graph. Respond to jetsam pressure — don't hardcode limits.
- **Gate regressions**: XCTest `measure(metrics:)` with device-specific baselines in CI; watch MetricKit + Organizer for real-user regressions.

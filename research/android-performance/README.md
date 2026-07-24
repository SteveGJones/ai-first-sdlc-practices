# Android Performance Engineering — Research Reference

Grounds the [`android-performance-specialist`](../../agents/core/android-performance-specialist.md)
agent (feature #226, sub-epic #225). Compiled 2026-07-23 from official Android sources. Vitals
thresholds, library minimums, and per-version behaviour are flagged ⚠️ version-sensitive.

| File | Covers |
|------|--------|
| [`01-android-performance.md`](01-android-performance.md) | Startup (cold/warm/hot, TTID/TTFD, App Startup lib, SplashScreen), Baseline Profiles & Macrobenchmark/Microbenchmark, rendering/jank (frame budgets, slow/frozen frames, JankStats), ANRs (ApplicationExitInfo), memory (LeakCanary, LMK, onTrimMemory, bitmaps), Perfetto/Studio Profiler/simpleperf, Play Vitals Core thresholds, app size, battery (Doze/standby buckets/wake locks) |

**At a glance:** measure on physical device + release/benchmark build; Play Core Vitals (crash ≥1.09%/≥8%, ANR ≥0.47%/≥8%) gate discoverability; Baseline Profiles ≈ 30% faster startup; slow frame 16–700ms / frozen >700ms; prioritize ANRs → frozen → slow frames.

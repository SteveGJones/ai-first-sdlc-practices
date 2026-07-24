# Gradle & AGP (Android build) — Research Reference

Grounds the [`gradle-build-specialist`](../../agents/core/gradle-build-specialist.md) agent (feature
#226, sub-epic #225). Compiled 2026-07-23 from official Android/Gradle docs. AGP deprecates
aggressively — exact minimum versions are flagged `[version-sensitive]`; re-check the compatibility
matrix before quoting.

| File | Covers |
|------|--------|
| [`01-gradle-agp.md`](01-gradle-agp.md) | Project structure & Kotlin DSL, version catalogs (`libs.versions.toml`), convention plugins (build-logic vs buildSrc), build performance (configuration cache vs build cache, configuration-time work, daemon/heap), KSP vs kapt, build types/flavors/variants, dependency management (implementation vs api, BOMs, constraints, locking), R8/shrinking, the AGP↔Gradle↔Kotlin↔JDK matrix, pitfalls |

**At a glance:** configuration cache + build-logic (not buildSrc) + KSP are the big build-speed wins; version catalogs are the single source of truth; `implementation` over `api`; AGP/Gradle/Kotlin/JDK move together (JDK 17 floor for AGP 9.x).

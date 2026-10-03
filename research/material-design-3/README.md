# Material Design 3 (M3) — Research Reference

Authoritative reference material on Google's **Material Design 3** ("Material You")
design language — https://m3.material.io — gathered to ground the
[`material-design-3-architect`](../../agents/core/material-design-3-architect.md) agent
(feature #214). Every claim is sourced to official Google documentation; each file carries
its own **Sources** list.

**Compiled:** 2026-07-22. M3 evolves (notably Material 3 Expressive, 2025), so version-sensitive
figures (library versions, latest components) should be re-checked against the linked sources
before quoting them as current.

## Sourcing caveat

`m3.material.io` is a client-rendered single-page app that returns only page titles to
non-browser fetchers. Numeric spec values below were therefore confirmed against Google's
**static** authoritative sources — the Android developer site (`developer.android.com`), the
Material Components GitHub repos (`material-components`, `material-foundation`), `material-web.dev`,
and the Flutter API — which mirror the canonical `md.sys.*` token values one-to-one.

## Contents

| File | Covers |
|------|--------|
| [`01-foundations-tokens.md`](01-foundations-tokens.md) | HCT color space, tonal palettes, dynamic color / Material You, the full color-role set, the three-tier token architecture (`md.ref` → `md.sys` → `md.comp`), type scale, shape scale, tonal elevation & surfaces, state layers |
| [`02-components-layout.md`](02-components-layout.md) | Full component catalog (6 categories), window size classes / breakpoints, canonical layouts (list-detail / supporting pane / feed), grid & units, navigation-selection rules, Material 3 Expressive (2025) |
| [`03-motion-accessibility-content.md`](03-motion-accessibility-content.md) | Easing & duration tokens, transition patterns, Expressive spring/physics motion, interaction states & ripple, accessibility (48dp targets, contrast, dynamic type, focus, screen readers, reduced motion), UX writing, Material Symbols |
| [`04-implementation-tooling-migration.md`](04-implementation-tooling-migration.md) | Platform implementations (Compose Material3, MDC-Views, `@material/web` [maintenance mode], Flutter), Material Theme Builder, material-color-utilities, Material Symbols, Style Dictionary interop, M2→M3 migration, M3-vs-alternatives decision guidance |

## Key facts at a glance

- **HCT** = CAM16 Hue + Chroma with CIELAB **L\*** as Tone (0–100). Load-bearing property:
  **ΔTone ≥ 40 ⇒ ≥ 3:1 contrast; ΔTone ≥ 50 ⇒ ≥ 4.5:1** — so every `on-` role is accessible by construction.
- **Three-tier tokens** cascade `md.ref.* → md.sys.* → md.comp.*`; dynamic color works because a
  wallpaper reseed changes **only** the reference tier while the semantic contract stays stable.
- **Type scale**: 5 roles (Display/Headline/Title/Body/Label) × 3 sizes = 15 baseline styles.
- **Shape scale**: none 0 · extra-small 4 · small 8 · medium 12 · large 16 · extra-large 28 · full (pill) dp.
- **Elevation**: 6 levels (0/1/3/6/8/12 dp) expressed via **tonal** surface tint / surface-container roles, not M2 overlays.
- **State layers**: hover 8% · focus 10% · pressed 10% · dragged 16%; disabled = content 38% / container 12%.
- **Breakpoints**: Compact <600 · Medium 600–839 · Expanded 840–1199 · Large 1200–1599 · Extra-large ≥1600 dp.
- **Material 3 Expressive (I/O 2025)**: spring/physics motion, ~35-shape morphing library, 5-size + round/square
  buttons, new components (FAB menu, button groups, split button, loading indicator, toolbars). Backed by 46 studies / 18k+ participants.
- **Platforms**: Compose `androidx.compose.material3` (primary, active) · MDC-Views `com.google.android.material` ·
  `@material/web` (**maintenance mode** — Angular → Angular Material) · Flutter (`useMaterial3` default since 3.16).

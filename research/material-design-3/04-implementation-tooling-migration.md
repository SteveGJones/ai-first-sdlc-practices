# Material Design 3 — Implementation, Tooling & Migration

Reference material for a specialist design-systems agent. Scope: platform
implementations, design tooling, M2→M3 migration, and decision guidance.
Last verified: July 2026. Prefer the official source URLs in the Sources
section for anything version-sensitive.

---

## 1. Platform Implementations

M3 is a **design specification** (m3.material.io) realised by separate
first-party code libraries per platform. Each library implements the same
token system (`md.sys.color.*`, `md.sys.typescale.*`, `md.sys.shape.*`,
`md.sys.elevation.*`) in a platform-idiomatic way.

### 1a. Web — Material Web Components (`@material/web`)

- **Package**: `@material/web` (npm). Repo: `github.com/material-components/material-web`.
  Published docs site: `material-web.dev`. Built on **Lit** (lightweight web
  components) + TypeScript + SCSS. Components are framework-agnostic custom
  elements (`<md-outlined-button>`, `<md-checkbox>`, `<md-text-field>`, etc.).
- **STATUS: MAINTENANCE MODE.** Announced in GitHub Discussion #5642
  ("❗MWC is in maintenance mode"). Google reassigned the Material Web
  engineering team to Google's large-scale **internal "Wiz" framework**.
  Latest release line is in the **v2.x** series (v2.5.0 tagged mid-2026), but
  releases are effectively frozen for new features.
  - What maintenance mode means concretely:
    - **NOT deprecated / not discontinued** — existing components remain
      stable and usable in production.
    - **No new components or features** are planned.
    - **PRs are not accepted by default**; small PRs may be reviewed
      case-by-case. Development continues only via volunteer/community effort.
    - The project is **seeking new maintainers** to resume active development.
- **Theming — CSS custom properties (design tokens).** Components expose their
  M3 tokens as CSS custom properties. Two layers:
  - **System-level color tokens**: `--md-sys-color-primary`,
    `--md-sys-color-on-primary`, `--md-sys-color-surface`,
    `--md-sys-color-surface-container`, `--md-sys-color-outline`, etc. Set these
    on `:root` (or any ancestor) and all components inherit the scheme. This is
    the recommended way to apply a full generated theme, and it is what the
    Material Theme Builder "Web (CSS)" export produces.
  - **Component-level tokens**: e.g. `--md-outlined-button-container-shape`,
    `--md-filled-button-label-text-color` for per-component overrides.
  - Typography tokens: `--md-sys-typescale-body-large-font`, etc. Shape tokens:
    `--md-sys-shape-corner-*`.
  - Dark mode is done by swapping the `--md-sys-color-*` values (e.g. under a
    `@media (prefers-color-scheme: dark)` block or a `.dark` class).
- **What Google recommends for web now**: There is **no single blessed
  replacement**. Guidance/community consensus:
  - **Angular apps → Angular Material** (`@angular/material`, actively
    maintained, M3-capable) — explicitly recommended in the announcement.
    Note: Angular Material and the Angular CDK are a **separate, unaffected**
    codebase from MWC.
  - Non-Angular apps: continue using `@material/web` as-is (stable), or a
    community M3 library such as **mdui**. Some teams choose non-M3 systems
    (MUI, etc.) for React.
  - For pure design tokens without the component library, teams generate
    `--md-sys-*` CSS with **Material Theme Builder** and style their own
    components.

### 1b. Android — Jetpack Compose (`androidx.compose.material3`)

- **Package**: `androidx.compose.material3:material3`. This is the **primary,
  actively developed** M3 implementation and Google's recommended path for new
  Android UI. Stable line reached **1.x** long ago; **1.4.0** shipped Sept 2025
  bringing Expressive to stable-ish, with Expressive APIs behind an opt-in.
  Add via `implementation "androidx.compose.material3:material3:$version"`.
- **`MaterialTheme`** composable wires three subsystems:
  ```kotlin
  MaterialTheme(
      colorScheme = colorScheme,   // ColorScheme (NOT M2's Colors)
      typography  = typography,     // Typography (display/headline/title/body/label × L/M/S)
      shapes      = shapes,         // Shapes (extraSmall..extraLarge)
  ) { /* content */ }
  ```
  Access at runtime via `MaterialTheme.colorScheme.primary`,
  `MaterialTheme.typography.titleLarge`, `MaterialTheme.shapes.medium`.
- **`ColorScheme`** — built with `lightColorScheme(...)` / `darkColorScheme(...)`.
  ~30+ named roles: `primary`, `onPrimary`, `primaryContainer`,
  `onPrimaryContainer`, `secondary`/`tertiary` families, `surface`,
  `surfaceVariant`, `surfaceContainer(Low/High/Highest)`, `background`,
  `error`, `outline`, `outlineVariant`, `surfaceTint`, `inverseSurface`, etc.
- **Dynamic color (Material You, Android 12+ / API 31+)**: derive the scheme
  from the user's wallpaper:
  ```kotlin
  val colorScheme = when {
      Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && darkTheme ->
          dynamicDarkColorScheme(context)
      Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !darkTheme ->
          dynamicLightColorScheme(context)
      darkTheme -> DarkColorScheme
      else -> LightColorScheme
  }
  ```
  `dynamicLightColorScheme(context)` / `dynamicDarkColorScheme(context)` are the
  key APIs; require a `Context`. Below API 31 you fall back to your brand scheme.
- **Elevation** is expressed with **`tonalElevation`** (tonal color overlay,
  tinted by `surfaceTint`, default `primary`) and/or `shadowElevation`
  (drop shadow). M2's elevation-overlay concept is gone.
- **Material 3 Expressive** (Android 16 era, announced May 13 2025):
  - New composable **`MaterialExpressiveTheme(...)`** — requires
    `@OptIn(ExperimentalMaterial3ExpressiveApi::class)`. Signature:
    ```kotlin
    @Composable fun MaterialExpressiveTheme(
        colorScheme: ColorScheme? = null,
        motionScheme: MotionScheme? = null,
        shapes: Shapes? = null,
        typography: Typography? = null,
        content: @Composable () -> Unit,
    )
    ```
    It is a wrapper over `MaterialTheme` that **defaults to the expressive
    motion scheme** (spring/physics-based animation applied to all M3 components).
  - **`MotionScheme`** is the new subsystem: `MotionScheme.expressive()`
    (bouncy, flashy) vs `MotionScheme.standard()` (smart, comfortable). Motion
    is now spring/physics-based rather than pure duration+easing curves.
  - ~15 new/updated components: **button groups, FAB menu, loading indicators,
    split button, toolbars** (new); app bars, carousel, common buttons,
    extended FAB, icon buttons, navigation bar, navigation rail, progress
    indicators (updated with new shapes/emphasis).
  - Backed by unusually heavy research: **46 studies, 18,000+ participants**.

### 1c. Android — Views / MDC (`com.google.android.material`)

- **Package**: `com.google.android.material:material` — Material Components for
  Android (MDC-Android). Repo: `github.com/material-components/material-components-android`.
  The classic **View/XML** system (not Compose). Still maintained.
- **Version gates**:
  - **M3 themes/styles**: require **1.5.0+**.
  - **Material3 Expressive themes/styles**: require **1.14.0+** (introduced in
    the 1.14.0-alpha line, e.g. `1.14.0-alpha04`).
- **Themes**: `Theme.Material3.*` (e.g. `Theme.Material3.DayNight.NoActionBar`,
  `Theme.Material3.Dark`). Applying a `Theme.Material3.*` parent enables a
  custom view inflater that swaps default framework widgets for their Material
  equivalents. Expressive variants are `Theme.Material3Expressive.*`.
- **Theming** is XML-attribute based: color roles map to theme attributes such
  as `?attr/colorPrimary`, `?attr/colorOnPrimary`, `?attr/colorPrimaryContainer`,
  `?attr/colorSurface`, `?attr/colorSurfaceContainer`, `?attr/colorOutline`.
  Typography via `?attr/textAppearanceBodyLarge` etc.; shapes via
  `shapeAppearance*` attributes. The Material Theme Builder generates an
  Android XML export that fills every role.
- Dynamic color for Views: `DynamicColors.applyToActivitiesIfAvailable(app)` /
  the `ThemeUtils`/`DynamicColors` helpers apply wallpaper-derived palettes on
  Android 12+.

### 1d. Flutter — Material 3 (`flutter/material`)

- M3 is built into the Flutter SDK's `material` library (no separate package
  for the components themselves).
- **`ThemeData.useMaterial3` is `true` by default** as of **Flutter 3.16**
  (opt-in landed earlier in 3.13.0-4.0.pre; became the default in 3.16). To
  fall back: `ThemeData(useMaterial3: false)` — but M2 support is slated for
  **deprecation and removal**, so migration is expected.
- **Theming** is driven mainly by `ThemeData.colorScheme` and
  `ThemeData.textTheme`, plus optional per-component themes
  (`SegmentedButtonThemeData`, `SnackBarThemeData`, etc.).
- **`ColorScheme.fromSeed(seedColor: ...)`** is the recommended way to produce a
  full, accessible, harmonised M3 scheme from one seed color (optionally
  `brightness:` and, in newer APIs, `dynamicSchemeVariant:`). Under the hood it
  uses `material_color_utilities`.
  ```dart
  MaterialApp(
    theme: ThemeData(
      // useMaterial3: true is the default
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
    ),
  );
  ```
- Dynamic color (wallpaper-based, Android): community package
  **`dynamic_color`** (pub.dev) bridges platform palettes into a Flutter
  `ColorScheme`.
- New/updated M3 widgets: `NavigationBar` (replaces `BottomNavigationBar`),
  `SegmentedButton`, updated `Card`, `Chip`, dialogs, etc. Motion tokens updated
  (old M2 curves renamed with a "legacy" suffix).

---

## 2. Design Tooling

### 2a. Material Theme Builder (MTB)

- Repo: `github.com/material-foundation/material-theme-builder`. Ships as a
  **Figma plugin** (search "Material Theme Builder" in Figma) **and a web tool**
  (`m3.material.io/theme-builder`).
- Workflow: pick a **seed/source color** (or extract from an image) → it
  generates the full M3 tonal palettes and role assignments → click **Create
  Theme** to materialise Material Design tokens as Figma styles / variables.
- **Custom colors**: add named custom colors that get harmonised into the scheme.
- **Export targets**: Android (XML themes + `Color.kt`), Jetpack Compose
  (`Color.kt` / `Theme.kt`), Flutter, **Web (CSS custom properties,
  `--md-sys-color-*`)**, and JSON design tokens.
- **JSON round-trip**: exact color values live in style properties; a **JSON
  import** updates same-named theme values, so themes move between files and
  between web and Figma. This is the interop seam for pipelines.

### 2b. material-color-utilities (MCU)

- Repo: `github.com/material-foundation/material-color-utilities`. The
  **algorithmic core** behind dynamic color and every seed→scheme generator
  (MTB, Compose `dynamic*ColorScheme`, Flutter `ColorScheme.fromSeed`, MDC).
- **Languages/packages**: Dart (`material_color_utilities` on pub.dev),
  TypeScript/JS (`@material/material-color-utilities` on npm), Java (embedded in
  MDC-Android), C++, Swift, Kotlin. Third-party ports exist (e.g. .NET
  `MaterialColorUtilities`, Rust `mcu-material-color`).
- **Modules**:
  - **hct** — the **HCT color space** (Hue, Chroma, Tone), built on CAM16 for
    perceptual accuracy + L* for tone; the foundation of the whole system.
  - **quantize** — extract dominant colors from an image. Implementations: Wu,
    WSMeans, **Celebi** (recommended composite), QuantizerMap.
  - **score** — rank quantized colors for suitability as theme source colors.
  - **palettes** — `TonalPalette` (13 tones per hue) and `CorePalette`.
  - **scheme** / **dynamiccolor** — generate static and dynamic color schemes
    from a seed or core palette, across variants (tonal spot, vibrant, expressive,
    fidelity, content, neutral, monochrome) and contrast levels.
  - **blend** — harmonise/interpolate colors (e.g. nudge a brand color toward
    the seed hue).
  - **contrast**, **dislike** (fix universally-disliked colors), **temperature**
    (warm/cool complements) — refinement utilities.
- **How it powers dynamic color**: wallpaper/image → **quantize** → **score** to
  pick a source → build **CorePalette/TonalPalette** in **HCT** → **scheme**
  assigns every M3 role at the right tone for light/dark + contrast. This yields
  accessible-by-construction schemes without manual color picking.

### 2c. Material Symbols

- The current icon library (successor to "Material Icons"). Repo:
  `github.com/google/material-design-icons`; served via Google Fonts. **~2,500+
  glyphs** in a single variable font, in **three styles**: **Outlined, Rounded,
  Sharp**.
- **Four variable-font axes** (with defaults):
  - **`wght` (weight)** 100–700 (default **400**) — stroke thickness.
  - **`FILL` (fill)** 0–1 (default **0**) — unfilled↔filled; animate for state
    transitions.
  - **`GRAD` (grade)** −50–200 (default **0**) — finer thickness adjustment than
    weight; e.g. slightly negative on dark backgrounds to reduce glare.
  - **`opsz` (optical size)** 20–48dp (default **48** static / typically 24 in
    use) — auto-adjusts stroke weight as icon scales.
- **Web usage** (Google Fonts):
  - Static (simplest): `<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">`
    then render via **ligatures** (snake_case icon name as text content, e.g.
    `<span class="material-symbols-outlined">settings</span>`).
  - Variable/full control: request axis ranges through the CSS API and drive them
    with **`font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;`**.
  - Optimisation: subset with **`&icon_names=`** (payload can drop from ~295 KB to
    ~1.7 KB), instance specific axes, add **`&display=block`** to avoid unstyled
    flash, or self-host via `@font-face`.

### 2d. Design-token export & Style Dictionary interop

- MTB exports **JSON design tokens** plus platform-native code. The JSON follows
  Material's token taxonomy (`md.sys.color.*`, `md.ref.palette.*`,
  `md.sys.typescale.*`, `md.sys.shape.*`).
- **Style Dictionary interop**: MTB's JSON is not automatically Style
  Dictionary–shaped. Common pipeline: use MTB (or a Figma variables exporter like
  the community **"Design Tokens" plugin** by lukasoppermann, which emits
  Amazon Style Dictionary–compatible JSON) → **Style Dictionary** transforms
  tokens into per-platform artefacts (CSS `--md-sys-color-*`, Android XML,
  Compose Kotlin, iOS Swift). Helper libs like `tokenizer-figma` parse exported
  Material Theme JSON.
- The web CSS export already emits `--md-sys-color-*` custom properties directly
  consumable by `@material/web`, so for web you often skip Style Dictionary.

---

## 3. Migration: Material 2 → Material 3

### Conceptual changes
- **Color**: M2's small fixed palette (`primary`, `primaryVariant`, `secondary`,
  `secondaryVariant`, `background`, `surface`, `error` + `on*`) → M3's **tonal
  role system** of ~30 roles derived from key colors via 13-tone tonal palettes.
  Adds container roles (`primaryContainer`, `surfaceContainer*`) and
  `surfaceTint`. Enables **dynamic color**.
- **Elevation**: M2 used shadows + dark-theme **elevation overlays**. M3 uses
  **tonal elevation** (surface tinted by `surfaceTint`/primary as it rises),
  optionally plus shadow. `ElevationOverlay`/`LocalElevationOverlay` removed;
  `LocalAbsoluteElevation` → `LocalAbsoluteTonalElevation`.
- **Typography**: role-based names replace the old scale.
- **Emphasis**: M2 conveyed emphasis via `ContentAlpha` (alpha on "on" colors);
  M3 uses **distinct color roles** (`onSurfaceVariant`) and **font weight**.
- **Shape**: 3-slot scale (`small/medium/large`) → 5-slot
  (`extraSmall..extraLarge`).

### Typography scale rename (Compose)
| M2 | M3 |
|---|---|
| `h1` | `displayLarge` |
| `h2` | `displayMedium` |
| `h3` | `displaySmall` |
| `h4` | `headlineMedium` (`headlineLarge` new) |
| `h5` | `headlineSmall` |
| `h6` | `titleLarge` |
| `subtitle1` | `titleMedium` |
| `subtitle2` | `titleSmall` |
| `body1` | `bodyLarge` |
| `body2` | `bodyMedium` |
| `caption` | `bodySmall` |
| `button` | `labelLarge` |
| `overline` | `labelSmall` (`labelMedium` new) |

### Component renames (Compose)
| M2 | M3 |
|---|---|
| `BottomNavigation` / `BottomNavigationItem` | `NavigationBar` / `NavigationBarItem` |
| `Chip` | `AssistChip` / `SuggestionChip` / `FilterChip` / `InputChip` |
| `ModalBottomSheetLayout` | `ModalBottomSheet` |
| `ModalDrawer` | `ModalNavigationDrawer` (+ `ModalDrawerSheet`) |
| `BackdropScaffold` | migrate to `Scaffold` / `BottomSheetScaffold` |
| `BottomDrawer` | migrate to `ModalBottomSheet` |
| `Badge(backgroundColor=)` | `Badge(containerColor=)` |
| `Surface(elevation=)` | `Surface(tonalElevation=, shadowElevation=)` |
| `Scaffold(backgroundColor=, scaffoldState=)` | `Scaffold(containerColor=)` + standalone `SnackbarHostState` |

### Migration tooling / process (Compose)
- **Coexistence**: add `androidx.compose.material3` alongside
  `androidx.compose.material` and migrate **screen-by-screen**; imports are
  namespaced so both can exist temporarily. Don't ship mixed long-term.
- **Recommended order**: migrate the **design system/theme first** (use Material
  Theme Builder to derive an M3 scheme from your M2 colors — note M2→MTB
  mapping: M2 `primary`→Primary, `primaryVariant`→Secondary, `secondary`→
  Tertiary, `surface/background`→Neutral), then migrate components.
- Reference migrations: the `android/compose-samples` apps (Reply, Jetchat,
  Jetnews) were migrated M2→M3.

### Migration (Web / Flutter)
- **Web**: MWC is Lit custom elements with no M2 predecessor to "migrate from"
  in the Compose sense; migration is mostly adopting `--md-sys-color-*` tokens
  and swapping to `<md-*>` elements. Given maintenance mode, weigh MWC vs Angular
  Material / community libs before investing.
- **Flutter**: flip `useMaterial3` (already default ≥3.16), move theming to
  `colorScheme` (via `ColorScheme.fromSeed`) + `textTheme`, and replace M2-only
  widgets (`BottomNavigationBar`→`NavigationBar`). Official guide:
  `docs.flutter.dev/release/breaking-changes/material-3-migration`.

### Common pitfalls
1. Generated M3 hex values **differ** from hand-picked M2 values (algorithmic).
   Expect a visual shift; don't try to pixel-match.
2. M3 Compose `Typography` has **no `defaultFontFamily`** — set `fontFamily` on
   each `TextStyle`.
3. `ColorScheme` has **no `isLight`** — thread light/dark via a
   `CompositionLocal` (or a wrapper theme) instead.
4. Top app bar scroll behavior needs the `Modifier.nestedScroll(...)` wiring or
   collapse won't work.
5. Drawers are wrappers (`ModalNavigationDrawer`), not `Scaffold` params.
6. Elevation: remember M3 needs `shadowElevation` **and/or** `tonalElevation`;
   reusing an M2 elevation Dp only on `tonalElevation` changes appearance
   (tint) rather than casting a shadow.
7. Snackbars: manage a standalone `SnackbarHostState`, not via `scaffoldState`.

---

## 4. Decision Guidance

### When M3 is a good fit
- **Android-first or Android-primary** products — it is the native, first-party,
  actively developed system (Compose `material3` + MDC Views); dynamic color is
  a differentiator only M3 offers.
- **Cross-platform apps wanting one design language** with real code on Android,
  Flutter, and (with caveats) web — shared token model keeps them coherent.
- Teams wanting **accessible-by-construction color** (MCU guarantees contrast)
  and fast theming from a single seed.
- Products that want **user-personalised theming** (Material You wallpaper
  coupling).

### When M3 is a weaker fit
- **iOS-primary / native-feel apps**: M3 conflicts with **Apple HIG**
  conventions (navigation patterns, controls, motion). Shipping M3 on iOS reads
  as non-native. Prefer HIG/SwiftUI there (or accept a deliberate cross-platform
  brand look).
- **Strong bespoke brand design languages**: if the brand demands a highly
  custom visual identity, M3's opinionated components can be more fight than
  help — though Expressive + full token theming narrows this gap (see below).
- **Data-dense enterprise/B2B**: **IBM Carbon** or **Ant Design** are often
  better tuned for dense tables, complex forms, enterprise React.
- **Microsoft ecosystem / Windows + web enterprise**: **Fluent 2** is the
  natural fit and spans more desktop platforms.
- **Web specifically, right now**: `@material/web` maintenance mode is a real
  risk factor for long-lived web products — favour Angular Material (Angular) or
  a maintained alternative, or use M3 as tokens-only over your own components.

### M3 vs other systems (quick map)
- **Apple HIG** — gold standard for iOS/macOS native feel; device-bound, weak
  cross-platform, minimal end-user theming. Choose for Apple-native apps.
- **Fluent 2 (Microsoft)** — broadest platform span (Web/Windows/iOS/Android/
  macOS), enterprise + Microsoft 365 coherence.
- **IBM Carbon** — enterprise, data-heavy, strong accessibility/WCAG posture.
- **Ant Design** — enterprise React component library (Alibaba/Ant Group).
- **M3** — best-in-class **dynamic/seed theming** and Android integration;
  strong accessibility.

### The "everything looks like Google" critique — how M3 answers it
- **Token-deep theming**: every surface is a role token; swapping the seed and
  the `--md-sys-color-*` / `ColorScheme` values re-skins the whole system.
  Custom colors harmonise in via MCU `blend`.
- **Shape & typography are fully parameterised** (`Shapes`, `Typography`), so the
  "Google" silhouette (default corner radii, Roboto/type scale) can be replaced
  wholesale.
- **Material 3 Expressive** is the explicit response: richer/variable shapes,
  spring-based **motion physics** (`MotionScheme.expressive()`), emphasized type,
  and new components (button groups, FAB menu, split button, toolbars) exist to
  let products feel distinct and emotionally resonant while keeping M3's
  usability and accessibility guarantees. Backed by 46 studies / 18k+
  participants.
- Net: M3 supplies **structure and accessibility** while intending customisation
  to be first-class; "looks like Google" is a default-config outcome, not a
  ceiling. The practical limits are component structure/interaction patterns
  (harder to restyle than color/shape/type) and, on iOS, HIG divergence.

---

## Sources
- Material Web maintenance-mode announcement — https://github.com/material-components/material-web/discussions/5642
- Material Web repo — https://github.com/material-components/material-web
- Material Web npm — https://www.npmjs.com/package/@material/web
- M3 Develop / Web — https://m3.material.io/develop/web
- M3 in Jetpack Compose — https://developer.android.com/develop/ui/compose/designsystems/material3
- Migrate M2→M3 in Compose — https://developer.android.com/develop/ui/compose/designsystems/material2-material3
- Compose Material3 releases — https://developer.android.com/jetpack/androidx/releases/compose-material3
- MaterialExpressiveTheme reference — https://composables.com/material3/materialexpressivetheme
- M3 Expressive announcement (Android 16) — https://9to5google.com/2025/05/13/android-16-material-3-expressive-redesign/
- M3 Expressive deep dive — https://www.androidauthority.com/google-material-3-expressive-features-changes-availability-supported-devices-3556392/
- MDC-Android getting started — https://github.com/material-components/material-components-android/blob/master/docs/getting-started.md
- MDC-Android releases — https://github.com/material-components/material-components-android/releases
- Flutter useMaterial3 default (breaking change) — https://docs.flutter.dev/release/breaking-changes/material-3-default
- Flutter M3 migration guide — https://docs.flutter.dev/release/breaking-changes/material-3-migration
- material-color-utilities repo — https://github.com/material-foundation/material-color-utilities
- MCU dynamic color scheme concept — https://github.com/material-foundation/material-color-utilities/blob/main/concepts/dynamic_color_scheme.md
- material_color_utilities (Dart / pub) — https://pub.dev/documentation/material_color_utilities/latest/hct_hct/
- Material Theme Builder repo/README — https://github.com/material-foundation/material-theme-builder/blob/main/README.md
- Material Theme Builder (web tool) — https://m3.material.io/theme-builder
- Material Symbols guide (Google Fonts) — https://developers.google.com/fonts/docs/material_symbols
- Material Symbols intro — https://m3.material.io/blog/introducing-symbols/
- material-design-icons repo — https://github.com/google/material-design-icons
- M3 Icons style — https://m3.material.io/styles/icons
- Design Tokens Figma plugin (Style Dictionary interop) — https://github.com/lukasoppermann/design-tokens
- Design-system comparison (M3 / HIG / Carbon) — https://medium.com/design-bootcamp/understanding-and-comparing-design-systems-material-3-apple-ios-and-ibm-carbon-28c585f893ed
- Motion — Material Design 3 — https://m3.material.io/styles/motion/

# Material Design 3 (M3) — Foundations & Design Tokens

Authoritative reference for an M3 specialist agent. Covers the color system, the
three-tier design-token architecture, typography, shape, elevation/surfaces, and
state layers. Values are the M3 **baseline** spec (the defaults you get before
dynamic color or M3 Expressive overrides). "dp" = density-independent pixels;
"sp" = scale-independent pixels (text). In web/CSS these map to px/rem.

---

## 1. Color system

### 1.1 HCT color space (Hue, Chroma, Tone)

**HCT** is the color space M3 is built on. It was created by Google (author:
James O'Leary) specifically so a design system could **guarantee contrast and
therefore accessibility**. It is a hybrid:

- **H — Hue** (0–360°): taken from the **CAM16** color-appearance model. CAM16
  gives perceptually even hues (colors that look like the same hue stay the same
  hue across lightness).
- **C — Chroma** (0 → ~120+, unbounded, gamut-limited): also from **CAM16**.
  Chroma is perceived colorfulness/saturation. Max achievable chroma depends on
  hue and tone (the sRGB gamut), so chroma is clamped when a requested value is
  out of gamut.
- **T — Tone** (0–100): this is **L\*** (CIELAB lightness, aka L\* from
  CIE Lab / measured against D65). L\* is the industry-standard perceptual
  lightness axis and is the same quantity WCAG contrast is (approximately) built
  on. Tone 0 = pure black, Tone 100 = pure white.

**Why the hybrid?** CAM16's own lightness (J) does not predict contrast well,
while CIELAB's hue is perceptually uneven. HCT keeps **CAM16 hue + chroma** and
swaps in **CIELAB L\* as tone**, giving both perceptually stable color and a
lightness axis that maps cleanly to contrast math.

**The key accessibility property:** a **tone difference of ~40 guarantees a
contrast ratio ≥ 3.0:1**, and a **tone difference of ~50 guarantees ≥ 4.5:1**.
This is why every M3 "on-" color is a fixed tonal distance from its background —
contrast is baked into the palette, not checked after the fact.

- Reference implementation: **`material-color-utilities`** (Google, multi-lang:
  Dart/JS/Java/Kotlin/C++/Swift), which contains the `Hct`, `Cam16`, and
  `TonalPalette` classes.

### 1.2 Tonal palettes and the 13 tones

From a single **source color** (a.k.a. seed color), HCT generates a set of
**tonal palettes**. Each tonal palette **fixes hue and chroma** and varies only
**tone**, producing swatches at these **13 standard tone stops**:

> **0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100**

(Note the non-uniform stops at the light end: 90, **95**, **99**, 100 — extra
resolution near white for surfaces.) M3 also uses additional tones internally for
new surface-container roles (e.g. 4, 6, 12, 17, 22, 24 on the neutral palette in
newer specs), but the classic named scale is the 13 above.

**The six key palettes** generated from the seed:

| Palette | Derivation from seed (baseline algorithm) | Drives |
|---|---|---|
| **Primary** (`a1`) | seed hue, high chroma (~48) | primary roles |
| **Secondary** (`a2`) | seed hue, lower chroma (~16) | secondary roles |
| **Tertiary** (`a3`) | seed hue rotated ~+60°, chroma ~24 | tertiary roles |
| **Neutral** (`n1`) | seed hue, very low chroma (~4) | surfaces, backgrounds |
| **Neutral-variant** (`n2`) | seed hue, low chroma (~8) | outlines, surface-variant |
| **Error** | fixed hue ~25 (red), high chroma | error roles |

Color **roles** are then assigned a **specific tone from a specific palette**,
and — critically — a **different tone in light vs dark mode**. Example (baseline
tonal-palette mapping):

| Role | Light (palette@tone) | Dark (palette@tone) |
|---|---|---|
| primary | Primary @ **40** | Primary @ **80** |
| on-primary | Primary @ **100** | Primary @ **20** |
| primary-container | Primary @ **90** | Primary @ **30** |
| on-primary-container | Primary @ **30** (newer: 10) | Primary @ **90** |
| surface | Neutral @ **98** | Neutral @ **6** |
| on-surface | Neutral @ **10** | Neutral @ **90** |
| on-surface-variant | Neutral-variant @ **30** | Neutral-variant @ **80** |
| outline | Neutral-variant @ **50** | Neutral-variant @ **60** |
| outline-variant | Neutral-variant @ **80** | Neutral-variant @ **30** |

Because on-primary is Primary@100 over primary Primary@40, the tone gap is 60 →
contrast ≥ 4.5:1, automatically.

### 1.3 Dynamic color & Material You

**Material You** (M3's personalization layer) generates a whole scheme from a
**source color** the user did not hand-pick:

- **Wallpaper extraction** — on Android 12+ the system runs **quantization**
  (Celebi/WSMeans k-means in HCT) over the wallpaper bitmap to pick candidate
  seed colors, then a **Score** step ranks them for chroma/usability. The winning
  color seeds all six tonal palettes.
- The generated palettes flow into the **same fixed set of color roles**, so any
  correctly-themed app recolors itself instantly and consistently.
- Sources of a scheme: **wallpaper**, a **user-chosen accent**, an **in-app brand
  color** ("content"-based dynamic color), or the static baseline.
- **Scheme variants** (algorithms that turn one seed into a full scheme):
  `Tonal Spot` (Android default), `Vibrant`, `Expressive`, `Fidelity`,
  `Content`, `Neutral`, `Monochrome`, `Rainbow`, `Fruit Salad`. They differ in
  how much chroma/hue rotation each palette gets.

### 1.4 Color roles / system color tokens (the full role set)

Roles are **semantic** — named by job, not by color. Two naming conventions:

- **`on-X`** = the color for **content (text/icons)** that sits **on top of** the
  `X` fill. Guaranteed accessible contrast against `X`.
- **`X-container`** = a **lower-emphasis fill** in the same hue family as `X`
  (e.g. a tonal button/chip background), paired with **`on-X-container`** for its
  content.
- **`X-variant`** = a lower-emphasis sibling of `X`.

**Accent families** (each has 4 roles):

- `primary`, `on-primary`, `primary-container`, `on-primary-container`
- `secondary`, `on-secondary`, `secondary-container`, `on-secondary-container`
- `tertiary`, `on-tertiary`, `tertiary-container`, `on-tertiary-container`
- `error`, `on-error`, `error-container`, `on-error-container`

**Surface & neutral family** (this is where M3 differs most from M2 — the old
single `surface` + elevation overlays were replaced by a graded set of surface
containers):

- `surface`, `on-surface`
- `on-surface-variant` (secondary text/icons on surface; lower emphasis)
- `surface-variant` (legacy fill; being phased toward surface-container roles)
- `surface-dim` (dimmest surface — darkest in light theme)
- `surface-bright` (brightest surface)
- `surface-container-lowest`
- `surface-container-low`
- `surface-container`
- `surface-container-high`
- `surface-container-highest`
- `surface-tint` (the tint color, = primary, used for tonal-elevation overlays)
- `background`, `on-background` (largely equal to surface/on-surface now; retained
  for back-compat)

**Outline family:**

- `outline` (decorative borders, dividers with emphasis, text-field outlines)
- `outline-variant` (low-emphasis dividers)

**Inverse family** (for elements that flip the theme locally, e.g. snackbars):

- `inverse-surface`
- `inverse-on-surface`
- `inverse-primary`

**Utility:**

- `scrim` (the dim overlay behind modals/drawers; usually neutral@0)
- `shadow` (the color used to cast shadows; usually neutral@0)

**Fixed accent roles** (2024 addition — colors that stay the **same in light and
dark**, useful for cross-theme UI): `primary-fixed`, `primary-fixed-dim`,
`on-primary-fixed`, `on-primary-fixed-variant`, and the same set for
`secondary-fixed*` and `tertiary-fixed*`.

### 1.5 Color schemes: light/dark, static/dynamic, contrast levels

- **Light & dark**: every role has a light and a dark tonal assignment (see 1.2).
  You never invert colors manually — you pick the role and the scheme supplies
  the right tone.
- **Static (baseline) vs dynamic**:
  - **Baseline** = the default static scheme (the classic M3 purple, seed
    ≈ `#6750A4`). Used as the **fallback** when dynamic color is unavailable.
  - **Static custom** = brand seed color chosen by the designer.
  - **Dynamic** = generated at runtime from wallpaper/content (Material You).
- **Contrast levels (2024)**: users/designers can pick **Standard**, **Medium**,
  or **High** contrast. Each level is a distinct full scheme (Material Theme
  Builder exports light+dark for all three). Higher levels push `on-` tones
  further from their backgrounds to raise contrast ratios.
- **2024 baseline scheme**: the color spec was refreshed in 2024 to add the
  `*-fixed*` roles and the three contrast levels, and to formalize the surface-
  container roles as the primary way to express elevation by color.

### 1.6 Accessible color: how tone maps to contrast

- Contrast is delivered by **tonal distance** (see 1.1): **ΔTone ≥ 40 ⇒ ≥ 3:1**
  (WCAG AA for large text / UI components), **ΔTone ≥ 50 ⇒ ≥ 4.5:1** (WCAG AA for
  normal text).
- Every `on-X` role is defined at a tone that clears the required distance from
  `X`, so **on-pairs are always accessible by construction**. Non-on pairings
  (e.g. two arbitrary roles) are **not** guaranteed and must be checked.
- The **High** contrast level exists for users who need ratios beyond AA.

---

## 2. Design-token architecture — the three tiers

M3 tokens are named **general → specific**, always starting `md.` (Material
Design). In CSS the dots become hyphens and gain a `--` prefix
(`md.sys.color.primary` → `--md-sys-color-primary`).

| Tier | Prefix | What it holds | Example names |
|---|---|---|---|
| **Reference** | `md.ref.*` | **Concrete literal values** — the raw palette swatches, base typefaces. The "paint tins." | `md.ref.palette.primary40`, `md.ref.palette.neutral99`, `md.ref.typeface.brand`, `md.ref.typeface.plain` |
| **System** | `md.sys.*` | **Semantic roles / design decisions** — points at a reference value and gives it a job. The stable API. | `md.sys.color.primary`, `md.sys.color.on-surface`, `md.sys.typescale.body-large`, `md.sys.shape.corner.medium`, `md.sys.elevation.level2`, `md.sys.state.hover-state-layer-opacity` |
| **Component** | `md.comp.*` | **Per-component attributes** — each points at a system token (or occasionally a literal). | `md.comp.filled-button.container.color`, `md.comp.filled-button.container.shape`, `md.comp.fab.container.elevation`, `md.comp.checkbox.selected.icon.color` |

**How they cascade:**

```
md.ref.palette.primary40  =  #6750A4      (concrete)
        ▲
md.sys.color.primary      →  md.ref.palette.primary40   (semantic role)
        ▲
md.comp.filled-button.container.color  →  md.sys.color.primary   (component)
```

**Why it matters for dynamic color:** when the wallpaper produces a new palette,
**only the reference tier changes** (`md.ref.palette.*` gets new hex values).
System tokens keep pointing at the same reference slots, and component tokens keep
pointing at the same system roles — so the whole UI recolors correctly with **no
component changes**. Reference tokens are the swap point; system tokens are the
stable contract; component tokens are the leaves.

> Web note: the `material-web` (MWC) implementation exposes reference typeface and
> **system + component** custom properties, but does **not** expose
> `--md-ref-palette-*` as live CSS vars; you theme via `--md-sys-*`. Its component
> tokens are named per component (e.g. `--md-filled-button-container-color`)
> rather than with a literal `comp` segment.

---

## 3. Typography — the M3 type scale

**5 roles × 3 sizes = 15 baseline styles** (M3 Expressive adds 15 "emphasized"
variants). Roles by intent: **Display** (largest, hero/expressive text) →
**Headline** (high-emphasis, shorter than display) → **Title** (medium-emphasis,
e.g. dialog/section titles) → **Body** (long-form reading text) → **Label**
(utilitarian: buttons, chips, captions).

**Default typefaces:** **Roboto** (`md.ref.typeface.plain` and historically
`brand`). M3 also standardizes on **Roboto Flex** (a variable font) so weight,
width, and optical size can be tuned continuously.

**Baseline type-scale values (Roboto):**

| Style | Weight | Size | Line height | Tracking (letter-spacing) |
|---|---|---|---|---|
| Display Large | Regular 400 | 57sp | 64 | −0.25 |
| Display Medium | Regular 400 | 45sp | 52 | 0 |
| Display Small | Regular 400 | 36sp | 44 | 0 |
| Headline Large | Regular 400 | 32sp | 40 | 0 |
| Headline Medium | Regular 400 | 28sp | 36 | 0 |
| Headline Small | Regular 400 | 24sp | 32 | 0 |
| Title Large | Regular 400 | 22sp | 28 | 0 |
| Title Medium | Medium 500 | 16sp | 24 | +0.15 |
| Title Small | Medium 500 | 14sp | 20 | +0.1 |
| Body Large | Regular 400 | 16sp | 24 | +0.5 |
| Body Medium | Regular 400 | 14sp | 20 | +0.25 |
| Body Small | Regular 400 | 12sp | 16 | +0.4 |
| Label Large | Medium 500 | 14sp | 20 | +0.1 |
| Label Medium | Medium 500 | 12sp | 16 | +0.5 |
| Label Small | Medium 500 | 11sp | 16 | +0.5 |

(Tracking is in **sp/px** here. In CSS `md-sys` typescale tokens tracking is often
expressed in rem, e.g. Body Large tracking 0.5px ≈ 0.03125rem.)

**Type tokens** — each style explodes into sub-property tokens:

- `md.sys.typescale.body-large.font` → `md.ref.typeface.plain` (Roboto)
- `md.sys.typescale.body-large.weight` → 400
- `md.sys.typescale.body-large.size` → 16sp
- `md.sys.typescale.body-large.line-height` → 24sp
- `md.sys.typescale.body-large.tracking` → 0.5

CSS form: `--md-sys-typescale-body-large-size`,
`--md-sys-typescale-body-large-line-height`, etc.

---

## 4. Shape

The **shape scale** defines corner roundedness. Baseline **7-step** scale:

| Shape role | Corner radius | Typical components |
|---|---|---|
| None | **0dp** | (square) — e.g. full-screen surfaces, some buttons |
| Extra small | **4dp** | menus, snackbars, text fields (top corners) |
| Small | **8dp** | chips, some cards |
| Medium | **12dp** | cards, small FABs |
| Large | **16dp** | FAB, extended FAB, navigation drawer, bottom sheets |
| Extra large | **28dp** | dialogs, large FAB, bottom sheets (top) |
| Full | **fully rounded** (radius = ½ height; often written **9999dp**) | buttons, chips, pill/stadium shapes, badges |

**Shape tokens:** `md.sys.shape.corner.none`, `.extra-small`, `.small`,
`.medium`, `.large`, `.extra-large`, `.full`. There are also directional variants
for rounding only some corners, e.g. `md.sys.shape.corner.extra-large.top`,
`md.sys.shape.corner.small.top`, `.bottom`, `.start`, `.end`. CSS:
`--md-sys-shape-corner-medium`.

**Component → shape mapping** is done via component tokens, e.g.
`md.comp.filled-button.container.shape` → `md.sys.shape.corner.full`;
`md.comp.card.container.shape` → `md.sys.shape.corner.medium`;
`md.comp.dialog.container.shape` → `md.sys.shape.corner.extra-large`.

> Implementation caveat: **`material-web`** ships a **reduced** shape set with
> different literals (`--md-sys-shape-corner-small: 4px`, `-medium: 6px`,
> `-large: 8px`). Those are MWC defaults, **not** the canonical M3 spec values
> above — treat the 0/4/8/12/16/28/full scale as the spec.

**M3 Expressive shape (2024–2025):** M3 Expressive greatly expands shape: a
larger library of ~**35 predefined shapes** and a finer **~10-step** corner
scale, plus **shape morphing** — components animate between shapes on interaction
(e.g. a button morphing its corners on press, or a loading indicator cycling
through shapes). Shape becomes an expressive/motion channel, not just a static
corner value.

---

## 5. Elevation & surfaces

M3 expresses elevation **two ways**, and **prefers tonal**:

1. **Tonal elevation (surface tint / color overlay)** — the higher a surface's
   elevation, the more it is tinted with **`surface-tint`** (= the **primary**
   color). No shadow required. This is why raised surfaces in an M3 app take on a
   subtle hue of the theme's primary. In the **2024** spec this is largely
   superseded by using the **surface-container roles** directly (pick
   `surface-container-high` instead of overlaying a tint) — cleaner and works the
   same in light/dark.
2. **Shadow elevation** — a traditional cast shadow using the `shadow` color.
   Reserve for elements that must clearly float above others (dialogs, menus) or
   to stop adjacent surfaces blending.

**The 6 elevation levels and their dp values:**

| Level | Elevation | Common usage |
|---|---|---|
| **Level 0** | **0dp** | flat components — filled/text buttons, outlined cards, chips at rest |
| **Level 1** | **1dp** | elevated cards; search bar (resting) |
| **Level 2** | **3dp** | navigation/top bars on scroll, menus, autocomplete |
| **Level 3** | **6dp** | FAB, extended FAB, dialogs, modal bottom sheets, rich tooltips |
| **Level 4** | **8dp** | navigation drawer; mostly hover/transient states |
| **Level 5** | **12dp** | mostly hover / dragged states, highest overlays |

**Elevation tokens:** `md.sys.elevation.level0` … `level5`. Components reference
them via `md.comp.<name>.container.elevation` (and separate `*.hover.container.
elevation`, `*.pressed.container.elevation`, etc.).

**Surface-container roles replace M2 elevation overlays.** In M2, elevation was
faked by overlaying white at increasing opacity on dark surfaces. M3 instead
gives you **named surfaces** (`surface-container-lowest` → `-low` → `-container`
→ `-high` → `-highest`) each at a fixed neutral tone, so "higher" surfaces are a
deliberate, accessible color choice rather than a computed overlay.

---

## 6. State layers (interaction states)

An interactive component shows its state via a **state layer**: a **semi-
transparent overlay of the content/`on-` color** placed between the container and
the content. It is a **fixed opacity per state**, so states compose consistently
across every component.

**States and their state-layer opacities (baseline):**

| State | State-layer opacity | Notes |
|---|---|---|
| **Enabled** (resting) | **0%** | no overlay |
| **Hover** | **8%** (0.08) | pointer over the component |
| **Focus** | **10%** (0.10) | keyboard/focus highlight |
| **Pressed** | **10%** (0.10) | plus a ripple from the contact point |
| **Dragged** | **16%** (0.16) | usually paired with an elevation bump (→ Level 4/5) |
| **Disabled** | — (no state layer) | see disabled treatment below |

**Disabled treatment** is different — it uses **content/container opacity**, not
a state layer:

- Disabled **content** (text/icon): **38%** opacity of the `on-` color.
- Disabled **container/fill**: **12%** opacity of the relevant color.
- Disabled outline: typically **12%** of on-surface.

**State tokens:** `md.sys.state.hover-state-layer-opacity` (0.08),
`md.sys.state.focus-state-layer-opacity` (0.10),
`md.sys.state.pressed-state-layer-opacity` (0.10),
`md.sys.state.dragged-state-layer-opacity` (0.16). The state-layer **color** is
chosen per component (usually `on-surface`, `primary`, or the relevant `on-`
role) via component tokens like
`md.comp.filled-button.hover.state-layer.color` +
`...hover.state-layer.opacity`.

State layers, elevation changes, and (in M3 Expressive) shape morphs are the
three channels a component uses to communicate interaction.

---

## Sources

Pages fetched or confirmed via search (official Google sources preferred).
Note: `m3.material.io` pages are client-rendered SPAs that return only a title to
WebFetch, so specifics were confirmed from Google's static docs (Android
developer site, `material-components` GitHub, `material-web.dev`) and cross-
checked search snippets.

- https://m3.material.io/styles/color/system/overview (color roles overview)
- https://m3.material.io/styles/color/system/how-the-system-works (HCT, tonal palettes)
- https://m3.material.io/foundations/design-tokens (three-tier tokens)
- https://m3.material.io/styles/typography/type-scale-tokens (type scale)
- https://m3.material.io/styles/shape/corner-radius-scale (shape scale)
- https://m3.material.io/styles/elevation/applying-elevation (elevation levels)
- https://m3.material.io/foundations/interaction/states/state-layers (state layers)
- https://developer.android.com/design/ui/wear/guides/styles/color/roles-tokens (fetched — color role enumeration + naming convention)
- https://material-web.dev/theming/color/ (fetched — `--md-sys-color-*` role tokens)
- https://github.com/material-components/material-web/blob/main/docs/theming/README.md (fetched — ref/sys/comp token tiers, examples)
- https://facelessuser.github.io/coloraide/colors/hct/ (HCT = CAM16 H,C + CIELAB L\* tone)
- https://github.com/material-foundation/material-color-utilities (reference HCT/palette implementation)

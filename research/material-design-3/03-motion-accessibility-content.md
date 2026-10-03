# Material Design 3 — Motion, Interaction, Accessibility & Content

Reference material for a specialist design-systems agent. Compiled 2026-07-22 from
m3.material.io and the Material Components Android (MDC) source docs, which mirror
the canonical `md.sys.motion.*` token values one-to-one. Note: m3.material.io is a
JS-rendered SPA that returns empty bodies to fetchers, so token values here were
confirmed against the MDC-Android motion reference doc (the authoritative
Google-owned mirror of the M3 motion spec — see Sources) and cross-checked with Flutter's
`Durations`/`Easing` classes. Values agree across all sources.

---

## 1. MOTION SYSTEM

M3 motion has two coexisting models today:

- **Classic M3 motion (2021–present)** — token-based, using **cubic-bezier easing
  curves + fixed durations**. Still the baseline and still valid.
- **Material 3 Expressive motion (announced May 2025)** — adds a **spring/physics
  motion system** (stiffness + damping), layered on top of (not replacing) the
  easing/duration tokens. Expressive is now the *recommended default* for new work
  in Compose M3 Expressive, but the cubic-bezier tokens remain in the spec.

### 1.1 Easing tokens (`md.sys.motion.easing.*`)

Easing is the acceleration/deceleration curve of an animation. M3 defines two
families — **Emphasized** (M3-styled, expressive, for prominent/hero transitions)
and **Standard** (utility, functional transitions) — each with a full, enter-only
(decelerate), and exit-only (accelerate) variant, plus **Linear** and a **Legacy**
(M2-compatibility) set.

| Token | cubic-bezier | Use |
|-------|--------------|-----|
| `emphasized` | **path-based**, not a single cubic-bezier | Default M3 curve for elements that begin *and* end on screen. Most transitions. |
| `emphasized.decelerate` | `cubic-bezier(0.05, 0.7, 0.1, 1.0)` | Elements **entering** the screen (persistent). |
| `emphasized.accelerate` | `cubic-bezier(0.3, 0.0, 0.8, 0.15)` | Elements **exiting** the screen (permanently leaving). |
| `standard` | `cubic-bezier(0.2, 0.0, 0.0, 1.0)` | Utility animations that begin and end on screen. |
| `standard.decelerate` | `cubic-bezier(0.0, 0.0, 0.0, 1.0)` | Utility elements **entering** the screen. |
| `standard.accelerate` | `cubic-bezier(0.3, 0.0, 1.0, 1.0)` | Utility elements **exiting** the screen. |
| `linear` | `cubic-bezier(0.0, 0.0, 1.0, 1.0)` | Simple non-stylized motion (e.g. continuous progress, opacity crossfades). |
| `legacy` | `cubic-bezier(0.4, 0.0, 0.2, 1.0)` | M2 "standard" curve, for backward compatibility. |
| `legacy.decelerate` | `cubic-bezier(0.0, 0.0, 0.2, 1.0)` | M2 decelerate. |
| `legacy.accelerate` | `cubic-bezier(0.4, 0.0, 1.0, 1.0)` | M2 accelerate. |

**Important nuance on `emphasized`:** the full emphasized curve is *not* expressible
as one cubic-bezier — it is a two-part path. MDC specifies it as an SVG-style path:
`M 0,0 C 0.05,0 0.133333,0.06 0.166666,0.4 C 0.208333,0.82 0.25,1 1,1`.
When a single cubic-bezier is required (e.g. CSS `transition-timing-function`),
Google's documented approximation is **`cubic-bezier(0.2, 0.0, 0.0, 1.0)`** (same as
`standard`), but for a truer feel the decelerate/accelerate split or a keyframed
path should be used. Do not report a single "emphasized cubic-bezier" as exact.

### 1.2 Duration tokens (`md.sys.motion.duration.*`)

Four bands (short/medium/long/extra-long), four steps each, 50–1000 ms.

| Token | ms | | Token | ms |
|-------|----|--|-------|----|
| `short1` | 50 | | `long1` | 450 |
| `short2` | 100 | | `long2` | 500 |
| `short3` | 150 | | `long3` | 550 |
| `short4` | 200 | | `long4` | 600 |
| `medium1` | 250 | | `extra-long1` | 700 |
| `medium2` | 300 | | `extra-long2` | 800 |
| `medium3` | 350 | | `extra-long3` | 900 |
| `medium4` | 400 | | `extra-long4` | 1000 |

**Rules of thumb:**
- **Short** — small utility transitions: state-layer/hover/selection, icon changes,
  switches, small components appearing/disappearing.
- **Medium** — components entering/exiting, expanding elements (chips, cards).
- **Long** — larger transitions crossing more of the screen.
- **Extra-long** — large/full-screen transitions. Longer durations are reserved for
  large surfaces so speed stays proportional to distance travelled.
- Exiting elements are generally *faster* than entering ones (accelerate vs
  decelerate easing pairs with shorter vs longer durations).

### 1.3 Transition patterns

M3 (inherited/refined from M2's "Material motion") defines four choreographed
patterns for moving between UI states/destinations:

1. **Container transform** — one element/container visually *morphs* into another
   (e.g. a card expands into a detail page, a FAB into a sheet). A persistent shared
   container grows/shrinks; contents cross-fade inside it. Use when there is a clear
   visual and logical relationship between the start and end surfaces. Strongest
   sense of continuity. Typically emphasized easing, medium–long duration.
2. **Shared axis** — start and end share a spatial/navigational relationship along
   **one axis**:
   - **X axis** — horizontal, for peer/sequential navigation (next/back steps, tabs,
     onboarding carousels).
   - **Y axis** — vertical, for up/down hierarchy or stepper flows.
   - **Z axis** — depth (scale + fade), for parent↔child navigation (drilling into a
     detail, opening from a launcher). Outgoing scales down/fades; incoming scales up.
   All three combine a directional translate/scale with a fade. Use when elements
   have a spatial or navigational relationship but are not the *same* container.
3. **Fade through** — outgoing element fades out **completely** (and slightly scales)
   *before* the incoming element fades in. Use when there is **no** strong
   relationship between the two states (e.g. switching bottom-nav destinations with
   unrelated content). Sequential, not simultaneous.
4. **Fade** — simple fade in/out, often with scale, for elements *entering or
   exiting within the bounds of the screen*: dialogs, menus, snackbars, elements
   appearing on top of existing UI. Use for UI that comes and goes without a spatial
   relationship to persistent content.

Choosing: *same element →* container transform; *related/sequential →* shared axis;
*unrelated swap →* fade through; *transient overlay →* fade.

### 1.4 Material 3 Expressive motion (spring / physics system, 2025)

Expressive replaces fixed curve+duration with **spring physics** for a more natural,
interruptible, device-appropriate feel. A spring is defined by:

- **Stiffness** — how quickly motion resolves (higher = faster, more energetic).
- **Damping ratio** — how quickly oscillation/bounce decays (1.0 = critically
  damped, no bounce; < 1.0 allows overshoot/bounce).
- **(Initial) velocity** — carried in from a gesture/fling for continuity.

Two **categories** × three **speeds**, giving six spring tokens
(`md.sys.motion.spring.*`):

- **Spatial** springs — for things that *move/resize/reshape* (position, size,
  scale, rotation). Configured with **damping ≈ 0.9** so they *overshoot slightly /
  bounce* — this is the source of Expressive's "spirited" feel.
- **Effects** springs — for **non-spatial** properties (color, opacity). Configured
  with **damping = 1.0** (critically damped, **no overshoot**) — bouncing color/
  opacity looks wrong.

MDC-Android exposes the concrete values (these are the phone/handset defaults;
Google notes exact numbers differ per form factor — wearable / phone / tablet — so
motion *feels* equally fast in context):

| Token | Damping | Stiffness | Scope of use |
|-------|---------|-----------|--------------|
| `spring.fast.spatial` | 0.9 | 1400 | Small components — switches, buttons, checkboxes. |
| `spring.fast.effects` | 1.0 | 3800 | Small-component color/opacity. |
| `spring.default.spatial` | 0.9 | 700 | Partial-screen — bottom sheets, nav drawer, expanding cards. |
| `spring.default.effects` | 1.0 | 1600 | Partial-screen effects. |
| `spring.slow.spatial` | 0.9 | 300 | Full-screen transitions. |
| `spring.slow.effects` | 1.0 | 800 | Full-screen effects. |

**Expressive vs Standard schemes:** Expressive documentation describes two schemes —
**Expressive** (lower damping, visible overshoot/bounce; recommended default, best
for hero moments and key interactions) and **Standard** (higher damping, minimal
bounce, calmer/utilitarian). "The expressive and standard schemes should be
sufficient for all motion needs."

**Accuracy note on what is "Expressive":** springs, the `spring.*` tokens, the
motion-physics model, and the two motion schemes are **Material 3 Expressive (2025)**.
The cubic-bezier easing set and the 50–1000 ms duration scale are **classic M3
(2021)** and remain in the spec — Expressive layers spring physics on top rather
than deleting them. Do not attribute the duration/easing tokens to Expressive, and
do not present springs as pre-2025.

---

## 2. INTERACTION & STATES

### 2.1 State layers

M3 visualizes interaction state with a **state layer**: a semi-transparent overlay
that uses the *same color as the content on top of it* (typically `on-surface`,
`primary`, etc.), applied at a **fixed opacity per state**. It sits between the
container and the content. Canonical opacities:

| State | State-layer opacity |
|-------|--------------------|
| Enabled / resting | 0% (no layer) |
| **Hover** | **8%** |
| **Focus** | **10%** |
| **Pressed** | **10%** |
| **Dragged** | **16%** |

(Some component specs and older M2 tables show focus/pressed at 12% — treat 8/10/10/16
as the M3 baseline and defer to the specific component spec when it differs.)

Behavior: **only one state layer is applied at a time.** If an element is focused and
then hovered, the hover layer shows until hover ends, then it returns to the focus
layer. Layers are *not* additive/stacked.

### 2.2 States covered

- **Enabled** — interactive, resting.
- **Disabled** — non-interactive; typically content at ~38% opacity, container at
  ~12%; no state layer.
- **Hover** — pointer over the target (pointer devices). Low-emphasis 8% layer.
- **Focus** — keyboard/programmatic focus. 10% layer **plus** a visible focus
  indicator (see Accessibility). Focus should be clearly distinguishable.
- **Pressed** — active touch/click. 10% layer combined with the **ripple**.
- **Dragged** — element being moved; state layer **plus an elevation increase** to
  lift it above surrounding content.
- **Selected / activated** — for toggles, selected list items, nav items (often
  paired with a color/emphasis change rather than only a state layer).

### 2.3 Ripple & touch feedback

- The **ripple** is M3's signature press feedback: a radial ink reaction that
  originates at the touch/click point and expands across the component, giving
  spatial confirmation of *where* the user touched. It is the pressed-state
  expression on top of the pressed state layer.
- Ripple is bounded (clipped to the component/container shape) or unbounded
  (e.g. icon buttons) depending on the component.
- **Gestures / touch feedback** — components should respond immediately to touch;
  swipe/drag gestures (dismissible chips, swipe-to-dismiss, bottom-sheet drag, slider
  thumb) carry velocity into the spring system under Expressive so the motion
  continues naturally from the gesture. Feedback should be immediate, targeted at the
  contact point, and reversible.

---

## 3. ACCESSIBILITY

M3 positions accessibility as *built in by default*, and is engineered toward
**WCAG 2.1/2.2** conformance.

### 3.1 Touch targets

- **Minimum touch target: 48 × 48 dp** for any interactive element, even when the
  visible component is smaller (the target extends beyond the visual bounds).
- ~48dp ≈ ~9mm of physical screen, comfortably operable by an average fingertip;
  this aligns with WCAG 2.5.5/2.5.8 target-size guidance and Android accessibility
  requirements.
- Adequate **spacing** between targets is required so adjacent controls aren't
  mis-tapped (M3 recommends spacing so targets don't overlap; ~8dp typical gap).

### 3.2 Color & contrast — guaranteed by the tonal system

- M3 color is built on **tonal palettes**: each key color is expanded into a tonal
  range with fixed **tones (0–100)**. Color **roles** are assigned specific tones,
  and the tone *distance* between a role and its "on-" pair is chosen to guarantee
  contrast.
- Because roles are defined by tone, an **`on-X` role is always contrast-safe against
  its `X` role** — e.g. `on-primary` vs `primary`, `on-surface` vs `surface` meet at
  least **WCAG AA (4.5:1)** for text by construction. This is why designers can pick
  a source color and get accessible schemes automatically.
- **Contrast targets:** normal text 4.5:1 (AA), large text 3:1, non-text/UI 3:1.
- **Contrast levels / high-contrast schemes:** M3 dynamic color supports selectable
  **contrast levels — Default, Medium, and High** — that regenerate the scheme with
  wider tonal separation. High-contrast schemes push role tones further apart to
  approach/meet **WCAG AAA (7:1)** for users who need it. Android exposes this as a
  system-level accessibility setting.

### 3.3 Type, dynamic type & content sizing

- M3 type scale is token-based (`display/headline/title/body/label`), which keeps
  hierarchy legible.
- Layouts must respect **dynamic/font scaling** — honor the OS font-size setting
  (Android `sp` units, iOS Dynamic Type). Text must reflow and containers grow
  without truncation or clipping when users enlarge text (large-text /
  content-size adaptation).
- Avoid fixed pixel heights on text containers; allow multi-line growth.

### 3.4 Focus, keyboard & indicators

- **Visible focus indicator** on the focused element (the focus state layer plus, for
  keyboard users, a clear focus ring/outline). Focus must never be invisible.
- **Logical focus order** — traversal order should follow reading/visual order and be
  predictable; group related controls.
- All interactive elements must be **keyboard operable** and reachable.

### 3.5 Screen readers (TalkBack / VoiceOver)

- Provide **content descriptions / accessible labels** for icons, icon buttons, and
  images (decorative elements should be marked to be skipped).
- In **Jetpack Compose**, expose meaning via **Semantics** properties (content
  description, role, state, `stateDescription`), merge semantics for composite
  components, and use live regions for dynamic updates.
- **TalkBack** (Android) and VoiceOver (iOS) are the target screen readers; announce
  state changes, and ensure custom components report role and state.
- **Spell words out** rather than abbreviating — abbreviations are hard for screen
  readers and low-literacy/non-native users.

### 3.6 Reduced motion

- Respect the user's **reduced-motion** preference (Android "Remove animations",
  iOS "Reduce Motion", CSS `prefers-reduced-motion`).
- When reduced motion is on: replace large spatial/parallax/spring transitions with
  simple **cross-fades** or instant state changes, remove non-essential
  decorative/looping animation, and shorten/disable large movements. Motion should
  never be the *only* way information is conveyed.

---

## 4. CONTENT DESIGN / UX WRITING

M3 content-design guidance lives under Foundations → Content design (overview +
style guide / UX-writing best practices). Core principles: **clear, concise,
consistent, and useful.**

### 4.1 Capitalization — sentence case

- **Use sentence case everywhere** — titles, headings, labels, menu items, nav items,
  app bar titles, dialog titles, **and button labels**. Only the first word (and
  proper nouns) is capitalized. M3 dropped M2-era ALL-CAPS button labels in favor of
  sentence case. (Title Case and ALL CAPS are avoided.)

### 4.2 Tone & voice

- **Clear, concise, and friendly-but-not-cute.** Write in a natural, human voice;
  avoid jargon, idioms, and unnecessary abbreviations (spell words out).
- Address the user directly ("you"); use active voice and present tense.
- Be **respectful and inclusive**; avoid blaming the user.
- Keep it **concise** — front-load the important information, cut filler, prefer short
  words and short sentences.

### 4.3 Button / action labels

- **Verb-led and specific** — describe the action/outcome ("Save changes", "Delete
  file", "Send"), not vague labels ("OK", "Submit", "Yes/No") where a specific verb
  is clearer.
- Sentence case; keep to ~1–3 words where possible.

### 4.4 Error messages

- Explain **what happened and how to fix it**, in plain language. State the
  **consequence of an action** clearly before the user commits.
- **Don't blame the user**; avoid technical codes/jargon as the primary message.
- Be specific and actionable; offer the next step or recovery path.

### 4.5 Empty states

- Use empty states to **orient and guide** — explain why the space is empty and give
  a clear next action (a primary action or brief instruction) rather than leaving a
  blank screen. Keep copy short and encouraging.

### 4.6 Iconography — Material Symbols

M3's icon system is **Material Symbols**, a **variable font** with **four axes**,
available in three styles: **Outlined, Rounded, Sharp**. ~2,500+ icons; every icon
supports all axes so a single glyph covers many states.

| Axis | Range | Notes |
|------|-------|-------|
| **Weight (`wght`)** | **100 (Thin) – 700 (Bold)**, default 400 | Stroke thickness; also affects overall size. Pair with the UI's text weight. |
| **Fill (`FILL`)** | **0 → 1** (0 = outlined, 1 = filled) | Animate/toggle between unfilled and filled to signal selection/emphasis (e.g. nav item selected). |
| **Grade (`GRAD`)** | **−25 to 200**, default **0** | Fine thickness adjustment, more granular than weight, minimal size impact. Use **−25** for light icons on dark backgrounds to keep optical weight consistent. |
| **Optical size (`opsz`)** | **20 – 48 dp**, default 24 | Adjusts stroke-to-size ratio so icons stay legible at their rendered size; match `opsz` to the actual display size. |

Guidance: keep icon style consistent across the product; use fill to denote
selected/active state; keep optical size matched to render size; ensure icons paired
with actions still meet the 48dp touch target and carry accessible labels.

### 4.7 Imagery

- Imagery should be **purposeful, relevant, and inclusive**; support the content
  rather than decorate.
- Respect **shape/containment** (M3 shape tokens) and elevation; apply appropriate
  aspect ratios and let images scale responsively.
- Provide **alt text / content descriptions** for meaningful images; mark purely
  decorative images to be ignored by assistive tech.
- Ensure text over imagery keeps sufficient contrast (scrims/overlays where needed).

---

## Sources

Fetched / searched 2026-07-22. m3.material.io pages are JS SPAs (empty to fetchers);
canonical token values confirmed via Google-owned MDC-Android docs and Flutter API,
which mirror `md.sys.motion.*`.

- https://m3.material.io/styles/motion/easing-and-duration/tokens-specs (easing & duration tokens — spec page)
- https://m3.material.io/styles/motion/ (motion overview / Expressive)
- https://m3.material.io/styles/motion/transitions/transition-patterns (transition patterns)
- https://raw.githubusercontent.com/material-components/material-components-android/master/docs/theming/Motion.md (authoritative cubic-bezier values, duration ms, spring damping/stiffness — Google-owned mirror)
- https://api.flutter.dev/flutter/material/Durations-class.html (duration values cross-check)
- https://m3.material.io/foundations/interaction/states/state-layers (state layers)
- https://m3.material.io/foundations/interaction-states (interaction states)
- https://m3.material.io/foundations/designing/structure (accessibility / structure)
- https://support.google.com/accessibility/android/answer/7101858 (48dp touch target)
- https://developer.android.com/design/ui/mobile/guides/foundations/accessibility (accessibility, TalkBack, Compose semantics)
- https://m3.material.io/styles/color/... (tonal palettes / contrast levels — Default/Medium/High)
- https://m3.material.io/foundations/content-design/overview (content design overview)
- https://m3.material.io/foundations/content-design/style-guide/ux-writing-best-practices (UX writing, sentence case)
- https://m3.material.io/styles/icons (Material Symbols icon system)
- https://m3.material.io/blog/introducing-symbols/ (Material Symbols axes: weight/fill/grade/optical size)
- https://developers.google.com/fonts/docs/material_symbols (Material Symbols axis ranges)
- https://m3.material.io/styles/motion/overview (Expressive spring scheme guidance — Expressive vs Standard)
- Supporting secondary confirmations: zoewave.medium.com (Compose M3 Expressive), supercharge.design/blog/material-3-expressive, note.com/howmanydesigns (M3 Expressive motion physics with CSS).

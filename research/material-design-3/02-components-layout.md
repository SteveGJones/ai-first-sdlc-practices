# Material Design 3 (M3) — Components, Layout & Adaptive Design

> Reference knowledge base compiled from official Google sources: `m3.material.io`,
> `developer.android.com`, and Android Developers Blog. Focus: component catalog,
> adaptive/responsive layout, navigation patterns, and the 2025 Material 3 Expressive update.
> Compiled 2026-07. Where a figure comes from Android's implementation docs it is noted.

---

## 1. Component Catalog

M3 organizes components into functional categories. The canonical grouping used on
`m3.material.io/components` and Android's component overview is: **Actions, Communication,
Containment, Navigation, Selection, Text inputs.** Below is the full enumerated set with
notes on the highest-value components.

### 1.1 Actions — "help people achieve an aim"

**Common buttons** (5 variants, ordered high → low emphasis):
- **Filled** — solid background, highest emphasis; the primary/most important final action ("Save", "Confirm").
- **Filled tonal** — filled with a secondary/tonal color; a middle-ground between filled and outlined. Good for a secondary action that still needs prominence.
- **Elevated** — outlined-style container with a shadow (elevation). Use when a button needs separation from a busy/colored/image background. Use sparingly.
- **Outlined** — stroked outline, no fill; medium-low emphasis, often paired next to a filled button.
- **Text** — text only, no container until interacted with; lowest emphasis, for the least-pronounced actions (e.g. dialog dismiss, "Learn more").
- *Anatomy:* container + label text (+ optional leading icon). *Usage:* only one high-emphasis (filled) button per view group; match emphasis to action importance.

**FAB — Floating Action Button** (the single most important/primary action on a screen):
- **Regular FAB**, **Small FAB**, **Large FAB** (size variants), and **Extended FAB** (FAB + text label).
- **FAB menu** *(Expressive, 2025)* — opens a small menu of related actions from any FAB size/color; replaces the old anti-pattern of stacking multiple secondary FABs.
- *Anatomy:* container + icon (+ label for extended). *Usage:* one primary FAB per screen; use for a constructive, screen-level action (compose, create, add). Not for destructive or minor actions.

**Icon buttons** — compact, symbol-only actions. Variants: **standard** and **toggle** (selected/unselected states); filled / filled-tonal / outlined / standard styling treatments. Used in app bars, cards, list items.

**Segmented buttons** — a linear group letting users select among related options; single-select or multi-select. Replaces M2 toggle buttons. Good for 2–5 related choices (e.g. view switches, filters).

**Button groups** *(Expressive, 2025)* — a row of related buttons; **standard** and **connected** variants. Connected groups only change the *shape* of the selected button (no cross-button interaction).

**Split button** *(Expressive, 2025)* — a two-part button: a **leading** button (primary action) + a **trailing** button (contextually related secondary action / menu trigger). The trailing part animates (spins/morphs shape) when activated.

### 1.2 Communication — "provide helpful information"
- **Badges** — small numeric/dot indicators (e.g. on nav items or icons) to signal new/unread items.
- **Progress indicators** — **linear** and **circular**; each **determinate** or **indeterminate**.
- **Loading indicator** *(Expressive, 2025)* — new component for waits under ~5s (e.g. pull-to-refresh); intended to replace most indeterminate circular progress uses.
- **Snackbars** — brief, transient messages at the bottom about an app process; optionally one action. Not for critical info requiring acknowledgement (use a dialog).
- **Tooltips** — **plain** (brief label) and **rich** (title + body + optional action) contextual hints.

### 1.3 Containment — "hold information and actions"
- **Cards** — group related content + actions into a single container. Variants: **elevated** (drop shadow), **filled** (subtle tonal fill, least emphasis), **outlined** (stroked boundary, greatest emphasis/definition). *Usage:* pick one variant per context; cards can contain any content — text, media, buttons.
- **Carousel** — scrollable set of visually prominent items (often images); supports hero/large-item layouts and dynamic item resizing.
- **Dialogs** — modal windows demanding a decision or focused sub-task. Variants: **basic** (title + supporting text + up to two text-button actions) and **full-screen** (mobile, for complex tasks requiring confirmation/save, e.g. create event). *Usage:* interrupt only for high-signal info or required choices.
- **Dividers** — thin lines (**full-width** or **inset**) separating content, often within lists.
- **Lists** — vertical index of one-, two-, or three-line rows; each row can hold leading/trailing icons, avatars, images, controls (switch/checkbox), metadata. *Anatomy:* container + list items (leading element, headline/supporting text, trailing element). *Usage:* the workhorse for scannable content; keep line count consistent within a list.
- **Bottom sheets** — surfaces anchored to the screen bottom holding secondary content/actions. Variants: **standard** (coexists with main content) and **modal** (scrim, blocks interaction; a mobile alternative to menus/dialogs). *Usage:* modal bottom sheet is the mobile-friendly place for the "supporting" content of a supporting-pane layout.
- **Side sheets** — surfaces anchored to the screen's side (left/right) for supplementary content/actions on larger windows; **standard** and **modal**.

### 1.4 Navigation — "help people move through the UI"
- **Navigation bar** — bottom bar with 3–5 top-level destinations; **compact & medium** widths only (see §3). *Anatomy:* 3–5 items, each icon (active/inactive) + label + optional badge. *Usage:* 3–5 destinations; fewer than 3 → use tabs; more than 5 → use a rail/drawer.
- **Navigation rail** — vertical strip of destinations at the side; **medium widths and larger**. Can pair with a FAB/menu button at top. A **modal/expanded rail** handles >5 destinations.
- **Navigation drawer** — side panel listing destinations, supports grouping/headers/many items. Variants: **modal** (`ModalNavigationDrawer`, scrim, for compact) and **standard/permanent** (`PermanentNavigationDrawer`, persistent on large/expanded windows). *Usage:* best when there are many destinations or destinations need labels/grouping.
- **Top app bar** — title + navigation + actions at the top of a screen. **4 variants:** **small**, **center-aligned**, **medium** (larger, title below actions row), **large** (largest, prominent title). Small/center-aligned for standard screens; medium/large for hero/section headers; supports scroll behaviors (title collapses on scroll). *Anatomy:* leading (nav/back) icon + title + trailing action icons + optional overflow.
- **Bottom app bar** — bottom container holding actions (and often a FAB) for the current screen; for primary actions rather than top-level navigation.
- **Tabs** — organize/switch between peer content groups within one screen; **primary** (top-level, with icon+label options) and **secondary** (nested); **fixed** or **scrollable**.
- **Search** — search bar (persistent entry point) and search view (full-screen input + suggestions/results surface).

### 1.5 Selection — "let people specify choices"
- **Checkbox** — multi-select from a set, or a single on/off with an indeterminate state.
- **Radio button** — single mutually-exclusive selection from a set.
- **Switch** — toggle a single item's on/off state; takes immediate effect (no confirm).
- **Chips** — compact elements for input, attributes, or actions. **4 types:** **assist** (smart/suggested action, e.g. "Set reminder"), **filter** (toggle filters on a set of content), **input** (represent user-entered info such as contacts/tags, removable), **suggestion** (dynamically generated recommendations to narrow intent). *Anatomy:* container + label (+ optional leading icon/avatar, trailing remove/close icon). *Usage:* match type to purpose; filter chips are selectable/toggleable, input chips are dismissible.
- **Sliders** — select a value or range along a track; **continuous** or **discrete** (with tick stops), single or range (two thumbs).
- **Menus** — temporary lists of choices/actions on a surface (dropdown/exposed dropdown, context menus).
- **Date pickers** — **docked**, **modal**, and **modal input**; single date or range.
- **Time pickers** — **dial** and **input** modes.

### 1.6 Text inputs
- **Text fields** — let users enter/edit text. **2 variants:** **filled** (shaded container, stronger visual weight — good on plain backgrounds/when field should stand out) and **outlined** (stroked container, lighter weight — good on busy layouts/dense forms). *Anatomy:* container + label (floats on focus) + input text + optional leading/trailing icon + supporting/helper text + optional character counter; supports error state, prefix/suffix. *Usage:* be consistent — don't mix filled and outlined in the same form.

---

## 2. Adaptive & Responsive Layout

### 2.1 Window size classes / Breakpoints

M3 (and Android) classify the *window* (not the physical device) by available **width** and
**height** independently — at any moment an app has one width class and one height class. Google
renamed "window size classes" to **breakpoints** in the current M3 docs, but the class names are
unchanged and **Large** + **Extra-large** were added to target desktop/connected displays.

**Width breakpoints** (source: Android `use-window-size-classes`):

| Class | Width range (dp) | Represents |
|---|---|---|
| **Compact** | `< 600` | ~99.96% of phones in portrait |
| **Medium** | `600 ≤ w < 840` | Most tablets in portrait; large unfolded inner displays in portrait |
| **Expanded** | `840 ≤ w < 1200` | Most tablets in landscape; unfolded inner displays in landscape |
| **Large** | `1200 ≤ w < 1600` | Large tablet / desktop displays |
| **Extra-large** | `≥ 1600` | Large desktop / connected displays |

**Height breakpoints** (Android supports compact/medium/expanded for height):

| Class | Height range (dp) |
|---|---|
| **Compact** | `< 480` (≈99.78% of phones in landscape) |
| **Medium** | `480 ≤ h < 900` |
| **Expanded** | `≥ 900` |

**Design rule of thumb:** most apps can adapt using **width alone**. Compact width → single pane;
medium/expanded/large/xl → multi-pane. Height matters mainly for edge cases (phone/foldable in
landscape = medium width but compact height, where two-pane layouts aren't practical). Panes
typically scale: single pane → two panes (large) → up to three panes (extra-large).

### 2.2 Canonical layouts

Three reusable, opinionated layouts, each with compact/medium/expanded configurations. Implemented
in Compose as adaptive scaffolds (`ListDetailPaneScaffold`, `SupportingPaneScaffold`, and a
`LazyVerticalGrid`-based feed).

- **List-detail** — two side-by-side panes: a **list** and the selected item's **detail**.
  - Expanded/large: both panes visible; selecting a list item updates the detail pane in place.
  - Compact/medium: only one pane at a time — selecting an item replaces the list with the detail; Back returns to the list.
  - *Use for:* messaging, contacts, email, settings, media browsers — anything "browse a list, drill into an item."
- **Supporting pane** — a dominant **primary** area plus a **supporting** secondary pane whose content is meaningful only relative to the primary.
  - Expanded: ~70/30 split (primary/supporting). Medium: ~50/50. Compact: supporting content moves into a bottom sheet, side sheet, or behind a menu/button.
  - *Use for:* document + comments/reviewer notes, video + related-videos/up-next, editor + tools/properties palette.
- **Feed** — equivalent content elements (usually **cards**, sometimes lists) in a resizable grid for scanning lots of content quickly. Size/position group and emphasize elements.
  - Column count adapts to width (`GridCells.Adaptive(minSize = …dp)`); compact ≈ single column, medium 2+, expanded multi-column. Headers/dividers span full width (`maxLineSpan`).
  - *Use for:* news, social feeds, photo galleries, dashboards, store fronts.

### 2.3 Grid, units, spacing, margins

- **Base grid:** an **8dp grid** governs most layout, sizing, and spacing; a finer **4dp grid** governs small elements (icons, type, component internals). Keep measurements to multiples of 4/8dp.
- **Units:** use **dp** (density-independent px, 160dpi reference) for layout; **sp** for font sizes (respects user text-size accessibility settings). `dp = (px × 160) / density`.
- **Layout grid** has three columns/margins/gutters that flex per breakpoint. Grid types: **column grid** (vertical columns, count changes per breakpoint), **modular grid** (uniform cells for equal-weight content like card galleries), **hierarchical grid** (variable cells reflecting content importance).
- **Panes** are the building block of multi-pane layouts; a scaffold arranges one, two, or three panes with pane spacing driven by the breakpoint. Fixed vs flexible panes let one pane hold width while another fills remaining space.
- **Margins/gutters** widen as the window grows (compact uses the tightest margins; expanded and above use wider margins and can introduce a max content width so line lengths stay readable on very wide displays). Exact per-breakpoint margin/column dp values live in the M3 "Applying layout" / "Layout basics" spec pages.

### 2.4 Foldables & large screens
- Design to **window size classes, not device types** — a foldable's inner display in landscape is just "expanded width," an outer cover screen is "compact."
- Support **table-top / book postures and hinges**: avoid placing interactive targets across the fold; Compose exposes trifold/landscape-foldable helpers for hinge-aware layouts.
- Preserve **state across configuration changes** (fold/unfold, rotate, resize, multi-window): e.g. expanded→medium should keep the detail visible and hide the list, not reset selection.
- Use the extra space to **reveal panes** (list-detail, supporting pane) rather than merely stretching a phone layout.

---

## 3. Navigation Patterns (choosing the nav UI)

M3 selects the navigation component by **width breakpoint** and **destination count**. The Compose
`NavigationSuiteScaffold` automates this — it swaps navigation bar ⇄ rail ⇄ drawer based on the
`WindowSizeClass` at runtime while you declare destinations once via `navigationSuiteItems`.

**By width breakpoint:**

| Width class | Recommended navigation UI |
|---|---|
| **Compact** | **Navigation bar** (bottom). Do not use a standard rail (too little horizontal space). |
| **Medium** | **Navigation rail** (side) preferred; navigation bar still acceptable. Rail preserves vertical content space. |
| **Expanded / Large / Extra-large** | **Navigation rail**, or a **standard/permanent navigation drawer** when destinations are numerous or need labels/grouping. Not a bottom navigation bar. |

**By destination count (for the bottom navigation bar):**
- **< 3 destinations** → don't use a nav bar; use **tabs**.
- **3–5 destinations** → **navigation bar** is ideal.
- **> 5 destinations** → don't use a nav bar (labels collide, no room for translated text); use a **navigation drawer** or a **modal/expanded navigation rail**.

**Primary vs secondary navigation:**
- **Primary navigation** = movement between the app's top-level destinations → nav bar / rail / drawer.
- **Secondary navigation** = movement *within* a destination or section → **tabs** (peer content groups) or in-content links.
- Keep the two distinct: don't mix top-level destinations into tabs, or nest whole sections into a bottom bar.

---

## 4. Material 3 Expressive (2025 update)

**What it is:** The 2025 evolution of Material 3, **announced at Google I/O 2025 (May 13, 2025)**.
It is an *expansion of*, not a replacement for, Material 3 / Material You — same tokens and theming
foundation, with new components plus more expressive shape, color, typography, and motion. Goal:
convey personality and improve usability (clearer emphasis, faster target recognition).

**Research behind it:** Google's largest design research effort for the system — **46 studies**,
hundreds of design variations, and **18,000+ participants**. Findings: expressive designs rated
higher on playfulness/creativity/friendliness, and users located key UI elements **up to ~4×
faster** than with the more uniform prior style.

**New components introduced (5 headline additions):**
1. **FAB menu** — expandable menu of actions from any FAB (replaces stacked secondary FABs).
2. **Button groups** — rows of related buttons; **standard** and **connected** variants (connected only reshapes the pressed button).
3. **Split button** — leading primary + trailing secondary/menu button that animates (spin/shape morph) on activation.
4. **Loading indicator** — for sub-5-second waits (e.g. pull-to-refresh); replaces most indeterminate circular spinners.
5. **Toolbars** — new floating/docked action toolbars (a flexible container of actions, distinct from the app bar).

Google's materials describe roughly **15 new or refreshed UI elements** overall — the five above
plus refinements to existing components (app bars, navigation bar/rail, etc.).

**Updated styling systems:**
- **Shape:** an expanded **shape library (~35 shapes)** with **shape morphing** (shapes animate/morph between states, e.g. on press). Buttons gain a **square ⇄ round** shape treatment.
- **Buttons (Expressive sizing):** five sizes — **xsmall, small, medium, large, xlarge** — plus the round/square shape toggle, giving far more range than classic M3's single button height.
- **Motion:** a new **physics-based motion system** built on **springs**. Spring tokens are defined by **stiffness** (higher = faster settle), **damping** (higher = less bounce; 1 = no bounce), and **initial velocity** (affects duration). Motion schemes ship as tokens for Compose and Android Views so motion is consistent and "alive."
- **Color & type:** refreshed dynamic color roles with clearer hierarchy; bolder/larger headline typography and stronger type hierarchy.

**Availability / rollout:**
- **Jetpack Compose:** landed in the **`androidx.compose.material3:material3:1.4.0`** line (Expressive APIs first in `1.4.0-alpha` builds, e.g. `1.4.0-alpha10`). Also came to **Wear OS** (Material 3 Expressive for Wear, Aug 2025) and MDC-Android spring tokens.
- **Android / first-party:** shipped on **Pixel 6 and newer** with **Android 16** via the **QPR1** update (~September 2025); Google's first-party apps adopted it through end of 2025.

**Expressive vs classic M3 — quick disambiguation:**
- *Classic M3 components* (still current): common buttons, standard/small/large/extended FAB, icon buttons, segmented buttons, cards, chips, text fields, app bars, nav bar/rail/drawer, tabs, dialogs, sheets, pickers, sliders, switches, snackbars, tooltips, progress indicators.
- *Expressive-only additions/changes:* **FAB menu, button groups, split button, loading indicator, toolbars**, the **5-size + round/square button system**, the **~35-shape morphing library**, and the **spring-based motion system**.

---

## Sources

- https://m3.material.io/components (component catalog)
- https://developer.android.com/design/ui/mobile/guides/components/material-overview (component categories & variants)
- https://m3.material.io/components/all-buttons (buttons, FAB, icon/segmented buttons, Expressive sizes/shapes)
- https://m3.material.io/components/buttons/guidelines
- https://m3.material.io/components/chips/specs (assist/filter/input/suggestion chips)
- https://m3.material.io/components/cards/guidelines (elevated/filled/outlined cards)
- https://m3.material.io/components/dialogs/specs
- https://m3.material.io/components/bottom-sheets/overview (standard/modal)
- https://m3.material.io/components/navigation-bar/guidelines (destination-count rules)
- https://m3.material.io/components/navigation-rail/guidelines
- https://m3.material.io/components/navigation-drawer/overview (modal/permanent)
- https://m3.material.io/components/app-bars/specs (small/center/medium/large top app bar)
- https://m3.material.io/components/segmented-buttons/overview
- https://m3.material.io/components/button-groups/specs (standard/connected — Expressive)
- https://developer.android.com/develop/ui/views/layout/use-window-size-classes (exact dp breakpoints, width & height)
- https://m3.material.io/foundations/layout/breakpoints/overview
- https://m3.material.io/foundations/layout/applying-layout/window-size-classes
- https://developer.android.com/develop/adaptive-apps/guides/canonical-layouts (list-detail / supporting pane / feed)
- https://m3.material.io/foundations/layout/canonical-examples/overview
- https://m3.material.io/foundations/layout/scaffold/panes
- https://developer.android.com/design/ui/mobile/guides/layout-and-content/grids-and-units (4dp/8dp grid, dp/sp, grid types)
- https://developer.android.com/develop/adaptive-apps/guides/build-adaptive-navigation (NavigationSuiteScaffold, nav by size class)
- https://m3.material.io/blog/building-with-m3-expressive (Expressive overview)
- https://m3.material.io/blog/m3-expressive-motion-theming (spring motion system)
- https://m3.material.io/styles/motion/ (motion tokens)
- https://developer.android.com/jetpack/androidx/releases/compose-material3 (material3 1.4.0 availability)
- https://android-developers.googleblog.com/2025/08/introducing-material-3-expressive-for-wear-os.html
- https://www.androidauthority.com/google-material-3-expressive-features-changes-availability-supported-devices-3556392/ (I/O 2025 announcement, 46 studies / 18,000 participants, rollout timeline)

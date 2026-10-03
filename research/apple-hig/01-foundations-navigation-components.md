# Apple Human Interface Guidelines — Foundations, Layout, Navigation & Components (iOS / iPadOS)

> Reference knowledge base for an `apple-hig-architect` specialist agent.
> Grounded in Apple's official Human Interface Guidelines (HIG) and the WWDC 2025 / iOS 26 "Adopting Liquid Glass" technology overview.
> Sourced from `developer.apple.com/design/human-interface-guidelines` (fetched via Apple's DocC JSON endpoints) and Apple developer documentation.
> Captured 2026-07 (current shipping design language = **Liquid Glass**, iOS 26). Point values are from Apple's own tables where given.
>
> **Legend for "new in 2025" flags:** 🆕 = introduced with Liquid Glass / iOS 26 (WWDC 2025). Everything else is long-standing HIG that remains current.

---

## 1. Design principles & foundations

### The classic tenets (clarity, deference, depth)
Apple's long-standing iOS design themes — **Clarity, Deference, Depth** — were introduced with iOS 7 (the "flat" redesign) and still frame Apple's thinking. As of the iOS 26 HIG, Apple no longer presents them as three numbered bullets on the platform page; instead **Deference and Depth are now literally embodied by the Liquid Glass material** (translucent controls that defer to content; a distinct floating control layer that establishes depth). Treat clarity/deference/depth as the enduring philosophy and Liquid Glass as its current material expression.

### How Apple actually frames "designing for iOS" today
The `designing-for-ios` page frames the platform around device character rather than a slogan:
- **Display:** "iPhone has a medium-size, high-resolution display."
- **Ergonomics:** held in one or both hands; viewing distance "no more than a foot or two"; users switch between portrait and landscape.
- **Inputs:** Multi-Touch, virtual keyboards, voice control — "while they're on the go."
- **App interactions:** sessions range from a minute (checking updates) to an hour (media/games); people keep multiple apps open and switch frequently.
- **System features:** widgets, Home Screen quick actions, Spotlight, Shortcuts, activity views.

**What makes an app "feel at home" on iOS** (verbatim guidance):
- "Great iPhone experiences integrate the platform and device capabilities that people value most."
- **Content focus:** "limit the number of onscreen controls while making secondary details and actions discoverable with minimal interaction."
- **Adaptive design:** "Adapt seamlessly to appearance changes — like device orientation, Dark Mode, and Dynamic Type."
- **Ergonomic interaction:** support the way people hold the device — "let people swipe to navigate back or initiate actions in a list row."
- **Platform integration:** with permission, pull in system data instead of asking people to type it.

### The 18 Foundations topics
Accessibility, App Icons, Branding, Color, Dark Mode, Icons, Images, Immersive Experiences, Inclusion, Layout, Materials, Motion, Privacy, Right to Left, SF Symbols, Spatial Layout, Typography, Writing.

### Platform differences (iOS vs iPadOS vs macOS)
- **iOS (iPhone):** compact-first; single window; tab bar at the **bottom**; navigation is drill-down via nav bars; touch ergonomics dominate.
- **iPadOS:** larger canvas → **sidebars**, **split views**, multiple windows, pointer/keyboard support, Split View / Slide Over multitasking, resizable windows. Tab bar sits **near the top**. 🆕 In iOS 26 the tab bar and sidebar are the same control (`sidebarAdaptable`) that morphs by width.
- **macOS:** window-and-menu-bar model, full menu bar, resizable/movable windows, denser information, pointer-first. Avoid putting critical controls at window bottom (windows get dragged off-screen).
The design goal is one recognizable app that **adapts** across size classes rather than three separate designs.

---

## 2. Liquid Glass (iOS 26 / WWDC 2025) — the 2025 design language 🆕

**What it is (Apple's definition):** Liquid Glass is a **new dynamic material** that "combines the optical properties of glass with a sense of fluidity." It is a **translucent material that reflects and refracts its surroundings** and dynamically transforms to bring focus to content. Announced at **WWDC 2025 (June 9, 2025)** and shipping in **iOS 26** — Apple's most significant visual overhaul since iOS 7. It is a **unified** language across iOS, iPadOS, macOS (Tahoe), tvOS, watchOS, and visionOS, and was inspired by the depth/dimensionality of visionOS, enabled by newer silicon/GPU.

**The core structural idea — a floating control layer:** Liquid Glass "forms a distinct functional layer for controls and navigation elements (tab bars, sidebars) that floats above the content layer," establishing clear hierarchy while content scrolls and **peeks through beneath**. This is the depth principle made literal.

**Two variants:**
- **Regular** — blurs and adjusts luminosity of the background to keep foreground legible; scroll-edge effects blur/reduce opacity at edges. Most system components use this. Use when background could hurt legibility or a component has significant text (alerts, sidebars, popovers).
- **Clear** — highly translucent, prioritizes seeing the content behind; ideal floating over media (photos/video). For bright backgrounds, add a **35% dark dimming layer**; over dark content / AVKit media controls, no dimming needed.
- By default **Liquid Glass has no inherent color** — it takes color from the content directly behind it. Apply tint sparingly (status indicators, primary actions).

**What changed vs the prior flat design:**
- Navigation bars, **tab bars**, toolbars, sidebars, and controls now render as translucent glass floating over content instead of opaque flat bars.
- Controls get refreshed behavior: **slider/toggle knobs transform into Liquid Glass on interaction**; buttons **fluidly morph into menus and popovers**; rounder forms; a new **extra-large** size option; corners align concentrically with the window.
- 🆕 **Tab bars minimize on scroll** (shrink to give content focus; re-expand on tap or scroll-to-top).
- App icons gain Liquid Glass attributes (specular highlights, refraction, translucency) — see §7.

**How designers/developers adopt it:**
- "Take advantage of this material with minimal code by using standard components from SwiftUI, UIKit, and AppKit." Standard components adopt it automatically when you build with the latest SDK.
- **Remove custom backgrounds** from split views, tab bars, toolbars, navigation elements, and controls — let the system supply the glass appearance.
- **Custom glass:** SwiftUI `View.glassEffect(_:in:)`, button styles `.glass` / `.glassProminent`; UIKit `UIGlassEffect`, `UIButton.Configuration.glass()` / `.prominentGlass()` / `.clearGlass()`; AppKit `NSGlassEffectView`, `NSButton.BezelStyle.glass`. Batch multiple custom glass elements in a `GlassEffectContainer` for correct blending/performance. **Use sparingly** — reserve for the most important functional elements.
- **Don't put Liquid Glass in the content layer** (exception: transient inline controls like sliders/toggles). Use **standard materials** for app backgrounds.
- **Adopt supporting APIs:** `.tabBarMinimizeBehavior(.onScrollDown)`, `.backgroundExtensionEffect()` (content appears to extend beneath sidebars/inspectors), `.scrollEdgeEffectStyle(_:for:)` / `.safeAreaBar(...)`, and concentric-corner shapes (`ConcentricRectangle`, `Shape.rect(corners:isUniform:)`, UIKit `UICornerConfiguration`).
- **Accessibility:** the material honors **Reduce Transparency** and **Reduce Motion**; test with those plus VoiceOver.
- **Backwards compatibility / opt-out:** set the `UIDesignRequiresCompatibility` Info.plist key to keep pre-iOS-26 appearance temporarily.

---

## 3. Layout

### Safe areas & margins
- **Safe area** = the region not covered by bars (navigation/toolbar/tab bar) and hardware intrusions (**Dynamic Island**, camera housing, home indicator, corner radii). Respect it. APIs: SwiftUI `.safeAreaInset()` / `SafeAreaRegions`; UIKit `UILayoutGuide`, `safeAreaInsets`, `NSLayoutGuide`.
- The system provides predefined **layout guides** for standard margins and for readable text width.
- 🆕 **Background extension view** (`View.backgroundExtensionEffect()` / `UIBackgroundExtensionView`) makes content appear to continue beneath a sidebar or inspector.

### Spacing / the grid
- iOS layout follows an **8-point grid** convention: standard spacing in multiples of 8 (8, 16, 24, 32 pt).
- **Minimum tap target: 44 × 44 pt** for any control (visionOS: 60 × 60 pt) — "a button needs a hit region of at least 44×44 pt … to ensure people can select it easily."

### Adaptivity & size classes
- **Size classes** are **Regular** (larger screen or landscape) and **Compact** (smaller screen or portrait), independently on width and height.
  - iPhone (standard, e.g. 16 Pro) — portrait: **compact width, regular height**; landscape: **compact width, compact height**.
  - iPhone Plus / Pro Max — landscape becomes **regular width, compact height**.
  - iPad (e.g. 12.9″) — **regular width, regular height** in both orientations.
- Design principle: "Design a layout that adapts gracefully to context changes while remaining recognizably consistent." Respect system safe areas/margins/guides.
- Adapt to: screen sizes/resolutions/color spaces, orientation, Dynamic Island / camera controls, external displays, Display Zoom, resizable iPad windows, **Dynamic Type**, and localization (RTL, text length).
- **Testing:** preview on multiple devices, orientations, localizations, and text sizes; test largest and smallest configs first; if landscape is supported, test both rotation directions.

### iPad multitasking, Split View / Slide Over, orientation
- iPad windows are freely resizable down to a minimum; account for the full range of window sizes; windows can fill halves, thirds, or quadrants.
- **"Defer switching to compact view for as long as possible"** — design the full-screen layout first, collapse to compact only when it no longer fits; for split views, hide tertiary columns (inspectors) first as width shrinks.
- 🆕 **Convertible tab bar / sidebar:** `TabViewStyle/sidebarAdaptable` launches as sidebar or tab bar and switches automatically with view width.
- **Orientation (iOS):** "Aim to support both portrait and landscape." If landscape-only, work equally when rotated left or right; don't instruct users to rotate.
- **Buttons:** "Avoid full-width buttons"; respect system margins and inset from screen edges; if full-width is needed, align with safe areas and hardware curvature.
- **Status bar:** keep visible; hide "only when it adds value" (immersive games/media).

### Screen sizes (points, portrait) — selected current devices
- **iPhone 17 Pro Max / 16 Pro Max:** 440 × 956 pt (@3x, 1320 × 2868 px)
- **iPhone 17 Pro / 17 / 16 Pro:** 402 × 874 pt (@3x)
- **iPhone Air:** 420 × 912 pt (@3x)
- **iPhone 16 Plus / 15 Pro Max:** 430 × 932 pt (@3x)
- **iPhone 16:** 393 × 852 pt (@3x); **iPhone 16e / 15-class base:** 390 × 844 pt
- **iPhone SE (4.7″) / 8:** 375 × 667 pt (@2x)
- **iPad Pro 13″:** 1032 × 1376 pt (@2x); **iPad Pro 12.9″:** 1024 × 1366 pt (@2x)
- **iPad Air 11″ / iPad 11″:** 820 × 1180 pt (@2x); **iPad mini 8.3″:** 744 × 1133 pt (@2x)

### Dynamic Island / notch
Treated as a device interactive/display feature the **safe area** already accounts for. Keep primary content and controls out of it; for full-bleed games/media, accommodate corner radius, sensor housing, and the Dynamic Island.

---

## 4. Navigation & structure

Three primary navigation models + a set of modal presentations.

### Tab bars (flat / peer navigation of top-level sections)
- **Purpose:** "help people understand the different types of information or functionality an app provides … quickly switch between sections while preserving the current navigation state within each section." (e.g. Clock's Alarm / Stopwatch / Timer).
- **Navigation, not actions:** "Use a tab bar to support navigation, not to provide actions." For actions on the current view, use a **toolbar**.
- **Placement:** iOS — **floats at the bottom** on a Liquid Glass background that content peeks through; iPadOS — **near the top**; visionOS — vertical, fixed to the window's leading side.
- **Count:** use as few as convey the app's hierarchy — "generally easier to navigate among fewer tabs." If customizable, default to **five or fewer** for continuity between compact and regular sizes.
- 🆕 **Sidebar-adaptable:** a tab bar can convert to a sidebar (`sidebarAdaptable`); 🆕 **minimize-on-scroll** with an inline accessory (e.g. Music MiniPlayer); a dedicated **search tab** can sit at the trailing end.

### Navigation bars + navigation stacks (hierarchical / drill-down)
- In iOS a navigation-specific toolbar is the **navigation bar**, appearing at the **top**; it "helps people move through a hierarchy of content."
- **Title:** give each view a concise title (**under ~15 characters**) confirming location; **don't title with the app name**.
- **Large titles:** "Use a large title to help people stay oriented." By default a large title transitions to a standard inline title as content scrolls, and back to large at the top. UIKit: `UINavigationBar.prefersLargeTitles`.
- **Back / Close:** use the **standard** Back (retrace hierarchy) and Close (dismiss modal) controls and standard symbols; don't relabel them "Back"/"Close." Custom versions must look and behave the same.

### Sidebars (iPad / regular width)
- "A sidebar appears on the leading side … lets people navigate between areas of your app or top-level collections of content (folders, playlists)."
- **Space cost:** needs lots of vertical and horizontal space; when space is limited, a **tab bar** may be better.
- **Recommendation:** "Consider using a tab bar first"; expose overflow areas via the tab bar's convertible sidebar appearance. Often you needn't choose — adopt the `sidebarAdaptable` tab style that provides both.
- **Deep hierarchies (>2 levels):** use a **split view** with a content list column between the sidebar and the detail view.

### Modality — choosing the right presentation
- **Sheets** — a card that slides up over the parent.
  - **Modality:** on macOS/tvOS/visionOS/watchOS always **modal**; on **iOS/iPadOS** can be **modal or nonmodal** (a nonmodal sheet affects the parent without being dismissed — e.g. Notes formatting).
  - **Detents** (iOS/iPadOS): heights where a sheet rests — **large** (fully expanded, default) and **medium** (~half height). "Consider supporting the medium detent to allow progressive disclosure" (share sheet). API: `UISheetPresentationController.detents`.
  - **Grabber:** include a grabber in a resizable sheet (drag to resize, tap to cycle detents, works with VoiceOver). API: `prefersGrabberVisible`.
  - **When not to use:** for complex/prolonged flows or media/editing, prefer the **full-screen modal** style instead.
- **Popovers** — "a transient view that appears above content when people tap a control/area." Small amount of info/functionality; a few related tasks; **arrow points at the originating element**. Nonmodal by default (dismisses on outside tap); can be kept open for multi-select. **iOS/iPadOS rule:** "Avoid displaying popovers in compact views" — reserve popovers for **wide (iPad) views**; in **compact (iPhone) views present a sheet / full-screen modal** instead. (This adaptivity is automatic with SwiftUI `.popover`.)
- **Alerts** — "usually unexpected," telling people about a problem or change that might need action; confirm/cancel only, **no additional related choices**. Keep buttons minimal.
- **Action sheets** — "Use an action sheet — not an alert — to offer choices related to an **intentional** action" (e.g. save vs. delete a draft). Destructive button at **top**; **Cancel at bottom**; avoid scrolling — fewer buttons is better. (Not supported in visionOS; watchOS max ~4 buttons incl. Cancel.)
- **Full-screen modal** — for immersive/multistep tasks (video, camera, document/photo editing).

### Search patterns
- If search is important, **give it a primary position**: a dedicated **search tab** at the trailing end of the tab bar (Photos, Apple TV), or a search field in a prominent toolbar (Notes).
- **Single searchable location** per app; local/section search can act as a **filter on the current view** (Music).
- **Show scope** via placeholder text, a **scope bar**, or a title. Support **scope bars and tokens**.
- **Suggestions:** show recent searches before typing and predictive suggestions while typing (SwiftUI `.searchSuggestions(_:)`). Respect privacy — offer a way to clear search history.

---

## 5. Typography

### System font: San Francisco (SF)
- Families: **SF Pro** (primary UI), SF Compact, SF Mono, plus script-specific SF Arabic/Armenian/Georgian/Hebrew, and rounded variants; **New York** (NY) is the system serif.
- **Variable font** with **dynamic optical sizing** — historically split into **SF Pro Display** (larger) and **SF Pro Text** (smaller) optical sizes, now interpolated continuously. Weights **Ultralight → Black**; widths Condensed/Expanded.
- **Use the system fonts by default** (don't embed them). Prefer **Regular, Medium, Semibold, Bold**; avoid Ultralight/Thin/Light at small sizes.

### iOS / iPadOS text styles (type scale) — Large (default) size
| Text style | Weight | Size (pt) | Leading (pt) | Emphasized weight |
|---|---|---|---|---|
| Large Title | Regular | 34 | 41 | Bold |
| Title 1 | Regular | 28 | 34 | Bold |
| Title 2 | Regular | 22 | 28 | Bold |
| Title 3 | Regular | 20 | 25 | Semibold |
| Headline | **Semibold** | 17 | 22 | Semibold |
| Body | Regular | 17 | 22 | Semibold |
| Callout | Regular | 16 | 21 | Semibold |
| Subhead | Regular | 15 | 20 | Semibold |
| Footnote | Regular | 13 | 18 | Semibold |
| Caption 1 | Regular | 12 | 16 | Semibold |
| Caption 2 | Regular | 11 | 13 | Semibold |

- **iOS default body = 17 pt; minimum = 11 pt.** (macOS default 13/min 10; watchOS 16/12; tvOS 29/23; visionOS 17/12.)
- Roles: **Large Title / Titles** for screen and section headers; **Headline** to emphasize a row's primary line; **Body** for reading content; **Callout/Subhead** for supporting text; **Footnote/Caption** for metadata and secondary annotations.

### Dynamic Type (a first-class requirement)
- Users scale text system-wide (including large Accessibility sizes). **Use the built-in text styles** to get Dynamic Type automatically; custom fonts must implement the same scaling behavior (SwiftUI "Applying Custom Fonts to Text").
- Layout must adapt at **all** sizes: minimize truncation, keep information hierarchy consistent, and scale meaningful interface icons alongside text. Supported on iOS/iPadOS/tvOS/visionOS/watchOS (not macOS).
- Leading control: loose leading for wide/long passages, tight leading for constrained rows — but avoid tight leading for 3+ lines. SwiftUI `Font.leading(_:)`. Emphasis via symbolic traits (`Text.bold()` / `UIFontDescriptor.SymbolicTraits.traitBold`) rather than size changes where possible.

---

## 6. Color & materials

### System & semantic (dynamic) colors
- Use **system colors** — they look right on varied backgrounds, adapt to light/dark/increased-contrast, vibrancy, and accessibility. **Don't hard-code system color values**; apply via API (SwiftUI `Color`). Documented values are for design reference only.
- **Dynamic system colors** are defined by **semantic purpose, not appearance**, and auto-adapt to light/dark. Don't redefine their meaning.
- **iOS/iPadOS backgrounds — two sets:**
  - System: `systemBackground`, `secondarySystemBackground`, `tertiarySystemBackground`.
  - Grouped (for grouped tables): `systemGroupedBackground`, `secondarySystemGroupedBackground`, `tertiarySystemGroupedBackground`.
  - Hierarchy: primary = overall view; secondary = groups within the view; tertiary = groups within secondary.
- **Foreground/semantic labels:** `label`, `secondaryLabel`, `tertiaryLabel`, `quaternaryLabel`, `placeholderText`, `separator`, `opaqueSeparator`, `link`.
- **System grays:** `systemGray` and `systemGray2…systemGray6` (SwiftUI `Color.gray` ≈ `systemGray`).
- **Unified SwiftUI named colors** (light/dark/high-contrast variants each): red, orange, yellow, green, mint, teal, cyan, blue, indigo, purple, pink, brown.
- **Tint/accent:** a prominent button uses the app's **accent color**; a destructive button uses **system red**. macOS 11+ supports app accent colors (user's system accent can override).

### Dark Mode
- Systemwide dark palette for low-light comfort. **Every color must work in light, dark, and increased-contrast** contexts — semantic colors handle this automatically. Test under varied lighting and on different displays (True Tone, etc.).

### Materials & vibrancy
- **Materials** create depth/layering by separating foreground (text/controls) from background (content). Two categories: **Liquid Glass** (control/navigation layer — see §2) and **standard materials** (differentiation within the content layer).
- **iOS/iPadOS standard materials (thickness):** `ultraThin` (mostly translucent) → `thin` → `regular` (default) → `thick` (mostly opaque). macOS adds "chrome"-style/vibrant named materials; visionOS uses `glass`.
  - Thicker = better text/contrast; thinner = retains more background context.
- **Vibrancy** amplifies/adjusts foreground color so it stays legible on a material. Use **system-defined vibrant colors** (they work on any material): label vibrancy `label / secondaryLabel / tertiaryLabel / quaternaryLabel` (avoid quaternary on thin/ultraThin), fills `fill / secondaryFill / tertiaryFill`, and `separator`. Choose materials/effects by **semantic meaning**, not apparent color.
- APIs: SwiftUI `Material`, `View.glassEffect(_:in:)`; UIKit `UIVisualEffectView`, `UIBlurEffect`, `UIVibrancyEffect`; AppKit `NSVisualEffectView`.

### Contrast & accessibility of color
- **Never rely on color alone** to convey status, interactivity, or essential info — add text labels, glyph shapes, or other indicators.
- Ensure sufficient contrast so icons/text don't blend with backgrounds; consider cultural color meanings (Stocks uses green-up in English, red-up in Chinese).
- **Wide color (Display P3, 16-bit, PNG)** for richer color on capable displays; provide sRGB fallbacks where P3 could clip.

---

## 7. Iconography & imagery

### SF Symbols
- **SF Symbols 7** (shipping with iOS 26): a library of **over 6,900** consistent, highly configurable symbols that integrate with the San Francisco font and **auto-align with text at all weights and sizes**.
- **9 weights** (Ultralight → Black), each matching an SF font weight for precise pairing; **3 scales** (Small, Medium [default], Large) defined relative to the SF **cap height**.
- **Rendering modes:** **Monochrome** (one color), **Hierarchical** (one color, opacity varies by layer depth), **Palette** (2+ colors, one per layer), **Multicolor** (intrinsic meaningful colors, e.g. green `leaf`, red `trash.slash`).
- **Variable color** expresses changing values (0–100%) — e.g. `speaker.wave.3` mapping wave layers to volume ranges.
- 🆕 SF Symbols 7 adds **Draw** animations, improved **Magic Replace**, gradients, and variable rendering.
- Prefer existing symbols for common actions (e.g. `square.and.arrow.up` for Share).

### App icons
- **1024 × 1024 px**, square canvas; the **system applies the rounded-rectangle mask** — keep content centered.
- 🆕 **Layered / Liquid Glass icons (iOS 26):** background layer + foreground layer(s); the system applies **specular highlights, refraction, translucency** that adapt with size — **don't bake in your own shadows/highlights/bevels/glows**. Prefer clearly-defined edges and vector art (SVG/PDF); vary foreground opacity for depth.
- **Icon Composer** (ships with Xcode) assembles layers and previews the **six appearance variants**: Default, Dark, Clear Light, Clear Dark, Tinted Light, Tinted Dark. Keep features consistent across variants; base the dark icon on the light one.
- Design tips: embrace simplicity; use filled overlapping shapes; minimize text; prefer illustration over photos; don't replicate Apple hardware. Color spaces: sRGB, Gray Gamma 2.2, Display P3.

### Imagery
- Deliver assets at the correct scale factors (@2x for iPad, @3x for most iPhones); use PDF/SVG vectors where possible; apply color profiles (sRGB or P3); respect safe areas for full-bleed art.

---

## 8. Core components (and SwiftUI/UIKit mapping)

### Buttons
- **Roles:** Normal (no meaning), **Primary** (default / most-likely choice; uses **accent color**), Cancel, **Destructive** (uses **system red**). Never assign the *primary* role to a destructive action.
- **Style, not size,** distinguishes the preferred choice; keep prominent buttons to **one or two per view**; always include a **press state** for custom buttons.
- **Minimum hit region 44 × 44 pt.**
- 🆕 **Liquid Glass button styles:** SwiftUI `.buttonStyle(.glass)` / `.glassProminent`; UIKit `UIButton.Configuration.glass() / .prominentGlass() / .clearGlass() / .prominentClearGlass()`; AppKit `NSButton.BezelStyle.glass`. Classic SwiftUI styles remain: `.plain`, `.bordered`, `.borderedProminent`, `.borderless`. Buttons can show an inline activity indicator during async work.

### Controls (map to SwiftUI / UIKit)
- **Switch** — `Toggle` / `UISwitch` (binary on/off).
- **Slider** — `Slider` / `UISlider` (continuous range); 🆕 knob morphs to Liquid Glass on drag.
- **Stepper** — `Stepper` / `UIStepper` (discrete increment/decrement).
- **Segmented control** — `Picker(.segmented)` / `UISegmentedControl`: 2+ equal-width segments for **closely related** choices affecting an object/state/view; use **text OR images, not both**; **≤5 segments on iPhone** (≤5–7 in wide interfaces); keep all segments selection-type or all action-type, not mixed.
- **Pickers** — `Picker` / `UIPickerView` / date pickers (wheel, menu, inline, compact, wheel-of-values).

### Lists & tables
- **iOS/iPadOS styles** (SwiftUI `ListStyle`): `.plain`, `.grouped`, `.insetGrouped`, `.sidebar` — **grouped/inset-grouped** "uses headers, footers, and additional space to separate groups" (the Settings pattern). macOS bordered style uses alternating row backgrounds; watchOS elliptical/carousel.
- Keep row text succinct to reduce truncation; use leading images + brief labels; use **disclosure indicators** (not info buttons) for navigation.
- Support **edit mode** (reorder/add/remove) and **swipe actions** on rows; give clear selection feedback (persistent highlight for hierarchical rows; brief highlight + checkmark for option rows).

### Forms & text input
- **Text fields** — `TextField` / `UITextField` (single line); **`placeholderText`** semantic color for placeholders; 🆕 gain Liquid Glass treatment. Configure keyboard type, content type (autofill), and return key.
- **Forms** — SwiftUI `Form` groups labeled controls; typically rendered as inset-grouped lists on iOS.
- **Search bars** — `.searchable(...)` / `UISearchController`; adapt placement per §4; support scopes, tokens, suggestions.

### Toolbars, context menus, and Liquid Glass integration
- **Toolbars** provide **actions on the current view** (vs tab bars for navigation); at top or bottom; 🆕 adopt Liquid Glass and support grouping and per-item hide (`ToolbarContent.hidden(_:)`, `UIBarButtonItem.isHidden`).
- **Context menus** — long-press/right-click menus for contextual actions (SwiftUI `.contextMenu` / UIKit `UIContextMenuInteraction`).
- 🆕 To get the Liquid Glass look, **remove custom backgrounds** from these standard components and let the system render the material; add supporting APIs (`scrollEdgeEffectStyle`, `backgroundExtensionEffect`, concentric corners) as needed.

---

## Quick-reference constants
- **Tap target:** 44 × 44 pt (visionOS 60 × 60).
- **Grid:** 8-pt spacing system (8/16/24/32).
- **iOS body text:** 17 pt default, 11 pt minimum; Large Title 34 pt.
- **Nav title length:** aim < 15 characters.
- **Tab count:** ≤5 default (customizable).
- **Segments:** ≤5 on iPhone.
- **Sheet detents:** medium (~½) and large (full).
- **App icon:** 1024×1024 px, system-masked; 6 appearance variants.
- **SF Symbols:** 6,900+ symbols, 9 weights, 3 scales, 4 rendering modes + variable color.
- **Clear Liquid Glass dimming:** 35% over bright content.

---

## Sources (URLs fetched)
Apple HIG pages were retrieved via Apple's DocC JSON data endpoints (`.../tutorials/data/design/human-interface-guidelines/<page> (JSON data endpoint)`), which back the JS-rendered pages at the public URLs below.

- https://developer.apple.com/design/human-interface-guidelines — HIG home
- https://developer.apple.com/design/human-interface-guidelines/foundations
- https://developer.apple.com/design/human-interface-guidelines/designing-for-ios
- https://developer.apple.com/design/human-interface-guidelines/layout
- https://developer.apple.com/design/human-interface-guidelines/materials
- https://developer.apple.com/design/human-interface-guidelines/color
- https://developer.apple.com/design/human-interface-guidelines/typography
- https://developer.apple.com/design/human-interface-guidelines/sf-symbols
- https://developer.apple.com/design/human-interface-guidelines/app-icons
- https://developer.apple.com/design/human-interface-guidelines/tab-bars
- https://developer.apple.com/design/human-interface-guidelines/navigation-bars (served under toolbars)
- https://developer.apple.com/design/human-interface-guidelines/sidebars
- https://developer.apple.com/design/human-interface-guidelines/sheets
- https://developer.apple.com/design/human-interface-guidelines/popovers
- https://developer.apple.com/design/human-interface-guidelines/action-sheets
- https://developer.apple.com/design/human-interface-guidelines/searching
- https://developer.apple.com/design/human-interface-guidelines/buttons
- https://developer.apple.com/design/human-interface-guidelines/segmented-controls
- https://developer.apple.com/design/human-interface-guidelines/lists-and-tables
- https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass — Liquid Glass adoption (WWDC 2025)
- https://9to5mac.com/2025/06/11/apple-releases-sf-symbols-7-beta/ — SF Symbols 7 (6,900+ symbols) corroboration
- https://www.engadget.com/big-tech/wwdc-2025-ios-26-new-liquid-glass-design-and-everything-else-apple-announced-171718769.html — WWDC 2025 / iOS 26 announcement
- https://techcrunch.com/ (Apple "Liquid Glass" unified design coverage) — announcement corroboration

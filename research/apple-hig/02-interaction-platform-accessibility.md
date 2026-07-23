# Apple Human Interface Guidelines — iOS Interaction, Platform UX Features & Accessibility

Reference material for the **apple-hig-architect** agent. Sourced primarily from Apple's official HIG
(`developer.apple.com/design/human-interface-guidelines`), fetched via Apple's page-data JSON API
(the HIG site is a JS SPA; the human-readable content lives at
`developer.apple.com/tutorials/data/design/human-interface-guidelines/<page> (JSON data endpoint)`). Direct Apple
quotes are marked with quotation marks. Verified July 2026. See **Sources** at the end.

> Scope note: this document is deliberately iOS/iPadOS-centric but retains cross-platform facts
> (watchOS/macOS/visionOS) where they clarify a rule. When advising an iOS app, ignore the
> other-platform rows unless the app is genuinely multiplatform.

---

## 1. Interaction & Inputs

### 1.1 Standard system gestures

Apple's core principle: **use standard gestures for standard actions, and don't overload familiar
gestures with unique meanings.** "In general, respond to gestures in ways that are consistent with
people's expectations." "Give people more than one way to interact with your app" — never make a
gesture the *only* way to reach an important action.

Standard gestures and their conventional actions (iOS/iPadOS):

| Gesture | Conventional action |
|---|---|
| **Tap** | Activate a control; select an item |
| **Swipe** | Reveal actions/controls; dismiss views; scroll |
| **Drag** | Move a UI element |
| **Touch (or pinch) and hold** ("long press") | Reveal additional controls/functionality (context menus, previews) |
| **Double tap** | Zoom in / zoom out |
| **Zoom / pinch** | Zoom a view; magnify content |
| **Rotate** | Rotate a selected item |
| **Edge swipe from left** | System **back / pop** navigation (the interactive pop gesture in a navigation stack) |
| **Three-finger swipe** | Undo (left) / redo (right) |
| **Three-finger pinch** | Copy (pinch in) / paste (pinch out) |
| **Four-finger swipe** (iPadOS) | Switch between apps |
| **Shake** | Undo / redo |

**Swipe-back / edge swipe:** The left-edge swipe to pop the current view is a system convention
provided free by `UINavigationController` / SwiftUI `NavigationStack`. Do not break it with custom
edge gestures; if you add an interactive drawer/edge control, it competes with system back and Notification
Center/Control Center edge pulls. Apple's rule: **"Avoid conflicting with gestures that access system UI."**

**Custom-gesture caution (Apple's four constraints):** "Add custom gestures only when necessary." Custom
gestures must be **discoverable, straightforward to perform, distinct from other gestures**, and **never
the only way to perform an important action.** Also: "Make custom gestures easy to learn," "Use shortcut
gestures to *supplement* standard gestures, not replace them," and "Handle gestures as responsively as
possible" (give continuous feedback that communicates the extent/type of movement required). "Indicate
when a gesture isn't available."

### 1.2 Touch targets (the 44×44 pt rule)

The single most-cited iOS interaction number: **minimum comfortable hit target is 44×44 pt on iOS/iPadOS.**
From the Accessibility guidance ("offer sufficiently sized controls"):

| Platform | Default control size | Minimum control size |
|---|---|---|
| **iOS, iPadOS** | **44×44 pt** | 28×28 pt |
| watchOS | 44×44 pt | 28×28 pt |
| tvOS | 66×66 pt | 56×56 pt |
| visionOS | 60×60 pt | 28×28 pt |
| macOS | 28×28 pt | 20×20 pt |

Note the nuance: 44×44 pt is the **default/recommended** target; Apple lists a 28×28 pt hard floor, but
44 pt remains the number to design to. Spacing matters as much as size: "add about **12 points of padding**
around elements that include a bezel"; for elements without a bezel, "**about 24 points of padding** works
well around the element's visible edges." (These same padding numbers appear in the iPad pointer guidance
for comfortable hit regions.)

Points vs pixels: 1 pt = 1 px @1x, 2 px @2x, 3 px @3x. Design in points; Apple scales for device density.

### 1.3 Pointer / trackpad interaction on iPad (iPadOS)

iPadOS turns the pointer into an **adaptive, magnetic** cursor rather than a desktop arrow. Three
system **content effects**:

- **Highlight** — pointer morphs into a translucent rounded-rectangle background behind the control, with
  gentle parallax. Default for bar buttons, tab bars, segmented controls, edit menus. Use for small
  transparent-background elements.
- **Lift** — pointer fades out beneath the element while iPadOS scales the element up, adds a shadow and a
  specular highlight (floating look). Default for app icons and Control Center buttons. Use for small
  opaque-background elements. Specify a corner radius via `UIPointerShape.roundedRect(_:radius:)` for
  non-standard shapes.
- **Hover** — generic custom scale/tint/shadow effect without transforming the pointer; use for large
  elements. Does **not** apply magnetism by default.

**Pointer magnetism** pulls the cursor toward targets (applied by default to lift/highlight elements and
text-entry areas; not to hover). The pointer auto-switches to an **I-beam** over text. Best practices:
prefer system pointer appearances; keep custom pointer shapes simple and non-decorative ("Avoid creating
gratuitous pointer and content effects"); create contiguous hit regions for custom bar buttons; support
band (rubber-band) multi-selection via `UIBandSelectionInteraction`. Provide a **consistent experience
across touch, pointer, keyboard, and eyes** — "people expect to move fluidly between multiple types of
input."

### 1.4 Hardware keyboard support & shortcuts

A physical keyboard "can be an essential input device" and connects to every device except Apple Watch;
iPad users often attach one. Rules:

- **Respect standard shortcuts; don't repurpose them.** Command-C/V/Z/A/S/F/N/P/Q, Command-Tab, Tab/Shift-Tab,
  Escape all carry system meaning — "don't repurpose standard keyboard shortcuts for custom actions."
- **Command (⌘)** is the primary modifier for custom shortcuts; **Shift (⇧)** for a secondary/complementary
  shortcut; **Option (⌥)** sparingly for power features; **avoid Control (⌃)** (system-reserved). List
  modifiers in order **Control, Option, Shift, Command.**
- Define custom shortcuts only for "the most frequently used app-specific commands." Don't invent an
  unrelated shortcut by adding a modifier to a known one (e.g. Shift-Command-Z must remain redo).
- Let the system localize and RTL-mirror shortcuts automatically.
- **Full Keyboard Access** (iOS/iPadOS/macOS/visionOS accessibility feature) lets people drive the entire
  UI from the keyboard — "support Full Keyboard Access when possible." On iPadOS, don't hand-roll keyboard
  navigation for individual controls; rely on Full Keyboard Access to reach them.
- SwiftUI: `KeyboardShortcut`, `.keyboardShortcut(_:modifiers:)`; UIKit: `UIKeyCommand`.

### 1.5 Apple Pencil

Not covered in the Keyboards page. Relevant Pencil facts surface elsewhere: **squeezing Apple Pencil Pro can
invoke App Shortcuts**, and Apple advises against continuous/long-lasting **haptics** on Apple Pencil Pro
("continuous or long-lasting haptics don't tend to clarify the writing or drawing experience and can even
make holding the pencil less pleasant"). For a Pencil-first drawing/notes app, design for low-latency
inking, palm rejection, hover preview (Pencil hover on supported iPads), and double-tap / squeeze tool
switching — but always provide non-Pencil fallbacks.

### 1.6 Drag and drop

Source → destination. Rule of thumb: **same container = move; different container = copy; between apps =
always copy.** Guidance:

- "Support drag and drop throughout your app" (system text views/fields get it free) and **offer
  alternative ways** to accomplish the same thing (menu commands).
- Support **multi-item** drag; use **drag flocking** (visually group multiple items, ungroup on drop).
- Prefer letting people **undo** a drop; confirm irreversible drops.
- **Feedback:** show a translucent drag image once the finger moves ~3 pt; highlight/insertion-point only
  where the destination can accept the item; show `circle.slash` or no feedback where it can't; on a failed
  drop, animate the item back to source or "evaporate" it (scale up + fade).
- **Spring loading:** dragging content over a control (button/segmented control) activates it — on iPad by
  **hovering while holding** the content, on Mac by force-click. Example: Calendar's toolbar day/week/month
  segments.

---

## 2. Haptics (the iOS haptics system)

"Playing haptics can engage people's sense of touch and bring their familiarity with the physical world
into your app." iOS ships three semantic feedback families via **`UIFeedbackGenerator`** subclasses, plus
**Core Haptics** for fully custom patterns.

### 2.1 Standard iOS haptic types

**Notification** (`UINotificationFeedbackGenerator`) — outcome of a task:
- **Success** — a task/action completed
- **Warning** — produced a warning
- **Error** — an error occurred

**Impact** (`UIImpactFeedbackGenerator`) — physical-metaphor collisions ("a tap when a view snaps into
place… a thud when two heavy objects collide"):
- **Light / Medium / Heavy** — collision of small / medium / large UI objects
- **Rigid / Soft** — hard/inflexible vs soft/flexible objects

**Selection** (`UISelectionFeedbackGenerator`) — "feedback while the values of a UI element are changing"
(e.g. spinning a picker).

### 2.2 Core Haptics (custom)

For custom patterns (mostly games, occasionally delight in apps). Building blocks:
- **Transient events** — brief taps/impulses (e.g. the Flashlight button tap).
- **Continuous events** — sustained vibrations (e.g. the Messages "lasers" effect).
- Every event has **sharpness** (soft/rounded/organic ↔ crisp/precise/mechanical) and **intensity**
  (strength). Patterns can vary **dynamically** with input/context.

### 2.3 When haptics are appropriate vs overused (Apple's rules)

1. **Use system patterns per their documented meaning** — don't repurpose a standard pattern to mean
   something else; use a generic/custom pattern instead.
2. **Be consistent** — build a clear causal relationship; the same pattern must not signal both a positive
   and negative outcome.
3. **Complement other feedback** — match haptic intensity/sharpness to the accompanying animation; sync
   with sound.
4. **Avoid overuse** — "Sometimes a haptic can feel just right when it happens occasionally, but become
   tiresome when it plays frequently… the best haptic experience is one that people may not be conscious
   of, but miss when it's turned off."
5. **Prefer short haptics for discrete events**; long-running haptics dilute meaning in apps.
6. **Make haptics optional** — the app must remain fully usable with haptics off/muted.
7. **Beware physical side effects** — vibration can disrupt the camera, gyroscope, or microphone.

**Platform APIs:** UIKit `UIFeedbackGenerator` (iOS/iPadOS); `Core Haptics` (custom, iPhone with the Taptic
Engine); watchOS `WKHapticType`; macOS `NSHapticFeedbackPerformer` (Magic Trackpad: Alignment / Level Change
/ Generic patterns). Accessibility tie-in: pair audio cues with haptics for people who can't hear them
(`Music Haptics` exists as a media-accessibility feature).

---

## 3. Motion

"Beautiful, fluid motions bring the interface to life… conveying status, providing feedback and
instruction." Core principles:

- **Add motion purposefully** — "Don't add motion for the sake of adding motion. Gratuitous or excessive
  animation can distract people and may make them feel disconnected or physically uncomfortable."
- **Make motion optional** — never the *only* channel for important information; supplement with haptics
  and audio.
- **Realistic, expectation-consistent feedback** — if a view arrives by sliding down from the top, it should
  leave the same way, not sideways.
- **Brief and precise** — short animations "feel lightweight and unobtrusive" and often convey information
  better than prominent animation.
- **Avoid motion on frequent interactions** — the system already animates standard controls subtly; don't
  make people watch unnecessary motion every time.
- **Let people cancel motion** — don't force people to wait for an animation to finish, especially on repeat.
- **Animated SF Symbols** (SF Symbols 5+) are a sanctioned, lightweight motion tool.
- Games: target a consistent **30–60 fps**; let people trade visual richness for performance/battery.

### 3.1 Reduce Motion (accessibility)

People sensitive to fast/blinking motion (dizziness, up to epileptic episodes) enable **Reduce Motion.**
When it's on, the app must:
- Reduce automatic/repetitive animation (zooming, scaling, peripheral motion)
- **Tighten animation springs** to cut bounce
- Track animations directly to the user's gesture
- Avoid animating **z-axis depth** changes
- **Replace x/y/z transitions with fades**
- Avoid animating into/out of blurs

Check the flag: SwiftUI `@Environment(\.accessibilityReduceMotion)`; UIKit `UIAccessibility.isReduceMotionEnabled`
(+ `.reduceMotionStatusDidChangeNotification`). Related: **Dim Flashing Lights** setting (respond to it in
video playback), and `UIAccessibility.isVideoAutoplayEnabled`.

---

## 4. iOS-Specific UX Patterns & Platform Features

This is the section that most distinguishes an iOS designer from a generic mobile designer.

### 4.1 Onboarding

"Ideally, people can understand your app simply by experiencing it." When onboarding is needed, make it
"**fast, fun, and optional**," and it happens **after** launch (it is not the launch experience). Rules:
teach through **interactivity** (let people do the task, not read about it); prefer **context-specific tips**
near the relevant UI over one long upfront flow; keep it brief; make separate tutorials skippable and never
re-shown if skipped (but findable later); **postpone non-essential setup** and ship sensible defaults;
**don't display licensing/legal** in onboarding (let the App Store do that); and **defer rating/purchase
prompts** until people are engaged. If the app genuinely needs a permission to function, fold that request
into onboarding so you can explain the benefit.

### 4.2 Requesting permissions & privacy

"Privacy is paramount." Apple's permission model is a **just-in-time, purpose-explained** one.

Data/resources that require explicit permission: location, health, contacts, photos, camera, microphone,
Bluetooth, local network, HomeKit, calendars, Face ID, motion, the **advertising identifier / tracking**,
and (visionOS) ARKit data.

**Core rules:**
- **Request only what a feature needs, only when the feature is used.** "Avoid requesting permission at
  launch unless the data or resource is required for your app to function" (navigation apps are the classic
  launch-time exception).
- **Purpose strings** (the `NS…UsageDescription` Info.plist keys) are mandatory and must clearly say *why*:
  a brief, specific, complete sentence in sentence case, active voice, ending with a period. Good: "The app
  records during the night to detect snoring sounds." Bad: "Microphone access is needed for a better
  experience." Missing/weak purpose strings are a **rejection** cause.
- **Priming screens** shown *before* the system alert may contain **exactly one button** that clearly leads
  to the system alert (label it "Continue"/"Next", **never "Allow"**), with **no other action** (no cancel).

**App Tracking Transparency (ATT):** required before tracking users across apps/sites or accessing the
advertising identifier (`AppTrackingTransparency` / `ATTrackingManager.requestTrackingAuthorization`).
Prohibited (all cause rejection): offering incentives for granting tracking; showing a screen that mirrors
or depicts the system alert; using "Allow"-style button titles in the pre-alert; adding visual cues that
push people toward Allow. "Never precede the system-provided alert with a custom screen… that could confuse
or mislead people."

**Location button** (`CLLocationButton`) — a lightweight, one-tap way to share location for a specific
feature without a persistent grant (grants "Allow Once"); if you distort/mis-customize it, the system revokes
its access.

**Data protection:** prefer **passkeys / Sign in with Apple / password autofill** over custom auth; store
secrets in the **Keychain**, never plain text; gate persistent logins behind Face ID/Touch ID/Optic ID.
App Store product pages show **Privacy Nutrition Labels** you declare at submission; process data on-device
where possible.

### 4.3 Notifications UX

Consent is required first (`UNUserNotificationCenter.requestAuthorization`); **provisional authorization**
(`.provisional`) lets notifications arrive quietly to Notification Center without an upfront prompt so people
can opt in from real examples.

Content rules: short **title** in title case, no ending punctuation; succinct body in sentence case with
proper punctuation; **don't truncate yourself** (system does it); **don't include your app name/icon**
(system adds the icon); provide **generic preview text** for when previews are hidden ("New comment,"
"Shipment"); **never put sensitive/personal info** in a notification. Frequency: "Avoid sending multiple
notifications for the same thing" — over-notifying makes people disable you entirely. Handle foreground
arrivals quietly (badge/inline update, not an alert). Use an **alert, not a notification, for error
messages.** Up to **four action buttons** per notification, each a short title-case verb phrase with an
optional SF Symbol; **avoid an action that merely opens the app**; prefer non-destructive actions.
**Badges** are only for unread-notification counts (not weather/scores), must stay current, and must never
be the sole channel for essential info.

### 4.4 Widgets (WidgetKit)

"Quick access to essential information and focused interactions… in additional contexts." Timely, glanceable,
personalizable. **System family sizes:** Small, Medium, Large, Extra Large (iPad/Mac/visionOS). **Accessory
sizes** (iPhone/iPad Lock Screen + Apple Watch complications): Circular, Rectangular, Inline, Corner. Rules:
pick one simple idea tied to the app's main purpose; **deep-link** into the app (don't just relaunch it);
prefer **dynamic content** that changes through the day; **don't just scale a small widget's content to fill
a bigger size**; **11 pt minimum text**, prefer system font + SF Symbols, never rasterize text (breaks
VoiceOver/scaling); standard margin **16 pt** (11 pt for tight content groupings). Widgets refresh on a
**budget** — they are **not real-time** (use Live Activities for that); animate updates up to **2 s**.
Widgets are **interactive** (buttons/toggles via App Intents) since iOS 17, but stay glanceable — don't build
app-like layouts. **Rendering modes:** full-color, accented/tinted, vibrant (Lock Screen/StandBy). Support
Lock Screen widgets, StandBy (two side-by-side, scaled up), and the Always-On display (reduced luminance —
keep contrast). **Smart Stack** relevance hints let the system surface the right widget at the right time.

### 4.5 Live Activities & Dynamic Island (ActivityKit)

"A Live Activity lets people track the progress of an activity, event, or task at a glance" — beyond a push
notification, updating over hours with interaction. Best for tasks with a **defined beginning and end** that
**don't exceed ~8 hours** (delivery ETA, sports score, live workout). Appears on Lock Screen, Home Screen,
**Dynamic Island**, StandBy, plus (per Dec 2025 update) the **Mac menu bar**, **Apple Watch Smart Stack**,
and **CarPlay Dashboard**.

Four required presentations:
- **Compact** — the two elements flanking the TrueDepth camera when one activity is active; design leading +
  trailing to read as a single unit.
- **Minimal** — a small pill/circle when multiple activities are active; still show live data, not just a logo.
- **Expanded** — shown on touch-and-hold; an enlarged, predictable version of compact/minimal.
- **Lock Screen** — a banner; **don't replicate a notification layout**; standard margin **14 pt**; look good
  in Dark Mode and Always-On.

Rules: focus on glanceable info; **no ads/promotions**; hide sensitive info (show an innocuous summary, reveal
in-app on tap); tapping opens the app at the relevant detail; keep interactivity to **essential, ideally a
single control** (play/pause, pause/resume workout); alert only for essential updates and **don't duplicate a
Live Activity with push notifications**; animations max **2 s** (none on Always-On reduced-luminance).
**Ending:** end immediately when the task ends; it persists up to **4 hours** on Lock Screen/menu bar/Smart
Stack — set a proportional custom dismissal, typically **15–30 min**. Dynamic Island corner radius is **44 pt**.

### 4.6 App Clips

"Deliver an experience from your app without requiring people to download the full app." Focused on **one
fast task or a demo**; stays on-device temporarily; privacy-limited (**no background operation**). **Keep it
small** (the App Clip binary is size-budgeted for instant launch). **Invocations:** App Clip Codes (≥256×256 px
PNG/SVG), NFC tags, QR codes, Maps, Safari App Clip cards / Smart App Banners, Messages links, Siri
Suggestions, and (iOS 17+) links from other apps. Rules: let people **complete the task without installing the
full app**; **native components only — avoid web views**; linear, minimal UI (no tab bars/complex nav/settings);
**omit splash screens**, include all assets, no launch wait; support **Apple Pay** for frictionless checkout;
**don't force account creation** upfront; recommend the full app **non-intrusively** via `SKOverlay` at a
natural pause (not via push). When the full app is installed it **replaces** the App Clip and future
invocations open the app — don't make people re-log-in. App Clips can schedule notifications for up to **8
hours** after launch, task-focused only.

### 4.7 Share sheet / activity views (`UIActivityViewController`)

"An activity view — often called a **share sheet** — presents a range of tasks people can perform in the
current context" (Messages/Mail/AirDrop/Copy/Print + frequently-used apps). Reveal it from the **Share button**
(the square-with-up-arrow) — don't build an alternative "share" affordance. Provide **app-specific activities**
(they list before cross-system actions) and **Share/Action extensions** to appear in *other* apps' sheets.
Rules: don't duplicate existing system actions (e.g. a second Print); use SF Symbols or a custom icon centered
in ~70×70 px; short verb-phrase titles without your brand name; **exclude** actions that don't apply (e.g.
Print). Supported on iOS/iPadOS/visionOS; not macOS/tvOS/watchOS.

### 4.8 Sign in with Apple (`AuthenticationServices`)

"A fast, private way to sign into apps and websites… Face ID/Touch ID/Optic ID… two-factor built in,"
optional **private relay email**, and "Apple doesn't use Sign in with Apple to profile people." **App Store
rule of thumb (Guideline 4.8):** if an app offers third-party/social login (Google/Facebook/etc.) as its
*only or primary* login, it generally must **also** offer an equivalent privacy-respecting option — Sign in
with Apple qualifies (there are carve-outs for apps using only your own account system, education/enterprise,
or a specific third-party citizen-identity service). Use the **system button** (`ASAuthorizationAppleIDButton`)
for approved appearance/localization/VoiceOver; titles limited to "Sign in / Sign up / Continue with Apple";
three styles (white, white-with-outline, black); minimum **140×30 pt**; adjustable corner radius. Custom
buttons are allowed but **App Review evaluates every custom Sign in with Apple button** (system-approved logo
art only, black/white only). UX rules: **prominent** (no smaller than other sign-in buttons); **delay sign-in
as long as possible**; ask for account only in exchange for value; **minimize data requests**; **never ask
for a password** or override a chosen relay address; be transparent about collected data.

### 4.9 Universal Links / Handoff / Continuity

- **Universal Links** — standard `https://` links that open your app directly (deep-linked to the right
  screen) instead of Safari, falling back to the website if the app isn't installed. Configured via the
  **Associated Domains** entitlement + an `apple-app-site-association` (AASA) file on your domain. Prefer them
  over custom URL schemes (which are spoofable and non-verifiable). This is the canonical iOS deep-linking
  mechanism and underpins App Clip/Smart Banner invocation.
- **Handoff** — start a task on one device and continue on another (iPhone → Mac/iPad) via `NSUserActivity`;
  surfaces on the receiving device's App Switcher / Dock / Lock Screen. Advertise the same activity types
  your Spotlight/Siri integration uses.
- **Continuity** — the broader family: Universal Clipboard, Continuity Camera, AirDrop, iPhone Mirroring,
  Phone/SMS relay. Design so state syncs (often via iCloud/CloudKit) and a task feels continuous across a
  person's devices.

### 4.10 Shortcuts / Siri / App Intents

**App Shortcuts** (built on the **App Intents** framework) expose "your app's key functions or content
throughout the system" — invokable via **Siri voice, Spotlight, the Shortcuts app, the Action button, and
squeezing Apple Pencil Pro**, available immediately on install. Limit: **up to 10 App Shortcuts per app.**
Rules: expose common, important tasks; keep spoken phrases short and memorable (must include the app name);
add at most one optional parameter; ask for clarification when info is missing; make shortcuts discoverable
via in-app tips; provide full dialogue for audio-only devices (AirPods/HomePod). Respond with **snippets**
(static custom views) or **Live Activities** (ongoing). Consider adopting **app schemas** so actions/content
reach **Apple Intelligence**. (Editorial: "Shortcuts" the app is title-case + plural; an individual "shortcut"
is lowercase.)

### 4.11 Controls & Control Center (iOS 18+)

"A control is a button or toggle that provides quick access to your app's features from other areas of the
system" (WidgetKit / App Intents). **Control buttons** perform an action, link into the app, or launch a
locked-device camera experience; **control toggles** switch two states. People add controls to **Control
Center**, the **Lock Screen**, or the **Action button.** Anatomy: **symbol** (required; provide on/off symbols
for toggles, e.g. `door.garage.open`/`closed`), **title**, optional **value**. Rules: offer controls for
high-value actions that avoid launching the app; keep state accurate (update on interaction/completion/push);
animate symbol state changes; pick a brand tint (applied to the on-state symbol and Dynamic Island value);
prompt for **configuration** when first added (`promptsForUserConfiguration()`); provide Action-button **hint
text** (`controlWidgetActionHint(_:)`); **redact sensitive title/value when locked** and require
authentication (`IntentAuthenticationPolicy`) for security-affecting actions. Locked-device camera capture
uses `LockedCameraCapture`. iOS/iPadOS/macOS only.

### 4.12 Focus

Focus (Do Not Disturb and its modes) filters notifications and can change Home Screen/Lock Screen. For app
designers the practical implication is: respect notification interruption levels (`.passive`, `.active`,
`.timeSensitive`, `.critical`) so the system can correctly deliver or defer your notifications under a user's
Focus, and only mark truly time-sensitive content as such. Don't try to defeat Focus.

---

## 5. Accessibility (Apple)

Apple frames an accessible interface as **intuitive, perceivable, and adaptable** — never relying on a single
sense or interaction. Communicate support via **Accessibility Nutrition Labels** on the App Store.

### 5.1 VoiceOver

The screen reader that "lets people experience your app's interface without needing to see the screen."
Every meaningful element needs a semantic description. APIs:
- UIKit: `accessibilityLabel` (what it is), `accessibilityHint` (what happens), `accessibilityTraits`
  (button/header/adjustable/selected/etc.), `accessibilityValue`.
- SwiftUI: `.accessibilityLabel(_:)`, `.accessibilityHint(_:)`, `.accessibilityValue(_:)`,
  `.accessibilityAddTraits(_:)`, `.accessibilityElement(children:)`, `.accessibilityHidden(_:)`.
- Never rasterize text (kills VoiceOver); label all icons/controls; group related elements; keep a logical
  focus order.

### 5.2 Dynamic Type (as an accessibility requirement)

Systemwide text-size setting (iOS/iPadOS/tvOS/visionOS/watchOS; **macOS does not support Dynamic Type**).
"Ideally, give people the option to enlarge text by **at least 200 percent** (or **140 percent** in watchOS)."
Adopt the built-in **text styles** (largeTitle, title, headline, body, callout, caption, etc.) with the
system fonts and text scales for free; **avoid light weights** (prefer Regular/Medium/Semibold/Bold; avoid
Ultralight/Thin/Light). Recommended default/minimum sizes:

| Platform | Default | Minimum |
|---|---|---|
| iOS, iPadOS | 17 pt | 11 pt |
| macOS | 13 pt | 10 pt |
| tvOS | 29 pt | 23 pt |
| visionOS | 17 pt | 12 pt |
| watchOS | 16 pt | 12 pt |

At large accessibility sizes: minimize truncation; adopt **stacked layouts** (label above value), reduce
columns; scale meaningful icons with text (**SF Symbols do this automatically**); keep hierarchy stable.
SwiftUI: `.font(.body)` + `@ScaledMetric`; UIKit: `UIFontMetrics` + `adjustsFontForContentSizeCategory`.
**System fonts:** San Francisco — **SF Pro** (iOS/iPadOS/macOS/tvOS/visionOS), **SF Compact** (watchOS),
plus SF Mono, SF Arabic/Hebrew/etc. and rounded variants; **New York (NY)** is the serif companion.

### 5.3 Color & contrast (with WCAG mapping)

Apple explicitly targets **WCAG 2 Level AA** and the Accessibility Inspector "uses WCAG Level AA values as
guidance":

| Text size | Weight | Minimum contrast ratio |
|---|---|---|
| Up to 17 pt | Any | **4.5:1** |
| 18 pt+ | Any | **3:1** |
| Any | Bold | **3:1** |

Prefer **system-defined semantic colors** (e.g. `systemRed`, `label`, `secondaryLabel`) — they carry
accessible variants that adapt to Increase Contrast and light/dark. Check contrast in **both** light and dark
appearances. Apple also references the **APCA** (Advanced Perceptual Contrast Algorithm) as an emerging method.

### 5.4 The "reduce/increase/differentiate" family

- **Reduce Motion** — see §3.1. (`accessibilityReduceMotion`)
- **Reduce Transparency** — the system dials back blur/translucency in materials/Liquid Glass; don't hard-code
  a look that assumes translucency. (`accessibilityReduceTransparency` /
  `UIAccessibility.isReduceTransparencyEnabled`) Materials & Liquid Glass "can differ in response to…
  accessibility settings that reduce transparency or increase contrast."
- **Increase Contrast** — provide a higher-contrast scheme; if you don't meet the minima by default, at least
  meet them when Increase Contrast is on. (`accessibilityDisplayShouldIncreaseContrast`)
- **Differentiate Without Color** — "convey information with more than color alone." Add shapes/icons/labels
  for red-green/blue-orange color blindness. (`accessibilityShouldDifferentiateWithoutColor`)

### 5.5 Other assistive technologies

- **Switch Control** — drive the app via external switches/game controllers/sounds; requires proper labels
  and a navigable element tree.
- **Voice Control** — operate the whole device by voice; **depends entirely on correct accessibility labels**
  so spoken commands map to controls; integrates with Siri/Shortcuts/the Action button.
- **Full Keyboard Access** & other mobility tech (AssistiveTouch, Pointer Control) — see §1.4.
- **Assistive Access** (iOS/iPadOS) — a streamlined mode for cognitive disabilities: identify core
  functionality and strip non-critical UI, one interaction per screen, and confirm twice for hard-to-undo
  actions.
- **Cognitive** — keep interactions simple/consistent; **minimize time-boxed (auto-dismissing) UI**; prefer
  explicit dismissal.
- **Media** — captions, subtitles, audio descriptions, transcripts; don't autoplay without controls; respond
  to **Dim Flashing Lights** and `isVideoAutoplayEnabled`.

**General accessibility gesture rules** (echoing §1): "support simple gestures," "avoid custom multifinger/
multihand gestures," and **always offer a non-gesture alternative** (e.g. a visible button beside a
swipe-to-dismiss). Test with **Accessibility Inspector** and on-device with the real assistive technologies.

---

## 6. App Store Presence (UX-relevant)

The product page and App Review Guidelines shape UX that must exist *inside* the app.

### 6.1 Product page — screenshots & app previews

- **Screenshots:** 1–10 per localization, JPEG/PNG. Recommended base upload sizes: **1320×2868** (6.9″ iPhone)
  and **2064×2752** (13″ iPad); Apple down-scales for smaller devices. Tell a cohesive story across the set;
  the first 1–3 dominate conversion because they show in search results.
- **App previews** (optional): up to **3 per device size per language**, **15–25 s**, ≤**500 MB**, H.264 or
  ProRes 422 HQ, must be all-ages appropriate (captured on-device motion). Missing localized preview falls
  back to the next-best language.
- Localize screenshots/previews per market; keep them honest — they must reflect actual in-app experience.

### 6.2 App Review Guidelines that drive in-app UX

- **5.1.1(v) Account deletion:** any app that supports **account creation must offer in-app account deletion**
  (full deletion of the account and associated personal data — not merely "deactivate"). It must be **easy to
  find**; confirmation steps are allowed; only **highly-regulated industries** may route deletion through
  customer service. Enforced since Jan 31, 2022.
- **5.1.1 Data collection & purpose strings:** request only necessary data, with clear justification;
  **`NS…UsageDescription` purpose strings are required** and must be specific (missing/vague strings ⇒
  rejection).
- **Deceptive/manipulative design ("dark patterns"):** Apple's guidelines repeatedly forbid designs meant to
  **trick or manipulate** — accurate metadata (**2.3**), hidden/undocumented features (**2.3.1**), and honest
  subscription/pricing UX that clearly discloses price, terms, and how to cancel (**3.1.2**). Confusing
  cancellation flows, disguised ads, fake system UI (see the ATT rules in §4.2), and bait-and-switch previews
  are grounds for rejection.
- **4.8 Login services** — see §4.8 (privacy-respecting login parity).
- **Permissions & tracking** — ATT is enforced at review; misleading pre-permission screens are rejected.
- **Minimum functionality (4.2):** thin "web-view wrapper"/marketing-only apps are rejected — relevant to
  App Clips too ("native components… avoid web views").

### 6.3 Onboarding & paywall guidance

From the HIG (§4.1) and review practice: **let people experience value before prompting for ratings or
purchases**; use `SKStoreReview.requestReview` sparingly (system throttles it); paywalls must clearly state
price/billing period/what's included and offer an obvious dismiss/restore-purchases path; don't gate an app's
core value behind a login/paywall the user can't evaluate first.

---

## 7. SwiftUI as the Implementation Vehicle

SwiftUI is the primary way HIG patterns map to code (UIKit remains where SwiftUI lacks coverage). Key mappings:

| HIG concept | SwiftUI | UIKit (where still relevant) |
|---|---|---|
| Hierarchical (push) navigation + back | `NavigationStack` (+ `NavigationLink`, `navigationDestination`) | `UINavigationController` |
| Two-/three-column split | `NavigationSplitView` | `UISplitViewController` |
| Tab bar | `TabView` (+ `Tab`, iOS 18 sidebar-adaptable tabs) | `UITabBarController` |
| Modal sheet / detents | `.sheet` + `.presentationDetents([.medium, .large])` | `UISheetPresentationController` |
| Search field | `.searchable(text:)` (+ scopes, suggestions) | `UISearchController` |
| Grouped/inset forms & settings | `Form` (+ `Section`, `LabeledContent`) | `UITableView` grouped |
| Lists w/ swipe actions | `List` + `.swipeActions` | `UITableView` |
| Context menu (long-press) | `.contextMenu` | `UIContextMenuInteraction` |
| System icons | `Image(systemName:)` / `Label` (**SF Symbols**) | `UIImage(systemName:)` |
| Accessibility | `.accessibilityLabel/Hint/Value/AddTraits`, `.accessibilityElement` | `UIAccessibility` protocols |
| Dynamic Type | text styles + `@ScaledMetric` | `UIFontMetrics` |
| Reduce Motion / Transparency | `@Environment(\.accessibilityReduceMotion / reduceTransparency)` | `UIAccessibility.is…Enabled` |
| Materials / Liquid Glass | `.background(.regularMaterial)`, `.glassEffect(_:in:)` | `UIVisualEffectView` (`UIBlurEffect`, `UIVibrancyEffect`) |
| Haptics | `.sensoryFeedback(_:trigger:)` (iOS 17+); `CoreHaptics` | `UIFeedbackGenerator` |
| Widgets / Live Activities / Controls | **WidgetKit** + **ActivityKit** + **App Intents** (SwiftUI views) | — |
| Charts | **Swift Charts** (`Chart`) | — |
| Keyboard shortcuts | `.keyboardShortcut(_:modifiers:)` | `UIKeyCommand` |

Use **semantic colors** (`Color.primary`, `.secondary`, `Color(.systemBackground)`) and **SF Symbols** for
free light/dark, contrast, and Dynamic Type adaptation. UIKit is still needed for some low-level camera/AR,
`PHPickerViewController`, advanced text engines, and fine collection-view control — bridge via
`UIViewControllerRepresentable`. iOS 26's **Liquid Glass** is picked up automatically by standard SwiftUI
components; apply `.glassEffect` to custom controls only sparingly and never in the content layer.

---

## 8. HIG vs Material Design 3 — Cross-Platform Comparison

Both are mature, opinionated design systems; shipping one look on both platforms usually feels "off" to native
users. Where they diverge and why it matters:

| Dimension | Apple HIG (iOS) | Material Design 3 (Android) | Cross-platform implication |
|---|---|---|---|
| **Design philosophy** | Deference, clarity, depth; flat + translucent **materials/Liquid Glass** | "Material" metaphor; expressive, tactile, **dynamic color** tokens | A single flat-Apple look on Android ignores M3 tonal/elevation language, and vice versa |
| **Navigation model** | Tab bar (bottom), navigation stack, large titles; back = top-left chevron **+ system left-edge swipe** | Bottom **navigation bar**/rail, top app bar; historically a system/nav **Back button** (gesture back added in Android 10) | Back is the biggest trap — iOS relies on edge-swipe + per-screen chevron; Android has a global Back affordance (gesture or button). Don't put a manual back button where the OS already provides one |
| **System font** | **San Francisco (SF Pro / SF Compact)** + New York serif | **Roboto** (+ Roboto Flex); brand fonts common | Use each platform's native font; forcing SF on Android (or Roboto on iOS) looks foreign and can break metrics/Dynamic Type vs `sp`/font-scale |
| **Typography scale** | Text styles (largeTitle…caption) driven by **Dynamic Type**, sized in **pt** | **Type scale** (Display/Headline/Title/Body/Label) sized in **sp**, respecting font-scale | Both scale for accessibility but via different tokens; map roles, don't copy pixel sizes |
| **Components** | Segmented controls, action sheets, share sheet, switches (rounded), swipe actions, `UIAlertController` | FABs, snackbars, chips, navigation drawer, bottom sheets, filled/tonal buttons, dialogs | The **FAB** and **snackbar** are quintessentially Android; **share sheet** and **action sheet** are iOS. Don't transplant a FAB onto iOS |
| **Motion** | Purposeful, brief, physical/realistic; Reduce Motion | **Expressive** motion system, emphasized easing, shared-axis/container transforms; reduced-motion setting | Both respect reduced-motion, but M3's transition vocabulary (container transform) has no direct iOS equivalent |
| **Color** | Semantic system colors, light/dark, Increase Contrast | **Dynamic color** from wallpaper + tonal palettes / design tokens | iOS palette is designer-set; M3 can theme from user wallpaper — a shared hardcoded palette underuses M3 |
| **Elevation/shadow** | Subtle; depth via **translucent layers** & Liquid Glass | Explicit **elevation** (tonal + shadow) as a core signifier | "Flat translucent" vs "elevated surfaces" read as different design languages |
| **Density & devices** | Apple controls the hardware → predictable point grid | Thousands of OEM sizes/densities → **dp/sp**, responsive/adaptive layouts critical | Test far more form factors on Android; iOS layout assumptions don't transfer |
| **Touch target** | **44×44 pt** | **48×48 dp** | Similar intent, different unit/number |
| **Icons** | **SF Symbols** (system, weight/scale-matched) | **Material Symbols** | Icon sets aren't interchangeable; SF Symbols are licensed for Apple platforms only |

**Practical guidance for cross-platform teams:** share **information architecture, flows, content, and brand**,
but let each platform own its **navigation, back behavior, components, fonts, iconography, and motion**.
A framework (SwiftUI vs Jetpack Compose, or Flutter/React Native with Cupertino+Material widget sets) should
render platform-appropriate chrome. The highest-risk mismatches when you ship one design on both are:
(1) **back navigation**, (2) **bottom-bar semantics** (iOS tab bar vs Android nav bar + FAB), (3) **system
fonts / type scale**, and (4) **share/action affordances**. Getting those wrong is what makes an app feel
"ported" rather than native.

---

## Sources

Apple HIG (fetched via `developer.apple.com/tutorials/data/design/human-interface-guidelines/*.json`; human
pages at the corresponding `developer.apple.com/design/human-interface-guidelines/*` URLs):

- https://developer.apple.com/design/human-interface-guidelines/gestures
- https://developer.apple.com/design/human-interface-guidelines/playing-haptics
- https://developer.apple.com/design/human-interface-guidelines/motion
- https://developer.apple.com/design/human-interface-guidelines/accessibility
- https://developer.apple.com/design/human-interface-guidelines/privacy
- https://developer.apple.com/design/human-interface-guidelines/notifications
- https://developer.apple.com/design/human-interface-guidelines/live-activities
- https://developer.apple.com/design/human-interface-guidelines/widgets
- https://developer.apple.com/design/human-interface-guidelines/app-clips
- https://developer.apple.com/design/human-interface-guidelines/activity-views
- https://developer.apple.com/design/human-interface-guidelines/onboarding
- https://developer.apple.com/design/human-interface-guidelines/typography
- https://developer.apple.com/design/human-interface-guidelines/drag-and-drop
- https://developer.apple.com/design/human-interface-guidelines/pointing-devices
- https://developer.apple.com/design/human-interface-guidelines/keyboards
- https://developer.apple.com/design/human-interface-guidelines/sign-in-with-apple
- https://developer.apple.com/design/human-interface-guidelines/materials
- https://developer.apple.com/design/human-interface-guidelines/controls
- https://developer.apple.com/design/human-interface-guidelines/app-shortcuts

Apple App Store / App Review:
- https://developer.apple.com/news/?id=12m75xbj (account deletion requirement)
- https://developer.apple.com/app-store/app-previews/
- https://www.developer.apple.com/help/app-store-connect/manage-app-information/upload-app-previews-and-screenshots
- https://www.termsfeed.com/blog/apple-requirement-in-app-deletion-accounts/

App Store screenshot/preview specs (third-party, cross-checked):
- https://splitmetrics.com/blog/app-store-screenshots-aso-guide/
- https://adapty.io/blog/app-store-screenshot-sizes-dimensions/

HIG vs Material Design 3 (third-party comparisons):
- https://www.appschopper.com/blog/google-material-design-apple-human-interface-guidelines-which-is-better-and-why/
- https://www.uxpin.com/studio/blog/ios-vs-andoid-ui-design-for-mobile/
- https://arounda.agency/blog/ios-vs-android-app-ui-design-the-differences-explained
- https://pageflows.com/resources/apples-human-interface-guidelines/

Note: SwiftUI/UIKit API mappings, Universal Links/Handoff/Continuity mechanics, and App Review guideline
numbering (4.8, 5.1.1, 2.3.x, 3.1.2) are stated from established Apple platform knowledge and cross-checked
against the fetched HIG pages; verify exact current guideline wording against
https://developer.apple.com/app-store/review/guidelines/ before quoting to Apple in a submission dispute.

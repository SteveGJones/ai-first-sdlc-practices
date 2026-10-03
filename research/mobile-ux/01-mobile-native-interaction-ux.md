# Mobile-Native Interaction & UX Design (Cross-Platform)

Authoritative, evidence-based reference for a **mobile-ux-architect** specialist agent. Scope:
platform-agnostic mobile-native interaction and UX patterns — the ones that apply to phone/tablet
apps regardless of iOS vs Android. Numbers and named patterns are cited to the sources listed at
the end.

> Convention: iOS measures in **points (pt)**, Android in **density-independent pixels (dp)**, and
> WCAG in **CSS pixels (px)**. For touch-sizing purposes these are near-equivalent reference units
> (each is a device-independent ~1/160-inch-ish logical unit), so a 44pt / 48dp / 44px target is
> roughly the same physical size. Do not confuse them with raw hardware pixels.

---

## 1. Ergonomics & Reachability — the Thumb Zone

**How people actually hold phones (Steven Hoober, 2013).** Hoober observed **1,333 people** using
phones in public. Grips fell into three patterns:

- **One-handed: 49%** (most common) — thumb does all the work.
- **Cradled: 36%** — held in one hand, tapped with a finger/thumb of the other.
- **Two-handed / "BlackBerry prayer": 15%** — both thumbs.

Of the one-handed users, **~67% used the right thumb**. Roughly **75% of all interactions are
thumb-driven** (Smashing/Hoober). Grip is not fixed — people constantly switch grips during a
session depending on task, so design must survive a **one-handed thumb** as the worst case.

**The Thumb-Zone map.** Coined by Hoober; popularised by Scott Hurff and Smashing Magazine. On a
phone held one-handed, the screen divides into three reach zones:

- **Natural / easy ("green")** — bottom-center arc where the thumb rests without strain. Put
  **primary, frequent actions here**.
- **Stretch / OK ("yellow")** — mid-screen and the sides; reachable but requires stretching.
  Secondary actions.
- **Hard / "ow" ("red")** — top corners (esp. the top-far corner diagonally opposite the holding
  hand). Requires a grip change or second hand. Reserve for **rare or deliberately
  friction-worthy** actions (e.g. delete, sign-out).

General rule (Smashing/Hoober): **frequent links in the easy zone, infrequent links in the
hard-to-reach zone.** As screens grew larger (phablets), the reachable share of the screen shrank,
which is *why* the industry shifted primary actions to the **bottom third**.

**Design consequences:**
- **Primary actions in the bottom third.** Bottom-anchored primary buttons, bottom nav, and
  bottom sheets keep the key targets in the natural zone.
- **Bottom-sheet-first.** Prefer bottom sheets over top-anchored modals/menus — content and its
  controls sit where the thumb already is.
- **Bottom navigation over top navigation.** Tab bars at the bottom beat top tab bars for
  one-handed reach.
- iOS **Reachability** (double-tap/pull the home indicator to slide the top of the screen down)
  and Android equivalents are OS-level mitigations, not a substitute for good placement.
- Swipe/gesture hit areas should be **≥ ~45px** tall/wide to avoid accidental triggers (Smashing).

---

## 2. Touch & Gestures

### Touch target sizes — the canonical numbers

| Guidance | Minimum target | Level / status |
|---|---|---|
| **Apple HIG** | **44 × 44 pt** | Recommended minimum |
| **Material Design (Android)** | **48 × 48 dp** (≈ 9mm physical) | Recommended minimum |
| **WCAG 2.5.8 Target Size (Minimum)** | **24 × 24 CSS px** | **AA** (WCAG 2.2) |
| **WCAG 2.5.5 Target Size (Enhanced)** | **44 × 44 CSS px** | **AAA** |
| **MIT Touch Lab (physical)** | finger **pad 10–14 mm**, fingertip **8–10 mm**; index finger width **16–20 mm** | Anthropometric basis |

- **MIT Touch Lab** anthropometry is the physiological "why": people touch with the **pad**
  (10–14mm), not the tip, so a target under ~1cm/~10mm invites mis-taps. This is the origin of the
  common "~10mm / ~0.4in minimum" heuristic and underpins the 44pt/48dp guidance.
- WCAG 2.5.8's **24px AA** floor is generous by design and comes with **exceptions**: inline links
  in text are exempt; targets with **≥24px spacing** between them can be smaller; and
  user-agent-controlled or essential targets are exempt. Treat 24px as a legal floor and
  **44–48px as the usability target**, larger for primary actions.
- **Spacing matters as much as size.** Adjacent targets need clear gaps (WCAG offset rule uses a
  24px spacing model) so a 44pt button surrounded by other 44pt buttons still needs margin to
  prevent fat-finger errors.

### The gesture vocabulary (cross-platform)

Core gestures users expect: **tap**, **double-tap**, **long-press** (context actions),
**swipe** (dismiss, reveal actions, navigate carousels), **edge-swipe back** (iOS back; Android
predictive back), **pull-to-refresh** (invented by Loren Brichter in Tweetie, 2008 — now a de-facto
standard for refreshing feeds), **drag/reorder**, **pinch-to-zoom**, and **two-finger pan**.

### The hidden-gesture / discoverability problem

Gestures have **no inherent affordance** — nothing on screen says "you can swipe here." Classic
failures: users don't know they can swipe the Spotify now-playing bar to change tracks; swipe-to-
delete in lists is invisible until discovered. Guidance:

- **Never make a core action gesture-only.** Every gesture that matters should have a **visible
  fallback** (a button, an overflow menu, a long-press menu). Recent research (GhostUI, arXiv 2026)
  catalogues six common gestures that routinely trigger functionality with **no visual affordance**.
- **Add affordances**: partial reveal ("peeking" the swipe action), pull-tab handles on bottom
  sheets, chevrons, microcopy, and short **first-run coach marks/tooltips** shown *in context* the
  first time an element appears.
- **Be consistent** with platform conventions users already know (edge-swipe back, pull-to-refresh)
  rather than inventing bespoke gestures.
- **Accessibility:** hidden gestures break screen readers and motor-impaired users — WCAG **2.5.1
  Pointer Gestures** requires a single-pointer alternative to any multipoint/path-based gesture.

---

## 3. Haptics

Haptic feedback (taptic/vibration) provides a **tactile confirmation** that an interaction was
registered — valuable because it's felt even when the user isn't looking closely, in noisy
environments, or when audio is off.

**When haptics help:**
- **Confirmation of a discrete, meaningful action** — toggle flip, successful submit, pull-to-
  refresh threshold reached, drag "snap" into place, picker detents, reaching a boundary.
- **Reinforcing state changes** the user can't otherwise easily perceive (long-press activated,
  selection begun).
- **Error/warning signals** paired with visual/audio (multi-modal redundancy).

**When haptics annoy (anti-patterns):**
- Firing on **every** tap/keystroke or minor/frequent action → sensory fatigue.
- **Inconsistent meaning** — the same buzz meaning different things in different places.
- Feedback that arrives **too late** to feel connected to the action.
- Creating **notification-like** patterns inside normal UI flow.

**Rules of thumb:** be purposeful ("if you can't say what the haptic communicates in one sentence,
it's probably unnecessary"); keep meanings **consistent**; **respect system settings** and provide
a way to disable (accessibility + battery); and **test on real iOS and Android devices** — the
actuators and perceived feel differ substantially across hardware (iOS Taptic Engine is far more
uniform than the wide range of Android vibration motors, so verify capability before using rich
effects).

---

## 4. Navigation Patterns

**Hidden navigation hurts UX metrics (NN/G study).** Comparing hidden (hamburger), visible, and
combo navigation:

- **Discoverability** is "cut almost in half" by hiding the main nav.
- **Mobile usage:** hidden nav used in **57%** of cases vs **86%** for combo (visible + hamburger) —
  visible/combo used **~1.5×** as much.
- **Desktop usage:** hidden **27%** vs visible/combo **48–50%**.
- **Task time:** hidden nav was **15% slower on mobile**, **39% slower on desktop**.
- **Perceived difficulty** (1–7 scale): hidden **2.6** vs visible **2.1** — a **~21% increase** in
  difficulty for hidden.
- When people do use hidden nav, they reach for it **later** in the task.

**Takeaway:** the hamburger isn't banned, but it **shouldn't be the default when there's room to
show navigation.** Prefer visible/combo nav for a phone's top-level destinations.

**Bottom tab bar vs hamburger/drawer:**
- **Bottom tab bar** for **3–5** frequently-switched top-level destinations (Material: **3–5**, up
  to 5; **< 3 → use tabs instead**; **> 5/6 → move overflow into a drawer/"More" tab**). Persistent,
  visible, thumb-reachable — the recommended default.
- **Hamburger/drawer** suits **infrequent** navigation, large/deep IA that won't fit a tab bar, or
  secondary destinations. Accept the discoverability cost.
- **Bottom sheets** are for **contextual/secondary actions and content**, not primary top-level
  navigation; they render **in front of** the bottom nav and temporarily cover it.

**Deep linking:** support URL/universal-link deep links so notifications, search, and external
links land users on the exact screen (not the home tab) with a **sensible back stack** — critical
for activation and re-engagement.

**Back-behavior differs by platform:**
- **iOS:** no OS back button — provide an **in-app back button (top-left)** *and* support the
  **edge-swipe-from-left back** gesture. The left→right edge swipe = "go back."
- **Android:** a **system/gesture Back** (predictive back in modern Android) exists — the app must
  maintain a correct **back stack** and handle Back predictably (dismiss sheets/dialogs, then pop
  screens, then exit). Note the same left→right swipe that means "back" on iOS is often used to
  **switch tabs** on Android — so a cross-platform app must not assume identical gesture semantics.

---

## 5. Onboarding

**Named patterns:**
- **Benefits-led onboarding** — communicates *why the app matters* (the outcome/value, "improve
  your life") rather than enumerating features. Generally more motivating than feature tours.
- **Feature-tour / carousel** — a few intro slides describing features. Cheap but often skipped and
  low-retention; weakest of the three when used alone.
- **Progressive / contextual onboarding** — teach features **just-in-time**, in context, as the
  user first encounters each one (tooltips, coach marks, empty-state prompts). Best for complex
  products; reduces first-run overwhelm and improves retention/completion.

**Reducing first-run friction:**
- **Show value before asking for anything.** Let users explore/experience core value before
  demanding an account.
- **Delay sign-in / avoid hard sign-in walls.** A **sign-in wall on launch** is a top drop-off
  point. Prefer **delayed/deferred sign-in** ("let me try it first"), guest mode, or sign-in only
  when the user hits a feature that genuinely needs an identity. Offer **social/one-tap** sign-in
  and platform autofill to cut typing.
- **Empty / first-use states** double as onboarding: an empty list should explain what will appear,
  why it's empty, and give a **single clear next action** to populate it (see §8).
- Keep it **short, skippable, and progress-visible**; ask for the minimum up front.

**What improves activation:** getting the user to their **first meaningful outcome ("aha moment")**
fast; every extra intro slide, permission prompt, or form field before that moment costs
activation. Measure activation as a **first-value event**, not just "opened the app" (see §10).

---

## 6. Permissions & Notifications UX

**Permission priming / pre-permission ("soft ask").** Never fire the OS permission dialog cold on
launch. Pattern: show your **own** in-context explanation screen ("Turn on notifications so we can
alert you when your order ships") **first**; only if the user accepts do you trigger the **native
(hard) dialog**.

- **Why it matters:** the OS dialog can typically be shown **only once** per permission. A **hard
  denial is expensive** — on iOS especially, once denied you cannot re-prompt; the user must dig
  into Settings. The soft-ask lets people who'd decline **decline harmlessly on your screen**,
  preserving your one real shot.
- **Timing:** ask **in context, tied to the feature**, at the moment the user is actively trying to
  use it — not on first launch. Deferring/priming yields materially higher grant rates (industry
  reports cite figures like **~28% higher grant rates** for deferred prompts; a user who accepts the
  soft-ask converts on the native prompt at very high rates).
- A **user-triggered** request (user taps "Enable location") outperforms even a passive priming
  screen, because the request is expected.

**Notifications / push best practices:**
- **Opt-in reality:** Android auto-granted historically (pushing opt-in ~**81%**, retail up to
  **~92%**); iOS requires explicit opt-in (~**51%**). Android 13+ now also requires runtime
  notification permission, so priming matters on both platforms.
- **Frequency tolerance:** **~46%** of users opt out at **2–5 messages/week**; **~32%** at
  **6–10/week**. A common safe starting cadence is **2–3 promotional pushes/week**, separate from
  transactional/triggered messages.
- **Relevance & value:** low opt-in + low open = messages too frequent or irrelevant. Personalise,
  segment, and make each push **actionable and timely**; **deep-link** to the exact screen.
- **Retention impact (Airship benchmark):** users who received **≥1** push had **~120%** higher
  retention vs zero; **weekly ~440%** higher; **daily ~820%** higher; overall **~3×** higher
  retention when users got push in their first 90 days. (Caveat: correlation — engaged users also
  opt in — but directionally strong.)
- Give users **granular controls** (notification categories/channels — Android **notification
  channels** make this native) so they can tune rather than nuke all notifications.

---

## 7. Forms & Input on Mobile

Mobile typing is slow and error-prone (the keyboard eats **~50% of the screen in portrait,
70–80% in landscape** — Baymard). The overriding goal: **minimize typing.**

- **Right keyboard per field.** Use `type`/`inputmode`: `type="email"` (@ key), `type="tel"` /
  `inputmode="numeric"` (dial pad / number pad), `type="url"`, `type="number"`. Baymard: **60% of
  top-50 mobile e-commerce sites fail ≥2 of 5 keyboard optimizations** (e.g. Amazon historically
  showed an alphanumeric keyboard for phone numbers — a real failure).
- **Autofill / autocomplete.** Set correct `autocomplete` tokens (name, email, tel,
  street-address, cc-number, one-time-code) and support platform password/address/OTP autofill.
  **Never `autocomplete="off"` on standard fields** — it kills the whole autofill benefit. Default
  **"Shipping = Billing"** to skip a whole address.
- **Single-column layout.** Baymard/NN/G: single-column beats multi-column — fewer errors, higher
  completion, a clear top-to-bottom path. **No side-by-side fields on mobile.**
- **Don't split inputs.** One field for phone, ZIP, full name, card number — not segmented boxes
  (segmentation adds friction and focus-management bugs). Use **input masking** to format as the
  user types instead.
- **Top-aligned labels** (Luke Wroblewski). Above the field, not inside and not left-aligned:
  they survive field zoom and stay visible when the keyboard is up. (Inline/floating labels can
  work but must not vanish on focus.)
- **Inline validation** at the field, as the user completes it — with positive confirmation *and*
  specific error messages. Inline validation has been measured at **~22% higher success and ~42%
  faster completion** vs submit-time validation. (Validate on blur/after a pause, not on every
  keystroke, to avoid premature "error" flashes.)
- **Reduce fields ruthlessly** — but note Baymard's key nuance: **effort matters more than raw
  count.** "Four fields that each require complex typing can feel worse than 12 fields with autofill
  and the right keyboard." Optimize the *typing effort*, not just the field number.
- Auto-detect where possible (geo/IP for country, **ZIP → city/state** lookup), and offer
  **guest checkout** prominently (60% of testers struggled to find it).

---

## 8. States & Perceived Performance

- **Skeleton screens vs spinners.** Use **skeleton screens** (grey placeholder shapes mirroring the
  final layout) for **content-heavy** screens (feeds, profiles, lists) — they set structural
  expectations and feel faster. Studies report users perceive skeleton-loaded content as loading
  up to **~30–50% faster** than spinner-loaded content at *identical* real load times. Use
  **spinners/indeterminate** only for **short (<~2s), momentary** operations where you can't predict
  structure. Use **determinate progress bars** for long, known-duration operations (uploads,
  downloads).
- **Optimistic UI.** Update the UI **immediately** on user action, assuming success; reconcile/roll
  back only if the server errors. Ideal for **frequent, low-risk** actions (like, bookmark, toggle,
  mark-complete, send message). It removes perceived latency entirely. Pair with a graceful,
  clearly-communicated rollback path for the failure case.
- **Empty states.** A good empty state says **what's happening, why, and what to do next** — plus a
  single clear CTA. Three flavours: **first-use** (onboarding opportunity), **user-cleared**
  (success/accomplishment), and **error/no-results**. Don't ship a blank screen.
- **Error states.** Be **clear, calm, and helpful**; no jargon or codes-only. Explain what happened
  and offer a **recovery action** (Retry, fallback content, contact). Preserve user input on error.
- **Offline / offline-first states.** The "no internet connection" screen is both an empty *and*
  error state — give a recognisable icon/illustration on-brand, a plain explanation, and a
  **Retry**. Better: **offline-first UX** — cache content so the app is usable offline, queue
  writes and sync when back online (pairs naturally with optimistic UI), and show an unobtrusive
  **offline banner** rather than blocking the whole UI.
- **Instant feedback / perceived-latency techniques.** Acknowledge every tap within ~**100ms**
  (ripple/press state, haptic); show progress for anything over ~1s; prefetch likely-next content;
  animate transitions to mask load. The felt speed is governed by **feedback latency**, not just
  total time.

---

## 9. Mobile Accessibility

- **Screen readers.** **VoiceOver (iOS)** and **TalkBack (Android)** navigate via touch gestures
  (swipe to move between elements, double-tap to activate) rather than a keyboard. Requirements:
  every interactive element needs an accessible **name/label/content-description**, correct
  **role/traits**, **state** (selected/expanded/disabled), a **logical focus order**, and grouped
  content where appropriate. Decorative images hidden from AT. Custom gestures must have AT-reachable
  alternatives.
- **Dynamic text sizing.** Support **Dynamic Type (iOS)** and **Android font-scale** so text
  reflows and scales with the OS setting (satisfies **WCAG 1.4.4 Resize Text** and **1.4.10
  Reflow**). Don't hard-code point sizes or fixed-height text containers; text must not clip or
  truncate at large sizes.
- **Contrast.** WCAG **1.4.3**: **4.5:1** for normal text, **3:1** for large text (AA); **3:1** for
  UI components and graphical objects (**1.4.11**). Especially critical outdoors (see situational).
- **Motor accessibility.** Adequate **target size** (§2) and **spacing**; keep primary controls in
  the **reachable zone** (§1); support **WCAG 2.5.1 Pointer Gestures** (single-pointer alternative
  to complex gestures) and **2.5.2 Pointer Cancellation** (action on up-event, so users can slide
  off to abort).
- **Reduce motion.** Honour **Reduce Motion / Remove Animations** OS settings (**WCAG 2.3.3
  Animation from Interactions**) — replace parallax/large transitions with fades/instant changes;
  avoid motion that can trigger vestibular disorders.
- **Motion actuation.** Provide non-motion alternatives to shake/tilt actions (**WCAG 2.5.4**).
- **Situational impairments** — design for able-bodied users in bad conditions, which broadens the
  same fixes: **bright sunlight** (high contrast, large text), **one hand / holding something**
  (thumb-zone, big targets), **on the move / walking** (large targets, forgiving hit areas,
  minimal precision), **cold hands / gloves**, **noisy or silent contexts** (don't rely on
  sound-only; multi-modal feedback). Accessibility and situational design reinforce each other.
- WCAG **2.1/2.2** added the mobile-relevant criteria: **1.3.4 Orientation** (don't lock to one
  orientation unless essential), **2.5.1 Pointer Gestures**, **2.5.2 Pointer Cancellation**,
  **2.5.4 Motion Actuation**, **2.5.5/2.5.8 Target Size**. Test with **real devices + real AT
  (VoiceOver/TalkBack)**, not just automated scanners.

---

## 10. Cross-Platform Strategy

**The core tension: native familiarity vs brand consistency.**

- **Follow native idioms when** familiarity and muscle memory dominate the value: system **Back**
  behaviour and back stack, **share sheets**, date/time pickers, keyboard/autofill,
  notification channels, platform typography (SF vs Roboto), navigation transitions, and
  platform-standard gestures (edge-swipe back, pull-to-refresh). Getting these "wrong per platform"
  is the fastest way to make an app "feel wrong." Users don't compare your iOS and Android apps —
  they compare your app to the **other apps on their own device**.
- **Prioritise consistent brand experience when** the interaction is your differentiator or the
  brand is the product. High-brand apps (Instagram, Spotify, Airbnb) look **essentially the same on
  both platforms** and users accept it. A single design system is also **cheaper to build and
  maintain** than two divergent ones.
- **Pragmatic default:** **consistent brand/content + platform-native mechanics.** Keep your layout,
  color, and content model identical; adapt the *plumbing* — Back behaviour, navigation chrome,
  pickers, permissions, typography, gestures — to each platform. React Native/Flutter apps should
  still branch on the platform for these mechanics (`Platform.select`, adaptive components).

**Mobile UX success metrics (what the agent should recommend measuring):**
- **Activation** — % of new users reaching the **first-value ("aha") event** (define per product;
  not just "opened app").
- **Retention** — **D1 / D7 / D30** return rates. 2025–26 medians ≈ **D1 25–26%, D7 11–13%, D30
  5–7%**; top quartile ≈ **D1 >30%, D7 >15%, D30 >8%**. Benchmarks vary widely by vertical
  (fintech/social retain higher; games/health lower), so compare within category. (Note: some
  studies report much lower D7/D30 medians when measured strictly on returning-user cohorts — use
  a consistent definition and compare like-for-like.)
- **Funnel / drop-off** — conversion at each step; find the biggest leak (sign-in walls, permission
  prompts, and long forms are usual suspects).
- **Task success rate & time-on-task** — usability-test measures for core flows.
- **Engagement** — session length/frequency, DAU/MAU stickiness, feature adoption.
- **Permission & notification opt-in rates** and **notification CTR** — leading indicators for
  re-engagement.

---

## Named-Pattern Quick Reference

| Pattern | One-line rule |
|---|---|
| Thumb zone | Primary actions in the bottom-third natural zone; rare/destructive in top corners |
| Bottom-sheet-first | Prefer bottom sheets to top modals; controls live where the thumb is |
| 44/48/24 rule | 44pt (iOS) / 48dp (Android) usability target; 24px WCAG AA floor, 44px AAA |
| Permission priming (soft ask) | Explain in your own UI in-context first; only then fire the one-shot native dialog |
| Progressive/contextual onboarding | Teach features just-in-time; show value before the sign-in wall |
| Skeleton screens | Structural placeholders for content loads; feel ~30–50% faster than spinners |
| Optimistic UI | Update instantly, reconcile on error — for frequent low-risk actions |
| Single-column + right keyboard | No side-by-side fields; correct `inputmode`/`autocomplete`; minimize typing |
| Inline validation | Validate at the field on blur; ~22% higher success, ~42% faster |
| Visible nav over hamburger | Hidden nav ≈ half the discoverability, 15% slower on mobile |
| Deep linking | Notifications/links land on the exact screen with a correct back stack |
| Offline-first | Cache, queue writes, sync on reconnect; non-blocking offline banner |
| Gesture + fallback | Never make a core action gesture-only; always a visible alternative |

---

## Sources

- Steven Hoober, "How Do Users Really Hold Mobile Devices?" (UXmatters, 2013) — via Smashing/Textbook of Usability: https://www.textbookofusability.com/references/hoober2013.html
- The Thumb Zone: Designing For Mobile Users — Smashing Magazine: https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/
- Scott Hurff, "How to Design for Thumbs in the Era of Huge Screens": https://www.scotthurff.com/posts/how-to-design-for-thumbs-in-the-era-of-huge-screens/
- Josh Clark / "How We Hold Our Gadgets" — A List Apart: https://alistapart.com/article/how-we-hold-our-gadgets/
- Hamburger Menus and Hidden Navigation Hurt UX Metrics — Nielsen Norman Group: https://www.nngroup.com/articles/hamburger-menus/
- Beyond the Hamburger: What Makes Navigation Discoverable on Mobile — NN/G: https://www.nngroup.com/articles/find-navigation-mobile-even-hamburger/
- WCAG 2.5.8 Target Size (Minimum) implementation guide — AllAccessible: https://www.allaccessible.org/blog/wcag-258-target-size-minimum-implementation-guide
- What Is the WCAG 2.5.8 Target Size Minimum — TestParty: https://testparty.ai/blog/wcag-target-size-guide
- Mobile Accessibility Testing: WCAG 2.2 Requirements — TestParty: https://testparty.ai/blog/mobile-accessibility-testing
- Mobile Patterns that Break (and Make) Accessibility: Bottom Sheets, Gestures, Infinite Scroll — TestParty: https://testparty.ai/blog/mobile-accessibility-patterns
- LukeW | Touch Target Sizes (MIT Touch Lab 10–14mm): https://www.lukew.com/ff/entry.asp?1085=
- Finger-Friendly Design: Ideal Mobile Touchscreen Target Sizes — Smashing Magazine: https://www.smashingmagazine.com/2012/02/finger-friendly-design-ideal-mobile-touchscreen-target-sizes/
- Determining Optimal Target Sizes for One-Handed Thumb Use (Univ. of Maryland HCIL): http://www.cs.umd.edu/hcil/trs/2006-11/2006-11.htm
- Gesture Discoverability: A Core Component of Interaction Design — David Shittu (Bootcamp/Medium): https://medium.com/design-bootcamp/gesture-discoverability-a-core-component-of-interaction-design-4026c8e67d6d
- Designing swipe-to-delete and swipe-to-reveal interactions — LogRocket: https://blog.logrocket.com/ux-design/accessible-swipe-contextual-action-triggers/
- Pull-to-refresh (history) — Wikipedia: https://en.wikipedia.org/wiki/Pull-to-refresh
- GhostUI: Unveiling Hidden Interactions in Mobile UI — arXiv: https://arxiv.org/pdf/2601.19258
- 2025 Guide to Haptics: Enhancing Mobile UX with Tactile Feedback — Saropa: https://saropa.com/articles/2025-guide-to-haptics-enhancing-mobile-ux-with-tactile-feedback/
- Haptics for Mobile: best practices for Android and iOS — WYVRN: https://www.wyvrn.com/blog/2021/05/13/haptics-for-mobile-the-best-practices-for-android-and-ios/
- Haptic UX — The Design Guide for Building Touch Experiences — Justin Baker (Muzli): https://medium.muz.li/haptic-ux-the-design-guide-for-building-touch-experiences-84639aa4a1b8
- Bottom navigation — Material Design: https://m2.material.io/components/bottom-navigation
- Bottom sheets — Material Design 3 guidelines: https://m3.material.io/components/bottom-sheets/guidelines
- App Navigation Patterns: Tab Bar vs Hamburger vs Bottom Sheet — Appy Pie: https://www.appypie.com/blog/app-navigation-patterns
- Priming users to grant mobile apps permission — Appcues: https://www.appcues.com/product-adoption-academy/mobile-app-onboarding-101/priming-users-to-grant-mobile-apps-permission
- Asking nicely: 3 strategies for successful mobile permission priming — Appcues: https://www.appcues.com/blog/mobile-permission-priming
- Permission Priming onboarding pattern — UserOnboard: https://www.useronboard.com/onboarding-ux-patterns/permission-priming/
- Mobile Permission Requests: Timing, Strategy & Compliance — Dogtown Media: https://www.dogtownmedia.com/the-ask-when-and-how-to-request-mobile-app-permissions-camera-location-contacts/
- A Guide To Push Notification Best Practices — Braze: https://www.braze.com/resources/articles/push-notifications-best-practices
- BENCHMARKS: How Push Notifications Impact Mobile App Retention Rates — Airship/Urban Airship: https://grow.urbanairship.com/rs/313-QPJ-195/images/WP_App_Retention_Rates_Benchmarks.pdf
- 50+ Push Notification Statistics for 2025 — MobiLoud: https://www.mobiloud.com/blog/push-notification-statistics
- Progressive Onboarding: contextual onboarding flows — Userpilot: https://userpilot.com/blog/progressive-onboarding/
- The essential guide to mobile user onboarding: UI/UX patterns — Appcues: https://www.appcues.com/blog/essential-guide-mobile-user-onboarding-ui-ux
- First Impressions - a Guide to Onboarding UX — Toptal: https://www.toptal.com/designers/product-design/guide-to-onboarding-ux
- 6 Mobile Checkout Usability Considerations — Baymard Institute: https://baymard.com/blog/mobile-checkout
- Ecommerce Checkout UX Guide — Baymard Institute: https://baymard.com/learn/checkout-flow-ux-optimization
- Forms On Mobile Devices: Modern Solutions — Smashing Magazine (Luke Wroblewski work): https://www.smashingmagazine.com/2010/03/forms-on-mobile-devices-modern-solutions/
- LukeW | Web Form Innovations on Mobile Devices: https://www.lukew.com/ff/entry.asp?1000=
- Skeleton Screens vs Loading Spinners: When to Use Each — Onething Design: https://www.onething.design/post/skeleton-screens-vs-loading-spinners
- Skeleton loading screen design — perceived performance — LogRocket: https://blog.logrocket.com/ux-design/skeleton-loading-screen-design/
- Empty States: The Most Overlooked Aspect of UX — Toptal: https://www.toptal.com/designers/ux/empty-state-ux-design
- Empty States in Application Design: 3 Guidelines — NN/G (video): https://www.nngroup.com/videos/empty-states-in-application-design-guidelines/
- Error Messages Designing and UX 101 — Usersnap: https://usersnap.com/blog/error-messages-best-practices/
- Mobile App Accessibility — iOS, Android & WCAG Guide (2026) — AccessibilityChecker: https://www.accessibilitychecker.org/guides/mobile-apps-accessibility/
- VoiceOver vs TalkBack: A Developer's Guide — Auditsu: https://auditsu.com/resources/voiceover-vs-talkback
- Designing native apps for Android and iOS: differences and similarities — Cheesecake Labs: https://cheesecakelabs.com/blog/designing-native-apps-for-android-and-ios-key-differences-and-similarities/
- iOS vs. Android UI Design: 9 Key Differences — UXPin: https://www.uxpin.com/studio/blog/ios-vs-andoid-ui-design-for-mobile/
- Design from iOS to Android (and Back Again) — Google Design: https://design.google/library/design-ios-android-and-back-again
- Retention (D1/D7/D30) — Mobile App Retention Benchmarks — MWM: https://mwm.ai/glossary/retention
- Increase app retention 2026: Benchmarks — Pushwoosh: https://www.pushwoosh.com/blog/increase-user-retention-rate/
- Retention Rates for Mobile Apps by Industry — Plotline: https://www.plotline.so/blog/retention-rates-mobile-apps-by-industry

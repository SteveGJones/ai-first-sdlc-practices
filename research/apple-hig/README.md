# Apple Human Interface Guidelines (HIG) — Research Reference

Authoritative reference on Apple's **Human Interface Guidelines** for iOS/iPadOS —
https://developer.apple.com/design/human-interface-guidelines — gathered to ground the
[`apple-hig-architect`](../../agents/core/apple-hig-architect.md) agent (feature #215).

**Compiled:** 2026-07-22. Current shipping design language is **Liquid Glass (iOS 26, WWDC 2025)**.
Version-sensitive figures (SwiftUI API names, App Review guideline numbers, device sizes) should be
re-checked against the linked official sources before quoting as current.

## Sourcing note

Apple's HIG pages are JS-rendered single-page apps that return only a page title to non-browser
fetchers. The human-readable content was retrieved from Apple's **DocC JSON data endpoints** (the
`tutorials/data/...` paths under `developer.apple.com` that back the public HIG pages) — so values
here are Apple's own text, not paraphrase. Each file has a full Sources list.

## Contents

| File | Covers |
|------|--------|
| [`01-foundations-navigation-components.md`](01-foundations-navigation-components.md) | Design principles (clarity/deference/depth), **Liquid Glass / iOS 26**, layout & safe areas, size classes, navigation & modality (tab bars, nav stacks, sidebars, sheets/detents, popovers, alerts, action sheets), SF Pro type scale + Dynamic Type, semantic/dynamic colors & materials, SF Symbols, core components + SwiftUI/UIKit mapping |
| [`02-interaction-platform-accessibility.md`](02-interaction-platform-accessibility.md) | Gestures, 44pt targets, iPad pointer, keyboard, drag & drop, haptics (UIFeedbackGenerator/Core Haptics), motion & Reduce Motion, iOS platform features (permissions/ATT, notifications, widgets, Live Activities/Dynamic Island, App Clips, share sheet, Sign in with Apple, Universal Links/Handoff, App Shortcuts/Siri, Controls), accessibility (VoiceOver, Dynamic Type, contrast/WCAG AA, reduce/increase/differentiate family), App Store UX, SwiftUI mapping, HIG-vs-Material-3 |

## Key facts at a glance

- **Liquid Glass (iOS 26, WWDC 2025-06-09)** — dynamic translucent material forming a floating
  control/navigation layer above content; Regular vs Clear variants; adopted via standard SwiftUI/UIKit
  components (custom: `.glassEffect`, `.buttonStyle(.glass)`, `GlassEffectContainer`); honours Reduce
  Transparency/Motion; `UIDesignRequiresCompatibility` opt-out. Biggest visual overhaul since iOS 7.
- **Touch target**: 44×44 pt minimum (28 pt hard floor); ~12 pt padding around bezelled, ~24 pt around unbezelled.
- **Type scale**: Large Title 34/41 → Caption 2 11/13 pt; iOS body 17 pt default / 11 pt min; **Dynamic Type** is a first-class requirement (support ≥200% enlargement).
- **Navigation**: tab bar (bottom, ≤5), navigation stack + large titles, sidebars (iPad); modality decision tree (sheets w/ medium/large detents, popovers→sheet in compact, alerts vs action sheets, full-screen).
- **Color**: semantic dynamic colors (`label`, `systemBackground`, `systemGray1–6`); never hard-code; auto-adapts to light/dark/increase-contrast.
- **Accessibility**: targets WCAG 2 AA (4.5:1 / 3:1); VoiceOver, Reduce Motion/Transparency, Increase Contrast, Differentiate Without Color.
- **iOS platform features** that distinguish native iOS UX: permission priming + ATT rules, provisional notifications, Widgets, Live Activities/Dynamic Island (~8h, 44pt radius), App Clips, share sheet, Sign in with Apple (Guideline 4.8), Universal Links, App Shortcuts (≤10).
- **App Review UX rules**: in-app account deletion (5.1.1(v)), specific purpose strings, no dark patterns, login parity.

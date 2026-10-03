# Mobile-Native Interaction UX — Research Reference

Authoritative, evidence-based reference on **platform-agnostic mobile-native interaction and UX** —
the patterns that apply to phone/tablet apps regardless of iOS vs Android — gathered to ground the
[`mobile-ux-architect`](../../agents/core/mobile-ux-architect.md) agent (feature #215).

**Compiled:** 2026-07-22. Cited to reputable primary/secondary sources (Nielsen Norman Group, Baymard
Institute, Smashing Magazine, LukeW, Hoober, WCAG/W3C, Airship). Retention benchmarks and industry
statistics are point-in-time — re-check before quoting as current.

## Contents

| File | Covers |
|------|--------|
| [`01-mobile-native-interaction-ux.md`](01-mobile-native-interaction-ux.md) | Thumb zones / reachability (Hoober), touch targets & the 44/48/24 rule, gesture vocabulary & discoverability, haptics, navigation patterns (visible-nav-vs-hamburger evidence, back-behavior by platform), onboarding, permission priming & notifications UX, mobile forms, states & perceived performance (skeleton screens, optimistic UI), mobile accessibility (WCAG 2.1/2.2 mobile criteria, situational impairments), cross-platform strategy & success metrics |

## Key facts at a glance

- **Thumb zone (Hoober, n=1,333)**: 49% one-handed, 36% cradled, 15% two-handed; ~75% of interactions thumb-driven → primary actions belong in the **bottom third**; bottom-nav & bottom-sheet-first.
- **Touch targets**: 44 pt (iOS) / 48 dp (Android) usability target; WCAG **2.5.8** AA floor 24 px, **2.5.5** AAA 44 px; MIT Touch Lab finger pad 10–14 mm. Spacing matters as much as size.
- **Hidden nav hurts (NN/G)**: hamburger cuts discoverability ~half; ~15% slower on mobile; prefer visible/combo nav for top-level destinations. Bottom tab bar for 3–5.
- **Permission priming (soft ask)**: explain in your own UI in-context first, then fire the one-shot native dialog — a hard denial is expensive (esp. iOS). Deferred prompts ≈ +28% grant rates.
- **Forms**: minimize *typing effort* (Baymard: effort > field count) — right `inputmode`/`autocomplete`, single column, top-aligned labels, inline validation (~+22% success, ~42% faster), guest checkout.
- **Perceived performance**: skeleton screens feel ~30–50% faster than spinners; optimistic UI for frequent low-risk actions; calm error/empty/offline states; acknowledge taps within ~100 ms.
- **Cross-platform**: consistent brand/content + **platform-native mechanics** (Back behavior, share, pickers, typography, gestures). The four highest-risk mismatches: back navigation, bottom-bar semantics, system fonts, share/action affordances.
- **Metrics**: activation (first-value event), D1/D7/D30 retention (2025–26 medians ≈ 25/12/6%), funnel drop-off, task success, opt-in rates.

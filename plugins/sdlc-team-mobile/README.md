# sdlc-team-mobile

Shared **cross-platform mobile** base plugin. Holds the mobile agents whose expertise applies to
**both** iOS and Android, so they live in one place rather than being duplicated into each platform
plugin.

## Agents (2)

- **`mobile-architect`** — mobile app *architecture*: native iOS/Android vs React Native vs Flutter vs
  Kotlin Multiplatform, cross-platform trade-offs, state management, mobile performance, mobile CI/CD,
  and mobile security.
- **`mobile-ux-architect`** — platform-agnostic mobile-native interaction UX: thumb-zone reachability,
  touch targets & gestures, permission priming, onboarding, mobile forms, loading/empty/error/offline
  states, mobile accessibility (WCAG 2.1/2.2), and cross-platform strategy & metrics.

## Relationship to other plugins

Install alongside the platform plugin(s):

- **`sdlc-team-ios`** — Apple Human Interface Guidelines specialist (`apple-hig-architect`)
- **`sdlc-team-android`** — Google Material Design 3 specialist (`material-design-3-architect`)

`/sdlc-core:setup-team` recommends this base automatically whenever you select an iOS or Android
project type. For framework-agnostic UX strategy and design-system governance, see `ux-ui-architect`
in `sdlc-team-fullstack`.

## Part of the SDLC plugin family

Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` for personalized recommendations.

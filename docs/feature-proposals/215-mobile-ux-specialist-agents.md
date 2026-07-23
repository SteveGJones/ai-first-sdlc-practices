# Feature Proposal: Mobile-UX Specialist Agents (apple-hig-architect + mobile-ux-architect)

**Proposal Number:** 215
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-22
**Target Branch:** `feature/material-design-3-agent` (continues the UX-specialist coverage work started for #214)
**GitHub Issue:** #215 (relates to #214)

---

## Problem Statement

Adding `material-design-3-architect` (#214) gave the suite deep **Android/Material** mobile-UX
coverage. An audit of mobile-UX capability then surfaced that coverage is **asymmetric** and seamed:

- **No iOS/HIG design specialist.** `mobile-architect` (source: `agents/core/mobile-architect.md`)
  covers Apple's Human Interface Guidelines only at an *architecture* level — `NavigationStack`,
  `TabView`, SF Symbols, Dynamic Type as compliance checkboxes. There is no agent that owns Apple
  HIG as a *design* discipline the way `material-design-3-architect` now owns Material 3. We created
  the asymmetry: Android UX has depth; iOS UX does not.
- **No mobile-native interaction/UX design agent.** The UX concerns unique to mobile *regardless of
  platform* — thumb reachability, gesture vocabulary & discoverability, haptics, permission priming,
  onboarding, notifications UX, offline/empty/error states, mobile forms, perceived performance — are
  split thinly between the deliberately **web-first** `ux-ui-architect` and the **architecture-first**
  `mobile-architect`. Nobody owns them.
- **Concrete bug.** `mobile-architect` handed UX off to a **`ux-designer`** agent that does not exist —
  a dangling reference. (Fixed as part of this work.)

**Who is affected:** any team building an iOS or cross-platform mobile product gets architecture-grade
platform-guideline notes but no design-grade iOS UX specialist, and no owner for cross-platform
mobile-native interaction design. iOS is the higher-revenue platform for many products; this is a
material gap.

## User Stories

- As an **iOS/SwiftUI team**, I want a specialist grounded in Apple HIG (including the 2025 Liquid
  Glass redesign) so I get iOS-idiomatic navigation, type, materials, and interaction — not a web or
  Android pattern transplanted onto iOS.
- As a **cross-platform mobile team**, I want an agent that owns mobile-native UX (thumb zones,
  gestures, permissions, onboarding, offline states) so those decisions aren't lost between the
  web-first generalist and the architecture agent.
- As a **product team**, I want to know when to follow each platform's native idioms vs. a consistent
  brand experience, with the trade-offs made explicit.
- As the **`mobile-architect` agent**, I want to hand UX to real, correctly-named specialists.
- As the **`ux-ui-architect` / `material-design-3-architect` agents**, I want clear boundaries with
  the iOS and mobile-interaction specialists so advice doesn't overlap or conflict.

## Proposed Solution

### High-Level Approach

Add **two** specialist agents to `sdlc-team-fullstack`, each grounded in dedicated deep research
against authoritative sources, and complete the cross-reference web so the five UX/mobile agents form
a clean, non-overlapping set:

| Agent | Owns |
|-------|------|
| `ux-ui-architect` | Framework-agnostic UX strategy, user research, IA, cross-design-system a11y governance |
| `material-design-3-architect` | Android / Material Design 3 fidelity (#214) |
| **`apple-hig-architect`** *(new)* | iOS/iPadOS UX to Apple HIG |
| **`mobile-ux-architect`** *(new)* | Platform-agnostic mobile-native interaction UX |
| `mobile-architect` | Mobile *architecture* (native/cross-platform, state, perf, CI/CD, security) |

### Technical Approach

1. **Deep-research reference sets** (parallel research agents, official-source-grounded), persisted
   under `research/`:
   - `research/apple-hig/` — HIG foundations/navigation/components; iOS interaction, platform
     features (permissions/ATT, notifications, widgets, Live Activities/Dynamic Island, share sheet,
     Sign in with Apple), accessibility, App Store UX, SwiftUI mapping, Liquid Glass (iOS 26).
   - `research/mobile-ux/` — cross-platform mobile-native interaction UX (thumb zones, targets &
     gestures, haptics, navigation, onboarding, permissions/notifications, forms, states/perceived
     performance, accessibility, cross-platform strategy & metrics).

2. **Two new source agents** following the established agent contract (mirrors
   `material-design-3-architect.md`): valid frontmatter (`name`, `description`, `model: sonnet`,
   `tools`, ≥2 `examples` with `<example>`/`<commentary>`, an allowed `color`, `first_party_alternatives`),
   body with core competencies, process, decision guidance, boundaries, and collaboration handoffs.

3. **Wiring**:
   - Add both source paths to `release-mapping.yaml` under `sdlc-team-fullstack`.
   - Regenerate `AGENT-INDEX.md` / `AGENT-CATALOG.json` via `build-agent-catalog.py`.
   - Cross-reference from `ux-ui-architect`, `material-design-3-architect`, and `mobile-architect`
     (the last also fixing the `ux-designer` dangling reference).
   - Technology-registry: add an Apple-HIG / SwiftUI entry so setup can surface `apple-hig-architect`
     on detecting iOS/SwiftUI signals (npm/pod signals are limited — document manual-surface cases,
     as with M3).
   - Bump `plugins/sdlc-team-fullstack` version; update CLAUDE.md / README agent counts.

4. **Validation**: `validate-agent-format`, `validate-agent-official`, technical-debt,
   broken-references, registry + setup tests, `--pre-push`. Release via `/sdlc-core:release-plugin`.

### Alternatives Considered

1. **Fold iOS + mobile-interaction UX into `mobile-architect`.** *Cons:* conflates architecture with
   design (already a stretch there), bloats one agent, and repeats the asymmetry problem. **Not chosen.**
2. **One combined `mobile-ux-architect` covering iOS + Android + generic.** *Cons:* iOS HIG and Material 3
   are each large, opinionated, and divergent; one agent can't hold both at specialist depth, and it
   would overlap `material-design-3-architect`. **Not chosen** — split iOS-specific from platform-agnostic.
3. **Only fix the dangling reference; add nothing.** *Cons:* leaves the real coverage gaps. **Rejected**
   (does not meet the need), though the fix is included here regardless.

---

## Implementation Plan

### Phase 1: Research (foundation)
- [ ] [P] Research Apple HIG foundations, navigation & components (incl. Liquid Glass / iOS 26)
- [ ] [P] Research iOS interaction, platform UX features & accessibility
- [ ] [P] Research platform-agnostic mobile-native interaction UX
- [ ] Distil into `research/apple-hig/` and `research/mobile-ux/` cited references

### Phase 2: Agent authoring
- [ ] Write `agents/core/apple-hig-architect.md`
- [ ] Write `agents/core/mobile-ux-architect.md`
- [ ] Self-review against `material-design-3-architect.md` for structural parity + CI fields

### Phase 3: Wiring, validation & release
- [x] Fix `ux-designer` dangling reference in `mobile-architect.md`
- [ ] Cross-reference from `ux-ui-architect`, `material-design-3-architect`, `mobile-architect`
- [ ] Add both to `release-mapping.yaml`; regenerate AGENT-INDEX/CATALOG
- [ ] Technology-registry entry for Apple HIG / SwiftUI
- [ ] Bump plugin version; update CLAUDE.md / README counts
- [ ] Run validators (format, official, technical-debt, broken-references, registry + setup tests)
- [ ] `/sdlc-core:release-plugin`; complete retrospective; PR

**Dependencies:** Web access for research (in progress). Builds on #214 (`material-design-3-architect`),
which the cross-references point to; this work stays on the same branch.

---

## Acceptance Criteria

```
Given a user asks "how should the navigation and top bar work for our iOS app under iOS 26"
When apple-hig-architect is invoked
Then it gives HIG-idiomatic guidance (tab bar vs navigation stack, Liquid Glass materials, SF type,
     safe areas) with correct SwiftUI mapping, distinct from Android/Material advice
```

```
Given a user asks "when and how should we ask for notification permission in our mobile app"
When mobile-ux-architect is invoked
Then it recommends in-context permission priming (not on launch), explains the cost of a hard denial,
     and gives a pattern that works on both iOS and Android
```

```
Given the two new agent files
When CI agent-format / official validation runs
Then both pass (valid frontmatter, >=2 examples with commentary, allowed color, no technical debt)
```

```
Given mobile-architect hands off a UX question
When it names the target agent
Then it references ux-ui-architect / apple-hig-architect / material-design-3-architect / mobile-ux-architect
     (no reference to a non-existent ux-designer)
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Liquid Glass / iOS 26 details are new and may be mis-stated | Med | Med | Ground in official Apple sources; date-stamp; flag new-2025 vs long-standing HIG explicitly |
| Overlap/conflict among the 5 UX/mobile agents | Med | Med | Explicit ownership table + bidirectional cross-references; each agent's Boundaries route out |
| Apple-HIG registry detection is weak (no npm signal) | Med | Low | Document manual-surface cases in the entry, as done for M3; detect SwiftUI/CocoaPods signals where possible |
| Agent-format CI failures | Low | Med | Mirror `material-design-3-architect.md`; run validators before PR (learned the color-enum constraint on #214) |

## Open Questions

- [ ] Agent naming: `apple-hig-architect` vs `ios-ux-architect`? (Proposal: `apple-hig-architect` — names the authority, covers iPadOS too.)
- [ ] Should `mobile-ux-architect` and `ux-ui-architect` merge long-term? (Proposal: no — mobile-native interaction is a distinct, deep enough discipline; keep separate with cross-refs.)
- [ ] One combined PR for #214 + #215, or split? (Proposal: one PR — the cross-references are interdependent and it tells a coherent "UX specialist agents" story.)

## Security & Privacy

N/A. Deliverables are static agent definitions (markdown) + research references. No code execution,
no auth changes, no data collection, no secrets. Research gathered from public official documentation.

---

**Retrospective**: `retrospectives/215-mobile-ux-specialist-agents.md` (link after implementation)

# Feature Proposal: sdlc-team-ios platform agents

**Proposal Number:** 219
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/ios-platform-agents`
**GitHub Issue:** #219 (phase of EPIC #217)

---

## Motivation

EPIC #217's structural split (#218) created a focused `sdlc-team-ios` plugin, but it ships only one
agent — `apple-hig-architect` (design). An iOS team also needs depth on **app architecture**,
**release engineering**, and **performance** — areas neither the HIG agent nor the cross-platform
`mobile-architect` (framework-selection altitude) covers. Fable's advice (in EPIC #217) identified
these as the three warranted iOS agents, deliberately excluding over-splits (TestFlight, widgets, and
iOS-security as standalone agents).

This proposal builds those three, grounded in deep research against official Apple sources — the same
research-first approach used for `material-design-3-architect` (#214) and `apple-hig-architect` (#216).

## User Stories

- As an **iOS engineer**, I want a `swiftui-architect` that speaks Observation/`@Observable`, MV vs TCA,
  `NavigationStack`, SwiftData, and structured concurrency so I get modern-iOS architecture guidance,
  not generic MVVM.
- As an **iOS release owner**, I want an `ios-release-engineer` that knows signing/provisioning,
  privacy manifests, App Store Connect/TestFlight, and App Review rules so submissions don't get
  rejected on avoidable issues.
- As an **iOS developer chasing jank or launch time**, I want an `ios-performance-specialist` that
  knows Instruments, MetricKit, launch phases, hitches, and app-size levers.
- As the **`apple-hig-architect` / `mobile-architect` agents**, I want clear boundaries so architecture,
  release, and performance route to the right specialist.

## Proposed Solution

### High-Level Approach

Add three agents to `sdlc-team-ios`, each grounded in a dedicated deep-research reference persisted
under `research/`. Follow the established agent contract (validated frontmatter with ≥2 examples,
allowed color, `first_party_alternatives`; body of competencies, process, decision guidance,
boundaries, collaboration). Cross-reference with `apple-hig-architect` (design), `mobile-architect`
(cross-platform architecture), and `mobile-ux-architect` (interaction).

### Technical Approach

1. **Research references** (`research/ios-swiftui-architecture/`, `research/ios-release-engineering/`,
   `research/ios-performance/`) — Apple-source-grounded, with Sources lists.
2. **Three source agents** in `agents/core/`: `swiftui-architect.md`, `ios-release-engineer.md`,
   `ios-performance-specialist.md`.
3. **Wiring**: add to `release-mapping.yaml` under `sdlc-team-ios`; populate the plugin `agents/`;
   bump `sdlc-team-ios` 0.1.0 → **0.2.0** (plugin.json + marketplace.json); regenerate
   AGENT-INDEX/CATALOG; update the plugin README, CLAUDE.md, and README counts.
4. **Validation**: `validate-agent-format`, `validate-agent-official`, technical-debt,
   broken-references, catalog/tests.

### Alternatives Considered

1. **Fewer/bigger agents** (fold release+performance into one "iOS engineering" agent). Rejected — the
   toolchains and expertise are distinct (App Store Connect vs Instruments); merging dilutes both.
2. **More agents now** (add widgets/App-Intents, iOS-security, Swift language). Rejected as over-split
   or out of scope — deferred per EPIC #217 (D2 for the language expert).
3. **Skills/validators in this PR.** Deferred — agents first (matches #214/#216); skills/validators are
   a follow-up phase so this PR stays reviewable.

---

## Implementation Plan

### Phase 1: Research
- [ ] [P] Research SwiftUI app architecture
- [ ] [P] Research iOS release engineering
- [ ] [P] Research iOS performance engineering
- [ ] Persist references under `research/ios-*`

### Phase 2: Agents
- [ ] Write `swiftui-architect.md`, `ios-release-engineer.md`, `ios-performance-specialist.md`
- [ ] Cross-reference with apple-hig-architect / mobile-architect / mobile-ux-architect

### Phase 3: Wiring, validation & release
- [ ] `release-mapping.yaml` + populate plugin agents; bump sdlc-team-ios 0.1.0 → 0.2.0 (both manifests)
- [ ] Regenerate AGENT-INDEX/CATALOG; update READMEs + CLAUDE.md counts
- [ ] Validators + tests; retrospective; PR

**Dependencies:** none beyond web research. Builds on #218 (sdlc-team-ios exists).

---

## Success Criteria

```
Given a user asks swiftui-architect "how should I manage state and navigation in a new iOS 26 app"
When it responds
Then it recommends Observation (@Observable), value-based NavigationStack, and SwiftData with correct
     modern APIs — distinct from HIG/design advice and from cross-platform framework selection
```

```
Given a user asks ios-release-engineer about a signing failure or App Store rejection
When it responds
Then it gives accurate provisioning/entitlement/privacy-manifest/App-Review guidance
```

```
Given the three new agent files
When CI agent-format / official validation runs
Then all pass (valid frontmatter, >=2 examples, allowed color, no technical debt, no broken refs)
```

```
Given sdlc-team-ios after this change
When its agents are listed
Then it contains apple-hig-architect + the 3 new agents (4 total); version is 0.2.0; catalog regenerated
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Apple APIs / guideline numbers date fast | Med | Med | Ground in official sources; date-stamp; flag version-sensitive items to re-verify |
| Overlap with apple-hig-architect / mobile-architect | Med | Low | Explicit boundaries + cross-references (design vs architecture vs release vs perf) |
| Broken-reference false positives from prose (`file.ext` tokens) | Med | Low | Avoid bare `filename.ext` in prose (learned in #214/#216) |
| Agent-format CI failure | Low | Med | Mirror validated agents; use allowed color enum; run validators pre-PR |

## Open Questions

- [ ] Swift language expert (`sdlc-lang-swift` vs bundled) — EPIC #217 D2, deferred.
- [ ] iOS skills/validators — follow-up phase after agents land.

## Security & Privacy

N/A. Static agent definitions + research references. No code execution, auth, data handling, or secrets.

---

**Retrospective**: `retrospectives/219-ios-platform-agents.md` (link after implementation)

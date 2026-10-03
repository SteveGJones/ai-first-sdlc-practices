# Feature Proposal: Split mobile plugins out of sdlc-team-fullstack

**Proposal Number:** 217
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-23
**Target Branch:** `feature/mobile-plugin-split`
**GitHub Issue:** #217 (EPIC — this is Phase 1: the structural split)

---

## Motivation

`sdlc-team-fullstack` has grown to **13 agents** spanning web frontend, backend, API, data, DevOps,
GitHub, integration testing, and (after #216) five UX/mobile agents. For a team doing focused **iOS**
or **Android** work this is **noisy** — most of the plugin is irrelevant, and the mobile-relevant
agents are buried among web/backend ones.

This proposal is **Phase 1 of EPIC #217**: the structural split. It creates focused platform plugins
from the *existing* agents and slims `sdlc-team-fullstack` back to an honest web bundle. It adds **no
new agents** — those are later phases of the EPIC. The split alone delivers the noise reduction the
EPIC's problem statement calls for.

Decisions settled with the maintainer before implementation:
- **Naming:** follow the family `sdlc-*` convention → `sdlc-team-ios`, `sdlc-team-android`, `sdlc-team-mobile`.
- **Migration:** clean cut — remove the four mobile agents from `sdlc-team-fullstack` in one breaking
  bump (→ 2.0.0) with a migration note; no dual-shipping (which would register agents twice).
- **Scope:** structural split only this pass; new platform agents/skills/validators are follow-up phases.

## User Stories

- As an **iOS developer**, I want an `sdlc-team-ios` plugin with only iOS-relevant agents so I'm not wading through backend/web/data specialists.
- As an **Android developer**, I want the same via `sdlc-team-android`.
- As a **cross-platform mobile team**, I want the shared mobile agents (architecture, interaction UX) in one base plugin so they aren't duplicated/registered twice when I install both platform plugins.
- As a **web full-stack team**, I want `sdlc-team-fullstack` to be an honest web bundle without mobile noise.
- As a **maintainer**, I want the split done via `release-mapping.yaml` re-mapping (no source moves, no content duplication) so it's low-risk and reversible.

## Proposed Solution

### High-Level Approach

Agent *sources* stay in `agents/core/`; `release-mapping.yaml` fans one source into N plugins at
release time. So this is a **manifest change**, not a file move or content duplication. The three
cross-platform agents are not duplicated into both platform plugins — they live once in a shared base.

### Target structure

```
sdlc-team-mobile     (NEW, 0.1.0)   mobile-architect, mobile-ux-architect
sdlc-team-ios        (NEW, 0.1.0)   apple-hig-architect
sdlc-team-android    (NEW, 0.1.0)   material-design-3-architect
sdlc-team-fullstack  (2.0.0)        9 web agents (mobile agents removed)
```

`sdlc-team-fullstack` after the split (9): `frontend-architect`, `backend-architect`, `api-architect`,
`devops-specialist`, `ux-ui-architect`, `frontend-security-specialist`, `data-architect`,
`integration-orchestrator`, `github-integration-specialist`.

**Why `ux-ui-architect` stays in fullstack:** its remit is framework-agnostic design systems + web
user research; on mobile its role is covered by the platform design agent + `mobile-ux-architect`.

### Technical Approach

1. **`release-mapping.yaml`**: remove the 4 mobile agents from `sdlc-team-fullstack`; add
   `sdlc-team-mobile`, `sdlc-team-ios`, `sdlc-team-android` sections mapping the relevant sources.
2. **New plugin dirs** (`plugins/sdlc-team-{mobile,ios,android}/`): `.claude-plugin/plugin.json`
   (0.1.0), `agents/` populated from the mapped sources, and a `README.md` each.
3. **`sdlc-team-fullstack`**: remove the 4 mobile agent files from `plugins/.../agents/`; bump
   `plugin.json` 1.2.0 → **2.0.0**; update description; add a migration note to its README.
4. **`.claude-plugin/marketplace.json`**: add the 3 new plugins; bump fullstack to 2.0.0 + new description.
5. **`setup-team` SKILL**: add "iOS app" / "Android app" project types recommending the platform
   plugin + `sdlc-team-mobile` as a unit; update the recommendation matrix.
6. **Docs/catalog**: regenerate `AGENT-INDEX.md` / `AGENT-CATALOG.json`; update `CLAUDE.md` plugin
   table + `README.md`; update `AGENT-INDEX` header counts and any cross-reference sites.
7. **Validation**: `check-broken-references.py`, technical-debt, agent-format (moved agents unchanged),
   registry + setup tests; verify no agent is registered twice.

**Note on agent cross-references:** agents are invoked by *name*, not by plugin, so the existing
"work closely with `<agent>`" prose keeps resolving across plugins — no agent-body edits needed.

### Alternatives Considered

1. **Duplicate shared agents into both platform plugins.** Rejected — a team with both installed sees each shared agent registered twice, re-creating the noise problem.
2. **Leave shared agents in fullstack; platform plugins depend on it.** Rejected — pulls the whole web bundle back in as a dependency, defeating the noise reduction.
3. **One-release deprecation window (dual-map).** Rejected per maintainer decision — overlap registers agents twice; clean cut + CHANGELOG note is cleaner.

---

## Implementation Plan

### Phase 1: Manifests
- [ ] Edit `release-mapping.yaml` (remove 4 from fullstack; add 3 new plugin sections)
- [ ] Create the 3 new plugin dirs (plugin.json + agents/ + README.md)
- [ ] Remove the 4 mobile agent files from the fullstack plugin; bump fullstack 1.2.0 → 2.0.0 + migration note

### Phase 2: Catalog, marketplace, setup
- [ ] Update `.claude-plugin/marketplace.json` (add 3, bump fullstack)
- [ ] Update `setup-team` SKILL (iOS/Android project types + matrix)
- [ ] Regenerate `AGENT-INDEX.md` / `AGENT-CATALOG.json`; update `CLAUDE.md`, `README.md` counts/tables

### Phase 3: Validation & release
- [ ] `check-broken-references.py`, technical-debt, format, registry + setup tests
- [ ] Verify no agent registered twice; marketplace ↔ plugin.json versions consistent
- [ ] Retrospective, PR

**Dependencies:** none (manifest + docs only). Follow-on EPIC phases add platform agents/skills/validators.

---

## Success Criteria

```
Given a developer installs sdlc-team-ios
When they list its agents
Then they see only iOS-relevant agents (apple-hig-architect), not web/backend/data specialists
```

```
Given a cross-platform team installs both sdlc-team-ios and sdlc-team-android
When they list installed agents
Then mobile-architect and mobile-ux-architect appear once (via sdlc-team-mobile), not duplicated
```

```
Given sdlc-team-fullstack after the split
When its agents are listed
Then it contains the 9 web agents and none of the 4 mobile agents; version is 2.0.0
```

```
Given the repository after the change
When check-broken-references.py and the catalog builder run
Then references are clean and AGENT-INDEX/CATALOG reflect the new plugin structure
```

```
Given a user runs /sdlc-core:setup-team and selects an "iOS app" or "Android app" project type
When recommendations are produced
Then the platform plugin + sdlc-team-mobile are recommended as a unit
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Qualified-name callers break (`sdlc-team-fullstack:mobile-architect`) | Med | Med | Breaking bump → 2.0.0 + migration note; agents still reachable by bare name and via new plugins |
| Missed cross-reference site (docs citing "13 agents"/fullstack mobile) | Med | Low | Grep the enumerated sites; run `check-broken-references.py`; regenerate catalog |
| Agent registered twice (overlap) | Low | Med | Clean cut (no dual-mapping); explicit verification step |
| setup-team tests assume old fullstack contents | Low | Med | Run `test_setup_smart_e2e.py` + registry tests; update fixtures if needed |

## Open Questions

- [ ] Swift/Kotlin language experts placement (symmetric `sdlc-lang-*` vs bundled) — deferred to a later EPIC phase (#217 D2); out of scope here.
- [ ] Should `ux-ui-architect` eventually move to `sdlc-team-common` as a cross-cutting design agent? Out of scope; noted for future.

## Security & Privacy

N/A. Manifest/packaging and documentation changes only. No code execution, no auth changes, no data
handling, no secrets.

---

**Retrospective**: `retrospectives/217-mobile-plugin-split.md` (link after implementation)

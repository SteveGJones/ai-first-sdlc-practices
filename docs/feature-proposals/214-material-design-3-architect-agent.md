# Feature Proposal: material-design-3-architect Agent

**Proposal Number:** 214
**Status:** Draft
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-07-22
**Target Branch:** `feature/material-design-3-agent`
**GitHub Issue:** #214

---

## Motivation

The plugin family ships exactly one UX agent — `ux-ui-architect` in `sdlc-team-fullstack`
(source: `agents/core/ux-ui-architect.md`). By design it is **design-system-agnostic**: it is an
expert in design tokens, WCAG 2.2/3.0 accessibility, user research, information architecture, and
design-to-development handoff, but it is not grounded in any specific design language.

Google **Material Design 3 (M3 / "Material You")** appears in that agent exactly once — as one of
four options ("Material Design, Ant Design, Carbon, Polaris") in a build-vs-buy table. The agent
therefore knows M3 *exists* but carries none of its substance:

- No **HCT color space**, dynamic color, tonal palettes, or Material You theming
- No **three-tier token taxonomy** (`md.ref.*` → `md.sys.*` → `md.comp.*`)
- No **M3 component specs** (the button family, FAB variants, navigation bar/rail/drawer, chips, etc.)
- No **adaptive layout** model (window size classes, canonical layouts)
- No **tonal elevation / surface container** roles (M3 replaced M2's shadow-overlay elevation)
- No **motion system** (emphasized easing, duration tokens, transition patterns, Expressive springs)
- No **implementation guidance** for Jetpack Compose Material3, Material Web (`@material/web`), or
  Flutter Material 3, and no `material-color-utilities` / Material Theme Builder tooling knowledge
- Nothing on **Material 3 Expressive** (the 2025 evolution announced at Google I/O 2025)

**Who is affected:** any team building an Android, Flutter, or Material-Web product on M3 has no
specialist to consult. They get generic design-system advice that never speaks M3's vocabulary,
tokens, or platform APIs.

**What happens if we don't fix it:** the UX offering stays a single generalist. Users on the most
widely-deployed design system in the world (every modern Android surface) get no first-class support,
and the "dogfood the specialists we ship" premise of this repo has a visible gap.

## User Stories

- As an **Android/Compose developer**, I want an agent that speaks M3 tokens and Compose Material3
  APIs so I can theme with `dynamicColor` / `ColorScheme.fromSeed` correctly instead of guessing.
- As a **design-system lead adopting M3**, I want authoritative guidance on the HCT color pipeline,
  the `md.sys.color.*` role set, and tonal elevation so my tokens match the spec.
- As a **Flutter or Material-Web engineer**, I want implementation-accurate advice (including that
  `@material/web` is in maintenance mode) so I don't build on a dead-end path.
- As a **product team**, I want to know when M3 is the right choice vs. when it fights my brand or an
  iOS Human Interface Guidelines target, and how M3 Expressive changes the trade-off.
- As the **`ux-ui-architect` agent**, I want to hand off M3-specific questions to a specialist rather
  than answer them shallowly, and receive framework-agnostic UX/accessibility strategy back.

## Proposed Solution

### High-Level Approach

Add a new specialist agent — **`material-design-3-architect`** — to the `sdlc-team-fullstack`
plugin, grounded in authoritative M3 knowledge gathered by deep research against the official
sources (m3.material.io, developer.android.com, github.com/material-components, flutter.dev). It sits
*alongside* `ux-ui-architect`, not replacing it: the generalist owns framework-agnostic UX,
accessibility strategy, and research; the M3 specialist owns Material Design 3 fidelity, tokens,
components, and platform implementation. The two cross-reference each other.

We chose this over grounding the existing agent in M3 (Alternative 1) because M3 is a large, opinionated,
platform-specific body of knowledge; folding it into the generalist would bloat that agent and blur its
deliberately neutral stance. A dedicated specialist keeps each agent focused and lets `ux-ui-architect`
stay design-system-agnostic while still routing M3 work to an expert.

### Technical Approach

1. **Deep-research reference set** — four research files (already produced on this branch under the
   session scratchpad, to be distilled into a durable `research/` artifact) covering:
   (a) foundations & tokens, (b) components & adaptive layout, (c) motion / accessibility / content,
   (d) implementation & tooling / migration. These are the source material for the agent's content and
   are retained so the agent's claims are traceable.

2. **New source agent** `agents/core/material-design-3-architect.md`, following the established agent
   file contract used by `ux-ui-architect.md`:
   - YAML frontmatter: `name`, `description`, `model` (sonnet), `tools`, `examples` (≥2, with
     `<example>`/`<commentary>` blocks — required by CI compliance), `color`, and
     `first_party_alternatives` (e.g. Material Theme Builder, Figma MCP).
   - Body: core competencies (color/HCT & dynamic color, token architecture, typography, shape,
     elevation/surfaces, components, adaptive layout, motion, accessibility, platform implementation,
     M2→M3 migration, M3 Expressive), a decision/process section, "when to use / when NOT to use",
     and collaboration handoffs (to `ux-ui-architect`, `frontend-architect`, `mobile-architect`,
     language experts).

3. **Wiring**:
   - Add the source path to `release-mapping.yaml` under `sdlc-team-fullstack:` agents.
   - Add a row to `AGENT-INDEX.md` and bump its agent count / plugin description.
   - Add cross-reference from `ux-ui-architect.md` (the M3 build-vs-buy line points to the specialist).
   - Bump `plugins/sdlc-team-fullstack/plugin.json` version and note in CHANGELOG/CLAUDE.md plugin table.

4. **Validation**: run `check-technical-debt`, the agent-format/CI compliance checks, broken-reference
   check, and `local-validation.py --pre-push`. Release the plugin via `/sdlc-core:release-plugin`.

### Alternatives Considered

1. **Ground the existing `ux-ui-architect` in M3** (add an M3 competency section). *Pros:* one agent,
   cheapest. *Cons:* couples a deliberately neutral generalist to one opinionated framework; bloats the
   agent; makes it awkward to also add e.g. an Apple-HIG or Fluent specialist later. **Not chosen.**
2. **Ingest M3 into the knowledge base only** (`kb-ingest` m3.material.io) so any agent can query it.
   *Pros:* dogfoods the KB; keeps agents generic. *Cons:* no *specialist voice* — nobody owns M3
   fidelity, quality of advice depends on the caller knowing what to ask. **Complementary, not a
   substitute** — we may still ingest the research into a KB later, but the ask here is an agent.
3. **Do both a specialist agent + KB ingest.** Deferred: ship the agent first (this proposal); a
   follow-up can ingest the research artifact into a project KB if demand exists.

---

## Implementation Plan

### Phase 1: Research (foundation)
- [x] [P] Research M3 foundations & tokens (color/HCT, 3-tier tokens, typography, shape, elevation, states)
- [x] [P] Research M3 components & adaptive layout (component catalog, window size classes, canonical layouts, Expressive)
- [x] [P] Research M3 motion, accessibility & content design
- [x] [P] Research M3 implementation, tooling & M2→M3 migration
- [ ] Distil the four research files into a durable, cited `research/material-design-3/` reference

### Phase 2: Agent authoring
- [ ] Write `agents/core/material-design-3-architect.md` (frontmatter + body) grounded in the research
- [ ] Self-review against `ux-ui-architect.md` for structural parity and CI-required fields
- [ ] Add cross-reference from `ux-ui-architect.md` to the new specialist

### Phase 3: Wiring, validation & release
- [ ] Add source path to `release-mapping.yaml` (sdlc-team-fullstack)
- [ ] Update `AGENT-INDEX.md` (row + counts) and the CLAUDE.md plugin table note
- [ ] Bump `plugins/sdlc-team-fullstack/plugin.json` version
- [ ] Run validators (technical-debt, agent-format/CI compliance, broken-references, `--pre-push`)
- [ ] `/sdlc-core:release-plugin` to package the agent into the plugin
- [ ] Complete retrospective, open PR

**Dependencies:** Web access for research (done via research agents); no new runtime libraries.

---

## Success Criteria

```
Given a user asks "how do I generate an M3 color scheme from a brand seed colour and apply it in Compose"
When the material-design-3-architect agent is invoked
Then it explains the HCT/tonal-palette pipeline, names the md.sys.color roles, and gives correct
     Compose Material3 guidance (ColorScheme.fromSeed / dynamicColor), citing M3 concepts accurately
```

```
Given the agent file agents/core/material-design-3-architect.md
When CI agent-format / compliance validation runs
Then it passes (valid frontmatter, >=2 examples with commentary, no technical debt, no broken references)
```

```
Given a user asks ux-ui-architect an M3-specific question
When ux-ui-architect responds
Then it routes M3-specific fidelity questions to material-design-3-architect rather than answering shallowly
```

```
Given /sdlc-core:release-plugin runs for sdlc-team-fullstack
When packaging completes
Then material-design-3-architect.md appears in plugins/sdlc-team-fullstack/agents/ and the plugin version is bumped
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Research captures stale/incorrect M3 details (spec evolves; Expressive is new) | Med | Med | Ground every claim in fetched official URLs; retain research files with a Sources list; date the reference |
| Agent overlaps/conflicts with `ux-ui-architect` | Med | Low | Explicit scope split + bidirectional cross-references; M3 = fidelity/impl, generalist = strategy/a11y |
| `@material/web` maintenance-mode / API churn dates the agent | Med | Low | State platform status explicitly and date-stamp; favour durable concepts (tokens, color) over volatile APIs |
| Agent-format CI failures (missing examples/fields) | Low | Med | Mirror `ux-ui-architect.md` structure; run compliance validators before PR |

## Open Questions

- [ ] Should the distilled research also be `kb-ingest`ed into a project KB now, or deferred to a follow-up? (Proposal defers.)
- [ ] Agent naming: `material-design-3-architect` vs `material-design-architect` (version-neutral)? (Proposal: keep the `-3` to signal M3-specific grounding; revisit if M4 ever lands.)
- [ ] Model tier — `sonnet` (matches `ux-ui-architect`) vs a lighter tier? (Proposal: `sonnet` for parity.)

## Security & Privacy

N/A. The deliverable is a static agent definition (markdown) plus a research reference. No code
execution, no authentication/authorization changes, no data collection, no secrets. Research was
gathered from public official documentation.

---

**Retrospective**: `retrospectives/214-material-design-3-architect-agent.md` (link after implementation)

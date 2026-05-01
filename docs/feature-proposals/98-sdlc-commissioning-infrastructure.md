# Feature Proposal: SDLC Commissioning Infrastructure (Phase C of EPIC #178)

**Proposal Number:** 98
**Status:** In Progress (Phase C of EPIC #178)
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-07; **adapted into EPIC #178** 2026-04-27
**Target Branch:** `feature/sdlc-programme-assured-bundles` (was `feature/sdlc-commissioning`; absorbed into EPIC #178)
**EPIC:** #97 (Multi-Option Commissioned SDLC) → **#178 (Joint Programme + Assured delivery)** absorbs this as Phase C
**Sub-feature:** #98 (sub-feature 1 of 7 in EPIC #97; Phase C in EPIC #178)

> **Note on absorption:** This proposal was originally authored for `feature/sdlc-commissioning` as a standalone sub-feature of EPIC #97. EPIC #178 absorbs it as Phase C because Programme (#103, Phase D) and Assured (#104, Phase E) both depend on commissioning infrastructure being in place. Splitting C out would force coordination overhead with no benefit. The proposal's substance is preserved; sections updated for EPIC #178 context are flagged "[Phase C update]".

---

## Executive Summary

Build the foundational infrastructure that lets the framework commission a fixed SDLC bundle per project. This is the first sub-feature of EPIC #97 and every other sub-feature in the EPIC depends on it. Until this exists, no option-specific bundle (Single-team, Solo, Programme, Assured) can be installed coherently.

The work delivers four things: a **bundle contract** (what an option plugin contains and how it's packaged), a **commission skill** (the user-facing entry point that picks an option and installs the bundle), a **schema extension** to `.sdlc/team-config.json` recording the commissioning decision, and **sdlc-enforcer awareness** of that record so the enforcer adapts behaviour to the chosen option.

This sub-feature builds the *machinery*. Sub-features 2 and 3 build the actual Single-team and Solo bundles that the machinery installs.

---

## Motivation

### Problem statement

Today the framework supports one shape of SDLC (`sdlc-core` plus team and language plugins layered on top) and applies its rules with progressive strictness through the Prototype/Production/Enterprise levels. This works for typical product teams but is silently universal — a side project gets the same Article 3 (six architecture documents required at Production+) as a payments system, and the framework offers no way to say "this project has a different shape, not just a different stringency dial."

The research at `research/sdlc/Agentic_SDLC_Options.md` describes four distinct SDLCs (Solo, Single-team, Programme, Assured) at different points on the scale, assurance, and regulatory spectrum. EPIC #97 commits the framework to supporting all four as commissionable bundles, with each bundle being a complete distribution (constitution + agents + skills + templates + validators) rather than a runtime-filtered slice of a master document.

This sub-feature builds the machinery that makes commissioning possible. Without it, none of the option bundles can be installed.

### Why machinery first

We deliberately separate building the machinery from building the bundles. There are two reasons.

First, we don't yet know the right shape for an option bundle until we have to install one. Designing the bundle contract in the abstract risks getting it wrong; designing it with one concrete bundle (Single-team, sub-feature 2) and then validating against a second (Solo, sub-feature 3) gives us two data points before anything is locked in.

Second, by validating the machinery against the existing framework state (extracting Single-team from current `sdlc-core`), we get to prove the design works on something we know is correct *before* we use it for anything new. If the machinery can't faithfully repackage what we already have, it isn't ready to package anything else.

### User stories

- As the framework author, I want a clear contract for what an option bundle contains so that adding new options is a structured exercise, not an ad-hoc one
- As a user starting a new project, I want the framework to ask me what kind of project I'm building and install an SDLC that fits, rather than assuming one shape
- As a user with an existing project, I want the framework to keep working unchanged when commissioning lands — defaulting silently to single-team if I haven't explicitly chosen
- As the sdlc-enforcer agent, I want to read which option a project commissioned so I can apply the right rules without guessing
- As a future contributor adding the Programme or Assured bundle, I want the bundle contract to already exist so I don't have to invent the packaging shape mid-implementation

---

## Proposed Solution

Four deliverables, all on `feature/sdlc-programme-assured-bundles`. **[Phase C update]**

### 1. Bundle contract

A documented specification of what an option plugin contains and how it is packaged. Includes:

- **Manifest schema** — option name, version, supported levels, dependencies on other plugins, list of agents/skills/templates/validators provided
- **File layout** — where the constitution lives inside the bundle, where agents live, where skills live, where templates live, how validators are configured
- **Plugin packaging shape** — each option becomes its own plugin alongside `sdlc-team-*` and `sdlc-lang-*` plugins. This is the architecture (a) → (b) path we agreed: sdlc-core stays as Single-team default for now (architecture a); the refactor toward architecture (b) happens during sub-feature 3 when Solo lands and forces the universal/specific split
- **Versioning rules** — how an option bundle declares its version, how a project records which version it commissioned, how migration handles version drift
- **[Phase C update] Decomposition support fields** — the bundle contract must support per-bundle declarations of decomposition primitives, granularity defaults, and validator opt-out semantics. Specifically, the contract reserves schema room for the four Phase E gaps surfaced by EPIC #178 Phase B's architect review:
  - **`source-paths` / `derived-paths` distinction** in any per-module `paths` field, so plugin-dir mirrors don't trigger false positives in `module-bound-check` validators
  - **`known-violation` declarations** for accepted runtime data-flow cycles (e.g., framework-research↔kb-skills coupling)
  - **`anaemic-context-detection: suppressed`** opt-out semantics for catalog-shaped modules
  - **ID format choice** — positional (`P1.SP2.M3.REQ-007`) vs named (`aisp.kb.kbsk.REQ-NNN`) — declared by the bundle contract once, applied uniformly within commissioning. *[Decision call: this proposal recommends positional, sortable, and terser; named convenience can layer above as user-facing aliases.]*

The bundle contract is documented in `docs/architecture/option-bundle-contract.md`.

**Phase C does NOT implement validator semantics for these fields** — that's Phase E (Assured bundle implementation). Phase C's job is to ensure the bundle contract has *room* for these fields so Phase E doesn't have to retrofit the contract.

### 2. Commission skill

A new skill at `skills/commission/SKILL.md`, invoked as `/sdlc-core:commission` (path may change once sub-feature 3 refactors sdlc-core toward architecture b). The skill:

1. **Detects context** — reads the current directory, looks for existing `.sdlc/team-config.json`, identifies whether this is a fresh project or a re-commissioning
2. **Asks structured questions** — derived from the research's decision matrix:
   - Team size (1-2 / 3-10 / 11-50 / 50+)
   - Blast radius of a defect (low / moderate / high / severe)
   - Regulatory burden (none / low / moderate / high)
   - Specification maturity (emergent / mixed / contract-first / formal)
   - Time-to-market pressure (very high / high / moderate / low)
3. **Recommends an option × level** with rationale, derived from the research's quick selection heuristic and decision matrix
4. **Lets the user override** the recommendation. If the override is unusual (e.g., Solo + Enterprise, Programme + Prototype), the skill warns but never blocks. The user knows things the framework doesn't.
5. **Installs the chosen bundle**:
   - Writes the option's constitution into the project (replaces or creates `CONSTITUTION.md`)
   - Installs option-specific agents into `.claude/agents/` (or wherever the project-scoped agent install lands once #81 is resolved)
   - Installs option-specific skills into `.claude/skills/`
   - Writes templates for the option's required artifacts (feature proposal template, retrospective template, architecture document templates if applicable, RACI template if applicable)
   - Configures validators (which checks run at `--syntax`, `--quick`, `--pre-push` for this option)
   - Records the decision in `.sdlc/team-config.json`

### 3. `.sdlc/team-config.json` schema extension

Four new fields:

| Field | Type | Description |
|---|---|---|
| `sdlc_option` | string | One of `solo` / `single-team` / `programme` / `assured` |
| `sdlc_level` | string | One of `prototype` / `production` / `enterprise` |
| `commissioned_at` | ISO 8601 timestamp | When the commissioning decision was made |
| `commissioned_by` | string | Human or agent identifier (e.g., username, "claude-agent") |
| `option_bundle_version` | string | The version of the option bundle that was installed |

Plus a `commissioning_history` array (initially with one entry, the original commissioning) that future migrations append to.

**[Phase C update] Reserved fields for Phase E** — the schema reserves (but does not yet require) two additional fields populated by Assured bundle commissioning:

| Field | Type | Description |
|---|---|---|
| `decomposition` | object \| null | Pointer to `library/_decomposition.md` (or path to declarative `programs` block); populated only by Assured bundle commissioning |
| `commissioning_options` | object | Per-bundle configuration knobs (e.g., `regulatory_context`, `change_impact_gate_enabled`, `id_format`) |

Reserving these now means Phase E doesn't have to bump schema version when Assured ships — the schema knows about them; Phase C just doesn't populate them.

The schema is documented in `CLAUDE-CORE.md`.

### 4. sdlc-enforcer awareness of the commissioning record

The `sdlc-enforcer` agent reads `.sdlc/team-config.json` on every invocation. If `sdlc_option` is set, it looks up the corresponding option's constitution and applies its rules. If `sdlc_option` is unset (existing project that predates commissioning), it silently defaults to `single-team` and continues working exactly as today. Existing users see no change.

The enforcer also records the option in its compliance reports so contributors can see at a glance which option a project was commissioned under.

---

## Success Criteria

- [ ] Bundle contract documented in `docs/architecture/option-bundle-contract.md` with complete manifest schema and file layout, including reserved schema fields for Phase E (source/derived paths, known-violations, anaemic-context-detection, ID format)
- [ ] Plugin packaging shape decided and documented (each option = its own plugin; how this composes with team-* and lang-* plugins)
- [ ] `commission` skill exists at `skills/commission/SKILL.md`, wired into `release-mapping.yaml`
- [ ] `commission` skill asks the structured questions from the research's decision matrix and derives a defensible recommendation
- [ ] `commission` skill respects user override of the recommendation, with a warning for unusual combinations and no blocking
- [ ] `commission` skill installs a bundle into a project (initially validated against a mock bundle; Phase D will validate against the real Programme bundle)
- [ ] `.sdlc/team-config.json` schema includes the five new fields (`sdlc_option`, `sdlc_level`, `commissioned_at`, `commissioned_by`, `option_bundle_version`) plus `commissioning_history` array, plus reserved Phase E fields (`decomposition`, `commissioning_options`)
- [ ] CLAUDE-CORE.md documents the new schema and the commissioning concept
- [ ] `sdlc-enforcer` reads the commissioning record and adapts behaviour based on `sdlc_option`
- [ ] Existing projects (no `sdlc_option` set) continue to work unchanged — silently default to `single-team`
- [ ] Unit tests for the commissioning skill against a mock bundle
- [ ] **[Phase C update] Containerised review** of the bundle contract spec via `sdlc-workflows` (architect + security review) before merge — the contract is load-bearing for Phase D and Phase E
- [ ] Pre-push validation passes
- [ ] Phase C retrospective committed
- [ ] Feature proposal merged

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bundle contract designed wrong, locks in a shape that doesn't fit Solo / Programme / Assured | Whole EPIC stalls | Validate against the existing Single-team state in sub-feature 2 *before* designing Solo. Refactor the contract during sub-feature 3 if Solo reveals problems. The contract is not frozen until the EPIC closes. |
| Existing projects break when commissioning lands | Trust loss with current users | Default `sdlc_option` to `single-team` silently when unset. No project should have to do anything to keep working. Test on real existing projects (this repo is one) before merge. |
| `commission` skill becomes a 20-question wizard that nobody runs | Adoption failure | Aim for under 5 questions. Strong defaults. Quick selection heuristic from the research as a fast path. Solo path should be near-zero questions. |
| Commissioning skill assumes plugin install permissions we don't have because of #81 | Skill installs nothing | Ship with the user-scope fallback: skill writes to `.sdlc/` and provides a manifest the user can install with `/plugin install`. Document the fallback clearly. |
| `sdlc_option` becomes a runtime toggle by accident, defeating the architectural commitment | Conceptual drift | Code review must enforce: `sdlc_option` is read at every enforcer invocation but only *written* by the commission and migrate skills. No other code path may write it. |
| Contract over-specifies and rejects bundles that don't fit a narrow shape | Programme and Assured can't be packaged | Bundle contract is permissive on what's optional. Required fields stay minimal. Add fields only when sub-features 2 and 3 prove they're needed. |

---

## Out of scope

- **Building the Single-team bundle.** Sub-feature 2 (#99).
- **Building the Solo bundle and refactoring sdlc-core toward architecture (b).** Sub-feature 3 (#100).
- **Migration between options.** Sub-feature 4 (#101).
- **Documentation polish, decision guides, self-knowledge inventory.** Sub-feature 5 (#102).
- **Programme and Assured bundles.** Sub-features 6 (#103) and 7 (#104), separate branches.
- **Resolving #81** (project-scoped plugin install). The commissioning skill will work around it with the user-scope fallback. #81 is its own platform-level issue.

---

## Changes Made

| Action | File |
|--------|------|
| Create | `docs/architecture/option-bundle-contract.md` |
| Create | `skills/commission/SKILL.md` |
| Create | `skills/commission/templates/` (mock bundle for testing) |
| Modify | `release-mapping.yaml` (add commission skill to sdlc-core.skills) |
| Modify | `CLAUDE-CORE.md` (document `sdlc_option` schema and commissioning concept) |
| Modify | `agents/core/sdlc-enforcer.md` (read commissioning record, adapt behaviour) |
| Create | `tests/unit/test_commission_skill.py` (or equivalent test harness) |
| Create | `docs/feature-proposals/98-sdlc-commissioning-infrastructure.md` (this file) |

---

## References

- EPIC: #97 — Multi-Option Commissioned SDLC
- Sub-features that depend on this: #99, #100, #101, #102 (this branch); #103, #104 (future branches)
- Research: `research/sdlc/Agentic_SDLC_Options.md` — four-option practitioner guide
- Research: `research/sdlc/Phase5_Final_Report.md` — academic synthesis with rubric and rankings
- Related platform issue: #81 — project-scoped plugin install (commissioning works around this)

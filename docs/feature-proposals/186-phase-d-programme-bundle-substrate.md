# Feature Proposal: Phase D — Programme Bundle (Method 1 Substrate)

**Proposal Number:** 186
**Status:** In Progress (Phase D of EPIC #178)
**Author:** Steve Jones (commissioning), Claude (drafting)
**Created:** 2026-04-27
**Target Branch:** `feature/sdlc-programme-assured-bundles`
**EPIC:** #178 (Joint Programme + Assured bundle delivery)
**Sub-feature:** #186 (Phase D of #178; replaces previous-phase tracking via #103)

---

## Summary

Build the **Programme bundle Method 1 substrate** — a complete, commissionable `sdlc-programme` plugin v0.1.0 implementing the formal waterfall phase-gate model from METHODS.md §3. Ships as the second-of-four bundle plugins envisioned in EPIC #97, after Single-team (default, currently `sdlc-core`) and before Solo (#100) and Assured (#104, Phase E of #178).

**Scope discipline**: this is the *substrate* — phase artefacts, phase-gate validators, mandatory cross-phase review skill, traceability-export skill, programme constitution. The full SAFe-Lite multi-team Programme bundle scope (4 multi-team agents, 6 multi-team skills, contract registry, audit consolidation) remains as #103's future v1.0 territory, deferred until a real multi-team collaborator is available.

The substrate is a meaningful test target on its own: any team commissioning to Programme gets phase-gate enforcement and traceability-export immediately. Multi-team SAFe-Lite features layer on top when ready.

## Sub-features

None. Phase D is one cohesive substrate; sub-tasks are managed via the implementation plan, not separate issues.

## Motivation

### Why now

Phase C (#98) shipped commissioning infrastructure: `sdlc-core:commission`, the bundle contract, the BundleManifest parser, the recorder, the installer, the sdlc-enforcer adaptation. Without a real bundle to install, that infrastructure is unproven. The sample-bundle fixture (Phase C task 4) is a mock, not a real bundle.

Programme is the natural first real bundle because:

- Method 1 (phase gates) is *less* exotic than Method 2 (traceability + decomposition + KB-for-code), so getting Programme right first lets us validate the bundle infrastructure with the simpler shape before Method 2 stresses it.
- Programme exercises every commissioning code path: bundle-specific constitution, bundle-specific agents, bundle-specific skills, bundle-specific templates, bundle-specific validator config. Single-team would too — but Programme has clearer differentiation (phase-gate enforcement) so its commissioning behaviour is more visibly distinct from "no bundle at all".
- A real Phase D ship makes Phase E (Assured bundle) plan-writing concrete: Phase E layers traceability + decomposition on top of Method 1's phase-gate substrate.

### User stories

- As a programme-of-work team, I commission to Programme + production level and get formal phase gates: I cannot push code that doesn't cite a test-spec section, the test-spec must cite both requirements-spec and design-spec, and broken cross-phase references block.
- As a programme reviewer, I get mandatory `phase-review` for design-spec and test-spec phases — human-in-the-loop verification that the cross-phase links are *meaningful* and not just *syntactically present*.
- As an audit-preparing team, I run `traceability-export csv` or `traceability-export markdown` and get an audit-friendly matrix of REQ ↔ DES ↔ TEST ↔ CODE.
- As a future Assured bundle author (Phase E), I inherit Method 1's substrate and layer traceability + decomposition + KB-for-code on top — without re-implementing phase gates.

## Proposed Solution

A new plugin at `plugins/sdlc-programme/` containing:

### 1. Plugin manifest and metadata

- `manifest.yaml` — bundle manifest per Phase C contract (`docs/architecture/option-bundle-contract.md`):
  - `schema_version: 1`, `name: programme`, `version: 0.1.0`
  - `supported_levels: [production, enterprise]` (Programme is overkill for prototype)
  - `description: "Multi-team programme SDLC with formal waterfall phase gates"`
  - `constitution: CONSTITUTION.md`
  - Lists agents, skills, templates, validators
- `.claude-plugin/plugin.json` — standard plugin metadata
- `README.md` — bundle overview, audience, level guidance, how to commission

### 2. Programme constitution

`CONSTITUTION.md` at bundle root. Overlays Single-team's foundations (universal articles 1-11) with Programme-specific articles:

- **Article 12 (Programme-specific)**: phase-gate compliance — every feature has requirements-spec → design-spec → test-spec → code in `docs/specs/<feature>/`
- **Article 13 (Programme-specific)**: cross-phase reference integrity — citations between phase artefacts must resolve to existing IDs; broken references block commit
- **Article 14 (Programme-specific)**: mandatory `phase-review` for design-spec and test-spec; human-signed review records committed alongside reviewed artefact

### 3. Phase artefact templates (in `plugins/sdlc-programme/templates/`)

- `requirements-spec.md` — feature-id, motivation, requirements list with stable IDs, success criteria
- `design-spec.md` — must reference requirements-spec by feature-id, design-elements with stable IDs, satisfies-table (DES → REQ), out-of-scope
- `test-spec.md` — must reference requirements-spec + design-spec by feature-id, test-cases with stable IDs, satisfies-table (TEST → REQ + DES), expected results

### 4. Phase gate validators (in `plugins/sdlc-programme/scripts/`)

Python helpers, mirror Phase C `commission/` pattern. Each validator:

- `requirements_gate.py` — checks requirements-spec exists, has all mandatory sections, has feature-id
- `design_gate.py` — checks design-spec exists, has mandatory sections, references requirements-spec by feature-id, all cited REQ-IDs exist in registry
- `test_gate.py` — checks test-spec exists, has mandatory sections, references both prior phases, all cited REQ + DES IDs exist
- `code_gate.py` — checks code commits cite a test-spec section + the cited section ID exists

Plus a shared `spec_parser.py` extracting IDs and references from phase markdown — so the gate validators don't each reimplement parsing.

### 5. Skills shipped

In `plugins/sdlc-programme/skills/`:

- `commission-programme/SKILL.md` — bundle-specific commissioning entry point (installs Programme bundle and writes record). Behaviour: same as `/sdlc-core:commission --option programme` but with the rationale + recommendation flow tailored to Programme audience.
- `phase-init/SKILL.md` — `phase-init <phase> <feature-id>` instantiates phase artefact from template; mkdirs `docs/specs/<feature>/`
- `phase-gate/SKILL.md` — `phase-gate <phase> <feature-id>` runs the gate validator; reports pass/fail with broken-reference details
- `phase-review/SKILL.md` — `phase-review <phase> <feature-id>` dispatches structured review of the artefact against its cited prior artefacts (uses `sdlc-team-common:solution-architect` for design-spec; `sdlc-team-fullstack:test-architect` or similar for test-spec)
- `traceability-export/SKILL.md` — `traceability-export <format> <feature-id>` produces audit-friendly matrices (csv, markdown)

### 6. Plugin packaging

- `release-mapping.yaml` — new top-level key `sdlc-programme:` with skills, agents (none in v0.1.0), templates, scripts
- `.claude-plugin/marketplace.json` — new entry for `sdlc-programme` v0.1.0
- `pyproject.toml` at plugin root — Python package for the validator scripts

### 7. Tests

- `tests/test_programme_validators.py` — phase gate behaviour (broken refs blocked; valid refs pass)
- `tests/test_programme_skills_integration.py` — end-to-end skill flow (phase-init creates from template; phase-gate runs validator; commission-programme writes record)
- `tests/fixtures/programme/` — minimal feature directory with each phase artefact

## Success Criteria

- [ ] `sdlc-programme` plugin v0.1.0 packaged and installable via marketplace.json
- [ ] All 4 phase gate validators implemented and unit-tested
- [ ] All 5 skills shipped (commission-programme, phase-init, phase-gate, phase-review, traceability-export) at root + plugin mirror
- [ ] Phase artefact templates copied into a project on commission (verified via test against the sample-bundle fixture from Phase C)
- [ ] `phase-review` is mandatory for design-spec and test-spec phases (skill enforces; not optional)
- [ ] `traceability-export csv` and `traceability-export markdown` formats supported
- [ ] Plugin packaging passes 13/13 (12 existing + sdlc-programme)
- [ ] Pre-push validation passes
- [ ] **Containerised architect review of the Programme bundle's design** before close (per `feedback_containerised_review_for_design_artefacts.md`)
- [ ] Phase D retrospective committed
- [ ] Issue #186 closed

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Programme constitution overlap with sdlc-core articles causes conflict on commissioning | Confused state on commissioned project | Programme constitution explicitly extends, doesn't replace; commission skill writes only the Programme constitution; sdlc-enforcer reads the bundle's constitution path from the manifest |
| Cross-phase reference parsing is brittle (markdown variations, ID format drift) | Validators flag false positives or miss real broken refs | Shared `spec_parser.py` with strict regex on REQ-/DES-/TEST- ID format; comprehensive unit tests including edge cases (codeblocks, frontmatter, nested headings) |
| Phase D scope creeps into multi-team Programme features | Branch never closes | Strict scope discipline: anything multi-team-specific is #103 territory and is rejected at PR review time |
| `phase-review` skill quality depends on which architect agent is dispatched | Inconsistent reviews across teams | `phase-review` SKILL.md specifies: design-spec → `sdlc-team-common:solution-architect`; test-spec → relies on `superpowers:requesting-code-review` pattern (test-architect agent doesn't exist as named) |

## Out of scope

- **Full SAFe-Lite multi-team Programme bundle** — remains #103's future v1.0 territory
- **Method 2 features** (traceability registry, decomposition, KB-for-code) — Phase E (Assured bundle) territory
- **New specialist agents** beyond what's already in the family — Programme uses existing agents (solution-architect, test-architect-equivalent via requesting-code-review, sdlc-enforcer with Phase C's commissioning awareness)
- **Migration from Single-team to Programme** — sub-feature #101's territory
- **Single-team bundle (#99) and Solo bundle (#100)** — separate sub-features of EPIC #97

## Dependencies

- Phase C (#98) commissioning infrastructure ✅ shipped on this branch
- Phase A (#179) design spec ✅
- Phase B (#180) decomposition spike ✅
- Bundle contract (`docs/architecture/option-bundle-contract.md`) ✅ refined via Phase C task 10 containerised review

## Implementation plan

Phase D plan to be authored via `superpowers:writing-plans` skill, saved to `docs/superpowers/plans/2026-04-27-phase-d-programme-bundle-substrate.md`. Expected ~12-15 tasks following the same TDD pattern as Phase C.

Each task ships its own commit with proof-of-completion artefact. Phase D retrospective consolidates at completion.

## Closing the phase

When all Success Criteria are checked, mark issue #186 closed and reference the commit SHAs. Phase E (#104, Assured bundle) becomes the next phase.

## References

- Parent EPIC: #178 (Joint Programme + Assured)
- Tracking issue: #186 (Phase D substrate; this proposal)
- Larger future scope: #103 (full SAFe-Lite Programme bundle)
- Method 1 design: `research/sdlc-bundles/METHODS.md` §3
- Phase D-E design spec: `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md`
- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Phase C closure: `retrospectives/98-phase-c-commissioning-infrastructure.md`
- Branch model precedent: EPIC #164 (PR #177)
- Containerised review pattern: `memory/feedback_containerised_review_for_design_artefacts.md`

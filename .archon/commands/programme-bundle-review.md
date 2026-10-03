# Programme Bundle Review

## Your Role

You are a senior solution architect reviewing the Programme bundle (`plugins/sdlc-programme/`) — the Method 1 phase-gate substrate from EPIC #178 Phase D. Phase E (Assured bundle) layers on top of this; getting Programme right matters.

You operate in a fresh container with SDLC plugins installed. Use the `sdlc-team-common:solution-architect` agent (via the Agent tool with `subagent_type="sdlc-team-common:solution-architect"`) for the architectural review — this command file briefs the agent and captures their output as your structured review.

## What you're reviewing

Primary input: `plugins/sdlc-programme/` (the entire bundle).

Walk these files specifically:

- `plugins/sdlc-programme/manifest.yaml` — bundle manifest
- `plugins/sdlc-programme/CONSTITUTION.md` — Programme constitution (Articles 12-14)
- `plugins/sdlc-programme/templates/{requirements-spec,design-spec,test-spec}.md` — phase artefact templates
- `plugins/sdlc-programme/scripts/programme/spec_parser.py` — ID extraction
- `plugins/sdlc-programme/scripts/programme/gates.py` — 4 phase-gate validators
- `plugins/sdlc-programme/scripts/programme/traceability.py` — REQ↔DES↔TEST matrix
- `plugins/sdlc-programme/skills/{commission-programme,phase-init,phase-gate,phase-review,traceability-export}/SKILL.md` — 5 skills
- `plugins/sdlc-programme/README.md` — bundle overview

## Required context

Read these adjacent documents before the review:

- `docs/architecture/option-bundle-contract.md` — bundle contract (Phase C deliverable). The Programme bundle MUST conform to this.
- `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md` — Phase D scope spec
- `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §3 — Method 1 design
- `research/sdlc-bundles/METHODS.md` §3 — Method 1 design summary
- `tests/fixtures/programme/feature-sample/` — minimal feature fixture used by gate tests
- `tests/test_programme_*.py` — 27 tests covering the bundle
- The Phase B containerised review at `research/sdlc-bundles/dogfood-workflows/architect-review-spike-output.md` and Phase C task 10 review at `research/sdlc-bundles/dogfood-workflows/bundle-contract-review-output.md` for review-style precedents

You may walk the existing 12-plugin family (`plugins/sdlc-knowledge-base/`, `plugins/sdlc-workflows/`, `plugins/sdlc-core/`) to compare conventions.

## What to do

Dispatch the `sdlc-team-common:solution-architect` agent with the prompt below. The agent should answer 5 review questions, each with a verdict label.

### Prompt to dispatch

```
You are conducting an INDEPENDENT critical review of the Programme bundle
at plugins/sdlc-programme/ — Phase D deliverable of EPIC #178.

Phase E (Assured bundle) layers on top of this Method 1 substrate;
getting Programme right matters.

Required reading first:
- docs/architecture/option-bundle-contract.md (Phase C contract)
- docs/feature-proposals/186-phase-d-programme-bundle-substrate.md (Phase D scope)
- research/sdlc-bundles/METHODS.md §3 (Method 1 design)
- plugins/sdlc-programme/ (the bundle itself)
- tests/test_programme_*.py (27 tests)

You may walk plugins/sdlc-knowledge-base/, plugins/sdlc-core/,
plugins/sdlc-workflows/ to compare conventions.

Answer these 5 questions, in order, each with a verdict (AGREE /
AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK):

1. **Constitution overlay soundness**: Articles 12-14 in
   plugins/sdlc-programme/CONSTITUTION.md extend the universal constitution
   (CONSTITUTION.md at repo root, articles 1-11). Are the new articles
   well-bounded, internally consistent with articles 1-11, and free of
   obvious gaps? Specifically: does Article 12 (phase-gate compliance) leave
   ambiguity about what "incomplete" means? Does Article 14 (mandatory
   phase-review) specify what makes a review record valid?

2. **Phase artefact templates fitness**: do the three templates at
   plugins/sdlc-programme/templates/ produce artefacts that the gates can
   actually validate? Specifically: when phase-init substitutes <feature-id>,
   does the resulting requirements-spec.md have a feature-id line in the
   right format for spec_parser to recognise? Does the design-spec template's
   **satisfies:** line use REQ-IDs that exist? Are there template structures
   the gates would need to special-case?

3. **Gate validator robustness**: do gates.py's 4 validators catch the
   kinds of broken-reference issue regulated-industry teams would care about?
   Specifically: does design_gate handle a design-spec where every DES
   declares satisfies but one of them references a REQ that doesn't exist?
   Does test_gate handle satisfies lines like "REQ-X-001, REQ-X-002 via
   DES-X-001, DES-X-002"? Does code_gate accept multiple # implements:
   annotations in the same code text? Where might they false-positive
   (block valid markdown that has REQ-IDs in code blocks or quoted text)?

4. **Phase-review skill realism**: phase-review/SKILL.md dispatches
   sdlc-team-common:solution-architect for design phase and
   sdlc-team-fullstack:backend-architect for test phase. Are these the right
   architectural choices? What's missing if the project doesn't have those
   agents installed (e.g., a project that doesn't install sdlc-team-fullstack
   plugin)? Should the skill have a fallback?

5. **Bundle layout vs Phase C contract**: does the actual Programme bundle
   layout match what docs/architecture/option-bundle-contract.md specifies?
   In particular:
   - Does manifest.yaml include the required fields (schema_version, name,
     version, supported_levels, description, constitution)?
   - Does the file layout match? (Plugin contract was updated in Phase C
     task 10 to drop a `validators/` directory it had originally; verify
     Programme doesn't have one either.)
   - Does the constitution: <path> field in manifest.yaml correctly point
     at CONSTITUTION.md?
   - Are any reserved Phase E fields (decomposition_support, id_format,
     paths_split_supported, known_violations_field, anaemic_context_opt_out)
     correctly NOT set (since Programme is Method 1, not Method 2)?

Then provide a SUMMARY paragraph stating whether the Programme bundle is
good enough to ship as v0.1.0 AND whether Phase E (Assured bundle) can build
on top of it without retrofit, or whether Phase D needs revision before
either.

End your review by writing the verbatim review (5 verdicts + summary) to:
research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md

Do NOT propose alternative bundles. Do NOT modify the bundle. Do NOT
dispatch other agents. Read-only review; output is a markdown file.
```

## Done criteria

The workflow node is done when:
- The agent has been dispatched
- The agent's verbatim response is written to `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md`
- The agent returned 5 verdict labels (one per question) plus a summary paragraph
- The agent stated explicit go/no-go on whether the bundle ships as v0.1.0 AND whether Phase E can build on top

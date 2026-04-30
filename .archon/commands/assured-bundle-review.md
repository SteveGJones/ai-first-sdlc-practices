# Assured Bundle Review

## Your Role

You are a senior solution architect reviewing the Assured bundle (`plugins/sdlc-assured/`) — the Method 2 regulated-industry substrate from EPIC #178 Phase E. This bundle layers on the Phase D Programme substrate. Phase F (real dogfood) layers on this; getting Assured right matters.

You operate in a fresh container with SDLC plugins installed. Use the `sdlc-team-common:solution-architect` agent (via the Agent tool with `subagent_type="sdlc-team-common:solution-architect"`) for the architectural review.

## What you're reviewing

Primary input: `plugins/sdlc-assured/` (the entire bundle).

Walk these files specifically:

- `plugins/sdlc-assured/manifest.yaml`
- `plugins/sdlc-assured/CONSTITUTION.md` — Articles 15-17
- `plugins/sdlc-assured/templates/{programs.yaml, visibility-rules.md, change-impact.md, requirements-spec-assured.md, design-spec-assured.md, test-spec-assured.md}`
- `plugins/sdlc-assured/scripts/assured/{ids.py, traceability_validators.py, decomposition.py, code_index.py, render.py, export.py}`
- `plugins/sdlc-assured/skills/*/SKILL.md` — 8 skills
- `plugins/sdlc-assured/README.md`

## Required context

- `docs/architecture/option-bundle-contract.md` — bundle contract (Phase C)
- `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §4 — Method 2 design
- `research/sdlc-bundles/METHODS.md` §4 — Method 2 summary
- `tests/fixtures/assured/feature-sample/` — minimal feature fixture
- `tests/test_assured_*.py` — unit and integration tests
- The Phase D containerised review at `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md` for review-style precedent

## What to do

Dispatch the `sdlc-team-common:solution-architect` agent with the prompt below.

### Prompt to dispatch

```
You are conducting an INDEPENDENT critical review of the Assured bundle
at plugins/sdlc-assured/ — Phase E deliverable of EPIC #178.

Phase F (real dogfood on EPIC #142) layers on this substrate; getting
Assured right matters.

Required reading first:
- docs/architecture/option-bundle-contract.md (Phase C contract)
- docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md §4 (Method 2 design)
- research/sdlc-bundles/METHODS.md §4
- plugins/sdlc-assured/ (the bundle itself)
- tests/test_assured_*.py

You may walk plugins/sdlc-programme/, plugins/sdlc-knowledge-base/,
plugins/sdlc-core/ to compare conventions.

Answer these 6 questions, in order, each with a verdict (AGREE /
AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK):

1. **Constitution overlay soundness (Articles 15-17)**: do the new
   articles extend articles 1-14 cleanly? Are there gaps between what
   the constitution promises and what the validators actually
   enforce?

2. **ID system fitness**: does the positional namespace ID format
   (`P1.SP2.M3.REQ-007`) coexist cleanly with the flat form
   (`REQ-feature-NNN`)? Does `remap_ids` actually preserve traceability
   under decomposition refactoring? What edge cases worry you?

3. **Traceability validator coverage**: do the 4 mandatory + 1 optional
   validators catch the broken-reference cases regulated-industry
   teams care about? Specifically: forward link integrity (DES with
   no satisfies, TEST with no satisfies), backward coverage (REQ
   with no DES, DES with no TEST), idempotency, annotation format.

4. **Decomposition validator coverage**: do the 5 module-bound
   validators correctly model DDD bounded contexts + Bazel
   visibility-rule discipline? Specifically: anaemic-context
   detection (does the implementation actually catch scattered
   logic?), granularity match (warns vs blocks correctly?),
   visibility rule advisory vs strict.

5. **KB integration realism**: does the `SYNTHESISE-ACROSS-SPEC-TYPES`
   mode actually compose with the existing `synthesis-librarian`
   without breaking the existing modes? Does the `_code-index.md`
   shelf-shape match what the `research-librarian` queries?

6. **Bundle layout vs Phase C contract**: does the actual Assured
   bundle layout match what docs/architecture/option-bundle-contract.md
   specifies? Are reserved Phase E fields (decomposition_support,
   id_format, paths_split_supported, known_violations_field,
   anaemic_context_opt_out) used correctly?

Then provide a SUMMARY paragraph stating whether the Assured bundle is
good enough to ship as v0.1.0 AND whether Phase F (real dogfood) can
proceed without retrofit, or whether Phase E needs revision before
either.

End your review by writing the verbatim review (6 verdicts + summary) to:
research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md

Do NOT propose alternative bundles. Do NOT modify the bundle. Do NOT
dispatch other agents. Read-only review; output is a markdown file.
```

## Done criteria

- The agent has been dispatched
- The agent's verbatim response is written to `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`
- The agent returned 6 verdict labels (one per question) plus a summary paragraph
- The agent stated explicit go/no-go on whether the bundle ships as v0.1.0 AND whether Phase F can proceed

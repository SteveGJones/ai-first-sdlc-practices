# Bundle Contract Review

## Your Role

You are a senior solution architect reviewing the bundle contract specification for the AI-First SDLC framework. The contract is `docs/architecture/option-bundle-contract.md` — the authoritative spec for what an option bundle contains, how it's packaged, and what schema fields it must support.

You operate in a fresh container with SDLC plugins installed. Use the `sdlc-team-common:solution-architect` agent (via the Agent tool with `subagent_type="sdlc-team-common:solution-architect"`) for the architectural review — this command file briefs the agent and captures their output as your structured review.

The contract is **load-bearing**: Phase D (#103, Programme bundle) and Phase E (#104, Assured bundle) will both build bundles against this contract. Schema mistakes here propagate. Your review must be rigorous.

## What you're reviewing

Primary input: `docs/architecture/option-bundle-contract.md` (in the worktree).

Read the WHOLE document before reviewing. It has these sections:

- Title + metadata (Version, Status, Authoritative for)
- "What a bundle is" — defines what a bundle contains
- "File layout" — directory tree
- "Manifest schema" — required + optional fields table
- "Reserved Phase E fields" — 5 capability flags
- "Versioning rules" — semver semantics
- "Reserved schema for `.sdlc/team-config.json`" — required + reserved fields
- "Validator configuration" — YAML example with bundle-defined identifier semantics
- "Backward compatibility" — uncommissioned project default
- "What Phase C does NOT cover" — out-of-scope

## Required context

Read these adjacent documents before the review:

- `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` — design spec the contract serves
- `research/sdlc-bundles/METHODS.md` — Method 1 / Method 2 design that drives bundle requirements
- `research/sdlc-bundles/decomposition-spike.md` — Phase B output with 4 schema gaps the contract reserves
- `library/regulatory-traceability-baseline.md` — regulatory rigour the Assured bundle must support
- `library/decomposition-ddd-bazel.md` — decomposition primitive the Assured bundle must accommodate

You may walk the repo (using Bash `ls` / `find`) to understand the existing 12-plugin family pattern.

## What to do

Dispatch the `sdlc-team-common:solution-architect` agent with the prompt below. The agent should answer the 5 review questions, with verdict labels per question.

### Prompt to dispatch

```
You are conducting an INDEPENDENT critical review of the option bundle contract at:
docs/architecture/option-bundle-contract.md

This contract is load-bearing: Phase D (Programme bundle) and Phase E (Assured
bundle) will both build bundles against it. Schema mistakes propagate.

Required reading first: METHODS.md, decomposition-spike.md (Phase B output),
library/regulatory-traceability-baseline.md, library/decomposition-ddd-bazel.md.

Answer these 5 questions, in order, each with a verdict (AGREE /
AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK):

1. **Manifest schema permissiveness**: is the manifest schema permissive enough
   for Programme + Assured + future Solo / Single-team without retrofit? Are
   there fields a bundle author would need that aren't here? Are there fields
   here that no bundle would actually use?

2. **Phase E reserved fields adequacy**: the contract reserves 5 manifest
   capability flags (decomposition_support, id_format, paths_split_supported,
   known_violations_field, anaemic_context_opt_out) and 2 team-config.json
   fields (decomposition, commissioning_options). Per the Phase B spike's 4
   schema gaps + 1 ID-format gap, are these reservations sufficient? Are any
   schema gaps still uncovered? Are any reserved fields visibly going to be
   wrong shape when Phase E lands?

3. **File layout vs existing 12-plugin family**: the contract specifies a
   bundle plugin layout (`plugins/sdlc-<option>/` with manifest.yaml,
   CONSTITUTION.md, agents/, skills/, templates/, validators/). Walk
   `plugins/sdlc-knowledge-base/` and `plugins/sdlc-workflows/` (existing
   plugins) and check: does the contract's layout match how plugins are
   actually packaged in this repo? Where does it diverge surprisingly? In
   particular, where does `validators/` live in existing plugins (if anywhere)?

4. **Backward compatibility tightness**: the contract claims projects without
   sdlc_option default to single-team behaviour. Read the actual sdlc-enforcer
   adaptation in `agents/core/sdlc-enforcer.md` (modified in Phase C task 9).
   Does the agent prompt actually implement the default-to-single-team path,
   or is the contract overstating what was built? If a project has a
   .sdlc/team-config.json with no sdlc_option (e.g., just `team_name` and
   `created`), what does the enforcer do?

5. **Regulated-industry adoption gap**: a regulated-industry team adopting the
   Assured bundle (Phase E, future) will read this contract to know what their
   bundle's manifest must declare. Walk through their viewpoint — what's
   missing? Specifically:
   - Can they declare per-validator audit-evidence requirements
     (e.g., "this validator's output is the regulator-facing artefact")?
   - Can they declare bundle-level certification scope (e.g., "this bundle
     supports DO-178C Level B but not Level A")?
   - Can they declare validator tool-qualification levels (TCL per ISO 26262-8)?

   Or are these all out-of-scope for the framework itself, properly handled
   by per-bundle README files and external certification documentation?

Then provide a SUMMARY paragraph stating whether the contract is good enough
to feed Phase D plan-writing (roadmap, skill inventory, commissioning flow)
AND Phase E plan-writing (validator design, schema implementation), or
whether it needs revision before either.

End your review by writing the verbatim review (8 verdicts + summary) to:
research/sdlc-bundles/dogfood-workflows/bundle-contract-review-output.md

Do NOT propose alternative contracts. Do NOT modify the contract. Do NOT
dispatch other agents. Read-only review; output is text only.
```

## Done criteria

The workflow node is done when:
- The agent has been dispatched
- The agent's verbatim response is written to `research/sdlc-bundles/dogfood-workflows/bundle-contract-review-output.md`
- The agent returned at least 5 verdict labels (one per question) plus a summary paragraph
- The agent stated explicit go/no-go on whether the contract feeds Phases D and E without revision

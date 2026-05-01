---
title: "Programme + Assured Bundle Research Campaign — Overview and Definitive Decisions"
domain: sdlc-bundles, programme-bundle, assured-bundle, research-campaign, method-1, method-2, epic-97
status: active
tags: [research-campaign, programme-bundle, assured-bundle, method-1, method-2, epic-97, sub-feature-103, sub-feature-104, design-decisions, scope-update]
source: research/sdlc-bundles/synthesis/overall-scope-update.md
cross_references:
  - research/sdlc-bundles/CLOSEOUT.md
  - research/sdlc-bundles/PLAN.md
  - research/sdlc-bundles/METHODS.md
  - library/regulatory-traceability-baseline.md
  - library/decomposition-ddd-bazel.md
  - library/decomposition-failure-modes.md
  - library/sphinx-needs-adoption-boundary.md
  - library/doors-cautionary-tale.md
  - library/change-impact-pattern.md
  - library/granularity-declaration.md
  - library/tool-neutral-traceability.md
---

## Key Question

What did the three-stage research campaign for EPIC #97 sub-features #103 (Programme bundle / Method 1) and #104 (Assured bundle / Method 2) determine, and what are the headline design decisions that flow from it?

## Core Findings

1. **The research campaign produced 61,061 words across 14 artefacts** (PLAN, METHODS, 3 stage-2 prompts, 2 stage-3 prompts, 3 raw research outputs at 8K-10K words each, 3 per-line syntheses, 1 verification report, 1 overall synthesis, 1 closeout). Citation discipline was strong throughout: 651 inline citations across 78 bibliography entries; CRAAP credibility notes preserved; counter-arguments cited per spec. — research/sdlc-bundles/CLOSEOUT.md
2. **Three independent research lines converged with no material conflicts.** Lines 1 (Regulatory Traceability), 2 (Decomposition Patterns), 3 (ALM Tools Landscape) all reinforced each other on the headline decisions: bidirectional traceability, DDD + Bazel decomposition, static link validation, annotation-driven code linking, file-based storage, and change-impact annotation. The absence of conflict is itself a strong quality signal. — overall-scope-update.md §2
3. **Decomposition primitive — final call**: Domain-Driven Design bounded contexts as the primary unit, layered with Bazel's visibility-rule discipline, with optional hexagonal architecture for within-module structure. The explicit failure mode designed against is anaemic contexts (business logic scattered across modules). — overall-scope-update.md §5; library/decomposition-ddd-bazel.md
4. **Traceability rigour calibration — final call**: bidirectional link integrity at requirement-level granularity (default; per-module declarable looser), with static build-time validation and annotation-driven code linking. Satisfies the strictest standard (ISO 26262) and is compatible with DO-178C, IEC 62304, IEC 61508, and FDA 21 CFR Part 820 simultaneously. — overall-scope-update.md §6; library/regulatory-traceability-baseline.md
5. **sphinx-needs adoption boundary**: adopt declarative need-type schema, static build-time link validation, file-based Git-native storage, annotation-driven code parsing, modular per-module rendering. Reject flat identifier scheme, absent decomposition primitive, dynamic computed-field functions, multiprocessing-for-large-projects, rich-text support. — overall-scope-update.md §7; library/sphinx-needs-adoption-boundary.md
6. **Method 1 scope changes (4 total)**: clarify phase-gate blocking on broken links; add `traceability-export` skill (audit format support); strengthen model-selection guidance (phase-review needs reasoning model, phase-gate is mechanical); make `phase-review` mandatory for design-spec and test-spec phases. — overall-scope-update.md §3
7. **Method 2 scope changes (10 total)**: enrich decomposition with DDD + Bazel concepts; support decomposition refactoring without ID invalidation; strengthen code-annotation validation + add `code-annotate` skill; optional hexagonal-structure tagging; `change-impact-annotate` skill + optional gate; `traceability-export` with standard-specific formats (DO-178C RTM, IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF); per-module granularity validation; commissioning guidance subsection (defer decomposition); strengthen out-of-scope (certification disclaimer + ReqIF one-way export); organisational metadata stays optional in YAML, never schema-baked. — overall-scope-update.md §4
8. **Recommended next action**: (a) update METHODS.md / design spec with these scope changes, then proceed to writing-plans. No follow-up research blocks plan-writing; six open questions are implementation details resolvable via prototype experiments during Stage 4. — overall-scope-update.md §10

## Frameworks Reviewed

| Research line | Decision informed | Headline finding | Confidence |
|---|---|---|---|
| **Line 1 — Regulatory traceability** | Assured bundle's traceability rigour | Bidirectional + per-module granularity + structured change-impact | HIGH |
| **Line 2 — Decomposition patterns** | Method 2 decomposition primitive | DDD + Bazel + optional hexagonal; design against anaemic contexts | HIGH |
| **Line 3 — ALM tools landscape** | Patterns to adopt vs avoid | Adopt sphinx-needs patterns; reject DOORS lock-in shape | HIGH |
| **Cross-line synthesis** | Integrated scope decisions | 8 cross-line agreements; 0 conflicts; 14 scope changes | VERY HIGH |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Cross-line conflicts | 0 of 8 cross-line agreements | overall-scope-update.md §2 | Strong quality signal |
| Total scope changes | 14 (4 Method 1 + 10 Method 2) | overall-scope-update.md §3, §4 | Manageable scope for one EPIC |
| New skills introduced | ~6 (Method 1: phase-* | Method 2: req-add, kb-codeindex, traceability-render, change-impact-annotate, traceability-export, code-annotate, module-bound-check) | Implementation budget guidance |
| Open questions blocking plan-writing | 0 | overall-scope-update.md §9 | Proceed to Stage 4 |

## Design Principles

1. **The research campaign's reference discipline becomes framework discipline.** Every design decision in METHODS.md should cite back to research findings. The framework should value the citations it teaches.
2. **No claim is incorporated without source.** Every Method 1 / Method 2 scope change traces back to a specific research finding via [Line N: Section X entry Y] form.
3. **Confidence is propagated, not laundered.** A LOW-confidence research finding becomes a LOW-confidence design decision. The synthesis chain preserves uncertainty.
4. **Cross-line agreement is a higher bar than single-line claims.** Eight cross-line agreements with 0 conflicts is the campaign's strongest finding; we lean on those most heavily.
5. **Implementation details deferred to Stage 4 are explicitly listed.** Six open questions (visualisation format, soft decomposition mode, index regeneration cycle, etc.) are handled at plan-writing time via prototype experiments.

## Key References

1. `research/sdlc-bundles/CLOSEOUT.md` — research campaign closeout with Definition-of-Done verification and headline decisions
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` — master scope-update document (5,104 words, 10 sections, all decisions)
3. `research/sdlc-bundles/synthesis/01-traceability-synthesis.md` — Line 1 synthesis (5,238 words)
4. `research/sdlc-bundles/synthesis/02-decomposition-synthesis.md` — Line 2 synthesis (4,703 words)
5. `research/sdlc-bundles/synthesis/03-alm-synthesis.md` — Line 3 synthesis (3,244 words)
6. `research/sdlc-bundles/outputs/01-traceability-standards/output-1.md` — raw research (8,268 words)
7. `research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md` — raw research (10,252 words)
8. `research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md` — raw research (8,823 words)
9. `research/sdlc-bundles/PLAN.md` and `research/sdlc-bundles/METHODS.md` — Stage 1 deliverables

## Programme Relevance

**This entry is the navigation hub for EPIC #97 sub-feature #103/#104 work.** When future agents work on the Programme or Assured bundles:

- Start by querying this entry to understand campaign output
- Drill into the topic-specific library entries (regulatory-traceability-baseline, decomposition-ddd-bazel, etc.) for design guidance on specific subsystems
- Reference the synthesis docs for traceable claims
- Reference the raw outputs only when defending a specific claim against pushback

**Stage 4 (plan-writing) entry point**: the 14 scope changes in overall-scope-update.md §3 and §4 become the input to `superpowers:writing-plans`. Each scope change is a unit of plan work; many of them combine into single phase-of-work commits.

**Out-of-scope clarifications** the framework now defends explicitly:
- AST-level code intelligence (no call graphs, no semantic analysis)
- IDE integration (filesystem-first)
- Full ALM database (no relational schema, no stored procedures)
- Industry certification itself (substrate that helps reach assurance, not certification)
- Decomposition suggestion (framework enforces declared decomposition, doesn't suggest where edges go)
- Bidirectional ReqIF sync (one-way export only, plugin-shaped if anyone wants it)

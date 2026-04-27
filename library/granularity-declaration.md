---
title: "Granularity Declaration — Per-Module, Declarative (Method 2)"
domain: sdlc-bundles, traceability, granularity, decomposition, regulated-industries, method-2, assured
status: active
tags: [granularity, do-178c, iec-62304, iso-26262, asil, sil, level, per-module-declaration, method-2, assured-bundle, epic-97]
source: research/sdlc-bundles/synthesis/01-traceability-synthesis.md
cross_references:
  - library/regulatory-traceability-baseline.md
  - library/decomposition-ddd-bazel.md
---

## Key Question

How should the Assured bundle support the varied traceability granularity that different standards demand (object-code in DO-178C Level A, function-level in ISO 26262, file-level in DO-178C Level D), without baking in any one standard's choice?

## Core Findings

1. **Granularity scales by standard and risk class.** DO-178C scales by Level: Level A requires traceability to individual object-code instructions; Level B/C requires source-code statement or function level; Level D permits file-level or higher [1]. IEC 62304 scales by Class (Class C demands function-level) [7]. ISO 26262 mandates requirement-level for safety reqs across all ASIL levels; implementation granularity scales with ASIL [9]. IEC 61508 scales by SIL [12]. FDA does not prescribe. — synthesis/01 §2 finding "Granularity of Traceability"
2. **The framework cannot infer granularity; it must be declared.** Each module in the decomposition registry declares its granularity target — `granularity: [requirement | function | module]`. Default is `requirement` (finest). Modules may declare `function` or `module` if appropriate to their risk or complexity. — synthesis/01 §3 Claim 3
3. **Validators enforce declared granularity.** If module M1 declares `granularity: requirement`, all code in M1 must carry REQ-level annotations; if M2 declares `granularity: function`, function-level annotations suffice. The validator warns when actual granularity exceeds declared target (underspecified links). — synthesis/01 §3 Claim 3; §5 Scope Change 2
4. **Cross-line triangulation confirms the pattern.** Line 1 documents that standards support per-system granularity; Line 2 recommends per-module declaration in the decomposition registry; Line 3 documents that sphinx-needs has no per-module granularity concept (gap to fill). All three converge: granularity declaration is innovation Method 2 adds. — synthesis/overall §1 Cross-Line Agreement 7 (HIGH confidence)
5. **Mixed-granularity projects are supported by design.** A single project may have M1 at requirement-level and M2 at function-level; validators are per-module. No additional research needed; the design supports mixing. — synthesis/01 §6 Open Question 4
6. **Object-code granularity (DO-178C Level A) is opt-in, not default.** The Assured bundle defaults to requirement-level and function-level (satisfying ISO 26262 and IEC 61508). Projects can declare finer granularity per module if their ASIL/SIL and domain require it. The framework does not enforce object-code granularity globally; that would exceed all other standards' requirements. — synthesis/01 §4 fourth rejection

## Frameworks Reviewed

| Standard | Granularity scaling | Method 2 declared value |
|---|---|---|
| **DO-178C Level A** | Object-code instructions | Module declares `granularity: object-code` (advanced) |
| **DO-178C Level B/C** | Source-code statement / function | `granularity: function` |
| **DO-178C Level D** | File or higher | `granularity: module` |
| **IEC 62304 Class A** | Natural function separation | `granularity: function` or `module` |
| **IEC 62304 Class C** | Function-level | `granularity: function` |
| **ISO 26262 ASIL A-D** | Requirement-level for safety | `granularity: requirement` (default) |
| **IEC 61508 SIL 1-4** | SIL-scaled, no minimum | Module declares per SIL |
| **FDA 21 CFR Part 820** | Not prescribed | Module declares per project |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Default granularity | `requirement` (finest in default) | synthesis/01 §3 Claim 3 | Set if not specified |
| Granularity field per module | Required in `programs` block | synthesis/01 §5 Scope Change 2 | Validator checks presence |
| Granularity match (declared vs actual) | 100% | synthesis/01 §3 Claim 3 | Warn if actual is coarser; never block (might be progressive) |
| Object-code granularity | Module-level opt-in only | synthesis/01 §4 fourth rejection | Never default global |

## Design Principles

1. **Declared, never inferred.** The team declares granularity per module; the framework does not guess based on directory structure or commit patterns.
2. **Per-module, never global.** A project's modules may have different granularities. The framework validates each independently.
3. **The default is conservative.** `requirement` is the finest granularity that all major standards accept. Teams declare looser granularity (`function`, `module`) explicitly when justified.
4. **Validators warn on underspecification, not over-specification.** If declared is `function` but actual is `module`, that's a warning (the team isn't meeting its own target). If declared is `module` but actual is `function`, that's fine (over-specification is harmless).
5. **No object-code default.** DO-178C Level A is exotic; making it default would break every non-aerospace project.

## Key References

1. `research/sdlc-bundles/synthesis/01-traceability-synthesis.md` §3 Claim 3, §5 Scope Change 2
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` §1 Agreement 7
3. RTCA DO-178C Section 6.3.1 — traceability obligations by Level. output-1.md bibliography [1]
4. IEC 62304 — software-class granularity. output-1.md [7]
5. ISO 26262 Part 6 — requirement-level mandate across ASIL levels. output-1.md [9]
6. IEC 61508 — SIL-scaled granularity. output-1.md [12]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)**:
- METHODS.md Section 4 "Decomposition" subsection extended with `granularity: [requirement | function | module]` field per module
- Validator added to `module-bound-check`: traceability links match declared granularity (warn on mismatch, never block — teams may be progressively tightening)
- Commissioning script asks regulatory context and proposes granularity per module:
  - DO-178C Level A → `granularity: function` (per-module opt-in to `object-code`)
  - DO-178C Level B/C → `granularity: function`
  - IEC 62304 Class C → `granularity: function`
  - ISO 26262 → `granularity: requirement`
  - Else → `granularity: requirement` (conservative default)
- Documentation example shows mixed-granularity project (e.g., M1 safety-critical at function-level, M2 admin tooling at module-level) — typical real-world shape

**Stage-4 plan-writing decision**: should the validator detect "actual granularity exceeds declared" via inspection of code annotations, or via a separate granularity-coverage report? Either works; pick at plan time based on integration with `kb-codeindex`.

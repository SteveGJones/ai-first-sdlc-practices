---
title: "Regulatory Traceability Baseline — Bidirectional Across Five Standards (Method 2 Calibration)"
domain: sdlc-bundles, traceability, regulated-industries, do-178c, iec-62304, iso-26262, iec-61508, fda, method-2, assured
status: active
tags: [bidirectional-traceability, do-178c, iec-62304, iso-26262, iec-61508, fda-21-cfr-820, regulated-industry, assurance-grade, method-2, assured-bundle, epic-97]
source: research/sdlc-bundles/synthesis/01-traceability-synthesis.md
cross_references:
  - research/sdlc-bundles/synthesis/overall-scope-update.md
  - research/sdlc-bundles/outputs/01-traceability-standards/output-1.md
  - research/sdlc-bundles/METHODS.md
  - library/tool-neutral-traceability.md
  - library/change-impact-pattern.md
---

## Key Question

What is the floor of traceability obligations imposed by the major safety-critical software standards, and how should the Assured bundle calibrate its native rigour to satisfy them all simultaneously without exceeding any?

## Core Findings

1. **Bidirectional traceability is the regulatory baseline across three of five standards.** DO-178C [1], ISO 26262:2018 [9], and IEC 61508-3 [12] mandate bidirectionality (forward REQ→DES→TEST→CODE plus backward indices). IEC 62304 permits unidirectionality [6][7] but practitioners implement bidirectionality for audit assurance anyway. FDA 21 CFR Part 820 emphasises forward traceability with backward confirmation via Design History File [14][15][16]. — synthesis/01 §2 finding "Cross-standard convergence", §3 Claim 1
2. **Bidirectional support exceeds no standard's requirement.** Implementing full bidirectionality in the Assured bundle's defaults satisfies all five standards simultaneously. Projects that need only IEC 62304 Class A can relax validators via commissioning configuration if their regulatory context permits. — synthesis/01 §4 Claim "Bidirectional optional"
3. **Granularity scales by standard.** DO-178C scales by Level (Level A = object-code; Level D = file-level) [1]. IEC 62304 scales by Class (Class C demands function-level) [7]. ISO 26262 mandates requirement-level for safety reqs across all ASIL levels [9]. IEC 61508 scales by SIL [12]. FDA does not prescribe granularity. **Implication**: granularity declaration must be per-module and declarative — the framework cannot infer it from the project structure. — synthesis/01 §3 Claim 3
4. **Change-impact assessment is universally required but variably gated.** IEC 62304 Clause 8.2.4 [8] and FDA 21 CFR §820.30(i) [16] treat change-impact as a mandatory blocking gate. DO-178C and ISO 26262 require it in configuration-management and design-change procedures but less explicitly as a blocker. IEC 61508 implies it through traceability-integrity. **Implication**: support structured annotation universally; offer optional gating validator for IEC 62304/FDA contexts. — synthesis/01 §3 Claims 2, 5
5. **All five standards are tool-neutral.** DO-178C [4], IEC 62304 [7], ISO 26262 [11], IEC 61508 [13], and FDA guidance [15] all specify objectives (what must be evidenced) but not means. Spreadsheet, database, commercial ALM, markdown — any form is acceptable provided evidence is producible and auditable. — synthesis/01 §3 Claim 4
6. **Regenerability is explicit in two standards.** ISO 26262 Part 8 Clause 11 and IEC 61508 [11][13] require traceability links to be reconstructible from primary artefacts (requirements, source code, test reports) without tool dependence. **Implication**: file-based markdown + Git satisfies this naturally; database-only tools (DOORS) do not. — synthesis/01 §3 Claim 4
7. **The framework promises substrate, not certification.** No standard claims an open-source framework certifies compliance; certification requires accredited authorities. The Assured bundle produces traceability records, decomposition declarations, change-impact records, phase gates, code annotations — substrate that helps reach assurance. It is not assurance and does not certify. — synthesis/01 §3 Claim 7

## Frameworks Reviewed

| Standard | Industry | Bidirectional? | Granularity floor | Change-impact gate? |
|---|---|---|---|---|
| **DO-178C** | Aerospace | Mandatory | Object-code (Level A) → file (Level D) | Implicit in CM plan |
| **IEC 62304** | Medical devices | Permitted unidirectional | Function (Class C) → natural (Class A) | **Mandatory blocking gate** |
| **ISO 26262** | Automotive | Mandatory across all ASIL | Requirement-level all ASIL; function-level ASIL B+ | Mandatory in design-change procedure |
| **IEC 61508** | Industrial / process control | Mandatory | SIL-scaled, no minimum prescribed | Implied via traceability integrity |
| **FDA 21 CFR Part 820** | US medical-device regulation | Forward + backward confirmation | Not prescribed | **Mandatory blocking gate (§820.30(i))** |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Forward link integrity | Every cited ID exists in registry | synthesis/01 §3 Claim 1 | Block on broken link |
| Backward coverage — REQ has DES | 100% | synthesis/01 §3 Claim 1 | Block on orphan REQ |
| Backward coverage — DES has TEST | 100% | synthesis/01 §3 Claim 1 | Block on orphan DES |
| Backward coverage — TEST has CODE | 100% | synthesis/01 §3 Claim 1 | Block on orphan TEST |
| Backward coverage — CODE has annotation | 100% | synthesis/01 §3 Claim 1 | Block on orphan CODE |
| Index regenerability | `kb-rebuild-indexes` is idempotent | synthesis/01 §3 Claim 4 | Auditor-verifiable |
| Index staleness threshold | 7 days (default; team-configurable) | synthesis/01 §3 Claim 4 | Warn (not block) |

## Design Principles

1. **The strictest common requirement is the default.** Assured bundle defaults to bidirectional traceability satisfying ISO 26262. Projects in less-strict contexts (IEC 62304 Class A) can relax via commissioning configuration.
2. **Granularity is declared per module, not globally.** A single project may have M1 at requirement-level and M2 at function-level; validators enforce each module's target independently.
3. **Tool-neutrality is preserved by markdown-first design.** Auditors regenerate indices from markdown source; tool choice is immaterial to traceability validity.
4. **Out-of-scope is documented, not implicit.** The Assured bundle's commissioning docs explicitly state "produces substrate, not certification" — this protects users from misunderstanding scope.
5. **Validators are syntactic, not semantic.** The framework checks links exist and are non-circular. It does not check whether a test actually exercises the requirement (semantic responsibility lives with humans in `phase-review`).

## Key References

1. `research/sdlc-bundles/synthesis/01-traceability-synthesis.md` — Stage 3 synthesis (5,238 words; 7-claim incorporation list)
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` Section 6 — final traceability rigour calibration
3. `research/sdlc-bundles/outputs/01-traceability-standards/output-1.md` — full research output (8,268 words, 22-entry bibliography)
4. RTCA DO-178C (2011), *Software Considerations in Airborne Systems and Equipment Certification*. output-1.md bibliography [1]
5. IEC 62304 (2015), *Medical device software — Software life cycle processes*. Bibliography [6][7][8]
6. ISO 26262:2018, Part 6 *Product development at the software level*, Part 8 *Supporting processes*. Bibliography [9][10][11]
7. IEC 61508 (2010), Part 3, Annex A.1. Bibliography [12]
8. FDA 21 CFR Part 820, *Quality System Regulation*, §820.30 Design Controls. Bibliography [14][15][16]
9. Tian et al. (2021) — peer-reviewed mapping study on traceability decay. Bibliography [17]
10. Cleland-Huang et al. (2003) — peer-reviewed work on granularity-cost scaling. Bibliography [21]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)**:
- The framework's bidirectional-traceability design is locked in by Core Finding 1 — implement validators per the Actionable Thresholds table
- Granularity declaration (Core Finding 3) is the deferred design call: per-module field `granularity: [requirement | function | module]` in the `programs` block
- Change-impact gating (Core Finding 4) is configurable per commissioning context — IEC 62304 / FDA / ISO 26262 contexts enable by default
- Regenerability (Core Finding 6) is preserved by `kb-rebuild-indexes` idempotence — make this an explicit design statement to fend off future "add a database" pressure
- The disclaimer (Core Finding 7) appears in commissioning docs and the framework README

**EPIC #97 sub-feature #103 (Programme bundle)**:
- Programme bundle does not need bidirectional-traceability validators — feature-scoped, not module-scoped
- Phase gates (req-spec → design-spec → test-spec → code) are the simpler analogue
- Forward references between phase artefacts are validated; backward indexing is unique to Method 2

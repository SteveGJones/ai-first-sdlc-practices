---
title: "Packaging vendor onboarding"
domain: packaging, semiconductor, OSAT
status: active
source: Industry data 2024
cross_references:
  - supplier-onboarding-procedures.md
---

## Key Question

What qualification process should govern OSAT packaging vendor onboarding for a new semiconductor programme?

## Core Findings

1. OSAT qualification cycle averages 9 months from initial engagement to full programme approval; first-pass yield acceptance threshold is 70%, full qualification requires sustained 90% yield over 60 days (industry data 2024).
2. Multi-site OSAT relationships require redundant tooling validation across sites; sole-source packaging risk carries a ~15% per-unit cost premium when factored across programme lifetime (industry analysis 2024).
3. Packaging-supplier technical transfer documentation requirements have increased significantly since 2022; OSATs now require structured design-rule compliance sign-off before accepting new device types.

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| OSAT qualification industry norms | Industry data 2024 | Varies significantly by package type (FC-BGA vs QFN vs CoWoS) |
| Multi-site redundancy modelling | Industry analysis 2024 | Sole-source premium is programme-specific |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Qualification cycle | 9 months | Industry 2024 | Below 6 months = quality-gate shortcuts suspected |
| First-pass yield acceptance | 70% | Industry 2024 | Below 60% = OSAT process review required |
| Full qualification yield | 90% over 60 days | Industry 2024 | Below 85% at end of 60 days = extend qualification |
| Sole-source risk premium | ~15% per-unit | Industry 2024 | Above 20% = dual-source qualification justified |

## Design Principles

- Start OSAT qualification before fab groundbreaking: 9-month cycle means packaging must be in qualification while fab is under construction
- Require multi-site capability validation from programme start; do not accept sole-source commitment as long-term arrangement
- Design-rule compliance documentation must be a programme input, not a post-design artefact

## Key References

1. OSAT qualification industry norms (2024)
2. Multi-site semiconductor packaging supply chain analysis (2024)

## Programme Relevance

The brazilian-fab packaging programme faces a specific geographic challenge: most tier-1 OSATs (ASE, Amkor, JCET) have limited Brazilian logistics infrastructure. The 9-month qualification timeline should be started no later than 18 months before planned first silicon, to allow for freight variability and customs clearance delays in the Brazilian import context. Sole-source packaging risk premium should be modelled at 18-20% (elevated from the 15% industry baseline) given the concentrated OSAT footprint relative to this geography.

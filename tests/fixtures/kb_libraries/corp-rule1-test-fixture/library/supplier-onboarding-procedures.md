---
title: "Supplier onboarding procedures"
domain: supplier, semiconductor, onboarding
status: active
source: Industry data 2024
cross_references:
  - packaging-vendor-onboarding.md
---

## Key Question

What qualification process should govern supplier onboarding for a new semiconductor programme?

## Core Findings

1. Supplier qualification cycle averages 9 months from initial engagement to full programme approval; first-pass yield acceptance threshold is 70%, full qualification requires sustained 90% yield over 60 days (industry data 2024).
2. Multi-site supplier relationships require redundant tooling validation across sites; sole-source risk carries a ~15% per-unit cost premium when factored across programme lifetime (industry analysis 2024).
3. Supplier technical transfer documentation requirements have increased significantly since 2022; vendors now require structured design-rule compliance sign-off before accepting new device types.

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| Supplier qualification industry norms | Industry data 2024 | Varies significantly by component type and tier |
| Multi-site redundancy modelling | Industry analysis 2024 | Sole-source premium is programme-specific |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Qualification cycle | 9 months | Industry 2024 | Below 6 months = quality-gate shortcuts suspected |
| First-pass yield acceptance | 70% | Industry 2024 | Below 60% = supplier process review required |
| Full qualification yield | 90% over 60 days | Industry 2024 | Below 85% at end of 60 days = extend qualification |
| Sole-source risk premium | ~15% per-unit | Industry 2024 | Above 20% = dual-source qualification justified |

## Design Principles

- Start supplier qualification before programme groundbreaking: 9-month cycle means suppliers must be in qualification while facility is under construction
- Require multi-site capability validation from programme start; do not accept sole-source commitment as long-term arrangement
- Design-rule compliance documentation must be a programme input, not a post-design artefact

## Key References

1. Supplier qualification industry norms (2024)
2. Multi-site semiconductor supply chain analysis (2024)

## Programme Relevance

Fab operators should start supplier qualification no later than 18 months before planned first silicon. Sole-source risk premium should be modelled at the 15% industry baseline as a starting point; operators with non-typical logistics profiles should adjust upward. Multi-site validation is the strongest mitigation for concentrated supplier risk, regardless of geography.

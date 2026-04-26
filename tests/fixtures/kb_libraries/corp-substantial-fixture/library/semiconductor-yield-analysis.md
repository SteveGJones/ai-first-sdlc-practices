---
title: "Semiconductor yield analysis"
domain: yield, semiconductor, fab-comparison
status: active
source: industry data + public earnings reports 2024
cross_references:
  - austin-fab-operations.md
  - nijmegen-fab-operations.md
---

## Key Question

What yield benchmarks apply across technology nodes, and how do fab-level operational factors influence yield in leading-edge versus mature node production?

## Core Findings

1. Industry yield benchmarks: 90%+ for mature 28nm production; 70-85% for leading-edge 3-5nm in first 12 months of volume production; below 65% in first 6 months is typical for new fab commissioning (industry data 2024)
2. Defect density is the primary yield driver at sub-5nm; particle contamination accounts for 45-55% of yield loss in Class 1 cleanroom environments (ITRS roadmap 2024)
3. Statistical Process Control (SPC) with six-sigma discipline reduces systematic yield loss by 30-40% vs. reactive-only defect management (SPC industry benchmarks 2023)
4. New fab commissioning consistently yields 15-25% below steady-state for the first 6-12 months; Nijmegen fab Q1 2024 data (152 wph vs 160 wph target) is consistent with this pattern

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| ITRS roadmap 2024 | Industry consensus | Aspirational targets; actual yields often lag |
| SPC industry benchmarks 2023 | Industry body | Aggregate across nodes; not fab-specific |
| Earnings report analysis (TSMC, Samsung) | Public data | Yield figures not directly disclosed; derived from utilisation + revenue |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Commissioning yield (3-5nm) | 65-70% | Industry 2024 | Below 60% triggers root-cause programme |
| Steady-state yield (3-5nm) | 80-85% | Industry 2024 | Below 75% at 18 months: process audit required |
| Mature node yield (28nm) | >90% | Industry 2024 | Below 88%: equipment or process drift |
| SPC implementation | Six-sigma | Industry benchmark | Reactive-only defect management costs 30-40% more yield |

## Design Principles

- Early SPC deployment: implement statistical process control in commissioning phase, not after yield problems appear
- Yield ramp expectations: plan 12-18 months of below-target yields in financial model; this is normal, not a failure signal
- Defect density tracking: instrument for particle contamination as primary yield metric from day one

## Key References

1. International Technology Roadmap for Semiconductors (ITRS) 2024 update
2. SPC industry benchmarks for semiconductor manufacturing (2023)
3. Nijmegen fab Q1 2024 production report (internal)

## Programme Relevance

The brazilian-fab yield model should use 65-70% as the commissioning target for first 6 months, ramping to 80% by month 18. This is consistent with both dutch-fab and austin-fab reference data. SPC tooling should be specified in the fab equipment list before groundbreaking; retrofitting SPC infrastructure post-commissioning is significantly more expensive. The Brazilian semiconductor context adds a workforce readiness dimension: SPC requires trained process engineers, and the technician pipeline (see austin-fab-operations.md university partnership model) should be scoped to include SPC competency.

---
title: "Tropical climate equipment derating"
domain: tropical-climate, semiconductor, fab
status: active
source: Industry analysis 2024
cross_references:
  - equipment-thermal-management.md
---

## Key Question

How should semiconductor equipment throughput be derated for tropical climate fab environments?

## Core Findings

1. Tool throughput must be derated 5-12% in tropical climate fabs to maintain stability margins; the derate range is driven by ambient RH (>70% RH) and temperature (>30°C ambient) interaction with process equipment thermal envelopes (industry analysis 2024).
2. Equipment cooling capacity must be sized at 1.4× temperate baseline for tropical-climate operation; under-sizing drives process drift and yield instability as ambient conditions vary seasonally.
3. HVAC redundancy requirements increase in tropical climates: N+2 chillers (vs N+1 in temperate fabs) is the industry standard to maintain RH control during monsoon-season peak loads.

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| Tropical fab climate modelling | Industry analysis 2024 | Limited sample of operating tropical fabs |
| HVAC redundancy standards | Equipment vendor specs 2024 | Vendor-specific cooling models |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Throughput derate | 5-12% | Industry 2024 | Above 12% = equipment resizing required |
| Cooling capacity multiplier | 1.4× temperate | Industry 2024 | Below 1.3× = RH instability risk |
| HVAC redundancy | N+2 chillers | Industry 2024 | N+1 insufficient for monsoon peak |

## Design Principles

- Size cooling infrastructure at 1.4× from the start; retrofitting is 2-3× more expensive than upfront sizing
- Instrument ambient RH and temperature at tool-level, not just fab-level, during commissioning
- Derate throughput targets in the financial model before fab construction; do not plan for temperate-equivalent throughput

## Key References

1. Industry analysis of tropical climate semiconductor fab operations (2024)
2. Equipment vendor cooling specifications for high-ambient environments (2024)

## Programme Relevance

The brazilian-fab sits in a tropical climate zone with ambient RH regularly exceeding 80% and temperatures above 32°C. The 5-12% throughput derate should be applied to all financial projections; using temperate-baseline throughput figures will overstate revenue in the ramp model. HVAC design should specify N+2 chillers from the start. The tropical-climate ambient RH interaction with EUV reticle stability requirements (RH <45%) creates a dual constraint that is more severe in this geography than in reference temperate fabs.

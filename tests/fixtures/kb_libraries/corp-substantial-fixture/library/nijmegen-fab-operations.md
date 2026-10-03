---
title: "Nijmegen fab operations"
domain: dutch-fab, semiconductor, fab-operations
status: active
source: internal engagement notes 2024
cross_references:
  - eindhoven-fab-cleanroom.md
  - dutch-supply-chain.md
  - euv-spec-asml-2024.md
---

## Key Question

How does the Nijmegen fab operate its EUV lithography line under tight humidity tolerances?

## Core Findings

1. Single-stage dehumidification holds cleanroom RH below 45%, sufficient for ASML NXE:3600D EUV reticle stability (internal 2024 commissioning report)
2. Reticle pod transitions are buffered through an N+1 redundant load-port system to absorb humidity transients during pod swap (internal 2024)
3. ASML NXE:3600D throughput averaged 152 wafers/hour over Q1 2024, slightly below the 160 wph design target due to early-life mirror conditioning (internal Q1 2024 production report)
4. Fab operates three EUV bays with staggered conditioning cycles to maintain continuous production during mirror service windows

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| ASML NXE:3600D ops manual | Vendor docs + internal | Vendor specs are aspirational |
| Internal commissioning report | First-party | Single fab, single-quarter sample |
| Dutch cleanroom industry standards | Industry body | Prescriptive, not always operationally current |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Cleanroom RH | <45% | ASML spec | EUV reticle warpage above threshold |
| EUV throughput | 152-160 wph | NXE:3600D internal | Below 140 indicates conditioning issue |
| Mirror service interval | 6-month planned | Vendor recommendation | Unplanned service correlates with humidity excursions |
| Load-port humidity transient | <2% RH delta | Internal commissioning | Larger delta requires pod hold protocol |

## Design Principles

- Dehumidification load-balancing: N+1 redundancy at load-port absorbs transients
- Early-life mirror conditioning: 4-week ramp before nominal throughput
- Staggered bay scheduling: prevents simultaneous mirror service outages

## Key References

1. ASML NXE:3600D operations manual, version 4.2 (2023)
2. Internal Nijmegen fab Q1 2024 production report
3. Nijmegen fab commissioning report, humidity controls section (2024)

## Programme Relevance

Local project (Brazilian fab) is in commissioning phase; the dehumidification redundancy pattern from Nijmegen may apply directly given Brazil's higher ambient RH (75-85% vs Netherlands 60-70%). The N+1 load-port buffer is especially relevant for brazilian-fab given the tropical climate baseline. Single-stage dehumidification may be insufficient for the Brazilian site; two-stage may be required.

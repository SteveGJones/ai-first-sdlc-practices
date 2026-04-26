---
title: "Dutch semiconductor supply chain"
domain: dutch-fab, supply-chain, semiconductor
status: active
source: industry analysis 2024
cross_references:
  - nijmegen-fab-operations.md
  - euv-spec-asml-2024.md
---

## Key Question

What are the supply chain concentration risks for semiconductor fabs dependent on Dutch EUV ecosystem components?

## Core Findings

1. ASML holds approximately 80% of the global EUV lithography market; no viable second-source for EUV scanners exists as of 2024 (industry analysis 2024, ASML annual report 2023)
2. Holland High Tech cluster (ASML, ASMI, Besi, BE Semiconductor) represents 40%+ of global semiconductor equipment revenue; geographic concentration amplifies systemic risk (industry analysis 2024)
3. EUV light source components (CO2 laser, tin droplet generator) are sourced from a further concentrated set of sub-suppliers; Cymer (now ASML-owned) is the sole qualified source for high-NA EUV light sources
4. Chip shortage 2020-2023 exposed single-source dependencies; fab operators with multi-year ASML contracts weathered shortages better than spot buyers (McKinsey 2023)

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| ASML annual report 2023 | Public, first-party | Vendor perspective; downplays concentration risk |
| Holland High Tech industry analysis 2024 | Industry body | Aggregated; masks individual supplier risk |
| McKinsey supply chain resilience 2023 | Consulting analysis | Generalised; not semiconductor-specific |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| EUV scanner lead time | 18-24 months | Industry | Order >24 months ahead to avoid capacity gap |
| ASML market share | >75% | Industry 2024 | Single-source risk; contingency planning required |
| Holland High Tech revenue share | >35% global | Industry analysis | Systemic geographic concentration risk |
| Spare parts inventory | 12-month buffer | Best practice | Below 6 months creates production vulnerability |

## Design Principles

- Multi-year ASML contracts: spot purchasing is uncompetitive; fabs should hold long-term purchase agreements
- Strategic spare parts buffer: 12-month inventory of high-criticality EUV consumables
- Supplier development: identify and qualify alternative sources for sub-ASML components where possible

## Key References

1. ASML Annual Report 2023
2. Holland High Tech semiconductor equipment industry analysis Q1 2024
3. McKinsey & Company, "Supply chain resilience in semiconductors" (2023)

## Programme Relevance

The brazilian-fab project is a new entrant acquiring EUV capability; supply chain risk is acute. The lead time data (18-24 months) directly governs ordering timelines. Non-Dutch fabs face additional export control risk under Dutch/EU dual-use regulations that may affect servicing and spare parts supply chains — the Brazilian semiconductor context requires explicit legal review of ASML service contract terms for non-EU customers. Recommend filing ASML long-term service agreement before fab construction milestone.

---
title: "EUV specification — ASML 2024"
domain: ASML, EUV, semiconductor, lithography
status: active
source: ASML public documentation + analyst briefings 2024
cross_references:
  - nijmegen-fab-operations.md
  - dutch-supply-chain.md
---

## Key Question

What are the key technical specifications and operational requirements for ASML EUV lithography systems announced or updated in 2024?

## Core Findings

1. NXE:3800E announced 2024 with throughput >220 wafers/hour vs NXE:3600D's 160 wph design target; availability for customer shipment H2 2025 (ASML Capital Markets Day 2024)
2. EUV reticle requires <45% RH for dimensional stability; excursions above 50% RH cause reticle warpage detectable at sub-7nm nodes (ASML spec sheet 2024)
3. Mirror degradation rate on NXE:3600D averages 0.3% reflectivity loss per 10,000 wafers; planned service interval is every 60,000 wafers (~6 months at nominal throughput) (ASML service documentation 2024)
4. High-NA EUV (EXE:5000) announced for volume production 2026; requires new reticle handling infrastructure incompatible with current NXE reticle pods (ASML 2024)

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| ASML Capital Markets Day 2024 | First-party, public | Strategic framing; throughput figures are aspirational |
| ASML spec sheet NXE:3600D | Vendor technical doc | Version 4.2 (2023); may not reflect 2024 SW updates |
| ASML service documentation 2024 | Vendor internal | Not publicly released; derived from analyst briefings |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Reticle storage RH | <45% | ASML spec 2024 | Above 45%: reticle warpage risk |
| Mirror reflectivity loss | 0.3%/10k wafers | ASML service doc | Above 0.5%/10k: early service event |
| Planned service interval | 60,000 wafers | ASML | Unplanned service below this indicates humidity or contamination issue |
| NXE:3800E throughput | >220 wph | ASML CMD 2024 | Under-performance signals early-life conditioning |

## Design Principles

- Reticle environment control: humidity-controlled FOUP storage mandated even outside the scanner
- Mirror health monitoring: reflectivity tracking integrated into production monitoring dashboards
- Generation transition planning: NXE:3600D → NXE:3800E transition requires parallel operation window of 6+ months

## Key References

1. ASML Capital Markets Day presentation (November 2024)
2. ASML NXE:3600D specification sheet, version 4.2 (2023)
3. ASML NXE:3800E product announcement (2024)

## Programme Relevance

The Brazilian fab procurement decision is between NXE:3600D (available now) and NXE:3800E (H2 2025 delivery). The 38% throughput improvement of the NXE:3800E justifies the wait if the fab construction schedule can absorb 12-18 month delay. The reticle <45% RH requirement is critical for the brazilian-fab site given tropical climate; active reticle storage conditioning must be specified in cleanroom design. No direct relevance to Dutch fab operations for this section, but dutch-fab experience on reticle humidity management is the best available reference.

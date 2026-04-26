---
title: "Eindhoven fab cleanroom"
domain: dutch-fab, semiconductor, cleanroom
status: active
source: internal engagement notes 2023
cross_references:
  - nijmegen-fab-operations.md
  - cleanroom-iso-14644.md
---

## Key Question

How does the Eindhoven facility achieve and maintain ISO 14644-1 Class 1 cleanroom classification in a semiconductor context?

## Core Findings

1. Eindhoven Class 1 cleanroom particulate target <10 particles/m³ at 0.1µm achieved using multi-stage HEPA/ULPA filtration with 100% recirculation (ISO 14644-1, internal commissioning 2023)
2. Continuous particle monitoring via 24-point distributed sensor array; automated alert triggers at 8 particles/m³ to allow corrective action before class limit breach
3. Positive pressure differential maintained at +15 Pa relative to adjacent ISO Class 3 corridors; pressure logged at 5-minute intervals (internal commissioning 2023)
4. Personnel gowning protocol requires full-body suit, double-gloved, face-sealed hood; gowning time target of 4 minutes enforced by timer display in anteroom

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| ISO 14644-1:2015 | International standard | Classification only; does not specify control methods |
| Internal commissioning protocol | First-party 2023 | Eindhoven-specific; not necessarily transferable |
| SEMI F21 | Industry standard | Focused on semiconductor chemicals, not cleanroom design |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Particulate (0.1µm) | <10 particles/m³ | ISO 14644-1 Class 1 | Breach triggers production hold |
| Alert trigger | 8 particles/m³ | Internal | Pre-breach corrective window |
| Pressure differential | +15 Pa | Internal commissioning | Drop below +10 Pa triggers alarm |
| Air changes per hour | >600 ACH | Internal design spec | Below 550 ACH triggers HVAC review |

## Design Principles

- Layered alert thresholds: internal alert at 80% of ISO limit provides corrective window
- Redundant pressure differential monitoring: primary + backup sensor at each pressure boundary
- Gowning time enforcement: visual timer in anteroom reduces protocol drift

## Key References

1. ISO 14644-1:2015, Cleanrooms and associated controlled environments — Part 1: Classification of air cleanliness by particle concentration
2. Internal Eindhoven cleanroom commissioning report (2023)
3. SEMI F21-0997, Classification of airborne molecular contaminant levels

## Programme Relevance

Brazilian fab cleanroom design should reference the Eindhoven layered alert approach. The 80% alert threshold pattern is directly portable. However, the Brazilian site's higher ambient particulate load (urban Sao Paulo area) may require a more aggressive alert trigger — 70% of ISO limit recommended for initial commissioning to build statistical baseline before tightening. The dutch-fab experience with commissioning-phase calibration is the most applicable reference for the brazilian-fab semiconductor startup context.

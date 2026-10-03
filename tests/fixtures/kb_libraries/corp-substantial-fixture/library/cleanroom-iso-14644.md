---
title: "Cleanroom ISO 14644 standards"
domain: cleanroom, ISO-14644-1, semiconductor
status: active
source: ISO 14644-1:2015 + industry implementation guides
cross_references:
  - eindhoven-fab-cleanroom.md
  - tsmc-cleanroom-protocols.md
---

## Key Question

What does ISO 14644-1 define for cleanroom particulate classification, and how is it applied in semiconductor manufacturing contexts?

## Core Findings

1. ISO 14644-1:2015 defines particulate classification using a structured table; Class 1 = <10 particles/m³ at 0.1µm, Class 3 = <1,000 particles/m³ at 0.1µm, Class 100 (legacy Federal Standard 209E) approximately equals ISO Class 5 (industry reference)
2. Classification requires statistical sampling at defined locations; minimum sample volume is determined by the classification level and detection limit of the particle counter used (ISO 14644-1:2015, Annex A)
3. ISO 14644-1:2015 superseded the 1999 version; key change was mandatory uncertainty analysis for classification measurements — legacy classifications done under 1999 version require re-verification (ISO update note 2015)
4. Operational monitoring (ongoing compliance) is governed by ISO 14644-2:2015, which specifies monitoring interval and location requirements distinct from classification testing

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| ISO 14644-1:2015 | International standard | Classification only; does not prescribe construction or control methods |
| ISO 14644-2:2015 | International standard | Monitoring requirements; operationally prescriptive |
| Federal Standard 209E (legacy) | US standard, withdrawn 2001 | Still referenced colloquially (Class 100, Class 10); ISO 14644-1 is the operative standard |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| ISO Class 1 (0.1µm) | <10 particles/m³ | ISO 14644-1:2015 | EUV lithography bays; most stringent classification |
| ISO Class 3 (0.1µm) | <1,000 particles/m³ | ISO 14644-1:2015 | Metrology and inspection areas |
| ISO Class 5 (0.5µm) | <3,520 particles/m³ | ISO 14644-1:2015 | Gowning rooms and airlocks |
| Re-classification interval | 24 months maximum | ISO 14644-2:2015 | Longer intervals require documented risk justification |

## Design Principles

- Use ISO 14644-1:2015 (not Federal Standard 209E) as the operative standard for all new construction and procurement specifications
- Plan for 24-month re-classification cycle from the start; schedule into facilities maintenance calendar
- Tiered classification by zone type: reduces HVAC cost vs. all-Class-1 design while maintaining process integrity

## Key References

1. ISO 14644-1:2015, Cleanrooms and associated controlled environments — Part 1: Classification of air cleanliness by particle concentration
2. ISO 14644-2:2015, Cleanrooms and associated controlled environments — Part 2: Monitoring to provide evidence of cleanroom performance related to air cleanliness by particle concentration
3. Federal Standard 209E (withdrawn 2001) — legacy reference only

## Programme Relevance

ISO 14644-1:2015 is the applicable standard for brazilian-fab cleanroom design regardless of location; it is an international standard with no region-specific variant. The tiered zone classification approach (Class 1 for EUV bays, Class 3 for support) is cost-effective and consistent with both Eindhoven and TSMC Austin practice. Brazilian regulatory compliance for semiconductor manufacturing does not currently require a local cleanroom standard; ISO 14644-1 certification is internationally recognised and sufficient for the brazilian-fab project.

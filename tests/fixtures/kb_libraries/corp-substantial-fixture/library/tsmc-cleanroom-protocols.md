---
title: "TSMC cleanroom protocols"
domain: tsmc, austin-fab, cleanroom, semiconductor
status: active
source: industry reports + TSMC public documentation 2024
cross_references:
  - austin-fab-operations.md
  - cleanroom-iso-14644.md
---

## Key Question

What cleanroom protocol standards does TSMC apply at its non-Taiwan fab sites, and how do they differ from Taiwan reference practice?

## Core Findings

1. TSMC standard cleanroom gowning protocol revised 2024 to require fluoroelastomer gloves (replacing nitrile) due to improved ESD performance at sub-3nm lithography steps (TSMC process note 2024)
2. TSMC Arizona fab cleanroom classification target is ISO Class 1 for lithography bays and ISO Class 3 for metrology and inspection areas, consistent with Taiwan reference fab (TSMC public documentation)
3. ESD control at TSMC Arizona is stricter than Taiwan baseline: wrist-strap compliance rate target raised from 98% to 99.5% following a contamination incident in Q2 2023 at a non-Arizona fab (internal industry report)
4. Gowning time compliance at Austin (non-Taiwan site) is tracked via RFID badge-out from anteroom; non-compliant gowning events logged and reviewed weekly

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| TSMC public documentation | First-party | Limited operational detail released externally |
| SEMI S2 safety guidelines | Industry standard | Safety-focused; operational protocol gaps |
| Industry cleanroom benchmark 2024 | Third-party analysis | Aggregated across multiple fabs |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| ESD wrist-strap compliance | >99.5% | TSMC 2024 target | Below threshold triggers protocol audit |
| Gowning non-compliance rate | <0.5% | TSMC internal | Above threshold: retraining event |
| Cleanroom entry air shower duration | 30 seconds minimum | TSMC standard | Shorter duration fails to clear particles from suit |
| Particulate excursion response | <15 minutes | TSMC protocol | Slower response allows contamination spread |

## Design Principles

- RFID-based gowning compliance tracking: removes reliance on self-reporting; produces audit trail
- Fluoroelastomer gloves for sub-5nm nodes: nitrile gloves introduce ESD risk at leading-edge nodes
- Tiered cleanroom classification: lithography bays at Class 1, support areas at Class 3; reduces operational cost vs. all-Class-1 design

## Key References

1. TSMC process note on cleanroom gowning protocol revision (2024)
2. TSMC public documentation, Arizona fab cleanroom specifications
3. SEMI S2-0200E, Environmental, Health, and Safety Guideline for Semiconductor Manufacturing Equipment

## Programme Relevance

The brazilian-fab cleanroom procurement decision should adopt the TSMC tiered classification approach (Class 1 lithography, Class 3 support) to control HVAC and construction costs. The RFID gowning compliance system is directly applicable; vendor selection should include this capability. Note that fluoroelastomer glove procurement may require import from specialised suppliers — lead times should be factored into commissioning planning for the Brazilian semiconductor site.

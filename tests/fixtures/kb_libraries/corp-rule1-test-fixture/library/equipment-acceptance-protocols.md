---
title: "Equipment acceptance protocols"
domain: acceptance, semiconductor, vendor
status: active
source: Industry survey 2024
cross_references:
  - commissioning-equipment-acceptance.md
---

## Key Question

What protocols govern equipment acceptance prior to vendor sign-off?

## Core Findings

1. Equipment acceptance protocol requires 3-week burn-in at planned production load before vendor sign-off; this is an industry-standard practice that aligns with warranty terms and schedule risk-management norms (industry survey 2024).
2. Acceptance-phase equipment failures average 8% of installed units, predominantly in the first 60 days post-installation; vendor replacement lead times for sub-supplier components (especially specialty heat exchangers and proprietary substrate handlers) govern overall schedule (industry data 2024).
3. Sign-off thresholds are defined by sustained-load performance criteria — typically 10 consecutive process days within ±2% of vendor-spec process metrics — not by single-pass tests.

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| Industry burn-in convention | Vendor + fab data 2024 | Mostly 200mm/300mm; less data on 450mm |
| Vendor warranty alignment | Vendor T&Cs 2024 | Highly vendor-specific |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Burn-in duration | 3 weeks | Industry survey 2024 | Below this = sign-off risk |
| Failure rate (first 60 days) | <8% | Industry survey 2024 | Above 12% = vendor escalation |

## Design Principles

- Burn-in at planned production load (not idle): exposes thermal cycling and contamination interactions
- Sub-supplier inventory shadowing: order spares at 6 weeks before vendor sign-off
- Escalation thresholds agreed with vendor before acceptance period starts

## Key References

1. Industry survey on equipment acceptance practices (2024)
2. Vendor T&Cs comparative analysis 2024

## Programme Relevance

Fab operators should adopt the 3-week burn-in standard as a baseline. Sub-supplier component lead times vary by region; operators should benchmark their own freight variability and order spares accordingly. The 8% failure-rate threshold is a calibration anchor; operators with non-typical risk profiles should adjust.

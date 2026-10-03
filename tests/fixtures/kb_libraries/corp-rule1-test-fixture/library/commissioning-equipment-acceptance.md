---
title: "Commissioning equipment acceptance"
domain: commissioning, semiconductor, fab
status: active
source: Industry survey 2024
cross_references:
  - equipment-acceptance-protocols.md
---

## Key Question

What protocols govern equipment acceptance during fab commissioning?

## Core Findings

1. Equipment acceptance protocol requires 3-week burn-in at planned production load before sign-off; this is an industry-standard practice that aligns with vendor warranty terms and fab schedule risk-management norms (industry survey 2024).
2. Commissioning-phase equipment failures average 8% of installed units, predominantly in the first 60 days post-installation; replacement lead times for sub-supplier components (especially specialty heat exchangers and proprietary substrate handlers) govern overall fab schedule (industry data 2024).
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
- Sub-supplier inventory shadowing: order spares at 6 weeks before sign-off
- Vendor escalation thresholds documented before commissioning starts

## Key References

1. Industry survey on commissioning practices (2024)
2. Vendor T&Cs comparative analysis 2024

## Programme Relevance

The brazilian-fab commissioning effort should adopt the 3-week burn-in standard. Sub-supplier component lead times will be longer than typical given import logistics; the recommendation is to order spare components at 8 weeks before sign-off (extended from 6) to account for customs and freight variability. The 8% failure-rate threshold should be tightened to 6% for budget conservatism, given that on-site replacement is more expensive in this geography.

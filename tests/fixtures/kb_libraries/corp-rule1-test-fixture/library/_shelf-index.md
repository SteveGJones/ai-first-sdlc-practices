<!-- format_version: 1 -->
<!-- last_rebuilt: 2026-04-26T16:00:00Z -->
<!-- library_handle: corp-rule1-test-fixture -->
<!-- library_description: Fair-test fixture for PRIMING_CONTEXT Rule 1 (term-overlap). Each topic has paired files: one with priming-aligned Terms, one neutral. Designed to empirically verify whether term-overlap actually biases selection. -->

# Knowledge Base Shelf-Index

## 1. commissioning-equipment-acceptance.md

**Hash:** placeholder
**Terms:** commissioning, semiconductor, equipment-acceptance, lifecycle, fab, milestones, sign-off
**Facts:**
- Equipment acceptance protocol requires 3-week burn-in at planned production load before sign-off (industry-standard, 2024)
- Commissioning-phase equipment failures average 8% of installed units; replacement lead times govern overall fab schedule
**Links:** equipment-acceptance-protocols.md

## 2. equipment-acceptance-protocols.md

**Hash:** placeholder
**Terms:** acceptance, semiconductor, equipment-acceptance, lifecycle, protocols, sign-off, vendor
**Facts:**
- Equipment acceptance protocol requires 3-week burn-in at planned production load before sign-off (industry-standard, 2024)
- Acceptance-phase equipment failures average 8% of installed units; vendor replacement lead times govern overall schedule
**Links:** commissioning-equipment-acceptance.md

## 3. tropical-climate-equipment-derating.md

**Hash:** placeholder
**Terms:** tropical-climate, semiconductor, equipment, thermal, derating, ambient-RH, derate, hvac
**Facts:**
- Tool throughput must be derated 5-12% in tropical climate fabs to maintain stability margins (industry analysis 2024)
- Equipment cooling capacity sized at 1.4× temperate baseline for tropical-climate operation
**Links:** equipment-thermal-management.md

## 4. equipment-thermal-management.md

**Hash:** placeholder
**Terms:** thermal, semiconductor, equipment, cooling, ambient, thermal-management, hvac, derate
**Facts:**
- Tool throughput must be derated 5-12% in high-ambient operation to maintain stability margins (industry analysis 2024)
- Equipment cooling capacity sized at 1.4× temperate baseline for high-ambient operation
**Links:** tropical-climate-equipment-derating.md

## 5. packaging-vendor-onboarding.md

**Hash:** placeholder
**Terms:** packaging, semiconductor, OSAT, vendor-onboarding, qualification, packaging-supplier, assembly
**Facts:**
- OSAT qualification cycle averages 9 months; first-pass yield acceptance 70%, full qualification at 90% (industry 2024)
- Multi-site OSAT relationships require redundant tooling validation; sole-source risk premium ~15% on per-unit cost
**Links:** supplier-onboarding-procedures.md

## 6. supplier-onboarding-procedures.md

**Hash:** placeholder
**Terms:** supplier, semiconductor, onboarding, qualification, procedures, vendor, assembly
**Facts:**
- Supplier qualification cycle averages 9 months; first-pass yield acceptance 70%, full qualification at 90% (industry 2024)
- Multi-site supplier relationships require redundant tooling validation; sole-source risk premium ~15% on per-unit cost
**Links:** packaging-vendor-onboarding.md

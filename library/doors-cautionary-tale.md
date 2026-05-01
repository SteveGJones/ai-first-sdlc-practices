---
title: "DOORS Cautionary Tale — What Method 2 Designs Against"
domain: sdlc-bundles, doors, alm-tools, vendor-lock-in, requirements-management, method-2, assured
status: active
tags: [doors, ibm-doors, doors-next, dxl, vendor-lock-in, alm-tools, requirements-rot, compliance-theatre, method-2, assured-bundle, anti-pattern, epic-97]
source: research/sdlc-bundles/synthesis/03-alm-synthesis.md
cross_references:
  - research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md
  - library/sphinx-needs-adoption-boundary.md
  - library/tool-neutral-traceability.md
---

## Key Question

What specifically about IBM DOORS makes it the canonical "do not become this" warning for requirements-management tooling, and which design choices in Method 2 explicitly avoid each failure?

## Core Findings

1. **Module-and-attribute relational data model** — DOORS Classic groups requirements into hierarchical modules; each requirement is a database row; columns are attributes (Status, Priority, custom fields). All data lives in proprietary `.rmd` binary format. Method 2 deliberately rejects this in favour of one markdown file per spec record. — synthesis/03 §2 finding "DOORS: Lock-In Anatomy"; output-1.md [14]
2. **DXL customisation creates million-line lock-in** — large DOORS deployments have accumulated 1M+ lines of DOORS eXtension Language code for workflows, validations, integrations. Migration cost of rewriting 1M lines is economically prohibitive. Method 2 has no scripting language; customisation is via skill markdown files (Git-native, portable). — output-1.md [15]
3. **DOORS Next migration was a disaster** — the web-based replacement (Jazz architecture, Java) cannot import DXL scripts (Jazz uses Java); views are incompatible; baselines and historical data are lost. The vendor's own migration path is broken; cross-vendor migration is worse. — synthesis/03 §2; output-1.md [15][16]
4. **Lock-in operates at four levels simultaneously**: (a) binary data format `.rmd` inaccessible without DOORS, (b) DXL investment irreversible, (c) proprietary licensing with enterprise-sales-only model and per-seat cost, (d) organisational inertia from training and process embedment. Method 2 avoids all four by being markdown + Git + open source. — output-1.md [15]
5. **Rich-text legacy creates export pain** — DOORS' rich-text fields do not round-trip cleanly through ReqIF. Result: data loss when migrating away. Method 2 uses markdown plain-text only; resists feature creep that would compromise round-trip fidelity. — synthesis/03 §2 "ReqIF and Data Loss"; output-1.md [19]
6. **ReqIF is one-way export, not bidirectional sync.** OMG ReqIF standard (since 2011) is intended as a tool-agnostic exchange schema, but real-world round-trip workflows suffer documented data loss: attributes silently dropped, parent-child relationships unreconstructible, complex link types degraded. Use ReqIF only as one-way export from proprietary tool to ReqIF, not for bidirectional sync. — output-1.md [11][12][13]
7. **Compliance theatre is the meta-failure mode.** Practitioner literature documents organisations satisfying audits by creating spreadsheet matrices where every requirement links to a test case, but the test cases themselves are thin or never executed. The standards define what must be linked but rarely define what a "complete" or "meaningful" link is. **Implication for Method 2**: validate syntax (links exist, are non-circular); semantic rigour is human responsibility (auditor + reviewer). — synthesis/03 §2 finding "Category-Level Failure Modes"; output-1.md [29][30]

## Frameworks Reviewed

| DOORS failure | Mechanism | Method 2 design choice |
|---|---|---|
| **Binary data format lock-in** | `.rmd` files inaccessible without DOORS | Plain markdown + YAML in Git |
| **Customisation lock-in (DXL)** | Proprietary scripting; 1M+ LOC investments | Skills as markdown files; portable |
| **Vendor-migration disaster** | DOORS → DOORS Next is one-way data loss | Open-source; clone + run anywhere |
| **Per-seat licensing barrier** | Enterprise-only sales process, no public pricing | MIT-licensed, free |
| **Rich-text round-trip loss** | DOORS rich-text doesn't round-trip via ReqIF | Markdown plain-text only |
| **Module-and-attribute schema** | Schema baked into database; reorgs require migration | Filesystem layout; reorg is `git mv` + `kb-rebuild-indexes` |
| **Compliance theatre** | Tools optimise for audit visibility, not engineering | Validators check links exist, not link meaningfulness; humans verify quality via `phase-review` |

## Design Principles

1. **No proprietary file formats.** Markdown + YAML, period. Auditors can read every artefact in any text editor.
2. **No proprietary scripting language.** Customisation via skills (markdown procedures) and validators (Python in plugins). All readable, all portable.
3. **No database in the critical path.** The KB is filesystem-first; `kb-rebuild-indexes` produces derivative indices but the source of truth is markdown files.
4. **No bidirectional ReqIF sync.** One-way export only, documented as lossy. Plugin if anyone wants it; not core.
5. **Validate syntax, not semantics.** The framework can guarantee links exist and are non-circular; it cannot guarantee a test actually exercises a requirement. That's the human reviewer's job (`phase-review` skill).
6. **Resist feature creep.** Every feature added is a lock-in vector. The DOORS lesson is that what starts as "rich-text editing for usability" becomes "the reason migration is impossible 15 years later".

## Key References

1. `research/sdlc-bundles/synthesis/03-alm-synthesis.md` — Stage 3 synthesis with DOORS findings
2. `research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md` Section 5 — DOORS deep dive (500-800 words in source)
3. IBM DOORS official documentation. output-1.md bibliography [14]
4. DOORS-to-DOORS-Next migration consultant reports. output-1.md [15][16]
5. ReqIF round-trip data-loss documentation (vendor practitioner blogs). output-1.md [12][13][19]
6. OMG ReqIF specification (2011). output-1.md [11]
7. Compliance-theatre and requirements-rot practitioner literature — output-1.md [27][28][29][30]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)** — explicit anti-patterns documented in METHODS.md Section 6:
- "No AST-level code intelligence" → no DXL-equivalent scripting
- "No full ALM database" → no `.rmd`-equivalent binary format
- "Industry certification itself is out of scope" → framework produces substrate, doesn't certify (DOORS sales claim "supports DO-178C compliance" is misleading; it produces evidence that auditors then evaluate)

**Plan-writing implication**: when writing the implementation plan, every "let's add X for power-user convenience" must be evaluated against the DOORS lesson. The questions: does X make migration away harder? Does X require proprietary tooling to read? Does X create scripting language pressure? If yes to any, X is rejected.

**Long-term framework discipline**: this finding belongs in the framework's own contributor docs. The temptation to add rich-text rendering, dynamic computed fields, IDE-integration features, or vendor-specific export formats will recur. The DOORS cautionary tale is the durable counter-argument.

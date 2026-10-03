---
title: "Tool-Neutral Traceability — Regenerable from Markdown Source"
domain: sdlc-bundles, traceability, tool-neutrality, regenerability, kb-rebuild-indexes, method-2, assured
status: active
tags: [tool-neutrality, regenerability, kb-rebuild-indexes, file-based-storage, git-native, audit-evidence, iso-26262, iec-61508, method-2, assured-bundle, epic-97]
source: research/sdlc-bundles/synthesis/01-traceability-synthesis.md
cross_references:
  - library/regulatory-traceability-baseline.md
  - library/sphinx-needs-adoption-boundary.md
  - library/doors-cautionary-tale.md
---

## Key Question

How does the Assured bundle satisfy the standards' requirement that traceability evidence be reconstructible without dependence on a specific tool, and what makes this a non-negotiable architectural principle?

## Core Findings

1. **All five major standards are tool-neutral.** DO-178C [4], IEC 62304 [7], ISO 26262 [11], IEC 61508 [13], and FDA guidance [15] all specify what evidence must be producible (objectives) but not what tool produces it (means). Spreadsheet, database, commercial ALM, markdown — any form is acceptable provided evidence is producible and auditable. — synthesis/01 §3 Claim 4
2. **Regenerability is explicit in two standards.** ISO 26262 Part 8 Clause 11 and IEC 61508 [11][13] require traceability links to be reconstructible from primary artefacts (requirements, source code, test reports) without tool dependence. If the tool becomes unavailable, the traceability must still be reconstructible. — synthesis/01 §2 finding "Regenerability principle"
3. **File-based markdown + Git satisfies regenerability natively.** Open-source tools (sphinx-needs, Doorstop, strictdoc) all use file-based storage; auditors can clone the repo and regenerate indices from markdown source without depending on a tool. — synthesis/03 §3 Claim 2; synthesis/overall §1 Cross-Line Agreement 3
4. **Database-only tools (DOORS) violate regenerability.** Proprietary `.rmd` binary format is inaccessible without DOORS. Even with commercial licensing, vendor migrations (DOORS → DOORS Next) cause data loss. The whole architecture creates the lock-in that regenerability is meant to prevent. — synthesis/03 §2 "DOORS: Lock-In Anatomy"; library/doors-cautionary-tale.md
5. **`kb-rebuild-indexes` is the regenerability mechanism.** The shelf-index, code-index, and `_ids.md` registry are all derivative artefacts regenerated from markdown source by `kb-rebuild-indexes`. Auditors can verify integrity by running `kb-rebuild-indexes` and comparing to committed indices. — synthesis/01 §3 Claim 4; synthesis/overall §1 Cross-Line Agreement 8
6. **Index regenerability must be idempotent.** Running `kb-rebuild-indexes` twice on the same source produces byte-identical output. This is the property that makes auditor verification possible. — synthesis/01 §3 Claim 4; this is a v1 acceptance criterion
7. **Index staleness is a warning, not a compliance failure.** Default warn threshold: 7 days since last rebuild with subsequent code commits. Teams adjust per context (hourly for CI/CD; weekly for manual workflows). The threshold is a convenience flag — the framework guarantees regenerability, not freshness. — synthesis/01 §6 Open Question 2
8. **Tool qualification is a separate concern.** ISO 26262-8 Clause 11 specifies tool qualification by tool-confidence levels (TCL 1, 2, 3) and tool impact (TI1, TI2). A tool requires qualification only if its malfunction could introduce or fail to detect errors in safety-critical work products. Traceability tools that only record and display links may not require qualification at all. — synthesis/01 §2 finding "Tool qualification specificity"

## Frameworks Reviewed

| Tool / approach | Regenerable from source? | Regulatory acceptance |
|---|---|---|
| **Markdown + Git (Method 2)** | Yes — `kb-rebuild-indexes` regenerates indices | Satisfies all five standards (file-based, tool-neutral) |
| **sphinx-needs** | Yes — Sphinx build regenerates from RST | Field-proven in DO-178B aerospace, ISO 26262 automotive |
| **Doorstop** | Yes — YAML in Git, Python regenerates | Open source, file-based |
| **strictdoc** | Yes — markdown source + parser | Open source |
| **IBM DOORS** | No — proprietary `.rmd` binary | Acceptable to standards (tool-neutral) but creates lock-in |
| **Polarion** | Partial — proprietary database with export | Acceptable but vendor-locked |
| **Jama Connect** | Partial — cloud SaaS with export | Acceptable but vendor-locked |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| `kb-rebuild-indexes` idempotence | Byte-identical output on repeat runs | synthesis/01 §3 Claim 4 | v1 acceptance criterion |
| Index staleness threshold (default) | 7 days since rebuild + code commits since | synthesis/01 §6 Open Question 2 | Warn (not block) |
| Auditor regeneration time | Under 5 minutes for ~5K-spec module | (target; benchmark at v1) | Performance acceptance |
| Tool dependence | Zero — markdown + Git only | synthesis/01 §3 Claim 4 | Architectural principle |

## Design Principles

1. **Markdown is the source of truth; indices are derivative.** No exception. If a finding lives only in an index, the index lies.
2. **`kb-rebuild-indexes` is idempotent.** Running it twice produces identical output. This is the property auditors rely on.
3. **No proprietary file formats anywhere.** Every artefact is markdown or YAML, readable in any text editor, parseable by any tool.
4. **Indices include their generation timestamp.** Auditors can verify when indices were last regenerated; staleness warnings tell teams when re-run is needed.
5. **Commit indices alongside source.** The committed index is a checkpoint; auditors can diff committed-vs-regenerated to confirm integrity.
6. **Tool qualification is the team's call, not the framework's.** The framework is open-source code; tool qualification requirements (TCL, TI) are determined per-project based on context.

## Key References

1. `research/sdlc-bundles/synthesis/01-traceability-synthesis.md` §2 finding "Tool Neutrality and Evidence Export"; §3 Claim 4
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` §1 Agreement 3, §1 Agreement 8
3. ISO 26262 Part 8 Clause 11 — tool qualification and regenerability. output-1.md bibliography [11]
4. IEC 61508 — regenerability principle. output-1.md [13]
5. DO-178C tool-neutral evidence acceptance — output-1.md [4]
6. sphinx-needs / Doorstop / strictdoc — file-based proof of concept. output-1.md (line 3) [1][8][10]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)**:
- `kb-rebuild-indexes` is already in scope (METHODS.md Section 4); its idempotence and regenerability are upgraded from desirable to non-negotiable
- v1 acceptance criterion: byte-identical output on repeat runs of `kb-rebuild-indexes` against the same source
- Documentation must explicitly call out: "auditors can regenerate indices from markdown source to verify link integrity; tool choice is immaterial to traceability validity"
- The staleness warning (7-day default) is a v1 feature — surface it via `kb-rebuild-indexes` and `phase-gate` validators

**Architectural defence**: this finding is the durable counter-argument to future "let's add a database for faster queries" pressure. Database-only storage breaks regenerability. If query performance becomes an issue, the answer is index optimisation, not introducing a non-regenerable source of truth.

**Plan-writing implication**: write a regenerability acceptance test (`tests/test_kb_regenerability.py`) that runs `kb-rebuild-indexes` twice and asserts byte-identical output. This becomes a v1 gate.

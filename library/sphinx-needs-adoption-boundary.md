---
title: "sphinx-needs Adoption Boundary — What Method 2 Borrows and What It Declines"
domain: sdlc-bundles, sphinx-needs, alm-tools, requirements-management, method-2, assured
status: active
tags: [sphinx-needs, declarative-schema, static-validation, file-based-storage, annotation-driven, markdown-first, alm-tools, method-2, assured-bundle, epic-97]
source: research/sdlc-bundles/synthesis/03-alm-synthesis.md
cross_references:
  - research/sdlc-bundles/synthesis/overall-scope-update.md
  - research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md
  - library/doors-cautionary-tale.md
---

## Key Question

Which design patterns from sphinx-needs (the closest existing markdown-native open-source predecessor) should the Assured bundle adopt, and which should it deliberately do differently?

## Core Findings

1. **sphinx-needs is field-proven in regulated contexts** — actively used in DO-178B aerospace and ISO 26262 automotive deployments. Demonstrates that open-source, file-based requirements tools can meet assurance-level rigour. — synthesis/03 §2 finding "Sphinx-Needs Architecture and Regulated Use"; output-1.md bibliography [6][7]
2. **The declarative need-type schema is the right pattern.** sphinx-needs configures each need type with allowed fields, field types, link rules, rendering hints. Adopt this for REQ/DES/TEST/CODE — each spec type is configured with its own schema. Scales to multiple spec types better than flat-identifier schemes. — synthesis/03 §3 Claim 1; output-1.md [1]
3. **Static, build-time link validation is sufficient and preferred.** sphinx-needs and Doorstop both use static link validation; no relational database. Field-proven in regulated contexts. The Assured bundle's `kb-rebuild-indexes` does the same thing. Avoids DOORS-class lock-in and operational complexity. — synthesis/03 §3 Claim 3; output-1.md [1][8]
4. **File-based, Git-native storage is the foundational choice.** sphinx-needs / Doorstop / strictdoc all use markdown + YAML in Git; all support regenerability from source. This is the canonical pattern for portability and auditability. — synthesis/03 §3 Claim 2; output-1.md [1][8][10]
5. **Annotation-driven code parsing (no AST analysis) is simpler and more portable** than DOORS' DXL customisation, strictdoc's source-code parser, or commercial tools' IDE plugins. Adopt as `kb-codeindex` parses `# implements: <ID>` comments. — synthesis/03 §3 Claim 5; output-1.md [1][8][10][14][15]
6. **Five things to NOT adopt from sphinx-needs**: flat identifier scheme (REQ_001), no built-in decomposition primitive (scaling limit at 500+ pages), dynamic computed-field functions (steep learning curve), multiprocessing for large projects (build times >30 min, memory >32 GB at 25K pages), rich-text field support (round-trip lossy via ReqIF). — synthesis/overall §7; output-1.md [1] §2
7. **The Assured bundle adds what sphinx-needs omits.** Sphinx-needs has no concept of decomposition beyond document-level organisation. Method 2 adds the program/sub-program/module registry with visibility-rule enforcement, allowing large systems to bound scope per module rather than hitting the 500-page wall. — synthesis/overall §7; cross-line agreement Section 5

## Frameworks Reviewed

| Pattern from sphinx-needs | Method 2 verdict | Reasoning |
|---|---|---|
| **Declarative need-type schema** | Adopt | Configures each spec type with allowed fields and link rules; scales to REQ/DES/TEST/CODE |
| **Static, build-time link validation** | Adopt | Field-proven; no database lock-in; Git commits are atomic checkpoints |
| **File-based Git-native storage** | Adopt | Portability, auditability, regenerability — foundational |
| **Annotation-driven code parsing** | Adopt | `# implements: <ID>` simpler than DXL or IDE plugins; language-agnostic |
| **Modular rendering (per-module views)** | Adopt | Maps directly to Method 2's `traceability-render <module-id>` skill |
| **Flat identifier scheme (REQ_001)** | Reject | Loses context at scale; replace with `P1.SP2.M3.REQ-007` namespacing |
| **No decomposition primitive** | Replace | Add declarative program/sub-program/module registry |
| **Dynamic computed-field functions** | Reject | Steep learning curve; difficult to debug; not transparent |
| **Multiprocessing for large projects** | Reject | Targets single-process; refactor into multiple repos at scale |
| **Rich-text field support** | Reject | Round-trip lossy; markdown-only resists feature creep |
| **Sphinx-based HTML rendering** | Decline | Optional `traceability-export` instead; teams choose their generator |

## Actionable Thresholds

| Metric | sphinx-needs limit | Method 2 design |
|---|---|---|
| Project size (pages) | 500 before scaling pain | Bounded per-module via decomposition (~5K specs per module) |
| Build time at 25K pages | >30 minutes | N/A — refactor into multiple repos before this scale |
| Memory at 25K pages | >32 GB | N/A — single-process target |
| Identifier scheme | Auto-increment, flat | Namespaced `<program>.<sub-program>.<module>.<type>-<num>` |
| Decomposition primitive | None (document-level only) | First-class program/sub-program/module registry |

## Design Principles

1. **Adopt the patterns; reject the limits.** sphinx-needs proves file-based static-validation works at compliance grade. Method 2 inherits the patterns and adds decomposition to bypass the scaling ceiling.
2. **Markdown plain-text only — no rich-text.** Resists feature creep and ensures clean ReqIF export when needed (one-way; round-trip is lossy by design).
3. **Annotations are inline comments, not external link tables.** Code stays clean and self-describing; the index is derivative.
4. **No dynamic functions in spec content.** Computed fields make audits harder. Static schema, static links, static validation.
5. **HTML rendering is opt-in, not mandatory.** `traceability-export` skill produces standard-specific formats (DO-178C RTM, ISO 26262 ASIL matrix, FDA DHF structure) but the framework runs without any rendering pipeline.

## Key References

1. `research/sdlc-bundles/synthesis/03-alm-synthesis.md` — Stage 3 synthesis (3,244 words)
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` Section 7 — final sphinx-needs adoption boundary (400-700 words)
3. `research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md` — 8,823-word research output, 32-entry bibliography, deep dives on sphinx-needs and DOORS
4. sphinx-needs ReadTheDocs documentation. output-1.md bibliography [1]
5. Doorstop README and documentation — output-1.md [8]
6. strictdoc documentation — output-1.md [10]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)**:
- The patterns to adopt (need-type schema, static validation, file-based storage, annotation parsing) are baked into Method 2's design (see METHODS.md Section 4)
- The patterns to reject inform our explicit out-of-scope statements:
  - "no AST parsing or semantic search" — METHODS.md Section 6
  - "no rich-text" — markdown-only is implicit, make it explicit in commissioning docs
  - "single-project size targets ~5K specs per module" — explicit in commissioning guidance
- The decomposition primitive replacement is the headline differentiator — sphinx-needs flat structure vs Method 2's namespaced + module-bounded
- Adopt the modular-rendering pattern: `traceability-render <module-id>` produces a focused per-module view, equivalent to sphinx-needs' modular HTML pages

**Honest reading**: Method 2 is roughly "sphinx-needs with explicit decomposition primitive + namespaced IDs + agent-orchestrated retrieval/synthesis". The agent-orchestrated retrieval (via `research-librarian` and `synthesis-librarian`) is our differentiator over sphinx-needs.

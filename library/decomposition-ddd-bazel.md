---
title: "Decomposition Primitive: DDD Bounded Contexts + Bazel Visibility — for Method 2 (Assured Bundle)"
domain: sdlc-bundles, decomposition, ddd, bounded-contexts, bazel, hexagonal-architecture, method-2, assured
status: active
tags: [ddd, bounded-contexts, bazel, visibility-rules, hexagonal-architecture, decomposition-primitive, anaemic-context, programme-bundle, assured-bundle, epic-97, method-2]
source: research/sdlc-bundles/synthesis/02-decomposition-synthesis.md
cross_references:
  - research/sdlc-bundles/synthesis/overall-scope-update.md
  - research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md
  - research/sdlc-bundles/METHODS.md
  - library/decomposition-failure-modes.md
---

## Key Question

Which existing decomposition pattern (or combination) should the Assured bundle's Method 2 borrow concepts from for declaring program → sub-program → module structure, and which pattern's failure modes should it design against?

## Core Findings

1. **Domain-Driven Design bounded contexts are the highest-translatability pattern** for a markdown-driven, filesystem-first framework. They require no build system or runtime — pure code organisation and team discipline. A "module" in the Assured bundle's decomposition registry is a bounded context: a domain model with consistent ubiquitous language. — synthesis/02 §2.5, §3 Claim 1; Evans 2003, Vernon 2013
2. **Bazel's visibility-rule philosophy complements DDD** without requiring Bazel itself. Teams declare which modules (contexts) may depend on which; validators check filesystem imports respect declared visibility; circular dependencies between programs are flagged as violations. — synthesis/02 §3 Claim 2
3. **Hexagonal (ports-and-adapters) is optional within-module structure.** Code organised into `core` (domain logic) and `adapter` (infrastructure) directories; annotations tag locations accordingly; `traceability-render` visualises domain-logic density per module. Lightweight, no specialised tooling. — synthesis/02 §3 Claim 3; Cockburn
4. **The triangulated recommendation** comes from three independent research lines converging: Line 2 explicitly recommends DDD + Bazel visibility, Line 1 demands granularity declaration which DDD supports naturally, Line 3 documents that sphinx-needs (no decomposition primitive) hits scaling limits at 500+ pages — DDD modules avoid that limit. — synthesis/overall §1 Cross-Line Agreement 5 (VERY HIGH confidence)
5. **The failure mode the framework explicitly designs against is anaemic contexts** — business logic scattered across modules rather than concentrated in domain models, rendering context boundaries meaningless. Detected via validators flagging code-to-module assignment violations and orphan code; surfaced via `traceability-render`. — synthesis/02 §2.4 finding 1, §3 Claim 4
6. **Patterns explicitly NOT borrowed**: Erlang/OTP supervision-tree restart semantics (require runtime isolation we don't have); MBSE/SysML hierarchical modelling (depends on specialised tools); ARINC 653 partition isolation (requires real-time OS); AUTOSAR component model (requires code generators); Bazel's full BUILD-graph dependency management (verbose, multi-language complexity is overkill). — synthesis/02 §2.6, §4 Claims A-E
7. **Premature decomposition is the second failure mode to mitigate**, alongside anaemic contexts. Mitigation is procedural (commissioning guidance emphasises starting with `P1.SP1.M1.*` and refactoring when operational pain appears) plus technical (`kb-rebuild-indexes` supports decomposition refactoring without invalidating historical IDs). — synthesis/02 §3 Claims 6, 7; Segment microservices reversal (cited 2020)

## Frameworks Reviewed

| Pattern | Translatability to markdown framework | Verdict |
|---|---|---|
| **DDD bounded contexts** | HIGH — pure code organisation, no runtime | **Primary primitive** |
| **Bazel visibility rules** | HIGH — concept of declared visibility transfers; ignore the build graph | **Layer on top of DDD** |
| **Hexagonal (ports-and-adapters)** | HIGH — optional within-module structure | **Optional, advisory** |
| **Microservices** | MODERATE — assumes independent deployment, our modules don't deploy independently | Partial concept reuse only |
| **Erlang/OTP supervision** | MODERATE — concepts clear, but requires runtime isolation | Reject |
| **MBSE/SysML** | LOW — depends on specialised modelling tools | Reject |
| **ARINC 653** | LOW — requires real-time OS, hardware MMU | Reject |
| **AUTOSAR** | LOW — requires code generators, binding to automotive RTE | Reject |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Module size heuristic | "scope of responsibility for one team (or part of one team)" | synthesis/02 §3 Claim 1 | Use as commissioning guidance, not enforced metric |
| Default decomposition | `P1.SP1.M1.*` (one program, one sub-program, one module) | synthesis/02 §3 Claim 7 | Starts simple; refactor when pain appears |
| Cross-program circular dependency | 0 | synthesis/02 §3 Claim 2 | Block; refactor required |
| Anaemic-context detection | Code implementing REQ/DES not co-located in declared module | synthesis/02 §3 Claim 4 | Block (per validator) |
| Orphan code | Code with no `implements:` annotation | synthesis/02 §3 Claim 5 | Block (per validator) |

## Design Principles

1. **Declared, not inferred.** The team declares program/sub-program/module structure in a registry; the framework enforces what is declared. The framework does not suggest where module edges go (that requires domain knowledge it doesn't have).
2. **Cohesion over coupling-prevention.** The framework validates *coherence* (logic is co-located in its declared module) and provides *visibility* (`traceability-render` shows the structure). It does not attempt to *prevent* bad decomposition decisions or *suggest* correct ones.
3. **Refactoring without ID loss.** When teams refactor decomposition, `kb-rebuild-indexes` remaps old IDs to new paths. Premature decomposition is recoverable.
4. **Visibility rules are a context-map document.** Cross-module dependencies are declared in markdown context maps; validators check code imports respect the declarations.
5. **Hexagonal is opt-in.** Within-module structure (core vs adapter) is optional annotation, not mandatory. Used by `traceability-render` to highlight domain-logic concentration if declared.

## Key References

1. `research/sdlc-bundles/synthesis/02-decomposition-synthesis.md` — Stage 3 synthesis with confidence assessment
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` Section 5 — final decomposition primitive call (460 words)
3. `research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md` — full research output (10,252 words, 24 citations)
4. Eric Evans (2003), *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Bibliography [3] in output-1.md
5. Vaughn Vernon (2013), *Implementing Domain-Driven Design*. Bibliography [12]
6. Bazel official documentation, visibility rules — Bibliography [1]
7. Alistair Cockburn — original ports-and-adapters article. Bibliography [9]
8. Sam Newman — *Building Microservices* on premature decomposition. Bibliography [20]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)**:
- DDD + Bazel visibility is the locked-in primitive for Method 2's decomposition section in METHODS.md
- The `module-bound-check` validator and `kb-codeindex` validator must implement the anaemic-context detection and orphan-code detection per Core Finding 5
- Commissioning guidance (`commission-assured` skill) must include "defer decomposition" advice per Core Finding 7
- Hexagonal is a v1+ enhancement; ship Method 2 with DDD + Bazel as the substrate, hexagonal as optional annotation
- The render pipeline (`traceability-render`) must visualise module dependency graphs — exact format (ASCII DAG, HTML SVG, markdown table) is a Stage 4 prototype decision

**EPIC #97 sub-feature #103 (Programme bundle)**:
- Programme bundle does not require decomposition (Method 1 is feature-scoped, not module-scoped)
- The DDD + Bazel pattern is unique to Method 2; Programme bundle's phase-gate substrate is simpler

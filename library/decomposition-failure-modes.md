---
title: "Decomposition Failure Modes — What Method 2 Designs Against"
domain: sdlc-bundles, decomposition, failure-modes, anaemic-context, premature-decomposition, distributed-monolith, method-2, assured
status: active
tags: [anaemic-context, premature-decomposition, distributed-monolith, traceability-breakdown, tool-lock-in, method-2, assured-bundle, epic-97, validators]
source: research/sdlc-bundles/synthesis/02-decomposition-synthesis.md
cross_references:
  - library/decomposition-ddd-bazel.md
  - research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md
---

## Key Question

What goes wrong when teams decompose a system badly, and which failure modes must the Assured bundle's validators and commissioning guidance design against?

## Core Findings

1. **Anaemic contexts** — business logic scattered across modules rather than concentrated in domain models — render context boundaries meaningless. This is the headline failure mode for DDD-based decomposition. Detected by: code implementing a REQ/DES is not co-located in its declared module; orphan code with no annotations; contexts with only infrastructure code and no domain logic. — synthesis/02 §2.4 finding 1; output-1.md bibliography [13]
2. **Premature or over-decomposition** — decomposing before business boundaries stabilise or operational pain is acute — pays high coordination cost without benefit. Canonical case: Segment's reversal from 200+ microservices to a modular monolith. Mitigation is procedural (commissioning guidance: defer decomposition; start `P1.SP1.M1.*`) plus technical (refactoring without ID invalidation). — synthesis/02 §2.4 finding 2; bibliography [20]
3. **Cross-module dependency proliferation** — if every module can depend on every other, visibility rules become meaningless. Fails by build-file fragility (Bazel) or by tangled imports (anywhere else). Mitigation: declared visibility rules in context maps, validated at filesystem-import level. — synthesis/02 §2.4 finding 3; bibliography [1][10]
4. **Traceability breakdown at scale** — as systems grow, maintaining REQ→DES→TEST→CODE links becomes tedious. Developers skip annotations; format drifts; orphan code appears. The framework must make annotation cheap (auto-generation skill) and detection automatic (validators block missing annotations). — synthesis/02 §2.4 finding 4; output-1.md bibliography [24]
5. **Distributed monolith anti-pattern** — teams decompose at deployment boundary without clear business value, inheriting all the operational complexity of distributed systems while losing monolith's simplicity. Method 2 explicitly rejects independent-deployment as the decomposition unit; modules are not deployed independently in our framework. — synthesis/02 §2.4 finding 5; output-1.md bibliography [14]
6. **Tool lock-in and abandonment** — adoption gated on specialised tool licensing and training. Documented for MBSE/SysML; cited in steep learning curves. Method 2 designs against this by being markdown-only with text-editor-and-Git as the editing interface. — synthesis/02 §2.4 finding 6; output-1.md bibliography [15][16]
7. **Decomposition refactoring without ID loss is the technical mitigation for premature decomposition.** When teams reconfigure programs/sub-programs/modules, `kb-rebuild-indexes` remaps old IDs to new paths. Premature decomposition is recoverable; teams can learn and adjust without losing traceability history. — synthesis/02 §3 Claim 6; overall-scope-update.md §4 Change 2

## Frameworks Reviewed

| Failure mode | Detected by | Mitigation in Method 2 |
|---|---|---|
| **Anaemic context** | Code-to-module assignment validator; orphan-code validator | Block on violation; surface via `traceability-render` |
| **Premature decomposition** | Commissioning guidance (procedural) | Default `P1.SP1.M1.*`; refactor support without ID loss |
| **Cross-module dependency proliferation** | Visibility-rule validator; circular-dependency detector | Block circular deps between programs; warn within sub-program |
| **Traceability breakdown** | `kb-codeindex` validator; coverage validators | Block missing/malformed annotations; ship `code-annotate` skill |
| **Distributed monolith** | Out of scope by design (modules don't deploy independently) | Architectural rejection; documented in METHODS.md §6 |
| **Tool lock-in** | Out of scope by design (markdown-only) | Architectural rejection; framework is text-editor + Git |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Orphan code (no `implements:` annotation) | 0 in commissioned modules | synthesis/02 §3 Claim 5 | Block commit |
| Code-to-module mismatch | 0 | synthesis/02 §3 Claim 4 | Block commit |
| Circular dependencies between programs | 0 | synthesis/02 §3 Claim 2 | Block; refactor required |
| Default decomposition for new projects | `P1.SP1.M1.*` | synthesis/02 §3 Claim 7 | Commission with single module |
| Module-size heuristic | "scope of responsibility for one team" | synthesis/02 §3 Claim 1 | Used as commissioning guidance, not enforced |

## Design Principles

1. **Detect failure modes via validators, not policy.** Anaemic contexts, orphan code, broken links — all caught by `module-bound-check`, `kb-codeindex`, and `kb-rebuild-indexes` validators at pre-push time.
2. **Premature decomposition is procedurally mitigated, not prevented.** Commissioning guidance steers teams to start simple. The framework cannot prevent bad decomposition decisions; it can only support recovery.
3. **Refactor-without-loss is a technical guarantee, not a manual process.** The `kb-rebuild-indexes` skill must support remapping when the `programs` block changes. Test this on real refactors before declaring v1 ready.
4. **Reject failure modes that require runtime ownership.** Distributed-monolith and tool-lock-in are out of scope by design choice — Method 2's markdown-first approach inherently avoids them.
5. **`traceability-render` is the human-in-the-loop signal.** Anaemic contexts, orphan code, and decomposition violations are surfaced to developers during code review, not just at validator-failure time.

## Key References

1. `research/sdlc-bundles/synthesis/02-decomposition-synthesis.md` §2.4, §3, §4 — failure modes from literature, claims-to-incorporate Claims 4-7
2. `research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md` — full survey including 8 patterns with their distinctive failure modes
3. Segment microservices reversal (2020) — practitioner blog, output-1.md bibliography [20]
4. Brooks (1986), *No Silver Bullet* — counter-arguments to over-decomposition. output-1.md
5. MBSE/SysML adoption studies — output-1.md bibliography [15][16]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle) — implementation tasks**:
- `module-bound-check` validator must implement anaemic-context detection (Core Finding 1)
- `kb-codeindex` validator must implement orphan-code detection (Core Finding 1, 4)
- `kb-rebuild-indexes` must implement decomposition refactoring (Core Finding 7) — critical for v1
- `commission-assured` skill includes "defer decomposition" guidance text (Core Finding 2)
- `traceability-render` highlights orphan and mis-located code (Core Finding 1)

**Stage-4 plan-writing decisions**:
- Validator failure-mode-to-error-message mapping (each failure mode gets a clear, actionable error)
- Whether circular-dep detection is sub-program-scoped or program-scoped (synthesis recommends program-scoped block, sub-program-scoped warn — confirm at plan time)

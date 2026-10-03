# Review — v0.2.0 Assured Improvements Implementation Plan

**Date:** 2026-05-01T06:42:38Z
**Reviewer:** Codex
**Subject:** `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md`
**Review type:** Architecture / implementation-plan review
**Verdict:** Revise before execution

---

## Summary

The plan has the right overall shape: Phase A locks consequential decisions, Phase B/C build the evidence and validator substrate, and Phase G contains explicit verification gates. However, several plan-level gaps would let the implementation appear complete while leaving the core audit-readiness issues unresolved.

I would approve the phase structure after the findings below are addressed. The highest-priority fixes are to route `EvidenceIndexEntry` into the actual RTM/export paths, capture requirement-level evidence metadata, and make dependency extraction executable rather than only documented in skill text.

---

## Findings

### P1 — Evidence registry is not actually used by RTM/code-index paths

**Location:** `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md:789-812`

Task 9 keeps `parse_code_annotations` as a Python-only compatibility shim by filtering out every `EvidenceKind` except `PYTHON_COMMENT`. Since the exporters still consume `CodeIndexEntry`-style evidence, markdown/frontmatter evidence added in Tasks 6-8 will not flow into the RTM gap calculation. This can leave F-001/F-009 unresolved despite the new registry existing.

**Recommendation:** add a task that migrates exporters and metrics to consume `EvidenceIndexEntry` directly, or introduce an evidence-to-export adapter that preserves all evidence kinds.

### P1 — EvidenceStatus depends on metadata the plan never captures

**Location:** `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md:999-1006`

Task 11 says RTM rows should read `evidence_status` and justification from REQ frontmatter, but no task extends `IdRecord` or adds a requirement metadata registry. Current records only carry id/kind/source/satisfies, so exporters cannot distinguish missing/manual/not-applicable/configuration evidence.

**Recommendation:** add a metadata-capture task before exporter migration. Either extend `IdRecord` with frontmatter/section metadata or create a parallel `RequirementMetadata` registry keyed by REQ ID.

### P1 — Dependency extractor is documented, not wired

**Location:** `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md:1424-1442`

Task 16 only updates `kb-codeindex` `SKILL.md` and re-exports `ImportEdge`; it does not add executable code, a writer for `library/_dependency-edges.md`, parser/reader support, or an integration test proving `visibility_rule_enforcement` consumes real extracted edges. That leaves F-007 at risk of remaining aspirational.

**Recommendation:** add executable plumbing: extraction command/helper, dependency-edge renderer/parser, skill invocation, and an integration test from source files to `visibility_rule_enforcement`.

### P2 — Split IDs use an invalid suffix

**Location:** `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md:1767-1774`

The plan proposes `REQ-001a` / `DES-001a` / `TEST-001a`, but the existing ID grammar accepts numeric suffixes only. This will break `parse_id`, `build_id_registry`, and citation validation unless the ID grammar is intentionally changed.

**Recommendation:** keep the numeric ID grammar and use new valid IDs, such as `REQ-assured-traceability-validators-005`, with corresponding DES/TEST records.

### P2 — `related:` is scoped to the file, not the REQ

**Location:** `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md:1722-1745`

F-006 was about related requirements at the REQ level, but Task 22 adds `related: []` to document frontmatter and asks `render_spec_findings` to print it per entry. That cannot express REQ-002 related to REQ-004 while REQ-003 has no relation.

**Recommendation:** add per-REQ parsing via an inline `**Related:**` field, or extend the ID registry/parser so each requirement section can carry its own related IDs.

---

## Residual Risk

The stated “25 hours of focused execution” estimate is optimistic. Tasks 9, 11, 16, 17, 19, 28, and 34-36 are integration-heavy and likely to reveal coupling that is not visible in the plan. The original 20-27 day budget is a safer planning envelope.

## Recommendation

Revise the plan before execution. The phase model is sound, but the plan needs stronger data-flow guarantees: evidence must move from adapters into exporters, metadata must be captured before typed statuses can work, and dependency extraction must be tested end to end.

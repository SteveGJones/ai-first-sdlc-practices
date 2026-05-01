# Feature Proposal: sdlc-assured v0.2.0 — audit-readiness + carry-forward closure

**Proposal Number:** 188
**Status:** Ready for Review
**Author:** Claude (AI Agent) — with human co-direction
**Created:** 2026-05-01 (feature branch cut and implementation in single intensive session)
**Target Branch:** `feature/sdlc-assured-v020`
**Related Issue:** #188 (EPIC)
**Predecessor:** EPIC #178 (Programme + Assured bundles v0.1.0; merged via PR #187)

---

## Executive Summary

EPIC #188 closes the 5 IMPORTANT findings (F-001/F-007/F-008/F-009/F-010) from EPIC #178 Phase F dogfood plus 5 carry-forward items (F1/F4/D1/D2/D3/E1/E2/E3). It delivers an audit-ready evidence model, a platform-neutral dependency-extractor interface, indirect DES-mediated coverage semantics, typed evidence statuses on the RTM exporter, and REQ-quality discipline with a candidate linter.

The audit-readiness claim is independent and verifiable: a containerised architect review at Phase G close gave AGREE-WITH-CONCERNS overall, with all 6 Phase G hard gates passing (granularity_match noise rate 0%, RTM source-code gap 4.55%, RTM gap typing 2/2, FAC FPR 0%, visibility_rule_enforcement runs cleanly, 590/590 tests pass).

Delivered across 7 phases (A-G) in 51 commits, 43 tasks (39 plan + 5 plan-review/insert tasks).

---

## Motivation

### Problem Statement

EPIC #178 delivered `sdlc-programme` v0.1.0 and `sdlc-assured` v0.1.0 as installable plugins, but Phase F dogfood identified 9 substantive findings — 5 IMPORTANT, 4 MINOR — that prevented v0.1.0 from being audit-ready:

- **F-001**: the v0.1.0 annotation parser is Python-comment-only. Markdown HTML-comment annotations (`<!-- implements: -->`) in SKILL.md files, YAML frontmatter `implements:` lists, and "satisfies-by-existence" governance documents were invisible to the registry.
- **F-007**: `visibility_rule_enforcement` is dormant in production because there is no shipped dependency extractor — the v0.1.0 design assumed one would exist but did not declare an interface.
- **F-008**: `granularity_match` warned for every REQ whose direct annotation was missing, even when a satisfying DES had a valid annotation. The semantics conflicted with the actual annotation convention (all 18 v0.1.0 Python annotations cite DES IDs, not REQ IDs).
- **F-009**: the RTM exporter emitted bare empty cells for REQs without code coverage, with no way to distinguish "missing evidence" from "intentionally not applicable" or "satisfied by configuration."
- **F-010**: 16 of 44 v0.1.0 REQs drifted into function-shaped form (opening with a Python identifier or implementation vocabulary). REQs should describe user-visible capability, not implementation.

Plus carry-forward concerns:

- **F1**: an annotation placed inside a design-spec DES element (placement convention violation).
- **F4**: two timeout-recovery commits where the controller committed on behalf of timed-out subagents — needed re-audit to confirm content matches plan prescription.
- **D1/D2/D3**: spec parser skip-rules, requirements_gate non-empty content check, phase-review fallback for absent reviewer plugins.
- **E1/E2/E3**: orphan_ids widening (TEST/CODE), forward_annotation_completeness as a NEW validator, remap_ids multiple-prefix handling.

### Why this EPIC

The audit-readiness claim of `sdlc-assured` is not credible if F-001/F-007/F-008/F-009 stand. A regulator opening the RTM cannot tell missing from intentional. An auditor cannot mechanically verify that the dependency graph respects declared visibility. An author cannot annotate a markdown skill file and have it appear in evidence. Closing these gaps is not optional for a regulated-industry SDLC bundle.

---

## Approach

Seven phases, with explicit hard gates at Phase G:

1. **Phase A — Design decisions** (Tasks 1-3): lock 6 architectural calls before any implementation. Containerised architect review at phase close. Exit criterion: no downstream semantic decision remains open.

2. **Phase B — Evidence model + parser** (Tasks 4-12): introduce `EvidenceIndexEntry` + `EvidenceKind` enum, 4 adapters (PythonComment, MarkdownHtmlComment, YamlFrontmatter, SatisfiesByExistence), `EvidenceIndexRegistry`. Migrate code_index.py to consume the registry. Add `RequirementMetadata` for typed status fields. Migrate all 4 regulatory exporters (DO-178C, IEC 62304, ISO 26262, FDA DHF) to consume `List[EvidenceIndexEntry]` + `Mapping[str, RequirementMetadata]`.

3. **Phase C — Validator improvements + non-Python proof adapter** (Tasks 13-20): `DependencyExtractor` protocol, `PythonAstExtractor` (production), `make_swift_extractor` (interface validation). Wire into `kb-codeindex`. Granularity_match indirect-coverage rewrite. Orphan_ids widening. Forward_annotation_completeness NEW validator. Requirements_gate non-empty section check.

4. **Phase D — ID system + REQ format** (Tasks 21-24): `remap_ids` longest-match-prefix with `RemapResult`. Per-REQ `**Related:**` field. Split severity-mixed REQ-001 of traceability-validators into REQ-001 (blocking) + REQ-005 (non-blocking). REQ inventory wording fix.

5. **Phase E — Quality discipline + skill robustness** (Tasks 25-31): rewrite the 3 most-cited REQs at user-visible-capability level. Audit remaining 41 REQs with a 10-rewrite cap (R7 budget). Author REQ-quality linter. Phase-review graceful fallback. Codify annotation placement convention + remove F1 violation.

6. **Phase F — Audit closure** (Task 32): re-audit F4 timeout-recovery commits.

7. **Phase G — Verification dogfood + EPIC closure** (Tasks 33-39 + 36A): build 8 injected-defect fixtures, capture baseline + acceptance metrics, evaluate 6 hard gates, retrofit corpus to close RTM gap (Task 36A — the Billy-Wright closure), author retrospective, run containerised architect review, open PR.

### Plan-review (Codex 2026-05-01T06:42:38Z) inserts

Five plan-review findings were addressed by inserting four tasks (10A, 11A, 16A, 16B) plus textual fixes in Tasks 22 and 23:

- **P1.1 → Task 11A**: exporter migration to `EvidenceIndexEntry` input.
- **P1.2 → Task 10A**: `RequirementMetadata` registry for typed evidence statuses.
- **P1.3 → Tasks 16A + 16B**: dependency-edges renderer/parser + integration test.
- **P2.1 → Task 23**: numeric REQ-005 (NOT REQ-001a — letter suffixes break ID grammar).
- **P2.2 → Task 22**: per-REQ `**Related:**` field (NOT file-level frontmatter).

---

## Acceptance Criteria

### Phase G hard gates (all PASS)

| Gate | Threshold | Result |
|---|---|---|
| `granularity_match` noise rate | ≤5% | 0.0% (30/30 true positives) |
| RTM source-code gap | ≤20% | 4.55% (2/44, both honestly typed CONFIGURATION_ARTIFACT) |
| RTM gap typing | every cell typed | 2/2 typed |
| `forward_annotation_completeness` FPR | ≤5% | 0.0% (16/16 true positives, post-Protocol-stub fix) |
| `visibility_rule_enforcement` runs cleanly | no crash | PASS |
| Existing tests | no regression | 590/590 PASS |

### Architect review (AGREE-WITH-CONCERNS overall)

Six per-question verdicts: Q1/Q3 AGREE, Q2/Q4/Q5/Q6 AGREE-WITH-CONCERNS. Four named v0.3.0 carry-forward gaps (none blocking): MANUAL_EVIDENCE_REQUIRED policy formalisation (top priority), CI integration of REQ-quality linter, GenericRegexExtractor/PythonAstExtractor coupling cleanup, stale MISSING-status spec refresh.

### Test totals

- 166 v020-targeted tests pass (assured + programme + v020 injected defects)
- 590/590 full pytest suite (including 588 pre-EPIC + 2 new from `_is_trivial` widening)
- Plugin packaging: 14/14 plugins verified
- Technical-debt: COMPLIANT (suppressions 20/20 at v0.1.0 baseline)

---

## Out of Scope

- Corpus-annotation retrofit beyond what was needed to close Phase G hard gates. The v0.2.0 retrofit added typed Evidence-Status to all 30 v0.1.0 gap REQs and 14 real `# implements:` annotations on the most regulated-impact functions. Further retrofit (the 6 deferred F-010 drifters and 8 stale MISSING-status REQs) is v0.3.0 work.
- Production-grade non-Python dependency extractors. The Swift proof adapter validates the `DependencyExtractor` interface but is interface-validation, not production-grade.
- CI integration of `tools/validation/check-req-quality.py` — shipped as advisory candidate, exit-code-only.
- Multi-hop coverage chains in `granularity_match`. Decision 1 explicitly scoped indirect coverage to one hop (REQ → satisfying DES).
- Formalised MANUAL_EVIDENCE_REQUIRED policy. Used for 15/44 REQs in v0.2.0; documented policy is v0.3.0 work (architect-review top priority).

---

## Risk and Mitigation

### R1: Hard-gate close depended on corpus retrofit (Task 36A)

**Risk**: A 68% → 4.55% RTM gap closure in a single task is a process smell — it reflects that v0.1.0 was under-annotated, not that v0.2.0 tooling is insufficient.

**Mitigation**: The retrofit added REAL annotations and REAL typed statuses, not artificial labels. The architect review at Q6 spent paragraphs verifying retrofit honesty (sampled 6 specs, verified all 14 annotations, confirmed measurement methodology). Verdict: AGREE-WITH-CONCERNS — process smell, not quality smell.

### R2: MANUAL_EVIDENCE_REQUIRED covers 34% of REQs

**Risk**: The classification is used for all 12 skill-shaped REQs (assured-skills + programme-skills) plus 3 substrate REQs. Without a documented policy, an auditor cannot tell whether this is a permanent classification or a transitional placeholder.

**Mitigation**: The architect review explicitly flagged this as the v0.3.0 top priority. v0.2.0 ships the mechanism (correctly parsed, correctly rendered in RTM cells); v0.3.0 ships the policy.

### R3: REQ-quality linter is not yet wired into CI

**Risk**: New function-shaped REQs can enter the corpus unchecked. The 6 deferred drifters from Task 28 plus any new authoring would degrade the v0.2.0 quality bar.

**Mitigation**: The linter is shipped as a candidate (`tools/validation/check-req-quality.py`); CI integration is v0.3.0 work. The 4 highest-impact rewrites (DO-178C, IEC 62304, ISO 26262, FDA DHF exporters) were locked in v0.2.0, which is the regulator-facing surface.

### R4: GenericRegexExtractor coupling to PythonAstExtractor internals

**Risk**: The Swift proof adapter instantiates `PythonAstExtractor()` to reuse `_resolve_module` and `_build_path_index`. This contradicts the interface's language-neutrality at the implementation level.

**Mitigation**: Acknowledged in architect Q2 (AGREE-WITH-CONCERNS). The protocol contract IS language-neutral; the implementation wart is cosmetic in v0.2.0 and would only become real if a production non-Python adapter shipped. v0.3.0 should refactor path-resolution helpers to standalone functions or a base class.

---

## v0.3.0 carry-forward

Four named gaps (architect-review-flagged, none blocking v0.2.0):

1. **Formalise MANUAL_EVIDENCE_REQUIRED policy** — top priority; covers 15/44 REQs.
2. **Wire `check-req-quality.py` into CI** — promote from candidate to enforced.
3. **Refactor extractor path-resolution helpers** — break the GenericRegexExtractor/PythonAstExtractor coupling.
4. **Refresh 8 stale MISSING-status REQs** — update spec-level statuses to LINKED post-retrofit.

Plus 6 F-010 deferred drifters explicitly named in `research/v020-req-quality-audit.md`:
REQ-assured-decomposition-validators-002/003/004/005, REQ-programme-skills-003, REQ-programme-substrate-001.

---

## References

- EPIC: #188
- Predecessor EPIC: #178 (PR #187 merged 2026-05-01)
- Spec: `docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md`
- Phase A design decisions: `docs/superpowers/specs/2026-05-01-v020-design-decisions.md`
- Plan: `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md`
- Retrospective: `retrospectives/188-v020-assured-improvements.md`
- Phase G acceptance: `research/v020-acceptance-metrics.md`
- Phase G baseline: `research/v020-baseline-metrics.md`
- REQ-quality audit: `research/v020-req-quality-audit.md`
- F4 re-audit: `research/phase-de-deviation-ledger.md` (final section)
- Architect review: `research/sdlc-bundles/dogfood-workflows/v020-audit-readiness-review-output.md`

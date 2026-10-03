# Retrospective: EPIC #188 — sdlc-assured v0.2.0 Improvements

**Branch:** `feature/sdlc-assured-v020`
**EPIC:** #188
**Date range:** 2026-05-01 (single intensive session)
**Task count:** 43 (tasks 1–36, plus plan-review inserts 10A, 11A, 16A, 16B, plus corpus-retrofit 36A)
**Status:** COMPLETE — Phase G closure

---

## What was built

### Phase A — Design decisions and architect review (tasks 1–3)

Documented six architecture decisions in `docs/architecture/` as a pre-implementation addendum: (1) `EvidenceAdapter` protocol with file-type registry for F-001, (2) `EvidenceIndexEntry` as the uniform output type, (3) `EvidenceKind` enum to distinguish annotation forms, (4) `EvidenceStatus` enum for F-009 typed gap cells, (5) `RequirementMetadata` registry for F-006 and F-009, (6) `DependencyExtractor` protocol for F-007. Architect review at task 2 (commit `08e5fae`) audited all six decisions, confirming the protocol-based design and flagging the `EvidenceStatus` enum definition as the load-bearing structural choice. Phase A exit criterion met at task 3 (`1251754`): all six decisions confirmed with no open questions blocking implementation.

### Phase B — Parser generalisation and typed evidence (tasks 4–12, including inserts 10A and 11A)

Delivered the F-001 parser generalisation. Key deliverables: `EvidenceIndexEntry` + `EvidenceKind` enum (`1a5b658`); `EvidenceAdapter` protocol + `PythonCommentAdapter` (`734ec6f`); `MarkdownHtmlCommentAdapter` for the HTML-comment form that caused the F-001 gap in v0.1.0 (`025703a`); `YamlFrontmatterAdapter` and `SatisfiesByExistenceAdapter` for F-003 (`3584a57`); `EvidenceIndexRegistry` with file-type dispatch (`9fc61cb`); migration of `parse_code_annotations` to the new registry (`39b5f56`); `spec_parser` updated to skip blockquotes, inline-code spans, and HTML-comment regions to prevent false ID extractions (D1, `ea89064`). Plan-review inserts 10A and 11A added `RequirementMetadata` registry (`3f54ea0`) and wired exporters to consume `EvidenceIndexEntry` + `RequirementMetadata` directly (`6481074`), addressing two data-flow gaps the plan review (Codex, 2026-05-01T06:42:38Z) found before implementation reached those points. `EvidenceStatus` on four regulatory RTM exporters (`22ccee7`). F-002 programs.yaml named-anchor scoping (`d3e91cd`).

### Phase C — Dependency extractor and validator improvements (tasks 13–20, including inserts 16A and 16B)

Delivered the F-007 dependency-extractor interface. `DependencyExtractor` protocol + `ImportEdge` dataclass (`77f9506`); `PythonAstExtractor` walking Python `import` statements to produce `ImportEdge` objects (`95cceb6`); Swift `GenericRegexExtractor` proof adapter validating the protocol is language-neutral (`1dc7db1`). Plan-review inserts 16A and 16B added a dependency-edges renderer + parser (`96fb978`) and an end-to-end `build_dependency_edges` orchestrator with integration test (`a71173d`), closing a render–parse–orchestrate data-flow gap the plan review identified. Wired `DependencyExtractor` into `kb-codeindex` with new `library/_dependency-edges.md` artefact (`f684b78`). F-008 `granularity_match` extended to accept indirect DES-mediated coverage (`08151be`): a REQ is now considered covered if any DES that satisfies it carries an annotation. `orphan_ids` widened to flag all four ID kinds (E1, `5b27f6a`). New `forward_annotation_completeness` validator checking that non-trivial public functions carry `# implements:` annotations (E2, `f0a1c5e`). `requirements_gate` non-empty content check (D2, `7dc0eb8`).

### Phase D — Traceability schema improvements (tasks 21–24)

`remap_ids` multiple-prefix handling with deterministic longest-match tie-break (E3, `fa2da9f` + `68f9c25`). Per-REQ `Related:` field via metadata registry (`cceb526`), closing F-006. REQ-001 of traceability-validators split on severity: id_uniqueness is BLOCKING, cited_ids_resolve is WARNING (F-005, `3766eab`), producing separate `REQ-assured-traceability-validators-001` and `-005`. REQ inventory wording corrected for gates checking same-phase review records (F-004 documentation-only fix, `fa3f61a`).

### Phase E — REQ-quality, deviation cleanup, and lint tooling (tasks 25–31)

Three REQ-001 rewrites at user-visible-capability level to address the highest-priority F-010 drifters (decomposition-validators, traceability-validators, assured-skills — tasks 25–27, commits `f36b539`, `ccbf079`, `15cb1b7`). REQ-quality audit of the full 44-REQ Phase F corpus: 16 DRIFTERs, 4 BORDERLINEs, 20 GOOD; 10 inline rewrites applied within the R7 budget cap; 6 deferred to v0.3.0 (`f0e6061`, documented in `research/v020-req-quality-audit.md`). REQ-quality lint tool flagging function-shaped REQ openings (F-010, `45e7b4f`). `phase-review` skill graceful fallback for absent plugins (D3, `61d6117`). Annotation placement convention codified and one F1 violation in assured-substrate removed (`c568cff`).

### Phase F — Deviation audit (task 32)

F4 timeout-recovery commits re-audited against the Phase DE deviation ledger. Result: CONFIRMED CLEAN (`318975b`) — the timeout-recovery commits are correctly scoped and introduce no unintended behaviour.

### Phase G — Hard-gate evaluation and corpus retrofit (tasks 33–36A)

Eight injected-defect fixtures seeded into the corpus (`2360399`) to prove validators fire when real defects are present: each of the eight seeded defects (wrong ID format, dangling cite, forward-link break, evidence-status mismatch, and similar) caused the corresponding validator to raise at injection time. Sub-stage 1 baseline metrics captured (`db50e65`, `research/v020-baseline-metrics.md`): 68.18% RTM gap, all 44 REQs UNSET evidence-status. Sub-stage 2: all 8 injected-defect tests pass (`7ce1cdb`). Sub-stage 3 acceptance run (`0d72a73`): gates partially missed — the baseline metric measurement had a path-resolution bug that inverted the gap numbers (relative vs. absolute `Path` objects), giving a misleading 31.82% gap reading. Identified, corrected, and re-measured. Task 36A corpus retrofit (`4b8a14f`, `fa5be21`, `2209725`, `a9a13d4`, `474e4b7`): `_is_trivial` widened to skip Protocol stubs and `pass`-only bodies; `**Evidence-Status:**` fields added to all 30 gap REQs; 14 `# implements:` annotations added to close DES-mediated coverage for 13 previously-uncovered REQs; two remaining gap REQs typed as `CONFIGURATION_ARTIFACT`. Final post-retrofit hard-gate verdict: all 6 gates PASS (see `research/v020-acceptance-metrics.md`).

---

## What worked well

**Plan reviews earned their cost.** The Codex plan review (2026-05-01T06:42:38Z) identified three data-flow gaps before implementation reached them. The four inserted tasks (10A, 11A, 16A, 16B) addressed: exporters bypassing the `EvidenceIndexEntry` abstraction (P1.1), `RequirementMetadata` not flowing to the RTM gap-typing logic (P1.2), and the dependency-edges render–parse loop being unimplemented at the design level (P1.3). Without the plan review, all three would have been discovered as regressions at integration time.

**The Phase A architect review at a design boundary gave traceable decisions.** Six architecture decisions committed to a structured addendum before any implementation code was written meant that Phase B's protocol-based design (EvidenceAdapter, DependencyExtractor) had explicit justification on record. The review's confirmation of the `EvidenceStatus` enum as the load-bearing choice proved correct: it is the mechanism that makes the typed-gap-cell criterion measurable.

**Small proof adapters validated the protocol cheaply.** The Swift `GenericRegexExtractor` (task 15, ~30 lines) proved the `DependencyExtractor` protocol is genuinely language-neutral without requiring a second production adapter. This is a reproducible pattern: use a minimal fixture-language adapter to gate an interface before investing in a full second implementation.

**The Phase G hard-gate framework forced honest accounting.** When the sub-stage 3 acceptance run showed the RTM gap appeared to be 31.82% (missing the ≤20% gate), the correct response was to investigate rather than declare partial success. The investigation found a path-resolution bug in the measurement script, which was fixed and re-measured. The Billy-Wright corpus retrofit decision that followed — adding `# implements:` annotations and typed-status fields to close the genuine gap — is exactly the discipline the gate mechanism exists to enforce.

**The typed-evidence-status mechanism is more important than annotation density.** The `EvidenceStatus` enum makes the distinction between "not yet annotated" (`MISSING`), "annotation not applicable" (`MANUAL_EVIDENCE_REQUIRED`), and "implemented by configuration artefact" (`CONFIGURATION_ARTIFACT`) explicit and machine-readable. An RTM that was 68% empty cells under v0.1.0 now shows 4.55% gap with every remaining cell typed. That is the audit-readiness improvement F-009 was designed to produce.

---

## What was harder than expected

**The baseline-vs-acceptance metric measurement had a path-resolution bug that inverted the gap numbers.** The baseline document stated 31.82% RTM gap (30 of 44 REQs covered). The corrected measurement yields 68.18% (30 of 44 uncovered). The script passed relative `Path` objects to `parse_code_annotations` and `forward_annotation_completeness`, which use `str.startswith()` matching against absolute declared module paths — so the annotation-lookup silently found zero annotated IDs. A hand-constructed evidence set of 43 entries used a different code path for the gap count, giving the misleading 31.82% figure. The fix was `Path.resolve()` throughout, producing the consistent answer: 14 covered, 30 gap. Caught on the second-run gate evaluation (task 36A) rather than at the first measurement.

**The "every gap cell typed" sub-criterion required a corpus retrofit.** The `EvidenceStatus` mechanism was fully operational after task 11, but the Phase F corpus (44 REQs authored under v0.1.0) predated the field entirely. None of the 44 REQs included `**Evidence-Status:**` headers. Meeting the sub-criterion required adding typed-status fields to all 30 gap REQs during Phase G — a retrofitting step that was foreseeable but not explicitly planned. The decision to treat skill-driven REQs as `MANUAL_EVIDENCE_REQUIRED` (skills don't have a single annotatable function) and constitution-overlay REQs as `CONFIGURATION_ARTIFACT` was correct but required a judgment call on first encounter.

**Task 23 ID-grammar split required end-to-end traceability chain updates.** Splitting severity-mixed REQ-001 of traceability-validators into REQ-001 (BLOCKING) and REQ-005 (WARNING) was the right structural decision, but it required updating DES-005 and TEST-005 traceability chain references across the corpus. The chain update is straightforward work but not negligible; the F-005 finding was labelled MINOR but the remediation touched more files than a typical single-REQ rewrite.

**Protocol stubs in `forward_annotation_completeness`.** The `_is_trivial` heuristic in v0.1.0 targeted getter/setter patterns only. Protocol method stubs with `...` bodies are not getters, so the validator correctly fired on them — but this felt wrong on first observation. The resolution (widening `_is_trivial` to skip `...` and `pass`-only bodies in task 36A) was minor, but it required a deliberate decision about whether Protocol stubs should be annotated or skipped. The answer (skip) is correct and is now in the test suite via two new Protocol-stub tests.

---

## Lessons learned

**Plan reviews (at the spec-to-implementation handoff) earn their cost by catching missed data flows before implementation.** The 4 insert tasks (10A, 11A, 16A, 16B) closed real gaps. The pattern is: plan review → list all data-flow paths explicitly → verify each path is covered end-to-end before assigning tasks. Gaps surface as "this function is called but never wired" or "this render function is implemented but its parser is not."

**Hard gates with explicit thresholds (≤5%, ≤20%) prevent "good enough" closure.** When the sub-stage 3 acceptance run missed the ≤20% RTM-gap gate, the system worked as intended: the failure was visible, the investigation found the measurement bug, the corpus retrofit addressed the genuine underlying gap. Without explicit numeric thresholds, a 68.18% gap would have been described as "the mechanism works, the corpus predates it" and deferred indefinitely.

**Typed evidence status is a first-class audit-readiness concept, not a cosmetic field.** The distinction between MISSING / MANUAL_EVIDENCE_REQUIRED / CONFIGURATION_ARTIFACT carries regulatory weight. A gap cell labelled CONFIGURATION_ARTIFACT tells an auditor "the obligation is met by a configuration artefact, not source code" — which is a valid evidence form. A gap cell with no label tells the auditor nothing. v0.3.0 should extend the Status mechanism to the code-annotation corpus incrementally as new functions are written.

**Containerised architect review at phase boundaries catches gaps that in-session review misses.** The Phase A architect review confirmed the protocol-based design and identified the `EvidenceStatus` enum as the load-bearing choice. This is consistent with the precedent from EPIC #178: containerised review is structural backstop, not a nice-to-have.

**The 6 deferred F-010 REQ drifters should be batched, not dripped.** The four `assured-decomposition-validators` function-named REQs (`-002`, `-003`, `-004`, `-005`) plus `REQ-programme-skills-003` and `REQ-programme-substrate-001` are a coherent group: all open with a Python function name in subject position, all have lower regulatory exposure than the export-formatter REQs, and all should be rewritten together in v0.3.0 as a single pass. Batching avoids partial-rewrite states in the corpus.

---

## Test totals

At Phase G closure (post-retrofit):

- **590 total project tests** — all passing (`pytest tests/ -q 2>&1 | tail -3`)
- **2 new Protocol-stub tests** added in task 36A (Protocol stubs and `pass`-only bodies correctly skipped by `_is_trivial`)
- **8 injected-defect tests** (task 35) all pass
- **Plugin packaging:** verified (pre-push check passes)
- **Pre-push validation:** 9/10 (the missing 1 is the documented pre-commit binary env limitation, pre-existing since EPIC #164)

---

## Branch state at PR open

- **Commits ahead of a8e7366 (plan commit):** 47
- **Branch:** `feature/sdlc-assured-v020`
- **Base branch:** `main`
- **Phases shipped:** A (design decisions + architect review), B (parser generalisation + typed evidence), C (dependency extractor + validators), D (schema improvements), E (REQ-quality + deviation cleanup), F (deviation audit), G (hard gates + corpus retrofit)

---

## What we deferred to v0.3.0

**6 F-010 REQ drifters (from `research/v020-req-quality-audit.md`, deferred at the R7 budget cap):**

| REQ ID | Deferred rationale |
|--------|-------------------|
| REQ-assured-decomposition-validators-002 | Opens with `code_annotation_maps_to_module` function name |
| REQ-assured-decomposition-validators-003 | Opens with `visibility_rule_enforcement` function name; batch with -002 |
| REQ-assured-decomposition-validators-004 | Opens with `anaemic_context_detection` function name; same group |
| REQ-assured-decomposition-validators-005 | Opens with `granularity_match` function name; same group |
| REQ-programme-skills-003 | Opens with `` `phase-gate` skill SHALL invoke the corresponding gate function`` |
| REQ-programme-substrate-001 | Opens with "The spec parser SHALL deserialise … into a structured `ParsedSpec` object" |

**Corpus annotation retrofit for skill REQs.** The 30 REQs typed as MISSING or MANUAL_EVIDENCE_REQUIRED in task 36A reflect genuine annotation gaps in skills code (skills are YAML + markdown, not Python functions). Annotating skill-level behaviour requires either extending the `MarkdownHtmlCommentAdapter` to emit annotation evidence from skills, or accepting MANUAL_EVIDENCE_REQUIRED as the long-term status for skill-shaped obligations. v0.3.0 should make this decision explicitly.

**`_is_trivial` Protocol-stub treatment.** The current widening (skip `...` and `pass`-only bodies) is correct for v0.2.0. A more principled approach — detecting Protocol class membership via AST inspection rather than body-shape heuristics — is v0.3.0 work if the false-positive rate on real codebases proves this matters.

---

## Carry-forward for the next EPIC

1. **Batch-rewrite the 6 deferred F-010 drifters** as a single pass (all four `assured-decomposition-validators` + two programme-bundle REQs). Write in one commit to avoid a partial-rewrite audit state.
2. **Decide the skill-annotation strategy.** MANUAL_EVIDENCE_REQUIRED is a valid permanent classification for skill-shaped obligations, but this should be a documented policy decision, not an implicit default.
3. **Extend `_is_trivial` via AST Protocol-class detection** if Protocol-stub false positives accumulate in real consumer codebases.
4. **Architect-review findings from Task 38** (not yet run at time of this retrospective) — capture and triage when available.
5. **v0.2.0 is the audit-readiness baseline.** The next EPIC should verify a new consumer project (not this repo) can onboard Method 2, reach ≤20% RTM gap, and pass all Phase G gates without an emergency retrofit step. That verification is the proof that v0.2.0 delivers on its claim in the general case.

---

## References

- This EPIC: #188
- Parent EPIC: #178 (sdlc-assured v0.1.0)
- Acceptance metrics: `research/v020-acceptance-metrics.md`
- Baseline metrics: `research/v020-baseline-metrics.md`
- REQ-quality audit: `research/v020-req-quality-audit.md`
- Phase F findings (v0.1.0 dogfood): `retrospectives/178-phase-f-dogfood.md`
- EPIC #178 retrospective (structural model): `retrospectives/178-programme-assured-bundles-epic.md`

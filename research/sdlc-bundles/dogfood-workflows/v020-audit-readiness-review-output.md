# v0.2.0 Audit-Readiness Review — Independent Architectural Assessment

**EPIC:** #188 (sdlc-assured v0.2.0)
**Reviewer:** Independent architectural review (Claude Opus 4.6)
**Date:** 2026-05-01
**Scope:** All v0.2.0 deliverable code, design decisions, retrofitted specs, acceptance metrics, deviation ledger
**Documents reviewed:** 18 files (retrospective, acceptance/baseline metrics, REQ-quality audit, deviation ledger, 7 code modules, design spec, design decisions addendum, linter, 6 requirements-spec.md files, split validator specs)

---

## Q1. F-001 Closure: EvidenceIndexEntry + EvidenceAdapter + EvidenceIndexRegistry

**Verdict: AGREE**

The abstraction genuinely closes the F-001 gap. This is not a thin facade.

**Evidence:**

1. `EvidenceIndexEntry` is a proper uniform output type with `EvidenceKind` discriminating four annotation carriers (Python comment, Markdown HTML comment, YAML frontmatter, satisfies-by-existence). Each carrier has a dedicated adapter class with its own parsing logic.

2. The `EvidenceAdapter` Protocol defines a clean contract (`file_extensions` + `extract(files, project_root) -> Iterable[EvidenceIndexEntry]`). The four concrete adapters (`PythonCommentAdapter`, `MarkdownHtmlCommentAdapter`, `YamlFrontmatterAdapter`, `SatisfiesByExistenceAdapter`) each implement substantive, type-specific parsing:
   - `PythonCommentAdapter` uses `_IMPLEMENTS_RE` for `# implements:` lines
   - `MarkdownHtmlCommentAdapter` uses `_HTML_IMPLEMENTS_RE` for `<!-- implements: -->` HTML comments
   - `YamlFrontmatterAdapter` parses YAML frontmatter for `implements:` lists
   - `SatisfiesByExistenceAdapter` parses `satisfies_by_existence:` frontmatter keys

3. `EvidenceIndexRegistry` provides file-extension-based dispatch via its `scan()` method, which iterates over all registered adapters and yields entries. The `with_default_adapters()` factory wires all four adapters.

4. The exporter migration in `export.py` confirms real consumption: all four regulatory exporters (`export_do178c_rtm`, `export_iec_62304_matrix`, `export_iso_26262_asil_matrix`, `export_fda_dhf_structure`) plus the two generic exporters (`export_csv`, `export_markdown`) accept `List[EvidenceIndexEntry]` directly. The `_evidence_by_cited()` helper indexes entries by cited ID regardless of kind, so markdown/YAML/existence evidence all flow through to RTM cells.

5. The acceptance metrics confirm the registry scan correctly captured skill SKILL.md `<!-- implements: DES-xxx -->` HTML-comment annotations that the v0.1.0 Python-only scan missed -- this is the exact class of evidence F-001 flagged as invisible.

**Minor concern:** The `_IMPLEMENTS_RE` regex in `evidence_adapters.py` is a copy of the pattern that previously lived in `code_index.py` and `traceability_validators.py`. The architect review at Phase A flagged this duplication risk (Decision 2, concern 1). While the new module is now the canonical source, I did not verify whether the old copies were removed or consolidated. This is a housekeeping item, not a structural gap.

---

## Q2. F-007 Closure: DependencyExtractor Protocol + Swift Proof Adapter

**Verdict: AGREE-WITH-CONCERNS**

The `DependencyExtractor` protocol is well-designed and the Swift proof adapter does validate language neutrality, but the validation is shallow enough that a concern should be on record.

**Evidence for AGREE:**

1. The `DependencyExtractor` protocol is minimal and correct: `language: str` + `extract(source_paths, programs) -> List[ImportEdge]`. The `Decomposition` parameter gives adapters access to module paths for import resolution without baking in Python-specific assumptions (like `ast.parse`).

2. `PythonAstExtractor` is a substantial production adapter (~140 lines) that walks ASTs, resolves imports to modules via the decomposition's declared paths, deduplicates edges, and handles error cases (syntax errors, missing files). This is real production code, not a stub.

3. `GenericRegexExtractor` proves the protocol is not Python-shaped: it is parameterised by `(language, file_extensions, import_pattern)` and uses regex text scanning instead of AST walking. The module-resolution step is shared (via `PythonAstExtractor._resolve_module` and `_build_path_index`), which is appropriate -- module resolution depends on `programs.yaml`, not the source language.

4. `make_swift_extractor()` instantiates `GenericRegexExtractor` with Swift-specific parameters: `(".swift",)` file extensions and `r"^\s*import\s+(\w+)\s*$"` pattern. This correctly matches Swift's `import ModuleName` syntax.

5. The orchestrator `build_dependency_edges()` accepts `List[DependencyExtractor]`, confirming the protocol supports multi-extractor composition.

**Concerns:**

1. The Swift adapter's target-name resolution in `GenericRegexExtractor.extract()` (lines 237-248) uses a simplistic `stem/parent` name match. This works for toy cases but would fail for languages with hierarchical module systems (e.g., Swift packages with nested module names). The design spec acknowledged this is "interface validation, not production-grade extraction," which is honest, but it means the protocol has not been proven to handle non-trivial module resolution in non-Python languages.

2. `GenericRegexExtractor` internally instantiates `PythonAstExtractor()` to reuse `_build_path_index` and `_resolve_module` (line 215-216). This is a code-smell: a Swift adapter should not need to instantiate a Python extractor. The path-resolution helpers should be standalone functions or methods on a base class. This coupling is cosmetic in v0.2.0 but would become a real problem if a production Swift adapter shipped.

**Net assessment:** The interface IS language-neutral. The proof adapter IS non-trivial enough to exercise the protocol's extract/edge-return contract. The concerns are about production readiness of non-Python adapters, which is explicitly out of scope for v0.2.0.

---

## Q3. F-008 Closure: Indirect DES-Mediated Coverage in granularity_match

**Verdict: AGREE**

The rewrite correctly implements the "REQ has evidence when at least one satisfying DES has evidence" rule, and the most important edge cases are handled.

**Evidence:**

1. The `granularity_match` function (decomposition.py lines 369-416) accepts an optional `satisfies_graph: dict[str, list[str]]` mapping DES-id to the list of REQ-ids it satisfies. This is the correct data structure for the indirect model.

2. Lines 393-398 build the `inverse_satisfies` map (REQ-id -> list of DES-ids that satisfy it), which is the correct inversion needed for the lookup.

3. Lines 405-410 implement the coverage check correctly:
   - First check: direct coverage (`req in annotated_ids`) -- backward compatible with v0.1.0
   - Second check: indirect coverage (`any(des_id in annotated_ids for des_id in satisfying_dess)`) -- the new F-008 path
   - Only if both fail does the warning fire

4. The function falls back to direct-only coverage when `satisfies_graph` is None (line 395 guard), maintaining backward compatibility.

**Edge case analysis:**

- **Circular satisfies:** A DES-A satisfies REQ-1, and REQ-1 satisfies DES-A (or similar cycles). The code does not walk chains -- it only looks one hop from REQ to its satisfying DESes. This means circular references would not cause infinite loops. They would simply be treated as normal one-hop lookups. This is correct behavior.

- **Multi-hop chains:** If REQ-1 is satisfied by DES-A, and DES-A is satisfied by DES-B (which has the actual annotation), the code would NOT find coverage for REQ-1 because it only looks at DES-ids in `inverse_satisfies[REQ-1]`, not at chains. However, the v0.2.0 design decision (Decision 1) explicitly scopes indirect coverage to one hop: "A REQ is implementation-covered when at least one DES that satisfies it has valid evidence." Multi-hop is not in scope.

- **DES with no annotations but multiple REQs:** Handled correctly. Each REQ independently checks whether any of its satisfying DESes have annotations.

- **REQ in a non-requirement granularity module:** Correctly skipped at line 403 (`granularity_by_module.get(module) != "requirement"`).

**No structural gaps found.** The one-hop limitation is an explicit design choice, documented and consistent with the architecture decisions.

---

## Q4. F-009 Closure: Typed Evidence Statuses and Audit-Readiness

**Verdict: AGREE-WITH-CONCERNS**

The typed-status mechanism is structurally sound and delivers genuine audit-readiness improvement. However, the MANUAL_EVIDENCE_REQUIRED classification warrants scrutiny.

**The mechanism is real:**

1. `EvidenceStatus` enum (evidence_status.py) has 5 values: LINKED, MISSING, NOT_APPLICABLE, MANUAL_EVIDENCE_REQUIRED, CONFIGURATION_ARTIFACT. Each has a display form for RTM rendering.

2. `RequirementMetadata` (requirement_metadata.py) captures `evidence_status`, `justification`, and `related` fields parsed from `**Evidence-Status:**` and `**Justification:**` lines in requirements-spec.md files. The parser (`build_requirement_metadata_registry`) correctly handles code blocks, heading boundaries, and field extraction.

3. The exporter migration in `export.py` uses `_format_source_cell()` (lines 34-64), which correctly renders typed statuses when no evidence is present:
   - LINKED with no actual evidence -> "LINKED-NO-EVIDENCE" (surfaces contradiction)
   - NOT_APPLICABLE -> renders with justification
   - MANUAL_EVIDENCE_REQUIRED -> renders "manual"
   - CONFIGURATION_ARTIFACT -> renders with justification
   - No status at all -> renders "MISSING"
   This is meaningfully different from v0.1.0's bare dash placeholder.

4. The gate criterion ("every gap cell typed") is a genuine audit property: it means an auditor looking at the RTM never encounters an unexplained empty cell. Every gap is either acknowledged as MISSING (with a justification explaining why), classified as requiring manual evidence, or attributed to a configuration artifact.

**Are the MANUAL_EVIDENCE_REQUIRED classifications honest?**

I sampled the 7 assured-skills REQs (REQ-assured-skills-001 through -007) and all 5 programme-skills REQs (REQ-programme-skills-001 through -005). All 12 are classified as MANUAL_EVIDENCE_REQUIRED with justifications of the form: "This requirement is satisfied by the `<skill-name>` skill workflow (a Claude Code skill YAML); the [behavioral contract] is defined in the skill YAML/prompt, not a single annotatable Python function."

**Assessment of honesty:** These classifications are HONEST. The skills in question are YAML-based Claude Code skill definitions that drive agent interactions. They genuinely do not have a single Python function that implements the obligation -- the "implementation" is the skill prompt plus the agent's behavior. The `MarkdownHtmlCommentAdapter` already handles `<!-- implements: -->` in markdown files, so in principle the SKILL.md files could carry HTML-comment annotations. However, the SKILL.md annotation would point at the whole skill file, not at a specific function -- which is structurally different from the Python annotation model. The v0.2.0 retrospective correctly identifies this as a v0.3.0 policy decision.

**Concerns:**

1. Of the 30 gap REQs, 15 are MANUAL_EVIDENCE_REQUIRED (all skills), 8 are MISSING (with justifications explaining that annotations exist but path-based lookup failed), 5 are unlabeled (I did not verify all 30), and 2 are CONFIGURATION_ARTIFACT. The 8 MISSING REQs with "annotations present but path matching failed" justifications are concerning -- they suggest the measurement methodology has a residual path-resolution issue that the Task 36A retrofit did not fully close. The justifications are honest (they explicitly say "should resolve once path matching is confirmed"), but they leave open whether the annotations actually do resolve in the final measurement. The acceptance metrics say 42/44 are covered post-retrofit, so presumably the path issue was fixed for most of them. But the spec-level justifications were not updated after the fix.

2. MANUAL_EVIDENCE_REQUIRED as a permanent classification for skill-shaped obligations is an open policy question. In a real audit, an assessor might ask: "Where is the evidence that this skill actually does what REQ-assured-skills-003 says it does?" The answer would be: "Run the skill and observe its behavior." This is valid evidence in agile contexts but may not satisfy all regulatory frameworks. v0.3.0 should make this a documented policy decision.

---

## Q5. F-010 Closure: REQ-Quality Discipline

**Verdict: AGREE-WITH-CONCERNS**

The 10 inline rewrites genuinely shifted the highest-impact REQs toward capability-shaped form. The 6 deferrals are honest about their rationale. But the linter is advisory-only and the corpus still has structural quality variance.

**Comparison of rewritten vs. deferred REQs:**

*Rewritten (high quality):*
- REQ-assured-export-formats-001 (rewritten): "Auditors working under DO-178C MUST be able to produce a Requirements Traceability Matrix from project artefacts in the standard-prescribed four-column format..." -- Opens with WHO (auditors), WHAT (produce an RTM), WHY (so it can be submitted without manual reformatting). This is genuinely capability-shaped.
- REQ-assured-traceability-validators-004 (rewritten): "The Assured bundle MUST detect malformed or dangling `# implements:` annotations before a phase gate..." -- Opens with WHO (the bundle), WHAT (detect malformed annotations), WHY (so broken annotations cannot silently corrupt the traceability graph). Capability-shaped.

*Deferred drifters (still function-shaped):*
- REQ-assured-decomposition-validators-002: "`code_annotation_maps_to_module` SHALL report a blocking error..." -- Opens with a Python function name in subject position. This is function-shaped.
- REQ-assured-decomposition-validators-003: "`visibility_rule_enforcement` SHALL emit blocking errors..." -- Same pattern.
- REQ-programme-skills-003: "The `phase-gate` skill SHALL invoke the corresponding gate function..." -- Opens with a skill name (borderline acceptable) but "invoke the corresponding gate function" reveals internal dispatch.
- REQ-programme-substrate-001: "The spec parser SHALL deserialise a phase spec file into a structured `ParsedSpec` object..." -- Implementation type leak (`ParsedSpec` object).

**Assessment:** The retrospective is correct that the deferred drifters are lower-priority than the regulated-industry exporters. The 10 rewrites targeted the REQs most likely to be read by a regulator (DO-178C, IEC 62304, ISO 26262, FDA DHF), which is the right prioritisation. The 6 deferrals are all internal-validator REQs with lower regulatory exposure.

**The linter (`check-req-quality.py`) is sound but limited:**
- It flags function-shaped openings (`^[a-z_][a-z0-9_]*\s*\(`) and implementation vocabulary ("function", "method") outside backticks
- It correctly strips backtick spans before vocabulary checks to avoid false positives on legitimate code references
- It handles inline code around identifiers (`` `my_func(x)` SHALL... ``)
- It does NOT flag the `ParsedSpec` type-leak pattern in REQ-programme-substrate-001, because that REQ opens with "The spec parser" (not a bare function name). A more sophisticated linter would flag type-name leaks, but this is reasonable for v0.2.0.

**Concern:** The linter is advisory-only (`return 1 if flags else 0` -- exit code, not wired into CI as a blocker). The retrospective notes it should be "wired into CI as a warning-only check at first, then promoted to a blocker once the corpus is clean." Until it is promoted, there is no automated enforcement preventing new function-shaped REQs from entering the corpus. v0.3.0 should wire it in.

---

## Q6. Phase G Hard-Gate Honesty

**Verdict: AGREE-WITH-CONCERNS**

The post-retrofit measurement is honest. The retrofit added real annotations and real typed-status fields. But the 68% -> 4.55% jump in a single task raises a process concern.

**The retrofit was real:**

1. 14 `# implements:` annotations were added to source functions across `code_index.py`, `export.py`, `ids.py`, and `traceability_validators.py`. I verified this by reading `export.py` -- lines 72, 120, 155, 200, 306, 326 all carry `# implements: DES-assured-export-formats-NNN` annotations. These are real annotations on real functions that genuinely implement the cited DES elements.

2. The `_is_trivial` widening (Protocol stubs and `pass`-only bodies) is justified: `_is_stub_body()` at decomposition.py lines 448-463 correctly detects `...` (Ellipsis) and `pass` bodies. These are non-substantive bodies that carry no implementation semantics.

3. The `**Evidence-Status:**` fields were added to all 30 gap REQs with specific justifications. I sampled 6 specs and all had coherent justifications explaining why the gap exists and what evidence form applies.

4. The measurement methodology was corrected (`Path.resolve()` throughout) and the full `EvidenceIndexRegistry` scan was used, correctly capturing HTML-comment evidence from SKILL.md files.

**Concerns:**

1. **The 68% -> 4.55% jump in a single retrofit task is a process smell, not a quality smell.** The annotations and typed statuses are real, but the fact that a single task (36A) could close 28 of 30 gap REQs suggests the v0.1.0 corpus was under-annotated from the start, not that the v0.2.0 tooling is insufficient. In a real regulated project, an auditor might ask: "If 14 annotations were missing, why were they missing? Were the implementations written without annotation discipline?" The answer is that v0.1.0 was a dogfood session where annotation discipline was not yet enforced. This is honest but it means the "audit-ready" claim applies to the tooling's capability, not to the corpus's inherent completeness.

2. **8 of the 30 gap REQs have MISSING status with justifications saying "annotation is present but path matching failed."** This is ambiguous: if the annotation IS present and the final measurement shows coverage, why is the Evidence-Status still MISSING rather than LINKED? The spec-level status fields appear to have been written during the retrofit based on the pre-fix state (before path resolution was corrected), and were not updated after the final measurement confirmed coverage. This is a documentation lag, not a substantive gap, but it would confuse an auditor reading the requirements-spec.md files.

3. **The acceptance metrics note that under the Protocol-stub-as-FP interpretation, the FAC FPR would be 8.0%, which MISSES the 5% gate.** The standard classification (Protocol stubs as TP) was used, but the note acknowledges the borderline. This is honest reporting, but it means the FAC gate passes by convention choice, not by comfortable margin.

---

## Summary

### Is v0.2.0 audit-ready?

**AGREE-WITH-CONCERNS.** The retrospective's claim holds with qualifications.

**What v0.2.0 delivers:**
- A genuine multi-format evidence model (`EvidenceIndexEntry` + 4 adapters) that closes the F-001 gap
- A language-neutral dependency-extractor interface with a real Python adapter and a meaningful proof adapter
- Correct indirect DES-mediated coverage semantics (F-008)
- A typed evidence-status mechanism that turns blank RTM cells into auditable classifications (F-009)
- 10 capability-shaped REQ rewrites targeting the highest-regulatory-exposure requirements
- A REQ-quality linter ready for CI integration
- All 6 Phase G hard gates passing with 0% noise/FPR rates

**What "audit-ready" means in context:**
The tooling is audit-ready: given a properly annotated corpus, the validators and exporters will produce structurally correct, regulator-facing traceability matrices with no unexplained gaps. This is a genuine and significant improvement over v0.1.0.

The corpus is NOT fully audit-ready: the dogfood corpus was retrofitted in a single task, 8 gap REQs have stale MISSING statuses despite having coverage, 15 skill REQs rely on an undocumented MANUAL_EVIDENCE_REQUIRED policy, and 6 REQs still have function-shaped openings.

### Hidden gaps the EPIC retrospective missed

1. **Stale Evidence-Status fields.** The 8 MISSING-status REQs whose justifications say "annotations are present but path matching failed" were not updated after path resolution was fixed. An auditor reading these specs would see MISSING where the measurement shows LINKED.

2. **No automated enforcement of REQ-quality discipline.** The linter exists but is not wired into CI or pre-push. New function-shaped REQs can enter the corpus unchecked.

3. **GenericRegexExtractor's coupling to PythonAstExtractor internals.** The Swift proof adapter instantiates `PythonAstExtractor()` to reuse path-resolution helpers. This is a code-level coupling that contradicts the interface's language-neutrality claim at the implementation level (even though the protocol interface itself is clean).

4. **MANUAL_EVIDENCE_REQUIRED as an undocumented policy.** The classification is used for 15 REQs but there is no documented policy decision on when it is appropriate, what evidence an auditor should expect in lieu of code annotations, or whether it is a permanent or transitional status. The retrospective mentions this as a v0.3.0 decision but does not flag it as a gap in the v0.2.0 audit-readiness claim.

### Single most important thing for v0.3.0

**Document and formalise the MANUAL_EVIDENCE_REQUIRED policy.** This classification covers 15 of 44 REQs (34% of the corpus). Without a documented policy that defines: (a) the criteria for when MANUAL_EVIDENCE_REQUIRED is an acceptable permanent status vs. a transitional placeholder, (b) what evidence form an auditor should expect for skill-shaped obligations, and (c) whether the `MarkdownHtmlCommentAdapter` should be extended to emit annotation evidence from SKILL.md files -- the audit-readiness claim has a 34% soft spot. The 6 deferred drifters and the CI linter integration are secondary to this.

---

## Gate verdicts summary

| Question | Verdict | Key finding |
|----------|---------|-------------|
| Q1. F-001 (evidence model) | AGREE | Real abstraction with 4 adapters; not a facade |
| Q2. F-007 (dependency extractor) | AGREE-WITH-CONCERNS | Protocol is language-neutral; Swift adapter is shallow but sufficient for interface validation; internal coupling concern |
| Q3. F-008 (indirect coverage) | AGREE | Correct one-hop model; no edge-case gaps found |
| Q4. F-009 (typed statuses) | AGREE-WITH-CONCERNS | Mechanism is real; MANUAL_EVIDENCE_REQUIRED policy is undocumented; 8 stale MISSING statuses |
| Q5. F-010 (REQ quality) | AGREE-WITH-CONCERNS | Right priorities; linter not yet enforced in CI |
| Q6. Phase G honesty | AGREE-WITH-CONCERNS | Retrofit is real; 68%->4.55% single-task jump is process smell; stale spec-level statuses |
| **Overall** | **AGREE-WITH-CONCERNS** | v0.2.0 tooling is audit-ready; corpus and policy documentation need v0.3.0 cleanup |

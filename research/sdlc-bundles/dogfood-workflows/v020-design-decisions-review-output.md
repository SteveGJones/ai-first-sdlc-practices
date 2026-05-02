# v0.2.0 Phase A Design Decisions — Architect Review

**Reviewer:** Solution Architect (independent)
**Date:** 2026-05-01
**Input:** docs/superpowers/specs/2026-05-01-v020-design-decisions.md

---

## Decision 1 — F-008 semantics: indirect DES-mediated coverage

**Verdict:** AGREE

The decision to treat a REQ as implementation-covered when at least one DES that `satisfies` it has valid evidence is well-grounded in the v0.1.0 codebase reality. Examining `decomposition.py:348-375`, the current `granularity_match` validator checks whether each REQ ID appears directly in the `cited_ids` set of code annotations. The Phase F dogfood proved this produces 100% noise (43/43 false positives, F-008) because all 18 Python annotations cite DES IDs exclusively — zero cite REQ IDs. The three-layer chain REQ -> DES -> CODE is already the established convention, visible in every annotated source file (e.g., `code_index.py:48` cites `DES-assured-code-index-001`, not its parent REQ).

The indirect DES-mediated model aligns the validator with: (a) the actual annotation convention, (b) the `satisfies:` graph already maintained in `ids.py:build_id_registry` (which captures DES -> REQ links via the `satisfies` field on `IdRecord`), and (c) the DO-178C RTM structure in `export.py:30-62` which already walks the REQ -> DES -> CODE chain (lines 53-56: it looks up DESes that satisfy each REQ, then looks up code that cites those DESes). The RTM exporter already implements the semantic model this decision codifies for the validator layer.

No downstream ambiguity remains. The decision coherently unifies F-001 (evidence sources), F-009 (typed evidence statuses), F-010 (REQ quality), and E2 (forward completeness) around a single contract: requirements express intent, designs bind intent to implementation evidence.

## Decision 2 — F-001 abstraction depth: full EvidenceIndexEntry registry

**Verdict:** AGREE-WITH-CONCERNS

The decision to build a full `EvidenceIndexEntry` abstraction with a file-type registry dispatch table is architecturally sound. The v0.1.0 `code_index.py` demonstrates the limitation clearly: `_IMPLEMENTS_RE` at line 28 is a single Python-comment regex (`^\s*#\s*implements:`), and `parse_code_annotations` (lines 45-84) only walks files matching this pattern. The `traceability_validators.py` duplicates this regex at line 165 with a slightly different `_IMPLEMENTS_RE` (using `re.MULTILINE`). F-001 quantified the gap: only 18 of 129 annotations (14%) were parsed because markdown HTML-comment annotations are invisible.

The proposed `EvidenceIndexEntry` dataclass with `(kind, source, line, cited_ids, terms, facts)` is a clean generalisation of the existing `CodeIndexEntry` at `code_index.py:34-42`. The `EvidenceKind` enum (`PYTHON_COMMENT`, `MARKDOWN_HTML_COMMENT`, `YAML_FRONTMATTER`, `SATISFIES_BY_EXISTENCE`) covers all four annotation carriers identified in the findings.

**Concerns:**

1. **Duplicate regex risk.** The existing `_IMPLEMENTS_RE` is defined in both `code_index.py:28` and `traceability_validators.py:165` with subtly different flags (`re.MULTILINE` in the validator, plain in the code indexer). The design decision does not explicitly state that the new abstraction consolidates these into one source of truth. If the registry dispatch table introduces a third copy, the duplicate-regex problem worsens. The plan-writer should ensure a single canonical regex per evidence kind, owned by the registry module.

2. **Migration path for `CodeIndexEntry` consumers.** `export.py` imports `CodeIndexEntry` directly (line 8) and uses it throughout all four RTM exporters. The transition from `CodeIndexEntry` to `EvidenceIndexEntry` must preserve backward compatibility or update all consumers in the same phase. The Q1 resolution (new `evidence_index.py` file) is sensible given `code_index.py` is already 200+ lines, but the consumer migration should be explicit in the Phase B plan.

Neither concern blocks the decision; both are implementation-planning details that Phase B should address.

## Decision 3 — F-007 interface shape: DependencyExtractor protocol

**Verdict:** AGREE

The `DependencyExtractor` protocol with `extract(source_paths, programs) -> List[ImportEdge]` is a clean fit. The `ImportEdge` dataclass already exists at `decomposition.py:244-249` with `from_module` and `to_module` fields, and `visibility_rule_enforcement` at lines 252-275 already consumes `List[ImportEdge]`. The interface shape is dictated by the existing validator contract — the protocol formalises what the validator already expects.

The decision to make the Python adapter (`PythonAstExtractor`) the production deliverable while keeping the non-Python proof adapter fixture-backed is pragmatic. The recovery plan (drop the proof adapter if the interface proves Python-shaped, defer to v0.3.0) is correctly scoped as a stretch deliverable.

The `language: str` field on the protocol is sufficient for dispatch without over-engineering. The `Decomposition` parameter in `extract()` gives the adapter access to module paths for resolving imports to owning modules, which is exactly what `visibility_rule_enforcement` needs (it checks edges against `decomp.visibility` rules).

No hidden decisions here. The interface is minimal, grounded in the existing type, and the validator contract does not need to change.

## Decision 4 — E2 forward-completeness validator scope

**Verdict:** AGREE-WITH-CONCERNS

The decision to walk all public functions (no leading underscore) in source files declared in `programs.yaml` paths, with exclusions for dunder methods, single-line getters/setters, test fixtures, and `@property` with docstring-only bodies, is a reasonable starting point. The acceptance criterion of 5% or lower false-positive rate on the dogfood corpus provides a concrete gate.

**Concerns:**

1. **"Non-trivial" boundary is under-specified for edge cases.** The exclusion list covers the obvious cases but does not address: (a) dataclass-generated methods (which are public but not authored by the developer), (b) protocol/ABC abstract methods (which declare intent but have no implementation body — the implementation is in a subclass), (c) `__init__` methods (excluded by the dunder rule, but `__init__` is often the most important function to annotate in a regulated context since it establishes invariants). The 5% false-positive gate will catch these empirically, but the plan-writer should anticipate that the exclusion list may need 1-2 additions during Phase C based on dogfood results.

2. **Scope is Python-only.** The decision implicitly assumes Python source files (it references `@property`, dunder methods, `**/test_*.py`). For v0.2.0 this is correct (Python adapter only), but the validator's exclusion rules are language-specific. If v0.3.0 adds Swift/Java support, the forward-completeness validator will need language-specific exclusion profiles. This is not a v0.2.0 blocker but should be noted as a known limitation.

3. **Interaction with Decision 1 (F-008 indirect coverage).** The forward-completeness validator checks "every public function has an annotation." But under Decision 1, coverage flows through DES, not directly from REQ to code. A function annotated with `# implements: DES-foo-001` satisfies both the forward-completeness check (it has an annotation) and the indirect REQ coverage check (the DES satisfies a REQ). This is coherent — but the addendum should state explicitly that the forward-completeness validator checks for the *existence* of any `# implements:` annotation, not specifically a REQ-level one. The current wording ("checks each has `# implements:`") is correct but could be misread.

None of these block the decision. The 5% gate is the correct safety valve.

## Decision 5 — D1 spec_parser skip-rule scope

**Verdict:** AGREE

The decision to skip all three (blockquotes, inline code, HTML comments) uniformly across both `programme.spec_parser` and `assured.ids.build_id_registry` is correct and low-risk.

Examining `ids.py:89-131`, `build_id_registry` currently skips only fenced code blocks (lines 117-120: toggling `in_code_block` on triple-backtick lines). It does not skip blockquotes, inline code, or HTML comments. This means a line like `> REQ-foo-001 is discussed in the literature` would have `REQ-foo-001` extracted as a declared ID via `_HEADING_RE` only if it starts with `###`, which blockquotes don't — so the heading regex provides some natural protection for blockquotes. However, inline code (`` `REQ-foo-001` ``) within a heading line *would* match `_HEADING_RE`, and HTML comments (`<!-- REQ-foo-001 -->`) could match `_REF_ID_RE` in the satisfies parser.

The Q4 resolution (also skip code blocks inside markdown tables) is consistent and adds minimal effort.

The risk of regression is low: the skip-rule extension is additive (more things are skipped, never fewer), so existing valid extractions are unaffected. Any test fixture that currently embeds IDs in blockquotes/inline-code/HTML-comments as *intentional declarations* would break, but such fixtures would represent the exact false-positive scenario D1 was filed to prevent.

## Decision 6 — F-002/F-003 fit with EvidenceIndexEntry

**Verdict:** AGREE

The subsumption of both F-002 and F-003 into the `EvidenceIndexEntry` abstraction is clean and avoids introducing separate mechanisms.

**F-002 (named anchors/sections):** The `programs.yaml` `paths_sections:` field declaring named anchor regions per file is a sound alternative to arbitrary line ranges. The addendum correctly rejects line ranges ("they rot too easily under refactoring"). The existing `Module` dataclass at `decomposition.py:17-22` has only `paths: List[str]` — extending with an optional `paths_sections` field is backward-compatible (existing YAML files without the field continue to work). The PythonComment and MarkdownHtmlComment adapters checking anchor membership during scanning is a natural extension of the evidence-kind dispatch table from Decision 2.

**F-003 (satisfies-by-existence):** The `SATISFIES_BY_EXISTENCE` evidence kind with `line: None` and YAML frontmatter as the evidence carrier directly addresses the category error described in F-003. The Phase F finding at lines 36-41 of the findings document describes the problem precisely: CONSTITUTION.md "IS the artefact satisfying a requirement" and the annotation model had no concept for this. A new `EvidenceKind` variant is the minimal-surface-area solution.

The fit is coherent with Decision 2 (both are evidence kinds in the registry) and Decision 1 (both produce `EvidenceIndexEntry` records that can satisfy a DES, which in turn satisfies a REQ). No separate mechanism is needed.

---

## Summary

### Is the Phase A exit criterion met?

**Yes, with one qualification.** The exit criterion states: "no downstream semantic decision remains open — Phases B-G must not relitigate any of the six decisions." All six decisions are substantively decided and internally coherent. The concerns raised on Decisions 2 and 4 are implementation-planning details (duplicate regex consolidation, `CodeIndexEntry` migration path, exclusion list edge cases) that can be resolved within the decided framework without re-opening the semantic choices. No decision contradicts another; the F-008 indirect-coverage model (Decision 1) is the load-bearing choice and it aligns cleanly with the evidence abstraction (Decision 2), the validator scope (Decision 4), and the subsumption of F-002/F-003 (Decision 6).

The one qualification: **Decision 4's interaction with Decision 1 should be made explicit in the addendum** — specifically, that the forward-completeness validator checks for the existence of *any* `# implements:` annotation (regardless of whether it cites a REQ or DES ID), and that REQ-level coverage flows indirectly through Decision 1's DES-mediated model. This is implied but not stated. If a Phase C implementer misreads Decision 4 as requiring REQ-level annotations on every function, it would contradict Decision 1 and force relitigation. A single clarifying sentence prevents this.

### Are there hidden decisions the addendum missed that could force relitigation mid-implementation?

Two potential hidden decisions identified:

1. **Evidence conflict resolution.** When multiple `EvidenceIndexEntry` records exist for the same DES (e.g., a Python comment annotation AND a YAML frontmatter declaration), which one takes precedence? The addendum does not address this. In practice, for Decision 1's indirect coverage model, it likely does not matter (any evidence suffices), but for Decision 2's typed evidence statuses on the RTM exporter (F-009: `linked / missing / not_applicable / manual_evidence_required / configuration_artifact`), conflicting evidence types for the same DES could produce ambiguous RTM cells. The plan-writer should define a merge/priority rule. This is unlikely to force relitigation of the six decisions but could cause a 0.5-1 day pause in Phase B if not anticipated.

2. **`annotation_format_integrity` scope expansion.** The existing validator at `traceability_validators.py:169-194` only checks Python files (it uses `_IMPLEMENTS_RE` which matches Python comments). When Decision 2 introduces markdown HTML-comment and YAML frontmatter evidence kinds, `annotation_format_integrity` must be updated to validate those formats too. This is an implementation detail, not a semantic decision — but the validator currently has its own `_IMPLEMENTS_RE` copy (line 165) that would need to be replaced with the registry-based approach. If not planned for, this could surface as a regression in Phase C when the new evidence kinds are indexed but not validated.

Neither hidden decision is severe enough to block Phase A closure. Both are implementation-level concerns that the Phase B/C plan-writer should address explicitly. The six semantic decisions are stable and should not require relitigation.

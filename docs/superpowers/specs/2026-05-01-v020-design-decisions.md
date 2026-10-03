# v0.2.0 Phase A Design Decisions Addendum

**Source spec:** `docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md`
**Phase:** A
**Status:** Confirmed (architect review complete — 2026-05-01, all 6 decisions agreed or agreed-with-concerns)

---

## Decision 1 — F-008 semantics: indirect DES-mediated coverage (CONFIRMED from spec)

A REQ is implementation-covered when at least one DES that `satisfies` it has valid evidence (any `EvidenceIndexEntry`). The architect review's role is to validate this aligns the F-001/F-009/F-010/E2 model coherently. Architect verdict: AGREE — the indirect DES-mediated model aligns with the actual annotation convention (all 18 v0.1.0 Python annotations cite DES IDs, not REQ IDs), the `satisfies:` graph in `ids.py`, and the DO-178C RTM exporter in `export.py` which already walks the REQ→DES→CODE chain; the decision coherently unifies F-001, F-009, F-010, and E2 around a single contract.

## Decision 2 — F-001 abstraction depth: full EvidenceIndexEntry registry (CONFIRMED from spec)

`EvidenceIndexEntry` is a dataclass with fields `(kind: EvidenceKind, source: str, line: Optional[int], cited_ids: List[str], terms: List[str], facts: List[str])`. `EvidenceKind` enum: `PYTHON_COMMENT`, `MARKDOWN_HTML_COMMENT`, `YAML_FRONTMATTER`, `SATISFIES_BY_EXISTENCE`. The registry is a dispatch table from file-extension/path-pattern to adapter. Architect verdict: AGREE-WITH-CONCERNS — the abstraction cleanly generalises `CodeIndexEntry` and the `EvidenceKind` enum covers all four annotation carriers. Concerns: (1) duplicate `_IMPLEMENTS_RE` in `code_index.py` and `traceability_validators.py` must be consolidated into a single source of truth in the registry module — the new abstraction must not introduce a third copy; (2) `export.py` imports `CodeIndexEntry` directly and all four RTM exporters need explicit migration to `EvidenceIndexEntry` in Phase B. Resolution: accepted as Phase B planning items; neither blocks Phase A closure.

## Decision 3 — F-007 interface shape

`DependencyExtractor` protocol:
```python
class DependencyExtractor(Protocol):
    language: str  # "python", "swift", "javascript", etc.
    def extract(self, source_paths: List[Path], programs: Decomposition) -> List[ImportEdge]: ...
```
The Python adapter (`PythonAstExtractor`) is the v0.2.0 production deliverable. The non-Python proof adapter (Phase C) is fixture-backed only. Architect verdict: AGREE — the interface is minimal and grounded in the existing `ImportEdge` type at `decomposition.py:244-249`; `visibility_rule_enforcement` already consumes `List[ImportEdge]`, so the protocol formalises the existing validator contract without changes; the `Decomposition` parameter gives adapters access to module paths for import resolution.

## Decision 4 — E2 forward-completeness validator scope

The validator walks all public functions (no leading underscore) in source files declared in `programs.yaml` paths. "Non-trivial" exclusions:
- dunder methods (`__*__`)
- single-line getters/setters (one-line property accessors)
- test fixtures (functions in files matching `**/test_*.py` or `**/conftest.py`)
- functions decorated with `@property` having a docstring-only or single-line body
Acceptance criterion: ≤5% false-positive rate on the v0.2.0 verification dogfood corpus. **Clarification (from architect review):** this validator checks for the *existence* of any `# implements:` annotation — it does not require the annotation to cite a REQ-level ID. REQ-level coverage flows indirectly through Decision 1's DES-mediated model; a function annotated `# implements: DES-foo-001` satisfies both this check and the indirect REQ coverage check. Phase C implementers must not misread this decision as requiring REQ-level annotations on every function. Architect verdict: AGREE-WITH-CONCERNS — the exclusion list covers the obvious cases; concerns: (1) dataclass-generated methods, protocol/ABC abstract methods, and `__init__` are not explicitly addressed — the 5% gate will catch empirically; (2) exclusion rules are Python-specific (v0.2.0 only; v0.3.0 will need language-specific profiles); (3) the Decision 1/Decision 4 interaction wording above was added as an inline fix per the architect's recommendation. Resolution: concern (1) accepted as Phase C empirical refinement; concern (2) noted as v0.3.0 known limitation; concern (3) fixed inline in this addendum.

## Decision 5 — D1 spec_parser skip-rule scope

Skip ALL three: blockquotes (`> ...`), inline code (`` `id-token` ``), HTML comments (`<!-- ... -->`). Apply uniformly across `programme.spec_parser` and `assured.ids.build_id_registry`. Architect verdict: AGREE — the extension is additive (more things are skipped, never fewer), so existing valid extractions are unaffected; the skip-rule extension correctly addresses the false-positive extraction paths identified in the codebase (`ids.py:89-131` currently only skips fenced code blocks); Q4 (skip code blocks inside markdown tables) is consistent and adds minimal effort.

## Decision 6 — F-002/F-003 fit with EvidenceIndexEntry

Both subsume into the new abstraction:
- F-002 (named anchors/sections): `programs.yaml` `paths_sections:` field declares named anchor regions per file. The PythonComment / MarkdownHtmlComment adapters check anchor membership when scanning.
- F-003 (satisfies-by-existence): `EvidenceKind.SATISFIES_BY_EXISTENCE` is a kind with `line: None` and the entry's existence in YAML frontmatter is the evidence. No code-comment scanning needed.
Architect verdict: AGREE — both subsume cleanly into the `EvidenceIndexEntry` abstraction: F-002 maps to anchor-region scoping in the evidence-kind dispatch (backward-compatible `paths_sections:` extension to `decomposition.py:Module`), F-003 maps to `SATISFIES_BY_EXISTENCE` kind (directly addresses the category error in the v0.1.0 annotation model); both are coherent with Decisions 1 and 2 and require no separate mechanism.

---

## Open questions deferred to plan-writing (Q1-Q4 from spec)

| # | Question | Resolution |
|---|---|---|
| Q1 | EvidenceIndexEntry location | Decided: new file `evidence_index.py` (file-size constraints; `code_index.py` already at 200+ lines after v0.1.0) |
| Q2 | EvidenceStatus dataclass vs enum | Decided: enum (5 values, no fields beyond identity) |
| Q3 | Verification dogfood in CI? | Decided: manual for v0.2.0; CI integration deferred to v0.3.0 |
| Q4 | Skip code blocks inside markdown tables? | Decided: yes (consistency with rule for fenced code blocks; minor effort) |

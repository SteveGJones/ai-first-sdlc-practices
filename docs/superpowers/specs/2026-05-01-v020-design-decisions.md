# v0.2.0 Phase A Design Decisions Addendum

**Source spec:** `docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md`
**Phase:** A
**Status:** Draft (pre-architect-review) → Confirmed (post-architect-review)

---

## Decision 1 — F-008 semantics: indirect DES-mediated coverage (CONFIRMED from spec)

A REQ is implementation-covered when at least one DES that `satisfies` it has valid evidence (any `EvidenceIndexEntry`). The architect review's role is to validate this aligns the F-001/F-009/F-010/E2 model coherently. Architect verdict: <to be filled at review close>.

## Decision 2 — F-001 abstraction depth: full EvidenceIndexEntry registry (CONFIRMED from spec)

`EvidenceIndexEntry` is a dataclass with fields `(kind: EvidenceKind, source: str, line: Optional[int], cited_ids: List[str], terms: List[str], facts: List[str])`. `EvidenceKind` enum: `PYTHON_COMMENT`, `MARKDOWN_HTML_COMMENT`, `YAML_FRONTMATTER`, `SATISFIES_BY_EXISTENCE`. The registry is a dispatch table from file-extension/path-pattern to adapter. Architect verdict: <to be filled>.

## Decision 3 — F-007 interface shape

`DependencyExtractor` protocol:
```python
class DependencyExtractor(Protocol):
    language: str  # "python", "swift", "javascript", etc.
    def extract(self, source_paths: List[Path], programs: Decomposition) -> List[ImportEdge]: ...
```
The Python adapter (`PythonAstExtractor`) is the v0.2.0 production deliverable. The non-Python proof adapter (Phase C) is fixture-backed only. Architect verdict: <to be filled>.

## Decision 4 — E2 forward-completeness validator scope

The validator walks all public functions (no leading underscore) in source files declared in `programs.yaml` paths. "Non-trivial" exclusions:
- dunder methods (`__*__`)
- single-line getters/setters (one-line property accessors)
- test fixtures (functions in files matching `**/test_*.py` or `**/conftest.py`)
- functions decorated with `@property` having a docstring-only or single-line body
Acceptance criterion: ≤5% false-positive rate on the v0.2.0 verification dogfood corpus. Architect verdict: <to be filled>.

## Decision 5 — D1 spec_parser skip-rule scope

Skip ALL three: blockquotes (`> ...`), inline code (`` `id-token` ``), HTML comments (`<!-- ... -->`). Apply uniformly across `programme.spec_parser` and `assured.ids.build_id_registry`. Architect verdict: <to be filled>.

## Decision 6 — F-002/F-003 fit with EvidenceIndexEntry

Both subsume into the new abstraction:
- F-002 (named anchors/sections): `programs.yaml` `paths_sections:` field declares named anchor regions per file. The PythonComment / MarkdownHtmlComment adapters check anchor membership when scanning.
- F-003 (satisfies-by-existence): `EvidenceKind.SATISFIES_BY_EXISTENCE` is a kind with `line: None` and the entry's existence in YAML frontmatter is the evidence. No code-comment scanning needed.
Architect verdict: <to be filled>.

---

## Open questions deferred to plan-writing (Q1-Q4 from spec)

| # | Question | Resolution |
|---|---|---|
| Q1 | EvidenceIndexEntry location | Decided: new file `evidence_index.py` (file-size constraints; `code_index.py` already at 200+ lines after v0.1.0) |
| Q2 | EvidenceStatus dataclass vs enum | Decided: enum (5 values, no fields beyond identity) |
| Q3 | Verification dogfood in CI? | Decided: manual for v0.2.0; CI integration deferred to v0.3.0 |
| Q4 | Skip code blocks inside markdown tables? | Decided: yes (consistency with rule for fenced code blocks; minor effort) |

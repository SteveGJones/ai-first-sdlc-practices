# v0.2.0 sdlc-assured Audit-Readiness + Carry-Forward Closure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver `sdlc-assured` v0.2.0 — make Method 2 audit-ready and clear all 18 v0.1.0 deferred-debt items per the EPIC #188 design spec.

**Architecture:** Seven-phase EPIC mirroring #178's shape. Phase A locks all six design decisions (with containerised architect review at close). Phases B-F implement against those locked decisions in dependency order: evidence model first (B), then validators that depend on it (C), then ID/REQ format (D), quality discipline (E), audit closure (F). Phase G verifies via baseline → injected-defect tests → acceptance metric deltas with hard gates. Final containerised architect review provides audit-readiness sign-off.

**Tech Stack:** Python 3.10+ (existing `sdlc-assured` modules); markdown (REQ/DES/TEST artefacts); YAML (`programs.yaml`, frontmatter); pytest with `from __future__ import annotations`; black + flake8; existing `EvidenceIndexEntry`-shaped abstractions per the architect-review-driven design.

**Branch:** `feature/sdlc-assured-v020` (already on it; design spec landed at `49599ab`). EPIC #188. No-PR-until-EPIC-complete.

**Pre-committed design directions (locked at spec approval, do not relitigate in implementation):**
- F-008 semantics: indirect DES-mediated coverage. A REQ is implementation-covered when at least one `satisfies`-linked DES has valid evidence.
- F-001 abstraction depth: full `EvidenceIndexEntry` registry (not regex extension).
- F-002 scoping: named anchors/sections only, no line ranges.
- F-005: split severity-mixed REQs when severity differs materially; parentheticals OK for minor nuance.

**Phase A exit criterion (hard gate):** no downstream semantic decision remains open. If a Phase B-G implementation surfaces a decision Phase A missed, escalate to user; do NOT decide-in-code-review.

---

## File structure

### New files

| Path | Responsibility |
|---|---|
| `docs/superpowers/specs/2026-05-XX-v020-design-decisions.md` | Phase A design-decisions addendum (six decisions resolved + architect review verdict) |
| `plugins/sdlc-assured/scripts/assured/evidence_index.py` | `EvidenceIndexEntry` dataclass + `EvidenceKind` enum + adapter protocol; replaces `code_index.py`'s monolithic parser |
| `plugins/sdlc-assured/scripts/assured/evidence_adapters.py` | File-type adapters: PythonComment, MarkdownHtmlComment, YamlFrontmatter, SatisfiesByExistence (F-003) |
| `plugins/sdlc-assured/scripts/assured/dependency_extractor.py` | `DependencyExtractor` protocol + `PythonAstExtractor` + non-Python proof adapter (F-007) |
| `plugins/sdlc-assured/scripts/assured/evidence_status.py` | `EvidenceStatus` enum (`linked` / `missing` / `not_applicable` / `manual_evidence_required` / `configuration_artifact`) for F-009 |
| `plugins/sdlc-assured/scripts/assured/requirement_metadata.py` | `RequirementMetadata` dataclass + `build_requirement_metadata_registry` — per-REQ `evidence_status` / `justification` / `related` from inline `**Field:**` lines (P1.2 + P2.2 plan-review fixes; foundation for F-006 + F-009) |
| `tests/test_assured_evidence_index.py` | Tests for evidence_index + adapters |
| `tests/test_assured_dependency_extractor.py` | Tests for dependency_extractor + Python adapter + non-Python proof |
| `tests/test_assured_evidence_status.py` | Tests for typed evidence statuses on the 4 regulatory exporters |
| `tests/test_assured_requirement_metadata.py` | Tests for the metadata registry (per-REQ frontmatter capture) |
| `tests/test_assured_validators_v020.py` | Tests for new/rewritten validators (granularity_match indirect, orphan_ids widened, forward_annotation_completeness, requirements_gate non-empty) |
| `tests/fixtures/v020-verification/` | Injected-defect fixtures for Phase G sub-stage 2 (one fixture per seeded defect) |
| `research/v020-baseline-metrics.md` | Phase G sub-stage 1 baseline measurement |
| `research/v020-acceptance-metrics.md` | Phase G sub-stage 3 final measurement (vs baseline) |
| `retrospectives/188-v020-assured-improvements.md` | EPIC #188 retrospective scaffold |

### Modified files

| Path | Modification |
|---|---|
| `plugins/sdlc-assured/scripts/assured/code_index.py` | Refactor to use `EvidenceIndexEntry` + adapters. Keep `render_code_index` and `render_spec_findings` as renderers. Remove `_IMPLEMENTS_RE` (moved to PythonComment adapter) |
| `plugins/sdlc-assured/scripts/assured/decomposition.py` | Rewrite `granularity_match` for indirect DES-mediated coverage (F-008); add new `forward_annotation_completeness` (E2) |
| `plugins/sdlc-assured/scripts/assured/traceability_validators.py` | Widen `orphan_ids` to all kinds (E1); add `requirements_gate_non_empty_content` helper for D2 |
| `plugins/sdlc-assured/scripts/assured/ids.py` | `remap_ids` multiple-prefix handling with warn-on-overlap (E3) |
| `plugins/sdlc-assured/scripts/assured/export.py` | All 4 regulatory exporters use `EvidenceStatus` instead of bare `—` placeholders (F-009) |
| `plugins/sdlc-programme/scripts/programme/spec_parser.py` | Skip-rules extended to blockquotes (`>`), inline code (`` ` ``), HTML comments (`<!-- -->`) (D1) |
| `plugins/sdlc-programme/scripts/programme/gates.py` | `requirements_gate` non-empty-content check (D2) |
| `plugins/sdlc-assured/templates/programs.yaml` | Add optional `paths_sections:` field for named-anchor scoping (F-002) |
| `plugins/sdlc-assured/templates/requirements-spec-assured.md` | Add optional `related:` field example to frontmatter (F-006) |
| `plugins/sdlc-assured/skills/phase-review/SKILL.md` (under Programme not Assured — verify) + plugin mirror | Graceful fallback for absent agent plugins (D3) |
| `docs/specs/assured-decomposition-validators/requirements-spec.md` | Rewrite REQ-001 at user-visible-capability level (F-010) |
| `docs/specs/assured-traceability-validators/requirements-spec.md` | Rewrite REQ-003 at user-visible-capability level (F-010); split severity-mixed REQ-001 if needed (F-005) |
| `docs/specs/assured-skills/requirements-spec.md` | Rewrite REQ-001 at user-visible-capability level (F-010) |
| `docs/specs/assured-substrate/design-spec.md` | Remove inline `<!-- implements: -->` annotation from DES-001 (F1 convention violation) |
| `research/phase-f-req-inventory.md` | Wording fix on programme-validators row (F-004) |

### Files NOT modified (boundary discipline)

- v0.1.0 fixture artefacts at `tests/fixtures/assured/feature-sample/` — they are the regression-test surface
- v0.1.0 retrospectives — historical record
- `programs.yaml` (the dogfood instance) — unchanged unless paths_sections is added experimentally for F-002 demo

---

## Phase A — Design decisions

### Task 1: Author Phase A design-decisions addendum

**Files:**
- Create: `docs/superpowers/specs/2026-05-XX-v020-design-decisions.md` (use today's date)

- [ ] **Step 1: Write the addendum**

The addendum confirms / refines the four pre-committed directions and resolves the two open Phase A decisions (F-007 interface shape, E2 scope, D1 implementation, F-002/F-003 fit). Use this exact structure:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-05-XX-v020-design-decisions.md  # use today's date
git commit -m "feat(v020): Phase A design-decisions addendum (six decisions, draft pre-architect-review) (Phase A task 1)"
```

---

### Task 2: Containerised architect review of design-decisions addendum

**Files:**
- Create: `research/sdlc-bundles/dogfood-workflows/v020-design-decisions-review.md` (workflow command brief)
- Create: `research/sdlc-bundles/dogfood-workflows/v020-design-decisions-review.yaml` (workflow node)
- Create: `research/sdlc-bundles/dogfood-workflows/v020-design-decisions-review-output.md` (architect output)

- [ ] **Step 1: Write the workflow files**

Same structure as #178's Phase E task 41. The command brief dispatches `sdlc-team-common:solution-architect` with this prompt:

```
You are conducting an INDEPENDENT review of the v0.2.0 Phase A design-decisions
addendum at docs/superpowers/specs/2026-05-XX-v020-design-decisions.md.

Required reading:
- docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md (EPIC scope)
- The addendum itself
- research/phase-f-dogfood-findings.md (the 10 findings the design decisions resolve)
- The relevant v0.1.0 modules: plugins/sdlc-assured/scripts/assured/{code_index,decomposition,traceability_validators,ids,export}.py

Answer 6 questions, one per design decision in the addendum. For each: AGREE / AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK with rationale.

Then SUMMARY: is the Phase A exit criterion met (no downstream semantic
decision remains open)? Are there hidden decisions the addendum missed?

End by writing your verbatim review to:
research/sdlc-bundles/dogfood-workflows/v020-design-decisions-review-output.md

Read-only review. Do NOT modify code or specs.
```

Workflow YAML uses `image: sdlc-worker:decomposition-review`, timeout `600000`.

- [ ] **Step 2: Run the workflow**

```bash
/sdlc-workflows:workflows-run v020-design-decisions-review
```

- [ ] **Step 3: Triage findings**

For each AGREE-WITH-CONCERNS or DISAGREE: decide inline-fix-now (update the addendum + re-run review) vs accept-the-concern (document why) vs escalate-to-user. NEEDS-REWORK = STOP and escalate.

- [ ] **Step 4: Update the addendum with architect verdicts**

Replace each `<to be filled>` placeholder with the architect's verdict.

- [ ] **Step 5: Commit**

```bash
git add research/sdlc-bundles/dogfood-workflows/v020-design-decisions-review.* \
        docs/superpowers/specs/2026-05-XX-v020-design-decisions.md
git commit -m "review(v020): Phase A architect review + addendum updated with verdicts (Phase A task 2)"
```

---

### Task 3: Phase A close — exit-criterion check

**Files:** none (this is a checkpoint commit only)

- [ ] **Step 1: Verify all six decisions confirmed**

Read the addendum. Confirm each `<to be filled>` placeholder is replaced. Confirm no decision is in NEEDS-REWORK state.

- [ ] **Step 2: Verify Phase A exit criterion**

The exit criterion is "no downstream semantic decision remains open." Review Phases B-G of the EPIC spec; for each phase, ask "is there a semantic choice this phase makes that should have been settled in Phase A?" If yes, return to Phase A and add a Decision N.

- [ ] **Step 3: Commit a marker**

```bash
git commit --allow-empty -m "phase(v020): Phase A close — all six decisions confirmed; exit criterion met (Phase A task 3)"
```

---

## Phase B — Evidence model + parser

### Task 4: EvidenceIndexEntry + EvidenceKind enum

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/evidence_index.py`
- Create: `tests/test_assured_evidence_index.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for assured.evidence_index — abstraction for the v0.2.0 file-type registry."""

from sdlc_assured_scripts.assured.evidence_index import (
    EvidenceIndexEntry,
    EvidenceKind,
)


def test_evidence_index_entry_construction() -> None:
    entry = EvidenceIndexEntry(
        kind=EvidenceKind.PYTHON_COMMENT,
        source="src/auth/login.py",
        line=42,
        cited_ids=["DES-auth-005"],
        terms=["login", "auth"],
        facts=["Issues a session cookie on success"],
    )
    assert entry.kind == EvidenceKind.PYTHON_COMMENT
    assert entry.line == 42


def test_evidence_kind_enum_has_four_values() -> None:
    kinds = {k.name for k in EvidenceKind}
    assert kinds == {
        "PYTHON_COMMENT",
        "MARKDOWN_HTML_COMMENT",
        "YAML_FRONTMATTER",
        "SATISFIES_BY_EXISTENCE",
    }


def test_evidence_index_entry_satisfies_by_existence_has_no_line() -> None:
    entry = EvidenceIndexEntry(
        kind=EvidenceKind.SATISFIES_BY_EXISTENCE,
        source="CONSTITUTION.md",
        line=None,
        cited_ids=["REQ-programme-substrate-003"],
        terms=[],
        facts=["Constitution authority document"],
    )
    assert entry.line is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_assured_evidence_index.py -v 2>&1 | tail -5
```

Expected: ImportError on `evidence_index`.

- [ ] **Step 3: Write the module**

```python
"""EvidenceIndexEntry abstraction — v0.2.0 file-type registry foundation.

Replaces the v0.1.0 monolithic parse_code_annotations approach.
See docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md §3 Phase A decisions 2 + 6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EvidenceKind(Enum):
    """Kind of evidence carried by an EvidenceIndexEntry."""

    PYTHON_COMMENT = "python_comment"
    MARKDOWN_HTML_COMMENT = "markdown_html_comment"
    YAML_FRONTMATTER = "yaml_frontmatter"
    SATISFIES_BY_EXISTENCE = "satisfies_by_existence"


@dataclass(frozen=True)
class EvidenceIndexEntry:
    """One unit of implementation evidence pointing at one or more spec IDs."""

    kind: EvidenceKind
    source: str
    line: Optional[int]
    cited_ids: List[str]
    terms: List[str] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m pytest tests/test_assured_evidence_index.py -v 2>&1 | tail -5
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/evidence_index.py tests/test_assured_evidence_index.py
git commit -m "feat(v020): EvidenceIndexEntry + EvidenceKind enum (Phase B task 4)"
```

---

### Task 5: Adapter protocol + PythonComment adapter

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/evidence_index.py` — add `EvidenceAdapter` protocol
- Create: `plugins/sdlc-assured/scripts/assured/evidence_adapters.py` — adapter implementations
- Modify: `tests/test_assured_evidence_index.py` — add adapter tests

- [ ] **Step 1: Append adapter test**

```python
from pathlib import Path

from sdlc_assured_scripts.assured.evidence_adapters import (
    PythonCommentAdapter,
)


def test_python_comment_adapter_extracts_implements_lines(tmp_path: Path) -> None:
    f = tmp_path / "login.py"
    f.write_text(
        "def login(token):\n"
        "    # implements: DES-auth-005, REQ-auth-003\n"
        "    return token\n"
    )
    adapter = PythonCommentAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.PYTHON_COMMENT
    assert entries[0].line == 2
    assert entries[0].cited_ids == ["DES-auth-005", "REQ-auth-003"]


def test_python_comment_adapter_skips_non_python_files(tmp_path: Path) -> None:
    f = tmp_path / "README.md"
    f.write_text("# implements: DES-x-001\n")
    adapter = PythonCommentAdapter()
    assert list(adapter.extract([f], project_root=tmp_path)) == []
```

- [ ] **Step 2: Run test (will fail)**

```bash
python3 -m pytest tests/test_assured_evidence_index.py::test_python_comment_adapter_extracts_implements_lines -v
```

Expected: ImportError.

- [ ] **Step 3: Add adapter protocol to evidence_index.py**

Append to `evidence_index.py`:

```python
from pathlib import Path
from typing import Iterable, Protocol


class EvidenceAdapter(Protocol):
    """Protocol for file-type-specific evidence adapters."""

    file_extensions: tuple[str, ...]

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]: ...
```

- [ ] **Step 4: Implement PythonCommentAdapter in evidence_adapters.py**

```python
"""File-type adapters for the v0.2.0 EvidenceIndexEntry registry."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .evidence_index import EvidenceIndexEntry, EvidenceKind


_IMPLEMENTS_RE = re.compile(r"^\s*#\s*implements:\s*(?P<ids>.+)$")
_ID_TOKEN_RE = re.compile(
    r"\b((?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)


class PythonCommentAdapter:
    """Adapter for Python `# implements: <ID>` annotations."""

    file_extensions = (".py",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions:
                continue
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            for line_no, line in enumerate(text.splitlines(), start=1):
                m = _IMPLEMENTS_RE.match(line)
                if not m:
                    continue
                cited = _ID_TOKEN_RE.findall(m["ids"])
                yield EvidenceIndexEntry(
                    kind=EvidenceKind.PYTHON_COMMENT,
                    source=rel_path,
                    line=line_no,
                    cited_ids=cited,
                )
```

- [ ] **Step 5: Run tests pass**

```bash
python3 -m pytest tests/test_assured_evidence_index.py -v 2>&1 | tail -8
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/evidence_index.py \
        plugins/sdlc-assured/scripts/assured/evidence_adapters.py \
        tests/test_assured_evidence_index.py
git commit -m "feat(v020): EvidenceAdapter protocol + PythonCommentAdapter (Phase B task 5)"
```

---

### Task 6: MarkdownHtmlCommentAdapter (F-001 markdown gap fix)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/evidence_adapters.py`
- Modify: `tests/test_assured_evidence_index.py`

- [ ] **Step 1: Append failing test**

```python
from sdlc_assured_scripts.assured.evidence_adapters import MarkdownHtmlCommentAdapter


def test_markdown_html_comment_adapter_extracts_html_implements_lines(tmp_path: Path) -> None:
    f = tmp_path / "SKILL.md"
    f.write_text(
        "---\n"
        "name: example-skill\n"
        "---\n"
        "<!-- implements: DES-foo-001 -->\n"
        "\n"
        "# Skill body\n"
    )
    adapter = MarkdownHtmlCommentAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.MARKDOWN_HTML_COMMENT
    assert entries[0].cited_ids == ["DES-foo-001"]


def test_markdown_html_comment_adapter_ignores_h1_implements(tmp_path: Path) -> None:
    """An H1 heading literally named '# implements:' must NOT be treated as evidence."""
    f = tmp_path / "doc.md"
    f.write_text("# implements: REQ-x-001\n")
    adapter = MarkdownHtmlCommentAdapter()
    assert list(adapter.extract([f], project_root=tmp_path)) == []
```

- [ ] **Step 2: Run (fails)**, **Step 3: Implement**, **Step 4: Run (passes)** — appends to `evidence_adapters.py`:

```python
_HTML_IMPLEMENTS_RE = re.compile(r"<!--\s*implements:\s*(?P<ids>.+?)\s*-->")


class MarkdownHtmlCommentAdapter:
    """Adapter for markdown `<!-- implements: <ID> -->` HTML-comment annotations."""

    file_extensions = (".md",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions:
                continue
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            for line_no, line in enumerate(text.splitlines(), start=1):
                m = _HTML_IMPLEMENTS_RE.search(line)
                if not m:
                    continue
                cited = _ID_TOKEN_RE.findall(m["ids"])
                yield EvidenceIndexEntry(
                    kind=EvidenceKind.MARKDOWN_HTML_COMMENT,
                    source=rel_path,
                    line=line_no,
                    cited_ids=cited,
                )
```

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/evidence_adapters.py tests/test_assured_evidence_index.py
git commit -m "feat(v020): MarkdownHtmlCommentAdapter for F-001 markdown gap (Phase B task 6)"
```

---

### Task 7: YamlFrontmatterAdapter + SatisfiesByExistenceAdapter (F-003 governance docs)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/evidence_adapters.py`
- Modify: `tests/test_assured_evidence_index.py`

- [ ] **Step 1-4: TDD cycle**

Test:
```python
from sdlc_assured_scripts.assured.evidence_adapters import (
    YamlFrontmatterAdapter,
    SatisfiesByExistenceAdapter,
)


def test_yaml_frontmatter_adapter_extracts_implements_list(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text(
        "---\n"
        "implements:\n"
        "  - DES-foo-001\n"
        "  - DES-foo-002\n"
        "---\n"
        "# Body\n"
    )
    adapter = YamlFrontmatterAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.YAML_FRONTMATTER
    assert sorted(entries[0].cited_ids) == ["DES-foo-001", "DES-foo-002"]


def test_satisfies_by_existence_adapter_emits_one_entry_per_satisfies_id(tmp_path: Path) -> None:
    f = tmp_path / "CONSTITUTION.md"
    f.write_text(
        "---\n"
        "satisfies_by_existence:\n"
        "  - REQ-programme-substrate-003\n"
        "---\n"
        "# Constitution\n"
    )
    adapter = SatisfiesByExistenceAdapter()
    entries = list(adapter.extract([f], project_root=tmp_path))
    assert len(entries) == 1
    assert entries[0].kind == EvidenceKind.SATISFIES_BY_EXISTENCE
    assert entries[0].line is None
    assert entries[0].cited_ids == ["REQ-programme-substrate-003"]
```

Implementation (append to `evidence_adapters.py`):

```python
import yaml as _yaml


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from a markdown document. Returns None if no frontmatter."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return _yaml.safe_load(parts[1]) or {}
    except _yaml.YAMLError:
        return None


class YamlFrontmatterAdapter:
    """Adapter for `implements: [...]` in YAML frontmatter."""

    file_extensions = (".md",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions or not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            if not fm or "implements" not in fm:
                continue
            ids = fm["implements"]
            if not isinstance(ids, list):
                continue
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            yield EvidenceIndexEntry(
                kind=EvidenceKind.YAML_FRONTMATTER,
                source=rel_path,
                line=None,
                cited_ids=[str(x) for x in ids],
            )


class SatisfiesByExistenceAdapter:
    """Adapter for governance documents declaring `satisfies_by_existence: [...]` (F-003)."""

    file_extensions = (".md",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions or not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            if not fm or "satisfies_by_existence" not in fm:
                continue
            ids = fm["satisfies_by_existence"]
            if not isinstance(ids, list):
                continue
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            yield EvidenceIndexEntry(
                kind=EvidenceKind.SATISFIES_BY_EXISTENCE,
                source=rel_path,
                line=None,
                cited_ids=[str(x) for x in ids],
            )
```

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/evidence_adapters.py tests/test_assured_evidence_index.py
git commit -m "feat(v020): YAML frontmatter + satisfies-by-existence adapters (F-003) (Phase B task 7)"
```

---

### Task 8: EvidenceIndexRegistry — file-type dispatch

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/evidence_index.py` — add `EvidenceIndexRegistry` class
- Modify: `tests/test_assured_evidence_index.py`

- [ ] **Step 1-4: TDD cycle**

Test:
```python
from sdlc_assured_scripts.assured.evidence_index import EvidenceIndexRegistry


def test_registry_dispatches_python_and_markdown_files(tmp_path: Path) -> None:
    py = tmp_path / "a.py"
    py.write_text("def f():\n    # implements: DES-x-001\n    pass\n")
    md = tmp_path / "b.md"
    md.write_text("<!-- implements: DES-x-002 -->\n")
    registry = EvidenceIndexRegistry.with_default_adapters()
    entries = list(registry.scan([py, md], project_root=tmp_path))
    kinds = {e.kind for e in entries}
    assert EvidenceKind.PYTHON_COMMENT in kinds
    assert EvidenceKind.MARKDOWN_HTML_COMMENT in kinds
    assert {e for e in entries if e.cited_ids == ["DES-x-001"]}
    assert {e for e in entries if e.cited_ids == ["DES-x-002"]}
```

Implementation (append to `evidence_index.py`):

```python
class EvidenceIndexRegistry:
    """Dispatches files to file-type-specific evidence adapters."""

    def __init__(self, adapters: list[EvidenceAdapter]) -> None:
        self._adapters = list(adapters)

    @classmethod
    def with_default_adapters(cls) -> "EvidenceIndexRegistry":
        from .evidence_adapters import (
            PythonCommentAdapter,
            MarkdownHtmlCommentAdapter,
            YamlFrontmatterAdapter,
            SatisfiesByExistenceAdapter,
        )

        return cls(
            [
                PythonCommentAdapter(),
                MarkdownHtmlCommentAdapter(),
                YamlFrontmatterAdapter(),
                SatisfiesByExistenceAdapter(),
            ]
        )

    def scan(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for adapter in self._adapters:
            yield from adapter.extract(files, project_root)
```

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/evidence_index.py tests/test_assured_evidence_index.py
git commit -m "feat(v020): EvidenceIndexRegistry with file-type dispatch (Phase B task 8)"
```

---

### Task 9: Migrate code_index.py to use EvidenceIndexRegistry

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/code_index.py`
- Modify: `tests/test_assured_code_index.py` — confirm existing tests still pass

- [ ] **Step 1: Run existing tests baseline**

```bash
python3 -m pytest tests/test_assured_code_index.py -v 2>&1 | tail -5
```

Expected: existing v0.1.0 tests pass.

- [ ] **Step 2: Refactor `parse_code_annotations` to use the registry**

Replace `parse_code_annotations` body with:

```python
def parse_code_annotations(
    files: List[Path], project_root: Path
) -> List[CodeIndexEntry]:
    """Walk files via EvidenceIndexRegistry; convert PYTHON_COMMENT entries to CodeIndexEntry.

    v0.1.0 compatibility shim: returns CodeIndexEntry for backward compatibility with
    existing render_code_index calls. New code paths should use EvidenceIndexRegistry directly.
    """
    from .evidence_index import EvidenceIndexRegistry, EvidenceKind

    registry = EvidenceIndexRegistry.with_default_adapters()
    entries: List[CodeIndexEntry] = []
    for ev in registry.scan(files, project_root):
        if ev.kind != EvidenceKind.PYTHON_COMMENT:
            continue
        entries.append(
            CodeIndexEntry(
                file_path=ev.source,
                line=ev.line or 0,
                cited_ids=list(ev.cited_ids),
            )
        )
    return entries
```

- [ ] **Step 3: Run tests pass (regression check)**

```bash
python3 -m pytest tests/test_assured_code_index.py tests/test_assured_evidence_index.py -v 2>&1 | tail -5
```

Expected: all tests pass (existing + new).

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/code_index.py
git commit -m "refactor(v020): migrate parse_code_annotations to EvidenceIndexRegistry (Phase B task 9)"
```

---

### Task 10: spec_parser skip-rules (D1)

**Files:**
- Modify: `plugins/sdlc-programme/scripts/programme/spec_parser.py`
- Modify: `tests/test_programme_spec_parser.py`

- [ ] **Step 1: Append failing tests**

```python
def test_parse_spec_skips_blockquoted_ids() -> None:
    text = (
        "## Requirements\n"
        "\n"
        "### REQ-foo-001\n"
        "Real requirement.\n"
        "\n"
        "> ### REQ-leak-001\n"
        "> This is in a blockquote and should be ignored.\n"
    )
    parsed = parse_spec(text, phase="requirements")
    assert "REQ-foo-001" in parsed.declared_ids
    assert "REQ-leak-001" not in parsed.declared_ids


def test_parse_spec_skips_inline_code_ids() -> None:
    text = (
        "## Requirements\n"
        "\n"
        "### REQ-foo-001\n"
        "Real requirement; see also `REQ-other-001` (inline code).\n"
    )
    parsed = parse_spec(text, phase="requirements")
    assert parsed.declared_ids == {"REQ-foo-001"}


def test_parse_spec_skips_html_comment_ids() -> None:
    text = (
        "## Requirements\n"
        "\n"
        "### REQ-foo-001\n"
        "Real one.\n"
        "<!-- ### REQ-comment-001 -->\n"
    )
    parsed = parse_spec(text, phase="requirements")
    assert "REQ-comment-001" not in parsed.declared_ids
```

- [ ] **Step 2: Run (fail)**, **Step 3: Implement skip-rules in spec_parser**

Read the existing spec_parser.py — it already toggles `in_code_block` on `` ``` `` lines. Add three more state toggles. Replace the line-walking loop in `parse_spec`:

```python
import re as _re

_INLINE_CODE_RE = _re.compile(r"`[^`]*`")


def _strip_inline_code(line: str) -> str:
    """Remove `inline code` spans from a markdown line so IDs inside backticks are ignored."""
    return _INLINE_CODE_RE.sub("", line)


# Inside parse_spec:
in_code_block = False
in_html_comment = False
for raw_line in text.splitlines():
    stripped = raw_line.strip()
    if stripped.startswith("```"):
        in_code_block = not in_code_block
        continue
    if in_code_block:
        continue
    # HTML comment toggle (multi-line aware)
    if "<!--" in raw_line and "-->" not in raw_line:
        in_html_comment = True
        continue
    if in_html_comment:
        if "-->" in raw_line:
            in_html_comment = False
        continue
    # Single-line HTML comment: strip it before processing
    if "<!--" in raw_line and "-->" in raw_line:
        raw_line = _re.sub(r"<!--.*?-->", "", raw_line)
    # Blockquote: skip lines starting with `> `
    if stripped.startswith(">"):
        continue
    # Inline code: strip backtick spans before regex matches
    line = _strip_inline_code(raw_line)
    # ... existing heading + satisfies parsing on `line` instead of `raw_line` ...
```

- [ ] **Step 4: Run tests pass**

```bash
python3 -m pytest tests/test_programme_spec_parser.py -v 2>&1 | tail -5
```

Expected: existing tests still pass + 3 new tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-programme/scripts/programme/spec_parser.py tests/test_programme_spec_parser.py
git commit -m "feat(v020): spec_parser skip blockquotes/inline-code/HTML-comments (D1) (Phase B task 10)"
```

---

### Task 10A: RequirementMetadata registry (foundation for F-009 typed statuses)

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/requirement_metadata.py`
- Create: `tests/test_assured_requirement_metadata.py`

**Why this task exists:** the v0.2.0 plan review (P1.2) caught that EvidenceStatus depends on metadata (`evidence_status`, `justification`, `related`) that `IdRecord` does not capture. Without this metadata-capture step, RTM exporters cannot distinguish `MISSING` from `NOT_APPLICABLE` from `MANUAL_EVIDENCE_REQUIRED` — they only see absence-of-annotation. This task adds a parallel registry keyed by REQ-ID, populated from the requirements-spec.md frontmatter PLUS per-REQ inline fields.

- [ ] **Step 1: Failing test**

```python
"""Tests for assured.requirement_metadata."""

from pathlib import Path

from sdlc_assured_scripts.assured.evidence_status import EvidenceStatus
from sdlc_assured_scripts.assured.requirement_metadata import (
    RequirementMetadata,
    build_requirement_metadata_registry,
)


def test_metadata_captured_from_per_req_inline_fields(tmp_path: Path) -> None:
    spec = tmp_path / "docs" / "specs" / "auth" / "requirements-spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "---\n"
        "feature_id: auth\n"
        "module: P1.SP1.M1\n"
        "---\n"
        "## Requirements\n"
        "\n"
        "### REQ-auth-001\n"
        "Real one.\n"
        "**Module:** P1.SP1.M1\n"
        "**Evidence-status:** linked\n"
        "\n"
        "### REQ-auth-002\n"
        "Configuration-only.\n"
        "**Module:** P1.SP1.M1\n"
        "**Evidence-status:** configuration_artifact\n"
        "**Justification:** Implemented entirely by `programs.yaml` declarations.\n"
        "**Related:** REQ-auth-001\n"
    )
    registry = build_requirement_metadata_registry(tmp_path)
    md1 = registry["REQ-auth-001"]
    assert md1.evidence_status == EvidenceStatus.LINKED
    assert md1.justification is None
    assert md1.related == []
    md2 = registry["REQ-auth-002"]
    assert md2.evidence_status == EvidenceStatus.CONFIGURATION_ARTIFACT
    assert "programs.yaml" in (md2.justification or "")
    assert md2.related == ["REQ-auth-001"]


def test_missing_evidence_status_field_defaults_to_none() -> None:
    md = RequirementMetadata(req_id="REQ-x-001")
    assert md.evidence_status is None
    assert md.justification is None
    assert md.related == []
```

- [ ] **Step 2: Run (fail on import)**

- [ ] **Step 3: Implement**

```python
"""Per-requirement metadata captured from inline `**Field:**` lines.

This complements `IdRecord` (which carries only id/kind/source/satisfies)
with the metadata that v0.2.0 typed-evidence-status (F-009) and per-REQ
relation tracking (F-006) require.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .evidence_status import EvidenceStatus


@dataclass(frozen=True)
class RequirementMetadata:
    req_id: str
    evidence_status: Optional[EvidenceStatus] = None
    justification: Optional[str] = None
    related: list[str] = field(default_factory=list)


_REQ_HEADING_RE = re.compile(
    r"^###\s+(?P<id>(?:P\d+\.SP\d+\.M\d+\.)?REQ-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)
_FIELD_RE = re.compile(r"^\*\*(?P<key>[A-Za-z][A-Za-z0-9-]*)?:\*\*\s+(?P<value>.+)$")
_ID_TOKEN_RE = re.compile(
    r"\b((?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)


def build_requirement_metadata_registry(project_root: Path) -> dict[str, RequirementMetadata]:
    """Walk docs/specs/**/requirements-spec.md; build {req_id: RequirementMetadata}."""
    registry: dict[str, RequirementMetadata] = {}
    specs_dir = project_root / "docs" / "specs"
    if not specs_dir.is_dir():
        return registry
    for spec_file in sorted(specs_dir.glob("**/requirements-spec.md")):
        text = spec_file.read_text(encoding="utf-8")
        current_id: Optional[str] = None
        evidence_status: Optional[EvidenceStatus] = None
        justification: Optional[str] = None
        related: list[str] = []
        in_code_block = False

        def _flush() -> None:
            nonlocal current_id, evidence_status, justification, related
            if current_id is not None:
                registry[current_id] = RequirementMetadata(
                    req_id=current_id,
                    evidence_status=evidence_status,
                    justification=justification,
                    related=list(related),
                )
            current_id = None
            evidence_status = None
            justification = None
            related = []

        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            heading = _REQ_HEADING_RE.match(line)
            if heading:
                _flush()
                current_id = heading["id"]
                continue
            if current_id is None:
                continue
            field_match = _FIELD_RE.match(line)
            if not field_match:
                continue
            key = (field_match["key"] or "").lower()
            value = field_match["value"].strip()
            if key == "evidence-status":
                try:
                    evidence_status = EvidenceStatus(value.lower())
                except ValueError:
                    pass
            elif key == "justification":
                justification = value
            elif key == "related":
                related = _ID_TOKEN_RE.findall(value)
        _flush()
    return registry
```

- [ ] **Step 4: Run tests pass**

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/requirement_metadata.py \
        tests/test_assured_requirement_metadata.py
git commit -m "feat(v020): RequirementMetadata registry (foundation for F-006 + F-009) (Phase B task 10A)"
```

---

### Task 11: EvidenceStatus enum + migration of regulatory exporters (F-009)

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/evidence_status.py`
- Create: `tests/test_assured_evidence_status.py`
- Modify: `plugins/sdlc-assured/scripts/assured/export.py` — replace `—` placeholders with typed `EvidenceStatus` cells

- [ ] **Step 1: Write enum + tests**

```python
"""EvidenceStatus enum for typed RTM cells (F-009)."""

from __future__ import annotations

from enum import Enum


class EvidenceStatus(Enum):
    LINKED = "linked"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    MANUAL_EVIDENCE_REQUIRED = "manual_evidence_required"
    CONFIGURATION_ARTIFACT = "configuration_artifact"

    def display(self) -> str:
        return {
            EvidenceStatus.LINKED: "linked",
            EvidenceStatus.MISSING: "MISSING",
            EvidenceStatus.NOT_APPLICABLE: "n/a",
            EvidenceStatus.MANUAL_EVIDENCE_REQUIRED: "manual",
            EvidenceStatus.CONFIGURATION_ARTIFACT: "config",
        }[self]
```

```python
"""Tests for EvidenceStatus."""

from sdlc_assured_scripts.assured.evidence_status import EvidenceStatus


def test_evidence_status_has_five_values() -> None:
    assert {s.name for s in EvidenceStatus} == {
        "LINKED",
        "MISSING",
        "NOT_APPLICABLE",
        "MANUAL_EVIDENCE_REQUIRED",
        "CONFIGURATION_ARTIFACT",
    }


def test_evidence_status_display_strings() -> None:
    assert EvidenceStatus.LINKED.display() == "linked"
    assert EvidenceStatus.MISSING.display() == "MISSING"
```

- [ ] **Step 2: Migrate `export_do178c_rtm` to use EvidenceStatus**

Modify `_build_rows` (or its equivalent in each exporter) to return `tuple[str, str, str, str, EvidenceStatus]` instead of bare strings. Update each exporter to print `{status.display()}: {payload}` for non-LINKED cells, or just `{payload}` for LINKED.

For each REQ row:
- if at least one `satisfies`-linked DES has evidence → LINKED
- if no DES has evidence and the REQ frontmatter declares `evidence_status: manual_evidence_required` → MANUAL_EVIDENCE_REQUIRED
- if `evidence_status: not_applicable` with justification → NOT_APPLICABLE
- if `evidence_status: configuration_artifact` (e.g. for plist/entitlement REQs) → CONFIGURATION_ARTIFACT
- otherwise → MISSING

Update `export_do178c_rtm`, `export_iec_62304_matrix`, `export_iso_26262_asil_matrix`, `export_fda_dhf_structure` accordingly.

- [ ] **Step 3: Add per-exporter test asserting typed cells**

```python
def test_export_do178c_rtm_uses_typed_evidence_status_for_missing() -> None:
    records, code = _three_id_chain_with_no_code()  # helper from test_assured_export.py
    out = export_do178c_rtm(records, code)
    assert "MISSING" in out
    assert "—" not in out  # placeholder eliminated
```

- [ ] **Step 4: Run all exporter tests pass**

```bash
python3 -m pytest tests/test_assured_export.py tests/test_assured_evidence_status.py -v 2>&1 | tail -8
```

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/evidence_status.py \
        plugins/sdlc-assured/scripts/assured/export.py \
        tests/test_assured_evidence_status.py tests/test_assured_export.py
git commit -m "feat(v020): typed EvidenceStatus on 4 regulatory RTM exporters (F-009) (Phase B task 11)"
```

---

### Task 11A: Migrate exporters from CodeIndexEntry to EvidenceIndexEntry input

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/export.py` — change exporter signatures to accept `List[EvidenceIndexEntry]` + `Mapping[str, RequirementMetadata]`
- Modify: `tests/test_assured_export.py`

**Why this task exists:** the v0.2.0 plan review (P1.1) caught that Task 9's compatibility shim filtered out every `EvidenceKind` except `PYTHON_COMMENT`. Without this migration, markdown SKILL.md / YAML frontmatter / satisfies-by-existence evidence (Tasks 6-8) never reaches the RTM. F-001 + F-009 stay broken despite the new abstraction existing. This task changes the exporters to consume the full `EvidenceIndexEntry` flow plus the metadata registry from Task 10A.

- [ ] **Step 1: Failing test**

```python
def test_export_do178c_rtm_recognises_markdown_evidence_in_source_code_column() -> None:
    """An entry with kind=MARKDOWN_HTML_COMMENT must populate the source-code column,
    not produce a MISSING placeholder. Regression test for F-001/F-009 plan-review P1.1."""
    records = [
        IdRecord(id="REQ-foo-001", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
        IdRecord(id="DES-foo-001", kind="DES", source="docs/specs/foo/design-spec.md", satisfies=["REQ-foo-001"]),
        IdRecord(id="TEST-foo-001", kind="TEST", source="docs/specs/foo/test-spec.md", satisfies=["DES-foo-001"]),
    ]
    evidence = [
        EvidenceIndexEntry(
            kind=EvidenceKind.MARKDOWN_HTML_COMMENT,
            source="plugins/sdlc-x/skills/foo/SKILL.md",
            line=5,
            cited_ids=["DES-foo-001"],
        ),
    ]
    metadata: dict[str, RequirementMetadata] = {}
    out = export_do178c_rtm(records, evidence, metadata)
    assert "plugins/sdlc-x/skills/foo/SKILL.md" in out
    assert "MISSING" not in out
```

- [ ] **Step 2: Run (fails on signature)**

- [ ] **Step 3: Update exporter signatures**

```python
def export_do178c_rtm(
    records: List[IdRecord],
    evidence: List[EvidenceIndexEntry],
    metadata: Mapping[str, RequirementMetadata],
) -> str:
    """DO-178C Requirements Traceability Matrix — v0.2.0 signature consumes
    EvidenceIndexEntry directly (P1.1 fix) and uses RequirementMetadata for
    typed evidence statuses (P1.2 fix)."""
    evidence_by_cited = _evidence_by_cited(evidence)  # NEW helper
    cited_by = _index_by_satisfies(records)
    lines = [
        "# Requirements Traceability Matrix (DO-178C)",
        "",
        (
            "Generated by `traceability-export do-178c-rtm`. Each row links a high-level requirement "
            + "to its low-level requirements (designs), implementing source code, and verifying test cases."
        ),
        "",
        "| HLR | LLR | Source code | Test case |",
        "|-----|-----|-------------|-----------|",
    ]
    for req in [r for r in records if r.kind == "REQ"]:
        deses = [d for d in cited_by.get(req.id, []) if d.kind == "DES"]
        for des in deses:
            tests = [t for t in cited_by.get(des.id, []) if t.kind == "TEST"]
            evidence_cells = (
                evidence_by_cited.get(req.id, []) + evidence_by_cited.get(des.id, [])
            )
            source_cell = _format_source_cell(evidence_cells, metadata.get(req.id))
            test_str = ", ".join(t.id for t in tests) or _format_missing()
            lines.append(f"| {req.id} | {des.id} | {source_cell} | {test_str} |")
        if not deses:
            source_cell = _format_source_cell([], metadata.get(req.id))
            lines.append(f"| {req.id} | — | {source_cell} | — |")
    return "\n".join(lines) + "\n"


def _evidence_by_cited(evidence: List[EvidenceIndexEntry]) -> dict[str, List[EvidenceIndexEntry]]:
    out: dict[str, List[EvidenceIndexEntry]] = defaultdict(list)
    for e in evidence:
        for cited in e.cited_ids:
            out[cited].append(e)
    return out


def _format_source_cell(
    evidence_cells: List[EvidenceIndexEntry],
    metadata: Optional[RequirementMetadata],
) -> str:
    """Render a source-code cell. Uses typed EvidenceStatus when no evidence
    is present and the REQ frontmatter declares a non-LINKED status."""
    if evidence_cells:
        return "; ".join(
            f"{e.source}:{e.line}" if e.line is not None else e.source
            for e in evidence_cells
        )
    if metadata is not None and metadata.evidence_status is not None:
        status = metadata.evidence_status
        if status == EvidenceStatus.NOT_APPLICABLE:
            return f"{status.display()}: {metadata.justification or '(no justification)'}"
        if status == EvidenceStatus.MANUAL_EVIDENCE_REQUIRED:
            return status.display()
        if status == EvidenceStatus.CONFIGURATION_ARTIFACT:
            return f"{status.display()}: {metadata.justification or '(unspecified)'}"
        if status == EvidenceStatus.LINKED:
            return "LINKED-NO-EVIDENCE"  # frontmatter claim contradicts reality — surface
    return EvidenceStatus.MISSING.display()
```

Apply the same signature change to `export_iec_62304_matrix`, `export_iso_26262_asil_matrix`, `export_fda_dhf_structure`. Update `_build_rows` (used by csv + markdown exporters) similarly.

- [ ] **Step 4: Update existing v0.1.0 export tests for new signature**

Existing tests pass `code` (a `List[CodeIndexEntry]`) — change to `evidence` (a `List[EvidenceIndexEntry]`). Add `metadata={}` for v0.1.0-shape tests where no metadata is captured.

- [ ] **Step 5: Run tests pass + commit**

```bash
git add plugins/sdlc-assured/scripts/assured/export.py tests/test_assured_export.py
git commit -m "feat(v020): exporters consume EvidenceIndexEntry + RequirementMetadata directly (P1.1 + P1.2 plan-review fixes) (Phase B task 11A)"
```

---

### Task 12: programs.yaml paths_sections schema (F-002 named anchors)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py` — extend `Module` dataclass
- Modify: `plugins/sdlc-assured/templates/programs.yaml` — example
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Extend Module dataclass**

```python
@dataclass(frozen=True)
class PathSection:
    """Named-anchor scoping within a file (F-002)."""

    file: str
    anchor: str  # e.g. "## Section Name" — match against headings in the file


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    paths: List[str]
    granularity: str
    structure: str
    owner: Optional[str] = None
    paths_sections: List[PathSection] = field(default_factory=list)
```

- [ ] **Step 2: Update parser**

Add to `parse_programs_yaml`:

```python
sections = m.get("paths_sections", []) or []
section_objs = [
    PathSection(file=s["file"], anchor=s["anchor"]) for s in sections
]
modules.append(
    Module(
        id=m["id"],
        name=m["name"],
        paths=list(m.get("paths", [])),
        granularity=m.get("granularity", "requirement"),
        structure=m.get("structure", "flat"),
        owner=m.get("owner"),
        paths_sections=section_objs,
    )
)
```

- [ ] **Step 3: Test**

```python
def test_module_paths_sections_round_trip(tmp_path: Path) -> None:
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - id: M1
            name: M1
            paths: [src/]
            granularity: requirement
            structure: flat
            paths_sections:
              - file: src/synthesis-librarian.md
                anchor: "### MODE: SYNTHESISE-ACROSS-SPEC-TYPES"
"""
    )
    decomp = parse_programs_yaml(pyaml)
    m = decomp.programs[0].sub_programs[0].modules[0]
    assert len(m.paths_sections) == 1
    assert m.paths_sections[0].anchor == "### MODE: SYNTHESISE-ACROSS-SPEC-TYPES"
```

- [ ] **Step 4: Run tests pass + black + flake8 + commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py \
        plugins/sdlc-assured/templates/programs.yaml \
        tests/test_assured_decomposition.py
git commit -m "feat(v020): programs.yaml paths_sections named-anchor scoping (F-002) (Phase B task 12)"
```

---

## Phase C — Validator improvements + non-Python proof adapter

### Task 13: DependencyExtractor protocol + ImportEdge

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/dependency_extractor.py`
- Create: `tests/test_assured_dependency_extractor.py`

- [ ] **Step 1: TDD cycle for protocol shell**

Test asserts `DependencyExtractor` protocol has `language: str` attribute and `extract(...)` method signature. Use `typing.runtime_checkable` for testability.

```python
from sdlc_assured_scripts.assured.dependency_extractor import (
    DependencyExtractor,
    ImportEdge,
)


def test_import_edge_dataclass() -> None:
    e = ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")
    assert e.from_module == "P1.SP1.M1"


def test_dependency_extractor_protocol_attributes() -> None:
    """The protocol declares `language` and `extract`."""
    # Smoke test: any class implementing the protocol shape passes runtime_checkable
    pass  # protocol verification by Python's structural typing
```

Implementation:

```python
"""Dependency extractor interface — F-007."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol, runtime_checkable

from .decomposition import Decomposition


@dataclass(frozen=True)
class ImportEdge:
    from_module: str
    to_module: str


@runtime_checkable
class DependencyExtractor(Protocol):
    """Language-specific extractor of cross-module dependency edges."""

    language: str  # e.g. "python", "swift"

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]: ...
```

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/dependency_extractor.py \
        tests/test_assured_dependency_extractor.py
git commit -m "feat(v020): DependencyExtractor protocol + ImportEdge (Phase C task 13)"
```

---

### Task 14: PythonAstExtractor adapter

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/dependency_extractor.py`
- Modify: `tests/test_assured_dependency_extractor.py`

- [ ] **Step 1: Test**

```python
def test_python_ast_extractor_walks_imports(tmp_path: Path) -> None:
    src_a = tmp_path / "src" / "a"
    src_a.mkdir(parents=True)
    (src_a / "module_a.py").write_text("from b.module_b import foo\n")
    src_b = tmp_path / "src" / "b"
    src_b.mkdir(parents=True)
    (src_b / "module_b.py").write_text("def foo(): return 1\n")

    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: A, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: B, paths: [src/b/], granularity: requirement, structure: flat}
"""
    )

    extractor = PythonAstExtractor()
    edges = extractor.extract(
        source_paths=[src_a / "module_a.py", src_b / "module_b.py"],
        programs=decomp,
    )
    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges
```

- [ ] **Step 2: Implementation**

```python
import ast


class PythonAstExtractor:
    """Python implementation of DependencyExtractor using ast.parse."""

    language = "python"

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]:
        path_to_module = self._build_path_index(programs)
        edges: set[ImportEdge] = set()
        for path in source_paths:
            if path.suffix != ".py" or not path.is_file():
                continue
            from_module = self._resolve_module(path, path_to_module)
            if from_module is None:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                target_module = self._import_target_module(node, path_to_module)
                if target_module and target_module != from_module:
                    edges.add(
                        ImportEdge(from_module=from_module, to_module=target_module)
                    )
        return list(edges)

    def _build_path_index(self, programs: Decomposition) -> dict[str, str]:
        """Map source-path-prefix → module-id."""
        index: dict[str, str] = {}
        for p in programs.programs:
            for sp in p.sub_programs:
                for m in sp.modules:
                    full_id = f"{p.id}.{sp.id}.{m.id}"
                    for path_prefix in m.paths:
                        index[path_prefix.rstrip("/")] = full_id
        return index

    def _resolve_module(self, path: Path, index: dict[str, str]) -> str | None:
        path_str = str(path)
        for prefix, module_id in index.items():
            if prefix in path_str:
                return module_id
        return None

    def _import_target_module(
        self, node: ast.AST, index: dict[str, str]
    ) -> str | None:
        if isinstance(node, ast.ImportFrom) and node.module:
            for prefix, module_id in index.items():
                base = prefix.split("/")[-2] if "/" in prefix else prefix
                if base in node.module:
                    return module_id
        return None
```

- [ ] **Step 3: Run tests + commit**

```bash
git add plugins/sdlc-assured/scripts/assured/dependency_extractor.py \
        tests/test_assured_dependency_extractor.py
git commit -m "feat(v020): PythonAstExtractor walks Python imports → ImportEdges (F-007) (Phase C task 14)"
```

---

### Task 15: Non-Python proof adapter (interface validation)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/dependency_extractor.py`
- Modify: `tests/test_assured_dependency_extractor.py`

- [ ] **Step 1: Implement a generic regex-based extractor**

```python
import re as _re


class GenericRegexExtractor:
    """Generic regex-based extractor parameterised by language + import pattern.

    Demonstrates the DependencyExtractor interface is not Python-shaped.
    Phase G uses this with a Swift-import pattern to validate cross-platform.
    """

    def __init__(
        self,
        language: str,
        file_extensions: tuple[str, ...],
        import_pattern: _re.Pattern[str],
    ) -> None:
        self.language = language
        self._file_extensions = file_extensions
        self._import_pattern = import_pattern

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]:
        # Same path resolution as PythonAstExtractor; pattern matching instead of AST
        py = PythonAstExtractor()
        path_to_module = py._build_path_index(programs)
        edges: set[ImportEdge] = set()
        for path in source_paths:
            if path.suffix not in self._file_extensions or not path.is_file():
                continue
            from_module = py._resolve_module(path, path_to_module)
            if from_module is None:
                continue
            text = path.read_text(encoding="utf-8")
            for match in self._import_pattern.finditer(text):
                target_name = match.group(1)
                for prefix, module_id in path_to_module.items():
                    if target_name.lower() in prefix.lower():
                        if module_id != from_module:
                            edges.add(
                                ImportEdge(
                                    from_module=from_module, to_module=module_id
                                )
                            )
                        break
        return list(edges)


def make_swift_extractor() -> GenericRegexExtractor:
    """Toy Swift import extractor for v0.2.0 interface validation."""
    return GenericRegexExtractor(
        language="swift",
        file_extensions=(".swift",),
        import_pattern=_re.compile(r"^\s*import\s+(\w+)\s*$", _re.MULTILINE),
    )
```

- [ ] **Step 2: Test (proves interface is generic)**

```python
def test_swift_extractor_finds_cross_module_import(tmp_path: Path) -> None:
    src_a = tmp_path / "src" / "a"
    src_a.mkdir(parents=True)
    (src_a / "ViewA.swift").write_text("import b\n")
    src_b = tmp_path / "src" / "b"
    src_b.mkdir(parents=True)
    (src_b / "ServiceB.swift").write_text("public class ServiceB {}\n")

    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: A, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: B, paths: [src/b/], granularity: requirement, structure: flat}
"""
    )

    swift = make_swift_extractor()
    assert swift.language == "swift"
    edges = swift.extract(
        source_paths=[src_a / "ViewA.swift", src_b / "ServiceB.swift"],
        programs=decomp,
    )
    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges
```

- [ ] **Step 3: Recovery check**

If the Swift adapter test fails because the interface is implicitly Python-shaped (e.g. ImportEdge requires AST-only data), STOP and document in the design-decisions addendum: "Phase C task 15 found the DependencyExtractor interface is X-shaped. Defer cross-platform validation to v0.3.0." Do NOT block Phase C close on the proof adapter — it is a stretch deliverable.

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/dependency_extractor.py \
        tests/test_assured_dependency_extractor.py
git commit -m "feat(v020): non-Python proof adapter (Swift via GenericRegexExtractor) — interface validation (Phase C task 15)"
```

---

### Task 16: Wire extractor into kb-codeindex

**Files:**
- Modify: `plugins/sdlc-assured/skills/kb-codeindex/SKILL.md` + plugin mirror — document the extractor invocation
- Modify: `plugins/sdlc-assured/scripts/assured/__init__.py` — re-export ImportEdge for convenience

- [ ] **Step 1: Update kb-codeindex SKILL.md to invoke the extractor**

Add a new step to the skill: after `parse_code_annotations`, run the registered extractors per language detected in the project paths, accumulate ImportEdges, write them to `library/_dependency-edges.md` (new artefact for visibility_rule_enforcement consumption).

- [ ] **Step 2: Sync plugin and root-mirror SKILL.md byte-identical**

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-assured/skills/kb-codeindex/SKILL.md \
        skills/kb-codeindex/SKILL.md \
        plugins/sdlc-assured/scripts/assured/__init__.py
git commit -m "feat(v020): wire DependencyExtractor into kb-codeindex; new library/_dependency-edges.md artefact (Phase C task 16)"
```

---

### Task 16A: Dependency-edges artefact — renderer + parser

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/dependency_extractor.py` — add `render_dependency_edges` + `parse_dependency_edges`
- Modify: `tests/test_assured_dependency_extractor.py`

**Why this task exists:** the v0.2.0 plan review (P1.3) caught that Task 16 only documented the wiring in SKILL.md and re-exported the dataclass — there was no executable plumbing. Without a renderer for `library/_dependency-edges.md`, a parser to read it back, and an integration helper, `visibility_rule_enforcement` cannot consume real extracted edges. F-007 stays aspirational. This task adds the executable round-trip.

- [ ] **Step 1: Failing test for render**

```python
def test_render_dependency_edges_emits_markdown_table() -> None:
    edges = [
        ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2"),
        ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M3"),
    ]
    out = render_dependency_edges(edges, library_handle="phase-f-dogfood")
    assert "| From | To |" in out
    assert "| P1.SP1.M1 | P1.SP1.M2 |" in out
    assert "<!-- library_handle: phase-f-dogfood -->" in out


def test_parse_dependency_edges_round_trips() -> None:
    original = [ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")]
    text = render_dependency_edges(original, library_handle="x")
    assert parse_dependency_edges(text) == original
```

- [ ] **Step 2: Implementation**

```python
def render_dependency_edges(edges: List[ImportEdge], library_handle: str) -> str:
    """Render edges as a markdown table for library/_dependency-edges.md."""
    lines = [
        "<!-- format_version: 1 -->",
        f"<!-- library_handle: {library_handle} -->",
        "# Module Dependency Edges",
        "",
        "Generated by `kb-codeindex`. One row per observed cross-module import edge.",
        "",
        "| From | To |",
        "|------|----|",
    ]
    for edge in sorted({(e.from_module, e.to_module) for e in edges}):
        lines.append(f"| {edge[0]} | {edge[1]} |")
    return "\n".join(lines) + "\n"


_EDGE_ROW_RE = re.compile(r"^\|\s+(\S+)\s+\|\s+(\S+)\s+\|$")


def parse_dependency_edges(text: str) -> List[ImportEdge]:
    """Parse a `library/_dependency-edges.md` file back into ImportEdge objects."""
    edges: List[ImportEdge] = []
    for line in text.splitlines():
        m = _EDGE_ROW_RE.match(line.strip())
        if not m:
            continue
        from_, to_ = m.group(1), m.group(2)
        if from_ == "From" or to_ == "To" or from_.startswith("--"):
            continue
        edges.append(ImportEdge(from_module=from_, to_module=to_))
    return edges
```

- [ ] **Step 3: Run tests pass + commit**

```bash
git add plugins/sdlc-assured/scripts/assured/dependency_extractor.py \
        tests/test_assured_dependency_extractor.py
git commit -m "feat(v020): dependency-edges renderer + parser for library/_dependency-edges.md (P1.3 plan-review fix) (Phase C task 16A)"
```

---

### Task 16B: Build helper + integration test (real source → edges → visibility validator)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/dependency_extractor.py` — add `build_dependency_edges` orchestrator
- Modify: `tests/test_assured_dependency_extractor.py` — integration test
- Modify: `plugins/sdlc-assured/skills/kb-codeindex/SKILL.md` + root mirror — invoke the orchestrator

**Why this task exists:** P1.3 also requires an end-to-end integration test — real source files → extracted edges → file written → file read → `visibility_rule_enforcement` consumes them. This task wires the loop end-to-end.

- [ ] **Step 1: Integration test**

```python
from sdlc_assured_scripts.assured.decomposition import visibility_rule_enforcement


def test_integration_python_source_to_visibility_validator(tmp_path: Path) -> None:
    """End-to-end: real Python source → PythonAstExtractor → render → parse → validator."""
    src_a = tmp_path / "src" / "a"
    src_a.mkdir(parents=True)
    (src_a / "module_a.py").write_text("from b.module_b import foo\n")
    src_b = tmp_path / "src" / "b"
    src_b.mkdir(parents=True)
    (src_b / "module_b.py").write_text("def foo(): return 1\n")

    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: A, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: B, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: []  # M1 → M2 is NOT declared
  - from: P1.SP1.M2
    to: []
"""
    )

    edges = build_dependency_edges(
        source_paths=[src_a / "module_a.py", src_b / "module_b.py"],
        programs=decomp,
        extractors=[PythonAstExtractor()],
    )
    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges

    # Round-trip through file
    out_path = tmp_path / "library" / "_dependency-edges.md"
    out_path.parent.mkdir(parents=True)
    out_path.write_text(render_dependency_edges(edges, library_handle="x"))
    parsed = parse_dependency_edges(out_path.read_text())

    # Validator consumes parsed edges
    result = visibility_rule_enforcement(parsed, decomp, mode="strict")
    assert result.passed is False
    assert any("P1.SP1.M1" in e and "P1.SP1.M2" in e for e in result.errors)
```

- [ ] **Step 2: Implement `build_dependency_edges`**

```python
def build_dependency_edges(
    source_paths: List[Path],
    programs: Decomposition,
    extractors: List[DependencyExtractor],
) -> List[ImportEdge]:
    """Run each extractor on source_paths; return deduplicated union of edges."""
    seen: set[ImportEdge] = set()
    for extractor in extractors:
        for edge in extractor.extract(source_paths, programs):
            seen.add(edge)
    return sorted(seen, key=lambda e: (e.from_module, e.to_module))
```

- [ ] **Step 3: Update kb-codeindex SKILL.md to invoke build_dependency_edges + write `library/_dependency-edges.md`**

- [ ] **Step 4: Sync root mirror; run tests pass; commit**

```bash
git add plugins/sdlc-assured/scripts/assured/dependency_extractor.py \
        tests/test_assured_dependency_extractor.py \
        plugins/sdlc-assured/skills/kb-codeindex/SKILL.md \
        skills/kb-codeindex/SKILL.md
git commit -m "feat(v020): build_dependency_edges orchestrator + end-to-end integration test (P1.3 plan-review fix) (Phase C task 16B)"
```

---

### Task 17: granularity_match rewrite for indirect DES-mediated coverage (F-008)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py` — rewrite `granularity_match`
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Append failing test**

```python
def test_granularity_match_indirect_coverage_via_des() -> None:
    """A REQ is covered if any satisfies-linked DES has annotation evidence (F-008)."""
    declared_reqs = ["REQ-foo-001"]
    # No annotation on REQ; one annotation on the satisfying DES
    annotations = [
        CodeAnnotation(file_path="src/foo.py", line=10, cited_ids=["DES-foo-001"]),
    ]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/], granularity: requirement, structure: flat}
"""
    )
    spec_lookup = {"REQ-foo-001": "P1.SP1.M1", "DES-foo-001": "P1.SP1.M1"}
    # NEW signature: needs the satisfies-graph
    satisfies_graph = {"DES-foo-001": ["REQ-foo-001"]}
    result = granularity_match(
        declared_reqs, annotations, decomp, spec_lookup, satisfies_graph
    )
    # Indirect coverage: REQ has no direct annotation but DES-foo-001 (which satisfies REQ-foo-001) does
    assert result.passed is True
    assert result.warnings == []  # NO under-specified warning
```

- [ ] **Step 2: Run test (fails — old signature)**

- [ ] **Step 3: Implement new signature + behaviour**

```python
def granularity_match(
    declared_reqs: List[str],
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict[str, str],
    satisfies_graph: dict[str, list[str]] | None = None,
) -> DecompositionValidatorResult:
    """For modules with granularity=requirement, every REQ must have at least one
    annotation — directly OR via a satisfies-linked DES (F-008 indirect coverage).

    satisfies_graph maps DES-id → list of REQ-ids it satisfies. If None, falls back to
    direct-only coverage (v0.1.0 behaviour, deprecated).
    """
    annotated_ids: set[str] = set()
    for ann in annotations:
        annotated_ids.update(ann.cited_ids)

    granularity_by_module: dict[str, str] = {}
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                granularity_by_module[f"{p.id}.{sp.id}.{m.id}"] = m.granularity

    # Build the inverse: REQ-id → list of DES-ids that satisfy it
    inverse_satisfies: dict[str, list[str]] = {}
    if satisfies_graph:
        for des_id, req_ids in satisfies_graph.items():
            for req_id in req_ids:
                inverse_satisfies.setdefault(req_id, []).append(des_id)

    warnings: List[str] = []
    for req in declared_reqs:
        module = spec_module_lookup.get(req)
        if module is None or granularity_by_module.get(module) != "requirement":
            continue
        # Direct coverage check
        if req in annotated_ids:
            continue
        # Indirect coverage: any satisfies-linked DES annotated?
        satisfying_dess = inverse_satisfies.get(req, [])
        if any(des_id in annotated_ids for des_id in satisfying_dess):
            continue
        warnings.append(
            f"under-specified: {req} (module {module}) has no `# implements:` "
            "annotation directly OR via a satisfies-linked DES"
        )
    return DecompositionValidatorResult(passed=True, warnings=warnings)
```

- [ ] **Step 4: Update existing tests for new signature**

Existing v0.1.0 tests that called `granularity_match(declared_reqs, annotations, decomp, spec_lookup)` need updating to pass `satisfies_graph={}` for backward-compat or test the new indirect-coverage behaviour explicitly.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(v020): granularity_match indirect DES-mediated coverage (F-008) (Phase C task 17)"
```

---

### Task 18: orphan_ids widening (E1)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1-4: TDD cycle**

Test:
```python
def test_orphan_ids_widened_warns_on_orphan_test() -> None:
    """E1: orphan_ids now also reports orphan TEST/CODE IDs, not just REQ/DES."""
    records = [
        IdRecord(id="TEST-foo-001", kind="TEST", source="t.md", satisfies=["DES-foo-001"]),
    ]
    result = orphan_ids(records)
    # No CODE record cites TEST-foo-001 → orphan warning
    assert result.passed is True
    assert any("TEST-foo-001" in w for w in result.warnings)
```

Implementation: change `if r.kind in {"REQ", "DES"}` to `if r.kind in {"REQ", "DES", "TEST", "CODE"}`. Update existing v0.1.0 tests if they assert TEST/CODE are exempt.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(v020): orphan_ids widened to all kinds (E1) (Phase C task 18)"
```

---

### Task 19: forward_annotation_completeness validator (E2 NEW)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py` — append new validator
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1-4: TDD cycle**

Test (write 4-5 cases covering the "non-trivial" definition from Phase A decision 4):

```python
def test_forward_annotation_completeness_passes_when_all_public_functions_annotated(tmp_path: Path) -> None:
    f = tmp_path / "src" / "auth.py"
    f.parent.mkdir(parents=True)
    f.write_text(
        "def login(token):\n"
        "    # implements: DES-auth-001\n"
        "    return token\n"
    )
    decomp = ...  # 1 module covering src/
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True


def test_forward_annotation_completeness_fails_on_unannotated_public_function(tmp_path: Path) -> None:
    f = tmp_path / "src" / "auth.py"
    f.parent.mkdir(parents=True)
    f.write_text("def login(token):\n    return token\n")
    decomp = ...
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is False
    assert any("login" in e for e in result.errors)


def test_forward_annotation_completeness_skips_dunder_methods(tmp_path: Path) -> None:
    f = tmp_path / "src" / "m.py"
    f.parent.mkdir(parents=True)
    f.write_text("class X:\n    def __init__(self):\n        pass\n")
    decomp = ...
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True


def test_forward_annotation_completeness_skips_test_files(tmp_path: Path) -> None:
    f = tmp_path / "tests" / "test_x.py"
    f.parent.mkdir(parents=True)
    f.write_text("def test_foo():\n    pass\n")
    decomp = ...
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True
```

Implementation uses `ast.parse` to walk function definitions, applies the Phase A "non-trivial" exclusion rules.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(v020): forward_annotation_completeness validator (E2 NEW) (Phase C task 19)"
```

---

### Task 20: requirements_gate non-empty content check (D2)

**Files:**
- Modify: `plugins/sdlc-programme/scripts/programme/gates.py`
- Modify: `tests/test_programme_gates.py`

- [ ] **Step 1-4: TDD cycle**

Test:
```python
def test_requirements_gate_fails_on_whitespace_only_mandatory_section(tmp_path: Path) -> None:
    feature_dir = tmp_path / "auth"
    feature_dir.mkdir()
    (feature_dir / "requirements-spec.md").write_text(
        "**Feature-id:** auth\n\n"
        "## Motivation\n\n"
        "   \n\n"  # whitespace-only
        "## Requirements\n\n"
        "### REQ-auth-001\nReal req.\n"
    )
    result = requirements_gate(feature_dir, feature_id="auth")
    assert result.passed is False
    assert any("non-empty" in e.lower() or "whitespace" in e.lower() for e in result.errors)
```

Implementation: `requirements_gate` reads the spec, extracts mandatory section bodies (Motivation, Requirements), checks that each body has at least one non-whitespace line.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-programme/scripts/programme/gates.py tests/test_programme_gates.py
git commit -m "feat(v020): requirements_gate non-empty content check (D2) (Phase C task 20)"
```

---

## Phase D — ID system + REQ format

### Task 21: remap_ids multiple-prefix handling (E3)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/ids.py`
- Modify: `tests/test_assured_ids.py`

- [ ] **Step 1-4: TDD cycle**

Test:
```python
def test_remap_ids_warns_on_multiple_prefix_match() -> None:
    records = [
        IdRecord(id="REQ-x-001", kind="REQ", source="docs/specs/foo/bar/spec.md", satisfies=[]),
    ]
    # Both prefixes match the record's source
    remapping = {
        "docs/specs/foo/": "renamed/foo/",
        "docs/specs/foo/bar/": "renamed/foobar/",
    }
    result = remap_ids(records, remapping, on_overlap="warn")
    # Deterministic: longest-prefix wins
    assert result.records[0].source == "renamed/foobar/spec.md"
    assert any("multiple prefix match" in w.lower() for w in result.warnings)
```

Implementation: change `remap_ids` return signature from `List[IdRecord]` to `RemapResult` (records + warnings). Use longest-matching-prefix rule. Warn on overlap with `on_overlap="warn"` (default), error with `on_overlap="error"`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/ids.py tests/test_assured_ids.py
git commit -m "feat(v020): remap_ids multiple-prefix handling with longest-match + warn (E3) (Phase D task 21)"
```

---

### Task 22: Per-REQ `**Related:**` field (F-006)

**Files:**
- Modify: `plugins/sdlc-assured/templates/requirements-spec-assured.md` — add inline `**Related:**` example under one of the example REQs
- Modify: `plugins/sdlc-assured/scripts/assured/code_index.py` — `render_spec_findings` consults the metadata registry from Task 10A and emits per-entry `Related:` line
- Modify: `tests/test_assured_code_index.py`

**Why scoped to per-REQ, not file:** the v0.2.0 plan review (P2.2) caught that file-level frontmatter `related:` cannot express "REQ-002 related to REQ-004 while REQ-003 has no relation." F-006 wanted per-REQ relations. The metadata registry from Task 10A already parses per-REQ inline `**Related:**` fields — Task 22 wires `render_spec_findings` to consume that registry.

- [ ] **Step 1: Update template**

Modify `plugins/sdlc-assured/templates/requirements-spec-assured.md` — add an inline `**Related:**` field to one example REQ:

```markdown
### REQ-<feature-id>-001

<Single declarative sentence describing one requirement.>

**Module:** P1.SP1.M1

### REQ-<feature-id>-002

<Single declarative sentence describing the next requirement.>

**Module:** P1.SP1.M1
**Related:** REQ-<feature-id>-001
```

The `**Related:**` field is OPTIONAL per REQ. Only emit it for requirements that genuinely cross-reference each other.

- [ ] **Step 2: Failing test**

```python
def test_render_spec_findings_emits_per_req_related_when_metadata_provided() -> None:
    records = [
        IdRecord(id="REQ-foo-001", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
        IdRecord(id="REQ-foo-002", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
        IdRecord(id="REQ-foo-003", kind="REQ", source="docs/specs/foo/requirements-spec.md", satisfies=[]),
    ]
    metadata = {
        "REQ-foo-002": RequirementMetadata(req_id="REQ-foo-002", related=["REQ-foo-001"]),
        # REQ-foo-001 and REQ-foo-003 have NO `Related:` line
    }
    out = render_spec_findings(records, library_handle="x", metadata=metadata)
    # Only REQ-foo-002 gets a Related: line
    assert "Related: REQ-foo-001" in out
    # REQ-foo-001 and REQ-foo-003 do NOT get Related: lines
    section_001 = out.split("REQ-foo-001")[1].split("REQ-foo-002")[0]
    assert "Related:" not in section_001
    section_003 = out.split("REQ-foo-003")[1]
    assert "Related:" not in section_003
```

- [ ] **Step 3: Update render_spec_findings signature**

```python
def render_spec_findings(
    records: List[IdRecord],
    library_handle: str,
    metadata: Optional[Mapping[str, "RequirementMetadata"]] = None,
) -> str:
    """Render REQ/DES/TEST records as shelf-index entries (spec-as-KB-finding).

    metadata: optional per-REQ metadata registry from build_requirement_metadata_registry.
              When provided, emits a `Related:` line per entry for REQs that have
              a non-empty `related` list.
    """
    metadata = metadata or {}
    # ... existing rendering loop ...
    for n, r in enumerate(records, start=1):
        # ... existing entry render ...
        md = metadata.get(r.id)
        if md is not None and md.related:
            lines.append(f"**Related:** {', '.join(md.related)}")
```

- [ ] **Step 4: Run tests pass + commit**

```bash
git add plugins/sdlc-assured/templates/requirements-spec-assured.md \
        plugins/sdlc-assured/scripts/assured/code_index.py \
        tests/test_assured_code_index.py
git commit -m "feat(v020): per-REQ Related: field via metadata registry (F-006; P2.2 plan-review fix) (Phase D task 22)"
```

---

### Task 23: Split severity-mixed REQ in v0.1.0 spec (F-005)

**Files:**
- Modify: `docs/specs/assured-traceability-validators/requirements-spec.md` — split REQ-001 (mixes blocking + warn-not-block)
- Modify: corresponding design-spec.md and test-spec.md to follow the split

- [ ] **Step 1: Read existing REQ-001 of assured-traceability-validators**

The v0.1.0 REQ-001 collapses `id_uniqueness` (blocking), `cited_ids_resolve` (blocking), `orphan_ids` (warn-not-block) under one requirement. Per F-005 + Phase A decision: split into separate REQs when severity differs materially.

- [ ] **Step 2: Rewrite as two REQs**

REQ-001 (existing): blocking integrity (`id_uniqueness` + `cited_ids_resolve`)
REQ-005 (NEW; numeric continuation, NOT a letter suffix): non-blocking orphan-warning (`orphan_ids`)

**Important:** the existing ID grammar (`_FLAT_RE` and `_HEADING_RE` in `assured.ids`) accepts numeric suffixes only. A `REQ-001a` form would break `parse_id`, `build_id_registry`, and citation validation. The split must use the next available numeric ID (REQ-005, since the file currently has REQ-001 through REQ-004).

- [ ] **Step 3: Update DES + TEST**

DES-001 references the blocking pair. New DES-005 covers `orphan_ids`. Update TEST-001 / TEST-005 accordingly. All numeric, valid grammar.

- [ ] **Step 4: Run validators on the modified specs**

```bash
python3 -c "
import sys; sys.path.insert(0, 'plugins/sdlc-assured/scripts')
from pathlib import Path
from assured.ids import build_id_registry
from assured.traceability_validators import id_uniqueness, cited_ids_resolve, forward_link_integrity
records = build_id_registry(Path('.'))
print('id_uniqueness:', id_uniqueness(records).passed)
print('cited_ids_resolve:', cited_ids_resolve(records).passed)
print('forward_link_integrity:', forward_link_integrity(records).passed)
"
```

Expected: all pass (the split doesn't break referential integrity).

- [ ] **Step 5: Commit**

```bash
git add docs/specs/assured-traceability-validators/
git commit -m "fix(v020): split severity-mixed REQ-001 of traceability-validators (F-005) (Phase D task 23)"
```

---

### Task 24: REQ inventory wording fix (F-004)

**Files:**
- Modify: `research/phase-f-req-inventory.md` — programme-validators table

- [ ] **Step 1: Update wording**

Change `design_gate` row from "requires a review record for the **requirements** phase" to "requires a review record for the **same** phase (i.e., design)". Same change for `test_gate`.

- [ ] **Step 2: Commit**

```bash
git add research/phase-f-req-inventory.md
git commit -m "docs(v020): correct REQ inventory wording — gates check same-phase review records (F-004) (Phase D task 24)"
```

---

## Phase E — Quality discipline + skill robustness

### Task 25: Rewrite REQ-assured-decomposition-validators-001

**Files:**
- Modify: `docs/specs/assured-decomposition-validators/requirements-spec.md`

- [ ] **Step 1: Read v0.1.0 REQ-001**

The current text opens with the function name `req_has_module_assignment`. Per F-010 + Phase A direction: rewrite at user-visible-capability level.

- [ ] **Step 2: Rewrite**

New text (example):

```markdown
### REQ-assured-decomposition-validators-001

The Assured bundle MUST refuse to commission a project whose decomposition declares any REQ assigned to a module that does not exist in the project's `programs.yaml` — preventing silent module-typo defects from shipping into traceability artefacts.

**Module:** P1.SP1.M2
**Related:** REQ-assured-substrate-001 (commission-assured behaviour)
```

The user-visible capability is "the bundle refuses bad commissioning"; the function `req_has_module_assignment` is the implementation, not the requirement.

- [ ] **Step 3: Commit**

```bash
git add docs/specs/assured-decomposition-validators/requirements-spec.md
git commit -m "fix(v020): rewrite REQ-001 of decomposition-validators at user-visible-capability level (F-010) (Phase E task 25)"
```

---

### Task 26: Rewrite REQ-assured-traceability-validators-003

**Files:**
- Modify: `docs/specs/assured-traceability-validators/requirements-spec.md`

- [ ] **Step 1: Rewrite**

Current opens with function name `index_regenerability` and describes byte-for-byte. New text (example):

```markdown
### REQ-assured-traceability-validators-003

Auditors MUST be able to verify the published ID registry has not been hand-edited by re-running the registry-build process and observing identical output, without any environment-specific drift (timestamps, machine identifiers, locale).

**Module:** P1.SP1.M2
```

The user-visible capability is "auditors can verify integrity by re-running"; byte-identical output is the implementation contract.

- [ ] **Step 2: Commit**

```bash
git add docs/specs/assured-traceability-validators/requirements-spec.md
git commit -m "fix(v020): rewrite REQ-003 of traceability-validators at audit-visible-capability level (F-010) (Phase E task 26)"
```

---

### Task 27: Rewrite REQ-assured-skills-001

**Files:**
- Modify: `docs/specs/assured-skills/requirements-spec.md`

- [ ] **Step 1: Rewrite REQ-001 (req-add)**

Current mixes workflow outcome with implementation details. New text (example):

```markdown
### REQ-assured-skills-001

A user adding a requirement to an existing feature MUST be able to invoke a skill that mints a unique, sequential REQ-ID, prompts for the requirement statement, and persists the new requirement to the canonical spec file — with no risk of duplicate IDs even when invoked concurrently in different terminals on the same project.

**Module:** P1.SP1.M2
```

- [ ] **Step 2: Commit**

```bash
git add docs/specs/assured-skills/requirements-spec.md
git commit -m "fix(v020): rewrite REQ-001 of assured-skills at user-visible-capability level (F-010) (Phase E task 27)"
```

---

### Task 28: REQ-quality audit of remaining 41 Phase F REQs

**Files:**
- Create: `research/v020-req-quality-audit.md`

- [ ] **Step 1: Audit each non-rewritten Phase F REQ**

For each REQ in `docs/specs/<feature-id>/requirements-spec.md` (excluding the 3 already rewritten in tasks 25-27), apply the F-010 bar:
- Does it open with a user-visible capability ("Users MUST", "The bundle MUST", "Auditors MUST")?
- Or does it drift into function/implementation language ("the function X", "begins with", "increments max")?

Record verdict per REQ in the audit file.

- [ ] **Step 2: Time-boxed cap**

Per spec risk R7: if more than ~10 drifters surface, defer the long tail to v0.3.0 with explicit list. Otherwise rewrite each drifter inline.

- [ ] **Step 3: Commit**

```bash
git add research/v020-req-quality-audit.md docs/specs/
git commit -m "docs(v020): REQ-quality audit of Phase F corpus + rewrites within budget (F-010) (Phase E task 28)"
```

---

### Task 29: REQ-quality lint candidate

**Files:**
- Create: `tools/validation/check-req-quality.py`
- Create: `tests/test_check_req_quality.py`

- [ ] **Step 1: Implement linter**

Walk all `docs/specs/<feature-id>/requirements-spec.md` files. For each `### REQ-...` heading, read the body. Flag if:
- Body opens with a Python identifier (regex: `^[a-z_][a-z0-9_]*\s*\(`)
- Body contains the literal word "function" or "method" outside a quoted string

Output: list of flagged REQ-IDs with file:line references. Exit code 1 if any flagged (CI-friendly).

- [ ] **Step 2: Test against the 3 rewritten REQs (should pass) + a synthetic flagged REQ (should fail)**

- [ ] **Step 3: Commit**

```bash
git add tools/validation/check-req-quality.py tests/test_check_req_quality.py
git commit -m "feat(v020): REQ-quality lint candidate — flags function-shaped REQs (F-010) (Phase E task 29)"
```

---

### Task 30: phase-review skill graceful fallback (D3)

**Files:**
- Modify: `plugins/sdlc-programme/skills/phase-review/SKILL.md` + root mirror

- [ ] **Step 1: Add fallback logic to SKILL.md**

Update the dispatch section: try the configured agent (`sdlc-team-common:solution-architect` for design phase; `sdlc-team-fullstack:backend-architect` for test phase). If the dispatch fails (agent not loaded), fall back to `superpowers:requesting-code-review` pattern. Log the fallback in the review record so auditors see which agent actually performed the review.

- [ ] **Step 2: Sync root mirror**

```bash
diff plugins/sdlc-programme/skills/phase-review/SKILL.md skills/phase-review/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-programme/skills/phase-review/SKILL.md skills/phase-review/SKILL.md
git commit -m "feat(v020): phase-review skill graceful fallback for absent plugins (D3) (Phase E task 30)"
```

---

### Task 31: Codify annotation placement convention + fix F1 violation

**Files:**
- Modify: `docs/specs/assured-substrate/design-spec.md` — remove inline `<!-- implements: DES-assured-substrate-001 -->` annotation that should not be there
- Modify: `plugins/sdlc-assured/skills/code-annotate/SKILL.md` + root mirror — codify the rule

- [ ] **Step 1: Remove the F1 violation**

Open `docs/specs/assured-substrate/design-spec.md`. Find the inline `<!-- implements: DES-assured-substrate-001 -->` annotation INSIDE the DES-001 element (placed there in Phase F task 9 as a deviation). Remove it. The annotation belongs on the IMPLEMENTING artefact (`commission-assured/SKILL.md`), not on the design-spec itself.

- [ ] **Step 2: Codify the rule in code-annotate SKILL.md**

Add a new section to `code-annotate/SKILL.md`:

```markdown
## Annotation placement rules

`<!-- implements: <DES-ID> -->` and `# implements: <DES-ID>` annotations ALWAYS go on the implementing artefact:

- A Python function body — first line of the body, comment form
- A SKILL.md file — immediately after frontmatter close `---`, HTML-comment form
- A governance document — YAML frontmatter `satisfies_by_existence: [...]` or `implements: [...]`

NEVER place annotations:
- Inside a design-spec.md DES element (the DES is what is satisfied, not what implements)
- Inside a requirements-spec.md REQ element
- Inside a test-spec.md TEST element

The spec layer expresses obligation; the implementing artefact carries evidence. Crossing the layers blurs the audit trail.
```

- [ ] **Step 3: Sync root mirror; commit**

```bash
git add docs/specs/assured-substrate/design-spec.md \
        plugins/sdlc-assured/skills/code-annotate/SKILL.md \
        skills/code-annotate/SKILL.md
git commit -m "fix(v020): codify annotation placement convention + remove F1 violation in assured-substrate (Phase E task 31)"
```

---

## Phase F — Audit closure

### Task 32: Re-audit timeout-recovery commits (F4)

**Files:** none (audit-only task; produces a finding-or-confirmation note)

- [ ] **Step 1: Re-read commit `4aa73d3` (Phase E Task 11)**

```bash
git show 4aa73d3 --stat
git show 4aa73d3 -- plugins/sdlc-assured/scripts/assured/decomposition.py | head -100
```

Read the Phase E plan Task 11 prescription (lines 1587-1734 of the v0.1.0 plan). Compare commit content to plan prescription byte-for-byte (modulo black/flake8 formatting).

- [ ] **Step 2: Re-read commit `dbff56c` (Phase F Task 39)**

Same comparison for the integration-tests fixture commit. Phase F plan Task 39 (lines 4432-4682 of v0.1.0 plan).

- [ ] **Step 3: Author the audit note**

Append to `research/phase-de-deviation-ledger.md` under F4:

```markdown
## F4 — Re-audit verdict (v0.2.0 Phase F closure)

**Audit date:** 2026-05-XX
**Verdict:** <CONFIRMED CLEAN / DRIFT FOUND>
**Commit `4aa73d3`:** byte-for-byte match with plan prescription / drift in N lines (specify)
**Commit `dbff56c`:** same
**Action:** <none / fix in commit XXXXX>
```

- [ ] **Step 4: If drift found, fix it**

Open a small fix commit. Otherwise no code change.

- [ ] **Step 5: Commit the audit note**

```bash
git add research/phase-de-deviation-ledger.md
git commit -m "audit(v020): F4 timeout-recovery commits re-audited — <verdict> (Phase F task 32)"
```

---

## Phase G — Verification dogfood + EPIC closure

### Task 33: Build injected-defect fixtures

**Files:**
- Create: `tests/fixtures/v020-verification/` directory tree with one fixture per seeded defect

- [ ] **Step 1: Create 8 seeded-defect fixtures**

Each fixture is a minimal project layout (programs.yaml + spec dir + source code) with exactly one deliberate defect:

1. `f-008-no-des-evidence/` — REQ whose all `satisfies`-linked DESes lack annotations (asserts `granularity_match` fires)
2. `f-007-undeclared-import/` — Python source with cross-module import not declared in `programs.yaml` visibility (asserts `visibility_rule_enforcement` fires)
3. `f-007-swift-undeclared-import/` — Swift source with same defect, validated by GenericRegexExtractor (asserts non-Python adapter fires)
4. `f-009-not-applicable-no-justification/` — REQ frontmatter `evidence_status: not_applicable` with no `justification` field (asserts F-009 typed-status validation fires)
5. `e1-orphan-test/` — TEST record cited by no CODE annotation (asserts widened `orphan_ids` warns)
6. `e2-unannotated-public-fn/` — Python public function with no `# implements:` (asserts `forward_annotation_completeness` fires)
7. `d1-blockquoted-req/` — REQ-ID inside a markdown blockquote that should NOT be extracted (asserts `spec_parser` skips it)
8. `d2-whitespace-only-section/` — requirements-spec.md with whitespace-only Motivation section (asserts `requirements_gate` fires)

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/v020-verification/
git commit -m "test(v020): injected-defect fixtures for Phase G sub-stage 2 (8 seeded defects) (Phase G task 33)"
```

---

### Task 34: Phase G sub-stage 1 — baseline metric capture

**Files:**
- Create: `research/v020-baseline-metrics.md`

- [ ] **Step 1: Run all v0.2.0 validators on the existing Phase F corpus**

```bash
# This is the same corpus from Phase F of #178 — programs.yaml at repo root,
# docs/specs/<feature-id>/, plugins/sdlc-{programme,assured}/, etc.

python3 << 'EOF'
import sys; sys.path.insert(0, 'plugins/sdlc-assured/scripts')
from pathlib import Path
from assured.ids import build_id_registry
from assured.evidence_index import EvidenceIndexRegistry
from assured.decomposition import parse_programs_yaml, granularity_match, forward_annotation_completeness
from assured.traceability_validators import orphan_ids
from assured.dependency_extractor import PythonAstExtractor

# ... measurement code ...
print("Granularity_match noise rate:", noise_rate)
print("RTM source-code gap %:", rtm_gap)
print("RTM typed-evidence-status distribution:", status_dist)
print("Orphan_ids warning count:", orphan_count)
print("Forward-completeness violation count:", fc_count)
print("Validator runtime (s):", runtime)
EOF
```

- [ ] **Step 2: Author baseline-metrics file**

Write `research/v020-baseline-metrics.md` with the actual numbers captured.

- [ ] **Step 3: Commit**

```bash
git add research/v020-baseline-metrics.md
git commit -m "test(v020): Phase G sub-stage 1 — baseline metrics on existing corpus (Phase G task 34)"
```

---

### Task 35: Phase G sub-stage 2 — injected-defect tests

**Files:**
- Create: `tests/test_v020_injected_defects.py`

- [ ] **Step 1: Write 8 tests**

One test per seeded defect from Task 33 fixtures. Each test runs the relevant validator against its fixture and asserts the validator fires (errors or warnings).

```python
"""Phase G sub-stage 2 — injected-defect tests for v0.2.0 validators."""

from pathlib import Path

# 8 tests, one per fixture in tests/fixtures/v020-verification/

def test_f008_no_des_evidence_fires_granularity_warning() -> None:
    fixture = Path("tests/fixtures/v020-verification/f-008-no-des-evidence")
    # ... load fixture, run granularity_match, assert warning includes the REQ-ID
    ...

def test_f007_python_undeclared_import_fires_visibility_error() -> None:
    fixture = Path("tests/fixtures/v020-verification/f-007-undeclared-import")
    # ... PythonAstExtractor + visibility_rule_enforcement, assert error
    ...

# ... 6 more tests, one per fixture
```

- [ ] **Step 2: Run tests; expect all 8 to pass**

```bash
python3 -m pytest tests/test_v020_injected_defects.py -v 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_v020_injected_defects.py
git commit -m "test(v020): Phase G sub-stage 2 — 8 injected-defect tests pass (Phase G task 35)"
```

---

### Task 36: Phase G sub-stage 3 — acceptance metric deltas (HARD GATES)

**Files:**
- Create: `research/v020-acceptance-metrics.md`

- [ ] **Step 1: Re-run all validators with v0.2.0 tooling**

Same script as Task 34 baseline, but now with v0.2.0 validators (granularity_match indirect, orphan_ids widened, forward_annotation_completeness, etc.).

- [ ] **Step 2: Compare to baseline; record deltas**

Required hard-gate outcomes (per spec §3 Phase G):

| Metric | Baseline (Task 34) | v0.2.0 | Hard gate |
|---|---|---|---|
| `granularity_match` noise rate | 100% | ? | **≤5%** |
| DO-178C RTM source-code-column gap | 65% | ? | **≤20%, every remaining cell typed** |
| `forward_annotation_completeness` false-positive rate | n/a (new) | ? | **≤5% on dogfood corpus** |
| `visibility_rule_enforcement` runs cleanly | n/a (dormant) | ? | **runs, no extractor crash** |
| Existing tests | passing | passing | **no regression** |

- [ ] **Step 3: If any hard gate is missed, STOP**

Per spec: if a hard gate is missed, Phase G does not close. Either fix the validator OR escalate to user for rescope.

- [ ] **Step 4: Author acceptance-metrics file + commit**

```bash
git add research/v020-acceptance-metrics.md
git commit -m "test(v020): Phase G sub-stage 3 — acceptance metric deltas (hard gates passed) (Phase G task 36)"
```

---

### Task 37: EPIC #188 retrospective

**Files:**
- Create: `retrospectives/188-v020-assured-improvements.md`

- [ ] **Step 1: Author retrospective**

Same structure as #178 EPIC retro. Sections: What was built (per phase), What worked well, What was harder than expected, Lessons learned, Test totals, Branch state at PR, What we deferred (v0.3.0 candidates).

- [ ] **Step 2: Commit**

```bash
git add retrospectives/188-v020-assured-improvements.md
git commit -m "docs(v020): EPIC #188 retrospective (Phase G task 37)"
```

---

### Task 38: Containerised architect review at Phase G close (audit-readiness sign-off)

**Files:**
- Create: `research/sdlc-bundles/dogfood-workflows/v020-audit-readiness-review.{md,yaml,output.md}`

- [ ] **Step 1: Workflow files**

Architect prompt: "Review v0.2.0 against the audit-readiness claim in the EPIC retrospective. Does v0.2.0 deliver on the F-001/F-007/F-008/F-009/F-010 + carry-forward closure? Are there hidden gaps?" 6 questions, AGREE/AGREE-WITH-CONCERNS/DISAGREE/NEEDS-REWORK.

- [ ] **Step 2: Run the workflow + capture output**

```bash
/sdlc-workflows:workflows-run v020-audit-readiness-review
```

- [ ] **Step 3: Triage findings**

NEEDS-REWORK or DISAGREE = STOP and escalate. AGREE-WITH-CONCERNS = inline-fix-now or document for v0.3.0.

- [ ] **Step 4: Commit**

```bash
git add research/sdlc-bundles/dogfood-workflows/v020-audit-readiness-review.*
git commit -m "review(v020): Phase G architect review — audit-readiness sign-off (Phase G task 38)"
```

---

### Task 39: Final validation + open EPIC PR

**Files:** none (verification + PR open)

- [ ] **Step 1: Run full validation pipeline**

```bash
python3 -m pytest tests/test_assured_*.py tests/test_programme_*.py tests/test_v020_*.py 2>&1 | tail -3
python3 tools/validation/check-plugin-packaging.py 2>&1 | tail -3
python3 tools/validation/local-validation.py --quick 2>&1 | tail -5
python3 tools/validation/local-validation.py --pre-push 2>&1 | tail -10
```

- [ ] **Step 2: Push + open PR**

```bash
git push 2>&1 | tail -3
gh pr create --title "feat: sdlc-assured v0.2.0 — audit-readiness + carry-forward closure (EPIC #188)" --body "$(cat /tmp/v020-pr-body.md)"
```

PR body summarises the 18 items, the 7 phases, the hard gates passed in Phase G, the architect-review sign-off, and the v0.3.0 backlog (any deferred drifters from F-010, any architect-review concerns from Phase G).

- [ ] **Step 3: Wait for CI + merge after green**

Same pattern as #178 PR #187: monitor CI; investigate failures; merge when green.

---

## Self-review

**Spec coverage check:** every section of `docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md` mapped to a task:

| Spec section | Task |
|---|---|
| §3 Phase A — Design decisions | Tasks 1-3 |
| §3 Phase B — Evidence model + parser | Tasks 4-12 + inserts 10A, 11A (data-flow fixes per plan-review P1.1 + P1.2) |
| §3 Phase C — Validator improvements + non-Python adapter | Tasks 13-20 + inserts 16A, 16B (executable wiring per plan-review P1.3) |
| §3 Phase D — ID system + REQ format | Tasks 21-24 |
| §3 Phase E — Quality discipline + skill robustness | Tasks 25-31 |
| §3 Phase F — Audit closure | Task 32 |
| §3 Phase G — Verification dogfood + EPIC closure | Tasks 33-39 |
| §3 18 items mapping | F-001=4-9 + 11A; F-002=12; F-003=7; F-004=24; F-005=23 (with P2.1 ID grammar fix); F-006=22 (with P2.2 per-REQ scope fix) + 10A; F-007=13-16, 16A, 16B; F-008=17; F-009=10A + 11 + 11A; F-010=25-29; F1=31; F4=32; D1=10; D2=20; D3=30; E1=18; E2=19; E3=21 |
| §4 success criteria | Task 36 hard gates + Task 38 architect review |
| §5 out of scope | (no task; spec-level constraint) |

All 18 items covered. **Plan-review (Codex 2026-05-01T06:42:38Z) findings P1.1, P1.2, P1.3, P2.1, P2.2 all incorporated** via 4 new tasks (10A, 11A, 16A, 16B) plus textual fixes in Tasks 22 and 23. Total task count: 43 tasks (was 39).

**Placeholder scan:** every code block contains real content. No "TBD", "TODO", "fill in details". The architect-review verdicts are explicit `<to be filled>` placeholders inside Task 1's addendum content — these are template placeholders the implementer fills in Task 2 Step 4.

**Type consistency:** `EvidenceIndexEntry`, `EvidenceKind`, `EvidenceAdapter`, `EvidenceIndexRegistry`, `EvidenceStatus`, `DependencyExtractor`, `ImportEdge`, `PythonAstExtractor`, `GenericRegexExtractor`, `make_swift_extractor`, `PathSection`, `RemapResult`, `granularity_match` (new signature with `satisfies_graph` kwarg), `orphan_ids` (widened), `forward_annotation_completeness` (new) — all defined once and referenced consistently.

**Phase A exit criterion:** Task 3 is the explicit checkpoint. Risk R9 codifies what to do if a Phase B-G implementation surfaces a missed decision.

**Hard gates:** Task 36 explicitly enumerates the 5 hard gates from spec §3 Phase G sub-stage 3.

---

## Execution

Use `superpowers:subagent-driven-development` to execute this plan task-by-task. Fresh subagent per task; spec-compliance review then code-quality review between tasks. Use a standard model (Sonnet) for the mostly-mechanical TDD tasks (Tasks 4-24); use a more capable model for design-decision tasks (Task 1) and architect-review-driven triage tasks (Tasks 2, 38). The verification-dogfood phase (Tasks 34-36) requires careful metric capture; pair-implementer-and-reviewer if seeded defects don't fire as expected.

## Time budget reality check

The 2026-05-01T06:42:38Z plan review (Codex) noted: *"the stated '25 hours of focused execution' estimate is optimistic. Tasks 9, 11A, 16A, 16B, 17, 19, 28, and 34-36 are integration-heavy and likely to reveal coupling that is not visible in the plan."*

**Use the spec's 20-27 day envelope as the primary budget**, not the optimistic 25-hour estimate. The 4 new plan-review tasks (10A, 11A, 16A, 16B) are themselves integration-heavy — they exist precisely because the original plan under-specified data-flow guarantees. Allow 1-2 extra days for these compared to the original 39-task estimate. Total revised target: 22-29 days.

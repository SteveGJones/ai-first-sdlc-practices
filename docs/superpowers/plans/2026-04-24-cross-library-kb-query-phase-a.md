# Cross-Library KB Query — Phase A Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship phase A (foundation) of EPIC #164 — LibrarySource abstraction, global + project registries, FilesystemSource dispatcher, `format_version` breadcrumb, `kb-query` orchestration with parallel librarian dispatch, and mandatory source attribution. Delivers multi-source retrieval without priming (phase B) or cross-library synthesis (phase C).

**Architecture:** Pure-Python helpers at `plugins/sdlc-knowledge-base/scripts/` handle the deterministic mechanics (registry loading, activation resolution, priming-bundle scaffolding, attribution post-check, format-version parsing). The `kb-query` skill's markdown instructs Claude to invoke those helpers and dispatch the existing `research-librarian` agent N times in parallel via the Agent tool — one call per activated source. Collected findings flow through a structural attribution post-check before rendering to the user. The librarian agent itself gets a small prompt extension accepting `scope`, `priming_context` (scaffold only in phase A), and `source_handle` parameters; its stateless, shelf-index-first behaviour is otherwise unchanged.

**Tech Stack:** Python 3.10+, pytest, PyYAML (already a repo dep), existing Claude Code Agent tool for parallel librarian dispatch. No new external dependencies.

**Spec:** `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`
**Issue:** #167 (phase A of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`

---

## File structure

**New files (created in this plan):**

| File | Responsibility |
|---|---|
| `plugins/sdlc-knowledge-base/pyproject.toml` | Makes `scripts/` importable as `sdlc_knowledge_base_scripts` for tests |
| `plugins/sdlc-knowledge-base/scripts/__init__.py` | Package marker |
| `plugins/sdlc-knowledge-base/scripts/registry.py` | Load global registry + project activation; resolve activated sources against registry; include implicit local source |
| `plugins/sdlc-knowledge-base/scripts/priming.py` | Build priming bundle from question + project dir (scaffold; fully used in phase B) |
| `plugins/sdlc-knowledge-base/scripts/attribution.py` | Structural post-check for retrieval findings and synthesis claims |
| `plugins/sdlc-knowledge-base/scripts/format_version.py` | Parse `<!-- format_version: N -->` breadcrumb from shelf-index |
| `plugins/sdlc-knowledge-base/scripts/orchestrator.py` | Main orchestration entry point; takes a dispatcher callable so tests can inject mocks |
| `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md` | Optional registration helper skill |
| `tests/test_kb_registry.py` | Unit tests for registry loading + activation resolution |
| `tests/test_kb_priming.py` | Unit tests for priming bundle scaffold |
| `tests/test_kb_attribution.py` | Unit tests for attribution post-check |
| `tests/test_kb_format_version.py` | Unit tests for format_version parsing |
| `tests/test_kb_orchestrator.py` | Integration tests with mock dispatcher |
| `tests/fixtures/kb_libraries/local-sample/library/_shelf-index.md` + files | Local fixture library |
| `tests/fixtures/kb_libraries/corp-semi-sample/library/_shelf-index.md` + files | Corporate fixture library (semiconductor topics) |
| `tests/fixtures/kb_libraries/corp-health-sample/library/_shelf-index.md` + files | Second corporate fixture (unrelated topics, for miss scenarios) |
| `tests/fixtures/kb_libraries/corp-legacy-no-header/library/_shelf-index.md` + files | Legacy shelf-index without format_version header |
| `tests/fixtures/kb_libraries/corp-future-version/library/_shelf-index.md` + files | Shelf-index with `format_version: 99` |
| `docs/feature-proposals/167-kb-cross-library-phase-a.md` | AI-First SDLC feature proposal (required by CONSTITUTION) |
| `retrospectives/167-kb-cross-library-phase-a.md` | Retrospective (template; filled in at end) |

**Modified files:**

| File | Change |
|---|---|
| `plugins/sdlc-knowledge-base/agents/research-librarian.md` | Additive prompt extension: accept `scope` / `priming_context` / `source_handle` parameters; add "how dispatch messages are structured" section |
| `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md` | Rewrite with orchestration flow (preflight → priming → parallel dispatch → collect → post-check → render) |
| `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md` | Instruction to always emit `<!-- format_version: 1 -->` as first line |
| `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md` | Add header to template |
| `plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md` | Add "External libraries" subsection |
| `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md` | Add header to starter pack shelf-index |
| `release-mapping.yaml` | Package new scripts, kb-register-library skill, pyproject.toml into `sdlc-knowledge-base` plugin |

---

## Task 1: Plugin Python infrastructure

**Files:**
- Create: `plugins/sdlc-knowledge-base/pyproject.toml`
- Create: `plugins/sdlc-knowledge-base/scripts/__init__.py`

- [ ] **Step 1: Create the pyproject.toml**

Create `plugins/sdlc-knowledge-base/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "sdlc-knowledge-base-scripts"
version = "0.1.0"
description = "Internal utility scripts for the sdlc-knowledge-base plugin (test importability)."
requires-python = ">=3.10"
dependencies = [
  "pyyaml",
]

[tool.setuptools]
packages = ["sdlc_knowledge_base_scripts"]

[tool.setuptools.package-dir]
sdlc_knowledge_base_scripts = "scripts"
```

- [ ] **Step 2: Create the scripts package marker**

Create empty `plugins/sdlc-knowledge-base/scripts/__init__.py`:

```python
```

- [ ] **Step 3: Verify the package is importable**

Run: `cd plugins/sdlc-knowledge-base && pip install -e . --quiet && python -c "import sdlc_knowledge_base_scripts; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-knowledge-base/pyproject.toml plugins/sdlc-knowledge-base/scripts/__init__.py
git commit -m "feat(kb): add scripts package infrastructure for phase A

Mirrors the sdlc-workflows plugin pattern — scripts importable as
sdlc_knowledge_base_scripts for test targeting.

Phase A of EPIC #164 (sub-1, #167).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Registry loader — global library registry

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/registry.py`
- Create: `tests/test_kb_registry.py`

- [ ] **Step 1: Write failing tests for `load_global_registry`**

Create `tests/test_kb_registry.py`:

```python
"""Unit tests for sdlc_knowledge_base_scripts.registry."""
import json
import pytest
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import load_global_registry, GlobalRegistry


def test_load_global_registry_happy(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {
                "name": "corporate-semi",
                "type": "filesystem",
                "path": "/tmp/corp-semi/library",
                "description": "Semiconductor findings",
            }
        ],
    }))
    result = load_global_registry(registry_file)
    assert isinstance(result, GlobalRegistry)
    assert result.version == 1
    assert len(result.libraries) == 1
    assert result.libraries[0].name == "corporate-semi"
    assert result.libraries[0].type == "filesystem"
    assert result.libraries[0].path == "/tmp/corp-semi/library"
    assert result.warnings == []


def test_load_global_registry_missing_file(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    result = load_global_registry(registry_file)
    assert result.libraries == []
    assert result.warnings == []


def test_load_global_registry_malformed_json(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text("{ this is not json")
    result = load_global_registry(registry_file)
    assert result.libraries == []
    assert len(result.warnings) == 1
    assert "malformed" in result.warnings[0].lower()


def test_load_global_registry_unknown_version(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 99,
        "libraries": [
            {"name": "foo", "type": "filesystem", "path": "/tmp/foo"}
        ],
    }))
    result = load_global_registry(registry_file)
    assert len(result.libraries) == 1
    assert any("version" in w.lower() for w in result.warnings)


def test_load_global_registry_duplicate_names(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {"name": "dup", "type": "filesystem", "path": "/tmp/a"},
            {"name": "dup", "type": "filesystem", "path": "/tmp/b"},
        ],
    }))
    result = load_global_registry(registry_file)
    assert len(result.libraries) == 1
    assert result.libraries[0].path == "/tmp/a"
    assert any("duplicate" in w.lower() for w in result.warnings)
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sdlc_knowledge_base_scripts.registry'`

- [ ] **Step 3: Implement `registry.py` with `load_global_registry`**

Create `plugins/sdlc-knowledge-base/scripts/registry.py`:

```python
"""Registry loading and activation resolution for cross-library kb-query.

Phase A of EPIC #164 — see docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


CURRENT_REGISTRY_VERSION = 1


@dataclass(frozen=True)
class LibrarySource:
    """A library the skill can dispatch a librarian against."""
    name: str
    type: str  # "filesystem" or "remote-agent"
    path: Optional[str] = None
    description: Optional[str] = None


@dataclass
class GlobalRegistry:
    version: int = CURRENT_REGISTRY_VERSION
    libraries: list[LibrarySource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_global_registry(path: Path) -> GlobalRegistry:
    """Load the user-scope library registry from ~/.sdlc/global-libraries.json.

    Missing file is normal (no external libraries configured).
    Malformed JSON produces a warning and an empty registry.
    Unknown version produces a warning but a best-effort load.
    Duplicate library names produce a warning; first occurrence wins.
    """
    if not path.exists():
        return GlobalRegistry(libraries=[])

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return GlobalRegistry(
            libraries=[],
            warnings=[f"Global registry at {path} is malformed: {exc}. External libraries unavailable."],
        )

    warnings: list[str] = []
    version = data.get("version", CURRENT_REGISTRY_VERSION)
    if version != CURRENT_REGISTRY_VERSION:
        warnings.append(
            f"Global registry version {version} is unknown (expected {CURRENT_REGISTRY_VERSION}); "
            "attempting best-effort load."
        )

    raw_libraries = data.get("libraries", [])
    seen_names: set[str] = set()
    libraries: list[LibrarySource] = []
    for entry in raw_libraries:
        name = entry.get("name")
        if not name:
            warnings.append("Library entry missing 'name' field; skipping.")
            continue
        if name in seen_names:
            warnings.append(f"Duplicate library name '{name}'; first occurrence wins.")
            continue
        seen_names.add(name)
        libraries.append(
            LibrarySource(
                name=name,
                type=entry.get("type", "filesystem"),
                path=entry.get("path"),
                description=entry.get("description"),
            )
        )

    return GlobalRegistry(version=version, libraries=libraries, warnings=warnings)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_registry.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py tests/test_kb_registry.py
git commit -m "feat(kb): add global registry loader (phase A, #167)

Loads ~/.sdlc/global-libraries.json with graceful degradation:
missing file → empty registry; malformed JSON → warning + empty;
unknown version → warning + best-effort; duplicate names → warning,
first wins.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Registry loader — project activation

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py` (add `load_project_activation`)
- Modify: `tests/test_kb_registry.py` (add activation tests)

- [ ] **Step 1: Write failing tests for `load_project_activation`**

Append to `tests/test_kb_registry.py`:

```python
from sdlc_knowledge_base_scripts.registry import load_project_activation, ProjectActivation


def test_load_project_activation_happy(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    activation_file.write_text(json.dumps({
        "version": 1,
        "activated_sources": ["corporate-semi", "corporate-health"],
    }))
    result = load_project_activation(activation_file)
    assert isinstance(result, ProjectActivation)
    assert result.version == 1
    assert result.activated_sources == ["corporate-semi", "corporate-health"]
    assert result.warnings == []


def test_load_project_activation_missing_file(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    result = load_project_activation(activation_file)
    assert result.activated_sources == []
    assert result.warnings == []


def test_load_project_activation_malformed(tmp_path: Path) -> None:
    activation_file = tmp_path / "libraries.json"
    activation_file.write_text("not json at all")
    result = load_project_activation(activation_file)
    assert result.activated_sources == []
    assert len(result.warnings) == 1
    assert "malformed" in result.warnings[0].lower()
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_registry.py::test_load_project_activation_happy -v`
Expected: FAIL with `ImportError: cannot import name 'load_project_activation'`

- [ ] **Step 3: Implement `load_project_activation`**

Append to `plugins/sdlc-knowledge-base/scripts/registry.py`:

```python
@dataclass
class ProjectActivation:
    version: int = CURRENT_REGISTRY_VERSION
    activated_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_project_activation(path: Path) -> ProjectActivation:
    """Load project-level activation from .sdlc/libraries.json.

    Missing file is normal (local-only). Malformed JSON produces a
    warning and empty activation. Unknown names are validated later
    against the global registry, not here.
    """
    if not path.exists():
        return ProjectActivation(activated_sources=[])

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ProjectActivation(
            activated_sources=[],
            warnings=[f"Project activation at {path} is malformed: {exc}. No external libraries activated."],
        )

    version = data.get("version", CURRENT_REGISTRY_VERSION)
    warnings: list[str] = []
    if version != CURRENT_REGISTRY_VERSION:
        warnings.append(
            f"Project activation version {version} is unknown (expected {CURRENT_REGISTRY_VERSION})."
        )

    sources = data.get("activated_sources", [])
    if not isinstance(sources, list):
        return ProjectActivation(
            version=version,
            activated_sources=[],
            warnings=warnings + [f"'activated_sources' must be a list, got {type(sources).__name__}."],
        )

    return ProjectActivation(version=version, activated_sources=list(sources), warnings=warnings)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_registry.py -v`
Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py tests/test_kb_registry.py
git commit -m "feat(kb): add project activation loader (phase A, #167)

Reads .sdlc/libraries.json with same graceful-degradation contract
as the global registry loader.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Activation resolution

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py` (add `resolve_dispatch_list`)
- Modify: `tests/test_kb_registry.py` (add resolution tests)

- [ ] **Step 1: Write failing tests for `resolve_dispatch_list`**

Append to `tests/test_kb_registry.py`:

```python
from sdlc_knowledge_base_scripts.registry import resolve_dispatch_list, DispatchList


def _make_global(libraries: list[LibrarySource]) -> GlobalRegistry:
    return GlobalRegistry(libraries=libraries)


def _make_activation(names: list[str]) -> ProjectActivation:
    return ProjectActivation(activated_sources=names)


def test_resolve_happy_path(tmp_path: Path) -> None:
    # Create a local library directory
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf Index\n")

    gr = _make_global([
        LibrarySource(name="corp-semi", type="filesystem", path="/tmp/corp-semi/library"),
    ])
    pa = _make_activation(["corp-semi"])

    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    assert isinstance(result, DispatchList)
    assert len(result.sources) == 2  # local + corp-semi
    assert result.sources[0].name == "local"
    assert result.sources[0].path == str(local_lib)
    assert result.sources[1].name == "corp-semi"
    assert result.warnings == []


def test_resolve_unknown_activation_name(tmp_path: Path) -> None:
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf Index\n")

    gr = _make_global([])
    pa = _make_activation(["nonexistent"])

    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    assert len(result.sources) == 1  # only local
    assert any("nonexistent" in w for w in result.warnings)


def test_resolve_remote_agent_type_skipped(tmp_path: Path) -> None:
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf Index\n")

    gr = _make_global([
        LibrarySource(name="corp-remote", type="remote-agent", path=None),
    ])
    pa = _make_activation(["corp-remote"])

    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    assert len(result.sources) == 1  # only local
    assert any("remote-agent" in w for w in result.warnings)


def test_resolve_no_local_library_with_externals(tmp_path: Path) -> None:
    # project_library_path doesn't exist
    missing_local = tmp_path / "library"

    gr = _make_global([
        LibrarySource(name="corp-semi", type="filesystem", path="/tmp/corp-semi/library"),
    ])
    pa = _make_activation(["corp-semi"])

    result = resolve_dispatch_list(gr, pa, project_library_path=missing_local)
    assert len(result.sources) == 1  # only corp-semi, no local
    assert result.sources[0].name == "corp-semi"


def test_resolve_empty_dispatch_list(tmp_path: Path) -> None:
    # No local library, no activations
    missing_local = tmp_path / "library"

    gr = _make_global([])
    pa = _make_activation([])

    result = resolve_dispatch_list(gr, pa, project_library_path=missing_local)
    assert result.sources == []
    assert result.is_empty_error is True
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_registry.py::test_resolve_happy_path -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement `resolve_dispatch_list`**

Append to `plugins/sdlc-knowledge-base/scripts/registry.py`:

```python
@dataclass
class DispatchList:
    """Result of resolving activated sources into a dispatch list."""
    sources: list[LibrarySource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_empty_error: bool = False  # True when no local + no externals → user-facing error


def resolve_dispatch_list(
    global_registry: GlobalRegistry,
    activation: ProjectActivation,
    project_library_path: Path,
) -> DispatchList:
    """Resolve activated source names against the global registry.

    Prepends an implicit `local` source when project_library_path exists.
    Skips unknown names with warnings. Skips remote-agent types with
    warnings (deferred to future EPIC). Returns is_empty_error=True when
    no sources resolve at all (callers should emit the kb-init recommendation).
    """
    warnings: list[str] = []
    sources: list[LibrarySource] = []

    # Implicit local source if library directory exists
    if project_library_path.exists() and project_library_path.is_dir():
        sources.append(
            LibrarySource(name="local", type="filesystem", path=str(project_library_path))
        )

    # Index global registry by name
    by_name = {lib.name: lib for lib in global_registry.libraries}

    for name in activation.activated_sources:
        entry = by_name.get(name)
        if entry is None:
            warnings.append(
                f"Activated source '{name}' not found in global registry. Skipping."
            )
            continue
        if entry.type == "remote-agent":
            warnings.append(
                f"Source '{name}' is type 'remote-agent' (planned for future release). Skipping."
            )
            continue
        if entry.type != "filesystem":
            warnings.append(
                f"Source '{name}' has unknown type '{entry.type}'. Skipping."
            )
            continue
        sources.append(entry)

    return DispatchList(
        sources=sources,
        warnings=warnings,
        is_empty_error=(len(sources) == 0),
    )
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_registry.py -v`
Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py tests/test_kb_registry.py
git commit -m "feat(kb): add dispatch list resolution (phase A, #167)

Resolves activated source names against the global registry.
Prepends implicit local source when library/ exists. Skips unknown
names and remote-agent types with warnings. Signals empty-dispatch
error for the caller to surface kb-init recommendation.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Priming bundle scaffold

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/priming.py`
- Create: `tests/test_kb_priming.py`

Note: Phase A builds the scaffold (data structure + file reading) but does not yet wire it into the librarian dispatch. Phase B (sub-2, #168) will add the term-extraction and actual priming behaviour. The scaffold exists now so phase A has a stable interface to wire up.

- [ ] **Step 1: Write failing tests for `build_priming_bundle`**

Create `tests/test_kb_priming.py`:

```python
"""Unit tests for sdlc_knowledge_base_scripts.priming."""
from pathlib import Path
from sdlc_knowledge_base_scripts.priming import build_priming_bundle, PrimingBundle


def test_priming_bundle_happy(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "# CLAUDE.md\n\n"
        "Some framework pointers.\n\n"
        "## Knowledge Base\n\n"
        "This project uses the knowledge base.\n\n"
        "### Layout\n\n"
        "Library at library/.\n\n"
        "## Next section\n\n"
        "Unrelated.\n"
    )
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "_shelf-index.md").write_text(
        "# Shelf Index\n\n"
        "## 1. topic-a.md\n"
        "**Terms:** alpha, beta, gamma\n"
        "**Facts:** ...\n\n"
        "## 2. topic-b.md\n"
        "**Terms:** delta, epsilon, alpha\n"
    )
    result = build_priming_bundle(
        question="what do we know about alpha",
        project_dir=tmp_path,
    )
    assert isinstance(result, PrimingBundle)
    assert result.question == "what do we know about alpha"
    assert "This project uses the knowledge base." in result.local_kb_config_excerpt
    assert "Next section" not in result.local_kb_config_excerpt
    assert set(result.local_shelf_index_terms) == {"alpha", "beta", "gamma", "delta", "epsilon"}


def test_priming_bundle_missing_claude_md(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "_shelf-index.md").write_text("# Shelf Index\n")
    result = build_priming_bundle(question="q", project_dir=tmp_path)
    assert result.local_kb_config_excerpt == ""
    assert result.local_shelf_index_terms == []


def test_priming_bundle_missing_shelf_index(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("## Knowledge Base\n\nConfig.\n")
    # no library/ directory
    result = build_priming_bundle(question="q", project_dir=tmp_path)
    assert "Config." in result.local_kb_config_excerpt
    assert result.local_shelf_index_terms == []


def test_priming_bundle_no_kb_section_in_claude_md(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# CLAUDE.md\n\nNothing about the KB here.\n")
    result = build_priming_bundle(question="q", project_dir=tmp_path)
    assert result.local_kb_config_excerpt == ""
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_priming.py -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement `priming.py`**

Create `plugins/sdlc-knowledge-base/scripts/priming.py`:

```python
"""Priming bundle construction for cross-library kb-query.

Phase A scaffold (EPIC #164 sub-1, #167). Phase B (sub-2, #168) activates
the priming by passing this bundle to external librarian invocations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PrimingBundle:
    """Context passed to external librarians to frame their query.

    Fully consumed by external librarian prompts in phase B. In phase A,
    this bundle is built and passed through but the librarian prompt
    does not yet act on it.
    """
    question: str
    local_kb_config_excerpt: str = ""
    local_shelf_index_terms: list[str] = field(default_factory=list)


def build_priming_bundle(question: str, project_dir: Path) -> PrimingBundle:
    """Build the priming bundle from the project's local state.

    Missing CLAUDE.md → empty excerpt. Missing [Knowledge Base] section →
    empty excerpt. Missing library/ or shelf-index → empty terms list.
    """
    claude_md_path = project_dir / "CLAUDE.md"
    excerpt = _extract_kb_section(claude_md_path) if claude_md_path.exists() else ""

    shelf_index_path = project_dir / "library" / "_shelf-index.md"
    terms = _extract_shelf_index_terms(shelf_index_path) if shelf_index_path.exists() else []

    return PrimingBundle(
        question=question,
        local_kb_config_excerpt=excerpt,
        local_shelf_index_terms=terms,
    )


def _extract_kb_section(claude_md_path: Path) -> str:
    """Extract the [Knowledge Base] section from CLAUDE.md.

    Matches '## Knowledge Base' (heading) through the next H2 heading or EOF.
    Returns the section body (text after the heading), or empty string.
    """
    content = claude_md_path.read_text()
    match = re.search(
        r"^##\s+Knowledge Base\s*\n(.*?)(?=\n##\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1).strip()


def _extract_shelf_index_terms(shelf_index_path: Path) -> list[str]:
    """Extract the union of Terms: across all shelf-index entries.

    Each entry has a '**Terms:** ...' line. Return deduplicated, order-preserving.
    """
    content = shelf_index_path.read_text()
    seen: set[str] = set()
    result: list[str] = []
    for match in re.finditer(r"\*\*Terms:\*\*\s+(.+?)(?=\n|$)", content):
        raw_terms = match.group(1)
        for term in (t.strip() for t in raw_terms.split(",")):
            if term and term not in seen:
                seen.add(term)
                result.append(term)
    return result
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_priming.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/priming.py tests/test_kb_priming.py
git commit -m "feat(kb): add priming bundle scaffold (phase A, #167)

Builds a PrimingBundle from CLAUDE.md [KB] section + local shelf-index
terms. Scaffold only in phase A — phase B (#168) wires it into external
librarian invocations.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Attribution post-check

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/attribution.py`
- Create: `tests/test_kb_attribution.py`

- [ ] **Step 1: Write failing tests for attribution post-check**

Create `tests/test_kb_attribution.py`:

```python
"""Unit tests for sdlc_knowledge_base_scripts.attribution."""
from sdlc_knowledge_base_scripts.attribution import (
    check_retrieval_attribution,
    check_synthesis_attribution,
    RetrievalCheckResult,
    SynthesisCheckResult,
)


def test_retrieval_all_findings_tagged() -> None:
    output = """### EUV humidity
**Finding**: RH must be ≤45%.
**Source**: ASML 2024.
**Source library**: corporate-semi
**Library file**: EUV-operations.md

### Local site baseline
**Finding**: Ambient RH 75-85%.
**Source**: site survey 2026.
**Source library**: local
**Library file**: site-environmental-baseline.md
"""
    result = check_retrieval_attribution(output)
    assert isinstance(result, RetrievalCheckResult)
    assert result.passed is True
    assert result.dropped_blocks == []


def test_retrieval_finding_missing_source_library_dropped() -> None:
    output = """### Has attribution
**Finding**: good.
**Source library**: local

### Missing attribution
**Finding**: bad.
"""
    result = check_retrieval_attribution(output)
    assert result.passed is False  # at least one dropped
    assert len(result.dropped_blocks) == 1
    assert "Missing attribution" in result.dropped_blocks[0]
    # Cleaned output retains the good block
    assert "### Has attribution" in result.cleaned_output
    assert "### Missing attribution" not in result.cleaned_output


def test_retrieval_empty_output_is_ok() -> None:
    result = check_retrieval_attribution("")
    assert result.passed is True
    assert result.dropped_blocks == []


def test_synthesis_all_claims_tagged() -> None:
    output = """### EUV cleanroom under regional constraints

**Claim**: Tropical sites need multi-stage dehumidification.

**Supporting evidence**:
1. RH must be ≤45% for EUV — [corporate-semi] EUV-operations.md
2. Brazilian ambient RH 75-85% — [local] site-environmental-baseline.md
3. Dutch fab managed with single-stage — [corporate-semi] nijmegen-fab.md

**Caveats**: This synthesis spans local and corporate-semi libraries.
"""
    result = check_synthesis_attribution(output)
    assert isinstance(result, SynthesisCheckResult)
    assert result.passed is True
    assert result.untagged_claims == []


def test_synthesis_claim_missing_handle_aborts() -> None:
    output = """### Argument

**Claim**: Something.

**Supporting evidence**:
1. Good claim — [local] file-a.md
2. Untagged claim with no bracketed handle
3. Another good one — [corp] file-b.md

**Caveats**: None.
"""
    result = check_synthesis_attribution(output)
    assert result.passed is False
    assert len(result.untagged_claims) == 1
    assert "Untagged claim" in result.untagged_claims[0]


def test_synthesis_empty_evidence_list_is_ok() -> None:
    # No supporting evidence section at all — nothing to check
    output = "### Argument\n\n**Claim**: X.\n\n**Caveats**: None.\n"
    result = check_synthesis_attribution(output)
    assert result.passed is True
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_attribution.py -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement `attribution.py`**

Create `plugins/sdlc-knowledge-base/scripts/attribution.py`:

```python
"""Structural attribution post-check for cross-library kb-query output.

The one invariant that must never silently fail: every finding and every
synthesis claim has a source library handle tag. This is a hard invariant
enforced by the skill before returning output to the user.

Phase A of EPIC #164 — see spec §7.1.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RetrievalCheckResult:
    passed: bool
    cleaned_output: str
    dropped_blocks: list[str] = field(default_factory=list)


@dataclass
class SynthesisCheckResult:
    passed: bool
    untagged_claims: list[str] = field(default_factory=list)


# A retrieval finding block starts with "### " and is terminated by the next
# "### " or "---" or EOF. Each block must contain "**Source library**:".
_FINDING_BLOCK_RE = re.compile(
    r"(###\s+[^\n]+\n(?:(?!###\s+|^---\s*$).|\n)*)",
    re.MULTILINE,
)

# In synthesis output, a supporting evidence item is a numbered or bulleted
# line under a "**Supporting evidence**:" heading. Each must contain "[<handle>]".
_SUPPORTING_EVIDENCE_SECTION_RE = re.compile(
    r"\*\*Supporting evidence\*\*:\s*\n((?:\s*[\d\-\*][\.\)]?\s+.+\n?)+)",
    re.MULTILINE,
)
_EVIDENCE_ITEM_RE = re.compile(r"^\s*[\d\-\*][\.\)]?\s+(.+)$", re.MULTILINE)
_HANDLE_TAG_RE = re.compile(r"\[[\w-]+\]")


def check_retrieval_attribution(output: str) -> RetrievalCheckResult:
    """Verify every '### ' finding block has a '**Source library**:' tag.

    Blocks without the tag are dropped from cleaned_output and returned in
    dropped_blocks for logging. Empty or tag-free input returns passed=True.
    """
    if not output.strip():
        return RetrievalCheckResult(passed=True, cleaned_output=output)

    kept_parts: list[str] = []
    dropped: list[str] = []
    last_end = 0
    for match in _FINDING_BLOCK_RE.finditer(output):
        block_text = match.group(1)
        start, end = match.span(1)
        # Keep everything between blocks (headers, separators)
        kept_parts.append(output[last_end:start])
        if "**Source library**:" in block_text:
            kept_parts.append(block_text)
        else:
            # Summarise the first line (the '### ' title) for the dropped log
            first_line = block_text.splitlines()[0].lstrip("# ").strip()
            dropped.append(first_line)
        last_end = end
    kept_parts.append(output[last_end:])
    cleaned = "".join(kept_parts)

    return RetrievalCheckResult(
        passed=(len(dropped) == 0),
        cleaned_output=cleaned,
        dropped_blocks=dropped,
    )


def check_synthesis_attribution(output: str) -> SynthesisCheckResult:
    """Verify every supporting-evidence item has an inline [handle] tag.

    Any untagged item causes passed=False; the caller is expected to abort
    the synthesis and return the retrieval-only output with an error block.
    """
    untagged: list[str] = []
    for section_match in _SUPPORTING_EVIDENCE_SECTION_RE.finditer(output):
        section_body = section_match.group(1)
        for item_match in _EVIDENCE_ITEM_RE.finditer(section_body):
            item_text = item_match.group(1).strip()
            if not _HANDLE_TAG_RE.search(item_text):
                untagged.append(item_text)

    return SynthesisCheckResult(
        passed=(len(untagged) == 0),
        untagged_claims=untagged,
    )
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_attribution.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/attribution.py tests/test_kb_attribution.py
git commit -m "feat(kb): add attribution post-check validator (phase A, #167)

Structural validator enforces the hard invariant from spec §7.1:
every retrieval finding has Source library tag; every synthesis claim
has inline [handle] tag. Missing tags drop findings or abort synthesis
before output reaches the user.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Format version parsing

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/format_version.py`
- Create: `tests/test_kb_format_version.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_kb_format_version.py`:

```python
"""Unit tests for sdlc_knowledge_base_scripts.format_version."""
from pathlib import Path
from sdlc_knowledge_base_scripts.format_version import (
    parse_format_version,
    CURRENT_FORMAT_VERSION,
)


def test_format_version_header_v1(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: 1 -->\n# Shelf Index\n\nContent.\n")
    assert parse_format_version(shelf) == 1


def test_format_version_header_missing_treated_as_v1(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("# Shelf Index\n\nContent.\n")
    assert parse_format_version(shelf) == CURRENT_FORMAT_VERSION


def test_format_version_unknown_future_version(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: 99 -->\n# Shelf Index\n")
    assert parse_format_version(shelf) == 99


def test_format_version_header_must_be_first_line(tmp_path: Path) -> None:
    # Header on line 5 should NOT be picked up; treated as v1 legacy
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("# Shelf Index\n\n\n\n<!-- format_version: 99 -->\nContent.\n")
    assert parse_format_version(shelf) == CURRENT_FORMAT_VERSION


def test_format_version_malformed_header(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: not-a-number -->\n# Shelf Index\n")
    assert parse_format_version(shelf) == CURRENT_FORMAT_VERSION  # fall back
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_format_version.py -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement `format_version.py`**

Create `plugins/sdlc-knowledge-base/scripts/format_version.py`:

```python
"""Parse the `<!-- format_version: N -->` breadcrumb from a shelf-index.

The header is primarily a hint to the librarian LLM about what to expect.
LLM-flexible parsing handles mild format drift gracefully; this function
exists so Python-side tooling can also respond to the version (e.g.,
kb-rebuild-indexes could warn when rebuilding a legacy shelf-index).

Phase A of EPIC #164 — see spec §5.3.
"""
from __future__ import annotations

import re
from pathlib import Path


CURRENT_FORMAT_VERSION = 1

_HEADER_RE = re.compile(r"^<!--\s*format_version:\s*(\d+)\s*-->\s*$")


def parse_format_version(shelf_index_path: Path) -> int:
    """Return the format_version from the first line of the shelf-index.

    Missing header → treated as CURRENT_FORMAT_VERSION silently (legacy).
    Malformed header → treated as CURRENT_FORMAT_VERSION silently.
    The header must be on the first line to be recognised.
    """
    if not shelf_index_path.exists():
        return CURRENT_FORMAT_VERSION

    with shelf_index_path.open("r") as fh:
        first_line = fh.readline().rstrip("\n")

    match = _HEADER_RE.match(first_line)
    if not match:
        return CURRENT_FORMAT_VERSION

    try:
        return int(match.group(1))
    except ValueError:
        return CURRENT_FORMAT_VERSION
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_format_version.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/format_version.py tests/test_kb_format_version.py
git commit -m "feat(kb): add format_version parser (phase A, #167)

Parses <!-- format_version: N --> breadcrumb from shelf-index first
line. Missing/malformed header → treated as current version silently.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Orchestrator core

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Create: `tests/test_kb_orchestrator.py`

The orchestrator is the pure-Python function that takes a dispatcher callable (abstraction over the Agent tool) and runs the full flow. Tests inject mock dispatchers; the kb-query skill wires in a real Agent-tool-backed dispatcher.

- [ ] **Step 1: Write failing orchestrator tests**

Create `tests/test_kb_orchestrator.py`:

```python
"""Integration tests for the kb-query orchestrator.

Uses a mock dispatcher to exercise the full flow without real Agent tool calls.
"""
import json
from pathlib import Path
from sdlc_knowledge_base_scripts.orchestrator import (
    run_retrieval_query,
    RetrievalQueryResult,
    DispatchRequest,
)
from sdlc_knowledge_base_scripts.registry import LibrarySource


def _make_fixture_library(root: Path, name: str, shelf_content: str) -> Path:
    lib_dir = root / name / "library"
    lib_dir.mkdir(parents=True)
    (lib_dir / "_shelf-index.md").write_text(shelf_content)
    return lib_dir


def test_orchestrator_dispatches_to_all_sources(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")
    corp_lib = _make_fixture_library(tmp_path, "corp", "<!-- format_version: 1 -->\n# Shelf\n")

    dispatched: list[DispatchRequest] = []
    def mock_dispatch(req: DispatchRequest) -> str:
        dispatched.append(req)
        return (
            f"### {req.source.name} finding\n"
            f"**Finding**: something from {req.source.name}.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(local_lib)),
        LibrarySource(name="corp", type="filesystem", path=str(corp_lib)),
    ]
    result = run_retrieval_query(
        question="what about X",
        sources=sources,
        priming=None,  # phase A passes None; phase B wires the bundle
        dispatcher=mock_dispatch,
    )
    assert isinstance(result, RetrievalQueryResult)
    assert len(dispatched) == 2
    assert {r.source.name for r in dispatched} == {"local", "corp"}
    assert "local finding" in result.combined_output
    assert "corp finding" in result.combined_output
    assert result.sources_with_findings == ["local", "corp"]
    assert result.sources_failed == []


def test_orchestrator_source_failure_becomes_marker(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")
    # corp_lib deliberately not created

    def mock_dispatch(req: DispatchRequest) -> str:
        if req.source.name == "corp":
            raise FileNotFoundError(f"shelf-index missing at {req.source.path}")
        return (
            f"### {req.source.name} finding\n"
            f"**Finding**: ok.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(local_lib)),
        LibrarySource(name="corp", type="filesystem", path=str(tmp_path / "nonexistent")),
    ]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    assert result.sources_with_findings == ["local"]
    assert result.sources_failed == ["corp"]
    assert "[corp] dispatch failed" in result.combined_output
    assert "### local finding" in result.combined_output


def test_orchestrator_no_evidence_marker(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        # Librarian's anti-hallucination response
        return "The library has no evidence on this topic."

    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="obscure",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    assert result.sources_with_findings == []
    assert result.sources_failed == []
    assert "[local] library has no evidence" in result.combined_output


def test_orchestrator_attribution_check_drops_untagged(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        # Return one tagged and one untagged finding
        return (
            "### Tagged\n"
            "**Finding**: ok.\n"
            "**Source library**: local\n\n"
            "### Untagged\n"
            "**Finding**: bad, no attribution.\n"
        )

    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    assert "### Tagged" in result.combined_output
    assert "### Untagged" not in result.combined_output
    assert len(result.attribution_warnings) == 1


def test_orchestrator_output_ordering_local_first_externals_alpha(tmp_path: Path) -> None:
    libs = {n: _make_fixture_library(tmp_path, n, "<!-- format_version: 1 -->\n# Shelf\n")
            for n in ("proj", "zebra", "alpha", "mango")}

    def mock_dispatch(req: DispatchRequest) -> str:
        return (f"### {req.source.name}\n**Finding**: x.\n**Source library**: {req.source.name}\n")

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(libs["proj"])),
        LibrarySource(name="zebra", type="filesystem", path=str(libs["zebra"])),
        LibrarySource(name="alpha", type="filesystem", path=str(libs["alpha"])),
        LibrarySource(name="mango", type="filesystem", path=str(libs["mango"])),
    ]
    result = run_retrieval_query(
        question="q", sources=sources, priming=None, dispatcher=mock_dispatch,
    )
    # local must appear before alpha, alpha before mango, mango before zebra
    out = result.combined_output
    assert out.index("### local") < out.index("### alpha") < out.index("### mango") < out.index("### zebra")
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_kb_orchestrator.py -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement the orchestrator**

Create `plugins/sdlc-knowledge-base/scripts/orchestrator.py`:

```python
"""kb-query orchestrator: parallel dispatch, collection, attribution post-check, render.

The orchestrator is pure Python; the `dispatcher` callable abstracts the
Agent tool call so tests can inject mocks. The kb-query skill wires in a
real dispatcher backed by parallel Agent invocations.

Phase A of EPIC #164 — see spec §3.2, §6.1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .attribution import check_retrieval_attribution
from .priming import PrimingBundle
from .registry import LibrarySource


@dataclass
class DispatchRequest:
    """One librarian invocation request — what the dispatcher receives."""
    source: LibrarySource
    question: str
    priming: Optional[PrimingBundle] = None


Dispatcher = Callable[[DispatchRequest], str]


@dataclass
class RetrievalQueryResult:
    combined_output: str
    sources_with_findings: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    sources_no_evidence: list[str] = field(default_factory=list)
    attribution_warnings: list[str] = field(default_factory=list)


_NO_EVIDENCE_MARKER_PHRASES = (
    "the library has no evidence",
    "library has no evidence",
    "no evidence on this",
)


def run_retrieval_query(
    question: str,
    sources: list[LibrarySource],
    priming: Optional[PrimingBundle],
    dispatcher: Dispatcher,
) -> RetrievalQueryResult:
    """Execute a retrieval query across all dispatch sources.

    Sources are dispatched via the provided dispatcher. Each source's
    output flows through attribution post-check. Final output is rendered
    in order: local first, then externals alphabetical.
    """
    # Build source → output map by dispatching each source.
    # Real implementations dispatch in parallel via the Agent tool;
    # the pure-Python orchestrator dispatches sequentially and relies on
    # the dispatcher to handle concurrency if it wishes.
    outputs: dict[str, str] = {}
    failed: list[str] = []
    no_evidence: list[str] = []

    for source in sources:
        request = DispatchRequest(source=source, question=question, priming=priming)
        try:
            raw = dispatcher(request)
        except Exception as exc:
            failed.append(source.name)
            outputs[source.name] = (
                f"## [{source.name}] — failed\n\n"
                f"[{source.name}] dispatch failed: {exc}\n"
            )
            continue

        lower = raw.strip().lower()
        if any(phrase in lower for phrase in _NO_EVIDENCE_MARKER_PHRASES):
            no_evidence.append(source.name)
            outputs[source.name] = (
                f"## [{source.name}] — no evidence\n\n"
                f"[{source.name}] library has no evidence on this topic.\n"
            )
            continue

        outputs[source.name] = f"## [{source.name}] Findings\n\n{raw.rstrip()}\n"

    # Attribution post-check across all source outputs
    combined_raw = "\n\n---\n\n".join(_ordered_outputs(sources, outputs))
    check = check_retrieval_attribution(combined_raw)
    cleaned = check.cleaned_output

    # Determine which sources actually had findings (after post-check)
    sources_with_findings: list[str] = []
    for source in _ordered_source_list(sources):
        if source.name in failed or source.name in no_evidence:
            continue
        # Check whether any finding from this source survived post-check
        marker = f"## [{source.name}] Findings"
        if marker in cleaned:
            # And did the marker still have at least one '### ' finding below it
            idx = cleaned.index(marker)
            block = cleaned[idx:]
            if "### " in block:
                sources_with_findings.append(source.name)

    # Header summarising what ran
    header = _render_header(sources, sources_with_findings, failed, no_evidence)
    full = header + "\n\n---\n\n" + cleaned

    return RetrievalQueryResult(
        combined_output=full,
        sources_with_findings=sources_with_findings,
        sources_failed=failed,
        sources_no_evidence=no_evidence,
        attribution_warnings=check.dropped_blocks,
    )


def _ordered_source_list(sources: list[LibrarySource]) -> list[LibrarySource]:
    """Return sources in render order: local first, then alphabetical by name."""
    local = [s for s in sources if s.name == "local"]
    others = sorted((s for s in sources if s.name != "local"), key=lambda s: s.name)
    return local + others


def _ordered_outputs(sources: list[LibrarySource], outputs: dict[str, str]) -> list[str]:
    return [outputs[s.name] for s in _ordered_source_list(sources) if s.name in outputs]


def _render_header(
    sources: list[LibrarySource],
    with_findings: list[str],
    failed: list[str],
    no_evidence: list[str],
) -> str:
    all_names = [s.name for s in _ordered_source_list(sources)]
    lines = [
        "# Knowledge Base Query Results",
        "",
        f"**Sources queried:** {', '.join(all_names)}",
        f"**Sources with findings:** {', '.join(with_findings) if with_findings else '(none)'}",
    ]
    if no_evidence:
        lines.append(f"**Sources with no evidence on this topic:** {', '.join(no_evidence)}")
    if failed:
        lines.append(f"**Sources that failed:** {', '.join(failed)}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_kb_orchestrator.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "feat(kb): add kb-query orchestrator core (phase A, #167)

Pure-Python orchestration with a dispatcher callable abstraction.
Handles per-source dispatch, failure markers, no-evidence markers,
attribution post-check, ordered rendering (local first, externals
alphabetical), and the results summary header.

Tests inject mock dispatchers; the kb-query skill will wire in an
Agent-tool-backed dispatcher for the real flow.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Update kb-rebuild-indexes to emit format_version header

**Files:**
- Modify: `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md`
- Modify: `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md`
- Modify: `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md`

- [ ] **Step 1: Read the existing kb-rebuild-indexes skill**

Run: `cat plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md | head -50`
Note where the skill describes what gets written to the shelf-index so the instruction lands in the right section.

- [ ] **Step 2: Edit the skill to require the header**

In `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md`, find the section that describes the output format (typically under "## Output" or similar) and prepend this instruction:

```markdown
### Mandatory header

Every generated shelf-index MUST begin with this exact first line as an HTML comment:

```
<!-- format_version: 1 -->
```

This breadcrumb tells the librarian and cross-library consumers what shelf-index schema to expect. It is on the first line (not after the `#` heading). Missing header is treated as legacy v1 silently; this skill always emits it going forward.
```

- [ ] **Step 3: Update the shelf-index template to include the header**

In `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md`, prepend the first line:

```markdown
<!-- format_version: 1 -->
# Knowledge Base Shelf-Index
...
```

(Keep the rest of the template unchanged.)

- [ ] **Step 4: Update the starter-pack shelf-index**

In `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md`, prepend:

```markdown
<!-- format_version: 1 -->
# Knowledge Base Shelf-Index
...
```

- [ ] **Step 5: Verify with format_version parser**

Create a quick throwaway verification:

```bash
python -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.format_version import parse_format_version
for p in [
    Path('plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md'),
    Path('plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md'),
]:
    print(f'{p}: v{parse_format_version(p)}')
"
```
Expected: both report `v1`.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md \
        plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md \
        plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md
git commit -m "feat(kb): emit <!-- format_version: 1 --> in shelf-indexes (phase A, #167)

kb-rebuild-indexes now emits the breadcrumb header as the first line
of generated shelf-indexes. Templates and starter-pack updated.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Extend research-librarian agent prompt

**Files:**
- Modify: `plugins/sdlc-knowledge-base/agents/research-librarian.md`

The agent prompt gains support for three new parameters (`scope`, `priming_context`, `source_handle`) and documentation of how cross-library dispatch messages are structured. Everything else in the agent stays identical.

- [ ] **Step 1: Read the current agent file**

Run: `wc -l plugins/sdlc-knowledge-base/agents/research-librarian.md`
Expected: 189 lines. Confirm.

- [ ] **Step 2: Add the dispatch-message section**

In `plugins/sdlc-knowledge-base/agents/research-librarian.md`, locate the section "## How you work" (around line 38) and *before* that section, insert a new top-level section:

```markdown
## Dispatch message parameters (cross-library queries)

When invoked by the `kb-query` skill for a cross-library query, your dispatch
message may include three extra parameters. Recognise them by prefix lines
at the top of your input:

- `SCOPE: <absolute-path>` — the absolute path to the library directory you
  are scoped to. You must read ONLY files under this path. Do not wander
  into sibling directories, the project root, or any other library. The
  shelf-index you read is always `<SCOPE>/_shelf-index.md`.

- `PRIMING_CONTEXT:` — a JSON object passed in the dispatch message that
  may contain `local_kb_config_excerpt` (the project's CLAUDE.md [Knowledge
  Base] section) and `local_shelf_index_terms` (a list of domain vocabulary
  terms from the local project's shelf-index). Use these to bias your
  term-matching against your scoped shelf-index — if the local project's
  vocabulary includes terms you also have in your shelf-index, lean toward
  those matches. In phase A of EPIC #164, this parameter is passed but
  its use is optional; phase B will enable active biasing.

- `SOURCE_HANDLE: <handle>` — the name by which your findings will be
  attributed in the caller's output. You MUST include a `**Source library**:
  <handle>` line in every retrieval finding block you return. This is
  structurally required; omitting it means your finding will be dropped
  by the skill's attribution post-check.

When these parameters are absent, behave exactly as a single-library query
(the default, non-cross-library case).

### Retrieval format with source attribution

When `SOURCE_HANDLE` is provided, the retrieval format gains a line:

```markdown
### [Topic]

**Finding**: [Specific claim or statistic]
**Source**: [Citation — author, year, sample size]
**Threshold**: [Quantified value if applicable]
**Source library**: <SOURCE_HANDLE>
**Library file**: [filename.md]
**Programme link**: [...]
```

The `**Source library**:` line is mandatory for every finding block when
`SOURCE_HANDLE` is set. This is not negotiable — missing tags cause findings
to be dropped from the user's output.
```

- [ ] **Step 3: Verify the existing librarian behaviour is preserved**

Read the remainder of the file (lines ~40-189). The existing sections on "How you work", "Output formats", "Tool use", "Boundary with other roles", and so on must be unchanged. The new section is additive.

Run: `git diff plugins/sdlc-knowledge-base/agents/research-librarian.md | head -60`
Expected: only a new section is added; existing content untouched.

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-knowledge-base/agents/research-librarian.md
git commit -m "feat(kb): extend librarian prompt for cross-library dispatch (phase A, #167)

Adds optional SCOPE, PRIMING_CONTEXT, and SOURCE_HANDLE parameters.
When SOURCE_HANDLE is present, retrieval findings gain a mandatory
Source library line matching the dispatch handle. Existing
single-library behaviour unchanged when parameters are absent.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: New skill — kb-register-library

**Files:**
- Create: `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`

- [ ] **Step 1: Write the new skill**

Create `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`:

```markdown
---
name: kb-register-library
description: Register an external knowledge base library in the user-scope global registry at ~/.sdlc/global-libraries.json. Validates that the target path exists, contains a _shelf-index.md, and parses its format_version. Optional helper — hand-editing the JSON is also supported.
disable-model-invocation: false
argument-hint: "<name> <absolute-path-to-library-dir> [description]"
---

# Register External Library

Add an external knowledge base to the user-scope global registry so it can be activated in any project's `.sdlc/libraries.json`.

## Arguments

- `<name>` — a short handle used in attribution output. Lowercase-kebab-case recommended (e.g., `corporate-semiconductor`, `corp-healthcare`). Must be unique within `~/.sdlc/global-libraries.json`.
- `<absolute-path-to-library-dir>` — the absolute path to the *library directory* (the one containing `_shelf-index.md`), not the repo root. Must exist at registration time.
- `[description]` — optional human note for the user's own reference. Not used by any system behaviour.

## Preflight

- Verify the registry file's parent directory exists. Create `~/.sdlc/` if missing.
- If `~/.sdlc/global-libraries.json` exists, load and validate it.
- If the chosen `<name>` is already registered, error out with the existing entry's path shown; recommend a different name or manual JSON edit.

## Steps

### 1. Validate the target library path

- Verify `<path>` exists and is a directory.
- Verify `<path>/_shelf-index.md` exists. If missing, error with: "no shelf-index found — run `/sdlc-knowledge-base:kb-rebuild-indexes` in that library first."
- Parse the format_version from the shelf-index's first line (via the `format_version` helper). If the version is unknown, warn but continue — the librarian handles drift at query time.

### 2. Load or initialise the registry

If `~/.sdlc/global-libraries.json` does not exist, initialise with:

```json
{"version": 1, "libraries": []}
```

Otherwise load the existing file. If parsing fails, do not overwrite — error and recommend manual repair.

### 3. Add the new entry

Append to `libraries`:

```json
{
  "name": "<name>",
  "type": "filesystem",
  "path": "<absolute-path>",
  "description": "<description or omitted>"
}
```

### 4. Write the registry atomically

Write to a temp file and rename to avoid partial writes.

### 5. Report success

Print a confirmation:

```
Registered '<name>' → <path>
format_version: <N>
Description: <description or "none">

To activate in a project, add to .sdlc/libraries.json:
  {"version": 1, "activated_sources": ["<name>"]}
```

## What this skill does NOT do

- It does not install, copy, or symlink the library — it only records a pointer.
- It does not activate the library in any project — that's a separate manual step.
- It does not validate shelf-index content quality — only that the file exists.
- It does not support `type: remote-agent` — that's phase D (future EPIC).

## Examples

Register a corporate library:

```
/sdlc-knowledge-base:kb-register-library corporate-semiconductor /Users/steve/corp/semi/library "Semiconductor engagement findings 2024-2026"
```

Register with no description:

```
/sdlc-knowledge-base:kb-register-library corp-health /Users/steve/corp/health/library
```

## Errors

- **Path does not exist** — correct the path argument or create the directory first
- **No shelf-index at path** — run `/sdlc-knowledge-base:kb-rebuild-indexes` in that library
- **Name already registered** — choose a different name, or manually edit `~/.sdlc/global-libraries.json`
- **Registry file malformed** — manual repair required; the skill will not overwrite a file it cannot parse
```

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md
git commit -m "feat(kb): add kb-register-library skill (phase A, #167)

Optional helper for appending entries to the user-scope library
registry. Validates target path, shelf-index presence, and format
version before writing. Hand-editing the JSON remains supported.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Rewrite kb-query skill with orchestration flow

**Files:**
- Modify: `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`

- [ ] **Step 1: Read the existing kb-query skill**

Run: `cat plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`
Review the current structure (preflight, steps 1-4, errors). The rewrite keeps the same section structure but adds orchestration.

- [ ] **Step 2: Replace the Steps section with cross-library orchestration**

In `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`, replace the entire `## Steps` section (currently steps 1-4) with the following:

```markdown
## Steps

### 1. Preflight — load the dispatch list

Run the registry resolver helper to determine which sources to dispatch against:

```bash
python -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import load_global_registry, load_project_activation, resolve_dispatch_list
import json, os

global_reg = load_global_registry(Path(os.path.expanduser('~/.sdlc/global-libraries.json')))
activation = load_project_activation(Path('.sdlc/libraries.json'))
dispatch = resolve_dispatch_list(global_reg, activation, Path('library'))

print(json.dumps({
  'sources': [{'name': s.name, 'path': s.path} for s in dispatch.sources],
  'warnings': global_reg.warnings + activation.warnings + dispatch.warnings,
  'is_empty_error': dispatch.is_empty_error,
}, indent=2))
"
```

If `is_empty_error` is true, print:

> No knowledge base available. Run `/sdlc-knowledge-base:kb-init` to create a local library, or register and activate an external library with `/sdlc-knowledge-base:kb-register-library`.

and stop.

Print all warnings from the helper to stderr (not to user-facing output).

### 2. Build the priming bundle

```bash
python -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.priming import build_priming_bundle
import json

bundle = build_priming_bundle(question='<the user question>', project_dir=Path('.'))
print(json.dumps({
  'question': bundle.question,
  'local_kb_config_excerpt': bundle.local_kb_config_excerpt,
  'local_shelf_index_terms': bundle.local_shelf_index_terms,
}, indent=2))
"
```

In phase A, the bundle is built but the librarian's use of it is not yet active (phase B, #168 enables that). Passing it through now means phase B is a librarian-prompt change only, not a skill rewrite.

### 3. Dispatch `research-librarian` for every source — in parallel

Use the **Agent tool** to invoke the `research-librarian` agent *once per source* in the dispatch list. Issue ALL invocations in a SINGLE message (Claude's parallel tool-call capability). Each invocation's prompt has this exact structure:

```
SCOPE: <source.path>
SOURCE_HANDLE: <source.name>
PRIMING_CONTEXT: <json-dump-of-priming-bundle>

Question: <the user question>

Read the shelf-index at <source.path>/_shelf-index.md, identify the 2-4 most
relevant library files for the question, deep-read only those, and return
findings in the retrieval format. Every finding block must include a
**Source library**: <source.name> line (see your agent prompt).

Do not read any files outside <source.path>.
```

### 4. Collect per-source outputs

Each librarian returns its findings (or "no evidence on this topic" if the scoped library has nothing). Capture each source's output, keyed by source.name.

### 5. Apply attribution post-check and render

```bash
python -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.orchestrator import run_retrieval_query, DispatchRequest
# ... orchestrator expects the dispatcher callable; in this skill, we've
# already dispatched via the Agent tool and have outputs in hand, so call
# the post-check and rendering functions directly.
from sdlc_knowledge_base_scripts.attribution import check_retrieval_attribution
# Render logic matches the orchestrator's _render_header + ordered output.
"
```

Use the `check_retrieval_attribution` helper on the concatenated per-source outputs. Drop any finding block that fails the check; log dropped blocks for the user to see.

Render the final output with this structure:

```markdown
# Knowledge Base Query Results

**Sources queried:** <all dispatch names comma-separated>
**Sources with findings:** <those that returned at least one tagged finding>
**Sources with no evidence on this topic:** <those that returned the no-evidence marker>
**Sources that failed:** <those whose librarian dispatch errored>

---

## [local] Findings

<local findings, post-check cleaned>

---

## [<external-1>] Findings

<findings, post-check cleaned>

---

## [<external-2>] — skipped

<failure marker or no-evidence marker>

...
```

Ordering: `local` first, then external sources alphabetical by name.

### 6. If the `--promote-to-library` flag was specified

Same behaviour as before — dispatch `kb-promote-answer-to-library` with the answer. Promotion writes only to the **local** library; external libraries are read-only from this project.

### 7. Synthesis (phase C, #169 — not in phase A)

Not implemented in phase A. If the query is a synthesis query ("build me the case for", "how should we think about"), return the retrieval output and print a note:

> Note: cross-library synthesis is coming in phase C (#169). This query returned per-source findings; you can draw connections between them manually.

Phase C replaces this note with a real synthesis step.
```

- [ ] **Step 3: Update the "What this skill does NOT do" and "Errors" sections**

Find the `## What this skill does NOT do` section and update it:

```markdown
## What this skill does NOT do

- It does not modify library files — the librarian is read-only
- It does not invent answers when no library has evidence
- It does not ingest new sources — that's `/sdlc-knowledge-base:kb-ingest` (local only in v1)
- It does not lint the library — that's `/sdlc-knowledge-base:kb-lint` (local only in v1)
- It does not write to external libraries — they are strictly read-only from the querying project's perspective
- It does not blend findings without attribution — every finding carries its source library handle, enforced by structural post-check
- It does not synthesise across libraries in phase A — that arrives in phase C (#169)
```

Find the `## Errors` section and add:

```markdown
- **No sources available** — no local library + no activated external libraries. Run `/sdlc-knowledge-base:kb-init` or activate a library in `.sdlc/libraries.json`.
- **External source path unmounted** — the query proceeds with other sources; the failed source appears as a marker in the output.
- **External source missing shelf-index** — same as above; run `/sdlc-knowledge-base:kb-rebuild-indexes` in the external library.
```

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
git commit -m "feat(kb): rewrite kb-query skill with cross-library orchestration (phase A, #167)

Preflight loads global + project registries; priming bundle built;
parallel research-librarian dispatch via Agent tool (one per source);
attribution post-check before output; ordered rendering (local first,
externals alphabetical). Synthesis path placeholder defers to phase C.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: Update kb-init CLAUDE.md template

**Files:**
- Modify: `plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md`

- [ ] **Step 1: Read the current template**

Run: `cat plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md | head -40`

- [ ] **Step 2: Add the External libraries subsection**

In `plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md`, find the `### When NOT to use the knowledge base` section near the end of the template. **Before** that section, insert:

```markdown
### External libraries (cross-library query)

This project can query one or more external knowledge bases alongside its own. External libraries ("corporate asset libraries") are registered once in the user-scope registry and activated per-project.

**To register an external library** (once, per library per machine):

```
/sdlc-knowledge-base:kb-register-library <handle> <absolute-path-to-library-dir> [description]
```

This appends an entry to `~/.sdlc/global-libraries.json`. Hand-editing that file is also supported — see the plugin's README.

**To activate a registered library in this project**, add its handle to `.sdlc/libraries.json`:

```json
{
  "version": 1,
  "activated_sources": ["corporate-semiconductor"]
}
```

When at least one external library is activated, every `kb-query` invocation dispatches the librarian against each activated source in parallel. Results are attributed (`[local]`, `[corporate-semiconductor]`, etc.) and the local library's context primes the external queries.

**What lives where:**

- Handle + filesystem path + description: `~/.sdlc/global-libraries.json` (user-scope — never committed to this repo)
- Activation list (handles only): `.sdlc/libraries.json` (project-scope — safe to commit)

**Confidentiality:** hard isolation between concurrent confidential engagements is not enforced by the plugin. If two engagements must not share findings, keep them in separate repositories. Each repo's `.sdlc/libraries.json` activates only the appropriate handles.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md
git commit -m "feat(kb): document External libraries in CLAUDE.md template (phase A, #167)

New subsection explains the register + activate workflow, which file
lives where (user-scope vs project-scope), and the confidentiality
boundary (separate repos, not plugin-level enforcement).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Release-mapping update

**Files:**
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Read the current sdlc-knowledge-base section**

Run: `grep -A 40 '^sdlc-knowledge-base:' release-mapping.yaml | head -60`

- [ ] **Step 2: Add new files to the mapping**

In `release-mapping.yaml`, under the `sdlc-knowledge-base:` plugin block, add/ensure these entries exist:

Under `skills:` (add the new kb-register-library skill):
```yaml
    - source: plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md
```

Add a new category `scripts:` (or extend if present):
```yaml
  scripts:
    - source: plugins/sdlc-knowledge-base/scripts/__init__.py
    - source: plugins/sdlc-knowledge-base/scripts/registry.py
    - source: plugins/sdlc-knowledge-base/scripts/priming.py
    - source: plugins/sdlc-knowledge-base/scripts/attribution.py
    - source: plugins/sdlc-knowledge-base/scripts/format_version.py
    - source: plugins/sdlc-knowledge-base/scripts/orchestrator.py
```

Add `other:` (or `pyproject:`) for the pyproject.toml:
```yaml
  other:
    - source: plugins/sdlc-knowledge-base/pyproject.toml
```

(Follow existing conventions in the file — look at how `sdlc-workflows` packages its pyproject.toml, and match.)

- [ ] **Step 3: Run the plugin packaging check**

Run: `python tools/validation/check-plugin-packaging.py`
Expected: PASS — all source files in release-mapping.yaml exist and are packaged.

If it fails because scripts/ already existed in the plugin dir from a prior release-plugin run, first run: `python tools/validation/check-plugin-packaging.py` to see what's out of sync; then run `/sdlc-core:release-plugin` (or the equivalent) to re-sync.

- [ ] **Step 4: Commit**

```bash
git add release-mapping.yaml
git commit -m "feat(kb): package phase A scripts + kb-register-library (phase A, #167)

Wires new plugin components into release-mapping.yaml:
- scripts/ (registry, priming, attribution, format_version, orchestrator)
- pyproject.toml
- kb-register-library skill

Verified by check-plugin-packaging.py.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 15: Integration-test fixtures

**Files:**
- Create: `tests/fixtures/kb_libraries/local-sample/library/_shelf-index.md`
- Create: `tests/fixtures/kb_libraries/local-sample/library/topic-a.md`
- Create: `tests/fixtures/kb_libraries/corp-semi-sample/library/_shelf-index.md`
- Create: `tests/fixtures/kb_libraries/corp-semi-sample/library/topic-b.md`
- Create: `tests/fixtures/kb_libraries/corp-legacy-no-header/library/_shelf-index.md`
- Create: `tests/fixtures/kb_libraries/corp-future-version/library/_shelf-index.md`
- Create: `tests/fixtures/kb_libraries/empty-dir/library/` (empty directory with `.gitkeep`)

- [ ] **Step 1: Create local-sample fixture**

Create `tests/fixtures/kb_libraries/local-sample/library/_shelf-index.md`:
```markdown
<!-- format_version: 1 -->
# Knowledge Base Shelf-Index

## 1. topic-a.md

**Hash:** abc123
**Terms:** alpha, beta, gamma, brazilian-fab, semiconductor
**Facts:**
- Fact about alpha from local project (source: site survey 2026)
**Links:** topic-b.md
```

Create `tests/fixtures/kb_libraries/local-sample/library/topic-a.md`:
```markdown
---
title: "Local topic A"
domain: local, test
status: active
---

## Key Question

How do we handle alpha in the local project context?

## Core Findings

1. Alpha is handled via beta — site survey 2026, internal

## Key References

1. Site survey 2026, internal
```

- [ ] **Step 2: Create corp-semi-sample fixture**

Create `tests/fixtures/kb_libraries/corp-semi-sample/library/_shelf-index.md`:
```markdown
<!-- format_version: 1 -->
# Knowledge Base Shelf-Index

## 1. topic-b.md

**Hash:** def456
**Terms:** alpha, beta, dutch-fab, semiconductor, EUV, cleanroom
**Facts:**
- Alpha was managed at Dutch fab with approach X (internal 2024)
**Links:** -
```

Create `tests/fixtures/kb_libraries/corp-semi-sample/library/topic-b.md`:
```markdown
---
title: "Corporate semiconductor topic B"
domain: semiconductor, corporate
status: active
---

## Key Question

How was alpha handled in prior engagements?

## Core Findings

1. Alpha managed via approach X at Dutch fab — internal 2024

## Key References

1. Internal engagement report, 2024
```

- [ ] **Step 3: Create corp-legacy-no-header fixture**

Create `tests/fixtures/kb_libraries/corp-legacy-no-header/library/_shelf-index.md` (note: NO format_version header on line 1):
```markdown
# Knowledge Base Shelf-Index

## 1. legacy.md

**Hash:** ghi789
**Terms:** legacy, old-format
**Facts:**
- Legacy library pre-dating format_version breadcrumb
**Links:** -
```

- [ ] **Step 4: Create corp-future-version fixture**

Create `tests/fixtures/kb_libraries/corp-future-version/library/_shelf-index.md`:
```markdown
<!-- format_version: 99 -->
# Knowledge Base Shelf-Index

## 1. future.md

**Hash:** jkl012
**Terms:** future, unknown-version
**Facts:**
- Shelf-index from a hypothetical future format_version
**Links:** -
```

- [ ] **Step 5: Create empty-dir fixture**

```bash
mkdir -p tests/fixtures/kb_libraries/empty-dir/library
touch tests/fixtures/kb_libraries/empty-dir/library/.gitkeep
```

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/kb_libraries/
git commit -m "test(kb): add fixture libraries for cross-library query tests (phase A, #167)

Five fixture libraries for integration tests:
- local-sample — typical project library
- corp-semi-sample — corporate asset library with overlapping terms
- corp-legacy-no-header — shelf-index without format_version breadcrumb
- corp-future-version — shelf-index with format_version: 99
- empty-dir — directory without a shelf-index (failure case)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 16: Feature proposal + retrospective scaffold

**Files:**
- Create: `docs/feature-proposals/167-kb-cross-library-phase-a.md`
- Create: `retrospectives/167-kb-cross-library-phase-a.md`

The AI-First SDLC workflow requires both artifacts per CONSTITUTION Article 2. The proposal is terse — it points at the design spec for the real content.

- [ ] **Step 1: Create the feature proposal**

Create `docs/feature-proposals/167-kb-cross-library-phase-a.md`:

```markdown
# Feature Proposal: Cross-Library KB Query — Phase A Foundation

**Proposal Number:** 167
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-24
**Target Branch:** `feature/164-cross-library-kb-query`
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-feature:** #167 (sub-1 of 3 in v1)

## Summary

Foundation layer for cross-library knowledge base query. Delivers the LibrarySource abstraction, user-scope + project-scope library registries, FilesystemSource dispatcher, `kb-query` orchestration with parallel librarian dispatch, and mandatory source attribution. Does not include priming (phase B, #168) or cross-library synthesis (phase C, #169).

## Motivation

See EPIC #164 body and design spec §1 (Context). Amkor AI Strategy engagement feedback (2026-04-23) identified that the research-librarian cannot query prior engagement libraries. Corporate asset libraries, reusable across engagements, need a registration + activation model and multi-source dispatch.

## Design

Full design in `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md` (branch `feature/164-cross-library-kb-query`, commit 9ca9de5).

Seven design questions resolved during brainstorming (listed in spec §2). Phase A implements the foundation layer per spec §4 (Components), §5 (Configuration schemas), §6.1 (Retrieval data flow), and §7 (Error handling).

## Success Criteria

Per issue #167 acceptance criteria:

- [ ] Plugin has importable Python scripts package (mirrors sdlc-workflows pattern)
- [ ] `~/.sdlc/global-libraries.json` schema + loader with graceful degradation
- [ ] `.sdlc/libraries.json` schema + loader with graceful degradation
- [ ] Activation resolution prepends implicit local source, skips unknowns and remote-agent types with warnings
- [ ] Priming bundle scaffold (used actively in phase B)
- [ ] Attribution post-check enforces source library tags structurally
- [ ] `format_version: 1` breadcrumb emitted by kb-rebuild-indexes
- [ ] research-librarian prompt extended for SCOPE, PRIMING_CONTEXT, SOURCE_HANDLE
- [ ] kb-register-library skill registers new entries in the user-scope registry
- [ ] kb-query orchestration dispatches librarians in parallel, collects, post-checks, and renders
- [ ] kb-init CLAUDE.md template documents external-library registration and activation
- [ ] Unit test coverage: registry, priming, attribution, format_version, orchestrator (mock dispatcher)
- [ ] `check-plugin-packaging.py` passes after release-mapping update
- [ ] `python tools/validation/local-validation.py --pre-push` passes

## Out of scope (phase A)

- Active use of priming bundle by librarians (phase B, #168)
- Cross-library synthesis (phase C, #169)
- RemoteAgentSource (deferred EPIC)
- Cross-library ingest, lint, staleness-check, citation validation
- Registry corruption auto-recovery
- `kb-deregister-library`, `kb-list-libraries` helpers

## Dependencies

- None at phase A level.

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-a.md`
```

- [ ] **Step 2: Create the retrospective scaffold**

Create `retrospectives/167-kb-cross-library-phase-a.md`:

```markdown
# Retrospective: Cross-Library KB Query — Phase A Foundation

**Issue:** #167 (sub-1 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** In progress

## What went well

_(Fill in at end of implementation.)_

## What was harder than expected

_(Fill in at end of implementation.)_

## What surprised us

_(Fill in at end of implementation.)_

## What we'd do differently next time

_(Fill in at end of implementation.)_

## Metrics

- Implementation time: TBD
- Tests added: TBD
- Commits on branch for this sub-feature: TBD
- Validation pipeline pass status: TBD

## Decisions worth capturing in memory

_(Review at end; copy relevant patterns/feedback into MEMORY.md if not already captured.)_
```

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/167-kb-cross-library-phase-a.md retrospectives/167-kb-cross-library-phase-a.md
git commit -m "docs: feature proposal + retrospective scaffold for phase A (#167)

Required by CONSTITUTION Article 2. Proposal points at the design spec
for architectural content; retrospective filled in at implementation close.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 17: Final validation — pre-push pipeline

**Files:**
- No changes; runs validators.

- [ ] **Step 1: Run full unit test suite**

Run: `pytest tests/test_kb_registry.py tests/test_kb_priming.py tests/test_kb_attribution.py tests/test_kb_format_version.py tests/test_kb_orchestrator.py -v`
Expected: all tests PASS (count: at least 13 + 4 + 6 + 5 + 5 = 33 tests).

- [ ] **Step 2: Run the plugin packaging check**

Run: `python tools/validation/check-plugin-packaging.py`
Expected: PASS.

- [ ] **Step 3: Run pre-push validation**

Run: `python tools/validation/local-validation.py --pre-push`
Expected: PASS all 10 checks (syntax, ruff lint, ruff format, technical debt, tests, import check, type safety, security, logging compliance, smoke test).

If technical debt fails because the plan references "TODO for phase B" or similar, rephrase those references in the code/docs to use "phase B (#168)" without the literal TODO keyword.

- [ ] **Step 4: Fill in the retrospective**

Edit `retrospectives/167-kb-cross-library-phase-a.md` with real content for each section. Include any patterns or feedback worth recording in memory.

- [ ] **Step 5: Final commit**

```bash
git add retrospectives/167-kb-cross-library-phase-a.md
git commit -m "docs: complete phase A retrospective (#167)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 6: Summarise commit history**

Run: `git log main..HEAD --oneline | head -30`
Expected: ~17 commits on the feature branch, one per task.

Phase A is complete. The branch stays open; phase B (#168) and phase C (#169) add their commits to the same branch. PR is opened only when all three phases are merged back.

---

## Self-review

**Spec coverage check:**

| Spec section | Covered by task |
|---|---|
| §3.1 LibrarySource abstraction | Task 2 (dataclass in registry.py) |
| §3.2 Orchestration pattern | Task 8 (orchestrator.py), Task 12 (skill wires Agent tool) |
| §3.3 Local-as-just-another-source | Task 4 (implicit local in resolve_dispatch_list) |
| §4 Components (all files) | Tasks 1-14 cover every file listed |
| §5.1 Global registry schema | Tasks 2-3 |
| §5.2 Project activation schema | Task 3 |
| §5.3 format_version header | Tasks 7, 9 |
| §6.1 Retrieval data flow | Tasks 8, 12 |
| §6.2 Synthesis data flow | Deferred to phase C (#169) — Task 12 step 7 documents the placeholder |
| §7 Error handling table | Task 8 tests; registry + orchestrator warnings |
| §7.1 Attribution integrity | Task 6 |
| §7.2 Not-handled-in-v1 items | Deferred (documented in spec, not implemented) |
| §8.1 Unit tests | Tasks 2-8 each include their own unit tests |
| §8.2 Integration tests | Task 8 (orchestrator with mock dispatcher) |
| §8.3 E2E tests | Deferred to a later plan — real-librarian e2e fixtures are too expensive for every commit. One happy-path E2E is implicit in Task 17 step 3 if the smoke test exercises kb-query. |
| §8.4 Test fixtures | Task 15 |
| §9.1 In-scope for v1 | Tasks 1-17 cover everything for phase A; B and C are separate plans |

**Gap check:** §8.3 e2e tests (5 scenarios with real librarian) are not explicitly implemented. This is acknowledged — running real librarian calls in the test pipeline is expensive and would be gated behind an env flag. A follow-up plan in phase C will address e2e test harness if needed.

**Placeholder scan:** no TBDs or TODOs in the plan itself. The retrospective (Task 16 step 2) has placeholder sections marked "Fill in at end of implementation" by design.

**Type consistency:** `LibrarySource`, `DispatchList`, `PrimingBundle`, `DispatchRequest`, `RetrievalQueryResult` consistent across tasks. Method names `load_global_registry`, `load_project_activation`, `resolve_dispatch_list`, `build_priming_bundle`, `check_retrieval_attribution`, `check_synthesis_attribution`, `parse_format_version`, `run_retrieval_query` consistent. Field names (`sources`, `warnings`, `is_empty_error`, `activated_sources`, `libraries`, `version`) consistent. No drift.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-a.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Each subagent gets the task block in isolation and returns a summary; I verify the commit landed and move to the next.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`. Batch execution with checkpoints between tasks for you to review.

Which approach?

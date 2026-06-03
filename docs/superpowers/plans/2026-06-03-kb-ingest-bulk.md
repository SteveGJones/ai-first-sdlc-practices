# kb-ingest-bulk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `kb-ingest-bulk` — a parallel map-reduce ingest path that loads large source sets into a project knowledge base in hours instead of weeks, updating shared topic files in parallel without write contention.

**Architecture:** Map (read-only `knowledge-extractor` agents, ≤N-wide, default Haiku) emit compact JSON extracts → Python router groups extracts by target library file, fuzzy-merges new-topic proposals, pre-allocates new files, and flags oversized topics → Reduce (one fresh-context `agent-knowledge-updater` per file, Sonnet) synthesises all routed extracts into that one file → single finalize (shelf-index rebuild + one `log.md` entry). All deterministic work is pure Python following the existing `orchestrator.py` injectable-dispatcher pattern; the skill drives agent fan-out via parallel Agent-tool calls.

**Tech Stack:** Python 3 (stdlib + `yaml`), pytest, Claude Code skills/agents. Spec: `docs/superpowers/specs/2026-06-03-kb-ingest-bulk-design.md`.

---

## Source-of-truth locations (READ FIRST — avoids the plugin-dir-wipe regression)

`release-plugin` copies *source* files into plugin dirs and **overwrites** them. Author edits in the source location, never the plugin-dir copy, or your work is silently wiped:

| Artifact | Author at (SOURCE) | Notes |
|---|---|---|
| New script `kb_ingest_bulk.py` | `plugins/sdlc-knowledge-base/scripts/` | Scripts are authored in-plugin (ship in place) |
| Tests | `tests/test_kb_ingest_bulk.py` | Imports `sdlc_knowledge_base_scripts.kb_ingest_bulk` |
| New agent `knowledge-extractor.md` | `agents/knowledge-base/` | ⚠️ ROOT source — NOT `plugins/.../agents/` |
| New skill `kb-ingest-bulk/SKILL.md` | `plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/` | Matches recent-skill convention |
| Edit `kb-init/SKILL.md` | `skills/kb-init/` | ⚠️ ROOT source — NOT `plugins/.../skills/` |
| Edit `kb-ingest-batch/SKILL.md` | `plugins/sdlc-knowledge-base/skills/kb-ingest-batch/` | Plugin-dir source |

`release-plugin` is run once at the end (Task 13), then `check-plugin-packaging.py` verifies sync in CI.

## Module API (defined once; later tasks reference these names)

`kb_ingest_bulk.py` exposes:

```python
# Dataclasses
@dataclass(frozen=True)
class ExtractDispatchRequest:   # map input
    source_path: str
    library_path: str
    shelf_index_path: str
    extractor_model: str

@dataclass(frozen=True)
class ReduceDispatchRequest:    # reduce input
    target_file: str            # filename relative to library, e.g. "cri-sustainability.md"
    is_new: bool
    library_path: str
    shelf_index_path: str
    extracts: list[dict]        # the extract dicts routed to this file

@dataclass
class RouteResult:
    targets: dict[str, dict]    # target_file -> {"extracts": [...], "is_new": bool, "est_tokens": int}
    oversized: list[str]        # target_files exceeding size_threshold (skipped)

# Functions
def discover_sources(spec) -> list[Path]            # glob str | dir Path | list[str]; deduped, sorted
def slug_for_source(path) -> str                     # stable slug from filename
def extract_path(extracts_dir, slug) -> Path         # extracts_dir / f"{slug}.json"
def persist_extract(extracts_dir, slug, extract) -> Path
def build_bulk_manifest(sources, existing=None, run_meta=None) -> dict
def mark_source_extracted(manifest, path) -> dict
def mark_source_failed(manifest, path, error) -> dict
def mark_target_reduced(manifest, target_file) -> dict
def mark_target_failed(manifest, target_file, error) -> dict
def retry_failed(manifest) -> dict
def normalize_slug(text) -> str
def estimate_tokens(text) -> int                     # len(text)//4 heuristic
def route_extracts(extracts, existing_files, size_threshold) -> RouteResult
def format_extract_prompt(req: ExtractDispatchRequest) -> str
def format_reduce_prompt(req: ReduceDispatchRequest) -> str
def summarize_run(manifest, oversized) -> str        # markdown summary + log.md line
def write_log_entry(log_path, summary_line) -> None
```

Manifest schema (`library/.extracts/.bulk-progress.json`):
```json
{
  "started_at": "<iso>",
  "run_meta": {"parallel_n": 16, "extractor_model": "claude-haiku-4-5", "size_threshold": 200000},
  "sources": {"<path>": {"slug": "...", "status": "pending|extracted|failed", "error": null}},
  "targets": {"<file>": {"status": "pending|reduced|failed", "source_count": 0, "is_new": false, "error": null}}
}
```

Reuse `load_manifest` / `save_manifest` (atomic) from `kb_ingest_batch` — they are schema-agnostic JSON helpers. Reuse `build_shelf_index.main([library_path])` for finalize.

---

## Task 0: Feature proposal + retrospective stubs

**Files:**
- Create: `docs/feature-proposals/208-kb-ingest-bulk.md`
- Create: `retrospectives/208-kb-ingest-bulk.md`

- [ ] **Step 1: Write the feature proposal**

Create `docs/feature-proposals/208-kb-ingest-bulk.md`:

```markdown
# Feature Proposal: kb-ingest-bulk — parallel map-reduce ingest (#208)

**Status:** In progress · **Branch:** `feature/208-kb-ingest-bulk`

## Problem
`kb-ingest` is single-source; `kb-ingest-batch` is create-only (defers existing-file
conflicts to manual). Neither updates shared topic files in parallel. CRI's 887-source
corpus projects to weeks-to-months.

## Solution
`kb-ingest-bulk`: map (parallel read-only extractors) → route (Python) → reduce (one
writer per file, parallel) → single finalize. Supersedes `kb-ingest-batch`.
Adds `--library` override (also to `kb-init`) for isolated testing / multi-library.

## Design
See `docs/superpowers/specs/2026-06-03-kb-ingest-bulk-design.md`.

## Out of scope
Full `--libraries` query federation → #209 (builds on EPIC #164 registry).
```

- [ ] **Step 2: Write the retrospective stub**

Create `retrospectives/208-kb-ingest-bulk.md`:

```markdown
# Retrospective: kb-ingest-bulk (#208)

## What we set out to do
Parallel map-reduce bulk ingest for large source sets; supersede kb-ingest-batch.

## What went well
_(fill in during/after implementation)_

## What was hard
_(fill in)_

## Lessons
_(fill in)_

## Test evidence
_(pytest counts, live-smoke result against tmp/cri-bulk-test/)_
```

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/208-kb-ingest-bulk.md retrospectives/208-kb-ingest-bulk.md
git commit -m "docs: feature proposal + retrospective stub for kb-ingest-bulk (#208)"
```

---

## Task 1: Scaffolding — gitignore, skill dir, empty module

**Files:**
- Modify: `.gitignore`
- Create: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Create: `plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/` (dir, via the SKILL file in Task 11)
- Create: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Add `.extracts/` to .gitignore**

Append to `.gitignore`:

```
# kb-ingest-bulk per-source extraction artefacts (resume tokens, regenerable)
library/.extracts/
**/library/.extracts/
```

- [ ] **Step 2: Create the module with imports + dataclasses**

Create `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`:

```python
"""Parallel map-reduce bulk ingest for sdlc-knowledge-base (issue #208).

Pure-Python orchestration core. Agent dispatch (map extractors, reduce
updaters) happens in the SKILL.md via parallel Agent-tool calls; this module
provides discovery, manifest CRUD, extract persistence, routing, prompt
formatting, and finalize helpers. Dispatch is injected as a callable so tests
run without real Agent calls — mirrors orchestrator.py.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Reuse the schema-agnostic atomic JSON helpers from the batch module.
from .kb_ingest_batch import load_manifest, save_manifest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ExtractDispatchRequest:
    source_path: str
    library_path: str
    shelf_index_path: str
    extractor_model: str


@dataclass(frozen=True)
class ReduceDispatchRequest:
    target_file: str
    is_new: bool
    library_path: str
    shelf_index_path: str
    extracts: list[dict]


@dataclass
class RouteResult:
    targets: dict = field(default_factory=dict)
    oversized: list = field(default_factory=list)
```

- [ ] **Step 3: Create the empty test file**

Create `tests/test_kb_ingest_bulk.py`:

```python
"""Tests for sdlc_knowledge_base_scripts.kb_ingest_bulk."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    ExtractDispatchRequest,
    ReduceDispatchRequest,
    RouteResult,
)


def test_module_imports() -> None:
    assert ExtractDispatchRequest is not None
    assert ReduceDispatchRequest is not None
    assert RouteResult is not None
```

- [ ] **Step 4: Run to verify it passes (import smoke)**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add .gitignore plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): scaffold kb_ingest_bulk module + dataclasses (#208)"
```

---

## Task 2: `discover_sources` — glob / dir / file-list

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_kb_ingest_bulk.py`:

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import discover_sources


def test_discover_sources_from_dir(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    (tmp_path / "skip.txt").write_text("x")
    found = discover_sources(tmp_path)
    assert [p.name for p in found] == ["a.md", "b.md"]


def test_discover_sources_from_glob(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    found = discover_sources(str(tmp_path / "*.md"))
    assert [p.name for p in found] == ["a.md", "b.md"]


def test_discover_sources_from_list_dedupes(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("a")
    found = discover_sources([str(f), str(f)])
    assert found == [f]


def test_discover_sources_missing_path_skipped(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("a")
    found = discover_sources([str(f), str(tmp_path / "nope.md")])
    assert found == [f]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k discover -v`
Expected: FAIL with `ImportError: cannot import name 'discover_sources'`

- [ ] **Step 3: Implement**

Add to `kb_ingest_bulk.py`:

```python
import glob as _glob


def discover_sources(spec) -> list[Path]:
    """Resolve a glob string, a directory Path, or a list of paths to .md files.

    - dir  -> all *.md directly in the dir (non-recursive), sorted by name
    - glob -> files matching the pattern, sorted
    - list -> each entry resolved; missing paths skipped; deduped, order-stable
    Only files that exist are returned.
    """
    out: list[Path] = []
    seen: set[Path] = set()

    def _add(p: Path) -> None:
        rp = p.resolve()
        if rp in seen:
            return
        if p.is_file():
            seen.add(rp)
            out.append(p)

    if isinstance(spec, (list, tuple)):
        for entry in spec:
            _add(Path(entry))
        return out

    if isinstance(spec, Path) and spec.is_dir():
        for p in sorted(spec.glob("*.md")):
            _add(p)
        return out

    # Treat as glob string (also handles a dir given as str via trailing match)
    pattern = str(spec)
    if Path(pattern).is_dir():
        for p in sorted(Path(pattern).glob("*.md")):
            _add(p)
        return out
    for match in sorted(_glob.glob(pattern)):
        _add(Path(match))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k discover -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): discover_sources for glob/dir/list (#208)"
```

---

## Task 3: Slug + extract persistence

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    extract_path, persist_extract, slug_for_source,
)


def test_slug_for_source_stable_and_safe() -> None:
    assert slug_for_source(Path("/x/02-03 Foo Bar.md")) == "02-03-foo-bar"
    assert slug_for_source(Path("/x/Foo_Bar.md")) == "foo-bar"


def test_persist_extract_writes_json(tmp_path: Path) -> None:
    extract = {"source": "a.md", "findings": ["f1"], "confidence": "high", "targets": []}
    p = persist_extract(tmp_path, "a", extract)
    assert p == tmp_path / "a.json"
    import json
    assert json.loads(p.read_text())["findings"] == ["f1"]


def test_extract_path() -> None:
    assert extract_path(Path("/lib/.extracts"), "a") == Path("/lib/.extracts/a.json")
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "slug or persist or extract_path" -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug_for_source(path: Path) -> str:
    """Stable, filesystem-safe slug from a source filename (stem)."""
    stem = Path(path).stem.lower()
    return _SLUG_RE.sub("-", stem).strip("-")


def extract_path(extracts_dir: Path, slug: str) -> Path:
    return Path(extracts_dir) / f"{slug}.json"


def persist_extract(extracts_dir: Path, slug: str, extract: dict) -> Path:
    """Write one extract as JSON to extracts_dir/<slug>.json (atomic)."""
    extracts_dir = Path(extracts_dir)
    extracts_dir.mkdir(parents=True, exist_ok=True)
    path = extract_path(extracts_dir, slug)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(extract, indent=2), encoding="utf-8")
    tmp.rename(path)
    return path
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "slug or persist or extract_path" -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): source slug + extract persistence (#208)"
```

---

## Task 4: Manifest build + source state transitions

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    build_bulk_manifest, mark_source_extracted, mark_source_failed,
)


def test_build_bulk_manifest_initial(tmp_path: Path) -> None:
    s = [tmp_path / "a.md", tmp_path / "b.md"]
    m = build_bulk_manifest(s, run_meta={"parallel_n": 16})
    assert set(m["sources"]) == {str(s[0]), str(s[1])}
    assert all(v["status"] == "pending" for v in m["sources"].values())
    assert m["run_meta"]["parallel_n"] == 16
    assert m["targets"] == {}


def test_build_bulk_manifest_resume_preserves_extracted(tmp_path: Path) -> None:
    s = [tmp_path / "a.md", tmp_path / "b.md"]
    m = build_bulk_manifest(s)
    m = mark_source_extracted(m, str(s[0]))
    # re-run with an extra new source
    s2 = s + [tmp_path / "c.md"]
    m2 = build_bulk_manifest(s2, existing=m)
    assert m2["sources"][str(s[0])]["status"] == "extracted"   # preserved
    assert m2["sources"][str(s2[2])]["status"] == "pending"    # new appended


def test_mark_source_failed_records_error(tmp_path: Path) -> None:
    s = [tmp_path / "a.md"]
    m = build_bulk_manifest(s)
    m = mark_source_failed(m, str(s[0]), "timeout")
    assert m["sources"][str(s[0])]["status"] == "failed"
    assert m["sources"][str(s[0])]["error"] == "timeout"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "manifest or mark_source" -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
def build_bulk_manifest(sources, existing=None, run_meta=None) -> dict:
    """Build or update a two-phase bulk manifest.

    Preserves prior source/target status from *existing*; appends new sources
    as pending. run_meta is set only on first build.
    """
    if existing is not None:
        manifest = {
            "started_at": existing.get("started_at", _now()),
            "run_meta": existing.get("run_meta", run_meta or {}),
            "sources": dict(existing.get("sources", {})),
            "targets": dict(existing.get("targets", {})),
        }
    else:
        manifest = {
            "started_at": _now(),
            "run_meta": run_meta or {},
            "sources": {},
            "targets": {},
        }
    for p in sources:
        key = str(p)
        if key not in manifest["sources"]:
            manifest["sources"][key] = {
                "slug": slug_for_source(Path(p)),
                "status": "pending",
                "error": None,
            }
    return manifest


def mark_source_extracted(manifest: dict, path: str) -> dict:
    manifest["sources"][path]["status"] = "extracted"
    manifest["sources"][path]["error"] = None
    return manifest


def mark_source_failed(manifest: dict, path: str, error: str) -> dict:
    manifest["sources"][path]["status"] = "failed"
    manifest["sources"][path]["error"] = error
    return manifest
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "manifest or mark_source" -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): two-phase bulk manifest + source transitions (#208)"
```

---

## Task 5: Target state transitions + retry_failed

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    mark_target_reduced, mark_target_failed, retry_failed,
)


def test_target_transitions(tmp_path: Path) -> None:
    m = build_bulk_manifest([tmp_path / "a.md"])
    m["targets"]["topic.md"] = {"status": "pending", "source_count": 2, "is_new": False, "error": None}
    m = mark_target_reduced(m, "topic.md")
    assert m["targets"]["topic.md"]["status"] == "reduced"
    m["targets"]["topic.md"] = {"status": "pending", "source_count": 2, "is_new": False, "error": None}
    m = mark_target_failed(m, "topic.md", "context overflow")
    assert m["targets"]["topic.md"]["status"] == "failed"
    assert m["targets"]["topic.md"]["error"] == "context overflow"


def test_retry_failed_requeues_both_phases(tmp_path: Path) -> None:
    m = build_bulk_manifest([tmp_path / "a.md"])
    m = mark_source_failed(m, str(tmp_path / "a.md"), "x")
    m["targets"]["t.md"] = {"status": "failed", "source_count": 1, "is_new": True, "error": "y"}
    m = retry_failed(m)
    assert m["sources"][str(tmp_path / "a.md")]["status"] == "pending"
    assert m["targets"]["t.md"]["status"] == "pending"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "target_trans or retry" -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
def mark_target_reduced(manifest: dict, target_file: str) -> dict:
    manifest["targets"][target_file]["status"] = "reduced"
    manifest["targets"][target_file]["error"] = None
    return manifest


def mark_target_failed(manifest: dict, target_file: str, error: str) -> dict:
    manifest["targets"][target_file]["status"] = "failed"
    manifest["targets"][target_file]["error"] = error
    return manifest


def retry_failed(manifest: dict) -> dict:
    """Reset all failed sources and targets back to pending."""
    for v in manifest["sources"].values():
        if v["status"] == "failed":
            v["status"] = "pending"
            v["error"] = None
    for v in manifest["targets"].values():
        if v["status"] == "failed":
            v["status"] = "pending"
            v["error"] = None
    return manifest
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "target_trans or retry" -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): target transitions + retry_failed (#208)"
```

---

## Task 6: `normalize_slug` + `estimate_tokens`

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import estimate_tokens, normalize_slug


def test_normalize_slug_collapses_variants() -> None:
    assert normalize_slug("Carbon Accounting") == "carbon-accounting"
    assert normalize_slug("carbon_accounting") == "carbon-accounting"
    assert normalize_slug("carbon-accounting.md") == "carbon-accounting"
    assert normalize_slug("  Carbon  Accounting  ") == "carbon-accounting"


def test_estimate_tokens_chars_over_four() -> None:
    assert estimate_tokens("a" * 400) == 100
    assert estimate_tokens("") == 0
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "normalize or estimate" -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
def normalize_slug(text: str) -> str:
    """Normalise a topic name/slug for new-topic dedup: lowercase, strip .md,
    collapse non-alphanumerics to single hyphens."""
    s = str(text).lower()
    if s.endswith(".md"):
        s = s[:-3]
    return _SLUG_RE.sub("-", s).strip("-")


def estimate_tokens(text: str) -> int:
    """Cheap token estimate: ~4 chars per token."""
    return len(text) // 4
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "normalize or estimate" -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): normalize_slug + estimate_tokens helpers (#208)"
```

---

## Task 7: `route_extracts` — group, fuzzy-merge new topics, pre-allocate, size-guard

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

This is the correctness heart of the reduce phase. An extract's `targets` is a list of
either `{"file": "<existing>.md", "finding_idx": [...]}` or
`{"new_topic_slug": "<slug>", "title": "<Title>", "finding_idx": [...]}`.

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import route_extracts


def _extract(source, targets):
    return {"source": source, "findings": ["f"], "statistics": [], "citations": [],
            "confidence": "medium", "targets": targets}


def test_route_groups_existing_files_by_name() -> None:
    extracts = [
        _extract("a.md", [{"file": "topic.md", "finding_idx": [0]}]),
        _extract("b.md", [{"file": "topic.md", "finding_idx": [0]}]),
    ]
    r = route_extracts(extracts, existing_files={"topic.md"}, size_threshold=10_000_000)
    assert set(r.targets) == {"topic.md"}
    assert len(r.targets["topic.md"]["extracts"]) == 2
    assert r.targets["topic.md"]["is_new"] is False
    assert r.oversized == []


def test_route_fuzzy_merges_new_topic_variants() -> None:
    extracts = [
        _extract("a.md", [{"new_topic_slug": "Carbon Accounting", "title": "Carbon Accounting", "finding_idx": [0]}]),
        _extract("b.md", [{"new_topic_slug": "carbon_accounting", "title": "Carbon Accounting", "finding_idx": [0]}]),
    ]
    r = route_extracts(extracts, existing_files=set(), size_threshold=10_000_000)
    assert set(r.targets) == {"carbon-accounting.md"}        # one pre-allocated new file
    assert r.targets["carbon-accounting.md"]["is_new"] is True
    assert len(r.targets["carbon-accounting.md"]["extracts"]) == 2


def test_route_new_topic_colliding_with_existing_file_routes_to_existing() -> None:
    extracts = [_extract("a.md", [{"new_topic_slug": "topic", "title": "Topic", "finding_idx": [0]}])]
    r = route_extracts(extracts, existing_files={"topic.md"}, size_threshold=10_000_000)
    assert set(r.targets) == {"topic.md"}
    assert r.targets["topic.md"]["is_new"] is False


def test_route_source_touching_multiple_files_fans_out() -> None:
    extracts = [_extract("a.md", [
        {"file": "x.md", "finding_idx": [0]},
        {"file": "y.md", "finding_idx": [1]},
    ])]
    r = route_extracts(extracts, existing_files={"x.md", "y.md"}, size_threshold=10_000_000)
    assert set(r.targets) == {"x.md", "y.md"}


def test_route_flags_oversized_and_excludes_from_targets() -> None:
    big = {"source": "a.md", "findings": ["x" * 4000], "statistics": [], "citations": [],
           "confidence": "low", "targets": [{"file": "hot.md", "finding_idx": [0]}]}
    r = route_extracts([big], existing_files={"hot.md"}, size_threshold=100)
    assert "hot.md" in r.oversized
    assert "hot.md" not in r.targets
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k route -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
def _target_key(target: dict, existing_files: set) -> tuple[str, bool]:
    """Resolve a single target entry to (target_file, is_new).

    Existing-file targets keep their filename. New-topic proposals are
    slug-normalised; if the normalised slug matches an existing file it routes
    there (is_new=False), else it becomes "<slug>.md" (is_new=True).
    """
    if "file" in target:
        return target["file"], False
    norm = normalize_slug(target.get("new_topic_slug", target.get("title", "")))
    candidate = f"{norm}.md"
    if candidate in existing_files:
        return candidate, False
    return candidate, True


def route_extracts(extracts, existing_files, size_threshold) -> RouteResult:
    """Group extracts by target library file.

    - existing-file targets group by filename
    - new-topic proposals are slug-normalised and fuzzy-merged (variants of the
      same slug collapse to one pre-allocated "<slug>.md")
    - a source touching multiple targets is added to each group
    - per-file: estimate combined token size; files exceeding size_threshold are
      moved to .oversized and excluded from .targets
    """
    existing_files = set(existing_files)
    targets: dict[str, dict] = {}

    for extract in extracts:
        for target in extract.get("targets", []):
            tfile, is_new = _target_key(target, existing_files)
            slot = targets.setdefault(
                tfile, {"extracts": [], "is_new": is_new, "est_tokens": 0}
            )
            # an existing-file resolution wins over a new-topic guess
            if not is_new:
                slot["is_new"] = False
            slot["extracts"].append(extract)

    # size estimate per target (sum of its extracts' serialized size)
    oversized: list[str] = []
    for tfile, slot in list(targets.items()):
        est = sum(estimate_tokens(json.dumps(e)) for e in slot["extracts"])
        slot["est_tokens"] = est
        if est > size_threshold:
            oversized.append(tfile)
            del targets[tfile]

    return RouteResult(targets=targets, oversized=sorted(oversized))
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k route -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): route_extracts grouping + fuzzy-merge + size-guard (#208)"
```

---

## Task 8: Prompt formatters (map + reduce)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    format_extract_prompt, format_reduce_prompt,
)


def test_format_extract_prompt_contains_contract() -> None:
    req = ExtractDispatchRequest(
        source_path="raw/a.md", library_path="library",
        shelf_index_path="library/_shelf-index.md", extractor_model="claude-haiku-4-5",
    )
    p = format_extract_prompt(req)
    assert "raw/a.md" in p
    assert "library/_shelf-index.md" in p
    assert "JSON" in p
    assert "targets" in p             # must instruct target proposal
    assert "read-only" in p.lower()   # must forbid library writes


def test_format_reduce_prompt_includes_extracts_and_mode() -> None:
    req = ReduceDispatchRequest(
        target_file="topic.md", is_new=False, library_path="library",
        shelf_index_path="library/_shelf-index.md",
        extracts=[{"source": "a.md", "findings": ["f1"], "targets": []}],
    )
    p = format_reduce_prompt(req)
    assert "topic.md" in p
    assert "f1" in p
    assert "BULK_REDUCE" in p
    assert "Do NOT run kb-rebuild-indexes" in p
    assert "Do NOT append to log.md" in p


def test_format_reduce_prompt_new_file_flag() -> None:
    req = ReduceDispatchRequest(
        target_file="new-topic.md", is_new=True, library_path="library",
        shelf_index_path="library/_shelf-index.md", extracts=[],
    )
    p = format_reduce_prompt(req)
    assert "create" in p.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "format_extract or format_reduce" -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
def format_extract_prompt(req: ExtractDispatchRequest) -> str:
    """Prompt for one knowledge-extractor (map phase). Read-only; returns JSON."""
    return "\n".join([
        "MAP_EXTRACT — read-only extraction, no library writes.",
        "",
        f"Source: {req.source_path}",
        f"Library: {req.library_path}",
        f"Shelf-index: {req.shelf_index_path}",
        "",
        "Read the source and the shelf-index (read-only — do NOT write any "
        "library file). Emit ONLY a JSON object with this shape:",
        '{',
        '  "source": "<source path>",',
        '  "findings": ["<concise finding>", ...],',
        '  "statistics": ["<stat with number + context>", ...],',
        '  "citations": ["<citation string>", ...],',
        '  "confidence": "high|medium|low",',
        '  "targets": [',
        '    {"file": "<existing-shelf-index-file>.md", "finding_idx": [<int>, ...]},',
        '    {"new_topic_slug": "<slug>", "title": "<Title>", "finding_idx": [<int>, ...]}',
        '  ]',
        '}',
        "",
        "Rules: keep findings SUMMARISED (no verbatim transcription); match "
        "existing files by name from the shelf-index; propose a new_topic only "
        "when no existing file fits; finding_idx are indices into findings[].",
    ])


def format_reduce_prompt(req: ReduceDispatchRequest) -> str:
    """Prompt for one agent-knowledge-updater (reduce phase) for a single file."""
    action = "CREATE this new file" if req.is_new else "UPDATE this existing file"
    return "\n".join([
        "BULK_REDUCE — synthesise all routed extracts into exactly one file.",
        "Constraints: (1) write ONLY the target file; (2) Do NOT run "
        "kb-rebuild-indexes; (3) Do NOT append to log.md.",
        "",
        f"Target file: {req.target_file} ({action})",
        f"Library: {req.library_path}",
        f"Shelf-index: {req.shelf_index_path}",
        "",
        "Apply the standard agent-knowledge-updater rules: extend-vs-create, "
        "contradiction flagging, citation discipline, and confidence frontmatter. "
        "You see ALL findings for this topic at once — dedupe and reconcile "
        "contradictions across them.",
        "",
        "Extracts routed to this file (JSON):",
        json.dumps(req.extracts, indent=2),
    ])
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "format_extract or format_reduce" -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): map/reduce prompt formatters (#208)"
```

---

## Task 9: Finalize — run summary + log entry

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`
- Test: `tests/test_kb_ingest_bulk.py`

- [ ] **Step 1: Write the failing tests**

```python
from sdlc_knowledge_base_scripts.kb_ingest_bulk import summarize_run, write_log_entry


def test_summarize_run_counts(tmp_path: Path) -> None:
    m = build_bulk_manifest([tmp_path / "a.md", tmp_path / "b.md", tmp_path / "c.md"])
    m = mark_source_extracted(m, str(tmp_path / "a.md"))
    m = mark_source_extracted(m, str(tmp_path / "b.md"))
    m = mark_source_failed(m, str(tmp_path / "c.md"), "timeout")
    m["targets"]["t1.md"] = {"status": "reduced", "source_count": 2, "is_new": True, "error": None}
    summary = summarize_run(m, oversized=["hot.md"])
    assert "3" in summary           # total sources
    assert "timeout" in summary or "1" in summary   # failure surfaced
    assert "hot.md" in summary      # oversized surfaced


def test_write_log_entry_appends(tmp_path: Path) -> None:
    log = tmp_path / "log.md"
    log.write_text("# Log\n")
    write_log_entry(log, "## [2026-06-03] ingest-bulk | 3 sources / 1 file / 1 failed")
    text = log.read_text()
    assert "ingest-bulk" in text
    assert text.startswith("# Log")   # appended, not overwritten
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "summarize or write_log" -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement**

```python
def summarize_run(manifest: dict, oversized: list) -> str:
    """Produce a human-readable run summary (also embeddable in log.md)."""
    sources = manifest["sources"]
    targets = manifest["targets"]
    total = len(sources)
    extracted = sum(1 for v in sources.values() if v["status"] == "extracted")
    failed_sources = [k for k, v in sources.items() if v["status"] == "failed"]
    reduced = sum(1 for v in targets.values() if v["status"] == "reduced")
    failed_targets = [k for k, v in targets.items() if v["status"] == "failed"]
    new_files = sum(1 for v in targets.values() if v.get("is_new"))

    lines = [
        f"Sources: {total} total, {extracted} extracted, {len(failed_sources)} failed",
        f"Files: {reduced} reduced ({new_files} new), {len(failed_targets)} failed",
    ]
    if failed_sources:
        lines.append("Failed sources: " + ", ".join(sorted(failed_sources)))
    if failed_targets:
        lines.append("Failed files: " + ", ".join(sorted(failed_targets)))
    if oversized:
        lines.append("Oversized (skipped, run manually): " + ", ".join(sorted(oversized)))
    return "\n".join(lines)


def write_log_entry(log_path: Path, summary_line: str) -> None:
    """Append a single consolidated entry to log.md (creates if absent)."""
    log_path = Path(log_path)
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    sep = "" if existing.endswith("\n") or not existing else "\n"
    log_path.write_text(existing + sep + summary_line + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -k "summarize or write_log" -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py tests/test_kb_ingest_bulk.py
git commit -m "feat(kb): run summary + consolidated log entry (#208)"
```

---

## Task 10: Integration test — full map→route→reduce→finalize with mocked dispatcher

**Files:**
- Test: `tests/test_kb_ingest_bulk.py`

This proves the pieces compose, using the orchestrator-style injectable dispatcher
pattern (no real Agent calls). It also locks the resume contract: an existing valid
extract file means the source is skipped.

- [ ] **Step 1: Write the failing integration test**

```python
import json as _json


def _seed_library(tmp_path: Path) -> tuple[Path, Path, Path]:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- existing.md\n")
    (lib / "existing.md").write_text("---\nlayer: domain\nconfidence: medium\n---\n# Existing\n")
    (lib / "log.md").write_text("# Log\n")
    return lib, lib / "_shelf-index.md", lib / "log.md"


def test_end_to_end_with_mock_dispatcher(tmp_path: Path) -> None:
    lib, shelf, log = _seed_library(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "s1.md").write_text("source one")
    (raw / "s2.md").write_text("source two")
    extracts_dir = lib / ".extracts"

    # --- MAP: mock extractor returns JSON keyed by source ---
    def map_dispatch(req: ExtractDispatchRequest) -> str:
        name = Path(req.source_path).name
        target = ([{"file": "existing.md", "finding_idx": [0]}] if name == "s1.md"
                  else [{"new_topic_slug": "fresh-topic", "title": "Fresh Topic", "finding_idx": [0]}])
        return _json.dumps({
            "source": req.source_path, "findings": [f"finding from {name}"],
            "statistics": [], "citations": [], "confidence": "medium", "targets": target,
        })

    sources = discover_sources(raw)
    manifest = build_bulk_manifest(sources, run_meta={"size_threshold": 10_000_000})
    for src in sources:
        result = map_dispatch(ExtractDispatchRequest(
            source_path=str(src), library_path=str(lib),
            shelf_index_path=str(shelf), extractor_model="claude-haiku-4-5"))
        extract = _json.loads(result)
        persist_extract(extracts_dir, slug_for_source(src), extract)
        mark_source_extracted(manifest, str(src))

    # --- ROUTE ---
    loaded = [_json.loads(p.read_text()) for p in sorted(extracts_dir.glob("*.json"))]
    route = route_extracts(loaded, existing_files={"existing.md"}, size_threshold=10_000_000)
    assert set(route.targets) == {"existing.md", "fresh-topic.md"}
    assert route.targets["fresh-topic.md"]["is_new"] is True

    # --- REDUCE: mock updater writes the file ---
    def reduce_dispatch(req: ReduceDispatchRequest) -> str:
        path = Path(req.library_path) / req.target_file
        path.write_text(f"# {req.target_file}\n" +
                        "\n".join(f"- {e['findings'][0]}" for e in req.extracts) + "\n")
        return "done"

    for tfile, slot in route.targets.items():
        manifest["targets"][tfile] = {
            "status": "pending", "source_count": len(slot["extracts"]),
            "is_new": slot["is_new"], "error": None}
        reduce_dispatch(ReduceDispatchRequest(
            target_file=tfile, is_new=slot["is_new"], library_path=str(lib),
            shelf_index_path=str(shelf), extracts=slot["extracts"]))
        mark_target_reduced(manifest, tfile)

    # --- FINALIZE ---
    summary = summarize_run(manifest, route.oversized)
    write_log_entry(log, "## [test] ingest-bulk\n" + summary)

    # Assertions: new file created, existing file rewritten, one log entry, no .extracts writes to library files
    assert (lib / "fresh-topic.md").exists()
    assert "finding from s2.md" in (lib / "fresh-topic.md").read_text()
    assert "finding from s1.md" in (lib / "existing.md").read_text()
    assert (log.read_text().count("ingest-bulk")) == 1
    # resume: re-running build_bulk_manifest keeps extracted status
    m2 = build_bulk_manifest(sources, existing=manifest)
    assert all(v["status"] == "extracted" for v in m2["sources"].values())
```

- [ ] **Step 2: Run to verify it passes**

Run: `python -m pytest tests/test_kb_ingest_bulk.py::test_end_to_end_with_mock_dispatcher -v`
Expected: PASS

- [ ] **Step 3: Run the full module suite**

Run: `python -m pytest tests/test_kb_ingest_bulk.py -v`
Expected: PASS (all tests from Tasks 1-10)

- [ ] **Step 4: Commit**

```bash
git add tests/test_kb_ingest_bulk.py
git commit -m "test(kb): end-to-end map-route-reduce-finalize integration (#208)"
```

---

## Task 11: `knowledge-extractor` agent

**Files:**
- Create: `agents/knowledge-base/knowledge-extractor.md` (⚠️ ROOT source)

- [ ] **Step 1: Write the agent definition**

Create `agents/knowledge-base/knowledge-extractor.md`:

```markdown
---
name: knowledge-extractor
description: "Read-only map-phase extractor for bulk knowledge-base ingest. Reads ONE source, emits a compact structured JSON extraction — findings, statistics, citations, confidence, and proposed target library files — and never writes any library file. Lightweight and Haiku-capable: mechanical extraction, not synthesis. Dispatched many-wide by kb-ingest-bulk; the agent-knowledge-updater does the synthesis in the reduce phase."
model: haiku
tools: Read, Glob, Grep, WebFetch
color: green
---

# Knowledge Extractor

You are the Knowledge Extractor — the map phase of bulk knowledge-base ingest.
You read **one** source and emit a compact structured extraction. You are
strictly **read-only against the library**: you never create, edit, or delete
any library file. The reduce phase (`agent-knowledge-updater`) does all writing.

## Your contract

1. **Read the one source** you are given (file path, or URL via WebFetch).
2. **Read the shelf-index** (read-only) to learn which library files already exist.
3. **Emit ONLY a JSON object** — no prose before or after — with this shape:

```json
{
  "source": "<source path or URL>",
  "findings": ["<concise, summarised finding>", "..."],
  "statistics": ["<statistic: number + unit + context>", "..."],
  "citations": ["<citation string as it appears in the source>", "..."],
  "confidence": "high|medium|low",
  "targets": [
    {"file": "<existing-file-from-shelf-index>.md", "finding_idx": [0, 2]},
    {"new_topic_slug": "<kebab-slug>", "title": "<Human Title>", "finding_idx": [1]}
  ]
}
```

## Rules

- **Summarise, never transcribe.** Findings are short statements, not verbatim
  paragraphs. This keeps extracts bounded so the reduce agent can hold many at once.
- **Match existing files by name** from the shelf-index whenever a finding fits one.
- **Propose a `new_topic_slug`** only when no existing file fits. Use a clear
  kebab-case slug and a human `title`.
- **`finding_idx`** are zero-based indices into your own `findings` array, mapping
  each finding to the file(s) it belongs in. A finding may appear under multiple targets.
- **Set `confidence`** from the source type (academic/industry-report → high;
  practitioner/case-study/vendor → medium; blog/informal → low).
- **Never write to the library.** If you cannot read the source, emit a JSON object
  with an empty `findings`/`targets` and `confidence: "low"` — do not guess content.
```

- [ ] **Step 2: Verify frontmatter parses**

Run: `python -c "import yaml,re,pathlib; t=pathlib.Path('agents/knowledge-base/knowledge-extractor.md').read_text(); m=re.match(r'^---\s*\n(.*?)\n---', t, re.DOTALL); print(yaml.safe_load(m.group(1))['name'])"`
Expected: `knowledge-extractor`

- [ ] **Step 3: Commit**

```bash
git add agents/knowledge-base/knowledge-extractor.md
git commit -m "feat(kb): knowledge-extractor map-phase agent (#208)"
```

---

## Task 12: `kb-ingest-bulk` skill

**Files:**
- Create: `plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/SKILL.md`

- [ ] **Step 1: Write the skill**

Create `plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/SKILL.md`. Model it on
`kb-ingest-batch/SKILL.md` (same module-loader bootstrap), but drive the four phases.
Full content:

````markdown
---
name: kb-ingest-bulk
description: Parallel map-reduce bulk ingest for large source sets. Map phase dispatches read-only knowledge-extractor agents (≤N-wide, default Haiku) emitting per-source JSON extracts; Python routes extracts by target library file (fuzzy-merging new topics, pre-allocating new files, flagging oversized topics); reduce phase dispatches one agent-knowledge-updater per file (parallel, one writer per file); single shelf-index rebuild + one log.md entry. Resumable. Supersedes kb-ingest-batch.
disable-model-invocation: false
argument-hint: "<glob|dir|file-list> [--library <path>] [--parallel <N>] [--extractor-model <id>] [--size-threshold <tokens>] [--retry-failed] [--clean]"
---

# Bulk Ingestion (map-reduce)

Load a large source set into the knowledge base in parallel. Four phases:
**map** (parallel extract) → **route** (Python) → **reduce** (parallel synthesis,
one writer per file) → **finalize** (one rebuild + one log entry).

## Arguments

| Argument | Description |
|---|---|
| `<glob\|dir\|file-list>` | Sources to ingest |
| `--library <path>` | Target library, bypassing CLAUDE.md resolution (default: CLAUDE.md-resolved). For isolated testing / multi-library — see #209 |
| `--parallel <N>` | Concurrency for map + reduce rounds (default 16, max 64) |
| `--extractor-model <id>` | Map model (default `claude-haiku-4-5`) |
| `--size-threshold <tokens>` | Per-file reduce size guard (default 200000) |
| `--retry-failed` | Re-queue failed sources/targets from a prior run |
| `--clean` | Remove `library/.extracts/` after a successful run |

## Preflight

1. Resolve `library_path`: if `--library` given, use it; else read CLAUDE.md
   `## Knowledge Base` section. Derive `shelf_index_path = <library>/_shelf-index.md`,
   `log_path = <library>/log.md`, `extracts_dir = <library>/.extracts`.
2. Verify `knowledge-extractor` and `agent-knowledge-updater` agents are available.
3. Clamp `--parallel` to [1, 64].

## Module bootstrap

Use the same `CLAUDE_PLUGIN_ROOT` loader block as `kb-ingest-batch/SKILL.md` to import
`sdlc_knowledge_base_scripts.kb_ingest_bulk`.

## Phase 1 — Map (parallel ≤N)

1. `discover_sources(<spec>)` → source list; `build_bulk_manifest(...)` (merge prior
   manifest if present; `retry_failed` if `--retry-failed`); `save_manifest`.
2. For each pending source whose extract file does NOT already exist (resume skip):
   dispatch `knowledge-extractor` with `format_extract_prompt(...)`, up to N concurrently
   (parallel Agent-tool calls). Capture each agent's JSON reply.
3. After each agent: `persist_extract(extracts_dir, slug, json)` then
   `mark_source_extracted`; on error/invalid-JSON `mark_source_failed`. `save_manifest`
   after each round.

## Phase 2 — Route (Python, no agents)

4. Load all extract JSON files. Compute `existing_files` = set of `*.md` in the library
   (excluding `_shelf-index.md`, `log.md`, `_index.md`, `raw/`).
5. `route = route_extracts(extracts, existing_files, size_threshold)`. Record each
   `route.targets` entry into `manifest["targets"]` as `pending` with `source_count`
   and `is_new`. Report `route.oversized` (skipped). `save_manifest`.

## Phase 3 — Reduce (parallel ≤N, one writer per file)

6. For each pending target: dispatch ONE `agent-knowledge-updater` with
   `format_reduce_prompt(ReduceDispatchRequest(...))`, up to N concurrently. Exactly one
   agent per file — never two agents on the same file.
7. After each: `mark_target_reduced` (success) or `mark_target_failed` (error).
   `save_manifest` after each round.

## Phase 4 — Finalize (once)

8. Rebuild the shelf-index once via `build_shelf_index.main([library_path])`.
9. `write_log_entry(log_path, "## [<date>] ingest-bulk\n" + summarize_run(manifest, route.oversized))`.
10. Print the summary table. If `--clean`, remove `extracts_dir`.

## Exit / partial failure

A failed source drops out of routing; a failed target leaves its extracts on disk for
`--retry-failed`. Report all failures + oversized topics. Non-zero exit only if nothing
succeeded.
````

- [ ] **Step 2: Verify frontmatter parses**

Run: `python -c "import yaml,re,pathlib; t=pathlib.Path('plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/SKILL.md').read_text(); m=re.match(r'^---\s*\n(.*?)\n---', t, re.DOTALL); print(yaml.safe_load(m.group(1))['name'])"`
Expected: `kb-ingest-bulk`

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/SKILL.md
git commit -m "feat(kb): kb-ingest-bulk orchestration skill (#208)"
```

---

## Task 13: Edits — `--library` on kb-init, deprecate kb-ingest-batch, release-mapping, docs

**Files:**
- Modify: `skills/kb-init/SKILL.md` (⚠️ ROOT source)
- Modify: `plugins/sdlc-knowledge-base/skills/kb-ingest-batch/SKILL.md`
- Modify: `release-mapping.yaml`
- Modify: `CLAUDE.md` (Available Skills table) and `plugins/sdlc-knowledge-base/README.md`

- [ ] **Step 1: Add `--library` to kb-init**

In `skills/kb-init/SKILL.md`, extend the `argument-hint` to include `[--library <path>]`,
add an Arguments row, and add a preflight line:

```markdown
- `--library <path>` — Initialise a library at this explicit path instead of `./library`
  and skip the CLAUDE.md append (the section assumes one library at the default path).
  Use for isolated testing or a secondary library. See #209.
```

In step 5 (directory creation), instruct: "If `--library <path>` is given, create the
structure under `<path>` instead of `./library`, and skip steps 2–4 (the CLAUDE.md
append)."

- [ ] **Step 2: Add deprecation banner to kb-ingest-batch**

At the top of `plugins/sdlc-knowledge-base/skills/kb-ingest-batch/SKILL.md` body (after
frontmatter), add:

```markdown
> **Deprecated (v0.3.0+):** Prefer `/sdlc-knowledge-base:kb-ingest-bulk`, which adds a
> parallel map-reduce path that can update existing shared files (this skill is
> create-only). `kb-ingest-batch` remains functional for simple create-only batches.
```

- [ ] **Step 3: Register new files in release-mapping.yaml**

Under `sdlc-knowledge-base:`, add to `agents:`:
```yaml
    - source: agents/knowledge-base/knowledge-extractor.md
```
to `skills:`:
```yaml
    - source: plugins/sdlc-knowledge-base/skills/kb-ingest-bulk/SKILL.md
```
to `scripts:`:
```yaml
    - source: plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py
```

- [ ] **Step 4: Update skill tables**

In `CLAUDE.md` Available Skills table and `plugins/sdlc-knowledge-base/README.md`, add a
`kb-ingest-bulk` row and mark `kb-ingest-batch` deprecated.

- [ ] **Step 5: Commit**

```bash
git add skills/kb-init/SKILL.md plugins/sdlc-knowledge-base/skills/kb-ingest-batch/SKILL.md release-mapping.yaml CLAUDE.md plugins/sdlc-knowledge-base/README.md
git commit -m "feat(kb): --library on kb-init, deprecate kb-ingest-batch, register bulk in release-mapping + docs (#208)"
```

---

## Task 14: Package, validate, live smoke

**Files:** none new — verification + release sync.

- [ ] **Step 1: Run release-plugin to sync sources into plugin dirs**

Run: `/sdlc-core:release-plugin` (or `python -m <release tool>` per repo convention).
This copies `agents/knowledge-base/knowledge-extractor.md` and the kb-init source edit
into the plugin dirs.

- [ ] **Step 2: Verify plugin packaging sync**

Run: `python tools/validation/check-plugin-packaging.py`
Expected: PASS (all sources packaged)

- [ ] **Step 3: Run the full module suite + broader kb suite**

Run: `python -m pytest tests/test_kb_ingest_bulk.py tests/test_kb_ingest_batch.py -v`
Expected: PASS

- [ ] **Step 4: Quick checks**

Run:
```bash
python tools/validation/check-technical-debt.py --threshold 0
python tools/validation/check-broken-references.py
```
Expected: no new violations.

- [ ] **Step 5: Live smoke against a throwaway library (~15 files)**

```bash
ls tmp_texts/*.md | head -15 > tmp/bulk-smoke-list.txt
mkdir -p tmp/cri-bulk-test
```
Then invoke (in-session, real agents):
- `/sdlc-knowledge-base:kb-init --empty --library tmp/cri-bulk-test/library`
- `/sdlc-knowledge-base:kb-ingest-bulk tmp/bulk-smoke-list.txt --library tmp/cri-bulk-test/library --parallel 8`

Verify: extracts created under `tmp/cri-bulk-test/library/.extracts/`, real + new topic
files written, `_shelf-index.md` rebuilt once, one `log.md` entry, project `library/`
untouched. Re-run the same command → all sources skipped (resume). Record evidence in the
retrospective.

- [ ] **Step 6: Commit any doc/evidence updates + final pre-push**

```bash
git add -A
git commit -m "test(kb): live-smoke evidence + packaging sync for kb-ingest-bulk (#208)"
python tools/validation/local-validation.py --pre-push
```

---

## Self-review notes

- **Spec coverage:** map/route/reduce/finalize (Tasks 2-12), resumable manifest (4,5,10),
  per-source extract files only / no shared writes in map (3,11), one writer per file
  (12 step 6), citation/contradiction rules preserved (reduce prompt Task 8 + reused
  agent), one rebuild + one log (9,12), extractor model configurable / updater Sonnet
  (11,12), graceful partial failure (5,9,12), `--library` (12,13), test plan tiers
  (10 = mocked; 14 step 5 = live smoke). New-file pre-allocation + fuzzy-merge (7).
  Size-guard flag-and-skip (7,9). Deprecation (13).
- **Out-of-scope confirmed:** chunked reduce, Workflow-tool orchestration, full
  `--libraries` federation (#209) — none implemented here.

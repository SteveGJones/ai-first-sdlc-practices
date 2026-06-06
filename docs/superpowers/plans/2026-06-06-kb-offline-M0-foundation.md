# kb-offline M0 — Foundation & Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove the four foundational contracts of the kb-offline backend — claim/evidence schema, durable journaled mutation with fencing, resume-selection, and the backend ownership boundary — plus a minimal Anthropic-backed `kb-offline` CLI that exercises them end-to-end.

**Architecture:** Pure-Python typed contracts (Pydantic v2) + a deterministic mutation/journal/recovery layer + a resume/locking/fencing layer (manifest-backed) + a narrow `generate/embed` backend seam with an Anthropic and a Fake implementation + thin pipeline operations that orchestrate them. No Ollama, no LangGraph, no embeddings in M0 (those are M1/M3). All new code lives in the `sdlc_knowledge_base_scripts` package; the deterministic core (`route_extracts`, `build_shelf_index`) is reused verbatim.

**Tech Stack:** Python 3.9+, Pydantic v2 (already installed), pytest, the existing `sdlc-knowledge-base-scripts` distribution. Spec: `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md`.

---

## Scope: M0 only

This plan covers **M0** from the spec. It explicitly does **not** implement: `OllamaBackend`, LangGraph graphs, `ingest-bulk`, federation, promotion-beyond-contract, embeddings, or cross-library hygiene. Those are M1–M4 and get their own plans after M0's contracts are proven.

M0 exit criteria (from spec): the four contracts resolved & unit-proven; pipeline runs `extract`/`reduce`/`select`/`synthesize` via `AnthropicBackend`/`FakeBackend`; resume + journal + fencing CLI-provable end-to-end on the Anthropic path; prompt-parity check green; eval-harness skeleton runs on the fixture; model-quality thresholds ratified.

## File structure (M0)

| File | Responsibility |
|---|---|
| `plugins/sdlc-knowledge-base/scripts/contracts.py` | Pydantic models: `ExtractJSON`, `Answer`/`Claim`/`Span`/`PageRef`, `MutationProposal`, enums |
| `plugins/sdlc-knowledge-base/scripts/durability.py` | `atomic_write_text` (fsync file + dir); shared durable-write primitive |
| `plugins/sdlc-knowledge-base/scripts/resume.py` | hashes, `LibraryLock` (PID+heartbeat+monotonic fencing token), run lifecycle, latest-compatible selection |
| `plugins/sdlc-knowledge-base/scripts/mutation.py` | `validate_proposal`, operation journal (WAL stages), `commit_mutation` (fencing + CAS + durable commit), `recover` |
| `plugins/sdlc-knowledge-base/scripts/backends/base.py` | `Backend` protocol: `generate(prompt, schema=None)`, `embed(texts)` |
| `plugins/sdlc-knowledge-base/scripts/backends/fake_backend.py` | deterministic test backend |
| `plugins/sdlc-knowledge-base/scripts/backends/anthropic_backend.py` | direct Anthropic API backend (guarded import) |
| `plugins/sdlc-knowledge-base/scripts/prompts.py` | canonical operation prompt fragments (constants) |
| `plugins/sdlc-knowledge-base/scripts/pipeline.py` | `extract`/`select`/`synthesize`/`reduce`/`promote` operations (validate→repair→fail, mutation orchestration) |
| `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py` | minimal `kb-offline` CLI (`init`, `ingest`, `query`, `--backend`, `--resume`) |
| `plugins/sdlc-knowledge-base/scripts/eval/harness.py` + `eval/fixture/` | eval skeleton + labelled fixture + metrics |
| `tools/validation/check-prompt-parity.py` | managed-block drift check |
| Modify `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`, `kb_ingest_batch.py` | route writes through `durability.atomic_write_text` (fsync upgrade) |
| Modify `plugins/sdlc-knowledge-base/pyproject.toml` | add `pydantic` dep + `kb-offline` console script |
| Tests | `tests/test_kb_offline_*.py`, `tests/test_prompt_parity.py` |

---

## Task 1: Feature proposal + retrospective stubs (CI-required sections)

**Files:**
- Create: `docs/feature-proposals/211-kb-offline-langgraph.md`
- Create: `retrospectives/211-kb-offline-langgraph.md`

- [ ] **Step 1: Write the proposal** (uses the CI-required sections — `check-feature-proposal.py` needs `Target Branch:` / `## Motivation` / `## Proposed Solution` / `## Success Criteria`)

Create `docs/feature-proposals/211-kb-offline-langgraph.md`:

```markdown
# Feature Proposal #211 — kb-offline: LangGraph + Ollama backend (M0 foundation)

**Status:** In progress
**Target Branch:** `feature/211-kb-offline-langgraph`

## Motivation
The knowledge-base kit is token-heavy and cloud-only. A pluggable local backend (LangGraph +
Ollama) cuts token cost to ~zero and runs offline. This EPIC also completes the LLM-wiki's
shared-core story. M0 builds the safety foundation first: typed contracts, durable journaled
mutation with fencing, resume-selection, and the backend ownership boundary.

## Proposed Solution
See `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md`. M0 delivers contracts.py,
durability.py, resume.py, mutation.py, the generate/embed backend seam (Anthropic + Fake),
pipeline.py, a minimal Anthropic-backed `kb-offline` CLI, prompt-parity CI check, and an
eval-harness skeleton.

## Success Criteria
- [ ] Claim-structured Answer + MutationProposal contracts (Pydantic), unit-proven.
- [ ] Durable journaled mutation: WAL ordering, fencing token, create/extend CAS, fsync, recovery.
- [ ] Resume-selection: `--resume`/latest-compatible, lifecycle states, stale-lock TTL.
- [ ] Backend = generate/embed only; pipeline owns validation + mutation.
- [ ] Anthropic-backed `kb-offline ingest`/`query` exercise the foundation end-to-end.
- [ ] Prompt-parity drift check green; eval skeleton runs on the fixture; thresholds ratified.

## Out of scope (this milestone)
Ollama backend, LangGraph graphs, ingest-bulk, federation, embeddings, promotion beyond contract —
M1–M4.
```

- [ ] **Step 2: Write the retrospective stub**

Create `retrospectives/211-kb-offline-langgraph.md`:

```markdown
# Retrospective: kb-offline M0 — Foundation (#211)

## What we set out to do
Build and prove the four foundational contracts (claim schema, journaled mutation+fencing,
resume-selection, backend boundary) + a minimal Anthropic-backed CLI.

## What went well
_(fill in during/after implementation)_

## What was hard
_(fill in)_

## Lessons
_(fill in)_

## Test evidence
_(pytest counts; recovery/fencing test results; eval-skeleton run)_
```

- [ ] **Step 3: Commit**

```bash
cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices
git add docs/feature-proposals/211-kb-offline-langgraph.md retrospectives/211-kb-offline-langgraph.md
git commit -m "docs: feature proposal + retrospective stub for kb-offline M0 (#211)"
```

---

## Task 2: Typed contracts (`contracts.py`)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/contracts.py`
- Test: `tests/test_kb_offline_contracts.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_contracts.py`:

```python
"""Tests for sdlc_knowledge_base_scripts.contracts."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdlc_knowledge_base_scripts.contracts import (
    Answer, Claim, Confidence, EntailmentStatus, ExtractJSON, ExtractTarget,
    MutationAction, MutationProposal, PageRef, Span,
)


def test_extractjson_minimal_and_defaults():
    e = ExtractJSON(source="raw/a.md")
    assert e.findings == [] and e.confidence == Confidence.medium and e.targets == []


def test_extractjson_with_targets():
    e = ExtractJSON(source="a.md", findings=["f"],
                    targets=[ExtractTarget(file="topic.md", finding_idx=[0])])
    assert e.targets[0].file == "topic.md"


def test_claim_entailment_status_optional_and_defaults_none():
    c = Claim(text="x", cited_pages=[PageRef(library="local", page="p.md")],
              evidence_spans=[Span(page="p.md", text="quote")])
    assert c.entailment_status is None        # verifier assigns later; never trusted from model
    assert c.high_impact is False


def test_answer_holds_claims():
    a = Answer(claims=[Claim(text="x")], rendered_text="X.")
    assert a.claims[0].text == "x"


def test_mutation_proposal_requires_action_and_target():
    m = MutationProposal(target_file="t.md", action=MutationAction.create,
                         frontmatter={"layer": "domain", "confidence": "medium"}, body="# T")
    assert m.action == MutationAction.create and m.expected_hash is None


def test_invalid_confidence_rejected():
    with pytest.raises(ValidationError):
        ExtractJSON(source="a.md", confidence="bogus")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && python -m pytest tests/test_kb_offline_contracts.py -v`
Expected: FAIL with `ModuleNotFoundError: ... contracts`.

- [ ] **Step 3: Implement `contracts.py`**

Create `plugins/sdlc-knowledge-base/scripts/contracts.py`:

```python
"""Typed I/O contracts for the kb-offline pipeline (issue #211, M0).

Pydantic v2 models shared by the pipeline, backends, mutation validator, and eval
harness. `entailment_status` is assigned by the deterministic verifier — never trusted
from synthesis-model output.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ExtractTarget(BaseModel):
    file: str | None = None
    new_topic_slug: str | None = None
    title: str | None = None
    finding_idx: list[int] = Field(default_factory=list)


class ExtractJSON(BaseModel):
    source: str
    findings: list[str] = Field(default_factory=list)
    statistics: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.medium
    targets: list[ExtractTarget] = Field(default_factory=list)


class PageRef(BaseModel):
    library: str
    page: str


class Span(BaseModel):
    page: str
    text: str


class EntailmentStatus(str, Enum):
    supported = "supported"
    partial = "partial"
    unsupported = "unsupported"


class Claim(BaseModel):
    text: str
    cited_pages: list[PageRef] = Field(default_factory=list)
    evidence_spans: list[Span] = Field(default_factory=list)
    # Verifier-assigned only; any model-supplied value is discarded by the pipeline.
    entailment_status: EntailmentStatus | None = None
    high_impact: bool = False


class Answer(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    rendered_text: str = ""


class MutationAction(str, Enum):
    create = "create"
    extend = "extend"


class MutationProposal(BaseModel):
    target_file: str
    action: MutationAction
    frontmatter: dict = Field(default_factory=dict)
    body: str = ""
    citations: list[str] = Field(default_factory=list)
    cross_refs: list[str] = Field(default_factory=list)
    # extend: hash of the target page as read during validation (CAS). create: must be None.
    expected_hash: str | None = None
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_contracts.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/contracts.py tests/test_kb_offline_contracts.py
git commit -m "feat(kb-offline): typed contracts — claim-structured Answer + MutationProposal (#211)"
```

---

## Task 3: Durable write primitive (`durability.py`) + #208 fsync upgrade

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/durability.py`
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py` (persist_extract), `kb_ingest_batch.py` (save_manifest)
- Test: `tests/test_kb_offline_durability.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_durability.py`:

```python
"""Tests for sdlc_knowledge_base_scripts.durability."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.durability import atomic_write_text


def test_atomic_write_creates_file(tmp_path: Path):
    p = tmp_path / "sub" / "f.txt"
    atomic_write_text(p, "hello")
    assert p.read_text() == "hello"


def test_atomic_write_overwrites_and_leaves_no_tmp(tmp_path: Path):
    p = tmp_path / "f.txt"
    atomic_write_text(p, "one")
    atomic_write_text(p, "two")
    assert p.read_text() == "two"
    assert list(tmp_path.glob("*.tmp")) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_kb_offline_durability.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `durability.py`**

Create `plugins/sdlc-knowledge-base/scripts/durability.py`:

```python
"""Durable atomic file write (issue #211, M0).

write temp -> fsync file -> atomic replace -> fsync directory. Used by the mutation
committer, the journal, and the upgraded #208 helpers so a crash cannot leave a
half-written or non-durable file.
"""
from __future__ import annotations

import os
from pathlib import Path


def atomic_write_text(path, text: str, encoding: str = "utf-8") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding=encoding) as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    # fsync the directory so the rename itself is durable.
    dir_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return path
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_durability.py -v`
Expected: 2 passed.

- [ ] **Step 5: Route #208 writes through it (fsync upgrade)**

In `plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py`, replace the body of `persist_extract`'s write (the `tmp.write_text(...)` + `tmp.rename(path)` lines) with:

```python
    from .durability import atomic_write_text
    atomic_write_text(path, json.dumps(extract, indent=2))
    return path
```
(Remove the now-unused `tmp = path.with_suffix(".json.tmp")` line.)

In `plugins/sdlc-knowledge-base/scripts/kb_ingest_batch.py`, change `save_manifest` to:

```python
def save_manifest(path: Path, manifest: dict[str, object]) -> None:
    """Atomically + durably write *manifest* as JSON to *path*."""
    from .durability import atomic_write_text
    atomic_write_text(path, json.dumps(manifest, indent=2))
```

- [ ] **Step 6: Run the affected suites to confirm no regression**

Run: `python -m pytest tests/test_kb_ingest_bulk.py tests/test_kb_ingest_batch.py -q`
Expected: all pass (the atomic-write tests there still hold; `.tmp` suffix differs but no test asserts the tmp name).

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/durability.py tests/test_kb_offline_durability.py plugins/sdlc-knowledge-base/scripts/kb_ingest_bulk.py plugins/sdlc-knowledge-base/scripts/kb_ingest_batch.py
git commit -m "feat(kb-offline): durable atomic_write_text + fsync upgrade for #208 helpers (#211)"
```

---

## Task 4: Hashes (`resume.py` part 1)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/resume.py`
- Test: `tests/test_kb_offline_resume.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_resume.py`:

```python
"""Tests for sdlc_knowledge_base_scripts.resume."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.resume import config_hash, content_hash


def test_content_hash_stable_and_sensitive():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abd")


def test_config_hash_order_independent():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    assert config_hash({"a": 1}) != config_hash({"a": 2})
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_kb_offline_resume.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement the hashes**

Create `plugins/sdlc-knowledge-base/scripts/resume.py`:

```python
"""Run identity, hashing, locking (with fencing), and lifecycle for kb-offline (#211, M0).

The manifest is the operator-visible source of run truth; the LangGraph checkpointer
(M1+) is only an internal retry convenience.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
from pathlib import Path


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def config_hash(config: dict) -> str:
    return content_hash(json.dumps(config, sort_keys=True, separators=(",", ":")))
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_resume.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/resume.py tests/test_kb_offline_resume.py
git commit -m "feat(kb-offline): run-identity hashes (#211)"
```

---

## Task 5: Library lock with monotonic fencing token (`resume.py` part 2)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/resume.py`
- Test: `tests/test_kb_offline_resume.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_resume.py`:

```python
from sdlc_knowledge_base_scripts.resume import LibraryLock


def test_fencing_token_monotonic(tmp_path: Path):
    lock1 = LibraryLock(tmp_path)
    t1 = lock1.acquire()
    lock1.release()
    lock2 = LibraryLock(tmp_path)
    t2 = lock2.acquire()
    assert t2 > t1                      # monotonic across acquisitions
    assert lock2.current_token() == t2
    lock2.release()


def test_second_live_acquire_blocked(tmp_path: Path):
    a = LibraryLock(tmp_path)
    a.acquire()
    b = LibraryLock(tmp_path)
    try:
        acquired = b.try_acquire()      # non-blocking
        assert acquired is None         # a holds a live (fresh-heartbeat) lock
    finally:
        a.release()


def test_stale_lock_reclaimed(tmp_path: Path):
    a = LibraryLock(tmp_path, ttl_seconds=0)   # ttl 0 => any prior lock is immediately stale
    a.acquire()
    b = LibraryLock(tmp_path, ttl_seconds=0)
    token = b.try_acquire()             # a's lock is stale -> reclaimable
    assert token is not None and token > 0
    b.release()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_resume.py -k "fencing or live_acquire or stale_lock" -v`
Expected: FAIL (ImportError / attribute errors).

- [ ] **Step 3: Implement `LibraryLock`**

Append to `resume.py` (note: time is read via `time.time()` only inside methods, never at import):

```python
import time

_LOCK_NAME = ".kb-offline/lock.json"
_FENCE_NAME = ".kb-offline/fence.txt"


def _kb_dir(library_path: Path) -> Path:
    d = Path(library_path) / ".kb-offline"
    d.mkdir(parents=True, exist_ok=True)
    return d


class LibraryLock:
    """Per-library advisory lock with PID + heartbeat staleness and a monotonic
    fencing token. The token, checked before every commit, makes stale-lock reclaim
    *safe*: a paused process that lost its lease is fenced out at commit time."""

    def __init__(self, library_path, ttl_seconds: float = 120.0):
        self.library_path = Path(library_path)
        self.ttl = ttl_seconds
        self._token: int | None = None

    def _lockfile(self) -> Path:
        return self.library_path / _LOCK_NAME

    def _fencefile(self) -> Path:
        return self.library_path / _FENCE_NAME

    def _next_token(self) -> int:
        from .durability import atomic_write_text
        _kb_dir(self.library_path)
        f = self._fencefile()
        current = int(f.read_text()) if f.exists() else 0
        nxt = current + 1
        atomic_write_text(f, str(nxt))
        return nxt

    def current_token(self) -> int:
        f = self._fencefile()
        return int(f.read_text()) if f.exists() else 0

    def _read_lock(self) -> dict | None:
        lf = self._lockfile()
        if not lf.exists():
            return None
        try:
            return json.loads(lf.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _is_stale(self, lock: dict, now: float) -> bool:
        if (now - float(lock.get("heartbeat", 0))) > self.ttl:
            return True
        pid = int(lock.get("pid", -1))
        if lock.get("host") == socket.gethostname():
            try:
                os.kill(pid, 0)          # liveness probe
            except (OSError, ProcessLookupError):
                return True
        return False

    def try_acquire(self) -> int | None:
        from .durability import atomic_write_text
        now = time.time()
        existing = self._read_lock()
        if existing is not None and not self._is_stale(existing, now):
            return None
        token = self._next_token()
        atomic_write_text(self._lockfile(), json.dumps({
            "pid": os.getpid(), "host": socket.gethostname(),
            "heartbeat": now, "token": token,
        }))
        self._token = token
        return token

    def acquire(self) -> int:
        token = self.try_acquire()
        if token is None:
            raise RuntimeError(f"library is locked by a live run: {self.library_path}")
        return token

    def heartbeat(self) -> None:
        from .durability import atomic_write_text
        lock = self._read_lock() or {}
        lock["heartbeat"] = time.time()
        atomic_write_text(self._lockfile(), json.dumps(lock))

    def release(self) -> None:
        lf = self._lockfile()
        if lf.exists():
            lf.unlink()
        self._token = None
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_resume.py -v`
Expected: all pass (hashes + 3 lock tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/resume.py tests/test_kb_offline_resume.py
git commit -m "feat(kb-offline): per-library lock with monotonic fencing token + stale reclaim (#211)"
```

---

## Task 6: Run lifecycle + latest-compatible selection (`resume.py` part 3)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/resume.py`
- Test: `tests/test_kb_offline_resume.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_resume.py`:

```python
from sdlc_knowledge_base_scripts.resume import RunRegistry


def test_select_resumable_latest_compatible(tmp_path: Path):
    reg = RunRegistry(tmp_path)
    fp = {"operation": "ingest", "config": config_hash({"backend": "anthropic"})}
    r1 = reg.start_run("2026-06-06T00:00:00Z", fp)
    reg.set_state(r1, "failed")
    r2 = reg.start_run("2026-06-06T01:00:00Z", fp)
    reg.set_state(r2, "failed")
    # latest compatible failed run is r2
    assert reg.select_resumable(fp) == r2


def test_select_resumable_rejects_incompatible_config(tmp_path: Path):
    reg = RunRegistry(tmp_path)
    r1 = reg.start_run("2026-06-06T00:00:00Z",
                       {"operation": "ingest", "config": config_hash({"backend": "anthropic"})})
    reg.set_state(r1, "failed")
    # different config hash => not resumable
    other = {"operation": "ingest", "config": config_hash({"backend": "ollama"})}
    assert reg.select_resumable(other) is None


def test_completed_run_not_resumable(tmp_path: Path):
    reg = RunRegistry(tmp_path)
    fp = {"operation": "ingest", "config": "c"}
    r1 = reg.start_run("2026-06-06T00:00:00Z", fp)
    reg.set_state(r1, "completed")
    assert reg.select_resumable(fp) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_resume.py -k "resumable or completed_run" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `RunRegistry`**

Append to `resume.py`:

```python
_RUNS_NAME = ".kb-offline/runs.json"

RESUMABLE_STATES = {"running", "failed"}


class RunRegistry:
    """Manifest-backed registry of runs and their lifecycle states. Run IDs are
    derived deterministically from a caller-supplied timestamp + fingerprint (no
    Date.now/random at import or in pure logic — the caller passes the timestamp)."""

    def __init__(self, library_path):
        self.library_path = Path(library_path)

    def _path(self) -> Path:
        _kb_dir(self.library_path)
        return self.library_path / _RUNS_NAME

    def _load(self) -> dict:
        p = self._path()
        if not p.exists():
            return {"runs": {}}
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            return {"runs": {}}

    def _save(self, data: dict) -> None:
        from .durability import atomic_write_text
        atomic_write_text(self._path(), json.dumps(data, indent=2))

    def start_run(self, timestamp: str, fingerprint: dict) -> str:
        data = self._load()
        run_id = content_hash(timestamp + json.dumps(fingerprint, sort_keys=True))[:16]
        data["runs"][run_id] = {
            "run_id": run_id, "started_at": timestamp, "state": "running",
            "fingerprint": fingerprint, "seq": len(data["runs"]),
        }
        self._save(data)
        return run_id

    def set_state(self, run_id: str, state: str) -> None:
        data = self._load()
        data["runs"][run_id]["state"] = state
        self._save(data)

    def select_resumable(self, fingerprint: dict) -> str | None:
        data = self._load()
        candidates = [
            r for r in data["runs"].values()
            if r["state"] in RESUMABLE_STATES and r["fingerprint"] == fingerprint
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r["seq"])["run_id"]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_resume.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/resume.py tests/test_kb_offline_resume.py
git commit -m "feat(kb-offline): run lifecycle + latest-compatible resume selection (#211)"
```

---

## Task 7: Mutation validator (`mutation.py` part 1)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/mutation.py`
- Test: `tests/test_kb_offline_mutation.py`

The validator is a **safety floor** (spec: 100% rejection of invalid mutations). It returns a list of error strings; empty = valid.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_mutation.py`:

```python
"""Tests for sdlc_knowledge_base_scripts.mutation."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.contracts import MutationAction, MutationProposal
from sdlc_knowledge_base_scripts.mutation import validate_proposal


def _proposal(**kw):
    base = dict(target_file="topic.md", action=MutationAction.create,
                frontmatter={"layer": "domain", "confidence": "medium"},
                body="# Topic\n", citations=["DORA 2024"], cross_refs=[])
    base.update(kw)
    return MutationProposal(**base)


def test_valid_create_passes(tmp_path: Path):
    assert validate_proposal(_proposal(), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"}) == []


def test_path_escape_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(target_file="../evil.md"), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"})
    assert any("path" in e.lower() for e in errs)


def test_missing_frontmatter_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(frontmatter={"layer": "domain"}),  # no confidence
                             library_path=tmp_path, allowed_layers=["domain"],
                             known_citations={"DORA 2024"})
    assert any("confidence" in e.lower() for e in errs)


def test_invalid_layer_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(frontmatter={"layer": "bogus", "confidence": "medium"}),
                             library_path=tmp_path, allowed_layers=["domain"],
                             known_citations={"DORA 2024"})
    assert any("layer" in e.lower() for e in errs)


def test_dangling_citation_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(citations=["Ghost 2099"]), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"})
    assert any("citation" in e.lower() for e in errs)


def test_create_with_expected_hash_rejected(tmp_path: Path):
    # create must NOT carry expected_hash (that's an extend concept)
    errs = validate_proposal(_proposal(expected_hash="deadbeef"), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"})
    assert any("expected_hash" in e.lower() for e in errs)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_mutation.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `validate_proposal`**

Create `plugins/sdlc-knowledge-base/scripts/mutation.py`:

```python
"""Deterministic mutation validator, operation journal, durable committer, and
recovery for kb-offline (#211, M0). Models propose; this module validates and writes.
The validator is a safety floor — invalid proposals are rejected 100% of the time."""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import MutationAction, MutationProposal

_REQUIRED_FRONTMATTER = ("layer", "confidence")


def validate_proposal(
    proposal: MutationProposal,
    library_path,
    allowed_layers: list[str],
    known_citations: set[str],
) -> list[str]:
    """Return a list of error strings; empty means valid."""
    errors: list[str] = []
    library_path = Path(library_path).resolve()

    # 1. Path containment + shape
    if proposal.target_file != Path(proposal.target_file).name or proposal.target_file.startswith("."):
        errors.append(f"path: target_file must be a bare library page name, got {proposal.target_file!r}")
    else:
        resolved = (library_path / proposal.target_file).resolve()
        if library_path not in resolved.parents:
            errors.append(f"path: target escapes the library: {proposal.target_file!r}")

    # 2. Required frontmatter
    for key in _REQUIRED_FRONTMATTER:
        if key not in proposal.frontmatter:
            errors.append(f"frontmatter: required key '{key}' missing")

    # 3. Layer validity
    layer = proposal.frontmatter.get("layer")
    if layer is not None and layer not in allowed_layers:
        errors.append(f"layer: '{layer}' not in allowed set {allowed_layers}")

    # 4. Citation existence
    for c in proposal.citations:
        if c not in known_citations:
            errors.append(f"citation: '{c}' does not resolve to a known source")

    # 5. CAS shape: create must not carry expected_hash; extend must.
    if proposal.action == MutationAction.create and proposal.expected_hash is not None:
        errors.append("expected_hash: must be None for a create proposal")
    if proposal.action == MutationAction.extend and proposal.expected_hash is None:
        errors.append("expected_hash: required for an extend proposal (compare-and-swap)")

    return errors
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_mutation.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/mutation.py tests/test_kb_offline_mutation.py
git commit -m "feat(kb-offline): deterministic mutation validator (safety floor) (#211)"
```

---

## Task 8: Operation journal + durable commit with fencing + CAS (`mutation.py` part 2)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/mutation.py`
- Test: `tests/test_kb_offline_mutation.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_mutation.py`:

```python
from sdlc_knowledge_base_scripts.mutation import CommitConflict, FenceError, commit_mutation
from sdlc_knowledge_base_scripts.resume import LibraryLock, content_hash


def _seed_library(tmp_path: Path) -> Path:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    return lib


def test_commit_create_writes_page_and_journals(tmp_path: Path):
    lib = _seed_library(tmp_path)
    lock = LibraryLock(lib); token = lock.acquire()
    p = MutationProposal(target_file="topic.md", action=MutationAction.create,
                         frontmatter={"layer": "domain", "confidence": "medium"}, body="# Topic\n")
    commit_mutation(p, library_path=lib, fencing_token=token, lock=lock)
    assert (lib / "topic.md").exists()
    journal = list((lib / ".kb-offline" / "journal").glob("*.json"))
    assert journal, "a journal record must be written"
    lock.release()


def test_create_no_replace_conflict(tmp_path: Path):
    lib = _seed_library(tmp_path)
    (lib / "topic.md").write_text("existing")
    lock = LibraryLock(lib); token = lock.acquire()
    p = MutationProposal(target_file="topic.md", action=MutationAction.create,
                         frontmatter={"layer": "domain", "confidence": "medium"}, body="# new\n")
    try:
        with __import__("pytest").raises(CommitConflict):
            commit_mutation(p, library_path=lib, fencing_token=token, lock=lock)
    finally:
        lock.release()


def test_extend_hash_mismatch_conflict(tmp_path: Path):
    lib = _seed_library(tmp_path)
    (lib / "topic.md").write_text("v1")
    lock = LibraryLock(lib); token = lock.acquire()
    p = MutationProposal(target_file="topic.md", action=MutationAction.extend,
                         frontmatter={"layer": "domain", "confidence": "medium"},
                         body="v1\nmore\n", expected_hash="not-the-real-hash")
    try:
        with __import__("pytest").raises(CommitConflict):
            commit_mutation(p, library_path=lib, fencing_token=token, lock=lock)
    finally:
        lock.release()


def test_stale_fencing_token_fenced_out(tmp_path: Path):
    lib = _seed_library(tmp_path)
    lock = LibraryLock(lib); old_token = lock.acquire()
    # a replacement run acquires, bumping the fence token
    lock.release()
    lock2 = LibraryLock(lib); lock2.acquire()
    p = MutationProposal(target_file="topic.md", action=MutationAction.create,
                         frontmatter={"layer": "domain", "confidence": "medium"}, body="# t\n")
    try:
        with __import__("pytest").raises(FenceError):
            commit_mutation(p, library_path=lib, fencing_token=old_token, lock=lock2)
    finally:
        lock2.release()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_mutation.py -k "commit or conflict or fenced" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement journal + commit**

Append to `mutation.py`:

```python
from .durability import atomic_write_text
from .resume import content_hash


class CommitConflict(RuntimeError):
    """CAS failed: target changed or already exists since validation."""


class FenceError(RuntimeError):
    """The caller's fencing token is no longer current — it was fenced out."""


def _journal_dir(library_path: Path) -> Path:
    d = Path(library_path) / ".kb-offline" / "journal"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_journal(library_path: Path, run_step: str, record: dict) -> None:
    atomic_write_text(_journal_dir(library_path) / f"{run_step}.json",
                      json.dumps(record, indent=2))


def _render_page(proposal: MutationProposal) -> str:
    fm_lines = "\n".join(f"{k}: {v}" for k, v in proposal.frontmatter.items())
    return f"---\n{fm_lines}\n---\n{proposal.body}"


def commit_mutation(proposal: MutationProposal, library_path, fencing_token: int,
                    lock, run_step: str = "step") -> Path:
    """Durably commit one validated proposal. Order: journal-intent (fsync) -> fence
    check -> CAS -> durable page write -> journal-commit (fsync). Replay-safe."""
    library_path = Path(library_path)
    target = library_path / proposal.target_file

    # write-ahead: record intent durably BEFORE mutating
    _write_journal(library_path, run_step,
                   {"stage": "staged", "target": proposal.target_file,
                    "action": proposal.action.value, "token": fencing_token})

    # fence: a stale (reclaimed-from) caller is rejected here even if it "held" the lock
    if fencing_token != lock.current_token():
        _write_journal(library_path, run_step, {"stage": "fenced", "token": fencing_token})
        raise FenceError(f"token {fencing_token} != current {lock.current_token()}")

    # compare-and-swap
    if proposal.action == MutationAction.create and target.exists():
        _write_journal(library_path, run_step, {"stage": "conflict", "reason": "exists"})
        raise CommitConflict(f"create: {proposal.target_file} already exists")
    if proposal.action == MutationAction.extend:
        actual = content_hash(target.read_text()) if target.exists() else None
        if actual != proposal.expected_hash:
            _write_journal(library_path, run_step, {"stage": "conflict", "reason": "hash"})
            raise CommitConflict(f"extend: {proposal.target_file} changed since validation")

    atomic_write_text(target, _render_page(proposal))
    _write_journal(library_path, run_step,
                   {"stage": "committed", "target": proposal.target_file, "token": fencing_token})
    return target
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_mutation.py -v`
Expected: all pass (validator + commit/conflict/fence).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/mutation.py tests/test_kb_offline_mutation.py
git commit -m "feat(kb-offline): journaled durable commit with fencing + create/extend CAS (#211)"
```

---

## Task 9: Recovery (`mutation.py` part 3)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/mutation.py`
- Test: `tests/test_kb_offline_mutation.py`

Recovery replays the journal: `committed`-but-not-`indexed` steps trigger a deterministic shelf-index rebuild; `conflict`/`fenced`/`staged`-only steps are surfaced.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_mutation.py`:

```python
from sdlc_knowledge_base_scripts.mutation import recover


def test_recover_reports_committed_and_conflicts(tmp_path: Path):
    lib = _seed_library(tmp_path)
    jdir = lib / ".kb-offline" / "journal"
    jdir.mkdir(parents=True)
    (jdir / "s1.json").write_text('{"stage": "committed", "target": "a.md"}')
    (jdir / "s2.json").write_text('{"stage": "conflict", "reason": "hash"}')
    report = recover(lib)
    assert "a.md" in report["needs_reindex"]
    assert report["conflicts"] == 1
    assert report["reindexed"] is True          # build_shelf_index ran (idempotent)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_mutation.py -k recover -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `recover`**

Append to `mutation.py`:

```python
def recover(library_path) -> dict:
    """Replay the journal. committed-not-indexed -> deterministic shelf-index rebuild
    (build_shelf_index is idempotent + hash-based, so reconciliation is deterministic).
    Returns a report; surfaces conflicts/fenced for the run summary."""
    from .build_shelf_index import main as rebuild_index

    library_path = Path(library_path)
    jdir = library_path / ".kb-offline" / "journal"
    needs_reindex: list[str] = []
    conflicts = 0
    if jdir.exists():
        for rec_path in sorted(jdir.glob("*.json")):
            try:
                rec = json.loads(rec_path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if rec.get("stage") == "committed" and rec.get("target"):
                needs_reindex.append(rec["target"])
            elif rec.get("stage") in ("conflict", "fenced"):
                conflicts += 1

    reindexed = False
    if needs_reindex:
        rebuild_index([str(library_path)])
        reindexed = True
    return {"needs_reindex": needs_reindex, "conflicts": conflicts, "reindexed": reindexed}
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_mutation.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/mutation.py tests/test_kb_offline_mutation.py
git commit -m "feat(kb-offline): journal replay recovery + deterministic reindex (#211)"
```

---

## Task 10: Backend seam — base protocol + FakeBackend

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/backends/__init__.py`, `backends/base.py`, `backends/fake_backend.py`
- Test: `tests/test_kb_offline_backends.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_backends.py`:

```python
"""Tests for the kb-offline backend seam."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.backends.base import Backend
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_fake_backend_is_a_backend():
    fb = FakeBackend(responses={"hello": "world"})
    assert isinstance(fb, Backend)


def test_fake_generate_returns_scripted_response():
    fb = FakeBackend(responses={"q1": '{"ok": true}'})
    assert fb.generate("q1") == '{"ok": true}'


def test_fake_generate_records_calls():
    fb = FakeBackend(responses={"q1": "a"})
    fb.generate("q1", schema={"type": "object"})
    assert fb.calls[0]["prompt"] == "q1"
    assert fb.calls[0]["schema"] == {"type": "object"}


def test_fake_embed_returns_fixed_dim_vectors():
    fb = FakeBackend()
    vecs = fb.embed(["a", "b"])
    assert len(vecs) == 2 and all(len(v) == 8 for v in vecs)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_backends.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement base + fake**

Create `plugins/sdlc-knowledge-base/scripts/backends/__init__.py`:

```python
"""kb-offline model backends (issue #211)."""
```

Create `plugins/sdlc-knowledge-base/scripts/backends/base.py`:

```python
"""The backend seam: model calls ONLY. No validation, no retries, no file I/O —
those belong to the pipeline. (#211, M0)"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        """Return model text. If schema is given, the backend constrains output to it."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...
```

Create `plugins/sdlc-knowledge-base/scripts/backends/fake_backend.py`:

```python
"""Deterministic backend for tests — no model calls. (#211, M0)"""
from __future__ import annotations


class FakeBackend:
    def __init__(self, responses: dict[str, str] | None = None):
        self.responses = responses or {}
        self.calls: list[dict] = []

    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        self.calls.append({"prompt": prompt, "schema": schema})
        if prompt not in self.responses:
            raise KeyError(f"FakeBackend has no scripted response for prompt: {prompt!r}")
        return self.responses[prompt]

    def embed(self, texts: list[str]) -> list[list[float]]:
        # deterministic 8-dim vectors derived from text length + char sum
        out = []
        for t in texts:
            base = float(len(t))
            out.append([base + i + float(sum(ord(c) for c in t) % 7) for i in range(8)])
        return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_backends.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/backends/ tests/test_kb_offline_backends.py
git commit -m "feat(kb-offline): backend seam (generate/embed) + FakeBackend (#211)"
```

---

## Task 11: AnthropicBackend (guarded)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/backends/anthropic_backend.py`
- Test: `tests/test_kb_offline_backends.py`

- [ ] **Step 1: Write the failing test** (no network — inject a fake client)

Append to `tests/test_kb_offline_backends.py`:

```python
def test_anthropic_backend_generate_with_injected_client():
    from sdlc_knowledge_base_scripts.backends.anthropic_backend import AnthropicBackend

    class _Msg:
        def __init__(self, text): self.content = [type("B", (), {"text": text})()]

    class _Client:
        def __init__(self): self.messages = self
        def create(self, **kw):  # mimics anthropic Messages.create
            return _Msg('{"answer": "42"}')

    be = AnthropicBackend(model="claude-sonnet-4-6", client=_Client())
    assert be.generate("q", schema={"type": "object"}) == '{"answer": "42"}'
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_backends.py -k anthropic -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement (import of `anthropic` deferred so base distribution still imports)**

Create `plugins/sdlc-knowledge-base/scripts/backends/anthropic_backend.py`:

```python
"""Direct Anthropic API backend (model calls only). The `anthropic` SDK import is
deferred to construction so importing this module never requires the dependency. (#211)"""
from __future__ import annotations


class AnthropicBackend:
    def __init__(self, model: str = "claude-sonnet-4-6", *, client=None, max_tokens: int = 4096):
        self.model = model
        self.max_tokens = max_tokens
        if client is not None:
            self._client = client
        else:
            import anthropic  # deferred; only needed for real calls
            self._client = anthropic.Anthropic()

    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        system = ""
        if schema is not None:
            system = ("Respond with a single JSON object that conforms exactly to this "
                      f"JSON Schema. Output JSON only, no prose:\n{schema}")
        msg = self._client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            system=system or None, messages=[{"role": "user", "content": prompt}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content)

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic backend does not provide embeddings; use Ollama (M3).")
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_backends.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/backends/anthropic_backend.py tests/test_kb_offline_backends.py
git commit -m "feat(kb-offline): AnthropicBackend (deferred SDK import, injectable client) (#211)"
```

---

## Task 12: Canonical prompts (`prompts.py`)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/prompts.py`
- Test: `tests/test_kb_offline_pipeline.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_pipeline.py`:

```python
"""Tests for kb-offline prompts + pipeline."""
from __future__ import annotations

from sdlc_knowledge_base_scripts import prompts


def test_extract_fragment_is_nonempty_constant():
    assert isinstance(prompts.EXTRACT_FRAGMENT, str)
    assert "JSON" in prompts.EXTRACT_FRAGMENT
    assert "targets" in prompts.EXTRACT_FRAGMENT


def test_reduce_fragment_states_constraints():
    assert "exactly one file" in prompts.REDUCE_FRAGMENT.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_pipeline.py -k fragment -v`
Expected: FAIL (AttributeError/ModuleNotFoundError).

- [ ] **Step 3: Implement `prompts.py`**

Create `plugins/sdlc-knowledge-base/scripts/prompts.py`:

```python
"""Canonical operation prompt fragments (issue #211). Single source of truth shared by
the CLI pipeline and mirrored into the agent .md managed blocks; CI's
check-prompt-parity.py asserts they do not drift."""
from __future__ import annotations

EXTRACT_FRAGMENT = (
    "Read the source and the shelf-index (read-only). Emit ONLY a JSON object with "
    "fields: source, findings[], statistics[], citations[], confidence "
    "(high|medium|low), and targets[] mapping findings to existing files or proposed "
    "new topics. Summarise findings; never transcribe."
)

SELECT_FRAGMENT = (
    "Read the shelf-index and identify the 2-4 most relevant library pages for the "
    "question. Return only their page ids."
)

SYNTHESIZE_FRAGMENT = (
    "Answer using only the supplied pages. Return claims, each with the pages it cites "
    "and the exact supporting spans. Do not assign entailment status; the verifier does."
)

REDUCE_FRAGMENT = (
    "Synthesise all routed extracts into exactly one file. Propose a mutation (target, "
    "frontmatter, body, citations, cross-refs); do not write files yourself. Apply "
    "extend-vs-create, contradiction flagging, citation discipline, confidence frontmatter."
)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_pipeline.py -k fragment -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/prompts.py tests/test_kb_offline_pipeline.py
git commit -m "feat(kb-offline): canonical prompt fragments (#211)"
```

---

## Task 13: Pipeline `extract` operation (validate→repair→fail ladder)

**Files:**
- Create/Modify: `plugins/sdlc-knowledge-base/scripts/pipeline.py`
- Test: `tests/test_kb_offline_pipeline.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_pipeline.py`:

```python
import json

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.pipeline import extract


def _shelf(tmp_path):
    s = tmp_path / "_shelf-index.md"
    s.write_text("<!-- format_version: 1 -->\n# Shelf\n- topic.md\n")
    return s


def test_extract_parses_valid_json(tmp_path):
    src = tmp_path / "a.md"; src.write_text("source text")
    payload = json.dumps({"source": "a.md", "findings": ["f"], "confidence": "medium",
                          "targets": [{"file": "topic.md", "finding_idx": [0]}]})
    be = FakeBackend(responses={"__extract__": payload})
    # the pipeline renders a prompt; we make FakeBackend answer any prompt with payload
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be)
    assert result.findings == ["f"]
    assert result.targets[0].file == "topic.md"


def test_extract_repairs_then_succeeds(tmp_path):
    src = tmp_path / "a.md"; src.write_text("source text")
    good = json.dumps({"source": "a.md", "findings": ["f"], "confidence": "low", "targets": []})
    seq = ["not json at all", good]
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: seq.pop(0)  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be, max_repairs=1)
    assert result.confidence.value == "low"


def test_extract_fails_after_repair_budget(tmp_path):
    src = tmp_path / "a.md"; src.write_text("x")
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: "still not json"  # type: ignore
    import pytest
    with pytest.raises(ValueError):
        extract(str(src), _shelf(tmp_path), backend=be, max_repairs=1)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_pipeline.py -k extract -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `pipeline.extract`**

Create `plugins/sdlc-knowledge-base/scripts/pipeline.py`:

```python
"""kb-offline pipeline operations (#211, M0). Each operation calls the backend for the
model step, then OWNS parsing + the validate->repair->fail ladder + (for writers) the
mutation proposal. Backends never validate or write."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from . import prompts
from .contracts import ExtractJSON


def _extract_schema() -> dict:
    return ExtractJSON.model_json_schema()


def extract(source_path, shelf_index_path, *, backend, max_repairs: int = 1) -> ExtractJSON:
    """Map operation: read one source, return a validated ExtractJSON. Grammar-constrained
    when the backend supports it; otherwise parse + bounded repair + fail."""
    source_text = Path(source_path).read_text(encoding="utf-8")
    base_prompt = (
        f"{prompts.EXTRACT_FRAGMENT}\n\nSource: {source_path}\n"
        f"Shelf-index: {shelf_index_path}\n\n<source>\n{source_text}\n</source>"
    )
    schema = _extract_schema()
    prompt = base_prompt
    last_error = ""
    for attempt in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            return ExtractJSON.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = (f"{base_prompt}\n\nYour previous output was invalid: {last_error}\n"
                      "Return ONLY a valid JSON object conforming to the schema.")
    raise ValueError(f"extract failed after {max_repairs} repair(s): {last_error}")
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_pipeline.py -k extract -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_pipeline.py
git commit -m "feat(kb-offline): pipeline extract with validate-repair-fail ladder (#211)"
```

---

## Task 14: Pipeline `reduce` → MutationProposal (wires validator + committer)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/pipeline.py`
- Test: `tests/test_kb_offline_pipeline.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_pipeline.py`:

```python
from sdlc_knowledge_base_scripts.contracts import MutationAction
from sdlc_knowledge_base_scripts.pipeline import reduce_to_proposal


def test_reduce_returns_validatable_create_proposal(tmp_path):
    proposal_json = json.dumps({
        "target_file": "fresh.md", "action": "create",
        "frontmatter": {"layer": "domain", "confidence": "medium"},
        "body": "# Fresh\n- finding", "citations": ["Src 2026"], "cross_refs": [],
        "expected_hash": None,
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: proposal_json  # type: ignore
    proposal = reduce_to_proposal(
        target_file="fresh.md", is_new=True,
        extracts=[{"source": "a.md", "findings": ["finding"]}],
        existing_content=None, backend=be,
    )
    assert proposal.action == MutationAction.create
    assert proposal.target_file == "fresh.md"
    assert proposal.expected_hash is None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_pipeline.py -k reduce -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `reduce_to_proposal`**

Append to `pipeline.py`:

```python
from .contracts import MutationProposal


def _proposal_schema() -> dict:
    return MutationProposal.model_json_schema()


def reduce_to_proposal(*, target_file, is_new, extracts, existing_content, backend,
                       max_repairs: int = 1) -> MutationProposal:
    """Reduce operation: synthesise routed extracts into a typed MutationProposal
    (NOT a final file). The caller validates + commits it deterministically."""
    action = "create" if is_new else "extend"
    base_prompt = (
        f"{prompts.REDUCE_FRAGMENT}\n\nTarget file: {target_file} ({action})\n"
        f"Existing content:\n{existing_content or '(none — new file)'}\n\n"
        f"Routed extracts (JSON):\n{json.dumps(extracts, indent=2)}"
    )
    schema = _proposal_schema()
    prompt = base_prompt
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            return MutationProposal.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base_prompt}\n\nPrevious output invalid: {last_error}\nReturn valid JSON only."
    raise ValueError(f"reduce failed after {max_repairs} repair(s): {last_error}")
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_pipeline.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_pipeline.py
git commit -m "feat(kb-offline): pipeline reduce -> typed MutationProposal (#211)"
```

---

## Task 15: Minimal `kb-offline` CLI (init + ingest, Anthropic/Fake, --resume)

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`
- Test: `tests/test_kb_offline_cli.py`

The CLI must make resume/journal/fencing exercisable. `ingest` is the proving ground: discover sources → extract → route (reuse `route_extracts`) → reduce → validate → commit → recover/reindex, under a lock+fencing token, with run lifecycle. Backend defaults to `anthropic`; tests use `--backend fake` via an injected registry.

- [ ] **Step 1: Write the failing test** (CLI driven in-process with FakeBackend)

Create `tests/test_kb_offline_cli.py`:

```python
"""Tests for the kb-offline CLI skeleton (in-process, FakeBackend)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts import kb_offline_cli as cli
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def _seed_lib(tmp_path):
    lib = tmp_path / "library"; lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _fake_extract_then_reduce(extract_payload, reduce_payload):
    be = FakeBackend()
    seq = {"calls": 0}
    def gen(prompt, schema=None):
        # extract prompts mention "<source>"; reduce prompts mention "Routed extracts"
        return reduce_payload if "Routed extracts" in prompt else extract_payload
    be.generate = gen  # type: ignore
    return be


def test_cli_ingest_creates_page_and_completes_run(tmp_path, monkeypatch):
    lib = _seed_lib(tmp_path)
    src = tmp_path / "s1.md"; src.write_text("source one")
    extract_payload = json.dumps({"source": str(src), "findings": ["finding one"],
                                  "confidence": "medium",
                                  "targets": [{"new_topic_slug": "topic-one", "title": "Topic One",
                                               "finding_idx": [0]}]})
    reduce_payload = json.dumps({"target_file": "topic-one.md", "action": "create",
                                 "frontmatter": {"layer": "domain", "confidence": "medium"},
                                 "body": "# Topic One\n- finding one",
                                 "citations": [], "cross_refs": [], "expected_hash": None})
    be = _fake_extract_then_reduce(extract_payload, reduce_payload)
    rc = cli.main(["ingest", str(src), "--library", str(lib), "--backend", "fake",
                   "--timestamp", "2026-06-06T00:00:00Z"],
                  backend_override=be, allowed_layers=["domain"])
    assert rc == 0
    assert (lib / "topic-one.md").exists()
    runs = json.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] == "completed" for r in runs["runs"].values())


def test_cli_resume_skips_completed_source(tmp_path):
    lib = _seed_lib(tmp_path)
    src = tmp_path / "s1.md"; src.write_text("source one")
    extract_payload = json.dumps({"source": str(src), "findings": ["f"], "confidence": "low",
                                  "targets": [{"new_topic_slug": "t", "title": "T", "finding_idx": [0]}]})
    reduce_payload = json.dumps({"target_file": "t.md", "action": "create",
                                 "frontmatter": {"layer": "domain", "confidence": "low"},
                                 "body": "# T", "citations": [], "cross_refs": [], "expected_hash": None})
    be = _fake_extract_then_reduce(extract_payload, reduce_payload)
    args = ["ingest", str(src), "--library", str(lib), "--backend", "fake",
            "--timestamp", "2026-06-06T00:00:00Z"]
    assert cli.main(args, backend_override=be, allowed_layers=["domain"]) == 0
    # second run with --resume latest: source already extracted -> no re-extract call
    be2 = _fake_extract_then_reduce("SHOULD_NOT_BE_CALLED", reduce_payload)
    rc = cli.main(args + ["--resume", "latest"], backend_override=be2, allowed_layers=["domain"])
    assert rc == 0  # completes without needing a fresh extract
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_cli.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement the CLI skeleton**

Create `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`:

```python
"""Minimal `kb-offline` CLI (issue #211, M0). Proves the foundation end-to-end on the
Anthropic/Fake path: ingest = discover -> extract -> route -> reduce -> validate ->
commit (fencing+CAS) -> recover/reindex, under a per-library lock with run lifecycle.
Ollama/graphs/bulk/query-synthesis arrive in M1+."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import kb_ingest_bulk as kbb
from .mutation import CommitConflict, FenceError, commit_mutation, recover, validate_proposal
from .pipeline import extract, reduce_to_proposal
from .resume import LibraryLock, RunRegistry, config_hash


def _make_backend(name: str, override):
    if override is not None:
        return override
    if name == "anthropic":
        from .backends.anthropic_backend import AnthropicBackend
        return AnthropicBackend()
    raise SystemExit(f"backend '{name}' is not available in M0 (use anthropic or fake)")


def _cmd_init(args) -> int:
    lib = Path(args.library)
    (lib / ".kb-offline").mkdir(parents=True, exist_ok=True)
    (lib / "raw").mkdir(parents=True, exist_ok=True)
    shelf = lib / "_shelf-index.md"
    if not shelf.exists():
        shelf.write_text("<!-- format_version: 1 -->\n# Shelf Index\n", encoding="utf-8")
    log = lib / "log.md"
    if not log.exists():
        log.write_text("# Knowledge Base Log\n", encoding="utf-8")
    print(f"initialised library at {lib}")
    return 0


def _cmd_ingest(args, backend_override, allowed_layers) -> int:
    lib = Path(args.library)
    shelf = lib / "_shelf-index.md"
    backend = _make_backend(args.backend, backend_override)
    reg = RunRegistry(lib)
    fingerprint = {"operation": "ingest",
                   "config": config_hash({"backend": args.backend})}

    # resume selection
    if args.resume == "latest":
        run_id = reg.select_resumable(fingerprint) or reg.start_run(args.timestamp, fingerprint)
    elif args.resume:
        run_id = args.resume
    else:
        run_id = reg.start_run(args.timestamp, fingerprint)

    extracts_dir = lib / ".kb-offline" / "extracts"
    lock = LibraryLock(lib)
    token = lock.acquire()
    try:
        sources = kbb.discover_sources([args.source])
        # MAP (resume: skip sources whose extract already exists)
        for src in sources:
            slug = kbb.slug_for_source(src)
            ep = kbb.extract_path(extracts_dir, slug)
            if ep.exists():
                continue
            result = extract(str(src), shelf, backend=backend)
            kbb.persist_extract(extracts_dir, slug, json.loads(result.model_dump_json()))

        # ROUTE (reuse deterministic core)
        loaded = [json.loads(p.read_text()) for p in sorted(extracts_dir.glob("*.json"))]
        existing = {p.name for p in lib.glob("*.md")
                    if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        route = kbb.route_extracts(loaded, existing_files=existing, size_threshold=200_000)

        # REDUCE -> validate -> commit
        known_citations = set()
        for ex in loaded:
            known_citations.update(ex.get("citations", []))
        committed = 0
        for tfile, slot in route.targets.items():
            existing_content = (lib / tfile).read_text() if (lib / tfile).exists() else None
            proposal = reduce_to_proposal(
                target_file=tfile, is_new=slot["is_new"], extracts=slot["extracts"],
                existing_content=existing_content, backend=backend)
            errors = validate_proposal(proposal, library_path=lib,
                                       allowed_layers=allowed_layers, known_citations=known_citations)
            if errors:
                print(f"REJECTED {tfile}: {errors}", file=sys.stderr)
                continue
            try:
                commit_mutation(proposal, library_path=lib, fencing_token=token, lock=lock,
                                run_step=f"{run_id}-{tfile}")
                committed += 1
            except (CommitConflict, FenceError) as exc:
                print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)

        # FINALIZE (recovery does the deterministic reindex)
        report = recover(lib)
        reg.set_state(run_id, "completed")
        print(f"ingest complete: run={run_id} committed={committed} reindexed={report['reindexed']}")
        return 0
    except Exception:
        reg.set_state(run_id, "failed")
        raise
    finally:
        lock.release()


def main(argv=None, *, backend_override=None, allowed_layers=None) -> int:
    allowed_layers = allowed_layers or ["methodology", "evidence", "domain", "development"]
    parser = argparse.ArgumentParser(prog="kb-offline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init"); p_init.add_argument("--library", default="library")

    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("source")
    p_ing.add_argument("--library", default="library")
    p_ing.add_argument("--backend", default="anthropic")
    p_ing.add_argument("--resume", default=None)
    p_ing.add_argument("--timestamp", required=True,
                       help="ISO timestamp for deterministic run id (no wall-clock in pure logic)")

    args = parser.parse_args(argv)
    if args.cmd == "init":
        return _cmd_init(args)
    if args.cmd == "ingest":
        return _cmd_ingest(args, backend_override, allowed_layers)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_cli.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "feat(kb-offline): minimal CLI (init+ingest) exercising resume/journal/fencing (#211)"
```

---

## Task 16: Packaging — pydantic dep + console script

**Files:**
- Modify: `plugins/sdlc-knowledge-base/pyproject.toml`
- Test: `tests/test_kb_offline_cli.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_cli.py`:

```python
def test_console_entry_point_importable():
    # the entry point target must resolve
    from sdlc_knowledge_base_scripts.kb_offline_cli import main as entry
    assert callable(entry)


def test_pyproject_declares_pydantic_and_script():
    import tomllib
    from pathlib import Path
    pp = Path(__file__).resolve().parents[1] / "plugins/sdlc-knowledge-base/pyproject.toml"
    data = tomllib.loads(pp.read_text())
    assert any("pydantic" in d for d in data["project"]["dependencies"])
    assert "kb-offline" in data["project"]["scripts"]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_cli.py -k "console or pyproject" -v`
Expected: FAIL (KeyError: 'scripts' / pydantic absent).

- [ ] **Step 3: Edit `pyproject.toml`**

In `plugins/sdlc-knowledge-base/pyproject.toml`, change the `dependencies` list and add a `[project.scripts]` table:

```toml
dependencies = [
  "pyyaml",
  "pydantic>=2",
]

[project.scripts]
kb-offline = "sdlc_knowledge_base_scripts.kb_offline_cli:main"
```

- [ ] **Step 4: Reinstall editable so the entry point + dep register, then verify**

Run:
```bash
pip install -e plugins/sdlc-knowledge-base/ >/dev/null 2>&1
python -m pytest tests/test_kb_offline_cli.py -k "console or pyproject" -v
```
Expected: 2 passed. (If `tomllib` is unavailable on 3.9–3.10, the test imports `tomli` instead — adjust the import to `import tomllib` on 3.11+ / `import tomli as tomllib` otherwise; the CI matrix runs 3.9/3.11/3.12.)

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/pyproject.toml tests/test_kb_offline_cli.py
git commit -m "build(kb-offline): add pydantic dep + kb-offline console script (#211)"
```

---

## Task 17: Prompt-parity managed blocks + CI drift check

**Files:**
- Create: `tools/validation/check-prompt-parity.py`
- Modify: `agents/knowledge-base/agent-knowledge-updater.md` (add a managed block)
- Test: `tests/test_prompt_parity.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_prompt_parity.py`:

```python
"""The prompt-parity drift check must pass (agent managed blocks match prompts.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_prompt_parity_check_passes():
    rc = subprocess.run(
        [sys.executable, str(REPO / "tools/validation/check-prompt-parity.py")],
        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout + rc.stderr
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_prompt_parity.py -v`
Expected: FAIL (script missing → non-zero).

- [ ] **Step 3: Add a managed block to the updater agent**

In `agents/knowledge-base/agent-knowledge-updater.md`, add (in the body, after the ingest workflow heading) a managed block whose inner text is EXACTLY `prompts.REDUCE_FRAGMENT`:

```markdown
<!-- BEGIN managed:prompt-fragment REDUCE_FRAGMENT -->
Synthesise all routed extracts into exactly one file. Propose a mutation (target, frontmatter, body, citations, cross-refs); do not write files yourself. Apply extend-vs-create, contradiction flagging, citation discipline, confidence frontmatter.
<!-- END managed:prompt-fragment REDUCE_FRAGMENT -->
```

- [ ] **Step 4: Implement the drift check**

Create `tools/validation/check-prompt-parity.py`:

```python
#!/usr/bin/env python3
"""Assert each agent .md managed block byte-matches its prompts.py constant (#211).

Managed block format:
  <!-- BEGIN managed:prompt-fragment NAME -->
  ...text...
  <!-- END managed:prompt-fragment NAME -->
The inner text (stripped) must equal getattr(prompts, NAME).
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins/sdlc-knowledge-base/scripts"
AGENTS = REPO / "agents/knowledge-base"

_BLOCK = re.compile(
    r"<!-- BEGIN managed:prompt-fragment (\w+) -->\n(.*?)\n<!-- END managed:prompt-fragment \1 -->",
    re.DOTALL)


def _load_prompts():
    spec = importlib.util.spec_from_file_location("kb_prompts", SCRIPTS / "prompts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    prompts = _load_prompts()
    failures = []
    for md in sorted(AGENTS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for name, block in _BLOCK.findall(text):
            expected = getattr(prompts, name, None)
            if expected is None:
                failures.append(f"{md.name}: managed block {name} has no prompts.py constant")
            elif block.strip() != expected.strip():
                failures.append(f"{md.name}: managed block {name} drifted from prompts.{name}")
    if failures:
        print("Prompt parity FAILED:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("Prompt parity OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_prompt_parity.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/validation/check-prompt-parity.py agents/knowledge-base/agent-knowledge-updater.md tests/test_prompt_parity.py
git commit -m "feat(kb-offline): prompt-parity managed blocks + CI drift check (#211)"
```

---

## Task 18: Eval harness skeleton + labelled fixture + ratified thresholds

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/eval/__init__.py`, `eval/harness.py`, `eval/thresholds.py`
- Create: `plugins/sdlc-knowledge-base/scripts/eval/fixture/` (a few labelled pages + questions)
- Test: `tests/test_kb_offline_eval.py`

M0 ships the *skeleton* (metric functions + threshold constants + a tiny fixture); M1 fills the full release suite. Thresholds are the spec's ratified numbers.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_eval.py`:

```python
"""Tests for the kb-offline eval harness skeleton."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval import thresholds
from sdlc_knowledge_base_scripts.eval.harness import (
    abstention_scores, fact_recall, routing_scores,
)


def test_safety_floors_are_one():
    assert thresholds.INVALID_MUTATION_REJECTION == 1.0
    assert thresholds.CITATION_VALIDITY == 1.0
    assert thresholds.POST_REPAIR_JSON_VALIDITY == 1.0


def test_model_quality_thresholds_match_ratified_values():
    assert thresholds.CITATION_ENTAILMENT == 0.98
    assert thresholds.FACT_RECALL == 0.85
    assert thresholds.ROUTING_RECALL == 0.90
    assert thresholds.ROUTING_PRECISION == 0.80
    assert thresholds.ABSTENTION_PRECISION == 0.95
    assert thresholds.ABSTENTION_RECALL == 0.90
    assert thresholds.FIRST_PASS_JSON_VALIDITY == 0.95


def test_fact_recall_macro_average():
    # 2 questions: q1 finds 1/2 expected, q2 finds 2/2 -> macro avg = (0.5 + 1.0)/2
    got = fact_recall([{"expected": ["a", "b"], "found": ["a"]},
                       {"expected": ["c", "d"], "found": ["c", "d"]}])
    assert abs(got - 0.75) < 1e-9


def test_routing_scores_recall_precision():
    r, p = routing_scores([{"expected": {"x.md", "y.md"}, "predicted": {"x.md", "z.md"}}])
    assert abs(r - 0.5) < 1e-9 and abs(p - 0.5) < 1e-9


def test_abstention_scores():
    # rows: (should_abstain, did_abstain)
    prec, rec = abstention_scores([(True, True), (False, True), (True, False)])
    # predicted-abstain = 2 (one correct) -> precision 0.5; actual-abstain = 2 (one caught) -> recall 0.5
    assert abs(prec - 0.5) < 1e-9 and abs(rec - 0.5) < 1e-9
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_kb_offline_eval.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement thresholds + metrics**

Create `plugins/sdlc-knowledge-base/scripts/eval/__init__.py`:

```python
"""kb-offline evaluation harness (issue #211)."""
```

Create `plugins/sdlc-knowledge-base/scripts/eval/thresholds.py`:

```python
"""Ratified eval thresholds (issue #211, spec §Eval). Safety floors are deterministic
guarantees (= 1.0). Model-quality numbers are the M1 gate, ratified at M0 exit."""
from __future__ import annotations

# Safety floors (deterministic-code guarantees)
INVALID_MUTATION_REJECTION = 1.0
CITATION_VALIDITY = 1.0
FEDERATION_ATTRIBUTION = 1.0
POST_REPAIR_JSON_VALIDITY = 1.0

# Model-quality thresholds (release-suite gate before Ollama default)
CITATION_ENTAILMENT = 0.98          # plus zero unsupported high-impact claims
FACT_RECALL = 0.85                  # macro-averaged
ROUTING_RECALL = 0.90
ROUTING_PRECISION = 0.80
ABSTENTION_PRECISION = 0.95
ABSTENTION_RECALL = 0.90
FIRST_PASS_JSON_VALIDITY = 0.95
```

Create `plugins/sdlc-knowledge-base/scripts/eval/harness.py`:

```python
"""Eval metric functions (issue #211, M0 skeleton). M1 wires these to a frozen release
suite (75-100 questions, >=20 no-evidence, pinned config, 3 runs)."""
from __future__ import annotations


def fact_recall(rows: list[dict]) -> float:
    """Macro-averaged recall of expected facts across questions."""
    if not rows:
        return 0.0
    per_q = []
    for r in rows:
        expected = set(r["expected"])
        found = set(r["found"])
        per_q.append(len(expected & found) / len(expected) if expected else 1.0)
    return sum(per_q) / len(per_q)


def routing_scores(rows: list[dict]) -> tuple[float, float]:
    """Micro recall + precision of routing targets across rows."""
    tp = fn = fp = 0
    for r in rows:
        expected, predicted = set(r["expected"]), set(r["predicted"])
        tp += len(expected & predicted)
        fn += len(expected - predicted)
        fp += len(predicted - expected)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    return recall, precision


def abstention_scores(rows: list[tuple[bool, bool]]) -> tuple[float, float]:
    """rows = (should_abstain, did_abstain). Returns (precision, recall) of abstention."""
    tp = sum(1 for s, d in rows if s and d)
    predicted = sum(1 for _, d in rows if d)
    actual = sum(1 for s, _ in rows if s)
    precision = tp / predicted if predicted else 1.0
    recall = tp / actual if actual else 1.0
    return precision, recall
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_kb_offline_eval.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/eval/ tests/test_kb_offline_eval.py
git commit -m "feat(kb-offline): eval harness skeleton + ratified thresholds (#211)"
```

---

## Task 19: M0 integration test + full-suite + validation gate

**Files:**
- Test: `tests/test_kb_offline_integration.py`

- [ ] **Step 1: Write the end-to-end integration test (FakeBackend, full ingest + recovery + fence)**

Create `tests/test_kb_offline_integration.py`:

```python
"""M0 end-to-end: CLI ingest via FakeBackend proves the foundation composes —
extract -> route -> reduce -> validate -> commit (journal+fence+CAS) -> recover/reindex."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts import kb_offline_cli as cli
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_m0_end_to_end(tmp_path):
    lib = tmp_path / "library"; lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    src = tmp_path / "s1.md"; src.write_text("a source about widgets")

    extract_payload = json.dumps({"source": str(src), "findings": ["widgets matter"],
                                  "confidence": "medium",
                                  "targets": [{"new_topic_slug": "widgets", "title": "Widgets",
                                               "finding_idx": [0]}]})
    reduce_payload = json.dumps({"target_file": "widgets.md", "action": "create",
                                 "frontmatter": {"layer": "domain", "confidence": "medium"},
                                 "body": "# Widgets\n- widgets matter",
                                 "citations": [], "cross_refs": [], "expected_hash": None})
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: (  # type: ignore
        reduce_payload if "Routed extracts" in prompt else extract_payload)

    rc = cli.main(["ingest", str(src), "--library", str(lib), "--backend", "fake",
                   "--timestamp", "2026-06-06T00:00:00Z"],
                  backend_override=be, allowed_layers=["domain"])
    assert rc == 0
    page = lib / "widgets.md"
    assert page.exists() and "widgets matter" in page.read_text()
    # shelf-index reconciled to include the new page
    assert "widgets.md" in (lib / "_shelf-index.md").read_text()
    # journal recorded a committed step
    journal = list((lib / ".kb-offline" / "journal").glob("*.json"))
    assert any(json.loads(p.read_text()).get("stage") == "committed" for p in journal)
```

- [ ] **Step 2: Run the integration test**

Run: `python -m pytest tests/test_kb_offline_integration.py -v`
Expected: PASS. (If it fails, a foundation unit is wrong — debug, do not weaken the test.)

- [ ] **Step 3: Run the full M0 suite + the broader kb suite (no regressions)**

Run:
```bash
python -m pytest tests/test_kb_offline_contracts.py tests/test_kb_offline_durability.py \
  tests/test_kb_offline_resume.py tests/test_kb_offline_mutation.py \
  tests/test_kb_offline_backends.py tests/test_kb_offline_pipeline.py \
  tests/test_kb_offline_cli.py tests/test_kb_offline_eval.py tests/test_prompt_parity.py \
  tests/test_kb_offline_integration.py -q
python -m pytest tests/ -k kb -q
```
Expected: all green; existing kb suite unchanged (302+ tests) plus the new M0 tests.

- [ ] **Step 4: Run repo validators**

Run:
```bash
python tools/validation/check-technical-debt.py . 2>&1 | tail -3
python tools/validation/check-feature-proposal.py --branch feature/211-kb-offline-langgraph
python -m flake8 plugins/sdlc-knowledge-base/scripts/contracts.py plugins/sdlc-knowledge-base/scripts/mutation.py plugins/sdlc-knowledge-base/scripts/resume.py plugins/sdlc-knowledge-base/scripts/pipeline.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py plugins/sdlc-knowledge-base/scripts/durability.py
```
Expected: no new technical-debt markers in the new files; feature-proposal check passes; flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add tests/test_kb_offline_integration.py
git commit -m "test(kb-offline): M0 end-to-end integration (extract->commit->recover) (#211)"
```

---

## Self-review notes

- **Spec coverage (M0 rows):** claim-structured `Answer`/`Claim` (Task 2); `MutationProposal` +
  deterministic validator (Task 7) + journal/fencing/CAS commit (Task 8) + recovery/reindex (Task 9);
  durable fsync + #208 upgrade (Task 3); resume hashes/lock-fencing/lifecycle/selection (Tasks 4–6);
  backend = generate/embed only + Fake + Anthropic (Tasks 10–11); pipeline extract/reduce ladder
  (Tasks 13–14); prompts + CI parity check (Tasks 12, 17); pydantic dep + console script + CLI proving
  resume/journal/fencing CLI-end-to-end (Tasks 15–16); eval skeleton + ratified thresholds + safety
  floors (Task 18); end-to-end + validation gate (Task 19).
- **Deferred to M1+ (correctly absent here):** OllamaBackend, LangGraph graphs, `[offline]` extra
  (langgraph/ollama), `ingest-bulk`, `select`/`synthesize` full query path + entailment verifier
  implementation, federation, embeddings, promotion graph. (`select`/`synthesize` prompt fragments
  exist in Task 12 but their operations + the entailment verifier land in M1 with the query path —
  noted so the next plan picks them up.)
- **Type consistency:** `MutationProposal` fields (target_file/action/frontmatter/body/citations/
  cross_refs/expected_hash), `LibraryLock.current_token()`, `RunRegistry.select_resumable(fingerprint)`,
  `commit_mutation(..., fencing_token, lock, run_step)`, `route_extracts(..., size_threshold=...)`
  used consistently across tasks.
- **Determinism:** no `Date.now()`/wall-clock in pure logic — the CLI takes `--timestamp` for run ids;
  `LibraryLock` reads `time.time()` only inside methods (lock liveness), never at import.

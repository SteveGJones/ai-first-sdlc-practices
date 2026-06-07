# kb-offline M1a — Ollama backend + ingest_graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the M0 single-ingest pipeline on a local Ollama model, orchestrated by a LangGraph `ingest_graph`, with the graph's identity tied to the M0 run/journal contract.

**Architecture:** Add an `OllamaBackend` (raw `ollama` client + `format=<schema>`, strict-offline localhost contract) behind the M0 `generate/embed` seam. Add a LangGraph `StateGraph` (`ingest_graph`) with one node per existing pipeline stage (thin wrappers over the M0 deterministic core/pipeline), compiled with `SqliteSaver`, `thread_id == run_id`, the canonical step-ID `f"{run_id}:{stage}:{item}"`, a `RetryPolicy` on the read-only extract node, and no retry on the mutating commit node. The CLI `ingest` runs through the graph; `--backend ollama` selects the local model.

**Tech Stack:** Python 3.9+, Pydantic v2, `ollama` client, `langgraph` + `langgraph-checkpoint-sqlite`, pytest, the project `.venv`. Specs: `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` + `docs/superpowers/specs/2026-06-07-kb-offline-M1-design-addendum.md`.

---

## Environment & scope

- **Use the project `.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. Never bare `python`/`pip`.
- flake8 (no E702/E402) + black(127) enforced; run `.venv/bin/python -m flake8`.
- Ollama is installed (v0.30.6, `gpt-oss:20b` + `nomic-embed-text` pulled) — the live smoke is runnable but gated skip-if-absent.
- **M1a only.** OUT of scope: `Send` fan-out / `ingest-bulk` (M1b); query path / `select`/`synthesize` / entailment verifier / provenance (M1c); embeddings (M3).

## File structure (M1a)

| File | Responsibility |
|---|---|
| `plugins/sdlc-knowledge-base/pyproject.toml` | add `[project.optional-dependencies] offline = [langgraph, langgraph-checkpoint-sqlite, ollama]` |
| `plugins/sdlc-knowledge-base/scripts/backends/ollama_backend.py` | `OllamaBackend` — raw `ollama` client, `format=schema`, strict-offline localhost contract, deferred import |
| `plugins/sdlc-knowledge-base/scripts/resume.py` (modify) | add `step_id(run_id, stage, item)` canonical helper |
| `plugins/sdlc-knowledge-base/scripts/graphs/__init__.py`, `graphs/ingest_graph.py` | `IngestState` + node wrappers + `build_ingest_graph(backend, …)` (StateGraph + SqliteSaver + RetryPolicy) |
| `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py` (modify) | `--backend ollama`; route `ingest` through `ingest_graph`; use `step_id` for the reduce commit |
| Tests | `tests/test_kb_offline_ollama_backend.py`, `tests/test_kb_offline_ingest_graph.py`, `tests/test_kb_offline_ollama_smoke.py`, updates to `tests/test_kb_offline_cli.py` |

---

## Task 1: `[offline]` optional-dependencies extra + install into .venv

**Files:** Modify `plugins/sdlc-knowledge-base/pyproject.toml`; Test `tests/test_kb_offline_cli.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_cli.py`:

```python
def test_pyproject_declares_offline_extra():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    from pathlib import Path
    pp = Path(__file__).resolve().parents[1] / "plugins/sdlc-knowledge-base/pyproject.toml"
    data = tomllib.loads(pp.read_text())
    extra = data["project"]["optional-dependencies"]["offline"]
    joined = " ".join(extra)
    assert "langgraph" in joined
    assert "langgraph-checkpoint-sqlite" in joined
    assert "ollama" in joined
    assert "langchain-ollama" not in joined  # deliberately excluded
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k offline_extra -v`
Expected: FAIL (KeyError: 'optional-dependencies').

- [ ] **Step 3: Add the extra to pyproject.toml**

In `plugins/sdlc-knowledge-base/pyproject.toml`, add after the `[project.scripts]` table:

```toml
[project.optional-dependencies]
offline = [
  "langgraph",
  "langgraph-checkpoint-sqlite",
  "ollama",
]
```

- [ ] **Step 4: Install the extra into the venv + verify imports**

Run:
```bash
.venv/bin/python -m pip install --quiet -e "plugins/sdlc-knowledge-base/[offline]"
.venv/bin/python -c "import langgraph, ollama; from langgraph.graph import StateGraph, START, END; from langgraph.types import Send; from langgraph.checkpoint.sqlite import SqliteSaver; print('offline deps import OK')"
.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k offline_extra -v
```
Expected: "offline deps import OK" and the test passes. If `SqliteSaver` import path differs in the installed version, note the actual path (it is provided by `langgraph-checkpoint-sqlite`) and use it consistently in Task 4.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/pyproject.toml tests/test_kb_offline_cli.py
git commit -m "build(kb-offline): add [offline] extra (langgraph + checkpoint-sqlite + ollama) (#211)"
```

---

## Task 2: `step_id` canonical helper + adopt it in the CLI commit

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/resume.py`, `kb_offline_cli.py`; Test `tests/test_kb_offline_resume.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_resume.py`:

```python
from sdlc_knowledge_base_scripts.resume import step_id


def test_step_id_canonical_formula():
    assert step_id("run123", "reduce", "topic.md") == "run123:reduce:topic.md"
    assert step_id("run123", "extract", "src-slug") == "run123:extract:src-slug"
    # deterministic
    assert step_id("r", "reduce", "t.md") == step_id("r", "reduce", "t.md")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_resume.py -k step_id -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `step_id` in resume.py**

Append to `plugins/sdlc-knowledge-base/scripts/resume.py`:

```python
def step_id(run_id: str, stage: str, item: str) -> str:
    """Canonical journal/graph step identifier: f"{run_id}:{stage}:{item}".

    Single scheme across the CLI, ingest_graph, and commit_mutation so a replayed
    node passes the identical journal step ID (idempotent replay). stage e.g.
    'extract'/'reduce'; item is the source slug or target filename."""
    return f"{run_id}:{stage}:{item}"
```

- [ ] **Step 4: Adopt it in the CLI commit call**

In `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`, import `step_id` (add to the
`from .resume import ...` line) and change the commit call's `run_step` from
`run_step=f"{run_id}-{tfile}"` to:

```python
                    run_step=step_id(run_id, "reduce", tfile),
```

- [ ] **Step 5: Run to verify pass + no CLI regression**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_resume.py tests/test_kb_offline_cli.py -q`
Expected: all pass (the SKIPPED-on-resume idempotency test still holds — the step id is still
deterministic per `(run_id, reduce, tfile)`).

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/resume.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_resume.py
git commit -m "feat(kb-offline): canonical step_id f'{run_id}:{stage}:{item}' adopted by CLI commit (#211)"
```

---

## Task 3: `OllamaBackend` (raw client, format=schema, strict-offline localhost)

**Files:** Create `plugins/sdlc-knowledge-base/scripts/backends/ollama_backend.py`; Test `tests/test_kb_offline_ollama_backend.py`

- [ ] **Step 1: Write the failing tests** (inject a fake `ollama`-like client; no daemon)

Create `tests/test_kb_offline_ollama_backend.py`:

```python
"""Tests for OllamaBackend (no live daemon — injected client)."""
from __future__ import annotations

import pytest

from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend


class _FakeClient:
    def __init__(self):
        self.calls = []

    def chat(self, *, model, messages, format=None, stream=False):
        self.calls.append({"model": model, "messages": messages, "format": format})
        return {"message": {"content": '{"ok": true}'}}

    def embed(self, *, model, input):
        return {"embeddings": [[0.0] * 4 for _ in input]}


def test_generate_passes_schema_as_format_and_returns_text():
    c = _FakeClient()
    be = OllamaBackend(model="gpt-oss:20b", client=c)
    out = be.generate("q", schema={"type": "object"})
    assert out == '{"ok": true}'
    assert c.calls[0]["format"] == {"type": "object"}
    assert c.calls[0]["model"] == "gpt-oss:20b"


def test_embed_returns_vectors():
    c = _FakeClient()
    be = OllamaBackend(model="gpt-oss:20b", client=c, embed_model="nomic-embed-text")
    vecs = be.embed(["a", "b"])
    assert len(vecs) == 2 and len(vecs[0]) == 4


def test_strict_offline_rejects_remote_host():
    with pytest.raises(ValueError):
        OllamaBackend(model="m", host="http://remote.example.com:11434")


def test_remote_host_allowed_when_opted_in():
    # constructing with allow_remote=True must not raise on host validation
    be = OllamaBackend(model="m", host="http://remote.example.com:11434",
                       allow_remote=True, client=_FakeClient())
    assert be.model == "m"


def test_localhost_variants_accepted():
    for h in ("http://localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434"):
        OllamaBackend(model="m", host=h, client=_FakeClient())
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_backend.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `OllamaBackend`**

Create `plugins/sdlc-knowledge-base/scripts/backends/ollama_backend.py`:

```python
"""Local Ollama backend — model calls only (#211, M1a). Uses the raw `ollama` client
with `format=<JSON schema>` for grammar-constrained output; the pipeline owns parsing.
Strict-offline by default: a non-loopback host is rejected unless allow_remote=True."""
from __future__ import annotations

from urllib.parse import urlparse

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_loopback(host: str) -> bool:
    netloc = urlparse(host).hostname or host
    return netloc in _LOOPBACK_HOSTS


class OllamaBackend:
    def __init__(self, model: str = "gpt-oss:20b", *, host: str = "http://localhost:11434",
                 embed_model: str = "nomic-embed-text", allow_remote: bool = False, client=None):
        if not allow_remote and not _is_loopback(host):
            raise ValueError(
                f"strict-offline: refusing non-loopback Ollama host {host!r}; "
                "pass allow_remote=True (--allow-remote-ollama) to override"
            )
        self.model = model
        self.embed_model = embed_model
        self.host = host
        if client is not None:
            self._client = client
        else:
            import ollama  # deferred — only needed for live calls
            self._client = ollama.Client(host=host)

    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        resp = self._client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            stream=False,
        )
        return resp["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embed(model=self.embed_model, input=texts)
        return resp["embeddings"]
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_backend.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/backends/ollama_backend.py tests/test_kb_offline_ollama_backend.py
git commit -m "feat(kb-offline): OllamaBackend (raw client, format=schema, strict-offline host) (#211)"
```

---

## Task 4: `ingest_graph` (StateGraph + SqliteSaver + RetryPolicy)

**Files:** Create `plugins/sdlc-knowledge-base/scripts/graphs/__init__.py`, `graphs/ingest_graph.py`; Test `tests/test_kb_offline_ingest_graph.py`

The graph is a thin re-expression of the existing M0 ingest stages — nodes call the same
`pipeline`/`kb_ingest_bulk`/`mutation` functions. State carries everything the nodes need.

- [ ] **Step 1: Verify the installed LangGraph import paths** (version drift guard — do this before writing code)

Run:
```bash
.venv/bin/python -c "from langgraph.graph import StateGraph, START, END; print('graph ok')"
.venv/bin/python -c "from langgraph.checkpoint.sqlite import SqliteSaver; print('sqlite saver ok')"
.venv/bin/python - <<'PY'
# RetryPolicy import path varies by version; find it
import importlib
for path in ("langgraph.types", "langgraph.pregel"):
    try:
        m = importlib.import_module(path)
        if hasattr(m, "RetryPolicy"):
            print("RetryPolicy at", path); break
    except Exception as e:
        print(path, "->", e)
PY
```
Use the confirmed `RetryPolicy` import path in Step 3. (If it's neither, check `langgraph` docs for the installed version and use that path; do not guess.)

- [ ] **Step 2: Write the failing test** (drive the graph with FakeBackend — no model calls)

Create `tests/test_kb_offline_ingest_graph.py`:

```python
"""Tests for the ingest_graph (FakeBackend; no live model)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.ingest_graph import build_ingest_graph


def _seed(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _fake(extract_payload, reduce_payload):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: (  # type: ignore
        reduce_payload if "Routed extracts" in prompt else extract_payload)
    return be


def test_ingest_graph_runs_end_to_end(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps({"source": str(src), "findings": ["finding one"],
                                  "confidence": "medium",
                                  "targets": [{"new_topic_slug": "topic-one", "title": "Topic One",
                                               "finding_idx": [0]}]})
    reduce_payload = json.dumps({"target_file": "topic-one.md", "action": "create",
                                 "frontmatter": {"layer": "domain", "confidence": "medium"},
                                 "body": "# Topic One\n- finding one",
                                 "citations": [], "cross_refs": [], "expected_hash": None})
    be = _fake(extract_payload, reduce_payload)
    graph = build_ingest_graph(be, allowed_layers=["domain"])
    state = {
        "library_path": str(lib), "source_spec": str(src),
        "run_id": "run-1", "fencing_token": None, "timestamp": "2026-06-07T00:00:00Z",
    }
    result = graph.invoke(state, config={"configurable": {"thread_id": "run-1"}})
    assert (lib / "topic-one.md").exists()
    assert result["committed"] == 1
    assert "topic-one.md" in (lib / "_shelf-index.md").read_text()
```

- [ ] **Step 3: Implement `graphs/ingest_graph.py`**

Create `plugins/sdlc-knowledge-base/scripts/graphs/__init__.py`:

```python
"""LangGraph orchestration adapters for kb-offline (issue #211)."""
```

Create `plugins/sdlc-knowledge-base/scripts/graphs/ingest_graph.py`. The node functions own the
acquire-lock/fencing lifecycle so the graph matches the M0 CLI behaviour exactly; the graph wires
them. Use the `RetryPolicy` import confirmed in Step 1 (shown here as `from langgraph.types import
RetryPolicy` — replace if Step 1 found a different path):

```python
"""ingest_graph: a thin LangGraph re-expression of the M0 single-ingest pipeline
(#211, M1a). Nodes wrap the existing deterministic core + pipeline ops; the graph
adds checkpoint persistence (SqliteSaver, thread_id == run_id) and an explicit
RetryPolicy on the read-only extract node. The manifest + journal remain the resume
authority; commit uses the canonical step_id so replay is idempotent."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import RetryPolicy  # NOTE: confirm path via Task 4 Step 1

from .. import kb_ingest_bulk as kbb
from ..mutation import (
    CommitConflict, FenceError, commit_mutation, recover, validate_proposal,
)
from ..pipeline import extract, reduce_to_proposal
from ..resume import LibraryLock, step_id


class IngestState(TypedDict, total=False):
    library_path: str
    source_spec: str
    run_id: str
    timestamp: str
    fencing_token: Optional[int]
    committed: int
    rejected: int
    conflicts: int
    reindexed: bool


def build_ingest_graph(backend, *, allowed_layers, retry_attempts: int = 3):
    """Construct + compile the single-ingest graph. `backend` is the model seam;
    `allowed_layers` gates mutation validation."""
    lib_of = lambda s: Path(s["library_path"])
    shelf_of = lambda s: lib_of(s) / "_shelf-index.md"
    extracts_of = lambda s: lib_of(s) / ".kb-offline" / "extracts"

    def n_discover(state: IngestState) -> dict:
        lock = LibraryLock(lib_of(state))
        token = lock.acquire()
        # store the lock on the state via a module-level handle keyed by run_id
        _LOCKS[state["run_id"]] = lock
        return {"fencing_token": token, "committed": 0, "rejected": 0, "conflicts": 0}

    def n_map_extract(state: IngestState) -> dict:
        edir = extracts_of(state)
        for src in kbb.discover_sources([state["source_spec"]]):
            slug = kbb.slug_for_source(src)
            if kbb.extract_path(edir, slug).exists():
                continue
            result = extract(str(src), shelf_of(state), backend=backend)
            kbb.persist_extract(edir, slug, json.loads(result.model_dump_json()))
        return {}

    def n_route_reduce_commit(state: IngestState) -> dict:
        lib = lib_of(state)
        edir = extracts_of(state)
        loaded = [json.loads(p.read_text()) for p in sorted(edir.glob("*.json"))]
        existing = {p.name for p in lib.glob("*.md")
                    if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        route = kbb.route_extracts(loaded, existing_files=existing, size_threshold=200_000)
        known = set()
        for ex in loaded:
            known.update(ex.get("citations", []))
        lock = _LOCKS[state["run_id"]]
        token = state["fencing_token"]
        committed = rejected = conflicts = 0
        for tfile, slot in route.targets.items():
            existing_content = (lib / tfile).read_text() if (lib / tfile).exists() else None
            proposal = reduce_to_proposal(
                target_file=tfile, is_new=slot["is_new"], extracts=slot["extracts"],
                existing_content=existing_content, backend=backend)
            errors = validate_proposal(proposal, library_path=lib,
                                       allowed_layers=allowed_layers, known_citations=known)
            if errors:
                rejected += 1
                continue
            try:
                commit_mutation(proposal, library_path=lib, fencing_token=token, lock=lock,
                                run_step=step_id(state["run_id"], "reduce", tfile))
                committed += 1
            except (CommitConflict, FenceError):
                conflicts += 1
        return {"committed": committed, "rejected": rejected, "conflicts": conflicts}

    def n_finalize(state: IngestState) -> dict:
        report = recover(lib_of(state))
        lock = _LOCKS.pop(state["run_id"], None)
        if lock is not None:
            lock.release()
        return {"reindexed": report["reindexed"]}

    builder = StateGraph(IngestState)
    builder.add_node("discover", n_discover)
    builder.add_node("map_extract", n_map_extract,
                     retry=RetryPolicy(max_attempts=retry_attempts))
    builder.add_node("route_reduce_commit", n_route_reduce_commit)
    builder.add_node("finalize", n_finalize)
    builder.add_edge(START, "discover")
    builder.add_edge("discover", "map_extract")
    builder.add_edge("map_extract", "route_reduce_commit")
    builder.add_edge("route_reduce_commit", "finalize")
    builder.add_edge("finalize", END)
    saver = SqliteSaver.from_conn_string(":memory:") if False else None  # see Step 3a
    return builder.compile(checkpointer=saver)


_LOCKS: dict = {}
```

- [ ] **Step 3a: Wire a real SqliteSaver under the library**

The checkpointer must persist under `library/.kb-offline/`. Since the conn string needs the library
path (known per-invocation, not at build time), change `build_ingest_graph` to accept the library
path for the saver, OR compile without a checkpointer and pass one at invoke. Simplest that matches
LangGraph's API: build the saver from a file path and compile with it. Replace the `saver = …` line
and the signature so the caller passes `checkpoint_path`:

```python
def build_ingest_graph(backend, *, allowed_layers, checkpoint_path=None, retry_attempts: int = 3):
    ...
    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver.from_conn_string(str(checkpoint_path))
    else:
        saver = None
    return builder.compile(checkpointer=saver)
```
`SqliteSaver.from_conn_string` is a context manager in some versions — if so, the confirmed pattern
from Task 4 Step 1 governs; adapt to return a compiled graph that holds an open saver (e.g. construct
`SqliteSaver(sqlite3.connect(path, check_same_thread=False))` directly). Use whatever the installed
version supports, verified in Step 1. The test passes `checkpoint_path=None` (in-memory/no checkpoint)
so graph logic is tested without the saver; the CLI (Task 5) passes the real path.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ingest_graph.py -v`
Expected: PASS. If `build_ingest_graph(... checkpoint_path=None)` requires a checkpointer for
`thread_id` configs, pass a `MemorySaver` (`from langgraph.checkpoint.memory import MemorySaver`) in
the test instead of `None` — confirm against the installed version.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/ tests/test_kb_offline_ingest_graph.py
git commit -m "feat(kb-offline): ingest_graph (StateGraph + SqliteSaver + RetryPolicy, thin re-expression) (#211)"
```

---

## Task 5: CLI routes ingest through the graph + `--backend ollama`

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`; Test `tests/test_kb_offline_cli.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_cli.py`:

```python
def test_make_backend_ollama_strict_offline_default(monkeypatch):
    # _make_backend('ollama', None) builds an OllamaBackend defaulting to localhost (no daemon call at construct)
    from sdlc_knowledge_base_scripts import kb_offline_cli as c
    be = c._make_backend("ollama", None)
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    assert isinstance(be, OllamaBackend)
    assert be.host == "http://localhost:11434"
```

(The existing `test_cli_ingest_*` tests already pass a `backend_override` and must keep passing once
ingest runs through the graph — behaviour is identical.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k "make_backend_ollama" -v`
Expected: FAIL (`_make_backend` raises SystemExit for 'ollama').

- [ ] **Step 3: Add the ollama branch + route ingest through the graph**

In `kb_offline_cli.py` `_make_backend`, add before the final `raise SystemExit`:

```python
    if name == "ollama":
        from .backends.ollama_backend import OllamaBackend
        return OllamaBackend()
```

Refactor `_cmd_ingest` so the discover→extract→route→reduce→commit→recover body runs via the graph
instead of the inline loop. Replace the inline body (from lock acquire through `recover`) with:

```python
    from .graphs.ingest_graph import build_ingest_graph
    checkpoint = lib / ".kb-offline" / "graph-checkpoint.sqlite"
    graph = build_ingest_graph(backend, allowed_layers=allowed_layers, checkpoint_path=checkpoint)
    try:
        out = graph.invoke(
            {"library_path": str(lib), "source_spec": args.source,
             "run_id": run_id, "timestamp": args.timestamp},
            config={"configurable": {"thread_id": run_id}},
        )
    except Exception:
        reg.set_state(run_id, "failed")
        raise
    committed = out.get("committed", 0)
    rejected = out.get("rejected", 0)
    conflicts = out.get("conflicts", 0)
    had_errors = rejected > 0 or conflicts > 0
    reg.set_state(run_id, "completed_with_errors" if had_errors else "completed")
    print(f"ingest: run={run_id} committed={committed} rejected={rejected} "
          f"conflicts={conflicts} reindexed={out.get('reindexed')}")
    return 1 if (committed == 0 and had_errors) else 0
```

(The graph's `discover`/`finalize` nodes now own lock acquire/release; remove the CLI's direct
`LibraryLock`/`commit_mutation`/`recover` usage and the now-unused imports. Keep the resume-selection
block and the unknown-`--resume` guard above the graph invoke. Note: the SKIPPED-on-resume guard logic
lives in `commit_mutation`'s caller; ensure the graph's `route_reduce_commit` preserves the same
create-conflict-is-idempotent-skip behaviour the M0 CLI test expects — if the existing
`test_cli_resume_skips_completed_source` relied on the CLI loop's SKIPPED handling, move that handling
into `n_route_reduce_commit` so the test still passes.)

- [ ] **Step 4: Run to verify pass + full CLI/graph regression**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py tests/test_kb_offline_ingest_graph.py tests/test_kb_offline_integration.py -v`
Expected: all pass. If the resume-skip test fails, port the idempotent-create-skip handling into
`n_route_reduce_commit` (treat a `CommitConflict` whose target already exists as a skip, not a
counted conflict) — mirror the M0 CLI behaviour exactly.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "feat(kb-offline): CLI ingest runs through ingest_graph; --backend ollama (#211)"
```

---

## Task 6: Live Ollama smoke (skip-if-absent) + validation gate

**Files:** Create `tests/test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Write the skip-gated live smoke**

Create `tests/test_kb_offline_ollama_smoke.py`:

```python
"""Live Ollama smoke — skipped unless a local daemon + model are present.
Proves OllamaBackend + ingest_graph produce a real page from a real source."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _ollama_ready(model="gpt-oss:20b"):
    if shutil.which("ollama") is None:
        return False
    try:
        import ollama
        names = [m.get("model", m.get("name", "")) for m in ollama.list().get("models", [])]
        return any(model in n for n in names)
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_single_ingest(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.ingest_graph import build_ingest_graph

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    src = next((REPO / "tmp_texts").glob("*.md"))   # one real CRI source

    be = OllamaBackend(model="gpt-oss:20b")
    graph = build_ingest_graph(be, allowed_layers=["methodology", "evidence", "domain", "development"],
                               checkpoint_path=lib / ".kb-offline" / "ck.sqlite")
    out = graph.invoke(
        {"library_path": str(lib), "source_spec": str(src),
         "run_id": "live-1", "timestamp": "2026-06-07T00:00:00Z"},
        config={"configurable": {"thread_id": "live-1"}})
    # at least the extract JSON was valid and persisted (real structured-output path exercised)
    extracts = list((lib / ".kb-offline" / "extracts").glob("*.json"))
    assert extracts, "no extract produced"
    json.loads(extracts[0].read_text())   # must be valid JSON
```

- [ ] **Step 2: Run it (will run if Ollama present, else skip)**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -v`
Expected: PASS (Ollama is present) or SKIP. If it runs and the extract JSON is invalid/empty, that is
real signal about `gpt-oss:20b` structured-output quality — record it (it informs the M1c eval gate)
but do NOT weaken the assertion; report DONE_WITH_CONCERNS with the observed output.

- [ ] **Step 3: Full M0+M1a suite + validation gate**

Run:
```bash
.venv/bin/python -m pytest tests/ -k kb -q
.venv/bin/python -m flake8 plugins/sdlc-knowledge-base/scripts/backends/ollama_backend.py plugins/sdlc-knowledge-base/scripts/graphs/ plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py plugins/sdlc-knowledge-base/scripts/resume.py
.venv/bin/python tools/validation/check-feature-proposal.py --branch feature/211-kb-offline-langgraph
.venv/bin/python tools/validation/check-prompt-parity.py
```
Report all counts/results. All must pass (smoke may SKIP if Ollama absent in the runner).

- [ ] **Step 4: Commit**

```bash
git add tests/test_kb_offline_ollama_smoke.py
git commit -m "test(kb-offline): live Ollama ingest smoke (skip-if-absent) + M1a validation gate (#211)"
```

---

## Self-review notes

- **Addendum coverage (M1a rows):** `[offline]` extra without langchain-ollama (Task 1); OllamaBackend
  raw client + `format=schema` + strict-offline localhost contract (Task 3); canonical
  `step_id` adopted by the commit caller (Task 2); `ingest_graph` one-node-per-stage + SqliteSaver +
  `thread_id==run_id` + `RetryPolicy` on extract + no-retry on commit (Tasks 4–5); CLI `--backend
  ollama` + ingest-through-graph (Task 5); manifest+journal stay resume authority (nodes call
  `commit_mutation`/`recover`); live smoke (Task 6).
- **Deferred to M1b/M1c (correctly absent):** `Send` fan-out / ingest-bulk, parallel reduce-by-target,
  query/select/synthesize, entailment verifier, provenance/layer, embeddings.
- **Version-drift honesty:** Task 4 Step 1 verifies `RetryPolicy`/`SqliteSaver` import paths against
  the installed LangGraph before code uses them — not hardcoded-and-hoped.
- **Type/name consistency:** `step_id(run_id, stage, item)`, `build_ingest_graph(backend, *,
  allowed_layers, checkpoint_path, retry_attempts)`, `IngestState` keys, and the
  `committed/rejected/conflicts/reindexed` return shape are used consistently across Tasks 4–5 and
  match the M0 `commit_mutation`/`recover` signatures.
- **Known risk flagged for execution:** routing ingest through the graph must preserve the M0 CLI's
  resume-skip (idempotent create-conflict) behaviour — Task 5 Step 4 calls this out explicitly so the
  existing `test_cli_resume_skips_completed_source` keeps passing.

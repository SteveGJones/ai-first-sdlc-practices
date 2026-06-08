# kb-offline M1b — ingest-bulk (parallel map-reduce) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest many sources in parallel through a LangGraph `Send` fan-out (bounded map) and a parallel reduce-by-target (one writer per file), reusing the M0 commit/fencing/CAS/journal core verbatim.

**Architecture:** A new `build_bulk_ingest_graph` widens M1a's single-ingest topology: `discover → (Send extract_one per source, bounded) → route → (Send reduce_one per target, bounded, one-writer-per-file) → finalize`. Parallel-worker outputs merge via `Annotated` state reducers. Concurrency is bounded by `--parallel N` (default 16, max 64). Each worker heartbeats the lock so long runs don't falsely expire. The single-ingest `ingest_graph` (M1a) is untouched.

**Tech Stack:** Python 3.9+, langgraph 1.2.4 (`Send`, `Annotated` reducers, `max_concurrency` config), the project `.venv`, pytest, Ollama. Specs: `docs/superpowers/specs/2026-06-07-kb-offline-M1-design-addendum.md` (M1b concurrency contract + decision 11) + the parent design spec.

---

## Environment & scope

- **Use the project `.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. Never bare python/pip.
- flake8 (no E702/E402) + black(127) enforced.
- **M1b only.** OUT of scope: query path / select / synthesize / entailment verifier / provenance (M1c); embeddings (M3). Single-ingest `ingest_graph` (M1a) is reused/untouched.
- M1b reuses verbatim: `pipeline.extract`/`reduce_to_proposal`, `mutation.validate_proposal`/`commit_mutation`/`recover`/`CommitConflict`/`FenceError`, `kb_ingest_bulk.discover_sources`/`slug_for_source`/`extract_path`/`persist_extract`/`route_extracts`, `resume.LibraryLock`/`step_id`/`release_lock`, `contracts.MutationAction`, `graphs.ingest_graph._LOCKS`/`release_lock`.

## Concurrency-safety rationale (why parallel reduce is safe)

Parallel `reduce_one` workers each write a **distinct** target file (route groups by filename) → no write contention (the #208 one-writer-per-file model). All workers share the run's single fencing token and lock — legitimate, since they're the one holder; `commit_mutation`'s per-file CAS + journal (distinct `run_step` per target) keep each write idempotent. The manifest/runs.json is written only by the CLI at the end, not by workers. So bounded parallel reduce is safe.

## File structure (M1b)

| File | Responsibility |
|---|---|
| `plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py` | `BulkIngestState` (Annotated reducers) + `build_bulk_ingest_graph` + `extract_one`/`reduce_one` workers + route node |
| `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py` (modify) | add `ingest-bulk <glob\|dir\|list>` subcommand (`--parallel`, `--backend`, `--resume`, `--timestamp`) |
| Tests | `tests/test_kb_offline_bulk_graph.py`, updates to `tests/test_kb_offline_cli.py`, `tests/test_kb_offline_ollama_smoke.py` |

---

## Task 1: Verify-first — pin the langgraph 1.2.4 Send / reducer / concurrency pattern

No production code yet — this records the exact working API the rest of M1b uses (version-drift guard, as in M1a).

**Files:** none committed (a scratch experiment) — record findings in the Task 2 implementation.

- [ ] **Step 1: Run a minimal fan-out experiment in the venv**

Run:
```bash
cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices
.venv/bin/python - <<'PY'
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class S(TypedDict, total=False):
    items: list
    results: Annotated[list, add]

def fan(state):
    return [Send("work", {"item": i}) for i in state["items"]]

def work(state):
    return {"results": [state["item"] * 10]}

b = StateGraph(S)
b.add_node("seed", lambda s: {"items": s["items"]})
b.add_node("work", work)
b.add_node("collect", lambda s: {})
b.add_edge(START, "seed")
b.add_conditional_edges("seed", fan, ["work"])
b.add_edge("work", "collect")
b.add_edge("collect", END)
g = b.compile()
out = g.invoke({"items": [1, 2, 3]})
print("results:", sorted(out["results"]))   # expect [10,20,30] merged via reducer

# concurrency bounding: does max_concurrency get accepted in config?
out2 = g.invoke({"items": [1, 2, 3, 4, 5]}, config={"max_concurrency": 2})
print("with max_concurrency=2 results:", sorted(out2["results"]))
PY
```
Record: (a) the exact `Send` import + conditional-edge fan-out shape that works; (b) whether `Annotated[list, add]` merges worker outputs into the parent state; (c) whether `config={"max_concurrency": N}` is accepted (no error) and bounds parallelism. 

- [ ] **Step 2: Decide the bounding mechanism**

If `max_concurrency` is accepted and bounds parallelism → **use it** (`config={"max_concurrency": N, "configurable": {"thread_id": run_id}}`). If it is NOT honored for `Send` fan-out → **chunked fallback**: the fan-out function returns Sends for only the next N pending items, with a loop-back edge re-entering the fan-out until all are dispatched (document which you chose). Record the chosen mechanism for Tasks 4-5. (Do not write production code in this task; this is the spike that de-risks Tasks 2-4.)

---

## Task 2: `BulkIngestState` + bounded map fan-out (extract_one)

**Files:** Create `plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py`; Test `tests/test_kb_offline_bulk_graph.py`

- [ ] **Step 1: Write the failing test** (multi-source map fan-out, FakeBackend)

Create `tests/test_kb_offline_bulk_graph.py`:

```python
"""Tests for the bulk ingest graph (FakeBackend; no live model)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.bulk_ingest_graph import build_bulk_ingest_graph


def _seed(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _multi_source_backend(sources):
    """generate() returns an extract per source (keyed by which source path is in the prompt)
    and a reduce proposal when asked to reduce a target."""
    def gen(prompt, schema=None):
        if "Routed extracts" in prompt:
            # reduce: emit a create proposal for the target named in the prompt
            import re
            m = re.search(r"Target file: (\S+)", prompt)
            tfile = m.group(1) if m else "topic.md"
            return json.dumps({"target_file": tfile, "action": "create",
                               "frontmatter": {"layer": "domain", "confidence": "low"},
                               "body": f"# {tfile}", "citations": [], "cross_refs": [],
                               "expected_hash": None})
        # extract: find which source path appears in the prompt
        for s in sources:
            if str(s) in prompt:
                slug = s.stem.lower().replace("_", "-")
                return json.dumps({"source": str(s), "findings": [f"f-{slug}"],
                                   "confidence": "low",
                                   "targets": [{"new_topic_slug": slug, "title": slug,
                                                "finding_idx": [0]}]})
        return json.dumps({"source": "?", "findings": [], "confidence": "low", "targets": []})
    be = FakeBackend()
    be.generate = gen
    return be


def test_bulk_map_fans_out_over_all_sources(tmp_path):
    lib = _seed(tmp_path)
    srcs = []
    for i in range(3):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)
    be = _multi_source_backend(srcs)
    graph = build_bulk_ingest_graph(be, allowed_layers=["domain"])
    out = graph.invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in srcs], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 8})
    # every source produced an extract file
    extracts = list((lib / ".kb-offline" / "extracts").glob("*.json"))
    assert len(extracts) == 3
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_bulk_graph.py -k fans_out -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement the map half of `bulk_ingest_graph.py`**

Create `plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py`. Use the `Send`/reducer pattern confirmed in Task 1. The `extract_one` worker heartbeats the lock (long-run safety) and is idempotent (skip if the extract file exists). `discover` acquires the lock (reuse the M1a `_LOCKS` + `release_lock`). The fan-out conditional edge returns one `Send("extract_one", {...})` per source.

```python
"""Bulk parallel map-reduce ingest graph (issue #211, M1b). Widens the M1a single-ingest
topology to a bounded Send fan-out for map (extract_one per source) and a parallel
reduce-by-target (reduce_one per target, one writer per file). Reuses the M0 commit /
fencing / CAS / journal core verbatim; parallel reduce is safe because each worker writes
a distinct target file. Concurrency is bounded by the caller's max_concurrency config."""
from __future__ import annotations

import json
import sqlite3
import sys
from operator import add
from pathlib import Path
from typing import Annotated, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .. import kb_ingest_bulk as kbb
from ..contracts import MutationAction
from ..mutation import CommitConflict, FenceError, commit_mutation, recover, validate_proposal
from ..pipeline import extract, reduce_to_proposal
from ..resume import LibraryLock, step_id
from .ingest_graph import _LOCKS, release_lock


class BulkIngestState(TypedDict, total=False):
    library_path: str
    source_specs: list  # resolved list of source path strings
    run_id: str
    fencing_token: Optional[int]
    # reduce-phase target plan, produced by the route node
    targets: list  # list of {"target_file","is_new","extracts"}
    known_citations: list
    # parallel-worker accumulators (merged via reducers)
    committed: Annotated[int, add]
    rejected: Annotated[int, add]
    conflicts: Annotated[int, add]
    reindexed: int


def _extracts_dir(lib: Path) -> Path:
    return lib / ".kb-offline" / "extracts"


def build_bulk_ingest_graph(backend, *, allowed_layers: list[str], checkpoint_path=None):
    def n_discover(state: BulkIngestState) -> dict:
        lib = Path(state["library_path"])
        lock = LibraryLock(lib)
        token = lock.acquire()
        _LOCKS[state["run_id"]] = lock
        return {"fencing_token": token}

    def fan_map(state: BulkIngestState):
        # one bounded Send per source; extract_one skips already-extracted sources
        return [Send("extract_one", {"library_path": state["library_path"],
                                     "run_id": state["run_id"], "source": s})
                for s in state["source_specs"]]

    def n_extract_one(state: dict) -> dict:
        lib = Path(state["library_path"])
        _LOCKS[state["run_id"]].heartbeat()  # keep the lease fresh during long fan-out
        edir = _extracts_dir(lib)
        src = Path(state["source"])
        slug = kbb.slug_for_source(src)
        if not kbb.extract_path(edir, slug).exists():
            result = extract(str(src), lib / "_shelf-index.md", backend=backend)
            kbb.persist_extract(edir, slug, json.loads(result.model_dump_json()))
        return {}

    def n_route(state: BulkIngestState) -> dict:
        lib = Path(state["library_path"])
        loaded = [json.loads(p.read_text()) for p in sorted(_extracts_dir(lib).glob("*.json"))]
        existing = {p.name for p in lib.glob("*.md")
                    if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        route = kbb.route_extracts(loaded, existing_files=existing, size_threshold=200_000)
        known = set()
        for ex in loaded:
            known.update(ex.get("citations", []))
        targets = [{"target_file": t, "is_new": slot["is_new"], "extracts": slot["extracts"]}
                   for t, slot in route.targets.items()]
        return {"targets": targets, "known_citations": sorted(known)}

    # reduce half is added in Task 3; map-only wiring here so the test for fan-out passes:
    builder = StateGraph(BulkIngestState)
    builder.add_node("discover", n_discover)
    builder.add_node("extract_one", n_extract_one)
    builder.add_node("route", n_route)
    builder.add_edge(START, "discover")
    builder.add_conditional_edges("discover", fan_map, ["extract_one"])
    builder.add_edge("extract_one", "route")
    builder.add_edge("route", END)  # TEMP — Task 3 re-points route → reduce fan-out → finalize

    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()
    return builder.compile(checkpointer=saver)
```
(Adapt `fan_map`/`add_conditional_edges` to the exact shape Task 1 confirmed. If Task 1 found `max_concurrency` is NOT honored, implement the chunked-rounds fallback in `fan_map` instead and document it.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_bulk_graph.py -k fans_out -v`
Expected: PASS (3 extract files). flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py tests/test_kb_offline_bulk_graph.py
git commit -m "feat(kb-offline): bulk_ingest_graph map fan-out (Send per source, bounded, heartbeat) (#211)"
```

---

## Task 3: Parallel reduce-by-target (reduce_one) + finalize

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py`; Test `tests/test_kb_offline_bulk_graph.py`

- [ ] **Step 1: Write the failing test** (end-to-end bulk: multiple sources → multiple pages committed in parallel)

Append to `tests/test_kb_offline_bulk_graph.py`:

```python
def test_bulk_end_to_end_commits_all_targets(tmp_path):
    lib = _seed(tmp_path)
    srcs = []
    for i in range(3):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)
    be = _multi_source_backend(srcs)
    graph = build_bulk_ingest_graph(be, allowed_layers=["domain"])
    out = graph.invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in srcs], "run_id": "b1"},
        config={"configurable": {"thread_id": "b1"}, "max_concurrency": 8})
    # 3 distinct new-topic pages created (one writer per file), all committed
    pages = [p.name for p in lib.glob("*.md") if p.name != "_shelf-index.md"]
    assert out["committed"] == 3
    assert len([p for p in pages if p not in {"log.md"}]) == 3
    assert "s0.md" in (lib / "_shelf-index.md").read_text() or out["reindexed"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_bulk_graph.py -k end_to_end -v`
Expected: FAIL (route currently routes to END; no commit happens; `committed` absent).

- [ ] **Step 3: Add the reduce fan-out + finalize, re-point the edges**

In `bulk_ingest_graph.py`, add the reduce worker + finalize node and re-wire `route → fan_reduce → reduce_one → finalize → END`. `reduce_one` mirrors the M1a commit branch EXACTLY (validate→commit, idempotent-create-skip, FenceError→conflict) but for a single target; it heartbeats; it returns the per-target counters that the `Annotated[int, add]` reducers sum:

```python
    def fan_reduce(state: BulkIngestState):
        return [Send("reduce_one", {"library_path": state["library_path"],
                                    "run_id": state["run_id"],
                                    "fencing_token": state["fencing_token"],
                                    "allowed_layers": allowed_layers,
                                    "known_citations": state["known_citations"],
                                    "target": t})
                for t in state["targets"]]

    def n_reduce_one(state: dict) -> dict:
        lib = Path(state["library_path"])
        run_id = state["run_id"]
        token = state["fencing_token"]
        lock = _LOCKS[run_id]
        lock.heartbeat()
        t = state["target"]
        tfile = t["target_file"]
        existing_content = (lib / tfile).read_text() if (lib / tfile).exists() else None
        proposal = reduce_to_proposal(
            target_file=tfile, is_new=t["is_new"], extracts=t["extracts"],
            existing_content=existing_content, backend=backend)
        errors = validate_proposal(proposal, library_path=lib,
                                   allowed_layers=state["allowed_layers"],
                                   known_citations=set(state["known_citations"]))
        if errors:
            print(f"REJECTED {tfile}: {errors}", file=sys.stderr)
            return {"rejected": 1}
        try:
            commit_mutation(proposal, library_path=lib, fencing_token=token, lock=lock,
                            run_step=step_id(run_id, "reduce", tfile))
            return {"committed": 1}
        except CommitConflict as exc:
            if proposal.action == MutationAction.create and (lib / tfile).exists():
                print(f"SKIPPED {tfile}: already committed", file=sys.stderr)
                return {}
            print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
            return {"conflicts": 1}
        except FenceError as exc:
            print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
            return {"conflicts": 1}

    def n_finalize(state: BulkIngestState) -> dict:
        report = recover(Path(state["library_path"]))
        release_lock(state["run_id"])
        return {"reindexed": report["reindexed"]}
```
Register the new nodes and re-point the edges (remove the TEMP `route → END`):
```python
    builder.add_node("reduce_one", n_reduce_one)
    builder.add_node("finalize", n_finalize)
    builder.add_conditional_edges("route", fan_reduce, ["reduce_one"])
    builder.add_edge("reduce_one", "finalize")
    builder.add_edge("finalize", END)
```
(Delete the temporary `builder.add_edge("route", END)` from Task 2.)

Note on counters: because `committed`/`rejected`/`conflicts` are `Annotated[int, add]`, each `reduce_one` returns a partial (e.g. `{"committed": 1}`) and LangGraph sums them. Confirm against Task 1's reducer finding that int+add works (if the reducer must be a list, accumulate `[1]` and sum in finalize — adapt to what Task 1 confirmed).

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_bulk_graph.py -v`
Expected: both tests pass (3 extracts, 3 committed). Then full kb suite — no regressions. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py tests/test_kb_offline_bulk_graph.py
git commit -m "feat(kb-offline): bulk reduce-by-target fan-out (one writer per file) + finalize (#211)"
```

---

## Task 4: Bounded-concurrency + resume + graceful-failure coverage

**Files:** Test `tests/test_kb_offline_bulk_graph.py`

- [ ] **Step 1: Write the failing/characterization tests**

Append:

```python
def test_bulk_resume_skips_extracted_sources(tmp_path):
    lib = _seed(tmp_path)
    srcs = [tmp_path / "s0.md"]
    srcs[0].write_text("source 0")
    be = _multi_source_backend(srcs)
    g = build_bulk_ingest_graph(be, allowed_layers=["domain"])
    g.invoke({"library_path": str(lib), "source_specs": [str(srcs[0])], "run_id": "b1"},
             config={"configurable": {"thread_id": "b1"}, "max_concurrency": 4})
    # second run: extract already on disk -> extract() not called again
    calls = {"n": 0}
    def gen(prompt, schema=None):
        if "Routed extracts" not in prompt:
            calls["n"] += 1
        return be.generate(prompt, schema)
    be2 = _multi_source_backend(srcs)
    inner = be2.generate
    be2.generate = lambda p, schema=None: (calls.__setitem__("n", calls["n"] + (0 if "Routed extracts" in p else 1)) or inner(p, schema))
    g2 = build_bulk_ingest_graph(be2, allowed_layers=["domain"])
    g2.invoke({"library_path": str(lib), "source_specs": [str(srcs[0])], "run_id": "b2"},
              config={"configurable": {"thread_id": "b2"}, "max_concurrency": 4})
    assert calls["n"] == 0


def test_bulk_rejected_target_counted(tmp_path):
    lib = _seed(tmp_path)
    s = tmp_path / "s0.md"
    s.write_text("source 0")
    be = _multi_source_backend([s])
    # allowed_layers excludes 'domain' (the proposal's layer) -> rejected
    g = build_bulk_ingest_graph(be, allowed_layers=["evidence"])
    out = g.invoke({"library_path": str(lib), "source_specs": [str(s)], "run_id": "b1"},
                   config={"configurable": {"thread_id": "b1"}, "max_concurrency": 4})
    assert out.get("rejected", 0) == 1 and out.get("committed", 0) == 0
```

- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_kb_offline_bulk_graph.py -v` — these characterize existing behaviour; both should PASS (the reduce worker already handles reject; extract_one already skips). If either fails, fix the graph (not the test) and report what surfaced.

- [ ] **Step 3: Commit**

```bash
git add tests/test_kb_offline_bulk_graph.py
git commit -m "test(kb-offline): bulk resume-skip + rejected-target coverage (#211)"
```

---

## Task 5: CLI `ingest-bulk` subcommand

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`; Test `tests/test_kb_offline_cli.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_cli.py`:

```python
def test_cli_ingest_bulk_creates_pages(tmp_path):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    lib = _seed_lib(tmp_path)
    srcs = []
    for i in range(2):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)

    def gen(prompt, schema=None):
        if "Routed extracts" in prompt:
            import re
            m = re.search(r"Target file: (\S+)", prompt)
            tfile = m.group(1) if m else "t.md"
            return _j.dumps({"target_file": tfile, "action": "create",
                            "frontmatter": {"layer": "domain", "confidence": "low"},
                            "body": "# x", "citations": [], "cross_refs": [], "expected_hash": None})
        for s in srcs:
            if str(s) in prompt:
                slug = s.stem.lower()
                return _j.dumps({"source": str(s), "findings": ["f"], "confidence": "low",
                                "targets": [{"new_topic_slug": slug, "title": slug, "finding_idx": [0]}]})
        return _j.dumps({"source": "?", "findings": [], "confidence": "low", "targets": []})
    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["ingest-bulk", str(tmp_path / "*.md"), "--library", str(lib),
                   "--backend", "fake", "--parallel", "4", "--timestamp", "2026-06-08T00:00:00Z"],
                  backend_override=be, allowed_layers=["domain"])
    assert rc == 0
    runs = _j.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] in ("completed", "completed_with_errors") for r in runs["runs"].values())
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k ingest_bulk -v`
Expected: FAIL (no `ingest-bulk` subcommand).

- [ ] **Step 3: Add the `ingest-bulk` subcommand + `_cmd_ingest_bulk`**

In `kb_offline_cli.py`: add an `ingest-bulk` subparser (positional `source` glob/dir/list; `--library`, `--backend`, `--parallel` (int, default 16), `--resume`, `--timestamp`), route it to a new `_cmd_ingest_bulk` that mirrors `_cmd_ingest` but: resolves sources via `kbb.discover_sources([source])` into `source_specs`, clamps `--parallel` to `[1, 64]`, builds `build_bulk_ingest_graph`, and invokes with `config={"configurable": {"thread_id": run_id}, "max_concurrency": parallel}`. Reuse the same resume-selection, run-lifecycle, lock-cleanup-on-error (`release_lock` + `set_state failed`), and `committed/rejected/conflicts`-based return-code logic as `_cmd_ingest`. Full code:

```python
def _cmd_ingest_bulk(args: argparse.Namespace, backend_override, allowed_layers: list[str]) -> int:
    from . import kb_ingest_bulk as kbb
    from .graphs.bulk_ingest_graph import build_bulk_ingest_graph
    from .graphs.ingest_graph import release_lock

    lib = Path(args.library)
    backend = _make_backend(args.backend, backend_override)
    reg = RunRegistry(lib)
    parallel = max(1, min(64, args.parallel))
    fingerprint = {"operation": "ingest-bulk",
                   "config": config_hash({"backend": args.backend, "parallel": parallel})}

    if args.resume == "latest":
        run_id = reg.select_resumable(fingerprint) or reg.start_run(args.timestamp, fingerprint)
    elif args.resume:
        if not reg.exists(args.resume):
            raise SystemExit(f"--resume: unknown run id {args.resume!r}")
        run_id = args.resume
    else:
        run_id = reg.start_run(args.timestamp, fingerprint)

    source_specs = [str(p) for p in kbb.discover_sources([args.source])]
    checkpoint = lib / ".kb-offline" / "bulk-graph-checkpoint.sqlite"
    graph = build_bulk_ingest_graph(backend, allowed_layers=allowed_layers, checkpoint_path=checkpoint)
    try:
        out = graph.invoke(
            {"library_path": str(lib), "source_specs": source_specs, "run_id": run_id},
            config={"configurable": {"thread_id": run_id}, "max_concurrency": parallel},
        )
    except Exception:
        release_lock(run_id)
        reg.set_state(run_id, "failed")
        raise
    committed = out.get("committed", 0)
    rejected = out.get("rejected", 0)
    conflicts = out.get("conflicts", 0)
    had_errors = rejected > 0 or conflicts > 0
    reg.set_state(run_id, "completed_with_errors" if had_errors else "completed")
    print(f"ingest-bulk: run={run_id} sources={len(source_specs)} committed={committed} "
          f"rejected={rejected} conflicts={conflicts} reindexed={out.get('reindexed')}")
    return 1 if (committed == 0 and had_errors) else 0
```
Add to `main`:
```python
    p_bulk = sub.add_parser("ingest-bulk")
    p_bulk.add_argument("source")
    p_bulk.add_argument("--library", default="library")
    p_bulk.add_argument("--backend", default="anthropic")
    p_bulk.add_argument("--parallel", type=int, default=16)
    p_bulk.add_argument("--resume", default=None)
    p_bulk.add_argument("--timestamp", required=True)
```
and the dispatch: `if args.cmd == "ingest-bulk": return _cmd_ingest_bulk(args, backend_override, allowed_layers)`.

- [ ] **Step 4: Run to verify pass + full regression**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py tests/test_kb_offline_bulk_graph.py -v` then `.venv/bin/python -m pytest tests/ -k kb -q`. Expected: all pass. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "feat(kb-offline): CLI ingest-bulk subcommand (--parallel bounded fan-out) (#211)"
```

---

## Task 6: Live Ollama bulk smoke (skip-if-absent) + validation gate

**Files:** Modify `tests/test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Append a bulk live smoke**

Append to `tests/test_kb_offline_ollama_smoke.py` (reuses the `_ollama_ready` gate already defined there):

```python
@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_bulk_ingest_three_sources(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.bulk_ingest_graph import build_bulk_ingest_graph

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    corpus = sorted((REPO / "tmp_texts").glob("*.md"))[:3]
    if len(corpus) < 3:
        pytest.skip("need >=3 tmp_texts sources")

    be = OllamaBackend(model="gpt-oss:20b")
    graph = build_bulk_ingest_graph(
        be, allowed_layers=["methodology", "evidence", "domain", "development"],
        checkpoint_path=lib / ".kb-offline" / "bulk.sqlite")
    out = graph.invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in corpus], "run_id": "bulk-live"},
        config={"configurable": {"thread_id": "bulk-live"}, "max_concurrency": 3})
    # all three sources produced valid extracts via the parallel map path
    extracts = list((lib / ".kb-offline" / "extracts").glob("*.json"))
    assert len(extracts) == 3
    for e in extracts:
        import json as _j
        _j.loads(e.read_text())   # valid JSON
```

- [ ] **Step 2: Run it**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -k bulk -v -s`
Expected: PASS (parallel map produces 3 valid extracts) or SKIP. If gpt-oss:20b produces invalid JSON under parallelism, that's real signal — report DONE_WITH_CONCERNS with the output; do NOT weaken the assertion. (Reduce-proposal rejections from the validator are expected signal for M1c, not a smoke failure — the smoke asserts on the extract path.)

- [ ] **Step 3: Validation gate**

Run:
```bash
.venv/bin/python -m pytest tests/ -k kb -q
.venv/bin/python -m flake8 plugins/sdlc-knowledge-base/scripts/graphs/bulk_ingest_graph.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py
.venv/bin/python tools/validation/check-feature-proposal.py --branch feature/211-kb-offline-langgraph
.venv/bin/python tools/validation/check-prompt-parity.py
```
Report all results. All pass (live smoke may SKIP if Ollama absent).

- [ ] **Step 4: Commit**

```bash
git add tests/test_kb_offline_ollama_smoke.py
git commit -m "test(kb-offline): live Ollama bulk ingest smoke + M1b validation gate (#211)"
```

---

## Self-review notes

- **Addendum M1b coverage:** bounded `Send` map fan-out (Task 2) + parallel reduce-by-target one-writer (Task 3); `--parallel N` (default 16, max 64) → `max_concurrency` (Task 5, mechanism pinned in Task 1); `lock.heartbeat()` per worker (Tasks 2-3); manifest+journal stay authority + M0 commit/fencing/CAS reused verbatim; lock cleanup on error (Task 5); resume-skip preserved (Task 4); live smoke (Task 6).
- **Deferred to M1c/M3 (correctly absent):** query/select/synthesize, entailment verifier, provenance/layer, embeddings.
- **Version-drift honesty:** Task 1 pins the exact `Send`/reducer/`max_concurrency` API in the installed langgraph 1.2.4 before any production code; Tasks 2-5 adapt to what it found (incl. the chunked-rounds fallback if `max_concurrency` doesn't bound `Send`).
- **Concurrency safety:** parallel reduce writes distinct files (one writer per file), shares the run's fencing token, per-file CAS + distinct journal `run_step` — safe by the #208 model; rationale documented at the top of the plan and the module.
- **Type/name consistency:** `build_bulk_ingest_graph(backend, *, allowed_layers, checkpoint_path)`, `BulkIngestState` keys (`source_specs`, `targets`, `committed/rejected/conflicts` as `Annotated[int, add]`), `_cmd_ingest_bulk`, and the reused `_LOCKS`/`release_lock`/`step_id`/`commit_mutation` signatures all match M0/M1a.
- **Known check for execution:** confirm in Task 1 whether the `Annotated[int, add]` int-reducer works or whether counters must accumulate as lists then be summed in finalize — adapt Tasks 3/5's `out.get("committed")` accordingly.

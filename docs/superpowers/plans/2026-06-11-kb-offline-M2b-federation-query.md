# kb-offline M2b — federation query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer a question across multiple federated libraries — fan out the M1c-1 query path per library (priming non-local ones with local vocabulary), verify per-library, and merge into one result with per-claim source-library attribution and a cross-library audit trail.

**Architecture:** `query --libraries a,b,c` resolves handles via the #164 registry, then a read-only `federation_query_graph` fans out (parallel `Send`) one per-library worker (`query_one_library`: select→read→synthesize→verify), and a merge node concatenates + attributes + dedupes-identical claims (union'd source handles) and applies the publication policy with an attribution suffix. No locks/writes; RRF deferred to M3.

**Tech Stack:** Python 3.9+, Pydantic v2, langgraph 1.2.4, the project `.venv`, pytest. Spec: `docs/superpowers/specs/2026-06-11-kb-offline-M2b-federation-query-design.md`.

---

## Environment & scope

- **`.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. Lint: `.venv/bin/python -m flake8 --max-line-length=127` (graph modules use `# noqa: E402` after the offline guard; black@88 NOT enforced).
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **In scope:** `select(priming=)`, `cross_library_query` audit type, `federation.query_one_library`/`merge_answers`/`render_federated`, `federation_query_graph`, CLI `--libraries` + `_resolve_libraries` + federated `--save`.
- **Out of scope:** RRF/embedding fusion (M3); federation-aware lint (M2c); promote of a federated answer into a library (later); remote-agent library types.

## Reused APIs (read before relying; verify signatures)

- `pipeline.select(question, shelf_index_path, *, backend, known_pages, max_repairs=1) -> SelectResult` — current prompt: `base = f"{prompts.SELECT_FRAGMENT}\n\nQuestion: {question}\n\nShelf-index:\n{shelf}"`. `pipeline.synthesize(question, pages, *, backend, max_repairs=1) -> Answer` (pages = list of `{"page","content"}`).
- `entailment.verify_entailment(answer, pages: dict[str,str], *, backend) -> Answer`.
- `provenance.filter_pages(library_path, page_names, *, layer=None, min_confidence=None) -> list[str]`.
- `publication.publish(answer) -> (rendered_text, rejected_claims)` — supported→body, partial→`"… (partially supported)"`, unsupported→`rejected_claims`.
- `contracts`: `Answer(claims, rendered_text)`, `Claim(text, cited_pages: [PageRef(library, page)], evidence_spans, entailment_status, high_impact)`, `EntailmentStatus.supported|.partial|.unsupported`.
- `registry.load_global_registry(path) -> GlobalRegistry`; `registry.ProjectActivation(activated_sources=[...])`; `registry.resolve_dispatch_list(global_registry, activation, project_library_path) -> DispatchList(sources: [LibrarySource(name, type, path)], warnings, is_empty_error)`. Global registry path = `Path(os.path.expanduser("~/.sdlc/global-libraries.json"))` (the path kb-query/kb-promote skills use).
- `priming.build_priming_bundle(question, project_dir: Path) -> PrimingBundle(question, local_kb_config_excerpt: str, local_shelf_index_terms: list[str])` (a dataclass).
- `audit.AuditEvent(timestamp, event_type, query, source_handle, reason, detail)`; `audit.log_event(log_path, event)`; `audit.VALID_EVENT_TYPES` (frozenset). Timestamp = `datetime.now(timezone.utc).isoformat()` (wall-clock audit time is fine — the no-clock rule targets resume-repro values, per the M2a promote audit precedent).
- `graphs/bulk_ingest_graph.py` — copy its offline-guard + `Send` + `Annotated[list, add]` reducer + `add_conditional_edges(node, fan_fn, [allowlist])` pattern. `graphs/query_graph.py` `n_select` — the candidate-page computation (`known = {*.md} - meta`, `filter_pages`, `select`) to mirror in `query_one_library`.
- `graphs/query_graph.py` query CLI is `_cmd_query(args, backend_override)` in `kb_offline_cli.py`; `query` subparser var is `p_q`; lib seed helper in `tests/test_kb_offline_cli.py` is `_seed_lib`; ollama smoke guard is `_ollama_ready()`.

## File structure (M2b)

| File | Responsibility |
|---|---|
| `scripts/pipeline.py` (modify) | `select` gains optional `priming` param |
| `scripts/audit.py` (modify) | add `"cross_library_query"` to `VALID_EVENT_TYPES` |
| `scripts/publication.py` (modify) | factor a shared `published_line(claim, *, suffix="")` policy helper |
| `scripts/federation.py` (new) | `query_one_library`, `merge_answers`, `render_federated` |
| `scripts/graphs/federation_query_graph.py` (new) | `build_federation_query_graph` (resolve → Send → merge_publish), read-only |
| `scripts/kb_offline_cli.py` (modify) | `_resolve_libraries`; `query --libraries` federated dispatch + `--save` real handles |
| Tests | `test_kb_offline_federation.py`, `test_kb_offline_federation_graph.py`, append to `test_kb_offline_query_pipeline.py`, `test_kb_offline_cli.py`, `test_kb_offline_ollama_smoke.py`, and an audit test |

---

## Task 1: `select` priming param

**Files:** Modify `scripts/pipeline.py`; Test append to `tests/test_kb_offline_query_pipeline.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_query_pipeline.py`:
```python
def test_select_without_priming_prompt_unchanged(tmp_path):
    from sdlc_knowledge_base_scripts.priming import PrimingBundle  # noqa: F401 (import-shape check)
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    select("q", _shelf(tmp_path), backend=be, known_pages={"a.md"})   # no priming
    assert "PRIMING" not in captured["prompt"]   # byte-identical to today: no priming block


def test_select_with_priming_prepends_block(tmp_path):
    from sdlc_knowledge_base_scripts.priming import PrimingBundle
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    bundle = PrimingBundle(question="q", local_kb_config_excerpt="Brazilian semiconductor packaging",
                           local_shelf_index_terms=["wirebond", "yield"])
    select("q", _shelf(tmp_path), backend=be, known_pages={"a.md"}, priming=bundle)
    assert "PRIMING" in captured["prompt"]
    assert "Brazilian semiconductor packaging" in captured["prompt"]
    assert "wirebond" in captured["prompt"]
```
(`_shelf(tmp_path)` + `json` + `FakeBackend` + `select` are already imported/defined in this test file from M1c-1.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -k priming -v`
Expected: FAIL (`select() got an unexpected keyword argument 'priming'`).

- [ ] **Step 3: Add the `priming` param to `select`**

In `scripts/pipeline.py`, change `select` to accept `priming=None` and prepend a PRIMING block when given:
```python
def select(question, shelf_index_path, *, backend, known_pages, max_repairs: int = 1, priming=None) -> SelectResult:
    """Pick the 2-4 most relevant library pages for the question by reasoning over the
    shelf-index. Drops any returned id that is not a known page (no fabricated targets).
    When `priming` (a PrimingBundle) is given, a PRIMING block biases selection toward the
    local project's vocabulary — used for NON-local libraries in federated query."""
    shelf = Path(shelf_index_path).read_text(encoding="utf-8")
    prime_block = ""
    if priming is not None:
        terms = ", ".join(priming.local_shelf_index_terms)
        prime_block = (
            "PRIMING (interpret findings under the local project's lens; prefer pages whose "
            f"terms overlap this vocabulary):\n{priming.local_kb_config_excerpt}\n"
            f"Local terms: {terms}\n\n"
        )
    base = f"{prime_block}{prompts.SELECT_FRAGMENT}\n\nQuestion: {question}\n\nShelf-index:\n{shelf}"
    schema = _select_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            result = SelectResult.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\n" "Return valid JSON only."
            continue
        return SelectResult(page_ids=[p for p in result.page_ids if p in set(known_pages)])
    raise ValueError(f"select failed after {max_repairs} repair(s): {last_error}")
```
(When `priming is None`, `prime_block` is `""`, so `base` is byte-identical to the previous prompt — existing single-library query + the eval suite are unaffected.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -v`
Expected: all pass (priming tests + existing select tests). Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions) + `.venv/bin/python tools/validation/check-prompt-parity.py` (parity OK — SELECT_FRAGMENT unchanged) + flake8 clean on `scripts/pipeline.py tests/test_kb_offline_query_pipeline.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_query_pipeline.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): select gains optional priming param (biases non-local federation selection) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `cross_library_query` audit event type

**Files:** Modify `scripts/audit.py`; Test `tests/test_kb_offline_federation.py` (audit part) or the existing audit test

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_federation.py` (start it here; more federation tests appended in Tasks 3-4):
```python
"""Federation query tests. kb-offline M2b (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.audit import VALID_EVENT_TYPES


def test_cross_library_query_is_a_valid_event_type():
    assert "cross_library_query" in VALID_EVENT_TYPES
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -v`
Expected: FAIL (assert — type not present).

- [ ] **Step 3: Add the event type**

In `scripts/audit.py`, add `"cross_library_query"` to the `VALID_EVENT_TYPES` frozenset (alongside the existing members). Read the file to place it in the set literal.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -v` (1 passed). Then run any existing audit test (`.venv/bin/python -m pytest tests/ -k audit -q`) — no regressions. flake8 clean on `scripts/audit.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/audit.py tests/test_kb_offline_federation.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): add cross_library_query audit event type for federated query (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `federation.query_one_library`

**Files:** Create `scripts/federation.py`; Test append to `tests/test_kb_offline_federation.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_federation.py`:
```python
import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import EntailmentStatus
from sdlc_knowledge_base_scripts.federation import query_one_library


def _lib(tmp_path, name, page, body):
    lib = tmp_path / name
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
    (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
    return lib


def test_query_one_library_returns_verified_answer(tmp_path):
    lib = _lib(tmp_path, "doracorp", "dora.md", "Elite teams deploy multiple times per day.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["dora.md"]})
        return json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                       "cited_pages": [{"library": "local", "page": "dora.md"}],
                                       "evidence_spans": [{"page": "dora.md",
                                                           "text": "deploy multiple times per day"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    answer, page_ids = query_one_library(str(lib), "how often deploy?", backend=be, priming=None)
    assert page_ids == ["dora.md"]
    assert answer.claims[0].entailment_status == EntailmentStatus.supported   # verified per-library
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -k query_one -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `query_one_library`**

Create `scripts/federation.py`:
```python
"""Federated query: per-library worker + merge/attribution. kb-offline M2b (#211).
Read-only — runs the M1c-1 query pipeline per library and merges VERIFIED answers with
per-claim source-library attribution. RRF score-fusion is deferred to M3."""
from __future__ import annotations

from pathlib import Path

from .contracts import Answer, EntailmentStatus
from .entailment import verify_entailment
from .pipeline import select, synthesize
from .provenance import filter_pages

_META = {"_shelf-index.md", "log.md", "_index.md"}


def query_one_library(library_path, question, *, backend, priming, layer=None, min_confidence=None):
    """Run select->read->synthesize->verify for ONE library. Returns (verified Answer, page_ids).
    Verification is against THIS library's pages only (no cross-library collision)."""
    lib = Path(library_path)
    shelf = lib / "_shelf-index.md"
    known = {p.name for p in lib.glob("*.md") if p.name not in _META}
    candidates = filter_pages(lib, sorted(known), layer=layer, min_confidence=min_confidence)
    sel = select(question, shelf, backend=backend, known_pages=set(candidates), priming=priming)
    pages = [{"page": pid, "content": (lib / pid).read_text(encoding="utf-8")}
             for pid in sel.page_ids if (lib / pid).is_file()]
    ans = synthesize(question, pages, backend=backend)
    pages_by_name = {p["page"]: p["content"] for p in pages}
    verified = verify_entailment(ans, pages_by_name, backend=backend)
    return verified, list(sel.page_ids)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -k query_one -v`
Expected: PASS. flake8 clean on `scripts/federation.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/federation.py tests/test_kb_offline_federation.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): federation.query_one_library — per-library verified query (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `merge_answers` + `render_federated` (+ factor publication policy)

**Files:** Modify `scripts/publication.py`, `scripts/federation.py`; Test append to `tests/test_kb_offline_federation.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_federation.py`:
```python
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, PageRef, Span
from sdlc_knowledge_base_scripts.federation import merge_answers, render_federated


def _claim(text, page, status):
    c = Claim(text=text, cited_pages=[PageRef(library="local", page=page)],
              evidence_spans=[Span(page=page, text="x")])
    c.entailment_status = status
    return c


def test_merge_dedupes_identical_and_unions_handles():
    a1 = Answer(claims=[_claim("Deploy daily.", "dora.md", EntailmentStatus.supported)], rendered_text="")
    a2 = Answer(claims=[_claim("Deploy daily.", "ops.md", EntailmentStatus.supported),
                        _claim("Use canary.", "ops.md", EntailmentStatus.supported)], rendered_text="")
    merged, handle_sets = merge_answers([("dora-corp", a1), ("acme-kb", a2)])
    texts = [c.text for c in merged.claims]
    assert texts.count("Deploy daily.") == 1          # deduped
    assert set(handle_sets["Deploy daily."]) == {"dora-corp", "acme-kb"}   # union'd
    assert "Use canary." in texts                      # distinct kept
    # each merged claim's cited_pages carry the source handle (not "local")
    deploy = next(c for c in merged.claims if c.text == "Deploy daily.")
    assert {r.library for r in deploy.cited_pages} == {"dora-corp", "acme-kb"}


def test_render_federated_attributes_and_applies_policy():
    a = Answer(claims=[_claim("Deploy daily.", "dora.md", EntailmentStatus.supported),
                       _claim("Maybe canary.", "dora.md", EntailmentStatus.partial),
                       _claim("Unfounded.", "dora.md", EntailmentStatus.unsupported)], rendered_text="")
    merged, handle_sets = merge_answers([("dora-corp", a)])
    rendered, rejected = render_federated(merged, handle_sets)
    assert "Deploy daily." in rendered and "[dora-corp]" in rendered
    assert "partially supported" in rendered.lower()           # partial caveated
    assert "Unfounded." not in rendered                        # unsupported excluded
    assert any("Unfounded." in r["text"] for r in rejected)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -k "merge or render_fed" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Factor the publication policy + implement merge/render**

In `scripts/publication.py`, factor the per-claim policy into a shared helper and have `publish` use it (no behavior change):
```python
def published_line(claim, *, suffix: str = "") -> tuple[str | None, dict | None]:
    """Apply the publication policy to ONE claim. Returns (body_line, rejected_entry) where
    exactly one is non-None: supported -> (text+suffix, None); partial -> (text+' (partially
    supported)'+suffix, None); unsupported/other -> (None, {text, reason, high_impact})."""
    if claim.entailment_status == EntailmentStatus.supported:
        return (f"{claim.text}{suffix}", None)
    if claim.entailment_status == EntailmentStatus.partial:
        return (f"{claim.text} (partially supported){suffix}", None)
    return (None, {"text": claim.text, "reason": "unsupported", "high_impact": claim.high_impact})


def publish(answer: Answer) -> tuple[str, list[dict]]:
    """(unchanged behavior) supported published; partial caveated; unsupported excluded+reported."""
    lines, rejected = [], []
    for c in answer.claims:
        line, rej = published_line(c)
        if line is not None:
            lines.append(line)
        if rej is not None:
            rejected.append(rej)
    return "\n".join(lines), rejected
```
(Keep the existing `publish` tests green — behavior is identical.)

Append to `scripts/federation.py`:
```python
def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def merge_answers(per_library):
    """per_library = [(handle, verified Answer)]. Returns (merged Answer, handle_sets) where
    claims with identical normalized text dedupe to one entry whose cited_pages carry the
    union of source handles; handle_sets maps claim.text -> ordered unique source handles."""
    from .contracts import PageRef
    order, by_key, handle_sets = [], {}, {}
    for handle, ans in per_library:
        for c in ans.claims:
            key = _norm(c.text)
            handles = handle_sets.setdefault(c.text, [])
            if handle not in handles:
                handles.append(handle)
            if key not in by_key:
                merged = c.model_copy(deep=True)
                # re-attribute cited pages to the source handle (replace per-library 'local')
                merged.cited_pages = [PageRef(library=handle, page=r.page) for r in c.cited_pages]
                by_key[key] = merged
                order.append(key)
            else:
                existing = by_key[key]
                existing.cited_pages = existing.cited_pages + [
                    PageRef(library=handle, page=r.page) for r in c.cited_pages
                ]
    return Answer(claims=[by_key[k] for k in order], rendered_text=""), handle_sets


def render_federated(merged, handle_sets):
    """Apply the publication policy with a per-claim source-attribution suffix
    (e.g. '  [dora-corp, acme-kb]'). Returns (rendered_text, rejected_claims)."""
    from .publication import published_line
    lines, rejected = [], []
    for c in merged.claims:
        suffix = f"  [{', '.join(handle_sets.get(c.text, []))}]"
        line, rej = published_line(c, suffix=suffix)
        if line is not None:
            lines.append(line)
        if rej is not None:
            rejected.append(rej)
    return "\n".join(lines), rejected
```
(`Answer`/`EntailmentStatus` already imported at the top of federation.py from Task 3; ensure `published_line` reads `EntailmentStatus` — it's imported in publication.py already.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py tests/test_kb_offline_provenance.py -v`
Expected: federation merge/render tests pass + the existing publication tests (in test_kb_offline_provenance.py) still pass. Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` + flake8 clean on `scripts/publication.py scripts/federation.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/publication.py plugins/sdlc-knowledge-base/scripts/federation.py tests/test_kb_offline_federation.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): federation merge (dedupe+union attribution) + render; factor publication policy (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `federation_query_graph` (parallel Send + audit)

**Files:** Create `scripts/graphs/federation_query_graph.py`; Test `tests/test_kb_offline_federation_graph.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_federation_graph.py`:
```python
"""federation_query_graph end-to-end (FakeBackend, 2 libraries). kb-offline M2b (#211)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.audit import read_log
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.federation_query_graph import build_federation_query_graph


def _lib(tmp_path, name, page, body):
    lib = tmp_path / name
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
    (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
    return lib


def test_federation_graph_merges_two_libraries(tmp_path):
    local = _lib(tmp_path, "local", "dora.md", "Elite teams deploy multiple times per day.")
    ext = _lib(tmp_path, "acme", "ops.md", "Elite teams deploy multiple times per day.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            page = "dora.md" if "dora.md" in prompt else "ops.md"
            return json.dumps({"page_ids": [page]})
        page = "dora.md" if "dora.md" in prompt else "ops.md"
        return json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                       "cited_pages": [{"library": "local", "page": page}],
                                       "evidence_spans": [{"page": page,
                                                           "text": "deploy multiple times per day"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_federation_query_graph(be)
    out = graph.invoke(
        {"library_specs": [["local", str(local)], ["acme-kb", str(ext)]],
         "local_project_dir": str(tmp_path), "question": "how often deploy?"},
        config={"configurable": {"thread_id": "fq1"}, "max_concurrency": 2})
    # identical claim from both libraries -> deduped to one line, both handles attributed
    assert out["rendered_text"].count("Elite teams deploy multiple times per day.") == 1
    assert "local" in out["rendered_text"] and "acme-kb" in out["rendered_text"]
    assert out["queried"] == 2
    # one cross_library_query audit event for the non-local library
    events = read_log(local / ".kb-offline" / "audit.log")
    handles = {e.source_handle for e in events if e.event_type == "cross_library_query"}
    assert "acme-kb" in handles and "local" not in handles   # local access is not 'cross-library'
```
(Confirm `read_log` returns objects with `.source_handle`/`.event_type` — it does per audit.py; adapt if the accessor differs.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation_graph.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `federation_query_graph.py`**

Create `scripts/graphs/federation_query_graph.py` (mirror bulk_ingest_graph's offline guard + Send + `Annotated[list, add]`; read-only — NO lock/journal):
```python
"""Federated query graph (#211, M2b): resolve -> Send one worker per library -> merge+publish.
Read-only (query never mutates). Parallel fan-out mirrors bulk_ingest_graph; per-library
results accumulate via an Annotated[list, add] reducer. OFFLINE INTEGRITY: tracing disabled
before importing langgraph."""
from __future__ import annotations

import os

os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

from datetime import datetime, timezone  # noqa: E402
from operator import add  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Annotated, Optional, TypedDict  # noqa: E402

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.types import Send  # noqa: E402

from ..audit import AuditEvent, log_event  # noqa: E402
from ..contracts import Answer  # noqa: E402
from ..federation import merge_answers, query_one_library, render_federated  # noqa: E402
from ..priming import build_priming_bundle  # noqa: E402


class FederationState(TypedDict, total=False):
    library_specs: list          # [[handle, path], ...]; first is the local root
    local_project_dir: str
    question: str
    layer: Optional[str]
    min_confidence: Optional[str]
    per_library: Annotated[list, add]
    rendered_text: str
    rejected_claims: list
    _answer: dict
    queried: int
    deduped: int


def build_federation_query_graph(backend, *, checkpoint_path=None):
    def n_resolve(state: FederationState) -> dict:
        return {}   # resolution happens in the CLI; this node is the fan-out anchor

    def fan_query(state: FederationState):
        specs = state.get("library_specs") or []
        if not specs:
            return "merge_publish"
        local_dir = state["local_project_dir"]
        return [
            Send("query_one", {
                "handle": handle, "path": path, "question": state["question"],
                "layer": state.get("layer"), "min_confidence": state.get("min_confidence"),
                "local_project_dir": local_dir, "is_local": (i == 0), "audit_lib": specs[0][1],
            })
            for i, (handle, path) in enumerate(specs)
        ]

    def n_query_one(state) -> dict:
        priming = None
        if not state["is_local"]:
            priming = build_priming_bundle(state["question"], Path(state["local_project_dir"]))
            # audit the cross-library access (local access is not 'cross-library')
            log_event(Path(state["audit_lib"]) / ".kb-offline" / "audit.log", AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="cross_library_query", query=state["question"],
                source_handle=state["handle"], reason="federated query",
                detail={"path": state["path"]}))
        answer, page_ids = query_one_library(
            state["path"], state["question"], backend=backend, priming=priming,
            layer=state["layer"], min_confidence=state["min_confidence"])
        return {"per_library": [{"handle": state["handle"], "answer": answer.model_dump(),
                                 "page_ids": page_ids}]}

    def n_merge_publish(state: FederationState) -> dict:
        per = [(d["handle"], Answer.model_validate(d["answer"])) for d in state.get("per_library", [])]
        merged, handle_sets = merge_answers(per)
        rendered, rejected = render_federated(merged, handle_sets)
        deduped = sum(len(a.claims) for _, a in per) - len(merged.claims)
        return {"rendered_text": rendered, "rejected_claims": rejected, "_answer": merged.model_dump(),
                "queried": len(per), "deduped": deduped}

    builder = StateGraph(FederationState)
    builder.add_node("resolve", n_resolve)
    builder.add_node("query_one", n_query_one)
    builder.add_node("merge_publish", n_merge_publish)
    builder.add_edge(START, "resolve")
    builder.add_conditional_edges("resolve", fan_query, ["query_one", "merge_publish"])
    builder.add_edge("query_one", "merge_publish")
    builder.add_edge("merge_publish", END)
    import sqlite3
    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        from langgraph.checkpoint.sqlite import SqliteSaver
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()
    return builder.compile(checkpointer=saver)
```
Notes: state carries `library_specs` as `[[handle, path], ...]` (JSON-ish lists, not tuples, so the checkpointer serializes cleanly). `queried` counts libraries actually queried. Confirm `read_log` accessor names against audit.py; if `add` accumulation of `per_library` across parallel workers needs the reducer (it does — `Annotated[list, add]`), the merge node reads the accumulated list.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation_graph.py -v`
Expected: PASS (dedup to one line, both handles attributed, queried==2, one cross_library_query audit event for acme-kb only). Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` + flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/federation_query_graph.py tests/test_kb_offline_federation_graph.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): federation_query_graph — parallel Send fan-out + merge + cross-library audit (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: CLI `--libraries` + `_resolve_libraries` + federated `--save` + live smoke

**Files:** Modify `scripts/kb_offline_cli.py`; Test append to `tests/test_kb_offline_cli.py`, `tests/test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Write the failing CLI test**

Append to `tests/test_kb_offline_cli.py`:
```python
def test_cli_query_libraries_federates(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    def _seed(name, page, body):
        lib = tmp_path / name
        lib.mkdir()
        (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
        (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
        return lib
    local = _seed("local", "dora.md", "Elite teams deploy multiple times per day.")
    ext = _seed("acme", "ops.md", "Use canary deploys for safety.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["dora.md"]}) if "dora.md" in prompt else _j.dumps({"page_ids": ["ops.md"]})
        if "dora.md" in prompt:
            return _j.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                         "cited_pages": [{"library": "local", "page": "dora.md"}],
                                         "evidence_spans": [{"page": "dora.md", "text": "deploy multiple times per day"}]}],
                             "rendered_text": ""})
        return _j.dumps({"claims": [{"text": "Use canary deploys for safety.",
                                     "cited_pages": [{"library": "local", "page": "ops.md"}],
                                     "evidence_spans": [{"page": "ops.md", "text": "canary deploys for safety"}]}],
                         "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "how do teams deploy?", "--library", str(local),
                   "--libraries", "acme-kb", "--backend", "fake"],
                  backend_override=be, library_specs_override=[["local", str(local)], ["acme-kb", str(ext)]])
    assert rc == 0
    out = capsys.readouterr().out
    assert "queried 2 libraries" in out
    assert "Use canary deploys for safety." in out and "acme-kb" in out
```
NOTE: federated resolution reads `~/.sdlc/global-libraries.json` which won't exist in the test env. To keep the test hermetic, add a **test-only seam** `library_specs_override` to `cli.main(...)`/`_cmd_query` (analogous to the existing `backend_override`): when provided, it bypasses `_resolve_libraries` and uses the given specs. Implement that seam in Step 3.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k libraries -v`
Expected: FAIL (`--libraries`/`library_specs_override` unknown).

- [ ] **Step 3: Implement the CLI federated path**

In `scripts/kb_offline_cli.py`:
1. Add `_resolve_libraries`:
```python
def _resolve_libraries(local_lib: Path, handles: list[str]):
    import os
    from .registry import ProjectActivation, load_global_registry, resolve_dispatch_list
    registry = load_global_registry(Path(os.path.expanduser("~/.sdlc/global-libraries.json")))
    activation = ProjectActivation(activated_sources=handles)
    dispatch = resolve_dispatch_list(registry, activation, local_lib)
    return [[s.name, s.path] for s in dispatch.sources], dispatch.warnings
```
2. Add `--libraries` to the `query` subparser (`p_q`):
```python
    p_q.add_argument("--libraries", default=None, help="comma-separated external library handles to federate")
```
3. Thread a `library_specs_override` kwarg through `main(...)` and into `_cmd_query` (mirror how `backend_override` is threaded). In `_cmd_query`, branch to federation when `--libraries` is set (or the override is given):
```python
def _cmd_query(args, backend_override, library_specs_override=None) -> int:
    backend = _make_backend(args.backend, backend_override)
    if not args.libraries and library_specs_override is None:
        # ... existing single-library query_graph path UNCHANGED ...
        return _existing_single_library_query(args, backend)   # keep the current body
    # federated path
    from .graphs.federation_query_graph import build_federation_query_graph
    local_lib = Path(args.library)
    if library_specs_override is not None:
        specs, warnings = library_specs_override, []
    else:
        handles = [h.strip() for h in args.libraries.split(",") if h.strip()]
        specs, warnings = _resolve_libraries(local_lib, handles)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if not specs:
        print("no libraries resolved — run kb-init / check ~/.sdlc/global-libraries.json", file=sys.stderr)
        return 1
    graph = build_federation_query_graph(backend)
    out = graph.invoke(
        {"library_specs": specs, "local_project_dir": str(local_lib), "question": args.question,
         "layer": args.layer, "min_confidence": args.min_confidence},
        config={"configurable": {"thread_id": "federated-query"}, "max_concurrency": 8})
    print(out.get("rendered_text", ""))
    rejected = out.get("rejected_claims", [])
    if rejected:
        print(f"\n[{len(rejected)} claim(s) excluded as unsupported]", file=sys.stderr)
    print(f"\nqueried {out.get('queried', 0)} libraries "
          f"({sum(len(...)) if False else len(out.get('_answer', {}).get('claims', []))} claims, "
          f"{out.get('deduped', 0)} deduped)")
    if args.save:
        from .answers import save_answer
        verified = Answer.model_validate(out["_answer"])
        ref = save_answer(args.library, args.question, verified,
                          libraries=[h for h, _ in specs], page_ids=[])
        print(f"saved: {ref}")
    return 0
```
Refactor cleanly: extract the existing single-library body into a helper (e.g. `_query_single`) so `_cmd_query` dispatches single-vs-federated without duplicating. Keep the single-library output + `--save` (which records `["local"]`) exactly as today; the federated `--save` records the resolved handles. Fix the summary line to a clean form, e.g.:
```python
    claims_n = len(out.get("_answer", {}).get("claims", []))
    print(f"\nqueried {out.get('queried', 0)} libraries ({claims_n} claims, {out.get('deduped', 0)} deduped)")
```
4. Thread `library_specs_override` in `main(...)`'s signature (`def main(argv=None, *, backend_override=None, allowed_layers=None, library_specs_override=None)`) and pass it to `_cmd_query` in the dispatch.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k "query or libraries" -v`
Expected: PASS (federated test + existing single-library query tests). Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions) + flake8 clean + `.venv/bin/python tools/validation/check-prompt-parity.py`.

- [ ] **Step 5: Append the live multi-library Ollama smoke** to `tests/test_kb_offline_ollama_smoke.py`:
```python
@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_federation(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.federation_query_graph import build_federation_query_graph

    def _seed(name, page, body):
        lib = tmp_path / name
        lib.mkdir()
        (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
        (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
        return lib
    local = _seed("local", "dora.md", "Elite teams deploy multiple times per day.")
    _seed("acme", "ops.md", "Canary deploys reduce blast radius.")
    be = OllamaBackend(model="gpt-oss:20b", options={"temperature": 0, "seed": 7, "num_ctx": 8192})
    graph = build_federation_query_graph(be)
    out = graph.invoke(
        {"library_specs": [["local", str(local)], ["acme-kb", str(tmp_path / "acme")]],
         "local_project_dir": str(tmp_path), "question": "How do teams deploy safely?"},
        config={"configurable": {"thread_id": "fq-live"}, "max_concurrency": 2})
    assert "rendered_text" in out and out["queried"] == 2
```

- [ ] **Step 6: Full gate**

```bash
.venv/bin/python -m pytest tests/ -k "kb and not live" -q
.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_offline_federation.py tests/test_kb_offline_federation_graph.py
.venv/bin/python tools/validation/check-prompt-parity.py
```
All green / clean / parity OK.

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py tests/test_kb_offline_ollama_smoke.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): CLI query --libraries federated dispatch + federated --save handles + live smoke (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** §1 resolution → Task 6 (`_resolve_libraries`, reuses resolve_dispatch_list); §2 priming → Task 1 (`select(priming=)`); §3 worker → Task 3 (`query_one_library`, verify-per-library); §4 merge+attribution → Task 4 (`merge_answers` dedupe+union, `render_federated`, factored `published_line`); §5 graph+audit → Task 5 (`federation_query_graph` Send + `cross_library_query` events) + Task 2 (event type); §6 CLI+save+tests → Task 6 (`--libraries`, federated `--save` real handles, live smoke). Decisions log 1-7 all covered.
- **Type/name consistency:** `select(..., priming=None)`; `query_one_library(library_path, question, *, backend, priming, layer, min_confidence) -> (Answer, page_ids)`; `merge_answers(per_library) -> (Answer, handle_sets)`; `render_federated(merged, handle_sets) -> (str, list)`; `published_line(claim, *, suffix="") -> (str|None, dict|None)`; `build_federation_query_graph(backend, *, checkpoint_path=None)`; `FederationState` keys; `_resolve_libraries(local_lib, handles) -> (specs, warnings)`; `library_specs_override` test seam — consistent across tasks.
- **Read-only preserved:** federation_query_graph has no lock/journal/fencing; the only writes are audit-log appends (which the in-agent federation also does). Single-library `query` path is untouched (Task 6 dispatches to the existing body).
- **Verification isolation:** each library verifies against its own pages inside `query_one_library` BEFORE merge — no cross-library page-name collision. The merge re-attributes cited_pages to handles but never re-grades.
- **Known verification points (flag during implementation):** `read_log` accessor field names (`.source_handle`/`.event_type`); `LibrarySource.path` is a str (Path() it); the exact `p_q` subparser var + the single-library `_cmd_query` body to extract; that `Annotated[list, add]` correctly accumulates `per_library` across parallel workers (the bulk graph proves the int-reducer; list-reducer is the same mechanism). The summary-line f-string in Task 6 Step 3 has a deliberately-broken placeholder (`sum(len(...))`) — use the clean `claims_n` form shown immediately after it.
- **No silent caps:** dispatch warnings are printed; the deduped count is surfaced in the summary line; rejected (unsupported) claims are reported to stderr.

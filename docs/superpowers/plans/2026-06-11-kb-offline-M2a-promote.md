# kb-offline M2a — compounding `promote` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an operator file a verified query answer back into the library as a new (or extended) curated page, through the same deterministic mutation machinery that governs ingest.

**Architecture:** `query --save` persists the verified `Answer`+provenance to `.kb-offline/answers/<ref>.json`. `promote <ref>` runs a `promote_graph` (mirrors `ingest_graph`): load the saved answer → draft page body from the `supported` claims (backend) → assemble a `MutationProposal` with deterministic frontmatter → `validate_proposal` + `commit_mutation` (lock/fencing/CAS/journal) → `recover` + shelf rebuild + audit event. Promoted pages are marked `provenance: promoted`.

**Tech Stack:** Python 3.9+, Pydantic v2, langgraph 1.2.4, the project `.venv`, pytest. Spec: `docs/superpowers/specs/2026-06-11-kb-offline-M2a-promote-design.md`.

---

## Environment & scope

- **`.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. Lint gate: `.venv/bin/python -m flake8 --max-line-length=127` (graph modules use `# noqa: E402` only on imports after the `os.environ.setdefault` offline guard; black@88 NOT enforced).
- Every commit ends with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **In scope:** answer persistence (`query --save`), `pipeline.promote`, `promote_graph`, CLI `promote`, deterministic derived frontmatter, promotion-mutation-validation safety tests, live promote smoke.
- **Out of scope (do NOT build):** federation/multi-library (M2b), federation-aware lint (M2c), embeddings (M3), auto/unattended promotion.

## Reused APIs (already on the branch — do not reimplement)

- `contracts`: `Answer(claims: list[Claim], rendered_text: str)`; `Claim(text, cited_pages: list[PageRef(library,page)], evidence_spans: list[Span(page,text)], entailment_status: EntailmentStatus|None, high_impact: bool)`; `EntailmentStatus.supported|.partial|.unsupported`; `MutationProposal(target_file, action: MutationAction, frontmatter: dict, body: str, citations: list[str], cross_refs: list[str], expected_hash: str|None)`; `MutationAction.create|.extend`.
- `mutation`: `validate_proposal(proposal, library_path, *, allowed_layers, known_citations) -> list[str]` (empty = valid; enforces bare target_file, in-library, required frontmatter keys incl. `layer`, citations resolve, create→expected_hash None, extend→expected_hash required); `commit_mutation(proposal, library_path, fencing_token, lock, run_step) -> Path` (journal→fence→CAS→write→journal; CAS for extend compares `content_hash(target.read_text())` against `proposal.expected_hash`); `recover(library_path) -> dict`; exceptions `CommitConflict`, `FenceError`.
- `resume`: `content_hash(text) -> sha256 hex`; `LibraryLock(lib)` with `.acquire()->token`, `.current_token()`, `.heartbeat()`, `.release()`; `RunRegistry(lib)` with `.start_run(timestamp, fingerprint)->run_id`, `.set_state(run_id, state)`, `.exists(run_id)`; `step_id(run_id, stage, item) -> f"{run_id}:{stage}:{item}"`; `config_hash(dict)`.
- `durability.atomic_write_text(path, text)` (fsync file+dir).
- `provenance.page_frontmatter(library_path, page_name) -> dict` (parsed YAML frontmatter, {} if absent).
- `graphs/ingest_graph.py` — copy its structure for `promote_graph`: the `os.environ.setdefault("LANGSMITH_TRACING"/"LANGCHAIN_TRACING_V2","false")` offline guard before langgraph imports (`# noqa: E402` after), `SqliteSaver(sqlite3.connect(path, check_same_thread=False))` / `MemorySaver`, the module-level `_LOCKS: dict[str, LibraryLock]` + `release_lock(run_id)` seam, `RetryPolicy` import from `langgraph.types`.
- `graphs/query_graph.py` — `n_verify_publish` currently returns `{"rendered_text", "rejected_claims"}`; you will add `_answer` to that return.
- `pipeline.reduce_to_proposal` — the template for `pipeline.promote` (prompt + validate→repair→fail ladder).
- `prompts.py` — holds canonical `*_FRAGMENT` constants (`SELECT_FRAGMENT`, `SYNTHESIZE_FRAGMENT`, `REDUCE_FRAGMENT`, …); `tools/validation/check-prompt-parity.py` tracks managed blocks vs these constants.
- `audit.py`: `AuditEvent`, `log_event(log_path, event)`.

## File structure (M2a)

| File | Responsibility |
|---|---|
| `scripts/answers.py` (new) | `SavedAnswer`, `compute_ref`, `save_answer`, `load_answer` |
| `scripts/prompts.py` (modify) | add `PROMOTE_FRAGMENT` |
| `scripts/pipeline.py` (modify) | add `promote(...)` body-drafting op |
| `scripts/graphs/query_graph.py` (modify) | `n_verify_publish` also returns `_answer` (verified Answer dict) |
| `scripts/graphs/promote_graph.py` (new) | `build_promote_graph` (load→draft→commit→finalize) |
| `scripts/kb_offline_cli.py` (modify) | `query --save`; new `promote` subcommand |
| Tests | `test_kb_offline_answers.py`, `test_kb_offline_promote_pipeline.py`, `test_kb_offline_promote_graph.py`, append to `test_kb_offline_cli.py` + `test_kb_offline_ollama_smoke.py` |

---

## Task 1: `answers.py` — SavedAnswer + persistence

**Files:** Create `scripts/answers.py`; Test `tests/test_kb_offline_answers.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_answers.py`:
```python
"""Saved-answer persistence tests. kb-offline M2a (#211)."""
from __future__ import annotations

import pytest

from sdlc_knowledge_base_scripts.answers import (
    SavedAnswer,
    compute_ref,
    load_answer,
    save_answer,
)
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span


def _answer():
    c = Claim(text="Elite teams deploy multiple times per day.",
              cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="multiple times per day")])
    c.entailment_status = EntailmentStatus.supported
    return Answer(claims=[c], rendered_text="Elite teams deploy multiple times per day.")


def test_compute_ref_is_deterministic_and_short():
    r1 = compute_ref("how often deploy?", "Elite teams deploy multiple times per day.")
    r2 = compute_ref("how often deploy?", "Elite teams deploy multiple times per day.")
    r3 = compute_ref("how often deploy?", "different text")
    assert r1 == r2 and r1 != r3
    assert r1.isalnum() and len(r1) <= 16


def test_save_then_load_round_trip(tmp_path):
    ref = save_answer(str(tmp_path), "how often deploy?", _answer(),
                      libraries=["local"], page_ids=["dora.md"])
    saved = load_answer(str(tmp_path), ref)
    assert isinstance(saved, SavedAnswer)
    assert saved.ref == ref
    assert saved.question == "how often deploy?"
    assert saved.page_ids == ["dora.md"]
    assert saved.answer.claims[0].entailment_status == EntailmentStatus.supported
    assert (tmp_path / ".kb-offline" / "answers" / f"{ref}.json").is_file()


def test_load_missing_ref_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_answer(str(tmp_path), "deadbeef")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_answers.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `answers.py`**

Create `scripts/answers.py`:
```python
"""Saved query answers — the promote entry point (#211, M2a). `query --save` persists a
verified Answer here; `promote <ref>` loads it. Read/write only under .kb-offline/answers/."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .contracts import Answer
from .durability import atomic_write_text
from .resume import content_hash


class SavedAnswer(BaseModel):
    ref: str
    question: str
    libraries: list[str] = Field(default_factory=list)
    page_ids: list[str] = Field(default_factory=list)
    answer: Answer
    rendered_text: str = ""


def compute_ref(question: str, rendered_text: str) -> str:
    """Deterministic short id (no clock dependency) for a saved answer."""
    return content_hash(f"{question}\x00{rendered_text}")[:16]


def _answers_dir(library_path) -> Path:
    return Path(library_path) / ".kb-offline" / "answers"


def save_answer(library_path, question: str, answer: Answer, *, libraries, page_ids) -> str:
    """Persist a verified Answer + provenance; return its ref."""
    ref = compute_ref(question, answer.rendered_text)
    saved = SavedAnswer(ref=ref, question=question, libraries=list(libraries),
                        page_ids=list(page_ids), answer=answer, rendered_text=answer.rendered_text)
    d = _answers_dir(library_path)
    d.mkdir(parents=True, exist_ok=True)
    atomic_write_text(d / f"{ref}.json", saved.model_dump_json(indent=2))
    return ref


def load_answer(library_path, ref: str) -> SavedAnswer:
    path = _answers_dir(library_path) / f"{ref}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no saved answer with ref {ref!r} under {_answers_dir(library_path)}")
    return SavedAnswer.model_validate_json(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_answers.py -v`
Expected: 3 passed. Then flake8 clean on `scripts/answers.py tests/test_kb_offline_answers.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/answers.py tests/test_kb_offline_answers.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): SavedAnswer persistence (compute_ref/save/load) for promote (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: query graph `_answer` output + CLI `query --save`

**Files:** Modify `scripts/graphs/query_graph.py`, `scripts/kb_offline_cli.py`; Test append to `tests/test_kb_offline_query_graph.py` + `tests/test_kb_offline_cli.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_query_graph.py`:
```python
def test_query_graph_returns_verified_answer_dict(tmp_path):
    lib = _lib(tmp_path)   # existing helper: shelf + a.md with "cost fell 30% over two years"

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [{"text": "Cost fell 30%.",
                                       "cited_pages": [{"library": "local", "page": "a.md"}],
                                       "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke({"library_path": str(lib), "question": "what about cost?"},
                       config={"configurable": {"thread_id": "qa1"}})
    assert "_answer" in out
    assert out["_answer"]["claims"][0]["entailment_status"] == "supported"
    assert out["_answer"]["claims"][0]["text"] == "Cost fell 30%."
```

Append to `tests/test_kb_offline_cli.py` (reuse the file's existing `_seed_lib`/helpers — adapt the name to the real one in that file):
```python
def test_cli_query_save_persists_ref(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.answers import load_answer
    lib = _seed_lib(tmp_path)
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\ncost fell 30%\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["a.md"]})
        return _j.dumps({"claims": [{"text": "Cost fell 30%.",
                                     "cited_pages": [{"library": "local", "page": "a.md"}],
                                     "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
                         "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "what about cost?", "--library", str(lib), "--backend", "fake", "--save"],
                  backend_override=be)
    assert rc == 0
    out = capsys.readouterr().out
    assert "saved:" in out
    ref = out.split("saved:")[1].split()[0].strip()
    saved = load_answer(str(lib), ref)               # the ref is loadable
    assert saved.answer.claims[0].text == "Cost fell 30%."
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py -k verified_answer tests/test_kb_offline_cli.py -k query_save -v`
Expected: FAIL (`_answer` not in out; `--save` unknown arg).

- [ ] **Step 3: Add `_answer` to the query graph**

In `scripts/graphs/query_graph.py`, add `_answer: dict` to the `QueryState` TypedDict, and change `n_verify_publish` to also return the verified answer dict:
```python
    def n_verify_publish(state: QueryState) -> dict:
        ans = Answer.model_validate(state["_synth"])
        pages_by_name = {p["page"]: p["content"] for p in state["pages"]}
        verified = verify_entailment(ans, pages_by_name, backend=backend)
        rendered, rejected = publish(verified)
        return {"rendered_text": rendered, "rejected_claims": rejected,
                "_answer": verified.model_dump()}
```
(Additive only — the read-only guarantee is unchanged; no library writes occur in a query.)

- [ ] **Step 4: Add `--save` to the CLI `query`**

In `scripts/kb_offline_cli.py`, add `--save` to the `query` subparser:
```python
    p_query.add_argument("--save", action="store_true", help="persist the verified answer; print its ref")
```
And in `_cmd_query`, after `out = graph.invoke(...)`, before/after printing rendered_text, persist when `--save`:
```python
    if args.save:
        from .answers import save_answer
        from .contracts import Answer
        verified = Answer.model_validate(out["_answer"])
        ref = save_answer(args.library, args.question, verified,
                          libraries=["local"], page_ids=list(out.get("page_ids", [])))
        print(f"saved: {ref}")
```
(Place the `saved:` print so it appears on stdout regardless of whether rendered_text is empty.)

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py tests/test_kb_offline_cli.py -v`
Expected: all pass. Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions) + flake8 clean on the two modified source files.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_query_graph.py tests/test_kb_offline_cli.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): query --save persists the verified answer for promote (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `PROMOTE_FRAGMENT` + `pipeline.promote`

**Files:** Modify `scripts/prompts.py`, `scripts/pipeline.py`; Test `tests/test_kb_offline_promote_pipeline.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_promote_pipeline.py`:
```python
"""promote body-drafting op tests. kb-offline M2a (#211)."""
from __future__ import annotations

import json

import pytest

from sdlc_knowledge_base_scripts.answers import SavedAnswer
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.pipeline import promote


def _saved(*statuses):
    claims = []
    for i, st in enumerate(statuses):
        c = Claim(text=f"claim {i}", cited_pages=[PageRef(library="local", page="a.md")],
                  evidence_spans=[Span(page="a.md", text=f"span {i}")])
        c.entailment_status = st
        claims.append(c)
    ans = Answer(claims=claims, rendered_text="rendered")
    return SavedAnswer(ref="r1", question="q?", libraries=["local"], page_ids=["a.md"],
                       answer=ans, rendered_text="rendered")


def test_promote_drafts_body_from_supported_claims_only():
    saved = _saved(EntailmentStatus.supported, EntailmentStatus.partial, EntailmentStatus.unsupported)
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"body": "# Title\n\nClaim 0 is grounded."})
    be = FakeBackend()
    be.generate = gen
    body = promote(saved, target_file="topic.md", action="create", existing_content=None, backend=be)
    assert body == "# Title\n\nClaim 0 is grounded."
    # only the supported claim's text reaches the prompt
    assert "claim 0" in captured["prompt"]
    assert "claim 1" not in captured["prompt"] and "claim 2" not in captured["prompt"]


def test_promote_zero_supported_raises():
    saved = _saved(EntailmentStatus.partial, EntailmentStatus.unsupported)
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"body": "x"})
    with pytest.raises(ValueError, match="no supported claims"):
        promote(saved, target_file="topic.md", action="create", existing_content=None, backend=be)


def test_promote_repairs_then_fails_on_invalid_json():
    saved = _saved(EntailmentStatus.supported)
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: "not json"
    with pytest.raises(ValueError, match="promote failed"):
        promote(saved, target_file="t.md", action="create", existing_content=None, backend=be, max_repairs=1)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_promote_pipeline.py -v`
Expected: FAIL (ImportError: promote).

- [ ] **Step 3: Add `PROMOTE_FRAGMENT` + `promote`**

In `scripts/prompts.py`, add a constant (match the style of the existing `*_FRAGMENT` constants):
```python
PROMOTE_FRAGMENT = (
    "You are writing a single curated knowledge-base page from a set of VERIFIED claims "
    "(each already grounded in cited source pages). Write coherent, well-structured Markdown "
    "body prose that states these claims faithfully and cites nothing beyond the given sources. "
    "Do NOT invent facts, statistics, or citations. Return ONLY a JSON object: {\"body\": \"<markdown>\"}."
)
```

In `scripts/pipeline.py`, add (alongside the other ops; reuse the existing `prompts`, `json`, `ValidationError` imports):
```python
def _promote_body_schema() -> dict:
    return {"type": "object", "properties": {"body": {"type": "string"}}, "required": ["body"]}


def promote(saved, *, target_file, action, existing_content, backend, max_repairs: int = 1) -> str:
    """Draft page BODY prose from the saved answer's `supported` claims ONLY. Returns the body
    string (the graph assembles the typed MutationProposal + deterministic frontmatter). Raises
    ValueError if there are zero supported claims, or if the model output stays invalid after
    repairs."""
    from .contracts import EntailmentStatus
    supported = [c for c in saved.answer.claims if c.entailment_status == EntailmentStatus.supported]
    if not supported:
        raise ValueError("promote: no supported claims to promote")
    claims_block = "\n".join(
        f"- {c.text}  [sources: {', '.join(r.page for r in c.cited_pages)}]" for c in supported
    )
    base = (f"{prompts.PROMOTE_FRAGMENT}\n\nQuestion: {saved.question}\n\n"
            f"Verified claims:\n{claims_block}")
    if action == "extend":
        base += f"\n\nExisting page content to extend (preserve it, append coherently):\n{existing_content or ''}"
    schema = _promote_body_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            data = json.loads(raw)
            body = data["body"]
            if not isinstance(body, str) or not body.strip():
                raise ValueError("empty body")
            return body
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\nReturn valid JSON only."
    raise ValueError(f"promote failed after {max_repairs} repair(s): {last_error}")
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_promote_pipeline.py -v`
Expected: 3 passed. Then `.venv/bin/python tools/validation/check-prompt-parity.py` (parity OK — the new constant has no managed block to drift) + flake8 clean on `scripts/prompts.py scripts/pipeline.py tests/test_kb_offline_promote_pipeline.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/prompts.py plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_promote_pipeline.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): promote pipeline op drafts body from supported claims (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `promote_graph` (load → draft → commit → finalize)

**Files:** Create `scripts/graphs/promote_graph.py`; Test `tests/test_kb_offline_promote_graph.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_promote_graph.py`:
```python
"""promote_graph end-to-end tests (FakeBackend). kb-offline M2a (#211)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.answers import save_answer
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.graphs.promote_graph import build_promote_graph
from sdlc_knowledge_base_scripts.provenance import page_frontmatter


def _lib(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: medium\n---\n# DORA\n"
                                 "Elite teams deploy multiple times per day.\n")
    return lib


def _save_supported(lib):
    c = Claim(text="Elite teams deploy multiple times per day.",
              cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="deploy multiple times per day")])
    c.entailment_status = EntailmentStatus.supported
    ans = Answer(claims=[c], rendered_text="Elite teams deploy multiple times per day.")
    return save_answer(str(lib), "how often do elite teams deploy?", ans,
                       libraries=["local"], page_ids=["dora.md"])


def _draft_backend():
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"body": "# Deploy Frequency\n\nElite teams deploy multiple times per day."})
    return be


def test_promote_graph_creates_marked_page(tmp_path):
    lib = _lib(tmp_path)
    ref = _save_supported(lib)
    graph = build_promote_graph(_draft_backend())
    out = graph.invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "deploy-frequency.md",
         "action": "create", "layer": None, "confidence": None, "run_id": "promote-1"},
        config={"configurable": {"thread_id": "promote-1"}})
    assert out["committed"] == 1
    page = lib / "deploy-frequency.md"
    assert page.is_file()
    fm = page_frontmatter(str(lib), "deploy-frequency.md")
    assert fm["provenance"] == "promoted"
    assert fm["derived_from"] == ref
    assert fm["sources"] == ["dora.md"]
    assert fm["confidence"] == "medium"   # min(source confidences) = medium (dora.md)
    assert fm["layer"] == "evidence"      # modal source layer
    # shelf-index rebuilt to include the new page
    assert "deploy-frequency.md" in (lib / "_shelf-index.md").read_text()


def test_promote_graph_zero_supported_is_graceful(tmp_path):
    lib = _lib(tmp_path)
    # save an answer with only an unsupported claim
    c = Claim(text="x", cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="absent text")])
    c.entailment_status = EntailmentStatus.unsupported
    ref = save_answer(str(lib), "q?", Answer(claims=[c], rendered_text="x"),
                      libraries=["local"], page_ids=["dora.md"])
    graph = build_promote_graph(_draft_backend())
    out = graph.invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "x.md", "action": "create",
         "layer": None, "confidence": None, "run_id": "promote-2"},
        config={"configurable": {"thread_id": "promote-2"}})
    assert out["committed"] == 0 and out.get("failed")
    assert not (lib / "x.md").exists()   # no write on a zero-supported promote
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_promote_graph.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `promote_graph.py`**

Create `scripts/graphs/promote_graph.py` (mirror `ingest_graph.py`'s guard/lock/release pattern — open `ingest_graph.py` and copy the offline-guard import block, the `_LOCKS`/`release_lock` seam, and the SqliteSaver/MemorySaver compile tail VERBATIM, adapting the nodes):
```python
"""Promote graph (#211, M2a): load saved answer -> draft body -> validate+commit (lock/
fencing/CAS/journal) -> finalize (recover + shelf rebuild + audit). Mirrors ingest_graph
for run-lifecycle/journal/checkpoint traceability. Reuses M0 mutation machinery verbatim."""
from __future__ import annotations

import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Optional, TypedDict

os.environ.setdefault("LANGSMITH_TRACING", "false")  # offline integrity
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402

from ..answers import load_answer  # noqa: E402
from ..audit import AuditEvent, log_event  # noqa: E402
from ..build_shelf_index import build_shelf_index  # noqa: E402
from ..contracts import EntailmentStatus, MutationAction, MutationProposal  # noqa: E402
from ..mutation import CommitConflict, FenceError, commit_mutation, recover, validate_proposal  # noqa: E402
from ..pipeline import promote  # noqa: E402
from ..provenance import page_frontmatter  # noqa: E402
from ..resume import LibraryLock, content_hash, step_id  # noqa: E402

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
_LOCKS: dict[str, LibraryLock] = {}


def release_lock(run_id: str) -> None:
    lock = _LOCKS.pop(run_id, None)
    if lock is not None:
        lock.release()


class PromoteState(TypedDict, total=False):
    library_path: str
    ref: str
    target_file: str
    action: str
    layer: Optional[str]
    confidence: Optional[str]
    run_id: str
    # derived
    body: str
    frontmatter: dict
    citations: list
    promoted: int
    dropped: int
    dropped_ids: list
    committed: int
    rejected: int
    conflicts: int
    failed: bool


def _derive_frontmatter(lib: Path, source_pages: list, *, layer, confidence) -> dict:
    """layer = explicit or modal source layer; confidence = explicit or MIN of source
    confidences (a synthesis is no more confident than its weakest grounded source)."""
    layers, confs = [], []
    for p in source_pages:
        fm = page_frontmatter(str(lib), p)
        if fm.get("layer"):
            layers.append(fm["layer"])
        if fm.get("confidence") in _CONFIDENCE_RANK:
            confs.append(fm["confidence"])
    modal_layer = Counter(layers).most_common(1)[0][0] if layers else "domain"
    min_conf = min(confs, key=lambda c: _CONFIDENCE_RANK[c]) if confs else "low"
    return {"layer": layer or modal_layer, "confidence": confidence or min_conf}


def build_promote_graph(backend, *, checkpoint_path=None, allowed_layers=None):
    allowed_layers = allowed_layers or ["methodology", "evidence", "domain", "development"]

    def n_load(state: PromoteState) -> dict:
        lib = Path(state["library_path"])
        _LOCKS[state["run_id"]] = LibraryLock(lib)
        saved = load_answer(str(lib), state["ref"])
        supported = [c for c in saved.answer.claims if c.entailment_status == EntailmentStatus.supported]
        dropped = [c for c in saved.answer.claims if c.entailment_status != EntailmentStatus.supported]
        source_pages = sorted({r.page for c in supported for r in c.cited_pages})
        return {"promoted": len(supported), "dropped": len(dropped),
                "dropped_ids": [c.text for c in dropped], "citations": source_pages,
                "_source_pages": source_pages, "failed": not supported}

    def n_draft(state: PromoteState) -> dict:
        if state.get("failed"):
            return {}
        lib = Path(state["library_path"])
        saved = load_answer(str(lib), state["ref"])
        tfile = state["target_file"]
        existing = (lib / tfile).read_text() if (lib / tfile).exists() else None
        body = promote(saved, target_file=tfile, action=state["action"],
                       existing_content=existing, backend=backend)
        fm = _derive_frontmatter(lib, state["citations"], layer=state.get("layer"),
                                 confidence=state.get("confidence"))
        fm.update({"sources": state["citations"], "provenance": "promoted", "derived_from": state["ref"]})
        return {"body": body, "frontmatter": fm}

    def n_commit(state: PromoteState) -> dict:
        if state.get("failed"):
            return {"committed": 0, "rejected": 0, "conflicts": 0}
        lib = Path(state["library_path"])
        tfile = state["target_file"]
        action = MutationAction.create if state["action"] == "create" else MutationAction.extend
        expected = content_hash((lib / tfile).read_text()) if action == MutationAction.extend and (lib / tfile).exists() else None
        proposal = MutationProposal(target_file=tfile, action=action, frontmatter=state["frontmatter"],
                                    body=state["body"], citations=list(state["citations"]),
                                    cross_refs=[], expected_hash=expected)
        errors = validate_proposal(proposal, library_path=lib, allowed_layers=allowed_layers,
                                   known_citations=set(state["citations"]))
        if errors:
            import sys
            print(f"REJECTED {tfile}: {errors}", file=sys.stderr)
            return {"committed": 0, "rejected": 1, "conflicts": 0}
        lock = _LOCKS[state["run_id"]]
        token = lock.acquire()
        try:
            commit_mutation(proposal, library_path=lib, fencing_token=token, lock=lock,
                            run_step=step_id(state["run_id"], "promote", tfile))
            return {"committed": 1, "rejected": 0, "conflicts": 0}
        except (CommitConflict, FenceError) as exc:
            import sys
            print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
            return {"committed": 0, "rejected": 0, "conflicts": 1}

    def n_finalize(state: PromoteState) -> dict:
        lib = Path(state["library_path"])
        report = recover(str(lib))
        build_shelf_index(str(lib))
        log_event(lib / ".kb-offline" / "audit.log", AuditEvent(
            operation="promote",
            detail={"ref": state["ref"], "target_file": state.get("target_file"),
                    "action": state.get("action"), "promoted": state.get("promoted", 0),
                    "dropped": state.get("dropped", 0), "dropped_ids": state.get("dropped_ids", [])},
        ))
        release_lock(state["run_id"])
        return {"reindexed": report.get("reindexed")}

    builder = StateGraph(PromoteState)
    builder.add_node("load", n_load)
    builder.add_node("draft", n_draft)
    builder.add_node("commit", n_commit)
    builder.add_node("finalize", n_finalize)
    builder.add_edge(START, "load")
    builder.add_edge("load", "draft")
    builder.add_edge("draft", "commit")
    builder.add_edge("commit", "finalize")
    builder.add_edge("finalize", END)
    if checkpoint_path is not None:
        saver = SqliteSaver(sqlite3.connect(str(checkpoint_path), check_same_thread=False))
    else:
        saver = MemorySaver()
    return builder.compile(checkpointer=saver)
```
IMPORTANT verification while implementing:
- Open `scripts/build_shelf_index.py` and confirm the function name + call signature (`build_shelf_index(library_path)`); adapt the call if it differs (e.g. takes a Path, or returns something). Open `scripts/audit.py` and confirm `AuditEvent`'s real field names (the draft uses `operation`/`detail` — match the ACTUAL dataclass/model fields; if they differ, e.g. `event_type`/`payload`/a required `timestamp`, adapt). Open `scripts/mutation.py` `recover` return keys and confirm `reindexed` exists (adapt the finalize return if not). These three are the most likely drift points — verify against the real modules, do not guess.
- Keep `_source_pages` out of the persisted state if the checkpointer rejects unknown keys; it's only used within `n_load`'s return — if it causes a TypedDict issue, drop it (it's redundant with `citations`).

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_promote_graph.py -v`
Expected: 2 passed. Fix any audit/shelf/recover signature drift surfaced here.

- [ ] **Step 5: Add the promotion-mutation-validation safety test**

Append to `tests/test_kb_offline_promote_graph.py` — prove the validator blocks an out-of-library / ungrounded promote (the M2a eval-gate slice):
```python
def test_promote_graph_rejects_out_of_library_target(tmp_path):
    lib = _lib(tmp_path)
    ref = _save_supported(lib)
    graph = build_promote_graph(_draft_backend())
    out = graph.invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "../escape.md",
         "action": "create", "layer": None, "confidence": None, "run_id": "promote-3"},
        config={"configurable": {"thread_id": "promote-3"}})
    assert out["committed"] == 0 and out["rejected"] == 1
    assert not (tmp_path / "escape.md").exists()
```

- [ ] **Step 6: Run + commit**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_promote_graph.py -v` (3 passed); `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions); flake8 clean on `scripts/graphs/promote_graph.py tests/test_kb_offline_promote_graph.py`.
```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/promote_graph.py tests/test_kb_offline_promote_graph.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): promote_graph — load/draft/commit/finalize with derived frontmatter + audit (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: CLI `promote` + live smoke + gate

**Files:** Modify `scripts/kb_offline_cli.py`; Test append to `tests/test_kb_offline_cli.py`, `tests/test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Write the failing CLI test**

Append to `tests/test_kb_offline_cli.py`:
```python
def test_cli_promote_creates_page(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.answers import save_answer
    from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
    lib = _seed_lib(tmp_path)
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# DORA\n"
                                 "Elite teams deploy multiple times per day.\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    c = Claim(text="Elite teams deploy multiple times per day.",
              cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="deploy multiple times per day")])
    c.entailment_status = EntailmentStatus.supported
    ref = save_answer(str(lib), "how often deploy?", Answer(claims=[c], rendered_text="..."),
                      libraries=["local"], page_ids=["dora.md"])

    be = FakeBackend()
    be.generate = lambda prompt, schema=None: _j.dumps({"body": "# Deploy\n\nElite teams deploy multiple times per day."})
    rc = cli.main(["promote", ref, "--new", "deploy", "--library", str(lib),
                   "--backend", "fake", "--timestamp", "20260611T000000Z"], backend_override=be)
    assert rc == 0
    assert (lib / "deploy.md").is_file()
    assert "promoted 1" in capsys.readouterr().out
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k promote -v`
Expected: FAIL (`invalid choice: 'promote'`).

- [ ] **Step 3: Implement the CLI `promote` subcommand**

In `scripts/kb_offline_cli.py`, add `_cmd_promote`:
```python
def _cmd_promote(args: argparse.Namespace, backend_override) -> int:
    from .graphs.promote_graph import build_promote_graph, release_lock
    from .resume import RunRegistry, config_hash
    lib = Path(args.library)
    backend = _make_backend(args.backend, backend_override)
    if args.new and args.into:
        raise SystemExit("promote: pass only one of --new / --into")
    if args.into:
        target_file, action = args.into, "extend"
        if not (lib / target_file).is_file():
            raise SystemExit(f"promote --into: page {target_file!r} does not exist")
    else:
        slug = args.new or _slugify(args.ref)   # default slug from ref; --new gives an explicit slug
        target_file, action = f"{slug}.md" if not slug.endswith('.md') else slug, "create"
    reg = RunRegistry(lib)
    fingerprint = {"operation": "promote", "config": config_hash({"ref": args.ref, "target": target_file})}
    run_id = reg.start_run(args.timestamp, fingerprint)
    checkpoint = lib / ".kb-offline" / "promote-graph-checkpoint.sqlite"
    graph = build_promote_graph(backend, checkpoint_path=checkpoint)
    try:
        out = graph.invoke(
            {"library_path": str(lib), "ref": args.ref, "target_file": target_file, "action": action,
             "layer": args.layer, "confidence": args.confidence, "run_id": run_id},
            config={"configurable": {"thread_id": run_id}})
    except Exception:
        release_lock(run_id)
        reg.set_state(run_id, "failed")
        raise
    committed = out.get("committed", 0)
    reg.set_state(run_id, "completed" if committed else "completed_with_errors")
    if out.get("failed"):
        print(f"promote: no supported claims in {args.ref} — nothing promoted")
        return 1
    print(f"promote: run={run_id} target={target_file} committed={committed} "
          f"rejected={out.get('rejected', 0)} promoted {out.get('promoted', 0)} claim(s), "
          f"dropped {out.get('dropped', 0)}")
    return 0 if committed else 1
```
Add a small `_slugify` helper (if none exists in the CLI) near the top:
```python
def _slugify(text: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "promoted-answer"
```
Add the subparser in `main(...)` (after the others):
```python
    p_promote = sub.add_parser("promote")
    p_promote.add_argument("ref")
    p_promote.add_argument("--new", default=None, help="create a new page with this slug")
    p_promote.add_argument("--into", default=None, help="extend an existing page")
    p_promote.add_argument("--library", default="library")
    p_promote.add_argument("--backend", default="anthropic")
    p_promote.add_argument("--layer", default=None)
    p_promote.add_argument("--confidence", default=None, choices=["low", "medium", "high"])
    p_promote.add_argument("--timestamp", required=True)
```
and the dispatch:
```python
    if args.cmd == "promote":
        return _cmd_promote(args, backend_override)
```
(`_make_backend` and `Path` are already imported. Confirm `RunRegistry.start_run(timestamp, fingerprint)` + `set_state` signatures against `resume.py` and adjust if needed.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k promote -v`
Expected: PASS.

- [ ] **Step 5: Append the live Ollama promote smoke**

Append to `tests/test_kb_offline_ollama_smoke.py` (reuse the file's `_ollama_ready()` guard + import style):
```python
@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_promote(tmp_path):
    import json as _j
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph
    from sdlc_knowledge_base_scripts.graphs.promote_graph import build_promote_graph
    from sdlc_knowledge_base_scripts.answers import save_answer
    from sdlc_knowledge_base_scripts.contracts import Answer
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# DORA\n"
                                 "Elite teams deploy multiple times per day.\n")
    be = OllamaBackend(model="gpt-oss:20b", options={"temperature": 0, "seed": 7, "num_ctx": 8192})
    qout = build_query_graph(be).invoke(
        {"library_path": str(lib), "question": "How often do elite teams deploy?"},
        config={"configurable": {"thread_id": "ql"}})
    ref = save_answer(str(lib), "How often do elite teams deploy?", Answer.model_validate(qout["_answer"]),
                      libraries=["local"], page_ids=list(qout.get("page_ids", [])))
    out = build_promote_graph(be).invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "deploy.md", "action": "create",
         "layer": None, "confidence": None, "run_id": "p-live"},
        config={"configurable": {"thread_id": "p-live"}})
    # ran end-to-end; either committed a grounded page or gracefully produced nothing
    assert "committed" in out
```

- [ ] **Step 6: Full regression + lint + parity gate**

```bash
.venv/bin/python -m pytest tests/ -k "kb and not live" -q
.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_offline_answers.py tests/test_kb_offline_promote_pipeline.py tests/test_kb_offline_promote_graph.py
.venv/bin/python tools/validation/check-prompt-parity.py
.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -k promote -v -s   # live, optional; SKIPs if no ollama
```
All green / clean / parity OK.

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py tests/test_kb_offline_ollama_smoke.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): CLI promote subcommand + live promote smoke (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** §1 persistence → Task 1 (`answers.py`) + Task 2 (`query --save` + `_answer`); §2 `pipeline.promote` supported-subset → Task 3; §3 `promote_graph` (load/draft/commit/finalize, deterministic frontmatter, lock/fencing/CAS/journal/recover, audit) → Task 4; §4 CLI `promote` + derived frontmatter (`--new`/`--into`, min-confidence, modal/`--layer`) → Tasks 4+5; §5 testing + promotion-mutation-validation safety floor → Task 4 Step 5 + Task 5 live smoke. Decisions log items 1-6 all covered.
- **Type/name consistency:** `SavedAnswer`/`compute_ref`/`save_answer`/`load_answer`; `promote(saved, *, target_file, action, existing_content, backend, max_repairs)` returns `str` (body); `build_promote_graph(backend, *, checkpoint_path, allowed_layers)`; `PromoteState` keys; `MutationProposal(... expected_hash=...)`; `release_lock(run_id)`; CLI flags `--new`/`--into`/`--layer`/`--confidence`/`--timestamp` — consistent across tasks and matching the reused M0 APIs.
- **Known verification points flagged in Task 4** (do not guess — read the real modules): `AuditEvent` field names + `log_event` signature; `build_shelf_index` function name/signature; `mutation.recover` return keys (`reindexed`); `RunRegistry.start_run`/`set_state` signatures. These are the cross-module drift risks; each task step says to verify against the actual source.
- **Read-only guarantee preserved:** Task 2 only ADDS `_answer` to the query graph's output and persists ONLY under explicit `--save`; a normal `query` still writes nothing to the library.
- **Safety floor exercised:** Task 4 Step 5 proves `validate_proposal` blocks an out-of-library target; the deterministic-citations assembly (citations = supported claims' cited pages, never model-invented) means promote cannot commit an ungrounded mutation — the M2a eval-gate slice.
- **No new mutation path:** promote reuses `validate_proposal` + `commit_mutation` + `recover` verbatim; the only new write surface is `answers.py` (under `.kb-offline/answers/`, not library pages).

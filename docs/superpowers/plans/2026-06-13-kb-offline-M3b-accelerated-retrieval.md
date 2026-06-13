# kb-offline M3b — accelerated retrieval + recall@k gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Opt-in, off-by-default accelerated retrieval — embeddings DISCOVER a top-N candidate shortlist, `select` REASONS over a reduced shelf of just those entries — plus section-fallback chunking and a recall@k eval gate proving the prefilter rarely drops a needed page.

**Architecture:** `chunk_pages` gains section-fallback (oversized pages → `##`-section rows resolving to the page). `retrieval.accelerated_candidates` embeds the query → `store.search` top-N → builds a reduced shelf. `pipeline.select` gains optional `shelf_text` so it reasons over the reduced shelf. `query --accelerate` wires it in `n_select` with a fresh-index check + full-shelf fallback. `recall_at_k` gate measures embedding recall of `expected_routing_targets`.

**Tech Stack:** Python 3.9+, numpy, the project `.venv`, pytest. Spec: `docs/superpowers/specs/2026-06-13-kb-offline-M3b-accelerated-retrieval-design.md`.

---

## Environment & scope

- **`.venv` for everything**; flake8@127; commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **In scope:** section chunking, `retrieval.accelerated_candidates`, `select(shelf_text=)`, `query --accelerate`, recall@k gate.
- **Out of scope:** federation accelerated discovery + shareable-embedding "find who to ask" (M3c), RRF + index-compat rejection (M3c), conflict lint (M3d).

## Reused APIs (verified)

- `embeddings.chunk_pages(library_path) -> [(page_id, embed_text, content_hash)]` (rglob; `_is_library_file` exclusions; `_strip_frontmatter`; page_id = POSIX rel path); `embeddings.corpus_hash([(page_id, content_hash)]) -> str`; `embeddings.EmbeddingStore.load(lib) -> store|None`, `.search(qvec, k) -> [(page_id, score)]` (best-per-page, k_eff-guarded), `.provenance.corpus_hash`; `content_hash`.
- `pipeline.select(question, shelf_index_path, *, backend, known_pages, max_repairs=1, priming=None)` — reads the shelf file; prompt = `f"{prime_block}{prompts.SELECT_FRAGMENT}\n\nQuestion: {question}\n\nShelf-index:\n{shelf}"`.
- `provenance.filter_pages(library_path, page_names, *, layer=None, min_confidence=None) -> list[str]` (reads `lib/<page_name>` frontmatter; handles relative paths like `sub/x.md`).
- `query_graph.n_select` currently: `known = {p.name for p in lib.glob("*.md")} - meta`; `filter_pages(lib, sorted(known), ...)`; `select(question, lib/"_shelf-index.md", backend=, known_pages=)`. (Note: `glob` is top-level; the accelerate path uses index page_ids directly via `filter_pages`, which is rglob/nested-correct.)
- `eval/harness.py` pure scorers; `eval/thresholds.py` constants; backend `embed(texts) -> list[list[float]]` (FakeBackend deterministic 8-dim).
- CLI: `main(... query subparser var p_q ...)`; backend_override seam; `import sys`.

## File structure (M3b)

| File | Responsibility |
|---|---|
| `scripts/embeddings.py` (modify) | `chunk_pages` gains `section_threshold`; `_split_sections` helper |
| `scripts/retrieval.py` (new) | `accelerated_candidates` + `_reduce_shelf` |
| `scripts/pipeline.py` (modify) | `select` gains optional `shelf_text` |
| `scripts/graphs/query_graph.py` (modify) | `n_select` accelerate branch + fresh-index check + fallback |
| `scripts/kb_offline_cli.py` (modify) | `query --accelerate [--accelerate-k]` threading |
| `scripts/eval/thresholds.py` (modify) | `EMBEDDING_RECALL_AT_K = 0.95` |
| `scripts/eval/harness.py` (modify) | `recall_at_k` scorer |
| `scripts/eval/runner.py` (modify) | `score_recall_at_k` measurement path |
| Tests | `test_kb_offline_embeddings.py`, `test_kb_offline_retrieval.py`, `test_kb_offline_query_pipeline.py`, `test_kb_offline_query_graph.py`, `test_kb_offline_cli.py`, `test_kb_offline_eval_scorers.py`, `test_kb_offline_ollama_smoke.py` |

---

## Task 1: section-fallback chunking

**Files:** Modify `scripts/embeddings.py`; Test append to `tests/test_kb_offline_embeddings.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
def test_chunk_pages_small_page_is_single_row(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _mk(lib, "small.md", "# Small\nshort body\n")
    rows = chunk_pages(lib)
    assert len([r for r in rows if r[0] == "small.md"]) == 1   # under threshold -> 1 row


def test_chunk_pages_oversized_splits_into_section_rows(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    big = "# Big\n" + ("preamble. " * 50) + "\n## Section A\n" + ("aaa " * 80) + "\n## Section B\n" + ("bbb " * 80) + "\n"
    _mk(lib, "big.md", big)
    rows = [r for r in chunk_pages(lib, section_threshold=200) if r[0] == "big.md"]
    assert len(rows) >= 3                       # preamble + Section A + Section B
    assert all(pid == "big.md" for pid, _, _ in rows)   # all share the page_id
    texts = " | ".join(t for _, t, _ in rows)
    assert "Section A" in texts and "Section B" in texts
    # distinct section content_hashes
    assert len({h for _, _, h in rows}) == len(rows)


def test_chunk_pages_default_threshold_keeps_normal_pages_single(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _mk(lib, "dora.md", "---\nlayer: evidence\n---\n# DORA\nElite teams deploy multiple times per day.\n")
    assert len(chunk_pages(lib)) == 1           # well under default 2000
```
(`_mk(lib, rel, body)` helper already exists in this test file from M3a.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k "section or single_row or default_threshold" -v`
Expected: FAIL (`chunk_pages` has no `section_threshold`).

- [ ] **Step 3: Implement section-fallback**

In `scripts/embeddings.py` add `import re` (if not present) and a splitter, and extend `chunk_pages`:
```python
def _split_sections(body: str) -> list:
    """Split a page body into a preamble part (before the first '## ' heading) + one part per
    '## ' section (heading included). Returns non-empty stripped-nonempty parts."""
    parts = re.split(r"(?m)^(?=\#\# )", body)
    return [p for p in parts if p.strip()]


def chunk_pages(library_path, *, section_threshold: int = 2000) -> list:
    """Rows (page_id, embed_text, content_hash). Pages whose frontmatter-stripped body is
    <= section_threshold chars -> ONE page-level row. Over threshold -> '##'-section rows
    (preamble + per-section), ALL sharing the page's page_id, each with its own content_hash;
    a section hit resolves to the whole page in EmbeddingStore.search (best-per-page)."""
    lib = Path(library_path)
    out = []
    for md in sorted(lib.rglob("*.md")):
        if not _is_library_file(md, lib):
            continue
        page_id = md.relative_to(lib).as_posix()
        body = _strip_frontmatter(md.read_text(encoding="utf-8"))
        if len(body) <= section_threshold:
            out.append((page_id, body, content_hash(body)))
        else:
            for section in _split_sections(body):
                out.append((page_id, section, content_hash(section)))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -v` → all pass (incl. the M3a tests — their pages are under 2000 chars so still single-row). flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/embeddings.py tests/test_kb_offline_embeddings.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): section-fallback chunking (oversized pages -> ## section rows by page_id) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `retrieval.accelerated_candidates`

**Files:** Create `scripts/retrieval.py`; Test `tests/test_kb_offline_retrieval.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_retrieval.py`:
```python
"""Accelerated discovery / reduced-shelf tests. kb-offline M3b (#211)."""
from __future__ import annotations

import numpy as np

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore, IndexRow, Provenance
from sdlc_knowledge_base_scripts.retrieval import accelerated_candidates


def _store(vectors, page_ids):
    rows = [IndexRow(page_id=p, content_hash=f"h{i}") for i, p in enumerate(page_ids)]
    prov = Provenance(model="fake-embed", dims=len(vectors[0]), normalization="l2", corpus_hash="c")
    return EmbeddingStore.from_rows(np.array(vectors, dtype=np.float32), rows, prov)


def _lib_with_shelf(tmp_path, entries):
    lib = tmp_path / "library"
    lib.mkdir()
    shelf = "<!-- format_version: 1 -->\n# Shelf Index\n\nIntro prose.\n" + "".join(
        f"- {pid} — about {pid}\n" for pid in entries)
    (lib / "_shelf-index.md").write_text(shelf, encoding="utf-8")
    return lib


def test_accelerated_candidates_returns_topk_and_reduced_shelf(tmp_path):
    lib = _lib_with_shelf(tmp_path, ["a.md", "b.md", "c.md"])
    store = _store([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ["a.md", "b.md", "c.md"])
    be = FakeBackend()
    be.embed = lambda texts: [[0.0, 1.0, 0.1]]    # query closest to b.md
    page_ids, reduced = accelerated_candidates("q", str(lib), store, backend=be, k=2)
    assert page_ids[0] == "b.md" and len(page_ids) == 2
    # reduced shelf keeps the header + ONLY the top-2 entries
    assert "# Shelf Index" in reduced and "Intro prose." in reduced
    assert "b.md" in reduced
    excluded = ({"a.md", "b.md", "c.md"} - set(page_ids)).pop()
    assert f"- {excluded}" not in reduced


def test_reduced_shelf_synthesizes_entry_when_shelf_has_no_bullet(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf Index\n", encoding="utf-8")
    store = _store([[1, 0, 0]], ["a.md"])
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    page_ids, reduced = accelerated_candidates("q", str(lib), store, backend=be, k=1)
    assert page_ids == ["a.md"]
    assert "a.md" in reduced       # synthetic entry so select still has the candidate
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_retrieval.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `retrieval.py`**

Create `scripts/retrieval.py`:
```python
"""Accelerated discovery (#211, M3b): embeddings discover a top-N candidate shortlist; build a
REDUCED shelf of just those entries for the reasoned `select` to read. OFF by default — the
query path opts in via --accelerate. Single-library; federation discovery is M3c."""
from __future__ import annotations

from pathlib import Path


def _reduce_shelf(shelf_path: Path, page_ids: list) -> str:
    """Header (lines before the first '- ' bullet) + the matching entry line for each candidate
    in discovery-rank order (synthetic '- <page_id>' if the shelf has no entry for it)."""
    text = shelf_path.read_text(encoding="utf-8") if shelf_path.is_file() else ""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].lstrip().startswith("- "):
        i += 1
    header, entries = lines[:i], lines[i:]
    chosen = []
    for pid in page_ids:
        base = pid.rsplit("/", 1)[-1]
        match = next((ln for ln in entries if pid in ln or base in ln), None)
        chosen.append(match if match is not None else f"- {pid}")
    return "\n".join(header + chosen) + "\n"


def accelerated_candidates(question, library_path, store, *, backend, k: int = 20) -> tuple:
    """Discovery: embed(question) -> store.search top-k -> (page_ids best-first, reduced_shelf)."""
    qvec = backend.embed([question])[0]
    hits = store.search(qvec, k=k)
    page_ids = [pid for pid, _ in hits]
    reduced = _reduce_shelf(Path(library_path) / "_shelf-index.md", page_ids)
    return page_ids, reduced
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_retrieval.py -v` → 2 passed. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/retrieval.py tests/test_kb_offline_retrieval.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): retrieval.accelerated_candidates — discover top-N + build reduced shelf (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `pipeline.select` optional `shelf_text`

**Files:** Modify `scripts/pipeline.py`; Test append to `tests/test_kb_offline_query_pipeline.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_query_pipeline.py`:
```python
def test_select_uses_shelf_text_when_given(tmp_path):
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    select("q", _shelf(tmp_path), backend=be, known_pages={"a.md"},
           shelf_text="REDUCED-SHELF-MARKER\n- a.md")
    assert "REDUCED-SHELF-MARKER" in captured["prompt"]   # reasoned over the provided text


def test_select_reads_file_when_shelf_text_none(tmp_path):
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    shelf = _shelf(tmp_path)   # writes "# Shelf\n- a.md\n- b.md\n" style content
    select("q", shelf, backend=be, known_pages={"a.md"})   # shelf_text=None -> read file
    assert "REDUCED-SHELF-MARKER" not in captured["prompt"]
    assert "Shelf-index:" in captured["prompt"]            # full-file path unchanged
```
(`_shelf(tmp_path)` writes a shelf file and returns its path — already defined in this file from M1c-1.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -k shelf_text -v`
Expected: FAIL (unexpected kwarg `shelf_text`).

- [ ] **Step 3: Add `shelf_text` to `select`**

In `scripts/pipeline.py`, change the `select` signature + the shelf read:
```python
def select(question, shelf_index_path, *, backend, known_pages, max_repairs: int = 1, priming=None,
           shelf_text=None) -> SelectResult:
    """... When `shelf_text` is given, reason over it instead of reading shelf_index_path (the
    accelerated reduced-shelf path); None reads the file (default, byte-identical to before)."""
    shelf = shelf_text if shelf_text is not None else Path(shelf_index_path).read_text(encoding="utf-8")
    # ... rest UNCHANGED (prime_block, base = f"{prime_block}{prompts.SELECT_FRAGMENT}...{shelf}", loop)
```
(Only the first line of the body changes — `shelf = ...`. Everything else stays identical.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -v` → all pass. Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions — select's default path byte-identical) + `.venv/bin/python tools/validation/check-prompt-parity.py` (parity OK) + flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_query_pipeline.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): select gains optional shelf_text (reason over a reduced shelf) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `query --accelerate` wiring (n_select branch + CLI + fallback)

**Files:** Modify `scripts/graphs/query_graph.py`, `scripts/kb_offline_cli.py`; Test `tests/test_kb_offline_query_graph.py`, `tests/test_kb_offline_cli.py`, `tests/test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_query_graph.py`:
```python
def test_query_graph_accelerate_uses_reduced_shelf(tmp_path):
    import numpy as np
    from sdlc_knowledge_base_scripts.embeddings import (EmbeddingStore, IndexRow, Provenance,
                                                        chunk_pages, corpus_hash)
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md — alpha\n- b.md — beta\n")
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\nalpha body\n")
    (lib / "b.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# B\nbeta body\n")
    # build a fresh index whose corpus_hash matches the current library
    rows = [IndexRow(page_id=p, content_hash=h) for p, _, h in chunk_pages(lib)]
    ch = corpus_hash([(p, h) for p, _, h in chunk_pages(lib)])
    # 2-dim vectors: a.md ~ [1,0], b.md ~ [0,1]
    vec = {"a.md": [1.0, 0.0], "b.md": [0.0, 1.0]}
    matrix = np.array([vec[r.page_id] for r in rows], dtype=np.float32)
    EmbeddingStore(matrix, rows, Provenance(model="fake-embed", dims=2, normalization="l2", corpus_hash=ch)).save(lib)

    seen = {}

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf" in prompt and "Question" in prompt:        # this is the select prompt
            seen["select_prompt"] = prompt
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [], "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    be.embed = lambda texts: [[1.0, 0.0]]                      # query ~ a.md
    graph = build_query_graph(be)
    out = graph.invoke({"library_path": str(lib), "question": "about alpha?", "accelerate": True,
                        "accelerate_k": 1},
                       config={"configurable": {"thread_id": "acc1"}})
    # accelerated: select reasoned over a REDUCED shelf containing a.md but NOT b.md's entry
    assert "a.md" in seen["select_prompt"]
    assert "beta" not in seen["select_prompt"]                # b.md's entry excluded by top-1 prefilter


def test_query_graph_accelerate_falls_back_without_index(tmp_path, capsys):
    lib = _lib(tmp_path)   # existing helper: shelf + a.md, NO embedding index

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
    out = graph.invoke({"library_path": str(lib), "question": "what about cost?", "accelerate": True},
                       config={"configurable": {"thread_id": "acc2"}})
    assert "Cost fell 30%." in out["rendered_text"]            # full-shelf fallback still answers
    assert "no fresh index" in capsys.readouterr().err.lower() # warned
```
Append to `tests/test_kb_offline_cli.py`:
```python
def test_cli_query_accelerate_flag_threads_through(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
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
    # --accelerate with no index -> warns + full-shelf fallback -> still answers, rc 0
    rc = cli.main(["query", "what about cost?", "--library", str(lib), "--backend", "fake", "--accelerate"],
                  backend_override=be)
    assert rc == 0
    assert "Cost fell 30%." in capsys.readouterr().out
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py -k accelerate tests/test_kb_offline_cli.py -k accelerate -v`
Expected: FAIL (`accelerate` ignored / `--accelerate` unknown).

- [ ] **Step 3: Wire the accelerate branch in `n_select`**

In `scripts/graphs/query_graph.py`: add `accelerate`/`accelerate_k` to `QueryState` (TypedDict) and rewrite `n_select` to branch (keep the existing full-shelf path verbatim as the `else`):
```python
    def n_select(state: QueryState) -> dict:
        import sys
        lib = Path(state["library_path"])
        shelf = lib / "_shelf-index.md"
        known = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        if state.get("accelerate"):
            from ..embeddings import EmbeddingStore, chunk_pages, corpus_hash
            from ..retrieval import accelerated_candidates
            store = EmbeddingStore.load(lib)
            fresh = store is not None and store.provenance.corpus_hash == corpus_hash(
                [(p, h) for p, _, h in chunk_pages(lib)])
            if fresh:
                cand_ids, reduced = accelerated_candidates(
                    state["question"], str(lib), store, backend=backend, k=state.get("accelerate_k") or 20)
                candidates = filter_pages(lib, cand_ids, layer=state.get("layer"),
                                          min_confidence=state.get("min_confidence"))
                res = select(state["question"], shelf, backend=backend, known_pages=set(candidates),
                             shelf_text=reduced)
                return {"page_ids": res.page_ids}
            print("[query] accelerate: no fresh index (run kb-offline index); falling back to full-shelf select",
                  file=sys.stderr)
        candidates = filter_pages(lib, sorted(known), layer=state.get("layer"),
                                  min_confidence=state.get("min_confidence"))
        res = select(state["question"], shelf, backend=backend, known_pages=set(candidates))
        return {"page_ids": res.page_ids}
```
Note: the accelerate candidate set comes from the INDEX's page_ids (rglob/nested-correct), filtered by `filter_pages` (which reads `lib/<page_id>` frontmatter — works for nested). The reduced shelf is built from the discovery order; `filter_pages` then drops any layer/min-confidence misfits. `known` (top-level glob) is only used by the unchanged full-shelf else-branch.

- [ ] **Step 4: Thread `--accelerate` through the CLI**

In `scripts/kb_offline_cli.py`, add to the `query` subparser `p_q`:
```python
    p_q.add_argument("--accelerate", action="store_true", help="use the embedding index to pre-filter candidates")
    p_q.add_argument("--accelerate-k", type=int, default=20)
```
And in the single-library query path (`_query_single` / `_cmd_query`'s graph.invoke state), add `accelerate`/`accelerate_k`:
```python
            "accelerate": getattr(args, "accelerate", False),
            "accelerate_k": getattr(args, "accelerate_k", 20),
```
(Add these keys to the state dict passed to the query graph in the single-library path. The federated path — `--libraries` — ignores accelerate in M3b; accelerate applies to single-library query only. If both `--accelerate` and `--libraries` are given, accelerate is silently ignored on the federated path for now — note this in the help or a stderr note is optional; keep M3b scoped to single-library.)

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py tests/test_kb_offline_cli.py -v` → all pass. Then `.venv/bin/python -m pytest tests/ -k "kb and not live" -q` (no regressions — non-accelerate query unchanged) + flake8 clean + parity OK.

- [ ] **Step 6: Append the live Ollama accelerate smoke** to `tests/test_kb_offline_ollama_smoke.py`:
```python
@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_query_accelerate(tmp_path):
    import numpy as np
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.embeddings import (EmbeddingStore, IndexRow, Provenance,
                                                        chunk_pages, corpus_hash)
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md — DORA metrics\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# DORA\nElite teams deploy multiple times per day.\n")
    be = OllamaBackend()
    rows = [IndexRow(page_id=p, content_hash=h) for p, _, h in chunk_pages(lib)]
    vecs = np.array(be.embed([t for _, t, _ in chunk_pages(lib)]), dtype=np.float32)
    ch = corpus_hash([(p, h) for p, _, h in chunk_pages(lib)])
    EmbeddingStore.from_rows(vecs, rows, Provenance(model=be.embedding_model_id(), dims=vecs.shape[1],
                             normalization="l2", corpus_hash=ch)).save(lib)
    out = build_query_graph(be).invoke(
        {"library_path": str(lib), "question": "How often do elite teams deploy?", "accelerate": True, "accelerate_k": 5},
        config={"configurable": {"thread_id": "acc-live"}})
    assert "rendered_text" in out and "rejected_claims" in out
```

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_query_graph.py tests/test_kb_offline_cli.py tests/test_kb_offline_ollama_smoke.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): query --accelerate — reduced-shelf select via embedding prefilter + full-shelf fallback (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: recall@k eval gate

**Files:** Modify `scripts/eval/thresholds.py`, `scripts/eval/harness.py`, `scripts/eval/runner.py`; Test `tests/test_kb_offline_eval_scorers.py`, `tests/test_kb_offline_retrieval.py` (runner-path)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_eval_scorers.py`:
```python
from sdlc_knowledge_base_scripts.eval.harness import recall_at_k
from sdlc_knowledge_base_scripts.eval import thresholds as _thr


def test_embedding_recall_at_k_threshold_ratified():
    assert _thr.EMBEDDING_RECALL_AT_K == 0.95


def test_recall_at_k_macro_mean():
    rows = [
        {"expected": ["a.md"], "shortlist": ["a.md", "x.md"]},          # 1.0
        {"expected": ["b.md", "c.md"], "shortlist": ["b.md", "z.md"]},  # 0.5
        {"expected": [], "shortlist": ["q.md"]},                        # vacuous -> 1.0
    ]
    assert abs(recall_at_k(rows) - (1.0 + 0.5 + 1.0) / 3) < 1e-9
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_eval_scorers.py -k "recall_at_k or embedding_recall" -v`
Expected: FAIL (ImportError / missing constant).

- [ ] **Step 3: Add the threshold + scorer**

In `scripts/eval/thresholds.py`, append:
```python

# M3b: embedding-prefilter recall floor — the accelerator's top-N shortlist must contain at
# least this fraction of expected routing targets (proves the prefilter rarely drops a needed page).
EMBEDDING_RECALL_AT_K = 0.95
```
In `scripts/eval/harness.py`, append:
```python
def recall_at_k(rows: list[dict]) -> float:
    """Macro mean over rows of |expected ∩ shortlist| / |expected| (1.0 when expected is empty).
    rows = [{expected: list[str], shortlist: list[str]}]."""
    if not rows:
        return 1.0
    per = []
    for r in rows:
        expected = set(r["expected"])
        if not expected:
            per.append(1.0)
            continue
        per.append(len(expected & set(r["shortlist"])) / len(expected))
    return sum(per) / len(per)
```

- [ ] **Step 4: Add the runner measurement path**

In `scripts/eval/runner.py`, append a helper that builds shortlists per non-abstention question over a prebuilt store:
```python
def score_recall_at_k(library_path, questions, store, *, backend, k: int = 20):
    """For each non-abstention question, the embedding top-k shortlist via accelerated_candidates;
    returns harness.recall_at_k over {expected_routing_targets, shortlist} rows."""
    from .. import retrieval
    rows = []
    for q in questions:
        if q.no_evidence:
            continue
        shortlist, _ = retrieval.accelerated_candidates(q.question, library_path, store, backend=backend, k=k)
        rows.append({"expected": q.expected_routing_targets, "shortlist": shortlist})
    return harness.recall_at_k(rows)
```
Add a runner test to `tests/test_kb_offline_retrieval.py`:
```python
def test_score_recall_at_k_over_built_index(tmp_path):
    import numpy as np
    from sdlc_knowledge_base_scripts.eval.runner import score_recall_at_k
    from sdlc_knowledge_base_scripts.eval.suite import EvalQuestion
    from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore, IndexRow, Provenance
    store = _store([[1, 0], [0, 1]], ["a.md", "b.md"])
    qs = [EvalQuestion(id="q1", question="alpha", kind="fact", expected_facts=[],
                       expected_routing_targets=["a.md"], no_evidence=False),
          EvalQuestion(id="q2", question="none", kind="abstention", expected_facts=[],
                       expected_routing_targets=[], no_evidence=True)]
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0]]      # always nearest a.md
    r = score_recall_at_k("ignored-for-shelf", qs, store, backend=be, k=1)
    # only q1 (non-abstention) scored; a.md in shortlist -> recall 1.0
    assert r == 1.0
```
(`accelerated_candidates` reads `<library_path>/_shelf-index.md` for the reduced shelf but `score_recall_at_k` only uses the returned page_ids — a missing shelf yields an empty header, harmless; pass a real tmp lib path if the test wants the shelf, but page_ids come from `store.search` regardless.)

- [ ] **Step 5: Run to verify pass + full gate**

```bash
.venv/bin/python -m pytest tests/test_kb_offline_eval_scorers.py tests/test_kb_offline_retrieval.py -v
.venv/bin/python -m pytest tests/ -k "kb and not live" -q
.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_offline_retrieval.py tests/test_kb_offline_eval_scorers.py
.venv/bin/python tools/validation/check-prompt-parity.py
```
All green / clean / parity OK.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/eval/thresholds.py plugins/sdlc-knowledge-base/scripts/eval/harness.py plugins/sdlc-knowledge-base/scripts/eval/runner.py tests/test_kb_offline_eval_scorers.py tests/test_kb_offline_retrieval.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): recall@k gate — EMBEDDING_RECALL_AT_K + recall_at_k scorer + runner path (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** §1 section chunking → Task 1; §2 accelerated_candidates + reduced shelf → Task 2; §3 select shelf_text → Task 3; §4 query --accelerate + fresh-index check + fallback → Task 4; §5 recall@k gate (threshold + scorer + runner) → Task 5. Decisions log 1-7 covered (reduced-shelf, N=20 default+override, recall ≥0.95 absolute, section split, --accelerate+fallback, shelf_text backward-compat + layer/min-conf honored, single-library).
- **Type/name consistency:** `chunk_pages(..., section_threshold=2000)`; `accelerated_candidates(question, library_path, store, *, backend, k=20) -> (page_ids, reduced_shelf)`; `select(..., shelf_text=None)`; QueryState `accelerate`/`accelerate_k`; `recall_at_k(rows)`; `score_recall_at_k(library_path, questions, store, *, backend, k)`; `EMBEDDING_RECALL_AT_K` — consistent.
- **Backward compatibility:** `chunk_pages` default threshold 2000 keeps M3a tests single-row; `select(shelf_text=None)` is byte-identical to before (existing query + eval + M2b federation unaffected); `query` without `--accelerate` unchanged. Confirmed via the regression runs in Tasks 3-4.
- **Read-only preserved:** the accelerate path only READS the index + reduced shelf; no writes. Fresh-index check uses corpus_hash (no mutation).
- **Known verification points:** the entry→page matching in `_reduce_shelf` (substring match of page_id/basename) is heuristic — the synthetic-entry fallback covers shelves without per-page bullets; confirm the eval-suite shelf format matches (bullets like `- dora.md — ...`). The accelerate path uses index page_ids (rglob) while the full-shelf else-branch uses top-level glob `known` — intentional (accelerate is index-driven). `--accelerate` + `--libraries` (federation) → accelerate ignored on the federated path in M3b (single-library scope).
- **No silent caps:** the missing/stale-index fallback prints a stderr warning; the recall@k gate is an explicit ratified threshold.

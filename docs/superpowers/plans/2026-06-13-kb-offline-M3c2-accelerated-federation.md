# kb-offline M3c-2 — accelerated federated query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `query --libraries a,b,c --accelerate` — embed the question once, RRF-interleave each library's embedding shortlist into ONE cross-library candidate list, hand it to a single reasoned `select` over a cross-library reduced shelf, then read/synthesize/verify across libraries with clean per-library attribution. Embeddings discover; the shelf reasons.

**Architecture:** A new `scripts/federation_accel.py` holds a single LINEAR function `accelerated_federation_query` (no graph): load+validate every store once (closes TOCTOU), embed once, search per library in `library_specs` order, filter, coverage-guard, fuse (M3c-1 `fuse_compatible` — RRF degenerates to rank-interleave over disjoint handle-qualified keys), build a cross-library reduced shelf from real `## N.` shelf blocks, one reasoned `select`, read across libraries with resolved-path containment, synthesize → verify → canonicalize attribution → attributed publish. Any gate/validity/coverage failure returns `None` so the CLI falls back to the full M2b federation (never drops a library's coverage). Supporting changes: qualified-id helpers in `fusion.py`, an optional `Span.library`, a shared `extract_entry_block` parser (also adopted by M3b's `_reduce_shelf`), and `canonicalize_attribution` in `federation.py`.

**Tech Stack:** Python 3.9+, the project `.venv`, pytest, numpy. No new deps. Spec: `docs/superpowers/specs/2026-06-13-kb-offline-M3c2-accelerated-federation-design.md`.

---

## Environment & scope

- **`.venv` for everything**; `flake8` line length 127; commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Source files live under `plugins/sdlc-knowledge-base/scripts/`; tests import them as the `sdlc_knowledge_base_scripts` package (registered by `tests/conftest.py`). Run pytest from the repo root.
- **In scope:** `qualify`/`split_qualified`; `Span.library`; `extract_entry_block`; M3b `_reduce_shelf` adoption of the shared parser; `canonicalize_attribution`; `accelerated_federation_query`; CLI routing + `--accelerate-k >= 1` validation.
- **Out of scope:** "find who to ask" discovery (M3c-3); semantic conflict lint (M3d); mid-call re-index handling.

## Reused APIs (already implemented — call, do not re-create)

- `fusion.fuse_compatible(reference_prov, entries, *, k_const=60) -> (fused, rejected)` where `entries=[(handle, prov, ranked_page_ids)]` and `fused=[((handle, page_id), score)]`; `fusion.compatible(a, b) -> bool`.
- `embeddings.EmbeddingStore.load(library_path) -> EmbeddingStore | None`; `.provenance` (`Provenance(model, dims, normalization, corpus_hash, schema_version)`); `.search(query_vec, k=8) -> [(page_id, score)]`; `EmbeddingStore.from_rows(matrix, rows, provenance)`; `.save(library_path)`.
- `embeddings.chunk_pages(library_path) -> [(page_id, embed_text, content_hash)]`; `embeddings.corpus_hash(page_hash_pairs) -> str`; `embeddings.IndexRow(page_id, content_hash)`.
- `provenance.filter_pages(library_path, page_names, *, layer=None, min_confidence=None) -> [page_id]`.
- `pipeline.select(question, shelf_index_path, *, backend, known_pages, max_repairs=1, priming=None, shelf_text=None) -> SelectResult(page_ids)`; `pipeline.synthesize(question, pages, *, backend, max_repairs=1) -> Answer` (pages = `[{"page": id, "content": str}]`).
- `entailment.verify_entailment(answer, pages_by_name, *, backend) -> Answer`.
- `priming.build_priming_bundle(question, project_dir: Path) -> PrimingBundle`.
- `federation._norm(text) -> str`; `federation.render_federated(merged, handle_sets) -> (rendered_text, rejected_claims)`.
- `audit.AuditEvent(timestamp, event_type, query, source_handle, reason, detail)`; `audit.log_event(log_path, event)`. `"cross_library_query"` is already a valid event type.
- `build_shelf_index._ENTRY_PATH_RE` = `re.compile(r"^## \d+\.\s+(.+)$", re.MULTILINE)`; `build_shelf_index.rebuild_shelf_index(library_path, shelf_index_path, full=False)`.
- `backends.fake_backend.FakeBackend` — has `.generate`, `.embed`, `.embedding_model_id() -> "fake-embed"`; tests override `.embed`/`.generate` with lambdas. `AnthropicBackend` intentionally OMITS `embedding_model_id`.

## File structure (M3c-2)

| File | Responsibility |
|---|---|
| `scripts/fusion.py` (modify) | `qualify`, `split_qualified` |
| `scripts/contracts.py` (modify) | `Span.library: str | None = None` |
| `scripts/build_shelf_index.py` (modify) | `extract_entry_block(shelf_text, file_path) -> str | None` |
| `scripts/retrieval.py` (modify) | `_reduce_shelf` adopts `extract_entry_block` (real `## N.` format) + bullet fallback + synthetic |
| `scripts/federation.py` (modify) | `canonicalize_attribution(answer) -> Answer` |
| `scripts/federation_accel.py` (new) | `accelerated_federation_query` + `_dedupe_specs`, `_cross_library_shelf`, `_resolve_in_root` |
| `scripts/kb_offline_cli.py` (modify) | route `--libraries --accelerate` → accel fn (None → M2b fallback); `--accelerate-k >= 1` |
| Tests | `tests/test_kb_offline_fusion.py`, `tests/test_kb_offline_contracts.py`, `tests/test_kb_offline_embeddings.py`, `tests/test_kb_offline_retrieval.py`, `tests/test_kb_offline_federation.py`, `tests/test_kb_offline_federation_accel.py` (new), `tests/test_kb_offline_cli.py`, `tests/test_kb_offline_ollama_smoke.py` |

---

## Task 1: Qualified-id helpers (`fusion.qualify` / `split_qualified`)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/fusion.py`
- Test: `tests/test_kb_offline_fusion.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_fusion.py`:
```python
from sdlc_knowledge_base_scripts.fusion import qualify, split_qualified


def test_qualify_round_trips_flat_and_nested_page_ids():
    assert qualify("acme-kb", "a.md") == "acme-kb/a.md"
    assert split_qualified("acme-kb/a.md") == ("acme-kb", "a.md")
    # nested page id: handle recovered by splitting on the FIRST '/'
    assert qualify("acme-kb", "sub/x.md") == "acme-kb/sub/x.md"
    assert split_qualified("acme-kb/sub/x.md") == ("acme-kb", "sub/x.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fusion.py -k qualify -v`
Expected: FAIL (ImportError: cannot import name `qualify`).

- [ ] **Step 3: Implement the helpers**

Append to `plugins/sdlc-knowledge-base/scripts/fusion.py`:
```python
def qualify(handle: str, page_id: str) -> str:
    """'handle/page_id'. Handles match ^[a-z][a-z0-9-]*$ (no '/'), so the handle is recoverable
    by splitting on the FIRST '/' even when page_id is nested (e.g. 'sub/x.md')."""
    return f"{handle}/{page_id}"


def split_qualified(qid: str) -> tuple:
    """Inverse of qualify: split on the first '/'. Returns (handle, page_id)."""
    handle, _, page_id = qid.partition("/")
    return handle, page_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_fusion.py -v`
Expected: PASS (all fusion tests). Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fusion.py tests/test_kb_offline_fusion.py` → clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/fusion.py tests/test_kb_offline_fusion.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): fusion.qualify/split_qualified — handle-qualified id boundary (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `Span.library` optional field

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/contracts.py:41-43`
- Test: `tests/test_kb_offline_contracts.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_contracts.py`:
```python
from sdlc_knowledge_base_scripts.contracts import Span


def test_span_library_defaults_to_none_and_is_optional():
    # backward compatible: existing two-arg construction unaffected
    s = Span(page="a.md", text="x")
    assert s.library is None
    # new optional field accepts a handle
    s2 = Span(library="acme-kb", page="a.md", text="x")
    assert s2.library == "acme-kb"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_contracts.py -k span_library -v`
Expected: FAIL (`Span` has no field `library`).

- [ ] **Step 3: Implement the field**

In `plugins/sdlc-knowledge-base/scripts/contracts.py`, change the `Span` class from:
```python
class Span(BaseModel):
    page: str
    text: str
```
to:
```python
class Span(BaseModel):
    library: str | None = None
    page: str
    text: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_contracts.py -v`
Expected: PASS. Then `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → no regressions (existing `Span(page=, text=)` call sites unaffected by an optional defaulted field).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/contracts.py tests/test_kb_offline_contracts.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): Span.library optional field (backward-compatible) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `extract_entry_block` shelf parser

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/build_shelf_index.py`
- Test: `tests/test_kb_offline_embeddings.py`

**Contract (spec §5.1):** exact-id `## N. <path>` header match (string equality — `a.md` must NOT match `data.md`; nested paths compared whole); the returned block runs from the matched header up to (but excluding) the next `_ENTRY_PATH_RE` header or EOF, carrying that entry's Hash/Layer/Confidence/Terms/Facts; `None` if no exact match.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_embeddings.py`:
```python
from sdlc_knowledge_base_scripts.build_shelf_index import extract_entry_block

_SHELF = (
    "<!-- format_version: 1 -->\n# Knowledge Base Shelf-Index\n\n---\n\n"
    "## 1. data.md\n\n**Hash:** aaa\n**Layer:** evidence\n**Confidence:** high\n"
    "**Terms:** data\n**Facts:**\n- data fact\n**Links:** \n\n"
    "## 2. a.md\n\n**Hash:** bbb\n**Layer:** domain\n**Confidence:** low\n"
    "**Terms:** alpha\n**Facts:**\n- a fact\n**Links:** \n\n"
    "## 3. sub/x.md\n\n**Hash:** ccc\n**Layer:** domain\n**Confidence:** medium\n"
    "**Terms:** nested\n**Facts:**\n- nested fact\n**Links:** \n"
)


def test_extract_entry_block_exact_id_no_substring_collision():
    block = extract_entry_block(_SHELF, "a.md")
    assert block is not None
    assert "## 2. a.md" in block
    assert "a fact" in block and "Layer:** domain" in block
    # does NOT bleed into data.md (a.md is a substring of nothing here, but guards the rule)
    assert "data fact" not in block
    # block ends before the next entry header
    assert "## 3." not in block


def test_extract_entry_block_does_not_match_data_for_a():
    # asking for 'data.md' returns data's block, not a.md's
    block = extract_entry_block(_SHELF, "data.md")
    assert "## 1. data.md" in block and "data fact" in block
    assert "## 2." not in block


def test_extract_entry_block_nested_path_whole():
    block = extract_entry_block(_SHELF, "sub/x.md")
    assert block is not None
    assert "## 3. sub/x.md" in block and "nested fact" in block


def test_extract_entry_block_returns_none_when_absent():
    assert extract_entry_block(_SHELF, "missing.md") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k extract_entry_block -v`
Expected: FAIL (ImportError: cannot import name `extract_entry_block`).

- [ ] **Step 3: Implement `extract_entry_block`**

In `plugins/sdlc-knowledge-base/scripts/build_shelf_index.py`, add this function (place it directly after `parse_existing_index`, which already uses `_ENTRY_PATH_RE`):
```python
def extract_entry_block(shelf_text: str, file_path: str) -> Optional[str]:
    """Return the '## N. <file_path>' entry block (header line through the line before the next
    entry header or EOF), or None if no header's captured path EQUALS file_path exactly.
    Exact-id match: 'a.md' must not match 'data.md'; nested paths ('sub/x.md') compared whole."""
    lines = shelf_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = _ENTRY_PATH_RE.match(line)
        if m and m.group(1).strip() == file_path:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _ENTRY_PATH_RE.match(lines[j]):
            end = j
            break
    return "\n".join(lines[start:end]).rstrip("\n") + "\n"
```

(`Optional` is already imported in this module — it is used in `parse_existing_index`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_embeddings.py -k extract_entry_block -v`
Expected: PASS (4 tests). Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/build_shelf_index.py` → clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/build_shelf_index.py tests/test_kb_offline_embeddings.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): build_shelf_index.extract_entry_block — exact-id shelf block parser (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: M3b `_reduce_shelf` adopts the shared parser

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/retrieval.py`
- Test: `tests/test_kb_offline_retrieval.py`

**Contract (spec §5.1):** per page try `extract_entry_block` (real `## N.` format) first, then the legacy `- <path>` bullet line, and only synthesize `- <page_id>` when neither matches. Header ends **before the first real `## N.` entry header**; fall back to "before the first `- ` bullet" ONLY when the shelf has no real entry headers (pure-legacy). Bullet fallback requires exact `page_id`; basename match allowed only when the candidate is flat (no `/`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_retrieval.py`:
```python
from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index


def _real_shelf_lib(tmp_path, pages):
    # pages: {page_id: (layer, body)}
    lib = tmp_path / "library"
    lib.mkdir()
    for pid, (layer, body) in pages.items():
        (lib / pid).write_text(f"---\nlayer: {layer}\nconfidence: high\n---\n# {pid}\n{body}\n",
                               encoding="utf-8")
    rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
    return lib


def test_reduce_shelf_keeps_layer_and_facts_on_real_generated_shelf(tmp_path):
    from sdlc_knowledge_base_scripts.retrieval import _reduce_shelf
    lib = _real_shelf_lib(tmp_path, {"a.md": ("evidence", "Alpha deploys daily."),
                                     "b.md": ("domain", "Beta uses canary.")})
    reduced = _reduce_shelf(lib / "_shelf-index.md", ["b.md"])
    # the selected entry keeps its structured metadata (was stripped before this fix)
    assert "## " in reduced and "b.md" in reduced
    assert "Layer:** domain" in reduced
    # the UNSELECTED first entry is entirely absent (header boundary fix)
    assert "a.md" not in reduced
    assert "Alpha deploys daily." not in reduced


def test_reduce_shelf_bullet_format_still_works(tmp_path):
    from sdlc_knowledge_base_scripts.retrieval import _reduce_shelf
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(
        "<!-- format_version: 1 -->\n# Shelf Index\n\nIntro.\n- a.md — about a\n- b.md — about b\n",
        encoding="utf-8")
    reduced = _reduce_shelf(lib / "_shelf-index.md", ["b.md"])
    assert "Intro." in reduced and "about b" in reduced
    assert "about a" not in reduced


def test_reduce_shelf_synthesizes_when_neither_matches(tmp_path):
    from sdlc_knowledge_base_scripts.retrieval import _reduce_shelf
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf Index\n", encoding="utf-8")
    reduced = _reduce_shelf(lib / "_shelf-index.md", ["ghost.md"])
    assert "- ghost.md" in reduced


def test_reduce_shelf_bullet_basename_not_overmatched_for_nested(tmp_path):
    from sdlc_knowledge_base_scripts.retrieval import _reduce_shelf
    lib = tmp_path / "library"
    lib.mkdir()
    # candidate 'sub/a.md' must NOT match a root '- a.md' bullet (basename over-match guard)
    (lib / "_shelf-index.md").write_text(
        "<!-- format_version: 1 -->\n# Shelf Index\n\n- a.md — root a\n", encoding="utf-8")
    reduced = _reduce_shelf(lib / "_shelf-index.md", ["sub/a.md"])
    assert "- sub/a.md" in reduced     # synthesized, not matched to root a.md
    assert "root a" not in reduced
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_retrieval.py -k "real_generated_shelf or basename_not_overmatched" -v`
Expected: FAIL — the current `_reduce_shelf` strips metadata (matches only `- ` bullets) and its header detection ends at the first `- ` (a fact bullet inside entry 1), so a real shelf reduces to bare ids and leaks entry 1.

- [ ] **Step 3: Rewrite `_reduce_shelf`**

In `plugins/sdlc-knowledge-base/scripts/retrieval.py`, add the imports and replace `_reduce_shelf` (keep `_entry_id` and `accelerated_candidates` unchanged). New top-of-file imports:
```python
from pathlib import Path

from .build_shelf_index import _ENTRY_PATH_RE, extract_entry_block
```
Replace the existing `_reduce_shelf` function body with:
```python
def _reduce_shelf(shelf_path: Path, page_ids: list) -> str:
    """Header + the matching entry for each candidate in discovery-rank order. Per page: a real
    '## N. <id>' block (via extract_entry_block, keeping Hash/Layer/Confidence/Terms/Facts), else
    the legacy '- <id>' bullet line, else a synthetic '- <page_id>'. Header runs up to the first
    real '## N.' entry header; on a pure-legacy bullet shelf (no real headers) up to the first
    '- ' bullet instead."""
    text = shelf_path.read_text(encoding="utf-8") if shelf_path.is_file() else ""
    lines = text.splitlines()
    hdr_end = next((i for i, ln in enumerate(lines) if _ENTRY_PATH_RE.match(ln)), None)
    if hdr_end is None:
        hdr_end = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("- ")), len(lines))
    header, entries = lines[:hdr_end], lines[hdr_end:]
    chosen = []
    for pid in page_ids:
        block = extract_entry_block(text, pid)
        if block is not None:
            chosen.append(block.rstrip("\n"))
            continue
        base = pid.rsplit("/", 1)[-1]
        allowed = {pid} if "/" in pid else {pid, base}
        match = next((ln for ln in entries if _entry_id(ln) in allowed), None)
        chosen.append(match if match is not None else f"- {pid}")
    return "\n".join(header + chosen) + "\n"
```

(If `from pathlib import Path` is already imported in `retrieval.py`, do not duplicate it — only add the `build_shelf_index` import.)

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_retrieval.py -v`
Expected: PASS — including the pre-existing M3b tests (`test_accelerated_candidates_returns_topk_and_reduced_shelf`, `test_reduced_shelf_synthesizes_entry_when_shelf_has_no_bullet`, `test_reduced_shelf_exact_id_match_no_substring_collision`). Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/retrieval.py tests/test_kb_offline_retrieval.py` → clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/retrieval.py tests/test_kb_offline_retrieval.py
git commit -m "$(cat <<'EOF'
fix(kb-offline): _reduce_shelf adopts extract_entry_block (real shelf keeps metadata) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `canonicalize_attribution`

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/federation.py`
- Test: `tests/test_kb_offline_federation.py`

**Contract (spec §4):** after `verify_entailment`, rewrite each claim's `cited_pages` (qualified id → `PageRef(library=handle, page=page_id)`) and `evidence_spans` (→ `Span(library=handle, page=page_id, text=…)`) via `split_qualified`. Never re-grades.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_federation.py`:
```python
from sdlc_knowledge_base_scripts.federation import canonicalize_attribution


def test_canonicalize_attribution_splits_qualified_ids():
    c = Claim(
        text="Teams deploy daily.",
        cited_pages=[PageRef(library="x", page="acme-kb/a.md"),
                     PageRef(library="x", page="dora-corp/ops.md")],
        evidence_spans=[Span(page="acme-kb/a.md", text="deploy daily")],
    )
    c.entailment_status = EntailmentStatus.supported
    out = canonicalize_attribution(Answer(claims=[c], rendered_text=""))
    refs = out.claims[0].cited_pages
    assert (refs[0].library, refs[0].page) == ("acme-kb", "a.md")
    assert (refs[1].library, refs[1].page) == ("dora-corp", "ops.md")
    span = out.claims[0].evidence_spans[0]
    assert (span.library, span.page, span.text) == ("acme-kb", "a.md", "deploy daily")
    # grading preserved (never re-graded)
    assert out.claims[0].entailment_status == EntailmentStatus.supported
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -k canonicalize -v`
Expected: FAIL (ImportError: cannot import name `canonicalize_attribution`).

- [ ] **Step 3: Implement `canonicalize_attribution`**

In `plugins/sdlc-knowledge-base/scripts/federation.py`, update the imports and append the function. Change the contracts import line to also bring in `Span`, and add the `split_qualified` import:
```python
from .contracts import Answer, PageRef, Span
from .fusion import split_qualified
```
Append at end of file:
```python
def canonicalize_attribution(answer):
    """Rewrite each claim's qualified-id references to per-library attribution: cited_pages ->
    PageRef(library=handle, page=page_id) and evidence_spans -> Span(library=handle, page=page_id,
    text=...), splitting each 'handle/page_id' on the first '/'. Verifier grading is preserved."""
    out_claims = []
    for c in answer.claims:
        nc = c.model_copy(deep=True)
        nc.cited_pages = []
        for r in c.cited_pages:
            handle, page_id = split_qualified(r.page)
            nc.cited_pages.append(PageRef(library=handle, page=page_id))
        nc.evidence_spans = []
        for s in c.evidence_spans:
            handle, page_id = split_qualified(s.page)
            nc.evidence_spans.append(Span(library=handle, page=page_id, text=s.text))
        out_claims.append(nc)
    return Answer(claims=out_claims, rendered_text=answer.rendered_text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation.py -v`
Expected: PASS (all federation tests, no regressions). Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/federation.py tests/test_kb_offline_federation.py` → clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/federation.py tests/test_kb_offline_federation.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): federation.canonicalize_attribution — qualified id -> per-library refs (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: `accelerated_federation_query` (linear path) — happy path + core fallbacks

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/federation_accel.py`
- Test: `tests/test_kb_offline_federation_accel.py`

This task builds the whole linear function and its happy path + the gate fallbacks that are easy to stage. Task 7 adds the security/edge tests that exercise branches implemented here.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_federation_accel.py`:
```python
"""Accelerated federated query (linear path). kb-offline M3c-2 (#211)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
from sdlc_knowledge_base_scripts.embeddings import (
    EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
from sdlc_knowledge_base_scripts.federation_accel import accelerated_federation_query


def _build_lib(tmp_path, name, pages, vectors, *, model="fake-embed", extra_rows=None):
    """pages: {page_id: (layer, confidence, body)}; vectors: {page_id: [floats]}.
    extra_rows: optional [(page_id, content_hash, [floats])] tampered rows added to the store
    WITHOUT changing provenance.corpus_hash (simulates a corrupt/stale/tampered index row)."""
    lib = tmp_path / name
    lib.mkdir()
    for pid, (layer, conf, body) in pages.items():
        (lib / pid).write_text(
            f"---\nlayer: {layer}\nconfidence: {conf}\n---\n# {pid}\n{body}\n", encoding="utf-8")
    rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
    rows = chunk_pages(lib)                          # [(page_id, embed_text, content_hash)]
    ch = corpus_hash([(pid, h) for pid, _, h in rows])
    dims = len(next(iter(vectors.values())))
    mat = [vectors[pid] for pid, _, _ in rows]
    irows = [IndexRow(page_id=pid, content_hash=h) for pid, _, h in rows]
    if extra_rows:
        for pid, h, vec in extra_rows:
            mat.append(vec)
            irows.append(IndexRow(page_id=pid, content_hash=h))
    prov = Provenance(model=model, dims=dims, normalization="l2", corpus_hash=ch)
    EmbeddingStore.from_rows(np.array(mat, dtype=np.float32), irows, prov).save(lib)
    return lib


def _gen_factory(select_ids, claim_text, cited_qids, span_qid):
    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": select_ids})
        return json.dumps({"claims": [{
            "text": claim_text,
            "cited_pages": [{"library": "x", "page": q} for q in cited_qids],
            "evidence_spans": [{"page": span_qid, "text": "deploys daily"}]}],
            "rendered_text": ""})
    return gen


def test_accelerated_federation_happy_path_comparative_claim(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "Local note on deploys.")},
                       {"local.md": [1.0, 0.0, 0.0]})
    acme = _build_lib(tmp_path, "acme",
                      {"a.md": ("evidence", "high", "Acme deploys daily.")},
                      {"a.md": [1.0, 0.0, 0.0]})
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    be.generate = _gen_factory(
        ["library/local.md", "acme/a.md"], "Teams deploy daily.",
        ["acme/a.md", "library/local.md"], "acme/a.md")
    specs = [("library", str(local)), ("acme", str(acme))]
    out = accelerated_federation_query(local, specs, "how often deploy?", backend=be, search_k=5)
    assert out is not None
    assert "Teams deploy daily." in out["rendered_text"]
    # ONE synthesis over BOTH libraries -> attribution carries both handles
    assert "acme" in out["rendered_text"] and "library" in out["rendered_text"]
    assert out["queried"] == 2


def test_accelerated_falls_back_when_backend_has_no_embeddings(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "x")}, {"local.md": [1.0, 0.0, 0.0]})

    class _NoEmbed:                      # like AnthropicBackend: no embedding_model_id
        def generate(self, prompt, schema=None):
            return "{}"
    out = accelerated_federation_query(
        local, [("library", str(local))], "q", backend=_NoEmbed(), search_k=5)
    assert out is None                   # caller falls back to M2b


def test_accelerated_falls_back_when_index_stale(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "x")}, {"local.md": [1.0, 0.0, 0.0]})
    # mutate a page after indexing -> corpus_hash no longer matches
    (local / "local.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# changed\n",
                                    encoding="utf-8")
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    out = accelerated_federation_query(local, [("library", str(local))], "q", backend=be, search_k=5)
    assert out is None


def test_accelerated_falls_back_when_index_incompatible(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"local.md": ("evidence", "high", "x")}, {"local.md": [1.0, 0.0, 0.0]})
    other = _build_lib(tmp_path, "acme",
                       {"a.md": ("evidence", "high", "y")}, {"a.md": [1.0, 0.0, 0.0]},
                       model="other-embed")     # different model -> incompatible
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    specs = [("library", str(local)), ("acme", str(other))]
    out = accelerated_federation_query(local, specs, "q", backend=be, search_k=5)
    assert out is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation_accel.py -v`
Expected: FAIL (ModuleNotFoundError: `federation_accel`).

- [ ] **Step 3: Implement `accelerated_federation_query`**

Create `plugins/sdlc-knowledge-base/scripts/federation_accel.py`:
```python
"""Accelerated federated query (#211, M3c-2). Linear (no graph): load+validate every store once
(closes the gate/worker TOCTOU), embed the question once, search each library in library_specs
order, filter, coverage-guard, RRF-interleave into ONE cross-library candidate list, hand it to a
single reasoned select over a cross-library reduced shelf, then read/synthesize/verify across
libraries with canonical per-library attribution. Embeddings discover; the shelf reasons. Returns
None (all-or-nothing) so the CLI falls back to the M2b federation, never dropping coverage."""
from __future__ import annotations

import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from .audit import AuditEvent, log_event
from .build_shelf_index import extract_entry_block
from .embeddings import EmbeddingStore, chunk_pages, corpus_hash
from .entailment import verify_entailment
from .federation import _norm, canonicalize_attribution, render_federated
from .fusion import compatible, fuse_compatible, qualify, split_qualified
from .pipeline import select, synthesize
from .priming import build_priming_bundle
from .provenance import filter_pages


def _dedupe_specs(library_specs):
    """Drop duplicate handles (first-appearance kept) with a stderr warning. Required so the
    RRF one-list-per-item invariant holds and external libraries are not double-audited."""
    seen, out = set(), []
    for handle, path in library_specs:
        if handle in seen:
            print(f"accelerate: duplicate library handle {handle!r} dropped", file=sys.stderr)
            continue
        seen.add(handle)
        out.append((handle, path))
    return out


def _resolve_in_root(root_dir: Path, page_id: str):
    """Resolve page_id under root_dir, following symlinks, and require the resolved target to be
    contained by the resolved root (root in target.parents). Returns the resolved Path or None
    for traversal / symlink escape."""
    root = root_dir.resolve()
    target = (root_dir / page_id).resolve()
    if root not in target.parents:
        return None
    return target


def _cross_library_shelf(fused_qids, shelf_texts):
    """Concatenate, in fused order, each fused qid's real shelf block with its header rewritten to
    the qualified id ('## i. handle/page_id'); synthesize a bare header when no block is found."""
    parts = ["# Cross-library reduced shelf\n"]
    for i, qid in enumerate(fused_qids, 1):
        handle, page_id = split_qualified(qid)
        block = extract_entry_block(shelf_texts.get(handle, ""), page_id)
        if block is None:
            parts.append(f"## {i}. {qid}\n")
            continue
        rest = block.split("\n", 1)[1] if "\n" in block else ""
        parts.append(f"## {i}. {qid}\n{rest}")
    return "\n".join(parts).rstrip("\n") + "\n"


def accelerated_federation_query(local_lib, library_specs, question, *, backend,
                                 search_k=20, layer=None, min_confidence=None, audit=True):
    """library_specs = [(handle, path), ...] (first = local). Returns a result dict on success,
    or None if the all-or-nothing gate / query-vector validity / per-library coverage check fails
    (caller falls back to M2b). Read-only; no graph."""
    if search_k < 1:
        return None
    specs = _dedupe_specs(library_specs)
    if not specs:
        return None

    # --- Gate (§3): embedding-capable backend ---
    model_fn = getattr(backend, "embedding_model_id", None)
    if model_fn is None:
        print("accelerate: backend has no embedding model — falling back to federation", file=sys.stderr)
        return None
    ref_model = model_fn()

    # local reference index
    local_path = Path(specs[0][1])
    ref_store = EmbeddingStore.load(local_path)
    if ref_store is None:
        print("accelerate: local embedding index missing — falling back", file=sys.stderr)
        return None
    local_prov = ref_store.provenance
    if ref_model != local_prov.model:
        print("accelerate: backend model != local index model — falling back", file=sys.stderr)
        return None

    # load + validate every library once (no later reload — closes TOCTOU)
    stores = {}
    for handle, path in specs:
        st = EmbeddingStore.load(Path(path))
        if st is None:
            print(f"accelerate: library {handle!r} has no index — falling back", file=sys.stderr)
            return None
        fresh = corpus_hash([(pid, h) for pid, _, h in chunk_pages(path)])
        if st.provenance.corpus_hash != fresh:
            print(f"accelerate: library {handle!r} index stale — falling back", file=sys.stderr)
            return None
        if not compatible(local_prov, st.provenance):
            print(f"accelerate: library {handle!r} index incompatible — falling back", file=sys.stderr)
            return None
        stores[handle] = st

    # --- Embed once + validate (§3) ---
    qvecs = backend.embed([question])
    if len(qvecs) != 1:
        print("accelerate: embedding did not return exactly one vector — falling back", file=sys.stderr)
        return None
    qvec = list(qvecs[0])
    if len(qvec) != local_prov.dims or not all(math.isfinite(x) for x in qvec):
        print("accelerate: query vector invalid — falling back", file=sys.stderr)
        return None

    # --- Per-library search + filter + coverage guard (§5 step 3) ---
    per_lib_ranked = []   # (handle, prov, ranked) in library_specs order
    for handle, path in specs:
        st = stores[handle]
        live_ids = {pid for pid, _, _ in chunk_pages(path)}
        hits = st.search(qvec, k=search_k)
        cand = [pid for pid, _ in hits if pid in live_ids]   # drop tampered/stale/deleted rows
        ranked = filter_pages(Path(path), cand, layer=layer, min_confidence=min_confidence)
        if not ranked:
            eligible = filter_pages(Path(path), sorted(live_ids), layer=layer,
                                    min_confidence=min_confidence)
            if eligible:
                print(f"accelerate: embedding cut missed eligible pages in {handle!r} — falling back",
                      file=sys.stderr)
                return None
        per_lib_ranked.append((handle, st.provenance, ranked))

    # --- 3a: audit ONLY at the commit point (after every fallback-producing check) ---
    if audit:
        audit_log = Path(specs[0][1]) / ".kb-offline" / "audit.log"
        for handle, path in specs[1:]:
            log_event(audit_log, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="cross_library_query", query=question,
                source_handle=handle, reason="accelerated federated query",
                detail={"path": path}))

    # --- Fuse (deterministic, library order) ---
    fused, _ = fuse_compatible(local_prov, per_lib_ranked, k_const=60)
    cut = max(search_k, len(specs))
    fused_qids = [qualify(handle, page_id) for (handle, page_id), _ in fused[:cut]]

    # --- Cross-library reduced shelf ---
    shelf_texts = {}
    for handle, path in specs:
        sp = Path(path) / "_shelf-index.md"
        shelf_texts[handle] = sp.read_text(encoding="utf-8") if sp.is_file() else ""
    reduced = _cross_library_shelf(fused_qids, shelf_texts)

    # --- Priming + one reasoned select ---
    priming = build_priming_bundle(question, Path(specs[0][1]).parent)
    sel = select(question, None, backend=backend, known_pages=set(fused_qids),
                 priming=priming, shelf_text=reduced)

    # --- Read across libraries (path-containment enforced; symlinks resolved) ---
    path_for = {handle: Path(path) for handle, path in specs}
    pages = []
    for qid in sel.page_ids:
        handle, page_id = split_qualified(qid)
        root_dir = path_for.get(handle)
        if root_dir is None:
            continue
        target = _resolve_in_root(root_dir, page_id)
        if target is None or not target.is_file():
            continue
        pages.append({"page": qid, "content": target.read_text(encoding="utf-8")})

    # --- Synthesize + verify + canonicalize ---
    ans = synthesize(question, pages, backend=backend)
    pages_by_name = {p["page"]: p["content"] for p in pages}
    verified = verify_entailment(ans, pages_by_name, backend=backend)
    canonical = canonicalize_attribution(verified)

    # --- Attributed publish (handle_sets per claim from canonicalized cited_pages) ---
    handle_sets = {}
    for c in canonical.claims:
        key = _norm(c.text)
        hs = handle_sets.setdefault(key, [])
        for r in c.cited_pages:
            if r.library not in hs:
                hs.append(r.library)
    rendered, rejected = render_federated(canonical, handle_sets)
    return {"rendered_text": rendered, "rejected_claims": rejected,
            "_answer": canonical.model_dump(), "queried": len(specs),
            "fused": len(fused_qids), "deduped": 0}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation_accel.py -v`
Expected: PASS (4 tests). Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/federation_accel.py tests/test_kb_offline_federation_accel.py` → clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/federation_accel.py tests/test_kb_offline_federation_accel.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): accelerated_federation_query — linear RRF-fused cross-library query (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: `accelerated_federation_query` — security & edge tests

**Files:**
- Test: `tests/test_kb_offline_federation_accel.py` (append)

These tests exercise branches already implemented in Task 6 (dedup, live-corpus intersection, coverage guard, qvec validity, layer filter, path containment). If any fails, fix the Task 6 function (do not weaken the test) and re-run.

- [ ] **Step 1: Write the tests**

Append to `tests/test_kb_offline_federation_accel.py`:
```python
def test_path_containment_rejects_traversal_and_symlink_escape(tmp_path):
    from sdlc_knowledge_base_scripts.federation_accel import _resolve_in_root
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "a.md").write_text("ok", encoding="utf-8")
    # legit page resolves inside
    assert _resolve_in_root(lib, "a.md") == (lib / "a.md").resolve()
    # parent traversal rejected
    assert _resolve_in_root(lib, "../secret.md") is None
    # symlink escaping the library rejected (resolve() follows the link)
    outside = tmp_path / "secret.md"
    outside.write_text("secret", encoding="utf-8")
    (lib / "link.md").symlink_to(outside)
    assert _resolve_in_root(lib, "link.md") is None


def test_live_corpus_intersection_drops_tampered_index_row(tmp_path):
    # a '../secret.md' row is injected into the store WITHOUT changing corpus_hash; it ranks first
    # but must be dropped by the live-corpus intersection before search results are used.
    local = _build_lib(tmp_path, "library",
                       {"a.md": ("evidence", "high", "Alpha deploys daily.")},
                       {"a.md": [0.0, 1.0, 0.0]},
                       extra_rows=[("../secret.md", "tampered", [1.0, 0.0, 0.0])])
    (tmp_path / "secret.md").write_text("TOP SECRET", encoding="utf-8")
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]   # nearest the tampered row
    be.generate = _gen_factory(["library/a.md"], "Alpha deploys daily.",
                               ["library/a.md"], "library/a.md")
    out = accelerated_federation_query(local, [("library", str(local))], "q", backend=be, search_k=5)
    assert out is not None
    assert "TOP SECRET" not in out["rendered_text"]


def test_duplicate_handle_is_deduped_with_warning(tmp_path, capsys):
    local = _build_lib(tmp_path, "library",
                       {"a.md": ("evidence", "high", "Alpha deploys daily.")},
                       {"a.md": [1.0, 0.0, 0.0]})
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    be.generate = _gen_factory(["library/a.md"], "Alpha deploys daily.",
                               ["library/a.md"], "library/a.md")
    specs = [("library", str(local)), ("library", str(local))]   # duplicate handle
    out = accelerated_federation_query(local, specs, "q", backend=be, search_k=5)
    assert out is not None
    assert out["queried"] == 1
    assert "duplicate library handle" in capsys.readouterr().err


def test_coverage_guard_falls_back_when_filter_empties_eligible_library(tmp_path):
    # the library HAS an eligible (evidence) page, but search_k=1 surfaces only the domain page,
    # which the layer=evidence filter drops -> filtered-empty-but-eligible -> fall back.
    local = _build_lib(tmp_path, "library",
                       {"ev.md": ("evidence", "high", "Evidence page."),
                        "dom.md": ("domain", "high", "Domain page.")},
                       {"ev.md": [0.0, 1.0, 0.0], "dom.md": [1.0, 0.0, 0.0]})
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]   # nearest dom.md (filtered out by layer)
    out = accelerated_federation_query(local, [("library", str(local))], "q",
                                       backend=be, search_k=1, layer="evidence")
    assert out is None


def test_layer_filter_selects_only_matching_pages(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"ev.md": ("evidence", "high", "Evidence deploys daily."),
                        "dom.md": ("domain", "high", "Domain note.")},
                       {"ev.md": [1.0, 0.0, 0.0], "dom.md": [0.0, 1.0, 0.0]})
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    be.generate = _gen_factory(["library/ev.md"], "Evidence deploys daily.",
                               ["library/ev.md"], "library/ev.md")
    out = accelerated_federation_query(local, [("library", str(local))], "q",
                                       backend=be, search_k=5, layer="evidence")
    assert out is not None and "Evidence deploys daily." in out["rendered_text"]


def test_invalid_query_vector_falls_back(tmp_path):
    local = _build_lib(tmp_path, "library",
                       {"a.md": ("evidence", "high", "x")}, {"a.md": [1.0, 0.0, 0.0]})
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0]]        # wrong dim (2 != 3) -> fall back
    out = accelerated_federation_query(local, [("library", str(local))], "q", backend=be, search_k=5)
    assert out is None
```

- [ ] **Step 2: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_federation_accel.py -v`
Expected: PASS (all Task 6 + Task 7 tests). If a branch is missing in `federation_accel.py`, fix it there and re-run.

- [ ] **Step 3: Lint**

Run: `.venv/bin/python -m flake8 --max-line-length=127 tests/test_kb_offline_federation_accel.py`
Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add tests/test_kb_offline_federation_accel.py
git commit -m "$(cat <<'EOF'
test(kb-offline): accel federation security/edge cases — traversal, dedup, coverage, qvec (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: CLI routing + `--accelerate-k >= 1` validation

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`
- Test: `tests/test_kb_offline_cli.py`

**Contract (spec §6):** `--libraries … --accelerate` routes to `accelerated_federation_query`; on `None` it falls back to the M2b `federation_query_graph` (with a stderr warning). `--accelerate-k` is argparse-validated `>= 1`. The post-query print/save block is shared between the accelerated and M2b paths.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_cli.py` (uses the existing `library_specs_override` test seam; check the top of the file for the established import of `main` and reuse it):
```python
def test_accelerate_k_below_one_is_rejected():
    import pytest as _pytest
    from sdlc_knowledge_base_scripts.kb_offline_cli import main
    with _pytest.raises(SystemExit):
        main(["query", "q", "--libraries", "acme", "--accelerate", "--accelerate-k", "0"])


def test_accelerate_routes_to_accel_then_falls_back_to_m2b(tmp_path, monkeypatch, capsys):
    from sdlc_knowledge_base_scripts import kb_offline_cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    calls = {"accel": 0, "m2b": 0}

    def fake_accel(local_lib, specs, question, **kw):
        calls["accel"] += 1
        return None                      # force the fallback path

    class _Graph:
        def invoke(self, state, config=None):
            calls["m2b"] += 1
            return {"rendered_text": "FELL BACK", "rejected_claims": [],
                    "_answer": {"claims": []}, "queried": 1, "deduped": 0}

    monkeypatch.setattr("sdlc_knowledge_base_scripts.federation_accel.accelerated_federation_query",
                        fake_accel)
    monkeypatch.setattr(
        "sdlc_knowledge_base_scripts.graphs.federation_query_graph.build_federation_query_graph",
        lambda backend: _Graph())

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n", encoding="utf-8")
    specs = [["library", str(lib)], ["acme", str(lib)]]
    rc = kb_offline_cli.main(
        ["query", "q", "--library", str(lib), "--libraries", "acme", "--accelerate"],
        backend_override=FakeBackend(), library_specs_override=specs)
    assert rc == 0
    assert calls["accel"] == 1 and calls["m2b"] == 1
    assert "FELL BACK" in capsys.readouterr().out


def test_accelerate_uses_accel_result_when_not_none(tmp_path, monkeypatch, capsys):
    from sdlc_knowledge_base_scripts import kb_offline_cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    def fake_accel(local_lib, specs, question, **kw):
        return {"rendered_text": "ACCEL ANSWER", "rejected_claims": [],
                "_answer": {"claims": []}, "queried": 2, "deduped": 0}

    monkeypatch.setattr("sdlc_knowledge_base_scripts.federation_accel.accelerated_federation_query",
                        fake_accel)
    lib = tmp_path / "library"
    lib.mkdir()
    specs = [["library", str(lib)], ["acme", str(lib)]]
    rc = kb_offline_cli.main(
        ["query", "q", "--library", str(lib), "--libraries", "acme", "--accelerate"],
        backend_override=FakeBackend(), library_specs_override=specs)
    assert rc == 0
    assert "ACCEL ANSWER" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k "accelerate" -v`
Expected: FAIL — `--accelerate-k 0` is accepted (no validation), and `--libraries --accelerate` runs M2b directly (no accel routing).

- [ ] **Step 3: Add `--accelerate-k` validation**

In `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`, add a positive-int argparse type near the other module-level helpers (above `main`):
```python
def _positive_int(s: str) -> int:
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError("--accelerate-k must be >= 1")
    return v
```
Then change the `query` subparser's flag from:
```python
    p_q.add_argument("--accelerate-k", type=int, default=20)
```
to:
```python
    p_q.add_argument("--accelerate-k", type=_positive_int, default=20)
```

- [ ] **Step 4: Extract the shared result emitter + route to accel**

In `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`, add a shared emitter (place it directly above `_cmd_query`):
```python
def _emit_federation_result(args, out, specs) -> int:
    print(out.get("rendered_text", ""))
    rejected = out.get("rejected_claims", [])
    if rejected:
        print(f"\n[{len(rejected)} claim(s) excluded as unsupported]", file=sys.stderr)
    claims_n = len(out.get("_answer", {}).get("claims", []))
    print(f"\nqueried {out.get('queried', 0)} libraries ({claims_n} claims, "
          f"{out.get('deduped', 0)} deduped)")
    if args.save:
        from .answers import save_answer
        from .contracts import Answer

        verified = Answer.model_validate(out["_answer"])
        ref = save_answer(args.library, args.question, verified,
                          libraries=[h for h, _ in specs], page_ids=[])
        print(f"saved: {ref}")
    return 0
```
Then replace the body of `_cmd_query` (the federation portion, after `specs`/`warnings` are resolved and the `if not specs:` guard) so it tries the accelerated path first when `--accelerate` is set, and uses the shared emitter for both paths. The resulting `_cmd_query` reads:
```python
def _cmd_query(args: argparse.Namespace, backend_override, library_specs_override=None) -> int:
    backend = _make_backend(args.backend, backend_override)
    if not getattr(args, "libraries", None) and library_specs_override is None:
        return _query_single(args, backend)

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

    specs = [tuple(s) for s in specs]
    if getattr(args, "accelerate", False):
        from .federation_accel import accelerated_federation_query
        result = accelerated_federation_query(
            local_lib, specs, args.question, backend=backend,
            search_k=getattr(args, "accelerate_k", 20),
            layer=args.layer, min_confidence=args.min_confidence)
        if result is not None:
            return _emit_federation_result(args, result, specs)
        print("accelerate: falling back to full federation", file=sys.stderr)

    from .graphs.federation_query_graph import build_federation_query_graph

    graph = build_federation_query_graph(backend)
    # Priming reads <project>/CLAUDE.md and <project>/library/_shelf-index.md, so
    # local_project_dir must be the PROJECT ROOT, not the library dir. The library is
    # conventionally <project>/library, so the project root is its parent.
    project_dir = local_lib.parent
    out = graph.invoke(
        {"library_specs": [list(s) for s in specs], "local_project_dir": str(project_dir),
         "question": args.question, "layer": args.layer, "min_confidence": args.min_confidence},
        config={"configurable": {"thread_id": "federated-query"}, "max_concurrency": 8})
    return _emit_federation_result(args, out, specs)
```

Notes for the implementer:
- `specs = [tuple(s) for s in specs]` normalizes both the `[name, path]` lists from `_resolve_libraries`/`library_specs_override` and any tuples into `(handle, path)` tuples (what `accelerated_federation_query` expects); the M2b graph wants lists, so it is re-listed at `graph.invoke`.
- The M2b graph node `n_query_one` reads `state["layer"]`/`state["min_confidence"]` directly, so keep passing them.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -v`
Expected: PASS (new accelerate tests + all pre-existing CLI tests — the M2b federation path is behaviourally unchanged, now routed through `_emit_federation_result`). Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py` → clean.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): route query --libraries --accelerate to accel fn with M2b fallback (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Live Ollama smoke coverage (optional flag)

**Files:**
- Test: `tests/test_kb_offline_ollama_smoke.py` (append)

The live smoke suite is gated behind the real Ollama backend (skipped when unavailable). Add one accelerated-federation smoke that builds two small real-indexed libraries and asserts the accelerated path returns a non-None result (or cleanly falls back). Follow the existing skip/guard pattern already in this file.

- [ ] **Step 1: Inspect the existing live-smoke guard**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -v` (observe how it skips without Ollama) and read the top of the file to reuse its `pytestmark` / skip fixture and its real-backend constructor.

- [ ] **Step 2: Write the smoke test**

Append a test mirroring the file's existing style (reuse its real-backend fixture; build two libraries with `rebuild_shelf_index` + a real `index` so `EmbeddingStore.load` succeeds against the live embedding model):
```python
def test_accelerated_federation_smoke(tmp_path, ollama_backend):  # fixture name per this file
    from sdlc_knowledge_base_scripts.federation_accel import accelerated_federation_query
    # build_two_real_indexed_libraries: write pages, rebuild_shelf_index, then run the CLI
    # `index` command (or embeddings build) so each library has a live EmbeddingStore.
    local, acme = _two_indexed_libs(tmp_path, ollama_backend)   # helper local to this test file
    out = accelerated_federation_query(
        local, [("library", str(local)), ("acme", str(acme))],
        "how often do elite teams deploy?", backend=ollama_backend, search_k=8)
    # Either accelerated federation runs end-to-end, or it cleanly falls back (None) — both are valid;
    # the smoke asserts no crash and a usable shape when present.
    assert out is None or "rendered_text" in out
```

If the file has no reusable two-library indexing helper, add a small `_two_indexed_libs` near the top of the test module that writes pages, calls `rebuild_shelf_index`, and builds + saves an `EmbeddingStore` from `chunk_pages` using `ollama_backend.embed`.

- [ ] **Step 3: Run (skips without Ollama)**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -v`
Expected: PASS or SKIP (skipped when Ollama is not running — never fails the suite in CI).

- [ ] **Step 4: Commit**

```bash
git add tests/test_kb_offline_ollama_smoke.py
git commit -m "$(cat <<'EOF'
test(kb-offline): live Ollama smoke for accelerated federation (skips w/o Ollama) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Final verification (after all tasks)

- [ ] **Full kb-offline suite green**

Run: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q`
Expected: all pass; no regressions in pipeline/query-graph/federation-graph/embeddings/retrieval/contracts.

- [ ] **Lint the whole changed surface**

Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/fusion.py plugins/sdlc-knowledge-base/scripts/contracts.py plugins/sdlc-knowledge-base/scripts/build_shelf_index.py plugins/sdlc-knowledge-base/scripts/retrieval.py plugins/sdlc-knowledge-base/scripts/federation.py plugins/sdlc-knowledge-base/scripts/federation_accel.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`
Expected: clean.

---

## Self-review notes

**Spec coverage:**
- §1 qualified-id helpers → Task 1. §2 RRF-is-interleaving + deterministic library-order → guaranteed by `fuse_compatible` over `per_lib_ranked` built in `library_specs` order (Task 6); the happy-path comparative test asserts both libraries' rank-1 survive and attribute. §3 all-or-nothing gate (dedupe → embedding-capable backend → local ref → per-lib load/fresh/compatible → backend model == ref model) + query-vector validity → Task 6 (`_dedupe_specs`, gate loop, embed-once validity) + Task 7 (dedup, stale, incompatible, no-embeddings, qvec-invalid tests). §4 `Span.library` + `canonicalize_attribution` → Tasks 2 + 5. §5 linear function steps 1–10 → Task 6; step-3 live-corpus intersection + coverage guard → Task 6 + Task 7 (tampered-row drop, coverage-guard fallback); step-3a audit-at-commit-point → Task 6 (audit loop placed after all fallback checks); step-8 path containment via `_resolve_in_root` (resolve + `root in target.parents`, symlink-safe per the user's note) → Task 6 + Task 7 (traversal/symlink test). §5.1 `extract_entry_block` + `_reduce_shelf` adoption (header boundary, bullet exact/basename-flat) → Tasks 3 + 4. §6 CLI routing + `--accelerate-k >= 1` + shared emitter → Task 8.
- Out-of-scope items (M3c-3, M3d, mid-call re-index) correctly excluded.

**Placeholder scan:** No TBD/TODO. Every code step shows complete code. Task 9's live-smoke helper names (`ollama_backend` fixture, `_two_indexed_libs`) are flagged as "match this file's existing pattern" because the live-smoke harness conventions live in that file — Step 1 inspects them before writing; this is a deliberate "follow the established fixture" instruction, not a placeholder for production code.

**Type/name consistency:** `qualify(handle, page_id) -> str` / `split_qualified(qid) -> (handle, page_id)` used identically in `federation_accel` and `canonicalize_attribution`. `extract_entry_block(shelf_text, file_path) -> str | None` consumed by both `_cross_library_shelf` (Task 6) and `_reduce_shelf` (Task 4). `accelerated_federation_query(local_lib, library_specs, question, *, backend, search_k, layer, min_confidence, audit)` — the CLI (Task 8) calls it with `search_k=accelerate_k, layer, min_confidence` and positional `(local_lib, specs, args.question)`, matching the signature. Result dict keys (`rendered_text`, `rejected_claims`, `_answer`, `queried`, `deduped`) match what `_emit_federation_result` reads. `fuse_compatible` entries `(handle, prov, ranked)` and fused items `((handle, page_id), score)` match the M3c-1 contract. `_resolve_in_root` returns `Path | None`, checked before `.is_file()`.

**Defense-in-depth note (honest):** the read-step `target.is_file()` guard is effectively unreachable in the single-process tool (every `page_id` that survives the live-corpus intersection came from `chunk_pages`, which only enumerates existing files, and nothing deletes between gate and read) — it is kept as cheap safety and is intentionally NOT given a dedicated test (it cannot be reached without contrivance). The traversal/symlink rejection in `_resolve_in_root` IS reachable and IS tested directly.

# kb-offline Slice 2 — synthesize-side cited-page normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover model citation/​span page-id corruption on the synthesize side by rewriting a corrupted id to a page actually read, only on a unique high-confidence match (fail-closed), so q035's false abstention flips to supported and `abstention_precision` rises — without reopening the anti-fabrication hole.

**Architecture:** A new frozen pure helper (`cited_page_normalize.py`) does opaque-string fuzzy resolution (exact-first, `difflib` ratio, floor 0.75 + runner-up margin 0.10, single-candidate margin bypass, rejected-score retention). `synthesize` invokes it per claim against the read-page set — normalizing **evidence spans then citations, before the existing back-fill** — and appends auditable rewrite records to an optional diagnostics sink. The graph node carries the sink to the eval trace as an `id_rewrites` field. Select-side is untouched by design.

**Tech Stack:** Python 3.14, Pydantic v2 (`PageRef`/`Span`/`Claim`/`Answer` BaseModels), `difflib.SequenceMatcher`, LangGraph (query graph state), pytest + `FakeBackend`. Env: `.venv/bin/python`; package import root `sdlc_knowledge_base_scripts` (registered by `tests/conftest.py`); flake8 `--max-line-length=127`.

**Spec:** `docs/superpowers/specs/2026-06-22-kb-offline-cited-page-normalize-design.md`

---

## File Structure

- **Create** `plugins/sdlc-knowledge-base/scripts/cited_page_normalize.py` — the frozen helper (`Resolution`, `resolve_cited_page`, `normalize_cited_page`). One responsibility: opaque-string fuzzy id resolution. No handle/library/pipeline awareness.
- **Modify** `plugins/sdlc-knowledge-base/scripts/pipeline.py` — `synthesize` gains a `rewrites_sink` param and the normalize-spans-then-citations-before-backfill step; add a tiny local `_handle()` bucketer.
- **Modify** `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py` — `QueryState` gains `_id_rewrites`; `n_synthesize` allocates a sink, passes it, returns it.
- **Modify** `plugins/sdlc-knowledge-base/scripts/eval/runner.py` — `_build_question_trace` emits `id_rewrites` (always serialized).
- **Create** `research/kb-offline-eval/harness/calibrate_id_normalize.py` — reproducible calibration over the committed trace + runtime-subset perturbation sweep.
- **Create** tests: `tests/test_kb_offline_cited_page_normalize.py`, `tests/test_kb_offline_calibrate_id_normalize.py`; **extend** `tests/test_kb_offline_pipeline.py` and `tests/test_kb_offline_eval_runner.py`.

---

## Task 1: Frozen helper `cited_page_normalize.py`

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/cited_page_normalize.py`
- Test: `tests/test_kb_offline_cited_page_normalize.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_cited_page_normalize.py`:

```python
"""Frozen cited-page normalizer (#211, Slice 2). Opaque, case-sensitive, fail-closed."""
import pytest

from sdlc_knowledge_base_scripts.cited_page_normalize import (
    Resolution,
    normalize_cited_page,
    resolve_cited_page,
)


def test_exact_match_bypasses_fuzzy_with_score_one():
    # exact candidate resolves immediately at 1.0 even with another near candidate present
    res = resolve_cited_page("a.md", ["a.md", "a-x.md"])
    assert res == Resolution(page="a.md", score=1.0, runner_up=None)


def test_q035_recovers_above_floor():
    assert normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"]) == "sdlc-single-team.md"


def test_q052_drops_below_floor_but_retains_score():
    res = resolve_cited_page("pair-summary.md", ["pair-programming.md"])
    assert res.page is None
    assert res.score == pytest.approx(0.588, abs=0.01)
    assert res.runner_up is None  # single candidate


def test_empty_candidates_score_none():
    assert resolve_cited_page("x.md", []) == Resolution(page=None, score=None, runner_up=None)
    assert normalize_cited_page("x.md", []) is None


def test_ambiguous_two_close_candidates_drop():
    # two candidates within margin of each other -> ambiguous -> None, scores retained
    res = resolve_cited_page("sdlc-single-tt.md", ["sdlc-single-team.md", "sdlc-single-tesm.md"])
    assert res.page is None
    assert res.score is not None and res.runner_up is not None
    assert (res.score - res.runner_up) < 0.10


def test_single_candidate_above_floor_recovers_margin_bypassed():
    # one distinct candidate: margin check skipped, recover iff >= floor, even with floor<margin
    assert normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"],
                                floor=0.75, margin=0.99) == "sdlc-single-team.md"


def test_single_candidate_below_floor_drops():
    assert normalize_cited_page("pair-summary.md", ["pair-programming.md"]) is None


def test_boundary_score_exactly_at_floor_accepted():
    # choose a candidate whose ratio == floor exactly is brittle; instead assert >= semantics
    # by setting floor to the measured best score and expecting acceptance.
    best = resolve_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"]).score
    assert normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"],
                                floor=best) == "sdlc-single-team.md"


def test_boundary_margin_exactly_at_margin_accepted():
    cands = ["sdlc-single-team.md", "pair-programming.md"]
    res = resolve_cited_page("sdlc-single-formm.md", cands)
    lead = res.score - res.runner_up
    assert normalize_cited_page("sdlc-single-formm.md", cands, margin=lead) == "sdlc-single-team.md"


def test_duplicate_candidates_deduped_no_false_ambiguity():
    # duplicates of the single good candidate must not register as a second candidate
    assert normalize_cited_page("sdlc-single-formm.md",
                                ["sdlc-single-team.md", "sdlc-single-team.md"]) == "sdlc-single-team.md"


def test_case_sensitive_not_exact():
    # different case is NOT an exact match; recovers only if ratio clears the floor
    res = resolve_cited_page("SDLC-Single-Team.md", ["sdlc-single-team.md"])
    assert res.score is not None and res.score < 1.0


def test_deterministic_order_independent_of_input_order():
    a = normalize_cited_page("sdlc-single-formm.md", ["tech-debt.md", "sdlc-single-team.md"])
    b = normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md", "tech-debt.md"])
    assert a == b == "sdlc-single-team.md"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cited_page_normalize.py -q`
Expected: collection/import error — `ModuleNotFoundError: ... cited_page_normalize`.

- [ ] **Step 3: Write the helper**

Create `plugins/sdlc-knowledge-base/scripts/cited_page_normalize.py`:

```python
"""Narrow fuzzy recovery of corrupted cited-page ids (#211, Slice 2).

Synthesize-side ONLY: repair a model citation/span page-id back to a page actually read,
when there is a unique high-confidence match above a calibrated floor and runner-up margin.
Page ids are opaque, case-sensitive strings; the function is fail-closed (returns no page
when uncertain). No handle/library awareness — same-handle bucketing lives in the caller.

Spec: docs/superpowers/specs/2026-06-22-kb-offline-cited-page-normalize-design.md
"""
from __future__ import annotations

import difflib
from collections.abc import Collection
from typing import NamedTuple


class Resolution(NamedTuple):
    page: str | None        # resolved candidate, or None when no confident match
    score: float | None     # best ratio among candidates; None ONLY for an empty set.
    runner_up: float | None  # second-best score, or None when <2 distinct candidates


def resolve_cited_page(
    cited_page: str,
    candidates: Collection[str],
    *,
    floor: float = 0.75,
    margin: float = 0.10,
) -> Resolution:
    """Resolve a (possibly corrupted) page id against candidates. Frozen decision function."""
    uniq = sorted(set(candidates))  # dedupe + deterministic order before scoring
    if not uniq:
        return Resolution(None, None, None)
    if cited_page in uniq:  # exact match bypasses fuzzy floor/margin entirely
        return Resolution(cited_page, 1.0, None)
    scored = sorted(
        ((difflib.SequenceMatcher(None, cited_page, c).ratio(), c) for c in uniq),
        key=lambda t: (-t[0], t[1]),
    )
    best_score, best = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else None
    if best_score < floor:  # >= floor accepted (boundary)
        return Resolution(None, best_score, runner_up)
    # single distinct candidate: margin check bypassed (no runner-up => cannot be ambiguous)
    if runner_up is not None and (best_score - runner_up) < margin:  # >= margin accepted
        return Resolution(None, best_score, runner_up)
    return Resolution(best, best_score, runner_up)


def normalize_cited_page(
    cited_page: str,
    candidates: Collection[str],
    *,
    floor: float = 0.75,
    margin: float = 0.10,
) -> str | None:
    """Narrow str|None wrapper over resolve_cited_page (contract callers + unit tests)."""
    return resolve_cited_page(cited_page, candidates, floor=floor, margin=margin).page
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cited_page_normalize.py -q`
Expected: all pass. Then `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/cited_page_normalize.py tests/test_kb_offline_cited_page_normalize.py` — no output.

If `test_ambiguous_two_close_candidates_drop` does not actually produce two within-margin scores, adjust the second candidate string until the two ratios are within 0.10 of each other (verify with a one-off `resolve_cited_page(...)` print); the test asserts the relationship it sets up, so keep the assertion and fix the fixture strings.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/cited_page_normalize.py tests/test_kb_offline_cited_page_normalize.py
git commit -m "feat(kb-offline): frozen cited-page normalizer — exact-first, floor+margin, fail-closed (#211)"
```

---

## Task 2: Wire normalization into `synthesize` (spans→citations, before back-fill)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/pipeline.py` (`synthesize`, ~line 143; per-claim loop ~158-177)
- Test: `tests/test_kb_offline_pipeline.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_pipeline.py` (it already imports `json`, `FakeBackend`, and at top-of-file `from ... import PageRef`; add imports inside each test as the existing tests do):

```python
def test_synthesize_recovers_corrupted_span_id_and_backfills():
    """q035 shape: raw cited_pages omitted, corrupted id only on the span. Normalizing the
    span (before back-fill) lets the back-fill produce a correct citation and grounding pass."""
    from sdlc_knowledge_base_scripts.contracts import EntailmentStatus
    from sdlc_knowledge_base_scripts.entailment import ground_claim
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "The single-team method suits one collaborating team.",
            "evidence_spans": [{"page": "sdlc-single-formm.md",
                                "text": "The single-team method suits one collaborating team."}],
        }],
        "rendered_text": "ok",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    pages = [{"page": "sdlc-single-team.md",
              "content": "The single-team method suits one collaborating team."}]
    sink: list = []
    ans = synthesize("q", pages, backend=be, rewrites_sink=sink)
    # span normalized, then back-fill -> correct citation
    assert [s.page for s in ans.claims[0].evidence_spans] == ["sdlc-single-team.md"]
    assert [r.page for r in ans.claims[0].cited_pages] == ["sdlc-single-team.md"]
    cap = ground_claim(ans.claims[0],
                       {"sdlc-single-team.md": "The single-team method suits one collaborating team."})
    assert cap == EntailmentStatus.supported
    # exactly one evidence_span rewrite, zero cited_page rewrites; 3-dp score
    kinds = [r["reference_kind"] for r in sink]
    assert kinds == ["evidence_span"]
    r = sink[0]
    assert (r["from"], r["to"]) == ("sdlc-single-formm.md", "sdlc-single-team.md")
    assert r["handle"] == "" and r["claim_index"] == 0 and r["reference_index"] == 0
    assert r["candidates"] == ["sdlc-single-team.md"] and r["stage"] == "synthesize"
    assert r["score"] == round(r["score"], 3) and 0.75 <= r["score"] <= 1.0


def test_synthesize_drops_genuinely_different_id_no_rewrite():
    """q052 shape: corrupted id is genuinely different (below floor) -> untouched, no record."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "x",
            "evidence_spans": [{"page": "pair-summary.md", "text": "y"}],
        }],
        "rendered_text": "x",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    sink: list = []
    ans = synthesize("q", [{"page": "pair-programming.md", "content": "..."}],
                     backend=be, rewrites_sink=sink)
    assert [s.page for s in ans.claims[0].evidence_spans] == ["pair-summary.md"]  # untouched
    assert sink == []


def test_synthesize_cross_handle_match_not_recovered():
    """A qualified-id corruption whose only good match is under a DIFFERENT handle must drop."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "x",
            "evidence_spans": [{"page": "alpha/sdlc-single-formm.md", "text": "y"}],
        }],
        "rendered_text": "x",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    sink: list = []
    # only candidate is under handle 'beta' -> different bucket -> no recovery
    ans = synthesize("q", [{"page": "beta/sdlc-single-team.md", "content": "..."}],
                     backend=be, rewrites_sink=sink)
    assert [s.page for s in ans.claims[0].evidence_spans] == ["alpha/sdlc-single-formm.md"]
    assert sink == []


def test_synthesize_without_sink_still_recovers():
    """Production callers (federation/accel) pass no sink: recovery still happens, no crash."""
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{
            "text": "z",
            "evidence_spans": [{"page": "sdlc-single-formm.md", "text": "z"}],
        }],
        "rendered_text": "z",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    ans = synthesize("q", [{"page": "sdlc-single-team.md", "content": "z"}], backend=be)
    assert [s.page for s in ans.claims[0].evidence_spans] == ["sdlc-single-team.md"]


def test_synthesize_safety_rewrite_target_always_in_read_set():
    """Invariant: any rewrite 'to' is a page actually read, same handle as 'from'."""
    from sdlc_knowledge_base_scripts.cited_page_normalize import resolve_cited_page  # noqa: F401
    from sdlc_knowledge_base_scripts.pipeline import synthesize

    payload = json.dumps({
        "claims": [{"text": "z", "evidence_spans": [{"page": "sdlc-single-formm.md", "text": "z"}]}],
        "rendered_text": "z",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    read = ["sdlc-single-team.md"]
    sink: list = []
    synthesize("q", [{"page": p, "content": "z"} for p in read], backend=be, rewrites_sink=sink)
    for r in sink:
        assert r["to"] in read
        assert (r["to"].split("/", 1)[0] if "/" in r["to"] else "") == r["handle"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_pipeline.py -q -k "recovers or genuinely_different or cross_handle or without_sink or safety_rewrite"`
Expected: FAIL — `synthesize() got an unexpected keyword argument 'rewrites_sink'` (and recovery assertions fail).

- [ ] **Step 3: Modify `synthesize`**

In `plugins/sdlc-knowledge-base/scripts/pipeline.py`, add the import near the other local imports at the top of the file:

```python
from .cited_page_normalize import resolve_cited_page
```

Add this module-level helper just above `def synthesize(`:

```python
def _handle(page_id: str) -> str:
    """Namespace bucket for same-library scoping: handle for qualified ids, '' for bare."""
    return page_id.split("/", 1)[0] if "/" in page_id else ""
```

Change the signature:

```python
def synthesize(question, pages, *, backend, max_repairs: int = 1,
               rewrites_sink: list | None = None) -> Answer:
```

Just before the `for c in ans.claims:` loop, compute the read-set once:

```python
        read_ids = sorted({p["page"] for p in pages})
```

Inside the loop, immediately after `c.entailment_status = None` and `c.high_impact = False` and **before** the `if not c.cited_pages and c.evidence_spans:` back-fill block, insert (use the loop index `ci`; change `for c in ans.claims:` to `for ci, c in enumerate(ans.claims):`):

```python
            # Slice 2 (#211): repair corrupted page-id references against the read-set —
            # spans FIRST so the back-fill below propagates the corrected id into cited_pages.
            # Same-handle scoped, unique-winner + margin, fail-closed. See cited_page_normalize.
            for kind, refs in (("evidence_span", c.evidence_spans), ("cited_page", c.cited_pages)):
                for ri, ref in enumerate(refs):
                    if ref.page in read_ids:
                        continue
                    cands = [r for r in read_ids if _handle(r) == _handle(ref.page)]
                    res = resolve_cited_page(ref.page, cands)
                    if res.page is not None and res.page != ref.page:
                        if rewrites_sink is not None:
                            rewrites_sink.append({
                                "from": ref.page, "to": res.page,
                                "score": round(res.score, 3), "handle": _handle(ref.page),
                                "candidates": cands, "stage": "synthesize",
                                "claim_index": ci, "reference_kind": kind, "reference_index": ri,
                            })
                        refs[ri] = ref.model_copy(update={"page": res.page})
```

Leave the existing back-fill block and the abstention-invariant block that follow it unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_pipeline.py -q`
Expected: all pass (including the pre-existing back-fill/sentinel/select tests).
Then flake8: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_pipeline.py` — no output.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_pipeline.py
git commit -m "feat(kb-offline): synthesize normalizes corrupted span/citation ids before back-fill (#211)"
```

---

## Task 3: Carry rewrites to the eval trace (`_id_rewrites` → `id_rewrites`)

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py` (`QueryState` ~line 30; `n_synthesize` ~line 99)
- Modify: `plugins/sdlc-knowledge-base/scripts/eval/runner.py` (`_build_question_trace` ~line 114)
- Test: `tests/test_kb_offline_eval_runner.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_eval_runner.py`:

```python
def test_build_question_trace_surfaces_id_rewrites():
    """The carrier: _build_question_trace emits id_rewrites from out['_id_rewrites']."""
    from sdlc_knowledge_base_scripts.contracts import Answer
    from sdlc_knowledge_base_scripts.eval.runner import _build_question_trace
    from sdlc_knowledge_base_scripts.eval.suite import load_questions

    q = load_questions(SMOKE / "questions.jsonl")[0]
    rewrites = [{"from": "x.md", "to": "y.md", "score": 0.821, "handle": "",
                 "candidates": ["y.md"], "stage": "synthesize",
                 "claim_index": 0, "reference_kind": "evidence_span", "reference_index": 0}]
    out = {"_synth": Answer().model_dump(), "pages": [], "page_ids": [],
           "_id_rewrites": rewrites}
    row = _build_question_trace(q, out, [], 1.0, known=set(), eligible=set(),
                                found=[], did_abstain=True, rendered="")
    assert row["id_rewrites"] == rewrites


def test_build_question_trace_id_rewrites_defaults_empty():
    """Always-serialized: absent _id_rewrites -> id_rewrites == []."""
    from sdlc_knowledge_base_scripts.contracts import Answer
    from sdlc_knowledge_base_scripts.eval.runner import _build_question_trace
    from sdlc_knowledge_base_scripts.eval.suite import load_questions

    q = load_questions(SMOKE / "questions.jsonl")[0]
    out = {"_synth": Answer().model_dump(), "pages": [], "page_ids": []}
    row = _build_question_trace(q, out, [], 1.0, known=set(), eligible=set(),
                               found=[], did_abstain=True, rendered="")
    assert row["id_rewrites"] == []
```

Note: this file already defines `SMOKE = Path("plugins/sdlc-knowledge-base/eval/suite/smoke")` and imports `load_questions` from `sdlc_knowledge_base_scripts.eval.suite` (verified). `_build_question_trace` is a module-level function in `eval/runner.py` — import it directly.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_eval_runner.py -q -k id_rewrites`
Expected: FAIL — `KeyError: 'id_rewrites'`.

- [ ] **Step 3: Wire the carrier**

In `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py`, add to the `QueryState` TypedDict body (alongside `_synth`/`_answer`):

```python
    _id_rewrites: list
```

Replace `n_synthesize`:

```python
    def n_synthesize(state: QueryState) -> dict:
        sink: list = []
        ans = synthesize(state["question"], state["pages"], backend=backend, rewrites_sink=sink)
        return {"_synth": ans.model_dump(), "_id_rewrites": sink}
```

In `plugins/sdlc-knowledge-base/scripts/eval/runner.py`, in the dict returned by `_build_question_trace`, add the field (next to `"claims": claim_rows`):

```python
        "id_rewrites": out.get("_id_rewrites", []),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_eval_runner.py tests/test_kb_offline_query_pipeline.py tests/test_kb_offline_federation_graph.py -q`
Expected: all pass (carrier surfaced; graph still builds).
Then flake8: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/eval/runner.py tests/test_kb_offline_eval_runner.py` — no output.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/eval/runner.py tests/test_kb_offline_eval_runner.py
git commit -m "feat(kb-offline): carry synthesize id_rewrites to the eval trace (#211)"
```

---

## Task 4: Reproducible calibration `calibrate_id_normalize.py`

**Files:**
- Create: `research/kb-offline-eval/harness/calibrate_id_normalize.py`
- Test: `tests/test_kb_offline_calibrate_id_normalize.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_calibrate_id_normalize.py`:

```python
"""The id-normalize calibration must pass with exit 0 (frozen-helper reproducibility)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research" / "kb-offline-eval" / "harness" / "calibrate_id_normalize.py"


def _load():
    spec = importlib.util.spec_from_file_location("calibrate_id_normalize", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_calibration_passes():
    assert _load().main() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_calibrate_id_normalize.py -q`
Expected: FAIL — script file does not exist (`spec` is None / FileNotFoundError).

- [ ] **Step 3: Write the calibration script**

Create `research/kb-offline-eval/harness/calibrate_id_normalize.py`:

```python
#!/usr/bin/env python3
"""Reproducible calibration for the cited-page normalizer floor/margin (#211, Slice 2, spec §6).

Proves, using the FROZEN resolve_cited_page imported from the shipped module (so calibration
cannot drift from production):
  * the two real trace cases separate around the floor: q035 (0.821) recovers, q052 (0.588) drops;
  * the no-wrong-snap safety property holds against RUNTIME-SHAPED subsets (1-2 read pages):
    for every shelf id S and every typo-style perturbation P of S, the helper returns S or None
    against any subset containing S, and None against any subset NOT containing S -- NEVER a
    different id. Single-edit perturbations (the calibrated tier) additionally must recover.

Run:  .venv/bin/python research/kb-offline-eval/harness/calibrate_id_normalize.py
Exit 0 + "OK: id-normalize floor 0.75 / margin 0.10 valid" when all invariants hold.
"""
from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path

# Register the shipped scripts dir so the FROZEN resolver is imported (no reimplementation).
SCRIPTS = Path(__file__).resolve().parents[3] / "plugins" / "sdlc-knowledge-base" / "scripts"
_spec = importlib.util.spec_from_file_location(
    "cited_page_normalize", SCRIPTS / "cited_page_normalize.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
resolve_cited_page = _mod.resolve_cited_page

FLOOR, MARGIN = 0.75, 0.10

# The 16-page smoke/ratification shelf (the universe of distinct ids).
SHELF = [
    "ci-cd.md", "code-review.md", "deployment-strategies.md", "dora.md", "feature-flags.md",
    "incident-response.md", "observability.md", "pair-programming.md", "release-management.md",
    "sdlc-assured.md", "sdlc-programme.md", "sdlc-single-team.md", "sdlc-solo.md",
    "tech-debt.md", "testing.md", "trunk-based.md",
]


def _single_edit_typos(s: str) -> list[str]:
    """Deterministic single-edit perturbations: drop each char, double each char."""
    out = set()
    for i in range(len(s)):
        out.add(s[:i] + s[i + 1:])           # deletion
        out.add(s[:i] + s[i] + s[i:])        # duplication
    out.discard(s)
    return sorted(out)


def main() -> int:
    failures: list[str] = []

    # 1) Real trace cases through the frozen resolver.
    q035 = resolve_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"])
    if q035.page != "sdlc-single-team.md":
        failures.append(f"q035 should recover, got {q035}")
    q052 = resolve_cited_page("pair-summary.md", ["pair-programming.md"])
    if q052.page is not None or q052.score is None or not (0.55 <= q052.score <= 0.62):
        failures.append(f"q052 should drop with retained score ~0.588, got {q052}")

    # 2) Runtime-subset safety sweep. For each S and each single-edit perturbation P of S,
    #    test singletons {S}, {X}; pairs {S,X}, {X,Y}. Invariant: result in {S, None} when S
    #    present, None when S absent -- never a non-source id.
    n_recover = n_failclosed = 0
    for s in SHELF:
        others = [x for x in SHELF if x != s]
        for p in _single_edit_typos(s):
            subsets = [(s,)] + [(x,) for x in others]
            subsets += [(s, x) for x in others]
            subsets += list(itertools.combinations(others, 2))
            for sub in subsets:
                page = resolve_cited_page(p, list(sub), floor=FLOOR, margin=MARGIN).page
                contains_s = s in sub
                if contains_s:
                    if page not in (s, None):
                        failures.append(f"WRONG-SNAP {p!r} in {sub} -> {page!r} (expected {s} or None)")
                else:
                    if page is not None:
                        failures.append(f"WRONG-SNAP {p!r} in {sub} -> {page!r} (expected None)")
            # Liveness for the calibrated tier: single-edit P must recover on the singleton {S}.
            if resolve_cited_page(p, [s], floor=FLOOR, margin=MARGIN).page == s:
                n_recover += 1
            else:
                n_failclosed += 1

    if failures:
        for f in failures[:20]:
            print("FAIL:", f)
        print(f"... {len(failures)} total failures")
        return 1
    print(f"single-edit perturbations: recover={n_recover} fail-closed={n_failclosed} wrong=0")
    print("OK: id-normalize floor 0.75 / margin 0.10 valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the script + test to verify they pass**

Run: `.venv/bin/python research/kb-offline-eval/harness/calibrate_id_normalize.py`
Expected: prints the recover/fail-closed counts and `OK: id-normalize floor 0.75 / margin 0.10 valid`, exit 0.

If any `WRONG-SNAP` is printed, that is a genuine calibration finding — STOP and report it (do not loosen the test to make it pass). A wrong-snap means the floor/margin does not guarantee safety on this shelf and the design must be revisited. (Per §6, the expected result is zero wrong-snaps.)

Then: `.venv/bin/python -m pytest tests/test_kb_offline_calibrate_id_normalize.py -q`
Expected: pass.
Then flake8: `.venv/bin/python -m flake8 --max-line-length=127 research/kb-offline-eval/harness/calibrate_id_normalize.py tests/test_kb_offline_calibrate_id_normalize.py` — no output.

- [ ] **Step 5: Commit**

```bash
git add research/kb-offline-eval/harness/calibrate_id_normalize.py tests/test_kb_offline_calibrate_id_normalize.py
git commit -m "test(kb-offline): reproducible id-normalize calibration over runtime-subset sweep (#211)"
```

---

## Task 5: Whole-slice verification

**Files:** none (verification only)

- [ ] **Step 1: Full non-live suite + lint**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: all pass (Slice 1's 317 + the new Slice 2 tests; no regressions).

Run: `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/cited_page_normalize.py plugins/sdlc-knowledge-base/scripts/pipeline.py plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/eval/runner.py research/kb-offline-eval/harness/calibrate_id_normalize.py`
Expected: no output.

- [ ] **Step 2: Confirm select-side untouched (q034 regression intent)**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_pipeline.py -q -k select`
Expected: the existing select abstention/filter tests still pass — confirming no select-side fuzzy recovery was introduced (Slice 2 touches only `synthesize`). Note in the slice review that q034's select-side drop is structurally unaffected because no select code changed.

- [ ] **Step 3: Hand off for whole-slice review + live ratification**

Per spec Workflow: whole-slice review, then a live gemma4:12b traced ratification (`num_ctx=8192`) as pre-merge evidence, then `superpowers:finishing-a-development-branch` (KEEP the branch — the EPIC accumulates). Live ratification is run by the user/session, not inside subagent-driven task execution.

---

## Self-Review (completed by plan author)

- **Spec coverage:** §1 helper → Task 1; §3 hook (spans+citations, before back-fill, handle-bucketing, `model_copy`) → Task 2; §4 carrier (`rewrites_sink` → `_id_rewrites` → `id_rewrites`, 3-dp score, `reference_kind`/`reference_index`/`handle`) → Tasks 2+3; §5 metric guarantee (read-set-only, select untouched) → Task 2 tests + Task 5 Step 2; §6 test matrix → Tasks 1–4; calibration runtime-subset sweep → Task 4. All covered.
- **Placeholder scan:** no TBD/TODO; every code step shows complete code; the only conditional ("adjust fixture strings" in Task 1 Step 4, "match existing `load_questions` call form" in Task 3 Step 1) are explicit instructions to match observed reality, not deferrals.
- **Type consistency:** `Resolution(page, score, runner_up)`, `resolve_cited_page`/`normalize_cited_page` signatures, `rewrites_sink` param, and the rewrite-record keys (`from/to/score/handle/candidates/stage/claim_index/reference_kind/reference_index`) are identical across Tasks 1–4 and the spec.

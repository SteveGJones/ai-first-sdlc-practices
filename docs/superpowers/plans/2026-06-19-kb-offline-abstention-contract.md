# kb-offline Slice 1 — abstention contract + verifier hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make "the KB has nothing relevant" a first-class structural outcome (select can abstain, the graph/federation short-circuit, synthesize never emits absence-claims) and harden the verifier so a claim is supported only by a span that is both present *and* relevant.

**Architecture:** Additive contract fields (`SelectResult`/`Answer`) + a deterministic claim↔span relevance floor in `ground_claim` (before the verbatim early-return) + a shared renderer-agnostic `finalize_answer` used by the graph and both federation paths. Pure units (tokenizer/floor, guard, finalizer, shelf reducer, reason normalizer) are front-loaded for isolated TDD; the graph/federation wiring follows.

**Tech Stack:** Python 3.9+, `.venv`, pytest, pydantic v2, LangGraph. No new deps. `flake8 --max-line-length=127`. Spec: `docs/superpowers/specs/2026-06-19-kb-offline-abstention-contract-design.md` (rev 5). Commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## Environment & conventions
- `.venv` for everything; pytest from repo root. Package imported as `sdlc_knowledge_base_scripts` (registered by `tests/conftest.py`). Branch `feature/211-kb-offline-langgraph` (one accumulating EPIC branch; no PR). TDD throughout.

## File structure

| File | Change | Responsibility |
|---|---|---|
| `plugins/sdlc-knowledge-base/scripts/contracts.py` | modify | `SelectResult`/`Answer` abstention fields |
| `plugins/sdlc-knowledge-base/scripts/pipeline.py` | modify | `_normalize_reason`; `select` abstain branches; `synthesize` abstain enforce |
| `plugins/sdlc-knowledge-base/scripts/retrieval.py` | modify | generalize `_reduce_shelf` → `reduce_shelf` (path|text, ordered ids) |
| `plugins/sdlc-knowledge-base/scripts/entailment.py` | modify | frozen tokenizer + claim↔span relevance floor; epistemic-absence guard; judge gets spans |
| `plugins/sdlc-knowledge-base/scripts/publication.py` | modify | shared `finalize_answer` |
| `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py` | modify | QueryState keys, n_select returns + eligible shelf, conditional edge, `n_abstain`, finalize in n_verify_publish |
| `plugins/sdlc-knowledge-base/scripts/federation.py` | modify | eligible shelf, per-library short-circuit, canonicalize_attribution preserve, merged finalize |
| `plugins/sdlc-knowledge-base/scripts/federation_accel.py` | modify | eligible cross-lib shelf, fused-select short-circuit, finalize |
| `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py` | modify | print `[abstained: <reason>]` to stderr |
| `plugins/sdlc-knowledge-base/scripts/prompts.py` | modify | SELECT/SYNTHESIZE abstain instructions |
| `research/kb-offline-eval/harness/calibrate_relevance_floor.py` | create | reproducible floor calibration |
| `tests/test_kb_offline_abstention.py` | create | most new unit tests |
| `tests/test_kb_offline_pipeline.py`, `tests/test_kb_offline_query_pipeline.py`, `tests/test_kb_offline_federation*.py`, `tests/test_kb_offline_cli.py` | modify | path-specific tests |

---

## Task 1: Contract fields

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/contracts.py`; Test `tests/test_kb_offline_abstention.py` (new).

- [ ] **Step 1: failing test** — create `tests/test_kb_offline_abstention.py`:
```python
"""Slice 1 abstention contract + verifier hardening (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.contracts import Answer, SelectResult


def test_select_result_abstention_fields_default():
    s = SelectResult(page_ids=["a.md"])
    assert s.no_relevant_page is False and s.abstention_reason is None
    s2 = SelectResult(page_ids=[], no_relevant_page=True, abstention_reason="nope")
    assert s2.no_relevant_page is True and s2.abstention_reason == "nope"


def test_answer_abstention_fields_default():
    a = Answer(claims=[], rendered_text="x")
    assert a.abstained is False and a.abstention_reason is None
    a2 = Answer(abstained=True, abstention_reason="no supported claims")
    assert a2.abstained is True and a2.rendered_text == "" and a2.abstention_reason == "no supported claims"
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -v` → FAIL (unexpected kwargs).

- [ ] **Step 3: implement** — in `contracts.py`, add fields:
```python
class SelectResult(BaseModel):
    page_ids: list[str] = Field(default_factory=list)
    no_relevant_page: bool = False
    abstention_reason: str | None = None
```
```python
class Answer(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    rendered_text: str = ""
    abstained: bool = False
    abstention_reason: str | None = None
```

- [ ] **Step 4: run, expect PASS** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -v` → PASS (2). Full non-live: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass (additive defaults). flake8 the two files → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/contracts.py tests/test_kb_offline_abstention.py
git commit -m "feat(kb-offline): SelectResult/Answer abstention fields (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `_normalize_reason` helper

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/pipeline.py`; Test `tests/test_kb_offline_abstention.py`.

- [ ] **Step 1: failing test** — append:
```python
from sdlc_knowledge_base_scripts.pipeline import _normalize_reason


def test_normalize_reason():
    assert _normalize_reason("  a\n  b  ", "fb") == "a b"
    assert _normalize_reason(None, "fb") == "fb"
    assert _normalize_reason("", "fb") == "fb"
    assert _normalize_reason("   ", "fb") == "fb"
    assert len(_normalize_reason("x" * 500, "fb")) <= 200
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k normalize_reason -v` → FAIL (ImportError).

- [ ] **Step 3: implement** — in `pipeline.py` (module level):
```python
def _normalize_reason(text, fallback: str) -> str:
    """Collapse whitespace/newlines, strip, cap at 200 chars; fallback for None/blank."""
    s = " ".join(text.split()) if isinstance(text, str) else ""
    return (s[:200] if s else fallback)
```

- [ ] **Step 4: run + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k normalize_reason -v` → PASS. flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_abstention.py
git commit -m "feat(kb-offline): _normalize_reason for abstention reasons (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Generalize `reduce_shelf` (path|text, ordered ids)

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/retrieval.py`; Test `tests/test_kb_offline_abstention.py`.

**Context:** `retrieval._reduce_shelf(shelf_path: Path, page_ids: list)` reads the shelf file and returns the header + `extract_entry_block` for each id in order. Generalize to accept a path OR shelf text, keeping the entry-block behaviour. READ `retrieval.py:20-45` first.

- [ ] **Step 1: failing test** — append (uses a tiny real shelf):
```python
from sdlc_knowledge_base_scripts.retrieval import reduce_shelf

_SHELF = ("<!-- format_version: 1 -->\n# Shelf Index\n\n"
          "## 1. a.md\nHash: x\nLayer: evidence\nTerms: alpha\n\n"
          "## 2. b.md\nHash: y\nLayer: domain\nTerms: beta\n\n"
          "## 3. c.md\nHash: z\nLayer: domain\nTerms: gamma\n")


def test_reduce_shelf_keeps_full_blocks_in_order_from_text():
    out = reduce_shelf(_SHELF, ["c.md", "a.md"])     # ordered, full blocks
    assert out.index("c.md") < out.index("a.md")     # order preserved
    assert "Terms: gamma" in out and "Terms: alpha" in out  # full entry blocks, not just headers
    assert "b.md" not in out                          # excluded
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k reduce_shelf -v` → FAIL (ImportError / signature).

- [ ] **Step 3: implement** — in `retrieval.py`, refactor `_reduce_shelf` into a text-or-path `reduce_shelf` and keep `_reduce_shelf` as a thin wrapper for existing callers:
```python
def reduce_shelf(shelf, ordered_ids: list[str]) -> str:
    """Reduced shelf-index = original header + the complete entry block for each id in
    `ordered_ids` (order preserved), via extract_entry_block. `shelf` is a Path/str path
    or the shelf text itself."""
    text = shelf if (isinstance(shelf, str) and "\n" in shelf) else Path(shelf).read_text(encoding="utf-8")
    # header = everything before the first '## ' entry
    head = text.split("\n## ", 1)[0]
    blocks = []
    for pid in ordered_ids:
        block = extract_entry_block(text, pid)
        if block:
            blocks.append(block)
    return head + ("\n\n" + "\n\n".join(blocks) if blocks else "")


def _reduce_shelf(shelf_path, page_ids: list[str]) -> str:   # back-compat wrapper
    return reduce_shelf(shelf_path, page_ids)
```
(Confirm `extract_entry_block(shelf_text, page_id)` and the header split match the real file format; adapt the `head`/join to reproduce the existing `_reduce_shelf` output byte-for-byte for the accelerated path. If the existing `_reduce_shelf` already builds head+blocks, simply widen its first param to accept text and rename — keep output identical.)

- [ ] **Step 4: run + regression + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k reduce_shelf -v` → PASS. Full non-live (accel path still works): `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass. flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/retrieval.py tests/test_kb_offline_abstention.py
git commit -m "refactor(kb-offline): generalize reduce_shelf (path|text, ordered ids) (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `ground_claim` claim↔span relevance floor + frozen tokenizer

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/entailment.py`; Test `tests/test_kb_offline_abstention.py`.

**Context (spec §6a):** a span grants support only if it is on a cited page AND shares meaningful tokens with the CLAIM (coverage ≥ 0.20). The coverage check runs INSIDE the span loop **before** the verbatim early-return (entailment.py:51). READ `ground_claim` first.

- [ ] **Step 1: failing test** — append:
```python
from sdlc_knowledge_base_scripts.contracts import Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.entailment import RELEVANCE_FLOOR, ground_claim


def _claim(text, page, span):
    return Claim(text=text, cited_pages=[PageRef(library="local", page=page)],
                 evidence_spans=[Span(page=page, text=span)])


def test_ground_claim_rejects_verbatim_but_irrelevant_span():
    # the §6.2 bug: span present on page, irrelevant to the claim -> unsupported
    pages = {"dora.md": "DORA Metrics. Elite teams deploy multiple times per day."}
    c = _claim("The company payroll schedule is not mentioned.", "dora.md", "DORA Metrics")
    assert ground_claim(c, pages) == EntailmentStatus.unsupported


def test_ground_claim_supports_relevant_verbatim_span():
    pages = {"dora.md": "Elite teams deploy multiple times per day."}
    c = _claim("Elite teams deploy multiple times per day.", "dora.md",
               "deploy multiple times per day")
    assert ground_claim(c, pages) == EntailmentStatus.supported


def test_ground_claim_supports_legitimate_negative():
    pages = {"sdlc-solo.md": "The solo method uses feature branches and requires no formal sign-off."}
    c = _claim("The solo method does not require formal sign-off.", "sdlc-solo.md",
               "requires no formal sign-off")
    assert ground_claim(c, pages) == EntailmentStatus.supported


def test_relevance_floor_value():
    assert RELEVANCE_FLOOR == 0.20
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k ground_claim -v` → FAIL (no RELEVANCE_FLOOR / irrelevant span still supported).

- [ ] **Step 3: implement** — in `entailment.py`, add the frozen tokenizer + floor, and gate each span on coverage **before** the verbatim return:
```python
RELEVANCE_FLOOR = 0.20
_RELEVANCE_STOPWORDS = frozenset(
    "a an the of to in on for and or is are was were be been being as that this these those it its "
    "with by from at into not no does do did has have had will would can could should may might".split())
_RELEVANCE_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _content_tokens(text: str) -> list[str]:
    return [t for t in _RELEVANCE_TOKEN_RE.findall(text.lower())
            if t not in _RELEVANCE_STOPWORDS and len(t) > 2]


def _claim_span_coverage(claim_text: str, span_text: str) -> float:
    c = _content_tokens(claim_text); s = set(_content_tokens(span_text))
    return (sum(1 for t in c if t in s) / len(c)) if c else 0.0
```
In `ground_claim`'s span loop, gate on coverage first (irrelevant spans can ground nothing):
```python
    for span in claim.evidence_spans:
        if span.page not in cited:
            continue
        page_text = pages.get(span.page)
        if page_text is None:
            continue
        if _claim_span_coverage(claim.text, span.text) < RELEVANCE_FLOOR:
            continue                                   # irrelevant span -> cannot ground
        if _norm(span.text) in _norm(page_text):
            return EntailmentStatus.supported
        page_tokens = set(_tokens(page_text))
        span_tokens = _tokens(span.text)
        if span_tokens:
            overlap = sum(1 for t in span_tokens if t in page_tokens) / len(span_tokens)
            if overlap >= fuzzy_threshold:
                best = EntailmentStatus.partial
    return best
```
(Add `import re` if not present — it is. Keep the cited-page hard-reject loop above unchanged.)

- [ ] **Step 4: run + regression + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k "ground_claim or relevance_floor" -v` → PASS. Full non-live (no fact_recall-class regression in existing verifier tests): `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass. flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/entailment.py tests/test_kb_offline_abstention.py
git commit -m "feat(kb-offline): claim<->span relevance floor in ground_claim (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Epistemic-absence guard

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/entailment.py`; Test `tests/test_kb_offline_abstention.py`.

**Context (spec §6c):** mark (don't remove) absence-shaped claims `unsupported`. Patterns must cover all trace forms; must NOT catch legit negatives.

- [ ] **Step 1: failing test** — append:
```python
from sdlc_knowledge_base_scripts.entailment import is_epistemic_absence


def test_epistemic_absence_matches_all_trace_forms():
    yes = ["The payroll schedule is not mentioned in the provided documents.",
           "The provided documents do not contain information regarding a CEO.",
           "I cannot find any information regarding dental insurance in the provided documents.",
           "The location of the London office is not provided in the source text.",
           "No information regarding the gym opening time."]
    for t in yes:
        assert is_epistemic_absence(t) is True, t


def test_epistemic_absence_ignores_legitimate_negatives():
    no = ["The solo method does not require formal sign-off.",
          "Feature flags should be removed when stale.",
          "Trunk-based development avoids long-lived branches."]
    for t in no:
        assert is_epistemic_absence(t) is False, t
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k epistemic -v` → FAIL (ImportError).

- [ ] **Step 3: implement** — in `entailment.py`:
```python
_ABSENCE_RE = re.compile(
    r"not mentioned|no information|do(es)? not contain|documents contain no|"
    r"not found in the (provided )?documents|cannot find any information|"
    r"not provided in the source|not provided in the (provided )?document",
    re.IGNORECASE)


def is_epistemic_absence(claim_text: str) -> bool:
    """True for corpus-relative epistemic-absence phrasing (NOT generic negation)."""
    return bool(_ABSENCE_RE.search(claim_text))
```
Wire into `verify_entailment`: after computing each claim's status, if `is_epistemic_absence(claim.text)` force `claim.entailment_status = EntailmentStatus.unsupported` (keep the claim in the list):
```python
        if is_epistemic_absence(claim.text):
            claim.entailment_status = EntailmentStatus.unsupported
```

- [ ] **Step 4: run + regression + lint** — guard tests PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/entailment.py tests/test_kb_offline_abstention.py
git commit -m "feat(kb-offline): epistemic-absence guard marks absence-claims unsupported (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: `judge_claim` receives declared spans

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/entailment.py`; Test `tests/test_kb_offline_abstention.py`.

**Context (spec §6b):** the judge prompt should include the claim's declared evidence spans + ask for relevance. READ `judge_claim` first.

- [ ] **Step 1: failing test** — append (assert the prompt the backend receives contains the span text):
```python
from sdlc_knowledge_base_scripts.entailment import judge_claim


def test_judge_claim_prompt_includes_declared_spans():
    seen = {}
    class B:
        def generate(self, prompt, schema=None):
            seen["p"] = prompt
            return '{"status": "supported"}'
    c = _claim("Elite teams deploy daily.", "dora.md", "deploy multiple times per day")
    judge_claim(c, {"dora.md": "Elite teams deploy multiple times per day."}, backend=B())
    assert "deploy multiple times per day" in seen["p"]      # declared span surfaced
    assert "relevan" in seen["p"].lower()                    # asks about relevance
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k judge_claim_prompt -v` → FAIL (span not in prompt).

- [ ] **Step 3: implement** — extend `judge_claim`'s prompt to add the declared spans + a relevance instruction:
```python
    spans = "; ".join(s.text for s in claim.evidence_spans) or "(none)"
    prompt = (
        "Judge whether the cited page text SUPPORTS the claim AND the declared spans are "
        "RELEVANT to the claim. Reply ONLY a JSON object "
        '{"status": "supported"|"partial"|"unsupported"}.\n\n'
        f"Claim: {claim.text}\n\nDeclared spans: {spans}\n\nCited pages:\n{cited}"
    )
```
(Keep the rest of `judge_claim` — schema, parse, conservative default — unchanged.)

- [ ] **Step 4: run + regression + lint** — PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/entailment.py tests/test_kb_offline_abstention.py
git commit -m "feat(kb-offline): judge_claim assesses span relevance with declared spans (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Shared `finalize_answer`

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/publication.py`; Test `tests/test_kb_offline_abstention.py`.

**Context (spec §6d):** renderer-agnostic finalizer; reconciles BOTH outcomes.

- [ ] **Step 1: failing test** — append:
```python
from sdlc_knowledge_base_scripts.publication import finalize_answer


def test_finalize_answer_empty_render_abstains():
    a = Answer(claims=[])
    finalize_answer(a, "", abstain_reason="no supported claims")
    assert a.abstained is True and a.rendered_text == "" and a.abstention_reason == "no supported claims"


def test_finalize_answer_nonempty_render_clears_stale_flag():
    a = Answer(claims=[], abstained=True, abstention_reason="stale")   # stale synth flag
    finalize_answer(a, "Some answer text.", abstain_reason="x")
    assert a.abstained is False and a.rendered_text == "Some answer text." and a.abstention_reason is None
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_abstention.py -k finalize_answer -v` → FAIL (ImportError).

- [ ] **Step 3: implement** — in `publication.py`:
```python
def finalize_answer(answer, rendered: str, *, abstain_reason: str) -> None:
    """Set rendered_text and reconcile abstention BOTH ways. Renderer-agnostic: the caller
    renders (publish OR render_federated) and passes the body."""
    answer.rendered_text = rendered
    if not rendered.strip():
        answer.abstained = True
        answer.abstention_reason = abstain_reason
    else:
        answer.abstained = False
        answer.abstention_reason = None
```

- [ ] **Step 4: run + lint** — PASS (both outcomes); flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/publication.py tests/test_kb_offline_abstention.py
git commit -m "feat(kb-offline): shared finalize_answer (renderer-agnostic, both outcomes) (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: `select` abstains (prompt + branches)

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/prompts.py`, `plugins/sdlc-knowledge-base/scripts/pipeline.py`; Test `tests/test_kb_offline_pipeline.py`.

**Context (spec §3):** distinguish three abstention causes; clear reason on success; normalize the model reason. READ `pipeline.select`'s return (line ~119) + `_select_schema` (so `no_relevant_page`/`abstention_reason` are in the schema).

- [ ] **Step 1: failing tests** — append to `tests/test_kb_offline_pipeline.py`:
```python
def test_select_explicit_abstention(tmp_path):
    from sdlc_knowledge_base_scripts.pipeline import select
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps(
        {"page_ids": [], "no_relevant_page": True, "abstention_reason": "  nothing\n fits "})
    r = select("q", _shelf(tmp_path), backend=be, known_pages={"topic.md"})
    assert r.no_relevant_page is True and r.page_ids == [] and r.abstention_reason == "nothing fits"


def test_select_all_filtered_abstains(tmp_path):
    from sdlc_knowledge_base_scripts.pipeline import select
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["ghost.md"]})  # not known
    r = select("q", _shelf(tmp_path), backend=be, known_pages={"topic.md"})
    assert r.no_relevant_page is True and r.page_ids == [] and "id/layer" in r.abstention_reason


def test_select_success_clears_reason(tmp_path):
    from sdlc_knowledge_base_scripts.pipeline import select
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["topic.md"]})
    r = select("q", _shelf(tmp_path), backend=be, known_pages={"topic.md"})
    assert r.no_relevant_page is False and r.page_ids == ["topic.md"] and r.abstention_reason is None
```
(`_shelf`, `FakeBackend`, `json` already in that test file.)

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_pipeline.py -k "select_explicit or select_all_filtered or select_success" -v` → FAIL.

- [ ] **Step 3: implement** — `prompts.SELECT_FRAGMENT` append: `" Return the fewest page ids that are actually relevant. If no page is relevant, set no_relevant_page true with a one-line reason; do not pad the list."` Replace `pipeline.select`'s return (line ~119) with the three-branch logic from spec §3 (uses `_normalize_reason`). Ensure `_select_schema` exposes `no_relevant_page`+`abstention_reason` (it's `SelectResult.model_json_schema()`, so Task 1 already added them).

- [ ] **Step 4: run + regression + lint** — the 3 new tests PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/prompts.py plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_pipeline.py
git commit -m "feat(kb-offline): select may abstain (no_relevant_page + reasons) (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: `synthesize` abstains, never absence-claims

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/prompts.py`, `plugins/sdlc-knowledge-base/scripts/pipeline.py`; Test `tests/test_kb_offline_pipeline.py`.

**Context (spec §5):** parse `abstained`; enforce invariant (abstained ⇒ claims=[], rendered_text=""). Keep the cited_pages back-fill.

- [ ] **Step 1: failing test** — append:
```python
def test_synthesize_abstains_zero_claims():
    from sdlc_knowledge_base_scripts.pipeline import synthesize
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps(
        {"claims": [], "rendered_text": "", "abstained": True, "abstention_reason": "pages don't answer"})
    ans = synthesize("q", [{"page": "a.md", "content": "x"}], backend=be)
    assert ans.abstained is True and ans.claims == [] and ans.rendered_text == "" and ans.abstention_reason == "pages don't answer"
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_pipeline.py -k synthesize_abstains -v` → FAIL.

- [ ] **Step 3: implement** — `prompts.SYNTHESIZE_FRAGMENT` append: `" If the supplied pages do not answer the question, return zero claims and set abstained true with a one-line reason. Never write a claim that merely states the answer is absent."` In `synthesize`, after validate + back-fill, enforce:
```python
        if ans.abstained:
            ans.claims = []
            ans.rendered_text = ""
            ans.abstention_reason = _normalize_reason(ans.abstention_reason, "pages do not answer the question")
```

- [ ] **Step 4: run + regression + lint** — PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/prompts.py plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_pipeline.py
git commit -m "feat(kb-offline): synthesize abstains instead of emitting absence-claims (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Query graph — state, eligible shelf, short-circuit, finalize

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py`; Test `tests/test_kb_offline_query_pipeline.py`.

**Context (spec §2/§4/§6d):** READ `query_graph.py` fully. Add QueryState keys; `n_select` returns them + builds the eligible reduced shelf (both branches); a conditional edge to `n_abstain`; `n_verify_publish` calls `finalize_answer`.

- [ ] **Step 1: failing tests** — append to `tests/test_kb_offline_query_pipeline.py` (FakeBackend through the real graph):
```python
def test_graph_abstains_on_no_relevant_page(tmp_path):
    # build a tiny library + shelf
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph
    lib = tmp_path / "library"; lib.mkdir()
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# a\nElite teams deploy daily.\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n\n## 1. a.md\nLayer: evidence\nTerms: deploy\n")
    calls = {"n": 0}
    def gen(prompt, schema=None):
        calls["n"] += 1
        if "Shelf" in prompt or "shelf" in prompt:        # select
            return json.dumps({"page_ids": [], "no_relevant_page": True, "abstention_reason": "nope"})
        raise AssertionError("synthesize must NOT be called after abstain")
    be = FakeBackend(); be.generate = gen
    out = build_query_graph(be).invoke(
        {"library_path": str(lib), "question": "unrelated?", "layer": None, "min_confidence": None},
        config={"configurable": {"thread_id": "t"}})
    assert out["abstained"] is True and out["rendered_text"] == "" and out["pages"] == []
    assert out["abstention_reason"] == "nope"
```

- [ ] **Step 2: run, expect FAIL** — `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -k graph_abstains -v` → FAIL.

- [ ] **Step 3: implement** — in `query_graph.py`:
  - add `no_relevant_page: bool`, `abstained: bool`, `abstention_reason: Optional[str]` to `QueryState`;
  - `n_select`: after computing `candidates` (both non-accel and accel branches), build the eligible reduced shelf via `reduce_shelf` (non-accel: `reduce_shelf(shelf, sorted(candidates))`; accel: `reduce_shelf(<lib shelf>, [c for c in cand_ids if c in candidates])`), pass as `shelf_text`; return `{"page_ids": res.page_ids, "no_relevant_page": res.no_relevant_page, "abstention_reason": res.abstention_reason}`;
  - add `n_abstain` (spec §4) and a conditional edge `select → (n_abstain if no_relevant_page or not page_ids else read)`;
  - `n_verify_publish`: call `finalize_answer(verified, rendered, abstain_reason=(ans.abstention_reason if ans.abstained else "no supported claims"))` and return `abstained`/`abstention_reason` too.

- [ ] **Step 4: run + regression + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -v` → PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py tests/test_kb_offline_query_pipeline.py
git commit -m "feat(kb-offline): query graph abstention short-circuit + eligible shelf + finalize (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Normal federation — eligible shelf, short-circuit, finalize

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/federation.py`; Test `tests/test_kb_offline_federation*.py` (use the existing federation test file; READ it for fixtures).

**Context (spec §2/§6d/§7):** `query_one_library` uses `reduce_shelf(shelf, sorted(candidates))`, short-circuits an abstaining/empty select (no `synthesize`), and `finalize_answer` per library; `canonicalize_attribution` must preserve `abstained`/`abstention_reason`; the merged answer is finalized after `render_federated`.

- [ ] **Step 1: failing test** — add a test asserting: (a) a library whose select abstains returns an abstained Answer without synthesize; (b) one library abstains + another publishes → merged not abstained; (c) all abstain → merged abstained with `"no library produced a supported answer"`. (Model the fixtures on the existing federation test; use FakeBackend per library.)

- [ ] **Step 2: run, expect FAIL.**

- [ ] **Step 3: implement** — in `federation.py`:
  - `query_one_library`: `candidates = filter_pages(...)`; `sel = select(question, shelf, known_pages=set(candidates), priming=priming, shelf_text=reduce_shelf(shelf, sorted(candidates)))`; if `sel.no_relevant_page or not sel.page_ids`: return `(Answer(abstained=True, abstention_reason=sel.abstention_reason), [])` WITHOUT synthesize; else proceed, then `finalize_answer(verified, *publish(verified)[:1], abstain_reason="no supported claims")` — i.e. render with publish per library and finalize.
  - `canonicalize_attribution`: preserve `abstained`/`abstention_reason` on the rebuilt Answer.
  - the federated driver (where `merge_answers` + `render_federated` are called): after `rendered, rejected = render_federated(merged, handle_sets)`, `finalize_answer(merged, rendered, abstain_reason="no library produced a supported answer")`.

- [ ] **Step 4: run + regression + lint** — PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/federation.py tests/test_kb_offline_federation*.py
git commit -m "feat(kb-offline): federation eligible shelf + per-library abstain + merged finalize (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Accelerated federation — eligible cross-lib shelf, short-circuit, finalize

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/federation_accel.py`; Test the federation-accel test file (READ it).

**Context (spec §2/§6d/§7):** keep `_cross_library_shelf` over the **fused eligible qualified ids** (best-first); if the fused select abstains/empty → return an abstained merged Answer before synthesize; after `canonicalize_attribution` (now metadata-preserving) + `render_federated`, `finalize_answer(canonical, rendered, abstain_reason="no library produced a supported answer")`.

- [ ] **Step 1: failing test** — assert: fused-select abstain → abstained merged Answer, no synthesize; a published cross-library answer → not abstained, and the canonical Answer retains no stale abstain flag.

- [ ] **Step 2: run, expect FAIL.**

- [ ] **Step 3: implement** — in `federation_accel.py`: feed `_cross_library_shelf` the fused **eligible** qualified ids; short-circuit the fused select; after `canonical = canonicalize_attribution(verified)` and `rendered, rejected = render_federated(canonical, handle_sets)`, call `finalize_answer(canonical, rendered, abstain_reason="no library produced a supported answer")` and return the canonical.

- [ ] **Step 4: run + regression + lint** — PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/federation_accel.py tests/test_kb_offline_federation*.py
git commit -m "feat(kb-offline): accel-federation eligible shelf + fused abstain + finalize (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: CLI surfaces abstention

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`; Test `tests/test_kb_offline_cli.py`.

- [ ] **Step 1: failing test** — append: a `query` whose backend abstains prints `[abstained: <reason>]` to stderr and exits 0 (use `backend_override` + capsys).

- [ ] **Step 2: run, expect FAIL.**

- [ ] **Step 3: implement** — in `_query_single` and `_emit_federation_result`, after printing `rendered_text`, if `out.get("abstained")`: `print(f"[abstained: {out.get('abstention_reason')}]", file=sys.stderr)`.

- [ ] **Step 4: run + regression + lint** — PASS; full non-live → all pass; flake8 → clean.

- [ ] **Step 5: commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "feat(kb-offline): CLI surfaces [abstained: reason] (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Calibration script (reproducible floor)

**Files:** Create `research/kb-offline-eval/harness/calibrate_relevance_floor.py`.

- [ ] **Step 1:** write a script that loads the committed trace + the legit-negative/short-claim/synthetic-irrelevant-span fixtures, computes `_claim_span_coverage` (importing the FROZEN tokenizer from `entailment`) over absence vs legit-supported claims, prints the distribution (absence max, legit min/median) and asserts `RELEVANCE_FLOOR` sits strictly between them. (Mirror the analysis already run: absence ≤ 0.0 < 0.20 < 0.286 ≤ legit.)

- [ ] **Step 2: run** — `.venv/bin/python research/kb-offline-eval/harness/calibrate_relevance_floor.py` → prints the separation and `OK: floor 0.20 valid`.

- [ ] **Step 3: lint + commit**
```bash
git add research/kb-offline-eval/harness/calibrate_relevance_floor.py
git commit -m "test(kb-offline): reproducible relevance-floor calibration script (#211)" -m "" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 15: Fresh traced release ratification (pre-merge, live)

**Files:** none (verification).

- [ ] **Step 1:** with Ollama free, run `PYTHONUNBUFFERED=1 .venv/bin/kb-offline eval release --stamp $(date -u +%Y%m%dT%H%M%SZ) --runs 1 --report-dir research/kb-offline-eval` (trace on by default).
- [ ] **Step 2:** confirm the gate metrics move as intended — `abstention_precision`/`abstention_recall` up, `fact_recall` NOT regressed vs 0.787, `routing_precision` movement; inspect the new trace's `dropped`/abstained rows. Commit the new report + trace as evidence. (Calibration data cannot prove this — only a fresh run can; spec §8.)

---

## Final verification (after all tasks)
- [ ] Full non-live suite: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass.
- [ ] Lint the whole changed surface (all modified scripts + new tests) with `flake8 --max-line-length=127` → clean.
- [ ] Whole-slice review, then `superpowers:finishing-a-development-branch` (keep branch — EPIC accumulates).

---

## Self-review notes
**Spec coverage:** §1 contracts → T1; reason normalization → T2/T8/T9; §2 eligible shelf (4 paths) → T3 (helper) + T10 (graph ×2) + T11 (normal fed) + T12 (accel fed); §3 select abstain → T8; §4 graph short-circuit/state/n_abstain → T10; §5 synthesize abstain → T9; §6a relevance floor + frozen tokenizer → T4; §6b judge spans → T6; §6c epistemic guard → T5; §6d finalize + reject-all + ownership → T7 (helper) + T10/T11/T12 (wiring) + canonicalize preserve → T11/T12; §7 federation merge → T11/T12; surfacing → T13; §8 calibration script + fresh ratification → T14/T15; §9 tests distributed across tasks.

**Placeholder scan:** T11/T12 Step 1 describe the assertions rather than paste full fixtures because the federation test fixtures must be read from the existing federation test files (their backend/priming setup is non-trivial and file-specific) — the implementer READs those files first; this is a deliberate "match existing fixtures" instruction, not an unspecified test. Every code step elsewhere is complete.

**Type/name consistency:** `_normalize_reason(text, fallback)`, `reduce_shelf(shelf, ordered_ids)`, `RELEVANCE_FLOOR`/`_claim_span_coverage`/`_content_tokens`, `is_epistemic_absence(text)`, `finalize_answer(answer, rendered, *, abstain_reason)`, `SelectResult.no_relevant_page/abstention_reason`, `Answer.abstained/abstention_reason` — used identically across tasks. Federated abstain reason string `"no library produced a supported answer"` consistent in T11/T12.

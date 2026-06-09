# kb-offline M1c-1 — query path (select / synthesize / entailment verifier) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer a question from the local library with claim-level, grounding-verified citations — `select → read → synthesize → verify_entailment → publish` — through a read-only LangGraph `query_graph` and a `kb-offline query` CLI command.

**Architecture:** New pipeline ops `select`/`synthesize`; a focused `entailment.py` (deterministic grounding cap + per-claim LLM-judge, `final = min(cap, judge)`; verifier-assigned `high_impact`); a `publication.py` (supported→publish / partial→caveat / unsupported→reject); a `provenance.py` (layer + min-confidence page filter). The query path is **read-only** — no lock/fencing/journal/mutation — so `query_graph` is a simple linear read graph. Reuses M0 contracts (Answer/Claim/Span/EntailmentStatus) and the backend seam.

**Tech Stack:** Python 3.9+, Pydantic v2, langgraph 1.2.4, ollama, the project `.venv`, pytest. Specs: `docs/superpowers/specs/2026-06-07-kb-offline-M1-design-addendum.md` (decisions 6–9, 16) + parent design.

---

## Environment & scope

- **`.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. flake8(no E702/E402)+black(127).
- **M1c-1 only.** OUT of scope: the eval gate / frozen fixture / threshold ratification / Ollama-default decision (M1c-2); federation fan-out across libraries (later); embeddings (M3). Single-library query only.
- Reuse: `contracts` (Answer, Claim, Span, PageRef, EntailmentStatus), `backends`, `prompts` (SELECT_FRAGMENT, SYNTHESIZE_FRAGMENT), the `os.environ.setdefault("LANGSMITH_TRACING"/"LANGCHAIN_TRACING_V2","false")` offline guard pattern (graph modules).
- **Query is read-only**: no LibraryLock, no commit_mutation, no journal, no run-mutation lifecycle.

## File structure (M1c-1)

| File | Responsibility |
|---|---|
| `scripts/contracts.py` (modify) | add `SelectResult(page_ids: list[str])` |
| `scripts/provenance.py` (new) | `page_frontmatter(...)`, `filter_pages(library, page_names, *, layer, min_confidence)` |
| `scripts/entailment.py` (new) | `ground_claim`, `classify_high_impact`, `judge_claim`, `verify_entailment` |
| `scripts/publication.py` (new) | `publish(answer) -> (rendered_text, rejected_claims)` |
| `scripts/pipeline.py` (modify) | add `select(...)` + `synthesize(...)` ops |
| `scripts/graphs/query_graph.py` (new) | read-only `build_query_graph` (select→read→synthesize→verify→publish) |
| `scripts/kb_offline_cli.py` (modify) | add `query "<q>" [--layer] [--min-confidence] [--backend]` |
| Tests | `tests/test_kb_offline_entailment.py`, `test_kb_offline_provenance.py`, `test_kb_offline_query_pipeline.py`, `test_kb_offline_query_graph.py`, `test_kb_offline_cli.py` (append), `test_kb_offline_ollama_smoke.py` (append) |

Severity ordering used throughout: `unsupported(0) < partial(1) < supported(2)`; "min cap/judge" = the lower-rank status.

---

## Task 1: `SelectResult` contract + `select` pipeline op

**Files:** Modify `scripts/contracts.py`, `scripts/pipeline.py`; Test `tests/test_kb_offline_query_pipeline.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kb_offline_query_pipeline.py`:

```python
"""Tests for kb-offline query pipeline ops (select/synthesize)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.pipeline import select


def _shelf(tmp_path):
    s = tmp_path / "_shelf-index.md"
    s.write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n- b.md\n")
    return s


def test_select_returns_known_page_ids(tmp_path):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["a.md", "b.md"]})
    res = select("q", _shelf(tmp_path), backend=be, known_pages={"a.md", "b.md"})
    assert res.page_ids == ["a.md", "b.md"]


def test_select_drops_unknown_page_ids(tmp_path):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["a.md", "ghost.md"]})
    res = select("q", _shelf(tmp_path), backend=be, known_pages={"a.md", "b.md"})
    assert res.page_ids == ["a.md"]   # ghost.md dropped (not a known page)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -k select -v`
Expected: FAIL (ImportError: SelectResult / select).

- [ ] **Step 3: Add `SelectResult` to contracts.py + `select` to pipeline.py**

In `scripts/contracts.py`, after `Answer`:
```python
class SelectResult(BaseModel):
    page_ids: list[str] = Field(default_factory=list)
```

In `scripts/pipeline.py`, add (alongside `extract`/`reduce_to_proposal`):
```python
from .contracts import Answer, SelectResult  # extend the existing contracts import


def _select_schema() -> dict:
    return SelectResult.model_json_schema()


def select(question, shelf_index_path, *, backend, known_pages, max_repairs: int = 1) -> SelectResult:
    """Pick the 2-4 most relevant library pages for the question by reasoning over the
    shelf-index. Drops any returned id that is not a known page (no fabricated targets)."""
    shelf = Path(shelf_index_path).read_text(encoding="utf-8")
    base = (f"{prompts.SELECT_FRAGMENT}\n\nQuestion: {question}\n\n"
            f"Shelf-index:\n{shelf}")
    schema = _select_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            result = SelectResult.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\nReturn valid JSON only."
            continue
        return SelectResult(page_ids=[p for p in result.page_ids if p in set(known_pages)])
    raise ValueError(f"select failed after {max_repairs} repair(s): {last_error}")
```
(Ensure `Answer`/`SelectResult` are imported and `ValidationError`/`prompts`/`Path` are already imported in pipeline.py — they are.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -k select -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/contracts.py plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_query_pipeline.py
git commit -m "feat(kb-offline): SelectResult contract + select pipeline op (drops unknown ids) (#211)"
```

---

## Task 2: `synthesize` pipeline op (claims + verbatim spans; strips model status)

**Files:** Modify `scripts/pipeline.py`; Test `tests/test_kb_offline_query_pipeline.py`

- [ ] **Step 1: Write the failing test**

Append:
```python
from sdlc_knowledge_base_scripts.pipeline import synthesize


def test_synthesize_returns_claims_and_strips_model_status(tmp_path):
    payload = json.dumps({
        "claims": [{
            "text": "Widgets cut cost 30%.",
            "cited_pages": [{"library": "local", "page": "a.md"}],
            "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}],
            "entailment_status": "supported",  # model-supplied — MUST be discarded
            "high_impact": True,               # model-supplied — MUST be discarded
        }],
        "rendered_text": "Widgets cut cost 30%.",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload
    ans = synthesize("q", [{"page": "a.md", "content": "cost fell 30%"}], backend=be)
    assert ans.claims[0].text == "Widgets cut cost 30%."
    assert ans.claims[0].entailment_status is None   # stripped — verifier assigns it
    assert ans.claims[0].high_impact is False         # stripped — verifier assigns it
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -k synthesize -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `synthesize`**

Append to `scripts/pipeline.py`:
```python
def _answer_schema() -> dict:
    return Answer.model_json_schema()


def synthesize(question, pages, *, backend, max_repairs: int = 1) -> Answer:
    """Answer using only the supplied pages. Returns claims with cited_pages + verbatim
    evidence_spans. The model NEVER sets entailment_status/high_impact — both are stripped
    here so only the verifier assigns them."""
    pages_block = "\n\n".join(f"<page id={p['page']}>\n{p['content']}\n</page>" for p in pages)
    base = (f"{prompts.SYNTHESIZE_FRAGMENT}\n\nQuestion: {question}\n\nPages:\n{pages_block}")
    schema = _answer_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            ans = Answer.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\nReturn valid JSON only."
            continue
        for c in ans.claims:                      # strip model-supplied verifier fields
            c.entailment_status = None
            c.high_impact = False
        return ans
    raise ValueError(f"synthesize failed after {max_repairs} repair(s): {last_error}")
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_pipeline.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/pipeline.py tests/test_kb_offline_query_pipeline.py
git commit -m "feat(kb-offline): synthesize pipeline op (claims+spans; strips model-set verifier fields) (#211)"
```

---

## Task 3: Grounding cap (`entailment.ground_claim`)

**Files:** Create `scripts/entailment.py`; Test `tests/test_kb_offline_entailment.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_entailment.py`:
```python
"""Tests for the entailment verifier (grounding cap + judge + high_impact)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.contracts import Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.entailment import ground_claim


def _claim(span_text, page="a.md"):
    return Claim(text="c", cited_pages=[PageRef(library="local", page=page)],
                 evidence_spans=[Span(page=page, text=span_text)])


PAGES = {"a.md": "The study found that cost fell 30% over two years."}


def test_verbatim_span_caps_supported():
    assert ground_claim(_claim("cost fell 30%"), PAGES) == EntailmentStatus.supported


def test_normalized_verbatim_caps_supported():
    # case + whitespace differences still ground verbatim
    assert ground_claim(_claim("COST   fell 30%"), PAGES) == EntailmentStatus.supported


def test_fuzzy_only_caps_partial():
    # most tokens present but not a contiguous substring -> fuzzy -> partial
    assert ground_claim(_claim("cost fell by thirty percent over two years"), PAGES) \
        == EntailmentStatus.partial


def test_no_match_unsupported():
    assert ground_claim(_claim("revenue tripled"), PAGES) == EntailmentStatus.unsupported


def test_cited_page_not_in_read_set_unsupported():
    c = Claim(text="c", cited_pages=[PageRef(library="local", page="ghost.md")],
              evidence_spans=[Span(page="ghost.md", text="anything")])
    assert ground_claim(c, PAGES) == EntailmentStatus.unsupported
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_entailment.py -k ground -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `ground_claim`**

Create `scripts/entailment.py`:
```python
"""Entailment verifier (#211, M1c-1). Deterministic grounding cap + per-claim LLM-judge.
final entailment_status = min(grounding cap, judge grade). high_impact is verifier-assigned.
The model never sets these — see pipeline.synthesize which strips them."""
from __future__ import annotations

import re

from .contracts import Answer, Claim, EntailmentStatus

_RANK = {EntailmentStatus.unsupported: 0, EntailmentStatus.partial: 1, EntailmentStatus.supported: 2}
_WORD = re.compile(r"\w+")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _min_status(a: EntailmentStatus, b: EntailmentStatus) -> EntailmentStatus:
    return a if _RANK[a] <= _RANK[b] else b


def ground_claim(claim: Claim, pages: dict, *, fuzzy_threshold: float = 0.8) -> EntailmentStatus:
    """Deterministic grounding cap for one claim:
      - any cited_page not in the read `pages` -> unsupported (hard reject)
      - a verbatim normalized-substring span on its cited page -> supported cap
      - else a fuzzy span (>= fuzzy_threshold of its tokens present on the page) -> partial cap
      - else unsupported
    """
    for ref in claim.cited_pages:
        if ref.page not in pages:
            return EntailmentStatus.unsupported

    best = EntailmentStatus.unsupported
    for span in claim.evidence_spans:
        page_text = pages.get(span.page)
        if page_text is None:
            return EntailmentStatus.unsupported
        norm_page = _norm(page_text)
        if _norm(span.text) in norm_page:
            return EntailmentStatus.supported            # verbatim wins immediately
        page_tokens = set(_tokens(page_text))
        span_tokens = _tokens(span.text)
        if span_tokens:
            overlap = sum(1 for t in span_tokens if t in page_tokens) / len(span_tokens)
            if overlap >= fuzzy_threshold:
                best = _min_status(EntailmentStatus.partial, EntailmentStatus.supported)
                best = EntailmentStatus.partial
    return best
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_entailment.py -k ground -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/entailment.py tests/test_kb_offline_entailment.py
git commit -m "feat(kb-offline): entailment grounding cap (verbatim->supported, fuzzy->partial) (#211)"
```

---

## Task 4: `high_impact` classifier + `judge_claim`

**Files:** Modify `scripts/entailment.py`; Test `tests/test_kb_offline_entailment.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
from sdlc_knowledge_base_scripts.entailment import classify_high_impact, judge_claim
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_high_impact_numbers_and_modals():
    assert classify_high_impact("Cost fell 30% in 2024.") is True       # number/%
    assert classify_high_impact("Teams should adopt trunk-based dev.") is True  # recommendation
    assert classify_high_impact("This must meet ISO 26262 compliance.") is True  # safety/compliance
    assert classify_high_impact("The topic is broadly discussed.") is False     # none


def test_judge_claim_maps_backend_grade():
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "partial"}'
    c = _claim("cost fell 30%")
    assert judge_claim(c, PAGES, backend=be) == EntailmentStatus.partial


def test_judge_invalid_grade_defaults_unsupported():
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "bogus"}'
    assert judge_claim(_claim("x"), PAGES, backend=be) == EntailmentStatus.unsupported
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_entailment.py -k "high_impact or judge" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement**

Append to `scripts/entailment.py`:
```python
import json

_HIGH_IMPACT_RE = re.compile(
    r"\d|%|\bshould\b|\bmust\b|\brecommend|\brequire|\bsafety\b|\bcomplian|\bregulat|"
    r"\bISO\s?\d|\bIEC\b|\bFDA\b|\bDO-178|\b62304\b|\b26262\b",
    re.IGNORECASE,
)


def classify_high_impact(claim_text: str) -> bool:
    """Verifier-owned (never model-supplied): a claim is high-impact if it carries a
    number/statistic/unit, a recommendation/modal directive, or safety/compliance/regulatory
    language. Conservative: when these markers appear, treat as high-impact."""
    return bool(_HIGH_IMPACT_RE.search(claim_text))


def judge_claim(claim: Claim, pages: dict, *, backend) -> EntailmentStatus:
    """LLM-judge: does the cited page text support the claim? Returns supported/partial/
    unsupported. Any non-conforming output defaults to unsupported (conservative)."""
    cited = "\n".join(f"<page id={r.page}>\n{pages.get(r.page, '')}\n</page>" for r in claim.cited_pages)
    prompt = (
        "Judge whether the cited page text SUPPORTS the claim. Reply ONLY a JSON object "
        '{"status": "supported"|"partial"|"unsupported"}.\n\n'
        f"Claim: {claim.text}\n\nCited pages:\n{cited}"
    )
    raw = backend.generate(prompt, schema={"type": "object",
                                           "properties": {"status": {"type": "string"}},
                                           "required": ["status"]})
    try:
        status = json.loads(raw).get("status", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        return EntailmentStatus.unsupported
    try:
        return EntailmentStatus(status)
    except ValueError:
        return EntailmentStatus.unsupported
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_entailment.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/entailment.py tests/test_kb_offline_entailment.py
git commit -m "feat(kb-offline): high_impact classifier + LLM-judge (defaults unsupported) (#211)"
```

---

## Task 5: `verify_entailment` (compose grounding cap + judge + high_impact)

**Files:** Modify `scripts/entailment.py`; Test `tests/test_kb_offline_entailment.py`

- [ ] **Step 1: Write the failing tests**

Append:
```python
from sdlc_knowledge_base_scripts.entailment import verify_entailment


def test_verify_caps_below_judge(tmp_path):
    # span only fuzzy-matches (cap=partial); judge says supported; final = min = partial
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "supported"}'
    ans = Answer(claims=[_claim("cost fell by thirty percent over two years")])
    out = verify_entailment(ans, PAGES, backend=be)
    assert out.claims[0].entailment_status == EntailmentStatus.partial
    assert out.claims[0].high_impact is True   # has a number/percent word


def test_verify_judge_lowers_within_cap(tmp_path):
    # verbatim span (cap=supported); judge says unsupported; final = unsupported
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: '{"status": "unsupported"}'
    ans = Answer(claims=[_claim("cost fell 30%")])
    out = verify_entailment(ans, PAGES, backend=be)
    assert out.claims[0].entailment_status == EntailmentStatus.unsupported


def test_verify_skips_judge_when_grounding_unsupported(tmp_path):
    calls = {"n": 0}
    be = FakeBackend()
    def gen(prompt, schema=None):
        calls["n"] += 1
        return '{"status": "supported"}'
    be.generate = gen
    ans = Answer(claims=[_claim("revenue tripled")])   # no grounding -> unsupported
    out = verify_entailment(ans, PAGES, backend=be)
    assert out.claims[0].entailment_status == EntailmentStatus.unsupported
    assert calls["n"] == 0   # judge not called when grounding already unsupported
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_entailment.py -k verify -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `verify_entailment`**

Append to `scripts/entailment.py`:
```python
def verify_entailment(answer: Answer, pages: dict, *, backend) -> Answer:
    """Assign each claim's entailment_status = min(grounding cap, LLM-judge grade), and set
    high_impact deterministically. Skips the judge call when grounding already caps at
    unsupported. Returns a new Answer (claims mutated in place is fine — it's the pipeline's)."""
    for claim in answer.claims:
        claim.high_impact = classify_high_impact(claim.text)
        cap = ground_claim(claim, pages)
        if cap == EntailmentStatus.unsupported:
            claim.entailment_status = EntailmentStatus.unsupported
            continue
        grade = judge_claim(claim, pages, backend=backend)
        claim.entailment_status = _min_status(cap, grade)
    return answer
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_entailment.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/entailment.py tests/test_kb_offline_entailment.py
git commit -m "feat(kb-offline): verify_entailment composes grounding cap + judge (min) + high_impact (#211)"
```

---

## Task 6: provenance filter + publication policy

**Files:** Create `scripts/provenance.py`, `scripts/publication.py`; Test `tests/test_kb_offline_provenance.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_provenance.py`:
```python
"""Tests for provenance/layer filtering + publication policy."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.provenance import filter_pages
from sdlc_knowledge_base_scripts.publication import publish


def _page(tmp_path, name, layer, confidence):
    (tmp_path / name).write_text(f"---\nlayer: {layer}\nconfidence: {confidence}\n---\n# {name}\n")


def test_filter_by_layer(tmp_path):
    _page(tmp_path, "a.md", "evidence", "high")
    _page(tmp_path, "b.md", "domain", "high")
    kept = filter_pages(tmp_path, ["a.md", "b.md"], layer="evidence", min_confidence=None)
    assert kept == ["a.md"]


def test_filter_by_min_confidence(tmp_path):
    _page(tmp_path, "a.md", "domain", "low")
    _page(tmp_path, "b.md", "domain", "high")
    kept = filter_pages(tmp_path, ["a.md", "b.md"], layer=None, min_confidence="medium")
    assert kept == ["b.md"]   # low < medium dropped


def test_publish_policy_splits_claims():
    def claim(text, status):
        c = Claim(text=text, cited_pages=[PageRef(library="local", page="a.md")],
                  evidence_spans=[Span(page="a.md", text="x")])
        c.entailment_status = status
        return c
    ans = Answer(claims=[
        claim("supported one", EntailmentStatus.supported),
        claim("partial one", EntailmentStatus.partial),
        claim("unsupported one", EntailmentStatus.unsupported),
    ])
    rendered, rejected = publish(ans)
    assert "supported one" in rendered
    assert "partial one" in rendered and "partially supported" in rendered.lower()
    assert "unsupported one" not in rendered
    assert any("unsupported one" in r["text"] for r in rejected)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_provenance.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `scripts/provenance.py`:
```python
"""Provenance/layer filtering for query candidate pages (#211, M1c-1)."""
from __future__ import annotations

import re
from pathlib import Path

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def page_frontmatter(library_path, page_name) -> dict:
    """Return the page's YAML frontmatter as a dict (empty if absent/unreadable)."""
    import yaml
    p = Path(library_path) / page_name
    if not p.is_file():
        return {}
    m = _FRONTMATTER.match(p.read_text(encoding="utf-8"))
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def filter_pages(library_path, page_names, *, layer=None, min_confidence=None) -> list[str]:
    """Keep pages whose frontmatter satisfies the layer and min-confidence filters.
    Pages missing the relevant field are dropped when a filter is active."""
    min_rank = _CONFIDENCE_RANK.get(min_confidence) if min_confidence else None
    kept = []
    for name in page_names:
        fm = page_frontmatter(library_path, name)
        if layer is not None and fm.get("layer") != layer:
            continue
        if min_rank is not None and _CONFIDENCE_RANK.get(fm.get("confidence"), -1) < min_rank:
            continue
        kept.append(name)
    return kept
```

Create `scripts/publication.py`:
```python
"""Query output publication policy (#211, M1c-1, addendum decision 7).
supported -> published; partial -> published WITH a caveat; unsupported -> excluded and
reported in rejected_claims."""
from __future__ import annotations

from .contracts import Answer, EntailmentStatus


def publish(answer: Answer) -> tuple[str, list[dict]]:
    """Return (rendered_text, rejected_claims). supported claims are published as-is;
    partial claims are published with a '(partially supported)' caveat; unsupported claims
    are excluded from the body and listed in rejected_claims."""
    lines: list[str] = []
    rejected: list[dict] = []
    for c in answer.claims:
        if c.entailment_status == EntailmentStatus.supported:
            lines.append(c.text)
        elif c.entailment_status == EntailmentStatus.partial:
            lines.append(f"{c.text} (partially supported)")
        else:
            rejected.append({"text": c.text, "reason": "unsupported",
                             "high_impact": c.high_impact})
    return "\n".join(lines), rejected
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_provenance.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/provenance.py plugins/sdlc-knowledge-base/scripts/publication.py tests/test_kb_offline_provenance.py
git commit -m "feat(kb-offline): provenance/layer filter + publication policy (supported/partial/rejected) (#211)"
```

---

## Task 7: read-only `query_graph` + CLI `query` + live smoke + gate

**Files:** Create `scripts/graphs/query_graph.py`; Modify `scripts/kb_offline_cli.py`; Test `tests/test_kb_offline_query_graph.py`, `test_kb_offline_cli.py`, `test_kb_offline_ollama_smoke.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_query_graph.py`:
```python
"""Tests for the read-only query_graph (FakeBackend)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph


def _lib(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n")
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\ncost fell 30% over two years\n")
    return lib


def test_query_graph_publishes_grounded_claim(tmp_path):
    lib = _lib(tmp_path)

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:                       # select
            return json.dumps({"page_ids": ["a.md"]})
        return json.dumps({"claims": [{                   # synthesize
            "text": "Cost fell 30%.",
            "cited_pages": [{"library": "local", "page": "a.md"}],
            "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
            "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_query_graph(be)
    out = graph.invoke(
        {"library_path": str(lib), "question": "what happened to cost?"},
        config={"configurable": {"thread_id": "q1"}})
    assert "Cost fell 30%." in out["rendered_text"]
    assert out["rejected_claims"] == []
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `query_graph.py`**

Create `scripts/graphs/query_graph.py` (read-only — no lock/journal):
```python
"""Read-only query graph (#211, M1c-1): select -> read -> synthesize -> verify -> publish.
No lock/fencing/journal (query never mutates the library)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, TypedDict

os.environ.setdefault("LANGSMITH_TRACING", "false")  # offline integrity
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402

from ..entailment import verify_entailment  # noqa: E402
from ..pipeline import select, synthesize  # noqa: E402
from ..provenance import filter_pages  # noqa: E402
from ..publication import publish  # noqa: E402


class QueryState(TypedDict, total=False):
    library_path: str
    question: str
    layer: Optional[str]
    min_confidence: Optional[str]
    page_ids: list
    pages: list
    rendered_text: str
    rejected_claims: list


def build_query_graph(backend):
    def n_select(state: QueryState) -> dict:
        lib = Path(state["library_path"])
        shelf = lib / "_shelf-index.md"
        known = {p.name for p in lib.glob("*.md")
                 if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        candidates = filter_pages(lib, sorted(known), layer=state.get("layer"),
                                  min_confidence=state.get("min_confidence"))
        res = select(state["question"], shelf, backend=backend, known_pages=set(candidates))
        return {"page_ids": res.page_ids}

    def n_read(state: QueryState) -> dict:
        lib = Path(state["library_path"])
        pages = [{"page": pid, "content": (lib / pid).read_text(encoding="utf-8")}
                 for pid in state["page_ids"] if (lib / pid).is_file()]
        return {"pages": pages}

    def n_synthesize(state: QueryState) -> dict:
        ans = synthesize(state["question"], state["pages"], backend=backend)
        return {"_answer": ans} if False else {"pages": state["pages"], "_synth": ans.model_dump()}

    # NOTE: LangGraph state must be JSON-ish for the checkpointer; carry the Answer as a dict
    def n_verify_publish(state: QueryState) -> dict:
        from ..contracts import Answer
        ans = Answer.model_validate(state["_synth"])
        pages_by_name = {p["page"]: p["content"] for p in state["pages"]}
        verified = verify_entailment(ans, pages_by_name, backend=backend)
        rendered, rejected = publish(verified)
        return {"rendered_text": rendered, "rejected_claims": rejected}

    builder = StateGraph(QueryState)
    builder.add_node("select", n_select)
    builder.add_node("read", n_read)
    builder.add_node("synthesize", n_synthesize)
    builder.add_node("verify_publish", n_verify_publish)
    builder.add_edge(START, "select")
    builder.add_edge("select", "read")
    builder.add_edge("read", "synthesize")
    builder.add_edge("synthesize", "verify_publish")
    builder.add_edge("verify_publish", END)
    return builder.compile(checkpointer=MemorySaver())
```
Note: add `_synth` to `QueryState` (a dict) so the synthesized Answer survives the checkpointer between nodes. Clean up the `n_synthesize` return to just `return {"_synth": synthesize(...).model_dump()}` and add `_synth: dict` to QueryState; verify against the test and adjust if the model_dump round-trips cleanly (it does for pydantic v2).

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py -v`
Expected: PASS. (If the checkpointer rejects non-JSON state, the `_synth` dict via `model_dump()`/`model_validate()` is the fix — already applied.)

- [ ] **Step 5: Add CLI `query` + a CLI test**

Append to `tests/test_kb_offline_cli.py`:
```python
def test_cli_query_prints_answer(tmp_path, capsys):
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
    rc = cli.main(["query", "what about cost?", "--library", str(lib), "--backend", "fake"],
                  backend_override=be)
    assert rc == 0
    assert "Cost fell 30%." in capsys.readouterr().out
```
In `kb_offline_cli.py`, add a `query` subparser (`question` positional; `--library`, `--backend`, `--layer` default None, `--min-confidence` default None) and `_cmd_query`:
```python
def _cmd_query(args: argparse.Namespace, backend_override) -> int:
    from .graphs.query_graph import build_query_graph
    backend = _make_backend(args.backend, backend_override)
    graph = build_query_graph(backend)
    out = graph.invoke(
        {"library_path": args.library, "question": args.question,
         "layer": args.layer, "min_confidence": args.min_confidence},
        config={"configurable": {"thread_id": "query"}})
    print(out.get("rendered_text", ""))
    rejected = out.get("rejected_claims", [])
    if rejected:
        print(f"\n[{len(rejected)} claim(s) excluded as unsupported]", file=sys.stderr)
    return 0
```
(`sys` is imported in the CLI. Add the subparser + `if args.cmd == "query": return _cmd_query(args, backend_override)` dispatch. `query` takes no `--timestamp`/`--resume` — it's read-only, no run lifecycle.)

- [ ] **Step 6: Append the live Ollama query smoke** to `tests/test_kb_offline_ollama_smoke.py`:
```python
@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_query(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n"
                                 "# DORA\nElite teams deploy multiple times per day.\n")
    graph = build_query_graph(OllamaBackend(model="gpt-oss:20b"))
    out = graph.invoke({"library_path": str(lib), "question": "How often do elite teams deploy?"},
                       config={"configurable": {"thread_id": "ql"}})
    # the query path ran end-to-end and returned a structured result (claims verified or all rejected)
    assert "rendered_text" in out and "rejected_claims" in out
```

- [ ] **Step 7: Run everything + validation gate**

Run:
```bash
.venv/bin/python -m pytest tests/test_kb_offline_query_graph.py tests/test_kb_offline_cli.py tests/test_kb_offline_query_pipeline.py tests/test_kb_offline_entailment.py tests/test_kb_offline_provenance.py -v
.venv/bin/python -m pytest tests/ -k "kb and not live" -q
.venv/bin/python -m pytest tests/test_kb_offline_ollama_smoke.py -k query -v -s   # live, ~30-90s
.venv/bin/python -m flake8 plugins/sdlc-knowledge-base/scripts/entailment.py plugins/sdlc-knowledge-base/scripts/provenance.py plugins/sdlc-knowledge-base/scripts/publication.py plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/pipeline.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py
.venv/bin/python tools/validation/check-feature-proposal.py --branch feature/211-kb-offline-langgraph
.venv/bin/python tools/validation/check-prompt-parity.py
```
All green (live query may SKIP if Ollama absent; report what gpt-oss:20b produced if it ran).

- [ ] **Step 8: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_query_graph.py tests/test_kb_offline_cli.py tests/test_kb_offline_ollama_smoke.py
git commit -m "feat(kb-offline): read-only query_graph + CLI query + live query smoke (#211)"
```

---

## Self-review notes

- **Addendum coverage (M1c-1):** select (Task 1) + synthesize stripping model verifier fields (Task 2); grounding cap verbatim→supported/fuzzy→partial/none→unsupported + page-not-read→unsupported (Task 3); high_impact verifier-owned classifier + LLM-judge defaulting unsupported (Task 4); verify_entailment final=min(cap,judge), skip-judge-when-unsupported (Task 5); provenance layer/min-confidence filter + publication supported/partial-caveat/unsupported-excluded (Task 6, decision 7); read-only query_graph + CLI query + live smoke (Task 7). Grounding composition = addendum decision 16.
- **Deferred to M1c-2 (correctly absent):** eval frozen suite, labelled fixture, threshold ratification, Ollama-default decision. Federation (multi-library query) and embeddings also absent.
- **Read-only correctness:** query_graph has NO LibraryLock/commit/journal — it only reads pages; safe to run concurrently with nothing to fence. No run-mutation lifecycle in `_cmd_query`.
- **Type/name consistency:** `SelectResult.page_ids`, `select(question, shelf_index_path, *, backend, known_pages)`, `synthesize(question, pages, *, backend)`, `ground_claim(claim, pages)`, `classify_high_impact(text)`, `judge_claim(claim, pages, *, backend)`, `verify_entailment(answer, pages, *, backend)`, `filter_pages(library, page_names, *, layer, min_confidence)`, `publish(answer) -> (str, list[dict])`, `build_query_graph(backend)`, `QueryState` keys — consistent across tasks and matching M0 contracts.
- **Known check for execution:** Task 7 carries the synthesized `Answer` between graph nodes as a dict (`_synth` via `model_dump()`/`model_validate()`) because the checkpointer serializes state — confirm the round-trip in Step 4 and keep `_synth: dict` in QueryState (remove the dead `if False` placeholder in the draft).

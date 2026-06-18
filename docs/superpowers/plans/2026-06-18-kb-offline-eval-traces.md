# kb-offline eval traces — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `kb-offline eval release` self-documenting — every run persists a per-question / per-verifier-label, per-stage diagnostic trace (raw model I/O, classified select drops, grounding cap vs final status, per-call timings) alongside its report, on by default with a `--no-trace` opt-out.

**Architecture:** A read-only trace layer in the eval harness. `RecordingBackend` stays a stateless per-call recorder; all derived fields (`stage_invocation`/`repair_attempt`/`accepted`) and drop classification are **pure functions** in a new `eval/trace.py`, computed by post-processing each per-question / per-label record *slice*. No pipeline contract or routing change; one behaviour-identical refactor (extract `known_page_ids`).

**Tech Stack:** Python 3.9+, `.venv`, pytest, pydantic v2. No new deps. `flake8 --max-line-length=127`. Spec: `docs/superpowers/specs/2026-06-18-kb-offline-eval-traces-design.md`. Commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## Environment & conventions
- `.venv` for everything; run pytest from the repo root. Source under `plugins/sdlc-knowledge-base/scripts/`; tests import the `sdlc_knowledge_base_scripts` package (registered by `tests/conftest.py`).
- Branch `feature/211-kb-offline-langgraph` (one accumulating EPIC branch; no PR).
- TDD throughout: write the failing test, watch it fail, implement minimally, watch it pass, commit.

## File structure

| File | Change | Responsibility |
|---|---|---|
| `plugins/sdlc-knowledge-base/scripts/eval/report.py` | modify | add `safe_model_name()` (filename sanitizer) |
| `plugins/sdlc-knowledge-base/scripts/provenance.py` | modify | add `known_page_ids(lib)` shared helper |
| `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py` | modify | `n_select` calls `known_page_ids` (byte-identical) |
| `plugins/sdlc-knowledge-base/scripts/eval/trace.py` | **new** | pure trace helpers: `derive_model_calls`, `classify_select_drops`, row builders |
| `plugins/sdlc-knowledge-base/scripts/eval/runner.py` | modify | `RecordingBackend` enrichment; `trace` side-channel in `run_questions`/`run_verifier_labels`/`score_run` |
| `plugins/sdlc-knowledge-base/scripts/eval/harness.py` | modify | `first_pass_json_validity` reads `json_parse_ok` |
| `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py` | modify | `--no-trace`; write trace JSONL per run; report stem uses `safe_model_name` |
| `tests/test_kb_offline_eval_naming.py` | **new** | `safe_model_name` |
| `tests/test_kb_offline_provenance.py` | modify/new | `known_page_ids` |
| `tests/test_kb_offline_eval_trace.py` | **new** | pure trace helpers + runner integration |
| `tests/test_kb_offline_eval_runner.py` | modify | `RecordingBackend` enrichment + harness rename guard |
| `tests/test_kb_offline_cli.py` | modify | `--no-trace` / default trace write / invariance |

---

## Task 1: `safe_model_name()` filename sanitizer

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/eval/report.py`; Test `tests/test_kb_offline_eval_naming.py` (new).

- [ ] **Step 1: Write the failing test** — create `tests/test_kb_offline_eval_naming.py`:
```python
"""safe_model_name filename sanitizer (#211, eval traces)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.report import safe_model_name


def test_safe_model_name_replaces_colon():
    assert safe_model_name("gemma4:12b") == "gemma4_12b"


def test_safe_model_name_replaces_slash_and_whitespace():
    assert safe_model_name("ns/custom:tag") == "ns_custom_tag"
    assert safe_model_name("a b") == "a_b"


def test_safe_model_name_idempotent_on_clean_name():
    assert safe_model_name("claude-sonnet-4-6") == "claude-sonnet-4-6"
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_naming.py -v` → FAIL (ImportError: cannot import name `safe_model_name`).

- [ ] **Step 3: Implement** — add to `plugins/sdlc-knowledge-base/scripts/eval/report.py` (top-level, after the module docstring/imports):
```python
import re as _re

_UNSAFE_NAME = _re.compile(r"[^A-Za-z0-9._-]+")


def safe_model_name(model: str) -> str:
    """Filesystem-safe form of a model id for report/trace filenames: collapse any run of
    characters outside [A-Za-z0-9._-] (e.g. ':' '/' whitespace) to a single underscore."""
    return _UNSAFE_NAME.sub("_", model)
```

- [ ] **Step 4: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_naming.py -v` → PASS (3). `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/eval/report.py tests/test_kb_offline_eval_naming.py` → clean.

- [ ] **Step 5: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/eval/report.py tests/test_kb_offline_eval_naming.py
git commit -m "$(printf 'feat(kb-offline): safe_model_name filename sanitizer for eval traces (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 2: `known_page_ids(lib)` shared helper + `n_select` refactor

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/provenance.py`, `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py`; Test `tests/test_kb_offline_provenance.py`.

**Context:** `n_select` currently inlines `known = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}`. The trace must recompute the identical set; extract it so they can't drift. READ `provenance.py` first to match its import style.

- [ ] **Step 1: Write the failing test** — append to `tests/test_kb_offline_provenance.py` (create with the header below if it does not exist):
```python
"""Provenance helpers (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.provenance import known_page_ids


def test_known_page_ids_roots_only_excludes_index_files(tmp_path):
    (tmp_path / "dora.md").write_text("x", encoding="utf-8")
    (tmp_path / "ci-cd.md").write_text("x", encoding="utf-8")
    (tmp_path / "_shelf-index.md").write_text("x", encoding="utf-8")
    (tmp_path / "log.md").write_text("x", encoding="utf-8")
    (tmp_path / "_index.md").write_text("x", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("x", encoding="utf-8")  # nested must NOT be known
    assert known_page_ids(tmp_path) == {"dora.md", "ci-cd.md"}
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_provenance.py -k known_page_ids -v` → FAIL (ImportError).

- [ ] **Step 3: Implement the helper** — add to `plugins/sdlc-knowledge-base/scripts/provenance.py`:
```python
from pathlib import Path

_INDEX_FILES = {"_shelf-index.md", "log.md", "_index.md"}


def known_page_ids(lib) -> set[str]:
    """The set of routable library page ids: root-level *.md minus the index/log files.
    Single source of truth shared by the query graph's select node and the eval trace
    (root glob only — nested files are not routable). (#211)"""
    return {p.name for p in Path(lib).glob("*.md") if p.name not in _INDEX_FILES}
```
(If `provenance.py` already imports `Path`/defines a similar constant, reuse it instead of duplicating.)

- [ ] **Step 4: Refactor `n_select`** in `plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py` — replace the inline known-set with the helper. Change:
```python
        known = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
```
to:
```python
        from ..provenance import known_page_ids
        known = known_page_ids(lib)
```
(Keep the existing `from ..provenance import filter_pages` import; you may consolidate to `from ..provenance import filter_pages, known_page_ids` at the top of the file if that matches the file's import style.)

- [ ] **Step 5: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_provenance.py -k known_page_ids -v` → PASS. Then the query path regression: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass (n_select still routes identically). `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/provenance.py plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py tests/test_kb_offline_provenance.py` → clean.

- [ ] **Step 6: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/provenance.py plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py tests/test_kb_offline_provenance.py
git commit -m "$(printf 'refactor(kb-offline): extract known_page_ids shared by n_select + trace (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 3: `RecordingBackend` stateless enrichment + harness rename

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/eval/runner.py`, `plugins/sdlc-knowledge-base/scripts/eval/harness.py`; Test `tests/test_kb_offline_eval_runner.py`.

**Context (spec Unit A):** `RecordingBackend` records ONLY stateless per-call fields: `{stage, first_pass, json_parse_ok, elapsed_ms, raw}`. It does NOT compute invocation/attempt/accepted. Rename `valid_json` → `json_parse_ok` and update `harness.first_pass_json_validity` (value identical).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_kb_offline_eval_runner.py`:
```python
def test_recording_backend_records_stage_rawtiming_jsonparse():
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts import prompts
    inner = FakeBackend()
    seq = iter(["not json", '{"page_ids": ["dora.md"]}', "Judge response not json"])
    inner.generate = lambda prompt, schema=None: next(seq)
    rec = RecordingBackend(inner)
    rec.generate(prompts.SELECT_FRAGMENT + "\n\nQuestion: q\n\nShelf-index:\n...")          # select, first pass, bad json
    rec.generate(prompts.SELECT_FRAGMENT + "\n...\n\nPrevious output invalid: x\n...")        # select repair
    rec.generate("Judge whether the cited page text SUPPORTS the claim. ...")                 # judge
    r0, r1, r2 = rec.records
    assert r0["stage"] == "select" and r0["first_pass"] is True and r0["json_parse_ok"] is False
    assert r1["stage"] == "select" and r1["first_pass"] is False and r1["json_parse_ok"] is True
    assert r2["stage"] == "judge" and r2["first_pass"] is True
    assert all("elapsed_ms" in r and isinstance(r["elapsed_ms"], (int, float)) for r in rec.records)
    assert r1["raw"] == '{"page_ids": ["dora.md"]}'
    assert all("valid_json" not in r for r in rec.records)  # renamed away
```
Also update the EXISTING `test_recording_backend_flags_first_pass_and_json_validity` to read `json_parse_ok` instead of `valid_json`:
```python
def test_recording_backend_flags_first_pass_and_json_validity():
    inner = FakeBackend()
    seq = iter(['not json', '{"ok": 1}'])
    inner.generate = lambda prompt, schema=None: next(seq)
    rec = RecordingBackend(inner)
    rec.generate("first attempt")
    rec.generate("retry\n\nPrevious output invalid: x")
    assert rec.records[0]["first_pass"] is True and rec.records[0]["json_parse_ok"] is False
    assert rec.records[1]["first_pass"] is False and rec.records[1]["json_parse_ok"] is True
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_runner.py -k recording_backend -v` → FAIL (KeyError `json_parse_ok` / missing `stage`).

- [ ] **Step 3: Implement** in `plugins/sdlc-knowledge-base/scripts/eval/runner.py`. Add `import time` at the top (next to `import json`/`import sys`). Add a stage classifier and rewrite `RecordingBackend.generate`:
```python
from .. import prompts

_SELECT_KEY = prompts.SELECT_FRAGMENT[:24]
_SYNTH_KEY = prompts.SYNTHESIZE_FRAGMENT[:24]


def _classify_stage(prompt: str) -> str:
    if prompt.startswith("Judge whether"):
        return "judge"
    if _SELECT_KEY in prompt:
        return "select"
    if _SYNTH_KEY in prompt:
        return "synthesize"
    return "other"
```
Then in `RecordingBackend.generate`:
```python
    def generate(self, prompt: str, *, schema=None) -> str:
        t0 = time.monotonic()
        out = self._inner.generate(prompt, schema=schema)
        self.records.append({
            "stage": _classify_stage(prompt),
            "first_pass": _REPAIR_MARKER not in prompt,
            "json_parse_ok": _valid_json(out),
            "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
            "raw": out,
        })
        return out
```
(`runner.py` already imports `prompts`? It imports `from . import harness`; add `from .. import prompts`. `_REPAIR_MARKER` and `_valid_json` already exist in the module.)

- [ ] **Step 4: Update the metric reader** in `plugins/sdlc-knowledge-base/scripts/eval/harness.py` — `first_pass_json_validity` change `r["valid_json"]` to `r["json_parse_ok"]`:
```python
def first_pass_json_validity(rows: list[dict]) -> float:
    first = [r for r in rows if r["first_pass"]]
    if not first:
        return 1.0
    return sum(1 for r in first if r["json_parse_ok"]) / len(first)
```

- [ ] **Step 5: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_runner.py -v` → PASS (existing + new). Full: `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass (the metric value is unchanged). Lint the three files → clean.

- [ ] **Step 6: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/eval/runner.py plugins/sdlc-knowledge-base/scripts/eval/harness.py tests/test_kb_offline_eval_runner.py
git commit -m "$(printf 'feat(kb-offline): RecordingBackend records stage/raw/timing; valid_json->json_parse_ok (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 4: `eval/trace.py` pure derivation — `derive_model_calls`

**Files:** Create `plugins/sdlc-knowledge-base/scripts/eval/trace.py`; Test `tests/test_kb_offline_eval_trace.py` (new).

**Context (spec Unit A/B):** Given a per-question record slice (the stateless records from Task 3), derive `stage_invocation`, `repair_attempt`, `accepted`. A `first_pass` call opens a new invocation per stage; a non-first-pass continues it. `accepted` = last call of each invocation, with the error rules from the spec.

- [ ] **Step 1: Write the failing tests** — create `tests/test_kb_offline_eval_trace.py`:
```python
"""Pure eval-trace derivation helpers (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.trace import derive_model_calls


def _rec(stage, first_pass, ok=True):
    return {"stage": stage, "first_pass": first_pass, "json_parse_ok": ok,
            "elapsed_ms": 1.0, "raw": "{}"}


def test_derive_select_repair_then_synth_then_two_judges_success():
    slice_ = [_rec("select", True, ok=False), _rec("select", False), _rec("synthesize", True),
              _rec("judge", True), _rec("judge", True)]
    calls = derive_model_calls(slice_, errored=False, error_msg="")
    # select invocation 1, attempts 1 & 2
    assert (calls[0]["stage_invocation"], calls[0]["repair_attempt"]) == (1, 1)
    assert (calls[1]["stage_invocation"], calls[1]["repair_attempt"]) == (1, 2)
    # synthesize invocation 1, attempt 1
    assert (calls[2]["stage_invocation"], calls[2]["repair_attempt"]) == (1, 1)
    # two judges => invocations 1 and 2, each attempt 1 (NOT a repair)
    assert (calls[3]["stage_invocation"], calls[3]["repair_attempt"]) == (1, 1)
    assert (calls[4]["stage_invocation"], calls[4]["repair_attempt"]) == (2, 1)
    # success: last call of each invocation accepted
    assert [c["accepted"] for c in calls] == [False, True, True, True, True]


def test_derive_accepted_on_select_repair_exhaustion_error():
    slice_ = [_rec("select", True, ok=False), _rec("select", False, ok=False)]
    calls = derive_model_calls(slice_, errored=True, error_msg="select failed after 1 repair(s): ...")
    # terminal (only) invocation is the failed stage -> nothing accepted
    assert [c["accepted"] for c in calls] == [False, False]


def test_derive_accepted_on_synth_exhaustion_keeps_select_accepted():
    slice_ = [_rec("select", True), _rec("synthesize", True, ok=False), _rec("synthesize", False, ok=False)]
    calls = derive_model_calls(slice_, errored=True, error_msg="synthesize failed after 1 repair(s): ...")
    # select invocation accepted; terminal synthesize invocation not
    assert calls[0]["accepted"] is True
    assert calls[1]["accepted"] is False and calls[2]["accepted"] is False


def test_derive_accepted_on_non_model_error_keeps_all_invocation_tails():
    # e.g. a publish/read error after synthesize was used -> every invocation's last call accepted
    slice_ = [_rec("select", True), _rec("synthesize", True)]
    calls = derive_model_calls(slice_, errored=True, error_msg="publish exploded")
    assert calls[0]["accepted"] is True and calls[1]["accepted"] is True
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -v` → FAIL (ImportError).

- [ ] **Step 3: Implement** — create `plugins/sdlc-knowledge-base/scripts/eval/trace.py`:
```python
"""Pure eval-trace helpers (#211): derive per-stage invocation/attempt/accepted from a
per-question (or per-label) RecordingBackend record slice, and classify select drops.
No model calls, no I/O — testable in isolation."""
from __future__ import annotations

_MODEL_FAIL_PREFIXES = ("select failed after", "synthesize failed after")


def derive_model_calls(records: list[dict], *, errored: bool, error_msg: str) -> list[dict]:
    """Annotate a record slice (stateless {stage, first_pass, json_parse_ok, elapsed_ms, raw})
    with stage_invocation, repair_attempt, accepted. A first_pass call opens a new invocation
    of its stage; a non-first_pass call continues it. accepted = the last call of each
    invocation that the pipeline used (positional):
      - success: every invocation's last call;
      - select/synthesize repair-exhaustion error: every invocation's last call EXCEPT the
        terminal invocation (the failed stage);
      - any other (non-model) error: every invocation's last call (model stages completed)."""
    out = []
    inv_counter: dict[str, int] = {}
    cur_attempt: dict[str, int] = {}
    for rec in records:
        stage = rec["stage"]
        if rec["first_pass"]:
            inv_counter[stage] = inv_counter.get(stage, 0) + 1
            cur_attempt[(stage, inv_counter[stage])] = 1
        else:
            cur_attempt[(stage, inv_counter.get(stage, 1))] = cur_attempt.get((stage, inv_counter.get(stage, 1)), 1) + 1
        inv = inv_counter.get(stage, 1)
        out.append({**rec, "stage_invocation": inv, "repair_attempt": cur_attempt[(stage, inv)],
                    "accepted": False})

    # index of the last call of each (stage, invocation) group
    last_idx: dict[tuple, int] = {}
    for i, c in enumerate(out):
        last_idx[(c["stage"], c["stage_invocation"])] = i
    tail_indices = set(last_idx.values())

    model_fail = errored and error_msg.startswith(_MODEL_FAIL_PREFIXES)
    terminal_key = (out[-1]["stage"], out[-1]["stage_invocation"]) if out else None
    for key, idx in last_idx.items():
        if model_fail and key == terminal_key:
            continue  # failed stage produced no usable output
        out[idx]["accepted"] = True
    _ = tail_indices  # (kept for readability; tails are exactly last_idx values)
    return out
```

- [ ] **Step 4: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -v` → PASS (4). Lint `plugins/sdlc-knowledge-base/scripts/eval/trace.py tests/test_kb_offline_eval_trace.py` → clean. (Remove the `_ = tail_indices` line if flake8 prefers; it is only illustrative.)

- [ ] **Step 5: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/eval/trace.py tests/test_kb_offline_eval_trace.py
git commit -m "$(printf 'feat(kb-offline): trace.derive_model_calls — invocation/attempt/accepted from slice (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 5: `eval/trace.py` — `classify_select_drops`

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/eval/trace.py`; Test `tests/test_kb_offline_eval_trace.py`.

**Context (spec Unit B):** classify each model-selected id that is not in the final routed set, and compute the complementary recall signal. `not_selected` is impossible (select preserves eligible ids), so only `unknown_id` / `filtered_out`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_kb_offline_eval_trace.py`:
```python
from sdlc_knowledge_base_scripts.eval.trace import classify_select_drops


def test_classify_select_drops_unknown_and_filtered():
    known = {"dora.md", "ci-cd.md", "sdlc-assured.md"}
    eligible = {"dora.md", "ci-cd.md"}                     # sdlc-assured filtered out by layer
    model_selected = ["dora.md", "telemetry.md", "sdlc-assured.md"]
    final = ["dora.md"]
    dropped, eligible_unselected = classify_select_drops(model_selected, final, known, eligible)
    by_id = {d["id"]: d["reason"] for d in dropped}
    assert by_id == {"telemetry.md": "unknown_id", "sdlc-assured.md": "filtered_out"}
    assert eligible_unselected == ["ci-cd.md"]             # eligible but the model didn't pick it


def test_classify_select_drops_empty_when_all_final():
    dropped, unsel = classify_select_drops(["dora.md"], ["dora.md"], {"dora.md"}, {"dora.md"})
    assert dropped == [] and unsel == []
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -k classify -v` → FAIL (ImportError).

- [ ] **Step 3: Implement** — append to `plugins/sdlc-knowledge-base/scripts/eval/trace.py`:
```python
def classify_select_drops(model_selected, final_page_ids, known, eligible):
    """Classify each model-selected id absent from the final routed set, and list eligible
    pages the model did not pick. Returns (dropped, eligible_unselected):
      dropped: [{"id", "reason"}] reason ∈ {"unknown_id" (not a known page),
               "filtered_out" (known but not eligible — layer/confidence)};
      eligible_unselected: sorted eligible ids the model never selected (recall signal).
    'not_selected' cannot occur: select preserves eligible ids."""
    final = set(final_page_ids)
    dropped = []
    for pid in model_selected:
        if pid in final:
            continue
        reason = "unknown_id" if pid not in known else "filtered_out"
        dropped.append({"id": pid, "reason": reason})
    eligible_unselected = sorted(set(eligible) - set(model_selected))
    return dropped, eligible_unselected
```

- [ ] **Step 4: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -v` → PASS (6). Lint → clean.

- [ ] **Step 5: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/eval/trace.py tests/test_kb_offline_eval_trace.py
git commit -m "$(printf 'feat(kb-offline): trace.classify_select_drops — unknown_id/filtered_out + unselected (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 6: Wire trace assembly into `run_questions`

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/eval/runner.py`; Test `tests/test_kb_offline_eval_trace.py`.

**Context (spec Unit B):** `run_questions` gains `trace: list | None = None`. When set and `backend` is a `RecordingBackend`, snapshot the record count before each `graph.invoke`, and after, assemble a `type:"question"` row from the slice + `out` + recomputed `ground_claim`/`known_page_ids`/`filter_pages`. The function's return value is unchanged.

- [ ] **Step 1: Write the failing test** — append to `tests/test_kb_offline_eval_trace.py` (integration via the real graph + FakeBackend, no Ollama):
```python
import json as _json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.eval.runner import RecordingBackend, run_questions
from sdlc_knowledge_base_scripts.eval.suite import load_questions

SMOKE = Path("plugins/sdlc-knowledge-base/eval/suite/smoke")


def _smoke_gen():
    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _json.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else _json.dumps({"page_ids": []})
        return _json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                        "cited_pages": [{"library": "local", "page": "dora.md"}],
                                        "evidence_spans": [{"page": "dora.md",
                                                            "text": "deploy multiple times per day"}]}],
                            "rendered_text": "Elite teams deploy multiple times per day."})
    return gen


def test_run_questions_emits_trace_rows(tmp_path):
    qs = load_questions(SMOKE / "questions.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = _smoke_gen()
    trace: list = []
    rows = run_questions(str(SMOKE / "library"), qs, backend=rec, trace=trace)
    assert len(rows) == len(qs)                       # return value unchanged in shape
    assert len(trace) == len(qs)                      # one trace row per question
    t = next(r for r in trace if r["id"] == "s1")
    assert t["type"] == "question"
    assert t["page_ids"] == ["dora.md"]
    assert any(c["stage"] == "select" for c in t["model_calls"])
    assert any(c["stage"] == "synthesize" for c in t["model_calls"])
    claim = t["claims"][0]
    assert claim["ground_cap"] == "supported" and claim["final_status"] == "supported"
    assert claim["evidence_spans"][0]["verbatim_in_page"] is True
    assert "elapsed_s" in t


def test_run_questions_no_trace_unchanged():
    qs = load_questions(SMOKE / "questions.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = _smoke_gen()
    rows = run_questions(str(SMOKE / "library"), qs, backend=rec)   # no trace arg
    assert len(rows) == len(qs) and all("error" in r for r in rows)
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -k run_questions -v` → FAIL (`run_questions() got an unexpected keyword argument 'trace'`).

- [ ] **Step 3: Implement** in `plugins/sdlc-knowledge-base/scripts/eval/runner.py`. Add imports at top: `from ..contracts import Answer, EntailmentStatus`, `from ..entailment import ground_claim`, `from ..provenance import filter_pages, known_page_ids`, `from . import trace as trace_mod`, `import json`. Add a row-builder helper and thread `trace` through `run_questions`:
```python
def _norm(s: str) -> str:  # already exists in runner.py; reuse it, do not redefine
    return " ".join(s.lower().split())


def _build_question_trace(q, out, slice_records, elapsed_s, lib):
    synth = Answer.model_validate(out["_synth"]) if "_synth" in out else Answer()
    verified = Answer.model_validate(out["_answer"]) if "_answer" in out else Answer()
    pages = {p["page"]: p["content"] for p in out.get("pages", [])}
    model_calls = trace_mod.derive_model_calls(slice_records, errored=False, error_msg="")
    # raw of the accepted select call -> model_selected + parse-ok flag
    sel_raw = next((c["raw"] for c in model_calls if c["stage"] == "select" and c["accepted"]), None)
    select_parse_ok, model_selected = True, []
    if sel_raw is not None:
        try:
            model_selected = list(json.loads(sel_raw).get("page_ids", []))
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
            select_parse_ok = False
    known = known_page_ids(lib)
    eligible = set(filter_pages(lib, sorted(known), layer=q.expected_layer, min_confidence=None))
    dropped, eligible_unselected = trace_mod.classify_select_drops(
        model_selected, out.get("page_ids", []), known, eligible)
    claim_rows = []
    for idx, c in enumerate(synth.claims):
        cap = ground_claim(c, pages)
        final = verified.claims[idx].entailment_status if idx < len(verified.claims) else None
        claim_rows.append({
            "text": c.text, "cited_pages": [r.page for r in c.cited_pages],
            "evidence_spans": [{"page": s.page, "text": s.text,
                                "verbatim_in_page": _norm(s.text) in _norm(pages.get(s.page, ""))}
                               for s in c.evidence_spans],
            "ground_cap": cap.value,
            "final_status": final.value if isinstance(final, EntailmentStatus) else None,
        })
    rendered = out.get("rendered_text", "")
    return {
        "type": "question", "id": q.id, "kind": q.kind, "no_evidence": q.no_evidence,
        "expected_facts": q.expected_facts, "expected_routing": q.expected_routing_targets,
        "model_calls": model_calls,
        "eligible_page_ids": sorted(eligible), "page_ids": list(out.get("page_ids", [])),
        "dropped": dropped, "eligible_unselected": eligible_unselected,
        "select_parse_ok": select_parse_ok,
        "pages_read": list(pages.keys()),
        "claims": claim_rows, "rendered_text": rendered,
        "did_abstain": rendered.strip() == "",
        "found_facts": [f for f in q.expected_facts if _norm(f) in _norm(rendered)],
        "elapsed_s": round(elapsed_s, 1),
    }
```
Now modify `run_questions` (signature + loop). New signature:
```python
def run_questions(library_path: str, questions, *, backend, progress: bool = False,
                  run_label: str = "", trace: list | None = None) -> list[dict]:
```
Inside the loop, wrap each invoke with a snapshot + timer (showing the full loop body for the success and error paths):
```python
    from pathlib import Path
    lib = Path(library_path)
    rec_backend = backend if isinstance(backend, RecordingBackend) else None
    tag = _progress_tag(run_label)
    rows = []
    total = len(questions)
    for idx, q in enumerate(questions, 1):
        t0 = time.monotonic()
        snap = len(rec_backend.records) if rec_backend is not None else 0
        graph = build_query_graph(backend)
        try:
            out = graph.invoke(
                {"library_path": library_path, "question": q.question,
                 "layer": q.expected_layer, "min_confidence": None},
                config={"configurable": {"thread_id": q.id}})
        except Exception as exc:  # noqa: BLE001
            print(f"[eval] question {q.id} errored: {exc!r}", file=sys.stderr)
            rows.append({
                "id": q.id, "expected_facts": q.expected_facts, "found_facts": [],
                "expected_routing": q.expected_routing_targets, "predicted_routing": [],
                "should_abstain": q.no_evidence, "did_abstain": False,
                "error": True, "error_msg": str(exc)[:200],
            })
            if trace is not None:
                sl = rec_backend.records[snap:] if rec_backend is not None else []
                try:
                    mc = trace_mod.derive_model_calls(sl, errored=True, error_msg=str(exc))
                except Exception as terr:  # noqa: BLE001
                    trace.append({"type": "question", "id": q.id, "trace_error": str(terr)[:200]})
                else:
                    trace.append({"type": "question", "id": q.id, "error": True,
                                  "error_msg": str(exc)[:200], "elapsed_s": round(time.monotonic() - t0, 1),
                                  "model_calls": mc})
            if progress:
                print(f"{tag} q {idx}/{total} {q.id} ERROR {time.monotonic() - t0:.1f}s", file=sys.stderr)
            continue
        rendered = out.get("rendered_text", "")
        norm_rendered = _norm(rendered)
        found = [f for f in q.expected_facts if _norm(f) in norm_rendered]
        did_abstain = rendered.strip() == ""
        rows.append({
            "id": q.id, "expected_facts": q.expected_facts, "found_facts": found,
            "expected_routing": q.expected_routing_targets,
            "predicted_routing": list(out.get("page_ids", [])),
            "should_abstain": q.no_evidence, "did_abstain": did_abstain, "error": False,
        })
        if trace is not None:
            sl = rec_backend.records[snap:] if rec_backend is not None else []
            try:
                trace.append(_build_question_trace(q, out, sl, time.monotonic() - t0, lib))
            except Exception as terr:  # noqa: BLE001
                trace.append({"type": "question", "id": q.id, "trace_error": str(terr)[:200]})
        if progress:
            status = "abstain" if did_abstain else f"ok facts {len(found)}/{len(q.expected_facts)}"
            print(f"{tag} q {idx}/{total} {q.id} {status} {time.monotonic() - t0:.1f}s", file=sys.stderr)
    return rows
```
(This preserves the existing rows/error/progress behaviour exactly; the trace block is purely additive. Keep the module's existing `_norm`, `_progress_tag`, `build_query_graph` import, and `sys`/`time` imports — add `time` if Task 3 hasn't.)

- [ ] **Step 4: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -v` → PASS. Full non-live suite → all pass. Lint `eval/runner.py tests/test_kb_offline_eval_trace.py` → clean.

- [ ] **Step 5: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/eval/runner.py tests/test_kb_offline_eval_trace.py
git commit -m "$(printf 'feat(kb-offline): assemble per-question trace rows in run_questions (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 7: Verifier trace (per-label slice) + `score_run` threading

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/eval/runner.py`; Test `tests/test_kb_offline_eval_trace.py`.

**Context (spec Unit B/C, R3-P3):** `run_verifier_labels` gains `trace` with a per-label snapshot; `score_run` threads `trace` to both runners.

- [ ] **Step 1: Write the failing test** — append to `tests/test_kb_offline_eval_trace.py`:
```python
from sdlc_knowledge_base_scripts.eval.runner import run_verifier_labels, score_run
from sdlc_knowledge_base_scripts.eval.suite import load_verifier_labels


def test_run_verifier_labels_emits_isolated_trace_rows():
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    rec = RecordingBackend(FakeBackend())
    rec._inner.generate = lambda prompt, schema=None: '{"status": "supported"}'
    trace: list = []
    run_verifier_labels(str(SMOKE / "library"), labels, backend=rec, trace=trace)
    assert len(trace) == len(labels)
    for row in trace:
        assert row["type"] == "verifier"
        assert all(c["stage"] == "judge" for c in row["model_calls"])   # only this label's call(s)
        assert "predicted_status" in row and "gold_status" in row


def test_score_run_threads_trace_to_both():
    qs = load_questions(SMOKE / "questions.jsonl")
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    rec_inner = _smoke_gen()
    be = FakeBackend(); be.generate = rec_inner
    trace: list = []
    score_run(str(SMOKE / "library"), qs, labels, backend=be, trace=trace)
    assert any(r["type"] == "question" for r in trace)
    assert any(r["type"] == "verifier" for r in trace)
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -k "verifier or threads" -v` → FAIL (unexpected `trace` kwarg).

- [ ] **Step 3: Implement** in `plugins/sdlc-knowledge-base/scripts/eval/runner.py`. `run_verifier_labels` signature + per-label snapshot:
```python
def run_verifier_labels(library_path: str, labels, *, backend, trace: list | None = None) -> list[dict]:
    lib = Path(library_path)
    pages = {p.name: p.read_text(encoding="utf-8") for p in lib.glob("*.md")}
    rec_backend = backend if isinstance(backend, RecordingBackend) else None
    rows = []
    for lb in labels:
        snap = len(rec_backend.records) if rec_backend is not None else 0
        claim = Claim(text=lb.claim_text, cited_pages=lb.cited_pages, evidence_spans=lb.evidence_spans)
        cap = ground_claim(claim, pages)
        if cap == EntailmentStatus.unsupported:
            predicted = EntailmentStatus.unsupported
        else:
            predicted = _min_status(cap, judge_claim(claim, pages, backend=backend))
        rows.append({"id": lb.id, "predicted_status": predicted.value, "gold_status": lb.gold_status})
        if trace is not None:
            sl = rec_backend.records[snap:] if rec_backend is not None else []
            mc = trace_mod.derive_model_calls(sl, errored=False, error_msg="")
            judge_raw = next((c["raw"] for c in mc if c["stage"] == "judge" and c["accepted"]), None)
            trace.append({"type": "verifier", "id": lb.id, "claim_text": lb.claim_text,
                          "ground_cap": cap.value, "judge_raw": judge_raw,
                          "predicted_status": predicted.value, "gold_status": lb.gold_status,
                          "model_calls": mc})
    return rows
```
(Imports needed — `Claim`, `EntailmentStatus`, `_min_status`, `ground_claim`, `judge_claim` — already used by this function today; keep them.)

Thread through `score_run`:
```python
def score_run(library_path: str, questions, labels, *, backend, progress: bool = False,
              run_label: str = "", trace: list | None = None) -> dict:
    rec = RecordingBackend(backend)
    q_rows = run_questions(library_path, questions, backend=rec, progress=progress,
                           run_label=run_label, trace=trace)
    if progress:
        print(f"{_progress_tag(run_label)} verifier: scoring {len(labels)} labels", file=sys.stderr)
    v_rows = run_verifier_labels(library_path, labels, backend=rec, trace=trace)
    # ... rest of score_run unchanged ...
```

- [ ] **Step 4: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_eval_trace.py -v` → PASS. Full non-live suite → all pass. Lint → clean.

- [ ] **Step 5: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/eval/runner.py tests/test_kb_offline_eval_trace.py
git commit -m "$(printf 'feat(kb-offline): per-label verifier trace + score_run trace threading (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Task 8: CLI wiring — write trace by default, `--no-trace`, safe filenames

**Files:** Modify `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`; Test `tests/test_kb_offline_cli.py`.

**Context (spec Unit C):** `_cmd_eval` release path writes `trace-<safe_model>-<stamp>-run<k>.jsonl` per run unless `--no-trace`; the report stem also adopts `safe_model_name`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_kb_offline_cli.py` (reuse the file's `cli`/`json`/`FakeBackend` imports; the eval release path accepts `backend_override`):
```python
def _eval_smoke_gen():
    import json as _j

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else _j.dumps({"page_ids": []})
        return _j.dumps({"claims": [], "rendered_text": ""})
    return gen


def test_eval_release_writes_trace_by_default(tmp_path):
    be = FakeBackend(); be.generate = _eval_smoke_gen()
    rc = cli.main(["eval", "release", "--suite", "plugins/sdlc-knowledge-base/eval/suite/smoke",
                   "--runs", "1", "--stamp", "T1", "--report-dir", str(tmp_path), "--model", "gemma4:12b"],
                  backend_override=be)
    assert rc in (0, 1)                                  # gate verdict may pass or fail; trace must exist
    traces = list(tmp_path.glob("trace-gemma4_12b-T1-run1.jsonl"))
    assert len(traces) == 1
    lines = [json.loads(x) for x in traces[0].read_text().splitlines() if x.strip()]
    assert any(r["type"] == "question" for r in lines)
    assert any(r["type"] == "verifier" for r in lines)


def test_eval_release_no_trace_suppresses(tmp_path):
    be = FakeBackend(); be.generate = _eval_smoke_gen()
    cli.main(["eval", "release", "--suite", "plugins/sdlc-knowledge-base/eval/suite/smoke",
              "--runs", "1", "--stamp", "T2", "--report-dir", str(tmp_path), "--model", "gemma4:12b",
              "--no-trace"], backend_override=be)
    assert list(tmp_path.glob("trace-*.jsonl")) == []
    assert list(tmp_path.glob("release-gemma4_12b-T2.md"))   # report still written
```
(NOTE: the smoke suite path under `eval release` uses the full suite by default; the test points `--suite` at the small `smoke` fixture so it runs fast on `FakeBackend`. Confirm `_cmd_eval` reads `args.suite` and that `release` uses `suite_root` (not `suite_root/smoke`) — pass the smoke dir directly as the suite root.)

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k "eval_release" -v` → FAIL (`--no-trace` unknown / no trace file).

- [ ] **Step 3: Implement** in `plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py`. Add the arg to the release subparser (next to `--runs`/`--stamp`):
```python
    p_rel.add_argument("--no-trace", action="store_true",
                       help="skip writing the per-question diagnostic trace JSONL")
```
In `_cmd_eval`, import the sanitizer and write traces. Replace the run loop + stem construction:
```python
    from .eval.report import safe_model_name
    import json as _json
    runs = []
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    safe = safe_model_name(args.model)
    for i in range(args.runs):
        print(f"[eval] starting run {i + 1}/{args.runs} — {len(questions)} questions, "
              f"{len(labels)} verifier labels (model={args.model})", file=sys.stderr)
        trace = None if args.no_trace else []
        runs.append(score_run(str(library), questions, labels, backend=backend,
                              progress=True, run_label=f"run {i + 1}/{args.runs}", trace=trace))
        if trace is not None:
            tp = report_dir / f"trace-{safe}-{args.stamp}-run{i + 1}.jsonl"
            try:
                tp.write_text("".join(_json.dumps(r) + "\n" for r in trace), encoding="utf-8")
            except OSError as exc:
                print(f"[eval] warning: failed to write trace {tp}: {exc}", file=sys.stderr)
```
And change the report stem to use `safe`:
```python
    stem = report_dir / f"release-{safe}-{args.stamp}"
```
(Remove the now-duplicated inline `report_dir = Path(...)` / `mkdir` later in the function, and the old `args.model.replace(':', '_')`.)

- [ ] **Step 4: Run tests + lint** — `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k eval_release -v` → PASS. Full non-live suite → all pass. Lint `kb_offline_cli.py tests/test_kb_offline_cli.py` → clean.

- [ ] **Step 5: Commit**
```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "$(printf 'feat(kb-offline): write eval trace JSONL by default; --no-trace; safe filenames (#211)\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>')"
```

---

## Final verification (after all tasks)

- [ ] **Full non-live suite green** — `.venv/bin/python -m pytest tests/ -k "kb_offline and not live" -q` → all pass; no regressions in eval/runner/harness/CLI.
- [ ] **Lint the whole changed surface** — `.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/eval/report.py plugins/sdlc-knowledge-base/scripts/eval/trace.py plugins/sdlc-knowledge-base/scripts/eval/runner.py plugins/sdlc-knowledge-base/scripts/eval/harness.py plugins/sdlc-knowledge-base/scripts/provenance.py plugins/sdlc-knowledge-base/scripts/graphs/query_graph.py plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_eval_trace.py tests/test_kb_offline_eval_naming.py tests/test_kb_offline_provenance.py tests/test_kb_offline_eval_runner.py tests/test_kb_offline_cli.py` → clean.
- [ ] **Smoke a real release trace (optional, no Ollama):** run the CLI eval against the smoke suite with a FakeBackend-style harness or, if Ollama is free, a tiny live run, and eyeball one `trace-*.jsonl` row for the empty-`cited_pages`-pre-normalization visibility (synthesize `raw` shows `cited_pages:[]`, `claims[].cited_pages` back-filled).

---

## Self-review notes

**Spec coverage:** Unit A (stateless RecordingBackend: stage/json_parse_ok/elapsed_ms/raw) → Task 3. Unit A→B derivation (invocation/attempt/accepted incl. error rules R3/R4) → Task 4. Drop classification + eligible_unselected (R2-P2a) → Task 5. Known-page drift guard (R2-P2b) → Task 2. Per-question assembly incl. error path (R1-P2b), ground_cap vs final, verbatim flag, raw synthesize via model_calls (R1-P1a) → Task 6. Per-label verifier isolation (R3-P3) + score_run threading → Task 7. CLI default-on + `--no-trace` + safe filenames (R1-P3) → Task 8. first_pass_json rename guard (R2-P3) → Task 3. Data shape (every field) → Tasks 6/7. No-trace invariance → Tasks 6/8.

**Placeholder scan:** none — every code step is complete. The Task 8 note about `--suite` pointing at `smoke` is a test-setup instruction, verified against `_cmd_eval`'s `args.suite` usage, not a placeholder.

**Type/name consistency:** `derive_model_calls(records, *, errored, error_msg) -> list[dict]`; `classify_select_drops(model_selected, final_page_ids, known, eligible) -> (list, list)`; `known_page_ids(lib) -> set[str]`; `safe_model_name(model) -> str`; record keys `{stage, first_pass, json_parse_ok, elapsed_ms, raw}` then derived `{stage_invocation, repair_attempt, accepted}`; `run_questions(..., trace=None)`, `run_verifier_labels(..., trace=None)`, `score_run(..., trace=None)` — used identically across tasks. `harness.first_pass_json_validity` reads `json_parse_ok` (Task 3) consistent with the RecordingBackend rename.

**Known risk to verify during execution:** the exact text of `_cmd_eval` (report-dir/mkdir/stem lines) — Task 8 must READ the current function and splice cleanly rather than duplicate the `report_dir`/`mkdir` block. Flagged in Task 8 Step 3.

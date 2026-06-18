# kb-offline eval traces — first-class per-question diagnostics (design)

**Issue:** EPIC #211 (kb-offline), M3/M4 hardening item #1 (highest priority — enabler for #2/#4/#5).
**Date:** 2026-06-18
**Status:** design, pending review. (Rev 3 — incorporates two review rounds: R1 P1–P3, R2 P1–P3.)

## Goal

Make the release eval **self-documenting**: every `kb-offline eval release` run persists a per-question, per-stage trace alongside its report, so a failing run is diagnosable from its artifacts instead of requiring a multi-hour re-run with ad-hoc instrumentation. This folds the throwaway `tmp/cc_baseline/diagnose_gemma.py` capability back into the harness.

Motivation: the `fact_recall = 0.000` root cause (empty `cited_pages` orphaned by the grounding gate) was invisible in the release artifacts — `runner.run_questions` keeps only scorer-ready rows. The trace was built outside the harness after the fact. See `research/kb-offline-eval/2026-06-18-gemma-ratification-findings.md` §7.1.

## Scope

**In scope:** a read-only trace-capture layer over the existing query path; a trace artifact written by default on `eval release`; a `--no-trace` opt-out; one behaviour-preserving refactor (extract the known-page computation into a shared helper to prevent trace/graph drift); unit tests on `FakeBackend`.

**Out of scope (later roadmap items, see [[project-kb-offline-select-hardening]]):** changing the `select`/`verify` *contracts or routing behaviour* (#2 `normalize_select_result`, #4 abstention contract); embedding-default routing (#3); judge-mode/latency changes (#5). This item only *instruments*.

**"Non-invasive" defined:** no change to any pipeline contract or routing behaviour. The trace layer lives in the eval harness (`RecordingBackend`, `runner.py`) and recomputes deterministic intermediates (`ground_claim`, `filter_pages`, the shared known-page helper) itself. The one graph-side edit is a pure extraction (§Unit B) that leaves `n_select` behaviour byte-identical.

## Current state (what exists)

- `eval/runner.py`:
  - `RecordingBackend` wraps a backend's `generate`, recording `{first_pass, valid_json}` per call (feeds `first_pass_json_validity`). No raw output, call-type, or timing. `valid_json` = `json.loads` succeeded — **not** Pydantic-schema validity.
  - `run_questions(...)` invokes the query graph per question, returns scorer-ready rows only, and already catches a per-question `graph.invoke` exception (records a zeroed error row).
  - `run_verifier_labels(...)` → `{id, predicted_status, gold_status}` per label.
  - `score_run(...)` builds the `RecordingBackend`, runs both, aggregates metrics; `first_pass_json_validity(rec.records)` reads `first_pass` + `valid_json`.
- `graphs/query_graph.py`:
  - `n_select` computes `known = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md","log.md","_index.md"}}` (**root glob, not rglob**), then `candidates = filter_pages(lib, sorted(known), layer=state["layer"], min_confidence=state["min_confidence"])`, then `select(question, shelf, known_pages=set(candidates))`. So `select`'s `known_pages` arg is the **eligible/candidate set**, and `select` returns `[p for p in model_ids if p in candidates]` — eligible ids are preserved; only ids outside the candidate set are dropped.
  - `graph.invoke(...)` returns `page_ids`, `pages`, `_synth` (synthesized `Answer` dict, **post-normalization** — the cited_pages back-fill runs inside `synthesize`), `_answer` (verified `Answer` dict), `rendered_text`.
- `pipeline.select`/`synthesize` repair loop: a first attempt; on parse-or-schema rejection, a repair attempt whose prompt carries `"Previous output invalid: <err>"`; returns on the first accepted parse, else raises after the budget. `judge_claim` makes **one** call per claim, **no** repair loop, and defaults to `unsupported` on any non-conforming output.
- `kb_offline_cli.py` `_cmd_eval` writes `release-<model>-<stamp>.{md,json}`, sanitizing the model inline as `args.model.replace(':', '_')`.
- `entailment.ground_claim`, `provenance.filter_pages` are deterministic/pure — safe to recompute.

## Architecture — non-invasive capture

### Unit A — `RecordingBackend` records stage, invocation, attempt, raw, timing
Each record becomes:
```
{stage, stage_invocation, repair_attempt, first_pass, json_parse_ok, accepted, elapsed_ms, raw}
```
- `stage` ∈ `select | synthesize | judge | other`, from the prompt (substring-match `prompts.SELECT_FRAGMENT` / `SYNTHESIZE_FRAGMENT`; judge prompt begins `"Judge whether"`).
- `first_pass` = the prompt does **not** contain the repair marker `"Previous output invalid:"`.
- **`stage_invocation` vs `repair_attempt` (R2-P1).** Distinguishing "another judge call" from "a repair":
  - A `first_pass` call **starts a new stage_invocation** of that stage (invocation counter per `(question, stage)` increments; `repair_attempt` resets to 1).
  - A non-`first_pass` (repair) call belongs to the **same** invocation; `repair_attempt` increments.
  - Result: select = invocation 1 with repair_attempts 1..N; synthesize = invocation 1 with repair_attempts 1..N; **judge = invocations 1,2,3… (one per judged claim), each repair_attempt 1** — no judge is ever mislabelled a repair.
- `json_parse_ok` (R2-P3, renamed from `valid_json` for honesty) = `json.loads` succeeded. It is **not** schema acceptance.
- **`accepted` is positional, not parse-based (R2-P3).** = the call whose output the pipeline actually used for its `stage_invocation`: the **last `repair_attempt` of a successful invocation** (the repair loop returns on the first accepted parse, so the last call of a non-erroring invocation is the accepted one — correct regardless of json-vs-schema). For `judge`, the single call is `accepted: true` (its result is always used, defaulting to `unsupported` if `json_parse_ok` is false). If an invocation exhausted its repair budget (→ the operation raised), **no** call is `accepted`.
- `elapsed_ms` = wall time of the one `generate` call (`time.monotonic` around `self._inner.generate`).
- Existing first-pass/json semantics preserved; `harness.first_pass_json_validity` is updated to read `json_parse_ok` (mechanical rename; computed value identical) and its test asserts the value is unchanged.

This list is the trace's **raw-I/O source of truth** — every attempt of every stage (raw select repairs P-R1b, raw synthesize pre-normalization P-R1a, every judge call), each timed (P-R1/P2c).

### Unit B — per-question trace assembly in `run_questions`
`run_questions` gains `trace: list | None = None` (default `None` = current behaviour exactly).

- **Per-question call slice.** Snapshot `len(backend.records)` before each `graph.invoke`; after, `backend.records[before:after]` is that question's `model_calls`. The invocation counters in Unit A reset at the per-question boundary (a fresh `first_pass` select always opens invocation 1).
- **Known-page helper (R2-P2 — drift guard).** Extract `n_select`'s known-page computation into a shared `known_page_ids(lib) -> set[str]` (root `glob("*.md")` minus `{_shelf-index.md, log.md, _index.md}`) and have **both** `n_select` and the trace call it. This is a pure refactor — `n_select` behaviour is byte-identical. (Fallback if a zero-graph-touch is preferred: inline the identical logic in the trace with a "must match n_select" comment. Recommend the shared helper.)
- **Drop classification (R1-P2a, corrected by R2-P2a).** Recompute `eligible_page_ids = filter_pages(lib, sorted(known_page_ids(lib)), layer=q.expected_layer, min_confidence=None)` — the same call `n_select` makes on the default path. Parse the `accepted` select attempt's raw ids (`model_selected`). Then:
  - `dropped` = `model_selected − page_ids`, each classified: `unknown_id` (not in `known_page_ids`) or `filtered_out` (in known but not in `eligible`). **`not_selected` is removed** — `select` preserves eligible ids, so it cannot occur.
  - `eligible_unselected` = `eligible − model_selected` (a *separate* field: eligible pages the model didn't pick — the select-recall signal, distinct from drops).
  - Accelerated path (`--accelerate`, not the current ratification path): `eligible_page_ids` is the embedding shortlist if recoverable, else recorded as `null` with `candidate_source: "accelerated-unrecorded"` — an explicit limitation, not a silent gap.
- **Claims.** Per `_synth` claim: recompute `ground_cap` (`ground_claim` vs read pages), pair `final_status` from `_answer`, and map `judge_raw` from the `judge` `model_calls` in `stage_invocation` order over the claims whose cap ≠ `unsupported` (cap = `unsupported` → judge not called → `judge_raw: null`), mirroring `verify_entailment`.
- **Error path (R1-P2b).** In the existing `graph.invoke` except branch, when tracing, append a `type:"question"` row with `error: true`, `error_msg`, `elapsed_s`, and the `model_calls` slice captured since the snapshot (raw call history is most valuable here). A failure while *assembling* a non-error row is caught and written as `{type:"question", id, trace_error}`.
- Return value unchanged; the trace is a side-channel.

`run_verifier_labels` gains the same side-channel: per label `{type:"verifier", id, claim_text, ground_cap, judge_raw, predicted_status, gold_status, model_calls}` (its single judge call is one `stage_invocation`).

### Unit C — `score_run` + `_cmd_eval` wiring + filename safety
- `score_run(..., trace=None)` threads the list into both runners.
- `_cmd_eval` release path: unless `--no-trace`, create `trace=[]` per run, pass to `score_run`, write `research/kb-offline-eval/trace-<safe_model>-<stamp>-run<k>.jsonl`. Smoke path / unit tests pass no trace → zero change.
- New arg `--no-trace` (`store_true`).
- **Filename safety (R1-P3).** Shared `safe_model_name(model) -> str` (replace `:`, `/`, whitespace with `_`); used for the trace filename and refactored into the report stem (guards both against `/` in namespaced model names).

## Data shape

One JSONL per run, `research/kb-offline-eval/trace-<safe_model>-<stamp>-run<k>.jsonl`. `model_calls` is the raw-I/O source of truth; other fields are the interpreted view.

**`type: "question"`**
```json
{
  "type": "question", "id": "q001", "kind": "fact", "no_evidence": false,
  "expected_facts": ["..."], "expected_routing": ["dora.md"],
  "model_calls": [
    {"stage": "select", "stage_invocation": 1, "repair_attempt": 1, "first_pass": true,
     "json_parse_ok": false, "accepted": false, "elapsed_ms": 1840, "raw": "page: dora.md"},
    {"stage": "select", "stage_invocation": 1, "repair_attempt": 2, "first_pass": false,
     "json_parse_ok": true, "accepted": true, "elapsed_ms": 1520, "raw": "{\"page_ids\":[\"dora.md\"]}"},
    {"stage": "synthesize", "stage_invocation": 1, "repair_attempt": 1, "first_pass": true,
     "json_parse_ok": true, "accepted": true, "elapsed_ms": 41200,
     "raw": "{\"claims\":[{\"text\":\"...\",\"cited_pages\":[],\"evidence_spans\":[{\"page\":\"dora.md\",\"text\":\"...\"}]}],\"rendered_text\":\"...\"}"},
    {"stage": "judge", "stage_invocation": 1, "repair_attempt": 1, "first_pass": true,
     "json_parse_ok": true, "accepted": true, "elapsed_ms": 9300, "raw": "{\"status\":\"supported\"}"}
  ],
  "eligible_page_ids": ["dora.md", "ci-cd.md", "..."],
  "page_ids": ["dora.md"],
  "dropped": [{"id": "telemetry", "reason": "unknown_id"}],
  "eligible_unselected": ["observability.md"],
  "pages_read": ["dora.md"],
  "claims": [
    {"text": "...", "cited_pages": ["dora.md"],
     "evidence_spans": [{"page": "dora.md", "text": "...", "verbatim_in_page": true}],
     "ground_cap": "supported", "judge_raw": "{\"status\": \"supported\"}", "final_status": "supported"}
  ],
  "rendered_text": "...", "did_abstain": false, "found_facts": ["..."], "elapsed_s": 67.2
}
```
The synthesize `raw` carries `cited_pages:[]` (pre-normalization) while `claims[].cited_pages` shows the back-filled `["dora.md"]` — the juxtaposition that makes the normalization visible (R1-P1a). A multi-claim question shows multiple `judge` calls as `stage_invocation` 1,2,3… all `accepted`, none mislabelled a repair (R2-P1).

**`type: "verifier"`**
```json
{"type": "verifier", "id": "v001", "claim_text": "...",
 "ground_cap": "supported", "judge_raw": "{\"status\": \"supported\"}",
 "predicted_status": "supported", "gold_status": "supported",
 "model_calls": [{"stage": "judge", "stage_invocation": 1, "repair_attempt": 1, "first_pass": true,
                  "json_parse_ok": true, "accepted": true, "elapsed_ms": 8800, "raw": "..."}]}
```

**`type: "question"` (graph-invoke error)**
```json
{"type": "question", "id": "q042", "error": true,
 "error_msg": "synthesize failed after 1 repair(s): ...", "elapsed_s": 3.1,
 "model_calls": [{"stage": "select", "stage_invocation": 1, "repair_attempt": 1, "...": "..."}]}
```

Notes:
- `pages_read`/`cited_pages` carry page **ids only**; raw model outputs in `model_calls` are **not** truncated (they are the diagnostic payload).
- `evidence_spans[].verbatim_in_page` — normalized-substring check (quoted vs paraphrased).
- `ground_cap` vs `final_status` — judge-override signal (#5).
- `dropped[].reason` — classified (#2): `unknown_id` is the format-mismatch instability `normalize_select_result` will fix; `eligible_unselected` is the complementary recall signal.
- per-call `elapsed_ms` — attributes the ~300s+ tail to a stage / repair (#5).
- `json_parse_ok` is json-parse only, not schema acceptance — `accepted` (positional) is the reliable "the pipeline used this" signal.

## Error handling
- A graph-invoke failure → `error:true` row **with** captured `model_calls`; a row-assembly failure → `{type:"question", id, trace_error}`.
- A failed trace **file write** → stderr warning, verdict unchanged — the gate result must never depend on the diagnostic artifact.
- Non-`RecordingBackend` backend (defensive) → tracing degrades to `out`-derived + recomputed fields only (no `model_calls`), no error.

## Testing (TDD, `FakeBackend` — no Ollama)
1. `RecordingBackend`: tags `stage`; sets `first_pass` from the repair marker; assigns `stage_invocation`/`repair_attempt` correctly — **a select first-pass+repair = invocation 1 / attempts 1,2; two judge calls = invocations 1,2 each attempt 1** (R2-P1 regression); `json_parse_ok` + `elapsed_ms` present; `accepted` = last attempt of a successful invocation, every judge `accepted`.
2. `harness.first_pass_json_validity` reads `json_parse_ok` and returns the same value as before the rename (guard).
3. Raw synthesize surfaced: an empty-`cited_pages` synthesized claim shows `cited_pages:[]` in the synthesize `raw` and the back-filled page in `claims[].cited_pages` (R1-P1a visibility guard).
4. Drop classification: a select returning a known-eligible id + an unknown id + a layer-filtered id → `dropped` reasons `unknown_id` / `filtered_out`; **no `not_selected`** ever produced (R2-P2a); `eligible_unselected` lists an eligible page the model omitted.
5. Known-page helper: `known_page_ids(lib)` matches `n_select`'s set exactly (root glob, index files excluded; a nested `sub/x.md` is **not** known) — and `n_select` still routes identically after the extraction (R2-P2b).
6. `ground_cap` vs `final_status` correct for a supported claim and an empty-`cited_pages`-then-backfilled claim.
7. Verifier rows: one `type:"verifier"` per label with `ground_cap`/`judge_raw`/`predicted`/`gold`/`model_calls`.
8. Error path: a backend that makes `synthesize` raise → a `type:"question"` `error:true` row carrying the `select` `model_calls` captured before the failure (R1-P2b).
9. No-trace invariance: `run_questions`/`score_run` with no `trace` return byte-identical results.
10. CLI: release writes `trace-*.jsonl` by default; `--no-trace` suppresses it; trace presence/absence changes neither report nor exit code.
11. `safe_model_name`: `gemma4:12b` → `gemma4_12b`, `ns/custom:tag` → `ns_custom_tag`; report stem and trace filename both use it (R1-P3).

## Self-review notes
- **Placeholders:** none.
- **Consistency:** strictly additive to behaviour except the one byte-identical `known_page_ids` extraction and the suppressible file write; return values, metrics, and the (renamed-but-equal) first-pass-json metric unchanged.
- **Scope:** single implementation plan; bounded to `runner.py`, a shared `known_page_ids` + `safe_model_name` helper, a one-line `n_select` refactor, a CLI arg, and tests.
- **Ambiguity resolved:** `accepted` is positional (the call the pipeline returned on), independent of `json_parse_ok`; multi-judge questions use `stage_invocation` (not `repair_attempt`); `dropped` is classified against the recomputed eligible set with `not_selected` removed as impossible and `eligible_unselected` added as the distinct recall signal; the known set is a shared helper to prevent trace/graph drift; accelerated candidates are an explicit recorded limitation.

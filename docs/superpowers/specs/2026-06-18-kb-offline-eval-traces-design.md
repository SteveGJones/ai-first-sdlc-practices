# kb-offline eval traces — first-class per-question diagnostics (design)

**Issue:** EPIC #211 (kb-offline), M3/M4 hardening item #1 (highest priority — enabler for #2/#4/#5).
**Date:** 2026-06-18
**Status:** design, pending review. (Rev 2 — incorporates spec-review P1–P3.)

## Goal

Make the release eval **self-documenting**: every `kb-offline eval release` run persists a per-question, per-stage trace alongside its report, so a failing run is diagnosable from its artifacts instead of requiring a multi-hour re-run with ad-hoc instrumentation. This folds the throwaway `tmp/cc_baseline/diagnose_gemma.py` capability back into the harness.

Motivation: the `fact_recall = 0.000` root cause (empty `cited_pages` orphaned by the grounding gate) was invisible in the release artifacts — `runner.run_questions` keeps only scorer-ready rows. The trace was built outside the harness after the fact. See `research/kb-offline-eval/2026-06-18-gemma-ratification-findings.md` §7.1.

## Scope

**In scope:** a read-only trace-capture layer over the existing query path; a trace artifact written by default on `eval release`; a `--no-trace` opt-out; unit tests on `FakeBackend`.

**Out of scope (later roadmap items, see [[project-kb-offline-select-hardening]]):** changing the `select`/`verify` contracts (#2 `normalize_select_result`, #4 abstention contract); embedding-default routing (#3); judge-mode/latency changes (#5). This item only *instruments* — it changes no pipeline behaviour. The trace's classified `dropped` ids, raw synthesize attempts, `ground_cap`-vs-`final_status`, and per-call timings are precisely the signals #2/#4/#5 will consume.

**"Non-invasive" defined:** no change to any pipeline contract or routing behaviour. The trace layer lives in the eval harness (`RecordingBackend`, `runner.py`) and recomputes deterministic intermediates (`ground_claim`, `filter_pages`) itself; it does not edit `select`, `synthesize`, `verify`, or the query graph.

## Current state (what exists)

- `eval/runner.py`:
  - `RecordingBackend` wraps a backend's `generate`, recording `{first_pass, valid_json}` per call (feeds `first_pass_json_validity`). It does **not** keep the raw output, a call-type tag, or timing.
  - `run_questions(library_path, questions, *, backend, progress=False, run_label="")` invokes the query graph per question and returns **scorer-ready rows only**; it already catches a per-question `graph.invoke` exception and records a zeroed error row.
  - `run_verifier_labels(...)` returns `{id, predicted_status, gold_status}` per label.
  - `score_run(...)` builds the `RecordingBackend`, runs both, aggregates metrics.
- `graphs/query_graph.py`: `graph.invoke(...)` returns the full channel state — `page_ids` (select), `pages` (read), `_synth` (synthesized `Answer` dict, **post-normalization** since the cited_pages back-fill runs inside `synthesize`), `_answer` (verified `Answer` dict), `rendered_text`. `n_select` computes its candidate set via `provenance.filter_pages(lib, known, layer=, min_confidence=)` (or the accelerated embedding shortlist).
- `kb_offline_cli.py` `_cmd_eval` release path writes `release-<model>-<stamp>.{md,json}`, sanitizing the model name inline as `args.model.replace(':', '_')`.
- `entailment.ground_claim` and `provenance.filter_pages` are deterministic and pure — safe to recompute in the trace layer.

## Architecture — non-invasive capture

Three small, isolated changes; **no pipeline behaviour changes** whether tracing is on or off (the only effect of tracing is an extra file write).

### Unit A — `RecordingBackend` records call-type, raw, attempt, timing
Extend each record to `{first_pass, valid_json, call_type, attempt, raw, elapsed_ms}`:
- `call_type` derived from the prompt by matching the canonical fragments (`prompts.SELECT_FRAGMENT` → `"select"`; `prompts.SYNTHESIZE_FRAGMENT` → `"synthesize"`; judge prompt begins `"Judge whether"` → `"judge"`; else `"other"`). Substring match so a repair-suffixed prompt still classifies.
- `attempt` — running index per `call_type` within the **current question** (reset by the per-question boundary; see Unit B). Attempt 1 = first pass; ≥2 = a repair attempt.
- `raw` — the backend's returned string (the **pre-parse, pre-normalization** model output — this is what surfaces "model emitted X, pipeline normalized to Y").
- `elapsed_ms` — wall time of the single `generate` call (`time.monotonic` around `self._inner.generate`).
- Existing `first_pass`/`valid_json` semantics unchanged → `first_pass_json_validity` is unaffected. Pure bookkeeping; adds no model calls.

This single record list is the trace's **source of truth for model I/O** — it captures *every* attempt of *every* stage (select/synthesize/judge), including raw synthesize attempts (P1a) and repaired select attempts (P1b), each timed (P2c).

### Unit B — per-question trace assembly in `run_questions`
`run_questions` gains `trace: list | None = None` (default `None` = current behaviour exactly).
- When `trace` is a list and `backend` is a `RecordingBackend`: snapshot `len(backend.records)` before each `graph.invoke`; after, the slice `backend.records[before:after]` is that question's `model_calls` (select attempts, synthesize attempts, judge calls, in order). The `accepted` flag per call = the last attempt of that `call_type` with `valid_json: true` (the attempt whose parse the pipeline used).
- Build the row from: question metadata; the `out` channels; the recomputed grounding cap per `_synth` claim (`ground_claim` against read pages); the recomputed candidate set (`filter_pages`, see drop classification); per-question timer; and the `model_calls` slice.
- **Drop classification (P2a).** Record `eligible_page_ids` = `filter_pages(lib, known_pages, layer=q.expected_layer, min_confidence=None)` (the non-accelerated default path; the trace recomputes it — no graph change). Parse the accepted select attempt's raw ids; classify each id **not** in final `page_ids` as:
  - `unknown_id` — not in `known_pages` (the select-instability signal #2 targets),
  - `filtered_out` — in `known_pages` but not in `eligible_page_ids` (layer/confidence),
  - `not_selected` — in `eligible_page_ids` but absent from final (model narrowed it).
  When the run uses `--accelerate` (not the current ratification path), `eligible_page_ids` reflects the embedding shortlist if recoverable, else is recorded as `null` with `candidate_source: "accelerated-unrecorded"` — an explicit known limitation, not a silent gap.
- Per-claim judge mapping: the `judge` records in the slice map to claims in `_synth` order over those whose recomputed cap ≠ `unsupported` (verify skips the judge when the cap is `unsupported`); where the cap is `unsupported`, `judge_raw` is `null`.
- **Error path (P2b).** `run_questions` already catches `graph.invoke` exceptions. In that branch, when tracing, append a `type:"question"` row with `error: true`, `error_msg`, `elapsed_s`, and the `model_calls` slice captured since the snapshot (the raw call history is most valuable exactly here). A failure while *assembling* a (non-error) row is itself caught and written as `{type:"question", id, trace_error}`.
- The function's **return value is unchanged**; the trace is a side-channel.

`run_verifier_labels` gains the same `trace` side-channel: per label, append `{type:"verifier", id, claim_text, ground_cap, judge_raw, predicted_status, gold_status, model_calls}`.

### Unit C — `score_run` + `_cmd_eval` wiring + filename safety
- `score_run(..., trace: list | None = None)` threads the list into both runners.
- `_cmd_eval` release path: unless `--no-trace`, create `trace = []` per run, pass to `score_run`, then write `research/kb-offline-eval/trace-<safe_model>-<stamp>-run<k>.jsonl`. Smoke path and unit tests pass no trace → zero change.
- New arg: `--no-trace` (`action="store_true"`, help: "skip writing the per-question diagnostic trace").
- **Filename safety (P3).** Add a shared `safe_model_name(model: str) -> str` helper (replace `:`, `/`, and whitespace with `_`) used for the trace filename; refactor the existing report-stem `replace(':','_')` to call it too (DRY; also guards report filenames against `/` in custom/namespaced Ollama model names).

## Data shape

One JSONL per run, `research/kb-offline-eval/trace-<safe_model>-<stamp>-run<k>.jsonl`, one object per line, discriminated by `type`. `model_calls` is the raw-I/O source of truth; the other fields are the interpreted view.

**`type: "question"`**
```json
{
  "type": "question", "id": "q001", "kind": "fact", "no_evidence": false,
  "expected_facts": ["..."], "expected_routing": ["dora.md"],
  "model_calls": [
    {"call_type": "select", "attempt": 1, "first_pass": true, "valid_json": false,
     "accepted": false, "elapsed_ms": 1840, "raw": "page: dora.md"},
    {"call_type": "select", "attempt": 2, "first_pass": false, "valid_json": true,
     "accepted": true, "elapsed_ms": 1520, "raw": "{\"page_ids\":[\"dora.md\"]}"},
    {"call_type": "synthesize", "attempt": 1, "first_pass": true, "valid_json": true,
     "accepted": true, "elapsed_ms": 41200, "raw": "{\"claims\":[{\"text\":\"...\",\"cited_pages\":[],\"evidence_spans\":[{\"page\":\"dora.md\",\"text\":\"...\"}]}],\"rendered_text\":\"...\"}"},
    {"call_type": "judge", "attempt": 1, "first_pass": true, "valid_json": true,
     "accepted": true, "elapsed_ms": 9300, "raw": "{\"status\":\"supported\"}"}
  ],
  "eligible_page_ids": ["dora.md", "ci-cd.md", "..."],
  "page_ids": ["dora.md"],
  "dropped": [{"id": "observability.md", "reason": "not_selected"}],
  "pages_read": ["dora.md"],
  "claims": [
    {"text": "...", "cited_pages": ["dora.md"],
     "evidence_spans": [{"page": "dora.md", "text": "...", "verbatim_in_page": true}],
     "ground_cap": "supported", "judge_raw": "{\"status\": \"supported\"}",
     "final_status": "supported"}
  ],
  "rendered_text": "...", "did_abstain": false,
  "found_facts": ["..."], "elapsed_s": 67.2
}
```
Note the synthesize `raw` above carries `cited_pages:[]` — the **pre-normalization** output — while `claims[].cited_pages` shows the back-filled `["dora.md"]`. That juxtaposition is exactly the diagnostic that the normalization is firing (P1a).

**`type: "verifier"`**
```json
{"type": "verifier", "id": "v001", "claim_text": "...",
 "ground_cap": "supported", "judge_raw": "{\"status\": \"supported\"}",
 "predicted_status": "supported", "gold_status": "supported",
 "model_calls": [{"call_type": "judge", "attempt": 1, "first_pass": true,
                  "valid_json": true, "accepted": true, "elapsed_ms": 8800, "raw": "..."}]}
```

**`type: "question"` (graph-invoke error)**
```json
{"type": "question", "id": "q042", "error": true, "error_msg": "synthesize failed after 1 repair(s): ...",
 "elapsed_s": 3.1, "model_calls": [{"call_type": "select", "attempt": 1, "...": "..."}]}
```

Notes:
- `pages_read` and `cited_pages` carry page **ids only** (full content lives in the library on disk; the trace stays compact). Raw model outputs in `model_calls` are not truncated — they are the diagnostic payload.
- `evidence_spans[].verbatim_in_page` — normalized-substring check against the read page (quoted-verbatim vs paraphrased).
- `ground_cap` vs `final_status` — judge-override signal (#5).
- `dropped[].reason` — classified select drops (#2): `unknown_id` is the format-mismatch instability `normalize_select_result` will fix.
- per-call `elapsed_ms` across `model_calls` — lets us attribute the ~300s+ tail to a specific stage / repair (#5).

## Error handling
- Trace assembly never aborts a run: a graph-invoke failure → an `error:true` row **with** the captured `model_calls` (P2b); a row-assembly failure → a `{type:"question", id, trace_error}` row.
- A failed trace **file write** logs a stderr warning and returns the verdict unchanged — the gate result must never depend on the diagnostic artifact.
- If `backend` is not a `RecordingBackend` (defensive), tracing degrades to the `out`-derived + recomputed fields only (no `model_calls`/`raw`), without error.

## Testing (TDD, `FakeBackend` — no Ollama)
1. `RecordingBackend` tags `call_type`, stores `raw`, increments `attempt` per call_type, and times each call (`elapsed_ms` present, monotonic); `first_pass`/`valid_json` unchanged.
2. Multi-attempt capture: a scripted select that returns invalid-then-valid produces two `select` `model_calls` (attempt 1 `valid_json:false accepted:false`, attempt 2 `valid_json:true accepted:true`) — neither attempt is lost (P1b).
3. Raw synthesize surfaced: a synthesized claim with empty `cited_pages` shows `cited_pages:[]` in the synthesize `raw` and the back-filled page in `claims[].cited_pages` (P1a regression-visibility guard).
4. Drop classification: a scripted select returning a known eligible id + an unknown id + a layer-filtered id yields `dropped` reasons `unknown_id` / `filtered_out` correctly, with `eligible_page_ids` populated (P2a).
5. `ground_cap` vs `final_status` correct for a supported claim and an empty-`cited_pages`-then-backfilled claim.
6. Verifier rows: one `type:"verifier"` row per label with `ground_cap`/`judge_raw`/`predicted`/`gold`/`model_calls`.
7. Error path: a backend that makes `synthesize` raise yields a `type:"question"` `error:true` row carrying the `select` `model_calls` captured before the failure (P2b).
8. No-trace invariance: `run_questions`/`score_run` with no `trace` arg return byte-identical results (guard against behaviour drift).
9. CLI: a release run writes `trace-*.jsonl` by default; `--no-trace` suppresses it; trace presence/absence changes neither the report nor the exit code.
10. `safe_model_name` maps `gemma4:12b` → `gemma4_12b` and `ns/custom:tag` → `ns_custom_tag` (no path separators); the report stem and trace filename use it (P3).

## Self-review notes
- **Placeholders:** none.
- **Consistency:** strictly additive — return values, metrics, and `first_pass_json_validity` unchanged; only behaviour change is an extra (suppressible) file write on release. `model_calls` is the single raw-I/O source; interpreted fields derive from it + `out` + recomputed deterministic intermediates.
- **Scope:** single implementation plan; no pipeline contract changes; bounded to `runner.py`, a CLI arg, a `safe_model_name` helper, and tests.
- **Ambiguity resolved:** "raw output" = each attempt's pre-parse/pre-normalization model string (every attempt kept, with `accepted` marking the one the pipeline used); "dropped" ids are classified by cause against the recomputed eligible set, not a single raw−final difference; judge-per-claim mapping is by call order over non-`unsupported`-capped claims, matching `verify_entailment`. Accelerated-path candidate set is an explicit recorded limitation, not a silent gap.

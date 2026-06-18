# kb-offline eval traces — first-class per-question diagnostics (design)

**Issue:** EPIC #211 (kb-offline), M3/M4 hardening item #1 (highest priority — enabler for #2/#4/#5).
**Date:** 2026-06-18
**Status:** design, pending review.

## Goal

Make the release eval **self-documenting**: every `kb-offline eval release` run persists a per-question, per-stage trace alongside its report, so a failing run is diagnosable from its artifacts instead of requiring a multi-hour re-run with ad-hoc instrumentation. This folds the throwaway `tmp/cc_baseline/diagnose_gemma.py` capability back into the harness.

Motivation: the `fact_recall = 0.000` root cause (empty `cited_pages` orphaned by the grounding gate) was invisible in the release artifacts — `runner.run_questions` keeps only scorer-ready rows. The trace was built outside the harness after the fact. See `research/kb-offline-eval/2026-06-18-gemma-ratification-findings.md` §7.1.

## Scope

**In scope:** a read-only trace-capture layer over the existing query path; a trace artifact written by default on `eval release`; a `--no-trace` opt-out; unit tests on `FakeBackend`.

**Out of scope (later roadmap items, see [[project-kb-offline-select-hardening]]):** changing the `select`/`verify` contracts (#2 `normalize_select_result`, #4 abstention contract); embedding-default routing (#3); judge-mode/latency changes (#5). This item only *instruments* — it changes no pipeline behavior. The trace's `dropped_ids` and `ground_cap`-vs-`final_status` fields are precisely the signals #2/#4/#5 will consume.

## Current state (what exists)

- `eval/runner.py`:
  - `RecordingBackend` wraps a backend's `generate`, recording `{first_pass, valid_json}` per call (feeds `first_pass_json_validity`). It does **not** keep the raw output or a call-type tag.
  - `run_questions(library_path, questions, *, backend, progress=False, run_label="")` invokes the query graph per question and returns **scorer-ready rows only** (`id, expected_facts, found_facts, expected_routing, predicted_routing, should_abstain, did_abstain, error`).
  - `run_verifier_labels(...)` returns `{id, predicted_status, gold_status}` per label.
  - `score_run(...)` builds the `RecordingBackend`, runs both, and aggregates metrics.
- `graphs/query_graph.py`: `graph.invoke(...)` returns the full channel state, including `page_ids` (select), `pages` (read), `_synth` (raw synthesized `Answer` dict), `_answer` (verified `Answer` dict), `rendered_text`.
- `kb_offline_cli.py` `_cmd_eval` release path: `for i in range(args.runs): score_run(..., progress=True, run_label=...)` then aggregates + writes `release-<model>-<stamp>.{md,json}`.
- `entailment.ground_claim(claim, pages)` is deterministic and pure — safe to recompute in the trace layer.

## Architecture — non-invasive capture

Three small, isolated changes; no pipeline behavior changes when tracing is off.

### Unit A — `RecordingBackend` records call-type + raw
Extend each record to `{first_pass, valid_json, call_type, raw}`.
- `call_type` is derived from the prompt by matching the canonical fragments (`prompts.SELECT_FRAGMENT` → `"select"`; `prompts.SYNTHESIZE_FRAGMENT` → `"synthesize"`; the judge prompt begins with `"Judge whether"` → `"judge"`; else `"other"`). Matching uses a substring of each fragment so a repair-suffixed prompt still classifies.
- `raw` is the backend's returned string (post-`generate`). Adds no model calls; pure bookkeeping.
- Existing `first_pass`/`valid_json` semantics unchanged → `first_pass_json_validity` is unaffected.

### Unit B — per-question trace assembly in `run_questions`
`run_questions` gains `trace: list | None = None` (default `None` = no tracing, current behavior exactly).
- When `trace` is a list and `backend` is a `RecordingBackend`: snapshot `len(backend.records)` before each `graph.invoke`, and after, slice `backend.records[before:after]` = that question's model calls (select, synthesize, judge×N, in order).
- Assemble a trace row from: the question metadata; the `out` channels (`page_ids`, `pages`, `_synth`, `_answer`, `rendered_text`); the record slice (raw select output; raw judge outputs); a per-question `time.monotonic()` timer; and `ground_claim` recomputed per `_synth` claim against the read pages (the grounding cap, separate from the final verified status).
- `dropped_ids` = ids parsed from `raw_select_output` minus final `page_ids`. (Parsing is best-effort: if the raw select JSON won't parse, record `raw_select_output` and leave `dropped_ids` empty with a `select_parse_ok: false` flag.)
- Per-claim `judge_raw`: the judge record(s) in the slice, mapped to claims in order over the claims whose recomputed cap ≠ `unsupported` (verify skips the judge when the cap is already `unsupported`). Where the cap is `unsupported`, `judge_raw` is `null` (judge not called) — matching the real pipeline.
- Append the assembled dict to `trace`. The function's **return value is unchanged** (still scorer-ready rows); the trace is a side-channel.

`run_verifier_labels` gains the same `trace` side-channel: per label, append `{type:"verifier", id, claim_text, ground_cap, judge_raw, predicted_status, gold_status}`.

### Unit C — `score_run` + `_cmd_eval` wiring
- `score_run(..., trace: list | None = None)` threads the same list into `run_questions` and `run_verifier_labels`.
- `_cmd_eval` release path: unless `--no-trace`, create a `trace = []` per run, pass it to `score_run`, then write `research/kb-offline-eval/trace-<model>-<stamp>-run<k>.jsonl` (one object per line). Smoke path and unit tests pass no trace → zero change.
- New arg: `p_rel.add_argument("--no-trace", action="store_true", help="skip writing the per-question diagnostic trace")`.

## Data shape

One JSONL per run, `research/kb-offline-eval/trace-<model>-<stamp>-run<k>.jsonl`, one object per line, discriminated by `type`:

**`type: "question"`**
```json
{
  "type": "question", "id": "q001", "kind": "fact", "no_evidence": false,
  "expected_facts": ["..."], "expected_routing": ["dora.md"],
  "raw_select_output": "{\"page_ids\": [\"dora.md\"]}", "select_parse_ok": true,
  "page_ids": ["dora.md"], "dropped_ids": [],
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

**`type: "verifier"`**
```json
{"type": "verifier", "id": "v001", "claim_text": "...",
 "ground_cap": "supported", "judge_raw": "{\"status\": \"supported\"}",
 "predicted_status": "supported", "gold_status": "supported"}
```

Notes:
- `pages_read` and `cited_pages` carry page **ids only** (full content lives in the library on disk; the trace stays compact).
- `evidence_spans[].verbatim_in_page` is the normalized-substring check against the read page — the signal that distinguishes "model quoted verbatim" from "paraphrased."
- `ground_cap` vs `final_status` is the judge-override signal (#5): if `ground_cap == supported` and `final_status != supported`, the judge downgraded it.
- `dropped_ids` is the select-instability signal (#2): non-empty means `select` named pages that the known-page filter discarded.

## Error handling
- Trace assembly never aborts a run: any exception while building a row is caught, and a minimal `{type:"question", id, trace_error: "<msg>"}` row is written instead (mirrors how `run_questions` already tolerates a per-question failure).
- A failed trace **file write** logs a stderr warning and returns the verdict unchanged (the gate result must not depend on the diagnostic artifact).
- If `backend` is not a `RecordingBackend` (defensive), tracing degrades to the `out`-derived fields only (no `raw_select_output`/`judge_raw`), without error.

## Testing (TDD, `FakeBackend` — no Ollama)
1. `RecordingBackend` tags `call_type` (select/synthesize/judge/other) and stores `raw`; `first_pass`/`valid_json` unchanged.
2. Traced `run_questions` appends one row per question with populated select/claims/timing fields; `dropped_ids` correct when the scripted select returns a known + an unknown id; `ground_cap` vs `final_status` correct for a supported claim and for an empty-`cited_pages` claim (the regression case).
3. Traced `run_verifier_labels` appends one `type:"verifier"` row per label with `ground_cap`/`judge_raw`/`predicted`/`gold`.
4. `run_questions`/`score_run` with no `trace` arg are byte-for-byte unchanged in return value (guard against behavior drift).
5. CLI: a release run writes `trace-*.jsonl` by default; `--no-trace` suppresses it; trace presence/absence does not change the report or exit code.
6. Trace-assembly exception path writes a `trace_error` row and the run still completes.

## Self-review notes
- **Placeholders:** none.
- **Consistency:** the trace is strictly additive — return values and metrics are unchanged; the only behavior change is an extra file write on release (suppressible). `first_pass_json_validity` is untouched because `RecordingBackend`'s existing fields are preserved.
- **Scope:** single implementation plan; no contract changes; bounded to `runner.py` + a CLI arg + tests.
- **Ambiguity:** "raw select output" = the model's returned string for the select call (pre-parse, pre-filter), captured via `RecordingBackend`; "dropped ids" = parsed-raw minus final, best-effort. Judge-per-claim mapping is by call order over non-`unsupported`-capped claims, matching `verify_entailment`'s own ordering.

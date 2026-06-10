# kb-offline M1c-2 — eval gate design (frozen labelled suite + ratification)

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph` (one branch, M0–M4 accumulate). **Builds on:** M1c-1 query path (`select → read → synthesize → verify_entailment → publish`) and the M0 `eval/` skeleton (`thresholds.py`, `harness.py`). **Parents:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (Eval section + decisions 9, 17) and `docs/superpowers/specs/2026-06-07-kb-offline-M1-design-addendum.md` (Eval gate section + decisions 8, 13, 15).

**Goal:** Grow the M0 eval skeleton into the **frozen release suite** that ratifies the already-agreed thresholds against a real local model, persist the result as a ratification artifact, and make the Ollama-as-default decision.

---

## What is already settled (not re-litigated here)

- **Frozen suite shape:** 75–100 labelled questions, ≥20 no-evidence, **pinned model+config, run 3×**.
- **Ratified thresholds** (in `scripts/eval/thresholds.py`): safety floors = 1.0 (invalid-mutation rejection, citation grounding validity, post-repair JSON validity); verifier accuracy precision ≥0.98 / recall ≥0.95; clean-published-claim support rate = 1.0; first-pass JSON ≥0.95; fact recall ≥0.85; routing recall ≥0.90 / precision ≥0.80; abstention precision ≥0.95 / recall ≥0.90.
- **Entailment = two distinct metrics** (verifier accuracy AND clean-published support rate), never conflated (addendum decision 8).
- **Execution split** (addendum decision 13): CI runs only scorer-correctness tests + a tiny smoke fixture (no real models, no gated thresholds); the **gated release run** is a deliberate, manually/CI-dispatched step with real pinned backends, 3×, producing a persisted report required to pass M1c.
- `kb-offline eval release` emits the report; **Ollama becomes default only after the chosen model clears BOTH the verifier-accuracy and the model-quality bars**, otherwise report the gap and keep Anthropic default / pull a stronger model.
- Default candidate model `gpt-oss:20b` (configurable). Cloud-vs-local agreement is **secondary** drift only — cloud output is not ground truth.

## Decisions made in this brainstorm (the genuinely-open parts)

1. **Fixture corpus = hand-authored synthetic.** ~16 small purpose-built pages with real frontmatter; labels are authored ground truth (exact, deterministic, license-clean, no churn). Not a curated real-corpus subset.
2. **M1c-2 builds AND executes** the gated 3× run on `gpt-oss:20b`, persists the report, and records the Ollama-default decision now (expected outcome given M1a/b/c-1 signal: report the gap, keep Anthropic default).
3. **3× pass rule = mean ≥ threshold AND per-metric sample stddev ≤ 0.05** (runs must agree within ~5 percentage points). Safety floors must = 1.0 on **every** run (deterministic → σ = 0). The variance cap `MAX_METRIC_STDDEV = 0.05` is ratified here as a new number.
4. **Anthropic comparison is opt-in, off by default.** The gate scores Ollama vs thresholds token-free by default; `--compare anthropic` adds the secondary cloud-vs-local drift section on demand.
5. **Approach A — layered eval module** (`suite.py` / `runner.py` / extended `harness.py` / `report.py` + CLI), not a monolith and not a pytest-expressed gate. Pytest is reserved for scorer-correctness + smoke (matching the execution split).

---

## §1 Fixture (hand-authored, committed)

A synthetic library plus two labelled record files, all committed as ratification evidence:

```
plugins/sdlc-knowledge-base/eval/suite/
  library/*.md          # ~16 synthetic pages; frontmatter: layer, confidence; topics:
                        #   DORA metrics, CI/CD, testing strategy, trunk-based dev,
                        #   SDLC methods (solo/single-team/programme/assured), code review,
                        #   incident response, observability, etc.
  questions.jsonl       # >=80 records (>=20 no_evidence)
  verifier_labels.jsonl # gold verifier-accuracy set (distinct from questions)
  smoke/                # tiny CI variant: ~3 pages, ~6 questions, ~4 verifier labels
    library/*.md
    questions.jsonl
    verifier_labels.jsonl
```

**`questions.jsonl` record:**
```json
{"id": "q001", "question": "How often do elite teams deploy?", "kind": "fact",
 "expected_facts": ["multiple deploys per day"], "expected_routing_targets": ["dora.md"],
 "no_evidence": false, "expected_layer": "evidence"}
```
- `kind ∈ {fact, routing, abstention}`. `no_evidence: true` records are the abstention set (the right answer is an empty published body / "no evidence"); they carry empty `expected_facts`/`expected_routing_targets`.
- `expected_routing_targets` = the page id(s) `select` should choose (scored as set overlap).
- `expected_layer` optional — exercises `--layer` filtering where relevant.

**`verifier_labels.jsonl` record (gold set for verifier accuracy):**
```json
{"id": "v001", "claim_text": "Cost fell 30%.",
 "cited_pages": [{"library": "local", "page": "dora.md"}],
 "evidence_spans": [{"page": "dora.md", "text": "cost fell 30%"}],
 "gold_status": "supported"}
```
- Deliberately includes adversarial cases: fabricated span (text not on the page → gold `unsupported`), fabricated cited page (page not in the read set → gold `unsupported`), and near-miss fuzzy quotes (gold `partial`). This is the set the P≥0.98/R≥0.95 verifier-accuracy metric is scored against.

The suite is committed in-repo as the ratification corpus but is **not** added to `release-mapping.yaml` (dev/release infra, not a plugin-consumer artifact). The eval *code* under `scripts/eval/` already ships.

## §2 Scorers (extend `scripts/eval/harness.py`)

Keep existing `fact_recall(rows)`, `routing_scores(rows)`, `abstention_scores(rows)`. Add three pure functions:

- `verifier_accuracy(rows) -> tuple[float, float]` — `rows = [{predicted_status, gold_status}]` with statuses in `{supported, partial, unsupported}`. Precision/recall are computed on the **safety-critical `supported` decision** (the operationally meaningful framing — the verifier's job is to never pass a non-supported claim through as `supported`): `precision = |predicted==supported AND gold==supported| / |predicted==supported|`; `recall = |predicted==supported AND gold==supported| / |gold==supported|`. The full 3-class confusion matrix is also recorded in the report for diagnostics, but the gated numbers (P≥0.98 / R≥0.95) are the supported-class precision/recall defined here. Empty-denominator → 1.0 (vacuous, consistent with the other scorers).
- `first_pass_json_validity(rows) -> float` — `rows = [{first_pass_valid: bool}]`; fraction of model calls whose first emitted JSON validated before any repair.
- `clean_published_support_rate(rows) -> float` — `rows = [{published_uncaveated: bool, status}]`; of claims published without a caveat, the fraction whose status is `supported`. Tautologically 1.0 under the publication policy, but measured to prove the policy holds (a regression that published a non-supported claim uncaveated would drop this below 1.0).

All scorers are pure over row dicts and unit-tested in CI on tiny synthetic inputs with known expected outputs.

## §3 Runner (`scripts/eval/runner.py`)

- `run_questions(library_path, questions, *, backend, build_graph=build_query_graph) -> list[dict]` — for each question, invoke the M1c-1 query path and emit a scorer-ready row: `expected`/`found` facts, `expected`/`predicted` routing targets, `(should_abstain, did_abstain)` where `did_abstain = (published body empty)`, and any `first_pass_valid` flags surfaced by the pipeline's validate→repair ladder. Fact "found" matching = case-insensitive normalized-substring of each expected fact against the published `rendered_text` (definition pinned in the plan).
- `run_verifier_labels(library_path, labels, *, backend) -> list[dict]` — scores the verifier set directly: builds a `Claim` from each label, runs the deterministic `ground_claim` + `judge_claim` composition (`verify_entailment`'s per-claim logic) against the fixture pages, emits `{predicted_status, gold_status}`. No synthesis step (we are testing the verifier, not the synthesizer).
- The runner is pure orchestration over M1c-1 functions + the injected backend; FakeBackend drives it deterministically in tests.

## §4 Report + gate (`scripts/eval/report.py`) + CLI

- `aggregate(runs: list[Metrics]) -> AggregatedReport` — per metric: mean, sample stddev, per-run values. A model-quality metric **passes iff `mean ≥ threshold AND stddev ≤ MAX_METRIC_STDDEV (0.05)`**. Safety floors must = 1.0 on every run (else immediate FAIL). Overall verdict = all gated metrics pass.
- `render_report(agg, *, model, drift=None) -> str` — markdown with: a metric table (threshold / mean / stddev / per-run / pass-fail), the safety-floor block, the overall PASS/FAIL, the Ollama-default recommendation, and (if `--compare anthropic`) a secondary drift section.
- **CLI** (new `eval` subcommand group in `kb_offline_cli.py`, or a dedicated `eval` entry — fixed in the plan):
  - `kb-offline eval smoke [--backend fake]` — runs the smoke fixture end-to-end, all scorers, **no thresholds gated**. Fast, CI-runnable, exit 0 unless the pipeline errors.
  - `kb-offline eval release [--model gpt-oss:20b] [--runs 3] [--compare anthropic] [--report-dir research/kb-offline-eval]` — pinned backend, full frozen suite, 3×, aggregate, gate, persist report to `research/kb-offline-eval/release-<model>-<stamp>.md` (+ a `.json` sidecar), print PASS/FAIL + recommendation. Exit 0 on PASS, non-zero on FAIL (so a CI-dispatched job can gate on it). `<stamp>` is passed in / derived from the run, not `Date.now()` inside any workflow.

## §5 Pinning, CI, execution

- **Pinning:** `pin = {"temperature": 0, "seed": <fixed const>, "top_p": 1, "num_ctx": <fixed>}` passed through `OllamaBackend`. If `OllamaBackend.generate` does not already forward an `options` dict to the ollama client, extend it minimally to do so (model-call seam only — no validation/IO added). The pinned config is recorded in the report header for reproducibility.
- **CI (pytest, never the gated run):**
  - `tests/test_kb_offline_eval_scorers.py` — every scorer on tiny synthetic inputs with known expected values (incl. the new verifier-accuracy / json-validity / clean-support scorers and the aggregate pass/fail + variance-cap logic).
  - `tests/test_kb_offline_eval_smoke.py` — `eval smoke` end-to-end on the smoke fixture via FakeBackend (deterministic), asserting the runner→scorer→report path produces a well-formed report and the expected rows. No thresholds gated.
  - The live gated run is **not** a CI test; it is the manual execution step below.
- **Execution + record (the M1c-2 closing step):** run `kb-offline eval release --model gpt-oss:20b` (3×) on the local Ollama, commit the persisted report under `research/kb-offline-eval/`, and record the outcome + the Ollama-default decision in the EPIC decisions log and session memory. Expected outcome given prior signal: model-quality bars (synthesis-substance: fact recall, clean-published support coverage) are missed → **report the gap, keep Anthropic default**, and document what a passing model would need. Safety floors and verifier-accuracy may still pass independently — the report records each bar separately.

---

## Components & isolation

| Unit | Responsibility | Depends on |
|---|---|---|
| `eval/suite.py` | load fixture library + parse `questions.jsonl` / `verifier_labels.jsonl` into typed records | stdlib json, contracts |
| `eval/harness.py` (extend) | pure scorer functions over row dicts | nothing |
| `eval/runner.py` | drive the M1c-1 query path / verifier per record → scorer-ready rows | pipeline, entailment, graphs.query_graph, backend |
| `eval/report.py` | 3× aggregate (mean/stddev), gate vs thresholds+cap, render markdown/json | harness, thresholds |
| `eval/thresholds.py` (extend) | add `MAX_METRIC_STDDEV = 0.05` | nothing |
| CLI `eval smoke|release` | wire fixture+runner+report; persist + exit-code | all of the above |

Each unit is testable in isolation with FakeBackend; the gated run is the only part that touches a real model, and it is never run in CI.

## Out of scope (correctly deferred)

- Federation / multi-library eval (M2). Promotion-mutation eval (M2). Embedding-accelerator retrieval-recall eval (M3).
- Re-tuning `fuzzy_threshold` or `_HIGH_IMPACT_RE` blindly — the gate *measures* them; any retune is a data-driven follow-up, not part of building the gate.
- Changing the ratified thresholds — they are fixed; M1c-2 measures against them.

## Decisions log (M1c-2 delta)

1. Fixture = hand-authored synthetic (~16 pages), committed in-repo, not packaged into the plugin release.
2. M1c-2 builds AND executes the gated 3× run and records the Ollama-default decision now.
3. 3× pass rule = `mean ≥ threshold AND stddev ≤ 0.05`; safety floors = 1.0 every run; new ratified constant `MAX_METRIC_STDDEV = 0.05`.
4. Anthropic comparison opt-in (`--compare anthropic`), off by default (token-free gate).
5. Approach A layered module; pytest reserved for scorer-correctness + smoke (execution split preserved).
6. Verifier-accuracy gold set is a **separate** labelled file (`verifier_labels.jsonl`) scored by the deterministic verifier directly, distinct from the Q&A suite — the two entailment metrics stay unconflated end-to-end.
7. `eval release` exits non-zero on FAIL so a CI-dispatched job can gate; CI's own test job never runs the gated 3× model evaluation.

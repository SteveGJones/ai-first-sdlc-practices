# kb-offline Offline-Backend Ratification — Findings & Improvement Report

**Date:** 2026-06-18
**Scope:** EPIC #211 (kb-offline), M3 ratification of the local Ollama backend (`gemma4:12b`) against the frozen release eval suite, including a root-cause investigation of an anomalous `fact_recall = 0.000` and a Claude Code (Sonnet) reference baseline.
**Audience:** maintainers + external technical reviewers. This report is self-contained; you do not need prior knowledge of the codebase to follow it or to suggest improvements. **Feedback explicitly invited** on §7 (Improvement avenues) and §8 (Open questions).

---

## 1. Executive summary

- We ratify an **optional, off-by-default offline backend** for the `sdlc-knowledge-base` plugin: a LangGraph query pipeline driven by a local Ollama model (`gemma4:12b`) instead of the cloud default (Anthropic **Claude Sonnet 4.6**).
- The first ratification scored **`fact_recall = 0.000`** — a literal zero across ~75 evidence questions. That is the signature of an implementation artifact, not a capable 12B model.
- **Root cause (confirmed against the real pipeline):** `gemma4:12b` produces correct, verbatim-grounded answers but leaves the claim's `cited_pages` list **empty** (it attributes the page inside the evidence *span* instead). The deterministic grounding step requires a span's page to appear in `cited_pages`, so **every span was orphaned → every claim marked unsupported → every answer dropped → recall 0**.
- **Fix (commit `32424c6`):** normalize the synthesized answer — back-fill `cited_pages` from the evidence spans when the model leaves it empty. **`fact_recall` recovered 0.000 → 0.787.**
- **Corrected verdict: still FAIL, but on genuine single-digit quality margins** (`fact_recall 0.787` vs 0.85; `routing_precision 0.795` vs 0.80; `abstention_precision 0.900` vs 0.95; `abstention_recall 0.818` vs 0.90). The model went from *catastrophic/unusable* to *near-miss*.
- The residual gaps trace **predominantly to a second issue — `select`-instability** (the page-selection step occasionally returns an empty or over-broad page set). This is the highest-leverage next investigation.
- **Decision:** keep Anthropic/Sonnet as the default backend for now — but for the *right* reason (a true ~6-point quality gap), not the phantom zero. Given the enterprise economics (local inference is ~1/10,000th the marginal cost of metered API), a near-miss is worth pursuing, not abandoning.

---

## 2. System under test

### 2.1 The query pipeline (LangGraph, read-only)
A KB question is answered by a five-node graph (`graphs/query_graph.py`):

```
select → read → synthesize → verify → publish
```

- **select** — the model reads a compact *shelf-index* (one line per library page) and returns the 2–4 most relevant page ids. Ids not in the known page set are dropped.
- **read** — the selected pages are loaded from disk.
- **synthesize** — the model answers using only those pages, returning an `Answer` of `claims`, each with `text`, `cited_pages`, and verbatim `evidence_spans`.
- **verify** — deterministic + model hybrid. For each claim: `ground_claim` computes a *grounding cap* (verbatim span on a cited page → `supported`; fuzzy ≥0.6 token overlap → `partial`; else `unsupported`); an LLM `judge_claim` then grades entailment; final status = `min(cap, judge)`.
- **publish** — `supported` claims are rendered as-is, `partial` with a caveat, `unsupported` excluded. The concatenation is `rendered_text`. **Empty `rendered_text` = the system abstained.**

The same backend drives select, synthesize, and judge (one model does all three) — true for both the local and cloud paths.

### 2.2 The release gate (`eval/`)
- **Frozen suite:** 97 questions (`fact` / `routing` / `abstention` kinds; ≥20 `no_evidence`) + 22 verifier labels, over a 16-page software-engineering library.
- **Pinned config:** `temperature=0, seed=7, top_p=1, num_ctx=8192`. `num_ctx` is pinned to 8192 because the model default (131072) reserves a KV cache large enough to drive the host into swap; pages are tiny (~200 tokens), so 8192 never truncates.
- **Thresholds** (`eval/thresholds.py`): `fact_recall ≥ 0.85`, `routing_recall ≥ 0.90`, `routing_precision ≥ 0.80`, `abstention_precision ≥ 0.95`, `abstention_recall ≥ 0.90`, `verifier_recall ≥ 0.95`, `citation_entailment ≥ 0.98`, `first_pass_json ≥ 0.95`; safety floors = 1.0; 3-run sample-stddev cap 0.05.
- **Scorers** (`eval/harness.py`):
  - `fact_recall` — macro recall of expected facts, where a fact is "found" iff its normalized phrase is a **substring** of the published `rendered_text` (lowercased, whitespace-collapsed; punctuation preserved). *Strict.*
  - `routing_recall/precision` — micro P/R of `select`'s page ids vs expected routing targets (evidence questions only).
  - `abstention_precision/recall` — over `(should_abstain, did_abstain)`; `did_abstain = empty rendered_text`.
  - `verifier_precision/recall` — the verifier's `supported` decision vs gold labels (the 22-label set).

### 2.3 Models
- **Local:** `gemma4:12b` — 11.9B params, Q4_K_M, ~7.8 GB in VRAM, Metal GPU, ChatML template, 8192 ctx. (Switched from `gpt-oss:20b`, which swapped this host.)
- **Cloud baseline:** **Claude Sonnet 4.6** (`claude-sonnet-4-6`), the documented default backend.

---

## 3. Methodology

### 3.1 The Claude Code (Sonnet) baseline — and why it isn't the metered API
The natural reference is "how well does the cloud default do the same task?" The eval ships a `--compare anthropic` path that calls the Anthropic API — but on a flat-rate Claude Code Max plan that bills per token *only for API accounts*, the apt comparison is **Claude Code itself**, run in-session at flat rate. (For an enterprise API account the model-selector route would be cheaper than `--compare`; either way, paying per-token to baseline against ourselves is the wrong instrument here.)

A Python eval process cannot call back into the agent session, so the baseline was produced by **in-session parallel subagents** (8 question agents + 1 verifier agent, all Sonnet) replicating the real `select → synthesize → self-judge` per question, writing structured JSON. Those outputs were then scored by **the real `ground_claim` / `publish` / harness functions** — so Sonnet's claims faced the identical verbatim-grounding gate gemma faced.

**Baseline caveats (do not over-read):** it uses subagents writing structured files, *not* the literal LangGraph machinery + repair ladder; `first_pass_json = 1.0` is "valid by construction," not a measured grammar-constrained number; single run; self-judge (faithful to gemma's single-backend design but still self-grading). It is a fair **quality** comparison, not a byte-identical pipeline run.

### 3.2 The diagnostic
To find the `0.000`, we ran the **real** `build_query_graph(OllamaBackend gemma4:12b)` on 10 evidence questions and dumped every stage boundary: selected page ids, raw synthesized claims, per-claim `ground_claim` cap, final entailment status, published text, and found-vs-expected facts. This is the authoritative instrument (not the subagent reconstruction).

---

## 4. Investigation & root cause

### 4.1 What was ruled out
- **Scorer too strict / phrase absent from source** — ruled out: all 60 evidence fact-questions have their expected phrase **verbatim in the source page**, and Sonnet scored 0.907 through the identical scorer.
- **`num_ctx` truncation** — ruled out: pages are 688–841 bytes (~200 tokens); 8192 is never approached.
- **The model-output sentinel bug** — ruled out: the corrected run had **0 errored questions** (a prior fix, commit `a74e2e9`, strips gemma's trailing `<|tool_response>` sentinel before JSON parsing in the pipeline paths).

### 4.2 The real-pipeline trace
On all 10 evidence questions: `select` routed correctly, `synthesize` produced a claim, the evidence span was a **verbatim substring** of the page — yet `ground_claim` capped **every** claim `unsupported`, so every answer was dropped → abstain → `found = 0`.

A claim with a verbatim span on the right page can only fail grounding via its two guards. The trace showed the cause:

```
q001  claim.text: "The four DORA key metrics are deployment frequency, lead time for changes, change failure rate, and time to restore service."  (correct)
      evidence span: "...deployment frequency, lead time for changes, change failure rate, and..."  (verbatim in dora.md)
      cited_pages: []          ← EMPTY
      ground_cap: unsupported
```

`ground_claim` builds `cited = {ref.page for ref in claim.cited_pages}` (empty), then for each span requires `span.page in cited` ("a span may only ground against a page the claim actually cited"). With `cited_pages = []`, **every span is skipped** and the claim falls through to `unsupported`. This was **10/10 claims** — gemma never populates `cited_pages`; it puts the page in the span only.

### 4.3 Minimal confirmation
```
q001 ground_claim AS-IS (cited_pages=[]):        unsupported
q001 ground_claim BACK-FILLED (cite span.page):  supported     ← one change flips it
```

### 4.4 The fix (commit `32424c6`)
In `pipeline.synthesize`, after validation: for any claim with evidence spans but **empty** `cited_pages`, set `cited_pages` to the unique pages declared by its spans (dedup; default library `"local"`). This restores grounding for span-attributing models and also repairs downstream `promote` citations (which read `cited_pages`). The anti-mis-attribution rule is preserved when `cited_pages` *is* populated (back-fill fires only on an empty list). TDD: a failing test (empty `cited_pages` + verbatim span → `supported` after `synthesize`) and a guard test (explicit `cited_pages` not overwritten).

### 4.5 Recovery
| | broken | fixed |
|---|---|---|
| `fact_recall` (10-q diagnostic) | 0.000 | 0.900 |
| `fact_recall` (full 97) | 0.000 | **0.787** |

The 10-q sample (0.900) was front-loaded with easy DORA/CI-CD questions; 0.787 is the honest full-suite number.

---

## 5. Results

Bars are the release thresholds. "broken" = pre-fix; "fixed" = post-fix (the true numbers); "Sonnet" = the in-session Claude Code baseline (§3.1 caveats apply).

| metric | bar | gemma broken | **gemma fixed** | Sonnet baseline |
|---|---|---|---|---|
| fact_recall | 0.85 | 0.000 | **0.787** ❌ | 0.907 ✅ |
| routing_recall | 0.90 | 0.933 | 0.933 ✅ | 1.000 ✅ |
| routing_precision | 0.80 | 0.795 | 0.795 ❌ | 0.987 ✅ |
| abstention_precision | 0.95 | 0.227 | 0.900 ❌ | 1.000 ✅ |
| abstention_recall | 0.90 | 1.000\* | 0.818 ❌ | 1.000 ✅ |
| verifier_precision | 0.98 | 1.000 | 1.000 ✅ | 1.000 ✅ |
| verifier_recall | 0.95 | 1.000 | 1.000 ✅ | 1.000 ✅ |
| first_pass_json | 0.95 | 0.957 | 0.969 ✅ | 1.000\*\* |
| **VERDICT** | | FAIL | **FAIL** | PASS |

\* The broken run's `abstention_recall = 1.0` is itself an artifact — it "abstained" on everything because every answer was dropped. \*\* "by construction" for the baseline (structured subagent output), not a measured grammar-constrained value.

**Latency / cost.** `gemma4:12b`: ~93–102 s/question average, range **37.5 s – 394 s** (≈10× spread; a fat tail). Sonnet baseline: ~3–4 s/question. So the local path is ~25× slower per query — but at roughly **1/10,000th the marginal token cost**, which inverts the trade for cost-sensitive / high-volume / air-gapped enterprise deployments. Latency alone is not disqualifying; quality is the gate.

---

## 6. Remaining-gap analysis (corrected run)

Exact arithmetic from the fixed run (22 no-evidence questions; 20 total abstentions observed):
- **18/22** no-evidence questions correctly abstained; **4** were wrongly answered (gemma found spurious relevance) → `abstention_recall = 0.818`.
- Of 20 total abstentions, **18 correct + 2 wrong** (2 evidence questions got an empty page set → empty answer → counted as a wrong abstention) → `abstention_precision = 0.900`.

Attribution of each failing metric:

| failing metric | value/bar | dominant cause |
|---|---|---|
| `routing_precision` | 0.795 / 0.80 | `select` **over-selects** (returns extra pages beyond the one needed) |
| `abstention_precision` | 0.900 / 0.95 | 2 `select`-**empties** on evidence questions → empty answers counted as wrong abstentions |
| `abstention_recall` | 0.818 / 0.90 | `select`/synthesize find **spurious relevance** on 4 no-evidence questions → answered instead of abstained |
| `fact_recall` | 0.787 / 0.85 | partly the `select`-empties above; partly harder questions; partly strict substring matching of multi-item facts |

**Unifying observation.** Three of four failures are downstream of the **`select` step** (empty sets, over-broad sets, spurious relevance on no-evidence). And the original 0.000 bug plus the `select`-empties share a deeper theme: **the deterministic layers are strict about output *shape*, and a semantically-capable model loses credit for minor format deviations** (empty `cited_pages`; page ids that don't exactly match known names). That theme is the most promising lever.

---

## 7. Improvement avenues (feedback invited)

### 7.1 `select`-instability (highest leverage — gates 3 of 4 failing metrics)
**Symptom:** `select` sometimes returns `[]` (empty) or over-broad sets. Not yet root-caused (next investigation). Leading hypotheses, by analogy to the `cited_pages` bug:
- gemma returns page ids in a slightly-off format (missing `.md`, different case, a descriptive phrase) → the strict `id in known_pages` filter drops them → `[]`.
- gemma returns malformed JSON that survives repair as an empty `SelectResult`.

**Candidate fixes:**
- **Format-tolerant id matching** in `select` (normalize case, add `.md`, fuzzy-match returned ids to known page names) — mirrors the `cited_pages` tolerance fix; likely removes most empties.
- **Embedding-accelerator-bounded select.** M3 already ships an embedding prefilter (`accelerated_candidates`). Constrain `select` to the top-k embedding shortlist and/or seed it with those candidates so it never returns nothing relevant. (Recall@k floor is already gated at 0.95.)
- First: **capture `select`'s raw output** on the empty/over-broad cases to confirm the cause before fixing.

### 7.2 Precision (`routing_precision`, `abstention_precision`)
- **Tighten the `select` prompt** to prefer the *fewest* sufficient pages (currently "2–4 most relevant") — trades a little recall for precision. Needs A/B on the suite.
- **Prune to contributing pages.** Today `predicted_routing` = `select`'s raw output. Deriving routing from the pages actually cited by *published* claims would raise precision and arguably measures the real signal ("pages used to answer") rather than "pages glanced at." This is a **metric-definition choice** — reviewer input wanted.
- **Embedding re-rank + similarity threshold** to drop low-relevance selections.
- `abstention_precision` is mostly gated by the `select`-empties (§7.1) — fixing those should lift it toward 1.0.

### 7.3 Abstention recall (don't answer no-evidence questions)
- **Relevance floor on select:** return an empty set when nothing clears an embedding-similarity threshold → correct abstention on genuinely-unanswerable questions (fixes the 4 spurious answers).
- **Explicit abstention instruction in synthesize:** "if the supplied pages do not answer the question, return no claims." gemma currently synthesizes a claim even from off-topic pages.

### 7.4 Fact recall
- Largely downstream of §7.1–7.3 (recover the `select`-empties; stop dropping grounded claims).
- **Scorer strictness:** `fact_recall` requires the expected phrase as a normalized **substring**. Multi-item facts (e.g., a 4-item DORA list in an exact order) are brittle — a correct answer with reordered items scores zero. Consider token-overlap or set-membership matching for list-type facts. **Scorer-design question — reviewer input wanted** (changing it changes what "0.85" means).

### 7.5 Cross-cutting: make deterministic layers format-tolerant
The `cited_pages` back-fill is one instance; tolerant `select` id-matching is another. A small, principled "normalize model output before the strict deterministic gate" layer would harden the pipeline for *any* capable-but-format-imperfect model, not just gemma — while preserving the safety properties (verbatim grounding, anti-mis-attribution) when the model *does* comply.

---

## 8. Open questions for reviewers

1. **Routing metric definition** — should `predicted_routing` be `select`'s raw output (current) or the pages actually cited by published claims? The latter rewards "used the page," not "considered the page."
2. **Fact-matching strictness** — is normalized-substring the right `fact_recall` definition, given multi-item / ordered facts? What would you use?
3. **Where to enforce abstention** — at `select` (relevance floor) or `synthesize` (explicit instruction) or both?
4. **Format-tolerance vs strictness** — how much output normalization is acceptable before it masks genuine model weakness the gate is meant to catch?
5. **Is 0.85 `fact_recall` the right bar** for a *cost-1/10,000th* backend, or should an offline tier have its own (lower, clearly-labelled) threshold profile?

---

## 9. Threats to validity

- **Single run** (`--runs 1`); the 3-run variance cap (0.05) has not been applied to the corrected numbers. (The pre-fix runs were 3× consistent.)
- **Sample vs full** — the 10-q diagnostic (0.900) overstated the full-suite `fact_recall` (0.787); always trust the full suite.
- **Baseline is a reconstruction** — the Sonnet baseline used in-session subagents + the real scorers, not the literal LangGraph machinery; treat it as a quality reference, not a pipeline-identical run.
- **Quantization / hardware** — `gemma4:12b` is Q4_K_M on a single Metal host; a higher-precision quant or different hardware may move both quality and latency.
- **Frozen suite size** — 97 questions; small per-metric denominators mean a few questions move a metric by points.

---

## 10. Recommendations

1. **Keep Anthropic / Claude Sonnet 4.6 as the default backend** (gemma fails the gate on real margins). Offline stays off-by-default by design.
2. **Investigate `select`-instability next** (capture raw output → format-tolerant matching and/or embedding-bounded select). Highest leverage: it gates `routing_precision`, both abstention metrics, and some `fact_recall`. gemma is within single digits of all four bars; this could plausibly clear the gate.
3. **Re-ratify after the `select` fix**, then run the full **3-run** gate if `--runs 1` clears.
4. **Review the routing-metric and fact-matching definitions** (§8) — some of the gap may be measurement, not model.
5. **Consider an offline-tier threshold profile** if a cost-1/10,000th backend warrants different bars.

---

## 11. Appendix — artifacts & reproduction

- **Fix commit:** `32424c6` (`pipeline.synthesize` cited_pages back-fill). Related: `a74e2e9` (sentinel strip), `1ee138a` (per-question progress logging).
- **Reports (`research/kb-offline-eval/`):**
  - `release-gemma4_12b-20260617T234246Z.md` — broken (fact_recall 0.000)
  - `release-gemma4_12b-20260618T044924Z.md` — fixed (fact_recall 0.787)
  - `baseline-claude-code-claude-20260618T035356Z.md` — Sonnet baseline (PASS)
- **Diagnostic + baseline harness:** `tmp/cc_baseline/` (`diagnose_gemma.py` real-pipeline tracer; `score.py` baseline scorer; `gemma_trace.json` per-stage trace). *(tmp/ is gitignored — promote into the repo if we want these as durable evidence.)*
- **Reproduce a single ratification:**
  `PYTHONUNBUFFERED=1 .venv/bin/kb-offline eval release --stamp <STAMP> --runs 1 --report-dir research/kb-offline-eval`
  (per-question progress streams to stderr; pin is applied automatically).
- **Reproduce the diagnostic:** `.venv/bin/python tmp/cc_baseline/diagnose_gemma.py 10`

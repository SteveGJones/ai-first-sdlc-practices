# kb-offline Offline-Backend Ratification — Findings & Improvement Report (rev 2)

**Date:** 2026-06-18 (rev 2: 2026-06-19, after external review)
**Scope:** EPIC #211 (kb-offline), M3 ratification of the local Ollama backend (`gemma4:12b`) against the frozen release eval suite — the `fact_recall = 0.000` root cause, the corrected verdict, a Claude Code agentic reference, and a trace-driven analysis of the residual failures.
**Audience:** maintainers + external technical reviewers. Self-contained. **Feedback invited** on §8–§9.
**Auditable evidence:** `harness/` (diagnostic + reference scorer + the 9 reference subagent outputs), `trace-gemma4_12b-20260619T044923Z-run1.jsonl` (the per-question trace this report analyses), and the `release-*.{md,json}` reports — all committed alongside this file.

---

## 1. Executive summary

- We assess an **optional, off-by-default offline backend** for `sdlc-knowledge-base`: a 5-stage LangGraph query pipeline driven by local `gemma4:12b` instead of the cloud default (`AnthropicBackend`, `claude-sonnet-4-6`).
- The first ratification scored **`fact_recall = 0.000`** — an implementation artifact, not model incapacity. **Root cause:** gemma emits correct, verbatim-grounded claims but leaves `claims[].cited_pages` empty; `ground_claim` requires a span's page to be in `cited_pages`, so every claim was capped `unsupported` and dropped. **Fix** (commit `32424c6`): back-fill `cited_pages` from the evidence spans. `fact_recall` recovered **0.000 → 0.787**.
- **Corrected verdict: still FAIL** on four margins — `fact_recall 0.787` (vs 0.85), `routing_precision 0.795` (vs 0.80), `abstention_precision 0.900` (vs 0.95), `abstention_recall 0.818` (vs 0.90). Reproduced identically across two corrected runs; the specified **3-run variance gate has not been run**, so this is consistent-but-not-yet-variance-ratified.
- The residual failures are now traced to two distinct problems: **`select` discipline** (over-selection, and a degenerate "select the whole shelf" on irrelevant questions) and a **verifier vulnerability** (an absence-claim grounded on an irrelevant verbatim span was published as `supported`).
- **Decision: keep `AnthropicBackend` as the default.** gemma independently fails the existing gate. This holds regardless of cost arguments (see §7, which no longer asserts an unverified cost ratio).

---

## 2. System under test

### 2.1 The query pipeline (LangGraph, read-only)
Four nodes, five logical stages:
```
select → read → synthesize → verify_publish   (verify + publish are one node)
```
- **select** — the model reads a compact *shelf-index* (one line/page) and returns 2–4 page ids. The select node passes the model the full shelf but accepts only ids in the **layer-filtered eligible set**; ids outside it are silently dropped (see §6.5 — this is a contract mismatch).
- **read** — selected pages loaded from disk.
- **synthesize** — the model answers using only those pages, returning `claims` (each `text` + `cited_pages` + verbatim `evidence_spans`). The pipeline now back-fills empty `cited_pages` from the spans (the §4 fix).
- **verify** — per claim: `ground_claim` caps status (verbatim span on a cited page → `supported`; fuzzy ≥0.6 token overlap → `partial`; else `unsupported`); an LLM `judge_claim` (same model) grades; final = `min(cap, judge)`.
- **publish** — `supported` as-is, `partial` caveated, `unsupported` excluded. Empty published text = abstention.

The **same model** drives select, synthesize, and judge (so the judge self-grades).

### 2.2 The release gate (`eval/`)
- **Frozen suite:** 97 questions (`fact`/`routing`/`abstention`; 22 `no_evidence`) + 22 verifier labels, over a 16-page library (page bodies **613–841 bytes**; full prompts are larger but still well under the pinned context).
- **Pinned config:** `temperature=0, seed=7, top_p=1, num_ctx=8192` (8192 chosen to avoid the default 131072 KV cache that swaps this host).
- **Gated thresholds** (`report._GATED_MINIMUMS`, 8 metrics): `fact_recall ≥0.85`, `routing_recall ≥0.90`, `routing_precision ≥0.80`, `abstention_precision ≥0.95`, `abstention_recall ≥0.90`, `verifier_precision ≥0.98` (vs `CITATION_ENTAILMENT`), `verifier_recall ≥0.95`, `first_pass_json ≥0.95`; plus a 3-run sample-stddev cap of 0.05. **Not gated** (despite existing as constants): `EMBEDDING_RECALL_AT_K`, `FEDERATION_ATTRIBUTION` (see §6.6).
- **Scorers** (`eval/harness.py`): `fact_recall` (macro recall; a fact is "found" iff its normalized phrase is a **substring** of published text — strict); routing micro-P/R (over `select` ids, evidence questions only); abstention P/R over `(should_abstain, did_abstain=empty-published)`; verifier P/R over the 22 fixed labels.

### 2.3 Models / references
- **Local:** `gemma4:12b` (11.9B, Q4_K_M, ~7.8 GB VRAM, Metal, ChatML, 8192 ctx).
- **Cloud default:** `AnthropicBackend` → `claude-sonnet-4-6`.
- **Reference (NOT the cloud backend):** a **Claude Code agentic reference** — see §3.1 for exactly what it is and is not.

---

## 3. Methodology

### 3.1 The Claude Code agentic reference (what it is, and is not)
To gauge "how well could a strong model do this task on the same scorers," we produced a reference using **9 Claude Code subagents** (8 question slices + 1 verifier, each pinned to `sonnet`) that replicated the `select → synthesize → self-judge` steps and wrote final structured JSON, scored by the **real `ground_claim`/`publish`/harness** functions. Outputs and scorer are committed under `harness/`.

**This is a Claude Code agentic reference, not a `claude-sonnet-4-6` cloud-backend baseline.** It does **not** exercise `AnthropicBackend`'s prompts, schema delivery, model calls, repair ladder, latency path, or orchestration. The persisted artifact records only `model: claude (Max plan)`. Treat its score (§5) as an **agentic upper-bound reference**, not a controlled measurement of the cloud default. For a true cloud-backend baseline, run the literal `eval release --compare anthropic` path (not yet done).

### 3.2 Diagnostic
The `0.000` was found by running the **real** `build_query_graph(OllamaBackend gemma4:12b)` over evidence questions and dumping every stage boundary (`harness/diagnose_gemma.py`). The release runner now writes equivalent per-question traces by default (`trace-*.jsonl`), which this report's §6 analyses.

---

## 4. Root cause of `fact_recall = 0.000` and the fix

Ruled out first: the scorer (all 60 evidence fact-questions have their expected phrase verbatim in-source; the reference scored 0.907 through the same scorer), `num_ctx` truncation (tiny pages), and the model-output sentinel bug (commit `a74e2e9`; 0 errored questions in the corrected runs).

**Cause:** gemma's claims were correct and carried verbatim spans naming the right page, but `claims[].cited_pages` was **empty** — it attributed the page via the *span* only. `ground_claim` requires `span.page ∈ cited_pages`, so every span was orphaned → every claim `unsupported` → dropped → empty answers → recall 0. Confirmed end-to-end: ground-cap was `unsupported` for claims whose span was verbatim; injecting the span's page into `cited_pages` flipped the same claim to `supported`.

**Fix (commit `32424c6`):** in `pipeline.synthesize`, when a claim has spans but empty `cited_pages`, back-fill `cited_pages` from the spans' pages (preserving the anti-mis-attribution rule when `cited_pages` is populated). TDD'd. Result: `fact_recall 0.000 → 0.787`.

---

## 5. Results

| metric | gate | gemma (broken) | **gemma (fixed)** | CC agentic reference¹ |
|---|---|---|---|---|
| fact_recall | 0.85 | 0.000 | **0.787** ❌ | 0.907 |
| routing_recall | 0.90 | 0.933 | 0.933 ✅ | 1.000 |
| routing_precision | 0.80 | 0.795 | 0.795 ❌ | 0.987 |
| abstention_precision | 0.95 | 0.227 | 0.900 ❌ | 1.000 |
| abstention_recall | 0.90 | 1.000² | 0.818 ❌ | 1.000 |
| verifier_precision | 0.98 | 1.000³ | 1.000³ | 1.000³ |
| verifier_recall | 0.95 | 1.000³ | 1.000³ | 1.000³ |
| first_pass_json | 0.95 | 0.957 | 0.969 ✅ | n/a⁴ |
| **VERDICT** | | FAIL | **FAIL** | (reference) |

¹ Agentic reference, not a cloud-backend measurement (§3.1). ² Artifact of abstaining on everything (all claims dropped). ³ `verifier_precision/recall` are over the **22 fixed labels only** — they do **not** cover generated absence-claims (§6.2). ⁴ "valid by construction" for the structured-output reference, not a measured number.

**Not measured (reported as deterministic invariants, not observations):** `clean_published_support_rate` is computed as `clean_published_support_rate([])` → vacuously `1.0` every run; the three safety floors (`invalid_mutation_rejection`, `citation_validity`, `post_repair_json_validity`) are **hardcoded `1.0`** in the query-only runner, not measured this run. They are deterministic guarantees of the query path, not release-suite measurements.

**Gap framing:** the `~6-point` shortfall is against the **0.85 gate**; against the agentic reference (0.907) the `fact_recall` gap is `~12 points`.

**Reproducibility:** two corrected runs produced identical numbers (seed-pinned). The **3-run variance gate has not been run**, so we say "consistent across two runs," not "deterministic/ratified."

---

## 6. Trace-driven analysis of the residual failures

From `trace-gemma4_12b-20260619T044923Z-run1.jsonl` (119 rows: 97 question + 22 verifier).

### 6.1 `select` relevance failure on no-evidence questions: 22/22 (not 4/22)
**Every** no-evidence question selected ~the whole library: 21 selected all 15 valid pages (plus the typo `release--management.md`), `q079` selected all 16. The correct taxonomy:
- **Selector relevance failure: 22/22** — the model never abstains at `select`; it dumps the shelf.
- **Non-empty publication failure: 4/22** — `q076/q078/q086/q088` leaked a published answer.
- **Metric "abstention success": 18/22** — these passed `abstention_recall` only because *verification dropped the claims*, not because the selector abstained.

This strengthens the case for a **select-level abstention contract**: the metric understates a pervasive selector failure that verification happens to mask 18 times out of 22.

### 6.2 Verifier vulnerability: an absence-claim graded `supported` (NEW — serious)
The 4 leaked answers are **semantic abstentions expressed as claims**, e.g. `q076` → *"The company payroll schedule is not mentioned in the provided documents."* — but the claim **cites `dora.md` with span `"DORA Metrics"`** (irrelevant to the claim) and is graded **`final=supported`**. All four follow this pattern.

Implications:
- gemma *understood* evidence was absent — but violated the structural abstention contract by emitting it as a claim.
- `ground_claim` accepted an **irrelevant** verbatim span (the string "DORA Metrics" is present on the page) → **verbatim-span presence does not imply claim support**.
- the **self-judge** did not catch the mismatch (the same model graded its own absence-claim "supported").
- an **unsupported claim reached publication as fully supported**. `verifier_precision = 1.0` covers only the 22 fixed labels and entirely misses this generated failure class.

This is more serious than "spurious relevance." Mitigations in §7.

### 6.3 Over-selection (routing_precision 0.795)
**13** evidence questions select the right page **plus** extras (q006, q008–q010, q018–q020, q034, q045, q047, q058, q069, q074). A separate **3** (q011, q039, q060) select extras **without** the expected page (a routing-recall miss, not over-selection). The 2–4-page prompt encourages breadth → precision loss.

### 6.4 Typo'd page ids (24 `unknown_id`, 4 distinct)
All are typos of real pages, fuzzy-mapping to their true page (nearest `difflib` ratio):
- `release--management.md` (double hyphen) → `release-management.md` (**0.977**), ×21 — **all on no-evidence questions**.
- `sdl-solo.md` → `sdlc-solo.md` (**0.957**); `sdl-single-team.md` → `sdlc-single-team.md` (**0.973**).
- `ci-cd.d` → `ci-cd.md` (**0.933**).

Because the 21 `release--management` typos are all on **no-evidence** questions (excluded from routing scoring), recovering them **cannot worsen routing_precision** — it would only increase pages-read and could affect abstention behaviour. The one routing-relevant recovery is `q032` (`sdl-solo` → the expected `sdlc-solo.md`).

### 6.5 Empty selects (2): one is a pipeline-input bug
- **`q032`** selected two `sdl-*` typos → both `unknown_id` → `page_ids=[]`. Fuzzy normalization would recover the expected page here.
- **`q005`** selected real but **wrong-layer** pages (`incident-response.md`, `observability.md` on an `evidence`-layer question); the deterministic layer filter silently dropped both → `page_ids=[]`. This is partly a **pipeline-input contract bug**: the non-accelerated path shows the model the *full* shelf but accepts only *layer-filtered* ids. The selector should receive a shelf of **eligible candidates only** (as the accelerated path already does), instead of being asked to infer an invisible layer restriction.

### 6.6 Empty selection wastes the synthesis budget
After `q032`'s empty select, the graph **still calls synthesis**: gemma spends ~321 s across failed+repaired synthesis (inventing a `"Page 1"` citation, eventually rejected); total question latency **396.7 s**. An empty `page_ids` should **short-circuit** to an empty published answer — a correctness, latency, and predictability win independent of fuzzy normalization.

### 6.7 fact_recall miss decomposition (16 misses — "largely downstream of select" was overstated)
- **5 routing-caused:** `q005`, `q011`, `q032`, `q039`, `q060`.
- **11 select-the-right-page-but-miss**, split into:
  - **scorer artifacts** (answer essentially right, scorer strict): `q015` (Oxford comma), `q051` (compound phrase split across claims), `q072` ("and" vs "or"), `q074` (article substitution).
  - **genuinely incomplete answers:** `q023` (omits the 400-line limit), `q040` (omits "complex systems at scale"), `q045` (omits "remove stale flags"), `q064`, `q071`, `q075` (omit the requested fact).

So fixing **all five routing-caused** misses could move recall to at most `64/75 = 0.853` — and only if the recovered answers also satisfy the (strict) scorer. Real headroom is mixed model-quality + scorer-strictness, not purely selection.

### 6.8 Not gated despite existing as constants
`EMBEDDING_RECALL_AT_K` (the embedding prefilter floor) and `FEDERATION_ATTRIBUTION` are threshold constants but are **not** in `_GATED_MINIMUMS` and are **not** invoked by `eval release`. Any prior claim that recall@k is "already gated at 0.95" is **incorrect** — it is unenforced. If the prefilter floor is intended as a gate, it must be wired into `gate()`.

---

## 7. Improvement avenues (revised by §6 + reviewer answers)

**Highest leverage — #4 abstention + selection discipline, enforced at three levels** (hits over-selection, the 22/22 selector failure, and the absence-claim vulnerability):
1. **`select`:** allow/encourage an explicit "no relevant page" result; bias toward the *fewest* sufficient pages.
2. **graph control-flow:** short-circuit an empty selection to an empty answer (§6.6).
3. **`synthesize`/verify:** return no claims when pages don't answer; **reject absence-claims** or represent abstention outside `Answer.claims`.

**Verifier hardening (from §6.2):** add negative/absence-claim tests; recognize that verbatim-span presence ≠ support; either reject absence-shaped claims at synthesis or have the judge require the span to be *about* the claim. The current self-judge + verbatim-grounding both miss this.

**`q005` contract fix (§6.5):** feed `select` a shelf of eligible (layer/confidence-filtered) candidates only — remove the prompt/validator mismatch.

**#2 fuzzy id-normalization — narrow, not blind:** normalize only **unambiguous syntax** (case/`.md`/basename) deterministically; fuzzy page matching must require a **unique winner, a strong score, and a margin over the runner-up**, with every correction **logged**. Net gain is modest (~1 routing-relevant recovery, `q032`); pair it with the abstention discipline above.

**Scorer evolution (versioned, not redefined in place):** keep raw `select` output as the routing metric and **add** a separate *published-citation-utilization* metric (don't replace routing precision); keep exact normalized matching as a lexical metric and **add** list/set-equivalence + semantic-coverage scorers. Any change to the frozen suite/thresholds must be **versioned**, not silently applied after observing failures.

**Cost/quality:** do **not** lower the ratification bar on cost grounds. A separate **offline tier** is reasonable only with an explicit degraded-quality product contract and risk-appropriate acceptance tests (its own versioned thresholds).

---

## 8. Open questions

1. Routing metric: keep `select`-output-based routing precision, and add citation-utilization separately? (Reviewer: yes — add, don't replace.)
2. fact-recall matching: lexical substring is brittle for lists/ordering — add set/semantic scorers under suite versioning? (Reviewer: yes — add, version, don't redefine.)
3. Abstention enforcement layer(s)? (Reviewer: all three — select / control-flow / synthesize+verify.)
4. How much output normalization before it masks real weakness? (Reviewer: unambiguous syntax only; fuzzy needs unique winner + margin + logging.)
5. Should a 1/10,000-cost backend get a lower bar? (Reviewer: not without a verified cost model and a separate, contract-bound offline tier.)

---

## 9. Threats to validity
- **Two identical corrected runs, but the 3-run variance gate has not run** — consistent, not variance-ratified.
- **The reference is a Claude Code agentic reference, not a cloud-backend baseline** (§3.1) — do not read its 0.907 as `claude-sonnet-4-6` via `AnthropicBackend`.
- **No measured cost or latency comparison.** Local latency is logged; the reference's per-question time came from *parallel* subagents and is not comparable to sequential pipeline latency. No token/price/energy/hardware model exists, so no cost ratio is asserted in this report.
- **Some "safety" numbers are deterministic invariants, not observations** (§5): `clean_published_support_rate` is vacuous; the floors are hardcoded; recall@k/federation-attribution are unenforced.
- **Quantization/hardware:** Q4_K_M on a single Metal host; another quant/host may move quality and latency.
- **Small suite** (97 Q / 22 labels): a few questions move a metric by points.

---

## 10. Recommendations
1. **Keep `AnthropicBackend` (`claude-sonnet-4-6`) as the default** — gemma fails the existing gate on four margins.
2. **Build the three-level abstention contract (§7) first** — highest leverage; it addresses the 22/22 selector failure, over-selection, and the no-evidence answers.
3. **Fix the verifier vulnerability (§6.2)** — add absence-claim tests; reject/relocate absence claims; don't treat verbatim presence as support.
4. **Short-circuit empty selects** (§6.6) and **feed `select` the eligible shelf** (§6.5) — cheap correctness/latency wins.
5. **Add #2 fuzzy normalization narrowly** (unique-winner + margin + logged), paired with the abstention work.
6. **Evolve scorers under versioning** (citation-utilization; list/semantic fact coverage) and **wire recall@k/federation-attribution into the gate** if they are meant to be enforced.
7. **Run the full 3-run variance gate** before any ratification claim, and the literal `--compare anthropic` path if a cloud-backend baseline is wanted.
8. **Correct the report-template line** in the generated reference report (it currently prints "recommend making Ollama the default backend" for the reference — a template error keyed on PASS/FAIL).

---

## 11. What is strong (unchanged)
- The `0.000` diagnosis is convincing; the `cited_pages` repair is narrow, tested, and explains the measured recovery.
- The primary gemma metrics and abstention arithmetic are correct.
- Keeping Anthropic as default is justified independently of any cost argument.
- The trace instrument turns "gemma is close" into a concrete, sourced work-list.

---

## Appendix — artifacts
- Report ↔ code fidelity: this rev integrates the prior addendum into the body (no separate contradictory section).
- `trace-gemma4_12b-20260619T044923Z-run1.jsonl` — per-question trace (this report's §6 source).
- `release-gemma4_12b-20260619T044923Z.{md,json}` — the analysed run's verdict.
- `harness/diagnose_gemma.py`, `harness/baseline_score.py`, `harness/claude-baseline-outputs/`, `harness/README.md` — diagnostic + reference scorer + reference outputs + identity/timing caveats.
- Fix: commit `32424c6`. Sentinel fix: `a74e2e9`. Eval-traces feature: `dd6cfd1..b476a5e`.

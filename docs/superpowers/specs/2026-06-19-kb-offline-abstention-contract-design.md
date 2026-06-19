# kb-offline Slice 1 — abstention contract + verifier hardening (design)

**Issue:** EPIC #211, select/verifier-hardening roadmap. Slice 1 of 3 (Slice 2 = fuzzy id-normalize; Slice 3 = scorer evolution + gate wiring — both deferred).
**Date:** 2026-06-19
**Status:** design, pending review.
**Grounded in:** `research/kb-offline-eval/2026-06-18-gemma-ratification-findings.md` (rev2) + `trace-gemma4_12b-20260619T044923Z-run1.jsonl`.

## Goal

Make "the KB has nothing relevant" a **first-class, structurally-enforced outcome** end-to-end, and harden the verifier so a claim is supported only by a span that is both present *and relevant*. This fixes: the 22/22 no-evidence selector failure (model dumps the whole shelf), the 4 leaked no-evidence answers, the §6.2 verifier vulnerability (an absence-claim grounded on the irrelevant span "DORA Metrics" graded `supported`), the q005 eligible-shelf contract mismatch, and the q032 empty-select 321 s waste.

## Scope

**In:** abstention contracts (`SelectResult`, `Answer`); eligible-shelf on **all four** query paths; `select` may abstain; a graph short-circuit + terminal abstain node; `synthesize` abstain-instead-of-absence-claim; deterministic claim↔span relevance floor in `ground_claim` + strengthened `judge_claim` + epistemic-absence guard; federation merge abstention semantics; CLI/trace surfacing.

**Out (deferred, by design):** embedding relevance-floor for select (Slice 3 — needs score-distribution calibration); any frozen-metric change/versioning (Slice 3 — we preserve `did_abstain = empty body`); fuzzy id-normalization (Slice 2 — so q032 remains a *recall* miss in Slice 1, though its 321 s waste disappears via the short-circuit).

## 1. Contracts (`contracts.py`)

```python
class SelectResult(BaseModel):
    page_ids: list[str] = Field(default_factory=list)
    no_relevant_page: bool = False
    abstention_reason: str | None = None

class Answer(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    rendered_text: str = ""
    abstained: bool = False
    abstention_reason: str | None = None
```
`abstention_reason` is the field name in **both** (no `reason`/`abstention_reason` split). Defaults preserve current behaviour.

**Abstention invariants (enforced, not just documented):**
- `SelectResult.no_relevant_page=True` ⇒ `page_ids=[]`.
- After id/layer filtering, if `page_ids` becomes empty and `no_relevant_page` is not already set ⇒ treat as abstention with a **deterministic fallback reason** (`"no eligible pages after id/layer filtering"`).
- `Answer.abstained=True` ⇒ `claims=[]` and `rendered_text=""`.
- If verification rejects **every** claim ⇒ the final `Answer` is marked `abstained=True`, `abstention_reason="no supported claims"`.

## 2. Eligible shelf — all four paths (review #1)

A shared helper builds the reduced shelf from the **post-filter eligible set**, so the model never sees a page it cannot pick:
```python
# provenance.py (next to filter_pages / known_page_ids)
def reduced_shelf(shelf_text: str, eligible_ids: set[str]) -> str:
    """Keep only shelf-index body lines whose page id is in eligible_ids (header/comment
    lines preserved). The single source of truth for 'what select is allowed to see'."""
```
Apply it in:
- **normal single-library** (`query_graph.n_select`, non-accel): build `reduced_shelf(shelf_file_text, set(candidates))`, pass as `shelf_text`.
- **accelerated single-library** (`query_graph.n_select`, accel): today it passes the embedding `reduced` shelf built from `cand_ids` but accepts only the further layer-filtered `candidates` — rebuild the reduced shelf from `candidates` (the final eligible set), not `cand_ids`.
- **normal federation** (`federation.query_one_library`): currently passes the full `shelf` file with `known_pages=candidates` — switch to `reduced_shelf` over `candidates`.
- **accelerated federation** (`federation_accel`): same — reduce to the final eligible set.

`select(...)` gains a `shelf_text` param if a path lacks it (the single-lib graph already has one); federation passes `shelf_text=reduced_shelf(...)`.

## 3. `select` may abstain + preserve fields (review #2)

- `SELECT_FRAGMENT` (prompts.py) gains: *"Return the fewest page ids that are actually relevant. If no page is relevant to the question, set `no_relevant_page` true and give a one-line reason; do not pad the list."* Trigger = **model judgment** (embedding floor deferred).
- `pipeline.select` must **preserve** the new fields when it reconstructs the filtered result (today line 119 drops them):
```python
    filtered = [p for p in result.page_ids if p in set(known_pages)]
    if result.no_relevant_page or (not filtered and result.page_ids != []) or not filtered:
        return SelectResult(page_ids=[], no_relevant_page=True,
                            abstention_reason=result.abstention_reason or "no eligible pages after id/layer filtering")
    return SelectResult(page_ids=filtered, no_relevant_page=False,
                        abstention_reason=result.abstention_reason)
```
(Net: model abstention OR everything-filtered both yield the abstention invariant with a reason.)

## 4. Graph short-circuit + complete terminal node (review #3)

`query_graph`: a conditional edge after `select` — if `no_relevant_page` or empty `page_ids` → `n_abstain`, else → `read`. The `n_abstain` node populates the **complete** state shape so trace/`--save`/consumers need no missing-field handling:
```python
def n_abstain(state):
    reason = state.get("_abstain_reason") or "no relevant page selected"
    ans = Answer(abstained=True, abstention_reason=reason)  # claims=[], rendered_text=""
    d = ans.model_dump()
    return {"pages": [], "_synth": d, "_answer": d, "rendered_text": "",
            "rejected_claims": [], "abstained": True, "abstention_reason": reason}
```
This removes q032's wasted synthesis (~321 s) — empty select never reaches `synthesize`.

## 5. `synthesize` — abstain, never absence-claims

`SYNTHESIZE_FRAGMENT` gains: *"If the supplied pages do not answer the question, return zero claims and set `abstained` true with a one-line reason. Never write a claim that merely states the answer is absent."* `synthesize` enforces the invariant on parse (if `abstained`, force `claims=[]`, `rendered_text=""`). The existing cited_pages back-fill stays.

## 6. Verify — deterministic claim↔span floor + judge + epistemic guard (review #4)

### 6a. `ground_claim` claim↔span relevance floor (deterministic)
A span may grant support **only if it is both on a cited page AND relevant to the claim**. Relevance = content-token coverage of the claim by the span:
```python
def _claim_span_coverage(claim_text, span_text) -> float:
    c = _content_tokens(claim_text); s = set(_content_tokens(span_text))
    return (sum(1 for t in c if t in s) / len(c)) if c else 0.0
```
`_content_tokens` drops stopwords + tokens ≤2 chars. **The coverage check runs INSIDE the span loop BEFORE the verbatim early-return** (entailment.py:51): a span below `RELEVANCE_FLOOR` is skipped entirely (it can ground nothing); only spans at/above the floor can yield `supported` (verbatim) or `partial` (fuzzy page-overlap).
- `RELEVANCE_FLOOR = 0.20` — **calibrated** against the committed trace: all 18 absence-shaped claims score **0.0**; all 76 legit supported claims score **≥ 0.286** (median 1.0). 0.20 sits clear of both with margin.

### 6b. `judge_claim` strengthening
The judge prompt receives the **declared evidence spans explicitly** (not only the full cited pages) and is asked to judge whether the spans actually *support* the claim. Final = `min(deterministic cap, judge)` as today.

### 6c. Epistemic-absence guard (defense-in-depth)
A guard detects **epistemic corpus-absence** phrasing specifically — `"not mentioned"`, `"no information"`, `"do(es) not contain"`, `"documents contain no"`, `"not found in the (provided )?documents"` — **NOT** generic `not/no/without` (a broad guard would wrongly reject legitimate negative facts like "X does not require Y"). A matched claim is **marked `unsupported`** (its `entailment_status`), **not removed** from `Answer.claims` — preserving claim-index alignment and auditability.

### 6d. Reject-all ⇒ abstain
`verify_entailment`/`publish`: if no claim is `supported`/`partial` (published body empty) ⇒ set `Answer.abstained=True`, `abstention_reason="no supported claims"`.

## 7. Output + federation merge (review #3)

- **Single-lib / published output:** on abstain, `rendered_text=""` (frozen `did_abstain` scorer unchanged). `abstained`/`abstention_reason` ride on the `Answer` + are written to the trace; the CLI prints `[abstained: <reason>]` to stderr.
- **Federation (`merge_answers`):** a single library abstaining must **not** abstain the whole query. The merged `Answer.abstained=True` **only when no library published a claim** (i.e. every per-library answer abstained / contributed zero supported claims); `abstention_reason` summarises (e.g. `"no library had relevant evidence"`).

## 8. Calibration vs regression evidence (review #5)

These are **separate** obligations:
- **Calibration (offline):** set `RELEVANCE_FLOOR` from the committed trace, the 22 fixed verifier labels, **explicit legitimate-negative fixtures** ("X does not require Y", "feature flags should be removed when stale"), and **short-claim/narrow-span** fixtures. Calibration proves the *deterministic verifier* separates absence from support without dropping legit (incl. negative) claims.
- **Deterministic regression:** the FakeBackend fixture/smoke suite must show no `fact_recall` regression and the new abstention behaviour (no-evidence → `abstained`, empty body, zero claims; empty select → short-circuit).
- **Fresh release ratification before merge:** the select/synthesize **prompts changed**, so model generation behaviour changed — a full traced `eval release` run is required pre-merge to confirm the gate metrics move the intended direction (abstention_recall/precision up, fact_recall not regressed) and nothing else regresses. (Calibration data cannot prove this; only a fresh run can.)

## 9. Testing (TDD, FakeBackend unless noted)
1. Contracts: invariants hold (`no_relevant_page⇒page_ids=[]`; `abstained⇒claims=[] & rendered_text=""`); `select` preserves fields + everything-filtered ⇒ abstention with fallback reason.
2. `reduced_shelf`: keeps only eligible body lines (header preserved); applied on all four paths (assert each path passes a reduced shelf — unit per path).
3. `select` abstains on model `no_relevant_page`; abstains on all-filtered.
4. Graph: `no_relevant_page`/empty → `n_abstain`; complete state shape (`pages=[]`, `_synth`/`_answer` abstained dicts, `rendered_text=""`, `rejected_claims=[]`); `synthesize` NOT called (the q032 short-circuit).
5. `synthesize`: abstain path forces `claims=[]`/`rendered_text=""`.
6. `ground_claim` relevance floor: §6.2 absence-claim (coverage 0.0) → unsupported; weakest legit (0.286) → supported; legitimate-negative fixture → supported; short-claim/narrow-span fixture → supported; floor check runs before the verbatim return (a verbatim-but-irrelevant span no longer grants support).
7. Epistemic-absence guard: corpus-absence phrasing → unsupported (kept in claims); "X does not require Y" → NOT guarded.
8. Reject-all ⇒ `abstained=True`/`"no supported claims"`.
9. Federation merge: one library abstains, another publishes → merged not abstained; all abstain → merged abstained.
10. CLI surfacing: `[abstained: …]` on stderr; trace row carries `abstained`/`abstention_reason`.
11. (pre-merge, live) fresh traced `eval release` ratification.

## Self-review notes
- **Placeholders:** none.
- **Consistency:** `did_abstain = empty body` preserved (no metric versioning); abstention is additive (new optional fields); the relevance floor is calibrated with margin (0.20 vs 0.286/0.0).
- **Scope:** one coherent contract across select/graph/synthesize/verify/federation; retrieval-score tuning (embedding floor) and scorer redesign explicitly deferred.
- **Ambiguity resolved:** relevance = claim-token coverage by span (`|C∩S|/|C|`, content tokens); floor before verbatim return; guarded claims marked unsupported (not removed); epistemic-absence patterns are specific, not generic negation; federation abstains only when no library publishes; `abstention_reason` in both contracts.
- **Risk:** the deterministic floor runs on all claims → calibration is load-bearing; mitigated by trace+labels+legit-negative+short-claim calibration and the mandatory fresh ratification before merge.

# kb-offline Slice 1 — abstention contract + verifier hardening (design)

**Issue:** EPIC #211, select/verifier-hardening roadmap. Slice 1 of 3 (Slice 2 = fuzzy id-normalize; Slice 3 = scorer evolution + gate wiring — both deferred).
**Date:** 2026-06-19
**Status:** design, pending review. (Rev 5 — round 5 semantic polish: reason None-on-success, guard covers all observed forms, finalizer reconciles success too, truthful federated reason.)
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
- `Answer.abstained=True` ⇒ `rendered_text=""` and **no published (supported/partial) claims**. The `claims` list **may** still contain `unsupported` entries (the §6c guard and §6d reject-all keep them for audit + claim-index alignment). (P1-1 — this is the unified invariant that reconciles §6c/§6d: "abstained" means *nothing was published*, not *the claim list is literally empty*. Select- and synthesize-origin abstentions happen to carry `claims=[]`; reject-all carries the rejected `unsupported` claims.)
- If verification rejects **every** claim ⇒ the final `Answer` is marked `abstained=True`, `abstention_reason="no supported claims"`.
- **`abstention_reason` is `None` on success, and a normalized non-empty single line when abstaining (P2-1):** when `abstained`/`no_relevant_page` is True it is normalized + non-empty; otherwise it is `None`. A shared `_normalize_reason(text, fallback) -> str` collapses whitespace/newlines, strips, caps length (~200 chars), and substitutes the deterministic fallback when the model returns `None`/blank/multiline — applied to both the `select` and `synthesize` model-supplied reasons before they enter the contracts, so an abstention's CLI/trace diagnostic is never empty or malformed.

## 2. Eligible shelf — all four paths (review #1)

**Reuse the existing `retrieval._reduce_shelf`** (review #1/#3) — do NOT write a naive body-line filter. `_reduce_shelf(shelf_path, page_ids: list)` already keeps **complete entry blocks** (Hash/Layer/Confidence/Terms/Facts via `build_shelf_index.extract_entry_block`) and takes an **ordered list** (so it preserves rank). Generalize it minimally to accept either a path or shelf text, and make it the single source of truth for "what `select` is allowed to see," called with the **post-filter eligible ids in their meaningful order**:
```python
# retrieval.py — generalized signature (path OR text); ordered ids preserved as-is
def reduce_shelf(shelf, ordered_ids: list[str]) -> str: ...   # rename/wrap _reduce_shelf
```
Apply it on all four paths, passing the eligible ids **in the right order** (sets would drop accel rank):
- **normal single-library** (`query_graph.n_select`, non-accel): `reduce_shelf(shelf_file, sorted(candidates))` → `shelf_text`.
- **accelerated single-library** (`query_graph.n_select`, accel): rebuild from the **final eligible set in best-first order** = `[c for c in cand_ids if c in candidates]` (today it reduces over `cand_ids` but accepts only `candidates` — the mismatch).
- **normal federation** (`federation.query_one_library`): replace the full `shelf` with `reduce_shelf(shelf, sorted(candidates))`.
- **accelerated federation** (`federation_accel`): this path is cross-library and already uses its **own** `_cross_library_shelf(fused_qids, shelf_texts)` to build qualified (`## i. handle/page_id`) blocks across libraries (P2-4). Keep/generalize `_cross_library_shelf` (it shares `extract_entry_block` with `_reduce_shelf`) and feed it the **fused eligible qualified ids** in best-first order — do NOT apply the single-library `reduce_shelf` here (it can't preserve qualified cross-library headers).

`select(...)` already accepts a `shelf_text` param (the single-lib graph uses it); single-lib federation passes `shelf_text=reduce_shelf(...)`, accel-federation continues via `_cross_library_shelf`.

## 3. `select` may abstain + preserve fields (review #2)

- `SELECT_FRAGMENT` (prompts.py) gains: *"Return the fewest page ids that are actually relevant. If no page is relevant to the question, set `no_relevant_page` true and give a one-line reason; do not pad the list."* Trigger = **model judgment** (embedding floor deferred).
- `pipeline.select` must **preserve** the new fields and **distinguish the three abstention causes** with distinct reasons (P2-3 — don't collapse them; clear the reason on success):
```python
    filtered = [p for p in result.page_ids if p in set(known_pages)]
    if result.no_relevant_page:                 # explicit model abstention
        return SelectResult(page_ids=[], no_relevant_page=True,
                            abstention_reason=_normalize_reason(result.abstention_reason, "model judged no page relevant"))
    if not result.page_ids:                     # model returned an empty selection
        return SelectResult(page_ids=[], no_relevant_page=True,
                            abstention_reason="no page selected by model")
    if not filtered:                            # model picked ids, all dropped by id/layer filter
        return SelectResult(page_ids=[], no_relevant_page=True,
                            abstention_reason="no eligible pages after id/layer filtering")
    return SelectResult(page_ids=filtered, no_relevant_page=False, abstention_reason=None)  # success: clear reason
```

## 4. Graph short-circuit + complete terminal node (review #3)

**`QueryState` gains the keys** (P1-2 — they must be declared and returned, or the selector reason is lost):
```python
class QueryState(TypedDict, total=False):
    ...                       # existing keys
    no_relevant_page: bool
    abstained: bool
    abstention_reason: Optional[str]
```
`n_select` **returns** them alongside `page_ids` (from the `SelectResult`):
```python
    res = select(...)         # SelectResult with page_ids/no_relevant_page/abstention_reason
    return {"page_ids": res.page_ids, "no_relevant_page": res.no_relevant_page,
            "abstention_reason": res.abstention_reason}
```
A **conditional edge** after `select` routes on that state — `n_abstain` if `state.get("no_relevant_page")` or `not state.get("page_ids")`, else `read`. The `n_abstain` node populates the **complete** state shape (so trace/`--save`/consumers need no missing-field handling), reading the propagated `abstention_reason`:
```python
def n_abstain(state):
    reason = state.get("abstention_reason") or "no relevant page selected"
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
A span may grant support **only if it is both on a cited page AND relevant to the claim**. Relevance = content-token coverage of the claim by the span. The tokenizer is **frozen** (P2-6 — the 0.286 boundary / 0.20 floor depend on it; an implementation must not silently change it):
```python
# entailment.py — FROZEN; changing these requires re-running calibrate_relevance_floor.py
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
(Exactly the tokenizer the calibration script used to derive the separation: **all 22 no-evidence claims score 0.0** — 18 span-less + 4 with irrelevant spans, only the 4 actually exercise relevance — vs the 76 legit supported claims at **≥0.286**.) **The coverage check runs INSIDE the span loop BEFORE the verbatim early-return** (entailment.py:51): a span below `RELEVANCE_FLOOR` is skipped entirely (it can ground nothing); only spans at/above the floor can yield `supported` (verbatim) or `partial` (fuzzy page-overlap).
- `RELEVANCE_FLOOR = 0.20` — **calibrated** against the committed trace, **but note the floor is only truly exercised by claims that HAVE a non-empty span**: of the **22** no-evidence claims, only **4** (q076/078/086/088) carry a non-empty *irrelevant* span ("DORA Metrics", coverage **0.0**) — the only natural adversarial cases; the other **18** have **no spans** (vacuously 0.0, they don't test relevance). All 76 legit supported claims (which DO have spans) score **≥ 0.286** (median 1.0). 0.20 sits clear with margin, but because only 4 natural adversarial cases exist, calibration MUST add **synthetic non-empty irrelevant-span fixtures** (see §8).

### 6b. `judge_claim` strengthening
The judge prompt receives the **declared evidence spans explicitly** (not only the full cited pages) and is asked to judge whether the spans actually *support* the claim. Final = `min(deterministic cap, judge)` as today.

### 6c. Epistemic-absence guard (defense-in-depth)
A guard detects **epistemic corpus-absence** phrasing specifically — the patterns must cover every form observed in the committed trace (P2-2): `"not mentioned"`, `"no information"`, `"do(es) not contain"`, `"documents contain no"`, `"not found in the (provided )?documents"`, **`"cannot find any information"`**, **`"not provided in the source"`**, **`"not provided in the (provided )?document"`** — all anchored to corpus/source language, **NOT** generic `not/no/without` (a broad guard would wrongly reject legitimate negative facts like "X does not require Y"). A matched claim is **marked `unsupported`** (its `entailment_status`), **not removed** from `Answer.claims` — preserving claim-index alignment and auditability. (The guard's pattern set is tested against all absence-shaped claim texts in the trace — see §9.)

### 6d. Reject-all ⇒ abstain, via a SHARED finalizer used on every path (P1-4 + P1-1)
`publish()` and `render_federated()` both return `(rendered_text, rejected_claims)` and do **not** mutate the `Answer`. The renderers differ by path (single-lib uses `publish`; federation uses `render_federated`), so the shared finalizer takes the **already-rendered body** rather than calling a renderer itself (P1 — `federation_accel` does ONE cross-library synthesize rendered via `render_federated`, not per-library `publish`):
```python
# publication.py — shared by the graph node and both federation paths
def finalize_answer(answer: Answer, rendered: str, *, abstain_reason: str) -> None:
    """Set the final rendered_text and reconcile the abstention fields BOTH ways (P2-3 — a
    non-empty render must clear any stale abstained flag). Renderer-agnostic: the caller
    renders (publish OR render_federated) and passes the body."""
    answer.rendered_text = rendered
    if not rendered.strip():
        answer.abstained = True
        answer.abstention_reason = abstain_reason
    else:                                  # something published -> definitively not abstained
        answer.abstained = False
        answer.abstention_reason = None
```
**Exact per-path order:**
- **Graph (`n_verify_publish`):** `verify_entailment` (entailment_status + §6c guard) → `rendered, rejected = publish(verified)` → `finalize_answer(verified, rendered, abstain_reason=(ans.abstention_reason if ans.abstained else "no supported claims"))` → return `rendered_text`/`rejected_claims`/`_answer`/`abstained`/`abstention_reason`.
- **Normal federation:** each `query_one_library` returns its verified Answer (the §7 no-page short-circuit returns an abstained one directly) → `merged, handle_sets = merge_answers(...)` → `rendered, rejected = render_federated(merged, handle_sets)` → `finalize_answer(merged, rendered, abstain_reason="no library produced a supported answer")`.
- **Accelerated federation (`federation_accel`):** single cross-library `synthesize` → `verify_entailment` → `canonical = canonicalize_attribution(verified)` → `rendered, rejected = render_federated(canonical, handle_sets)` → `finalize_answer(canonical, rendered, abstain_reason="no library produced a supported answer")`. (The fused-select no-page case short-circuits to an abstained Answer *before* the synthesize.)

**`canonicalize_attribution` must preserve metadata (P1):** it currently rebuilds `Answer(claims=…, rendered_text=…)` and would drop `abstained`/`abstention_reason`. Carry them through (and since finalize runs *after* canonicalize on the accel path, the canonical Answer is what gets finalized — order matters).

Net (single-library): a **synthesize-origin** abstention keeps its model reason; a **reject-all** abstention gets `"no supported claims"`. In **federation**, the merged answer's reason is always the generic `"no library produced a supported answer"` (per-library model reasons are not surfaced on the merged result — they remain on each per-library Answer for the trace).

## 7. Output + federation merge (review #3)

- **Single-lib / published output:** on abstain, `rendered_text=""` (frozen `did_abstain` scorer unchanged). `abstained`/`abstention_reason` ride on the `Answer` + are written to the trace; the CLI prints `[abstained: <reason>]` to stderr.
- **Per-library / fused-select short-circuit (P2-5):** both federation paths are procedural (no graph), so they short-circuit themselves after `select`: if `no_relevant_page` or empty `page_ids`, skip `synthesize`. Normal federation does this **per library** (an abstaining library contributes nothing to the merge); accelerated federation does it on the **single fused cross-library select** (returns an abstained merged Answer directly). Same latency/correctness win as `n_abstain`.
- **Merge & merged finalization:** a single library abstaining must **not** abstain the whole query. The merged Answer is rendered via `render_federated` and then **finalized via `finalize_answer(merged, rendered, abstain_reason="no library produced a supported answer")`** (§6d) — so it abstains **only when no library published a claim**. (Reject-all *within* a library is handled by the merge naturally: that library contributes zero published claims.)

## 8. Calibration vs regression evidence (review #5)

These are **separate** obligations:
- **Calibration (offline):** set `RELEVANCE_FLOOR` from the committed trace (note: of the **22** no-evidence claims only **4** are natural adversarial cases — non-empty irrelevant spans; the other **18** are span-less and don't test the floor), so **add synthetic non-empty irrelevant-span fixtures** (a real verbatim page string unrelated to the claim), the 22 fixed verifier labels, **explicit legitimate-negative fixtures** ("X does not require Y", "feature flags should be removed when stale"), and **short-claim/narrow-span** fixtures. The calibration is **reproducible**: the tokenizer is frozen (§6a) and a committed script (`harness/calibrate_relevance_floor.py`) regenerates the coverage distribution + the chosen floor from the trace + fixtures, so an implementation can't silently shift the 0.286 boundary. Calibration proves the *deterministic verifier* separates irrelevant-but-present spans from relevant ones without dropping legit (incl. negative / short) claims.
- **Deterministic regression:** the FakeBackend fixture/smoke suite must show no `fact_recall` regression and the new abstention behaviour: select/synth-origin no-evidence → `abstained`, empty body, **zero claims**; **reject-all** → `abstained`, empty body, claims **retained as unsupported** (not zero); empty select → short-circuit (no synthesize).
- **Fresh release ratification before merge:** the select/synthesize **prompts changed**, so model generation behaviour changed — a full traced `eval release` run is required pre-merge to confirm the gate metrics move the intended direction (abstention_recall/precision up, fact_recall not regressed) and nothing else regresses. (Calibration data cannot prove this; only a fresh run can.)

## 9. Testing (TDD, FakeBackend unless noted)
1. Contracts/invariants (split by abstention origin, per the unified invariant — P1-2):
   - `no_relevant_page=True ⇒ page_ids=[]`;
   - **select/synthesize-origin** abstention ⇒ `abstained=True`, `claims==[]`, `rendered_text==""`;
   - **reject-all** abstention ⇒ `abstained=True`, `rendered_text==""`, and `claims` **retains the unsupported entries** (NOT empty) — nothing published;
   - `select` distinguishes the three causes with distinct reasons (model-abstain / empty-output / all-filtered) and clears `abstention_reason` on success.
2. Shelf reduction: `reduce_shelf` keeps **complete eligible entry blocks** (incl. Hash/Layer/Confidence/Terms/Facts via `extract_entry_block`), not just header lines, in the given order; assert per path — non-accel = `sorted(candidates)`; accel-single = best-first order; accel-federation = `_cross_library_shelf` qualified ordered blocks (`## i. handle/page_id`).
3. `select` abstains on model `no_relevant_page`; abstains on all-filtered.
4. Graph: `no_relevant_page`/empty → `n_abstain`; complete state shape (`pages=[]`, `_synth`/`_answer` abstained dicts, `rendered_text=""`, `rejected_claims=[]`); `synthesize` NOT called (the q032 short-circuit).
5. `synthesize`: abstain path forces `claims=[]`/`rendered_text=""`.
6. `ground_claim` relevance floor: §6.2 absence-claim (coverage 0.0) → unsupported; **synthetic non-empty irrelevant-span fixture** (a real page string unrelated to the claim) → unsupported (the core regression guard — verbatim-but-irrelevant no longer grants support, and the check runs BEFORE the verbatim early-return); weakest legit (0.286) → supported; legitimate-negative fixture → supported; short-claim/narrow-span fixture → supported.
7. Epistemic-absence guard: **every** absence-shaped claim text in the committed trace → matched → unsupported (kept in claims) — incl. "not mentioned", "do(es) not contain", "no information", "cannot find any information", "not provided in the source text"; "X does not require Y" / "feature flags should be removed when stale" → NOT guarded.
8. `finalize_answer` both outcomes (P2-3): empty render → `abstained=True` + given reason; non-empty render → `abstained=False`, `abstention_reason=None` (clears a stale flag). Reject-all ⇒ `abstained=True`/`"no supported claims"`. `_normalize_reason`: blank/None/multiline → fallback single line.
9. Federation: per-library short-circuit — an abstaining/empty-select library returns an abstained Answer **without calling `synthesize`**; merge — one library abstains + another publishes → merged not abstained; all abstain → merged abstained.
10. CLI surfacing: `[abstained: …]` on stderr; trace row carries `abstained`/`abstention_reason`.
11. (pre-merge, live) fresh traced `eval release` ratification.

## Self-review notes
- **Placeholders:** none.
- **Consistency:** `did_abstain = empty body` preserved (no metric versioning); abstention is additive (new optional fields); the relevance floor is calibrated with margin (0.20 vs 0.286/0.0).
- **Scope:** one coherent contract across select/graph/synthesize/verify/federation; retrieval-score tuning (embedding floor) and scorer redesign explicitly deferred.
- **Ambiguity resolved:** relevance = claim-token coverage by span (`|C∩S|/|C|`, content tokens); floor before verbatim return; guarded claims marked unsupported (not removed); epistemic-absence patterns are specific, not generic negation; federation abstains only when no library publishes; `abstention_reason` in both contracts.
- **Risk:** the deterministic floor runs on all claims → calibration is load-bearing; mitigated by trace+labels+legit-negative+short-claim calibration and the mandatory fresh ratification before merge.

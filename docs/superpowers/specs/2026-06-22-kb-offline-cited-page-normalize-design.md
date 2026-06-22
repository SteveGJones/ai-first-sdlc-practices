# kb-offline Slice 2 — synthesize-side cited-page normalization (design)

**Issue:** EPIC #211, select/verifier-hardening roadmap. Slice 2 of 3 (Slice 1 = abstention contract, COMPLETE & RATIFIED; Slice 3 = scorer evolution + gate wiring, deferred).
**Date:** 2026-06-22
**Status:** design, approved in brainstorming — pending written-spec review.
**Grounded in:** the committed Slice 1 ratification trace `research/kb-offline-eval/trace-gemma4_12b-20260621T183228Z-run1.jsonl` (re-analyzed this session), and memory `project-kb-offline-select-hardening`.

## Goal

Recover model **citation id-corruption** that exact matching cannot — narrowly, on the synthesize side only, without reopening the anti-fabrication hole. When the model selects and reads the *right* page but then cites a corrupted version of that page's id, the claim is orphaned, dropped, and the answer abstains. A single high-confidence, logged rewrite of the corrupted id back to a page actually read repairs this. The headline case is **q035** (`sdlc-single-formm.md` → `sdlc-single-team.md`): the model read `sdlc-single-team.md`, then referenced `sdlc-single-formm.md` on **both** the claims' `cited_pages` and their `evidence_spans` — both claims went `unsupported`, and the answer abstained — a **false abstention** dragging `abstention_precision` (0.917, the failing gate margin). The fix must normalize page-id references consistently across spans *and* citations (see §3).

## Scope

**In:** a new frozen pure helper `normalize_cited_page` (`scripts/cited_page_normalize.py`); a single invocation at the `synthesize` boundary in `pipeline.py`, scoped to pages actually read for the question and to the same library/handle; a `id_rewrites` diagnostic field threaded into the per-question trace; the calibration script `research/kb-offline-eval/harness/calibrate_id_normalize.py`; full unit + integration test matrix.

**Out (deferred, by design):**
- **Select-side fuzzy recovery.** The committed trace's only remaining select-side drop is **q034** (`sdl-single-team.md`, ratio 0.973) — and recovering it would *add a non-expected page* and **regress `routing_precision`** (the drop currently masks a spurious over-selection). There is no runtime signal distinguishing a "good" select typo from a "bad" one, and zero beneficial select-side cases survive Slice 1's eligible-shelf work. Select-side is therefore explicitly excluded; a regression test pins q034's behavior as untouched.
- `first_pass_json` 0.926 — Slice 3 scorer evolution (measurement artifact; pipeline already sanitizes the trailing `<|tool_response>` sentinel and parses fine).
- Any frozen-metric redefinition / gate re-wiring — Slice 3, must be versioned.
- Embedding relevance-floor for select — Slice 3.

## Empirical calibration (from the committed trace)

The whole trace contains exactly **two** unresolved citations (cited page not in `pages_read`):

| Case | cited | best read-page | char ratio | jaccard | decision |
|------|-------|----------------|-----------|---------|----------|
| q035 | `sdlc-single-formm.md` | `sdlc-single-team.md` | **0.821** | 0.60 | recover ✅ |
| q052 | `pair-summary.md` | `pair-programming.md` | **0.588** | 0.50 | drop ⛔ (genuinely different) |

- **Algorithm:** `difflib.SequenceMatcher(None, a, b).ratio()`, character-level. Token-set Jaccard separates the two cases by only 0.10 vs char-ratio's 0.233 — char ratio is the more discriminating metric and is frozen.
- **Floor = 0.75** sits cleanly in the gap: `0.588 < 0.75 < 0.821`.
- **Cross-match safety:** across the 16-page shelf, **no two distinct ids score ≥ 0.70** char ratio — the shelf is well-separated, so a corrupted citation cannot snap to a wrong *distinct* page at this floor.
- **Perturbation:** the deepest realistic corruption bottoms out at 0.821; every other typo-style perturbation stays ≥ 0.90. The floor admits realistic typos with headroom while failing closed on genuine mismatches.
- **Read-set size:** synthesis reads 1 page in 71/74 answer cases, 2 pages in 3, never more. The runner-up margin almost never binds, but is retained for the multi-page case.

## 1. Helper — `scripts/cited_page_normalize.py`

```python
from collections.abc import Collection

def normalize_cited_page(
    cited_page: str,
    candidates: Collection[str],
    *,
    floor: float = 0.75,
    margin: float = 0.10,
) -> str | None:
    ...
```

**Contract (frozen):**
1. Return an **exact** candidate immediately (string equality; opaque, **case-sensitive** — no basename, path, or case normalization).
2. Otherwise score every candidate with `difflib.SequenceMatcher(None, cited_page, candidate).ratio()`.
3. **Deduplicate and deterministically order** candidates before scoring (sorted), so duplicates cannot create false ambiguity and the result is input-order-independent.
4. Return the single best candidate **only when** `best_score >= floor` **and** the margin test passes. When there is **exactly one distinct candidate**, the margin check is **explicitly bypassed** — recovery succeeds iff `best_score >= floor` (a single candidate has no runner-up, so it cannot be "ambiguous" regardless of how `floor`/`margin` relate). With two or more distinct candidates, require `best_score - runner_up_score >= margin`. (This avoids the contradiction that `runner_up_score = 0.0` would otherwise create when a caller passes `floor < margin`.)
5. **Boundary semantics:** comparisons are `>=` — a score exactly at `floor` and a lead exactly at `margin` are **accepted**.
6. Return `None` for empty candidates, ambiguous matches (lead `< margin`), or below-floor matches. **Decisions use the full float** (no pre-rounding); rounding happens only at trace serialization (§4).
7. Page ids are opaque strings; the helper has **no** handle/library awareness (that lives in the hook, §3). This keeps it intentionally narrow and discourages accidental select-side reuse — the filename `cited_page_normalize.py` signals the same.

## 2. Algorithm rationale

Exact-first preserves the common case at zero risk. The floor (0.75) is the calibrated separator. The margin (0.10) guards the rare 2-page read-set: with distinct shelf ids < 0.70 apart and the floor at 0.75, a corruption of one read page scores ≥ ~0.82 against its source and < 0.70 against the other, so the lead comfortably exceeds 0.10 — while genuinely ambiguous inputs drop. Fail-closed is the safe default: a missed recovery merely reproduces today's behavior (claim drops → abstain), so the asymmetry favors a conservative floor over an aggressive one.

## 3. Hook point — `synthesize` (`pipeline.py`)

`synthesize(question, pages, *, backend, max_repairs=1)` is called identically from all three paths (`graphs/query_graph.py`, `federation.py`, `federation_accel.py`); `pages` is a list of `{"page": <id>, "content": ...}` dicts where `<id>` is **bare** in the graph/per-library paths and **qualified `handle/page_id`** in the accelerated-federation path. Both `PageRef` (`library`, `page`) and `Span` (`library`, `page`, `text`) are Pydantic `BaseModel`s.

**Why both reference kinds must be normalized (the P1 lesson).** `ground_claim` (entailment.py:48) rejects a claim if **any** `cited_pages` ref is absent from the read `pages` dict, *and then* only lets a span ground when `span.page` is in the cited set, loading content via `pages.get(span.page)`. In the motivating case (q035) the corrupted id `sdlc-single-formm.md` appears on **both** `cited_pages` and `evidence_spans[].page`. Normalizing only the `PageRef` is insufficient — the span still points at the corrupted id, fails the `span.page in cited` test, and the claim stays `unsupported`. **Page-id references must be normalized consistently across evidence spans and citations.** Equally, the existing empty-`cited_pages` back-fill (`pipeline.py:169`) copies `span.page` → `cited_pages`; if spans are normalized first, the back-fill propagates the corrected id automatically.

**Procedure** — in the existing per-claim loop, after stripping `entailment_status`/`high_impact` and **before** the back-fill (and therefore before grounding):

1. Build the candidate set once per question: `read_ids = sorted({p["page"] for p in pages})` — exactly the pages read, the structural guarantee that recovery can never introduce **unread** evidence.
2. Define `handle(s) = s.split("/", 1)[0] if "/" in s else ""`. For each claim (index `ci`), normalize **both** reference lists in order `evidence_spans` then `cited_pages`. For each reference list `kind ∈ {"evidence_span", "cited_page"}`, for each reference at index `ri` with page `ref.page`:
   - If `ref.page in read_ids` → unchanged.
   - Else bucket to the ref's handle: `cands = [r for r in read_ids if handle(r) == handle(ref.page)]`. Bare ids fall in the `""` bucket (one namespace); qualified ids bucket by real handle — making **"never cross-library"** structural and test-provable.
   - `resolved = normalize_cited_page(ref.page, cands)`. On a hit (`resolved is not None and resolved != ref.page`): replace the list element via `ref.model_copy(update={"page": resolved})` (preserves all other fields, changes only `page`) and append a rewrite record (§4) to the diagnostics sink. On `None`: leave the ref untouched — the grounding/judge rejection path stays authoritative and fails closed (q052 stays dropped).
3. **Then** run the existing back-fill (`if not c.cited_pages and c.evidence_spans`), which now copies already-normalized span pages.

Because normalization completes before grounding, a recovered claim re-grounds against the correct page's spans and can legitimately reach `supported` — flipping q035 from abstain → supported and lifting `abstention_precision`. Candidates are scoped to **all pages read for the question, same handle** — never to the claim's own spans (circular: normalization precedes grounding, and the corrupted id is often *why* span linkage failed). The abstention invariant downstream is unchanged.

## 4. Trace & CLI surfacing

**CLI: no change — trace-only.** A normalized citation reads identically to one the model got right; surfacing "I fixed your typo" adds noise. This mirrors how dropped ids are diagnostics-only.

**Carrier (the P1b plumbing).** `synthesize` currently returns only `Answer`; the graph node `n_synthesize` (query_graph.py:99) stores `ans.model_dump()` under `_synth`, and `_build_question_trace` (runner.py:76) rebuilds the row from `out["_synth"]` + `out["pages"]`, re-deriving diagnostics in the harness. Rewrite records must reach the trace **without polluting the model-facing `Answer` schema**, so:

- `synthesize` gains a keyword-only **diagnostics sink**: `synthesize(question, pages, *, backend, max_repairs=1, rewrites_sink: list | None = None)`. When `rewrites_sink is not None`, it appends one record per rewritten reference. Default `None` keeps the production federation/per-library callers untouched (recovery still happens there — just unrecorded, which is correct: those paths emit no per-question trace).
- `n_synthesize` allocates a fresh `sink = []`, passes it, and returns `{"_synth": ans.model_dump(), "_id_rewrites": sink}`. `QueryState` gains an `_id_rewrites: list` channel (excluded from `Answer`).
- `_build_question_trace` reads `out.get("_id_rewrites", [])` and writes it as the per-question **`id_rewrites`** field — **always serialized**, `[]` when no rewrite occurred (alongside the existing `dropped`/`eligible_unselected`).

Each rewrite record identifies the exact reference site (P2c — q035's original corruption is on an evidence *span*, which has no citation index, so `reference_kind` + `reference_index` replace `citation_index`; and the namespace is a **handle**, not a page id):

```json
{"from": "sdlc-single-formm.md", "to": "sdlc-single-team.md",
 "score": 0.821, "handle": "",
 "candidates": ["sdlc-single-team.md"],
 "stage": "synthesize", "claim_index": 0,
 "reference_kind": "evidence_span", "reference_index": 0}
```

- `reference_kind ∈ {"evidence_span", "cited_page"}` and `reference_index` pin the exact list element; `claim_index` the claim. q035 thus emits four records (2 claims × {span, cited_page}).
- `handle` is the effective namespace bucket — `""` for bare ids, the real handle for qualified ids (never a page id).
- `score` serialized at **fixed 3-decimal precision** (decisions use the full float; only the recorded value is rounded).
- `candidates` records the same-handle candidate set actually scored.

## 5. Metric-interaction guarantee

Recoveries can only help on the current corpus:
- **q035** false abstention removed → `abstention_precision` ↑; its page was already selected/read so routing is untouched; recovered supported claims can only help `fact_recall`.
- **Select-side untouched** → `routing_precision`/`routing_recall` cannot move; **q034 pinned** by regression test.
- **q052** stays dropped (0.588 < floor) → no spurious support introduced.
- Structural invariant: a rewrite's target is always a member of the read-set, same handle → no metric measuring unread/cross-library attribution can regress.

## 6. Test matrix (TDD, `FakeBackend`, no Ollama)

**Helper unit tests (`cited_page_normalize`):**
- exact candidate returns immediately even when a closer fuzzy exists
- q035: `sdlc-single-formm.md` + `[sdlc-single-team.md]` → recovers (0.821 ≥ 0.75)
- q052 negative: `pair-summary.md` + `[pair-programming.md]` → `None` (0.588 < 0.75)
- empty candidates → `None`
- ambiguous: two candidates within `margin` → `None`
- single candidate above floor → recovers (infinite margin); below floor → `None`
- **boundary:** score exactly at `floor` accepted; lead exactly at `margin` accepted (`>=`)
- **duplicate candidates** deduplicated — cannot create false ambiguity
- case-sensitivity: `SDLC-Single-Team.md` vs `sdlc-single-team.md` is not exact and recovers only if ratio clears the floor (documents opaque-string contract)
- deterministic ordering: shuffled candidate input → identical result

**Pipeline integration tests (`synthesize`):**
- **q035 end-to-end:** a claim whose corrupted id is on **both** `cited_pages` and `evidence_spans[].page` re-grounds and reaches `supported` — proving span *and* citation are normalized consistently (the P1a regression guard); a span-only-corruption variant (empty `cited_pages`) also recovers via normalize-then-back-fill
- cross-library guard: corrupted id whose only good match is in a different handle → untouched (`None`), claim drops
- sink/trace carrier: `n_synthesize` populates `_id_rewrites`; `_build_question_trace` emits `id_rewrites` with `reference_kind`/`reference_index`/`claim_index`/`handle` and 3-dp `score`
- unresolved (q052-style) path unchanged — existing rejection authoritative
- safety invariant assertion: no rewrite ever yields a page outside the read-set, and `handle` of `to` equals `handle` of `from`
- **trace serialization includes `id_rewrites: []`** when no rewrite occurs
- production callers (`federation`, `federation_accel`) call `synthesize` without a sink and still recover (no crash, no record)
- **select-side regression:** q034-style drop remains a drop — select behavior untouched

**Calibration script** (`harness/calibrate_id_normalize.py`, analog to `calibrate_relevance_floor.py`): reloads the **frozen** helper and **recomputes** everything from committed inputs (no hardcoded 0.588/0.821 fixtures):

- **Real cases:** replay the trace's two unresolved citations and assert q035 recovers (`normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"]) == "sdlc-single-team.md"`) and q052 drops (`... is None`).
- **Perturbation sweep (the corrected cross-match test):** for each shelf id, generate typo-style perturbations and **score each perturbation against the entire shelf** via the helper's own scoring. The hard invariant (must hold for **every** perturbation): `normalize_cited_page(perturbation, full_shelf)` returns **either the true source id or `None`** — **never a different id**. This is what proves a corrupted id cannot *prefer* a wrong candidate, which canonical-id pairwise separation alone does **not** establish (P2a). Separately, for the **realistic typo tier** (single-edit perturbations — the class the floor is calibrated to catch), assert recovery actually happens: the source is the unique best, clears the floor, and leads the runner-up by ≥ margin. Deeper synthetic corruptions are allowed to fail closed (`None`); the report counts recover-to-source vs fail-closed, and **recover-to-wrong must be zero**.
- Emit the floor/margin and the score distributions so the threshold choice is reproducible, not a magic number.

## Workflow

`writing-plans` → `subagent-driven-development` (fresh implementer + 2-stage review per task) → whole-slice review → live gemma4:12b traced ratification (pre-merge evidence) → `finishing-a-development-branch` (KEEP the branch — EPIC accumulates).

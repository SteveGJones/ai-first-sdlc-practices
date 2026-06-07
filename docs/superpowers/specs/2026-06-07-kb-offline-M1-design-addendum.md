# Design Addendum: kb-offline M1 (Ollama backend) — resolving the open parts

**Issue:** #211 (EPIC) · **Branch:** `feature/211-kb-offline-langgraph` · **Date:** 2026-06-07
**Status:** Approved (brainstorming) — pending spec review, then M1a implementation plan
**Parent spec:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (M0 complete). This
addendum resolves the M1 areas the parent spec left thin; the parent's decisions still hold.

## API currency note (verified 2026-06-07, not from stale memory)

- LangGraph: `from langgraph.graph import StateGraph, START, END`; `from langgraph.types import Send`
  (map-reduce fan-out); merge parallel-worker outputs via `Annotated[list, operator.add]` state
  reducers; `builder.compile(checkpointer=...)`; invoke with `config={"configurable":{"thread_id":...}}`.
  Checkpointer: `from langgraph.checkpoint.sqlite import SqliteSaver` (`langgraph-checkpoint-sqlite`
  package, refreshed 2026-05-12).
- Ollama structured output: `langchain-ollama`'s `ChatOllama.with_structured_output()` parses into a
  model *inside the backend* — which violates our ownership boundary. We instead use the **raw
  `ollama` client with `format=<JSON-schema>`** (constrains decoding, returns a string; pipeline owns
  parse→repair→fail). Sources: docs.langchain.com/oss/python/langgraph/graph-api;
  pypi.org/project/langgraph-checkpoint-sqlite; docs.ollama.com/capabilities/structured-outputs.

## Decomposition: three sub-plans (all on feature/211, sequential)

- **M1a** — `OllamaBackend` + `[offline]` extra + structured-output ladder + `ingest_graph` + single
  ingest on `--backend ollama`.
- **M1b** — `ingest-bulk` parallel map-reduce (see "M1b concurrency contract" below): bounded `Send`
  fan-out for map AND parallel reduce-by-target.
- **M1c** — query path (`select`/`synthesize` + entailment verifier + provenance/layer + `query_graph`)
  + the eval gate vs ratified thresholds (Ollama not defaulted until it passes).

## M1a — OllamaBackend + ingest_graph

**OllamaBackend** (model calls only, per the M0 ownership boundary):
- `generate(prompt, *, schema=None) -> str`: `ollama.chat(model=self.model, messages=[{role:user,
  content:prompt}], format=schema)` when schema given (grammar-constrained JSON), returns the text
  content. No parsing/validation here — the pipeline's validate→repair→fail ladder owns that.
- `embed(texts) -> list[list[float]]`: `ollama.embed(model=embed_model, input=texts)` (used in M3).
- Default text model `gpt-oss:20b` (installed), configurable via flag/config; eval (M1c) ratifies the
  final default. Deferred `import ollama` (guarded) so the base distribution imports without the extra.
- **Local-endpoint contract (enforces the parent's offline/private claim):** the backend resolves its
  host from `OLLAMA_HOST` (default `http://localhost:11434`) and runs in **strict-offline mode by
  default** — a non-loopback host (anything but `localhost`/`127.0.0.1`/`::1`) is **rejected** at
  construction unless `--allow-remote-ollama` is explicitly passed. Offline/private is thus enforced,
  not assumed.

**ingest_graph** — built now (one node per existing pipeline stage), widened in M1b:
- `IngestState` TypedDict carrying library/run context + accumulators.
- Nodes (thin wrappers over the existing deterministic core / pipeline ops): `discover` →
  `map_extract` → `route` → `reduce_commit` → `finalize_recover`. Edges `START→discover→…→finalize→END`.
- `map_extract` in M1a iterates sources sequentially (single-ingest); **M1b** replaces the
  `discover→map_extract` edge with a conditional edge fanning out to `extract_one` workers and an
  `Annotated[list, add]` reducer collecting per-source extracts (see the concurrency contract below).

**M1b concurrency contract (resolves the unbounded-fan-out risk):**
- **Bounded map concurrency** — never dispatch all N sources at once (887 simultaneous local-model
  calls would crush the Ollama server). Bound to `--parallel <N>` (default 16, max 64, same knob as
  #208) via LangGraph's `config={"max_concurrency": N}` if honored, else by **chunking the `Send`
  batch into rounds of N** (deterministic fallback). The chosen mechanism is verified against the
  installed LangGraph version during M1b, not assumed.
- **Reduce is parallel-by-target, one writer per file** — not sequential. Group routed extracts by
  target file (the #208 `route_extracts` model), then fan out reduce workers bounded by the same
  `--parallel N`, with **exactly one writer per target file** (the M0 `commit_mutation` per-file
  fencing/CAS already enforces single-writer safety). Distinct journal `run_step` per
  `(run_id, target)`.
- **Heartbeat during long calls** — the map/reduce loops call `lock.heartbeat()` each round so a
  long-running bulk job (many slow local-model calls) does not exceed the lock TTL and get falsely
  reclaimed; the fencing token still makes any genuine reclaim safe.
- Compiled with `SqliteSaver` under `library/.kb-offline/`. **A checkpointer provides *persistence*,
  not retries** — any per-node retry is configured explicitly via a LangGraph `RetryPolicy` on the
  node (we add one only where a transient model/IO failure warrants it, e.g. the extract node), not
  implied by the checkpointer.

**Graph identity & replay (explicitly tied to the M0 run identity):**
- **`thread_id == manifest run_id`** — the graph's checkpoint thread IS the run, so a resumed run
  reattaches to its own checkpoint.
- **One canonical step-ID formula:** `step_id(run_id, stage, item) = f"{run_id}:{stage}:{item}"`
  (stage ∈ {`extract`, `reduce`, …}; item = source slug for `extract`, target filename for `reduce`).
  This supersedes M0's stage-less `f"{run_id}-{target}"` — **M1a updates the existing
  `commit_mutation` caller to this formula** (`stage="reduce"`, `item=target_file`) so there is a
  single scheme everywhere. Because the formula is pure-deterministic from `(run_id, stage, item)`, a
  replayed `reduce_commit` node passes the **identical** step ID, keeping journal records idempotent
  (no duplicate/clobbered records on replay).
- **Manifest/journal recovery runs BEFORE graph continuation:** on resume, `recover(library)` replays
  the journal (reindex committed/staged-existing, surface conflicts) first; only then does the graph
  continue. The manifest + journal remain the **resume source of truth**; the checkpointer is the
  in-graph convenience the parent spec designated, never the authority. Fencing, CAS, lifecycle are
  unchanged — graph nodes call the same `commit_mutation`/`recover`.

**M1a retry policy (concrete):**
- **Retryable (transport/transient only):** Ollama connection errors, timeouts, 5xx/`ResponseError`
  from the endpoint. A LangGraph `RetryPolicy(max_attempts=3, backoff_factor=2.0, initial_interval≈1s,
  jitter=True)` is attached to the **read-only model-call nodes** (`extract`; in M1c also
  `select`/`synthesize`/judge).
- **Non-retryable (content):** malformed/schema-invalid model output is **not** a RetryPolicy concern —
  it's handled by the pipeline's bounded validate→repair→fail ladder; after the repair budget it is
  **terminal**, recorded as `mark_source_failed`/`mark_target_failed` in the manifest (graceful partial
  failure). No RetryPolicy wraps validation failure.
- **No retry around the mutation commit:** the `reduce_commit` node carries **no `RetryPolicy`**. Its
  durability/idempotency come from the journal + fencing + CAS; if it re-executes on resume it reuses
  the **identical** canonical step ID (above), so the journal stays idempotent. (A retry that generated
  a fresh step ID would be unsafe — hence none.)
- Terminal failures (retries exhausted, or repair budget exhausted) are recorded in the manifest and
  surfaced in the run summary.

## M1c — query path + entailment verifier

New pipeline operations (backend for the model step; pipeline owns validation):
- `select(question, shelf_index) -> SelectResult(page_ids)` — librarian reasoning over the shelf-index
  (curated-wiki retrieval; embeddings are M3, off by default). Unknown returned ids dropped + logged.
- `synthesize(question, pages) -> Answer` — emits `claims[]` each with `cited_pages` + `evidence_spans`;
  **never sets `entailment_status`**. `rendered_text` derived from claims.

Entailment verifier — `verify_entailment(answer, pages) -> Answer` — *assigns* `entailment_status`:
1. **Grounding floor (deterministic, 100% safety floor):** each `evidence_span` must appear on its
   `cited_page` under a normalized/fuzzy match (case-/whitespace-insensitive substring). A claim whose
   spans aren't grounded → `unsupported`; a `cited_page` not in the read set is a hard reject. This is
   the parent spec's "citation reference validity = 100%".
2. **Judge grade (LLM, per grounded claim):** a `backend.generate` judge call ("does this span support
   this claim? supported|partial|unsupported") sets the grade. The judge is a backend call (Ollama or
   Anthropic) → eval-measurable, model-swappable. Model-supplied status is always discarded.

**`high_impact` is verifier/policy-owned, never model-controlled (resolves the gaming risk).** If
synthesis set `high_impact`, it could mark everything low-impact and make "zero unsupported
high-impact" meaningless. So a **deterministic classifier in the verifier assigns `high_impact`**
(any model-supplied value is discarded): a claim is high-impact if it contains a number/statistic/unit,
a recommendation/modal directive ("should", "must", "recommend"), or safety/compliance/regulatory
terms. Conservative bias — when uncertain, classify high-impact.

**Query output publication policy (resolves "unsupported claims could still be published").** The
verifier's status drives what the answer actually contains — not merely "surfaced":
- `supported` → **published** in the answer.
- `partial` → published **only with an explicit caveat marker** (e.g. "(partially supported)"); never
  silently mixed with supported claims.
- `unsupported` → **excluded from the answer body** and listed in a separate `rejected_claims` report
  with the reason. A high-impact `unsupported` claim additionally flags the whole answer as degraded.
- `promote` (M2) requires **all published claims `supported`** (no `partial`).
This makes the published answer's support guarantee enforceable, not advisory.

**Provenance/layer (#4):** `select`/`synthesize` honor `--layer` (filter candidate pages by frontmatter
`layer`) and `--min-confidence` (drop weak pages); synthesis weights higher-confidence pages and
surfaces confidence. `query_graph` = `select → read → synthesize → verify_entailment` (single-library
in M1c; federation fan-out is a later milestone). CLI: `kb-offline query "<q>" [--layer] [--min-confidence]`.

## Eval gate (M1c exit — the M1 release criterion)

Grow the M0 harness skeleton into the **frozen release suite**: 75–100 labelled questions (≥20
no-evidence) over a fixed library fixture, **pinned model+config, run 3×**. Wire the metric functions
to real pipeline runs on both backends; score against the ratified thresholds:
- Safety floors (deterministic, must = 100%): invalid-mutation rejection, citation grounding validity,
  post-repair JSON validity.
- **Entailment is TWO distinct metrics (do not conflate):**
  - **Verifier accuracy** — precision/recall of `verify_entailment` against a labelled supported/
    partial/unsupported set (does the verifier classify correctly?). Gate: precision ≥98%, recall ≥95%.
  - **Clean-published-claim support rate** — of claims published **without a caveat** (the
    `supported` set; `partial` claims carry a caveat and are excluded from this set, `unsupported` are
    not published at all), the fraction that are `supported`. Gate: **100%** — tautological-but-
    enforced by the publication policy: only `supported` claims are published uncaveated. This is the
    answer-faithfulness guarantee (distinct from verifier accuracy above). Caveated `partial` claims
    are tracked/reported separately, not counted as clean support.
- Other model-quality gates: first-pass JSON ≥95%; fact recall ≥85% (macro); routing ≥90%/≥80%;
  abstention ≥95%/≥90%.
- Cloud-vs-local agreement = secondary drift report only.
`kb-offline eval release` emits the comparison report. **Ollama becomes the default backend only after
the chosen model clears BOTH the verifier-accuracy and the model-quality bars**; otherwise report the
gap and keep Anthropic default / pull a stronger model.

## Dependency / packaging delta

- `[offline]` extra = **`langgraph`, `langgraph-checkpoint-sqlite`, `ollama`** (drop `langchain-ollama`
  — the raw `ollama` client keeps the model-call seam thin). M3 adds the embeddings dep
  (`sqlite-vec` or numpy).
- All offline imports stay guarded so the base distribution imports without the extra (M0 pattern).

## Testing

- Graph logic driven by `FakeBackend` (no model calls): `ingest_graph`/`query_graph` deterministic;
  `Send` fan-out tested with a multi-source fixture + the reducer.
- Grounding floor tested adversarially (fabricated span / fabricated cited page → reject).
- Live Ollama smoke behind the skip-if-absent marker (now runnable — Ollama v0.30.6 present with
  `gpt-oss:20b`, `nomic-embed-text`).
- **Eval execution is two separate things (not contradictory):**
  - **CI** runs only the *scorer correctness* tests (the metric functions on tiny synthetic inputs)
    and the smoke fixture — fast, no real models, no thresholds gated.
  - **The gated release run** is a deliberate, manual/CI-dispatched step: real pinned backends, the
    75–100-question frozen suite, run 3×, producing a **persisted report that is required to pass
    M1c** (and to flip the default to Ollama). CI never runs the pinned 3× model evaluation.
- All runs use the project `.venv` (`.venv/bin/python`).

## Decisions log (M1 delta)

1. Entailment verifier = **deterministic grounding floor + per-claim LLM-judge grade**; model never
   sets `entailment_status`.
2. **Three sub-plans** M1a/M1b/M1c.
3. `ingest_graph` introduced in **M1a** (one-node-per-stage + SqliteSaver), widened to `Send` fan-out
   in M1b; manifest+journal stay the resume authority, checkpointer is in-graph convenience only.
4. `OllamaBackend` uses the **raw `ollama` client + `format=schema`** (not `langchain-ollama`);
   `[offline]` extra = langgraph + langgraph-checkpoint-sqlite + ollama.
5. Default model `gpt-oss:20b` (configurable), ratified by the M1c eval gate before Ollama is defaulted.
6. Query path single-library in M1c; federation fan-out deferred to a later milestone.
7. **Query output publication policy**: `supported` published; `partial` published only with an
   explicit caveat; `unsupported` excluded + reported in `rejected_claims`; `promote` requires all
   published claims `supported`. Published-claim support guarantee is enforced, not advisory.
8. **Entailment gate is two metrics**: verifier accuracy (precision ≥98% / recall ≥95% vs labelled)
   AND **clean-published-claim support rate** (=100%; the uncaveated/`supported` set — `partial` is
   caveated and excluded, `unsupported` unpublished). Not conflated.
9. **`high_impact` is verifier/policy-assigned** by a deterministic classifier (numbers/units,
   recommendation/modal, safety/compliance terms; conservative bias to high-impact); never trusted
   from synthesis output — so "zero unsupported high-impact" can't be gamed.
10. **Graph identity tied to M0 run identity**: `thread_id == manifest run_id`; **one canonical step
    ID `f"{run_id}:{stage}:{item}"`** (supersedes M0's stage-less form; M1a updates the caller);
    replayed `reduce_commit` reuses the identical step ID; `recover()` runs before graph continuation;
    manifest+journal stay the resume authority. A checkpointer is persistence, not retries.
14. **M1a retry policy**: `RetryPolicy(max_attempts=3, backoff)` on read-only model-call nodes for
    transport/transient errors only; content/validation failures go through the bounded
    validate→repair→fail ladder → terminal `mark_*_failed`; **no RetryPolicy on `reduce_commit`**
    (idempotency from journal+fencing+CAS; re-execution reuses the identical step ID).
11. **M1b bounded concurrency**: map fan-out bounded by `--parallel N` (default 16, max 64) via
    `max_concurrency` or chunked `Send` rounds; **reduce is parallel-by-target, one writer per file**
    (#208 model + M0 per-file fencing/CAS); `lock.heartbeat()` each round during long runs.
12. **Local-endpoint contract**: `OllamaBackend` defaults to `localhost`, strict-offline by default,
    rejects non-loopback hosts unless `--allow-remote-ollama` — enforces the offline/private claim.
13. **Eval execution split**: CI = scorer-correctness + smoke fixture only (no gated thresholds);
    gated release run = real pinned backends, 3×, persisted report required to pass M1c.

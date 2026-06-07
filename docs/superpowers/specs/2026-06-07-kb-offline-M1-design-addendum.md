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
- **M1b** — `ingest-bulk` parallel map-reduce: widen `ingest_graph`'s map node to `Send` fan-out.
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

**ingest_graph** — built now (one node per existing pipeline stage), widened in M1b:
- `IngestState` TypedDict carrying library/run context + accumulators.
- Nodes (thin wrappers over the existing deterministic core / pipeline ops): `discover` →
  `map_extract` → `route` → `reduce_commit` → `finalize_recover`. Edges `START→discover→…→finalize→END`.
- `map_extract` in M1a iterates sources sequentially (single-ingest); **M1b** replaces the
  `discover→map_extract` edge with a conditional edge returning `[Send("extract_one", {...})]` and an
  `Annotated[list, add]` reducer collecting per-source extracts.
- Compiled with `SqliteSaver` under `library/.kb-offline/` for in-graph retry only.
- **The manifest + journal remain the resume source of truth** (M0 contract). The checkpointer is the
  in-graph convenience the parent spec designated, never the resume authority. Run lifecycle, fencing,
  CAS, and recovery are unchanged — graph nodes call the same `commit_mutation`/`recover`.

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
- High-impact claims with non-`supported` status are surfaced; `promote` (M2) requires all-`supported`.

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
- Model-quality gate: citation entailment ≥98% + zero unsupported high-impact; first-pass JSON ≥95%;
  fact recall ≥85%; routing ≥90%/≥80%; abstention ≥95%/≥90%.
- Cloud-vs-local agreement = secondary drift report only.
`kb-offline eval release` emits the comparison report. **Ollama becomes the default backend only after
the chosen model clears the model-quality bar**; otherwise report the gap and keep Anthropic default /
pull a stronger model.

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
- Eval release suite runs in CI on the fixture; the full 3×-pinned run is a deliberate manual/gated step.
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

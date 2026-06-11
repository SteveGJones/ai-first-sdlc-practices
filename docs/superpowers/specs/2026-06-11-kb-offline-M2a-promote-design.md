# kb-offline M2a — compounding `promote` design (the LLM-wiki loop)

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph` (one branch, M0–M4 accumulate). **Builds on:** M1c-1 query path (`select → read → synthesize → verify_entailment → publish`, claim-structured `Answer` with verifier-assigned `entailment_status`/`high_impact`) and M0 mutation machinery (`MutationProposal`, `validate_proposal`, `commit_mutation` WAL+fencing+CAS, `recover`, `RunRegistry`, `build_shelf_index`). **Parent:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (wiki enhancement #1 "Compounding loop"; operation contract `promote(verified_answer) -> MutationProposal`; "verified answer" definition).

**Goal:** Close the LLM-wiki compounding loop for the offline kit — let an operator file a verified query answer back into the library as a new (or extended) curated page, through the same deterministic mutation machinery that governs ingest.

**Decomposition note:** M2 is three independent subsystems — **M2a (compounding promote, this spec)**, M2b (federation query), M2c (federation-aware lint). Each gets its own spec → plan → implementation cycle. M2a is single-library and self-contained; it does not depend on M2b/M2c.

---

## Decisions (from brainstorm)

1. **Answer persistence is opt-in (`query --save`).** Normal queries stay read-only; `--save` persists the `Answer`+provenance to `.kb-offline/answers/<ref>.json` and prints `<ref>`. `ref` = short content hash of question+rendered_text (deterministic — no clock dependency).
2. **Promote operates on the `supported` subset.** It builds the page from only the `supported` claims (the uncaveated set), silently dropping `partial`/`unsupported` and recording them for audit/provenance. Refuses only if there are **zero** supported claims.
3. **Operator-directed target, model-drafted body.** `promote <ref> --new <slug> | --into <page>` (default `--new`, slug from the question). The backend drafts only the page **body prose**; the **frontmatter is set deterministically** (never trusted from the model), consistent with M1c's verifier-owned-fields principle.
4. **Promoted pages are marked derived, with conservative confidence.** Frontmatter: `provenance: promoted`, `derived_from: <ref>`, `sources: [cited pages]`; **confidence = min(source-page confidences)** (override `--confidence`); layer = `--layer` or modal source-page layer.
5. **`promote_graph` (LangGraph), mirroring `ingest_graph`** — for run-lifecycle/journal/checkpoint **traceability consistency** across all mutation ops. Reuses M0 lock/fencing/CAS/journal/recover verbatim; no new write path.

---

## §1 Answer persistence (`scripts/answers.py` + `query --save`)

New module `scripts/answers.py`:

```python
class SavedAnswer(BaseModel):
    ref: str
    question: str
    libraries: list[str] = Field(default_factory=list)   # ["local"] in M2a (federation = M2b)
    page_ids: list[str] = Field(default_factory=list)     # pages the answer read
    answer: Answer                                        # full claims incl. entailment_status/high_impact
    rendered_text: str

def compute_ref(question: str, rendered_text: str) -> str   # short stable content hash (resume.content_hash-style)
def save_answer(library_path, question, answer: Answer, *, libraries, page_ids) -> str  # writes .kb-offline/answers/<ref>.json, returns ref
def load_answer(library_path, ref: str) -> SavedAnswer       # raises a clear error if absent
```

- Storage: `.kb-offline/answers/<ref>.json` via `durability.atomic_write_text` (fsync). The directory is created on first save.
- `query --save`: after `verify_entailment` runs in the query path, the CLI persists the verified `Answer` and prints `saved: <ref>`. Implemented in the CLI `_cmd_query` (so the read-only `query_graph` itself stays unchanged); the CLI already holds the graph output (`rendered_text`, `page_ids`) and can re-validate or carry the verified `Answer`. To get the full verified `Answer` (not just `rendered_text`), the query graph's `verify_publish` node will additionally return the verified `Answer` dict in its output (`_answer`) so `--save` can persist it; this is an additive output key, the read-only guarantee is unchanged (no library writes on a normal query).

## §2 `pipeline.promote` (supported-subset, model drafts body)

```python
def promote(saved: SavedAnswer, *, target_file, action, existing_content, backend, max_repairs: int = 1) -> str:
    """Draft coherent page BODY PROSE from the answer's `supported` claims only. Returns the
    body string (the graph assembles the typed MutationProposal with deterministic frontmatter).
    Raises ValueError if the saved answer has zero supported claims."""
```

- Selects `supported` claims: `[c for c in saved.answer.claims if c.entailment_status == EntailmentStatus.supported]`. Zero → `ValueError("promote: no supported claims to promote")`.
- Prompt = new canonical `PROMPTS.PROMOTE_FRAGMENT` + the question + the supported claims (text + cited pages) + (for `extend`) the existing page content, asking for a coherent, cited body. Same validate→repair→fail ladder as `reduce_to_proposal`.
- The model returns **body prose only** (not frontmatter, not citations metadata) — a thin structured output `{ "body": str }` validated against a tiny schema. Frontmatter/citations are assembled deterministically in §3.
- `PROMOTE_FRAGMENT` added to `prompts.py` and covered by `check-prompt-parity.py` (the agent-side promote skill, if any, carries the managed block; for M2a no agent `.md` change is required, so parity simply tracks the new constant).

## §3 `promote_graph` (`scripts/graphs/promote_graph.py`, mirrors `ingest_graph`)

Read-then-mutate graph, compiled with `SqliteSaver` (checkpoint) like ingest; `thread_id == promote run_id`:

- **`n_load`** — `load_answer(ref)`; split claims into `supported` vs `dropped`; resolve source pages = the distinct `cited_pages[].page` across supported claims; read each source page's frontmatter (`provenance.page_frontmatter`) to compute **confidence = min(source confidences)** and **modal layer**. If zero supported → set `failed` and route to finalize (graceful).
- **`n_draft`** — call `pipeline.promote(...)` for the body; assemble the typed `MutationProposal`:
  - `target_file` = `<slug>.md` (`--new`) or the existing page (`--into`); `action` = create|extend.
  - `frontmatter` = `{layer: <--layer or modal>, confidence: <--confidence or min(sources)>, sources: [source pages], provenance: "promoted", derived_from: <ref>}`.
  - `body` = model draft; `citations` = the source pages (deterministic, from the supported claims — NOT model-invented); `cross_refs` = [].
- **`n_commit`** — `validate_proposal` then `commit_mutation` (lock + fencing token + CAS + journal). No `RetryPolicy` on commit (idempotent via journal+fencing, same as ingest). A failing proposal → `mark_*_failed`.
- **`n_finalize`** — `recover(library_path)` (reindex staged) + `build_shelf_index` rebuild; append an **audit event** (`audit.log_event`): `{op: "promote", ref, target_file, action, promoted: N, dropped: M, dropped_ids: [...]}`. Surface committed/rejected/conflict counts like ingest.

`RunRegistry` lifecycle as in ingest (`start_run`/`set_state` completed|failed). The CLI releases the lock + marks the run failed on any graph error (the ingest pattern, reused).

## §4 CLI `promote` + derived frontmatter

```
kb-offline promote <ref> [--new <slug> | --into <page>] [--library PATH] [--layer L]
                         [--confidence low|medium|high] [--backend ...] [--timestamp <UTC>]
```

- `--new`/`--into` mutually exclusive; default `--new` with a slug derived from the question (lowercased, hyphenated, deduped against existing pages). `--into <page>` requires the page to exist (extend).
- `--timestamp` required (caller-supplied; no clock in code — same convention as ingest/eval-release) → the promote run_id.
- Prints: the committed page path, frontmatter summary, and `promoted N claims, dropped M (partial/unsupported)`; exit non-zero if the proposal was rejected/zero-supported.

## §5 Testing + eval-gate slice

- **`answers.py`**: save→load round-trip; `compute_ref` stable/deterministic; load of missing ref errors clearly.
- **`pipeline.promote`**: drafts body from supported claims only; zero-supported → ValueError; repair ladder on invalid JSON.
- **`promote_graph`** (FakeBackend): create end-to-end (page written, frontmatter `provenance: promoted`/`derived_from`/min-confidence/modal-layer correct, shelf rebuilt, audit event logged); extend into an existing page; zero-supported answer → graceful failed run, no write.
- **Promotion-mutation-validation safety floor (the M2a eval-gate slice):** a promote whose assembled proposal cites a page absent from the library, or targets a path outside the library, is **rejected by `validate_proposal`** — promote can never commit an ungrounded/invalid mutation. (Citations are assembled deterministically from the supported claims' cited pages, which were themselves grounded by the verifier — so this is belt-and-braces, tested adversarially.)
- **Live Ollama promote smoke** behind the `_ollama_ready()` skip guard: `query --save` then `promote <ref>` against the smoke library, asserting a grounded page is written.
- CI keeps the execution split: all gated tests use FakeBackend; no real model in CI.

## Components & isolation

| File | Responsibility |
|---|---|
| `scripts/answers.py` (new) | `SavedAnswer`, `compute_ref`, `save_answer`, `load_answer` |
| `scripts/pipeline.py` (modify) | add `promote(...)` body-drafting op |
| `scripts/prompts.py` (modify) | add `PROMOTE_FRAGMENT` |
| `scripts/graphs/query_graph.py` (modify) | `verify_publish` additionally returns the verified `Answer` dict (`_answer`) for `--save` |
| `scripts/graphs/promote_graph.py` (new) | `build_promote_graph` (load→draft→commit→finalize), mirrors ingest |
| `scripts/kb_offline_cli.py` (modify) | `query --save`; new `promote` subcommand |
| Tests | `test_kb_offline_answers.py`, `test_kb_offline_promote_pipeline.py`, `test_kb_offline_promote_graph.py`, append to `test_kb_offline_cli.py` + `test_kb_offline_ollama_smoke.py` |

## Out of scope (correctly deferred)

- Federation: multi-library query/promote, per-claim source-library attribution merge, priming, cross-library audit (M2b).
- Federation-aware lint / cross-library conflict + staleness (M2c).
- Embedding accelerator (M3).
- Auto-promotion / unattended compounding — promote stays a deliberate operator action.

## Decisions log (M2a delta)

1. Answer persistence opt-in via `query --save`; `ref` = content hash (no clock).
2. Promote the `supported` subset; refuse only on zero supported; record dropped claims.
3. Operator-directed target (`--new`/`--into`, default `--new`); model drafts body only; frontmatter deterministic.
4. Promoted page marked `provenance: promoted` + `derived_from`; confidence = min(source confidences); layer = `--layer` or modal.
5. `promote_graph` (LangGraph) mirroring ingest for traceability consistency; reuses M0 lock/fencing/CAS/journal/recover.
6. M2a eval-gate slice = promotion-mutation-validation safety floor (validator rejects ungrounded/out-of-library proposals); federation-attribution eval deferred to M2b.

# kb-offline M2b — federation query design (multi-library fan-out + attribution)

**Issue:** #211 (EPIC kb-offline); relates to #209 (per-invocation `--library`/`--libraries`). **Branch:** `feature/211-kb-offline-langgraph` (one branch, M0–M4 accumulate). **Builds on:** M1c-1 query path (`select → read → synthesize → verify_entailment → publish`), M2a (`SavedAnswer.libraries` field already reserved), the merged #164 federation primitives (`registry.resolve_dispatch_list`, `priming.build_priming_bundle`, `audit.log_event`/`AuditEvent`), and `bulk_ingest_graph`'s read-only `Send` fan-out pattern. **Parent:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (wiki enhancement #2 "Federation query layer").

**Goal:** Answer a question across multiple federated libraries in the offline kit — fan out the M1c-1 query path per library, prime non-local libraries with local vocabulary, and merge per-library *verified* answers into one result with per-claim source-library attribution and a cross-library audit trail.

**Decomposition note:** M2 = M2a (promote, DONE) / **M2b (federation query, this spec)** / M2c (federation-aware lint). M2b is read-only and self-contained; M2c depends on it.

---

## Decisions (from brainstorm)

1. **Library resolution reuses `resolve_dispatch_list`.** Load the global registry from its standard path, build an ad-hoc `ProjectActivation(activated_sources=<--libraries handles>)`, resolve against the registry + local path. Identical federation behavior to the in-agent skills (path-denylist validation, remote-agent skip, implicit-`local` prepend, warnings).
2. **Merge = concatenate + attribute + dedupe-identical.** Each claim tagged with its source-library handle; claims with identical normalized text dedupe to one entry whose source-handle list is the union. No ranking (RRF deferred to M3).
3. **Priming included, threaded into `select`.** `select` gains an optional `priming` param; non-local libraries' selection is biased toward local vocabulary; the local library is not primed.
4. **Parallel `Send` fan-out** (`federation_query_graph`), read-only — no locks/journal/fencing.
5. **Verify per-library before merge** — each library's claims grounded against that library's own pages; the merge operates on already-verified answers (no cross-library page-name collision).
6. **New audit event type `cross_library_query`** added to `audit.VALID_EVENT_TYPES`; one event per library access (mirrors the M2a `answer_promotion` addition — the existing set has no successful-cross-library-query type).

---

## §1 Library resolution (`--libraries`)

CLI helper in `kb_offline_cli.py`:
```python
def _resolve_libraries(local_lib: Path, handles: list[str]) -> tuple[list[tuple[str, Path]], list[str]]:
    """Resolve --libraries handles to (handle, path) pairs via the #164 registry.
    Returns (resolved, warnings). Implicit `local` is prepended by resolve_dispatch_list."""
    from .registry import load_global_registry, ProjectActivation, resolve_dispatch_list
    registry = load_global_registry(<standard global-registry path>)
    activation = ProjectActivation(activated_sources=handles)
    dispatch = resolve_dispatch_list(registry, activation, local_lib)
    resolved = [(s.name, Path(s.path)) for s in dispatch.sources]
    return resolved, dispatch.warnings
```
- The standard global-registry path is whatever `registry.py`/the in-agent skills already use (confirm during planning — likely `~/.config/...` or a project-relative location; reuse the existing constant, do not invent a new path).
- `--library` always names the **local** library root (default `library`), exactly as today. `--libraries a,b,c` is an additional flag: when **absent**, `query` runs the unchanged M1c-1 single-library read-only path; when **present**, it federates the local library with the named external handles (the resolver prepends implicit `local` for the `--library` root). So the two flags are complementary, not mutually exclusive.
- `is_empty_error` (no local + no externals resolved) → exit with the kb-init recommendation; warnings always surfaced to the operator.

## §2 Priming (`pipeline.select` optional param)

`pipeline.select(question, shelf_index_path, *, backend, known_pages, max_repairs=1, priming=None)`:
- New optional `priming: PrimingBundle | None`. When provided, the SELECT prompt gets a prepended PRIMING block built from `priming.local_kb_config_excerpt` + `priming.local_shelf_index_terms` (a compact "interpret/term-bias toward this local vocabulary" instruction). When `None`, the prompt is byte-identical to today (backward-compatible — existing single-library query + eval are unaffected).
- The federation worker builds `bundle = build_priming_bundle(question, <local project dir>)` once and passes it to `select` for **non-local** libraries only; the local library's `select` gets `priming=None`.

## §3 Per-library worker (`federation.query_one_library`)

```python
def query_one_library(library_path, question, *, backend, priming, layer=None, min_confidence=None) -> tuple[Answer, list[str]]:
    """Run the M1c-1 query pipeline for ONE library: filter candidate pages (provenance),
    select (primed iff priming given) -> read -> synthesize -> verify_entailment. Returns the
    VERIFIED Answer + the page_ids read. Verification is against THIS library's pages only."""
```
- Reuses `provenance.filter_pages`, `pipeline.select`, `pipeline.synthesize`, `entailment.verify_entailment` directly (the same ops `query_graph` wires). No new model/verification logic.
- Returns the verified `Answer` (NOT yet published) so the merge can attribute before publication.

## §4 Merge + attribution (`scripts/federation.py`)

```python
def merge_answers(per_library: list[tuple[str, Answer]]) -> Answer:
    """Merge per-(handle, verified Answer) into one Answer. Each claim's cited_pages get
    library=<handle> (replacing the per-library 'local'); claims with identical normalized
    text dedupe to one entry whose attributed-handle set is the union. Distinct claims kept,
    grouped by first-seen source. entailment_status/high_impact preserved from per-library
    verification (the merge never re-grades)."""

def render_federated(merged: Answer, handle_sets: dict[str, list[str]]) -> tuple[str, list[dict]]:
    """Apply the publication policy (supported published / partial caveated / unsupported
    excluded) with a per-claim source-attribution suffix, e.g. 'claim text  [dora-corp, acme-kb]'.
    Returns (rendered_text, rejected_claims)."""
```
- Normalized-text dedupe key = `" ".join(text.lower().split())` (same normalization as the verifier/publication).
- Attribution lives on the claim (`cited_pages[].library` = handle) AND in the rendered suffix; `handle_sets` maps claim → its union of source handles for rendering.
- Reuses `publication.publish`'s supported/partial/unsupported policy; `render_federated` is the attribution-decorated variant (factor the shared policy so the two don't drift).

## §5 `federation_query_graph` (parallel `Send` fan-out) + audit

`scripts/graphs/federation_query_graph.py`, read-only (mirrors `bulk_ingest_graph`'s offline-guard + `Send` pattern; MemorySaver/SqliteSaver; NO lock/journal/fencing):
- **`n_resolve`** — resolve libraries (passed in as `(handle, path)` list from the CLI), build the priming bundle from the local project dir.
- **`Send` fan-out** — one `n_query_one` worker per library (bounded by `max_concurrency`); each calls `query_one_library` (primed iff non-local) → returns `{handle, answer_dict, page_ids}` accumulated via a list reducer; each worker also appends a `cross_library_query` `AuditEvent` (`source_handle=handle`, truncated `query`, `reason="federated query"`) to `<local>/.kb-offline/audit.log`.
- **`n_merge_publish`** — `merge_answers` + `render_federated` → `{rendered_text, rejected_claims, _answer (merged), queried, deduped, warnings}`.
- Add `"cross_library_query"` to `audit.VALID_EVENT_TYPES` (+ a test asserting it's valid; the existing set has no successful-cross-library-access type).

## §6 CLI + testing

- `query "<q>" --libraries a,b,c [--library <local root>] [--layer] [--min-confidence] [--backend] [--save]`. `--libraries` present → federated path (build `federation_query_graph`, invoke with resolved libraries); absent → unchanged single-library `query_graph`.
- Output: the merged attributed answer; dispatch warnings; a summary line `queried N libraries (M claims, K deduped)`.
- **`--save` interplay**: a federated answer is saveable; `SavedAnswer.libraries` carries the **real resolved handles** (the field M2a reserved, currently hardcoded `["local"]`). Promote of a federated answer is a later concern (note for M2c / a follow-up) — for M2b, federated `--save` simply records all source handles.
- **Tests (FakeBackend):** `_resolve_libraries` incl. skip/warning + implicit-local paths; `select` priming prepends only when given (and byte-identical when not); `query_one_library` verifies against its own pages; `merge_answers` dedupe-and-union-attribution + distinct-claims-kept; `render_federated` attribution suffix + publication policy; `federation_query_graph` end-to-end across 2 libraries (FakeBackend routing per-library); one `cross_library_query` audit event per library; CLI `--libraries` dispatch + summary line. **Live multi-library Ollama smoke** behind the `_ollama_ready()` skip guard (two tiny libraries). CI keeps the execution split: all gated tests FakeBackend; live smoke skips in CI.

## Components & isolation

| File | Responsibility |
|---|---|
| `scripts/pipeline.py` (modify) | `select` gains optional `priming` param (backward-compatible) |
| `scripts/audit.py` (modify) | add `cross_library_query` to `VALID_EVENT_TYPES` |
| `scripts/federation.py` (new) | `query_one_library`, `merge_answers`, `render_federated` |
| `scripts/graphs/federation_query_graph.py` (new) | `build_federation_query_graph` (resolve → Send → merge_publish), read-only |
| `scripts/kb_offline_cli.py` (modify) | `_resolve_libraries`; `query --libraries` federated dispatch + `--save` real handles |
| `scripts/publication.py` (modify) | factor the supported/partial/unsupported policy so `render_federated` reuses it (no drift) |
| Tests | `test_kb_offline_federation.py`, `test_kb_offline_federation_graph.py`, append to `test_kb_offline_query_pipeline.py` (priming), `test_kb_offline_cli.py`, `test_kb_offline_ollama_smoke.py`, `test_*audit*` (new event type) |

## Out of scope (correctly deferred)

- RRF / embedding-based cross-library score fusion (M3).
- Federation-aware lint — cross-library conflicting-value + staleness (M2c).
- Promote of a federated answer into a specific library (later; M2b just records the handles on `--save`).
- Remote-agent library types (registry already skips them; future EPIC).

## Decisions log (M2b delta)

1. `--libraries` resolution reuses `resolve_dispatch_list` (registry + ad-hoc ProjectActivation); warnings + is_empty_error surfaced.
2. Merge = concatenate + attribute + dedupe-identical (union source handles); no ranking.
3. Priming included via optional `select(priming=...)`; non-local libraries primed, local not.
4. Parallel `Send` fan-out, read-only `federation_query_graph`.
5. Verify per-library before merge (no cross-library page-name collision).
6. New `cross_library_query` audit event type; one per library access; logged to `.kb-offline/audit.log`.
7. `--save` of a federated answer records the real resolved handles in `SavedAnswer.libraries`.

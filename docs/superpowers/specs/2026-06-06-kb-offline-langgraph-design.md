# Design: kb-offline — LangGraph + Ollama backend for the knowledge-base kit

**Issue:** #211 (EPIC) · **Plugin:** `sdlc-knowledge-base` · **Branch:** `feature/211-kb-offline-langgraph` · **Date:** 2026-06-06
**Status:** Approved (brainstorming, revised after **two** external review rounds) — next step is a **contract-resolution M0 plan only** (claim/evidence schema, mutation journal/recovery, resume-selection, backend ownership); detailed M1–M4 planning follows M0
**Relates to:** #209 (federation), #164 (cross-library query, merged), #208 (bulk ingest, merged)

> **Revision note (external review):** this spec was revised to (1) state parity honestly,
> (2) make the executable pipeline + safe mutation + resume contracts the load-bearing foundation,
> (3) replace "resume for free" with explicit idempotency/locking, (4) require typed mutation
> proposals validated by deterministic code, (5) make labelled ground truth (not cloud output) the
> primary eval signal, (6) use rank fusion for federation, (7) correct packaging facts.

## Motivation

The knowledge-base kit is **token-heavy**: bulk ingest fans 16–64 extractor agents per run,
query/synthesis are LLM-bound. For large corpora (CRI: 887 sources) this is expensive and
cloud-only. A **local execution backend** (LangGraph + Ollama) cuts token cost to ~zero, runs
offline/private, and makes the wiki's compounding loop affordable to run routinely.

This EPIC is two things:
1. **Complete the LLM-wiki's shared-core story** — compounding loop first-class, federation query
   layer, provenance/layer-aware retrieval, federation-aware hygiene (wiki-native; benefit any backend).
2. **Make the wiki backend-pluggable** — add an Ollama backend so the *same executable pipeline* runs
   token-free, plus an optional embedding accelerator for scale.

## Core principle: parity (stated honestly)

**One wiki, one library format, one deterministic core, one set of prompts, and — for the standalone
CLI — one typed executable pipeline.** What varies is the model behind the dispatch seam.

### Parity is contract + pipeline for the CLI; contract-only (behaviorally verified) for in-agent skills

There are two **invocation contexts**, and they are not unified at the code level — deliberately:

| Context | How it runs | Backend | Pipeline |
|---|---|---|---|
| In-agent skills (today) | Claude Code main agent dispatches sub-agents via the Agent tool | Anthropic (Claude) | Orchestration expressed in the SKILL (e.g. `kb-query` renders prompts, parallel-dispatches `research-librarian`, runs attribution post-check) |
| Standalone CLI (`kb-offline`, new) | Plain Python process runs the typed executable pipeline | Ollama (default) or Anthropic API (`--backend`) | The shared executable pipeline |

**Why we deliberately do NOT make the skills shell out to the CLI** (the rejected "true single
pipeline" option): Max-subscription users get Claude-Code-native tokens as part of their plan, so
keeping the in-agent skills on native sub-agent dispatch lets them use those included tokens rather
than incurring extra Anthropic-API cost from a subprocess pipeline. Enterprise-contract users see no
difference. This is a cost-of-use decision, recorded explicitly.

**Therefore parity is claimed precisely as:**
- **Shared, literally-reused code**: the deterministic core (`discover_sources`, `route_extracts`,
  manifests, `build_shelf_index`, slugs, `attribution`) and **`prompts.py`** as the **canonical
  source of the operation prompt fragments**.
- **One typed executable pipeline** for the CLI's two backends (Ollama/Anthropic) — byte-identical
  algorithm, model is the only variable, so local-vs-cloud is A/B-able.
- The in-agent skills are a **thin presentation** over the same core + prompts; the **eval harness
  holds them behaviorally equivalent** to the CLI pipeline. We do **not** claim the skill *is* the
  executable pipeline.

**Prompt-parity mechanism (enforceable — resolves the "render from prompts.py vs skills unchanged"
conflict).** The agent `.md` files are not rewritten by hand to "render from" `prompts.py` at
runtime (they can't — the agent reads its own `.md`). Instead:
- `prompts.py` holds the **canonical operation fragments** (the extractor JSON contract, the
  librarian retrieval instructions, the reducer rules) as named constants.
- Each agent `.md` carries those fragments inside an explicitly delimited **managed block**
  (`<!-- BEGIN managed:prompt-fragment NAME -->…<!-- END -->`).
- A **CI drift-check** (`check-prompt-parity.py`) asserts each managed block byte-matches its
  `prompts.py` constant; drift fails CI. Hand-written narrative *outside* the managed blocks is free.
This makes the shared-prompt claim *enforceable*, not aspirational, without "rewriting" the skills.

LLM-wiki (curated, reasoned retrieval) is the paradigm; we do not replace reasoned retrieval with
vector similarity (see §Embedding accelerator).

## The typed executable pipeline (the foundation — build first)

A single Python module defining each operation as a typed, testable function over the shared core,
with the model-touching steps delegated to an injected **backend**. This is the load-bearing
foundation; Ollama is then "just a backend."

### Ownership boundary (resolves backend vs pipeline vs LangGraph ambiguity)

Three distinct layers — do not conflate them:
- **Backend** = *model calls only*. Narrow interface:
  `generate(prompt, *, schema=None) -> str | dict` and `embed(texts) -> vectors`. No validation,
  no retries, no file I/O. (`OllamaBackend`, `AnthropicBackend`, `FakeBackend`.)
- **Pipeline** (`pipeline.py`) = the deterministic operations that *own* parsing, the
  validate→repair→fail ladder, deterministic logic (routing, etc.), and **mutation orchestration**.
  Pipeline operations call the backend for the model step.
- **LangGraph** (`graphs/`) = a *scheduling + checkpoint adapter* around pipeline steps (fan-out,
  ordering, in-graph retry). It orchestrates; it never owns validation or writes.

### Operation contracts (pipeline operations — typed Pydantic I/O)

```
extract(source, shelf_index)        -> ExtractJSON                # map
select(question, shelf_index)       -> SelectResult(page_ids)     # retrieval
synthesize(question, pages)         -> Answer                     # query synthesis (claim-structured)
reduce(target, extracts, existing)  -> MutationProposal           # ingest writer  (NOT raw content)
promote(verified_answer)            -> MutationProposal           # compounding     (NOT raw content)
```

**Claim-structured `Answer` (enables entailment — resolves P1):** a flat `(text, citations[])`
cannot carry the claim→citation→evidence mapping that promotion's entailment check requires. So:

```
Answer(claims: Claim[], rendered_text: str)
Claim(text: str, cited_pages: PageRef[], evidence_spans: Span[], entailment_status: enum)
        # entailment_status ∈ {supported, unsupported, partial}; high-impact claims must be 'supported'
```

`synthesize` must emit claims with their cited pages and the supporting spans; the entailment check
then verifies each claim against its spans, and `rendered_text` is derived from the claims.

### Safe mutation boundary (deterministic code owns all writes)

Backends **never** return final writable file content. They return a typed **`MutationProposal`**
(target path, intended frontmatter, body, citations, cross-refs, action ∈ {create, extend}). A
deterministic **validator** gate then enforces, before any write:

- target path is within the library and matches the allowed slug/layout;
- required frontmatter present and well-formed (`layer`, `confidence`, sources);
- every citation resolves to a real source/page; source attribution present;
- cross-references resolve to existing (or co-created) pages;
- **no deletion** of existing content not explicitly in scope; **no confidence escalation** of an
  existing page beyond policy.

**A single operation is multi-file and must be journaled (resolves P1 — atomic per-file ≠ atomic
mutation).** One successful `reduce`/`promote` changes the **page, the manifest, the shelf-index, and
possibly answer/audit records**; a crash between those writes leaves inconsistent state. So:

- An **operation journal** (append-only, under `library/.kb-offline/journal/`) records the intended
  mutation set with commit **stages**: `proposed → validated → staged → committed → indexed`.
- **Expected-target hash (compare-and-swap):** an `extend` proposal records the hash of the target
  page *as read during validation*; the writer commits only if the on-disk page still matches that
  hash, else it aborts as `conflict` (prevents clobbering edits made since validation).
- **Durable staged commit:** write temp → **`fsync` the file** → atomic `rename` → **`fsync` the
  directory**. (This *extends* #208's `persist_extract`/`save_manifest`, which today rename *without*
  `fsync` — the spec earlier overclaimed "exactly as #208"; #208's helpers will be upgraded to fsync
  as part of M0.)
- **Recovery rules:** on startup/resume, replay the journal — re-apply `staged`-but-not-`committed`
  mutations idempotently (hash-guarded), roll forward `committed`-but-not-`indexed` by re-running the
  deterministic **shelf-index reconciliation** (`build_shelf_index` is itself idempotent and
  hash-based, so reconciliation is deterministic), and surface `conflict`/`failed` entries in the run
  report. The journal + manifest together are the recovery source of truth.

A failing proposal → `mark_*_failed` (graceful partial failure). **"Verified answer"** (input to
`promote`) is defined as: an `Answer` whose every claim has `entailment_status = supported` (no
`unsupported` high-impact claims) with valid citations + attribution, and that the operator has
confirmed for promotion.

### Resume & idempotency (explicit — not "free")

The **manifest is the operator-visible source of run truth** (retain #208 semantics; do not replace
with opaque graph checkpoints). Contracts:

- **Run ID** per invocation; **thread/step IDs** derived deterministically from `(run, operation,
  item)`.
- Each work item records an **input + prompt + model + config hash**; on resume, a cached
  result is reused only if all hashes match (**resume-invalidation**: changed source, prompt, model,
  or config ⇒ re-run that item).
- **Idempotent write tasks**: extract files / pages are addressed by stable slug; re-running a
  completed item is a no-op or a hash-guarded overwrite, never a duplicate.
- **Resume selection (resolves P1):** `kb-offline <op> --resume <run-id>` resumes a specific run; with
  no `--resume`, the default is **deterministic latest-compatible-run selection** — the most recent
  run for this `(operation, library, input-set)` whose config/model/prompt hashes still match,
  otherwise a fresh run. `--resume latest` is sugar for that.
- **Manifest lifecycle states:** each run is `running → completed | failed | abandoned`. A run is
  `abandoned` if its lock is stale (below); only `running`/`failed` runs are resumable.
- **Per-library lock** with **stale-lock handling**: lockfile under `library/.kb-offline/` records
  PID + host + heartbeat timestamp; a lock is stale if the PID is dead or the heartbeat exceeds a TTL,
  in which case the run is marked `abandoned` and the lock is reclaimed (with a logged warning). Two
  live runs can never mutate one library concurrently.
- The LangGraph **checkpointer is an internal convenience only** (in-graph retry), never the resume
  authority; nodes that mutate tolerate replay (validate-then-commit + journal is idempotent).

## Architecture

### The backend seam

Interface = **model calls only** (per the ownership boundary above):
`generate(prompt, *, schema=None) -> str | dict`, `embed(texts) -> vectors`. Implementations:
- `OllamaBackend` — calls Ollama (CLI default); `generate` uses `format=`<schema> for grammar-constrained JSON.
- `AnthropicBackend` — direct Anthropic API calls (`--backend anthropic`).
- `FakeBackend` (tests) — deterministic, no model calls.

The pipeline operations (`extract`/`select`/`synthesize`/`reduce`/`promote`) wrap these with
parsing, the validate→repair→fail ladder, and mutation orchestration. In-agent skills are
**unchanged** (per the parity decision).

### Package layout (in the `sdlc-knowledge-base-scripts` distribution)

```
scripts/
  pipeline.py           # typed pipeline operations (own parsing/validate-repair/mutation orchestration)
  contracts.py          # Pydantic models: ExtractJSON, Answer, Claim, MutationProposal, ...
  mutation.py           # validator + operation journal + durable staged-commit writer + recovery
  resume.py             # run/thread IDs, hashing, invalidation, lifecycle states, locking (manifest-backed)
  backends/   base.py (generate/embed only), ollama_backend.py, anthropic_backend.py, fake_backend.py
  graphs/     ingest_graph.py, query_graph.py, promote_graph.py   # LangGraph scheduling/checkpoint adapters
  prompts.py            # canonical operation prompt fragments (shared; CI drift-checked vs agent .md)
  embeddings.py         # optional accelerator (guarded import)
  kb_offline_cli.py     # `kb-offline` console-script entry
```
Plus `tools/validation/check-prompt-parity.py` (the managed-block drift check) and an upgrade to
`#208`'s `persist_extract`/`save_manifest` to `fsync` before/after rename.

### Packaging corrections (verified against current `pyproject.toml`)

Current distribution is **`sdlc-knowledge-base-scripts`** v0.1.0, dep `pyyaml` only, **no console
scripts, no extras**, and **no pydantic**. This EPIC must:
- add a **console-script** entry point `kb-offline = sdlc_knowledge_base_scripts.kb_offline_cli:main`;
- add an **optional extra** `[offline]` → `langgraph`, `langgraph-checkpoint-sqlite`,
  `langchain-ollama`, `ollama`, embeddings deps (sqlite-vec or numpy);
- add **`pydantic`** to base deps (the typed contracts) — it is light and used by the validator too;
- guard all offline imports so the base distribution still imports without the extra.
- Install line is `pip install "sdlc-knowledge-base-scripts[offline]"` (corrected from the earlier
  `sdlc-knowledge-base[offline]`).

### CLI surface

```
kb-offline init        [--library PATH]
kb-offline ingest      <source> [--library PATH] [--backend ollama|anthropic]
kb-offline ingest-bulk <glob|dir|list> [--parallel N] [--backend ...] [--extractor-model ...]
kb-offline query       "<question>" [--libraries a,b,c] [--layer L] [--min-confidence C]
kb-offline promote     <query-result-ref>
kb-offline lint        [--libraries ...]
kb-offline index       [--library PATH]
kb-offline eval        <suite>
```

## Wiki-native enhancements (shared core)

**#1 Compounding loop.** `query` returns `Answer` + provenance, persisted under
`.kb-offline/answers/`. `promote <ref>` runs the promote operation → `MutationProposal` → validator →
staged commit → shelf-index rebuild. Deliberate/reviewable; requires a *verified* answer (defined above).

**#2 Federation query layer.** Reuses #164's registry. `query --libraries a,b,c` runs the same
select→read→synthesize per library, then merges with **per-claim source-library attribution**.
**Priming**: local KB config/shelf-index terms bias each library's selection. **Audit**: every
cross-library access appended to an audit log (mirrors `kb-audit-query`).

**#4 Provenance/layer-weighted retrieval & synthesis.** `confidence`/`layer` frontmatter first-class:
`--layer` filters candidates, `--min-confidence` drops weak sources, synthesis weights higher-confidence
pages and surfaces confidence. Threaded through shared `select`/`synthesize`.

**#5 Federation-aware hygiene.** `lint` extends within-library checks with cross-library passes:
same claim with conflicting values across libraries → flagged with both sources; cross-library
staleness. Read-only report.

## Embedding accelerator (optional, shared core, OFF by default)

**Purpose:** a derived, rebuildable index that **pre-filters candidate pages before the librarian
reasons** — earns its place only at scale or across many federated libraries. Never replaces
shelf-index reasoning. Benefits any backend; off by default.

**Chunking — "find fine, read coarse" (parent-document retrieval):**
- **Default: page-level embedding** (1 vector/page) — curated pages are single-topic & bounded, so
  the holistic vector is the better signal; 1 page → 1 row; hit = page = citable unit.
- **Adaptive section-level fallback** only for oversized pages: split on existing markdown `##`
  headings, embed each section, but **always resolve a hit to its whole page and read the full page**.
- Always-section / fixed-window RAG chunking **rejected** (false positives from keyword-y sections,
  false negatives on holistic relevance, noisy short-section embeddings—worse on local embedders—,
  page-hogging top-k, index bloat against the scale goal).

**Store:** `library/.kb-offline/embeddings.sqlite` (sqlite-vec) or numpy `.npz` — gitignored,
derived, rebuilt by `kb-offline index` with hash-based change detection (only re-embed changed pages).

**Index compatibility + federation merge (revised):** each index **persists its embedding provenance**
(model name, dimensions, normalization, metric) in a header. Federation **rejects incompatible
indexes** and uses **rank fusion (Reciprocal Rank Fusion)** across libraries rather than raw-score
merging (raw cross-index scores are not comparable). The fused shortlist (with source attribution)
is handed to the librarian for reasoned selection.

## Local-model robustness

**Structured-output enforcement.** Local models are worse at strict JSON (#208: 1/15 *cloud* Haiku
emitted malformed JSON):
- **Grammar-constrained decoding** primary: Ollama `format` = JSON Schema derived from the
  `ExtractJSON` Pydantic model (single source of truth).
- **Validate → repair → fail** ladder: parse + Pydantic-validate; one bounded repair re-prompt with
  the error; still bad → `mark_source_failed`. No infinite retries.
- `select` must return known page-ids; `synthesize` citations validated for **entailment** against
  pages actually read (not mere presence).

**Model defaults (configurable):** extraction — Qwen2.5-7B/14B or Llama3.1-8B; synthesis — a larger
local model where hardware allows. Override via flag/config.

## Eval / quality harness (primary gate; ground truth, not cloud)

`kb-offline eval <suite>` scores **both backends against a labelled fixture** (the primary signal).
Cloud-vs-local agreement is **secondary** drift analysis only — cloud output is not ground truth.

| Metric (primary) | Catches | Scoring |
|---|---|---|
| Fact recall vs labelled expected facts | does the answer contain the right facts | match vs labelled key |
| Routing-target agreement | extract routes to the right pages | set overlap vs labelled targets |
| Abstention correctness | says "no evidence" when it should | vs labelled no-evidence questions |
| Citation **entailment** | does the cited page actually support the claim | entailment check (rule + optional LLM-judge) |
| Extraction-JSON validity | local JSON reliability | schema-validate; % first-pass + post-repair |
| Attribution correctness (federation) | right source-library per claim | vs labelled source |
| (secondary) cloud-vs-local agreement | drift between backends | overlap, reported separately |

**Suites (two sizes — resolves the "15 questions is too coarse" P2):**
- **Smoke suite** (~15 questions, in-repo) — fast CI signal; *not* used for release percentages.
- **Frozen release suite** — **75–100 labelled questions including ≥20 no-evidence cases**, with
  **pinned model + config**, run **3×** (report mean/variance). This is the suite the thresholds
  below are measured on.

**Metric definitions + non-negotiable safety floors (baked in now; numeric model-quality thresholds
proposed now, ratified at M0 exit before M1 tuning):**

| Metric | Type | Bar |
|---|---|---|
| Invalid mutation / path / citation **rejection** | safety floor (deterministic) | **100%** |
| Citation reference validity & federation attribution | safety floor (deterministic) | **100%** |
| Post-repair JSON validity | safety floor | **100%** |
| Citation **entailment** | model-quality | **≥98%**, and **zero unsupported high-impact claims** |
| First-pass JSON validity | model-quality | **≥95%** |
| Fact recall (macro-averaged) | model-quality | **≥85%** |
| Routing-target recall / precision | model-quality | **≥90% / ≥80%** |
| Abstention precision / recall | model-quality | **≥95% / ≥90%** |
| (secondary) cloud-vs-local agreement | drift | reported, not gated |

The **safety floors are deterministic-code guarantees** (the validator/attribution checks enforce
them — not model behavior), so 100% is a correctness invariant. The **model-quality numbers are the
proposed M1 gate**, ratified at M0 exit. Ollama is not defaulted until the release suite meets them.

## Sequencing — one branch, foundation-first, eval-gated milestones

All on `feature/211-kb-offline-langgraph`; each milestone lands green, commits, and **must pass its
gate before the next begins**.

| Milestone | Delivers | Gate |
|---|---|---|
| **M0 — Foundation & contracts** (planned & built first, on its own; M1–M4 are *not* detail-planned until M0's contracts are resolved) | `contracts.py` (incl. **claim-structured `Answer`**); `mutation.py` (proposal + validator + **operation journal + expected-hash CAS + durable fsync commit + recovery + shelf-index reconciliation**); `resume.py` (IDs, hashing, invalidation, **lifecycle states, `--resume`/latest-compatible selection, stale-lock TTL/PID**); `pipeline.py`; `prompts.py` + `check-prompt-parity.py`; `#208` fsync upgrade; narrow `generate/embed` backend base + `AnthropicBackend` + `FakeBackend`; eval-harness skeleton + ratified thresholds | The four contracts resolved & unit-proven (claim/evidence schema, mutation journal/recovery, resume-selection, backend ownership); pipeline runs existing operations via `AnthropicBackend`/`FakeBackend`; prompt-parity check green; thresholds ratified |
| **M1 — Ollama ingest/query** | `OllamaBackend`, `ingest_graph`, `query_graph`, structured-output ladder; CLI `init`/`ingest`/`ingest-bulk`/`query`; provenance/layer (#4) | **Eval gate**: Ollama meets the agreed thresholds on fact recall, routing, abstention, citation entailment, JSON validity — *before* Ollama is defaulted |
| **M2 — Promotion + federation** | compounding `promote` (#1); federation query, attribution, priming, audit (#2); cross-library hygiene `lint` (#5) | Eval gate on federation attribution + promotion-mutation validation |
| **M3 — Embeddings + scale** | optional accelerator (#3): `index`, sqlite-vec, page+section fallback, RRF federation merge, index-compat rejection | Eval gate: retrieval recall@k with accelerator ≥ shelf-index baseline at scale; off-by-default preserved |
| **M4 — Ship** | `[offline]` extra + console script + pydantic/langgraph deps; CRI-scale manual run; release-mapping; version bump; README | packaging check, full validation, retrospective |

## Testing strategy

- **Shared core** — existing tests reused unchanged (parity guarantee).
- **Pipeline + backends** — contract tests against `FakeBackend` (mirrors `orchestrator.py`
  dispatcher-mock pattern); both real backends tested for conformance.
- **Mutation validator** — adversarial tests: bad path, missing frontmatter, dangling citation,
  attempted deletion, confidence escalation → all rejected; valid proposal → staged commit.
- **Resume** — hash-mismatch invalidation, replay-is-idempotent, lock prevents concurrent mutation.
- **Graphs** — driven with `FakeBackend`; structured-output ladder tested by injecting malformed
  outputs (assert repair-then-fail).
- **Eval harness** — runs on the labelled fixture in CI; emits ground-truth scores + cloud-vs-local
  drift report.
- **Live Ollama smoke** — pytest marker that skips if Ollama is absent (CI green without a model);
  run manually like #208's smoke.

## Out of scope

- Making in-agent skills run the executable pipeline / shell out to the CLI (deliberately rejected —
  Max-token rationale above). Skills stay native; eval verifies behavioral equivalence.
- Graph database / stateful store (files-as-ledger authoritative; embeddings + link graph are derived).
- Always-section / fixed-window RAG chunking (rejected).
- Hybrid map-offline/reduce-cloud auto-escalation (pluggable backend enables it later; not built v1).

## Open questions (resolve during implementation)

- Embedding store: sqlite-vec vs numpy `.npz` (lean sqlite-vec; confirm dep footprint).
- Exact local-model defaults — pending M1 eval numbers on the frozen release suite.
- Final ratification of the proposed model-quality thresholds at M0 exit (definitions + safety
  floors are already fixed above; only the model-quality numbers can move, and only with rationale).

## Decisions log

1. **Pluggable backend, Ollama default**, Anthropic retained, escalation-ready (not pure-offline).
2. **CLI + package inside the `sdlc-knowledge-base-scripts` distribution**, `[offline]` extra,
   `kb-offline` console script (not a new plugin or MCP server).
3. **Parity = shared core + shared prompts + one CLI executable pipeline; in-agent skills are a thin
   presentation held behaviorally-equivalent by eval.** True single-pipeline (skills shell out)
   **rejected** so Max users keep using Claude-Code-native tokens; Enterprise unaffected.
4. **Embeddings = optional shared-core accelerator, off by default** (not a RAG paradigm shift);
   default retrieval stays the curated shelf-index librarian.
5. **Chunking: page-level default + adaptive section fallback, find-then-read-all**; always-section rejected.
6. All five wiki elements in scope, **one branch**.
7. **Mutation boundary**: backends return typed `MutationProposal`s; deterministic validator owns all
   writes (path/frontmatter/citation/attribution/cross-ref/no-deletion/no-confidence-escalation);
   staged→atomic commit. "Verified answer" defined.
8. **Resume is explicit**: manifest is source of truth; run/thread IDs, input+prompt+model+config
   hashes, invalidation, idempotent writes, per-library lock; LangGraph checkpointer is internal only.
9. **Eval primary signal is labelled ground truth** (facts/routing/abstention/citation-entailment);
   cloud-vs-local is secondary drift; thresholds set before Ollama becomes default.
10. **Federation retrieval uses rank fusion + index-compatibility rejection**, not raw-score merge.
11. **One branch, foundation-first, eval-gated milestones M0–M4.**
12. **`Answer` is claim-structured** (`Claim` with cited_pages + evidence_spans + entailment_status) —
    a flat text+citations cannot support the entailment guarantee.
13. **A mutation is journaled, not just per-file-atomic**: operation journal with commit stages,
    expected-target-hash compare-and-swap for `extend`, durable fsync staged-commit, replay-based
    recovery, deterministic shelf-index reconciliation. (#208 helpers upgraded to fsync.)
14. **Resume selection is explicit**: `--resume <run-id>` / deterministic latest-compatible-run;
    manifest lifecycle states (running/completed/failed/abandoned); stale-lock via PID + heartbeat TTL.
15. **Ownership boundary**: backend = model calls only (`generate`/`embed`); pipeline owns
    validation/repair/deterministic-ops/mutation; LangGraph = scheduling/checkpoint adapter.
16. **Prompt parity is CI-enforced**: canonical fragments in `prompts.py`, mirrored into agent `.md`
    managed blocks, drift-checked by `check-prompt-parity.py`.
17. **Two eval suites** (smoke ~15; frozen release 75–100 incl. ≥20 no-evidence, pinned config, 3×).
    Safety floors (rejection/citation-validity/attribution/post-repair-JSON = 100%) baked now;
    model-quality thresholds proposed now, ratified at M0 exit before M1 tuning.

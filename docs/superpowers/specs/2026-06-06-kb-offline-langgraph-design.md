# Design: kb-offline — LangGraph + Ollama backend for the knowledge-base kit

**Issue:** #211 (EPIC) · **Plugin:** `sdlc-knowledge-base` · **Branch:** `feature/211-kb-offline-langgraph` · **Date:** 2026-06-06
**Status:** Approved (brainstorming, revised after external review) — pending spec re-review, then implementation plan
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
  manifests, `build_shelf_index`, slugs, `attribution`) and **`prompts.py`** (single prompt source
  both the agent `.md` files and the CLI pipeline render from).
- **One typed executable pipeline** for the CLI's two backends (Ollama/Anthropic) — byte-identical
  algorithm, model is the only variable, so local-vs-cloud is A/B-able.
- The in-agent skills are a **thin presentation** over the same core + prompts; the **eval harness
  holds them behaviorally equivalent** to the CLI pipeline (it runs the labelled suite through the
  skills' logic too). We do **not** claim the skill *is* the executable pipeline.

LLM-wiki (curated, reasoned retrieval) is the paradigm; we do not replace reasoned retrieval with
vector similarity (see §Embedding accelerator).

## The typed executable pipeline (the foundation — build first)

A single Python module defining each operation as a typed, testable function over the shared core,
with the model-touching steps delegated to an injected **backend**. This is the load-bearing
foundation; Ollama is then "just a backend."

### Operation contracts (typed I/O — Pydantic models)

```
extract(source, shelf_index)        -> ExtractJSON                # map
select(question, shelf_index)       -> SelectResult(page_ids)     # retrieval
synthesize(question, pages)         -> Answer(text, citations[])  # query synthesis
reduce(target, extracts, existing)  -> MutationProposal           # ingest writer  (NOT raw content)
promote(verified_answer)            -> MutationProposal           # compounding     (NOT raw content)
```

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

Only on pass does the writer perform a **staged → atomic-commit** write (temp file → fsync → rename),
exactly as #208's `persist_extract` does. A failing proposal → `mark_*_failed` (graceful partial
failure). **"Verified answer"** (input to `promote`) is defined as: an `Answer` whose every claim
passed the attribution + citation-**entailment** checks and that the operator has confirmed for
promotion.

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
- **Per-library lock** (lockfile under `library/.kb-offline/`) so two runs can't mutate one library
  concurrently.
- The LangGraph **checkpointer is an internal convenience only** (in-graph retry), never the resume
  authority; nodes that mutate are written to tolerate replay (validate-then-commit is idempotent).

## Architecture

### The backend seam

Interface = the operation contracts above. Implementations:
- `OllamaBackend` — LangGraph node functions calling Ollama (CLI default).
- `AnthropicBackend` — direct Anthropic API calls (`--backend anthropic`).
- `FakeBackend` (tests) — deterministic, no model calls.

In-agent skills are **unchanged** (per the parity decision).

### Package layout (in the `sdlc-knowledge-base-scripts` distribution)

```
scripts/
  pipeline.py           # the typed executable pipeline (operation functions)
  mutation.py           # MutationProposal + deterministic validator + staged-commit writer
  resume.py             # run/thread IDs, hashing, invalidation, locking (manifest-backed)
  backends/   base.py, ollama_backend.py, anthropic_backend.py, fake_backend.py
  graphs/     ingest_graph.py, query_graph.py, promote_graph.py   # LangGraph adapters over pipeline.py
  prompts.py            # single shared prompt source
  embeddings.py         # optional accelerator (guarded import)
  kb_offline_cli.py     # `kb-offline` console-script entry
```

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

**Quality thresholds are set before Ollama is made the default**, on this harness — not deferred.
Fixture is small (~a dozen pages, ~15 questions) and in-repo; CRI corpus = realistic-scale manual check.

## Sequencing — one branch, foundation-first, eval-gated milestones

All on `feature/211-kb-offline-langgraph`; each milestone lands green, commits, and **must pass its
gate before the next begins**.

| Milestone | Delivers | Gate |
|---|---|---|
| **M0 — Foundation** | typed executable `pipeline.py`; `mutation.py` (proposal + validator + staged commit); `resume.py` (IDs, hashing, invalidation, locking, manifest-backed); `prompts.py`; `AnthropicBackend`; `FakeBackend`; eval-harness skeleton | Pipeline runs the existing operations via `AnthropicBackend`/`FakeBackend`; mutation validator + resume contracts unit-proven; eval harness runs on the fixture |
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
- Exact local-model defaults — pending M1 eval numbers.
- The exact pass thresholds per eval metric — proposed at M0, ratified before M1's gate.

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

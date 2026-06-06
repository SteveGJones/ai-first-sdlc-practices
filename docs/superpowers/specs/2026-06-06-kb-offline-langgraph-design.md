# Design: kb-offline — LangGraph + Ollama backend for the knowledge-base kit

**Issue:** #211 (EPIC) · **Plugin:** `sdlc-knowledge-base` · **Branch:** `feature/211-kb-offline-langgraph` · **Date:** 2026-06-06
**Status:** Approved (brainstorming) — pending spec review, then implementation plan
**Relates to:** #209 (federation), #164 (cross-library query, merged), #208 (bulk ingest, merged)

## Motivation

The knowledge-base kit is **token-heavy**: bulk ingest fans 16–64 extractor agents per run,
and query/synthesis are LLM-bound. For large corpora (CRI: 887 sources) this is expensive and
cloud-only. A **local execution backend** (LangGraph orchestration + Ollama models) cuts token
cost to ~zero, runs fully offline/private, and — because local inference is cheap — makes the
wiki's *compounding loop* affordable to run routinely.

This EPIC is two things, not one:
1. **Complete the LLM-wiki's shared-core story** — compounding loop first-class, federation query
   layer, provenance/layer-aware retrieval, federation-aware hygiene. These are wiki-native
   enhancements that benefit online **and** offline identically.
2. **Make the wiki backend-pluggable** — add an Ollama dispatcher so the *same* pipeline runs
   token-free, plus an optional embedding accelerator for scale.

## Core principle: parity

**One wiki, one pipeline. The library (curated markdown pages + shelf-index + log) and the
algorithm are identical regardless of backend. The only thing that varies is the model behind the
dispatch seam.** This is non-negotiable: offline must not become a different architecture (e.g.
RAG) from online, or we maintain two systems.

### Two invocation contexts (an honest nuance)

| Context | How it runs | Backend |
|---|---|---|
| Online, in-agent (today's skills) | Claude Code main agent dispatches sub-agents via the Agent tool | Anthropic (Claude) |
| Standalone CLI (new — `kb-offline`) | A plain Python process drives the pipeline directly, no Claude agent loop | Ollama (default) or Anthropic API (`--backend`) |

"Parity" means precisely:
- **The deterministic core is literally shared code** — `discover_sources`, `route_extracts`,
  manifests, `build_shelf_index`, slugs, `attribution` — reused verbatim from
  `sdlc_knowledge_base_scripts`.
- **Prompts are a single shared source** (`prompts.py`) that both the agent `.md` files and the
  CLI graphs render from.
- The CLI's two backends run the byte-identical pipeline, so local-vs-cloud quality is A/B-able on
  the same algorithm; that pipeline mirrors the in-agent skills because they share core + prompts.

LLM-wiki (curated, reasoned retrieval) is the paradigm. We do **not** replace reasoned retrieval
with vector similarity; embeddings are only an optional accelerator (see §Embedding accelerator).

## Architecture

### The backend seam

A small interface (the only model-touching surface):

```
extract(source, shelf_index)        -> ExtractJSON
select(question, shelf_index)       -> [page_id]
synthesize(question, pages)         -> Answer        # free text + citations
reduce(target, extracts, existing)  -> page_content
promote(answer)                     -> page_content
```

Implementations:
- `OllamaBackend` — LangGraph node functions calling Ollama (default for the CLI).
- `AnthropicBackend` — direct Anthropic API calls (`--backend anthropic`).
- `FakeBackend` (tests) — deterministic, no model calls.

The existing in-agent skills are **unchanged**.

### Package layout (in `sdlc-knowledge-base`)

```
scripts/
  backends/   base.py, ollama_backend.py, anthropic_backend.py, fake_backend.py
  graphs/     ingest_graph.py, query_graph.py, promote_graph.py
  prompts.py            # single shared prompt source
  embeddings.py         # optional accelerator (guarded import)
  kb_offline_cli.py     # `kb-offline` console-script entry
```

- **Optional extra**: `pip install sdlc-knowledge-base[offline]` pulls `langgraph`,
  `langchain-ollama`, `ollama`, and embedding deps. Cloud-only users install nothing new; offline
  imports are guarded so the base plugin imports without the extra.
- Each operation is a LangGraph `StateGraph` with a **checkpointer** (SQLite under
  `library/.kb-offline/`) → resume for free (offline analogue of `.bulk-progress.json`). Model-call
  nodes delegate to the injected backend, so the graph is identical across backends.

### CLI surface

```
kb-offline init        [--library PATH]
kb-offline ingest      <source> [--library PATH] [--backend ollama|anthropic]
kb-offline ingest-bulk <glob|dir|list> [--parallel N] [--backend ...] [--extractor-model ...]
kb-offline query       "<question>" [--libraries a,b,c] [--layer L] [--min-confidence C]
kb-offline promote     <query-result-ref>
kb-offline lint        [--libraries ...]
kb-offline index       [--library PATH]        # build/refresh the optional embedding view
kb-offline eval        <suite>                 # parity/quality harness
```

## Wiki-native enhancements (shared core, online + offline)

**#1 Compounding loop (first-class).** `query` returns an answer + provenance (pages, libraries,
confidence), persisted under `.kb-offline/answers/`. `promote <ref>` runs a graph: verified answer
→ new curated page (frontmatter, citations back to source pages, cross-refs) → write via updater
path → rebuild shelf-index. Deliberate/reviewable, not automatic.

**#2 Federation query layer.** Reuses #164's registry (`~/.sdlc/global-libraries.json`).
`query --libraries a,b,c` fans the same select→read→synthesize pipeline across each library, then a
merge node assembles one answer with **per-claim source-library attribution**. **Priming**: local
project KB config/shelf-index terms bias each library's selection. **Audit**: every cross-library
access appended to an audit log (mirrors `kb-audit-query`).

**#4 Provenance/layer-weighted retrieval & synthesis.** Page frontmatter (`confidence`, `layer`)
first-class in query: `--layer` filters candidates, `--min-confidence` drops weak sources,
synthesis weights higher-confidence pages and surfaces confidence. Threaded through the shared
`select` + `synthesize` nodes (holds for both backends).

**#5 Federation-aware hygiene.** `lint` extends within-library checks (contradictions, staleness,
orphans) with cross-library passes: same claim with conflicting values across libraries → flagged
with both sources; cross-library staleness. Read-only report.

## Embedding accelerator (optional, shared core, OFF by default)

**Purpose (narrow):** a derived, rebuildable index that **pre-filters candidate pages before the
librarian reasons** — earns its place only at scale (hundreds–thousands of pages) or across many
federated libraries. Never replaces shelf-index reasoning; it only shortens the list the reasoner
reads. Benefits online and offline equally; off by default.

**Chunking — find fine, read coarse ("small-to-big" / parent-document retrieval):**
- **Default: page-level embedding** — one vector per curated page. Curated pages are already
  single-topic and bounded, so the holistic page vector is usually the better relevance signal;
  1 page → 1 row keeps the index rebuildable and attribution clean (hit = page = citable unit).
- **Adaptive section-level fallback** — only when a page exceeds a size threshold, split on existing
  markdown `##` section headings (semantic boundaries curation already created), embed each section,
  but **always resolve a hit back to its whole page before reading**. No fixed-token windowing, no
  overlap tuning.
- **Never** read a section in isolation — always read the full page. This preserves the page's
  framing/caveats/contradiction-handling and keeps hallucination/attribution risk low. Always-section
  chunking is rejected: for a curated wiki it adds false positives (keyword-y sections), false
  negatives (holistic-relevance pages), noisy short-section embeddings (worse on local embedders),
  page-hogging top-k, and index bloat that works against the scale goal — for marginal recall.

**Store:** `library/.kb-offline/embeddings.sqlite` (sqlite-vec) — gitignored, derived, rebuilt by
`kb-offline index` with the same hash-based change detection as `build_shelf_index` (only re-embed
changed pages). Ollama embeddings (`nomic-embed-text` / `mxbai-embed-large`).

**Federation merge:** query each enabled library's index → top-k per library → merge by score with
source-library attribution → hand the merged shortlist to the librarian for reasoned selection.

## Local-model robustness

**Structured-output enforcement (map phase lifeline).** Local models are worse at strict JSON
(#208 smoke: 1/15 *cloud* Haiku emitted malformed JSON), so offline this is engineered:
- **Grammar-constrained decoding** primary: Ollama `format` parameter accepts a JSON Schema derived
  from the `ExtractJSON` Pydantic model (single source of truth for the contract).
- **Validate → repair → fail** ladder per item: parse + Pydantic-validate; on failure, one bounded
  repair re-prompt with the parse error; still bad → `mark_source_failed` (graceful partial failure,
  proven in #208). No infinite retries.
- `select` must return known page-ids; `synthesize` citations validated against pages actually read
  (reuse existing `attribution` check).

**Model defaults (configurable):** extraction (map) — Qwen2.5-7B/14B or Llama3.1-8B; synthesis
(reduce/query) — a larger local model where hardware allows. `--extractor-model` / config override.

## Eval / parity harness (the long pole)

`kb-offline eval <suite>` runs a fixed labelled corpus + question set through **both** backends and
scores a cloud-vs-local comparison report. Doubles as regression protection.

| Metric | Catches | Scoring |
|---|---|---|
| Extraction-JSON validity rate | local JSON reliability | schema-validate; % first-pass + post-repair |
| Routing agreement | local routing vs labelled target files | set overlap vs key |
| Retrieval hit rate | select/embedding surfaces right pages | recall@k vs labelled relevant pages |
| Synthesis faithfulness | hallucination / unsupported claims | every claim cites a read page; flag uncited (auto) + optional LLM-judge |
| Attribution correctness (federation) | right source-library per claim | vs labelled source |

Labelled fixture is small (~a dozen pages, ~15 questions), in-repo. CRI corpus = realistic-scale
manual check.

## Sequencing (one branch, ordered increments — each leaves the tree green & commits)

| Phase | Delivers |
|---|---|
| A | Backend interface + shared `prompts.py` + `AnthropicBackend` + eval-harness skeleton (parity baseline before any local model) |
| B | `OllamaBackend` + `ingest_graph` (map→route→reduce→finalize) + structured-output ladder + checkpointer resume; CLI `init`/`ingest`/`ingest-bulk` |
| C | `query_graph` (select→read→synthesize) + provenance/layer filtering (#4); CLI `query` |
| D | Federation (#2): multi-library query, attribution, priming, audit + cross-library `lint` (#5) |
| E | Compounding loop (#1): `promote_graph`; CLI `promote` |
| F | Embedding accelerator (#3, opt-in): `kb-offline index`, sqlite-vec, page-level + section fallback, federation merge |
| G | Eval fill-out + CRI-scale manual run + `[offline]` extra + release-mapping + version bump + README |

## Testing strategy

- **Shared core** — existing tests reused unchanged (parity guarantee).
- **Backend interface** — contract tests against deterministic `FakeBackend` (mirrors
  `orchestrator.py` dispatcher-mock pattern); both real backends tested for conformance.
- **Graphs** — driven with `FakeBackend`; zero model calls. Structured-output ladder tested by
  injecting malformed outputs (assert repair-then-fail).
- **Eval harness** — runs on the small labelled fixture in CI; emits cloud-vs-local report.
- **Live Ollama smoke** — gated behind a pytest marker that skips if Ollama is absent (CI stays
  green without a local model); run manually like #208's smoke.

## Out of scope

- Replacing the existing in-agent skills (additive — a backend + a CLI, not a removal).
- Graph database / stateful store (files-as-ledger stays authoritative; embeddings + any link graph
  are derived, rebuildable views).
- Always-section / fixed-window RAG chunking (rejected above).
- Hybrid map-offline/reduce-cloud auto-escalation (the pluggable backend makes this easy later, but
  it is not built in v1).

## Open questions (resolve during implementation / spec review)

- Embedding store: sqlite-vec vs numpy `.npz` (lean sqlite-vec; confirm dependency footprint).
- Exact local-model defaults pending the eval-harness numbers.
- Quality bar: which eval scores make offline "good enough" to recommend as default.

## Decisions log (forks resolved in brainstorming)

1. **Pluggable backend, Ollama default**, Anthropic retained, escalation-ready — *not* pure-offline.
2. **CLI + package inside `sdlc-knowledge-base`**, `[offline]` extra, `kb-offline` console script —
   *not* a new plugin or MCP server.
3. **Parity**: shared core + shared prompts; model is the only variable; two invocation contexts.
4. **Embeddings = optional shared-core accelerator, off by default** — *not* a paradigm shift to RAG;
   default retrieval stays the curated shelf-index librarian, identical online & offline.
5. **Chunking: page-level default + adaptive section fallback, find-then-read-all** — always-section
   rejected.
6. All five wiki elements (#1 compounding, #2 federation, #4 provenance/layer, #5 hygiene, plus #3 as
   the opt-in accelerator) **in scope, one branch**.

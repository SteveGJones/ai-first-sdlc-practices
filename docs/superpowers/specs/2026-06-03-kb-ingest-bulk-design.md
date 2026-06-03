# Design: `kb-ingest-bulk` — parallel map-reduce ingest for large source sets

**Issue:** #208 · **Plugin:** `sdlc-knowledge-base` · **Date:** 2026-06-03
**Status:** Approved (brainstorming) — pending spec review then implementation plan

## Problem

`kb-ingest` integrates one source at a time via a single `agent-knowledge-updater`
— the only agent with write access to the library. Many sources contend for the
same shared topic files, so writes must be serialized. The existing
`kb-ingest-batch` sidesteps contention only by running **create-only** (it refuses
to touch existing files, deferring every conflict to manual single-source ingest).
Neither path can update shared topic files in parallel.

Real-world impact (CRI KB, 887 source PDFs): a hand-rolled Ralph loop processes
~5/iteration strictly sequentially (~5–6 min/file), projecting to weeks-to-months
for the full corpus. The serial constraint is architectural, not a tuning problem.

## Solution overview

A new skill `kb-ingest-bulk <glob|file-list|dir>` separates **extraction** from
**synthesis** (map-reduce), so the expensive read happens massively in parallel and
synthesis happens with exactly one writer per file:

1. **Map** (parallel, cheap model) — one read-only `knowledge-extractor` per source
   emits a compact structured extraction. Zero write contention.
2. **Route** (deterministic Python) — group extractions by target library file;
   pre-allocate new-topic files; merge near-duplicate new-topic proposals.
3. **Reduce** (parallel across files, Sonnet) — one fresh-context
   `agent-knowledge-updater` per target file synthesizes all routed extracts into
   that one file. One writer per file ⇒ no contention; files independent ⇒ parallel.
4. **Finalize** (once) — single shelf-index rebuild + one consolidated `log.md` entry.

Expected outcome: CRI's 887 sources go from weeks to ~1–2 hours wall-clock.

### Relationship to existing batch tooling (decided)

- **`kb-ingest-bulk` supersedes `kb-ingest-batch`.** `kb-ingest-batch` gains a
  deprecation banner pointing to bulk but stays functional. Bulk is strictly more
  capable (it updates existing shared files in parallel; batch is create-only).
- **`kb-prepare-batch` is unchanged** — it remains the staging/conversion front-end;
  its `library/raw/*.md` output is a valid input glob to `kb-ingest-bulk`.
- **`kb-ingest` (single source) is unchanged.**

## Architecture & components

Python owns all deterministic work (following the existing `orchestrator.py` +
injectable-dispatcher pattern used by `kb-query`). The skill drives agent fan-out
via **parallel Agent-tool calls** (portable across harnesses; no Workflow-tool
dependency — consistent with `kb-ingest-batch --parallel`).

| Artifact | Type | Role |
|---|---|---|
| `skills/kb-ingest-bulk/SKILL.md` | skill | Orchestration recipe |
| `agents/knowledge-extractor.md` | agent (new) | Map: read-only, **default Haiku** (configurable), returns structured JSON, never writes the library |
| `scripts/kb_ingest_bulk.py` | Python (new) | Discover sources, manage manifest, persist extracts, route, pre-allocate new files, finalize |
| `agents/agent-knowledge-updater.md` | agent (reused) | Reduce: one fresh-context Sonnet agent per target file |
| `scripts/build_shelf_index.py` | Python (reused) | Single finalize rebuild |
| `skills/kb-ingest-batch/SKILL.md` | skill (edit) | Deprecation banner → bulk |

**Concurrency:** `--parallel <N>`, **default 16, max 64** (raisable for capable
machines). Python hands the skill rounds of ≤N items to dispatch concurrently and
reconciles the manifest between rounds.

**Models:** extractor model configurable (`--extractor-model`, default
`claude-haiku-4-5`); updater stays Sonnet (`agent-knowledge-updater`'s declared model).

## Data flow

### Phase 1 — Map (parallel, ≤N-wide, Haiku)

1. Python `discover_sources()` resolves glob/file-list/dir → deduped source list;
   builds/updates the manifest.
2. Skill dispatches rounds of ≤N `knowledge-extractor` agents. Each reads **one**
   source + the shelf-index (read-only) and returns JSON:
   ```json
   {
     "source": "<path>",
     "findings": ["..."],
     "statistics": ["..."],
     "citations": ["..."],
     "confidence": "high|medium|low",
     "targets": [
       {"file": "cri-sustainability.md", "finding_idx": [0, 2]},
       {"new_topic_slug": "carbon-accounting", "title": "Carbon Accounting", "finding_idx": [1]}
     ]
   }
   ```
   The extractor groups its own findings by proposed target — existing-file match
   (by name, against the shelf-index) or proposed new topic `{slug, title}`.
3. Python persists each result to `library/.extracts/<slug>.json` and marks the
   source `extracted`. **The agent never writes the library** — Python owns the
   write, keeping map contention-free and making the extract file the resume token.

### Phase 2 — Route (Python, deterministic, no agent)

4. `route_extracts()` unions all extracts by target. Existing-file targets group by
   filename. New-topic proposals are slug-normalized and **fuzzy-merged**
   (near-duplicate slugs collapse to one). Python **pre-allocates** exactly one file
   path per distinct new topic *before* any reducer runs (prevents two reducers
   creating the same new file). A source touching multiple targets fans its findings
   across the relevant groups.
5. **Per-file size guard:** estimate grouped-extract token size; any file exceeding
   the configurable threshold (`--size-threshold`, default set well below the
   context limit) is **flagged in the report and skipped** — not silently risked.
   Chunked-reduce is documented as future work, not built in v1.

### Phase 3 — Reduce (parallel across files, ≤N-wide, Sonnet)

6. Skill dispatches one `agent-knowledge-updater` per target file, fresh context.
   Each receives all extracts routed to its file + the existing file content, and
   applies the **existing** extend-vs-create / contradiction-flagging / citation /
   confidence rules. It writes that **one** file. One writer per file ⇒ no
   contention; files independent ⇒ run in parallel. Because one agent sees *all*
   findings for a topic at once, dedup and contradiction handling improve over the
   incremental single-source path.

### Phase 4 — Finalize (once)

7. Single `build_shelf_index.py` rebuild + one consolidated `log.md` entry
   summarizing the run (totals, succeeded, failed, oversized-flagged topics).

## Why context overflow is not the core risk

The reduce agent never sees raw sources — only compact extracts. For a hot topic of
~150 sources: ~150 × ~1,000 words ≈ 150,000 words against a ~750,000-word / 1M-token
fresh context (~20% utilisation). Input overflow only bites at ~500–700 extracts
routed to a *single* file (10k-source-scale corpora). Therefore:

- **Default reduce = one fresh-context agent per file, no chunking.**
- The map phase is the compression boundary — **extracts must be bounded** (summary,
  not verbatim transcription). This is a contract on the extractor agent.
- The size guard (step 5) is a cheap measurement-based safety flag for the rare tail,
  not a default code path.

## Manifest, resumability, error handling

**Manifest:** `library/.extracts/.bulk-progress.json` (replaces hand-rolled
`kb_ingested.txt`). Atomic writes. Two-phase state:

```json
{
  "sources": { "<path>": {"slug": "...", "status": "pending|extracted|failed", "error": null} },
  "targets": { "<file>": {"status": "pending|reduced|failed", "source_count": 0, "is_new": false, "error": null} },
  "run_meta": {"parallel_n": 16, "extractor_model": "claude-haiku-4-5", "size_threshold": 200000}
}
```

**Resume / idempotency:** re-running skips sources whose extract file exists and is
valid, and skips already-`reduced` targets. New sources are appended to `pending`.
`--retry-failed` re-queues failed entries (mirrors `kb-ingest-batch`).

**Graceful partial failure:**
- A map extractor that errors/times-out → source marked `failed`, dropped from
  routing, run continues.
- A reduce updater that errors → target marked `failed`; its extracts remain on disk
  so a re-run retries just that file.
- All failures + oversized-flagged topics are surfaced in the final report and
  `log.md`. Exit non-zero only if *nothing* succeeded.

**`.extracts/` lifecycle:** gitignored; retained after the run for audit/resume;
`--clean` removes them.

## Skill arguments

| Argument | Description |
|---|---|
| `<glob \| file-list \| dir>` | Sources to ingest (e.g. `library/raw/*.md`, a dir, or a newline list) |
| `--parallel <N>` | Concurrency for map and reduce rounds (default 16, max 64) |
| `--extractor-model <id>` | Map model (default `claude-haiku-4-5`) |
| `--size-threshold <tokens>` | Per-file reduce size guard (default conservative) |
| `--retry-failed` | Re-queue failed sources/targets from a prior run |
| `--clean` | Remove `library/.extracts/` after a successful run |

## Testing (TDD — Python is the testable core; agents mocked via dispatcher)

- `discover_sources` — glob / file-list / dir; dedup; missing paths.
- Manifest — build, resume-skip, retry-failed, atomic write, malformed-file recovery.
- `route_extracts` — union by existing file; new-topic fuzzy-merge collision
  avoidance; multi-target source fans findings correctly; pre-allocation determinism.
- Size guard — flag-and-skip at the threshold boundary.
- Finalize — exactly one rebuild, one log entry; summary content.
- Dispatch — mocked via the injectable dispatcher callable (same as `orchestrator.py`
  tests); contract tests on extractor/updater JSON shape.

## Out of scope (v1)

- Chunk-and-merge reduce for pathological single-file topics (documented future work).
- Workflow-tool-based orchestration (parallel Agent dispatch is the portable default).
- Changes to `kb-prepare-batch` or single-source `kb-ingest`.

## Risks / open questions (resolved)

- **Large topics** → resolved: fresh-context reducer + bounded extracts + size guard.
- **Routing accuracy** → resolved: extractor proposes, Python router groups + fuzzy-
  merges; new topics pre-allocated before reduce.
- **New-file collisions** → resolved: router pre-allocates one path per distinct new
  topic before any reducer runs.

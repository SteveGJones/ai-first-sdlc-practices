# Feature Proposal #208 — kb-ingest-bulk: parallel map-reduce bulk ingest

**Status:** In progress
**Target Branch:** `feature/208-kb-ingest-bulk`

## Motivation

`kb-ingest` integrates one source at a time via a single `agent-knowledge-updater`
(the only agent with library write access), so sources contend for the same shared
topic files and writes must be serialized. The existing `kb-ingest-batch` sidesteps
contention only by running **create-only** — it refuses to touch existing files,
deferring every conflict to manual single-source ingest. Neither path can update shared
topic files in parallel. The CRI knowledge base (887 source PDFs) projects to
weeks-to-months on the serial path; the constraint is architectural, not a tuning
problem.

## Proposed Solution

Add a `kb-ingest-bulk <glob|dir|file-list>` skill that separates **extraction** from
**synthesis** (map-reduce):

1. **Map** (parallel, cheap model) — a new read-only `knowledge-extractor` agent runs
   per source (≤N-wide, default 16, max 64; default Haiku), emitting a compact JSON
   extraction. Zero write contention.
2. **Route** (deterministic Python) — group extractions by target library file,
   fuzzy-merge near-duplicate new-topic proposals, pre-allocate new files, flag oversized
   topics (size-guard).
3. **Reduce** (parallel across files, Sonnet) — one `agent-knowledge-updater` per target
   file synthesizes all routed extracts into that one file. One writer per file ⇒ no
   contention; topics independent ⇒ parallel. Updates *existing* shared files, which
   `kb-ingest-batch` cannot.
4. **Finalize** (once) — single shelf-index rebuild + one consolidated `log.md` entry.

Supersedes `kb-ingest-batch` (deprecated, still functional). Adds a `--library <path>`
override on `kb-ingest-bulk` + `kb-init` for isolated testing / multi-library. Full
design: `docs/superpowers/specs/2026-06-03-kb-ingest-bulk-design.md`; plan:
`docs/superpowers/plans/2026-06-03-kb-ingest-bulk.md`.

## Success Criteria

- [x] `kb-ingest-bulk` accepts a glob, a file-list, or a directory.
- [x] Resumable/idempotent via a two-phase manifest; re-running skips done sources.
- [x] Map phase writes only per-source extract files (no shared-file writes).
- [x] Reduce phase guarantees exactly one writer per library file.
- [x] Citation/contradiction rules from `agent-knowledge-updater` preserved in reduce.
- [x] One index rebuild + one log entry per run.
- [x] Extractor model configurable (default Haiku); updater stays Sonnet.
- [x] Graceful partial failure: a failed source/target drops out; reported at the end.
- [x] `--library` override on `kb-ingest-bulk` + `kb-init`.
- [x] 30 unit tests + mocked end-to-end integration; live smoke validated end-to-end.

## Out of scope

- Chunk-and-merge reduce for pathological single-file topics (documented future work).
- Full `--libraries` query federation across the remaining KB skills → tracked as **#209**
  (builds on EPIC #164's registry).

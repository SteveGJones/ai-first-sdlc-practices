# Feature Proposal: kb-ingest-bulk — parallel map-reduce ingest (#208)

**Status:** In progress · **Branch:** `feature/208-kb-ingest-bulk`

## Problem
`kb-ingest` is single-source; `kb-ingest-batch` is create-only (defers existing-file
conflicts to manual). Neither updates shared topic files in parallel. CRI's 887-source
corpus projects to weeks-to-months.

## Solution
`kb-ingest-bulk`: map (parallel read-only extractors) → route (Python) → reduce (one
writer per file, parallel) → single finalize. Supersedes `kb-ingest-batch`.
Adds `--library` override (also to `kb-init`) for isolated testing / multi-library.

## Design
See `docs/superpowers/specs/2026-06-03-kb-ingest-bulk-design.md`.

## Out of scope
Full `--libraries` query federation → #209 (builds on EPIC #164 registry).

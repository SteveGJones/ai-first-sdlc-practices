# Retrospective: kb-ingest-bulk (#208)

## What we set out to do
Parallel map-reduce bulk ingest for large source sets; supersede kb-ingest-batch.
Map (read-only extractors, ≤N-wide, Haiku) → Python route (group by target file,
fuzzy-merge new topics, pre-allocate, size-guard) → reduce (one writer per file,
parallel, Sonnet) → single finalize. Plus `--library` override for isolated testing.

## What went well
- **Clean Python/agent split.** All deterministic logic is pure Python (orchestrator
  dispatcher pattern); agent fan-out is the skill's job. Made the core fully unit-testable
  (30 tests) without real agent calls.
- **TDD throughout** — every helper landed test-first. Final suite: 30 kb_ingest_bulk
  tests, 302 kb tests total, zero regressions; plugin packaging green.
- **Two-stage review caught real issues.** Final review found a Critical slug-collision bug
  (same filename stem in different dirs → silent extract overwrite) fixed with a
  collision-free, resume-safe path-hash slug.
- **Live smoke (15 real CRI files) validated the whole pipeline end-to-end:**
  map (15 Haiku extractors, read-only) → route (82 targets, fuzzy-merge collapsed 2
  sources into one file) → reduce (3 representative files via real Sonnet agents, one
  writer per file, multi-source synthesis with proper frontmatter) → finalize (single
  index rebuild + one log entry) → resume (14 extracted sources skipped on re-run).

## What was hard / surprised us
- **Extractor JSON reliability.** 1 of 15 extractors emitted malformed JSON (a delimiter
  error mid-file). The persist-time `json.loads` + `mark_source_failed` path handled it
  gracefully — exactly the graceful-partial-failure design. Confirms that validating
  extractor output at persist time (not trusting the agent) is essential.
- **New-topic proliferation.** 14 sources against an *empty* library produced **82**
  proposed new-topic files (mostly singletons; only one fuzzy-merge). This is the
  "routing accuracy" risk the issue flagged. With no shared shelf-index vocabulary,
  extractors fragment into narrow micro-topics. Mitigations worth considering: seed a
  layer/topic vocabulary (kb-layers) to bias extractor target proposals; or a coarser
  routing pass. Related to follow-up #209.

## Lessons
- For LLM-emitted structured output, **always validate at the persistence boundary** and
  treat parse failure as a per-item failure, not a run abort.
- Slugs used as filesystem keys must be **collision-free AND deterministic per source**
  (resume-safe) — stem alone is neither.
- A throwaway `--library` makes real-agent smoke testing safe: the project library was
  provably untouched (zero git changes outside tmp/).

## Test evidence
- Unit/integration: `pytest tests/test_kb_ingest_bulk.py` → **30 passed**; full kb suite
  **302 passed**, 0 regressions. Plugin packaging: **PASSED (14 plugins)**.
- Live smoke (`tmp/cri-bulk-test/library/` via `--library`, 15 files from `tmp_texts/`):
  14/15 extracted (1 graceful failure), 82 routed targets (1 fuzzy-merged), 3 reduced to
  real library files, single shelf-index rebuild (3 entries) + 1 log entry, resume
  skipped 14. Project library untouched.
- Deferred (out of scope, per spec): chunked-reduce for pathological topics; full
  `--libraries` query federation (#209).

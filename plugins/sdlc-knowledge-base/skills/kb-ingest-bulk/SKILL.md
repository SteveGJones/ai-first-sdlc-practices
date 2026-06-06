---
name: kb-ingest-bulk
description: Parallel map-reduce bulk ingest for large source sets. Map phase dispatches read-only knowledge-extractor agents (≤N-wide, default Haiku) emitting per-source JSON extracts; Python routes extracts by target library file (fuzzy-merging new topics, pre-allocating new files, flagging oversized topics); reduce phase dispatches one agent-knowledge-updater per file (parallel, one writer per file); single shelf-index rebuild + one log.md entry. Resumable. Supersedes kb-ingest-batch.
disable-model-invocation: false
argument-hint: "<glob|dir|file-list> [--library <path>] [--parallel <N>] [--extractor-model <id>] [--size-threshold <tokens>] [--retry-failed] [--clean]"
---

# Bulk Ingestion (map-reduce)

Load a large source set into the knowledge base in parallel. Four phases:
**map** (parallel extract) → **route** (Python) → **reduce** (parallel synthesis,
one writer per file) → **finalize** (one rebuild + one log entry).

## Arguments

| Argument | Description |
|---|---|
| `<glob\|dir\|file-list>` | Sources to ingest |
| `--library <path>` | Target library, bypassing CLAUDE.md resolution (default: CLAUDE.md-resolved). For isolated testing / multi-library — see #209 |
| `--parallel <N>` | Concurrency for map + reduce rounds (default 16, max 64) |
| `--extractor-model <id>` | Map model (default `claude-haiku-4-5`) |
| `--size-threshold <tokens>` | Per-file reduce size guard (default 200000) |
| `--retry-failed` | Re-queue failed sources/targets from a prior run |
| `--clean` | Remove `library/.extracts/` after a successful run |

## Preflight

1. Resolve `library_path`: if `--library` given, use it; else read CLAUDE.md
   `## Knowledge Base` section. Derive `shelf_index_path = <library>/_shelf-index.md`,
   `log_path = <library>/log.md`, `extracts_dir = <library>/.extracts`.
2. Verify `knowledge-extractor` and `agent-knowledge-updater` agents are available.
3. Clamp `--parallel` to [1, 64].

## Module bootstrap

Use this `CLAUDE_PLUGIN_ROOT` importlib loader block to import the
`sdlc_knowledge_base_scripts.kb_ingest_bulk` helpers. It is self-contained — no
other file needs to be opened.

```bash
python3 -c "
import sys, os, importlib.util, json
PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
SCRIPTS = os.path.join(PLUGIN_ROOT, 'scripts')
INIT = os.path.join(SCRIPTS, '__init__.py')
if os.path.isfile(INIT) and 'sdlc_knowledge_base_scripts' not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        'sdlc_knowledge_base_scripts', INIT, submodule_search_locations=[SCRIPTS])
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules['sdlc_knowledge_base_scripts'] = mod
        spec.loader.exec_module(mod)
from sdlc_knowledge_base_scripts.kb_ingest_bulk import (
    discover_sources, build_bulk_manifest, load_manifest, save_manifest,
    retry_failed, persist_extract, slug_for_source, mark_source_extracted,
    mark_source_failed, route_extracts, format_extract_prompt,
    format_reduce_prompt, ReduceDispatchRequest, mark_target_reduced,
    mark_target_failed, summarize_run, write_log_entry, ExtractDispatchRequest
)
"
```

## Phase 1 — Map (parallel ≤N)

1. `discover_sources(<spec>)` → source list; `build_bulk_manifest(...)` (merge prior
   manifest via `load_manifest` if present; `retry_failed` if `--retry-failed`);
   `save_manifest`.
2. For each pending source whose extract file does NOT already exist (resume skip):
   dispatch `knowledge-extractor` with `format_extract_prompt(...)`, up to N
   concurrently (parallel Agent-tool calls). Capture each agent's JSON reply.
3. After each agent: `persist_extract(extracts_dir, slug, json)` then
   `mark_source_extracted`; on error/invalid-JSON `mark_source_failed`.
   `save_manifest` after each round.

## Phase 2 — Route (Python, no agents)

4. Load all extract JSON files. Compute `existing_files` = set of `*.md` in the
   library (excluding `_shelf-index.md`, `log.md`, `_index.md`, and anything under `raw/`).
5. `route = route_extracts(extracts, existing_files, size_threshold)`. Record each
   `route.targets` entry into `manifest["targets"]` as `pending` with `source_count`
   and `is_new`. Report `route.oversized` (skipped). `save_manifest`.

## Phase 3 — Reduce (parallel ≤N, one writer per file)

6. For each pending target: dispatch ONE `agent-knowledge-updater` with
   `format_reduce_prompt(ReduceDispatchRequest(...))`, up to N concurrently. Exactly
   one agent per file — never two agents on the same file.
7. After each: `mark_target_reduced` (success) or `mark_target_failed` (error).
   `save_manifest` after each round.

## Phase 4 — Finalize (once)

8. Rebuild the shelf-index once via `build_shelf_index.main([library_path])`.
9. `write_log_entry(log_path, "## [<date>] ingest-bulk\n" + summarize_run(manifest, route.oversized))`.
10. Print the summary table. If `--clean`, remove `extracts_dir`.

## Exit / partial failure

A failed source drops out of routing; a failed target leaves its extracts on disk
for `--retry-failed`. Report all failures + oversized topics. Non-zero exit only if
nothing succeeded.

---
name: kb-ingest-batch
description: Drive agent-knowledge-updater over a batch of staged files in library/raw/. Tracks progress in .batch-progress.json for resume support. Sequential by default; --parallel <N> opt-in (max 5). Single shelf-index rebuild and one consolidated log.md entry at the end.
disable-model-invocation: false
argument-hint: "[<dir-or-manifest>] [--parallel <N>] [--retry-failed]"
---

# Batch Ingestion

Drive `agent-knowledge-updater` over every staged file in `library/raw/`, with progress tracking and resume support. Second stage of the batch workflow: **prepare** (`kb-prepare-batch`) then **ingest** (this skill).

## Arguments

| Argument | Description |
|---|---|
| (none) | Process all `.md` files in `library/raw/` with `status: raw` |
| `<dir>` | Process all `.md` files in this directory |
| `--parallel <N>` | Dispatch up to N agents concurrently (max: 5) |
| `--retry-failed` | Re-queue failed entries from a prior run |

## Resume behaviour

Progress is tracked in `library/raw/.batch-progress.json`. On re-invocation:
- `completed` files are skipped
- `failed` files are left alone unless `--retry-failed` is passed
- New `status: raw` files in raw/ are appended to `pending`

## Preflight

1. Read CLAUDE.md to resolve `library_path`, `shelf_index_path`, `log_path`
2. Verify `agent-knowledge-updater` agent is available

## Steps

### 1. Discover files and build/update manifest

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
from sdlc_knowledge_base_scripts.kb_ingest_batch import (
    discover_raw_files, load_manifest, build_manifest, save_manifest, retry_failed
)
from pathlib import Path
raw_dir = Path('<raw_dir>')
manifest_path = raw_dir / '.batch-progress.json'
existing = load_manifest(manifest_path)
if existing and <retry_failed_flag>:
    existing = retry_failed(existing)
source_files = discover_raw_files(raw_dir)
manifest = build_manifest(source_files, existing=existing)
save_manifest(manifest_path, manifest)
print(json.dumps({'pending': len(manifest['pending']), 'total': manifest['total']}))
"
```

Replace `<raw_dir>` and `<retry_failed_flag>` with resolved values.

### 2. Process pending files (sequential)

For each file in `pending`:

a. **Build the dispatch prompt** using `format_batch_dispatch_prompt()`:
   ```
   BATCH_MODE: create-only

   Integrate the following source into the knowledge base. Batch mode constraints:
   (1) Do NOT modify existing library files — record conflict-existing-file status and stop;
   (2) Do NOT run kb-rebuild-indexes;
   (3) Do NOT append to log.md.

   Source: <path>
   Library: <library_path>
   Shelf-index: <shelf_index_path>
   ```

b. **Dispatch `agent-knowledge-updater`** with this prompt using the Agent tool.

c. **Update manifest** after each dispatch (atomic write):
   - Success or conflict-existing-file → `mark_completed()`
   - Error or timeout → `mark_failed()`

d. **Parallel mode** (`--parallel <N>`): dispatch up to N agents concurrently using parallel Agent tool calls. Update manifest after each group.

### 3. Final phase

After all dispatches complete:

a. **Rebuild shelf-index** (one run):
```bash
python3 -c "... from sdlc_knowledge_base_scripts.build_shelf_index import main; sys.exit(main(['<library_path>']))"
```

b. **Write consolidated log.md entry**:
```markdown
## [YYYY-MM-DD] ingest-batch | <total>/<succeeded>/<failed>
```

c. **Print summary table**.

## BATCH_MODE constraints on agent-knowledge-updater

Every dispatch includes `BATCH_MODE: create-only`. The agent:
1. Does NOT modify existing library files (records `conflict-existing-file`)
2. Does NOT run `kb-rebuild-indexes`
3. Does NOT append to `log.md`

Run `/sdlc-knowledge-base:kb-ingest` individually for conflict files.

---
name: kb-stats
description: Pure-Python knowledge base statistics dashboard. Reads shelf-index and log.md; emits Inventory, Layer distribution, Domain distribution, Recent Activity, and Staleness sections. No agent dispatch. Read-only.
disable-model-invocation: false
argument-hint: "[--output <path>] [--since <ISO-date>]"
---

# Knowledge Base Statistics

> **Lightweight**: This skill reads only index metadata (shelf-index + log.md). Inline execution is acceptable — no agent dispatch needed.

Surfaces library health metrics in a single markdown report.

## Arguments

- `--output <path>` — Write report to a file instead of stdout
- `--since <ISO-date>` — Override the recent-activity window start date (default: 30 days ago)

## Preflight

Read CLAUDE.md `[Knowledge Base]` section to resolve `library_path` (default `library/`) and `shelf_index_path` (default `library/_shelf-index.md`).

## Steps

### 1. Resolve configuration

Extract `library_path`, `shelf_index_path`, and `log_path` (default `library/log.md`) from CLAUDE.md.

### 2. Run kb_stats.py

```bash
python3 -c "
import sys, os, importlib.util
PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
SCRIPTS = os.path.join(PLUGIN_ROOT, 'scripts')
INIT = os.path.join(SCRIPTS, '__init__.py')
if os.path.isfile(INIT) and 'sdlc_knowledge_base_scripts' not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        'sdlc_knowledge_base_scripts', INIT,
        submodule_search_locations=[SCRIPTS])
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules['sdlc_knowledge_base_scripts'] = mod
        spec.loader.exec_module(mod)
from sdlc_knowledge_base_scripts.kb_stats import main
args = ['--library-path', '<library_path>',
        '--shelf-index-path', '<shelf_index_path>',
        '--log-path', '<log_path>']
# If --output <path> passed: args += ['--output', '<output_path>']
# If --since <date> passed:  args += ['--since', '<since_date>']
sys.exit(main(args))
"
```

### 3. Report results

Print the markdown report (5 sections). If `--output` was passed, confirm the file was written.

## What this skill does NOT do

- Does not validate citations (`kb-validate-citations` does that)
- Does not detect contradictions (`kb-lint` does that)
- Does not query findings (`kb-query` does that)
- Does not invoke any agent

## Errors

- **Library directory not found** — run `/sdlc-knowledge-base:kb-init` first
- **No shelf-index** — run `/sdlc-knowledge-base:kb-rebuild-indexes` first

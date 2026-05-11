---
name: kb-audit-query
description: Filter and summarise the cross-library KB audit log. Reports confidentiality events (attribution drops, synthesis aborts, dispatcher failures, no-evidence markers, cross-library promotions) over a date range, by event type, and by source handle.
disable-model-invocation: false
argument-hint: "[--since <ISO-date>] [--until <ISO-date>] [--event-type <type>] [--source <handle>] [--summary]"
---

# Audit Log Query

> **Lightweight**: This skill reads only index metadata (timestamps / audit log entries). Inline execution is acceptable.

Filter and summarise events from `library/audit.log` for the current project. The audit log is project-scope (lives in the project's library directory) and append-only; this skill is read-only.

## Arguments

All optional:

- `--since <ISO-date>` — events at or after this timestamp (e.g., `2026-01-01T00:00:00Z`)
- `--until <ISO-date>` — events at or before this timestamp
- `--event-type <type>` — one of: `attribution_drop_retrieval`, `synthesis_aborted_attribution`, `synthesis_aborted_dispatcher_error`, `source_dispatch_failed`, `no_evidence_marker`, `cross_library_promotion`
- `--source <handle>` — events for this library handle only
- `--summary` — emit count-by-type summary instead of detailed event list

## Steps

### Preflight: verify scripts package importable

```bash
python3 -c "
import sys, os, importlib.util
PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
SCRIPTS = os.path.join(PLUGIN_ROOT, 'scripts')
INIT = os.path.join(SCRIPTS, '__init__.py')
if os.path.isfile(INIT) and 'sdlc_knowledge_base_scripts' not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        'sdlc_knowledge_base_scripts',
        INIT,
        submodule_search_locations=[SCRIPTS],
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules['sdlc_knowledge_base_scripts'] = module
        spec.loader.exec_module(module)
try:
    import sdlc_knowledge_base_scripts.audit  # noqa: F401
    print('OK')
except ImportError:
    print('MISSING')
"
```

If output is `MISSING`, see kb-query for the install fallback. Otherwise prepend the importlib preamble to subsequent snippets.

### 1. Read and filter

```bash
python3 -c "
import sys, os, importlib.util, json
PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
SCRIPTS = os.path.join(PLUGIN_ROOT, 'scripts')
INIT = os.path.join(SCRIPTS, '__init__.py')
if os.path.isfile(INIT) and 'sdlc_knowledge_base_scripts' not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        'sdlc_knowledge_base_scripts',
        INIT,
        submodule_search_locations=[SCRIPTS],
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules['sdlc_knowledge_base_scripts'] = module
        spec.loader.exec_module(module)

from pathlib import Path
from sdlc_knowledge_base_scripts.audit import read_log

events = read_log(
    Path('library/audit.log'),
    event_type=<event-type or None>,
    source_handle=<source or None>,
    since=<since or None>,
    until=<until or None>,
)
print(json.dumps([e.__dict__ for e in events], indent=2))
"
```

Substitute the actual argument values into the read_log call. Quote string args; use Python None literal for unspecified ones.

### 2. Summarise (if --summary)

If `--summary` was specified, group results by event_type and count:

```python
from collections import Counter
counts = Counter(e.event_type for e in events)
for event_type, count in counts.most_common():
    print(f"{event_type}: {count}")
```

### 3. Render results

Render either:

- **Detailed view** (default): one block per event with timestamp, event_type, source_handle, reason, detail summary
- **Summary view** (`--summary`): count by type, then "see kb-audit-query --event-type X for details"

## Examples

Show all events in the last 90 days:

```
/sdlc-knowledge-base:kb-audit-query --since 2026-01-26T00:00:00Z
```

Count events by type for the last quarter:

```
/sdlc-knowledge-base:kb-audit-query --since 2026-01-01T00:00:00Z --summary
```

Investigate attribution drops on a specific source:

```
/sdlc-knowledge-base:kb-audit-query --event-type attribution_drop_retrieval --source corp-semi
```

## What this skill does NOT do

- It does not modify the audit log (read-only)
- It does not query other projects' audit logs (project-scope)
- It does not export audit data to external systems (the JSON output can be redirected if needed)

## Errors

- **Audit log file missing** — emit "No audit log at library/audit.log. Either no events have been logged yet, or this project has no library/ directory."
- **Malformed log file** — read_log skips malformed lines; the output may be smaller than expected

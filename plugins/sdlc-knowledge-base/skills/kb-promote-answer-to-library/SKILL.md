---
name: kb-promote-answer-to-library
description: File a librarian query result back into the library as a new page with provenance tracking. Karpathy's "good answers can be filed back into the wiki as new pages" insight made concrete. The library compounds from explorations, not just from external sources.
disable-model-invocation: false
argument-hint: "<query-result-text-or-file> [--title <title>] [--path <library-file-path>] [--target <handle>]"
---

# Promote Answer to Library

> **Agent-only**: Dispatch this operation via the Agent tool (`research-librarian` for queries/lint/validate, `agent-knowledge-updater` for ingest/promote). Running inline fills the main session context and degrades subsequent tasks. See `CLAUDE-CONTEXT-knowledge-base.md`.

When the librarian answers a query well — a comparison, an analysis, a connection between findings the library hadn't explicitly captured — that answer is itself valuable. It shouldn't disappear into chat history. This skill files the answer back into the library as a new page so explorations compound just like ingested sources do.

This is Karpathy's "good answers can be filed back into the wiki as new pages" insight from the LLM Wiki gist.

## Arguments

- **Query result** (required) — the text of the answer to file. Can be:
  - A file path containing the answer
  - The answer text passed inline
  - The output of a recent `kb-query` invocation (when called with `kb-query --promote-to-library`, this is automatic)
- **`--title <title>`** (optional) — explicit title for the new library file. If omitted, derive from the query that produced the answer (extract from the answer's heading or first paragraph).
- **`--path <library-file-path>`** (optional) — explicit destination path. If omitted, derive from the title using kebab-case conversion (e.g., `library/cycle-time-and-pi-planning.md`).
- **`--target <handle>`** (optional) — the registered library handle to promote into. When omitted, promotes to the local library (default behaviour, backwards compatible). When set to a registered external library handle:
  - The handle must resolve in `~/.sdlc/global-libraries.json`
  - The library must be filesystem type (remote-agent rejected)
  - The library's directory must be writeable
  - The promotion writes a new file there + updates that library's shelf-index

## Preflight

- Verify the knowledge base is configured.
- Verify the destination path doesn't already exist (no overwriting; if the user wants to update an existing file, they edit it directly and run `kb-rebuild-indexes`).

## Steps

### 1. Parse the answer

Extract from the answer text:
- The claim or topic (becomes the file's `## Key Question` answer)
- The supporting findings with their citations (becomes `## Core Findings`)
- Any caveats or contradictions noted (becomes part of `## Design Principles` or a dedicated `## Caveats` subsection)
- The library files the librarian referenced (becomes the `derived_from` frontmatter and `cross_references`)

The librarian's output format is structured, so this parsing is mechanical when the answer came from `kb-query`. For free-form answers, extract heuristically.

### 2. Determine title and path

If `--title` provided, use it. Otherwise extract from:
1. The first `### <heading>` in the answer
2. The first sentence's noun phrase
3. Fall back to "synthesis-<timestamp>" if nothing extracts cleanly

If `--path` provided, use it. Otherwise derive: kebab-case the title, prepend `library/`, append `.md`.

If the destination already exists, abort with: "Destination `<path>` already exists. Use `--path` to specify an alternative or edit the existing file directly."

### 3. Resolve and validate target

If `--target <handle>` was specified:

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

from pathlib import Path
from sdlc_knowledge_base_scripts.registry import (
    load_global_registry, validate_library_path
)

handle = '<--target argument>'
gr = load_global_registry(Path(os.path.expanduser('~/.sdlc/global-libraries.json')))
matches = [lib for lib in gr.libraries if lib.name == handle]
if not matches:
    print(f'ERROR: target handle {handle!r} not registered')
    exit(1)
entry = matches[0]
if entry.type != 'filesystem':
    print(f'ERROR: target {handle!r} is type {entry.type!r}; remote-agent promotion is not supported in v1')
    exit(1)
ok, reason = validate_library_path(Path(entry.path))
if not ok:
    print(f'ERROR: target path invalid: {reason}')
    exit(1)
target_dir = Path(entry.path)
test_file = target_dir / '.kb-promote-write-test'
try:
    test_file.write_text('')
    test_file.unlink()
except OSError as exc:
    print(f'ERROR: target directory not writeable: {exc}')
    exit(1)
print(f'OK: target {handle!r} -> {entry.path}')
"
```

If the validator emits ERROR, surface it to the user and stop. The default behaviour (no `--target`, write to local `library/`) is unchanged.

Set `TARGET_DIR` to the resolved external library path if `--target` was specified, or to `library/` (relative to the local knowledge base root) if omitted.

### 4. Construct the library file

Use the library file format with provenance metadata:

```markdown
---
title: "<title from arg or extracted>"
domain: <inherit from source files' domains, deduplicated>
status: active
provenance: synthesis
derived_from:
  - <source library file 1>
  - <source library file 2>
  - <source library file 3>
synthesised_at: <ISO date>
synthesised_by: kb-promote-answer-to-library
tags: <inherit from source files' tags>
cross_references:
  - <source library file 1>
  - <source library file 2>
  - <source library file 3>
---

## Key Question

<the question this synthesis answers — derived from the query that produced the answer, or stated explicitly>

## Core Findings

<the answer's findings, preserving the original citations from the source library files>

## Frameworks Reviewed

<copy any frameworks discussed in the answer; if the answer didn't discuss frameworks, omit this section or note "(none — this is a synthesis page)">

## Actionable Thresholds

<any specific numbers or thresholds the synthesis surfaces; copy from source files if not in the answer>

## Design Principles

<the synthesised conclusions or recommendations from the answer>

## Key References

<all citations from the source library files; deduplicate; preserve formatting>

## Programme Relevance

This is a synthesis page. The librarian produced this answer by combining findings from the files listed in `derived_from`. To update this synthesis, either:
1. Re-query the librarian on the same question and re-promote
2. Edit this file directly and run kb-rebuild-indexes

The lint operation may flag this synthesis as stale if any of its source files change after `synthesised_at`. That's the signal to re-query and re-promote.
```

### 5. Write the file

Use Write to create the new library file at `<TARGET_DIR>/<filename>.md` (where `TARGET_DIR` is the resolved value from Step 3). Verify the write succeeded.

### 6. Update the shelf-index

Invoke `/sdlc-knowledge-base:kb-rebuild-indexes` (incremental) against `<TARGET_DIR>`. The new file will be added to that library's index automatically.

### 7. Write audit event (only when --target was used)

If `--target <handle>` was specified, write a `cross_library_promotion` audit event to the project's audit log:

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

from pathlib import Path
from datetime import datetime, timezone
from sdlc_knowledge_base_scripts.audit import log_event, AuditEvent

log_event(Path('library/audit.log'), AuditEvent(
    timestamp=datetime.now(timezone.utc).isoformat(),
    event_type='cross_library_promotion',
    query='<question or topic that produced the answer>',
    source_handle='<--target handle>',
    reason='answer promoted to external library',
    detail={
        'source_file': '<local file path or answer source identifier>',
        'target_path': '<absolute path to target library file just written>',
    },
))
"
```

The audit log lives at `library/audit.log` in the current project (project-scope, append-only). The `cross_library_promotion` event records that knowledge moved from this engagement into a corporate library — useful for asking later "show me every cross-library promotion this quarter."

Substitute the actual question/topic, target handle, source file, and target path values into the snippet.

If --target was NOT used (default local-only promotion), skip this step.

### 8. Append to log.md

```markdown
## [YYYY-MM-DD] promote-answer | <title>

Source: kb-query result
Derived from: <source library files>
New file: <destination path>
Target: <handle if --target was specified, otherwise "local">
```

### 9. Final report

```
Answer promoted to: <TARGET_DIR>/<filename>.md
Target shelf-index updated: <TARGET_DIR>/_shelf-index.md
```

If `--target` was used (external promotion), also output:

```
Audit event written: cross_library_promotion (target=<handle>)

NOTE: the target library is a separate filesystem location, possibly
in its own git repo. This skill does NOT auto-commit or push the
target library. To complete promotion:
  cd <target-repo-root>
  git add library/<filename>.md library/_shelf-index.md
  git commit -m "..."
  git push
```

This reminds the user that the corporate library has its own version control discipline.

If `--target` was NOT used (local promotion, default), output:

```
Note: this file is a synthesis. The lint operation will flag it as
stale if any source files change after today's date. To refresh,
re-query the librarian and re-promote.
```

## Provenance tracking

Synthesis files are explicitly distinguished from primary research files by:
- `provenance: synthesis` in frontmatter
- `derived_from` array listing source files
- `synthesised_at` timestamp
- The note in `## Programme Relevance`

This matters because:
- Future librarian queries can decide whether to trust synthesis files at the same level as primary research (configurable)
- The lint operation can flag synthesis files whose source files have changed since synthesis (staleness)
- A user reviewing the library can distinguish "what the original research said" from "what the librarian inferred"

Synthesis files are second-class citizens in a sense, but they're also where exploration compounds. Karpathy is explicit that this is the most valuable insight beyond just retrieval — and the production projects bear it out when they use it.

## What this skill does NOT do

- It does not invoke the librarian — that's `kb-query`. This skill takes an existing answer and files it.
- It does not modify the source library files referenced in `derived_from`
- It does not validate the answer's citations — run `kb-validate-citations` separately
- It does not auto-promote every query result — promotion is always explicit (the user decides what's worth keeping)
- It does not auto-commit or push a target external library — that library has its own git discipline

## Errors

- **No knowledge base configured** — run `/sdlc-knowledge-base:kb-init` first
- **Destination already exists** — pick a different path or edit the existing file
- **Answer is unparseable** — the answer text doesn't contain enough structure to extract findings; recommend re-querying with a more structured prompt
- **No source files referenced in the answer** — the answer wasn't from the librarian (or the librarian failed to cite); recommend re-querying
- **Target handle not registered** — run `/sdlc-knowledge-base:kb-query` to list registered libraries, or check `~/.sdlc/global-libraries.json`
- **Target is remote-agent type** — only filesystem libraries support direct promotion in v1; use the target library's own ingestion workflow
- **Target directory not writeable** — check permissions on the external library path

## Example

```
/sdlc-knowledge-base:kb-query "How do DORA metrics interact with SAFe-style PI planning?" --promote-to-library

# librarian returns its synthesis answer
# kb-promote-answer-to-library is invoked automatically with --promote-to-library

Promoted answer to library: library/dora-and-safe-pi-planning.md

  Title: DORA Metrics and SAFe PI Planning Interaction
  Provenance: synthesis (derived from 3 source files)
  Source files:
    - library/dora-metrics.md
    - library/safe-essentials.md
    - library/programme-cadence.md
  Index rebuilt: yes
  Log entry: yes
```

Cross-library promotion example:

```
/sdlc-knowledge-base:kb-promote-answer-to-library answer.md --target corporate-semi

Answer promoted to: /opt/corporate-kb/library/dora-and-safe-pi-planning.md
Target shelf-index updated: /opt/corporate-kb/library/_shelf-index.md
Audit event written: cross_library_promotion (target=corporate-semi)

NOTE: the target library is a separate filesystem location, possibly
in its own git repo. This skill does NOT auto-commit or push the
target library. To complete promotion:
  cd /opt/corporate-kb
  git add library/dora-and-safe-pi-planning.md library/_shelf-index.md
  git commit -m "promote synthesis: DORA and SAFe PI Planning"
  git push
```

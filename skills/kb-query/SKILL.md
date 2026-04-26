---
name: kb-query
description: Query the project knowledge base. Wraps the research-librarian agent. The librarian reads the shelf-index, identifies the 2-4 most relevant library files for the question, deep-reads only those, and returns structured evidence with citations. Stateless — reads the index fresh on every query.
disable-model-invocation: false
argument-hint: "<question> [--promote-to-library]"
---

# Knowledge Base Query

Ask a question against the project's knowledge base. This is the **query** operation in the three-operations model (ingest / query / lint).

## Argument

A natural-language question. Two forms:

- **Retrieval**: "What does our research say about X?" — returns specific findings with citations
- **Synthesis**: "Build me the case for X" or "How should we think about X?" — returns a connected argument across multiple findings with caveats

Optional flag:

- `--promote-to-library` — after the librarian answers, file the answer back into the library as a new page via `kb-promote-answer-to-library`. Use when the answer is worth keeping for future queries.

## Preflight

- Verify the `research-librarian` agent is available.
- Library availability and shelf-index presence are checked in Step 1 via the registry resolver — no manual path checks needed here.

## Preflight: verify scripts package importable

Before running any subsequent step, verify the kb scripts package can be imported:

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
    import sdlc_knowledge_base_scripts.registry  # noqa: F401
    print('OK')
except ImportError:
    print('MISSING')
"
```

If output is `MISSING`, prepend this preamble to every subsequent bash snippet in this skill:

```python
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
```

The `CLAUDE_PLUGIN_ROOT` environment variable is set by Claude Code when it loads the plugin. The scripts subdirectory is always packaged as `<plugin>/scripts/`. If `CLAUDE_PLUGIN_ROOT` is not set (running outside Claude Code), the user can either set it manually (`export CLAUDE_PLUGIN_ROOT=plugins/sdlc-knowledge-base`) or editable-install the plugin (`pip install -e plugins/sdlc-knowledge-base`).

## Steps

### 1. Preflight — load the dispatch list

Run the registry resolver helper to determine which sources to dispatch against:

```bash
python3 -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import load_global_registry, load_project_activation, resolve_dispatch_list
import json, os

global_reg = load_global_registry(Path(os.path.expanduser('~/.sdlc/global-libraries.json')))
activation = load_project_activation(Path('.sdlc/libraries.json'))
dispatch = resolve_dispatch_list(global_reg, activation, Path('library'))

print(json.dumps({
  'sources': [{'name': s.name, 'path': s.path} for s in dispatch.sources],
  'warnings': global_reg.warnings + activation.warnings + dispatch.warnings,
  'is_empty_error': dispatch.is_empty_error,
}, indent=2))
"
```

If `is_empty_error` is true, print:

> No knowledge base available. Run `/sdlc-knowledge-base:kb-init` to create a local library, or register and activate an external library with `/sdlc-knowledge-base:kb-register-library`.

and stop.

Print all warnings from the helper to stderr (not to user-facing output).

### 2. Build the priming bundle

```bash
python3 -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.priming import build_priming_bundle
import json

bundle = build_priming_bundle(question='<the user question>', project_dir=Path('.'))
print(json.dumps({
  'question': bundle.question,
  'local_kb_config_excerpt': bundle.local_kb_config_excerpt,
  'local_shelf_index_terms': bundle.local_shelf_index_terms,
}, indent=2))
"
```

The bundle's contents flow into each librarian dispatch via `format_dispatch_prompt`
in Step 3. The librarian uses `local_shelf_index_terms` to bias term-matching against
its scoped shelf-index, and `local_kb_config_excerpt` to frame findings in the local
project's lens (see the librarian agent's `PRIMING_CONTEXT` documentation).

### 3. Format and dispatch one librarian per source — in parallel

For each source in the dispatch list, render the librarian prompt via the orchestrator's
helper (it produces the exact `SCOPE: / SOURCE_HANDLE: / PRIMING_CONTEXT:` shape the
librarian expects):

```bash
python3 -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.orchestrator import format_dispatch_prompt
from sdlc_knowledge_base_scripts.priming import PrimingBundle
from sdlc_knowledge_base_scripts.registry import LibrarySource
import json

# Reconstruct the priming bundle from the JSON produced in Step 2
priming_data = json.loads('<priming_bundle_json_from_step_2>')
priming = PrimingBundle(
    question=priming_data['question'],
    local_kb_config_excerpt=priming_data['local_kb_config_excerpt'],
    local_shelf_index_terms=priming_data['local_shelf_index_terms'],
)

source = LibrarySource(name='<source.name>', type='filesystem', path='<source.path>')
prompt = format_dispatch_prompt(
    source=source,
    question='<the user question>',
    priming=priming,
)
print(prompt)
"
```

Then use the **Agent tool** to invoke the `research-librarian` agent *once per source* in
the dispatch list. Issue ALL invocations in a SINGLE message so they run in parallel
(Claude's parallel tool-call capability). Pass each source's rendered prompt as the
agent's input.

The rendered prompt structure looks like:

```
SCOPE: <source.path>
SOURCE_HANDLE: <source.name>
PRIMING_CONTEXT:
{
  "local_kb_config_excerpt": "...",
  "local_shelf_index_terms": [...]
}

Question: <the user question>

Read the shelf-index at <source.path>/_shelf-index.md, identify the 2-4
most relevant library files for the question, deep-read only those, and
return findings in the retrieval format. Every finding block must include
a **Source library**: <source.name> line (see your agent prompt).

Do not read any files outside <source.path>. Do not emit --- horizontal
rules inside a finding block (they are treated as structural separators
by the post-check tokenizer).
```

The librarian agent's prompt spec defines how it consumes `PRIMING_CONTEXT` — the orchestrator
helper, the librarian prompt, and this skill stay in lockstep on the format.

### 4. Collect per-source outputs and run attribution post-check

Each librarian returns its findings (or "no evidence on this topic" if the scoped library has nothing, or an error). Collect each source's output, keyed by source.name.

Then run the orchestrator to apply per-source attribution post-check and render the combined output:

```bash
python3 -c "
# The orchestrator is designed to take a dispatcher callable. In this
# skill, you have already dispatched via the Agent tool and have the
# outputs in hand. Call the pure-Python post-processing directly.
from sdlc_knowledge_base_scripts.orchestrator import run_retrieval_query, DispatchRequest
from sdlc_knowledge_base_scripts.priming import PrimingBundle
from sdlc_knowledge_base_scripts.registry import LibrarySource
import json

# Reconstruct sources from the dispatch list (step 1) and build a
# pass-through dispatcher that returns the already-collected outputs.
collected = {
    'local': '<output from local librarian>',
    'corporate-semi': '<output from corporate-semi librarian>',
    # ... one entry per source
}

def pass_through(req: DispatchRequest) -> str:
    return collected[req.source.name]

sources = [
    LibrarySource(name='local', type='filesystem', path='<path>'),
    # ... one entry per activated source
]

# Reconstruct from Step 2's JSON output if not already in scope
priming_data = json.loads('<priming_bundle_json_from_step_2>')
priming = PrimingBundle(
    question=priming_data['question'],
    local_kb_config_excerpt=priming_data['local_kb_config_excerpt'],
    local_shelf_index_terms=priming_data['local_shelf_index_terms'],
)

result = run_retrieval_query(
    question='<the user question>',
    sources=sources,
    priming=priming,  # built in Step 2, formatted into each dispatch by Step 3
    dispatcher=pass_through,
    audit_log_path=Path('library/audit.log'),
)
print(result.combined_output)
"
```

Alternatively, assemble the combined output manually by:
- Writing a header with `**Sources queried:**`, `**Sources with findings:**`, `**Sources that failed:**` lines
- For each source in order (local first, externals alphabetical), wrap its output in a `## [source-name] Findings` section
- Joining with `\n\n---\n\n` separators
- Calling `check_retrieval_attribution` per-source to drop any untagged findings

The orchestrator helper is the preferred approach for consistency.

### 5. If the `--promote-to-library` flag was specified

Same behaviour as before — dispatch `kb-promote-answer-to-library` with the answer. Promotion writes only to the **local** library; external libraries are read-only from this project.

### 6. Cross-library synthesis (when the question calls for it)

After Step 5, decide whether to run synthesis. The orchestrator's
`run_synthesis_query` handles the decision and the dispatch:

```bash
python3 -c "
from sdlc_knowledge_base_scripts.orchestrator import (
    run_synthesis_query,
    format_synthesis_prompt,
    is_synthesis_query,
    RetrievalQueryResult,
)
from sdlc_knowledge_base_scripts.priming import PrimingBundle
from sdlc_knowledge_base_scripts.registry import LibrarySource
import json

# Reconstruct the retrieval result, sources, and per-source findings collected in Steps 3-5
retrieval = RetrievalQueryResult(
    combined_output='<combined retrieval output from Step 5>',
    sources_with_findings=['<list of source names that returned findings>'],
)
sources = [
    LibrarySource(name='<source.name>', type='filesystem', path='<source.path>'),
    # ... one entry per dispatched source
]
per_source = {
    '<source.name>': '<raw librarian output for that source>',
    # ... one entry per source that returned findings
}
priming_data = json.loads('<priming_bundle_json_from_step_2>')
priming = PrimingBundle(
    question=priming_data['question'],
    local_kb_config_excerpt=priming_data['local_kb_config_excerpt'],
    local_shelf_index_terms=priming_data['local_shelf_index_terms'],
)

# is_synthesis_query handles the heuristic check; run_synthesis_query decides
# whether to actually dispatch (it will skip if <2 sources have findings)
def synthesis_dispatcher(prompt):
    # In the real skill, this wraps the Agent tool: dispatch one
    # synthesis-librarian invocation with the synthesis prompt as input.
    raise NotImplementedError('replace with Agent tool dispatch in the skill body')

result = run_synthesis_query(
    question='<the user question>',
    retrieval=retrieval,
    priming=priming,
    sources=sources,
    synthesis_dispatcher=synthesis_dispatcher,
    per_source_findings=per_source,
    audit_log_path=Path('library/audit.log'),
)
print(result.combined_output)
"
```

In the actual skill flow, replace the `synthesis_dispatcher` placeholder with the
**Agent tool** invocation: when `is_synthesis_query(question)` returns True AND at
least 2 sources have findings, use the **Agent tool** to invoke the `synthesis-librarian` agent (NOT research-librarian — synthesis-librarian has tools: [] which makes 'no file reads' structural) with the synthesis prompt as its input. Otherwise, skip — the orchestrator detects this and
returns the retrieval output unchanged.

The dispatched synthesis prompt looks like:

```
MODE: SYNTHESISE-ACROSS-SOURCES
PRIMING_CONTEXT:
{
  "local_kb_config_excerpt": "...",
  "local_shelf_index_terms": [...]
}

Question: <the user question>

Per-source findings (your only source of facts — do not read any files):

--- [local] ---
<local librarian's findings>

--- [corp-semi] ---
<corp-semi librarian's findings>

Produce a single connected argument that addresses the question, drawing on
the findings above. Use the synthesis output format (Claim / Supporting
evidence / Caveats / Programme application).

MANDATORY: every claim in the Supporting evidence list must carry an inline
[<handle>] tag identifying which source library it came from ...
```

The synthesis-librarian agent's prompt describes how to consume this; the orchestrator's `format_synthesis_prompt` produces it; the skill, agent prompt, and orchestrator stay in lockstep on the format.

After the synthesis call returns, the orchestrator runs `check_synthesis_attribution` (with `valid_handles` drawn from the dispatch sources) on the librarian's output. If any supporting-evidence claim lacks an inline `[handle]` tag, or the bracketed token is not in the source whitelist (e.g., `[TODO]`, `[0]`), the synthesis is aborted: the retrieval output is preserved and an explanatory error block is appended. The user always sees something they can act on.

## Audit logging

Every query writes confidentiality events (attribution drops, synthesis aborts, dispatcher failures) to `library/audit.log` for later audit via `/sdlc-knowledge-base:kb-audit-query`. The audit log is project-scope (lives in this project's `library/`) and append-only.

## What this skill does NOT do

- It does not modify library files — the librarian is read-only
- It does not invent answers when no library has evidence
- It does not ingest new sources — that's `/sdlc-knowledge-base:kb-ingest` (local only in v1)
- It does not lint the library — that's `/sdlc-knowledge-base:kb-lint` (local only in v1)
- It does not write to external libraries — they are strictly read-only from the querying project's perspective
- It does not blend findings without attribution — every finding carries its source library handle, enforced by structural post-check
- It does not synthesise across libraries when fewer than 2 sources have findings — the orchestrator skips synthesis and returns the retrieval output unchanged

## Examples

**Retrieval query:**
```
/sdlc-knowledge-base:kb-query "What does our research say about cycle time as a delivery metric?"
```

Expected response: structured findings with DORA citations, sample sizes, thresholds, library file references.

**Synthesis query:**
```
/sdlc-knowledge-base:kb-query "Build me the case for adopting trunk-based development"
```

Expected response: per-source findings from all activated libraries, then a cross-library synthesis section (Claim / Supporting evidence / Caveats / Programme application) drawn from both sources.

**Query with promotion:**
```
/sdlc-knowledge-base:kb-query "How do DORA metrics interact with SAFe-style PI planning?" --promote-to-library
```

Expected: the librarian answers; the answer is then filed back into the **local** library as a new file (likely `dora-vs-safe-pi.md`) with provenance pointing at the source files the librarian read.

**Multi-source query (two activated libraries):**
```
/sdlc-knowledge-base:kb-query "What patterns exist for platform engineering team topologies?"
```

Expected: two parallel `research-librarian` invocations — one scoped to `library/`, one scoped to the activated external path. Output rendered with `## [local] Findings` and `## [corporate-platform] Findings` sections, joined by `---` separators, with header:

**Sources queried:** local, corporate-platform
**Sources with findings:** local, corporate-platform

**Out-of-scope query:**
```
/sdlc-knowledge-base:kb-query "What is the airspeed velocity of an unladen swallow?"
```

Expected response: "The library has no evidence on this. The closest entries are <none>. Recommendation: this query is out of scope for the project knowledge base."

## Errors

- **No knowledge base configured** — run `/sdlc-knowledge-base:kb-init` first
- **Shelf-index missing** — run `/sdlc-knowledge-base:kb-rebuild-indexes` first
- **Plugin not installed** — install `sdlc-knowledge-base@ai-first-sdlc`
- **Library is empty** — no library files exist yet. Add raw sources to `library/raw/` and run `/sdlc-knowledge-base:kb-ingest` to populate the library.
- **No sources available** — no local library + no activated external libraries. Run `/sdlc-knowledge-base:kb-init` or activate a library in `.sdlc/libraries.json`.
- **External source path unmounted** — the query proceeds with other sources; the failed source appears as a marker in the output.
- **External source missing shelf-index** — same as above; run `/sdlc-knowledge-base:kb-rebuild-indexes` in the external library.

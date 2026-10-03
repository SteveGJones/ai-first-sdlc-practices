---
name: kb-setup-consulting
description: Onboarding workflow for cross-library KB query in a consulting practice. Discovers existing user-scope library registrations, prompts for additions, validates each library, helps activate the relevant ones for the current project, runs a smoke test, and reports a clear "ready" or "issues to fix" verdict. Use --verify-only to skip prompting and just validate existing setup (sub-task 23 of #176).
disable-model-invocation: false
argument-hint: "[--dry-run] [--verify-only]"
---

# Cross-Library KB Onboarding

Walk a new consultant or a fresh project through KB cross-library setup. Replaces the hand-walked sequence of "discover ~/.sdlc/global-libraries.json, get paths from someone, run kb-register-library or hand-edit, test it manually" with a single skill.

## Modes

- **Default** — full interactive setup (discover → add → validate → activate → smoke-test → report)
- **--dry-run** — go through discovery + validation but don't write to `.sdlc/libraries.json` or modify any files
- **--verify-only** — skip prompting; just validate existing registry + activation and report status (covers Task 23 functionality)

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
    import sdlc_knowledge_base_scripts.registry
    print('OK')
except ImportError:
    print('MISSING')
"
```

If MISSING, see kb-query for fallback options.

### 1. Discover existing user-scope registrations

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
from sdlc_knowledge_base_scripts.registry import load_global_registry, validate_library_path
from sdlc_knowledge_base_scripts.shelf_index_header import parse_shelf_index_header

gr = load_global_registry(Path(os.path.expanduser('~/.sdlc/global-libraries.json')))
print(f'Registered libraries: {len(gr.libraries)}')
for lib in gr.libraries:
    print(f'  {lib.name}  ({lib.type})  -> {lib.path}')
    if lib.type == 'filesystem' and lib.path:
        ok, reason = validate_library_path(Path(lib.path))
        if ok:
            header = parse_shelf_index_header(Path(lib.path) / '_shelf-index.md')
            print(f'    last_rebuilt: {header.last_rebuilt}, handle: {header.library_handle}')
        else:
            print(f'    INVALID: {reason}')
for w in gr.warnings:
    print(f'  Warning: {w}')
"
```

This shows what's already known + the validation status of each registration.

### 2. Prompt for additions (skip in --verify-only mode)

In default mode: ask the user if they want to register additional libraries beyond what's already there. For each one:

- Get handle, absolute path, optional description
- Validate via `validate_library_path` (the kb-register-library skill's logic)
- If valid, append to `~/.sdlc/global-libraries.json` (preserving the JSON structure)

If the user has no additions, proceed to step 3.

In --verify-only mode: skip this step. Just report on what's already registered.

### 3. Validate all registrations

For every library in the (possibly updated) registry:

- Path validation: validate_library_path returns OK
- Header parse: shelf-index has at least format_version
- Handle consistency: if shelf-index has library_handle, it must match the registry name

Report per-library status. Don't block on a single failure — list them all so the user has a punch-list.

### 4. Per-project activation (skip in --verify-only mode)

In default mode:

```bash
# Read current activation
test -f .sdlc/libraries.json && cat .sdlc/libraries.json || echo '{"version": 1, "activated_sources": []}'
```

Show the user the list of registered library handles. Ask which apply to this engagement (multi-select). Write the activated handles to `.sdlc/libraries.json`:

```bash
mkdir -p .sdlc
cat > .sdlc/libraries.json <<'EOF'
{
  "version": 1,
  "activated_sources": ["<selected handles>"]
}
EOF
```

In --verify-only mode: just read and report what's currently activated.

### 5. Smoke test

For each activated library, dispatch a trivial query via the **research-librarian** Agent tool:

```
SCOPE: <library path>
SOURCE_HANDLE: <library handle>

Question: test connection — what is the most recent finding in your library?

Read the shelf-index, identify any one library file, deep-read it, and return its title and one fact. This is a smoke test confirming the library is queryable.
```

Capture which sources respond successfully. A source that returns valid findings → smoke test passed for that source. A source that errors or returns "no evidence" → smoke test note (the latter may be expected for a fresh empty library).

### 6. Final report

Output one of:

**Ready (all sources smoke-test passed):**
```
✓ KB environment ready
  Registered libraries: 3 (corp-semi, corp-health, internal-research)
  Activated for this project: 2 (corp-semi, internal-research)
  Smoke test: 2 of 2 passed
```

**Issues to fix:**
```
✗ KB environment NOT ready — fix these issues:
  • corp-semi: path /Users/.../semi-library has no _shelf-index.md
    Suggestion: cd /Users/.../semi-library && /sdlc-knowledge-base:kb-rebuild-indexes
  • corp-health: handle in registry conflicts with shelf-index handle
    Suggestion: rebuild shelf-index with --handle corp-health, or rename registry entry
  • Smoke test failed for internal-research: dispatcher timeout

Re-run /sdlc-knowledge-base:kb-setup-consulting --verify-only after fixing.
```

## What this skill does NOT do

- It does not create corporate libraries — those exist independently and must be cloned/mounted by the user before registration
- It does not modify corporate libraries — only registers pointers
- It does not run kb-rebuild-indexes against external libraries (their owners control that)
- It does not write audit log entries — onboarding is a setup operation, not a query operation

## Examples

First-time setup for a new consultant:
```
/sdlc-knowledge-base:kb-setup-consulting
```

Verify environment after fixing reported issues:
```
/sdlc-knowledge-base:kb-setup-consulting --verify-only
```

Preview without writing:
```
/sdlc-knowledge-base:kb-setup-consulting --dry-run
```

## Errors

- **~/.sdlc/global-libraries.json is malformed** — error and recommend manual repair
- **No CLAUDE_PLUGIN_ROOT set** — print install fallback (export var or pip install -e the plugin)

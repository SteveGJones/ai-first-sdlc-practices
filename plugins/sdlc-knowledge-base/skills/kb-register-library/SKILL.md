---
name: kb-register-library
description: Register an external knowledge base library in the user-scope global registry at ~/.sdlc/global-libraries.json. Validates that the target path exists, contains a _shelf-index.md, and parses its format_version. Optional helper — hand-editing the JSON is also supported.
disable-model-invocation: false
argument-hint: "<name> <absolute-path-to-library-dir> [description]"
---

# Register External Library

Add an external knowledge base to the user-scope global registry so it can be activated in any project's `.sdlc/libraries.json`.

## Arguments

- `<name>` — a short handle used in attribution output. Lowercase-kebab-case recommended (e.g., `corporate-semiconductor`, `corp-healthcare`). Must be unique within `~/.sdlc/global-libraries.json`.
- `<absolute-path-to-library-dir>` — the absolute path to the *library directory* (the one containing `_shelf-index.md`), not the repo root. Must exist at registration time.
- `[description]` — optional human note for the user's own reference. Not used by any system behaviour.

## Preflight

- Verify the registry file's parent directory exists. Create `~/.sdlc/` if missing.
- If `~/.sdlc/global-libraries.json` exists, load and validate it.
- Validate `<name>` matches `^[a-z][a-z0-9-]*$` (lowercase letters, digits, hyphens; must start with a letter). If not, error with: "Library handle must match ^[a-z][a-z0-9-]*$ — found '<name>'. Choose a different name."
- If the chosen `<name>` is already registered, error out with the existing entry's path shown; recommend a different name or manual JSON edit.

## Steps

### 1. Validate the target library path

Run the path validator:

```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import validate_library_path
ok, reason = validate_library_path(Path('<path>'))
if not ok:
    print(f'ERROR: {reason}')
    exit(1)
print('OK')
"
```

If the validator returns an error, surface the exact `reason` string to the user and stop. Common reasons:

- "path 'X' must be absolute" — relative path; correct it
- "path 'X' does not exist" — directory doesn't exist; create it or correct path
- "path 'X' has no _shelf-index.md" — run `/sdlc-knowledge-base:kb-rebuild-indexes` in that library first
- "path 'X' resolves to '...' which contains denylisted fragment '...'" — refuse to register; user should pick a different path

### 2. Load or initialise the registry

If `~/.sdlc/global-libraries.json` does not exist, initialise with:

```json
{"version": 1, "libraries": []}
```

Otherwise load the existing file. If parsing fails, do not overwrite — error and recommend manual repair.

### 3. Add the new entry

Append to `libraries`:

```json
{
  "name": "<name>",
  "type": "filesystem",
  "path": "<absolute-path>",
  "description": "<description or omitted>"
}
```

### 4. Write the registry atomically

Write to a temp file and rename to avoid partial writes.

### 5. Report success

Print a confirmation:

```
Registered '<name>' → <path>
format_version: <N>
Description: <description or "none">

To activate in a project, add to .sdlc/libraries.json:
  {"version": 1, "activated_sources": ["<name>"]}
```

## What this skill does NOT do

- It does not install, copy, or symlink the library — it only records a pointer.
- It does not activate the library in any project — that's a separate manual step.
- It does not validate shelf-index content quality — only that the file exists.
- It does not support `type: remote-agent` — that's phase D (future EPIC).

## Examples

Register a corporate library:

```
/sdlc-knowledge-base:kb-register-library corporate-semiconductor /Users/steve/corp/semi/library "Semiconductor engagement findings 2024-2026"
```

Register with no description:

```
/sdlc-knowledge-base:kb-register-library corp-health /Users/steve/corp/health/library
```

## Errors

- **Path does not exist** — correct the path argument or create the directory first
- **No shelf-index at path** — run `/sdlc-knowledge-base:kb-rebuild-indexes` in that library
- **Name already registered** — choose a different name, or manually edit `~/.sdlc/global-libraries.json`
- **Registry file malformed** — manual repair required; the skill will not overwrite a file it cannot parse

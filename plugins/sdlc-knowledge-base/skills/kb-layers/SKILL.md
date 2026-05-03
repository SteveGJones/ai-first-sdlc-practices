---
name: kb-layers
description: Manage the project's layer vocabulary — list allowed layers with file counts, add new layers, or safely remove unused layers. Reads the shelf-index for usage data; writes CLAUDE.md atomically. No agent dispatch.
disable-model-invocation: false
argument-hint: "[--add <layer> | --remove <layer> [--force]]"
---

# Manage KB Layer Vocabulary

> **Lightweight**: This skill reads only index metadata and writes CLAUDE.md. Inline execution is acceptable — no agent dispatch needed.

Manage the project's allowed layer vocabulary for the `layer:` frontmatter field in library files.

## Arguments

| Form | Description |
|---|---|
| (none) | List allowed layers with file counts from shelf-index |
| `--add <layer>` | Add a layer to the allowed set |
| `--remove <layer>` | Remove a layer (refused if any file uses it) |
| `--remove <layer> --force` | Remove a layer bypassing usage check |

## Preflight

Read CLAUDE.md and locate the `[Knowledge Base]` section. Extract `library_path` (default `library/`) and `shelf_index_path` (default `library/_shelf-index.md`).

## Steps

### 1. Resolve configuration

Read CLAUDE.md `[Knowledge Base]` section to resolve `library_path` and `shelf_index_path`.

### 2. Run kb_layers.py

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
from sdlc_knowledge_base_scripts.kb_layers import main
args = ['--project-dir', '<project_dir>', '--shelf-index-path', '<shelf_index_path>']
# Append --add <layer>, --remove <layer>, or --force as appropriate
sys.exit(main(args))
"
```

Replace `<project_dir>` with the project root and `<shelf_index_path>` with the resolved path.

### 3. Report the result

Print the script output. For list mode:
```
# Project layer set

Mode: defaults

Allowed layers:
  - methodology            (15 files)
  - evidence               (22 files)
  - domain                 ( 7 files)
  - development            ( 3 files)
```

## What this skill does NOT do

- Does not read library file content (only the shelf-index **Layer:** entries)
- Does not rename `layer:` values in existing library files — do that manually and run `kb-rebuild-indexes`
- Does not dispatch any agent

## Errors

- **Invalid layer name** — must match `^[a-z][a-z0-9-]*$` (lowercase, hyphenated)
- **Layer in use** — use `--force` to remove anyway (leaves dangling references; `kb-lint --strict-layer` will catch them)
- **Last remaining layer** — cannot remove; at least one layer value is required

## Examples

```
/sdlc-knowledge-base:kb-layers
/sdlc-knowledge-base:kb-layers --add regulatory
/sdlc-knowledge-base:kb-layers --remove clinical-evidence
/sdlc-knowledge-base:kb-layers --remove methodology --force
```

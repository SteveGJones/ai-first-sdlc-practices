---
name: kb-rebuild-indexes
description: Rebuild the knowledge base shelf-index with hash-based change detection. Incremental by default — only re-extracts files whose content has changed since the last index. Use after ingesting new sources, after editing library files, or whenever the librarian agent reports a stale index.
disable-model-invocation: false
argument-hint: "[--full] [--dry-run] [--force]"
---

# Rebuild Knowledge Base Indexes

> **Script-based**: This skill runs `build_shelf_index.py` via Bash — no agent dispatch needed and no library file content loaded into session context.

Rebuild the shelf-index for the knowledge base. Incremental by default: compares each library file's content hash against the recorded hash in the index, and only re-extracts entries whose hash has changed.

## Arguments

- `--full` — Force complete rebuild. Re-extracts every entry even when the hash matches. Use this when:
  - The extraction logic itself has changed (you updated this skill)
  - You suspect the index has drifted in a way the hash check missed
  - You're starting from a deleted or corrupted index

  Without this flag, the rebuild is incremental and skips unchanged files.
- `--dry-run` — Report what would change (including the `Scanned:` / `Excluded:` breakdown) without writing `_shelf-index.md` or `log.md`.
- `--force` — Override the bulk-add safety rail (see "Safety rail" below). **Never pass this on your own initiative** — only after the user has seen the breakdown and confirmed.

## Excluding directories: `.kb-index-ignore`

The rebuild indexes every `.md` file under the library, except the top-level `raw/` directory (always excluded). To keep other directories out of the index — vendored dumps, scraped reference material, anything that is not a curated library file — create `<library_path>/.kb-index-ignore`:

```
# one library-relative directory per line
iso20022/
vendor/standards
```

- One directory path per line, relative to the library root; a trailing `/` is optional.
- A path matches that directory and everything under it. No globs.
- `#` comments and blank lines are ignored.
- Absolute paths and `..` entries are rejected. An entry that matches nothing produces a warning.

## Preflight

Verify the project has a knowledge base. The `[Knowledge Base]` section in `CLAUDE.md` should declare:

- `library_path` — default `library/`
- `shelf_index_path` — default `library/_shelf-index.md`

If `CLAUDE.md` does not contain a `[Knowledge Base]` section, report: "No knowledge base configured. Add a `[Knowledge Base]` section to CLAUDE.md (see `plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md`) before running this skill."

If the library path does not exist, report: "Library directory `<path>` does not exist. Create it or run `/sdlc-knowledge-base:kb-init` before running this skill."

## Steps

### 1. Read knowledge base configuration

Read `CLAUDE.md` and locate the `[Knowledge Base]` section. Extract:
- `library_path` — default `library/`
- `shelf_index_path` — default `library/_shelf-index.md`

Stop with the preflight errors above if either check fails.

### 2. Verify build_shelf_index module importable

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
        module = importlib.util.module_from_spec(spec)
        sys.modules['sdlc_knowledge_base_scripts'] = module
        spec.loader.exec_module(module)
try:
    import sdlc_knowledge_base_scripts.build_shelf_index  # noqa: F401
    print('OK')
except ImportError:
    print('MISSING')
"
```

If output is `MISSING`: report "build_shelf_index module not found. Update the sdlc-knowledge-base plugin." and stop.

### 3. Run the rebuild script

Construct the argument list from Step 1 and the skill argument (`--full` if provided):

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
        module = importlib.util.module_from_spec(spec)
        sys.modules['sdlc_knowledge_base_scripts'] = module
        spec.loader.exec_module(module)
from sdlc_knowledge_base_scripts.build_shelf_index import main
args = ['<library_path>', '--shelf-index-path', '<shelf_index_path>']
# Append flags the skill was called with:
# args.append('--full')       # skill argument --full
# args.append('--dry-run')    # skill argument --dry-run
# args.append('--force')      # ONLY on the re-run after the user confirms a safety-rail refusal
sys.exit(main(args))
"
```

Replace `<library_path>` and `<shelf_index_path>` with the values from Step 1. Uncomment each `args.append(...)` line that applies: `--full` and `--dry-run` when the skill argument included them, and `--force` only on the re-run after the user has confirmed a safety-rail refusal (see below). Never add `--force` on the first run.

### 4. Report results

Print the script output directly to the user. Expected format:

```
Shelf-index rebuilt: library/_shelf-index.md

  Mode: incremental
  Files scanned: 22
  Unchanged:    18  (skipped)
  Modified:     3  (re-extracted)
  Added:        1  (new entries)
  Removed:      0  (entries dropped)

  Index entries: 22
  Scanned:
    domain/: 21
    ./: 1
  Excluded:
    iso20022/
    raw/

Warnings — 1 exclusion issue(s):
  - .kb-index-ignore: entry 'Domain' differs only in case from the real directory 'domain'; entries are case-sensitive, so use 'domain' (entry not applied)
```

`Scanned:` lists indexed files per top-level directory (`./` is the library root). `Excluded:` names the directories skipped by `raw/` or `.kb-index-ignore`; they are not walked, so no file counts are shown. The `Warnings` block appears only when an ignore entry is unsafe, matches no directory, differs from the real directory name only in case, is a symlink, or cannot be read; such entries are warned about and not applied. Check these lines when the file count looks wrong.

If the script exits with code 2, the **safety rail** refused the rebuild — see below. If it exits with code 1, surface the error and recommend:
- `/sdlc-knowledge-base:kb-init` — if the library directory is missing
- `/sdlc-knowledge-base:kb-ingest` — if the library exists but is empty

## Safety rail (exit code 2)

A rebuild that adds 50 or more entries **and** would grow the index to 2x or more of its current size is almost always an un-ignored dump, not a real ingest. In that case the script writes **neither** `_shelf-index.md` nor `log.md` and exits with code 2, naming the top-level directories responsible (for example `iso20022/: 412 added`). A first build with no index (or an empty one) is exempt.

When this happens you MUST:

1. Show the user the per-directory breakdown from the script output.
2. Ask whether those files really belong in the index. If not, add the directories to `.kb-index-ignore` and re-run.
3. Re-run with `--force` **only after the user explicitly confirms** the large addition is intended. Never add `--force` automatically or to "get past" the refusal.

## Hash strategy

SHA-256 over raw file content, stored per-entry in the shelf-index. Any file change (including whitespace) triggers re-extraction on the next incremental run. See `build_shelf_index.py` for the full implementation.

## What this skill does NOT do

- **It does not invoke the librarian.** That's `kb-query`.
- **It does not ingest new sources.** That's `kb-ingest`.
- **It does not validate citations.** That's `kb-validate-citations`.
- **It does not check for logical drift** (contradictions, orphans). That's `kb-lint`.
- **It does not rebuild the codebase-index.** The codebase-index is a future feature.

This skill only manages the shelf-index for the curated library files.

## Example invocation

```
/sdlc-knowledge-base:kb-rebuild-indexes

Shelf-index rebuilt: library/_shelf-index.md

  Mode: incremental
  Files scanned: 3
  Unchanged:    1  (skipped)
  Modified:     1  (re-extracted)
  Added:        1  (new entries)
  Removed:      1  (entries dropped)

  Index entries: 3
  Scanned:
    domain/: 3
  Excluded:
    (none)
```

---
name: kb-prepare-batch
description: Stage source files into library/raw/, converting non-markdown formats via markitdown (PDF/DOCX/PPTX/XLSX/HTML/CSV) or pandoc (TeX/EPUB/RST/ORG). Adds provenance frontmatter. No agent dispatch.
disable-model-invocation: false
argument-hint: "[--copy|--move] [--from <manifest>] [files...] [--overwrite] [--force-pandoc|--force-markitdown]"
---

# Prepare Batch for Ingestion

Stage source files into `library/raw/`, converting non-markdown formats. First stage of the two-stage batch workflow: **prepare** (this skill) then **ingest** (`kb-ingest-batch`). No agent invoked.

## Arguments

| Argument | Description |
|---|---|
| `files...` | Source file paths |
| `--from <manifest>` | File with one path per line |
| `--copy` | Leave source files in place (default) |
| `--move` | Move source files into raw/ |
| `--overwrite` | Allow re-conversion of already-staged files |
| `--force-markitdown` | Use markitdown for all files |
| `--force-pandoc` | Use pandoc for all files |

## Format routing

| Extension | Converter |
|---|---|
| `.md` | Pass-through |
| `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.html`, `.csv` | `markitdown` |
| `.tex`, `.epub`, `.rst`, `.org` | `pandoc` |
| Anything else | Error per file; rest of batch continues |

## Preflight

1. Check `markitdown --help` — warn if absent
2. Check `pandoc --version` — warn if absent
3. If only `.md` files: proceed without converters

## Steps

### 1. Resolve configuration

Read CLAUDE.md `[Knowledge Base]` section to extract `library_path` (default `library/`). Target is `<library_path>/raw/`.

### 2. Run kb_prepare_batch.py

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
from sdlc_knowledge_base_scripts.kb_prepare_batch import main
args = ['--target-dir', '<raw_dir>']
# Add --copy or --move (default: --copy)
# Add source file paths
# Add --from <manifest> if passed
# Add --overwrite if passed
# Add --force-markitdown or --force-pandoc if passed
sys.exit(main(args))
"
```

### 3. Report results

```
Batch preparation complete:
  Staged:  12
  Skipped:  0
  Failed:   1

Issues:
  - presentation.key: unsupported extension '.key'
```

## Next steps

```
/sdlc-knowledge-base:kb-ingest-batch
```

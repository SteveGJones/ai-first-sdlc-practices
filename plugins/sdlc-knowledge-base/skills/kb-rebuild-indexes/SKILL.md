---
name: kb-rebuild-indexes
description: Rebuild the knowledge base shelf-index with hash-based change detection. Incremental by default — only re-extracts files whose content has changed since the last index. Use after ingesting new sources, after editing library files, or whenever the librarian agent reports a stale index.
disable-model-invocation: false
argument-hint: "[--full]"
---

# Rebuild Knowledge Base Indexes

Rebuild the shelf-index for the knowledge base. Incremental by default: compares each library file's content hash against the recorded hash in the index, and only re-extracts entries whose hash has changed.

## Arguments

- `--full` — Force complete rebuild. Re-extracts every entry even when the hash matches. Use this when:
  - The extraction logic itself has changed (you updated this skill)
  - You suspect the index has drifted in a way the hash check missed
  - You're starting from a deleted or corrupted index

  Without this flag, the rebuild is incremental and skips unchanged files.

## Preflight

Verify the project has a knowledge base. The `[Knowledge Base]` section in `CLAUDE.md` should declare:

- `library_path` — default `library/`
- `shelf_index_path` — default `library/_shelf-index.md`

If `CLAUDE.md` does not contain a `[Knowledge Base]` section, report: "No knowledge base configured. Add a `[Knowledge Base]` section to CLAUDE.md (see plugins/sdlc-knowledge-base/templates/claude-md-section.md) before running this skill."

If the library path does not exist, report: "Library directory `<path>` does not exist. Create it before running this skill."

## Steps

### 1. Read the existing shelf-index (if any)

If `shelf_index_path` exists, parse it. Each entry has the structure:

```markdown
## N. <relative-path-from-library-root>

**Hash:** <sha256-hex>
**Terms:** <comma-separated keywords>
**Facts:** <bulleted statistics with citations>
**Links:** <cross-references and project links>
```

Build an in-memory map: `{file_path → recorded_hash}` from the existing index.

If the file does not exist, treat the existing index as empty (this is the first build).

### 2. Discover library files

Use Glob to find all `.md` files under `library_path` excluding the index files themselves and the `raw/` directory:

```
library/**/*.md
```

Exclude:
- `library/_shelf-index.md` (this file)
- `library/_index.md` (master index, if present)
- `library/raw/**` (raw sources, not synthesised library files)
- `library/log.md` (log, not a library file)

The remaining files are the library entries.

### 3. Compute current hashes

Use Bash to compute SHA-256 hashes for all discovered library files in one pass:

```bash
find library -name "*.md" \
  ! -name "_shelf-index.md" \
  ! -name "_index.md" \
  ! -name "log.md" \
  ! -path "library/raw/*" \
  -exec sha256sum {} \;
```

Each line is `<hash>  <path>`. Build an in-memory map: `{file_path → current_hash}`.

### 4. Classify each file

For each file in the current set, classify it:

| Recorded hash | Current hash | Classification | Action |
|---|---|---|---|
| Missing | Present | **Added** | Extract entry, add to index |
| Present | Matches | **Unchanged** | Skip (or re-extract if `--full`) |
| Present | Differs | **Modified** | Re-extract entry, update index |
| Present | Missing | **Removed** | Remove entry from index |

### 5. Extract entries for added and modified files

For each file that needs extraction (added or modified, plus all files if `--full`), read the file and produce a shelf-index entry.

Extraction is judgment-based — read the library file's content and produce four fields:

#### Hash

```bash
sha256sum <file> | cut -d' ' -f1
```

#### Terms (20-30 keywords)

Identify the 20-30 most distinctive terms from the file. Sources of good terms:

- The `title` and `domain` from the frontmatter
- Section headings (especially the `## Key Question`)
- Names of frameworks, methodologies, authors, organisations mentioned in `## Frameworks Reviewed` and `## Key References`
- Specific metrics, thresholds, and units from `## Actionable Thresholds`
- Domain-specific vocabulary the file uses repeatedly

Aim for terms a future query would actually contain. Generic words ("research", "study", "framework") are useless — they'll match every file. Specific terms ("DORA cycle time", "TLA+ model checker", "PKCE flow") narrow the search effectively.

#### Facts (3-5 headline statistics with citations)

Identify the 3-5 most important findings from the `## Core Findings` section. Each fact should be:

- A specific claim (not a general statement)
- A specific number, threshold, or sample size
- A citation in compact form: `(author, year, n=sample_size)` or `(study name, year)`

Example facts:
- "Elite teams have cycle time <1 hour, n=39000 (DORA 2024)"
- "TDD reduces defect density by 40-50% (Madeyski 2010)"
- "TLA+ caught 6 critical bugs in DynamoDB before launch (AWS 2018)"

If the file has more than 5 strong facts, pick the 5 most distinctive.

#### Links (cross-references and project links)

Two kinds:

- Cross-references to other library files: extract from the `cross_references` frontmatter field
- Project-specific links: extract from the `## Programme Relevance` section if present, listing any project artifacts (issue numbers, ADRs, design docs) the file connects to

Format as a comma-separated list.

### 6. Write the updated shelf-index

Construct the updated shelf-index from the entries: keep unchanged entries as-is, add new ones, replace modified ones, drop removed ones. Sort by file path for stability.

### Mandatory format_version header

Every generated shelf-index MUST begin with this exact first line as an HTML comment:

    <!-- format_version: 1 -->

This breadcrumb tells the librarian and cross-library consumers what shelf-index schema to expect. It is on the first line, before the `#` heading. Missing header is treated as legacy v1 silently; this skill always emits it going forward.

Write to `shelf_index_path` using the format:

```markdown
<!-- format_version: 1 -->
# Knowledge Base Shelf-Index

Generated by `/sdlc-knowledge-base:kb-rebuild-indexes`. This file is the librarian agent's first-read on every query — it identifies which library files are relevant before deep-reading them.

**Do not edit this file by hand.** Run `/sdlc-knowledge-base:kb-rebuild-indexes` after editing library files to update.

---

## 1. <first-file-path>

**Hash:** <sha256-hex>
**Terms:** <comma-separated keywords>
**Facts:**
- <fact 1>
- <fact 2>
- <fact 3>
**Links:** <cross-references and project links>

## 2. <second-file-path>

**Hash:** <sha256-hex>
**Terms:** <comma-separated keywords>
**Facts:**
- <fact 1>
- <fact 2>
**Links:** <cross-references and project links>

...
```

Numbering is sequential by sorted file path. Numbers can change between rebuilds — that's fine, the file path is the canonical identifier.

### 7. Append to log.md (if present)

If `library/log.md` exists, append an entry:

```markdown
## [YYYY-MM-DD] rebuild-indexes | <unchanged>/<modified>/<added>/<removed>

Mode: <incremental|full>
Files unchanged: N
Files updated: M
Files added: K
Files removed: J
```

Use today's date in ISO format. If `log.md` does not exist, skip silently — the user has not opted into chronological logging.

### 8. Report results

Print a summary:

```
Shelf-index rebuilt: <shelf_index_path>

  Mode: incremental (or full)
  Files scanned: <total>
  Unchanged:    <N>  (skipped)
  Modified:     <M>  (re-extracted)
  Added:        <K>  (new entries)
  Removed:      <J>  (entries dropped)

  Index entries: <total in updated index>
  Index size:    <line count> lines
```

If any extraction failed (file unreadable, frontmatter malformed, etc.), report the failure and skip that file rather than aborting the whole rebuild.

## Error handling

- **Library path missing** — fail with the preflight error from above
- **Shelf-index path is in a directory that doesn't exist** — create the directory, then write the file
- **A library file has malformed frontmatter** — log a warning, skip extraction for that file, leave its existing index entry intact (or omit it if it's new)
- **Bash command fails** — fall back to per-file hashing one at a time
- **`sha256sum` not available** — try `shasum -a 256` (macOS); if neither, fail with "Install coreutils or use macOS shasum"

## Notes on the hash strategy

- Hash is SHA-256 over the **raw file content**, including frontmatter. Any change to the file (even whitespace) produces a new hash and triggers re-extraction. This is intentional — we want false positives (re-extract slightly more often than strictly necessary) over false negatives (missing real changes).
- The hash lives **inline in each shelf-index entry**, not in a separate header block. This makes each entry self-contained and removing an entry doesn't leave dangling state.
- Hashes are stored as hex strings. The full 64-char SHA-256 is used; we don't truncate.

## What this skill does NOT do

- **It does not invoke the librarian.** That's `kb:query`.
- **It does not ingest new sources.** That's `kb:ingest`.
- **It does not validate citations.** That's `kb:validate-citations`.
- **It does not check for logical drift** (contradictions, orphans). That's `kb:lint`.
- **It does not rebuild the codebase-index.** The codebase-index is sub-feature 13, future branch.

This skill only manages the shelf-index for the curated library files.

## Example invocation

```
/sdlc-knowledge-base:kb-rebuild-indexes

Shelf-index rebuilt: library/_shelf-index.md

  Mode: incremental
  Files scanned: 22
  Unchanged:    18  (skipped)
  Modified:      3  (re-extracted)
  Added:         1  (new entries)
  Removed:       0  (entries dropped)

  Index entries: 22
  Index size:    178 lines
```

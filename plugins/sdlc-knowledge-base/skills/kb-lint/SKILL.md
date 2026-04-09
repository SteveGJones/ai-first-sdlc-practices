---
name: kb-lint
description: Health-check the project knowledge base. Looks for contradictions between files, stale claims that newer sources have superseded, orphan files with no inbound cross-references, important concepts mentioned but lacking their own page, missing cross-references, and data gaps. Returns a structured report; does not auto-fix.
disable-model-invocation: false
argument-hint: "[--scope <pattern>]"
---

# Knowledge Base Lint

Periodic health-check for the project's knowledge base. This is the **lint** operation in the three-operations model (ingest / query / lint), adopted from Karpathy's LLM Wiki gist.

The staleness check that runs in environment validation catches one kind of drift (file changed since last index). Lint catches the other kinds: logical drift, orphan accumulation, missing concepts, contradictions, gaps. Both are needed.

## Argument

Optional `--scope <pattern>` to limit lint to a subset of library files. Default is the entire library.

Examples:
- `--scope dora-*.md` — lint only DORA-related files
- `--scope library/architecture/*.md` — lint a sub-directory
- (no argument) — lint everything

## Preflight

- Verify the knowledge base is configured.
- Verify the shelf-index is fresh: invoke `kb-rebuild-indexes` first if any library files are newer than the index. (The lint output is only meaningful against an up-to-date index.)
- Verify there are at least 3 library files. Linting an empty or near-empty library is not useful.

## Steps

### 1. Read the shelf-index

Use the index to enumerate library files. Apply the `--scope` filter if provided.

### 2. Run six checks

For each library file in scope, the librarian agent (in lint mode) performs the following checks:

#### Check 1: Contradictions between files

Look for findings in different files that disagree. Flag any case where:
- Two files report different numbers for the same metric
- Two files cite different sources for the same claim
- Two files draw opposite conclusions from similar evidence

For each contradiction, report:
- The conflicting findings (with their source files and citations)
- A suggested resolution: one source is more authoritative, both are valid in different contexts, or genuine disagreement that needs human judgment

#### Check 2: Stale claims

Look for findings whose citation date is significantly older than the most recent file in the same domain. Heuristic:
- If file A cites a 2018 source and file B (same domain) cites a 2024 source with updated numbers, file A's findings may be stale
- If a file's `## Programme Relevance` references project artifacts that no longer exist or have evolved (e.g., deleted issues, renamed components), the section may be stale

For each stale candidate, report:
- The potentially stale finding
- The newer source that suggests it's stale
- A recommendation: review and update, or annotate as historical

#### Check 3: Orphan files

Files with no inbound cross-references from other library files. An orphan is either:
- A genuinely standalone file (acceptable, but consider whether it should be cross-referenced from related domains)
- A file that should be cross-referenced but isn't (a maintenance gap)

For each orphan, report:
- The file path
- A list of files that mention the orphan's domain or terms in their content (suggesting they should cross-reference it)

#### Check 4: Missing cross-references

Files that mention a concept by name where another library file exists for that concept, but the cross-reference isn't declared in frontmatter. Use Grep against the library to find:
- File X's content mentions "DORA metrics" → if `dora-metrics.md` exists and isn't in X's `cross_references`, flag it

For each missing cross-reference, report:
- The file that should reference
- The file it should reference
- The text in the source file that triggered the suggestion

#### Check 5: Important concepts lacking their own page

Look for terms or topics that appear repeatedly across multiple library files but have no dedicated file. Heuristic:
- A term appears in 3+ files but has no file with that term in its title or domain → consider creating a dedicated file

For each candidate, report:
- The term or topic
- The files that mention it
- A recommendation: consider creating a dedicated library file (or skip if the concept is too broad to be useful as its own page)

#### Check 6: Data gaps

Look for places where the library would benefit from research it doesn't have. Heuristic:
- A file's `## Frameworks Reviewed` mentions a framework but has no `## Core Findings` for it → research gap
- A file's `## Actionable Thresholds` table has a row with no Source → unsourced threshold needs verification
- A `## Key Question` whose `## Core Findings` doesn't actually answer it

For each gap, report:
- The file with the gap
- What's missing
- A suggested next step (commission research via `kb-ingest`, find the source for the unsourced threshold, etc.)

### 3. Produce the structured report

Output format:

```markdown
# Knowledge Base Lint Report

**Date:** YYYY-MM-DD
**Scope:** all files (or pattern)
**Files scanned:** N

## Summary

| Check | Issues found |
|---|---|
| 1. Contradictions | C |
| 2. Stale claims | S |
| 3. Orphan files | O |
| 4. Missing cross-references | X |
| 5. Concepts lacking pages | M |
| 6. Data gaps | G |

**Total issues:** TOTAL

---

## 1. Contradictions

### 1.1 [Conflicting topic]
**File A:** dora-metrics.md — "Elite teams have cycle time <1 hour, n=39000 (DORA 2024)"
**File B:** continuous-delivery-evidence.md — "Top performers achieve cycle time <30 minutes, n=12 (Bytedance 2025)"
**Suggested resolution:** Both are valid in different contexts. DORA 2024 is the broader cross-industry benchmark; Bytedance is a single-org case study with stricter internal targets. Suggest annotating both files to distinguish industry-wide vs single-org thresholds.

(Continue for each contradiction...)

## 2. Stale claims

(...)

## 3. Orphan files

(...)

## 4. Missing cross-references

(...)

## 5. Concepts lacking pages

(...)

## 6. Data gaps

(...)

---

## Recommended actions (prioritised)

1. [Highest-priority issue]
2. [Next-priority issue]
3. ...
```

### 4. Append to log.md

If `library/log.md` exists, append:

```markdown
## [YYYY-MM-DD] lint | <total issues>

Mode: full (or scoped: <pattern>)
Files scanned: N
Contradictions: C
Stale claims: S
Orphan files: O
Missing cross-references: X
Concepts lacking pages: M
Data gaps: G
```

### 5. Do NOT auto-fix

The lint operation is read-only and reports issues. It does not:
- Automatically resolve contradictions
- Automatically add cross-references
- Automatically create new files for missing concepts
- Automatically annotate stale claims

The user reviews the report and decides what to act on. Some issues are real maintenance work; others are intentional (an orphan file may be standalone by design; a contradiction may be a known disagreement worth preserving).

For issues the user wants to fix, the workflow is:
- Manual: edit the library files directly, then run `kb-rebuild-indexes`
- Automated: run `kb-ingest` with new sources that resolve the gap, run `kb-rebuild-indexes`, re-run `kb-lint`

## What this skill does NOT do

- It does not invoke `kb-rebuild-indexes` automatically (preflight checks for staleness and recommends it, but doesn't run it)
- It does not modify any library files
- It does not query the library on behalf of users — that's `kb-query`
- It does not validate citations — that's `kb-validate-citations`

## Examples

**Lint the entire library:**
```
/sdlc-knowledge-base:kb-lint
```

**Lint a subset:**
```
/sdlc-knowledge-base:kb-lint --scope dora-*.md
```

**After fixes, re-lint to confirm:**
```
/sdlc-knowledge-base:kb-lint
# Apply the fixes manually
/sdlc-knowledge-base:kb-rebuild-indexes
/sdlc-knowledge-base:kb-lint  # confirm issues are resolved
```

## Errors

- **No knowledge base configured** — run `/sdlc-knowledge-base:kb-init` first
- **Shelf-index stale** — run `/sdlc-knowledge-base:kb-rebuild-indexes` first
- **Library too small** — fewer than 3 files; lint produces little value at this scale. Add more files first.
- **Scope pattern matches nothing** — verify the pattern matches at least one file in the library

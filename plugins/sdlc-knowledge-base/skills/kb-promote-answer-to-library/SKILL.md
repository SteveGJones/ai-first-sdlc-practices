---
name: kb-promote-answer-to-library
description: File a librarian query result back into the library as a new page with provenance tracking. Karpathy's "good answers can be filed back into the wiki as new pages" insight made concrete. The library compounds from explorations, not just from external sources.
disable-model-invocation: false
argument-hint: "<query-result-text-or-file> [--title <title>] [--path <library-file-path>]"
---

# Promote Answer to Library

When the librarian answers a query well — a comparison, an analysis, a connection between findings the library hadn't explicitly captured — that answer is itself valuable. It shouldn't disappear into chat history. This skill files the answer back into the library as a new page so explorations compound just like ingested sources do.

This is Karpathy's "good answers can be filed back into the wiki as new pages" insight from the LLM Wiki gist.

## Arguments

- **Query result** (required) — the text of the answer to file. Can be:
  - A file path containing the answer
  - The answer text passed inline
  - The output of a recent `kb-query` invocation (when called with `kb-query --promote-to-library`, this is automatic)
- **`--title <title>`** (optional) — explicit title for the new library file. If omitted, derive from the query that produced the answer (extract from the answer's heading or first paragraph).
- **`--path <library-file-path>`** (optional) — explicit destination path. If omitted, derive from the title using kebab-case conversion (e.g., `library/cycle-time-and-pi-planning.md`).

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

### 3. Construct the library file

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

### 4. Write the file

Use Write to create the new library file at the destination path. Verify the write succeeded.

### 5. Update the shelf-index

Invoke `/sdlc-knowledge-base:kb-rebuild-indexes` (incremental). The new file will be added to the index automatically.

### 6. Append to log.md

```markdown
## [YYYY-MM-DD] promote-answer | <title>

Source: kb-query result
Derived from: <source library files>
New file: <destination path>
```

### 7. Report

```
Promoted answer to library: <destination path>

  Title: <title>
  Provenance: synthesis (derived from N source files)
  Source files: <list>
  Index rebuilt: yes
  Log entry: yes (or skipped)

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

## Errors

- **No knowledge base configured** — run `/sdlc-knowledge-base:kb-init` first
- **Destination already exists** — pick a different path or edit the existing file
- **Answer is unparseable** — the answer text doesn't contain enough structure to extract findings; recommend re-querying with a more structured prompt
- **No source files referenced in the answer** — the answer wasn't from the librarian (or the librarian failed to cite); recommend re-querying

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

---
name: kb-query
description: Query the project knowledge base. Wraps the research-librarian agent. The librarian reads the shelf-index, identifies the 2-4 most relevant library files for the question, deep-reads only those, and returns structured evidence with citations. Stateless — reads the index fresh on every query.
disable-model-invocation: true
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

- Verify the project has a knowledge base configured.
- Verify the shelf-index exists at the configured path. If not, recommend running `/sdlc-core:kb-rebuild-indexes` first.
- Verify the `research-librarian` agent is available.

## Steps

### 1. Dispatch the research-librarian

Invoke the `research-librarian` agent with the question. The librarian's workflow is fixed:

1. Read the shelf-index fresh
2. Match the question against terms, facts, links
3. Identify the 2-4 most relevant library files
4. Deep-read only those files
5. Return structured evidence

The librarian will use one of two output formats automatically based on the question type:

- **Retrieval format** for "what does X say" — specific findings, one per topic, with `Finding`, `Source`, `Threshold`, `Library file`, `Programme link` fields
- **Synthesis format** for "build the case" or "how should we think about" — connected argument with `Claim`, `Supporting evidence`, `Caveats`, `Programme application`

### 2. If the librarian says "the library has no evidence on this"

This is the librarian's anti-hallucination behaviour. Don't override it. Print the librarian's response, which will typically include:

- Confirmation that no relevant files were found
- The closest related entries (if any)
- A recommended next step (commission research via `kb-ingest`, or query an external research engine)

Do not paraphrase, expand, or invent content to fill the gap.

### 3. If the librarian asks a clarifying question

The librarian will ask one clarifying question maximum when a query is too vague. Pass the question through to the user, get their answer, re-invoke the librarian with the clarification.

### 4. If `--promote-to-library` was specified

After the librarian returns its answer, dispatch `kb-promote-answer-to-library` with the answer as input. The promote skill files it as a new library page with provenance tracking (the source library files the librarian read) and rebuilds the shelf-index.

Otherwise, the answer is returned to the user and not stored anywhere.

## What this skill does NOT do

- It does not modify library files — the librarian is read-only
- It does not invent answers when the library lacks evidence
- It does not ingest new sources — that's `/sdlc-core:kb-ingest`
- It does not lint the library — that's `/sdlc-core:kb-lint`

## Examples

**Retrieval query:**
```
/sdlc-core:kb-query "What does our research say about cycle time as a delivery metric?"
```

Expected response: structured findings with DORA citations, sample sizes, thresholds, library file references.

**Synthesis query:**
```
/sdlc-core:kb-query "Build me the case for adopting trunk-based development"
```

Expected response: a connected argument citing trunk-based-development.md, dora-metrics.md, continuous-delivery-evidence.md, with caveats and the programme application.

**Query with promotion:**
```
/sdlc-core:kb-query "How do DORA metrics interact with SAFe-style PI planning?" --promote-to-library
```

Expected: the librarian answers; the answer is then filed back into the library as a new file (likely `dora-vs-safe-pi.md`) with provenance pointing at the source files the librarian read.

**Out-of-scope query:**
```
/sdlc-core:kb-query "What is the airspeed velocity of an unladen swallow?"
```

Expected response: "The library has no evidence on this. The closest entries are <none>. Recommendation: this query is out of scope for the project knowledge base."

## Errors

- **No knowledge base configured** — run `/sdlc-core:kb-init` first
- **Shelf-index missing** — run `/sdlc-core:kb-rebuild-indexes` first
- **Plugin not installed** — install `sdlc-knowledge-base@ai-first-sdlc`
- **Library is empty** — no library files exist yet. Add raw sources to `library/raw/` and run `/sdlc-core:kb-ingest` to populate the library.

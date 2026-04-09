---
name: kb-ingest
description: Integrate a new source into the project knowledge base. Wraps the agent-knowledge-updater agent. Source can be a local file path, a URL, or pasted content. The updater reads the source, classifies it, identifies which existing library files it touches, makes surgical updates or creates new files, rebuilds the shelf-index, and appends to log.md.
disable-model-invocation: true
argument-hint: "<source-path-or-url-or-text>"
---

# Knowledge Base Ingest

Take a new source and integrate it into the project's knowledge base. This is the **ingest** operation in the three-operations model (ingest / query / lint).

## Argument

A source. Can be:
- A local file path: `library/raw/some-paper.md`, `~/Downloads/dora-2024.pdf`
- A URL: `https://example.com/research-report`
- Pasted text: `<long pasted excerpt>`

## Preflight

- Verify the project has a knowledge base configured (the `[Knowledge Base]` section in `CLAUDE.md` exists). If not, run `/sdlc-knowledge-base:kb-init` first.
- Verify the `agent-knowledge-updater` agent is available (sdlc-knowledge-base plugin is installed).

## Steps

### 1. Resolve the source

If the argument is a file path: verify the file exists and is readable.
If the argument is a URL: prepare for WebFetch (the agent will fetch).
If the argument is pasted text: capture it for the agent.

If the source is a URL or a path outside `library/raw/`, recommend (but don't require) saving a local copy to `library/raw/` for provenance:

```
Source is at <url>. Recommended: save a local copy to library/raw/<descriptive-name>.md before ingesting so provenance is preserved. Continue with direct fetch? (y/N)
```

If the user accepts, proceed with WebFetch in the agent. If they want to save locally first, pause and let them.

### 2. Invoke the agent-knowledge-updater

Dispatch the `agent-knowledge-updater` agent with the source as input. The agent's workflow:

1. Read the source
2. Classify it (does it belong in the knowledge base?)
3. Read the shelf-index to find existing files this source touches
4. Make surgical updates or create new files
5. Rebuild the shelf-index (incremental)
6. Append to log.md

The updater is opinionated about what belongs in the knowledge base. If it determines the source belongs elsewhere (operational knowledge → CONTRIBUTING.md, ADRs, project tracker, auto-memory), it will say so and not ingest. Respect that decision.

### 3. Report the result

Print the agent's summary:

```
Ingest complete: <source>

  Files updated: N
  Files created: M
  Findings extracted: K
  Citations added: J

  Index rebuilt: yes
  Log entry: yes (or skipped if no log.md)

Next steps (if any): <e.g., "Review the new file X for accuracy">
```

If the agent declined to ingest, print its rationale and the recommended destination if it provided one.

## What this skill does NOT do

- It does not query the library — that's `/sdlc-knowledge-base:kb-query`
- It does not lint the library — that's `/sdlc-knowledge-base:kb-lint`
- It does not validate citations — that's `/sdlc-knowledge-base:kb-validate-citations`
- It does not write directly to library files — only the agent does that

## Examples

**Ingest a local academic paper:**
```
/sdlc-knowledge-base:kb-ingest library/raw/forsgren-2024-cycle-time-update.md
```

**Ingest from a URL:**
```
/sdlc-knowledge-base:kb-ingest https://cloud.google.com/devops/state-of-devops/2024
```

**Ingest pasted text (e.g., a conversation excerpt with research findings):**
```
/sdlc-knowledge-base:kb-ingest "<paste the excerpt here>"
```

## Errors

- **No knowledge base configured** — run `/sdlc-knowledge-base:kb-init` first
- **Plugin not installed** — install `sdlc-knowledge-base@ai-first-sdlc`
- **Source unreadable** — verify the file exists and you have read permissions
- **WebFetch fails** — check the URL is valid and reachable; fall back to manually downloading and ingesting the local file
- **Updater declines ingest** — the source doesn't belong in the knowledge base. Follow the recommended destination.

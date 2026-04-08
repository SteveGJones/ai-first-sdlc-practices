# sdlc-knowledge-base

Filesystem-based project knowledge base for projects that need to ground decisions in evidence.

**Status:** scaffolding only — content sub-features in progress on `feature/sdlc-knowledge-base`. See EPIC #105.

## What this plugin will provide

When complete, this plugin packages a reusable research library pattern validated in production by three projects:

- **`research-librarian` agent** — stateless retrieval-and-synthesis agent that reads a hash-tracked shelf-index, identifies the 2-4 most relevant library files for a query, deep-reads only those, and returns structured evidence with citations
- **`agent-knowledge-updater` agent** — proactive ingest agent that integrates new sources into existing library files
- **`kb:ingest` / `kb:query` / `kb:lint` skills** — the three operations from Karpathy's LLM Wiki framing
- **`kb:rebuild-indexes` skill** — incremental index rebuild using content hashes
- **`kb:promote-answer-to-library` skill** — file query results back as new library pages
- **Citation validator** — DOI resolution, arXiv ID validation
- **Templates** — library file format, shelf-index format, log.md format
- **Schema section template** — `[Knowledge Base]` section appended to the project's CLAUDE.md
- **Opt-in env validation extension** — staleness checks for the shelf-index

## When to install

- Projects making evidence-grounded decisions (architecture, design, transformation strategy)
- Programmes building stakeholder reports that need citations
- Teams accumulating research over time and wanting it organised rather than scattered
- Compatible with all four SDLC options (Solo, Single-team, Programme, Assured); particularly valuable for Programme and Assured

## When NOT to install

- Small projects without research needs
- Throwaway prototypes
- Projects where decisions don't need citation

See EPIC #105 for the full design and the per-sub-feature breakdown.

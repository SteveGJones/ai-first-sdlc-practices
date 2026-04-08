# Knowledge Base Pattern — Reusable Essence

**Sub-feature 1 deliverable for EPIC #105 (sdlc-knowledge-base)**
**Status:** Draft for review
**Date:** 2026-04-08
**Author:** Claude (AI Agent) and Steve Jones

This document extracts the reusable essence of the research library pattern that three projects are using in production. It synthesises three sources:

1. The original proposal at `research/research-library-approach.md` (the first project's design)
2. Steve's descriptions of how the second and third projects extended the pattern
3. Karpathy's [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), which describes the same conceptual shape independently

The output is a single document that scopes sub-features 2-12 of the EPIC. No code is written in this sub-feature.

> **Note on assumptions:** Some sections are based on Steve's verbal description of how the production projects work. Where I'm making assumptions to fill in detail, those are flagged with **[assumption]** for explicit review and correction.

---

## Overview

The pattern is a filesystem-based knowledge management approach for projects that need to ground decisions in evidence. It produces a structured, citable knowledge base that any team member or AI agent can query for evidence-backed decisions, without depending on embedding databases or vector search infrastructure.

It solves three problems:

1. **Research is expensive to do but cheap to store.** Deep research engines synthesise hundreds of sources in minutes; the investment is in designing good prompts.
2. **Findings decay without structure.** Raw research results are long, unindexed, and unsearchable six months later. The library layer compresses them into structured, tagged, cross-referenced files.
3. **Knowledge leaves with people.** A structured library with a librarian agent means the evidence base survives team changes.

The pattern was first deployed on the ODP programme (22 library files, 300+ findings, 200+ peer-reviewed citations, queried 50+ times in week one). Two more projects have since adopted it. All three implemented it in Claude Code in roughly a day. Each kept the original librarian system prompt as-is and extended the pattern with hash-based change detection, an `agent-knowledge-updater` for proactive curation, Sonnet over Haiku for command-line tool use, and staleness checks integrated into environment validation.

The plugin's job is to package the *infrastructure* — templates, agent definitions, skills, validators, schema. Each adopting project brings its own *content* — its research questions, raw sources, synthesised findings, and project-specific cross-references.

---

## The Three Layers

The pattern has three layers, each serving a different purpose and a different audience.

### Layer 1: Raw sources

Immutable source documents collected by the human: academic papers, articles, reports, internal documents, conversation excerpts. The agents read from this layer but never modify it. This is the source of truth that everything else derives from.

Default location: `library/raw/` (configurable).

### Layer 2: Library files

Synthesised, structured markdown files — one per topic. Each file compresses raw research into a 1,500-3,000 word structured synthesis with tagged frontmatter, numbered findings, actionable thresholds, and full citations. The `agent-knowledge-updater` writes to this layer; the `research-librarian` reads from it.

Default location: `library/` (configurable).

### Layer 3: The schema

A `[Knowledge Base]` section in the project's `CLAUDE.md` defining where the library lives, the frontmatter conventions, the workflow for ingest/query/lint, and the model and tool guidance for the agents. This is what makes the agents disciplined knowledge maintainers rather than generic chatbots. Karpathy's "schema is the configuration that makes the LLM a disciplined wiki maintainer" maps directly onto our convention of CLAUDE.md as the project configuration.

Co-evolved by the user and the agents over time.

### Plus: the librarian and the updater

Two agents bracket the layers:

- **`research-librarian`** reads the indexes, finds the 2-4 most relevant library files for a query, deep-reads only those, and returns structured evidence with citations. Stateless by design — reads the shelf-index fresh every time, so library updates take effect immediately.
- **`agent-knowledge-updater`** processes new sources from layer 1 and integrates them into layer 2. Updates existing files where the source touches them, creates new files where it doesn't, updates the shelf-index, and appends to log.md. This is the actually-novel piece compared to the original proposal — the original was about retrieval only; production added curation.

### Plus: the indexes

Two index files help the librarian and the user navigate the library:

- **Shelf-index** (`library/_shelf-index.md`) — compact machine-readable index for the librarian. Per file: terms (20-30 keywords), facts (3-5 headline statistics with citations), links (cross-references), and a content hash for staleness detection. Read first by the librarian on every query. Regenerated incrementally by `kb:rebuild-indexes` based on hash comparison.
- **Master index** (`library/_index.md`) — human-friendly multi-dimensional lookup with by-question, by-artifact, by-issue, and full-catalogue tables. **[assumption]** This was in the original proposal; not certain whether all three production projects actually maintain it or if the shelf-index has subsumed it. Worth confirming.

---

## The Three Operations

Karpathy's three-operations framing (ingest, query, lint) cleanly captures the workflow. The production projects already do ingest and query; lint is a Karpathy import that all three projects would benefit from.

### Ingest

Take a new source and integrate it into the library. The `agent-knowledge-updater` reads the source, identifies which existing files it touches, updates them, creates new files where needed, updates the shelf-index, and appends to log.md.

A single source might touch 5-15 library files. The user can ingest sources one at a time and stay involved (read summaries, check updates, guide emphasis) or batch-ingest with less supervision.

### Query

Ask the library a question. The `research-librarian` reads the shelf-index, identifies the 2-4 most relevant files, deep-reads them, and returns either retrieval-format output (specific findings with citations) or synthesis-format output (a connected argument across multiple findings).

Karpathy's insight: good answers can be **filed back into the library as new pages**. A comparison the librarian produced, an analysis, a connection between findings — these are valuable and shouldn't disappear into chat history. The plugin provides `kb:promote-answer-to-library` for this, with provenance tracking so synthesis files are distinguishable from primary research.

### Lint

Periodically health-check the library. Look for: contradictions between files, stale claims newer sources have superseded, orphan files with no inbound references, important concepts mentioned but lacking their own page, missing cross-references, data gaps that could be filled with a web search. Returns a structured report; does not auto-fix.

The lint operation is a Karpathy import. The production projects' staleness checks (in env validation) catch one kind of drift (file changed since last index); lint catches the other kinds (logical drift, orphan accumulation, missing concepts). Both are needed.

---

## Universal Components (ship as-is)

These are things all three projects do identically, derived from the original proposal and Steve's descriptions. The plugin ships these without configuration.

### Library file format

Frontmatter (verbatim from the original proposal):

```yaml
---
title: "[Topic]"
domain: [comma-separated topic tags]
status: active
tags: [array of search terms]
source: [path to raw research result]
cross_references:
  - library/related-file-1.md
  - library/related-file-2.md
---
```

Section structure:

```markdown
## Key Question
[The research question this file answers — one sentence]

## Core Findings
[Numbered list. Each finding: specific claim + specific number/data point + citation]

## Frameworks Reviewed
[Table comparing relevant frameworks, evidence base, limitations]

## Actionable Thresholds
[Table: Metric | Threshold | Source | Signal]

## Design Principles
[What the research says about how to build, not just what to measure]

## Key References
[10-20 full citations for primary sources]

## Programme Relevance
[Project-specific mapping; this section is the most maintenance-intensive]
```

### Shelf-index format

Compact machine-readable index. Per file:

```markdown
## N. filename.md
**Hash:** [content hash for staleness detection]
**Terms:** [20-30 keywords for query matching]
**Facts:** [3-5 headline statistics with citations]
**Links:** [cross-references and project-specific links]
```

**[assumption]** The hash field is an extension added by the production projects. Whether it lives inside each entry (as shown above) or in a separate header block is one of the open questions for review. I've placed it inline because that's the simplest design that supports incremental rebuild. Confirm if this matches production.

### Librarian system prompt

The original proposal's librarian behaviour, validated by all three projects keeping it as-is:

- Read the shelf-index first on every query
- Match the query against terms, facts, links
- Identify the 2-4 most relevant files
- Deep-read only those files
- Return structured evidence in retrieval format or synthesis format
- Never invent statistics or citations
- Say "the library has no evidence on this" rather than guessing
- Boundary: retrieve and synthesise evidence; do not make architecture decisions, recommend implementation, or provide change management advice — those are separate roles that consume the librarian's output

### Stateless retrieval

The librarian holds no state between queries. Reads the shelf-index fresh every time. This means library updates take effect immediately and the librarian can be invoked from any context without setup.

### Cross-references

Library files cross-reference each other aggressively — 2-4 cross-references per file is the documented norm. Findings that converge across multiple files get flagged as stronger evidence in the librarian's synthesis output.

---

## Configurable Components (ship default, expose customisation)

These are things all three projects do, but each has reasonable customisation needs. The plugin ships a sensible default and exposes the configuration point in the `[Knowledge Base]` section of CLAUDE.md.

### Library directory location

Default: `library/`. Configurable for projects that use a different convention.

### Raw sources directory location

Default: `library/raw/`. Configurable.

### Shelf-index location

Default: `library/_shelf-index.md`. Configurable.

### Master index location

Default: `library/_index.md`. **[assumption]** May be optional based on whether all three production projects maintain it.

### Default librarian model

Default: **Sonnet** (not Haiku). The original proposal recommended Haiku for cost reasons. At least one production project upgraded to Sonnet because the librarian needs to use command-line tools (`find`, `grep`) reliably to navigate the filesystem, and Haiku struggled with tool-use patterns. Documentation explains the trade-off: users who don't need command-line navigation can downgrade to Haiku themselves.

### Citation format

Default: author-year format with sample size and methodology where available. Configurable for projects that prefer different citation styles (Vancouver, APA, etc.).

### Frontmatter optional fields

Required: `title`, `domain`, `status`, `source`. Optional: `tags`, `cross_references`, plus any project-specific extensions (e.g., `evidence_strength`, `last_reviewed`).

---

## Value-add Components (optional or future)

These are things some projects do that aren't required for the core pattern to work. The plugin ships them as opt-in or defers them to future sub-features.

### `agent-knowledge-updater`

Proactive ingest agent. Reads new sources, integrates them into the library, updates indexes, appends to log.md. **[assumption]** I'm classifying this as a value-add core component — meaning it ships in the core plugin but a project can ignore it and ingest manually if they prefer. The original proposal didn't include it; the production extension added it. If all three production projects use it heavily, it should probably be promoted to "universal." Worth confirming.

### Citation validator

DOI resolution, arXiv ID validation, journal existence check. Catches obvious citation hallucinations from deep research engines. Recommended but optional. New addition not in any of the production projects (this is our value-add, not theirs).

### `kb:promote-answer-to-library`

Files a librarian query result back into the library as a new page with provenance tracking. Karpathy's "answers compound" insight. Optional but recommended for projects that do heavy exploratory querying.

### Lint operation

Periodic health-check for contradictions, orphans, missing cross-references, stale claims, data gaps. Karpathy import. Recommended but optional — a project can run lint manually or skip it entirely.

### `log.md`

Chronological append-only record of ingest/query/lint events. Karpathy's parseable convention with `## [YYYY-MM-DD] <op> | <title>` headers. Optional but recommended — gives a timeline of library evolution and helps diagnose "why does the library look like this?" questions.

### Codebase-index

Same hash-based index mechanism applied to source code files instead of library files. Used by the librarian (or a code-aware peer) to fetch only relevant code into the main context during planning, preventing context overload on large codebases. **Filed as sub-feature 13 — explicit value-add, future branch.** One of the three projects already uses this; the others don't.

### Env validation staleness integration

Existing env validation skill learns to check the shelf-index hashes and report stale entries. Opt-in via configuration in the CLAUDE.md schema section. Filed as sub-feature 12.

---

## Karpathy Concepts: Adopted, Diverged, Skipped

### Adopted

| Karpathy concept | Why we adopt it |
|---|---|
| **Three operations framing (ingest / query / lint)** | Clean conceptual model. The production projects already do ingest and query implicitly; making the three explicit gives users a shared vocabulary. |
| **Lint operation** | Production projects only catch staleness drift; Karpathy's lint catches logical drift (contradictions, orphans, missing concepts). Both are needed. |
| **`log.md`** | Cheap to add, parseable with simple unix tools, gives timeline of library evolution. The `agent-knowledge-updater` writes to it. |
| **Schema as CLAUDE.md section** | Karpathy literally names CLAUDE.md as the example. Maps onto our existing convention without adding a new file. |
| **"Good answers can be filed back into the wiki"** | The most important insight Karpathy adds beyond the original proposal. Compounds the library from explorations, not just from external sources. Implemented as `kb:promote-answer-to-library`. |
| **Wiki as compounding artifact** | Reframes the librarian's role: not just a searcher of static content, but the front-end of a knowledge base that grows with use. |

### Diverged

| Production pattern | Karpathy's gist | Why we go with production |
|---|---|---|
| Compact shelf-index with hashes | Single content-oriented `index.md` | Production projects validated that compact index + hash-based incremental rebuild scales better than a monolithic catalogue |
| Sonnet librarian | Karpathy is model-agnostic | Production reasoning (command-line tool use) is concrete; Sonnet wins |
| Two-index design (shelf + codebase) at one project | Single index | Codebase-index is value-add (#118); core stays single-index for now |

### Skipped

| Karpathy concept | Why we skip |
|---|---|
| Obsidian Web Clipper | Obsidian dependency we don't want |
| Obsidian hotkeys, graph view, Dataview | All Obsidian-specific |
| Image handling and download workflows | Research/library content is mostly text + citations |
| qmd / BM25 / vector search | The shelf-index is sufficient at the scales the production projects operate; embedding-based retrieval is heavyweight infrastructure that doesn't fit a Claude Code plugin |
| Marp slide deck generation | Interesting but unrelated to SDLC; users can compose this themselves if they want it |
| Memex / Vannevar Bush philosophical framing | Nice for documentation but not actionable in code |

---

## Open Questions for Sub-features 2-12

These are questions where I'm making assumptions that should be confirmed or corrected by Steve. Each is answerable in a sentence and none of them block sub-feature 1's deliverable from being useful.

1. **Does any of the three projects modify the library file frontmatter schema** beyond the original proposal's fields (`title`, `domain`, `status`, `tags`, `source`, `cross_references`)? Particularly: do any add `evidence_strength`, `last_reviewed`, `confidence`, or similar?

2. **Where does the content hash live in the shelf-index?** Inline per entry (as I've drafted) or in a separate header block? And is the hash computed over the raw library file or over a normalised version (e.g., excluding the frontmatter)?

3. **Does all three projects use the `agent-knowledge-updater`?** Or is it only one or two? This determines whether it ships as universal-core (universal section) or value-add-core (value-add section). I've drafted it as value-add-core.

4. **Does any project maintain the master index** (`_index.md`) in addition to the shelf-index, or has the shelf-index subsumed it? I've left master-index as configurable-optional pending confirmation.

5. **What does the `agent-knowledge-updater`'s decision logic look like?** Explicit rules ("always update files in domain X, ask human for Y, defer Z") or case-by-case reasoning? This shapes whether sub-feature 5 ships prompt-based reasoning or configuration-driven rules.

6. **`log.md` entry format** — is it Karpathy's `## [YYYY-MM-DD] ingest | <title>` or something different in the production projects? Does it include the touched files, or just the source title?

7. **Env validation integration shape** — does the staleness check sit at the start of env validation, the end, or as a discrete check? Default to warning or failure? I've defaulted to warning in sub-feature 12.

8. **The "rebuild-indexes" skill behaviour** — does it always try incremental rebuild and fall back to full rebuild on inconsistency, or is full rebuild the default? I've drafted incremental as the default with `--full` as an explicit flag.

9. **Citation format conventions** — author-year is the default in the original proposal; do any of the three projects use Vancouver, APA, or another style? Affects the citation validator's parsing in sub-feature 9.

10. **Are there project-specific skills I haven't anticipated?** The original proposal lists ingest, query, rebuild-index, validate-citations, promote-answer-to-library, lint. The production projects added agent-knowledge-updater. Are there others I'm missing?

---

## Adjustments to Sub-feature Scopes

Based on the analysis above, sub-features 2-12 are mostly correctly scoped. Two minor adjustments worth flagging:

### Sub-feature 5 (`agent-knowledge-updater`) — possible scope shift

If all three production projects use the updater heavily, it should be treated as universal-core rather than value-add. This doesn't change the implementation effort but it does change how prominently we feature it in documentation. Confirm during sub-feature 1 review.

### Sub-features 5 and 6 — tight coupling

Sub-feature 5 (the updater agent) and sub-feature 6 (the three operations skills, which include `kb:ingest` that wraps the updater) are tightly coupled. The `kb:ingest` skill is essentially "invoke the updater." Worth doing sub-feature 5 first, then sub-feature 6 immediately after, possibly merging them in the same commits.

### Sub-feature 4 (librarian) — Sonnet decision is locked in

The librarian agent ships with Sonnet as the default model. Documentation explains why (command-line tool use) and how to downgrade to Haiku for cost-conscious projects that don't need filesystem navigation.

### Sub-feature 12 (env validation extension) — opt-in default confirmed

The env validation integration is opt-in via configuration. The default is OFF — installing the plugin does not change env validation behaviour automatically. Projects opt in by adding one line to the `[Knowledge Base]` section of CLAUDE.md.

### No sub-features need to be removed, merged, or split

The dependency graph in the EPIC is sound. The work can proceed in roughly the order it's filed, with sub-feature 5+6 done together and sub-feature 11 (documentation) last.

---

## Summary

The pattern is clear enough to start building. Three production validations, the original proposal, and Karpathy's gist together give us enough specificity to implement sub-features 2-12 without needing to copy verbatim files from non-public projects. The ten open questions above are calibration points — answering them mid-build will save review cycles, but their absence doesn't block progress.

**Next sub-features in dependency order:**
1. **Sub-feature 2 (#107)** — plugin scaffolding. Mechanical: directory structure, manifest, release-mapping entries.
2. **Sub-feature 4 (#109)** — librarian agent. The system prompt is validated; the work is the agent definition file, model selection, tool allowlist, and adversarial testing.
3. **Sub-feature 7 (#112)** — index management. Hash-based change detection, shelf-index format, `kb:rebuild-indexes` skill.
4. **Sub-feature 3 (#108)** — schema section template for CLAUDE.md.
5. **Sub-feature 5 (#110)** + **sub-feature 6 (#111)** — `agent-knowledge-updater` and the three operations skills, done together.
6. **Sub-feature 8 (#113)** — templates and starter pack with our SDLC research as dogfood.
7. **Sub-feature 9 (#114)** — citation validator.
8. **Sub-feature 10 (#115)** — `kb:promote-answer-to-library`.
9. **Sub-feature 12 (#117)** — opt-in env validation extension.
10. **Sub-feature 11 (#116)** — documentation and positioning. Last.

Sub-feature 13 (#118, codebase-index) is a future branch.

---

*This document is the deliverable for sub-feature 1 of EPIC #105. It is open for review and correction. The ten open questions above are the highest-value targets for Steve's confirmation.*

# Feature Proposal: Knowledge Base Pattern Extraction

**Proposal Number:** 106
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `feature/sdlc-knowledge-base`
**EPIC:** #105 (sdlc-knowledge-base — reusable project knowledge base plugin)
**Sub-feature:** #106 (sub-feature 1 of 13)

---

## Executive Summary

The first sub-feature of EPIC #105 is **research, not build**. Three projects are already using the research library pattern proposed by the first project. Each implemented it in Claude Code in roughly a day. They converged on the same shape but extended it in production with hash-based change detection, two-index design, an `agent-knowledge-updater` agent, Sonnet (not Haiku) for the librarian, and staleness checks integrated into environment validation.

Before we package any of this as the `sdlc-knowledge-base` plugin, we need to know what's actually shared across the three implementations versus what each project customised. This sub-feature surveys the three implementations, cross-references the findings against Karpathy's LLM Wiki gist, and produces a "reusable essence" document that scopes sub-features 2-12.

The output is a single document at `docs/architecture/knowledge-base-pattern.md`. No code is written in this sub-feature.

---

## Motivation

### Problem statement

We have a pattern that works in production at three independent projects. We have a foundation document (`research/research-library-approach.md`) describing the original proposal. We have user-reported extensions (hashes, two indexes, agent-knowledge-updater, Sonnet librarian, env validation integration). We have Karpathy's LLM Wiki gist describing the same conceptual shape independently.

What we don't have is a clear inventory of:
- Which parts of the pattern are universal across all three projects (signal for "core, ship as-is")
- Which parts each project customised differently (signal for "configurable, ship a default")
- Which parts only one or two projects use (signal for "value-add, optional")
- Which Karpathy concepts the production pattern adopted vs missed
- Which Karpathy concepts the production pattern doesn't include but should

Without this inventory, sub-features 2-12 of the EPIC are guessing at the shape. Implementing the wrong shape is expensive: we'd ship a plugin that doesn't quite match what the production projects use, and the existing users would rightly ignore it.

### Why this must come first

Sub-feature 1 is the chicken-and-egg moment. Every other sub-feature in the EPIC depends on knowing the right shape:

- **Sub-feature 2 (plugin scaffolding)** needs to know what files to scaffold
- **Sub-feature 3 (schema template)** needs to know the conventions to encode
- **Sub-feature 4 (librarian agent)** needs to verify the system prompt is unchanged
- **Sub-feature 5 (agent-knowledge-updater)** needs to know what the production agent actually does
- **Sub-feature 6 (three operations skills)** needs to know how the production projects organise the workflow
- **Sub-feature 7 (index management)** needs to know the index format and the hash strategy
- **Sub-feature 8 (templates and starter pack)** needs to know the library file format
- **Sub-feature 9 (citation validator)** needs to know what citations look like in the production library files
- **Sub-feature 10 (promote-answer-to-library)** needs to know how synthesis files are distinguished from primary research
- **Sub-feature 11 (documentation)** needs to describe what we built
- **Sub-feature 12 (env validation extension)** needs to know how the production projects integrate staleness

If sub-feature 1 finds that the production projects have converged on something significantly different from the original proposal, sub-features 2-12 may need to be re-sized, re-ordered, merged, or split. That's the right thing to discover *now*, not three weeks into building the wrong plugin.

### User stories

- As the framework author, I want a clear inventory of what's shared across the three production implementations so the plugin matches what they actually use, not what I guessed at
- As a contributor implementing sub-features 2-12, I want a single reference document that tells me the format, the schema, the agent prompts, and the workflow conventions so I'm not guessing
- As one of the three existing pattern users, I want to be able to look at the plugin and recognise it as what I built — with optional defaults that match my customisations
- As a future fourth user, I want the plugin to be the version of the pattern that has been validated in production, not a re-derivation from the original proposal

---

## Proposed Solution

A focused research and synthesis exercise producing one document. Four steps.

### Step 1: Survey the three implementations

For each of the three projects already using the pattern, gather (from Steve, since the projects are not public):

- **Library file structure** — frontmatter schema, sections used, citation format
- **Index design** — shelf-index format, codebase-index format if used, master-index if used, hash strategy
- **Librarian agent system prompt** — verbatim if possible, or a confirmation that it matches the original proposal
- **Workflow skills** — what custom skills did they build (ingest path, query path, lint path, rebuild-index path)
- **Touch-points with existing SDLC operations** — env validation, retrospectives, anywhere else the indexes are consumed
- **`agent-knowledge-updater`** — the system prompt, what triggers it, what decisions it makes, what it touches
- **Hash-based change detection** — how it's implemented, when indexes are rebuilt incrementally, how stale entries are pruned
- **Model choices** — which agents use which models, why

The minimum needed is the actual files (or summaries of them). If walking through them in conversation is easier than file access, that works too — but the goal is concrete artifacts, not abstract descriptions.

### Step 2: Build the convergence/divergence matrix

For each component identified in step 1, classify it as one of:

- **Universal** — all three projects do this the same way. Signal: ship as-is in the plugin, no configuration.
- **Configurable** — all three projects do this, but each customised it differently. Signal: ship a sensible default, expose the configuration point.
- **Value-add** — only one or two projects do this. Signal: ship as optional or defer to a future sub-feature.
- **Project-specific** — done in only one project for project-specific reasons that don't generalise. Signal: don't ship; document as an extension pattern.

The matrix is the most important output. It's the explicit answer to "what is the reusable essence?"

### Step 3: Cross-reference Karpathy's gist

Karpathy's LLM Wiki gist describes the same conceptual pattern independently and is more abstract than the production implementations. For each Karpathy concept, classify as:

- **Adopted by production** — the production pattern matches Karpathy here (validates the design)
- **Diverged from Karpathy** — the production pattern does this differently (worth understanding why; may or may not be worth importing back)
- **Missing from production but worth importing** — Karpathy concepts the production pattern doesn't include but that would add value (e.g., the lint operation, log.md format, the "promote answer to library" insight, the schema-as-CLAUDE.md pattern)
- **Not relevant to SDLC use** — Karpathy concepts that don't apply or are too heavyweight (Obsidian integration, qmd vector search, Marp slide decks, image handling hotkeys)

### Step 4: Produce the reusable essence document

Synthesise steps 1-3 into a single document at `docs/architecture/knowledge-base-pattern.md` with the following sections:

1. **Overview** — what the pattern is, in one paragraph
2. **Three layers** — raw sources, library files, librarian; what each layer contains and who writes to it
3. **Three operations** — ingest, query, lint; how each works in the production pattern
4. **Universal components** — the things all three projects do identically (ship as-is)
5. **Configurable components** — the things each project customised (ship a default, expose configuration)
6. **Value-add components** — the things only some projects do (optional or future)
7. **Karpathy concepts adopted** — what we're importing from the gist and why
8. **Karpathy concepts skipped** — what we're not importing and why
9. **Open questions for sub-features 2-12** — specific decisions that depend on findings here (e.g., "exact frontmatter schema", "log.md entry format", "lint check categories")
10. **Adjustments to sub-feature scopes** — if the survey reveals that any of sub-features 2-12 should be re-sized, merged, split, or removed, this section documents the adjustments and references the affected issues

---

## Success Criteria

- [ ] All three implementations surveyed; concrete artifacts (files, system prompts, workflow definitions) gathered or summarised
- [ ] Convergence/divergence matrix produced — every component classified as universal / configurable / value-add / project-specific
- [ ] Karpathy's gist cross-referenced — every Karpathy concept classified as adopted / diverged / missing-but-worth-importing / not-relevant
- [ ] `docs/architecture/knowledge-base-pattern.md` exists, is reviewed by Steve, and is committed to the branch
- [ ] Open questions for sub-features 2-12 documented (specific, answerable, not vague)
- [ ] Sub-features 2-12 of the EPIC are re-sized or re-scoped if the survey reveals they should be — issue updates committed and visible
- [ ] No code written in this sub-feature

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Three projects diverged more than expected — "pattern" is really three different implementations | Plugin can't ship one shape that matches all three | The matrix will surface this. If divergence is high, the plugin ships configurable points and a sensible default; users override per project. Worst case: scope down the EPIC to a smaller core that all three do share. |
| One project's extension is genuinely worth shipping but the others don't have it (e.g., codebase-index in only one project) | Risk of over-shipping for two projects, under-shipping for one | The codebase-index is already filed as value-add (#118). Other extensions surfaced by the survey get classified the same way. |
| Steve's time is the bottleneck for surveying three non-public projects | Sub-feature 1 stalls | Multiple paths: file access, conversation walkthroughs, summary documents. Whatever is fastest for Steve. The sub-feature can complete with summaries — verbatim files are nice but not essential. |
| The reusable essence document becomes a 50-page survey rather than a useful spec | Doesn't actually unblock sub-features 2-12 | Document target: 5-15 pages. If it grows beyond that, split into a survey appendix and a focused essence document. The essence document is the deliverable; the survey is supporting evidence. |
| Karpathy's gist is the wrong reference point for production patterns that diverged from it | Wasted cross-referencing effort | The gist is one of several inputs, not the primary source of truth. Production wins. If they diverged from Karpathy, that's a finding, not a problem. |

---

## Out of scope

- **Building any plugin code.** Sub-features 2-12 do that. Sub-feature 1 produces only a document.
- **Validating the citation accuracy of any library files.** Sub-feature 9 builds the validator.
- **Re-evaluating whether the pattern is worth packaging.** The EPIC has already committed to packaging it; this sub-feature decides the *shape* of the package.
- **Embedding-based retrieval / vector search.** Out of scope for the entire EPIC.

---

## Changes Made

| Action | File |
|--------|------|
| Create | `docs/architecture/knowledge-base-pattern.md` (the reusable essence document; produced by this sub-feature) |
| Possibly modify | Sub-feature issues #107-#117 (re-scoped if the survey reveals adjustments are needed) |
| Create | `docs/feature-proposals/106-knowledge-base-pattern-extraction.md` (this file) |

---

## Required from Steve before this sub-feature can start

The three projects using the pattern are not public. To survey them I need access to (or summaries of) the actual artifacts:

1. **The librarian agent definition** for at least one project (the original proposal claims all three kept it identical — verify)
2. **The library file template / frontmatter schema** as actually used in each project
3. **The shelf-index format** as actually used in each project
4. **The `agent-knowledge-updater` definition** from whichever project has it
5. **Any custom skills** built around the workflow (ingest, query, lint, rebuild-index)
6. **The env validation integration code or configuration** showing how staleness is detected
7. **The codebase-index format** from the project that has it (informs sub-feature 13)
8. **Model choices and the rationale** for any deviations from the original proposal (e.g., Sonnet over Haiku)

If walking through these in conversation is easier than sharing files, that works equally well. The output is the same: a clear picture of what each project actually built.

---

## References

- EPIC: #105 — sdlc-knowledge-base
- Sub-features that depend on this: #107, #108, #109, #110, #111, #112, #113, #114, #115, #116, #117 (every other core sub-feature)
- Foundation document: `research/research-library-approach.md` (commit `0f1155c` on this branch)
- Karpathy LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Independent of EPIC #97 (commissioning) — the knowledge base is orthogonal to SDLC option choice

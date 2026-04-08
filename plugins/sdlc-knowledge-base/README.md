# sdlc-knowledge-base

Filesystem-based project knowledge base for projects that need to ground decisions in evidence.

The plugin packages a research library pattern validated in production by three projects. It ships a librarian agent, an active curator agent, hash-tracked indexes, the three operations from Karpathy's LLM Wiki framing (ingest / query / lint), citation validation, and an opt-in environment validation extension. Orthogonal to the SDLC option a project commissioned — install alongside Solo, Single-team, Programme, or Assured.

## Quick start

```bash
# Install the plugin
/plugin install sdlc-knowledge-base@ai-first-sdlc

# Initialise your project (default: with starter pack)
/sdlc-core:kb-init

# Try a query against the starter pack
/sdlc-core:kb-query "What does our research say about specification formality?"

# Replace placeholder hashes with real ones
/sdlc-core:kb-rebuild-indexes
```

That's the minimal flow. The starter pack ships with three example library files synthesised from Agentic SDLC research; replace or extend with library files relevant to your own problem space.

## What this plugin provides

### Agents

| Agent | Purpose | Model |
|---|---|---|
| `research-librarian` | Stateless retrieval-and-synthesis. Reads the shelf-index, identifies the 2-4 most relevant library files for a query, deep-reads only those, returns structured evidence with citations. **Read-only.** | Sonnet (for command-line tool use) |
| `agent-knowledge-updater` | Proactively integrates new sources into the library. Reads a source, classifies it, identifies which existing files it touches, makes surgical updates or creates new files, updates the shelf-index, appends to log.md. **The only agent with write access to the library.** Opinionated about what belongs. | Sonnet |

### Skills (10)

| Skill | Purpose |
|---|---|
| `/sdlc-core:kb-init` | Initialise a project: append `[Knowledge Base]` section to CLAUDE.md, create `library/` structure, optionally seed with starter pack |
| `/sdlc-core:kb-ingest <source>` | Integrate a new source into the library (wraps `agent-knowledge-updater`) |
| `/sdlc-core:kb-query <question>` | Query the library (wraps `research-librarian`); supports `--promote-to-library` |
| `/sdlc-core:kb-lint` | Six-check health report: contradictions, stale claims, orphan files, missing cross-references, concepts lacking pages, data gaps |
| `/sdlc-core:kb-rebuild-indexes` | Hash-based incremental rebuild of the shelf-index |
| `/sdlc-core:kb-promote-answer-to-library` | File a query result back as a new library page with provenance tracking |
| `/sdlc-core:kb-validate-citations` | Spot obvious citation hallucinations (DOI resolution, arXiv ID validation) |
| `/sdlc-core:kb-staleness-check` | Opt-in check for shelf-index drift; designed to be wired into pre-push hooks |

### Templates and starter pack

- `[Knowledge Base]` section template for appending to CLAUDE.md (Karpathy's "schema as CLAUDE.md" pattern)
- Library file template (frontmatter + 7-section structure)
- Shelf-index format example
- Three example library files (the starter pack) synthesised from Agentic SDLC research

## When to use this plugin

**Use it when:**
- You're making evidence-grounded decisions and want them traceable to research
- You're accumulating research over time and want it organised rather than scattered
- You need citable findings for stakeholder communications, executive reports, expert reviews
- Your project survives team changes — knowledge needs to outlast individuals
- You're running a programme with multiple consuming teams and decisions need defensible evidence

**Don't use it when:**
- The project is a throwaway prototype with no need for long-term knowledge
- Decisions don't need citation (routine maintenance, simple bug fixes)
- The information is operational state, not domain evidence (use a tracker, runbook, or auto-memory instead)
- You don't have any research to put in it — empty knowledge bases are zero-value

**Compatible with all four SDLC options.** Particularly valuable for Programme and Assured contexts where evidence quality directly affects decision quality.

## The three modes

The plugin supports three usage modes depending on how much investment you want to make:

### Minimal (1 day setup)

- Run `/sdlc-core:kb-init --with-starter-pack` (the default)
- The starter pack gives you 3 working library files immediately
- Add 2-3 more library files of your own using the format shown in the starter pack
- Skip deep research engines; manually curate sources from things you already have
- Skip lint and validation initially
- **Use case**: a small team that wants to start grounding decisions in evidence without committing to a big upfront investment

### Standard (1 week setup)

- Run `/sdlc-core:kb-init`
- Use a deep research engine (Perplexity Pro, Gemini Deep Research, ChatGPT Deep Research) to commission 10-15 research prompts on the project's key topics
- Synthesise the raw results into 10-20 library files via `/sdlc-core:kb-ingest`
- Run `/sdlc-core:kb-rebuild-indexes` after each batch
- Run `/sdlc-core:kb-validate-citations` to spot obvious hallucinations
- Run `/sdlc-core:kb-lint` periodically (weekly or before major reviews)
- **Use case**: a team or programme that wants the full research library pattern as developed by the original three production projects. This is the proven shape.

### Programme (2+ weeks setup)

- Standard mode plus:
- Cross-team library: multiple sub-domains, each with its own set of library files
- Wire `/sdlc-core:kb-staleness-check --strict` into pre-push validation
- Use `kb-promote-answer-to-library` regularly to compound exploration value
- Periodic lint with action items tracked back to research commissions
- **Use case**: a programme with multiple teams making interdependent decisions, where evidence quality is institutional rather than individual

## Relationship to other concepts

This is the most important section to read before installing. The knowledge base is one of several knowledge stores in the framework, and using the right one for the right purpose is essential.

| Concept | Scope | Belongs in knowledge base? |
|---|---|---|
| **Architecture Decision Records (ADRs)** | Decisions made by the project (the "we chose X because Y") | No — ADRs are their own thing. ADRs **cite** library files. They are complementary. |
| **Auto-memory system** | Session and project context (user preferences, recent work, framework decisions) | No — auto-memory is for personal/project context. The knowledge base is for **domain evidence about a problem space**. |
| **`deep-research-agent`** | Runs structured research campaigns to *produce* new research output | Complementary — the deep-research-agent **feeds** the knowledge base. Run a research campaign with deep-research-agent, then ingest the result with `kb-ingest`. |
| **Commissioning options (EPIC #97)** | The shape of the project's SDLC (Solo / Single-team / Programme / Assured) | Orthogonal — the knowledge base installs alongside whatever option a project commissioned. Doesn't change the SDLC shape. |
| **Operational state** (deployments, configs, secrets) | Project infrastructure | No — this belongs in your tracker, runbooks, or secrets manager. The knowledge base is for evidence, not operational state. |
| **Internal contact information** | Team directory | No — team directory. |
| **Research findings, frameworks, thresholds, citations** | Evidence about a problem space | **Yes** — this is exactly what the knowledge base is for. |

The `agent-knowledge-updater` is opinionated about this distinction. When you ask it to ingest something that doesn't belong in the knowledge base, it tells you and recommends the right destination instead of silently accepting it.

## Honest limitations

**Citation accuracy needs manual spot-checking.** Deep research engines occasionally fabricate DOIs, attribute findings to the wrong author, or invent journal names. The `kb-validate-citations` skill catches obvious cases (DOIs that don't resolve, arXiv IDs that don't exist) but cannot guarantee accuracy. Spot-check 10-20% of citations manually, especially for high-stakes claims.

**The librarian is only as good as the library.** If a topic isn't in the library, the librarian says so. It does not guess. Set expectations that the library covers specific topics, not everything.

**The library needs active maintenance.** Programme Relevance sections drift as projects evolve. New findings need to be integrated, not just appended. The lint operation surfaces issues; it does not auto-fix them. Plan for regular library hygiene.

**Deep research engines aren't free or universally accessible.** The standard and programme modes assume access to Perplexity Pro, Gemini Deep Research, ChatGPT Deep Research, or equivalent. The minimal mode and manual curation work without them, but slower.

**The plugin assumes specific kinds of projects.** Research-heavy, evidence-based, decisions consequential enough to justify the upfront investment. Most small projects don't need it. Be honest about whether your project fits.

**The librarian uses Sonnet by default.** Cost per query is higher than Haiku. The reason is reliable command-line tool use (find, grep) which Haiku struggles with. If your project doesn't need filesystem navigation, you can downgrade to Haiku in the agent's frontmatter.

## Migration from a hand-rolled implementation

The pattern was first deployed by three projects independently. If your project already uses a hand-rolled version of the same pattern, the plugin should be a near-drop-in replacement:

1. **Librarian system prompt** — the plugin's `research-librarian` is close to the original proposal that all three projects kept as-is. If you customised the system prompt, diff against `agents/knowledge-base/research-librarian.md` and re-apply your customisations.
2. **Library file format** — the plugin's frontmatter and section structure match the original proposal. If your files match, no migration needed. If you added custom frontmatter fields, they remain — the librarian ignores fields it doesn't know about.
3. **Shelf-index format** — the plugin uses inline content hashes per entry. If your existing index doesn't have hashes, run `/sdlc-core:kb-rebuild-indexes --full` to regenerate the index with hashes.
4. **agent-knowledge-updater** — if you have your own updater, compare its decision rules against the plugin's. The plugin's updater is opinionated about what belongs in the knowledge base; if your version is more permissive, decide which philosophy to keep.
5. **Custom skills** — if you built custom skills around the workflow, they keep working. The plugin's skills coexist; you can adopt them gradually.

The plugin's job is to make a fourth project's setup take minutes instead of a day. It doesn't force migration — it lowers the barrier for new adopters.

## References

- Pattern document: `docs/architecture/knowledge-base-pattern.md` (in the framework repo)
- Original proposal: `research/research-library-approach.md` (in the framework repo)
- Karpathy's LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- EPIC: #105 (Multi-Option Commissioned SDLC EPIC #97 is independent)

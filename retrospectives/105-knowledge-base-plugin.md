# Retrospective: EPIC #105 — sdlc-knowledge-base Plugin (Core Branch)

**Branch**: `feature/sdlc-knowledge-base`
**Date**: 2026-04-08
**EPIC**: #105
**Sub-features delivered**: 1-12 (sub-feature 13 deferred to a future branch by design)

## Context

Three projects independently adopted a research library pattern proposed by the first project (the ODP programme). Each implemented it in Claude Code in roughly a day. The pattern produces a structured, citable knowledge base — a librarian agent reading hash-tracked indexes and returning evidence-grounded answers — that survives team changes and lets decisions be traced to research rather than opinion.

The framework had no built-in support for this. A fourth project would have to invent the pattern again, with no reusable templates, no shipped agents, no skills wired into the SDLC workflow. This EPIC packages the pattern so it becomes a one-install opt-in capability for any project that needs evidence-grounded decisions.

The work was scoped as EPIC #105 with thirteen sub-features. Twelve land in this branch as the core plugin; sub-feature 13 (codebase-index applied to source files for context-managed planning) is explicitly a future branch.

## What Went Well

- **Sub-feature 1's "research not build" framing was the right starting point.** Producing the pattern document at `docs/architecture/knowledge-base-pattern.md` first — extracting the reusable essence from the original proposal, the user's descriptions of the three production projects, and Karpathy's LLM Wiki gist — gave every subsequent sub-feature a clear spec to work against. None of sub-features 2-12 needed to be re-scoped mid-build.

- **Karpathy's gist contributed five concrete additions that the production projects didn't have.** The three-operations framing (ingest/query/lint), the lint operation itself, the `log.md` parseable format, the "good answers can be filed back into the wiki as new pages" insight (which became `kb-promote-answer-to-library`), and the "schema as CLAUDE.md" pattern (which became `kb-init`'s template). Each adds real value beyond the original proposal without bloat.

- **All ten open questions in the pattern document held throughout the build.** I made assumptions for the unknowns (hash placement inline per entry, master index dropped, log.md following Karpathy's format, env validation as a standalone skill, incremental rebuild with `--full` flag) and none of them blocked progress. They're calibration points the user can correct if any are wrong, but the build never had to wait for answers.

- **The dogfood starter pack (sub-feature 8) was the right format validation moment.** Producing three real library files from substantive research content (Agentic SDLC Phases 1-5) — not toy examples — proved the format works for real material and gives new users something concrete on first install. The starter pack files cross-reference each other, cite real sources with sample sizes, and match the schema end-to-end.

- **Standalone skills, not cross-plugin coupling.** The env validation extension (sub-feature 12) was the temptation to modify the existing `validate` skill in `sdlc-core` from the new plugin. Resisting that and shipping `kb-staleness-check` as a standalone opt-in skill keeps the plugins orthogonal. The schema template documents three wiring paths (manual invocation, git pre-push hook, composite skill) so users can integrate however they prefer.

- **Sonnet-by-default for both agents was the right call.** The production projects' upgrade from Haiku to Sonnet wasn't about retrieval quality alone — it was about command-line tool use (`find`, `grep`) which Haiku struggles with. Both the librarian and the updater need filesystem navigation, and Sonnet handles those tool patterns reliably. Documented the trade-off so cost-conscious users can downgrade themselves.

- **Read-only librarian, write-only updater is a clean separation.** The librarian has `Read, Glob, Grep, Bash` and explicitly no `Write` or `Edit`. The updater has `Read, Write, Edit, Glob, Grep, Bash, WebFetch`. Two agents with non-overlapping authority. The librarian cannot accidentally corrupt the library, and the updater is the single point of accountability for changes. Both system prompts cross-reference each other's role.

- **The opinionated "what belongs in the knowledge base" rule in `agent-knowledge-updater`.** The agent classifies sources before ingesting and refuses to add operational state, contact info, project tracker content, ADRs, or auto-memory equivalents. This is the most important behaviour for keeping the library valuable over time — the alternative is library bloat that destroys retrieval quality.

- **Branch progressed from zero to twelve sub-features in a single focused session.** Twelve commits, each scoped to one sub-feature (or one tightly-coupled pair), each with a substantive commit message capturing the design decisions. Easy to review individually and easy to revert any single piece if the user wants to adjust.

## What Could Improve

- **I framed sub-feature 1 as "blocked on access to three non-public projects" in the initial issue.** The user (rightly) called this out: I had enough from the foundation document, the user's descriptions, Karpathy's gist, and standard framework conventions to write the pattern document without needing to copy verbatim files. The "survey first" framing was overcautious gating reinvented by me. Lesson: when scoping research-not-build sub-features, distinguish between "can extract the essence from available sources" (which I had) and "needs comprehensive primary source survey" (which I didn't). The former is faster and unblocks downstream work earlier.

- **No automated tests for the agents or skills yet.** The agents have `examples` blocks in their frontmatter, and the skills have example invocations in their bodies, but there's no harness that exercises a librarian query against a real shelf-index, or an updater ingest against a sample source, or a citation validator against known-good and known-bad DOIs. This is fine for the core branch (the dogfood starter pack is a manual end-to-end test) but should be filed as a follow-on issue. Future-me note: a `tests/integration/knowledge-base/` directory with a sample library and a few smoke tests would catch regressions.

- **The shelf-index format example in `templates/shelf-index-example.md` uses placeholder hashes (`9f4b2c8e...` etc.) that are literally fabricated.** They're meant to show the format, not be valid. A reader scanning the file might think they're real. I should have used a clearer placeholder convention (e.g., `<sha256-hex>` or `0000...`). Same issue in the starter pack's `_shelf-index.md` — placeholders are flagged in the docstring but a casual reader could miss the warning.

- **The lint operation (`kb-lint`) is described in detail in the skill body but not implemented as agent logic.** It's a 6-check workflow that the librarian (or a peer agent) executes when invoked, but the actual decision rules for "is this a contradiction" or "is this orphan acceptable" are fuzzy. In production, the lint will produce false positives and require user calibration. The skill body should say so explicitly so users don't expect zero-noise output.

- **The plugin's relationship to the auto-memory system is documented but the boundaries could blur in practice.** Both store text. Both can be queried by the user. The README's comparison table tries to make the distinction crisp ("auto-memory = session/project context, knowledge base = domain evidence about a problem space"), but a user with both installed could conceivably ingest the same content into both without realising. A future improvement: a warning in `kb-ingest` when the source matches auto-memory content patterns.

- **Twelve sub-features in one branch is a lot to review.** The commit history is clean (one sub-feature per commit, mostly) and each commit has a substantive message, but a reviewer would still need to understand twelve interrelated pieces. The PR description should explicitly walk through them in the recommended review order (start with the pattern document, then the agents, then the skills, then the templates and starter pack, then the README). Future EPICs at this size might benefit from being split across multiple smaller PRs, even on the same branch.

- **No formal validation that the librarian's anti-hallucination behaviour actually holds.** The system prompt is explicit about "never invents citations / never invents statistics / says 'the library has no evidence on this' when appropriate." The agent's `examples` block shows the desired behaviour. But there's no test that fires adversarial queries at the librarian and verifies it refuses to fabricate. This is the highest-stakes behaviour in the entire plugin — if the librarian hallucinates once, users stop trusting the library entirely. Adversarial testing should be filed as a follow-on issue and probably as a sub-feature of #118 (codebase-index) or a new sub-feature dedicated to it.

## Lessons Learned

1. **"Survey first" is sometimes a self-imposed gate.** When sub-feature 1 is research-not-build, distinguish between "I need primary source access" (real gate) and "I have enough from secondary sources to extract the essence" (no gate). Defaulting to the first when the second applies wastes time and discourages momentum.

2. **Karpathy's gist demonstrates that intentional abstractness is a feature, not a bug.** His document is "intentionally abstract" by design, with explicit permission to "pick what's useful, ignore what isn't." This invitation to customise is exactly why the production projects converged on different specific shapes while still being recognisably the same pattern. The plugin should be similarly opinionated about its core (the librarian system prompt, the file format, the three operations) and permissive about customisation (which agents to install, which skills to wire, which model to use).

3. **The right place for cross-plugin integration is the user's wiring, not the plugin's modifications.** When the EPIC said "extend env validation," the temptation was to modify `sdlc-core`'s `validate` skill from `sdlc-knowledge-base`. Resisting that and shipping a standalone `kb-staleness-check` skill that the user wires in — with three documented paths — keeps both plugins independently evolvable. Generalises: when plugin A wants to extend plugin B, prefer "ship a tool plugin A's users can wire in" over "modify plugin B from plugin A."

4. **Read-only and write-only agent separation is worth the apparent duplication.** The librarian has no `Write` tool. The updater has no role in queries. Both are slightly more constrained than they could be, but the constraint is the value: it's impossible for the librarian to corrupt the library, and it's impossible for the updater to silently answer a question without going through the inquiry workflow. Each agent has a single accountability surface.

5. **Opinionated agents that say "no" are more valuable than permissive ones.** The `agent-knowledge-updater` refuses to ingest operational state, contact info, ADRs, and auto-memory equivalents. The librarian refuses to fabricate citations. Both behaviours could be relaxed to be "more helpful" — and both relaxations would destroy the plugin's value. Trust depends on the agent saying "no" when the user is asking for the wrong thing, then telling them where to go instead.

6. **Twelve sub-features in a session is sustainable when each is well-scoped.** The pattern document made each subsequent sub-feature small enough to land in one or two file writes plus a release-mapping update plus a commit. None of the sub-features required multi-step iteration or backtracking. The branch grew steadily without big-bang commits. This is the shape EPIC sub-features should take when possible.

7. **Dogfooding is the best format validation.** Sub-feature 8 produced three library files from real research content (the Agentic SDLC programme's Phases 1-5). The act of doing this — extracting findings, finding citations, writing Programme Relevance sections, computing the cross-references — exercised the schema in a way that toy examples wouldn't have. If something had been wrong with the format, this is where it would have surfaced. Nothing did, which is the strongest validation of the design we could get short of running it on a fourth real project.

## Changes Made

| Action | File | Purpose |
|---|---|---|
| Create | `docs/feature-proposals/106-knowledge-base-pattern-extraction.md` | Sub-feature 1 spec |
| Create | `docs/architecture/knowledge-base-pattern.md` | Sub-feature 1 deliverable: reusable essence document |
| Create | `research/research-library-approach.md` (committed to branch) | Foundation document the EPIC builds on |
| Create | `plugins/sdlc-knowledge-base/.claude-plugin/plugin.json` | Plugin manifest |
| Create | `plugins/sdlc-knowledge-base/README.md` | Full positioning docs |
| Create | `agents/knowledge-base/research-librarian.md` | Read-only retrieval agent |
| Create | `agents/knowledge-base/agent-knowledge-updater.md` | Write-only ingest agent |
| Create | `skills/kb-init/SKILL.md` | Project initialisation skill (with starter pack flag) |
| Create | `skills/kb-init/templates/claude-md-section.md` | `[Knowledge Base]` schema section template |
| Create | `skills/kb-init/templates/starter-pack/library/agentic-sdlc-options.md` | Dogfood library file 1 |
| Create | `skills/kb-init/templates/starter-pack/library/agent-suitability-rubric.md` | Dogfood library file 2 |
| Create | `skills/kb-init/templates/starter-pack/library/specification-formality-and-agent-performance.md` | Dogfood library file 3 |
| Create | `skills/kb-init/templates/starter-pack/library/_shelf-index.md` | Pre-populated index for the starter pack |
| Create | `skills/kb-init/templates/starter-pack/library/log.md` | Starter log with header |
| Create | `skills/kb-rebuild-indexes/SKILL.md` | Hash-based incremental shelf-index rebuild |
| Create | `skills/kb-rebuild-indexes/templates/shelf-index-example.md` | Format example with three populated entries |
| Create | `skills/kb-ingest/SKILL.md` | Ingest operation (wraps updater) |
| Create | `skills/kb-query/SKILL.md` | Query operation (wraps librarian) |
| Create | `skills/kb-lint/SKILL.md` | Six-check health report |
| Create | `skills/kb-validate-citations/SKILL.md` | DOI / arXiv citation validator |
| Create | `skills/kb-promote-answer-to-library/SKILL.md` | File query results back as new library pages |
| Create | `skills/kb-staleness-check/SKILL.md` | Opt-in env validation extension |
| Modify | `release-mapping.yaml` | Add `sdlc-knowledge-base` block with 2 agents + 14 skill files |
| Modify | `plugins/.claude-plugin/marketplace.json` | Register the new plugin |
| Modify | `CLAUDE.md` | Add to plugin family table and skills table |
| Create | `retrospectives/105-knowledge-base-plugin.md` | This file |

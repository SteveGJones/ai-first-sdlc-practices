# Retrospective: #145 + #146 — Technology Registry Schema Design + Population

**Branch**: `feature/142-tech-registry`
**Date**: 2026-04-10
**Issues**: #145 (schema design), #146 (population)
**Type**: Schema design + data population
**Context**: Sub-features 3 and 4 of EPIC #142 (Curated Technology Registry)

## Context

Setup-team and pipeline-orchestrator discover technology-specific tools via real-time web search. This is slow, non-deterministic, and produces inconsistent results. EPIC #142 aims to replace this with a curated, version-controlled technology registry.

Sub-feature 3 (#145) was the schema design. Sub-feature 4 (#146) was populating the registry for the top technologies. The user chose to merge both into a single branch after deciding to expand the initial population from 3 example entries to 31 technologies.

## What Went Well

- **Brainstorming surfaced 7 design questions before writing any files.** Structured Q&A resolved Section C representation, install snippets, cross-references, trusted sources, freshness tracking, aliases, and detection patterns. No ambiguity remained when writing the spec.

- **User-driven design pivots improved the outcome.** Three decisions the user overrode from the recommended approach all proved correct:
  1. Split files over monolithic (recommended: single file for 30 entries; user chose split for future scalability)
  2. YAML over JSON (surfaced as a late question — fewer tokens, more readable)
  3. Expanded scope from 3 examples to 31 technologies (merged sub-features 3+4)

- **Parallel research agents were highly effective.** 10 research agents covering 34 technologies ran in parallel, completing in ~5 minutes total. Every agent returned verified data with exact package names, publishers, URLs, and capabilities. This replaced what would have been hours of sequential web search.

- **Research revealed significant differences from assumptions.** Every illustrative example in the original plan was wrong in at least one field:
  - MongoDB: package is `mongodb-mcp-server` (not `@mongodb/mcp-server`), has a full Claude Code plugin, `motor` is deprecated
  - Redis: official MCP is on PyPI not npm (`redis-mcp-server`), env vars are granular (not a single URL), `ioredis` is on maintenance mode
  - AWS: 84+ official MCP servers (not 1), all on PyPI as `awslabs.*`, SDK v2 is end-of-support

- **Cross-validation caught real issues during the process.** The Redis subagent discovered YAML parse errors from unquoted colons in publisher names and fixed them before committing.

- **Detection patterns added to the index was a valuable late addition.** Originally not in the proposed schema, adding detection patterns to `_index.yaml` makes the registry self-contained — adding a technology automatically teaches setup-team to detect it.

## What Could Improve

- **The example entries in the spec doc are now stale.** The schema doc (`docs/architecture/technology-registry-schema.md`) still contains the original illustrative MongoDB/Redis/AWS examples with incorrect package names. The actual files have correct data, but someone reading the spec might be confused by the discrepancy. Should update the spec examples to match reality, or add a note that examples are illustrative.

- **Section B ecosystem enum doesn't cover Java/Go.** The schema defines `ecosystem` as one of `pip`, `npm`, `cargo`, `go`, `gem` — but the `go` value was intended for Go modules (pkg.go.dev), and Java (Maven/Gradle) has no match. Java, Go, and Terraform technology files omit Section B as a workaround. Future schema evolution should add `maven` and `go-module` to the ecosystem enum, or rename `go` to `go-module` for clarity.

- **Some technology files were created by subagents that committed independently.** This created 5 separate commits for what could have been a single atomic commit of all 31 files. Not a problem functionally, but the git history is noisier than ideal.

- **Vue was included without dedicated research.** The Vue entry is minimal — no MCP servers, just the framework package. It was added to fill a gap in the JS framework category but should be properly researched in a future update.

## Decisions Made

See `docs/architecture/technology-registry-schema.md` — Design Decisions Log (11 decisions with rationale).

Additional decisions made during implementation:
- Merged sub-features 3 and 4 into one branch (user direction)
- Curated AWS to 8 of 84+ servers in the registry file (noted full catalog URL)
- Excluded deprecated/archived MCP servers (@modelcontextprotocol/server-postgres, @elastic/mcp-server-elasticsearch)
- Noted tools on maintenance mode (ioredis, kafkajs) with recommended alternatives

## Key Artifacts

| Artifact | Path |
|----------|------|
| Schema design doc | `docs/architecture/technology-registry-schema.md` |
| Implementation plan | `docs/superpowers/plans/2026-04-10-technology-registry-schema.md` |
| Registry index | `data/technology-registry/_index.yaml` |
| Technology files (31) | `data/technology-registry/*.yaml` |

## Metrics

- 31 technologies populated
- 31 aliases defined
- 116 detection patterns across 7 ecosystems (pip, npm, docker, env, go, gem, cargo)
- 10 parallel research agents completed in ~5 minutes
- 5 parallel implementation agents created all files in ~3 minutes
- All cross-validation rules pass
- All project validation checks pass

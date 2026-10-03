# Feature Proposal: Curated Technology Registry — Schema Design + Population

**Proposal Number:** 145 + 146
**Status:** Complete
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-10
**Target Branch:** `feature/142-tech-registry`
**EPIC:** #142
**Sub-features:** #145 (schema design), #146 (populate registry)

---

## Motivation

Setup-team and pipeline-orchestrator discover technology-specific tools via real-time web search (setup-team step 5c, pipeline-orchestrator Phase 0). This is:

1. **Slow** — each technology requires multiple web searches (npm, PyPI, GitHub, vendor sites)
2. **Non-deterministic** — same technology searched twice may yield different results
3. **Missing curated quality** — web search results lack verified install instructions, Section C gap templates, and framework cross-references
4. **Hardcoded detection** — package-to-technology mappings (e.g., `psycopg2` -> PostgreSQL) are hardcoded in the skill

---

## Proposed Solution

A curated technology registry at `data/technology-registry/` — split YAML files (one per technology) with an `_index.yaml` index. This PR delivers both the schema design (#145) and initial population of 31 technologies (#146).

### What the registry provides

1. **Data-driven detection**: `_index.yaml` contains 116 detection patterns across 7 ecosystems (pip, npm, docker, env, go, gem, cargo), replacing hardcoded mappings
2. **Pre-authored discovery data**: each technology file contains Section A (Claude Code tools), Section B (project libraries), and Section C (gap templates) — ready to emit in discovery reports
3. **Framework cross-references**: `our_agents` maps technologies to complementary SDLC agents with plugin name and relevance string
4. **Freshness tracking**: per-entry `verified_date` + registry-level `staleness_threshold_days`
5. **Fallback-safe**: technologies not in the registry fall back to existing web search behavior

### Key design decisions

See `docs/architecture/technology-registry-schema.md` for the full schema and 11 design decisions with rationale. Key choices:

- YAML over JSON (~20-30% fewer tokens for LLM consumers)
- Split files (one per technology) for scalability and clean git diffs
- Detection patterns in index (data-driven, no code changes to add technologies)
- Pre-authored Section C gap templates (curated quality, no web search latency)
- Hybrid install snippets (category templates + install_override for edge cases)
- Separate alias lookup table (cross-cutting concern)
- Per-technology agent cross-references with context

### Technologies populated (31)

| Category | Technologies |
|----------|-------------|
| Databases | MongoDB, PostgreSQL, MySQL, Elasticsearch, SQLite, Redis, Supabase |
| Cloud | AWS (84+ MCP servers), Azure, GCP |
| Messaging | Kafka, RabbitMQ, Flink |
| Python frameworks | Flask, Django, FastAPI, Streamlit |
| JS frameworks | Express, Next.js, React, Vue |
| Languages | Java, Go, Rust, Ruby, Python |
| DevOps | Docker, Kubernetes, Terraform |
| Services | Stripe, GitHub Actions |

---

## Success Criteria

- [x] Schema design document at `docs/architecture/technology-registry-schema.md`
- [x] `_index.yaml` with aliases, detection patterns, and manifest for 31 technologies
- [x] 31 technology YAML files with verified data from web research
- [x] All YAML files parse correctly
- [x] Cross-validation passes (rules 7-10: index-file consistency, alias/detection targets, no duplicates)
- [x] Per-entry validation passes (required fields, type/ecosystem/source-type enums)
- [x] Project validation passes (`--quick`)

---

## Changes Made

| Action | File |
|--------|------|
| Create | `docs/architecture/technology-registry-schema.md` (schema design) |
| Create | `docs/superpowers/plans/2026-04-10-technology-registry-schema.md` (implementation plan) |
| Create | `data/technology-registry/_index.yaml` (registry index) |
| Create | `data/technology-registry/*.yaml` (31 technology files) |
| Create | `docs/feature-proposals/145-technology-registry-schema.md` (this file) |
| Create | `retrospectives/145-technology-registry-schema.md` |

---

## Downstream

| Sub-feature | Issue | Next step |
|-------------|-------|-----------|
| 5: Wire into setup-team | #147 | Modify skill to read registry before web search |
| 6: Wire into pipeline-orchestrator | #148 | Modify agent Phase 0 to check registry first |
| 7: Cross-reference our plugins | #149 | Review and expand `our_agents` across all files |
| 8: Maintenance strategy | #150 | Define staleness checks, update cadence, validator CI |

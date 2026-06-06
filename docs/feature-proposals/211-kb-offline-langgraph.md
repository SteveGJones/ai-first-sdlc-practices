# Feature Proposal #211 — kb-offline: LangGraph + Ollama backend (M0 foundation)

**Status:** In progress
**Target Branch:** `feature/211-kb-offline-langgraph`

## Motivation
The knowledge-base kit is token-heavy and cloud-only. A pluggable local backend (LangGraph +
Ollama) cuts token cost to ~zero and runs offline. This EPIC also completes the LLM-wiki's
shared-core story. M0 builds the safety foundation first: typed contracts, durable journaled
mutation with fencing, resume-selection, and the backend ownership boundary.

## Proposed Solution
See `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md`. M0 delivers contracts.py,
durability.py, resume.py, mutation.py, the generate/embed backend seam (Anthropic + Fake),
pipeline.py, a minimal Anthropic-backed `kb-offline` CLI, prompt-parity CI check, and an
eval-harness skeleton.

## Success Criteria
- [ ] Claim-structured Answer + MutationProposal contracts (Pydantic), unit-proven.
- [ ] Durable journaled mutation: WAL ordering, fencing token, create/extend CAS, fsync, recovery.
- [ ] Resume-selection: `--resume`/latest-compatible, lifecycle states, stale-lock TTL.
- [ ] Backend = generate/embed only; pipeline owns validation + mutation.
- [ ] Anthropic-backed `kb-offline ingest`/`query` exercise the foundation end-to-end.
- [ ] Prompt-parity drift check green; eval skeleton runs on the fixture; thresholds ratified.

## Out of scope (this milestone)
Ollama backend, LangGraph graphs, ingest-bulk, federation, embeddings, promotion beyond contract —
M1–M4.

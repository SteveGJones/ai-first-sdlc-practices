# Feature Proposal: Local MLX backend for the model council

**Proposal Number:** 234
**Status:** Implemented (PR #234)
**Author:** Claude (Opus 4.8) — pairing with SteveGJones
**Created:** 2026-07-26
**Target Branch:** `feature/model-council-mlx`
**Tracking Issue:** #232 (follow-on)

---

## Motivation

`sdlc-model-council` v1 (PR #233) assesses the models reachable via hosted peer
CLIs (codex, agy, opencode) and casts them into a roster. Every one of those is a
**paid, hosted** model that sends prompts off-device. Apple-Silicon machines can
run capable coder models **locally** via MLX at genuine **$0 marginal cost, no
egress, fully private**. The open question this feature answers with real numbers:
**does a local MLX model grade well enough on the standardized problem stack to
earn a roster seat against the paid hosted fleet — as a privacy-preserving,
zero-cost reviewer/worker?** This must be measured on a constrained (32 GB
unified-memory) machine where the local wave runs sequentially.

## Problem Statement

MLX models are not reachable through the existing adapters. Two integration
routes exist, and the first-order question is which one yields a **fair** quality
signal on a 32 GB Mac without an engine rewrite.

## User Stories

- As a council operator on Apple Silicon, I want to assess local MLX models on the
  same stack as the hosted fleet, so I can see grade / $0 / latency side by side.
- As a privacy-conscious team, I want a $0, no-egress local reviewer in the roster
  for code that must not leave the machine.

## Proposed Solution

### High-Level Approach

Evaluate **Path A first** (MLX *through* OpenCode's OpenAI-compatible custom
provider, addressed `opencode:mlx/<model>`, reusing the existing opencode adapter
with zero new code). If Path A yields a fair signal, ship it; otherwise build
**Path B** — a dedicated `mlx:<model>` adapter (one directory: `adapter.json` +
`adapter.sh` + a small client, zero engine edits) that talks to a local
`mlx_lm.server` OpenAI endpoint sending **only the item prompt** (no agentic
system prompt).

### Technical Approach

- `mlx-local` free family in `pricing.json` + `priors/mlx-local.json` (matches
  `opencode:mlx/`, `mlx:`), so budget gates treat MLX as genuine $0.
- Run each MLX model on its own `mlx_lm.server` at `--max-concurrent 1` (32 GB
  can't hold two large models); merge per-model results into one roster.
- Include a hosted anchor in the comparison for a true local-vs-hosted roster.

### Alternatives Considered

Path A (opencode-mediated) was tried first and **rejected for the comparison**:
OpenCode's tool-schema-heavy agentic system prompt induced small local models to
escape quotes in reproduced code, corrupting file-block answers and scoring 0 —
a harness artifact, not a quality signal. The raw server (Path B) is clean.

## Implementation Plan

1. Path-A smoke test (solve the `OPENCODE_CONFIG` provider-precedence wrinkle).
2. `mlx-local` family + priors.
3. Path B dedicated `mlx` adapter + mock + resume test.
4. Gated live comparison (7B/14B/32B + hosted anchor) → roster + diversity.
5. Re-derive priors from the audition; record findings.

## Success Criteria

- A local MLX model is assessable on the 4 objective dims via the council, at $0.
- The comparison answers: does a local model grade ≥ B on bug-fix / code-review?
  what is the quality-vs-latency curve across 7B/14B/32B? does a local member add
  material (decorrelated) value to a hosted panel?
- Full council test suite stays green; zero technical debt in new code.

## Acceptance Criteria

- `mlx` adapter passes descriptor lint + a mock-based resume test; `list-backends`
  shows it correctly.
- Live comparison run recorded in `retrospectives/232-external-agent-delegation.md`.

## Risks

- 32 GB memory pressure on 32B (long-context KV cache → swap): mitigated by
  running 32B on a reduced dim set.
- Local latency is high: mitigated by generous timeouts and sequential runs.

## Security & Privacy

MLX runs fully on-device with no network egress — the privacy headline of the
feature. The adapter wires no tools, so `read-only` is structurally absolute.

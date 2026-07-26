# Feature Proposal: Council tool-use & command-line-execution assessment

**Proposal Number:** 235
**Status:** Draft
**Author:** Claude (Opus 4.8) — pairing with SteveGJones
**Created:** 2026-07-26
**Target Branch:** `feature/council-tool-use-assessment`
**Tracking Issue:** #235 (follow-on to #232 / PR #234)

---

## Motivation

The `sdlc-model-council` assessment (v1 + the local-MLX backend, PR #234) grades
models on **four static, single-turn** dimensions — code-review, bug-fix,
long-context, instruction-format. None of them measures **agentic tool use**:
emit a tool/command call → execute → observe output → decide the next action →
iterate → know when to stop. The `tool-use` prior is an un-audited placeholder
(0.42), explicitly flagged as not exercised by the v1 stack.

That leaves a recurring, practical question answerable only by extrapolation:
**how do models compare at command-line execution and monitoring** — local MLX
(Qwen2.5-Coder 7B/14B/32B) vs **Haiku 4.5** vs the hosted fleet (codex/agy/
opencode)? The intuition (fast, agentic-tuned hosted models win on latency ×
tool-call reliability across long loops; local's measured strengths are one-shot
code tasks and a $0 private review voice) has **no head-to-head numbers**, and
Haiku has never been in the comparison at all.

## Problem Statement

The council cannot currently grade a model on tool use / command-line execution,
and cannot produce a local-vs-Haiku-vs-hosted comparison for that capability,
because (a) there is no agentic tool-use dimension in the stack and (b) the Path
B `mlx` adapter is deliberately text-only (no tool surface), so local models
literally cannot execute commands as integrated today.

## User Stories

- As a council operator, I want a tool-use / command-line-execution grade per
  model so I can route command-running and monitoring work to the right backend.
- As a privacy-conscious team, I want to know whether a $0 local model is *good
  enough* at command execution/monitoring to replace a hosted agentic model.
- As a framework maintainer, I want the tool-use prior backed by real audition
  data rather than a placeholder.

## Proposed Solution

### High-Level Approach

Add a **tool-use / command-line-execution** capability to the assessment stack
and run a comparison that includes **Haiku 4.5 as an anchor** alongside local MLX
and the hosted fleet. Because agentic execution is both a harness problem and a
safety problem, the first design decision is *how* to elicit and score the
capability (see Alternatives).

### Technical Approach (to be refined during design)

- New stack dimension `tool-use` (and possibly a distinct `command-exec` /
  `monitoring` split) with deterministic items and a scorer.
- A **propose-and-score** default: the model is given a goal + a simulated
  terminal transcript and must emit the correct command(s)/next action; scoring
  is deterministic against a golden command set / decision, with **no real shell
  execution** in the default path (safety + reproducibility). An optional,
  sandboxed real-execution mode is a stretch.
- Metrics beyond a scalar grade: tool-call **format validity**, **task success**,
  **turns-to-success**, **latency** (compounds badly for local), **cost** (local
  $0) — surfaced in the roster.
- Reuse the existing schedule/estimate/roster/diversity machinery; add the new
  dimension to priors for every relevant family (including a real, non-placeholder
  `mlx-local` tool-use prior once auditioned).

### Alternatives Considered

- **Real sandboxed shell execution** for each turn — highest fidelity but a
  safety/reproducibility burden (non-determinism, destructive-command risk);
  deferred to an opt-in stretch mode.
- **Wire a tool surface into the `mlx` adapter** so local models can truly
  execute — larger scope, and conflates model capability with harness plumbing;
  the propose-and-score proxy isolates the capability first.
- **Skip local, compare only hosted** — rejected; the local-vs-Haiku question is
  the whole point.

## Implementation Plan

1. Design the dimension + scoring contract (propose-and-score; item schema;
   metrics) — via `superpowers:writing-plans-and-specs`.
2. Author 3–5 deterministic command-line-execution / monitoring items with golden
   answers.
3. Add the scorer + wire the dimension into the stack, priors, roster, diversity.
4. Run the gated comparison: local MLX (7B/14B/32B) + **Haiku 4.5** + hosted fleet.
5. Re-derive the `tool-use` prior from the audition; record findings.

## Success Criteria

- A `tool-use` / command-line-execution dimension is integrated and gradable via
  the existing council flow, with deterministic scoring.
- A recorded comparison with **Haiku 4.5 as an anchor** produces real grade /
  task-success / turns-to-success / latency / $ numbers for local MLX vs Haiku vs
  the hosted fleet.
- The `mlx-local` `tool-use` prior is replaced with an audition-derived value.
- Full council test suite stays green; zero technical debt in new code.

## Acceptance Criteria

- New scorer + items pass unit tests; the dimension appears in the roster/diversity
  outputs.
- Comparison results and the local-vs-Haiku verdict recorded in
  `retrospectives/235-council-tool-use-assessment.md`.

## Risks

- **Safety of real execution** → default to propose-and-score with no live shell;
  gate any real-execution mode behind explicit opt-in + sandboxing.
- **Fairness across backends** — the text-only `mlx` adapter vs tool-native CLIs;
  the propose-and-score proxy keeps the elicitation uniform (single prompt, no
  agentic system prompt), consistent with the Path B fairness lesson from #234.
- **Latency** — local agentic loops are slow; keep item turn-counts bounded and
  record latency as a first-class metric rather than a blocker.

## Open Questions

- Is a single `tool-use` dimension enough, or should `command-exec` and
  `monitoring` (stop-condition judgment over a stream) be separate dimensions?
- Should Haiku be reached via the Claude API directly or through an existing
  agentic CLI wrapper, for an apples-to-apples harness?

## Security & Privacy

Default path performs **no real command execution** (propose-and-score only), so
no destructive-command or egress risk from the assessment itself. Any real-shell
stretch mode must run under a sandbox with a read-only/safe task set and explicit
operator authorisation.

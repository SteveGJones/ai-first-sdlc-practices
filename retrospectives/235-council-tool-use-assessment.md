# Retrospective: Council tool-use & command-line-execution assessment

**Branch:** `feature/council-tool-use-assessment`
**Date:** 2026-07-26 (started)
**Duration:** In progress
**Tracking Issue:** #235 (follow-on to #232 / PR #234)

---

## Summary

Add a **tool-use / command-line-execution** capability to the `sdlc-model-council`
assessment and run a comparison across local MLX (Qwen2.5-Coder 7B/14B/32B),
**Haiku 4.5**, and the hosted fleet — turning the currently un-audited `tool-use`
prior (0.42 placeholder) and the extrapolated "Haiku should win command execution
on latency × tool-call reliability" intuition into real, measured numbers.

## Why this feature exists

The v1 stack measures only static, single-turn dimensions; nothing exercises the
agentic loop (emit command → observe → decide → iterate → stop). The local-MLX
comparison (PR #234) therefore could not answer "how do local models compare with
Haiku for command-line execution and monitoring?" — the answer was extrapolation
only. This feature closes that gap with a deterministic, safety-first assessment.

## Goals / success criteria (from the proposal)

- A `tool-use` / command-line-execution dimension integrated into the stack,
  priors, roster, and diversity machinery, with deterministic scoring.
- A recorded comparison with **Haiku 4.5 as an anchor** producing grade /
  task-success / turns-to-success / latency / $ numbers.
- Replace the `mlx-local` `tool-use` placeholder with an audition-derived prior.
- Full council suite green; zero technical debt.

## Decisions & rationale

- _(to be filled in as the design lands)_ — leading candidate is a
  **propose-and-score** contract (no live shell in the default path) for safety
  and reproducibility, keeping elicitation uniform (single prompt, no agentic
  system prompt) consistent with the Path B fairness lesson from #234.

## What went well

- _(to be filled in during implementation)_

## What was hard / surprising

- _(to be filled in during implementation)_

## Follow-ups

- _(to be filled in)_

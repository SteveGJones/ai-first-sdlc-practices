# Charter: `sdlc-model-council` — cross-model fan-out with a team-onboarding assessment

**Issue:** #232 · **Branch:** `feature/external-agent-delegation` · **Status:** Charter (pivot from `sdlc-simple-orchestration`) · **Date:** 2026-07-25
**Supersedes the *positioning* of:** `2026-07-24-sdlc-simple-orchestration-design.md` (the adapter engine + unified contract from that doc are KEPT as the substrate; the "delegate to a backend" framing is demoted to an internal primitive).

## Why this pivot

Honest self-assessment (2026-07-25): as a "delegate a task to one external CLI" tool, `sdlc-simple-orchestration` was **close to a needless addition** — the official `codex-plugin-cc` and the `antigravity` plugin already wrap their vendors with richer per-vendor features, and our context-isolation / extensibility advantages are not user-visible differentiators. The ONE thing no base plugin does is reason about **which models, in what combination, for what work** — cross-model fan-out. That becomes the charter.

## Charter statement

> **`sdlc-model-council`** — Onboard the AI models reachable on this machine (via codex, agy, opencode… which are themselves *gateways* to many models) by assessing them against a **standardized problem stack**, cast them into roles from the results, and run **cross-model fan-out strategies** (consensus, contrast+synthesis, best-of-N, generator↔verifier) that deploy the right models for each task — with the strategy chosen **per project** from the live roster.

The metaphor is deliberate and native to this repo: **team formation, but for models instead of agent personas.** Models audition, earn roles, and the fan-out plays deploy the roster.

## Core concepts

### 1. The fleet
Backends are model *gateways*, not single models: `agy models` lists Gemini 3.x, Claude-Opus, gpt-oss…; opencode routes to many providers (incl. free models); codex is GPT-5.x. The addressable fleet is 15+ models across 3 adapters — too many to hand-pick, which is why the assessment + roster exist. A model is addressed as `(adapter, model-id)`.

### 2. The onboarding assessment (the spine)
A curated **standardized problem stack** of graded micro-tasks, each scored by the MOST OBJECTIVE method available (not just a judge):

| Dimension | Task | Scorer (objectivity) |
|---|---|---|
| code-gen | implement a small spec | hidden tests pass (objective) |
| bug-fix | buggy code + failing test → fix | test goes green (objective) |
| code-review | diff with **planted defects** | found / missed / false-positive (objective) |
| refactor | restructure | behavior preserved (tests) + complexity drop (metric) |
| reasoning/architecture | design question | rubric, judge-scored (subjective) |
| research | web-grounded question | cited-fact check (semi-objective) |
| long-context | needle-in-haystack | exact match (objective) |
| instruction/format | strict output contract | parse check (objective) |
| tool-use/agentic | multi-step sandbox goal | goal achieved (objective) |

Each reachable model runs the stack (via its adapter) → **per-dimension normalized scores + cost + latency**, plus a **diversity map** computed from *where models agree/disagree on the same items* (so fan-out casts a *decorrelated* panel, not models sharing blind spots). Output = a project-local **roster card**: each model's strengths, cost, suggested roles, confidence.

Objective-scored dims (planted defects, hidden tests, needle) avoid judge bias; a judge (Claude, the orchestrator) is used only for inherently subjective dims, and never grades a peer it will later be pooled with without that being noted.

### 3. The fan-out plays (v1 patterns)
| Play | Input → combine | Best for |
|---|---|---|
| **Diff + Synthesis** | same task → N models → agreement/disagreement → attributed synthesis | reviews & analysis (v1 lead) |
| **Consensus / Vote** | same task → majority verdict | high-stakes yes/no gates |
| **Best-of-N** | divergent generations → score (tests/judge) → select winner | generation ("different options, compare outcomes") |
| **Generator ↔ Verifier** | one produces, a *different* model checks | catch hallucinations/bugs |

(Full taxonomy also includes Union/Sweep, Debate, Cascade, Map/Partition, Specialist-Routing — later.)

### 4. The project policy
`task-type → { play, cast of models, budget guardrail }`, chosen at project start from the roster + project characterization (languages, task-mix, risk, budget/latency). Persisted; consulted at runtime so `/delegate` and `/compare` auto-pick the play. This is the "team dynamic."

### 5. Rating sourcing (decided)
**Static priors + optional audition.** Ship coarse versioned per-family priors (instant, day-one usable); the onboarding assessment is opt-in at commission time and grounds ratings in the *actually reachable* models. **Learned/adaptive** (update the roster from accepted-vs-reverted outcomes over the project) is a fast-follow.

## Kept substrate (from v0.1.0, 313 tests)
The adapter engine (`extdel.sh` + `turn-supervisor.pl`), the unified return contract, `list-backends`, graded postures, and the one-directory adapter model — all become the **execution substrate** the assessment and plays run on. Nothing there is thrown away; fan-out *requires* its uniform results.

## Decisions locked (2026-07-25)
- **Name:** `sdlc-model-council` (rename from `sdlc-simple-orchestration`).
- **v1 patterns:** all four (Diff+Synthesis, Consensus, Best-of-N, Generator↔Verifier).
- **Rating source:** static priors + optional audition; adaptive later.
- **v1 vertical slice (prove value fast):** onboarding assessment → roster card → **Diff+Synthesis** end-to-end on a real decision, before building all four plays.

## Open questions for the architecture design
- Assessment harness: how to run the stack across N models cheaply/safely (free models for calibration; budget caps); how scorers plug in; how to keep the stack versioned + extensible.
- Diversity/correlation computation from per-item results.
- Roster + policy file formats (a KB page? a project config?).
- Judge selection & bias handling for subjective dims and for synthesis.
- Cost model: fan-out multiplies spend; free OpenCode models change the math; the policy must be budget-aware.
- How much of the `sdlc-core:setup-team` / commissioning flow to reuse (models-as-teammates).

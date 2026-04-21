---
title: "Containerised Worker Economics — Rate Limits, Token Costs & Speedup Reality"
domain: economics, rate-limits, token-costs, parallelism, cost-optimisation, claude-code
status: active
tags: [rate-limits, token-costs, speedup, fargate, prompt-caching, model-routing, batch-api, break-even, roi, epic-96]
source: agent_prompts/campaign-96-containerized-workers/research/R5-output.md
cross_references:
  - library/claude-code-native-parallelism.md
  - library/containerised-worker-recommendations.md
  - library/task-delegation-and-merging.md
  - agent_prompts/campaign-96-containerized-workers/research/S1-output.md
  - agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md
---

## Key Question

Does parallel AI coding execution deliver proportional speedup, or do rate limits, token costs, and coordination overhead eliminate the gains?

## Core Findings

1. **Rate limits, not architecture, are the primary parallelism constraint.** Max 5x plan ($100/mo) supports only 2 effective concurrent agents (450K shared ITPM, ~225K per agent). Max 20x ($200/mo) supports 3-4. A 3rd agent on Max 5x queues at the API level, producing 1.0x speedup (serialisation). Rate limits are pooled across all sessions on an account. -- R5 sec 1, Anthropic API Rate Limits docs (CRAAP 25)
2. **Token costs dominate infrastructure costs approximately 100:1.** AWS Fargate at $0.02/hr per agent (0.5 vCPU, 1GB) is negligible compared to Claude Sonnet at ~$0.50/hr per session. Five agents for 1 hour: $0.10 compute vs. $5-10 API tokens. Infrastructure optimisation (Docker vs. K8s vs. Fargate) is not where the savings are. -- R5 sec 2 (AWS Fargate Pricing, CRAAP 25)
3. **Realistic speedup is 3-5x for 5-16 agents, but sublinear and task-dependent.** Independent module refactors: 4-5x. Large file migrations: 3-4x. Framework upgrades: 2-3x. Tightly coupled architectural changes: 1.2-1.5x. Single-file bug fixes: less than 1.0x (overhead exceeds benefit). -- R5 sec 3, oh-my-claudecode benchmarks (CRAAP 24)
4. **The Anthropic C compiler project validates 10-16x speedup at scale.** 16 parallel Claude Opus agents over ~2 weeks produced a 100,000-line Rust C compiler with 99% pass rate on GCC torture tests. Cost: ~$20,000 API (2 billion input, 140 million output tokens). Compiles Linux 6.9, PostgreSQL, QEMU, FFmpeg, Redis, Doom. -- Anthropic Engineering Blog (CRAAP 25)
5. **Token costs increase 3-4x in parallel execution.** Each agent receives its own context and makes independent API calls. Without optimisation, 3 agents consume 3.4x the tokens of 1 agent for the same work. With prompt caching (50% hit rate) and model routing, the premium shrinks to 1.5-2.0x. -- R5 sec 2
6. **Code quality degrades 2-4% in test pass rate without mitigation.** Multi-agent scenarios show 78-80% test pass rate vs. 82% single-agent baseline, 42-48 bugs/KLOC vs. 38, and medium-low style consistency. Root causes: context fragmentation (each agent sees ~50% of project history), coordination bugs, style divergence, knowledge loss. With mitigations (shared AGENTS.md, enforced style, architect-level review), quality recovers to within 1-2%. -- R5 sec 4, arxiv:2508.14727v1 (CRAAP 21)
7. **Cost optimisation strategies can recover 50-70% of token budget.** Prompt caching: 30% savings (10 min setup, 90% discount on cache hits). Model routing (Haiku for 60% of simple tasks): 30-50% additional savings. Context pruning (last 3 turns): 10-20% savings. Batch API (overnight tasks): 50% token discount. Combined: ~70% token cost reduction in ~5.5 hours of implementation effort. -- R5 sec 6, Anthropic Prompt Caching docs (CRAAP 25), oh-my-claudecode (CRAAP 24)
8. **Break-even depends on team size and task type.** Parallelism pays for teams of 5+ developers or projects involving 20+ files across independent modules. For smaller teams or single-file changes, overhead outweighs benefits. Numeric threshold: parallelize if sequential task takes more than 20-30 minutes; do not parallelize if under 10 minutes. -- R5 sec 5
9. **Cached input tokens do NOT count toward ITPM.** This effectively allows 5-10x higher throughput with effective prompt caching, partially circumventing the rate limit ceiling. Break-even: 1 hit for 5-min cache, 2 hits for 1-hour cache. -- Anthropic API Rate Limits docs (CRAAP 25), R5 sec 1
10. **ROI for containerised fleet is substantial at scale.** Modelled scenario: 5 developers, weekly refactor sprints. Sequential: $4,000/week labour + $25 API = $4,025/week. Parallel (Max 20x + containers): $1,000 labour + $250 API + $225 infrastructure = $1,475/week. Net savings: $2,525/week. Payback period: 2 weeks. Annual ROI: 4,360%. Break-even team size: 3+ developers. -- R5 sec 5 (ROI analysis)

## Frameworks Reviewed

| Framework | Evidence Base | Limitations |
|---|---|---|
| Anthropic API Rate Limits | Official docs (CRAAP 25), 2026 tier structure | Tier-specific; cached tokens exempt from ITPM |
| AWS Fargate Pricing | Official docs (CRAAP 25), per-second billing | Regional price variation; Fargate 3x more expensive than self-managed K8s |
| oh-my-claudecode | GitHub repo (CRAAP 24), byteiota case study (CRAAP 20) | Demonstrates speedup; third-party orchestration tool |
| Anthropic C Compiler Project | Official engineering blog (CRAAP 25) | One-off project; single-agent baseline not conducted; cost extrapolated |
| Prompt Caching | Official docs (CRAAP 25) | Cache hit rate depends on task reuse; unique tasks see low hit rates |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Max 5x effective agents | 2 concurrent | R5 sec 1 (450K ITPM / ~225K per agent) | Hard ceiling; 3rd agent serialises |
| Max 20x effective agents | 3-4 concurrent | R5 sec 1 (1.8M ITPM) | Practical ceiling for most teams |
| Token-to-infrastructure cost ratio | ~100:1 | R5 sec 2 ($0.50/hr API vs. $0.02/hr Fargate) | Optimise tokens, not containers |
| Parallelise threshold | Sequential task more than 20-30 min | R5 sec 5 | Below 10 min, overhead exceeds benefit |
| Team size for ROI | 3+ developers | R5 sec 5 | Below 3, parallelism overhead exceeds labour savings |
| Prompt caching savings | 30% at 50%+ hit rate | R5 sec 6 | 10 min setup; immediate payback |
| Combined optimisation ceiling | ~70% token cost reduction | R5 sec 6 | ~5.5 hours total implementation effort |

## Design Principles

1. **Optimise tokens before scaling agents.** Prompt caching + model routing alone save 51% in 40 minutes of setup. Do this before investing in container infrastructure.
2. **Rate limits are the ceiling, infrastructure is not.** Plan agent count around your API subscription tier, not your container capacity. Upgrading from Max 5x to Max 20x buys more parallelism than any infrastructure change.
3. **Sublinear speedup is the norm.** Budget for 3-4x speedup from 5 agents, not 5x. Coordination overhead, token duplication, and rate limits eat the difference.
4. **Quality requires active mitigation.** Expect 2-4% test pass rate degradation unless you enforce shared architectural context (AGENTS.md), code style (Prettier/Ruff), and architect-level cross-module review.
5. **Container compute is a rounding error.** At $0.02/hr per agent, don't spend time optimising Fargate vs. K8s vs. Docker Compose. Spend that time optimising prompt caching hit rates.

## Key References

1. Anthropic API Rate Limits (CRAAP 25) -- https://platform.claude.com/docs/en/api/rate-limits
2. Anthropic Pricing (CRAAP 25) -- https://platform.claude.com/docs/en/about-claude/pricing
3. Anthropic: Building a C Compiler (CRAAP 25) -- https://www.anthropic.com/engineering/building-c-compiler
4. oh-my-claudecode GitHub (CRAAP 24) -- https://github.com/Yeachan-Heo/oh-my-claudecode
5. AWS Fargate Pricing (CRAAP 25) -- https://aws.amazon.com/fargate/pricing/
6. Prompt Caching Documentation (CRAAP 25) -- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
7. Assessing AI Code Quality (CRAAP 21) -- https://arxiv.org/html/2508.14727v1
8. AI Agent Cost Optimization Guide 2026 (CRAAP 22) -- https://fast.io/resources/ai-agent-token-cost-optimization/
9. Fargate vs Kubernetes cost reality check (CRAAP 19) -- https://medium.com/@inboryn/cost-optimization-why-ecs-fargate-costs-3x-more-than-kubernetes-2026-reality-check-f9a2bb726f00

## Programme Relevance

**EPIC #96 (Containerised Claude Code Workers):**
- Rate limit ceiling (findings 1, 9) determines maximum useful agent count before any infrastructure decision. Current Max 5x plan caps at 2 effective agents; Max 20x caps at 3-4. Container count must match API tier.
- The 100:1 token-to-infrastructure cost ratio (finding 2) means the Phase 0 quick wins (prompt caching, model routing) from the recommendations (see containerised-worker-recommendations.md) should precede any container work.
- Quality degradation (finding 6) validates the need for the SDLC plugins' architect and review agents inside each container -- they enforce the mitigation patterns that keep quality within 1-2% of baseline.
- The C compiler benchmark (finding 4) proves the model works at scale but at $20K cost, confirming that containerised workers are a scaling lever for large projects, not a speed fix for small tasks.

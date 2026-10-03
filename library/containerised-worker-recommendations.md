---
title: "Containerised Worker Recommendations — Strategic Synthesis & Phased Roadmap for EPIC #96"
domain: strategy, recommendations, roadmap, evaluation, containerisation, claude-code
status: active
tags: [conditional-go, phased-roadmap, docker-compose, kubernetes, ecs-fargate, quick-wins, evaluation-candidates, open-questions, epic-96]
source: agent_prompts/campaign-96-containerized-workers/research/S3-output.md
cross_references:
  - library/claude-code-native-parallelism.md
  - library/multi-agent-framework-landscape.md
  - library/containerised-worker-economics.md
  - library/task-delegation-and-merging.md
  - library/archon-workflow-engine.md
  - agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md
---

## Key Question

Should we build containerized Claude Code workers, or is native subagent parallelism sufficient? If we proceed, what is the phased roadmap?

## Core Findings

1. **Decision: Conditional GO with a critical pivot.** Containers are justified but NOT as the primary execution model. Native subagents remain the default (cheaper, simpler). Containerize only specific high-parallelism tasks where isolation is empirically necessary: multi-agent refactors (5+ agents), database schema migrations, multi-module feature development, CI/CD pipeline integration. -- S3 Deliverable 1 (consolidating R1-R5, S1-S2)
2. **Rate limits are the real ceiling, not architecture.** Max 5x plan ($100/mo) = 2 effective parallel agents. Max 20x ($200/mo) = 3-4. Containers cannot circumvent rate limits; they add operational cost for the same effective parallelism. Upgrade API plan before investing in container orchestration. -- S3 Deliverable 1 evidence (from R5 sec 1, S1 Cost Control)
3. **Five quick wins require no new infrastructure and should be implemented immediately.** (1) Prompt caching: 30% token savings, 10 min setup. (2) Model routing (Haiku for simple tasks): 30-50% savings. (3) Spec-driven task decomposition: 20-30% fewer merge conflicts. (4) Heartbeat liveness detection: detect stuck agents in less than 5 min. (5) Structured token logging: identify top 20% of agents consuming 80% of tokens. -- S3 Deliverable 2
4. **Five evaluation candidates for containerised workers, ranked by complexity.** (1) Docker Compose + shared volume polling (simplest MVP, 3-5 hours, 2-5 agents). (2) Kubernetes Jobs + Workload Identity (cloud-ready, 2-4 weeks, auto-scaling). (3) ECS Fargate + Task Roles (lowest ops on AWS, 2-3 weeks, serverless). (4) Queue-based dispatch via NATS/RabbitMQ (most scalable, 2-3 weeks, 10+ agents). (5) Hybrid local + containerised (most cost-efficient, 1-2 weeks, mixed routing). -- S3 Deliverable 3
5. **Phased roadmap with go/no-go triggers between phases.** Phase 0 (this week): quick wins, no infrastructure. Phase 1 (1-2 weeks): Docker Compose MVP with 2-3 agents, measure speedup. Phase 2 (2-4 weeks, conditional): K8s or ECS production deployment, triggered if Phase 1 shows 1.5x+ speedup. Phase 3 (2-3 weeks, conditional): scale to 5-10 agents, add queue-based dispatch if needed. Phase 4 (3-4 weeks, optional): production hardening, auto-scaling, hybrid execution. -- S3 Deliverable 4
6. **Phase 1 go/no-go trigger: 1.5x+ speedup on real tasks.** If Phase 1 Docker Compose MVP shows less than 1.5x speedup, parallelism is not effective for the team's workload; skip Phase 2 and stay with native subagents. Decision rule: measure single-agent task latency + task queue depth; if queue is empty (tasks finish before next arrives), no parallelism benefit from containers. -- S3 Deliverable 4, Phase 1 triggers
7. **File-level partitioning (95% success) plus sequential git merge (85%) are the recommended merge strategies.** Containers add isolation but not merge reliability. Good decomposition drives merge success, not container count. AI-assisted merge (60-75%) is experimental and should not be relied upon. -- S3 Deliverable 1 evidence (from R4 sec 3, S1 Result Aggregation)
8. **Existing A2A orchestrator should be kept and augmented.** Containers wrap workers; they do not replace the supervisor-worker orchestration pattern. Integration point: extend orchestrator to support Docker Compose spawning in parallel with native subagent spawning. Mixed execution (1 native + 1 containerised) should be validated in Phase 1. -- S3 Deliverable 1, S1 Orchestration decision
9. **Token optimisation (50-70% savings) buys more parallelism than infrastructure scaling.** Prompt caching + model routing alone save 51% in 40 minutes. This effectively gives 2-3x more parallelism budget without adding containers. Implement before Phase 1. -- S3 Deliverable 2 analysis (from R5 sec 6)
10. **Ten open questions require empirical answers during Phases 1-2.** (1) A2A protocol maturity timeline. (2) Empirical rate limit ceiling for team's API plan. (3) File-level partitioning success rate on actual codebase. (4) Prompt caching hit rate on team's tasks. (5) K8s vs. ECS Fargate selection. (6) Agent count threshold for queue-based dispatch. (7) A2A orchestrator integration with containers. (8) Minimum viable credential management for MVP. (9) Rate limit saturation handling at 5-10 agents. (10) Speedup threshold for declaring "parallelism not worth it" (recommended: less than 1.3x). -- S3 Deliverable 5

## Frameworks Reviewed

| Framework | Evidence Base | Limitations |
|---|---|---|
| Docker Compose (MVP) | S3 Candidate 1, tested pattern | Single-machine; manual scaling; not production-grade |
| Kubernetes Jobs | S3 Candidate 2, S1 Execution layer | Operational overhead; requires K8s cluster; 2-4 weeks setup |
| ECS Fargate | S3 Candidate 3, S1 Execution layer | AWS-only; serverless simplicity; 2-3 weeks setup |
| NATS Queue Dispatch | S3 Candidate 4, S2 patterns | Additional broker dependency; operational overhead; best for 10+ agents |
| Hybrid Local+Container | S3 Candidate 5, R5 cost analysis | Two execution paths to maintain; classifier accuracy critical |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Phase 1 go/no-go | 1.5x+ speedup | S3 Phase 1 trigger | Below this, containers not justified |
| Parallelism abandonment | Less than 1.3x speedup | S3 Question 10 | Coordination overhead (30%) exceeds benefit |
| Phase 2 entry | 3+ tasks waiting in queue | S3 Phase 2 trigger | Sustained demand justifies cloud orchestration |
| Phase 3 entry | 99%+ success rate over 1 week | S3 Phase 3 trigger | System stable enough to scale |
| Merge conflict ceiling | Less than 10% | S3 Summary Table | Above this, re-decompose tasks |
| Cost per task target | Less than $0.15 | S3 Summary Table | Includes API tokens + compute |

## Design Principles

1. **Native first, containerise on evidence.** Keep native subagents as the default execution model. Containerize only when empirical measurement shows isolation is necessary (database conflicts, environment collisions, 10+ agents).
2. **Phase 0 before Phase 1.** Implement the five quick wins (prompt caching, model routing, spec-driven decomposition, heartbeat liveness, token logging) before building any container infrastructure. These are zero-cost changes with 30-70% token savings.
3. **Go/no-go at every phase boundary.** Each phase has explicit entry and skip triggers. Do not proceed to Phase 2 without Phase 1 speedup validation. Do not proceed to Phase 3 without Phase 2 stability.
4. **Measure before scaling.** Empirically determine rate limit ceiling, merge success rate, caching hit rate, and speedup on real tasks before committing to production infrastructure.
5. **Augment, do not replace.** Containers wrap workers inside the existing supervisor-worker orchestration pattern. The existing A2A orchestrator continues to manage decomposition, delegation, and merge.

## Key References

1. S3-output.md -- Terminal recommendation synthesising R1-R5, S1-S2
2. S1-output.md -- Landscape map and build-vs-adopt decision matrix
3. S2-output.md -- Architecture patterns and anti-patterns (referenced by S3)
4. R1-output.md -- Claude Code native capabilities and isolation gaps
5. R2-output.md -- Multi-agent framework landscape
6. R4-output.md -- Task decomposition and merging strategies
7. R5-output.md -- Economics and real-world performance
8. archon-workflow-engine.md -- Archon as orchestration layer (compose, not compete)

## Programme Relevance

**EPIC #96 (Containerised Claude Code Workers):**
- This is the terminal recommendation for EPIC #96. The conditional GO means the team proceeds with containers but follows the phased roadmap with explicit go/no-go triggers.
- Phase 0 quick wins (finding 3) are immediate work items that should be implemented regardless of the containerisation decision.
- Docker Compose MVP (finding 4, Candidate 1) is the first container implementation target, scoped to 2-3 agents and 3-5 hours of setup.
- The 10 open questions (finding 10) form the research agenda for Phases 1-2. Each question has a suggested experiment and action item.
- The Archon integration model (see archon-workflow-engine.md) provides the process layer (DAG execution, parallelism, isolation, retry) while our SDLC plugins provide the team layer (68+ specialist agents). The Docker image containing Archon + Claude Code + SDLC plugins is the integration point.

**EPIC #97 (Commissioned SDLC):**
- The phased roadmap here informs EPIC #97's execution model. If containerised workers prove effective, commissioned SDLC options could leverage the same infrastructure for parallel phase execution.

**EPIC #142 (Technology Registry):**
- Model routing (finding 3, quick win 2) could be informed by the technology registry's model capability data. The registry could recommend which model to route each agent type to.

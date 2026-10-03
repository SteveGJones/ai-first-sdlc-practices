---
title: "Architecture Alternatives — Archon vs Build-Your-Own vs Framework Adoption"
domain: architecture, orchestration, alternatives-analysis, decision-matrix
status: active
tags: [archon, langgraph, crewai, openhands, agent-teams, build-vs-adopt, epic-96, containerisation]
source: agent_prompts/campaign-96-containerized-workers/research/R2-output.md
cross_references:
  - library/archon-workflow-engine.md
  - library/multi-agent-framework-landscape.md
  - library/claude-code-native-parallelism.md
  - library/containerised-worker-recommendations.md
---

## Key Question

Given the research landscape, should we adopt Archon, adopt a different framework, or build our own containerised worker orchestration? What are the concrete trade-offs?

## Core Findings

1. **No framework provides production-grade containerised multi-Claude-Code orchestration.** The closest are Archon (worktree isolation, container type planned but unbuilt), OpenHands (Docker sandbox but not Claude-native), and Claude Agent Teams (native but experimental, no containers). We will be assembling from parts regardless of choice. — R2 sec 6, S1 cross-cutting findings
2. **The research's S3 phased roadmap (build-your-own) independently reinvents what Archon already provides.** Docker Compose MVP → production orchestration → scale maps to implementing Archon's ContainerProvider and writing SDLC workflows as Archon DAGs. The build-it-yourself path takes 4-8 weeks to reach parity with Archon's existing DAG executor, worktree management, SDK wrapper, retry logic, output passing, and cost tracking. — S3 Deliverables 3-4 vs Archon source analysis
3. **Spec-driven decomposition (human/supervisor specifies boundaries) prevents 90% of agent collisions.** AI self-decomposition is unproven at scale. CrewAI's core value proposition (AI-driven manager coordination) contradicts this finding. Archon's deterministic DAG model aligns with it. — R4 sec 1.4, S1 Finding 2
4. **Rate limits, not architecture, cap parallelism.** Max 5x = 2 effective concurrent agents, Max 20x = 3-4. No framework or container strategy can circumvent Anthropic's ITPM ceiling. This limits the value of elaborate orchestration — simple is better when you can only run 2-4 agents anyway. — R5 sec 1, S1 Finding 3
5. **Token costs dominate infrastructure costs 100:1.** Fargate at $0.02/hr per agent vs Claude at $0.50/hr per agent session. Framework overhead, container runtime choice, and orchestration complexity are noise compared to token spend optimisation (caching, routing, context pruning). — R5 sec 2, S1 Finding 5

## Alternatives Comparison

### Option A: Archon + Our Plugins (Recommended)

| Dimension | Assessment |
|---|---|
| **What we get for free** | DAG executor (Promise.allSettled), worktree lifecycle, Claude SDK wrapper, retry/idle timeout, output passing ($node_id.output), cost cap (maxBudgetUsd), approval gates, model routing, multi-platform delivery (CLI/web/Slack/Discord/GitHub), 20 bundled workflow templates |
| **What we must build** | ContainerProvider (implementing IIsolationProvider for Docker), Docker image with Archon + Claude Code + SDLC plugins, SDLC workflows as Archon YAML DAGs, credential management for multi-container |
| **Integration model** | Archon orchestrates containers → each container runs Claude Code → Claude Code loads our plugins → node prompts reference our agents by name. No command-format bridge needed; Docker image is the integration point. |
| **Estimated effort** | 2-3 weeks (ContainerProvider + Docker image + 2-3 prototype workflows) |
| **Risk** | Archon is evolving rapidly; APIs may change. Container isolation is unbuilt (we'd be first implementers). Ralph DAG overlap with our Ralph usage needs investigation. |
| **Strength** | Leverages 15k-star MIT project. Mature DAG engine with production-tested patterns. Extensible isolation architecture. Community and maintainer support. |

### Option B: Build Our Own (S3 Phased Roadmap)

| Dimension | Assessment |
|---|---|
| **What we get** | Full control over architecture. No external dependency. Fits our existing plugin model exactly. |
| **What we must build** | DAG executor, worktree/container lifecycle management, Claude SDK wrapper, retry logic, output passing between workers, cost tracking, supervisor polling/queue dispatch, merge coordination, heartbeat liveness |
| **Integration model** | Custom Python/TypeScript orchestrator → spawns Claude Code via Agent SDK → manages Docker containers → coordinates via shared volumes or message queue |
| **Estimated effort** | 4-8 weeks for Phase 0-1 (to reach Docker Compose MVP with 2-3 agents). 8-12 weeks to match Archon's feature set. |
| **Risk** | Significant engineering time reinventing solved problems. Maintenance burden grows with features. No community to share load. |
| **Strength** | Zero dependency on external project. Architecture matches our mental model exactly. Can make any trade-off we want. |

### Option C: LangGraph + Custom Container Layer

| Dimension | Assessment |
|---|---|
| **What we get** | Most cited production orchestration framework. Graph-based state machines with Send() parallelism. Native checkpointing for long-running workflows. Python-native. |
| **What we must build** | Container lifecycle (LangGraph has no isolation concept), Docker image, credential injection, merge coordination, all Claude Code integration (LangGraph is LLM-agnostic), SDLC workflow definitions in Python code (not YAML) |
| **Integration model** | LangGraph graph nodes → call Claude Agent SDK → each node can optionally run in container. Custom container management layer wraps LangGraph. |
| **Estimated effort** | 4-6 weeks (LangGraph learning curve + container layer + Claude integration) |
| **Risk** | LangGraph doesn't handle isolation or container lifecycle — we'd build that ourselves. Python-only (our SDLC framework is mixed Python/Markdown). Heavier dependency than Archon (LangChain ecosystem). |
| **Strength** | Strongest state machine model. Checkpointing enables resume-from-failure. Most production evidence. |

### Option D: OpenHands (Learn From, Don't Adopt)

| Dimension | Assessment |
|---|---|
| **What we get** | Docker sandbox, event-stream architecture, hierarchical agent delegation, REST API coordination, audit trails |
| **What we must build** | Translation layer (our Claude Code agents → OpenHands agent abstraction), lose Claude Code-native capabilities (permission modes, --bare, Agent tool, worktrees) |
| **Integration model** | OpenHands platform → spawn sandboxed Docker containers → each container runs OpenHands agent runtime → Claude API via external integration |
| **Estimated effort** | 6-10 weeks (significant translation cost, unfamiliar framework) |
| **Risk** | High translation cost. Lose Claude Code-native features. OpenHands designed for LLM-agnostic approach, not Claude Code-specific patterns. |
| **Strength** | Best reference for containerised sandboxing. Event-stream architecture provides strong audit trails. Apache 2.0 licence. |

### Option E: Claude Agent Teams (Wait and Monitor)

| Dimension | Assessment |
|---|---|
| **What we get** | Native Claude Code integration. Zero setup. 2-8 parallel teammates with own context windows. Task-based coordination with implicit dependency management. |
| **What we must build** | Nothing for basic parallelism. But: no container isolation, no custom delegation logic, no workflow definition, no approval gates, no retry/escalation, no multi-platform delivery. |
| **Integration model** | Enable experimental flag → Claude Code natively coordinates teammates. No containers, no external tooling. |
| **Estimated effort** | 1 day to enable and test. But: if it doesn't meet needs, no path to extend. |
| **Risk** | Experimental API may change or be removed. No env/DB/port isolation. No cloud deployment path. Limited to 8 agents. No deterministic workflow control. |
| **Strength** | Zero infrastructure. Works today. Native Claude Code integration. |

## Decision Matrix

| Criterion | Weight | Archon+Plugins (A) | Build Own (B) | LangGraph (C) | OpenHands (D) | Agent Teams (E) |
|---|---|---|---|---|---|---|
| Time to first parallel run | High | 2-3 wk | 4-8 wk | 4-6 wk | 6-10 wk | 1 day |
| Container isolation | Must-have | Build ContainerProvider | Build from scratch | Build from scratch | Built-in | None |
| Claude Code native | Must-have | Yes (SDK wrapper) | Yes (SDK) | Partial (LLM-agnostic) | No (API only) | Yes (native) |
| Our plugin compatibility | Must-have | Yes (Docker image) | Yes (native) | Partial (Python wrapping) | No (translation needed) | Yes (native) |
| Workflow portability (YAML) | Nice-to-have | Yes | Custom format | No (Python code) | No | No |
| Community/maintenance | Important | 15k stars, active | Us only | LangChain ecosystem | Active OSS | Anthropic-maintained |
| Deterministic DAGs | Important | Yes | Must build | Yes | Partial | No |
| Rate limit economics | Critical | Per-node maxBudgetUsd | Must build | No built-in | No | No |
| Cloud deployment path | Must-have | Dockerfile exists | Must build | No | Docker-native | None |
| EPIC #97 alignment | Nice-to-have | YAML workflows = SDLC options | Custom mapping | Code-based mapping | No alignment | No |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Archon integration effort | <3 weeks | Source code analysis | If ContainerProvider + Docker image + 2-3 workflows takes <3 weeks, Archon wins over build-your-own |
| Build-your-own break-even | 4-8 weeks | S3 phased roadmap | If it takes longer than 8 weeks to match Archon's DAG executor + lifecycle, building is wrong |
| Rate limit ceiling | 2-4 agents (Max 5x/20x) | R5 sec 1 | Caps the complexity we need — simple orchestration may suffice |
| Token cost dominance | 100:1 over compute | R5 sec 2 | Optimise tokens, not infrastructure — frameworks matter less than prompt engineering |

## Design Principles

1. **Orchestration is commodity; domain intelligence is the differentiator.** Any framework can run a DAG. Our 68+ specialist agents, SDLC validation pipeline, and knowledge base are what make the system valuable. Don't spend 8 weeks building commodity orchestration.
2. **The Docker image is the integration point.** Archon + Claude Code + SDLC plugins in one image. No command-format bridges, no translation layers. The image IS the team member.
3. **Rate limits enforce simplicity.** We can run 2-4 agents on current plans. Elaborate orchestration for 2-4 workers is over-engineering. Start simple.
4. **Deterministic DAGs beat AI-driven decomposition.** Research shows spec-driven decomposition prevents 90% of collisions. Archon's YAML DAGs enforce this; CrewAI's AI-manager approach contradicts it.
5. **Build the ContainerProvider, not the orchestrator.** The highest-value contribution is implementing the container isolation that Archon's type system already declares but hasn't built. Let Archon handle the DAG execution.

## Key References

1. coleam00/Archon — https://github.com/coleam00/Archon (15.5k stars, MIT, TypeScript/Bun)
2. LangGraph — https://github.com/langchain-ai/langgraph (MIT, Python)
3. CrewAI — https://github.com/crewaiinc/crewai (MIT, Python)
4. OpenHands — https://github.com/OpenHands/OpenHands (Apache 2.0, Python)
5. Claude Code Agent Teams — https://code.claude.com/docs/en/agent-teams (Experimental)
6. S3-output.md — Terminal recommendations from research campaign
7. R2-output.md — Multi-agent framework landscape

## Programme Relevance

**EPIC #96**: This analysis narrows the architecture decision from 5 options to a clear recommendation: Archon + our plugins (Option A), with Option B (build our own) as fallback if Archon integration proves harder than estimated.

**EPIC #97**: Archon's YAML workflow format maps naturally to commissioned SDLC options. Each SDLC option becomes an Archon workflow, all using the same team of specialist agents. This synergy doesn't exist with LangGraph (Python code) or OpenHands (different paradigm).

**Decision point**: The brainstorming session should validate or challenge this recommendation before proceeding to design.

---
title: "Multi-Agent Framework Landscape — Orchestration, Sandboxing & Communication (2026)"
domain: multi-agent, orchestration, frameworks, sandboxing, communication-protocols, claude-code
status: active
tags: [openhands, crewai, langgraph, devin, agent-teams, metagpt, sandbox, docker, gvisor, firecracker, mcp, a2a, epic-96]
source: agent_prompts/campaign-96-containerized-workers/research/R2-output.md
cross_references:
  - library/archon-workflow-engine.md
  - library/claude-code-native-parallelism.md
  - library/task-delegation-and-merging.md
  - library/containerised-worker-recommendations.md
  - agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md
---

## Key Question

Has someone already built containerized multi-Claude-Code orchestration, and what established patterns, frameworks, and sandbox technologies should we build on vs. build ourselves?

## Core Findings

1. **No single framework comprehensively addresses containerized multi-Claude-Code orchestration.** The field has consolidated around five coding-specific frameworks (OpenHands, SWE-agent, MetaGPT, ChatDev, Devin), three general orchestrators (LangGraph, CrewAI, AutoGen/AG2), but none combine Claude Code-native execution + container orchestration + multi-agent coordination in one package. -- R2 Executive Summary, 31 primary sources (CRAAP 22+)
2. **OpenHands is the closest reference architecture.** Event-stream-based platform where each task spawns a Docker sandbox with REST API connectivity. Hierarchical agent delegation, event stream audit trails, optional sandboxing (Docker no longer mandatory as of V1 SDK, April 2026). Apache 2.0 license. -- R2 sec 2.1
3. **CrewAI popularised the "allowed_agents" pattern for scoped delegation.** Manager-worker model with hierarchical or sequential process modes, event-driven async execution, configurable memory types (short-term, entity, contextual). Full Anthropic provider support in v2.4+. Simpler than LangGraph for straightforward workflows. -- R2 sec 2.2
4. **LangGraph models multi-agent workflows as directed graphs.** Parallel execution via `Send()` mechanism creating independent threads. Native checkpointing for long-running tasks (days/weeks). Fan-out/fan-in with configurable `max_concurrency`. Most cited production framework in 2026. -- R2 sec 2.3
5. **Devin 2.0 demonstrates production-grade cloud sandbox isolation.** Each instance runs in an isolated microVM with gRPC/WebSocket communication. Supports parallel multi-instance with fork/rollback. Proprietary only; no self-hosted option; $20/instance/month. Reference value for execution isolation patterns. -- R2 sec 2.4
6. **Claude Code Agent Teams (experimental, April 2026) support 2-8 parallel teammates.** Team lead coordinates; teammates work independently with full Claude Code capabilities. Task-based coordination with implicit dependency management. Production-stable but API still experimental. No custom delegation logic, no result aggregation patterns, no failure escalation. -- R2 sec 2.5, Claude Code docs (CRAAP 25)
7. **Four architecture patterns dominate multi-agent orchestration.** (A) Centralized manager (CrewAI, MetaGPT) -- single point of control, easy monitoring, manager bottleneck risk. (B) Hierarchical delegation (OpenHands, Agency Swarm) -- recursive delegation, distributes load, harder to debug. (C) Graph-based (LangGraph) -- DAG/state machine, explicit branching/loops, requires upfront graph definition. (D) Event-driven mesh (CrewAI async) -- agents subscribe to shared event bus, highly scalable, harder to trace. -- R2 sec 3.1
8. **Sandbox technologies span a clear isolation/overhead trade-off.** Docker containers (process-level, 500ms-2s startup, 50-200MB). gVisor (user-space kernel, 1-4s startup, 10-30% I/O overhead, drop-in Docker replacement). Firecracker microVMs (hardware KVM isolation, 80-200ms startup, 5MB memory, 150 VMs/sec/host). WebAssembly (sub-10ms, limited to WASM-compiled code). -- R2 sec 5.1
9. **Two emerging communication protocols define the 2026 agent ecosystem.** MCP (Model Context Protocol) for agent-to-tool communication -- natively supported by Anthropic, OpenAI, Google, Microsoft; ISO standardization track. A2A (Agent-to-Agent) protocol for peer-to-peer agent communication -- supports negotiation, delegation, capability discovery; still experimental. Recommended pattern: MCP for tools + A2A for delegation. -- R2 sec 3.5
10. **Six critical gaps remain unsolved across all frameworks.** (1) Claude Code-specific multi-instance orchestration with native IDE/terminal access. (2) Containerized execution with full IDE simulation. (3) Stateful multi-session persistence spanning days/weeks. (4) Cost-aware agent orchestration with dynamic model selection. (5) Formal verification of agent guardrails. (6) True horizontal scaling with multi-coordinator networks. -- R2 sec 6

## Frameworks Reviewed

| Framework | Evidence Base | Limitations |
|---|---|---|
| OpenHands (fmr. OpenDevin) | ICLR 2025 paper (CRAAP 23), GitHub repo (CRAAP 24), official docs | Claude via API integration only (not native); LLM-agnostic design |
| CrewAI 2.4+ | Official docs (CRAAP 24), GitHub repo (CRAAP 24) | No native sandboxing; hierarchical delegation requires careful agent scoping |
| LangGraph | Official docs (CRAAP 24), GitHub repo (CRAAP 24), production guides | Requires explicit graph definition; less natural for emergent decomposition |
| Devin 2.0 | Official blog (CRAAP 24), technical deep dive (CRAAP 21) | Proprietary; no self-hosted; no Claude integration; premium pricing |
| Claude Code Agent Teams | Official Anthropic docs (CRAAP 25) | Experimental; max 8 teammates; no custom delegation; no container orchestration |
| MetaGPT | GitHub repo (CRAAP 24), official docs (CRAAP 24) | Assembly-line role sequence; rigid; less flexible for non-waterfall work |
| SWE-agent | Official docs (CRAAP 24), MiniSandbox paper (CRAAP 23) | Research-focused; Ray-distributed; lightweight sandboxing only |
| AutoGen/AG2 | GitHub repo (CRAAP 23) | Maintenance mode since Feb 2026; no longer actively developed |
| E2B | Official docs (CRAAP 24), GitHub (CRAAP 23) | Cloud-only Firecracker; enterprise $3k/month minimum; no self-hosted |
| Daytona | Official site (CRAAP 23), GitHub (CRAAP 23) | Pivoted Feb 2025 to AI workloads; less mature than E2B |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Frameworks with full Claude support | 8 of 14 reviewed | R2 sec 4.2 | Strong Claude ecosystem; framework selection is viable |
| Agent Teams teammate limit | 2-8 | Claude Code docs | Architectural ceiling for native multi-agent without containers |
| Docker startup time | 500ms-2s | R2 sec 5.1 | Acceptable for batch operations; fast enough for CI/CD |
| Firecracker startup | 80-200ms | R2 sec 5.1 | Faster than Docker but higher operational complexity |
| gVisor I/O overhead | 10-30% | R2 sec 5.2 | Acceptable trade-off for semi-trusted code isolation |
| E2B Fortune 100 adoption | 88% trial/deployed | R2 sec 5.3 | Market validation for managed Firecracker sandboxes |

## Design Principles

1. **Compose, don't replace.** Our SDLC plugins (68+ specialist agents) provide domain expertise; orchestration frameworks provide process management. These layers are complementary, not competing.
2. **MCP for tools, A2A for agents.** Use MCP for connecting agents to external tools and data sources. Monitor A2A protocol maturity for direct agent-to-agent communication (expected production Q3 2026).
3. **Sandbox selection follows trust level.** Trusted code: Docker/runc. Semi-trusted: gVisor (drop-in replacement). Untrusted: Firecracker or managed service (E2B/Daytona). Start with Docker; escalate only on evidence.
4. **Graph-based orchestration for complex workflows.** When workflows have explicit branching, loops, conditionals, and long-running persistence needs, LangGraph's DAG model is the most expressive option.
5. **Existing orchestrator first.** If you already have a working supervisor-worker pattern, containerize the workers rather than switching orchestration frameworks.

## Key References

1. OpenHands: An Open Platform for AI Software Developers (ICLR 2025, arxiv:2407.16741) -- CRAAP 23
2. CrewAI official documentation (2026) -- https://docs.crewai.com -- CRAAP 24
3. LangGraph GitHub repository -- https://github.com/langchain-ai/langgraph -- CRAAP 24
4. Devin 2.0 announcement -- https://cognition.ai/blog/devin-2 -- CRAAP 24
5. Claude Code Agent Teams docs -- https://code.claude.com/docs/en/agent-teams -- CRAAP 25
6. MCP 2026 Roadmap -- https://blog.modelcontextprotocol.io/2026-mcp-roadmap -- CRAAP 24
7. Anthropic: How We Built Our Multi-Agent Research System -- https://anthropic.com/engineering/multi-agent-research-system -- CRAAP 24
8. Northflank: How to Sandbox AI Agents (Firecracker, gVisor comparison) -- CRAAP 22
9. Awesome AI Agents 2026 curated list (340+ resources, 20+ categories) -- CRAAP 23

## Programme Relevance

**EPIC #96 (Containerised Claude Code Workers):**
- No existing framework provides the exact combination we need (Claude Code-native + container isolation + multi-agent + our specialist agents), confirming the need for a custom integration layer.
- OpenHands (finding 2) is the closest reference architecture for event-stream-based containerized orchestration.
- Docker is the right starting sandbox technology (finding 8) given that token costs dominate infrastructure costs 100:1 (see containerised-worker-economics.md) and our agents run trusted code.
- The Archon integration model (see archon-workflow-engine.md) aligns with the "compose, don't replace" principle -- Archon orchestrates containers, our plugins provide the team inside them.
- Agent Teams (finding 6) may reduce the container use case for small parallel workloads (2-8 agents) once it exits experimental.

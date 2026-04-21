# Knowledge Base Shelf-Index

Generated manually. Run `/sdlc-knowledge-base:kb-rebuild-indexes` after editing library files to regenerate with real content hashes.

---

## 1. archon-workflow-engine.md

**Hash:** manual-entry-2026-04-10-pending-rebuild
**Terms:** archon, workflow-engine, dag-executor, claude-agent-sdk, worktree-isolation, container-provider, parallel-execution, fan-out-fan-in, fresh-context, ralph-dag, isolation-provider, promise-allSettled, yaml-dag, approval-gates, cost-cap, epic-96, containerisation
**Facts:**
- Archon is an open-source workflow engine (15.5k stars, MIT, TypeScript/Bun) executing AI coding workflows as YAML DAGs via Claude Agent SDK (coleam00/Archon, 2026-04-10)
- Isolation type system declares `worktree | container | vm | remote` but only worktree is implemented — container provider is the extension point for EPIC #96
- DAG executor runs independent nodes concurrently via Promise.allSettled; idea-to-pr workflow fans out 5 parallel review agents with trigger_rule: one_success
- Production Dockerfile uses non-root user appuser (UID 1001) with gosu privilege dropping — matches our smoke test pattern
- Archon and SDLC plugins are different layers (process vs team) — Archon orchestrates, our plugins provide specialist agents inside the containers; Docker image is the integration point, no bridge layer needed
- Three integration options narrowed to one: Archon orchestrates containers, each container is a Claude Code instance with our SDLC plugins pre-installed, node prompts reference our agents by name
**Links:** library/raw/archon-analysis-2026-04-10.md, agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md, retrospectives/85-docker-smoke-test.md

---

## 2. claude-code-native-parallelism.md

**Hash:** manual-entry-2026-04-10-pending-rebuild
**Terms:** claude-code, subagents, worktree-isolation, agent-sdk, headless-mode, agent-teams, permission-modes, mcp, gap-analysis, parallelism, context-window, isolation-gaps, bypassPermissions, bare-mode, github-actions, epic-96
**Facts:**
- Practical subagent ceiling is 5-7 concurrent agents; beyond 10, resource exhaustion and system lockup risk (GitHub #15487)
- Worktree isolation is file-level only — agents share process (Node.js event loop), environment variables, database instances, network interfaces, port space
- All subagents share parent session's 200K token budget; 5+ simultaneous completions can exhaust context window (GitHub #10212)
- Agent SDK (Python/TypeScript) provides full programmatic control: hooks, native subagent spawning, MCP integration, async parallel coroutines
- Agent Teams (experimental) support 2-8 teammates with independent context windows; requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
- Seven isolation gaps containers resolve: process, environment, database, port, file permissions, resource limits, credential isolation
- Three unsolved capabilities: subagent inter-communication, automatic maxParallelAgents, per-subagent context windows
**Links:** agent_prompts/campaign-96-containerized-workers/research/R1-output.md, library/archon-workflow-engine.md, library/containerised-worker-economics.md, library/containerised-worker-recommendations.md

---

## 3. multi-agent-framework-landscape.md

**Hash:** manual-entry-2026-04-10-pending-rebuild
**Terms:** multi-agent, orchestration, openhands, crewai, langgraph, devin, agent-teams, metagpt, swe-agent, sandbox, docker, gvisor, firecracker, mcp, a2a, communication-protocols, event-stream, dag, epic-96
**Facts:**
- No single framework combines Claude Code-native execution + container orchestration + multi-agent coordination (31 primary sources, CRAAP 22+)
- OpenHands is closest reference architecture: event-stream-based platform with Docker sandbox, hierarchical delegation, optional sandboxing (Apache 2.0)
- Four architecture patterns dominate: centralized manager (CrewAI), hierarchical delegation (OpenHands), graph-based (LangGraph), event-driven mesh (CrewAI async)
- Sandbox trade-offs: Docker (process-level, 500ms-2s), gVisor (user-space kernel, 10-30% I/O overhead), Firecracker (hardware KVM, 80-200ms, 5MB)
- Two emerging communication protocols: MCP (tool integration, ISO standardization track) + A2A (agent-to-agent, experimental)
- Six critical gaps unsolved: Claude-specific multi-instance orchestration, containerized IDE simulation, stateful multi-session persistence, cost-aware orchestration, formal verification, horizontal scaling
**Links:** agent_prompts/campaign-96-containerized-workers/research/R2-output.md, library/archon-workflow-engine.md, library/claude-code-native-parallelism.md, library/task-delegation-and-merging.md

---

## 4. containerised-worker-economics.md

**Hash:** manual-entry-2026-04-10-pending-rebuild
**Terms:** rate-limits, token-costs, speedup, fargate, prompt-caching, model-routing, batch-api, break-even, roi, cost-optimisation, itpm, max-5x, max-20x, c-compiler, epic-96
**Facts:**
- Rate limits are the primary parallelism constraint: Max 5x = 2 effective agents (450K ITPM), Max 20x = 3-4 agents; 3rd agent on Max 5x serialises
- Token costs dominate infrastructure costs ~100:1 ($0.50/hr API vs. $0.02/hr Fargate per agent)
- Realistic speedup is 3-5x for 5-16 agents but sublinear; tightly coupled work achieves only 1.2-1.5x
- Anthropic C compiler: 16 parallel Opus agents, 100K-line Rust compiler, 99% test pass rate, ~$20K cost
- Token costs increase 3-4x in parallel execution; with caching + routing, premium shrinks to 1.5-2.0x
- Code quality degrades 2-4% test pass rate without mitigation; recovers to within 1-2% with shared AGENTS.md + style enforcement + architect review
- Cost optimisation strategies recover 50-70% of token budget: caching (30%), routing (30-50%), pruning (10-20%), batch API (50%)
**Links:** agent_prompts/campaign-96-containerized-workers/research/R5-output.md, agent_prompts/campaign-96-containerized-workers/research/S1-output.md, library/claude-code-native-parallelism.md, library/containerised-worker-recommendations.md

---

## 5. task-delegation-and-merging.md

**Hash:** manual-entry-2026-04-10-pending-rebuild
**Terms:** task-decomposition, file-partitioning, context-passing, merge-strategy, worktrees, failure-handling, circuit-breaker, checkpoint, spec-driven, minimal-viable-context, sequential-merge, epic-96
**Facts:**
- Accuracy degrades steeply with task size: 87% single function, 60-75% single file, 19% multi-file, 5-10% module-level
- Five decomposition strategies with success rates: file-level partitioning (90%+), feature-based (75-80%), module-based (70-75%), layer-based (70%), step-based (65-70%)
- Spec-driven decomposition by supervisor prevents ~90% of agent collisions; AI self-decomposition works as on-failure fallback only
- Minimal viable context (spec + tool access, 200-500 tokens/agent) achieves ~81% accuracy; full repo clone (10k-50k tokens) achieves only ~65%
- Sequential git merge achieves 85% success; file-level partitioning achieves 95%; AI-assisted merge achieves 60-75% (unproven at scale)
- Shared files (package.json, routes, config) cannot be safely parallelised — use file locking or central manager
- Circuit breaker pattern: open after 3 consecutive failures, 5-minute cool-off, half-open test with 1 request
**Links:** agent_prompts/campaign-96-containerized-workers/research/R4-output.md, library/claude-code-native-parallelism.md, library/containerised-worker-economics.md, library/containerised-worker-recommendations.md

---

## 6. containerised-worker-recommendations.md

**Hash:** manual-entry-2026-04-10-pending-rebuild
**Terms:** conditional-go, phased-roadmap, docker-compose, kubernetes, ecs-fargate, quick-wins, evaluation-candidates, open-questions, prompt-caching, model-routing, heartbeat, token-logging, spec-driven, epic-96
**Facts:**
- Decision: Conditional GO — containers justified but as augmentation, not primary execution model; native subagents remain default
- Five quick wins before containers: prompt caching (30%), model routing (30-50%), spec-driven decomposition, heartbeat liveness, structured token logging
- Phased roadmap: Phase 0 quick wins (this week) → Phase 1 Docker Compose MVP 2-3 agents (1-2 weeks) → Phase 2 K8s/ECS production (2-4 weeks, conditional) → Phase 3 scale to 5-10 agents (2-3 weeks, conditional)
- Phase 1 go/no-go trigger: 1.5x+ speedup on real tasks; below 1.3x means parallelism not worth it
- Five evaluation candidates: Docker Compose (simplest), K8s Jobs (cloud-ready), ECS Fargate (lowest ops), NATS queue (most scalable), hybrid local+container (most cost-efficient)
- Ten open questions for empirical resolution during Phases 1-2 (rate limit ceiling, merge success rate, caching hit rate, K8s vs ECS, etc.)
- Token optimisation (50-70% savings) buys more parallelism than infrastructure scaling
**Links:** agent_prompts/campaign-96-containerized-workers/research/S3-output.md, library/claude-code-native-parallelism.md, library/multi-agent-framework-landscape.md, library/containerised-worker-economics.md, library/task-delegation-and-merging.md, library/archon-workflow-engine.md

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

---

## 7. sdlc-bundle-research-overview.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** sdlc-bundles, programme-bundle, assured-bundle, method-1, method-2, research-campaign, design-decisions, scope-update, epic-97, sub-feature-103, sub-feature-104, ddd-bazel, bidirectional-traceability, change-impact, granularity, tool-neutral, sphinx-needs, doors
**Facts:**
- Research campaign produced 61,061 words across 14 artefacts with 651 inline citations across 78 bibliography entries; CRAAP credibility notes preserved; counter-arguments cited
- Three independent research lines (regulatory traceability, decomposition patterns, ALM tools) converged with 0 material conflicts and 8 cross-line agreements at HIGH or VERY HIGH confidence
- Decomposition primitive final call: DDD bounded contexts + Bazel visibility-rule discipline; optional hexagonal architecture for within-module structure; explicit failure mode designed against = anaemic contexts
- Traceability rigour final call: bidirectional link integrity + per-module granularity declaration + structured change-impact annotation + static build-time validation; satisfies ISO 26262 baseline simultaneously with DO-178C, IEC 62304, IEC 61508, FDA 21 CFR Part 820
- sphinx-needs adoption: borrow declarative schema, static link validation, file-based storage, annotation-driven code parsing; reject flat IDs, no decomposition primitive, dynamic computed fields, multiprocessing-for-large-projects, rich-text fields
- 14 scope changes total (4 Method 1, 10 Method 2); 0 open questions block plan-writing; recommended next action is (a) update METHODS.md and proceed to writing-plans
**Links:** research/sdlc-bundles/CLOSEOUT.md, research/sdlc-bundles/synthesis/overall-scope-update.md, research/sdlc-bundles/METHODS.md, library/regulatory-traceability-baseline.md, library/decomposition-ddd-bazel.md, library/decomposition-failure-modes.md, library/sphinx-needs-adoption-boundary.md, library/doors-cautionary-tale.md, library/change-impact-pattern.md, library/granularity-declaration.md, library/tool-neutral-traceability.md

---

## 8. regulatory-traceability-baseline.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** bidirectional-traceability, do-178c, iec-62304, iso-26262, iec-61508, fda-21-cfr-820, regulated-industry, assurance-grade, granularity, change-impact, tool-neutrality, regenerability, method-2, assured-bundle, epic-97
**Facts:**
- Three of five regulated standards (DO-178C, ISO 26262, IEC 61508) mandate bidirectional traceability; IEC 62304 permits unidirectional but practitioners implement bidirectional anyway; FDA emphasises forward + DHF backward confirmation
- Implementing bidirectionality in Assured defaults exceeds no standard's requirement and satisfies ISO 26262's strictness — defensible as "assurance-grade"
- Granularity scales by standard (DO-178C Level A object-code; Level D file-level; ISO 26262 requirement-level all ASIL; IEC 62304 by Class) — must be declared per-module, never inferred
- Change-impact assessment universally required but variably gated: IEC 62304 §8.2.4 and FDA §820.30(i) are blocking gates; DO-178C/ISO 26262/IEC 61508 less explicit
- All five standards are tool-neutral (objectives not means); ISO 26262-8 and IEC 61508 explicitly require regenerability from primary artefacts
- Framework promises substrate (traceability records, decomposition, change-impact records, phase gates, code annotations) — NOT certification (requires accredited authority)
**Links:** research/sdlc-bundles/synthesis/01-traceability-synthesis.md, research/sdlc-bundles/synthesis/overall-scope-update.md, library/change-impact-pattern.md, library/granularity-declaration.md, library/tool-neutral-traceability.md

---

## 9. decomposition-ddd-bazel.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** ddd, bounded-contexts, bazel, visibility-rules, hexagonal-architecture, decomposition-primitive, anaemic-context, programme-bundle, assured-bundle, method-2, epic-97
**Facts:**
- DDD bounded contexts are the highest-translatability decomposition pattern for markdown-driven, filesystem-first frameworks (no build system or runtime required)
- Bazel's visibility-rule philosophy complements DDD without requiring Bazel itself — declared visibility in context maps; validators check filesystem imports; circular cross-program deps blocked
- Hexagonal (ports-and-adapters) is optional within-module structure; code organised core/adapter; lightweight; opt-in via annotation
- Triangulated recommendation: Line 2 explicitly recommends DDD + Bazel; Line 1 demands granularity declaration; Line 3 documents sphinx-needs scaling limits absent decomposition — DDD modules avoid the limit
- Failure mode designed against: anaemic contexts (logic scattered across modules) — detected by code-to-module assignment validator and orphan-code validator; surfaced via traceability-render
- Patterns NOT borrowed: Erlang/OTP supervision (needs runtime isolation), MBSE/SysML (needs specialised tools), ARINC 653 (needs RTOS), AUTOSAR (needs code generators), Bazel full BUILD-graph (overkill)
- Premature decomposition is the second failure mode; mitigated procedurally (commission with default P1.SP1.M1.*) plus technically (refactor without ID loss)
**Links:** research/sdlc-bundles/synthesis/02-decomposition-synthesis.md, research/sdlc-bundles/synthesis/overall-scope-update.md, library/decomposition-failure-modes.md, library/sdlc-bundle-research-overview.md

---

## 10. decomposition-failure-modes.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** anaemic-context, premature-decomposition, distributed-monolith, traceability-breakdown, tool-lock-in, validators, decomposition, method-2, assured-bundle, epic-97
**Facts:**
- Anaemic contexts are the headline failure mode for DDD-based decomposition — business logic scattered across modules rather than concentrated in domain models, rendering boundaries meaningless
- Premature decomposition pays high coordination cost without benefit; canonical case is Segment's reversal from 200+ microservices to modular monolith
- Cross-module dependency proliferation makes visibility rules meaningless; mitigated by declared visibility in context maps validated at filesystem-import level
- Traceability breakdown at scale: developers skip annotations, format drifts, orphan code appears — mitigated by cheap annotation (auto-generation skill) plus block-on-missing validators
- Distributed monolith is rejected by design: Method 2 modules don't deploy independently; if independent deployment is needed it's a deployment refactor not SDLC-level
- Tool lock-in (MBSE/SysML adoption hindered by tool licensing/training) is rejected by design: framework is markdown-only with text-editor + Git as editing interface
- Decomposition refactoring without ID loss is the technical mitigation for premature decomposition — kb-rebuild-indexes remaps old IDs to new paths
**Links:** research/sdlc-bundles/synthesis/02-decomposition-synthesis.md, library/decomposition-ddd-bazel.md

---

## 11. sphinx-needs-adoption-boundary.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** sphinx-needs, declarative-schema, static-validation, file-based-storage, annotation-driven, markdown-first, alm-tools, method-2, assured-bundle, epic-97
**Facts:**
- sphinx-needs is field-proven in regulated contexts (DO-178B aerospace, ISO 26262 automotive) — proves open-source file-based requirements tools can meet assurance-level rigour
- Patterns to ADOPT: declarative need-type schema; static build-time link validation; file-based Git-native storage; annotation-driven code parsing; modular per-module rendering
- Patterns to REJECT: flat identifier scheme (REQ_001) — replace with namespaced P1.SP2.M3.REQ-007; no decomposition primitive (scaling fails at 500+ pages); dynamic computed-field functions (steep learning curve); multiprocessing for large projects (build >30 min, memory >32 GB at 25K pages); rich-text field support (round-trip lossy via ReqIF)
- Honest reading: Method 2 ≈ "sphinx-needs + namespaced IDs + explicit decomposition primitive + agent-orchestrated retrieval/synthesis"; the agent-orchestrated layer is our differentiator
**Links:** research/sdlc-bundles/synthesis/03-alm-synthesis.md, research/sdlc-bundles/synthesis/overall-scope-update.md, library/doors-cautionary-tale.md

---

## 12. doors-cautionary-tale.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** doors, ibm-doors, doors-next, dxl, vendor-lock-in, alm-tools, requirements-rot, compliance-theatre, anti-pattern, method-2, assured-bundle, epic-97
**Facts:**
- DOORS Classic uses module-and-attribute relational schema with .rmd binary format — proprietary, inaccessible without DOORS, creates vendor lock-in
- DXL (DOORS eXtension Language) customisation creates million-line lock-in; large deployments accumulated 1M+ LOC of DXL; migration cost is prohibitive
- DOORS Next migration was a disaster: DXL unmigratable to Jazz/Java, views incompatible, baselines lost
- Lock-in operates at four levels: binary format, scripting investment, proprietary licensing, organisational inertia from training/process embedment
- Rich-text fields don't round-trip via ReqIF — when migrating away, data is lost
- ReqIF round-trip workflows suffer documented data loss (attributes dropped, parent-child unreconstructible, complex links degraded) — use one-way export only
- Compliance theatre is the meta-failure: tools deployed for audit visibility, not engineering effectiveness; matrices exist but tests are thin or never executed
- Method 2 design choices explicitly avoid each: markdown + YAML in Git, no proprietary scripting, no database in critical path, no bidirectional ReqIF sync, validate syntax not semantics
**Links:** research/sdlc-bundles/synthesis/03-alm-synthesis.md, library/sphinx-needs-adoption-boundary.md, library/tool-neutral-traceability.md

---

## 13. change-impact-pattern.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** change-impact, change-impact-annotate, change-impact-gate, iec-62304, fda-21-cfr-820, iso-26262, structured-annotation, method-2, assured-bundle, epic-97
**Facts:**
- All five regulated standards require change-impact assessment but with variable formalisation
- IEC 62304 §8.2.4 and FDA §820.30(i) treat it as mandatory blocking gate; DO-178C, ISO 26262, IEC 61508 require it but less explicitly as blocker
- Practitioner research shows change-impact is post-hoc in practice — compliance-theatre pattern when not gated
- Pragmatic middle ground: structured annotation (e.g., "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B") — upfront, auditable, human-decided, no AST analysis required
- Optional change-impact-gate validator blocks commits where code changes lack change-impact annotation; default disabled; enabled at commissioning for IEC 62304/FDA/ISO 26262 ASIL C/D
- Automatic semantic change-impact detection rejected — would require call graphs/data-flow analysis/AI reasoning, conflicts with markdown-first design
- change-impact-annotate skill makes the obligation cheap to satisfy; reduces friction so teams do it upfront not at audit time
**Links:** research/sdlc-bundles/synthesis/01-traceability-synthesis.md, library/regulatory-traceability-baseline.md

---

## 14. granularity-declaration.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** granularity, do-178c, iec-62304, iso-26262, asil, sil, level, per-module-declaration, method-2, assured-bundle, epic-97
**Facts:**
- Granularity scales by standard and risk class: DO-178C Level A object-code; Level D file-level; IEC 62304 Class C function-level; ISO 26262 requirement-level all ASIL; IEC 61508 SIL-scaled
- Framework cannot infer granularity; each module declares its target — granularity: [requirement | function | module]
- Default granularity is requirement (finest accepted by all standards); modules may declare looser explicitly when justified
- Validators warn on actual-vs-declared mismatch (underspecified links); never block (might be progressive tightening)
- Mixed-granularity projects supported by design: M1 at requirement-level, M2 at function-level — validators are per-module
- Object-code granularity (DO-178C Level A) is opt-in only; making it default would break every non-aerospace project
- Commissioning script proposes granularity per module based on declared regulatory context
**Links:** research/sdlc-bundles/synthesis/01-traceability-synthesis.md, library/regulatory-traceability-baseline.md, library/decomposition-ddd-bazel.md

---

## 15. tool-neutral-traceability.md

**Hash:** manual-entry-2026-04-26-pending-rebuild
**Terms:** tool-neutrality, regenerability, kb-rebuild-indexes, file-based-storage, git-native, audit-evidence, iso-26262, iec-61508, method-2, assured-bundle, epic-97
**Facts:**
- All five major regulated standards are tool-neutral — they specify objectives (what evidence) not means (which tool)
- ISO 26262 Part 8 Clause 11 and IEC 61508 explicitly require regenerability — links must be reconstructible from primary artefacts without tool dependence
- File-based markdown + Git satisfies regenerability natively; sphinx-needs/Doorstop/strictdoc all proven file-based in regulated contexts
- Database-only tools (DOORS) violate regenerability — proprietary .rmd format inaccessible without DOORS; vendor migration causes data loss
- kb-rebuild-indexes is the regenerability mechanism — auditors verify integrity by running it and comparing to committed indices
- v1 acceptance criterion: kb-rebuild-indexes is idempotent (byte-identical output on repeat runs)
- Index staleness threshold (default 7 days with subsequent code commits) is convenience flag — framework guarantees regenerability not freshness
- Tool qualification (TCL/TI per ISO 26262-8) is project-level concern not framework concern
**Links:** research/sdlc-bundles/synthesis/01-traceability-synthesis.md, research/sdlc-bundles/synthesis/overall-scope-update.md, library/sphinx-needs-adoption-boundary.md, library/doors-cautionary-tale.md

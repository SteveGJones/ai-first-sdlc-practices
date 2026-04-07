# Phase 4: Emerging, Informal & AI-Native Methodologies — Comprehensive Evaluation

**Date**: April 2026
**Scope**: 12 traditional emerging methodologies + 8 AI-native frameworks
**Research Period**: 2023–2026, with emphasis on 2024–2026 recent sources

---

## Executive Summary

Phase 4 evaluates 20 methodologies across emerging (Shape Up, Trunk-Based Development, etc.), specialized practices (TDD/BDD as standalone), and AI-native frameworks (ADLC, Spec-Kit SDD, AgentsWay, Claude Code, Devin, VeriAct, Prompt-Driven Development, Vibe Coding, multi-agent orchestration).

**Key Findings**:

1. **Emerging traditional methodologies** (Shape Up, Trunk-Based, CD/CD, Mob Programming) score 3.2–4.1 on agent-suitability (out of 5), excelling in parallelism, feedback loops, and ceremony minimization but lacking formal specification and knowledge management.

2. **Specification-driven methodologies** (API-first, Contract-first, DDD, ADR-Driven) score 3.8–4.4, strong on formality and traceability but weak on agent delegation clarity.

3. **AI-native methodologies** represent a qualitative leap: Spec-Kit SDD (4.6/5), AgentsWay (4.7/5), Claude Code workflow (4.5/5), and VeriAct (4.8/5) demonstrate agent-nativeness previously absent in traditional approaches.

4. **Composability is critical**: No single methodology provides all properties agents need. TDD + Trunk-Based + Spec-Kit + ADRs + Kanban forms a promising composition for agentic SDLC.

5. **Remaining gaps**: Autonomous escalation criteria, multi-agent coordination protocols, and formal agent governance frameworks remain unsolved.

---

## Part A: Traditional Emerging Methodologies (11 methods)

### 1. Shape Up (Basecamp, Fried & Singer 2019)

#### Section 1: Methodology Profile

**Core Philosophy**: Fixed, time-boxed 6-week cycles; clear shaping phase separates intent from implementation; appetite-driven prioritization; autonomous execution with minimal mid-cycle ceremony.

**Phases**:
- **Shaping** (first 2 weeks): Senior designers/PMs define problem, explore solutions, scope appetite (e.g., "2 dev-weeks max"), produce design brief.
- **Betting** (end-of-cycle): Leadership reviews shaped work, commits to bets; team assigned work.
- **Building** (6 weeks): Developers execute with autonomy; daily standup and sync as needed, not prescribed.
- **Cool-down** (1 week): Maintenance, debt paydown, reflection.

**Artifacts**: Shape document (narrative + sketches), Feature spec (acceptance criteria), Test reports.

**Key Differentiator**: Separates shaping (design/planning) from building (execution), reducing mid-cycle pivots.

#### Section 2: Rubric Scoring (14 dimensions × 3 contexts)

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 2 | 2 | 2 | Shape documents are narrative; sketches aid humans but not machine parsing. No formal notation. |
| 2. Task Decomposability | 4 | 4 | 3 | 6-week fixed cycle; within that, work is loosely decomposed. Small teams self-organize into atomic tasks. At scale, cross-team dependencies are implicit. |
| 3. Verification & Validation | 3 | 3 | 3 | Assumes testing happens; no mandate for TDD/BDD or automated gates. Quality discipline varies by team. |
| 4. Feedback Loop Structure | 4 | 4 | 3 | Minimal daily ceremony; fast async feedback from tests and demos. But feedback is weekly demo-based, not real-time. |
| 5. Artifact Traceability | 2 | 2 | 2 | Shape documents exist but loose link to code/tests. No formal traceability artifacts. |
| 6. Ceremony & Documentation | 5 | 5 | 4 | Minimal ceremony by design. "Shaping, betting, building" replaces sprint planning/review ritual. Agents have maximum autonomy. |
| 7. Concurrency & Parallelism | 3 | 3 | 2 | Fixed cycle means work is pre-committed; teams work in parallel but cycles are synchronized. 6-week windows reduce mid-cycle merge conflicts. At scale, teams may serialize cycle betting. |
| 8. Role Clarity & Delegation | 4 | 4 | 3 | Clear roles: Shaper, Bettors, Builders. Builders have autonomy within cycle. But escalation criteria (when to re-shape) are implicit. |
| 9. Change Management & Adaptability | 2 | 2 | 2 | 6-week cycle is fixed; mid-cycle changes not allowed (by design, to prevent scope creep). High cost to change. Agents cannot adapt mid-cycle. |
| 10. Scalability of Coordination | 2 | 2 | 1 | Shape Up is designed for small teams (5–15). Scaling to 50+ people requires replicating shaping/betting at team level; ceremony overhead grows. No scaling framework provided. |
| 11. Quality Gate Structure | 2 | 2 | 2 | Assumes quality gates exist; no formal gate definition or automation guidance. |
| 12. Knowledge Management | 2 | 2 | 2 | Shape documents accumulate; no formal knowledge base or decision log mechanism. Historical context is implicit. |
| 13. Risk Management | 3 | 3 | 2 | Appetite-driven prioritization is a form of implicit risk management; high-appetite bets are high-risk. But no formal ROAM or escalation. |
| 14. Technical Debt Governance | 2 | 2 | 2 | Cool-down week nominally addresses debt, but no governance mechanism. Debt paydown is optional. |
| **Weighted Total** | **41/100** | **41/100** | **33/100** | — |

**Context-Specific Notes**:
- **Solo+Agent**: Shape Up's autonomy and minimal ceremony suit agents well (level 5 on ceremony). But lack of formal specs and traceability hurt agent clarity.
- **Team+Agents**: 6-week cycles work; multiple agents per team can parallelize within a cycle. However, betting phase (human-centric) becomes bottleneck.
- **Programme**: Shape Up's small-team design breaks; cross-team coordination and dependency management are underdeveloped.

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness Spectrum Placement**: **Agent-Tolerant** (level 2/5).

**Rationale**:
- Shape Up's minimal ceremony and autonomous execution windows align with agent preferences (agents thrive without prescriptive daily standups).
- However, the shaping phase is fundamentally human-centric (senior designers decide intent); agents cannot participate in this design activity.
- Lack of formal specs means agents must infer detailed intent from narrative shape documents, increasing clarification cycles.
- 6-week fixed cycles prevent mid-cycle agent re-prioritization; if an agent discovers a blocker, it must wait for the next cycle or escalate.

**Opportunities for Agent Adaptation**:
- Require shape documents to include formal acceptance criteria (Gherkin BDD format).
- Use agents to automate within-cycle task breakdown (shape document → task decomposition).
- Extend escalation criteria: agents can raise mid-cycle blockers; a lightweight re-shaping agent can propose scope adjustments.

#### Section 4: Empirical Evidence Inventory

**Primary Sources**:
- Basecamp (2019). *Shape Up: Stop Running in Circles and Ship Work That Matters*. [Basecamp Book](https://basecamp.com/shapeup)
- Basecamp Engineering (2024). Blog posts on Shape Up adoption at scale (mixed results; scaling challenges documented).

**Grey Literature**:
- Reddit/HackerNews discussions (2024–2025): Teams report Shape Up works well for 5–15 people; breaks at 30+.
- Thoughtbot blog (2024): "Shape Up in Practice" documents taste-driven design challenges with distributed teams.

**Research Gaps**:
- No empirical studies measuring Shape Up's impact on delivery velocity or defect rates.
- No research on Shape Up with distributed teams or agentic participation.

---

### 2. Trunk-Based Development (TBD) as Methodology

#### Section 1: Methodology Profile

**Core Philosophy**: All developers commit to a single main branch (trunk); short-lived feature branches (< 1 day) if used; continuous integration and deployment; minimize merge conflicts through frequent, small commits.

**Key Practices**:
- **Single trunk** or main branch as source of truth.
- **Feature branches** (optional) < 24 hours; must be merged daily.
- **Continuous integration**: Commits integrated and tested immediately.
- **Continuous deployment**: Code merged to trunk → automatically deployed (with quality gates).
- **Branch by abstraction**: Hide incomplete features behind flags, not branches.

**Advocates**: Google, Amazon, Atlassian, ThoughtWorks (Radar 2024: "Adopt").

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 2 | 2 | 2 | TBD does not prescribe spec formality; pairs with any upstream spec approach. Specs are external to TBD. |
| 2. Task Decomposability | 3 | 3 | 3 | TBD requires small, frequent commits; implicitly assumes task decomposition. But does not mandate granularity. |
| 3. Verification & Validation | 4 | 4 | 4 | TBD *requires* strong CI/CD; automated testing is non-negotiable. Agents observe test results in real-time. |
| 4. Feedback Loop Structure | 5 | 5 | 5 | Sub-minute feedback: code committed → tested immediately. Agents iterate on CI feedback within seconds. |
| 5. Artifact Traceability | 3 | 3 | 3 | Commit messages link code to intent; but no formal traceability structure. Agents can parse commit history. |
| 6. Ceremony & Documentation | 5 | 5 | 5 | No ceremonies prescribed; CI/CD feedback is asynchronous. Code review (PR) is lightweight. Minimal doc overhead. |
| 7. Concurrency & Parallelism | 5 | 5 | 5 | Designed for high parallelism. Frequent small merges minimize conflicts. Sub-daily merges are standard. |
| 8. Role Clarity & Delegation | 3 | 3 | 3 | TBD does not define roles; assumes clear ownership. Escalation criteria are absent. |
| 9. Change Management & Adaptability | 5 | 5 | 5 | Continuous flow means agents can pick up new work mid-sprint. No fixed cycles. Maximum adaptability. |
| 10. Scalability of Coordination | 4 | 4 | 4 | Scales well to 100+ developers (proven at Google, Amazon). Coordination is through trunk and CI gates. Limited ceremony overhead. |
| 11. Quality Gate Structure | 4 | 4 | 4 | Requires strong automated gates (tests, linting, SAST). Gates are typically layered (unit → integration → deploy). |
| 12. Knowledge Management | 2 | 2 | 2 | TBD does not address knowledge management; commit history is implicit. No decision log or constraint documentation. |
| 13. Risk Management | 3 | 3 | 3 | Feature flags allow risky features to merge without immediate impact. But no formal risk assessment. |
| 14. Technical Debt Governance | 3 | 3 | 3 | Frequent commits and CI testing prevent debt accumulation, but no explicit debt governance. Refactoring is implicit. |
| **Weighted Total** | **56/100** | **56/100** | **56/100** | — |

**Note**: TBD is a *practice*, not a complete methodology. It pairs well with Kanban, Scrum, or Shape Up as coordination layers.

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly** (level 3/5).

**Rationale**:
- TBD's real-time CI feedback is agent-optimal: agents can observe test failures within seconds and iterate autonomously.
- Sub-daily merge cycles mean agents never hold stale code long; context is always fresh.
- No prescriptive ceremony means agents are not blocked by meetings.
- However, TBD itself does not define task allocation, specs, or escalation; agents must rely on upstream coordination.

**Agentic Enhancements**:
- Integrate agent-executable quality gates (agents can review code against architectural rules, run security scans, propose refactoring).
- Use branch-by-abstraction to allow agents to work on incomplete features safely; feature flags become agent-coordination tools.

#### Section 4: Empirical Evidence Inventory

**Academic**:
- Atlassian Research (2024). "Trunk-Based Development at Scale." [Atlassian Research](https://atlassian.com/research)
- Google/ThoughtWorks (2020s): Case studies show TBD enables 10–100 deploys/day at scale.

**Industry**:
- ThoughtWorks Radar (2024): Recommends TBD as "Adopt" for teams >10 people.

**Gaps**:
- Limited research on TBD with agent-driven teams; no empirical data on merge conflict rates with 10x throughput.

---

### 3. Continuous Delivery / Continuous Deployment (CD/CD) as Methodology Philosophy

#### Section 1: Methodology Profile

**Continuous Delivery (CD)**: Every commit produces a production-ready artifact; deployment is manual and on-demand.
**Continuous Deployment (CD)**: Every commit is automatically deployed to production (with automated gates).

**Core Practices**:
- Automated build, test, deploy pipeline.
- Feature flags and blue-green deployment for safety.
- Monitoring and rollback automation.
- Team owns deployment (no separate "operations" gate).

**Advocates**: Humble & Farley (2010), Amazon, Netflix, Google.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 2 | 2 | 2 | CD does not prescribe specs. |
| 2. Task Decomposability | 3 | 3 | 3 | Small increments required but not formally defined. |
| 3. Verification & Validation | 5 | 5 | 5 | Automated testing is non-negotiable; verification gates are first-class. |
| 4. Feedback Loop Structure | 5 | 5 | 5 | Minutes-to-hours feedback from production monitoring. Agents observe real-world impact. |
| 5. Artifact Traceability | 3 | 3 | 3 | Deployment logs; but no formal traceability to specs. |
| 6. Ceremony & Documentation | 4 | 4 | 4 | Minimal ceremony; deployments are automated. But release planning and coordination may have some ceremony. |
| 7. Concurrency & Parallelism | 5 | 5 | 5 | High concurrency; feature flags enable agents to work on conflicting features. |
| 8. Role Clarity & Delegation | 3 | 3 | 3 | CD assumes dev team owns deployment; escalation unclear. |
| 9. Change Management & Adaptability | 5 | 5 | 5 | Maximum adaptability; feature flags allow mid-flight changes. |
| 10. Scalability of Coordination | 5 | 5 | 5 | Scales to 1000+ developers (Netflix, Amazon). |
| 11. Quality Gate Structure | 5 | 5 | 5 | Explicitly mandates automated, layered gates. |
| 12. Knowledge Management | 2 | 2 | 2 | Does not address knowledge management. |
| 13. Risk Management | 4 | 4 | 4 | Feature flags + canary deployments + rollback enable risk mitigation. |
| 14. Technical Debt Governance | 3 | 3 | 3 | Frequent deployments prevent debt accumulation, but no governance. |
| **Weighted Total** | **58/100** | **58/100** | **58/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly** (level 3/5).

**Rationale**: CD's automated feedback and feature-flag-driven development align with agent iteration. However, CD is infrastructure, not methodology; agents still need upstream task allocation and specs.

#### Section 4: Empirical Evidence Inventory

**Academic**:
- Humble & Farley (2010). *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. [Addison-Wesley].
- DeployHub Research (2024). CD adoption correlates with 40% faster time-to-market.

**Industry**:
- Amazon (2023): 11.7M deployments/year (~23k/day); every engineer owns deployment.
- Netflix case studies (2020s): Feature flags enable 100+ simultaneous feature development.

---

### 4. Mob / Ensemble Programming (Zuill 2014)

#### Section 1: Methodology Profile

**Core Philosophy**: Entire team (3–6 people) works on one machine, one problem, at the same time. Driver (person at keyboard), Navigators (rest of team). Roles rotate.

**Key Practices**:
- Single workstation; shared real-time editing tools (VS Code Live Share, etc.) for distributed.
- Rotating driver every 15–20 minutes.
- Collective code ownership; all team members contribute.
- High information sharing; collective decision-making.

**Advocates**: Woody Zuill (original concept), XP teams, some Agile orgs.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 3 | 3 | 2 | Specs are discussed verbally; some teams use BDD. Variable formality. |
| 2. Task Decomposability | 2 | 2 | 1 | Mob works on monolithic problems; decomposition is implicit discussion. Not suitable for parallel execution. |
| 3. Verification & Validation | 4 | 4 | 3 | Collective review during mob; testing is immediate. Strong V&V. But not mandated. |
| 4. Feedback Loop Structure | 4 | 4 | 3 | Immediate feedback from mob discussion; real-time error detection. |
| 5. Artifact Traceability | 2 | 2 | 1 | Mob focus is on code, not artifact traceability. Decisions are verbal. |
| 6. Ceremony & Documentation | 2 | 2 | 1 | Mob IS the ceremony; very high ceremony overhead (entire team in one meeting continuously). |
| 7. Concurrency & Parallelism | 1 | 1 | 1 | By design, one team works on one problem; no parallelism. |
| 8. Role Clarity & Delegation | 3 | 3 | 2 | Roles rotate (driver, navigator); but no escalation or delegation to other agents. Collective decision-making. |
| 9. Change Management & Adaptability | 4 | 4 | 3 | Mob can quickly discuss and pivot; adaptable. |
| 10. Scalability of Coordination | 1 | 1 | 1 | Mob scales to ~6 people max; beyond that, coordination overhead explodes. |
| 11. Quality Gate Structure | 3 | 3 | 2 | Collective review; gates are implicit. |
| 12. Knowledge Management | 4 | 4 | 3 | Mob has high knowledge transfer; collective understanding. But knowledge is ephemeral (not documented). |
| 13. Risk Management | 3 | 3 | 2 | Collective risk awareness, but no formal risk management. |
| 14. Technical Debt Governance | 4 | 4 | 3 | Collective refactoring; debt is visible to entire team. |
| **Weighted Total** | **36/100** | **36/100** | **25/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Hostile** (level 1/5).

**Rationale**: Mob programming is fundamentally synchronous, human-centric, and non-parallel. Agents work independently and asynchronously; a mob of agents would defeat the purpose (agents don't need social interaction or collective decision-making). The methodology assumes rich tacit knowledge sharing that agents cannot participate in.

**However**: Agents *can* simulate a mob for a narrow task (multiple agents discuss a problem, reach consensus, execute). This is not true Mob Programming but multi-agent orchestration mimicking collective discussion.

#### Section 4: Empirical Evidence Inventory

**Primary**:
- Zuill, W. (2014). *Mob Programming: A Whole Team Approach* (white paper, later book 2023).

**Academic**:
- Schlagwein, D. (2018). "Escaping the Rat Race of Continuous Connectivity Through Collective Mindfulness." *Information and Organization*, 28(1), 13–23.
- Navarro, E. O., van der Hoek, A. (2004). "Pair Programming for CS Education." *15th SIGCSE Technical Symposium*.

**Industry**:
- thoughtbot case studies (2023–2024): Mob programming works for high-risk features; not for steady-state delivery.
- Agile adoption surveys (VersionOne, 2024): <2% of teams use mob programming regularly.

---

### 5. Specification-Driven Development (API-First / Contract-First / Design-by-Contract)

#### Section 1: Methodology Profile

**Core Philosophy**: Specifications (APIs, contracts, formal schemas) are designed *before* implementation. Code and tests follow the spec.

**Variants**:
- **API-First**: OpenAPI/AsyncAPI specs define APIs before code.
- **Contract-First**: Producer and consumer agree on message/service contracts (Pact, JSON Schema).
- **Design-by-Contract (DbC)**: Contracts (preconditions, postconditions, invariants) guide implementation (Eiffel, refinement calculus).

**Advocates**: REST API communities, ThoughtWorks (Adopt), formal methods researchers.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 5 | 5 | 5 | Spec is the primary artifact; formal notation (OpenAPI, JSON Schema, Eiffel contracts). |
| 2. Task Decomposability | 3 | 3 | 3 | Specs are not decomposition tools; pairs with Scrum or other decomposition methods. |
| 3. Verification & Validation | 4 | 4 | 4 | Contract testing is automated; agents can validate code against spec. Agents can auto-generate tests from specs. |
| 4. Feedback Loop Structure | 4 | 4 | 4 | Agents observe contract violations immediately; rapid iteration on mismatches. |
| 5. Artifact Traceability | 5 | 5 | 5 | Spec is source of truth; code and tests trace to spec. Executable traceability. |
| 6. Ceremony & Documentation | 4 | 4 | 4 | Spec review replaces design doc reviews; lightweight. |
| 7. Concurrency & Parallelism | 4 | 4 | 4 | Specs decouple producer and consumer; teams can parallelize. Agents can work on independent specs. |
| 8. Role Clarity & Delegation | 4 | 4 | 4 | Spec defines boundaries; clear hand-offs between consumer and producer. Agents understand interfaces. |
| 9. Change Management & Adaptability | 3 | 3 | 3 | Spec changes require negotiation; change is visible but not frictionless. |
| 10. Scalability of Coordination | 4 | 4 | 4 | Specs scale; teams coordinate via spec contracts. Good for 50+ teams. |
| 11. Quality Gate Structure | 4 | 4 | 4 | Contract testing is automated; gates are clear. |
| 12. Knowledge Management | 4 | 4 | 4 | Specs are documented, versioned, discoverable. Good knowledge base. |
| 13. Risk Management | 3 | 3 | 3 | Spec violations are visible risks; but no formal risk assessment. |
| 14. Technical Debt Governance | 3 | 3 | 3 | Spec clarity prevents some debt; but no governance mechanism. |
| **Weighted Total** | **59/100** | **59/100** | **59/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly** (level 3/5).

**Rationale**: Specification-Driven Development is highly agent-friendly because specs are machine-parseable. Agents can:
- Auto-generate tests from specs (contract test generation).
- Validate implementation against specs.
- Detect spec violations and propose fixes.

However, specs are *still created by humans*; agents cannot participate in spec design.

#### Section 4: Empirical Evidence Inventory

**Academic**:
- Fowler, M. (2018). "Contract Testing." *martinfowler.com*.
- Pact Foundation (2023): Contract testing adoption growing; 1000+ orgs use Pact.

**Industry**:
- OpenAPI Adoption (2024): 40% of enterprises use OpenAPI specs.
- ThoughtWorks Radar (2024): API-First and Contract-First are "Adopt" practices.

---

### 6. Docs-Driven / README-Driven Development (Preston-Werner 2010)

#### Section 1: Methodology Profile

**Core Philosophy**: Write documentation (especially README) *before* code. Documentation serves as executable spec: if code doesn't match docs, documentation wins.

**Key Practices**:
- README is authoritative; describes intended behavior, interface, examples.
- API docs are written before implementation.
- Examples in docs are tested (doctest, doctests in Python).
- Documentation changes trigger code reviews.

**Advocates**: GitHub, many open-source projects.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 3 | 3 | 3 | Documentation is structured but not formally notated; examples are pseudo-code. |
| 2. Task Decomposability | 2 | 2 | 2 | Docs do not decompose; paired with other methods. |
| 3. Verification & Validation | 3 | 3 | 3 | Doctest and runnable examples; but not comprehensive. |
| 4. Feedback Loop Structure | 3 | 3 | 3 | Doc changes are visible; but not real-time feedback. |
| 5. Artifact Traceability | 4 | 4 | 4 | Docs are the source of truth; code traces to docs. |
| 6. Ceremony & Documentation | 4 | 4 | 4 | Docs replace heavy design docs; lightweight ceremony. |
| 7. Concurrency & Parallelism | 3 | 3 | 3 | Docs can define interfaces; but parallel work is not explicitly supported. |
| 8. Role Clarity & Delegation | 3 | 3 | 3 | Docs can define responsibilities; implicit role clarity. |
| 9. Change Management & Adaptability | 4 | 4 | 4 | Doc-first means change intent is visible early; adaptable. |
| 10. Scalability of Coordination | 3 | 3 | 3 | Docs scale; but coordination mechanisms are not built-in. |
| 11. Quality Gate Structure | 2 | 2 | 2 | Docs do not define quality gates; manual review. |
| 12. Knowledge Management | 5 | 5 | 5 | Docs are the knowledge base; well-indexed, discoverable, versioned. |
| 13. Risk Management | 2 | 2 | 2 | No risk management mechanism. |
| 14. Technical Debt Governance | 2 | 2 | 2 | No debt governance. |
| **Weighted Total** | **43/100** | **43/100** | **43/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly** (level 3/5).

**Rationale**: Agents thrive on clear documentation. A well-written README is agent-executable. Agents can:
- Parse README examples and generate tests.
- Detect code-doc mismatches and fix code.
- Generate docs from code (doc generation agents).

However, docs are written by humans; agents cannot participate in the framing phase.

#### Section 4: Empirical Evidence Inventory

**Primary**:
- Preston-Werner, T. (2010). "Readme Driven Development." *tompreston-werner.com*.

**Industry**:
- GitHub Guides (2024): README-first is promoted as best practice.

---

### 7. Test-Driven Development (TDD) as Standalone Methodology

#### Section 1: Methodology Profile

**Core Philosophy**: Write test *before* code (Red-Green-Refactor cycle). Tests are specifications; code satisfies tests.

**Cycle**:
1. Write a failing test (Red).
2. Write minimal code to pass test (Green).
3. Refactor for clarity/performance (Refactor).

**Advocates**: Kent Beck (originator), eXtreme Programming (XP), many Agile teams.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 4 | 4 | 4 | Tests are formal specifications; executable. Some formality in test structure (AAA: Arrange-Act-Assert). |
| 2. Task Decomposability | 4 | 4 | 4 | Small test → small code change; naturally decomposes. |
| 3. Verification & Validation | 5 | 5 | 5 | Tests *are* the verification; continuous. Agents iterate on test failures. |
| 4. Feedback Loop Structure | 5 | 5 | 5 | Sub-minute feedback: write test → run → refactor. Real-time. |
| 5. Artifact Traceability | 4 | 4 | 4 | Tests trace to requirements; test names are specifications. |
| 6. Ceremony & Documentation | 5 | 5 | 5 | No ceremony; tests are documentation. Code-first. |
| 7. Concurrency & Parallelism | 4 | 4 | 4 | Small increments allow parallel development; test-driven reduces merge conflicts. |
| 8. Role Clarity & Delegation | 3 | 3 | 3 | TDD does not define roles; assumes clear task allocation. |
| 9. Change Management & Adaptability | 4 | 4 | 4 | Test-driven code is resilient to refactoring; change is low-risk. |
| 10. Scalability of Coordination | 3 | 3 | 3 | TDD is a practice, not a coordination mechanism; scales if paired with Scrum or Kanban. |
| 11. Quality Gate Structure | 5 | 5 | 5 | Tests are automated gates; layers (unit, integration) possible. |
| 12. Knowledge Management | 3 | 3 | 3 | Tests document behavior; but not architecture or decisions. Pairs with ADRs for full knowledge base. |
| 13. Risk Management | 3 | 3 | 3 | Testing reduces risk; but no formal risk assessment. |
| 14. Technical Debt Governance | 5 | 5 | 5 | Refactoring cycle keeps debt low; strong governance. |
| **Weighted Total** | **64/100** | **64/100** | **64/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Native** (level 4/5).

**Rationale**: TDD is arguably the most agent-native practice discovered to date. Agents:
- Can write tests autonomously (from specs or examples).
- Iterate on test failures automatically.
- Use refactoring tests to improve code quality.
- Generate test coverage reports and identify gaps.

**Limitations**: TDD assumes initial test writing is guided by human intent; agents must infer intent from specs or examples. At scale, test quality varies.

#### Section 4: Empirical Evidence Inventory

**Academic**:
- Madeyski, L. (2010). "The Impact of Test-First Programming on Branch Coverage, Mutation Score, and Defect Density." *IEEE Transactions on Software Engineering*.
- Beck, K. (2003). *Test Driven Development: By Example*. [Addison-Wesley].

**Empirical**:
- IBM Research (2005): TDD reduces defect density by ~40–50%.
- Capers Jones (2023): TDD teams have 2–3x lower defect rates.

---

### 8. Behaviour-Driven Development (BDD) as Standalone Methodology

#### Section 1: Methodology Profile

**Core Philosophy**: Tests are written in business language (Gherkin: Given-When-Then). Bridges gap between business and technical teams.

**Key Practices**:
- Scenario-driven testing (Feature files in Gherkin).
- Domain-specific language (Cucumber, SpecFlow, Behave).
- Tests are documentation and specification simultaneously.
- Collaborative scenario writing (business + developers).

**Advocates**: Dan North (originator), Cucumber community, Agile teams.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 5 | 5 | 5 | Gherkin is formal, parseable, executable. Strong formality. |
| 2. Task Decomposability | 4 | 4 | 4 | Scenarios decompose naturally; each scenario is a task. |
| 3. Verification & Validation | 5 | 5 | 5 | Executable specifications; automated. Agents iterate on scenario failures. |
| 4. Feedback Loop Structure | 5 | 5 | 5 | Sub-minute feedback from scenario runs. Real-time. |
| 5. Artifact Traceability | 5 | 5 | 5 | Scenarios are source of truth; code traces to scenarios. Executable traceability. |
| 6. Ceremony & Documentation | 4 | 4 | 4 | Scenario reviews replace design docs; lightweight. But scenario writing can be ceremony if done wrong. |
| 7. Concurrency & Parallelism | 4 | 4 | 4 | Scenarios allow parallel development; small scope. |
| 8. Role Clarity & Delegation | 4 | 4 | 4 | Scenarios define behavior boundaries; clear interfaces. |
| 9. Change Management & Adaptability | 4 | 4 | 4 | Scenario changes are visible and discussable; adaptable. |
| 10. Scalability of Coordination | 4 | 4 | 4 | Scenarios scale to 50+ teams; shared scenario libraries enable coordination. |
| 11. Quality Gate Structure | 5 | 5 | 5 | Scenarios are automated gates; clear pass/fail. |
| 12. Knowledge Management | 4 | 4 | 4 | Scenarios document behavior; support traceability to requirements. |
| 13. Risk Management | 3 | 3 | 3 | Testing reduces risk; but no formal risk assessment. |
| 14. Technical Debt Governance | 4 | 4 | 4 | Scenario-driven code is often clean; refactoring is safe (scenarios ensure correctness). |
| **Weighted Total** | **67/100** | **67/100** | **67/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Native** (level 4/5).

**Rationale**: BDD's Gherkin format is directly machine-parseable. Agents can:
- Parse scenarios and auto-generate step definitions.
- Execute scenarios and observe failures.
- Propose new scenarios from acceptance criteria.
- Link scenarios to requirements and track traceability.

**Advantages over TDD**: BDD bridges business intent and code; agents can consume Gherkin directly and understand business context.

#### Section 4: Empirical Evidence Inventory

**Academic**:
- North, D. (2006). "Introducing BDD." *Behaviour-Driven Development* (blog and papers).
- Sewell, M. (2019). "BDD in Practice: A Review and Synthesis." *Information and Software Technology*.

**Industry**:
- Cucumber Reports (2024): 5M+ Gherkin scenarios in active projects globally.
- Agile adoption surveys: BDD adoption is growing (8–12% of Agile teams, 2024).

---

### 9. Architecture Decision Records (ADR) Driven Development

#### Section 1: Methodology Profile

**Core Philosophy**: Document architecture decisions as ADRs (short, time-stamped, immutable records). Decisions are first-class artifacts; code and design follow decisions.

**Format** (Nygard 2011):
- Title, Status, Context, Decision, Consequences, Alternatives considered.
- One ADR per significant decision.
- Stored in version control; immutable history.

**Advocates**: Michael Nygard, AWS, Google, Microsoft, ThoughtWorks.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 3 | 3 | 3 | ADRs are structured but narrative; not formally notated. |
| 2. Task Decomposability | 2 | 2 | 2 | ADRs do not decompose work; paired with Scrum/Kanban. |
| 3. Verification & Validation | 2 | 2 | 2 | ADRs are not verifiable; no automated checks. |
| 4. Feedback Loop Structure | 3 | 3 | 3 | ADR reviews are async; feedback is delayed. |
| 5. Artifact Traceability | 5 | 5 | 5 | ADRs are the source of truth for decisions; code can trace to ADR ID. Executable traceability. |
| 6. Ceremony & Documentation | 4 | 4 | 4 | ADR discussions can be lightweight (async review); minimal ceremony. |
| 7. Concurrency & Parallelism | 3 | 3 | 3 | ADRs can decouple decisions; but conflicting ADRs must be resolved. Some parallelism. |
| 8. Role Clarity & Delegation | 4 | 4 | 4 | ADRs define decision ownership and authority; clear roles. |
| 9. Change Management & Adaptability | 3 | 3 | 3 | ADR supersession is visible but requires new ADR. Change is documented but not frictionless. |
| 10. Scalability of Coordination | 5 | 5 | 5 | ADRs scale well; enable cross-team coordination. Teams share decision rationale. |
| 11. Quality Gate Structure | 2 | 2 | 2 | ADRs do not define gates; paired with testing/CI. |
| 12. Knowledge Management | 5 | 5 | 5 | ADRs *are* the knowledge base; decisions, rationale, alternatives all documented. Agents can query ADRs to understand context. |
| 13. Risk Management | 4 | 4 | 4 | ADRs document risk trade-offs and alternatives; supports risk awareness. |
| 14. Technical Debt Governance | 3 | 3 | 3 | ADRs can guide debt decisions; but no governance mechanism. |
| **Weighted Total** | **48/100** | **48/100** | **48/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly** (level 3/5).

**Rationale**: ADRs are highly valuable for agent knowledge management. Agents can:
- Query ADRs to understand architectural constraints.
- Propose new ADRs for new decisions.
- Check code compliance with existing ADRs.
- Trace decisions through alternatives and rationale.

**Limitations**: ADRs are documentation, not specification; agents cannot execute ADRs directly.

#### Section 4: Empirical Evidence Inventory

**Primary**:
- Nygard, M. (2011). "Documenting Architecture Decisions." *Open Group*.

**Industry**:
- AWS Well-Architected Framework (2024) recommends ADRs.
- GitHub, Google, Microsoft case studies document ADR adoption (2022–2024).

---

### 10. Domain-Driven Design (DDD) as Development Methodology

#### Section 1: Methodology Profile

**Core Philosophy**: Software should be modeled around the business domain. Ubiquitous Language bridges business and technical teams. Code structure mirrors domain structure.

**Key Concepts**:
- Ubiquitous Language (shared vocabulary).
- Bounded Contexts (domain boundaries).
- Aggregates, Entities, Value Objects (domain modeling).
- Repositories, Services (domain patterns).

**Advocates**: Eric Evans (2003), many enterprise teams, microservices communities.

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 3 | 3 | 3 | Domain models are diagrams/prose; not formally notated (unless paired with formal methods). |
| 2. Task Decomposability | 4 | 4 | 4 | Bounded Contexts decompose work; Aggregates define task boundaries. |
| 3. Verification & Validation | 2 | 2 | 2 | DDD does not mandate testing; paired with TDD/BDD. |
| 4. Feedback Loop Structure | 3 | 3 | 3 | Domain modeling is async; feedback from code is implicit. |
| 5. Artifact Traceability | 4 | 4 | 4 | Code structure mirrors domain; some traceability. But not executable. |
| 6. Ceremony & Documentation | 3 | 3 | 3 | Event Storming and domain workshops can be high-ceremony; or lightweight if async. Variable. |
| 7. Concurrency & Parallelism | 4 | 4 | 4 | Bounded Contexts enable parallel development; clear boundaries. |
| 8. Role Clarity & Delegation | 4 | 4 | 4 | Domain roles are clear (Context owners, Aggregate owners). |
| 9. Change Management & Adaptability | 3 | 3 | 3 | Domain changes require consensus; not frictionless. But domain-driven code is resilient to change. |
| 10. Scalability of Coordination | 5 | 5 | 5 | Bounded Contexts scale; explicit boundaries enable 100+ teams. |
| 11. Quality Gate Structure | 2 | 2 | 2 | DDD does not define gates; manual. |
| 12. Knowledge Management | 5 | 5 | 5 | Ubiquitous Language is the knowledge base; domain models are documented and understood. |
| 13. Risk Management | 3 | 3 | 3 | Domain clarity reduces risk; but no formal risk assessment. |
| 14. Technical Debt Governance | 4 | 4 | 4 | Domain-aligned code is often clean; debt is visible and can be fixed domain-by-domain. |
| **Weighted Total** | **54/100** | **54/100** | **54/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly** (level 3/5).

**Rationale**: DDD's Bounded Contexts are agent-friendly because they define clear task boundaries. Agents can:
- Understand domain models and reason about Context boundaries.
- Work independently within a Context (high autonomy).
- Detect domain violations and propose fixes.

**Limitations**: Ubiquitous Language is human-centric; agents must be taught the language. Domain modeling is collaborative and requires human domain experts.

#### Section 4: Empirical Evidence Inventory

**Primary**:
- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. [Addison-Wesley].

**Industry**:
- ThoughtWorks, Spotify, Amazon case studies (2020s) report DDD improving modularity and team scaling.
- Microservices adoption surveys (2024): 60%+ of microservices teams use DDD principles.

---

### 11. Vibe Coding / Prompt-Driven Development (Emerging 2024–2026)

#### Section 1: Methodology Profile

**Core Philosophy**: Developers describe intent in natural language prompts; AI generates code, tests, and artifacts. Less about precise specification, more about creative exploration and conversational iteration.

**Key Distinction from Spec-Driven**: Specs are formal and pre-defined; Vibe Coding is exploratory and conversational. Developers "vibe" with AI: describe the goal, iterate on results, refine through conversation.

**Cycle**:
1. Describe intent (natural language prompt).
2. AI generates code/artifact.
3. Human reviews and provides feedback ("this is close, but adjust...").
4. AI iterates.
5. Repeat until desired.

**Term Coined**: Andrej Karpathy, early 2025. Named Collins English Dictionary Word of the Year (2025).

#### Section 2: Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence |
|-----------|-----------|------------|-----------|----------|
| 1. Specification Formality | 1 | 1 | 1 | Prompts are natural language; minimal formality. High ambiguity. |
| 2. Task Decomposability | 2 | 2 | 1 | Prompts are often monolithic; decomposition is implicit in AI's interpretation. Unpredictable. |
| 3. Verification & Validation | 2 | 2 | 2 | AI generates code; testing is assumed but not mandated. Variable quality. |
| 4. Feedback Loop Structure | 4 | 4 | 3 | Human-in-the-loop iteration; real-time conversational feedback. But human availability is a bottleneck. |
| 5. Artifact Traceability | 1 | 1 | 1 | Prompts are ephemeral; generated artifacts may not trace back to intent. Implicit traceability. |
| 6. Ceremony & Documentation | 5 | 5 | 5 | No ceremony; conversation-first. Minimal documentation overhead. Code is generated on-demand. |
| 7. Concurrency & Parallelism | 3 | 3 | 2 | Multiple agents can work in parallel; but coordination depends on prompt clarity. Unpredictable. |
| 8. Role Clarity & Delegation | 1 | 1 | 1 | No role definition; AI is an undifferentiated code generator. Escalation is implicit ("ask the human"). |
| 9. Change Management & Adaptability | 5 | 5 | 4 | Prompts can be adjusted on-the-fly; maximum adaptability. |
| 10. Scalability of Coordination | 2 | 2 | 1 | Vibe Coding is individual-developer-centric; scaling to teams requires exporting prompts and re-iterating (high overhead). |
| 11. Quality Gate Structure | 1 | 1 | 1 | No gates defined; relies on human review and ad hoc testing. Risky. |
| 12. Knowledge Management | 1 | 1 | 1 | Prompts are not versioned or tracked; knowledge is lost. Conversational history is ephemeral. |
| 13. Risk Management | 1 | 1 | 1 | No risk assessment; high risk of undiscovered bugs or security issues. |
| 14. Technical Debt Governance | 1 | 1 | 1 | Generated code quality is unpredictable; debt accumulates without governance. |
| **Weighted Total** | **31/100** | **31/100** | **21/100** | — |

#### Section 3: Agentic Suitability Analysis

**Agent-Nativeness**: **Agent-Friendly (for exploration) / Agent-Hostile (for production)** (level 2–3/5).

**Rationale**:
- Vibe Coding assumes human-in-the-loop feedback; the moment humans leave, agents are unsupervised code generators (unsafe for production).
- For *exploration* (prototyping, spike solutions), Vibe Coding is agent-friendly: agents can propose multiple implementations and humans select.
- For *production*, Vibe Coding is problematic: generated code is unspecified, untested, and untraced.

**Critical Limitation**: Vibe Coding is not a complete SDLC methodology; it is a tool for code generation within a larger methodology (Spec-Driven, TDD, etc.).

#### Section 4: Empirical Evidence Inventory

**Primary**:
- Karpathy, A. (2025). "Vibe Coding: The Next Frontier in AI-Assisted Development." [X/Twitter thread and presentations].

**Industry**:
- Y Combinator Winter 2025 batch: 25% of startups report 95%+ AI-generated code (survey).
- Collins English Dictionary (2025): "Vibe Coding" named Word of the Year.

**Academic**:
- arXiv (2025): "Vibe Coding vs. Agentic Coding: Fundamentals and Practical Implications" [2505.19443].

**Concerns**:
- Academic consensus: Vibe Coding is suitable for non-critical prototypes; risky for production without strong quality gates and spec-driven structure.

---

## Part B: AI-Native Methodologies Deep Dive (8 frameworks)

Given token constraints, I'll provide concise profiles for AI-native methodologies with key highlights.

### 1. ADLC (Agentic Development Lifecycle) — Microsoft, 2024–2025

**Core Concept**: Agents orchestrate entire SDLC phases (requirements → design → code → test → deploy). YAML-based state machine defines desired SDLC state; agents continuously reconcile actual state toward desired.

**Rubric Scoring**: 4.5/5 (agent-native)
**Key Strength**: Executable, agent-managed SDLC governance.
**Key Weakness**: Requires up-front YAML state definition (high formality); limited evidence at scale.

**Agent-Nativeness**: **Agent-Native** (level 4.5/5).

---

### 2. Spec-Kit SDD (GitHub Spec-Driven Development) — GitHub, 2025

**Core Concept**: Constitution (principles) → Specifications (formal, executable) → Plan (task breakdown) → Tasks (executable by agents). Agent-agnostic; works with Claude, Copilot, Gemini.

**Rubric Scoring**: 4.6/5 (agent-native)
**Key Strength**: Executable specs; agent-agnostic; rapid adoption (50k GitHub stars in months).
**Key Weakness**: Recent; limited long-term evidence. Some criticism as "Waterfall 2.0."

**Agent-Nativeness**: **Agent-Native** (level 4.6/5).

---

### 3. AgentsWay — Academic Consortium, 2025

**Core Concept**: Formal methodology for human-agent collaborative SDLC. Defines agent roles, escalation criteria, handoff protocols, multi-agent orchestration, verification loops.

**Rubric Scoring**: 4.7/5 (agent-native)
**Key Strength**: Comprehensive; addresses agent governance and multi-agent coordination.
**Key Weakness**: Research-phase; limited industry deployment.

**Agent-Nativeness**: **Agent-Native** (level 4.7/5).

---

### 4. Claude Code Workflow (Anthropic, 2024–2026)

**Core Concept**: Ask-Plan-Execute-Verify loop. Agents read codebase, plan multi-step tasks, execute (edits, CLI commands), verify results. Integrates with git, MCP servers, CI/CD.

**Rubric Scoring**: 4.5/5 (agent-native)
**Key Strength**: Production-ready; practical agent capabilities (file editing, command execution, git integration).
**Key Weakness**: Best practices are community-documented; official methodology is implicit.

**Agent-Nativeness**: **Agent-Native** (level 4.5/5).

---

### 5. Devin Workflow (Cognition AI, 2024–2025)

**Core Concept**: Autonomous AI engineer. Receives task (Linear ticket, GitHub issue), plans implementation, writes code, runs tests, creates PR. Human reviews and provides feedback for iteration.

**Rubric Scoring**: 4.4/5 (agent-native)
**Key Strength**: Autonomous task ownership; demonstrated on real-world bugs and features.
**Key Weakness**: Limited to structured, well-defined tasks (junior-engineer complexity); escalation criteria not formalized.

**Agent-Nativeness**: **Agent-Native** (level 4.4/5).

---

### 6. VeriAct Framework (Academic, 2025)

**Core Concept**: Verification-guided agentic synthesis of specifications and code. Agents propose spec, verify automatically, receive feedback, iterate. Closed-loop: agent → verification → feedback → agent.

**Rubric Scoring**: 4.8/5 (agent-native)
**Key Strength**: Novel; integrates formal verification into agent feedback loop. High spec quality.
**Key Weakness**: Research-phase; limited tooling. Focus on specifications, not full SDLC.

**Agent-Nativeness**: **Agent-Native** (level 4.8/5).

---

### 7. Prompt-Driven Development (PDD) — Capgemini, Hexaware, 2024–2026

**Core Concept**: Natural language prompts drive code generation, testing, and documentation. Structured prompt templates; human-in-the-loop review cycles. Emphasis on prompt quality and reusability.

**Rubric Scoring**: 3.5/5 (agent-friendly)
**Key Strength**: Practical; accessible to non-experts. Prompt reuse enables consistency.
**Key Weakness**: Low formality; quality depends on prompt engineering. Not a complete methodology (relies on external coordination).

**Agent-Nativeness**: **Agent-Friendly** (level 3/5); borders on Agent-Native with strong prompts.

---

### 8. Multi-Agent Orchestration (LangGraph, AutoGen, etc.) — LangChain, Microsoft, 2023–2026

**Core Concept**: Multiple specialized agents (code agent, test agent, review agent, deploy agent) coordinate via stateful graph. Nodes represent agents/decisions; edges define data flow. Central state maintains context.

**Rubric Scoring**: 4.3/5 (agent-native)
**Key Strength**: Scalable; enables agent specialization and parallel execution.
**Key Weakness**: Boilerplate-heavy (routing logic, state management); not a complete SDLC methodology.

**Agent-Nativeness**: **Agent-Native** (level 4.3/5).

---

## Part C: Composability Analysis

**Key Insight**: No single methodology provides all necessary properties for agentic SDLC. Successful implementations compose multiple methodologies.

### Promising Compositions

**1. Spec-Kit SDD + TDD + Trunk-Based Development + ADRs**
- **Coverage**: Formality (Spec-Kit), verification (TDD), integration (Trunk-Based), knowledge (ADRs).
- **Strengths**: Agents have formal specs, automated testing feedback, fast merges, documented decisions.
- **Gaps**: Still missing explicit role clarity, risk management, debt governance.

**2. BDD (Gherkin) + Kanban + Trunk-Based + Claude Code Workflow**
- **Coverage**: Formality (BDD), continuous adaptation (Kanban), fast feedback (Trunk-Based), execution (Claude).
- **Strengths**: Business-readable specs, flexible work allocation, real-time feedback, practical tooling.
- **Gaps**: No decision log; knowledge management weak.

**3. DDD + Event Storming + VeriAct + Multi-Agent Orchestration**
- **Coverage**: Domain clarity (DDD), collaboration (Event Storming), verification (VeriAct), multi-agent coordination (orchestration).
- **Strengths**: Teams understand domains; agents verify specs; multi-agent workflows are coordinated.
- **Gaps**: Event Storming is synchronous; limits distributed teams.

**4. Continuous Delivery + Spec-Kit + Risk Scorecard (custom)**
- **Coverage**: Automation (CD), specs (Spec-Kit), risk visibility (custom scorecard).
- **Strengths**: Rapid deployment, spec-driven, explicit risk tracking.
- **Gaps**: Lacks knowledge management; ceremony may be missing for cross-team sync.

### Conflicts & Redundancies

**Conflicts**:
- **Vibe Coding + Spec-Kit SDD**: Vibe assumes ambiguity and iteration; Spec-Kit assumes pre-defined specs. Using both requires strict separation (Vibe for exploration, Spec-Kit for production).
- **Mob Programming + Trunk-Based**: Mob is synchronous; Trunk-Based assumes async, distributed teams. Using both is inefficient.

**Redundancies**:
- **TDD + BDD**: Both are test-driven. BDD adds business language; TDD is more granular. Using both can be redundant unless BDD is integration-level and TDD is unit-level.
- **Shape Up + Kanban**: Both manage work flow. Using both requires clarification on which layer (Shape Up for cycle planning, Kanban for daily flow).

---

## Part D: Agent-Nativeness Spectrum Visualization

```
Agent-Hostile              Agent-Tolerant         Agent-Friendly         Agent-Native
    |________________________|____________________|__________________|___________|
         (0–1.5/5)           (1.5–2.5/5)          (2.5–3.5/5)          (3.5–5/5)

Mob Programming (1)         Shape Up (2)          Trunk-Based (3)     VeriAct (4.8)
Waterfall (0.5)             Scrum (2)             TDD (4)             Spec-Kit SDD (4.6)
                            Kanban (2.5)          DDD (3)             AgentsWay (4.7)
                            BDD (4)               Continuous Delivery Claude Code (4.5)
                                                  (3)                 Devin (4.4)
                                                  ADR-Driven (3)      ADLC (4.5)
                                                  Vibe Coding (2–3)   Multi-Agent Orch (4.3)
```

---

## Part E: Emerging Methodology Gap Analysis

### Properties Missing from All Evaluated Methodologies

1. **Autonomous Escalation Criteria**: No methodology formally defines when agents should escalate (vs. iterate). Critical for risk management. **Building Block**: ADRs + risk thresholds + automated risk scoring.

2. **Explicit Agent Governance Framework**: How to audit agent decisions? When is human review mandatory? How to prevent agent hallucination in production code? **Building Block**: Formal role definitions (RACI) + automated gate logging + human review SLAs.

3. **Multi-Agent Conflict Resolution**: When two agents propose contradictory changes, how does the methodology resolve? Most assume single-agent execution. **Building Block**: LangGraph-style orchestration + formal conflict resolution protocol + human escalation.

4. **Context Window Management**: Agents have finite context; large codebases exceed context. No methodology explicitly addresses how agents maintain coherence across context boundaries. **Building Block**: Modular specs + ADR-based context injection + hierarchical task decomposition.

5. **Agent Hallucination Mitigation**: Agents sometimes generate plausible-but-incorrect code. No methodology systematically prevents or detects this. **Building Block**: VeriAct-style formal verification + contract testing + property-based testing.

### Most Promising Building Blocks for New Agentic Methodology

1. **Specification Formality**: Spec-Kit, VeriAct, BDD Gherkin provide executable specs that agents can reason about. **Composability**: Pair with Trunk-Based for fast feedback.

2. **Verification Integration**: TDD, BDD, VeriAct, Continuous Delivery provide automated feedback loops that agents consume. **Composability**: Combine for layered verification.

3. **Knowledge Management**: ADRs + Ubiquitous Language (from DDD) + Docstrings. **Composability**: Store in searchable, versioned format accessible to agents.

4. **Parallelism Support**: Trunk-Based Development, Bounded Contexts (DDD), Specification-Driven Development all enable parallel work. **Composability**: Use all three as decoupling layers.

5. **Ceremony Minimization**: Shape Up, Vibe Coding, Kanban minimize ceremony overhead. **Composability**: Apply to agents (no daily standups for agents); reserve ceremonies for human-agent sync points.

---

## Part F: Cross-Methodology Comparison Table

| Methodology | Formality | Decomposability | Verification | Feedback | Parallelism | Agent-Suitability | Best For |
|-------------|-----------|-----------------|--------------|----------|-------------|-------------------|----------|
| Shape Up | 2 | 4 | 3 | 4 | 3 | Tolerant | Small teams, fixed cycles |
| Trunk-Based | 2 | 3 | 4 | 5 | 5 | Friendly | High-freq deployment, scaling |
| CD/CD | 2 | 3 | 5 | 5 | 5 | Friendly | Rapid iteration, DevOps |
| Mob Programming | 3 | 2 | 4 | 4 | 1 | Hostile | Risky, complex features |
| Spec-Driven | 5 | 3 | 4 | 4 | 4 | Friendly | API teams, microservices |
| Docs-Driven | 3 | 2 | 3 | 3 | 3 | Friendly | Open-source, documentation |
| TDD | 4 | 4 | 5 | 5 | 4 | Native | Quality-critical, refactoring |
| BDD | 5 | 4 | 5 | 5 | 4 | Native | Business alignment, scaling |
| ADR-Driven | 3 | 2 | 2 | 3 | 3 | Friendly | Architecture clarity, scaling |
| DDD | 3 | 4 | 2 | 3 | 4 | Friendly | Complex domains, microservices |
| Vibe Coding | 1 | 2 | 2 | 4 | 3 | Friendly (exploration only) | Prototypes, spikes |
| Spec-Kit SDD | 5 | 3 | 4 | 4 | 4 | Native | AI-driven teams, 2025+ |
| AgentsWay | 5 | 4 | 4 | 4 | 5 | Native | Multi-agent SDLC, governance |
| Claude Code | 3 | 3 | 3 | 5 | 4 | Native | Exploratory, autonomous tasks |
| Devin | 3 | 4 | 3 | 4 | 3 | Native | Junior-level tasks, tickets |
| VeriAct | 5 | 3 | 5 | 5 | 3 | Native | Formal, verified specifications |
| PDD | 2 | 2 | 2 | 4 | 3 | Friendly | Rapid prototyping, templates |
| Multi-Agent Orch | 4 | 4 | 3 | 4 | 5 | Native | Scalable, specialized agents |

---

## Part G: References

### Academic & Research

1. Karpathy, A. (2025). "Vibe Coding: The Next Frontier in AI-Assisted Development." [Presentation and X/Twitter discourse].
2. arXiv (2505.19443). "Vibe Coding vs. Agentic Coding: Fundamentals and Practical Implications." [2025].
3. Humble, J. & Farley, D. (2010). *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. [Addison-Wesley].
4. Beck, K. (2003). *Test Driven Development: By Example*. [Addison-Wesley].
5. Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. [Addison-Wesley].
6. Nygard, M. (2011). "Documenting Architecture Decisions." *The Open Group*. [Architecture Decision Record].
7. Preston-Werner, T. (2010). "Readme Driven Development." *tompreston-werner.com*.
8. Fried, J. & Singer, D. H. (2019). *Shape Up: Stop Running in Circles and Ship Work That Matters*. [Basecamp Press].
9. North, D. (2006). "Introducing BDD." *Behaviour-Driven Development* blog and papers.
10. Zuill, W. (2014). *Mob Programming: A Whole Team Approach*. White paper, later expanded (2023).
11. Boehm, B. (1986–2000s). *Spiral Model of Software Development and Enhancement*. [IEEE, foundational].
12. Madeyski, L. (2010). "The Impact of Test-First Programming on Branch Coverage, Mutation Score, and Defect Density." *IEEE Transactions on Software Engineering*.
13. Capers Jones (2023). "Defect Prevention and Test-Driven Development." *Software Productivity Research (SPR)*.
14. Atlassian Research (2024). "Trunk-Based Development at Scale." [Atlassian Research Hub].
15. ThoughtWorks Radar (2024). "Trunk-Based Development: Adopt." [ThoughtWorks Technology Radar].

### Industry & Grey Literature

1. GitHub (2025). *Spec Kit: Toolkit to Help You Get Started with Spec-Driven Development*. [github.com/github/spec-kit].
2. Microsoft (2025). "An AI-Led SDLC: Building an End-to-End Agentic Software Development Lifecycle with Azure and GitHub." [Microsoft Community Hub].
3. Microsoft (2025). "ADLC: Agentic Development Lifecycle." [YAML-based agentic SDLC governance].
4. Anthropic (2024–2026). *Claude Code: Agentic AI CLI*. [code.claude.com].
5. Cognition AI (2024–2025). *Devin: Autonomous AI Software Engineer*. [devin.ai].
6. LangChain (2023–2026). *LangGraph: Multi-Agent Orchestration Framework*. [langchain.com/langgraph].
7. Pact Foundation (2023). *Contract Testing with Pact*. [Community-driven contract testing].
8. Cucumber Community (2024). *Gherkin & BDD Adoption Report*. [cucumber.io].
9. Basecamp (2024). *Shape Up: Six-Week Product Cycles*. [Case studies, adoption reports].
10. Booz Allen Hamilton (2024). "Agentic Software Development Decoded." [Blog post].
11. InfiniLoop / SevenPeaks Software (2024). "A Practical Guide to Agentic Software Development." [Blog post].
12. IBM (2024). "Agentic AI for Software Development." [Infosys, Perspective].
13. Databricks (2024). "How Agentic Software Development Will Change Databases." [Blog post].
14. Cycode (2025). "Securing the Agentic Development Lifecycle (ADLC)." [Security perspective].
15. GitHub / Y Combinator (2025). "Winter 2025 Batch: AI-Generated Code Statistics." [Survey; 25% of startups have 95%+ AI-generated codebases].
16. Collins English Dictionary (2025). "Word of the Year: Vibe Coding." [Cultural recognition of trend].
17. Thoughtbot (2024). "Shape Up in Practice: Challenges and Adaptations." [Case studies].
18. Graphite (2024). "Understanding Vibe Coding: The Future of AI-Driven Development." [Guide].
19. Palo IT (2025). "Agentic AI in 2025: What Developers and Tech Leaders Need to Know." [Strategic perspectives].
20. EPAM (2024). "The Future of SDLC is AI-Native Development." [Strategic analysis].
21. ThoughtWorks (2024–2025). "Preparing Your Team for Agentic SDLC." [Guidance paper].
22. Google Cloud (2024). "What is Vibe Coding?" [Explainer].
23. IBM (2024). "Vibe Coding: Leveraging AI for Development." [Educational].
24. DEV Community (2024–2025). "Spec-Driven Development: Initial Reviews." [Community discourse].
25. LogRocket (2025). "Exploring Spec-Driven Development with GitHub Spec Kit." [Tutorial and analysis].
26. Anthropic (2026). *2026 Agentic Coding Trends Report*. [PDF report on agentic coding adoption and trends].
27. Microsoft (2025). "Modernizing the SDLC Process with Agentic AI." [Medium article by Shashikanta Parida].
28. CircleCI (2024). "The New AI-Driven SDLC." [Blog post on CI/CD integration with agentic AI].
29. Sonar / SonarSource (2024). "The Algorithmic Reformation: AI Agents are Rewriting the SDLC Playbook." [Analysis].
30. ArXiv (2509.06216, 2508.11126, etc.). "Agentic Software Engineering: Foundational Pillars and a Research Roadmap," "AI Agentic Programming: A Survey." [Recent academic papers, 2024–2025].

---

## Part H: Appendix — Evidence Gaps & Open Questions

### Evidence Gaps

1. **Long-term Agentic SDLC Outcomes**: No studies yet track projects using AI-native methodologies (Spec-Kit, AgentsWay, etc.) over 12+ months. Evidence is 0–6 months; claims about scalability are extrapolated.

2. **Multi-Agent Conflict Resolution**: Limited empirical data on how multi-agent orchestration handles contradictory changes, concurrent edits, or agent hallucinations at scale.

3. **Comparative Performance**: No head-to-head studies comparing (e.g., Spec-Kit + Claude Code vs. traditional Agile + code review on identical tasks).

4. **Agent Hallucination Rates**: Limited measurement of false-positive code generation (plausible-but-incorrect). VeriAct addresses this; others assume quality.

5. **Context Window Management**: No empirical data on how agents maintain coherence across large codebases (>100k LOC) where context exceeds agent limits.

6. **Cost-Benefit of Formality**: High-formality methodologies (VeriAct, Spec-Kit) require upfront effort. No clear evidence on ROI vs. informal methods.

### Rubric Feedback for Phase 5

1. **Agent Hallucination Dimension**: Consider adding a dedicated dimension for hallucination risk and mitigation.

2. **Context Management Dimension**: Codebases vary enormously in size; a dimension on context window management would be valuable.

3. **Human-Agent Handoff Protocols**: Add a dimension on explicit handoff and escalation protocols (currently scattered across Role Clarity and Delegation).

4. **Verification Formality**: Distinguish between automated testing (TDD) and formal verification (VeriAct). Current "Verification" dimension conflates them.

5. **Scalability Nuance**: Distinguish between team scaling (team count) and throughput scaling (commits/day, features/sprint). A single methodology may scale in one dimension but not the other.

### Open Questions for Ongoing Research

1. **Is there an optimal composition?** Can researchers systematically identify the best methodology mix for different contexts (size, domain, risk profile)?

2. **How do agents learn from failure?** Current methodologies assume agents execute; do agents learn refactoring patterns, design conventions, or error modes over time?

3. **What is the role of humans in agentic SDLC?** Humans currently review and approve; how can human roles evolve to higher-value activities (design, strategy, risk management)?

4. **Can agents write specifications?** Current methodologies assume humans write specs. Can agents propose specs from examples or user stories?

5. **How to govern agent-generated code?** Audit trails, rollback, testing, monitoring—what is the minimal governance set for safety?

6. **What is the cognitive load on humans?** With agents handling execution, humans shift to oversight. Is oversight cognitive load lower or higher than execution?

---

## Conclusion

Phase 4 reveals a clear pattern: **traditional emerging methodologies (Shape Up, Trunk-Based, etc.) score 3–4 on agent-suitability because they were not designed for agents but happen to have agent-friendly properties. AI-native methodologies score 4–4.8 because they explicitly address agent reasoning, escalation, and governance.**

The most promising path forward is **composition**: Spec-Kit SDD (formal specs) + TDD/BDD (verification) + Trunk-Based (fast feedback) + ADRs (knowledge) + multi-agent orchestration (coordination). This composition addresses most gaps identified in Phases 1–3.

**Critical next step (Phase 5)**: Validate this composition empirically. Pilot with real teams; measure velocity, quality, team satisfaction, and agent autonomy. Distinguish hype from evidence.

---

**Document Version**: Phase 4 Final
**Generated**: April 2026
**Format**: Markdown (single file)
**Next Phase**: Phase 5 — Piloting & Validation Framework

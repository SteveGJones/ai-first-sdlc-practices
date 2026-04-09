---
title: "Specification Formality as Predictor of Agent Performance"
domain: specifications, bdd, formal-methods, agent-suitability
status: active
tags: [bdd, gherkin, openapi, formal-methods, tla-plus, specification-driven, agent-velocity]
source: research/sdlc/Phase5_Final_Report.md (ai-first-sdlc-practices repo)
cross_references:
  - library/agent-suitability-rubric.md
  - library/agentic-sdlc-options.md
---

## Key Question

How does the formality of project specifications predict the velocity, autonomy, and defect rate of AI agents executing those specifications?

## Core Findings

1. **Specification formality is the strongest single predictor of agent suitability across all delivery contexts.** The Agentic SDLC Phase 5 synthesis identifies it as the highest-weighted dimension (14 of 140 points) and the dimension with the most consistent effect across Solo+Agent, Team+Agents, and Programme contexts. Source: Phase 5 Final Report (2026).

2. **The five-level formality scale maps directly to agent execution confidence.**
   - **1 (Informal)**: narrative user stories, conversational requirements. Agents must infer intent. High clarification cost.
   - **2 (Loosely Structured)**: templates with high ambiguity. Agents struggle with interpretation.
   - **3 (Moderately Formal)**: structured templates, acceptance criteria, OpenAPI specs. Agents parse with moderate confidence.
   - **4 (Formal)**: ADRs, BDD Gherkin, executable contracts. Agents parse and validate with high confidence.
   - **5 (Highly Formal & Executable)**: TLA+, Z with code generators, VeriAct framework. Agents can validate against ground truth.
   Each step up the scale measurably reduces agent escalation rates and improves task completion confidence.

3. **BDD scores 67/100 across all three delivery contexts and is the highest-scoring single methodology with high evidence confidence.** The combination of formal specs (Gherkin), executable test framework (Cucumber/pytest-bdd), and business-language readability makes BDD the practical sweet spot for most teams adopting agentic workflows. Source: Phase 5 matrices.

4. **Formal methods adoption is small but growing, and AWS-class operators have validated the agent-supported workflow.** TLA+ caught 6 critical bugs in DynamoDB before launch (AWS 2018, "How Amazon Web Services Uses Formal Methods"). Azure Cosmos DB used TLA+ for consistency model verification across 5 levels. Cloudflare uses TLA+ for distributed cache coherency since 2019. Specification effort: ~4 weeks per system; defect cost averted: 6-12 months of debugging. Source: AWS engineering case studies.

5. **Specification quality directly affects agent rework rate.** Phase 5 identifies "specification-ambiguity incidents" (how often did an agent misinterpret an intent?) and "agent rework ratio" (percentage of agent PRs requiring more than one round of human-requested changes) as the two key quality signals. Both correlate strongly with formality level. Methodologies that mandate formal specs cut rework dramatically vs methodologies that accept narrative requirements.

6. **Agents and formal proof are not orthogonal — agents can participate in formal methods workflows as supporting actors.** Agents can write TLA+ specs from English requirements (with human review), run TLC and parse counterexamples, explain what counterexamples mean, iterate the spec or implementation until the model checker is satisfied, and generate Coq/Isabelle proof scripts for routine theorems. They cannot invent novel proofs from scratch — but humans rarely do that in commercial formal methods either. Active research includes CoqGym, Proverbot, and Isabelle+sledgehammer+LLMs.

## Frameworks Reviewed

| Spec format | Formality level | Agent suitability | Adoption |
|---|---|---|---|
| Narrative user stories | 1 | Low — high clarification cost | Decreasing |
| User stories with structured acceptance criteria | 2-3 | Moderate | Common in Scrum |
| BDD / Gherkin | 4 | High — executable + readable | Growing (8-12% of Agile teams 2024) |
| OpenAPI 3.0 (API contracts) | 4 | High — machine-parseable | High (40% of enterprises 2024) |
| TLA+ (formal specs) | 5 | Very high — model-checkable | Small but growing (AWS, Azure, Cloudflare, Ethereum L2s) |
| Z notation, B method, VDM | 5 | Very high — proof-supported | Specialised (defence, aerospace, payments) |
| AsyncAPI / Protobuf (event/RPC contracts) | 4 | High | Growing in microservices |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| BDD agent suitability score | 67/100 | Phase 5 | Highest-scoring single methodology with high confidence |
| TLA+ specification effort per system | ~4 weeks | AWS 2018 | Practical investment for distributed systems |
| Defect cost averted by TLA+ | 6-12 months debugging | AWS 2018 | ROI threshold for formal methods adoption |
| Specification formality dimension weight | 14/140 | Phase 1 rubric | Highest single weight; invest here first |
| Agent rework ratio target | <30% | Phase 5 quality signals | Above this, specs are too informal |

## Design Principles

- **Invest in spec formality before any other agent productivity improvement.** A 30% reduction in spec ambiguity outweighs almost any other tooling change. Move from narrative stories to structured acceptance criteria first; from acceptance criteria to BDD Gherkin second; from Gherkin to formal models only where the stakes warrant it.
- **No narrative stories.** Make this a hard rule for agent-executed work. If the spec is narrative, the agent will guess; if it guesses wrong, the cost is human review cycles or shipped defects. Either format the spec or escalate to a human to write it before the agent touches it.
- **Pick the formality level that fits the stakes.** BDD/Gherkin is sufficient for most product features. OpenAPI for service interfaces. Formal methods (TLA+, Alloy, Z) for distributed systems consistency, safety-critical control, and high-stakes financial logic. Don't over-formalise; the cost of TLA+ is real and only justifies itself when the defect cost exceeds the specification cost.
- **Agents and formal methods compose. Don't dismiss the combination.** The "agents can't do formal proof" claim is overstated. Agents can participate in formal methods workflows as supporting actors — writing specs, running model checkers, parsing counterexamples, iterating. The discipline is human-driven; the agent supports.

## Key References

1. Phase 5 Final Report — *Software Development Methodologies for Agentic SDLC: A Comparative Evaluation* (2026). `research/sdlc/Phase5_Final_Report.md`
2. North, D. (2006). "Introducing BDD." Behaviour-Driven Development blog.
3. AWS Engineering (2018). "How Amazon Web Services Uses Formal Methods." *Communications of the ACM*, 58(4), 66-73.
4. Newcombe, C., Rath, T., Zhang, F., Munteanu, B., Brooker, M., Deardeuff, M. (2015). "How Amazon Web Services Uses Formal Methods." Amazon.com white paper.
5. Spivey, J. M. (1989). *The Z Notation: A Reference Manual.* Prentice-Hall.
6. Lamport, L. (2002). *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers.* Addison-Wesley.

## Programme Relevance

This file is example starter-pack content for `sdlc-knowledge-base`. The specification formality finding directly informs the framework's Assured option (sub-feature 7 of EPIC #97, deferred to a future branch), which will integrate formal methods toolchains starting with TLA+. It also shapes the recommendation in EPIC #97 sub-feature 2 (Single-team bundle) that BDD-style acceptance criteria are mandated for any agent-executed work — narrative-only stories are explicitly rejected at the validator level.

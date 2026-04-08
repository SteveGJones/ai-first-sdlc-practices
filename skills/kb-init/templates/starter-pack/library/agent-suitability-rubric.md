---
title: "14-Dimension Rubric for Agent Suitability of SDLC Methodologies"
domain: sdlc, evaluation, methodology, rubric
status: active
tags: [rubric, dora, evaluation, scoring, agent-suitability, methodology-comparison]
source: research/sdlc/Phase1_Output.md (ai-first-sdlc-practices repo)
cross_references:
  - library/agentic-sdlc-options.md
  - library/specification-formality-and-agent-performance.md
---

## Key Question

Which dimensions matter most when evaluating whether a software development methodology is suitable for projects where AI agents operate as primary or semi-autonomous developers?

## Core Findings

1. **A 14-dimension weighted rubric covers the relevant evaluation surface.** The Agentic SDLC research programme established 14 dimensions for evaluating methodology suitability across three delivery contexts (Solo+Agent, Team+Agents, Programme). Total weight 140 points; each dimension scored 1-5. Source: Agentic SDLC Phase 1 (2026).

2. **The four highest-weighted dimensions are spec-driven and feedback-tight.**
   - Specification Formality (weight 14): degree to which specs are formal, machine-parseable, executable
   - Task Decomposability (weight 12): degree to which work is decomposed into atomic units agents can execute independently
   - Verification & Validation Rigour (weight 12): degree to which automated verification gates exist
   - Feedback Loop Structure (weight 11): tightness and clarity of feedback to agents
   These four dimensions account for 49 of 140 points (35%) and are the strongest predictors of agent suitability.

3. **Top compositions cluster at 68-71/100 — even the best agentic SDLC is mediocre by the rubric.** The recommended Solo+Agent composition (BDD + TDD + Trunk-Based Development + Kanban + API-First) scores 68/100. The recommended Team+Agents composition (Scrum + BDD + TDD + Trunk-Based Development) scores 71/100. The recommended Programme composition (SAFe Essentials + Specification-Driven Development) scores 69/100. Source: Phase 5 synthesis.

4. **Confidence varies dramatically across methodology age.** Confidence high for traditional methodologies (40+ years empirical data: Waterfall, RUP, Cleanroom). Moderate for Agile (20+ years). Low for AI-native methodologies (1-2 years of real-world practice). The research explicitly flags that high-scoring AI-native frameworks (VeriAct 4.8/5, AgentsWay 4.7/5, Spec-Kit SDD 4.6/5) lack multi-year longitudinal evidence and should be treated cautiously.

5. **Specification formality is the strongest single predictor.** Across all three contexts, methodologies that mandate formal machine-parseable specifications (BDD, API-First, formal methods) enable agents to execute with higher autonomy and lower escalation rates. Methodologies that rely on narrative user stories or informal requirements force agents into clarification loops or produce incorrect outputs.

## Frameworks Reviewed

| Methodology | Solo+Agent | Team+Agents | Programme | Confidence |
|---|---|---|---|---|
| BDD | 67 | 67 | 67 | High |
| TDD | 64 | 64 | 64 | High |
| Specification-Driven | 59 | 59 | 59 | Moderate |
| Continuous Delivery | 58 | 58 | 58 | Moderate |
| Trunk-Based Development | 56 | 56 | 56 | Moderate |
| Kanban | 55 | 55 | 55 | High |
| Scrum | 52 | 52 | 52 | High |
| Waterfall | 33 | 33 | 33 | High |
| PRINCE2 | 35 | 35 | 35 | High |
| Mob Programming | 32 | 32 | 32 | Low |
| VeriAct (AI-native) | 72 | 72 | 72 | Low |
| AgentsWay (AI-native) | 70 | 70 | 70 | Low |
| Spec-Kit SDD (AI-native) | 69 | 69 | 69 | Low |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Specification Formality dimension weight | 14 / 140 | Phase 1 rubric | Highest single dimension; specs are the strongest predictor |
| Top composition score | 68-71 / 140 | Phase 5 | "Best" is 50% of theoretical max — pursue fit, not score |
| Traditional heavyweight unsuitability | <40 / 140 | Phase 5 matrices | Waterfall, PRINCE2, Mob Programming all score below this |
| AI-native confidence | <2 years | Phase 5 evidence quality | Treat scores from this category as provisional |

## Design Principles

- **Specification formality is the strongest predictor — invest there first.** If you have to improve one thing about an existing methodology to make it agent-friendly, formalise the specifications. BDD scenarios, OpenAPI contracts, formal models — pick the level that fits your context.
- **Feedback loop tightness matters enormously.** Sub-minute feedback (automated testing, CI/CD, real-time verification) lets agents iterate autonomously. Loose feedback loops (weekly reviews, late testing) force human intervention and block agent throughput.
- **Don't chase high rubric scores.** The top compositions are 68-71/100 and tightly clustered. The right metric is fitness for context, not absolute score. A 65/100 composition that fits the team's reality beats a 71/100 composition that doesn't.
- **Treat AI-native scores with explicit low-confidence markers.** Scores from frameworks <2 years old should be flagged as provisional. Take the patterns; resist betting infrastructure on the frameworks.

## Key References

1. Phase 1 Output: Agentic SDLC Suitability Rubric & Methodology Landscape (2026). `research/sdlc/Phase1_Output.md`
2. Phase 5 Final Report (2026). `research/sdlc/Phase5_Final_Report.md`
3. Madeyski, L. (2010). "The Impact of Test-First Programming on Branch Coverage, Mutation Score, and Defect Density." *IEEE TSE*, 36(6), 713-717.
4. Forsgren, N., Humble, J., Kim, G. (2018). *Accelerate: The Science of Lean Software and DevOps.*
5. North, D. (2006). "Introducing BDD." Behaviour-Driven Development blog.

## Programme Relevance

This file is example starter-pack content for `sdlc-knowledge-base`. The 14-dimension rubric is the evaluation framework underlying EPIC #97's commissioning decisions — choosing which SDLC option fits a project requires understanding what each option scores well on and what trade-offs each makes. The framework's commissioning skill (sub-feature 1 of EPIC #97) uses this rubric's dimensions implicitly when asking projects about team size, blast radius, and regulatory exposure.
